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
