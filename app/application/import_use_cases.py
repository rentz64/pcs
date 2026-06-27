from dataclasses import replace
from datetime import datetime, timezone

from app.application.dto import CreateImportJobCommand, RegisterExternalAccountCommand, RegisterExternalSourceCommand
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import ExternalAccountNotFound, ExternalSourceNotFound, ImportAdapterNotFound, ImportJobNotFound
from app.domain.import_adapters import ImportAdapter
from app.domain.imports import ExternalAccount, ExternalSource, ImportBatch, ImportJob, ImportJobStatus
from app.domain.repositories import (
    AuditRepository,
    ContentRepository,
    ExternalAccountRepository,
    ExternalSourceRepository,
    ImportBatchRepository,
    ImportJobRepository,
)


class ImportUseCases:
    def __init__(
        self,
        sources: ExternalSourceRepository,
        accounts: ExternalAccountRepository,
        jobs: ImportJobRepository,
        batches: ImportBatchRepository,
        content: ContentRepository,
        audits: AuditRepository,
        adapters: dict[str, ImportAdapter],
    ):
        self.sources = sources
        self.accounts = accounts
        self.jobs = jobs
        self.batches = batches
        self.content = content
        self.audits = audits
        self.adapters = adapters

    def register_source(self, user: User, name: str, source_type: str) -> ExternalSource:
        source = self.sources.add(ExternalSource(id=None, owner_id=user.id, name=name, source_type=source_type))
        self._audit(user.id, "external_source_registered", "external_source", source.id, source.name)
        return source

    def register_source_command(self, user: User, command: RegisterExternalSourceCommand) -> ExternalSource:
        return self.register_source(user, command.name, command.source_type)

    def list_sources(self, user: User) -> list[ExternalSource]:
        return self.sources.list_for_owner(user.id)

    def register_account(self, user: User, source_id: int, name: str, external_account_ref: str) -> ExternalAccount:
        source = self._source(user, source_id)
        account = self.accounts.add(
            ExternalAccount(
                id=None,
                owner_id=user.id,
                source_id=source.id,
                name=name,
                external_account_ref=external_account_ref,
            )
        )
        self._audit(user.id, "external_account_registered", "external_account", account.id, account.name)
        return account

    def register_account_command(self, user: User, command: RegisterExternalAccountCommand) -> ExternalAccount:
        return self.register_account(user, command.source_id, command.name, command.external_account_ref)

    def list_accounts(self, user: User) -> list[ExternalAccount]:
        return self.accounts.list_for_owner(user.id)

    def list_supported_content_types(self, user: User, source_id: int) -> tuple[str, ...]:
        source = self._source(user, source_id)
        return self._adapter(source).list_available_content_types()

    def create_import_job(self, user: User, source_id: int, account_id: int, content_types: tuple[str, ...]) -> ImportJob:
        source = self._source(user, source_id)
        account = self._account(user, account_id)
        if account.source_id != source.id:
            raise ExternalAccountNotFound()
        job = self.jobs.add(
            ImportJob(
                id=None,
                owner_id=user.id,
                source_id=source.id,
                account_id=account.id,
                content_types=content_types,
            )
        )
        self._audit(user.id, "import_job_created", "import_job", job.id, None)
        return job

    def create_import_job_command(self, user: User, command: CreateImportJobCommand) -> ImportJob:
        return self.create_import_job(user, command.source_id, command.account_id, command.content_types)

    def execute_import_job(self, user: User, job_id: int) -> ImportJob:
        job = self._job(user, job_id)
        source = self._source(user, job.source_id)
        account = self._account(user, job.account_id)
        adapter = self._adapter(source)
        running = self.jobs.update(replace(job, status=ImportJobStatus.RUNNING, updated_at=datetime.now(timezone.utc)))
        batch = self.batches.add(
            ImportBatch(id=None, owner_id=user.id, job_id=running.id, source_id=source.id, account_id=account.id)
        )
        imported_count = 0
        for imported in adapter.import_content(source, account, running):
            imported_at = datetime.now(timezone.utc)
            item = self.content.add(
                ContentItem(
                    id=None,
                    owner_id=user.id,
                    title=imported.title,
                    description=imported.summary,
                    content_type=imported.external_content_type,
                    original_filename=f"{imported.external_content_id}.import",
                    stored_filename=f"import:{batch.id}:{imported.external_content_id}",
                    mime_type=None,
                    size_bytes=len(imported.body.encode("utf-8")),
                    tags=imported.tags,
                    origin="imported",
                    external_source_id=source.id,
                    external_account_id=account.id,
                    external_content_id=imported.external_content_id,
                    external_content_type=imported.external_content_type,
                    imported_at=imported_at,
                    import_batch_id=batch.id,
                    source_url=imported.source_url,
                    source_reference=imported.source_reference,
                )
            )
            imported_count += 1
            self._audit(user.id, "content_imported", "content_item", item.id, item.external_content_id)
        completed = self.jobs.update(
            replace(running, status=ImportJobStatus.COMPLETED, imported_count=imported_count, updated_at=datetime.now(timezone.utc))
        )
        self._audit(user.id, "import_job_executed", "import_job", completed.id, str(imported_count))
        return completed

    def list_import_jobs(self, user: User) -> list[ImportJob]:
        return self.jobs.list_for_owner(user.id)

    def get_import_job_status(self, user: User, job_id: int) -> ImportJob:
        return self._job(user, job_id)

    def _source(self, user: User, source_id: int) -> ExternalSource:
        source = self.sources.get_for_owner(source_id, user.id)
        if not source:
            raise ExternalSourceNotFound()
        return source

    def _account(self, user: User, account_id: int) -> ExternalAccount:
        account = self.accounts.get_for_owner(account_id, user.id)
        if not account:
            raise ExternalAccountNotFound()
        return account

    def _job(self, user: User, job_id: int) -> ImportJob:
        job = self.jobs.get_for_owner(job_id, user.id)
        if not job:
            raise ImportJobNotFound()
        return job

    def _adapter(self, source: ExternalSource) -> ImportAdapter:
        adapter = self.adapters.get(source.source_type)
        if not adapter:
            raise ImportAdapterNotFound()
        return adapter

    def _audit(self, user_id: int | None, action: str, entity_type: str, entity_id: int | None, details: str | None) -> None:
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                details=details,
            )
        )
