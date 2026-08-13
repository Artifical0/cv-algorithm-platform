import pytest
from fastapi.testclient import TestClient

from cv_platform.dependencies import get_container
from cv_platform.main import create_app


class RecordingTaskQueue:
    def __init__(self) -> None:
        self.submitted: list[str] = []
        self.cancelled: list[str] = []

    def submit(self, task_id: str) -> None:
        self.submitted.append(task_id)

    def cancel(self, task_id: str) -> None:
        self.cancelled.append(task_id)

    def shutdown(self) -> None:
        return None


@pytest.fixture
def client() -> TestClient:
    get_container.cache_clear()
    container = get_container()
    container.task_queue.shutdown()
    container.build_queue.shutdown()
    object.__setattr__(container, "task_queue", RecordingTaskQueue())
    with TestClient(create_app()) as test_client:
        login = test_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "ChangeMe-Local-123!"},
        )
        assert login.status_code == 200
        yield test_client
    get_container.cache_clear()
