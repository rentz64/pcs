from __future__ import annotations

from io import BytesIO

from app.application.content_use_cases import ContentUseCases
from app.application.dto import UploadContentCommand
from app.domain.content_handlers import ContentTypeHandlerRegistry
from app.domain.entities import CollectionRef, ContentItem, ContentMetadata, User, VersionMetadata, parse_tags
from app.domain.repositories import SearchQuery
from tests.test_use_cases import FakeAudit, FakeContent, FakeStorage


class RecordingSearch:
    def __init__(self, results: list[ContentItem]):
        self.results = results
        self.queries: list[SearchQuery] = []

    def search(self, query: SearchQuery) -> list[ContentItem]:
        self.queries.append(query)
        return self.results


class RecordingHandler:
    content_type = "document"

    def __init__(self):
        self.calls: list[tuple[str | None, str]] = []

    def normalize_content_type(self, requested_content_type: str, mime_type: str | None, original_filename: str) -> str:
        self.calls.append((mime_type, original_filename))
        return requested_content_type


def test_parse_tags_normalizes_and_deduplicates_legacy_tag_string():
    assert parse_tags(" architecture, mvp,architecture ,, Sprint 3 ") == ("architecture", "mvp", "Sprint 3")


def test_content_item_exposes_shared_metadata_without_changing_legacy_tags_field():
    item = ContentItem(
        id=1,
        owner_id=2,
        title="Architecture Notes",
        description="Sprint document",
        content_type="document",
        original_filename="notes.txt",
        stored_filename="stored.txt",
        mime_type="text/plain",
        size_bytes=5,
        tags="architecture,mvp",
    )

    assert item.metadata == ContentMetadata(tags=("architecture", "mvp"))
    assert item.tags == "architecture,mvp"
    assert item.collections == ()
    assert item.version == VersionMetadata()


def test_content_item_accepts_collections_and_version_metadata():
    item = ContentItem(
        id=1,
        owner_id=2,
        title="Versioned",
        description=None,
        content_type="document",
        original_filename="v2.txt",
        stored_filename="stored-v2.txt",
        mime_type="text/plain",
        size_bytes=2,
        tags="draft",
        collections=(CollectionRef(id=10, name="Planning"),),
        version=VersionMetadata(version_number=2, version_label="review", previous_content_id=1),
    )

    assert item.collections[0].name == "Planning"
    assert item.version.version_number == 2
    assert item.version.previous_content_id == 1


def test_content_use_case_delegates_search_to_search_abstraction():
    expected = ContentItem(
        id=1,
        owner_id=7,
        title="Result",
        description=None,
        content_type="document",
        original_filename="result.txt",
        stored_filename="stored-result.txt",
        mime_type="text/plain",
        size_bytes=1,
        tags="found",
    )
    search = RecordingSearch([expected])
    use_cases = ContentUseCases(FakeContent(), FakeAudit(), FakeStorage(), search=search)
    user = User(id=7, username="owner", password_hash="x", role="owner")

    result = use_cases.search_for_user(user, "found")

    assert result == [expected]
    assert search.queries == [SearchQuery(owner_id=7, text="found")]


def test_content_use_case_invokes_content_type_handler_on_upload():
    handler = RecordingHandler()
    registry = ContentTypeHandlerRegistry()
    registry.register(handler)
    content = FakeContent()
    use_cases = ContentUseCases(content, FakeAudit(), FakeStorage(), handlers=registry)
    user = User(id=7, username="owner", password_hash="x", role="owner")

    item = use_cases.upload(
        user,
        UploadContentCommand(
            title="Handled",
            content_type="document",
            description=None,
            tags="handled",
            original_filename="handled.txt",
            mime_type="text/plain",
            content=BytesIO(b"ok"),
        ),
    )

    assert item.content_type == "document"
    assert handler.calls == [("text/plain", "handled.txt")]
