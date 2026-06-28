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


def test_fake_email_import_list_search_get_attachments_download_and_audit(client, auth_headers):
    imported = client.post("/email/import/fake", headers=auth_headers)
    assert imported.status_code == 200
    message = imported.json()
    assert message["subject"] == "Fake Email"
    assert message["external_message_id"] == "fake-message-1"
    assert message["has_attachments"] is True

    listing = client.get("/email/messages", headers=auth_headers)
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [message["id"]]

    search = client.get("/email/messages?q=fake", headers=auth_headers)
    assert search.status_code == 200
    assert search.json()[0]["id"] == message["id"]

    by_id = client.get(f"/email/messages/{message['id']}", headers=auth_headers)
    assert by_id.status_code == 200
    assert by_id.json()["id"] == message["id"]

    attachments = client.get(f"/email/messages/{message['id']}/attachments", headers=auth_headers)
    assert attachments.status_code == 200
    attachment = attachments.json()[0]
    assert attachment["filename"] == "fake.txt"

    download = client.get(f"/email/attachments/{attachment['id']}/download", headers=auth_headers)
    assert download.status_code == 200
    assert download.content == b"fake attachment"

    from app.main import app

    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    try:
        actions = [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]
    finally:
        db_gen.close()
    assert "email_imported" in actions
    assert "email_viewed" in actions
    assert "email_attachment_downloaded" in actions


def test_fake_email_import_is_idempotent_per_account(client, auth_headers):
    first = client.post("/email/import/fake", headers=auth_headers)
    second = client.post("/email/import/fake", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_email_api_owner_scoping(client, auth_headers):
    add_user("email-other", "other-password")
    other_headers = login(client, "email-other", "other-password")

    imported = client.post("/email/import/fake", headers=auth_headers).json()

    other_get = client.get(f"/email/messages/{imported['id']}", headers=other_headers)
    assert other_get.status_code == 404

    other_list = client.get("/email/messages", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []


def test_fake_email_import_rejects_malformed_payload(client, auth_headers):
    response = client.post("/email/import/fake?malformed=true", headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"detail": "Malformed email payload"}
