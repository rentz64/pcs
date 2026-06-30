import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.archive_import import ArchiveFile, ArchiveImportSet, ArchiveStatus
from app.domain.blog import BlogPost, BlogStatus
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.email import EmailAttachment, EmailMessage
from app.domain.imports import ExternalAccount, ExternalSource, ImportBatch, ImportJob, ImportJobStatus
from app.domain.jobs import Job, JobStatus
from app.domain.media import MediaItem, MediaType
from app.domain.repositories import SearchQuery
from app.domain.travel import ItineraryStatus, TravelItinerary, TravelPlace, TravelRoute
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
        import_set_id=row.import_set_id,
        archive_file_id=row.archive_file_id,
        original_archive_filename=row.original_archive_filename,
        original_archive_internal_path=row.original_archive_internal_path,
        normalised_path=row.normalised_path,
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


def _travel_place(row: orm_models.TravelPlace) -> TravelPlace:
    return TravelPlace(
        id=row.id,
        itinerary_id=row.itinerary_id,
        name=row.name,
        description=row.description,
        address=row.address,
        latitude=row.latitude,
        longitude=row.longitude,
        visit_start=row.visit_start,
        visit_end=row.visit_end,
        sequence_order=row.sequence_order,
    )


def _travel_route(row: orm_models.TravelRoute) -> TravelRoute:
    return TravelRoute(
        id=row.id,
        itinerary_id=row.itinerary_id,
        origin_place_id=row.origin_place_id,
        destination_place_id=row.destination_place_id,
        transport_mode=row.transport_mode,
        distance_meters=row.distance_meters,
        duration_seconds=row.duration_seconds,
        sequence_order=row.sequence_order,
    )


