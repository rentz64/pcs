from dataclasses import replace
from datetime import datetime, timezone

from app.application.dto import CreateJobCommand, EnqueueTaskCommand
from app.domain.entities import AuditEntry
from app.domain.errors import InvalidJobState, JobAttemptsExhausted, JobNotFound
from app.domain.events import ApplicationEvent, EventPublisher
from app.domain.jobs import Job, JobStatus
from app.domain.repositories import AuditRepository, JobRepository
from app.domain.tasks import TaskExecutionContext, TaskRegistry, build_default_task_registry


class JobUseCases:
    def __init__(self, jobs: JobRepository, events: EventPublisher, tasks: TaskRegistry | None = None, audits: AuditRepository | None = None):
        self.jobs = jobs
        self.events = events
        self.tasks = tasks or build_default_task_registry()
        self.audits = audits

    def create_job(self, command: CreateJobCommand) -> Job:
        now = datetime.now(timezone.utc)
        payload = command.payload or {}
        job = self.jobs.add(
            Job(
                id=None,
                name=command.name,
                task_type=command.name,
                payload=payload,
                payload_json=payload,
                queued_at=now,
            )
        )
        self._publish("job.created", job)
        return job

    def enqueue_task(self, command: EnqueueTaskCommand, user_id: int | None = None) -> Job:
        now = datetime.now(timezone.utc)
        max_attempts = max(1, command.max_attempts)
        job = self.jobs.add(
            Job(
                id=None,
                name=command.task_type,
                task_type=command.task_type,
                payload_json=command.payload or {},
                max_attempts=max_attempts,
                queued_at=now,
            )
        )
        self._publish("job.queued", job)
        self._audit(user_id, "job_queued", job, None)
        return job

    def list_jobs(self) -> list[Job]:
        return self.jobs.list()

    def get_job(self, job_id: int) -> Job:
        job = self.jobs.get(job_id)
        if not job:
            raise JobNotFound()
        return job

    def mark_running(self, job_id: int) -> Job:
        existing = self.get_job(job_id)
        if existing.status is not JobStatus.QUEUED:
            raise InvalidJobState()
        job = self._mark(job_id, JobStatus.RUNNING, started_at=datetime.now(timezone.utc), attempts=existing.attempts + 1)
        self._publish("job.running", job)
        return job

    def mark_succeeded(self, job_id: int, result: str | None = None) -> Job:
        job = self._mark(job_id, JobStatus.SUCCEEDED, result=result, error_message=None)
        self._publish("job.succeeded", job)
        return job

    def mark_failed(self, job_id: int, error_message: str) -> Job:
        job = self._mark(job_id, JobStatus.FAILED, error_message=error_message)
        self._publish("job.failed", job)
        return job

    def execute_next_queued_job(self, user_id: int | None = None) -> Job:
        job = self.jobs.next_queued()
        if not job:
            raise JobNotFound()
        return self.execute_job(job.id, user_id)

    def execute_job(self, job_id: int, user_id: int | None = None) -> Job:
        job = self.get_job(job_id)
        if job.status is not JobStatus.QUEUED:
            raise InvalidJobState()
        handler = self.tasks.get(job.task_type)
        running = self._mark(job.id, JobStatus.RUNNING, started_at=datetime.now(timezone.utc), attempts=job.attempts + 1)
        self._publish("job.started", running)
        self._audit(user_id, "job_started", running, None)
        result = handler(TaskExecutionContext(job_id=running.id, task_type=running.task_type, payload=running.payload_json))
        completed_at = datetime.now(timezone.utc)
        if result.success:
            succeeded = self._mark(
                running.id,
                JobStatus.SUCCEEDED,
                result_json=result.result,
                result=str(result.result),
                error_message=None,
                completed_at=completed_at,
            )
            self._publish("job.succeeded", succeeded)
            self._audit(user_id, "job_succeeded", succeeded, None)
            return succeeded
        failed = self._mark(
            running.id,
            JobStatus.FAILED,
            result_json=result.result,
            error_message=result.error_message or "Task failed",
            completed_at=completed_at,
        )
        self._publish("job.failed", failed)
        self._audit(user_id, "job_failed", failed, failed.error_message)
        return failed

    def retry_failed_job(self, job_id: int, user_id: int | None = None) -> Job:
        job = self.get_job(job_id)
        if job.status is not JobStatus.FAILED:
            raise InvalidJobState()
        if job.attempts >= job.max_attempts:
            raise JobAttemptsExhausted()
        retried = self.jobs.update(
            replace(
                job,
                status=JobStatus.QUEUED,
                error_message=None,
                result_json=None,
                result=None,
                queued_at=datetime.now(timezone.utc),
                started_at=None,
                completed_at=None,
                updated_at=datetime.now(timezone.utc),
            )
        )
        self._publish("job.retried", retried)
        self._audit(user_id, "job_retried", retried, None)
        return retried

    def cancel_queued_job(self, job_id: int, user_id: int | None = None) -> Job:
        job = self.get_job(job_id)
        if job.status is not JobStatus.QUEUED:
            raise InvalidJobState()
        cancelled = self._mark(job.id, JobStatus.CANCELLED, completed_at=datetime.now(timezone.utc))
        self._publish("job.cancelled", cancelled)
        self._audit(user_id, "job_cancelled", cancelled, None)
        return cancelled

    def count_by_status(self) -> dict[JobStatus, int]:
        return self.jobs.count_by_status()

    def _mark(
        self,
        job_id: int,
        status: JobStatus,
        result: str | None = None,
        result_json: dict[str, object] | None = None,
        error_message: str | None = None,
        attempts: int | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> Job:
        job = self.get_job(job_id)
        return self.jobs.update(
            replace(
                job,
                status=status,
                attempts=attempts if attempts is not None else job.attempts,
                result=result if result is not None else job.result,
                result_json=result_json if result_json is not None else job.result_json,
                error_message=error_message,
                started_at=started_at if started_at is not None else job.started_at,
                completed_at=completed_at if completed_at is not None else job.completed_at,
                updated_at=datetime.now(timezone.utc),
            )
        )

    def _publish(self, name: str, job: Job) -> None:
        self.events.publish(
            ApplicationEvent(
                name=name,
                payload={"job_id": job.id, "job_name": job.name, "task_type": job.task_type, "status": job.status.value},
            )
        )

    def _audit(self, user_id: int | None, action: str, job: Job, details: str | None) -> None:
        if not self.audits:
            return
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user_id,
                action=action,
                entity_type="job",
                entity_id=str(job.id) if job.id is not None else None,
                details=details,
            )
        )
