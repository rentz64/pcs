# PCS Development Guide

## 1. Purpose

This guide defines how PCS is developed, tested, documented, and released.

## 2. Roles

The user acts as Product Owner, tester, and final integrator.

ChatGPT acts as software architect, technical lead, reviewer, documentation assistant, and planning assistant.

Codex CLI acts as the local coding agent that implements tasks inside the repository.

## 3. Development Platform

Primary platform:

- Windows 11
- PowerShell 7
- Python 3.12
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