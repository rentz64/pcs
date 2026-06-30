from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.config import settings
from app.domain.entities import User
from app.infrastructure.db import orm_models
from app.infrastructure.db.repositories import SqlAlchemyUserRepository
from app.infrastructure.db.session import SessionLocal, create_schema, engine
from app.infrastructure.security.password import Pbkdf2PasswordHasher
from app.interfaces.api.routes_audit import router as audit_router
from app.interfaces.api.routes_archive_import import router as archive_import_router
from app.interfaces.api.routes_auth import router as auth_router
from app.interfaces.api.routes_blog import router as blog_router
from app.interfaces.api.routes_content import router as content_router
from app.interfaces.api.routes_email import router as email_router
from app.interfaces.api.routes_imports import router as imports_router
from app.interfaces.api.routes_media import router as media_router
from app.interfaces.api.routes_system import router as system_router
from app.interfaces.api.routes_travel import router as travel_router


def init_db() -> None:
    Path("storage").mkdir(exist_ok=True)
    create_schema()
    db = SessionLocal()
    try:
        users = SqlAlchemyUserRepository(db)
        if not users.get_by_username("admin"):
            password_hash = Pbkdf2PasswordHasher().hash("admin-change-me")
            users.add(User(id=None, username="admin", password_hash=password_hash, role="owner"))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise and cleanly release application resources."""
    init_db()
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description=settings.description,
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router, tags=["auth"])
app.include_router(content_router, tags=["content"])
app.include_router(blog_router, tags=["blog"])
app.include_router(imports_router, tags=["imports"])
app.include_router(media_router, tags=["media"])
app.include_router(email_router, tags=["email"])
app.include_router(travel_router, tags=["travel"])
app.include_router(audit_router, tags=["audit"])
app.include_router(archive_import_router)
app.include_router(system_router)

_ = orm_models
