from pathlib import Path
from dataclasses import dataclass
from typing import BinaryIO, Protocol

from .blog import BlogPost
from .entities import AuditEntry, ContentItem, User
from .imports import ExternalAccount, ExternalSource, ImportBatch, ImportJob


@dataclass(frozen=True)
class SearchQuery:
    owner_id: int
    text: str = ""
    content_types: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    collection_ids: tuple[int, ...] = ()


class UserRepository(Protocol):
    def get_by_username(self, username: str) -> User | None:
        ...

    def add(self, user: User) -> User:
        ...


class ContentRepository(Protocol):
    def add(self, item: ContentItem) -> ContentItem:
        ...

    def list_for_owner(self, owner_id: int) -> list[ContentItem]:
        ...

    def search_for_owner(self, owner_id: int, query: str) -> list[ContentItem]:
        ...

    def get_for_owner(self, content_id: int, owner_id: int) -> ContentItem | None:
        ...


class ContentSearch(Protocol):
    def search(self, query: SearchQuery) -> list[ContentItem]:
        ...


class BlogPostRepository(Protocol):
    def add(self, post: BlogPost) -> BlogPost:
        ...

    def update(self, post: BlogPost) -> BlogPost:
        ...

    def get_for_owner(self, post_id: int, owner_id: int) -> BlogPost | None:
        ...

    def get_by_slug_for_owner(self, slug: str, owner_id: int) -> BlogPost | None:
        ...

    def list_for_owner(self, owner_id: int) -> list[BlogPost]:
        ...

    def search_for_owner(self, owner_id: int, query: str) -> list[BlogPost]:
        ...


class ExternalSourceRepository(Protocol):
    def add(self, source: ExternalSource) -> ExternalSource:
        ...

    def list_for_owner(self, owner_id: int) -> list[ExternalSource]:
        ...

    def get_for_owner(self, source_id: int, owner_id: int) -> ExternalSource | None:
        ...


class ExternalAccountRepository(Protocol):
    def add(self, account: ExternalAccount) -> ExternalAccount:
        ...

    def list_for_owner(self, owner_id: int) -> list[ExternalAccount]:
        ...

    def get_for_owner(self, account_id: int, owner_id: int) -> ExternalAccount | None:
        ...


class ImportJobRepository(Protocol):
    def add(self, job: ImportJob) -> ImportJob:
        ...

    def update(self, job: ImportJob) -> ImportJob:
        ...

    def list_for_owner(self, owner_id: int) -> list[ImportJob]:
        ...

    def get_for_owner(self, job_id: int, owner_id: int) -> ImportJob | None:
        ...


class ImportBatchRepository(Protocol):
    def add(self, batch: ImportBatch) -> ImportBatch:
        ...


class AuditRepository(Protocol):
    def add(self, entry: AuditEntry) -> AuditEntry:
        ...

    def list_for_user(self, user_id: int, limit: int = 100) -> list[AuditEntry]:
        ...


class ObjectStorage(Protocol):
    def save(self, original_filename: str, content: BinaryIO) -> tuple[str, int]:
        ...

    def path_for(self, stored_filename: str) -> Path:
        ...

    def exists(self, stored_filename: str) -> bool:
        ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        ...

    def verify(self, password: str, password_hash: str) -> bool:
        ...


class TokenService(Protocol):
    def create(self, username: str) -> str:
        ...

    def decode_username(self, token: str) -> str | None:
        ...
