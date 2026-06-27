def test_upload_list_search_download_and_audit(client, auth_headers):
    upload = client.post(
        "/content",
        headers=auth_headers,
        data={
            "title": "Architecture Notes",
            "description": "Sprint 1 test document",
            "content_type": "document",
            "tags": "architecture,mvp",
        },
        files={"file": ("notes.txt", b"hello private content", "text/plain")},
    )
    assert upload.status_code == 200
    item = upload.json()
    assert item["title"] == "Architecture Notes"
    assert item["size_bytes"] == len(b"hello private content")

    listing = client.get("/content", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    search = client.get("/content/search?q=mvp", headers=auth_headers)
    assert search.status_code == 200
    assert search.json()[0]["original_filename"] == "notes.txt"

    download = client.get(f"/content/{item['id']}/download", headers=auth_headers)
    assert download.status_code == 200
    assert download.content == b"hello private content"

    audit = client.get("/audit", headers=auth_headers)
    assert audit.status_code == 200
    actions = [entry["action"] for entry in audit.json()]
    assert "content_uploaded" in actions
    assert "content_downloaded" in actions
