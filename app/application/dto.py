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
    slug: str | None = None
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
