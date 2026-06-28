from datetime import datetime, timezone
from io import BytesIO

from app.application.dto import DownloadContent
from app.domain.email import EmailAttachment, EmailMessage, EmailPayload
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import EmailAttachmentNotFound, EmailMessageNotFound, InvalidEmailPayload, StoredObjectNotFound
from app.domain.imports import ExternalAccount, ExternalSource, ImportBatch
from app.domain.repositories import AuditRepository, ContentRepository, EmailRepository, ObjectStorage


class EmailUseCases:
    def __init__(
        self,
        emails: EmailRepository,
        content: ContentRepository,
        audits: AuditRepository,
        storage: ObjectStorage,
    ):
        self.emails = emails
        self.content = content
        self.audits = audits
        self.storage = storage

    def import_email(
        self,
        user: User,
        source: ExternalSource,
        account: ExternalAccount,
        batch: ImportBatch,
        payload: EmailPayload,
    ) -> EmailMessage:
        self._validate_payload(payload)
        existing = self.emails.get_by_external_message_id(user.id, account.id, payload.external_message_id)
        if existing:
            return existing
        imported_at = datetime.now(timezone.utc)
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
                imported_at=imported_at,
                import_batch_id=batch.id,
                source_reference=payload.message_id_header,
            )
        )
        message = self.emails.add(
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
                has_attachments=bool(payload.attachments),
                text_body=payload.text_body,
                html_body=payload.html_body,
            )
        )
        for filename, mime_type, data in payload.attachments:
            object_key, size = self.storage.save(filename, BytesIO(data))
            self.emails.add_attachment(
                EmailAttachment(
                    id=None,
                    email_id=message.id,
                    filename=filename,
                    mime_type=mime_type,
                    size_bytes=size,
                    object_key=object_key,
                )
            )
        self._audit(user.id, "email_imported", message.id, message.subject)
        return message

    def list_emails(self, user: User) -> list[EmailMessage]:
        return self.emails.list_for_owner(user.id)

    def get_email(self, user: User, email_id: int) -> EmailMessage:
        message = self.emails.get_for_owner(email_id, user.id)
        if not message:
            raise EmailMessageNotFound()
        self._audit(user.id, "email_viewed", message.id, message.subject)
        return message

    def search_emails(self, user: User, query: str) -> list[EmailMessage]:
        return self.emails.search_for_owner(user.id, query)

    def list_attachments(self, user: User, email_id: int) -> list[EmailAttachment]:
        if not self.emails.get_for_owner(email_id, user.id):
            raise EmailMessageNotFound()
        return self.emails.list_attachments_for_email(email_id, user.id)

    def prepare_attachment_download(self, user: User, attachment_id: int) -> tuple[EmailAttachment, DownloadContent]:
        attachment = self.emails.get_attachment_for_owner(attachment_id, user.id)
        if not attachment:
            raise EmailAttachmentNotFound()
        if not self.storage.exists(attachment.object_key):
            raise StoredObjectNotFound()
        self._audit(user.id, "email_attachment_downloaded", attachment.id, attachment.filename)
        item = ContentItem(
            id=None,
            owner_id=user.id,
            title=attachment.filename,
            description=None,
            content_type="email_attachment",
            original_filename=attachment.filename,
            stored_filename=attachment.object_key,
            mime_type=attachment.mime_type,
            size_bytes=attachment.size_bytes,
            tags="",
        )
        return attachment, DownloadContent(item=item, path=self.storage.path_for(attachment.object_key))

    def _validate_payload(self, payload: EmailPayload) -> None:
        if not payload.external_message_id.strip() or not payload.subject.strip() or not payload.sender.strip():
            raise InvalidEmailPayload()

    def _audit(self, user_id: int | None, action: str, entity_id: int | None, details: str | None) -> None:
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user_id,
                action=action,
                entity_type="email_message",
                entity_id=str(entity_id) if entity_id is not None else None,
                details=details,
            )
        )
