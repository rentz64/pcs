from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.dto import EnqueueTaskCommand
from app.config import settings
from app.application.job_use_cases import JobUseCases
from app.domain.entities import User
from app.domain.errors import InvalidJobState, JobAttemptsExhausted, JobNotFound, TaskHandlerNotFound
from app.domain.jobs import Job
from app.domain.jobs import JobStatus
from app.interfaces.api.dependencies import current_user, get_db_session, get_job_use_cases, get_storage
from app.interfaces.api.schemas import JobCreate, JobOut
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


def _job_out(job: Job) -> JobOut:
    return JobOut(
        id=job.id,
        name=job.name,
        task_type=job.task_type,
        status=job.status.value,
        payload_json=job.payload_json,
        result_json=job.result_json,
        error_message=job.error_message,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        queued_at=job.queued_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _translate_job_error(error: Exception) -> HTTPException:
    if isinstance(error, JobNotFound):
        return HTTPException(status_code=404, detail="Job not found")
    if isinstance(error, TaskHandlerNotFound):
        return HTTPException(status_code=404, detail="Task handler not found")
    if isinstance(error, JobAttemptsExhausted):
        return HTTPException(status_code=409, detail="Job attempts exhausted")
    if isinstance(error, InvalidJobState):
        return HTTPException(status_code=409, detail="Invalid job state")
    return HTTPException(status_code=500, detail="Job execution failed")


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


@router.post("/jobs", response_model=JobOut)
def enqueue_job(
    payload: JobCreate,
    jobs: JobUseCases = Depends(get_job_use_cases),
    user: User = Depends(current_user),
) -> JobOut:
    return _job_out(jobs.enqueue_task(EnqueueTaskCommand(payload.task_type, payload.payload, payload.max_attempts), user.id))


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(
    jobs: JobUseCases = Depends(get_job_use_cases),
    user: User = Depends(current_user),
) -> list[JobOut]:
    _ = user
    return [_job_out(job) for job in jobs.list_jobs()]


@router.post("/jobs/execute-next", response_model=JobOut)
def execute_next_job(
    jobs: JobUseCases = Depends(get_job_use_cases),
    user: User = Depends(current_user),
) -> JobOut:
    try:
        return _job_out(jobs.execute_next_queued_job(user.id))
    except Exception as error:
        raise _translate_job_error(error)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    jobs: JobUseCases = Depends(get_job_use_cases),
    user: User = Depends(current_user),
) -> JobOut:
    _ = user
    try:
        return _job_out(jobs.get_job(job_id))
    except Exception as error:
        raise _translate_job_error(error)


@router.post("/jobs/{job_id}/execute", response_model=JobOut)
def execute_job(
    job_id: int,
    jobs: JobUseCases = Depends(get_job_use_cases),
    user: User = Depends(current_user),
) -> JobOut:
    try:
        return _job_out(jobs.execute_job(job_id, user.id))
    except Exception as error:
        raise _translate_job_error(error)


@router.post("/jobs/{job_id}/retry", response_model=JobOut)
def retry_job(
    job_id: int,
    jobs: JobUseCases = Depends(get_job_use_cases),
    user: User = Depends(current_user),
) -> JobOut:
    try:
        return _job_out(jobs.retry_failed_job(job_id, user.id))
    except Exception as error:
        raise _translate_job_error(error)


@router.post("/jobs/{job_id}/cancel", response_model=JobOut)
def cancel_job(
    job_id: int,
    jobs: JobUseCases = Depends(get_job_use_cases),
    user: User = Depends(current_user),
) -> JobOut:
    try:
        return _job_out(jobs.cancel_queued_job(job_id, user.id))
    except Exception as error:
        raise _translate_job_error(error)
