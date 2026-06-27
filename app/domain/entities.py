from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: int | None
    username: str
    password_hash: str
    role: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class ContentItem:
    id: int | None
    owner_id: int
    title: str
    description: str | None
    content_type: str
    original_filename: str
    stored_filename: str
    mime_type: str | None
    size_bytes: int
    tags: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class AuditEntry:
    id: int | None
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None = None
    details: str | None = None
    created_at: datetime | None = None

