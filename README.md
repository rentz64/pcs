# PCS Backend

Private Content Service (PCS) backend.

## Current scope

The current backend preserves the Release 1.1 API contract and implements the first end-to-end content lifecycle:

1. Local user authentication.
2. Local SQLite database.
3. Local object storage under `storage/objects`.
4. File upload with metadata.
5. File download.
6. Content library listing.
7. Search by title, description, filename, tags, and content type.
8. Central runtime configuration with a sanitized status summary.
9. System health and status endpoints for API, database, object storage, and background job foundation checks.
10. External import foundation with source/account registration, import jobs, and imported content provenance.
11. Media library foundation for image and video uploads.
12. Email mirroring foundation using a fake/local adapter.
13. Blog post draft, publish, unpublish, listing, slug lookup, and search workflows.
14. Travel itinerary foundation with places and routes.
15. Executable background task engine with manual local job execution.
16. Internal in-process application event publisher separate from audit logging.
17. Google Takeout and generic ZIP archive import foundation.
18. Audit logging for important actions.
19. Test suite using pytest and FastAPI TestClient.

Real Gmail OAuth, live email service connections, sending email, two-way mailbox sync, Google Drive, Maps, IMAP, OAuth integrations, cloud integrations, real map services, live geocoding, route optimisation, advanced media processing, AI classification, OCR, transcription, collaborative editing, advanced full-text extraction, and frontend UI are intentionally outside the current scope.

## Technology choices

The backend uses Python 3.14, FastAPI, SQLite through SQLAlchemy, and local filesystem object storage. Sprint 2 arranged the code as Clean Architecture / Ports and Adapters while keeping SQLite and local storage as infrastructure details. Sprint 3 adds the internal Unified Content Platform foundation: shared content metadata, tag normalization, collection references, version metadata, a search port, and a content type handler registry. Sprint 4 adds the External Import Foundation on top of `ContentItem` provenance metadata. Sprint 6 adds media library foundations for image and video content. Sprint 7 adds email mirroring foundations with a fake/local import adapter. Sprint 8 adds travel itineraries, places, and routes as specialised content without live map integrations. Sprint 9 adds application infrastructure for configuration, health/status, background jobs, internal events, and cleaner OpenAPI discovery before UI work begins. Sprint 10 turns the job foundation into a manual local task execution engine without external schedulers. Sprint 11 adds Google Takeout and generic ZIP archive import sets for local archive ingestion without Google APIs or OAuth.

## Project structure

```text
app/
  domain/          # entities, metadata, handlers, errors, repository/storage/security/search protocols
  application/     # auth, content, and audit use cases plus DTOs
  infrastructure/  # SQLAlchemy, SQLite session, local storage, password and token services
  interfaces/api/  # FastAPI routes, schemas, and dependency wiring
  main.py          # app creation, lifespan, health, router registration
docs/
  adr/             # architecture decision records
```

Domain and application code must not import FastAPI or SQLAlchemy.

## Unified content platform

`ContentItem` is the generic domain model for uploaded content. It keeps the Release 1.1 fields used by the API and adds internal shared metadata:

- normalized tag tuples derived from the legacy comma-separated `tags` field
- collection references for future grouping workflows
- version metadata for future revision tracking
- a `SearchQuery` abstraction so search can move behind a dedicated adapter later
- a `ContentTypeHandlerRegistry` so future content types can plug in behavior without changing core use cases

Sprint 3 does not add product-specific content workflows or new API endpoints.

## External import foundation

Imported content is represented by `ContentItem` with provenance fields:

- `origin`
- `external_source_id`
- `external_account_id`
- `external_content_id`
- `external_content_type`
- `imported_at`
- `import_batch_id`
- `source_url`
- `source_reference`

The import foundation adds external sources, external accounts, import jobs, import batches, an `ImportAdapter` port, and a deterministic local dummy adapter. It does not implement real external service integrations or credentials.

