# PCS MVP Sprint 1

Private Content Service (PCS) - Sprint 1 MVP implementation.

## Sprint 1 scope

This release implements the first end-to-end content lifecycle:

1. Local user authentication.
2. Local SQLite database.
3. Local object storage under `storage/objects`.
4. File upload with metadata.
5. File download.
6. Content library listing.
7. Search by title, description, filename, tags, and content type.
8. Audit logging for important actions.
9. Test suite using pytest and FastAPI TestClient.

Cloud mirroring, IMAP mirroring, collaborative editing, advanced full-text extraction, and frontend UI are intentionally outside Sprint 1.

## Technology choices

The backend uses Python and FastAPI. The database uses SQLite through SQLAlchemy. Object storage uses the local filesystem. The design keeps the storage service abstract enough to support a future encrypted cloud mirror.

## Installation

```bash
python -m venv .venv
. .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate # Windows PowerShell
pip install -r requirements.txt
```

## Running tests

The project follows a warning-free test policy. DeprecationWarning and ResourceWarning are treated as test failures through `pytest.ini`.

```powershell
.venv\Scripts\python.exe -m pytest
```

PowerShell 7-compatible commands will become the reference automation style from Sprint 2 onwards, while remaining usable on Windows 11 during development where practical.

## Running the service

```bash
uvicorn app.main:app --reload
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

## Local storage layout

Runtime data lives under:

```text
storage/
  pcs.sqlite3
  objects/
```

These files are excluded from Git by `.gitignore`.

## Test-driven development notes

The Sprint 1 tests cover authentication, upload, listing, search, download, and audit creation. New features should start from failing tests and then implementation.

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

Use a clear branch name for every sprint, for example `sprint-1-mvp-foundation`, `sprint-2-clean-architecture`, `sprint-3-blog-management`, and so on.

## Sprint 1 v0.3 Bugfix

This package includes a Windows-specific pytest teardown fix. The test fixture explicitly disposes the temporary SQLite test engine before pytest removes the temporary database directory, avoiding `PermissionError: [WinError 32]` on Windows.

## Sprint 1.1 Maintenance Release

This package replaces FastAPI's deprecated `@app.on_event("startup")` hook with the modern lifespan handler. The lifespan handler initialises the local SQLite database at startup and disposes the SQLAlchemy engine during shutdown.

The release also adds `pytest.ini` so deprecation and resource warnings fail the test run. A sprint is considered complete only when tests pass without warnings.
