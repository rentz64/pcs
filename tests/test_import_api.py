from app.infrastructure.db.orm_models import AuditLog, ContentItem
from app.interfaces.api.dependencies import get_db_session
from app.main import app


def open_test_db_session():
    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    return db, db_gen


def close_test_db_session(db_gen) -> None:
    db_gen.close()


def test_import_source_account_job_execution_and_provenance(client, auth_headers):
    source_response = client.post(
        "/imports/sources",
        headers=auth_headers,
        json={"name": "Local Import", "source_type": "local"},
    )
    assert source_response.status_code == 200
    source = source_response.json()

    account_response = client.post(
        "/imports/accounts",
        headers=auth_headers,
        json={"source_id": source["id"], "name": "Local Account", "external_account_ref": "local-test"},
    )
    assert account_response.status_code == 200
    account = account_response.json()

    content_types = client.get(f"/imports/sources/{source['id']}/content-types", headers=auth_headers)
    assert content_types.status_code == 200
    assert content_types.json() == {"content_types": ["document", "note"]}

    job_response = client.post(
        "/imports/jobs",
        headers=auth_headers,
        json={"source_id": source["id"], "account_id": account["id"], "content_types": ["note"]},
    )
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    assert job["imported_count"] == 1

    jobs = client.get("/imports/jobs", headers=auth_headers)
    assert jobs.status_code == 200
    assert [item["id"] for item in jobs.json()] == [job["id"]]

    by_id = client.get(f"/imports/jobs/{job['id']}", headers=auth_headers)
    assert by_id.status_code == 200
    assert by_id.json()["status"] == "completed"

    db, db_gen = open_test_db_session()
    try:
        imported = db.query(ContentItem).filter(ContentItem.origin == "imported").first()
        assert imported.external_source_id == source["id"]
        assert imported.external_account_id == account["id"]
        assert imported.external_content_id == "local-note-1"
        assert imported.external_content_type == "note"
        assert imported.import_batch_id is not None
        assert imported.imported_at is not None
        assert imported.source_url == "local://note/1"
        actions = [row.action for row in db.query(AuditLog).all()]
        assert "external_source_registered" in actions
        assert "external_account_registered" in actions
        assert "import_job_created" in actions
        assert "import_job_executed" in actions
        assert "content_imported" in actions
    finally:
        close_test_db_session(db_gen)


def test_import_api_rejects_invalid_source_and_account(client, auth_headers):
    missing_source = client.post(
        "/imports/accounts",
        headers=auth_headers,
        json={"source_id": 999, "name": "Missing", "external_account_ref": "missing"},
    )
    assert missing_source.status_code == 404

    source = client.post(
        "/imports/sources",
        headers=auth_headers,
        json={"name": "Local Import", "source_type": "local"},
    ).json()
    missing_account = client.post(
        "/imports/jobs",
        headers=auth_headers,
        json={"source_id": source["id"], "account_id": 999, "content_types": ["note"]},
    )
    assert missing_account.status_code == 404


def test_import_api_is_owner_scoped(client, auth_headers):
    source = client.post(
        "/imports/sources",
        headers=auth_headers,
        json={"name": "Local Import", "source_type": "local"},
    ).json()

    from app.infrastructure.db.orm_models import User
    from app.infrastructure.security.password import hash_password

    db, db_gen = open_test_db_session()
    try:
        db.add(User(username="other-importer", password_hash=hash_password("other-password"), role="owner"))
        db.commit()
    finally:
        close_test_db_session(db_gen)
    login = client.post("/auth/login", json={"username": "other-importer", "password": "other-password"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    other_sources = client.get("/imports/sources", headers=other_headers)
    assert other_sources.status_code == 200
    assert other_sources.json() == []

    other_content_types = client.get(f"/imports/sources/{source['id']}/content-types", headers=other_headers)
    assert other_content_types.status_code == 404
