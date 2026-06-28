from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app.domain.entities import ContentItem


@dataclass(frozen=True)
class UploadContentCommand:
    title: str
    content_type: str
    description: str | None
    tags: str
    original_filename: str
    mime_type: str | None
    content: BinaryIO


@dataclass(frozen=True)
class DownloadContent:
    item: ContentItem
    path: Path


@dataclass(frozen=True)
class CreateBlogPostCommand:
    title: str
    slug: str
    body: str = ""
    summary: str | None = None
    tags: str = ""
    collections: tuple[int, ...] = ()


@dataclass(frozen=True)
class UpdateBlogPostCommand:
    title: str | None = None
    slug: str | None = None
    body: str | None = None
    summary: str | None = None
    tags: str | None = None
    collections: tuple[int, ...] | None = None


@dataclass(frozen=True)
class RegisterExternalSourceCommand:
    name: str
    source_type: str


@dataclass(frozen=True)
class RegisterExternalAccountCommand:
    source_id: int
    name: str
    external_account_ref: str


@dataclass(frozen=True)
class CreateImportJobCommand:
    source_id: int
    account_id: int
    content_types: tuple[str, ...]


@dataclass(frozen=True)
class UploadMediaCommand:
    title: str
    description: str | None
    tags: str
    original_filename: str
    mime_type: str
    content: BinaryIO


@dataclass(frozen=True)
class CreateTravelItineraryCommand:
    title: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str = "draft"


@dataclass(frozen=True)
class UpdateTravelItineraryCommand:
    title: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class AddTravelPlaceCommand:
    name: str
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    visit_start: str | None = None
    visit_end: str | None = None
    sequence_order: int = 0


@dataclass(frozen=True)
class UpdateTravelPlaceCommand:
    name: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    visit_start: str | None = None
    visit_end: str | None = None
    sequence_order: int | None = None


@dataclass(frozen=True)
class AddTravelRouteCommand:
    origin_place_id: int
    destination_place_id: int
    transport_mode: str
    distance_meters: int | None = None
    duration_seconds: int | None = None
    sequence_order: int = 0


@dataclass(frozen=True)
class UpdateTravelRouteCommand:
    origin_place_id: int | None = None
    destination_place_id: int | None = None
    transport_mode: str | None = None
    distance_meters: int | None = None
    duration_seconds: int | None = None
    sequence_order: int | None = None
