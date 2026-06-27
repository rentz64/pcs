from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from io import BytesIO

import pytest

from app.application.auth_use_cases import AuthUseCases
from app.application.content_use_cases import ContentUseCases
from app.application.dto import UploadContentCommand
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import ContentNotFound, InvalidCredentials


class FakeUsers:
    def __init__(self, users: list[User]):
        self.users = {user.username: user for user in users}

    def get_by_username(self, username: str) -> User | None:
        return self.users.get(username)

    def add(self, user: User) -> User:
        self.users[user.username] = user
        return user


class FakeAudit:
    def __init__(self):
        self.entries: list[AuditEntry] = []

    def add(self, entry: AuditEntry) -> AuditEntry:
        self.entries.append(entry)
        return entry

    def list_for_user(self, user_id: int, limit: int = 100) -> list[AuditEntry]:
        return [entry for entry in self.entries if entry.user_id == user_id][:limit]


class FakeContent:
    def __init__(self):
        self.items: list[ContentItem] = []

    def add(self, item: ContentItem) -> ContentItem:
        saved = replace(item, id=len(self.items) + 1)
        self.items.append(saved)
        return saved

    def list_for_owner(self, owner_id: int) -> list[ContentItem]:
        return [item for item in self.items if item.owner_id == owner_id]

    def search_for_owner(self, owner_id: int, query: str) -> list[ContentItem]:
        lowered = query.lower()
        return [
            item
            for item in self.list_for_owner(owner_id)
            if lowered in item.title.lower()
            or (item.description and lowered in item.description.lower())
            or lowered in item.original_filename.lower()
            or lowered in item.tags.lower()
            or lowered in item.content_type.lower()
        ]

    def get_for_owner(self, content_id: int, owner_id: int) -> ContentItem | None:
        return next((item for item in self.items if item.id == content_id and item.owner_id == owner_id), None)


class FakeStorage:
    def __init__(self):
        self.saved: dict[str, bytes] = {}

    def save(self, original_filename: str, content) -> tuple[str, int]:
        stored_name = f"stored-{original_filename}"
        data = content.read()
        self.saved[stored_name] = data
        return stored_name, len(data)

    def path_for(self, stored_filename: str):
        return stored_filename

    def exists(self, stored_filename: str) -> bool:
        return stored_filename in self.saved


class PlainPassword:
    def verify(self, password: str, password_hash: str) -> bool:
        return password == password_hash

    def hash(self, password: str) -> str:
        return password


class StaticTokens:
    def create(self, username: str) -> str:
        return f"token:{username}"

    def decode_username(self, token: str) -> str | None:
        if token.startswith("token:"):
            return token.removeprefix("token:")
        return None


def test_authenticate_user_returns_token_and_audits_login():
    user = User(id=1, username="admin", password_hash="secret", role="owner", created_at=datetime.now(timezone.utc))
    audit = FakeAudit()
    use_cases = AuthUseCases(FakeUsers([user]), audit, PlainPassword(), StaticTokens())

    token = use_cases.login("admin", "secret")

    assert token == "token:admin"
    assert audit.entries[0].action == "login"
    assert audit.entries[0].entity_type == "user"
    assert audit.entries[0].entity_id == "1"


def test_authenticate_user_rejects_bad_password():
    user = User(id=1, username="admin", password_hash="secret", role="owner", created_at=datetime.now(timezone.utc))
    use_cases = AuthUseCases(FakeUsers([user]), FakeAudit(), PlainPassword(), StaticTokens())

    with pytest.raises(InvalidCredentials):
        use_cases.login("admin", "wrong")


def test_upload_content_saves_object_item_and_audit_entry():
    content = FakeContent()
    audit = FakeAudit()
    storage = FakeStorage()
    use_cases = ContentUseCases(content, audit, storage)
    owner = User(id=7, username="owner", password_hash="x", role="owner", created_at=datetime.now(timezone.utc))

    item = use_cases.upload(
        owner,
        UploadContentCommand(
            title="Architecture Notes",
            content_type="document",
            description="Sprint document",
            tags="architecture",
            original_filename="notes.txt",
            mime_type="text/plain",
            content=BytesIO(b"hello"),
        ),
    )

    assert item.id == 1
    assert item.owner_id == owner.id
    assert item.stored_filename == "stored-notes.txt"
    assert item.size_bytes == 5
    assert audit.entries[0].action == "content_uploaded"


def test_download_content_requires_owner_item():
    use_cases = ContentUseCases(FakeContent(), FakeAudit(), FakeStorage())
    owner = User(id=7, username="owner", password_hash="x", role="owner", created_at=datetime.now(timezone.utc))

    with pytest.raises(ContentNotFound):
        use_cases.prepare_download(owner, 123)
