from typing import Protocol

from app.domain.imports import ExternalAccount, ExternalSource, ImportedContent, ImportJob


class ImportAdapter(Protocol):
    def list_available_content_types(self) -> tuple[str, ...]:
        ...

    def authenticate(self, account: ExternalAccount) -> bool:
        ...

    def test_connection(self, account: ExternalAccount) -> bool:
        ...

    def import_content(self, source: ExternalSource, account: ExternalAccount, job: ImportJob) -> list[ImportedContent]:
        ...
