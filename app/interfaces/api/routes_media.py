from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.application.dto import UploadMediaCommand
from app.application.media_use_cases import MediaUseCases
from app.domain.entities import User
from app.domain.errors import InvalidMediaType, MediaItemNotFound, StoredObjectNotFound
from app.domain.media import MediaItem
from app.interfaces.api.dependencies import current_user, get_media_use_cases
from app.interfaces.api.schemas import MediaOut

router = APIRouter(prefix="/media")


def _out(item: MediaItem) -> MediaOut:
    return MediaOut(
        id=item.id,
        content_item_id=item.content_item.id,
        title=item.content_item.title,
        description=item.content_item.description,
        media_type=item.media_type.value,
        original_filename=item.original_filename,
        mime_type=item.mime_type,
        size_bytes=item.size_bytes,
        width=item.width,
        height=item.height,
        duration_seconds=item.duration_seconds,
        tags=item.content_item.tags,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("", response_model=MediaOut)
def upload_media(
    title: str = Form(...),
    description: str | None = Form(None),
    tags: str = Form(""),
    file: UploadFile = File(...),
    media: MediaUseCases = Depends(get_media_use_cases),
    user: User = Depends(current_user),
) -> MediaOut:
    try:
        return _out(
            media.upload(
                user,
                UploadMediaCommand(
                    title=title,
                    description=description,
                    tags=tags,
                    original_filename=file.filename or "uploaded.bin",
                    mime_type=file.content_type or "",
                    content=file.file,
                ),
            )
        )
    except InvalidMediaType:
        raise HTTPException(status_code=400, detail="Unsupported media type")


@router.get("", response_model=list[MediaOut])
def list_media(
    q: str = "",
    media: MediaUseCases = Depends(get_media_use_cases),
    user: User = Depends(current_user),
) -> list[MediaOut]:
    items = media.search_media(user, q) if q else media.list_media(user)
    return [_out(item) for item in items]


@router.get("/{media_id}", response_model=MediaOut)
def get_media(
    media_id: int,
    media: MediaUseCases = Depends(get_media_use_cases),
    user: User = Depends(current_user),
) -> MediaOut:
    try:
        return _out(media.get_media(user, media_id))
    except MediaItemNotFound:
        raise HTTPException(status_code=404, detail="Media item not found")


@router.get("/{media_id}/download")
def download_media(
    media_id: int,
    media: MediaUseCases = Depends(get_media_use_cases),
    user: User = Depends(current_user),
) -> FileResponse:
    try:
        download = media.prepare_download(user, media_id)
    except MediaItemNotFound:
        raise HTTPException(status_code=404, detail="Media item not found")
    except StoredObjectNotFound:
        raise HTTPException(status_code=404, detail="Stored object not found")
    return FileResponse(download.path, media_type=download.item.mime_type, filename=download.item.original_filename)
