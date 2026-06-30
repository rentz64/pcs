# Changelog

## Sprint 11

- Added Google Takeout and generic ZIP archive import sets for grouping multiple archives by external account/export set.
- Added archive file registration with local storage, size tracking, SHA-256 hashing, status, and error metadata.
- Added ZIP scanning without full extraction, including standard `Takeout/` services and arbitrary wrapper roots such as `t1/` and `t2/`.
- Added service/content classification for Gmail MBOX, Drive-like files, Calendar ICS, Contacts VCF, Tasks, Maps, Chrome bookmarks, photos-like media, and generic archive/binary files.
- Added file-like archive import into local object storage and `ContentItem` records with import set, archive, original ZIP path, normalised path, account, source, batch, and import timestamp provenance.
- Added streaming-oriented synthetic MBOX import foundation using the existing Email Mirroring repository behavior for duplicate message safety.
- Added `/archive-import` API routes for import set lifecycle, archive registration/listing, archive/import-set scanning, import execution, and summaries.
- Added audit records for import set creation, archive registration/scanning, import start/completion, and imported content.
- Added synthetic archive, arbitrary-root, multiple-ZIP, provenance, MBOX duplicate, account separation, and owner scoping tests.

## Sprint 10

- Added the executable Task Execution Engine on top of the Sprint 9 job foundation.
- Added task definitions, handlers, execution context/result models, and an in-process task registry.
- Added default local-only task handlers for no-op, intentional failure, content reindex placeholder, and import placeholder tasks.
- Extended jobs with task type, JSON payload/result fields, attempts, retry limits, and queued/started/completed timestamps.
- Added job execution, execute-next, retry, cancel, listing, and status use cases with state-transition rules.
- Added `/system/jobs` API endpoints for enqueuing and manually executing background tasks without an external scheduler.
- Added internal event and audit records for queued, started, succeeded, failed, retried, and cancelled jobs.
- Added Sprint 10 task registry, execution, state transition, retry/cancel, failing task, API, audit, and regression tests.

## Sprint 9

- Added centralized runtime configuration with sanitized configuration summaries.
- Added `/system/health` and `/system/status` endpoints for API version, SQLite, local object storage, and background job foundation status.
- Added generic background job domain model, repository port, SQLite repository, and job lifecycle use cases.
- Added internal `ApplicationEvent` and in-process event publisher while keeping audit logging separate.
- Added reusable error response and pagination schema models for future API consistency without changing existing endpoint contracts.
- Improved OpenAPI metadata with title, version, description, and route tags.
- Added Sprint 9 unit, API, OpenAPI, and regression tests.

## Sprint 8

- Added Travel Itinerary Foundation as a specialised content type on the Unified Content Platform.
- Added itinerary, place, and route domain models, use cases, repository ports, and SQLite persistence.
- Added `/travel` API routes for itinerary, place, and route lifecycle operations with owner scoping and validation.
- Added GeoJSON, GPX, and KML import/export placeholder use cases without parsers or external map services.
- Added audit logging for itinerary, place, and route changes.
- Added travel unit and API integration tests.

## Sprint 7

- Added Email Mirroring Foundation as a specialised imported content type on the Unified Content Platform.
- Added email message and attachment metadata persistence linked to imported `ContentItem` records.
- Added fake/local email import adapter for deterministic tests without real credentials or external service connections.
- Added email import, listing, lookup, search, attachment listing, and attachment download use cases.
- Added `/email` API routes with owner scoping, duplicate external message handling, malformed payload validation, and audit logging.
- Added email unit and API integration tests.

## Sprint 6

- Added Media Library Foundation for image and video content on top of the Unified Content Platform.
- Added media metadata persistence linked to `ContentItem`.
- Added media upload, metadata lookup, listing, search, and download use cases.
- Added `/media` API routes with MIME validation, owner scoping, local object storage reuse, and audit logging.
- Added media unit and API integration tests.

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

