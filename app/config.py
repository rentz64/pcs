from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Private Content Service"
    database_url: str = "sqlite:///./storage/pcs.sqlite3"
    object_storage_dir: Path = Path("./storage/objects")
    jwt_secret: str = "change-this-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60


settings = Settings()
