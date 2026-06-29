def test_core_api_families_remain_discoverable(client, auth_headers):
    checks = [
        ("GET", "/content"),
        ("GET", "/blog/posts"),
        ("GET", "/media"),
        ("GET", "/email/messages"),
        ("GET", "/travel/itineraries"),
        ("GET", "/imports/sources"),
    ]

    for method, path in checks:
        response = client.request(method, path, headers=auth_headers)
        assert response.status_code == 200, path


def test_openapi_metadata_and_tags_are_clean(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Private Content Service"
    assert schema["info"]["version"] == "0.9.0"
    assert schema["info"]["description"]
    assert "system" in schema["paths"]["/system/health"]["get"]["tags"]
    assert "content" in schema["paths"]["/content"]["get"]["tags"]
