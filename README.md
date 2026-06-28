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
8. External import foundation with source/account registration, import jobs, and imported content provenance.
9. Media library foundation for image and video uploads.
10. Blog post draft, publish, unpublish, listing, slug lookup, and search workflows.
11. Audit logging for important actions.
12. Test suite using pytest and FastAPI TestClient.

Real Gmail, Google Drive, Maps, IMAP, OAuth, cloud integrations, advanced media processing, AI classification, OCR, transcription, collaborative editing, advanced full-text extraction, and frontend UI are intentionally outside the current scope.

## Technology choices

The backend uses Python 3.14, FastAPI, SQLite through SQLAlchemy, and local filesystem object storage. Sprint 2 arranged the code as Clean Architecture / Ports and Adapters while keeping SQLite and local storage as infrastructure details. Sprint 3 adds the internal Unified Content Platform foundation: shared content metadata, tag normalization, collection references, version metadata, a search port, and a content type handler registry. Sprint 4 adds the External Import Foundation on top of `ContentItem` provenance metadata. Sprint 6 adds media library foundations for image and video content.

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
7. Manage blog posts under `/blog/posts`.
8. Register import sources/accounts and execute import jobs under `/imports`.
9. Upload and download media under `/media`.

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
