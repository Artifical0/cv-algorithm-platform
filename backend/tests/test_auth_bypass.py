from fastapi.testclient import TestClient

from cv_platform.core.config import get_settings
from cv_platform.dependencies import get_container
from cv_platform.main import create_app


def test_authentication_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("CV_PLATFORM_AUTH_ENABLED", "false")
    get_settings.cache_clear()
    get_container.cache_clear()

    try:
        with TestClient(create_app()) as client:
            session = client.get("/api/v1/auth/me")
            assert session.status_code == 200
            assert session.json()["username"] == "admin"
            assert session.json()["role"] == "admin"
            assert session.json()["authentication_enabled"] is False
            assert client.get("/api/v1/users").status_code == 200
    finally:
        get_container.cache_clear()
        get_settings.cache_clear()
