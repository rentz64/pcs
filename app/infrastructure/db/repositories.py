from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.blog import BlogPost, BlogStatus
from app.domain.entities import AuditEntry, ContentItem, User
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
