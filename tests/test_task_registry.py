import pytest

from app.domain.errors import TaskHandlerNotFound
from app.domain.tasks import TaskExecutionContext, TaskExecutionResult, TaskRegistry


def test_task_registry_registers_and_resolves_handlers():
    registry = TaskRegistry()

    def handler(context: TaskExecutionContext) -> TaskExecutionResult:
        return TaskExecutionResult.succeeded({"seen": context.payload["value"]})

    registry.register("demo.echo", handler)

    result = registry.get("demo.echo")(TaskExecutionContext(job_id=1, task_type="demo.echo", payload={"value": "ok"}))

    assert result.success is True
    assert result.result == {"seen": "ok"}
    assert registry.task_types() == ("demo.echo",)


def test_task_registry_raises_for_unknown_task_type():
    registry = TaskRegistry()

    with pytest.raises(TaskHandlerNotFound):
        registry.get("missing")
