# ADR-0005: Blog Posts as Specialised Content Items

## Status

Accepted for Sprint 4.

## Context

Sprint 3 established `ContentItem` as the generic foundation for uploaded and future content. Sprint 4 adds Blog Management without changing existing upload, listing, search, download, authentication, storage, or audit behaviour.

Blog posts need fields that do not belong in every generic content item: slug, body, summary, draft/published status, and published timestamp. At the same time, blogs should reuse shared metadata such as title, tags, ownership, timestamps, content type, and future collection/version concepts.

## Decision

Represent each blog post as:

- a `ContentItem` with `content_type = "blog_post"` for shared content metadata
- a `blog_posts` infrastructure table for blog-specific fields
- a `BlogPost` domain entity that composes the foundational `ContentItem`

The blog application layer depends on repository protocols. FastAPI routes remain adapters, and SQLAlchemy details remain in infrastructure.

## Consequences

Existing Release 1.1 content APIs remain compatible. Blog fields can evolve independently without bloating every generic content item. Existing SQLite databases need the `blog_posts` table created by startup schema initialization before blog APIs can persist posts.
