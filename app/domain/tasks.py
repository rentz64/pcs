from collections.abc import Callable
from dataclasses import dataclass, field

from app.domain.errors import TaskHandlerNotFound


JsonValue = str | int | float | bool | None | dict[str, "JsonValue"] | list["JsonValue"]
JsonObject = dict[str, JsonValue]


@dataclass(frozen=True)
class TaskDefinition:
    task_type: str
    description: str = ""


@dataclass(frozen=True)
class TaskExecutionContext:
    job_id: int
    task_type: str
    payload: JsonObject = field(default_factory=dict)


@dataclass(frozen=True)
class TaskExecutionResult:
    success: bool
    result: JsonObject = field(default_factory=dict)
    error_message: str | None = None

    @classmethod
    def succeeded(cls, result: JsonObject | None = None) -> "TaskExecutionResult":
        return cls(success=True, result=result or {})

    @classmethod
    def failed(cls, error_message: str, result: JsonObject | None = None) -> "TaskExecutionResult":
        return cls(success=False, result=result or {}, error_message=error_message)


TaskHandler = Callable[[TaskExecutionContext], TaskExecutionResult]


class TaskRegistry:
    def __init__(self):
        self._handlers: dict[str, TaskHandler] = {}
        self._definitions: dict[str, TaskDefinition] = {}

    def register(self, task_type: str, handler: TaskHandler, description: str = "") -> None:
        self._handlers[task_type] = handler
        self._definitions[task_type] = TaskDefinition(task_type=task_type, description=description)

    def get(self, task_type: str) -> TaskHandler:
        handler = self._handlers.get(task_type)
        if not handler:
            raise TaskHandlerNotFound()
        return handler

    def task_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))


def noop_task(context: TaskExecutionContext) -> TaskExecutionResult:
    return TaskExecutionResult.succeeded({"ok": True, "task": context.task_type})


def failing_task(context: TaskExecutionContext) -> TaskExecutionResult:
    message = context.payload.get("message")
    return TaskExecutionResult.failed(str(message or "Task failed"))


def content_reindex_placeholder_task(context: TaskExecutionContext) -> TaskExecutionResult:
    return TaskExecutionResult.succeeded({"ok": True, "task": context.task_type, "indexed": 0})


def import_job_placeholder_task(context: TaskExecutionContext) -> TaskExecutionResult:
    return TaskExecutionResult.succeeded({"ok": True, "task": context.task_type, "imported": 0})


def build_default_task_registry() -> TaskRegistry:
    registry = TaskRegistry()
    registry.register("system.noop", noop_task, "No-op task for smoke tests")
    registry.register("system.fail", failing_task, "Failing task for error-path tests")
    registry.register("content.reindex", content_reindex_placeholder_task, "Placeholder content reindex task")
    registry.register("imports.placeholder", import_job_placeholder_task, "Placeholder import task")
    return registry
