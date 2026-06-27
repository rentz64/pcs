from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ContentOut(BaseModel):
    id: int
    title: str
    description: str | None
    content_type: str
    original_filename: str
    mime_type: str | None
    size_bytes: int
    tags: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BlogPostCreate(BaseModel):
    title: str
    slug: str
    body: str = ""
    summary: str | None = None
    tags: str = ""
    collections: tuple[int, ...] = ()


class BlogPostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    body: str | None = None
    summary: str | None = None
    tags: str | None = None
    collections: tuple[int, ...] | None = None


class BlogPostOut(BaseModel):
    id: int
    content_item_id: int
    title: str
    slug: str
    body: str
    summary: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    tags: str
    collections: tuple[int, ...] = ()