def _travel_itinerary(row: orm_models.TravelItinerary) -> TravelItinerary:
    return TravelItinerary(
        id=row.id,
        owner_id=row.owner_id,
        content_item=_content(row.content_item),
        title=row.title,
        description=row.description,
        start_date=row.start_date,
        end_date=row.end_date,
        status=ItineraryStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
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


def _job(row: orm_models.Job) -> Job:
    payload_json = json.loads(row.payload_json or "{}")
    result_json = json.loads(row.result_json) if row.result_json else None
    return Job(
        id=row.id,
        name=row.name,
        status=JobStatus(row.status),
        task_type=row.task_type,
        payload_json=payload_json,
        result_json=result_json,
        error_message=row.error_message,
        attempts=row.attempts,
        max_attempts=row.max_attempts,
        queued_at=row.queued_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        payload={str(key): str(value) for key, value in payload_json.items()},
        result=row.result,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _archive_import_set(row: orm_models.ArchiveImportSet) -> ArchiveImportSet:
    return ArchiveImportSet(
        id=row.id,
        owner_id=row.owner_id,
        external_source_id=row.external_source_id,
        external_account_id=row.external_account_id,
        display_name=row.display_name,
        source_type=row.source_type,
        notes=row.notes,
        created_at=row.created_at,
    )


def _archive_file(row: orm_models.ArchiveFile) -> ArchiveFile:
    return ArchiveFile(
        id=row.id,
        import_set_id=row.import_set_id,
        original_filename=row.original_filename,
        stored_filename=row.stored_filename,
        size_bytes=row.size_bytes,
        sha256_hash=row.sha256_hash,
        status=ArchiveStatus(row.status),
        error_message=row.error_message,
        registered_at=row.registered_at,
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
            import_set_id=item.import_set_id,
            archive_file_id=item.archive_file_id,
            original_archive_filename=item.original_archive_filename,
            original_archive_internal_path=item.original_archive_internal_path,
            normalised_path=item.normalised_path,
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


class SqlAlchemyTravelRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_itinerary(self, itinerary: TravelItinerary) -> TravelItinerary:
        row = orm_models.TravelItinerary(
            owner_id=itinerary.owner_id,
            content_item_id=itinerary.content_item.id,
            title=itinerary.title,
            description=itinerary.description,
            start_date=itinerary.start_date,
            end_date=itinerary.end_date,
            status=itinerary.status.value,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _travel_itinerary(row)

    def update_itinerary(self, itinerary: TravelItinerary) -> TravelItinerary:
        row = self.db.query(orm_models.TravelItinerary).filter(orm_models.TravelItinerary.id == itinerary.id).first()
        if row is None:
            raise ValueError("Travel itinerary not found")
        row.title = itinerary.title
        row.description = itinerary.description
        row.start_date = itinerary.start_date
        row.end_date = itinerary.end_date
        row.status = itinerary.status.value
        row.updated_at = orm_models.now_utc()
        row.content_item.title = itinerary.title
        row.content_item.description = itinerary.description
        row.content_item.updated_at = orm_models.now_utc()
        self.db.commit()
        self.db.refresh(row)
        return _travel_itinerary(row)

    def get_itinerary_for_owner(self, itinerary_id: int, owner_id: int) -> TravelItinerary | None:
        row = (
            self.db.query(orm_models.TravelItinerary)
            .filter(orm_models.TravelItinerary.id == itinerary_id, orm_models.TravelItinerary.owner_id == owner_id)
            .first()
        )
        return _travel_itinerary(row) if row else None

    def list_itineraries_for_owner(self, owner_id: int) -> list[TravelItinerary]:
        rows = (
            self.db.query(orm_models.TravelItinerary)
            .filter(orm_models.TravelItinerary.owner_id == owner_id)
            .order_by(orm_models.TravelItinerary.created_at.desc())
            .all()
        )
        return [_travel_itinerary(row) for row in rows]

    def search_itineraries_for_owner(self, owner_id: int, query: str) -> list[TravelItinerary]:
        pattern = f"%{query}%"
        rows = (
            self.db.query(orm_models.TravelItinerary)
            .filter(orm_models.TravelItinerary.owner_id == owner_id)
            .filter(
                or_(
                    orm_models.TravelItinerary.title.ilike(pattern),
                    orm_models.TravelItinerary.description.ilike(pattern),
                )
            )
            .order_by(orm_models.TravelItinerary.created_at.desc())
            .all()
        )
        return [_travel_itinerary(row) for row in rows]

    def add_place(self, place: TravelPlace) -> TravelPlace:
        row = orm_models.TravelPlace(
            itinerary_id=place.itinerary_id,
            name=place.name,
            description=place.description,
            address=place.address,
            latitude=place.latitude,
            longitude=place.longitude,
            visit_start=place.visit_start,
            visit_end=place.visit_end,
            sequence_order=place.sequence_order,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _travel_place(row)

    def update_place(self, place: TravelPlace) -> TravelPlace:
        row = self.db.query(orm_models.TravelPlace).filter(orm_models.TravelPlace.id == place.id).first()
        if row is None:
            raise ValueError("Travel place not found")
        row.name = place.name
        row.description = place.description
        row.address = place.address
        row.latitude = place.latitude
        row.longitude = place.longitude
        row.visit_start = place.visit_start
        row.visit_end = place.visit_end
        row.sequence_order = place.sequence_order
        self.db.commit()
        self.db.refresh(row)
        return _travel_place(row)

    def remove_place(self, place_id: int) -> None:
        row = self.db.query(orm_models.TravelPlace).filter(orm_models.TravelPlace.id == place_id).first()
        if row is not None:
            self.db.delete(row)
            self.db.commit()

    def get_place_for_owner(self, place_id: int, owner_id: int) -> TravelPlace | None:
        row = (
            self.db.query(orm_models.TravelPlace)
            .join(orm_models.TravelItinerary, orm_models.TravelPlace.itinerary_id == orm_models.TravelItinerary.id)
            .filter(orm_models.TravelPlace.id == place_id, orm_models.TravelItinerary.owner_id == owner_id)
            .first()
        )
        return _travel_place(row) if row else None

    def list_places_for_itinerary(self, itinerary_id: int) -> list[TravelPlace]:
        rows = (
            self.db.query(orm_models.TravelPlace)
            .filter(orm_models.TravelPlace.itinerary_id == itinerary_id)
            .order_by(orm_models.TravelPlace.sequence_order.asc(), orm_models.TravelPlace.id.asc())
            .all()
        )
        return [_travel_place(row) for row in rows]

    def add_route(self, route: TravelRoute) -> TravelRoute:
        row = orm_models.TravelRoute(
            itinerary_id=route.itinerary_id,
            origin_place_id=route.origin_place_id,
            destination_place_id=route.destination_place_id,
            transport_mode=route.transport_mode,
            distance_meters=route.distance_meters,
            duration_seconds=route.duration_seconds,
            sequence_order=route.sequence_order,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _travel_route(row)

    def update_route(self, route: TravelRoute) -> TravelRoute:
        row = self.db.query(orm_models.TravelRoute).filter(orm_models.TravelRoute.id == route.id).first()
        if row is None:
            raise ValueError("Travel route not found")
        row.origin_place_id = route.origin_place_id
        row.destination_place_id = route.destination_place_id
        row.transport_mode = route.transport_mode
        row.distance_meters = route.distance_meters
        row.duration_seconds = route.duration_seconds
        row.sequence_order = route.sequence_order
        self.db.commit()
        self.db.refresh(row)
        return _travel_route(row)

    def remove_route(self, route_id: int) -> None:
        row = self.db.query(orm_models.TravelRoute).filter(orm_models.TravelRoute.id == route_id).first()
        if row is not None:
            self.db.delete(row)
            self.db.commit()

    def get_route_for_owner(self, route_id: int, owner_id: int) -> TravelRoute | None:
        row = (
            self.db.query(orm_models.TravelRoute)
            .join(orm_models.TravelItinerary, orm_models.TravelRoute.itinerary_id == orm_models.TravelItinerary.id)
            .filter(orm_models.TravelRoute.id == route_id, orm_models.TravelItinerary.owner_id == owner_id)
            .first()
        )
        return _travel_route(row) if row else None

    def list_routes_for_itinerary(self, itinerary_id: int) -> list[TravelRoute]:
        rows = (
            self.db.query(orm_models.TravelRoute)
            .filter(orm_models.TravelRoute.itinerary_id == itinerary_id)
            .order_by(orm_models.TravelRoute.sequence_order.asc(), orm_models.TravelRoute.id.asc())
            .all()
        )
        return [_travel_route(row) for row in rows]


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


class SqlAlchemyArchiveImportSetRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, import_set: ArchiveImportSet) -> ArchiveImportSet:
        row = orm_models.ArchiveImportSet(
            owner_id=import_set.owner_id,
            external_source_id=import_set.external_source_id,
            external_account_id=import_set.external_account_id,
            display_name=import_set.display_name,
            source_type=import_set.source_type,
            notes=import_set.notes,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _archive_import_set(row)

    def list_for_owner(self, owner_id: int) -> list[ArchiveImportSet]:
        rows = (
            self.db.query(orm_models.ArchiveImportSet)
            .filter(orm_models.ArchiveImportSet.owner_id == owner_id)
            .order_by(orm_models.ArchiveImportSet.created_at.desc())
            .all()
        )
        return [_archive_import_set(row) for row in rows]

    def get_for_owner(self, import_set_id: int, owner_id: int) -> ArchiveImportSet | None:
        row = (
            self.db.query(orm_models.ArchiveImportSet)
            .filter(orm_models.ArchiveImportSet.id == import_set_id, orm_models.ArchiveImportSet.owner_id == owner_id)
            .first()
        )
        return _archive_import_set(row) if row else None


class SqlAlchemyArchiveFileRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, archive: ArchiveFile) -> ArchiveFile:
        row = orm_models.ArchiveFile(
            import_set_id=archive.import_set_id,
            original_filename=archive.original_filename,
            stored_filename=archive.stored_filename,
            size_bytes=archive.size_bytes,
            sha256_hash=archive.sha256_hash,
            status=archive.status.value,
            error_message=archive.error_message,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _archive_file(row)

    def update(self, archive: ArchiveFile) -> ArchiveFile:
        row = self.db.query(orm_models.ArchiveFile).filter(orm_models.ArchiveFile.id == archive.id).first()
        if row is None:
            raise ValueError("Archive file not found")
        row.status = archive.status.value
        row.error_message = archive.error_message
        self.db.commit()
        self.db.refresh(row)
        return _archive_file(row)

    def list_for_import_set(self, import_set_id: int) -> list[ArchiveFile]:
        rows = (
            self.db.query(orm_models.ArchiveFile)
            .filter(orm_models.ArchiveFile.import_set_id == import_set_id)
            .order_by(orm_models.ArchiveFile.registered_at.asc(), orm_models.ArchiveFile.id.asc())
            .all()
        )
        return [_archive_file(row) for row in rows]

    def get(self, archive_id: int) -> ArchiveFile | None:
        row = self.db.query(orm_models.ArchiveFile).filter(orm_models.ArchiveFile.id == archive_id).first()
        return _archive_file(row) if row else None


class SqlAlchemyJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, job: Job) -> Job:
        row = orm_models.Job(
            name=job.name,
            status=job.status.value,
            task_type=job.task_type,
            payload_json=json.dumps(job.payload_json, sort_keys=True),
            result_json=json.dumps(job.result_json, sort_keys=True) if job.result_json is not None else None,
            result=job.result,
            error_message=job.error_message,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            queued_at=job.queued_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _job(row)

    def update(self, job: Job) -> Job:
        row = self.db.query(orm_models.Job).filter(orm_models.Job.id == job.id).first()
        if row is None:
            raise ValueError("Job not found")
        row.status = job.status.value
        row.task_type = job.task_type
        row.payload_json = json.dumps(job.payload_json, sort_keys=True)
        row.result_json = json.dumps(job.result_json, sort_keys=True) if job.result_json is not None else None
        row.result = job.result
        row.error_message = job.error_message
        row.attempts = job.attempts
        row.max_attempts = job.max_attempts
        row.queued_at = job.queued_at
        row.started_at = job.started_at
        row.completed_at = job.completed_at
        row.updated_at = orm_models.now_utc()
        self.db.commit()
        self.db.refresh(row)
        return _job(row)

    def list(self) -> list[Job]:
        rows = self.db.query(orm_models.Job).order_by(orm_models.Job.created_at.desc()).all()
        return [_job(row) for row in rows]

    def get(self, job_id: int) -> Job | None:
        row = self.db.query(orm_models.Job).filter(orm_models.Job.id == job_id).first()
        return _job(row) if row else None

    def next_queued(self) -> Job | None:
        row = (
            self.db.query(orm_models.Job)
            .filter(orm_models.Job.status == JobStatus.QUEUED.value)
            .order_by(orm_models.Job.queued_at.asc(), orm_models.Job.id.asc())
            .first()
        )
        return _job(row) if row else None

    def count_by_status(self) -> dict[JobStatus, int]:
        counts = {status: 0 for status in JobStatus}
        rows = self.db.query(orm_models.Job.status).all()
        for (status,) in rows:
            counts[JobStatus(status)] += 1
        return counts


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
