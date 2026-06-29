from app.domain.events import ApplicationEvent


class InProcessEventPublisher:
    def __init__(self):
        self.events: list[ApplicationEvent] = []

    def publish(self, event: ApplicationEvent) -> None:
        self.events.append(event)
