from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.blog import BlogPost, BlogStatus
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.email import EmailAttachment, EmailMessage
from app.domain.imports import ExternalAccount, ExternalSource, ImportBatch, ImportJob, ImportJobStatus
from app.domain.media import MediaItem, MediaType
from app.domain.repositories import SearchQuery
from app.infrastructure.db import orm_models


def _user(row: orm_models.User) -> User:
    return User(
        id=row.id,
        username=row.username,
        password_hash=row.password_hash,
        role=row.role,
        created_at=row.created_at,
    )


def _content(row: orm_models.ContentItem) -> ContentItem:
    return ContentItem(
        id=row.id,
        owner_id=row.owner_id,
        title=row.title,
        description=row.description,
        content_type=row.content_type,
        original_filename=row.original_filename,
        stored_filename=row.stored_filename,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        tags=row.tags,
        origin=row.origin,
        external_source_id=row.external_source_id,
        external_account_id=row.external_account_id,
        external_content_id=row.external_content_id,
        external_content_type=row.external_content_type,
        imported_at=row.imported_at,
        import_batch_id=row.import_batch_id,
        source_url=row.source_url,
        source_reference=row.source_reference,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _blog(row: orm_models.BlogPost) -> BlogPost:
    return BlogPost(
        id=row.id,
        owner_id=row.owner_id,
        content_item=_content(row.content_item),
        slug=row.slug,
        body=row.body,
        summary=row.summary,
        status=BlogStatus(row.status),
        tags=row.content_item.tags,
        created_at=row.created_at,
        updated_at=row.updated_at,
        published_at=row.published_at,
    )


def _media(row: orm_models.MediaItem) -> MediaItem:
    return MediaItem(
        id=row.id,
        owner_id=row.owner_id,
        content_item=_content(row.content_item),
        media_type=MediaType(row.media_type),
        original_filename=row.original_filename,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        width=row.width,
        height=row.height,
        duration_seconds=row.duration_seconds,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _email(row: orm_models.EmailMessage) -> EmailMessage:
    return EmailMessage(
        id=row.id,
        owner_id=row.owner_id,
        content_item=_content(row.content_item),
        external_source_id=row.external_source_id,
        external_account_id=row.external_account_id,
        external_message_id=row.external_message_id,
        message_id_header=row.message_id_header,
        thread_id=row.thread_id,
        subject=row.subject,
        sender=row.sender,
        recipients_to=row.recipients_to,
        recipients_cc=row.recipients_cc,
        recipients_bcc=row.recipients_bcc,
        sent_at=row.sent_at,
        received_at=row.received_at,
        folder=row.folder,
        labels=row.labels,
        has_attachments=bool(row.has_attachments),
        text_body=row.text_body,
        html_body=row.html_body,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _email_attachment(row: orm_models.EmailAttachment) -> EmailAttachment:
    return EmailAttachment(
        id=row.id,
        email_id=row.email_id,
        filename=row.filename,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        object_key=row.object_key,
    )


def _audit(row: orm_models.AuditLog) -> AuditEntry:
    return AuditEntry(
        id=row.id,
        user_id=row.user_id,
        action=row.action,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        details=row.details,
        created_at=row.created_at,
    )


def _external_source(row: orm_models.ExternalSource) -> ExternalSource:
    return ExternalSource(
        id=row.id,
        owner_id=row.owner_id,
        name=row.name,
        source_type=row.source_type,
        created_at=row.created_at,
    )


def _external_account(row: orm_models.ExternalAccount) -> ExternalAccount:
    return ExternalAccount(
        id=row.id,
        owner_id=row.owner_id,
        source_id=row.source_id,
        name=row.name,
        external_account_ref=row.external_account_ref,
        created_at=row.created_at,
    )


def _import_job(row: orm_models.ImportJob) -> ImportJob:
    return ImportJob(
        id=row.id,
        owner_id=row.owner_id,
        source_id=row.source_id,
        account_id=row.account_id,
        content_types=tuple(filter(None, row.content_types.split(","))),
        status=ImportJobStatus(row.status),
        imported_count=row.imported_count,
        error_message=row.error_message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _import_batch(row: orm_models.ImportBatch) -> ImportBatch:
    return ImportBatch(
        id=row.id,
        owner_id=row.owner_id,
        job_id=row.job_id,
        source_id=row.source_id,
        account_id=row.account_id,
        imported_count=row.imported_count,
        created_at=row.created_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        row = self.db.query(orm_models.User).filter(orm_models.User.username == username).first()
        return _user(row) if row else None

    def add(self, user: User) -> User:
        row = orm_models.User(username=user.username, password_hash=user.password_hash, role=user.role)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _user(row)


class SqlAlchemyContentRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, item: ContentItem) -> ContentItem:
        row = orm_models.ContentItem(
            owner_id=item.owner_id,
            title=item.title,
            description=item.description,
            content_type=item.content_type,
            original_filename=item.original_filename,
            stored_filename=item.stored_filename,
            mime_type=item.mime_type,
            size_bytes=item.size_bytes,
            tags=item.tags,
            origin=item.origin,
            external_source_id=item.external_source_id,
            external_account_id=item.external_account_id,
            external_content_id=item.external_content_id,
            external_content_type=item.external_content_type,
            imported_at=item.imported_at,
            import_batch_id=item.import_batch_id,
            source_url=item.source_url,
            source_reference=item.source_reference,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _content(row)

    def list_for_owner(self, owner_id: int) -> list[ContentItem]:
        rows = (
            self.db.query(orm_models.ContentItem)
            .filter(orm_models.ContentItem.owner_id == owner_id)
            .order_by(orm_models.ContentItem.created_at.desc())
            .all()
        )
        return [_content(row) for row in rows]

    def search_for_owner(self, owner_id: int, query: str) -> list[ContentItem]:
        return self.search(SearchQuery(owner_id=owner_id, text=query))

    def search(self, query: SearchQuery) -> list[ContentItem]:
        pattern = f"%{query.text}%"
        rows = (
            self.db.query(orm_models.ContentItem)
            .filter(orm_models.ContentItem.owner_id == query.owner_id)
            .filter(
                or_(
                    orm_models.ContentItem.title.ilike(pattern),
                    orm_models.ContentItem.description.ilike(pattern),
                    orm_models.ContentItem.original_filename.ilike(pattern),
                    orm_models.ContentItem.tags.ilike(pattern),
                    orm_models.ContentItem.content_type.ilike(pattern),
                )
            )
            .order_by(orm_models.ContentItem.created_at.desc())
            .all()
        )
        return [_content(row) for row in rows]

    def get_for_owner(self, content_id: int, owner_id: int) -> ContentItem | None:
        row = (
            self.db.query(orm_models.ContentItem)
            .filter(orm_models.ContentItem.id == content_id, orm_models.ContentItem.owner_id == owner_id)
            .first()
        )
        return _content(row) if row else None


class SqlAlchemyBlogPostRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, post: BlogPost) -> BlogPost:
        row = orm_models.BlogPost(
            owner_id=post.owner_id,
            content_item_id=post.content_item.id,
            slug=post.slug,
            body=post.body,
            summary=post.summary,
            status=post.status.value,
            published_at=post.published_at,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _blog(row)

    def update(self, post: BlogPost) -> BlogPost:
        row = self.db.query(orm_models.BlogPost).filter(orm_models.BlogPost.id == post.id).first()
        if row is None:
            raise ValueError("Blog post not found")
        content_row = row.content_item
        content_row.title = post.content_item.title
        content_row.description = post.content_item.description
        content_row.original_filename = post.content_item.original_filename
        content_row.stored_filename = post.content_item.stored_filename
        content_row.size_bytes = post.content_item.size_bytes
        content_row.tags = post.content_item.tags
        content_row.updated_at = orm_models.now_utc()
        row.slug = post.slug
        row.body = post.body
        row.summary = post.summary
        row.status = post.status.value
        row.published_at = post.published_at
        row.updated_at = orm_models.now_utc()
        self.db.commit()
        self.db.refresh(row)
        return _blog(row)

    def get_for_owner(self, post_id: int, owner_id: int) -> BlogPost | None:
        row = (
            self.db.query(orm_models.BlogPost)
            .filter(orm_models.BlogPost.id == post_id, orm_models.BlogPost.owner_id == owner_id)
            .first()
        )
        return _blog(row) if row else None

    def get_by_slug_for_owner(self, slug: str, owner_id: int) -> BlogPost | None:
        row = (
            self.db.query(orm_models.BlogPost)
            .filter(orm_models.BlogPost.slug == slug, orm_models.BlogPost.owner_id == owner_id)
            .first()
        )
        return _blog(row) if row else None

    def list_for_owner(self, owner_id: int) -> list[BlogPost]:
        rows = (
            self.db.query(orm_models.BlogPost)
            .filter(orm_models.BlogPost.owner_id == owner_id)
            .order_by(orm_models.BlogPost.created_at.desc())
            .all()
        )
        return [_blog(row) for row in rows]

    def search_for_owner(self, owner_id: int, query: str) -> list[BlogPost]:
        pattern = f"%{query}%"
        rows = (
            self.db.query(orm_models.BlogPost)
            .join(orm_models.ContentItem)
            .filter(orm_models.BlogPost.owner_id == owner_id)
            .filter(
                or_(
                    orm_models.ContentItem.title.ilike(pattern),
                    orm_models.BlogPost.body.ilike(pattern),
                    orm_models.BlogPost.summary.ilike(pattern),
                    orm_models.ContentItem.tags.ilike(pattern),
                )
            )
            .order_by(orm_models.BlogPost.created_at.desc())
            .all()
        )
        return [_blog(row) for row in rows]


class SqlAlchemyMediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, media: MediaItem) -> MediaItem:
        row = orm_models.MediaItem(
            owner_id=media.owner_id,
            content_item_id=media.content_item.id,
            media_type=media.media_type.value,
            original_filename=media.original_filename,
            mime_type=media.mime_type,
            size_bytes=media.size_bytes,
            width=media.width,
            height=media.height,
            duration_seconds=media.duration_seconds,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _media(row)

    def get_for_owner(self, media_id: int, owner_id: int) -> MediaItem | None:
        row = (
            self.db.query(orm_models.MediaItem)
            .filter(orm_models.MediaItem.id == media_id, orm_models.MediaItem.owner_id == owner_id)
            .first()
        )
        return _media(row) if row else None

    def list_for_owner(self, owner_id: int) -> list[MediaItem]:
        rows = (
            self.db.query(orm_models.MediaItem)
            .filter(orm_models.MediaItem.owner_id == owner_id)
            .order_by(orm_models.MediaItem.created_at.desc())
            .all()
        )
        return [_media(row) for row in rows]

    def search_for_owner(self, owner_id: int, query: str) -> list[MediaItem]:
        pattern = f"%{query}%"
        rows = (
            self.db.query(orm_models.MediaItem)
            .join(orm_models.ContentItem, orm_models.MediaItem.content_item_id == orm_models.ContentItem.id)
            .filter(orm_models.MediaItem.owner_id == owner_id)
            .filter(
                or_(
                    orm_models.ContentItem.title.ilike(pattern),
                    orm_models.ContentItem.description.ilike(pattern),
                    orm_models.MediaItem.original_filename.ilike(pattern),
                    orm_models.ContentItem.tags.ilike(pattern),
                    orm_models.MediaItem.mime_type.ilike(pattern),
                )
            )
            .order_by(orm_models.MediaItem.created_at.desc())
            .all()
        )
        return [_media(row) for row in rows]


class SqlAlchemyEmailRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, message: EmailMessage) -> EmailMessage:
        row = orm_models.EmailMessage(
            owner_id=message.owner_id,
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
            has_attachments=1 if message.has_attachments else 0,
            text_body=message.text_body,
            html_body=message.html_body,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _email(row)

    def get_for_owner(self, email_id: int, owner_id: int) -> EmailMessage | None:
        row = (
            self.db.query(orm_models.EmailMessage)
            .filter(orm_models.EmailMessage.id == email_id, orm_models.EmailMessage.owner_id == owner_id)
            .first()
        )
        return _email(row) if row else None

    def get_by_external_message_id(self, owner_id: int, account_id: int, external_message_id: str) -> EmailMessage | None:
        row = (
            self.db.query(orm_models.EmailMessage)
            .filter(
                orm_models.EmailMessage.owner_id == owner_id,
                orm_models.EmailMessage.external_account_id == account_id,
                orm_models.EmailMessage.external_message_id == external_message_id,
            )
            .first()
        )
        return _email(row) if row else None

    def list_for_owner(self, owner_id: int) -> list[EmailMessage]:
        rows = (
            self.db.query(orm_models.EmailMessage)
            .filter(orm_models.EmailMessage.owner_id == owner_id)
            .order_by(orm_models.EmailMessage.received_at.desc(), orm_models.EmailMessage.created_at.desc())
            .all()
        )
        return [_email(row) for row in rows]

    def search_for_owner(self, owner_id: int, query: str) -> list[EmailMessage]:
        pattern = f"%{query}%"
        rows = (
            self.db.query(orm_models.EmailMessage)
            .filter(orm_models.EmailMessage.owner_id == owner_id)
            .filter(
                or_(
                    orm_models.EmailMessage.subject.ilike(pattern),
                    orm_models.EmailMessage.sender.ilike(pattern),
                    orm_models.EmailMessage.text_body.ilike(pattern),
                    orm_models.EmailMessage.labels.ilike(pattern),
                )
            )
            .order_by(orm_models.EmailMessage.received_at.desc(), orm_models.EmailMessage.created_at.desc())
            .all()
        )
        return [_email(row) for row in rows]

    def add_attachment(self, attachment: EmailAttachment) -> EmailAttachment:
        row = orm_models.EmailAttachment(
            email_id=attachment.email_id,
            filename=attachment.filename,
            mime_type=attachment.mime_type,
            size_bytes=attachment.size_bytes,
            object_key=attachment.object_key,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _email_attachment(row)

    def list_attachments_for_email(self, email_id: int, owner_id: int) -> list[EmailAttachment]:
        if not self.get_for_owner(email_id, owner_id):
            return []
        rows = self.db.query(orm_models.EmailAttachment).filter(orm_models.EmailAttachment.email_id == email_id).all()
        return [_email_attachment(row) for row in rows]

    def get_attachment_for_owner(self, attachment_id: int, owner_id: int) -> EmailAttachment | None:
        row = (
            self.db.query(orm_models.EmailAttachment)
            .join(orm_models.EmailMessage, orm_models.EmailAttachment.email_id == orm_models.EmailMessage.id)
            .filter(orm_models.EmailAttachment.id == attachment_id, orm_models.EmailMessage.owner_id == owner_id)
            .first()
        )
        return _email_attachment(row) if row else None

class SqlAlchemyExternalSourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, source: ExternalSource) -> ExternalSource:
        row = orm_models.ExternalSource(owner_id=source.owner_id, name=source.name, source_type=source.source_type)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _external_source(row)

    def list_for_owner(self, owner_id: int) -> list[ExternalSource]:
        rows = (
            self.db.query(orm_models.ExternalSource)
            .filter(orm_models.ExternalSource.owner_id == owner_id)
            .order_by(orm_models.ExternalSource.created_at.desc())
            .all()
        )
        return [_external_source(row) for row in rows]

    def get_for_owner(self, source_id: int, owner_id: int) -> ExternalSource | None:
        row = (
            self.db.query(orm_models.ExternalSource)
            .filter(orm_models.ExternalSource.id == source_id, orm_models.ExternalSource.owner_id == owner_id)
            .first()
        )
        return _external_source(row) if row else None


class SqlAlchemyExternalAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, account: ExternalAccount) -> ExternalAccount:
        row = orm_models.ExternalAccount(
            owner_id=account.owner_id,
            source_id=account.source_id,
            name=account.name,
            external_account_ref=account.external_account_ref,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _external_account(row)

    def list_for_owner(self, owner_id: int) -> list[ExternalAccount]:
        rows = (
            self.db.query(orm_models.ExternalAccount)
            .filter(orm_models.ExternalAccount.owner_id == owner_id)
            .order_by(orm_models.ExternalAccount.created_at.desc())
            .all()
        )
        return [_external_account(row) for row in rows]

    def get_for_owner(self, account_id: int, owner_id: int) -> ExternalAccount | None:
        row = (
            self.db.query(orm_models.ExternalAccount)
            .filter(orm_models.ExternalAccount.id == account_id, orm_models.ExternalAccount.owner_id == owner_id)
            .first()
        )
        return _external_account(row) if row else None


class SqlAlchemyImportJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, job: ImportJob) -> ImportJob:
        row = orm_models.ImportJob(
            owner_id=job.owner_id,
            source_id=job.source_id,
            account_id=job.account_id,
            content_types=",".join(job.content_types),
            status=job.status.value,
            imported_count=job.imported_count,
            error_message=job.error_message,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _import_job(row)

    def update(self, job: ImportJob) -> ImportJob:
        row = self.db.query(orm_models.ImportJob).filter(orm_models.ImportJob.id == job.id).first()
        if row is None:
            raise ValueError("Import job not found")
        row.status = job.status.value
        row.imported_count = job.imported_count
        row.error_message = job.error_message
        row.updated_at = orm_models.now_utc()
        self.db.commit()
        self.db.refresh(row)
        return _import_job(row)

    def list_for_owner(self, owner_id: int) -> list[ImportJob]:
        rows = (
            self.db.query(orm_models.ImportJob)
            .filter(orm_models.ImportJob.owner_id == owner_id)
            .order_by(orm_models.ImportJob.created_at.desc())
            .all()
        )
        return [_import_job(row) for row in rows]

    def get_for_owner(self, job_id: int, owner_id: int) -> ImportJob | None:
        row = (
            self.db.query(orm_models.ImportJob)
            .filter(orm_models.ImportJob.id == job_id, orm_models.ImportJob.owner_id == owner_id)
            .first()
        )
        return _import_job(row) if row else None


class SqlAlchemyImportBatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, batch: ImportBatch) -> ImportBatch:
        row = orm_models.ImportBatch(
            owner_id=batch.owner_id,
            job_id=batch.job_id,
            source_id=batch.source_id,
            account_id=batch.account_id,
            imported_count=batch.imported_count,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _import_batch(row)

class SqlAlchemyAuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, entry: AuditEntry) -> AuditEntry:
        row = orm_models.AuditLog(
            user_id=entry.user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            details=entry.details,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _audit(row)

    def list_for_user(self, user_id: int, limit: int = 100) -> list[AuditEntry]:
        rows = (
            self.db.query(orm_models.AuditLog)
            .filter(orm_models.AuditLog.user_id == user_id)
            .order_by(orm_models.AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_audit(row) for row in rows]
