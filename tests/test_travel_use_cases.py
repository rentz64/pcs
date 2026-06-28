from dataclasses import replace

import pytest

from app.application.dto import AddTravelPlaceCommand, AddTravelRouteCommand, CreateTravelItineraryCommand
from app.application.travel_use_cases import TravelUseCases
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import InvalidTravelItinerary, InvalidTravelPlace, InvalidTravelRoute, TravelItineraryNotFound
from app.domain.repositories import AuditRepository, ContentRepository, TravelRepository
from app.domain.travel import ItineraryStatus, TravelItinerary, TravelPlace, TravelRoute


class FakeContentRepository(ContentRepository):
    def __init__(self):
        self.items: list[ContentItem] = []

    def add(self, item: ContentItem) -> ContentItem:
        saved = replace(item, id=len(self.items) + 1)
        self.items.append(saved)
        return saved

    def list_for_owner(self, owner_id: int) -> list[ContentItem]:
        return [item for item in self.items if item.owner_id == owner_id]

    def search_for_owner(self, owner_id: int, query: str) -> list[ContentItem]:
        return [
            item
            for item in self.list_for_owner(owner_id)
            if query.casefold() in item.title.casefold() or query.casefold() in (item.description or "").casefold()
        ]

    def get_for_owner(self, content_id: int, owner_id: int) -> ContentItem | None:
        return next((item for item in self.items if item.id == content_id and item.owner_id == owner_id), None)


class FakeTravelRepository(TravelRepository):
    def __init__(self):
        self.itineraries: list[TravelItinerary] = []
        self.places: list[TravelPlace] = []
        self.routes: list[TravelRoute] = []

    def add_itinerary(self, itinerary: TravelItinerary) -> TravelItinerary:
        saved = replace(itinerary, id=len(self.itineraries) + 1)
        self.itineraries.append(saved)
        return saved

    def update_itinerary(self, itinerary: TravelItinerary) -> TravelItinerary:
        self.itineraries = [itinerary if row.id == itinerary.id else row for row in self.itineraries]
        return itinerary

    def get_itinerary_for_owner(self, itinerary_id: int, owner_id: int) -> TravelItinerary | None:
        return next((row for row in self.itineraries if row.id == itinerary_id and row.owner_id == owner_id), None)

    def list_itineraries_for_owner(self, owner_id: int) -> list[TravelItinerary]:
        return [row for row in self.itineraries if row.owner_id == owner_id]

    def search_itineraries_for_owner(self, owner_id: int, query: str) -> list[TravelItinerary]:
        return [
            row
            for row in self.list_itineraries_for_owner(owner_id)
            if query.casefold() in row.title.casefold() or query.casefold() in (row.description or "").casefold()
        ]

    def add_place(self, place: TravelPlace) -> TravelPlace:
        saved = replace(place, id=len(self.places) + 1)
        self.places.append(saved)
        return saved

    def update_place(self, place: TravelPlace) -> TravelPlace:
        self.places = [place if row.id == place.id else row for row in self.places]
        return place

    def remove_place(self, place_id: int) -> None:
        self.places = [row for row in self.places if row.id != place_id]

    def get_place_for_owner(self, place_id: int, owner_id: int) -> TravelPlace | None:
        owner_itinerary_ids = {row.id for row in self.itineraries if row.owner_id == owner_id}
        return next((row for row in self.places if row.id == place_id and row.itinerary_id in owner_itinerary_ids), None)

    def list_places_for_itinerary(self, itinerary_id: int) -> list[TravelPlace]:
        return [row for row in self.places if row.itinerary_id == itinerary_id]

    def add_route(self, route: TravelRoute) -> TravelRoute:
        saved = replace(route, id=len(self.routes) + 1)
        self.routes.append(saved)
        return saved

    def update_route(self, route: TravelRoute) -> TravelRoute:
        self.routes = [route if row.id == route.id else row for row in self.routes]
        return route

    def remove_route(self, route_id: int) -> None:
        self.routes = [row for row in self.routes if row.id != route_id]

    def get_route_for_owner(self, route_id: int, owner_id: int) -> TravelRoute | None:
        owner_itinerary_ids = {row.id for row in self.itineraries if row.owner_id == owner_id}
        return next((row for row in self.routes if row.id == route_id and row.itinerary_id in owner_itinerary_ids), None)

    def list_routes_for_itinerary(self, itinerary_id: int) -> list[TravelRoute]:
        return [row for row in self.routes if row.itinerary_id == itinerary_id]


