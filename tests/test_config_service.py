from pathlib import Path

from app.config import RuntimeEnvironment, Settings


def test_settings_summary_exposes_runtime_values_without_secrets():
    settings = Settings(
        app_name="PCS",
        api_version="9.0-test",
        runtime_environment=RuntimeEnvironment.TEST,
        database_url="sqlite:///./storage/test.sqlite3",
        object_storage_dir=Path("./storage/test-objects"),
        jwt_secret="super-secret",
    )

    summary = settings.runtime_summary()

    assert summary["app_name"] == "PCS"
    assert summary["api_version"] == "9.0-test"
    assert summary["runtime_environment"] == "test"
    assert summary["database"] == "sqlite"
    assert summary["object_storage"] == "local_filesystem"
    assert summary["object_storage_dir"] == "storage/test-objects"
    assert "jwt_secret" not in summary


def test_settings_distinguishes_known_runtime_environments():
    assert Settings(runtime_environment="development").runtime_environment is RuntimeEnvironment.DEVELOPMENT
    assert Settings(runtime_environment="test").runtime_environment is RuntimeEnvironment.TEST
    assert Settings(runtime_environment="local").runtime_environment is RuntimeEnvironment.LOCAL
