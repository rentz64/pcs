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
