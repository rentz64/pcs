# PCS Development Guide

## 1. Purpose

This guide defines how PCS is developed, tested, documented, and released.

## 2. Roles

The user acts as Product Owner, tester, and final integrator.

ChatGPT acts as software architect, technical lead, reviewer, documentation assistant, and planning assistant.

Codex CLI acts as the local coding agent that implements tasks inside the repository.
Codex starts from the repository root, which is also the Python project root.

## 3. Development Platform

Primary platform:

- Windows 11
- PowerShell 7
- Python 3.14.6
- Git
- Node.js LTS
- Notepad++
- Codex CLI

PowerShell 7 is the reference shell because it also runs on Linux.

## 4. Repository Rule

GitHub is the single source of truth.

No source code, documentation, backlog item, architecture decision, release note, or licence record is considered official unless committed to Git.

## 5. Branching Strategy

The `main` branch must always contain tested, stable code.

Development is performed on sprint branches only.

Branch naming convention:

```text
sprint/1
sprint/1.1
sprint/2
sprint/3
sprint/4
```

The current project baseline is Python 3.14.

Do not work directly on `main`. Use the current sprint branch for all development work.

## 6. Development Rules

- Use the project virtual environment and project scripts from the repository root.
- Do not use bare `python`; run Python through `.venv\Scripts\python.exe`.
- Do not introduce Java or .NET components.
- Do not commit secrets, databases, local storage, generated caches, or virtual environments.
- Use test-driven development for behaviour changes.
- Keep the project warning-free.

## 7. Testing

Run the full test suite from the repository root:

```powershell
.venv\Scripts\python.exe -m pytest
```

## 8. Architecture

PCS uses a Clean Architecture / Ports and Adapters layout:

```text
app/
  domain/
  application/
  infrastructure/
  interfaces/api/
```

Dependency direction points inward. The domain and application layers must not import FastAPI or SQLAlchemy. Infrastructure owns SQLite, SQLAlchemy, local filesystem object storage, password hashing, and token signing. API route modules are adapters that translate HTTP requests and responses to application use cases.

The Unified Content Platform lives in the domain and application layers. Generic content metadata, tags, collections, version metadata, search ports, and content type handlers must remain independent of FastAPI and SQLAlchemy. Product-specific workflows such as blogs, email, maps, media, and cloud sync should be added only when a sprint explicitly requires them.

Blog Management is implemented as a specialised content workflow on top of `ContentItem`. Blog domain and use-case code must remain independent of FastAPI and SQLAlchemy. Blog API routes should stay thin and translate HTTP payloads/errors to application use cases.

The External Import Foundation is implemented through domain/application ports and infrastructure adapters. Import code must not use real external service credentials or call Gmail, Google Drive, Maps, IMAP, OAuth, or cloud services unless a future sprint explicitly introduces those integrations.

Codex should start from the repository root, preserve existing API behaviour unless explicitly asked to change it, and run the full test suite before reporting completion.
