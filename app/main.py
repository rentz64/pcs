from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .audit import audit
from .config import settings
from .database import Base, engine, get_db
from .dependencies import current_user
from .models import AuditLog, ContentItem, User
from .schemas import ContentOut, LoginRequest, TokenResponse
from .security import authenticate_user, create_access_token, hash_password
from .storage import LocalObjectStorage

storage = LocalObjectStorage()


def init_db() -> None:
    Path("storage").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=hash_password("admin-change-me"), role="owner"))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise and cleanly release application resources.

    FastAPI's @app.on_event startup/shutdown hooks are deprecated.  The
    lifespan context keeps startup and shutdown behaviour in one place and
    gives us a clean location for future resource disposal.
    """
    init_db()
    try:
        yield
    finally:
        # Close pooled database connections explicitly. This is especially
        # important on Windows, where open SQLite handles can block file
        # deletion during test teardown or local maintenance operations.
        engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    audit(db, user.id, "login", "user", str(user.id))
    return TokenResponse(access_token=create_access_token(user.username))


@app.post("/content", response_model=ContentOut)
def upload_content(
    title: str = Form(...),
    content_type: str = Form("document"),
    description: str | None = Form(None),
    tags: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ContentItem:
    stored_name, size = storage.save_upload(file)
    item = ContentItem(
        owner_id=user.id,
        title=title,
        description=description,
        content_type=content_type,
        original_filename=file.filename or "uploaded.bin",
        stored_filename=stored_name,
        mime_type=file.content_type,
        size_bytes=size,
        tags=tags,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    audit(db, user.id, "content_uploaded", "content_item", str(item.id), item.original_filename)
    return item


@app.get("/content", response_model=list[ContentOut])
def list_content(db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[ContentItem]:
    return (
        db.query(ContentItem)
        .filter(ContentItem.owner_id == user.id)
        .order_by(ContentItem.created_at.desc())
        .all()
    )


@app.get("/content/search", response_model=list[ContentOut])
def search_content(q: str = "", db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[ContentItem]:
    pattern = f"%{q}%"
    return (
        db.query(ContentItem)
        .filter(ContentItem.owner_id == user.id)
        .filter(
            or_(
                ContentItem.title.ilike(pattern),
                ContentItem.description.ilike(pattern),
                ContentItem.original_filename.ilike(pattern),
                ContentItem.tags.ilike(pattern),
                ContentItem.content_type.ilike(pattern),
            )
        )
        .order_by(ContentItem.created_at.desc())
        .all()
    )


@app.get("/content/{content_id}/download")
def download_content(content_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)) -> FileResponse:
    item = db.query(ContentItem).filter(ContentItem.id == content_id, ContentItem.owner_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    path = storage.path_for(item.stored_filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored object not found")
    audit(db, user.id, "content_downloaded", "content_item", str(item.id), item.original_filename)
    return FileResponse(path, media_type=item.mime_type, filename=item.original_filename)


@app.get("/audit")
def list_audit(db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[dict]:
    rows = db.query(AuditLog).filter(AuditLog.user_id == user.id).order_by(AuditLog.created_at.desc()).limit(100).all()
    return [
        {"action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "created_at": row.created_at.isoformat()}
        for row in rows
    ]
