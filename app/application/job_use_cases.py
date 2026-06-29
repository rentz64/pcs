from dataclasses import replace
from datetime import datetime, timezone

from app.application.dto import CreateJobCommand
from app.domain.errors import JobNotFound
from app.domain.events import ApplicationEvent, EventPublisher
from app.domain.jobs import Job, JobStatus
from app.domain.repositories import JobRepository


class JobUseCases:
    def __init__(self, jobs: JobRepository, events: EventPublisher):
        self.jobs = jobs
        self.events = events

    def create_job(self, command: CreateJobCommand) -> Job:
        job = self.jobs.add(Job(id=None, name=command.name, payload=command.payload or {}))
        self._publish("job.created", job)
        return job

    def list_jobs(self) -> list[Job]:
        return self.jobs.list()

    def get_job(self, job_id: int) -> Job:
        job = self.jobs.get(job_id)
        if not job:
            raise JobNotFound()
        return job

    def mark_running(self, job_id: int) -> Job:
        job = self._mark(job_id, JobStatus.RUNNING)
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

    def count_by_status(self) -> dict[JobStatus, int]:
        return self.jobs.count_by_status()

    def _mark(
        self,
        job_id: int,
        status: JobStatus,
        result: str | None = None,
        error_message: str | None = None,
    ) -> Job:
        job = self.get_job(job_id)
        return self.jobs.update(
            replace(
                job,
                status=status,
                result=result if result is not None else job.result,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
        )

    def _publish(self, name: str, job: Job) -> None:
        self.events.publish(ApplicationEvent(name=name, payload={"job_id": job.id, "job_name": job.name, "status": job.status.value}))
