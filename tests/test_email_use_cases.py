from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.application.email_use_cases import EmailUseCases
from app.domain.email import EmailAttachment, EmailMessage, EmailPayload
from app.domain.entities import User
from app.domain.errors import EmailAttachmentNotFound, EmailMessageNotFound, InvalidEmailPayload, StoredObjectNotFound
from app.domain.imports import ExternalAccount, ExternalSource, ImportBatch
from tests.test_import_use_cases import FakeAccounts, FakeBatches, FakeSources
from tests.test_use_cases import FakeAudit, FakeContent, FakeStorage


class FakeEmails:
    def __init__(self):
        self.messages: list[EmailMessage] = []
        self.attachments: list[EmailAttachment] = []

    def add(self, message: EmailMessage) -> EmailMessage:
        saved = replace(message, id=len(self.messages) + 1)
        self.messages.append(saved)
        return saved

    def get_for_owner(self, email_id: int, owner_id: int) -> EmailMessage | None:
        return next((message for message in self.messages if message.id == email_id and message.owner_id == owner_id), None)

    def get_by_external_message_id(self, owner_id: int, account_id: int, external_message_id: str) -> EmailMessage | None:
        return next(
            (
                message
                for message in self.messages
                if message.owner_id == owner_id
                and message.external_account_id == account_id
                and message.external_message_id == external_message_id
            ),
            None,
        )

    def list_for_owner(self, owner_id: int) -> list[EmailMessage]:
        return [message for message in self.messages if message.owner_id == owner_id]

    def search_for_owner(self, owner_id: int, query: str) -> list[EmailMessage]:
        lowered = query.lower()
        return [
            message
            for message in self.list_for_owner(owner_id)
            if lowered in message.subject.lower() or lowered in message.sender.lower() or lowered in message.text_body.lower()
        ]

    def add_attachment(self, attachment: EmailAttachment) -> EmailAttachment:
        saved = replace(attachment, id=len(self.attachments) + 1)
        self.attachments.append(saved)
        return saved

    def list_attachments_for_email(self, email_id: int, owner_id: int) -> list[EmailAttachment]:
        message = self.get_for_owner(email_id, owner_id)
        if not message:
            return []
        return [attachment for attachment in self.attachments if attachment.email_id == email_id]

    def get_attachment_for_owner(self, attachment_id: int, owner_id: int) -> EmailAttachment | None:
        return next(
            (
                attachment
                for attachment in self.attachments
                if attachment.id == attachment_id and self.get_for_owner(attachment.email_id, owner_id)
            ),
            None,
        )


def owner(user_id: int = 7) -> User:
    return User(id=user_id, username=f"user-{user_id}", password_hash="x", role="owner")


def payload() -> EmailPayload:
    return EmailPayload(
        external_message_id="msg-1",
        message_id_header="<msg-1@example.test>",
        thread_id="thread-1",
        subject="Hello Email",
        sender="sender@example.test",
        recipients_to=("to@example.test",),
        recipients_cc=(),
        recipients_bcc=(),
        sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        folder="Inbox",
        labels=("inbox",),
        text_body="Hello body",
        html_body=None,
        attachments=(("hello.txt", "text/plain", b"attachment"),),
    )


def make_use_cases():
    sources = FakeSources()
    accounts = FakeAccounts()
    batches = FakeBatches()
    emails = FakeEmails()
    content = FakeContent()
    audit = FakeAudit()
    storage = FakeStorage()
    source = sources.add(ExternalSource(None, owner_id=7, name="Fake Email", source_type="fake_email"))
    account = accounts.add(ExternalAccount(None, owner_id=7, source_id=source.id, name="Fake Account", external_account_ref="fake"))
    batch = batches.add(ImportBatch(None, owner_id=7, job_id=1, source_id=source.id, account_id=account.id))
    use_cases = EmailUseCases(emails, content, audit, storage)
    return use_cases, source, account, batch, emails, content, audit, storage


def test_import_email_creates_imported_content_message_attachment_and_audit():
    use_cases, source, account, batch, emails, content, audit, storage = make_use_cases()

    message = use_cases.import_email(owner(), source, account, batch, payload())

    assert message.content_item.origin == "imported"
    assert message.content_item.content_type == "email"
    assert message.external_message_id == "msg-1"
    assert message.has_attachments is True
    assert content.items[0] == message.content_item
    assert emails.attachments[0].filename == "hello.txt"
    assert emails.attachments[0].object_key in storage.saved
    assert audit.entries[0].action == "email_imported"


def test_duplicate_external_message_id_returns_existing_message_safely():
    use_cases, source, account, batch, *_ = make_use_cases()

    first = use_cases.import_email(owner(), source, account, batch, payload())
    second = use_cases.import_email(owner(), source, account, batch, payload())

    assert second.id == first.id


def test_malformed_email_payload_is_rejected():
    use_cases, source, account, batch, *_ = make_use_cases()
    bad = replace(payload(), subject="")

    with pytest.raises(InvalidEmailPayload):
        use_cases.import_email(owner(), source, account, batch, bad)


def test_email_owner_scoping_and_attachment_download_missing_object():
    use_cases, source, account, batch, emails, _, _, storage = make_use_cases()
    message = use_cases.import_email(owner(7), source, account, batch, payload())

    with pytest.raises(EmailMessageNotFound):
        use_cases.get_email(owner(8), message.id)

    attachments = use_cases.list_attachments(owner(7), message.id)
    storage.saved.clear()
    with pytest.raises(StoredObjectNotFound):
        use_cases.prepare_attachment_download(owner(7), attachments[0].id)

    with pytest.raises(EmailAttachmentNotFound):
        use_cases.prepare_attachment_download(owner(8), attachments[0].id)

