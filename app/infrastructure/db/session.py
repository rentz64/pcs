from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_schema() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_content_import_columns()


def _ensure_sqlite_content_import_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "content_items" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("content_items")}
    columns = {
        "origin": "VARCHAR(32) DEFAULT 'native'",
        "external_source_id": "INTEGER",
        "external_account_id": "INTEGER",
        "external_content_id": "VARCHAR(255)",
        "external_content_type": "VARCHAR(128)",
        "imported_at": "DATETIME",
        "import_batch_id": "INTEGER",
        "source_url": "TEXT",
        "source_reference": "TEXT",
    }
    with engine.begin() as connection:
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE content_items ADD COLUMN {name} {definition}"))
