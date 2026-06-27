# ADR-0005: External Import Foundation

## Status

Accepted for Sprint 4.

## Context

The Unified Content Platform needs a foundation for imported content without binding the domain or application layers to any real provider. Future sources may include Gmail, Google Drive, Maps, IMAP, OAuth-backed services, and cloud systems, but Sprint 4 must not implement those integrations or store real credentials.

Imported content also needs provenance so PCS can distinguish native content from imported content and trace the source, account, external identifier, content type, batch, and import time.

## Decision

Extend `ContentItem` with nullable import provenance fields:

- `origin`
- `external_source_id`
- `external_account_id`
- `external_content_id`
- `external_content_type`
- `imported_at`
- `import_batch_id`
- `source_url`
- `source_reference`

Add import domain entities for external sources, external accounts, import jobs, import batches, and imported content references. Add repository protocols and SQLite implementations for sources, accounts, jobs, and batches. Add an `ImportAdapter` protocol with content type listing, authentication, connection testing, and content import methods.

The only adapter in this sprint is a deterministic local dummy adapter. It does not call external services or use secrets.

## Consequences

PCS can execute import jobs through a stable application port and record imported content provenance in `ContentItem`. Existing Release 1.1 content APIs remain compatible because all provenance fields are nullable and native content defaults to `origin = "native"`.

Existing SQLite databases need the new import tables and nullable `content_items` provenance columns. Startup schema initialization creates new tables and applies a small SQLite compatibility migration for the added `content_items` columns.
