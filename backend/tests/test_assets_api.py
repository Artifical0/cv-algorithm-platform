import io

from fastapi.testclient import TestClient
from PIL import Image


def make_image_bytes(color: str = "red") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (32, 24), color=color).save(output, format="PNG")
    return output.getvalue()


def test_upload_list_and_reuse_image_asset(client: TestClient) -> None:
    content = make_image_bytes()
    first = client.post(
        "/api/v1/assets/upload",
        files=[("files", ("sample.png", content, "image/png"))],
    )
    second = client.post(
        "/api/v1/assets/upload",
        files=[("files", ("duplicate.png", content, "image/png"))],
    )

    assert first.status_code == 201
    assert first.json()["assets"][0]["width"] == 32
    assert first.json()["assets"][0]["height"] == 24
    assert second.json()["assets"][0]["id"] == first.json()["assets"][0]["id"]
    assert len(client.get("/api/v1/assets").json()) == 1


def test_upload_rejects_content_type_mismatch(client: TestClient) -> None:
    response = client.post(
        "/api/v1/assets/upload",
        files=[("files", ("sample.jpg", make_image_bytes(), "image/jpeg"))],
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INPUT_INVALID"
