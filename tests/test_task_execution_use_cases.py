from dataclasses import replace

import pytest

from app.application.dto import EnqueueTaskCommand
from app.application.job_use_cases import JobUseCases
from app.domain.errors import InvalidJobState, JobAttemptsExhausted, JobNotFound, TaskHandlerNotFound
from app.domain.events import ApplicationEvent
from app.domain.jobs import Job, JobStatus
from app.domain.tasks import build_default_task_registry


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

    def next_queued(self) -> Job | None:
        return next((job for job in self.jobs if job.status is JobStatus.QUEUED), None)

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


def make_use_cases() -> tuple[JobUseCases, FakeEvents]:
    events = FakeEvents()
    return JobUseCases(FakeJobs(), events, build_default_task_registry()), events


def test_enqueue_and_execute_noop_task_succeeds_with_timestamps():
    use_cases, events = make_use_cases()
    job = use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.noop", payload={"message": "hello"}))

    executed = use_cases.execute_job(job.id)

    assert executed.status is JobStatus.SUCCEEDED
    assert executed.task_type == "system.noop"
    assert executed.payload_json == {"message": "hello"}
    assert executed.result_json == {"ok": True, "task": "system.noop"}
    assert executed.attempts == 1
    assert executed.queued_at is not None
    assert executed.started_at is not None
    assert executed.completed_at is not None
    assert [event.name for event in events.events] == ["job.queued", "job.started", "job.succeeded"]


def test_execute_next_runs_oldest_queued_job():
    use_cases, _ = make_use_cases()
    first = use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.noop"))
    use_cases.enqueue_task(EnqueueTaskCommand(task_type="content.reindex"))

    executed = use_cases.execute_next_queued_job()

    assert executed.id == first.id
    assert executed.status is JobStatus.SUCCEEDED


def test_failing_task_records_failure_and_error():
    use_cases, events = make_use_cases()
    job = use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.fail", payload={"message": "expected failure"}))

    failed = use_cases.execute_job(job.id)

    assert failed.status is JobStatus.FAILED
    assert failed.error_message == "expected failure"
    assert failed.attempts == 1
    assert events.events[-1].name == "job.failed"


def test_state_rules_prevent_restarting_succeeded_running_and_cancelled_jobs():
    use_cases, _ = make_use_cases()
    succeeded = use_cases.execute_job(use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.noop")).id)
    running = use_cases.mark_running(use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.noop")).id)
    cancelled = use_cases.cancel_queued_job(use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.noop")).id)

    with pytest.raises(InvalidJobState):
        use_cases.execute_job(succeeded.id)
    with pytest.raises(InvalidJobState):
        use_cases.execute_job(running.id)
    with pytest.raises(InvalidJobState):
        use_cases.execute_job(cancelled.id)


def test_retry_failed_job_until_max_attempts():
    use_cases, events = make_use_cases()
    job = use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.fail", max_attempts=2))
    failed = use_cases.execute_job(job.id)

    retried = use_cases.retry_failed_job(failed.id)

    assert retried.status is JobStatus.QUEUED
    assert retried.attempts == 1
    assert retried.error_message is None
    assert events.events[-1].name == "job.retried"

    failed_again = use_cases.execute_job(retried.id)
    with pytest.raises(JobAttemptsExhausted):
        use_cases.retry_failed_job(failed_again.id)


def test_retry_requires_failed_job_and_cancel_requires_queued_job():
    use_cases, _ = make_use_cases()
    queued = use_cases.enqueue_task(EnqueueTaskCommand(task_type="system.noop"))
    succeeded = use_cases.execute_job(queued.id)

    with pytest.raises(InvalidJobState):
        use_cases.retry_failed_job(succeeded.id)
    with pytest.raises(InvalidJobState):
        use_cases.cancel_queued_job(succeeded.id)


def test_execute_missing_or_unknown_task_fails_predictably():
    use_cases, _ = make_use_cases()

    with pytest.raises(JobNotFound):
        use_cases.execute_job(999)

    job = use_cases.enqueue_task(EnqueueTaskCommand(task_type="missing.task"))
    with pytest.raises(TaskHandlerNotFound):
        use_cases.execute_job(job.id)
