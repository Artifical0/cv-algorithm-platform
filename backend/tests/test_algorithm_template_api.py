from io import BytesIO
from zipfile import ZipFile

import pytest
import yaml
from cv_algorithm_sdk import AlgorithmManifest
from fastapi.testclient import TestClient

TASK_TYPES = [
    "object_detection",
    "classification",
    "segmentation",
    "ocr",
    "pose_estimation",
]


@pytest.mark.parametrize("task_type", TASK_TYPES)
def test_download_algorithm_template(client: TestClient, task_type: str) -> None:
    response = client.get(f"/api/v1/algorithms/template?task_type={task_type}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert task_type in response.headers["content-disposition"]
    with ZipFile(BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert {
            "manifest.yaml",
            "service.py",
            "algorithm.py",
            "requirements.txt",
            "README.md",
            "test/sample.jpg",
        } <= names
        assert not any(name.lower().endswith("dockerfile") for name in names)
        manifest = AlgorithmManifest.model_validate(
            yaml.safe_load(archive.read("manifest.yaml"))
        )
        assert manifest.task_type.value == task_type
        assert manifest.output.type.value == task_type


def test_downloaded_template_can_be_imported(client: TestClient) -> None:
    template = client.get(
        "/api/v1/algorithms/template?task_type=object_detection"
    )

    response = client.post(
        "/api/v1/algorithms/import",
        files={"package": ("template.zip", template.content, "application/zip")},
    )

    assert response.status_code == 201
    assert response.json()["key"] == "template-object-detection"
    assert response.json()["status"] == "uploaded"
