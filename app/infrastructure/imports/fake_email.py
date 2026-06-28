from datetime import datetime, timezone

from app.domain.email import EmailPayload


class FakeEmailImportAdapter:
    def import_message(self, malformed: bool = False) -> EmailPayload:
        subject = "" if malformed else "Fake Email"
        return EmailPayload(
            external_message_id="fake-message-1",
            message_id_header="<fake-message-1@example.test>",
            thread_id="fake-thread-1",
            subject=subject,
            sender="sender@example.test",
            recipients_to=("owner@example.test",),
            recipients_cc=(),
            recipients_bcc=(),
            sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            folder="Inbox",
            labels=("inbox", "fake"),
            text_body="Fake email body",
            html_body=None,
            attachments=(("fake.txt", "text/plain", b"fake attachment"),),
        )
