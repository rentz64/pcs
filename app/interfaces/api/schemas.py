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
