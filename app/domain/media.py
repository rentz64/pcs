from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.entities import ContentItem


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass(frozen=True)
class MediaItem:
    id: int | None
    owner_id: int
    content_item: ContentItem
    media_type: MediaType
    original_filename: str
    mime_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
