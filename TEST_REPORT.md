# Test Report

## Sprint 1.1 Maintenance Release

Date: 2026-06-25

Command executed in the build container:

```bash
.venv/bin/python -m pytest -q
```

Equivalent Windows command:

```powershell
.venv\Scripts\python.exe -m pytest
```

Result:

```text
3 passed
```

## Warning policy

`pytest.ini` treats `DeprecationWarning` and `ResourceWarning` as errors. The Sprint 1.1 test run passed with this policy enabled.

## Changes verified

- Replaced deprecated FastAPI `@app.on_event("startup")` hook with a lifespan handler.
- Kept database initialisation during application startup.
- Added explicit SQLAlchemy engine disposal during application shutdown.
- Preserved the Windows SQLite file-locking fix in the test fixture.
- Confirmed authentication, upload/list/search/download, and audit tests pass.
