from __future__ import annotations

from dataclasses import replace

import pytest

from app.application.import_use_cases import ImportUseCases
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import ExternalAccountNotFound, ExternalSourceNotFound
from app.domain.imports import (
    ExternalAccount,
    ExternalSource,
    ImportedContent,
    ImportJob,
    ImportJobStatus,
)
from tests.test_use_cases import FakeAudit, FakeContent


class FakeSources:
    def __init__(self):
        self.sources: list[ExternalSource] = []

    def add(self, source: ExternalSource) -> ExternalSource:
        saved = replace(source, id=len(self.sources) + 1)
        self.sources.append(saved)
        return saved

    def list_for_owner(self, owner_id: int) -> list[ExternalSource]:
        return [source for source in self.sources if source.owner_id == owner_id]

    def get_for_owner(self, source_id: int, owner_id: int) -> ExternalSource | None:
        return next((source for source in self.sources if source.id == source_id and source.owner_id == owner_id), None)


class FakeAccounts:
    def __init__(self):
        self.accounts: list[ExternalAccount] = []

    def add(self, account: ExternalAccount) -> ExternalAccount:
        saved = replace(account, id=len(self.accounts) + 1)
        self.accounts.append(saved)
        return saved

    def list_for_owner(self, owner_id: int) -> list[ExternalAccount]:
        return [account for account in self.accounts if account.owner_id == owner_id]

    def get_for_owner(self, account_id: int, owner_id: int) -> ExternalAccount | None:
        return next((account for account in self.accounts if account.id == account_id and account.owner_id == owner_id), None)


class FakeJobs:
    def __init__(self):
        self.jobs: list[ImportJob] = []

    def add(self, job: ImportJob) -> ImportJob:
        saved = replace(job, id=len(self.jobs) + 1)
        self.jobs.append(saved)
        return saved

    def update(self, job: ImportJob) -> ImportJob:
        for index, existing in enumerate(self.jobs):
            if existing.id == job.id:
                self.jobs[index] = job
                return job
        raise AssertionError("job not found")

    def list_for_owner(self, owner_id: int) -> list[ImportJob]:
        return [job for job in self.jobs if job.owner_id == owner_id]

    def get_for_owner(self, job_id: int, owner_id: int) -> ImportJob | None:
        return next((job for job in self.jobs if job.id == job_id and job.owner_id == owner_id), None)


class FakeBatches:
    def __init__(self):
        self.batches = []

    def add(self, batch):
        saved = replace(batch, id=len(self.batches) + 1)
        self.batches.append(saved)
        return saved


class DummyAdapter:
    def list_available_content_types(self) -> tuple[str, ...]:
        return ("document", "note")

    def authenticate(self, account: ExternalAccount) -> bool:
        return True

    def test_connection(self, account: ExternalAccount) -> bool:
        return True

    def import_content(self, source: ExternalSource, account: ExternalAccount, job: ImportJob) -> list[ImportedContent]:
        return [
            ImportedContent(
                external_content_id="ext-1",
                external_content_type="note",
                title="Imported Note",
                body="Imported body",
                summary="Imported summary",
                tags="imported,note",
                source_url="local://ext-1",
            )
        ]


def owner(user_id: int = 7) -> User:
    return User(id=user_id, username=f"user-{user_id}", password_hash="x", role="owner")


def make_use_cases(adapter=None):
    content = FakeContent()
    audit = FakeAudit()
    use_cases = ImportUseCases(
        FakeSources(),
        FakeAccounts(),
        FakeJobs(),
        FakeBatches(),
        content,
        audit,
        adapters={"local": adapter or DummyAdapter()},
    )
    return use_cases, content, audit


def test_register_source_account_and_list_content_types():
    use_cases, _, audit = make_use_cases()
    user = owner()

    source = use_cases.register_source(user, "Local Files", "local")
    account = use_cases.register_account(user, source.id, "Local Account", "local-test")

    assert source.source_type == "local"
    assert account.external_account_ref == "local-test"
    assert use_cases.list_supported_content_types(user, source.id) == ("document", "note")
    assert [entry.action for entry in audit.entries] == [
        "external_source_registered",
        "external_account_registered",
    ]


def test_execute_import_job_records_provenance_and_audit():
    use_cases, content, audit = make_use_cases()
    user = owner()
    source = use_cases.register_source(user, "Local Files", "local")
    account = use_cases.register_account(user, source.id, "Local Account", "local-test")
    job = use_cases.create_import_job(user, source.id, account.id, ("note",))

    executed = use_cases.execute_import_job(user, job.id)

    assert executed.status == ImportJobStatus.COMPLETED
    imported = content.items[0]
    assert imported.origin == "imported"
    assert imported.external_source_id == source.id
    assert imported.external_account_id == account.id
    assert imported.external_content_id == "ext-1"
    assert imported.external_content_type == "note"
    assert imported.import_batch_id is not None
    assert imported.imported_at is not None
    assert imported.source_url == "local://ext-1"
    assert "content_imported" in [entry.action for entry in audit.entries]


def test_import_jobs_are_owner_scoped_and_validate_source_account():
    use_cases, _, _ = make_use_cases()
    source = use_cases.register_source(owner(1), "Local Files", "local")
    account = use_cases.register_account(owner(1), source.id, "Local Account", "local-test")

    with pytest.raises(ExternalSourceNotFound):
        use_cases.create_import_job(owner(2), source.id, account.id, ("note",))

    with pytest.raises(ExternalAccountNotFound):
        use_cases.create_import_job(owner(1), source.id, 999, ("note",))

