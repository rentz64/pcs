# Changelog

## Sprint 4

- Added the External Import Foundation for the Unified Content Platform.
- Extended `ContentItem` with import provenance fields for origin, external source/account identifiers, external content identifiers, import batch, import timestamp, and source reference data.
- Added external source, external account, import job, import batch, and imported content reference domain entities.
- Added import adapter, repository, and use-case ports with SQLite infrastructure implementations.
- Added deterministic local dummy import adapter support without real external service credentials or network integrations.
- Added `/imports` API routes for source/account registration, supported content types, import job execution, job listing, and job status lookup.
- Added import audit events for source/account registration, job creation/execution, and imported content.
- Added import use-case and API integration tests.
- Added ADR-0005 for the External Import Foundation decision.

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