```text
POST /imports/sources
GET /imports/sources
POST /imports/accounts
GET /imports/accounts
GET /imports/sources/{source_id}/content-types
POST /imports/jobs
GET /imports/jobs
GET /imports/jobs/{job_id}
```

## Archive Import API

Sprint 11 adds local ZIP archive import sets for Google Takeout and generic file archives. An import set groups one or more ZIP files that belong to a specific external account/export set, so separate Google accounts remain distinguishable over time.

```text
POST /archive-import/import-sets
GET /archive-import/import-sets
GET /archive-import/import-sets/{import_set_id}
POST /archive-import/import-sets/{import_set_id}/archives
GET /archive-import/import-sets/{import_set_id}/archives
POST /archive-import/archives/{archive_id}/scan
POST /archive-import/import-sets/{import_set_id}/scan
POST /archive-import/import-sets/{import_set_id}/import
GET /archive-import/import-sets/{import_set_id}/summary
```

The scanner inspects ZIP central-directory metadata and individual entries without extracting the full archive. It recognises standard `Takeout/` paths and artificial wrapper roots such as `t1/` or `t2/` from manually split archives. Original internal ZIP paths are preserved while logical paths are normalised for classification.

Initial import supports file-like content such as PDFs, Office documents, images, videos, text files, ZIP/TGZ archives, and generic binaries. Gmail MBOX support is streaming-oriented and imports synthetic/simple messages through the existing Email Mirroring foundation; attachment extraction and full Gmail label fidelity remain future work.

## Blog API

Blog posts are implemented as specialised content backed by `ContentItem` plus blog-specific persistence.

```text
POST /blog/posts
GET /blog/posts
GET /blog/posts/{id}
GET /blog/posts/slug/{slug}
PUT /blog/posts/{id}
POST /blog/posts/{id}/publish
POST /blog/posts/{id}/unpublish
```

Slugs are unique per owner. Draft posts may be incomplete, but publishing requires a non-empty body.

## Media API

Media items are implemented as specialised content backed by `ContentItem`, local object storage, and media-specific metadata. The foundation accepts common image and video MIME types and stores width, height, and duration metadata as nullable fields for future processing.

```text
POST /media
GET /media
GET /media/{media_id}
GET /media/{media_id}/download
```

## Email API

Mirrored emails are represented as imported `ContentItem` records with email-specific metadata and attachment metadata. Sprint 7 uses only a fake/local adapter for deterministic tests.

```text
POST /email/import/fake
GET /email/messages
GET /email/messages/{email_id}
GET /email/messages/{email_id}/attachments
GET /email/attachments/{attachment_id}/download
```

## Travel API

Travel itineraries are implemented as specialised content backed by `ContentItem` plus itinerary, place, and route metadata. Sprint 8 stores user-provided coordinates and route placeholders only; it does not call map services, geocode addresses, or optimise routes.

```text
POST /travel/itineraries
GET /travel/itineraries
GET /travel/itineraries/{itinerary_id}
PUT /travel/itineraries/{itinerary_id}
POST /travel/itineraries/{itinerary_id}/places
PUT /travel/places/{place_id}
DELETE /travel/places/{place_id}
POST /travel/itineraries/{itinerary_id}/routes
PUT /travel/routes/{route_id}
DELETE /travel/routes/{route_id}
```

## System API

Sprint 9 adds public system endpoints for local runtime checks:

```text
GET /system/health
GET /system/status
```

These endpoints report the API version, SQLite status, local object storage status, and background job foundation status. `/system/status` also includes a sanitized runtime configuration summary and never exposes secrets.

## Background jobs and events

Sprint 9 introduced a generic `Job` domain model with queued, running, succeeded, failed, and cancelled states plus job repository/use-case ports. Sprint 10 adds executable tasks with:

- `TaskDefinition`
- `TaskHandler`
- `TaskRegistry`
- `TaskExecutionContext`
- `TaskExecutionResult`