class FakeAuditRepository(AuditRepository):
    def __init__(self):
        self.entries: list[AuditEntry] = []

    def add(self, entry: AuditEntry) -> AuditEntry:
        saved = replace(entry, id=len(self.entries) + 1)
        self.entries.append(saved)
        return saved

    def list_for_user(self, user_id: int, limit: int = 100) -> list[AuditEntry]:
        return [entry for entry in self.entries if entry.user_id == user_id][:limit]


@pytest.fixture()
def use_cases():
    return TravelUseCases(FakeTravelRepository(), FakeContentRepository(), FakeAuditRepository())


@pytest.fixture()
def user():
    return User(id=1, username="owner", password_hash="hash", role="owner")


def test_create_and_search_itinerary(use_cases, user):
    itinerary = use_cases.create_itinerary(
        user,
        CreateTravelItineraryCommand(
            title="Athens Weekend",
            description="Acropolis and Plaka",
            start_date="2026-09-01",
            end_date="2026-09-03",
        ),
    )

    assert itinerary.id == 1
    assert itinerary.content_item.content_type == "travel_itinerary"
    assert itinerary.status == ItineraryStatus.DRAFT
    assert use_cases.search_itineraries(user, "plaka") == [itinerary]


def test_rejects_invalid_itinerary_date_range(use_cases, user):
    with pytest.raises(InvalidTravelItinerary):
        use_cases.create_itinerary(
            user,
            CreateTravelItineraryCommand(title="Bad dates", start_date="2026-09-03", end_date="2026-09-01"),
        )


def test_place_and_route_lifecycle(use_cases, user):
    itinerary = use_cases.create_itinerary(user, CreateTravelItineraryCommand(title="Route test"))
    first = use_cases.add_place(user, itinerary.id, AddTravelPlaceCommand(name="Hotel", sequence_order=0))
    second = use_cases.add_place(user, itinerary.id, AddTravelPlaceCommand(name="Museum", latitude=37.97, longitude=23.72, sequence_order=1))

    route = use_cases.add_route(
        user,
        itinerary.id,
        AddTravelRouteCommand(origin_place_id=first.id, destination_place_id=second.id, transport_mode="walk"),
    )

    loaded = use_cases.get_itinerary(user, itinerary.id)
    assert [place.name for place in loaded.places] == ["Hotel", "Museum"]
    assert loaded.routes == (route,)

    use_cases.remove_route(user, route.id)
    use_cases.remove_place(user, second.id)
    loaded = use_cases.get_itinerary(user, itinerary.id)
    assert loaded.routes == ()
    assert [place.name for place in loaded.places] == ["Hotel"]


def test_validates_place_coordinates_and_route_endpoints(use_cases, user):
    itinerary = use_cases.create_itinerary(user, CreateTravelItineraryCommand(title="Validation"))
    first = use_cases.add_place(user, itinerary.id, AddTravelPlaceCommand(name="One"))

    with pytest.raises(InvalidTravelPlace):
        use_cases.add_place(user, itinerary.id, AddTravelPlaceCommand(name="Bad", latitude=95))

    with pytest.raises(InvalidTravelRoute):
        use_cases.add_route(
            user,
            itinerary.id,
            AddTravelRouteCommand(origin_place_id=first.id, destination_place_id=999, transport_mode="walk"),
        )


def test_owner_scoping(use_cases, user):
    other = User(id=2, username="other", password_hash="hash", role="owner")
    itinerary = use_cases.create_itinerary(user, CreateTravelItineraryCommand(title="Private"))

    with pytest.raises(TravelItineraryNotFound):
        use_cases.get_itinerary(other, itinerary.id)


def test_geo_format_placeholders(use_cases, user):
    itinerary = use_cases.create_itinerary(user, CreateTravelItineraryCommand(title="Exportable"))

    assert use_cases.export_placeholder(user, itinerary.id, "geojson")["status"] == "not_implemented"
    assert use_cases.import_placeholder(user, "gpx")["status"] == "not_implemented"
