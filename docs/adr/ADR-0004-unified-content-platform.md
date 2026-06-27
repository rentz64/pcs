# ADR-0004: Unified Content Platform Foundation

## Status

Accepted for Sprint 3.

## Context

PCS needs to support more content categories over time without turning the core content lifecycle into separate product-specific implementations. Release 1.1 already supports a generic upload, listing, search, download, and audit flow. Sprint 2 introduced Clean Architecture boundaries. Sprint 3 uses those boundaries to establish a generic content platform before adding any specific workflows.

## Decision

Keep `ContentItem` as the generic domain model and extend it with shared metadata:

- normalized tags derived from the existing comma-separated API field
- collection references for future grouping
- version metadata for future revision tracking
- a `SearchQuery` port for search adapters
- a `ContentTypeHandlerRegistry` for future content type plugins

The Release 1.1 API fields, endpoints, authentication behaviour, SQLite storage, and local filesystem object storage remain unchanged. Blogs, email, maps, media-specific workflows, and cloud sync are explicitly out of scope for Sprint 3.

## Consequences

Future product workflows can build on shared content primitives instead of duplicating metadata, search, and handler concepts. The current database schema does not change; collection and version metadata exist in the domain model as forward-compatible defaults until a sprint requires persisted workflows and migrations.
