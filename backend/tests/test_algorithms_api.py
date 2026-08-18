from uuid import NAMESPACE_URL, uuid5

from fastapi.testclient import TestClient


def test_list_seeded_algorithms(client: TestClient) -> None:
    response = client.get("/api/v1/algorithms")
    assert response.status_code == 200
    payload = response.json()
    assert [item["key"] for item in payload] == ["faster-rcnn-resnet50", "yolo-detector"]
    assert all(item["status"] == "available" for item in payload)
    assert payload[0]["id"] == str(
        uuid5(NAMESPACE_URL, "cv-platform:faster-rcnn-resnet50:1.0.0")
    )
    assert list(payload[0]["parameters"]) == [
        "confidence",
        "nms_threshold",
        "max_detections",
        "min_box_area",
    ]
    assert payload[0]["parameters"]["nms_threshold"]["title"] == "NMS 重叠阈值"


def test_get_unknown_algorithm_returns_business_error(client: TestClient) -> None:
    response = client.get("/api/v1/algorithms/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["code"] == "ALGORITHM_NOT_FOUND"
