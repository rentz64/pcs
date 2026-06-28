from app.infrastructure.db.orm_models import AuditLog, User
from app.infrastructure.security.password import hash_password
from app.interfaces.api.dependencies import get_db_session


def add_user(username: str, password: str) -> None:
    from app.main import app

    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    try:
        db.add(User(username=username, password_hash=hash_password(password), role="owner"))
        db.commit()
    finally:
        db_gen.close()


def login(client, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_upload_list_search_download_media_and_audit(client, auth_headers):
    upload = client.post(
        "/media",
        headers=auth_headers,
        data={"title": "Header Image", "description": "A header", "tags": "site,image"},
        files={"file": ("header.png", b"image-bytes", "image/png")},
    )
    assert upload.status_code == 200
    item = upload.json()
    assert item["media_type"] == "image"
    assert item["original_filename"] == "header.png"
    assert item["mime_type"] == "image/png"
    assert item["size_bytes"] == len(b"image-bytes")

    listing = client.get("/media", headers=auth_headers)
    assert listing.status_code == 200
    assert [row["id"] for row in listing.json()] == [item["id"]]

    search = client.get("/media?q=header", headers=auth_headers)
    assert search.status_code == 200
    assert search.json()[0]["id"] == item["id"]

    download = client.get(f"/media/{item['id']}/download", headers=auth_headers)
    assert download.status_code == 200
    assert download.content == b"image-bytes"

    from app.main import app

    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    try:
        actions = [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]
    finally:
        db_gen.close()
    assert "media_uploaded" in actions
    assert "media_downloaded" in actions


def test_media_upload_rejects_unsupported_mime_type(client, auth_headers):
    upload = client.post(
        "/media",
        headers=auth_headers,
        data={"title": "Document"},
        files={"file": ("doc.pdf", b"pdf", "application/pdf")},
    )

    assert upload.status_code == 400
    assert upload.json() == {"detail": "Unsupported media type"}


def test_media_is_owner_scoped(client, auth_headers):
    add_user("media-other", "other-password")
    other_headers = login(client, "media-other", "other-password")

    upload = client.post(
        "/media",
        headers=auth_headers,
        data={"title": "Private Image"},
        files={"file": ("private.png", b"private", "image/png")},
    )
    assert upload.status_code == 200
    item = upload.json()

    other_get = client.get(f"/media/{item['id']}", headers=other_headers)
    assert other_get.status_code == 404

    other_download = client.get(f"/media/{item['id']}/download", headers=other_headers)
    assert other_download.status_code == 404

    other_list = client.get("/media", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []
