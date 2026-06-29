def test_system_health_reports_dependencies(client):
    response = client.get("/system/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_version"]
    assert body["database"]["status"] == "ok"
    assert body["object_storage"]["status"] == "ok"
    assert body["background_jobs"]["status"] == "ok"


def test_system_status_exposes_sanitized_runtime_summary(client):
    response = client.get("/system/status")

    assert response.status_code == 200
    body = response.json()
    assert body["api_version"]
    assert body["configuration"]["runtime_environment"] in {"development", "test", "local"}
    assert "jwt_secret" not in body["configuration"]
    assert body["database"]["status"] == "ok"
    assert body["object_storage"]["backend"] == "local_filesystem"
    assert set(body["background_jobs"]["counts"]) == {"queued", "running", "succeeded", "failed", "cancelled"}
