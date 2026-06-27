from app.application.dto import DownloadContent, UploadContentCommand
from app.domain.content_handlers import ContentTypeHandlerRegistry
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import ContentNotFound, StoredObjectNotFound
from app.domain.repositories import AuditRepository, ContentRepository, ContentSearch, ObjectStorage, SearchQuery


class ContentUseCases:
    def __init__(
        self,
        content: ContentRepository,
        audits: AuditRepository,
        storage: ObjectStorage,
        search: ContentSearch | None = None,
        handlers: ContentTypeHandlerRegistry | None = None,
    ):
        self.content = content
        self.audits = audits
        self.storage = storage
        self.search = search
        self.handlers = handlers or ContentTypeHandlerRegistry()

    def upload(self, user: User, command: UploadContentCommand) -> ContentItem:
        stored_name, size = self.storage.save(command.original_filename, command.content)
        handler = self.handlers.get(command.content_type)
        content_type = handler.normalize_content_type(command.content_type, command.mime_type, command.original_filename)
        item = self.content.add(
            ContentItem(
                id=None,
                owner_id=user.id,
                title=command.title,
                description=command.description,
                content_type=content_type,
                original_filename=command.original_filename,
                stored_filename=stored_name,
                mime_type=command.mime_type,
                size_bytes=size,
                tags=command.tags,
            )
        )
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user.id,
                action="content_uploaded",
                entity_type="content_item",
                entity_id=str(item.id),
                details=item.original_filename,
            )
        )
        return item

    def list_for_user(self, user: User) -> list[ContentItem]:
        return self.content.list_for_owner(user.id)

    def search_for_user(self, user: User, query: str) -> list[ContentItem]:
        if self.search:
            return self.search.search(SearchQuery(owner_id=user.id, text=query))
        return self.content.search_for_owner(user.id, query)

    def prepare_download(self, user: User, content_id: int) -> DownloadContent:
        item = self.content.get_for_owner(content_id, user.id)
        if not item:
            raise ContentNotFound()
        if not self.storage.exists(item.stored_filename):
            raise StoredObjectNotFound()
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user.id,
                action="content_downloaded",
                entity_type="content_item",
                entity_id=str(item.id),
                details=item.original_filename,
            )
        )
        return DownloadContent(item=item, path=self.storage.path_for(item.stored_filename))
