def test_health_contract(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_bearer_token_is_rejected(client):
    response = client.get("/content")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_invalid_bearer_token_is_rejected(client):
    response = client.get("/content", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_unknown_content_download_returns_existing_detail(client, auth_headers):
    response = client.get("/content/999/download", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Content not found"}


def test_upload_uses_existing_form_defaults(client, auth_headers):
    response = client.post(
        "/content",
        headers=auth_headers,
        data={"title": "Defaults"},
        files={"file": ("defaults.bin", b"abc", "application/octet-stream")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content_type"] == "document"
    assert body["description"] is None
    assert body["tags"] == ""
    assert body["original_filename"] == "defaults.bin"
    assert body["mime_type"] == "application/octet-stream"
