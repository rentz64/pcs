from app.infrastructure.db.orm_models import AuditLog
from app.interfaces.api.dependencies import get_db_session
from app.main import app


def open_test_db_session():
    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    return db, db_gen


def close_test_db_session(db_gen) -> None:
    db_gen.close()


def test_system_job_api_enqueue_execute_and_get_status(client, auth_headers):
    create_response = client.post(
        "/system/jobs",
        headers=auth_headers,
        json={"task_type": "system.noop", "payload": {"message": "api"}, "max_attempts": 2},
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "queued"
    assert created["task_type"] == "system.noop"
    assert created["payload_json"] == {"message": "api"}

    execute_response = client.post(f"/system/jobs/{created['id']}/execute", headers=auth_headers)
    assert execute_response.status_code == 200
    executed = execute_response.json()
    assert executed["status"] == "succeeded"
    assert executed["attempts"] == 1
    assert executed["result_json"] == {"ok": True, "task": "system.noop"}
    assert executed["started_at"] is not None
    assert executed["completed_at"] is not None

    get_response = client.get(f"/system/jobs/{created['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "succeeded"


def test_system_job_api_execute_next_and_list(client, auth_headers):
    first = client.post("/system/jobs", headers=auth_headers, json={"task_type": "content.reindex"}).json()
    second = client.post("/system/jobs", headers=auth_headers, json={"task_type": "imports.placeholder"}).json()

    execute_next = client.post("/system/jobs/execute-next", headers=auth_headers)

    assert execute_next.status_code == 200
    assert execute_next.json()["id"] == first["id"]
    jobs = client.get("/system/jobs", headers=auth_headers)
    assert jobs.status_code == 200
    statuses = {job["id"]: job["status"] for job in jobs.json()}
    assert statuses[first["id"]] == "succeeded"
    assert statuses[second["id"]] == "queued"


def test_system_job_api_retry_and_cancel(client, auth_headers):
    failing = client.post(
        "/system/jobs",
        headers=auth_headers,
        json={"task_type": "system.fail", "payload": {"message": "api failure"}, "max_attempts": 2},
    ).json()
    failed = client.post(f"/system/jobs/{failing['id']}/execute", headers=auth_headers)
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"

    retry = client.post(f"/system/jobs/{failing['id']}/retry", headers=auth_headers)
    assert retry.status_code == 200
    assert retry.json()["status"] == "queued"
    assert retry.json()["attempts"] == 1

    queued = client.post("/system/jobs", headers=auth_headers, json={"task_type": "system.noop"}).json()
    cancel = client.post(f"/system/jobs/{queued['id']}/cancel", headers=auth_headers)
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    db, db_gen = open_test_db_session()
    try:
        actions = [row.action for row in db.query(AuditLog).all()]
        assert "job_queued" in actions
        assert "job_started" in actions
        assert "job_failed" in actions
        assert "job_retried" in actions
        assert "job_cancelled" in actions
    finally:
        close_test_db_session(db_gen)


def test_system_job_api_rejects_invalid_transitions(client, auth_headers):
    job = client.post("/system/jobs", headers=auth_headers, json={"task_type": "system.noop"}).json()
    client.post(f"/system/jobs/{job['id']}/execute", headers=auth_headers)

    execute_again = client.post(f"/system/jobs/{job['id']}/execute", headers=auth_headers)
    retry_succeeded = client.post(f"/system/jobs/{job['id']}/retry", headers=auth_headers)

    assert execute_again.status_code == 409
    assert retry_succeeded.status_code == 409
