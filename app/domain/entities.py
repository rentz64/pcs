from dataclasses import dataclass, field
from datetime import datetime


def parse_tags(tags: str) -> tuple[str, ...]:
    parsed: list[str] = []
    seen: set[str] = set()
    for tag in (part.strip() for part in tags.split(",")):
        if not tag:
            continue
        key = tag.casefold()
        if key not in seen:
            parsed.append(tag)
            seen.add(key)
    return tuple(parsed)


@dataclass(frozen=True)
class User:
    id: int | None
    username: str
    password_hash: str
    role: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class CollectionRef:
    id: int
    name: str


@dataclass(frozen=True)
class VersionMetadata:
    version_number: int = 1
    version_label: str | None = None
    previous_content_id: int | None = None


@dataclass(frozen=True)
class ContentMetadata:
    tags: tuple[str, ...] = ()
    source: str = "local_upload"
    attributes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_legacy_tags(cls, tags: str) -> "ContentMetadata":
        return cls(tags=parse_tags(tags))


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
    origin: str = "native"
    external_source_id: int | None = None
    external_account_id: int | None = None
    external_content_id: str | None = None
    external_content_type: str | None = None
    imported_at: datetime | None = None
    import_batch_id: int | None = None
    source_url: str | None = None
    source_reference: str | None = None
    metadata: ContentMetadata | None = None
    collections: tuple[CollectionRef, ...] = ()
    version: VersionMetadata = field(default_factory=VersionMetadata)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", ContentMetadata.from_legacy_tags(self.tags))


@dataclass(frozen=True)
class AuditEntry:
    id: int | None
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None = None
    details: str | None = None
    created_at: datetime | None = None

