from dataclasses import replace
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from cv_platform.dependencies import get_container
from cv_platform.modules.instances.domain.models import RuntimeInstance, RuntimeRequest


class FakeManagerGateway:
    def __init__(self) -> None:
        self.items: dict[str, RuntimeInstance] = {}

    def list_instances(self) -> list[RuntimeInstance]:
        return list(self.items.values())

    def ensure_running(self, request: RuntimeRequest) -> RuntimeInstance:
        now = datetime.now(UTC)
        instance = RuntimeInstance(
            id="container-1",
            algorithm_version_id=request.algorithm_version_id,
            image=request.image,
            container_name=request.container_name,
            endpoint=f"http://{request.container_name}:{request.internal_port}",
            status="healthy",
            device=request.device,
            created_at=now,
            updated_at=now,
        )
        self.items[instance.id] = instance
        return instance

    def stop(self, instance_id: str) -> RuntimeInstance:
        instance = replace(self.items[instance_id], status="stopped")
        self.items[instance_id] = instance
        return instance

    def remove(self, instance_id: str) -> None:
        self.items.pop(instance_id)

    def logs(self, instance_id: str, tail: int = 200) -> list[str]:
        return [f"logs:{instance_id}:{tail}"]

    def list_gpus(self) -> list[dict[str, object]]:
        return []

    def touch(self, instance_id: str) -> RuntimeInstance:
        return self.items[instance_id]


def test_start_list_stop_and_remove_algorithm_instance(client: TestClient) -> None:
    container = get_container()
    manager = FakeManagerGateway()
    object.__setattr__(container, "algorithm_manager", manager)
    algorithm_id = client.get("/api/v1/algorithms").json()[0]["id"]

    started = client.post(f"/api/v1/algorithms/{algorithm_id}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "healthy"
    assert started.json()["container_name"].startswith("cv-algorithm-")

    listed = client.get("/api/v1/instances")
    assert len(listed.json()) == 1

    stopped = client.post("/api/v1/instances/container-1/stop")
    assert stopped.json()["status"] == "stopped"

    removed = client.delete("/api/v1/instances/container-1")
    assert removed.status_code == 204
