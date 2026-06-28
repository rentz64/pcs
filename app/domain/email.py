from dataclasses import dataclass
from datetime import datetime

from app.domain.entities import ContentItem


@dataclass(frozen=True)
class EmailPayload:
    external_message_id: str
    message_id_header: str | None
    thread_id: str | None
    subject: str
    sender: str
    recipients_to: tuple[str, ...]
    recipients_cc: tuple[str, ...]
    recipients_bcc: tuple[str, ...]
    sent_at: datetime | None
    received_at: datetime | None
    folder: str
    labels: tuple[str, ...]
    text_body: str
    html_body: str | None = None
    attachments: tuple[tuple[str, str, bytes], ...] = ()


@dataclass(frozen=True)
class EmailMessage:
    id: int | None
    owner_id: int
    content_item: ContentItem
    external_source_id: int
    external_account_id: int
    external_message_id: str
    message_id_header: str | None
    thread_id: str | None
    subject: str
    sender: str
    recipients_to: str
    recipients_cc: str
    recipients_bcc: str
    sent_at: datetime | None
    received_at: datetime | None
    folder: str
    labels: str
    has_attachments: bool
    text_body: str
    html_body: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class EmailAttachment:
    id: int | None
    email_id: int
    filename: str
    mime_type: str
    size_bytes: int
    object_key: str
