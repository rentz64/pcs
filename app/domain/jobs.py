from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.domain.tasks import JsonObject


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Job:
    id: int | None
    name: str
    status: JobStatus = JobStatus.QUEUED
    task_type: str = "system.noop"
    payload_json: JsonObject = field(default_factory=dict)
    result_json: JsonObject | None = None
    error_message: str | None = None
    attempts: int = 0
    max_attempts: int = 1
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    payload: dict[str, str] = field(default_factory=dict)
    result: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
