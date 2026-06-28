from dataclasses import replace
from datetime import datetime, timezone

from app.application.dto import (
    AddTravelPlaceCommand,
    AddTravelRouteCommand,
    CreateTravelItineraryCommand,
    UpdateTravelItineraryCommand,
    UpdateTravelPlaceCommand,
    UpdateTravelRouteCommand,
)
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import (
    InvalidTravelItinerary,
    InvalidTravelPlace,
    InvalidTravelRoute,
    TravelItineraryNotFound,
    TravelPlaceNotFound,
    TravelRouteNotFound,
)
from app.domain.repositories import AuditRepository, ContentRepository, TravelRepository
from app.domain.travel import ItineraryStatus, TravelItinerary, TravelPlace, TravelRoute


class TravelUseCases:
    def __init__(self, travel: TravelRepository, content: ContentRepository, audits: AuditRepository):
        self.travel = travel
        self.content = content
        self.audits = audits

    def create_itinerary(self, user: User, command: CreateTravelItineraryCommand) -> TravelItinerary:
        self._validate_title(command.title)
        self._validate_date_range(command.start_date, command.end_date)
        status = self._parse_status(command.status)
        content_item = self.content.add(
            ContentItem(
                id=None,
                owner_id=user.id,
                title=command.title,
                description=command.description,
                content_type="travel_itinerary",
                original_filename=f"{self._slug(command.title)}.travel",
                stored_filename=f"travel:{user.id}:{datetime.now(timezone.utc).timestamp()}",
                mime_type="application/vnd.pcs.travel+json",
                size_bytes=0,
                tags="",
            )
        )
        itinerary = self.travel.add_itinerary(
            TravelItinerary(
                id=None,
                owner_id=user.id,
                content_item=content_item,
                title=command.title,
                description=command.description,
                start_date=command.start_date,
                end_date=command.end_date,
                status=status,
            )
        )
        self._audit(user.id, "travel_itinerary_created", "travel_itinerary", itinerary.id, itinerary.title)
        return self._hydrate(itinerary)

    def update_itinerary(self, user: User, itinerary_id: int, command: UpdateTravelItineraryCommand) -> TravelItinerary:
        itinerary = self._get_itinerary(user, itinerary_id)
        title = command.title if command.title is not None else itinerary.title
        description = command.description if command.description is not None else itinerary.description
        start_date = command.start_date if command.start_date is not None else itinerary.start_date
        end_date = command.end_date if command.end_date is not None else itinerary.end_date
        status = self._parse_status(command.status) if command.status is not None else itinerary.status
        self._validate_title(title)
        self._validate_date_range(start_date, end_date)
        updated = self.travel.update_itinerary(
            replace(
                itinerary,
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                status=status,
                updated_at=datetime.now(timezone.utc),
            )
        )
        self._audit(user.id, "travel_itinerary_updated", "travel_itinerary", updated.id, updated.title)
        return self._hydrate(updated)

    def get_itinerary(self, user: User, itinerary_id: int) -> TravelItinerary:
        return self._hydrate(self._get_itinerary(user, itinerary_id))

    def list_itineraries(self, user: User) -> list[TravelItinerary]:
        return [self._hydrate(row) for row in self.travel.list_itineraries_for_owner(user.id)]

    def search_itineraries(self, user: User, query: str) -> list[TravelItinerary]:
        return [self._hydrate(row) for row in self.travel.search_itineraries_for_owner(user.id, query)]

    def add_place(self, user: User, itinerary_id: int, command: AddTravelPlaceCommand) -> TravelPlace:
        self._get_itinerary(user, itinerary_id)
        self._validate_place(command.name, command.latitude, command.longitude, command.sequence_order)
        place = self.travel.add_place(
            TravelPlace(
                id=None,
                itinerary_id=itinerary_id,
                name=command.name,
                description=command.description,
                address=command.address,
                latitude=command.latitude,
                longitude=command.longitude,
                visit_start=self._parse_datetime(command.visit_start),
                visit_end=self._parse_datetime(command.visit_end),
                sequence_order=command.sequence_order,
            )
        )
        self._audit(user.id, "travel_place_added", "travel_place", place.id, place.name)
        return place

    def update_place(self, user: User, place_id: int, command: UpdateTravelPlaceCommand) -> TravelPlace:
        place = self._get_place(user, place_id)
        name = command.name if command.name is not None else place.name
        latitude = command.latitude if command.latitude is not None else place.latitude
        longitude = command.longitude if command.longitude is not None else place.longitude
        sequence_order = command.sequence_order if command.sequence_order is not None else place.sequence_order
        self._validate_place(name, latitude, longitude, sequence_order)
        updated = self.travel.update_place(
            replace(
                place,
                name=name,
                description=command.description if command.description is not None else place.description,
                address=command.address if command.address is not None else place.address,
                latitude=latitude,
                longitude=longitude,
                visit_start=self._parse_datetime(command.visit_start) if command.visit_start is not None else place.visit_start,
                visit_end=self._parse_datetime(command.visit_end) if command.visit_end is not None else place.visit_end,
                sequence_order=sequence_order,
            )
        )
        self._audit(user.id, "travel_place_updated", "travel_place", updated.id, updated.name)
        return updated

    def remove_place(self, user: User, place_id: int) -> None:
        place = self._get_place(user, place_id)
        self.travel.remove_place(place_id)
        self._audit(user.id, "travel_place_removed", "travel_place", place.id, place.name)

    def add_route(self, user: User, itinerary_id: int, command: AddTravelRouteCommand) -> TravelRoute:
        self._get_itinerary(user, itinerary_id)
        self._validate_route(
            user,
            itinerary_id,
            command.origin_place_id,
            command.destination_place_id,
            command.transport_mode,
            command.sequence_order,
        )
        route = self.travel.add_route(
            TravelRoute(
                id=None,
                itinerary_id=itinerary_id,
                origin_place_id=command.origin_place_id,
                destination_place_id=command.destination_place_id,
                transport_mode=command.transport_mode,
                distance_meters=command.distance_meters,
                duration_seconds=command.duration_seconds,
                sequence_order=command.sequence_order,
            )
        )
        self._audit(user.id, "travel_route_added", "travel_route", route.id, route.transport_mode)
        return route

    def update_route(self, user: User, route_id: int, command: UpdateTravelRouteCommand) -> TravelRoute:
        route = self._get_route(user, route_id)
        origin_place_id = command.origin_place_id if command.origin_place_id is not None else route.origin_place_id
        destination_place_id = (
            command.destination_place_id if command.destination_place_id is not None else route.destination_place_id
        )
        transport_mode = command.transport_mode if command.transport_mode is not None else route.transport_mode
        sequence_order = command.sequence_order if command.sequence_order is not None else route.sequence_order
        self._validate_route(user, route.itinerary_id, origin_place_id, destination_place_id, transport_mode, sequence_order)
        updated = self.travel.update_route(
            replace(
                route,
                origin_place_id=origin_place_id,
                destination_place_id=destination_place_id,
                transport_mode=transport_mode,
                distance_meters=command.distance_meters if command.distance_meters is not None else route.distance_meters,
                duration_seconds=command.duration_seconds if command.duration_seconds is not None else route.duration_seconds,
                sequence_order=sequence_order,
            )
        )
        self._audit(user.id, "travel_route_updated", "travel_route", updated.id, updated.transport_mode)
        return updated

    def remove_route(self, user: User, route_id: int) -> None:
        route = self._get_route(user, route_id)
        self.travel.remove_route(route_id)
        self._audit(user.id, "travel_route_removed", "travel_route", route.id, route.transport_mode)

    def export_placeholder(self, user: User, itinerary_id: int, format_name: str) -> dict[str, str]:
        self._get_itinerary(user, itinerary_id)
        return self._placeholder(format_name)

    def import_placeholder(self, user: User, format_name: str) -> dict[str, str]:
        _ = user
        return self._placeholder(format_name)

    def _get_itinerary(self, user: User, itinerary_id: int) -> TravelItinerary:
        itinerary = self.travel.get_itinerary_for_owner(itinerary_id, user.id)
        if not itinerary:
            raise TravelItineraryNotFound()
        return itinerary

    def _get_place(self, user: User, place_id: int) -> TravelPlace:
        place = self.travel.get_place_for_owner(place_id, user.id)
        if not place:
            raise TravelPlaceNotFound()
        return place

    def _get_route(self, user: User, route_id: int) -> TravelRoute:
        route = self.travel.get_route_for_owner(route_id, user.id)
        if not route:
            raise TravelRouteNotFound()
        return route

    def _hydrate(self, itinerary: TravelItinerary) -> TravelItinerary:
        if itinerary.id is None:
            return itinerary
        places = tuple(sorted(self.travel.list_places_for_itinerary(itinerary.id), key=lambda row: (row.sequence_order, row.id or 0)))
        routes = tuple(sorted(self.travel.list_routes_for_itinerary(itinerary.id), key=lambda row: (row.sequence_order, row.id or 0)))
        return replace(itinerary, places=places, routes=routes)

    def _validate_title(self, title: str) -> None:
        if not title.strip():
            raise InvalidTravelItinerary("Title is required")

    def _validate_date_range(self, start_date: str | None, end_date: str | None) -> None:
        if start_date and end_date and end_date < start_date:
            raise InvalidTravelItinerary("End date cannot precede start date")

    def _validate_place(self, name: str, latitude: float | None, longitude: float | None, sequence_order: int) -> None:
        if not name.strip():
            raise InvalidTravelPlace("Place name is required")
        if latitude is not None and not -90 <= latitude <= 90:
            raise InvalidTravelPlace("Latitude must be between -90 and 90")
        if longitude is not None and not -180 <= longitude <= 180:
            raise InvalidTravelPlace("Longitude must be between -180 and 180")
        if sequence_order < 0:
            raise InvalidTravelPlace("Sequence order must be non-negative")

    def _validate_route(
        self,
        user: User,
        itinerary_id: int,
        origin_place_id: int,
        destination_place_id: int,
        transport_mode: str,
        sequence_order: int,
    ) -> None:
        if not transport_mode.strip():
            raise InvalidTravelRoute("Transport mode is required")
        if sequence_order < 0:
            raise InvalidTravelRoute("Sequence order must be non-negative")
        origin = self.travel.get_place_for_owner(origin_place_id, user.id)
        destination = self.travel.get_place_for_owner(destination_place_id, user.id)
        if not origin or not destination or origin.itinerary_id != itinerary_id or destination.itinerary_id != itinerary_id:
            raise InvalidTravelRoute("Route endpoints must belong to the itinerary")

    def _parse_status(self, status: str) -> ItineraryStatus:
        try:
            return ItineraryStatus(status)
        except ValueError:
            raise InvalidTravelItinerary("Invalid itinerary status")

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise InvalidTravelPlace("Invalid visit datetime")

    def _placeholder(self, format_name: str) -> dict[str, str]:
        normalized = format_name.casefold()
        if normalized not in {"geojson", "gpx", "kml"}:
            raise InvalidTravelItinerary("Unsupported travel format")
        return {"format": normalized, "status": "not_implemented"}

    def _slug(self, value: str) -> str:
        slug = "-".join(value.strip().lower().split())
        return slug or "itinerary"

    def _audit(
        self,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None,
        details: str | None,
    ) -> None:
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                details=details,
            )
        )
