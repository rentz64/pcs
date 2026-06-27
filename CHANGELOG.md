# Changelog

## Sprint 2

- Refactored the Release 1.1 backend into a Clean Architecture / Ports and Adapters layout.
- Preserved existing FastAPI endpoints, authentication behaviour, SQLite persistence, local object storage, and response contracts.
- Added use-case unit tests with fake repositories and storage.
- Added API characterization tests for health, authentication errors, download errors, and upload defaults.
- Added ADR-0003 for the Clean Architecture decision.

## Sprint 1.1

- Replaced deprecated FastAPI startup hooks with lifespan handling.
- Added warning-free pytest configuration.

