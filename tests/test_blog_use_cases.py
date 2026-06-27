from __future__ import annotations

from dataclasses import replace

import pytest

from app.application.blog_use_cases import BlogPostUseCases
from app.application.dto import CreateBlogPostCommand, UpdateBlogPostCommand
from app.domain.blog import BlogPost, BlogStatus
from app.domain.entities import ContentItem, User
from app.domain.errors import BlogPostNotFound, DuplicateSlug, InvalidBlogPost
from tests.test_use_cases import FakeContent


class FakeBlogPosts:
    def __init__(self):
        self.posts: list[BlogPost] = []

    def add(self, post: BlogPost) -> BlogPost:
        saved = replace(post, id=len(self.posts) + 1)
        self.posts.append(saved)
        return saved

    def update(self, post: BlogPost) -> BlogPost:
        for index, existing in enumerate(self.posts):
            if existing.id == post.id:
                self.posts[index] = post
                return post
        raise AssertionError("post not found")

    def get_for_owner(self, post_id: int, owner_id: int) -> BlogPost | None:
        return next((post for post in self.posts if post.id == post_id and post.owner_id == owner_id), None)

    def get_by_slug_for_owner(self, slug: str, owner_id: int) -> BlogPost | None:
        return next((post for post in self.posts if post.slug == slug and post.owner_id == owner_id), None)

    def list_for_owner(self, owner_id: int) -> list[BlogPost]:
        return [post for post in self.posts if post.owner_id == owner_id]

    def search_for_owner(self, owner_id: int, query: str) -> list[BlogPost]:
        lowered = query.lower()
        return [
            post
            for post in self.list_for_owner(owner_id)
            if lowered in post.title.lower() or lowered in post.body.lower() or lowered in post.tags.lower()
        ]


def owner(user_id: int = 7) -> User:
    return User(id=user_id, username=f"user-{user_id}", password_hash="x", role="owner")


def test_create_blog_draft_uses_content_item_foundation():
    content = FakeContent()
    blogs = FakeBlogPosts()
    use_cases = BlogPostUseCases(blogs, content)

    post = use_cases.create_draft(
        owner(),
        CreateBlogPostCommand(
            title="First Post",
            slug="first-post",
            body="",
            summary=None,
            tags="pcs, blog",
            collections=(),
        ),
    )

    assert post.status == BlogStatus.DRAFT
    assert post.content_item.content_type == "blog_post"
    assert post.content_item.title == "First Post"
    assert post.content_item.tags == "pcs, blog"
    assert content.items[0] == post.content_item


def test_blog_slug_must_be_unique_per_owner():
    use_cases = BlogPostUseCases(FakeBlogPosts(), FakeContent())
    use_cases.create_draft(owner(), CreateBlogPostCommand("First", "same", "", None, "", ()))

    with pytest.raises(DuplicateSlug):
        use_cases.create_draft(owner(), CreateBlogPostCommand("Second", "same", "", None, "", ()))


def test_update_draft_rejects_published_posts():
    blogs = FakeBlogPosts()
    use_cases = BlogPostUseCases(blogs, FakeContent())
    post = use_cases.create_draft(owner(), CreateBlogPostCommand("First", "first", "body", None, "", ()))
    published = use_cases.publish(owner(), post.id)

    with pytest.raises(InvalidBlogPost):
        use_cases.update_draft(owner(), published.id, UpdateBlogPostCommand(title="Changed"))


def test_publish_requires_body_and_unpublish_returns_to_draft():
    use_cases = BlogPostUseCases(FakeBlogPosts(), FakeContent())
    post = use_cases.create_draft(owner(), CreateBlogPostCommand("First", "first", "", None, "", ()))

    with pytest.raises(InvalidBlogPost):
        use_cases.publish(owner(), post.id)

    updated = use_cases.update_draft(owner(), post.id, UpdateBlogPostCommand(body="Ready"))
    published = use_cases.publish(owner(), updated.id)
    unpublished = use_cases.unpublish(owner(), published.id)

    assert published.status == BlogStatus.PUBLISHED
    assert published.published_at is not None
    assert unpublished.status == BlogStatus.DRAFT
    assert unpublished.published_at is None


def test_blog_posts_are_scoped_to_owner():
    use_cases = BlogPostUseCases(FakeBlogPosts(), FakeContent())
    post = use_cases.create_draft(owner(1), CreateBlogPostCommand("First", "first", "", None, "", ()))

    with pytest.raises(BlogPostNotFound):
        use_cases.get_by_id(owner(2), post.id)

