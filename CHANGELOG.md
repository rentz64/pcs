# Changelog

## Sprint 3

- Added the Unified Content Platform domain foundation while preserving the Release 1.1 API contract.
- Added shared content metadata, normalized tag parsing, collection references, and version metadata to the generic `ContentItem` domain model.
- Added a `SearchQuery` abstraction and made the SQLAlchemy content repository satisfy the search port without changing search behaviour.
- Added a `ContentTypeHandlerRegistry` plugin point for future content-specific handlers.
- Added platform unit tests for metadata, tags, search delegation, and handler dispatch.
- Added ADR-0004 for the Unified Content Platform decision.

## Sprint 2

- Refactored the Release 1.1 backend into a Clean Architecture / Ports and Adapters layout.
- Preserved existing FastAPI endpoints, authentication behaviour, SQLite persistence, local object storage, and response contracts.
- Added use-case unit tests with fake repositories and storage.
- Added API characterization tests for health, authentication errors, download errors, and upload defaults.
- Added ADR-0003 for the Clean Architecture decision.

## Sprint 1.1

- Replaced deprecated FastAPI startup hooks with lifespan handling.
- Added warning-free pytest configuration.

