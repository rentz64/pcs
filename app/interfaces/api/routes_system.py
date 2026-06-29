from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.application.job_use_cases import JobUseCases
from app.domain.jobs import JobStatus
from app.interfaces.api.dependencies import get_db_session, get_job_use_cases, get_storage
from app.infrastructure.storage.local import LocalObjectStorage

router = APIRouter(prefix="/system", tags=["system"])


def _database_status(db: Session) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return {"status": "error", "backend": "sqlite"}
    return {"status": "ok", "backend": "sqlite"}


def _object_storage_status(storage: LocalObjectStorage) -> dict[str, str]:
    try:
        Path(storage.root).mkdir(parents=True, exist_ok=True)
    except OSError:
        return {"status": "error", "backend": "local_filesystem"}
    return {"status": "ok", "backend": "local_filesystem"}


def _background_job_status(jobs: JobUseCases) -> dict[str, object]:
    counts = jobs.count_by_status()
    return {
        "status": "ok",
        "backend": "in_process_foundation",
        "counts": {status.value: counts.get(status, 0) for status in JobStatus},
    }


@router.get("/health")
def health(
    db: Session = Depends(get_db_session),
    storage: LocalObjectStorage = Depends(get_storage),
    jobs: JobUseCases = Depends(get_job_use_cases),
) -> dict[str, object]:
    database = _database_status(db)
    object_storage = _object_storage_status(storage)
    background_jobs = _background_job_status(jobs)
    status = "ok" if {database["status"], object_storage["status"], background_jobs["status"]} == {"ok"} else "error"
    return {
        "status": status,
        "api_version": settings.api_version,
        "database": database,
        "object_storage": object_storage,
        "background_jobs": background_jobs,
    }


@router.get("/status")
def status(
    db: Session = Depends(get_db_session),
    storage: LocalObjectStorage = Depends(get_storage),
    jobs: JobUseCases = Depends(get_job_use_cases),
) -> dict[str, object]:
    return {
        "api_version": settings.api_version,
        "configuration": settings.runtime_summary(),
        "database": _database_status(db),
        "object_storage": _object_storage_status(storage),
        "background_jobs": _background_job_status(jobs),
    }
