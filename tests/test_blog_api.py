from app.infrastructure.db.orm_models import AuditLog, User
from app.infrastructure.security.password import hash_password
from app.interfaces.api.dependencies import get_db_session


def add_user(username: str, password: str) -> None:
    from app.main import app

    override = app.dependency_overrides[get_db_session]
    db_gen = override()
    db = next(db_gen)
    try:
        db.add(User(username=username, password_hash=hash_password(password), role="owner"))
        db.commit()
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def login(client, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_blog_post_draft_publish_unpublish_flow(client, auth_headers):
    create = client.post(
        "/blog/posts",
        headers=auth_headers,
        json={"title": "Sprint Notes", "slug": "sprint-notes", "tags": "pcs,blog"},
    )
    assert create.status_code == 200
    draft = create.json()
    assert draft["status"] == "draft"
    assert draft["body"] == ""
    assert draft["published_at"] is None

    blocked_publish = client.post(f"/blog/posts/{draft['id']}/publish", headers=auth_headers)
    assert blocked_publish.status_code == 400
    assert blocked_publish.json() == {"detail": "Body is required for publishing"}

    update = client.put(
        f"/blog/posts/{draft['id']}",
        headers=auth_headers,
        json={"body": "Ready to publish", "summary": "Ready"},
    )
    assert update.status_code == 200

    publish = client.post(f"/blog/posts/{draft['id']}/publish", headers=auth_headers)
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"
    assert publish.json()["published_at"] is not None

    unpublish = client.post(f"/blog/posts/{draft['id']}/unpublish", headers=auth_headers)
    assert unpublish.status_code == 200
    assert unpublish.json()["status"] == "draft"
    assert unpublish.json()["published_at"] is None

    from app.main import app

    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    try:
        actions = [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]
    finally:
        db_gen.close()
    assert "blog_post_created" in actions
    assert "blog_post_updated" in actions
    assert "blog_post_published" in actions
    assert "blog_post_unpublished" in actions


def test_blog_post_slug_is_generated_when_omitted(client, auth_headers):
    response = client.post("/blog/posts", headers=auth_headers, json={"title": "Hello, PCS Blog!"})

    assert response.status_code == 200
    assert response.json()["slug"] == "hello-pcs-blog"


def test_blog_slug_lookup_listing_search_and_uniqueness(client, auth_headers):
    response = client.post(
        "/blog/posts",
        headers=auth_headers,
        json={"title": "Searchable", "slug": "searchable", "body": "alpha beta", "tags": "alpha"},
    )
    assert response.status_code == 200
    post = response.json()

    duplicate = client.post("/blog/posts", headers=auth_headers, json={"title": "Duplicate", "slug": "searchable"})
    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "Slug already exists"}

    by_id = client.get(f"/blog/posts/{post['id']}", headers=auth_headers)
    assert by_id.status_code == 200
    assert by_id.json()["slug"] == "searchable"

    by_slug = client.get("/blog/posts/slug/searchable", headers=auth_headers)
    assert by_slug.status_code == 200
    assert by_slug.json()["id"] == post["id"]

    listing = client.get("/blog/posts", headers=auth_headers)
    assert listing.status_code == 200
    assert [item["slug"] for item in listing.json()] == ["searchable"]

    search = client.get("/blog/posts?q=beta", headers=auth_headers)
    assert search.status_code == 200
    assert [item["slug"] for item in search.json()] == ["searchable"]


def test_blog_posts_are_owner_scoped(client, auth_headers):
    add_user("other", "other-password")
    other_headers = login(client, "other", "other-password")

    response = client.post("/blog/posts", headers=auth_headers, json={"title": "Private", "slug": "private"})
    assert response.status_code == 200
    post = response.json()

    other_get = client.get(f"/blog/posts/{post['id']}", headers=other_headers)
    assert other_get.status_code == 404

    other_slug = client.get("/blog/posts/slug/private", headers=other_headers)
    assert other_slug.status_code == 404

    other_list = client.get("/blog/posts", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []
