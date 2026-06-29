from app.domain.events import ApplicationEvent
from app.infrastructure.events import InProcessEventPublisher


def test_in_process_event_publisher_records_events_in_order():
    publisher = InProcessEventPublisher()
    first = ApplicationEvent(name="job.created", payload={"job_id": 1})
    second = ApplicationEvent(name="job.running", payload={"job_id": 1})

    publisher.publish(first)
    publisher.publish(second)

    assert publisher.events == [first, second]
