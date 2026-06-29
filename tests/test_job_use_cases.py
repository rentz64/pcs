from dataclasses import replace

import pytest

from app.application.dto import CreateJobCommand
from app.application.job_use_cases import JobUseCases
from app.domain.errors import JobNotFound
from app.domain.events import ApplicationEvent
from app.domain.jobs import Job, JobStatus


class FakeJobs:
    def __init__(self):
        self.jobs: list[Job] = []

    def add(self, job: Job) -> Job:
        saved = replace(job, id=len(self.jobs) + 1)
        self.jobs.append(saved)
        return saved

    def update(self, job: Job) -> Job:
        for index, existing in enumerate(self.jobs):
            if existing.id == job.id:
                self.jobs[index] = job
                return job
        raise ValueError("Job not found")

    def list(self) -> list[Job]:
        return list(self.jobs)

    def get(self, job_id: int) -> Job | None:
        return next((job for job in self.jobs if job.id == job_id), None)

    def count_by_status(self) -> dict[JobStatus, int]:
        counts = {status: 0 for status in JobStatus}
        for job in self.jobs:
            counts[job.status] += 1
        return counts


class FakeEvents:
    def __init__(self):
        self.events: list[ApplicationEvent] = []

    def publish(self, event: ApplicationEvent) -> None:
        self.events.append(event)


def test_create_list_and_get_job():
    jobs = FakeJobs()
    events = FakeEvents()
    use_cases = JobUseCases(jobs, events)

    job = use_cases.create_job(CreateJobCommand(name="thumbnail-build", payload={"content_id": "7"}))

    assert job.id == 1
    assert job.status is JobStatus.QUEUED
    assert use_cases.list_jobs() == [job]
    assert use_cases.get_job(1) == job
    assert events.events[0].name == "job.created"


def test_job_lifecycle_transitions_publish_events():
    jobs = FakeJobs()
    events = FakeEvents()
    use_cases = JobUseCases(jobs, events)
    job = use_cases.create_job(CreateJobCommand(name="import-preview"))

    running = use_cases.mark_running(job.id)
    succeeded = use_cases.mark_succeeded(job.id, result="done")

    assert running.status is JobStatus.RUNNING
    assert succeeded.status is JobStatus.SUCCEEDED
    assert succeeded.result == "done"
    assert [event.name for event in events.events] == ["job.created", "job.running", "job.succeeded"]


def test_mark_failed_records_error_message():
    use_cases = JobUseCases(FakeJobs(), FakeEvents())
    job = use_cases.create_job(CreateJobCommand(name="broken"))

    failed = use_cases.mark_failed(job.id, "boom")

    assert failed.status is JobStatus.FAILED
    assert failed.error_message == "boom"


def test_get_job_raises_for_missing_job():
    use_cases = JobUseCases(FakeJobs(), FakeEvents())

    with pytest.raises(JobNotFound):
        use_cases.get_job(999)
