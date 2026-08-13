import importlib.util
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).parents[1]


def load_service(example: str):
    service_path = PROJECT_ROOT / "examples" / example / "service.py"
    source_path = service_path.parent / "src"
    if source_path.is_dir():
        sys.path.insert(0, str(source_path))
    spec = importlib.util.spec_from_file_location(f"{example}_service", service_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("example", ["faster-rcnn", "yolo"])
def test_example_implements_algorithm_contract(example: str) -> None:
    mode_variable = "CV_FASTER_RCNN_MODE" if example == "faster-rcnn" else "CV_YOLO_MODE"
    os.environ[mode_variable] = "stub"
    try:
        module = load_service(example)
        with TestClient(module.app) as client:
            health = client.get("/health")
            metadata = client.get("/metadata")
            prediction = client.post(
                "/predict",
                json={
                    "request_id": f"contract-{example}",
                    "input": {"asset_uri": "file:///data/demo.jpg"},
                    "parameters": {"confidence": 0.5},
                },
            )
    finally:
        os.environ.pop(mode_variable, None)

    assert health.json() == {"status": "ok", "ready": True}
    assert metadata.json()["output_type"] == "object_detection"
    assert prediction.status_code == 200
    assert prediction.json()["type"] == "object_detection"
