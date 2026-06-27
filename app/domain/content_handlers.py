from typing import Protocol


class ContentTypeHandler(Protocol):
    content_type: str

    def normalize_content_type(self, requested_content_type: str, mime_type: str | None, original_filename: str) -> str:
        ...


class GenericContentTypeHandler:
    content_type = "*"

    def normalize_content_type(self, requested_content_type: str, mime_type: str | None, original_filename: str) -> str:
        return requested_content_type or "document"


class ContentTypeHandlerRegistry:
    def __init__(self, fallback: ContentTypeHandler | None = None):
        self._handlers: dict[str, ContentTypeHandler] = {}
        self._fallback = fallback or GenericContentTypeHandler()

    def register(self, handler: ContentTypeHandler) -> None:
        self._handlers[handler.content_type] = handler

    def get(self, content_type: str) -> ContentTypeHandler:
        return self._handlers.get(content_type, self._fallback)
