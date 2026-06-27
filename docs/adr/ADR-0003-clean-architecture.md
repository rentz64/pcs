# ADR-0003: Clean Architecture Backend Layout

## Status

Accepted for Sprint 2.

## Context

Release 1.1 implemented the backend in a compact FastAPI module. That was sufficient for the first local content lifecycle, but routing, persistence, storage, authentication, and audit behaviour were tightly coupled. Sprint 2 needs a structure that keeps the existing API contract stable while making future features easier to test and change.

## Decision

Refactor the backend into Clean Architecture / Ports and Adapters:

- `app/domain` contains plain entities, errors, and protocols.
- `app/application` contains use cases and DTOs.
- `app/infrastructure` contains SQLAlchemy/SQLite repositories, local filesystem object storage, password hashing, and token signing.
- `app/interfaces/api` contains FastAPI schemas, dependencies, and route adapters.
- `app/main.py` creates the FastAPI app, manages lifespan initialization, and registers routers.

Domain and application layers do not import FastAPI or SQLAlchemy. SQLite and local filesystem object storage remain the infrastructure implementations.

## Consequences

The API remains compatible with Release 1.1 while the code has clearer dependency boundaries. Use cases can be unit tested with fake repositories and storage. Future infrastructure changes can be isolated behind protocols, but the current project still keeps the same database, storage layout, and authentication behaviour.
