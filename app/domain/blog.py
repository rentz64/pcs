from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.entities import CollectionRef, ContentItem


class BlogStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass(frozen=True)
class BlogPost:
    id: int | None
    owner_id: int
    content_item: ContentItem
    slug: str
    body: str
    summary: str | None
    status: BlogStatus
    tags: str
    collections: tuple[CollectionRef, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published_at: datetime | None = None

    @property
    def title(self) -> str:
        return self.content_item.title
