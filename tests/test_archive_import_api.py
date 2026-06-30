from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.infrastructure.db.orm_models import ContentItem, EmailMessage
from app.interfaces.api.dependencies import get_db_session
from app.main import app


def zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def mbox_bytes(message_id: str, subject: str) -> bytes:
    return (
        b"From sender@example.com Sat Jan 01 00:00:00 2022\n"
        + f"Message-ID: <{message_id}>\n".encode()
        + f"Subject: {subject}\n".encode()
        + b"From: Sender <sender@example.com>\n"
        + b"To: Receiver <receiver@example.com>\n"
        + b"Date: Sat, 01 Jan 2022 00:00:00 +0000\n"
        + b"\n"
        + b"Hello from mbox.\n"
    )


def open_test_db_session():
    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    return db, db_gen


def close_test_db_session(db_gen) -> None:
    db_gen.close()


def create_import_set(client, auth_headers, account_label="person@example.com", display_name="Takeout"):
    response = client.post(
        "/archive-import/import-sets",
        headers=auth_headers,
        json={
            "display_name": display_name,
            "account_label": account_label,
            "source_type": "google_takeout",
            "notes": "synthetic",
        },
    )
    assert response.status_code == 200
    return response.json()


def register_archive(client, auth_headers, import_set_id, filename, data):
    response = client.post(
        f"/archive-import/import-sets/{import_set_id}/archives",
        headers=auth_headers,
        files={"file": (filename, data, "application/zip")},
    )
    assert response.status_code == 200
    return response.json()


def test_register_scan_and_import_multiple_archives_with_provenance(client, auth_headers):
    import_set = create_import_set(client, auth_headers)
    first = register_archive(
        client,
        auth_headers,
        import_set["id"],
        "takeout-001.zip",
        zip_bytes({"Takeout/Drive/report.pdf": b"pdf-data"}),
    )
    second = register_archive(
        client,
        auth_headers,
        import_set["id"],
        "takeout-002.zip",
        zip_bytes({"t1/My Drive/photo.jpg": b"jpg-data"}),
    )

    scan = client.post(f"/archive-import/import-sets/{import_set['id']}/scan", headers=auth_headers)
    assert scan.status_code == 200
    summary = scan.json()
    assert summary["archive_count"] == 2
    assert summary["counts_by_service"]["drive"] == 2

    imported = client.post(f"/archive-import/import-sets/{import_set['id']}/import", headers=auth_headers)
    assert imported.status_code == 200
    assert imported.json()["imported_count"] == 2

    db, db_gen = open_test_db_session()
    try:
        rows = db.query(ContentItem).filter(ContentItem.import_set_id == import_set["id"]).all()
        assert len(rows) == 2
        by_name = {row.original_filename: row for row in rows}
        assert by_name["report.pdf"].archive_file_id == first["id"]
        assert by_name["report.pdf"].original_archive_filename == "takeout-001.zip"
        assert by_name["report.pdf"].original_archive_internal_path == "Takeout/Drive/report.pdf"
        assert by_name["report.pdf"].normalised_path == "Drive/report.pdf"
        assert by_name["photo.jpg"].archive_file_id == second["id"]
        assert by_name["photo.jpg"].normalised_path == "My Drive/photo.jpg"
        assert all(row.import_batch_id is not None for row in rows)
        assert all(row.imported_at is not None for row in rows)
    finally:
        close_test_db_session(db_gen)


def test_import_sets_are_distinguished_by_google_account(client, auth_headers):
    first = create_import_set(client, auth_headers, "first@example.com", "First")
    second = create_import_set(client, auth_headers, "second@example.com", "Second")

    sets = client.get("/archive-import/import-sets", headers=auth_headers)

    assert sets.status_code == 200
    by_id = {item["id"]: item for item in sets.json()}
    assert by_id[first["id"]]["external_account_id"] != by_id[second["id"]]["external_account_id"]


def test_mbox_import_is_duplicate_safe(client, auth_headers):
    import_set = create_import_set(client, auth_headers)
    register_archive(
        client,
        auth_headers,
        import_set["id"],
        "mail.zip",
        zip_bytes({"Takeout/Mail/All mail.mbox": mbox_bytes("synthetic-1@example.com", "Synthetic Mail")}),
    )

    first = client.post(f"/archive-import/import-sets/{import_set['id']}/import", headers=auth_headers)
    second = client.post(f"/archive-import/import-sets/{import_set['id']}/import", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    db, db_gen = open_test_db_session()
    try:
        messages = db.query(EmailMessage).all()
        assert len(messages) == 1
        assert messages[0].external_message_id == "synthetic-1@example.com"
        assert messages[0].subject == "Synthetic Mail"
    finally:
        close_test_db_session(db_gen)


def test_archive_import_owner_scoping(client, auth_headers):
    import_set = create_import_set(client, auth_headers)

    from app.infrastructure.db.orm_models import User
    from app.infrastructure.security.password import hash_password

    db, db_gen = open_test_db_session()
    try:
        db.add(User(username="other-archive", password_hash=hash_password("other-password"), role="owner"))
        db.commit()
    finally:
        close_test_db_session(db_gen)

    login = client.post("/auth/login", json={"username": "other-archive", "password": "other-password"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.get("/archive-import/import-sets", headers=other_headers).json() == []
    assert client.get(f"/archive-import/import-sets/{import_set['id']}", headers=other_headers).status_code == 404
