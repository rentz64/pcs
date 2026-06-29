from pydantic import BaseModel
from enum import StrEnum
from os import getenv
from pathlib import Path


class RuntimeEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    LOCAL = "local"


class Settings(BaseModel):
    app_name: str = "Private Content Service"
    api_version: str = "0.9.0"
    description: str = "Private Content Service backend API"
    runtime_environment: RuntimeEnvironment = RuntimeEnvironment.DEVELOPMENT
    database_url: str = "sqlite:///./storage/pcs.sqlite3"
    object_storage_dir: Path = Path("./storage/objects")
    jwt_secret: str = "change-this-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    def runtime_summary(self) -> dict[str, str | int]:
        return {
            "app_name": self.app_name,
            "api_version": self.api_version,
            "runtime_environment": self.runtime_environment.value,
            "database": "sqlite" if self.database_url.startswith("sqlite") else "other",
            "object_storage": "local_filesystem",
            "object_storage_dir": self.object_storage_dir.as_posix(),
            "access_token_minutes": self.access_token_minutes,
        }


def load_settings() -> Settings:
    return Settings(
        app_name=getenv("PCS_APP_NAME", Settings.model_fields["app_name"].default),
        api_version=getenv("PCS_API_VERSION", Settings.model_fields["api_version"].default),
        description=getenv("PCS_DESCRIPTION", Settings.model_fields["description"].default),
        runtime_environment=getenv("PCS_RUNTIME_ENVIRONMENT", Settings.model_fields["runtime_environment"].default),
        database_url=getenv("PCS_DATABASE_URL", Settings.model_fields["database_url"].default),
        object_storage_dir=Path(getenv("PCS_OBJECT_STORAGE_DIR", str(Settings.model_fields["object_storage_dir"].default))),
        jwt_secret=getenv("PCS_JWT_SECRET", Settings.model_fields["jwt_secret"].default),
        jwt_algorithm=getenv("PCS_JWT_ALGORITHM", Settings.model_fields["jwt_algorithm"].default),
        access_token_minutes=int(getenv("PCS_ACCESS_TOKEN_MINUTES", str(Settings.model_fields["access_token_minutes"].default))),
    )


settings = load_settings()
