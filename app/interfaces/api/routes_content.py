from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.application.content_use_cases import ContentUseCases
from app.application.dto import UploadContentCommand
from app.domain.entities import ContentItem, User
from app.domain.errors import ContentNotFound, StoredObjectNotFound
from app.interfaces.api.dependencies import current_user, get_content_use_cases
from app.interfaces.api.schemas import ContentOut

router = APIRouter()


@router.post("/content", response_model=ContentOut)
def upload_content(
    title: str = Form(...),
    content_type: str = Form("document"),
    description: str | None = Form(None),
    tags: str = Form(""),
    file: UploadFile = File(...),
    content: ContentUseCases = Depends(get_content_use_cases),
    user: User = Depends(current_user),
) -> ContentItem:
    return content.upload(
        user,
        UploadContentCommand(
            title=title,
            content_type=content_type,
            description=description,
            tags=tags,
            original_filename=file.filename or "uploaded.bin",
            mime_type=file.content_type,
            content=file.file,
        ),
    )


@router.get("/content", response_model=list[ContentOut])
def list_content(
    content: ContentUseCases = Depends(get_content_use_cases),
    user: User = Depends(current_user),
) -> list[ContentItem]:
    return content.list_for_user(user)


@router.get("/content/search", response_model=list[ContentOut])
def search_content(
    q: str = "",
    content: ContentUseCases = Depends(get_content_use_cases),
    user: User = Depends(current_user),
) -> list[ContentItem]:
    return content.search_for_user(user, q)


@router.get("/content/{content_id}/download")
def download_content(
    content_id: int,
    content: ContentUseCases = Depends(get_content_use_cases),
    user: User = Depends(current_user),
) -> FileResponse:
    try:
        download = content.prepare_download(user, content_id)
    except ContentNotFound:
        raise HTTPException(status_code=404, detail="Content not found")
    except StoredObjectNotFound:
        raise HTTPException(status_code=404, detail="Stored object not found")
    return FileResponse(download.path, media_type=download.item.mime_type, filename=download.item.original_filename)

