import gc
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import hash_password
from app.storage import LocalObjectStorage
import app.main as main_module


@pytest.fixture()
def client():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        engine = create_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}", connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=engine)

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        main_module.storage = LocalObjectStorage(tmp_path / "objects")
        db = TestingSessionLocal()
        db.add(User(username="admin", password_hash=hash_password("admin-change-me"), role="owner"))
        db.commit()
        db.close()
        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            # Windows keeps SQLite files locked until every SQLAlchemy connection
            # in the pool has been closed.  Disposing the test engine before the
            # TemporaryDirectory context exits prevents WinError 32 during pytest
            # fixture teardown.
            app.dependency_overrides.clear()
            engine.dispose()
            gc.collect()


@pytest.fixture()
def auth_headers(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin-change-me"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
