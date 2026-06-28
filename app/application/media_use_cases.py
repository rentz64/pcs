from app.application.dto import DownloadContent, UploadMediaCommand
from app.domain.entities import AuditEntry, ContentItem, User
from app.domain.errors import InvalidMediaType, MediaItemNotFound, StoredObjectNotFound
from app.domain.media import MediaItem, MediaType
from app.domain.repositories import AuditRepository, ContentRepository, MediaRepository, ObjectStorage


IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
VIDEO_MIME_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


class MediaUseCases:
    def __init__(
        self,
        media: MediaRepository,
        content: ContentRepository,
        audits: AuditRepository,
        storage: ObjectStorage,
    ):
        self.media = media
        self.content = content
        self.audits = audits
        self.storage = storage

    def upload(self, user: User, command: UploadMediaCommand) -> MediaItem:
        media_type = self._media_type(command.mime_type)
        stored_name, size = self.storage.save(command.original_filename, command.content)
        content_item = self.content.add(
            ContentItem(
                id=None,
                owner_id=user.id,
                title=command.title,
                description=command.description,
                content_type=media_type.value,
                original_filename=command.original_filename,
                stored_filename=stored_name,
                mime_type=command.mime_type,
                size_bytes=size,
                tags=command.tags,
            )
        )
        item = self.media.add(
            MediaItem(
                id=None,
                owner_id=user.id,
                content_item=content_item,
                media_type=media_type,
                original_filename=command.original_filename,
                mime_type=command.mime_type,
                size_bytes=size,
            )
        )
        self._audit(user.id, "media_uploaded", item.id, item.original_filename)
        return item

    def get_media(self, user: User, media_id: int) -> MediaItem:
        item = self.media.get_for_owner(media_id, user.id)
        if not item:
            raise MediaItemNotFound()
        return item

    def list_media(self, user: User) -> list[MediaItem]:
        return self.media.list_for_owner(user.id)

    def search_media(self, user: User, query: str) -> list[MediaItem]:
        return self.media.search_for_owner(user.id, query)

    def prepare_download(self, user: User, media_id: int) -> DownloadContent:
        item = self.get_media(user, media_id)
        if not self.storage.exists(item.content_item.stored_filename):
            raise StoredObjectNotFound()
        self._audit(user.id, "media_downloaded", item.id, item.original_filename)
        return DownloadContent(item=item.content_item, path=self.storage.path_for(item.content_item.stored_filename))

    def _media_type(self, mime_type: str) -> MediaType:
        if mime_type in IMAGE_MIME_TYPES:
            return MediaType.IMAGE
        if mime_type in VIDEO_MIME_TYPES:
            return MediaType.VIDEO
        raise InvalidMediaType("Unsupported media type")

    def _audit(self, user_id: int | None, action: str, media_id: int | None, details: str | None) -> None:
        self.audits.add(
            AuditEntry(
                id=None,
                user_id=user_id,
                action=action,
                entity_type="media_item",
                entity_id=str(media_id) if media_id is not None else None,
                details=details,
            )
        )
