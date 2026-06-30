from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from typing import BinaryIO, Callable, Protocol

from app.domain.archive_import import ArchiveFile, ArchiveImportResult, ArchiveImportSet, ArchiveScanSummary, ArchiveStatus, ImportSetSummary
from app.domain.email import EmailPayload
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import ArchiveFileNotFound, ArchiveImportSetNotFound
from app.domain.imports import ExternalAccount, ExternalSource, ImportBatch, ImportJob
from app.domain.repositories import (
    ArchiveFileRepository,
    ArchiveImportSetRepository,
    AuditRepository,
    ContentRepository,
    EmailRepository,
    ExternalAccountRepository,
    ExternalSourceRepository,
    ImportBatchRepository,
    ImportJobRepository,
    ObjectStorage,
)


class ArchiveScanner(Protocol):
    def scan(self, archive_path: Path, archive_file_id: int | None = None) -> ArchiveScanSummary:
        ...


MboxPayloadReader = Callable[[BinaryIO], object]


class ArchiveImportUseCases:
    def __init__(
        self,
        import_sets: ArchiveImportSetRepository,
        archives: ArchiveFileRepository,
        sources: ExternalSourceRepository,
        accounts: ExternalAccountRepository,
        import_jobs: ImportJobRepository,
        batches: ImportBatchRepository,
        content: ContentRepository,
        emails: EmailRepository,
        audits: AuditRepository,
        storage: ObjectStorage,
        scanner: ArchiveScanner,
        mbox_payloads,
    ):
        self.import_sets = import_sets
        self.archives = archives
        self.sources = sources
        self.accounts = accounts
        self.import_jobs = import_jobs
        self.batches = batches
        self.content = content
        self.emails = emails
        self.audits = audits
        self.storage = storage
        self.scanner = scanner
        self.mbox_payloads = mbox_payloads

    def create_import_set(self, user: User, display_name: str, account_label: str, source_type: str, notes: str | None) -> ArchiveImportSet:
        source = self._source(user, source_type)
        account = self._account(user, source, account_label)
        import_set = self.import_sets.add(
            ArchiveImportSet(
                id=None,
                owner_id=user.id,
                external_source_id=source.id,
                external_account_id=account.id,
                display_name=display_name,
                source_type=source_type,
                notes=notes,
            )
        )
        self._audit(user.id, "archive_import_set_created", "archive_import_set", import_set.id, display_name)
        return import_set

    def list_import_sets(self, user: User) -> list[ArchiveImportSet]:
        return self.import_sets.list_for_owner(user.id)

    def get_import_set(self, user: User, import_set_id: int) -> ArchiveImportSet:
        import_set = self.import_sets.get_for_owner(import_set_id, user.id)
        if not import_set:
            raise ArchiveImportSetNotFound()
        return import_set

    def register_archive(self, user: User, import_set_id: int, original_filename: str, data) -> ArchiveFile:
        self.get_import_set(user, import_set_id)
        stored_filename, size = self.storage.save(original_filename, data)
        path = self.storage.path_for(stored_filename)
        digest = self._sha256(path)
        archive = self.archives.add(
            ArchiveFile(
                id=None,
                import_set_id=import_set_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                size_bytes=size,
                sha256_hash=digest,
            )
        )
        self._audit(user.id, "archive_registered", "archive_file", archive.id, original_filename)
        return archive

    def list_archives(self, user: User, import_set_id: int) -> list[ArchiveFile]:
        self.get_import_set(user, import_set_id)
        return self.archives.list_for_import_set(import_set_id)

    def scan_archive(self, user: User, archive_id: int) -> ArchiveScanSummary:
        archive = self._archive_for_user(user, archive_id)
        summary = self.scanner.scan(self.storage.path_for(archive.stored_filename), archive.id)
        self.archives.update(replace(archive, status=ArchiveStatus.SCANNED, error_message=None))
        self._audit(user.id, "archive_scanned", "archive_file", archive.id, archive.original_filename)
        return summary

    def scan_import_set(self, user: User, import_set_id: int) -> ImportSetSummary:
        self.get_import_set(user, import_set_id)
        summaries = [self.scan_archive(user, archive.id) for archive in self.archives.list_for_import_set(import_set_id)]
        return self._combine(import_set_id, summaries)

    def get_summary(self, user: User, import_set_id: int) -> ImportSetSummary:
        self.get_import_set(user, import_set_id)
        summaries = [
            self.scanner.scan(self.storage.path_for(archive.stored_filename), archive.id)
            for archive in self.archives.list_for_import_set(import_set_id)
        ]
        return self._combine(import_set_id, summaries)

    def import_set(self, user: User, import_set_id: int) -> ArchiveImportResult:
        import_set = self.get_import_set(user, import_set_id)
        source = self._source_by_id(user, import_set.external_source_id)
        account = self._account_by_id(user, import_set.external_account_id)
        job = self.import_jobs.add(
            ImportJob(
                id=None,
                owner_id=user.id,
                source_id=source.id,
                account_id=account.id,
                content_types=("archive",),
            )
        )
        batch = self.batches.add(ImportBatch(id=None, owner_id=user.id, job_id=job.id, source_id=source.id, account_id=account.id))
        self._audit(user.id, "archive_import_started", "archive_import_set", import_set.id, import_set.display_name)
        imported_count = 0
        email_count = 0
        for archive in self.archives.list_for_import_set(import_set_id):
            path = self.storage.path_for(archive.stored_filename)
            summary = self.scanner.scan(path, archive.id)
            with ZipFile(path) as zip_file:
                for entry in summary.entries:
                    if entry.content_type == "email" and entry.extension == ".mbox":
                        with zip_file.open(entry.original_path) as stream:
                            for payload in self.mbox_payloads(stream):
                                if self._import_email(user, source, account, batch, payload):
                                    email_count += 1
                        continue
                    if entry.service in {"mail", "calendar", "contacts", "tasks", "maps", "chrome"} and entry.content_type not in {
                        "document",
                        "image",
                        "video",
                        "archive",
                        "spreadsheet",
                        "binary",
                    }:
                        continue
                    with zip_file.open(entry.original_path) as stream:
                        stored_filename, size = self.storage.save(Path(entry.normalised_path).name, stream)
                    item = self.content.add(
                        ContentItem(
                            id=None,
                            owner_id=user.id,
                            title=Path(entry.normalised_path).name,
                            description=None,
                            content_type=entry.content_type,
                            original_filename=Path(entry.normalised_path).name,
                            stored_filename=stored_filename,
                            mime_type=None,
                            size_bytes=size,
                            tags="archive-import",
                            origin="imported",
                            external_source_id=source.id,
                            external_account_id=account.id,
                            external_content_id=f"{archive.id}:{entry.original_path}",
                            external_content_type=entry.content_type,
                            imported_at=datetime.now(timezone.utc),
                            import_batch_id=batch.id,
                            source_reference=entry.original_path,
                            import_set_id=import_set.id,
                            archive_file_id=archive.id,
                            original_archive_filename=archive.original_filename,
                            original_archive_internal_path=entry.original_path,
                            normalised_path=entry.normalised_path,
                        )
                    )
                    imported_count += 1
                    self._audit(user.id, "content_imported", "content_item", item.id, entry.original_path)
            self.archives.update(replace(archive, status=ArchiveStatus.IMPORTED, error_message=None))
        self._audit(user.id, "archive_import_completed", "archive_import_set", import_set.id, str(imported_count + email_count))
        return ArchiveImportResult(import_set_id=import_set_id, imported_count=imported_count, email_count=email_count)

    def _import_email(
        self,
        user: User,
        source: ExternalSource,
        account: ExternalAccount,
        batch: ImportBatch,
        payload: EmailPayload,
    ) -> bool:
        if self.emails.get_by_external_message_id(user.id, account.id, payload.external_message_id):
            return False
        content_item = self.content.add(
            ContentItem(
                id=None,
                owner_id=user.id,
                title=payload.subject,
                description=payload.text_body[:255] if payload.text_body else None,
                content_type="email",
                original_filename=f"{payload.external_message_id}.eml",
                stored_filename=f"email:{batch.id}:{payload.external_message_id}",
                mime_type="message/rfc822",
                size_bytes=len(payload.text_body.encode("utf-8")) + len((payload.html_body or "").encode("utf-8")),
                tags=",".join(payload.labels),
                origin="imported",
                external_source_id=source.id,
                external_account_id=account.id,
                external_content_id=payload.external_message_id,
                external_content_type="email",
                imported_at=datetime.now(timezone.utc),
                import_batch_id=batch.id,
                source_reference=payload.message_id_header,
            )
        )
        from app.domain.email import EmailMessage

        self.emails.add(
            EmailMessage(
                id=None,
                owner_id=user.id,
                content_item=content_item,
                external_source_id=source.id,
                external_account_id=account.id,
                external_message_id=payload.external_message_id,
                message_id_header=payload.message_id_header,
                thread_id=payload.thread_id,
                subject=payload.subject,
                sender=payload.sender,
                recipients_to=",".join(payload.recipients_to),
                recipients_cc=",".join(payload.recipients_cc),
                recipients_bcc=",".join(payload.recipients_bcc),
                sent_at=payload.sent_at,
                received_at=payload.received_at,
                folder=payload.folder,
                labels=",".join(payload.labels),
                has_attachments=False,
                text_body=payload.text_body,
                html_body=payload.html_body,
            )
        )
        return True

    def _archive_for_user(self, user: User, archive_id: int) -> ArchiveFile:
        archive = self.archives.get(archive_id)
        if not archive:
            raise ArchiveFileNotFound()
        self.get_import_set(user, archive.import_set_id)
        return archive

    def _source(self, user: User, source_type: str) -> ExternalSource:
        for source in self.sources.list_for_owner(user.id):
            if source.source_type == source_type and source.name == "Google Takeout":
                return source
        return self.sources.add(ExternalSource(id=None, owner_id=user.id, name="Google Takeout", source_type=source_type))

    def _source_by_id(self, user: User, source_id: int) -> ExternalSource:
        source = self.sources.get_for_owner(source_id, user.id)
        if source is None:
            raise ArchiveImportSetNotFound()
        return source

    def _account(self, user: User, source: ExternalSource, account_label: str) -> ExternalAccount:
        for account in self.accounts.list_for_owner(user.id):
            if account.source_id == source.id and account.external_account_ref == account_label:
                return account
        return self.accounts.add(
            ExternalAccount(id=None, owner_id=user.id, source_id=source.id, name=account_label, external_account_ref=account_label)
        )

    def _account_by_id(self, user: User, account_id: int) -> ExternalAccount:
        account = self.accounts.get_for_owner(account_id, user.id)
        if account is None:
            raise ArchiveImportSetNotFound()
        return account

    def _combine(self, import_set_id: int, summaries: list[ArchiveScanSummary]) -> ImportSetSummary:
        service: dict[str, int] = {}
        content_type: dict[str, int] = {}
        extension: dict[str, int] = {}
        entries = 0
        for summary in summaries:
            entries += len(summary.entries)
            self._merge(service, summary.counts_by_service)
            self._merge(content_type, summary.counts_by_content_type)
            self._merge(extension, summary.counts_by_extension)
        return ImportSetSummary(import_set_id, len(summaries), entries, service, content_type, extension)

    def _merge(self, target: dict[str, int], source: dict[str, int]) -> None:
        for key, value in source.items():
            target[key] = target.get(key, 0) + value

    def _sha256(self, path: Path) -> str:
        digest = sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

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
