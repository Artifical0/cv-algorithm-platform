from fastapi.testclient import TestClient


def test_create_task_applies_default_algorithm_parameters(client: TestClient) -> None:
    algorithm = client.get("/api/v1/algorithms").json()[0]
    response = client.post(
        "/api/v1/tasks",
        json={
            "algorithm_version_id": algorithm["id"],
            "asset_uri": "file:///data/demo.jpg",
            "parameters": {},
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "queued"
    assert response.json()["parameters"]["confidence"] == 0.5
    assert response.json()["parameters"]["nms_threshold"] == 0.5
    assert response.json()["parameters"]["max_detections"] == 100
    assert response.json()["parameters"]["min_box_area"] == 0


def test_create_task_rejects_unknown_parameter(client: TestClient) -> None:
    algorithm = client.get("/api/v1/algorithms").json()[0]
    response = client.post(
        "/api/v1/tasks",
        json={
            "algorithm_version_id": algorithm["id"],
            "asset_uri": "file:///data/demo.jpg",
            "parameters": {"unknown": True},
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "PARAMETER_INVALID"


def test_create_task_rejects_unmanaged_asset_uri(client: TestClient) -> None:
    algorithm = client.get("/api/v1/algorithms").json()[0]
    response = client.post(
        "/api/v1/tasks",
        json={
            "algorithm_version_id": algorithm["id"],
            "asset_uri": "file:///etc/passwd",
            "parameters": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INPUT_INVALID"


def test_cancel_and_retry_task(client: TestClient) -> None:
    algorithm = client.get("/api/v1/algorithms").json()[0]
    created = client.post(
        "/api/v1/tasks",
        json={
            "algorithm_version_id": algorithm["id"],
            "asset_uri": "file:///data/demo.jpg",
            "parameters": {},
        },
    ).json()

    cancelled = client.post(f"/api/v1/tasks/{created['id']}/cancel")
    retried = client.post(f"/api/v1/tasks/{created['id']}/retry")

    assert cancelled.json()["status"] == "cancelled"
    assert retried.status_code == 201
    assert retried.json()["retry_of"] == created["id"]
