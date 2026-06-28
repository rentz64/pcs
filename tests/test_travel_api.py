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


def test_itinerary_place_route_lifecycle_and_audit(client, auth_headers):
    create = client.post(
        "/travel/itineraries",
        headers=auth_headers,
        json={
            "title": "Athens Weekend",
            "description": "Walkable itinerary",
            "start_date": "2026-09-01",
            "end_date": "2026-09-03",
        },
    )
    assert create.status_code == 200
    itinerary = create.json()
    assert itinerary["title"] == "Athens Weekend"
    assert itinerary["status"] == "draft"
    assert itinerary["places"] == []

    update = client.put(
        f"/travel/itineraries/{itinerary['id']}",
        headers=auth_headers,
        json={"status": "active", "description": "Updated"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "active"

    first = client.post(
        f"/travel/itineraries/{itinerary['id']}/places",
        headers=auth_headers,
        json={"name": "Hotel", "sequence_order": 0},
    )
    second = client.post(
        f"/travel/itineraries/{itinerary['id']}/places",
        headers=auth_headers,
        json={"name": "Museum", "latitude": 37.97, "longitude": 23.72, "sequence_order": 1},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    route = client.post(
        f"/travel/itineraries/{itinerary['id']}/routes",
        headers=auth_headers,
        json={
            "origin_place_id": first.json()["id"],
            "destination_place_id": second.json()["id"],
            "transport_mode": "walk",
            "sequence_order": 0,
        },
    )
    assert route.status_code == 200

    listing = client.get("/travel/itineraries?q=athens", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()[0]["places"][1]["name"] == "Museum"
    assert listing.json()[0]["routes"][0]["transport_mode"] == "walk"

    assert client.delete(f"/travel/routes/{route.json()['id']}", headers=auth_headers).status_code == 200
    assert client.delete(f"/travel/places/{second.json()['id']}", headers=auth_headers).status_code == 200

    from app.main import app

    db_gen = app.dependency_overrides[get_db_session]()
    db = next(db_gen)
    try:
        actions = [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]
    finally:
        db_gen.close()
    assert "travel_itinerary_created" in actions
    assert "travel_itinerary_updated" in actions
    assert "travel_place_added" in actions
    assert "travel_route_removed" in actions


def test_travel_validation_errors(client, auth_headers):
    invalid_dates = client.post(
        "/travel/itineraries",
        headers=auth_headers,
        json={"title": "Bad", "start_date": "2026-09-03", "end_date": "2026-09-01"},
    )
    assert invalid_dates.status_code == 400

    itinerary = client.post("/travel/itineraries", headers=auth_headers, json={"title": "Validation"}).json()
    bad_place = client.post(
        f"/travel/itineraries/{itinerary['id']}/places",
        headers=auth_headers,
        json={"name": "Bad", "latitude": -91},
    )
    assert bad_place.status_code == 400

    bad_route = client.post(
        f"/travel/itineraries/{itinerary['id']}/routes",
        headers=auth_headers,
        json={"origin_place_id": 1, "destination_place_id": 2, "transport_mode": "walk"},
    )
    assert bad_route.status_code == 400


def test_travel_owner_scoping(client, auth_headers):
    add_user("travel-other", "other-password")
    other_headers = login(client, "travel-other", "other-password")

    itinerary = client.post("/travel/itineraries", headers=auth_headers, json={"title": "Private"}).json()

    assert client.get(f"/travel/itineraries/{itinerary['id']}", headers=other_headers).status_code == 404
    assert client.get("/travel/itineraries", headers=other_headers).json() == []


def test_existing_content_upload_still_works(client, auth_headers):
    response = client.post(
        "/content",
        headers=auth_headers,
        data={"title": "Existing API", "content_type": "document", "description": "", "tags": ""},
        files={"file": ("note.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Existing API"
