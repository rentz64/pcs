from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ImportJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ExternalSource:
    id: int | None
    owner_id: int
    name: str
    source_type: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class ExternalAccount:
    id: int | None
    owner_id: int
    source_id: int
    name: str
    external_account_ref: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class ImportJob:
    id: int | None
    owner_id: int
    source_id: int
    account_id: int
    content_types: tuple[str, ...]
    status: ImportJobStatus = ImportJobStatus.PENDING
    imported_count: int = 0
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ImportBatch:
    id: int | None
    owner_id: int
    job_id: int
    source_id: int
    account_id: int
    imported_count: int = 0
    created_at: datetime | None = None


@dataclass(frozen=True)
class ImportedContent:
    external_content_id: str
    external_content_type: str
    title: str
    body: str = ""
    summary: str | None = None
    tags: str = ""
    source_url: str | None = None
    source_reference: str | None = None


@dataclass(frozen=True)
class ImportedContentReference:
    content_item_id: int
    source_id: int
    account_id: int
    external_content_id: str
    external_content_type: str
    import_batch_id: int
    imported_at: datetime
    source_url: str | None = None
    source_reference: str | None = None

