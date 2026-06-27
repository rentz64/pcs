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
from app.interfaces.api.routes_auth import router as auth_router
from app.interfaces.api.routes_blog import router as blog_router
from app.interfaces.api.routes_content import router as content_router
from app.interfaces.api.routes_imports import router as imports_router


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


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(content_router)
app.include_router(blog_router)
app.include_router(imports_router)
app.include_router(audit_router)

_ = orm_models
