import pytest
from pydantic import TypeAdapter, ValidationError

from cv_algorithm_sdk import (
    AlgorithmManifest,
    AlgorithmResult,
    BoundingBox,
    ClassificationResult,
    ObjectDetectionResult,
)
from cv_algorithm_sdk.results import Segment


def test_manifest_accepts_valid_detection_algorithm() -> None:
    manifest = AlgorithmManifest.model_validate(
        {
            "id": "mock-detector",
            "name": "Mock Detector",
            "version": "1.0.0",
            "task_type": "object_detection",
            "runtime": {"framework": "pytorch", "device": "cpu"},
            "input": {"media_types": ["image/jpeg"]},
            "output": {"type": "object_detection"},
            "parameters": {
                "confidence": {
                    "type": "number",
                    "default": 0.5,
                    "minimum": 0,
                    "maximum": 1,
                    "step": 0.01,
                    "title": "置信度阈值",
                    "description": "过滤低分检测框",
                }
            },
        }
    )
    assert manifest.parameters["confidence"].default == 0.5
    assert manifest.parameters["confidence"].step == 0.01
    assert manifest.parameters["confidence"].title == "置信度阈值"


def test_manifest_rejects_mismatched_result_type() -> None:
    with pytest.raises(ValidationError):
        AlgorithmManifest.model_validate(
            {
                "id": "mock-detector",
                "name": "Mock Detector",
                "version": "1.0.0",
                "task_type": "object_detection",
                "runtime": {"framework": "pytorch"},
                "input": {"media_types": ["image/jpeg"]},
                "output": {"type": "classification"},
            }
        )


def test_manifest_validates_supplied_parameter_values() -> None:
    manifest = AlgorithmManifest.model_validate(
        {
            "id": "mock-detector",
            "name": "Mock Detector",
            "version": "1.0.0",
            "task_type": "object_detection",
            "runtime": {"framework": "pytorch"},
            "input": {"media_types": ["image/jpeg"]},
            "output": {"type": "object_detection"},
            "parameters": {
                "confidence": {
                    "type": "number", "default": 0.5, "minimum": 0, "maximum": 1
                }
            },
        }
    )
    assert manifest.resolve_parameters({}) == {"confidence": 0.5}
    with pytest.raises(ValueError):
        manifest.resolve_parameters({"confidence": 1.5})


def test_bbox_requires_positive_area() -> None:
    with pytest.raises(ValidationError):
        BoundingBox.model_validate([10, 10, 5, 20])


def test_detection_result_round_trip() -> None:
    result = ObjectDetectionResult.model_validate(
        {
            "request_id": "task-1",
            "algorithm": {"id": "mock-detector", "version": "1.0.0"},
            "input": {"width": 1280, "height": 720},
            "timing": {"inference_ms": 12.5},
            "data": {
                "detections": [
                    {"label": "person", "score": 0.95, "bbox": [10, 20, 100, 200]}
                ]
            },
        }
    )
    assert result.data.detections[0].bbox.root == [10.0, 20.0, 100.0, 200.0]


def test_classification_result_uses_discriminated_union() -> None:
    result = TypeAdapter(AlgorithmResult).validate_python(
        {
            "request_id": "task-classification",
            "type": "classification",
            "algorithm": {"id": "classifier", "version": "1.0.0"},
            "input": {"width": 320, "height": 240},
            "timing": {"inference_ms": 5},
            "data": {"predictions": [{"label": "cat", "score": 0.9}]},
        }
    )

    assert isinstance(result, ClassificationResult)
    assert result.data.predictions[0].label == "cat"


def test_segmentation_mask_rejects_external_uri() -> None:
    with pytest.raises(ValidationError):
        Segment(label="road", score=0.9, mask_uri="https://example.com/mask.png")
