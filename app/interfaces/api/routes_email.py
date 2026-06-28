from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.application.email_use_cases import EmailUseCases
from app.domain.email import EmailAttachment, EmailMessage
from app.domain.entities import User
from app.domain.errors import EmailAttachmentNotFound, EmailMessageNotFound, InvalidEmailPayload, StoredObjectNotFound
from app.domain.imports import ExternalAccount, ExternalSource, ImportBatch
from app.infrastructure.imports.fake_email import FakeEmailImportAdapter
from app.interfaces.api.dependencies import current_user, get_email_use_cases, get_fake_email_adapter
from app.interfaces.api.schemas import EmailAttachmentOut, EmailMessageOut

router = APIRouter(prefix="/email")


def _message_out(message: EmailMessage) -> EmailMessageOut:
    return EmailMessageOut(
        id=message.id,
        content_item_id=message.content_item.id,
        external_source_id=message.external_source_id,
        external_account_id=message.external_account_id,
        external_message_id=message.external_message_id,
        message_id_header=message.message_id_header,
        thread_id=message.thread_id,
        subject=message.subject,
        sender=message.sender,
        recipients_to=message.recipients_to,
        recipients_cc=message.recipients_cc,
        recipients_bcc=message.recipients_bcc,
        sent_at=message.sent_at,
        received_at=message.received_at,
        folder=message.folder,
        labels=message.labels,
        has_attachments=message.has_attachments,
        text_body=message.text_body,
        html_body=message.html_body,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


def _attachment_out(attachment: EmailAttachment) -> EmailAttachmentOut:
    return EmailAttachmentOut(
        id=attachment.id,
        email_id=attachment.email_id,
        filename=attachment.filename,
        mime_type=attachment.mime_type,
        size_bytes=attachment.size_bytes,
    )


@router.post("/import/fake", response_model=EmailMessageOut)
def import_fake_email(
    malformed: bool = False,
    emails: EmailUseCases = Depends(get_email_use_cases),
    adapter: FakeEmailImportAdapter = Depends(get_fake_email_adapter),
    user: User = Depends(current_user),
) -> EmailMessageOut:
    source = ExternalSource(id=1, owner_id=user.id, name="Fake Email", source_type="fake_email")
    account = ExternalAccount(id=1, owner_id=user.id, source_id=source.id, name="Fake Account", external_account_ref="fake")
    batch = ImportBatch(id=1, owner_id=user.id, job_id=1, source_id=source.id, account_id=account.id)
    try:
        return _message_out(emails.import_email(user, source, account, batch, adapter.import_message(malformed)))
    except InvalidEmailPayload:
        raise HTTPException(status_code=400, detail="Malformed email payload")


@router.get("/messages", response_model=list[EmailMessageOut])
def list_messages(
    q: str = "",
    emails: EmailUseCases = Depends(get_email_use_cases),
    user: User = Depends(current_user),
) -> list[EmailMessageOut]:
    messages = emails.search_emails(user, q) if q else emails.list_emails(user)
    return [_message_out(message) for message in messages]


@router.get("/messages/{email_id}", response_model=EmailMessageOut)
def get_message(
    email_id: int,
    emails: EmailUseCases = Depends(get_email_use_cases),
    user: User = Depends(current_user),
) -> EmailMessageOut:
    try:
        return _message_out(emails.get_email(user, email_id))
    except EmailMessageNotFound:
        raise HTTPException(status_code=404, detail="Email message not found")


@router.get("/messages/{email_id}/attachments", response_model=list[EmailAttachmentOut])
def list_attachments(
    email_id: int,
    emails: EmailUseCases = Depends(get_email_use_cases),
    user: User = Depends(current_user),
) -> list[EmailAttachmentOut]:
    try:
        return [_attachment_out(attachment) for attachment in emails.list_attachments(user, email_id)]
    except EmailMessageNotFound:
        raise HTTPException(status_code=404, detail="Email message not found")


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    emails: EmailUseCases = Depends(get_email_use_cases),
    user: User = Depends(current_user),
) -> FileResponse:
    try:
        attachment, download = emails.prepare_attachment_download(user, attachment_id)
    except EmailAttachmentNotFound:
        raise HTTPException(status_code=404, detail="Email attachment not found")
    except StoredObjectNotFound:
        raise HTTPException(status_code=404, detail="Stored object not found")
    return FileResponse(download.path, media_type=attachment.mime_type, filename=attachment.filename)
