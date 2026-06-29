from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class ApplicationEvent:
    name: str
    payload: dict[str, str | int | float | bool | None] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventPublisher(Protocol):
    def publish(self, event: ApplicationEvent) -> None:
        ...
