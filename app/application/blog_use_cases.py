from dataclasses import replace
from datetime import datetime, timezone
import re

from app.application.dto import CreateBlogPostCommand, UpdateBlogPostCommand
from app.domain.blog import BlogPost, BlogStatus
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import BlogPostNotFound, DuplicateSlug, InvalidBlogPost
from app.domain.repositories import AuditRepository, BlogPostRepository, ContentRepository


class BlogPostUseCases:
    def __init__(self, blog_posts: BlogPostRepository, content: ContentRepository, audits: AuditRepository | None = None):
        self.blog_posts = blog_posts
        self.content = content
        self.audits = audits

    def create_draft(self, user: User, command: CreateBlogPostCommand) -> BlogPost:
        self._validate_title(command.title)
        slug = self._normalise_slug(command.slug, command.title)
        self._validate_slug_available(user.id, slug)
        content_item = self.content.add(
            ContentItem(
                id=None,
                owner_id=user.id,
                title=command.title,
                description=command.summary,
                content_type="blog_post",
                original_filename=f"{slug}.md",
                stored_filename=f"blog:{user.id}:{slug}",
                mime_type="text/markdown",
                size_bytes=len(command.body.encode("utf-8")),
                tags=command.tags,
            )
        )
        post = self.blog_posts.add(
            BlogPost(
                id=None,
                owner_id=user.id,
                content_item=content_item,
                slug=slug,
                body=command.body,
                summary=command.summary,
                status=BlogStatus.DRAFT,
                tags=command.tags,
            )
        )
        self._audit(user.id, "blog_post_created", post.id, post.slug)
        return post

    def update_draft(self, user: User, post_id: int, command: UpdateBlogPostCommand) -> BlogPost:
        post = self._get_post(user, post_id)
        if post.status != BlogStatus.DRAFT:
            raise InvalidBlogPost("Published posts cannot be edited")
        title = command.title if command.title is not None else post.title
        slug = self._normalise_slug(command.slug, title) if command.slug is not None else post.slug
        body = command.body if command.body is not None else post.body
        summary = command.summary if command.summary is not None else post.summary
        tags = command.tags if command.tags is not None else post.tags
        self._validate_title(title)
        if slug != post.slug:
            self._validate_slug_available(user.id, slug)
        content_item = replace(
            post.content_item,
            title=title,
            description=summary,
            original_filename=f"{slug}.md",
            stored_filename=f"blog:{user.id}:{slug}",
            size_bytes=len(body.encode("utf-8")),
            tags=tags,
        )
        updated = self.blog_posts.update(
            replace(
                post,
                content_item=content_item,
                slug=slug,
                body=body,
                summary=summary,
                tags=tags,
                updated_at=datetime.now(timezone.utc),
            )
        )
        self._audit(user.id, "blog_post_updated", updated.id, updated.slug)
        return updated

    def publish(self, user: User, post_id: int) -> BlogPost:
        post = self._get_post(user, post_id)
        if not post.body.strip():
            raise InvalidBlogPost("Body is required for publishing")
        updated = self.blog_posts.update(
            replace(
                post,
                status=BlogStatus.PUBLISHED,
                published_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        self._audit(user.id, "blog_post_published", updated.id, updated.slug)
        return updated

    def unpublish(self, user: User, post_id: int) -> BlogPost:
        post = self._get_post(user, post_id)
        updated = self.blog_posts.update(
            replace(post, status=BlogStatus.DRAFT, published_at=None, updated_at=datetime.now(timezone.utc))
        )
        self._audit(user.id, "blog_post_unpublished", updated.id, updated.slug)
        return updated

    def get_by_id(self, user: User, post_id: int) -> BlogPost:
        return self._get_post(user, post_id)

    def get_by_slug(self, user: User, slug: str) -> BlogPost:
        post = self.blog_posts.get_by_slug_for_owner(slug, user.id)
        if not post:
            raise BlogPostNotFound()
        return post

    def list_posts(self, user: User) -> list[BlogPost]:
        return self.blog_posts.list_for_owner(user.id)

    def search_posts(self, user: User, query: str) -> list[BlogPost]:
        return self.blog_posts.search_for_owner(user.id, query)

    def _get_post(self, user: User, post_id: int) -> BlogPost:
        post = self.blog_posts.get_for_owner(post_id, user.id)
        if not post:
            raise BlogPostNotFound()
        return post

    def _validate_title(self, title: str) -> None:
        if not title.strip():
            raise InvalidBlogPost("Title is required")

    def _normalise_slug(self, slug: str | None, title: str) -> str:
        candidate = slug.strip() if slug else ""
        if not candidate:
            candidate = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        if not candidate:
            raise InvalidBlogPost("Slug is required")
        return candidate

    def _validate_slug_available(self, owner_id: int, slug: str) -> None:
        if self.blog_posts.get_by_slug_for_owner(slug, owner_id):
            raise DuplicateSlug()

    def _audit(self, user_id: int | None, action: str, post_id: int | None, details: str | None) -> None:
        if not self.audits:
            return
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user_id,
                action=action,
                entity_type="blog_post",
                entity_id=str(post_id) if post_id is not None else None,
                details=details,
            )
        )
