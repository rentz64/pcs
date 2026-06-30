from email.parser import BytesParser
from email.policy import default
from email.utils import parsedate_to_datetime
from io import BytesIO
from typing import BinaryIO, Iterator

from app.domain.email import EmailPayload


def iter_mbox_payloads(stream: BinaryIO) -> Iterator[EmailPayload]:
    buffer = BytesIO()
    for line in stream:
        if line.startswith(b"From ") and buffer.tell() > 0:
            yield _parse_message(buffer.getvalue())
            buffer = BytesIO()
            continue
        if not line.startswith(b"From "):
            buffer.write(line)
    if buffer.tell() > 0:
        yield _parse_message(buffer.getvalue())


def _parse_message(data: bytes) -> EmailPayload:
    message = BytesParser(policy=default).parsebytes(data)
    message_id = (message.get("Message-ID") or "").strip().strip("<>")
    subject = str(message.get("Subject") or "(no subject)")
    sender = str(message.get("From") or "unknown")
    recipients_to = tuple(_split_addresses(str(message.get("To") or "")))
    recipients_cc = tuple(_split_addresses(str(message.get("Cc") or "")))
    date_header = message.get("Date")
    parsed_date = parsedate_to_datetime(date_header) if date_header else None
    body = ""
    html_body = None
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and not body:
                body = str(part.get_content())
            elif content_type == "text/html" and html_body is None:
                html_body = str(part.get_content())
    else:
        content = message.get_content()
        if message.get_content_type() == "text/html":
            html_body = str(content)
        else:
            body = str(content)
    external_id = message_id or f"mbox:{abs(hash(data))}"
    return EmailPayload(
        external_message_id=external_id,
        message_id_header=message_id or None,
        thread_id=None,
        subject=subject,
        sender=sender,
        recipients_to=recipients_to,
        recipients_cc=recipients_cc,
        recipients_bcc=(),
        sent_at=parsed_date,
        received_at=parsed_date,
        folder="takeout",
        labels=("takeout",),
        text_body=body,
        html_body=html_body,
    )


def _split_addresses(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]
