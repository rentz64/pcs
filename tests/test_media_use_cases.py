from __future__ import annotations

from dataclasses import replace
from io import BytesIO

import pytest

from app.application.dto import UploadMediaCommand
from app.application.media_use_cases import MediaUseCases
from app.domain.entities import ContentItem, User
from app.domain.errors import InvalidMediaType, MediaItemNotFound, StoredObjectNotFound
from app.domain.media import MediaItem, MediaType
from tests.test_use_cases import FakeAudit, FakeContent, FakeStorage


class FakeMedia:
    def __init__(self):
        self.items: list[MediaItem] = []

    def add(self, media: MediaItem) -> MediaItem:
        saved = replace(media, id=len(self.items) + 1)
        self.items.append(saved)
        return saved

    def get_for_owner(self, media_id: int, owner_id: int) -> MediaItem | None:
        return next((item for item in self.items if item.id == media_id and item.owner_id == owner_id), None)

    def list_for_owner(self, owner_id: int) -> list[MediaItem]:
        return [item for item in self.items if item.owner_id == owner_id]

    def search_for_owner(self, owner_id: int, query: str) -> list[MediaItem]:
        lowered = query.lower()
        return [
            item
            for item in self.list_for_owner(owner_id)
            if lowered in item.content_item.title.lower()
            or lowered in item.original_filename.lower()
            or lowered in item.content_item.tags.lower()
        ]


def owner(user_id: int = 7) -> User:
    return User(id=user_id, username=f"user-{user_id}", password_hash="x", role="owner")


def upload_command(mime_type: str = "image/png") -> UploadMediaCommand:
    return UploadMediaCommand(
        title="Header Image",
        description="A header",
        tags="site,image",
        original_filename="header.png",
        mime_type=mime_type,
        content=BytesIO(b"image-bytes"),
    )


def test_upload_media_creates_content_item_media_metadata_and_audit():
    content = FakeContent()
    media = FakeMedia()
    audit = FakeAudit()
    use_cases = MediaUseCases(media, content, audit, FakeStorage())

    item = use_cases.upload(owner(), upload_command())

    assert item.media_type == MediaType.IMAGE
    assert item.content_item.content_type == "image"
    assert item.content_item.stored_filename == "stored-header.png"
    assert item.original_filename == "header.png"
    assert item.mime_type == "image/png"
    assert item.size_bytes == len(b"image-bytes")
    assert content.items[0] == item.content_item
    assert audit.entries[0].action == "media_uploaded"


def test_upload_media_rejects_non_media_mime_type():
    use_cases = MediaUseCases(FakeMedia(), FakeContent(), FakeAudit(), FakeStorage())

    with pytest.raises(InvalidMediaType):
        use_cases.upload(owner(), upload_command("application/pdf"))


def test_prepare_download_enforces_owner_and_existing_object():
    storage = FakeStorage()
    media = FakeMedia()
    use_cases = MediaUseCases(media, FakeContent(), FakeAudit(), storage)
    item = use_cases.upload(owner(1), upload_command())

    with pytest.raises(MediaItemNotFound):
        use_cases.prepare_download(owner(2), item.id)

    storage.saved.clear()
    with pytest.raises(StoredObjectNotFound):
        use_cases.prepare_download(owner(1), item.id)


def test_list_and_search_media_are_owner_scoped():
    use_cases = MediaUseCases(FakeMedia(), FakeContent(), FakeAudit(), FakeStorage())
    use_cases.upload(owner(1), upload_command())
    use_cases.upload(owner(2), UploadMediaCommand("Other", None, "video", "clip.mp4", "video/mp4", BytesIO(b"video")))

    assert len(use_cases.list_media(owner(1))) == 1
    assert [item.original_filename for item in use_cases.search_media(owner(1), "header")] == ["header.png"]

