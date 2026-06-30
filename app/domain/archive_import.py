from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ArchiveStatus(StrEnum):
    REGISTERED = "registered"
    SCANNED = "scanned"
    IMPORTED = "imported"
    FAILED = "failed"


@dataclass(frozen=True)
class ArchiveImportSet:
    id: int | None
    owner_id: int
    external_source_id: int
    external_account_id: int
    display_name: str
    source_type: str
    notes: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class ArchiveFile:
    id: int | None
    import_set_id: int
    original_filename: str
    stored_filename: str
    size_bytes: int
    sha256_hash: str | None
    status: ArchiveStatus = ArchiveStatus.REGISTERED
    error_message: str | None = None
    registered_at: datetime | None = None


@dataclass(frozen=True)
class ArchiveEntry:
    original_path: str
    normalised_path: str
    service: str
    content_type: str
    extension: str
    size_bytes: int


@dataclass(frozen=True)
class ArchiveScanSummary:
    archive_file_id: int | None
    top_level_folders: tuple[str, ...]
    entries: tuple[ArchiveEntry, ...]
    counts_by_service: dict[str, int] = field(default_factory=dict)
    counts_by_content_type: dict[str, int] = field(default_factory=dict)
    counts_by_extension: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportSetSummary:
    import_set_id: int
    archive_count: int
    entries_count: int
    counts_by_service: dict[str, int]
    counts_by_content_type: dict[str, int]
    counts_by_extension: dict[str, int]


@dataclass(frozen=True)
class ArchiveImportResult:
    import_set_id: int
    imported_count: int
    email_count: int = 0
