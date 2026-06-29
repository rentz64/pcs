from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


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
    payload: dict[str, str] = field(default_factory=dict)
    result: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
