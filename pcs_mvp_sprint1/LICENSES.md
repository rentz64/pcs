# Licences Inventory

This file records the licence of each component intentionally introduced in Sprint 1. It should be updated whenever a dependency is added, removed, or replaced.

| Component | Role | Licence | Notes |
|---|---|---|---|
| Python | Runtime | Python Software Foundation License | Open source runtime. |
| FastAPI | Web API framework | MIT | Preferred lightweight Python API framework. |
| Starlette | ASGI toolkit used by FastAPI | BSD-3-Clause | Transitive runtime dependency of FastAPI. |
| Pydantic | Data validation | MIT | Used by FastAPI for schemas and validation. |
| Uvicorn | ASGI server | BSD-3-Clause | Local development server. |
| SQLAlchemy | ORM / database access | MIT | SQLite access and domain persistence. |
| Python standard library hashlib/hmac/base64/json | Local password hashing and signed bearer tokens | Python Software Foundation License | Used in Sprint 1 to keep the dependency set small; may be replaced by a dedicated security library later. |
| python-multipart | Multipart upload parsing | Apache-2.0 | Required by FastAPI file uploads. |
| pytest | Test runner | MIT | Test-driven development. |
| httpx | Test HTTP client | BSD-3-Clause | Used by FastAPI TestClient. |
| SQLite | Local database engine | Public domain | Embedded local database. |

## Licensing policy

PCS prefers open source components. For this private MVP, components with permissive licences such as MIT, BSD, Apache-2.0, Python Software Foundation License, and public-domain software are preferred. Components with more restrictive open source licences may be considered where necessary because commercial exploitation is not currently planned, but such decisions should be documented here before adoption.
