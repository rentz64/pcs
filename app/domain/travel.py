from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.entities import ContentItem


class ItineraryStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class TravelPlace:
    id: int | None
    itinerary_id: int
    name: str
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    visit_start: datetime | None = None
    visit_end: datetime | None = None
    sequence_order: int = 0


@dataclass(frozen=True)
class TravelRoute:
    id: int | None
    itinerary_id: int
    origin_place_id: int
    destination_place_id: int
    transport_mode: str
    distance_meters: int | None = None
    duration_seconds: int | None = None
    sequence_order: int = 0


@dataclass(frozen=True)
class TravelItinerary:
    id: int | None
    owner_id: int
    content_item: ContentItem
    title: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: ItineraryStatus = ItineraryStatus.DRAFT
    places: tuple[TravelPlace, ...] = ()
    routes: tuple[TravelRoute, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