Jobs now store task type, JSON payload/result data, error messages, attempts, retry limits, and queued/started/completed timestamps. Execution is still local and manual; PCS does not run an external scheduler or worker service.

Built-in local task handlers:

```text
system.noop
system.fail
content.reindex
imports.placeholder
```

Task/job API:

```text
POST /system/jobs
GET /system/jobs
GET /system/jobs/{job_id}
POST /system/jobs/{job_id}/execute
POST /system/jobs/execute-next
POST /system/jobs/{job_id}/retry
POST /system/jobs/{job_id}/cancel
```

Internal `ApplicationEvent` publishing is handled by a simple in-process publisher. Audit logging remains a separate user/action record and is not replaced by internal events.

## Installation

Run commands from the repository root.

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Running tests

The project follows a warning-free test policy. DeprecationWarning and ResourceWarning are treated as test failures through `pytest.ini`.

```powershell
.venv\Scripts\python.exe -m pytest
```

PowerShell 7-compatible commands will become the reference automation style from Sprint 2 onwards, while remaining usable on Windows 11 during development where practical.

## Running the service

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open the generated API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Default test user

The application creates a default local user on startup:

```text
username: admin
password: admin-change-me
```

Change this before using the service with real data.

## Basic API flow

1. `POST /auth/login` with JSON body:

```json
{"username": "admin", "password": "admin-change-me"}
```

2. Use the returned bearer token.

3. Upload content with `POST /content` using multipart form data.

4. List content with `GET /content`.

5. Search with `GET /content/search?q=...`.

6. Download with `GET /content/{content_id}/download`.
7. Check system health with `GET /system/health`.
8. Manage blog posts under `/blog/posts`.
9. Register import sources/accounts and execute import jobs under `/imports`.
10. Upload and download media under `/media`.
11. Import and browse fake mirrored email under `/email`.
12. Manage travel itineraries, places, and routes under `/travel`.
13. Register and scan local Takeout/archive ZIPs under `/archive-import`.

## Local storage layout

Runtime data lives under:

```text
storage/
  pcs.sqlite3
  objects/
```

These files are excluded from Git by `.gitignore`.

## Test-driven development notes

The integration tests cover authentication, upload, listing, search, download, and audit creation. Use-case and platform tests use fake repositories/storage. New behaviour should start from failing tests and then implementation.

## Branching and merge workflow

Each sprint must be developed on its own Git branch. The `main` branch should remain the stable, tested baseline. Sprint work should only be merged into `main` after local testing and user acceptance.

Recommended workflow for each sprint:

```powershell
git checkout main
git pull
git checkout -b sprint-2-clean-architecture
```

During the sprint, commit normally on the sprint branch:

```powershell
git status
git add .
git commit -m "Implement Sprint 2 clean architecture baseline"
```

Before merging back to `main`, run the full test suite:

```powershell
.venv\Scripts\python.exe -m pytest
```

If the tests pass and the sprint has been reviewed, merge into `main`:

```powershell
git checkout main
git merge sprint-2-clean-architecture
git tag sprint-2-accepted
```

Use a clear branch name for every sprint, for example `sprint/1`, `sprint/2`, `sprint/3`, and so on.

## Sprint 1 v0.3 Bugfix

This package includes a Windows-specific pytest teardown fix. The test fixture explicitly disposes the temporary SQLite test engine before pytest removes the temporary database directory, avoiding `PermissionError: [WinError 32]` on Windows.

## Sprint 1.1 Maintenance Release

This package replaces FastAPI's deprecated `@app.on_event("startup")` hook with the modern lifespan handler. The lifespan handler initialises the local SQLite database at startup and disposes the SQLAlchemy engine during shutdown.

The release also adds `pytest.ini` so deprecation and resource warnings fail the test run. A sprint is considered complete only when tests pass without warnings.
