from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ContentOut(BaseModel):
    id: int
    title: str
    description: str | None
    content_type: str
    original_filename: str
    mime_type: str | None
    size_bytes: int
    tags: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BlogPostCreate(BaseModel):
    title: str
    slug: str
    body: str = ""
    summary: str | None = None
    tags: str = ""
    collections: tuple[int, ...] = ()


class BlogPostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    body: str | None = None
    summary: str | None = None
    tags: str | None = None
    collections: tuple[int, ...] | None = None


class BlogPostOut(BaseModel):
    id: int
    content_item_id: int
    title: str
    slug: str
    body: str
    summary: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    tags: str
    collections: tuple[int, ...] = ()


class ExternalSourceCreate(BaseModel):
    name: str
    source_type: str


class ExternalSourceOut(BaseModel):
    id: int
    name: str
    source_type: str
    created_at: datetime


class ExternalAccountCreate(BaseModel):
    source_id: int
    name: str
    external_account_ref: str


class ExternalAccountOut(BaseModel):
    id: int
    source_id: int
    name: str
    external_account_ref: str
    created_at: datetime


class ContentTypesOut(BaseModel):
    content_types: list[str]


class ImportJobCreate(BaseModel):
    source_id: int
    account_id: int
    content_types: list[str] = []


class ImportJobOut(BaseModel):
    id: int
    source_id: int
    account_id: int
    content_types: list[str]
    status: str
    imported_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class MediaOut(BaseModel):
    id: int
    content_item_id: int
    title: str
    description: str | None
    media_type: str
    original_filename: str
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None
    duration_seconds: float | None
    tags: str
    created_at: datetime
    updated_at: datetime


class EmailMessageOut(BaseModel):
    id: int
    content_item_id: int
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
    created_at: datetime
    updated_at: datetime


class EmailAttachmentOut(BaseModel):
    id: int
    email_id: int
    filename: str
    mime_type: str
    size_bytes: int
