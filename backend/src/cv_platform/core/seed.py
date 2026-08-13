from uuid import NAMESPACE_URL, uuid5

from cv_algorithm_sdk import AlgorithmManifest

from .container import ApplicationContainer
from ..modules.algorithms.domain.entities import AlgorithmVersion


def seed_demo_data(container: ApplicationContainer) -> None:
    if container.algorithms.list():
        return
    definitions = [
        ({
            "id": "faster-rcnn-resnet50",
            "name": "Faster R-CNN ResNet50",
            "version": "1.0.0",
            "description": "现有原型迁移目标算法",
            "task_type": "object_detection",
            "runtime": {"framework": "pytorch", "device": "gpu", "min_memory_mb": 4096},
            "input": {"media_types": ["image/jpeg", "image/png"]},
            "output": {"type": "object_detection"},
            "parameters": {
                "confidence": {"type": "number", "default": 0.5, "minimum": 0, "maximum": 1}
            },
        }, "cv-platform/faster-rcnn:dev"),
        ({
            "id": "yolo-detector",
            "name": "YOLO Detector",
            "version": "1.0.0",
            "description": "用于验证多算法隔离的第二个示例",
            "task_type": "object_detection",
            "runtime": {"framework": "pytorch", "device": "gpu", "min_memory_mb": 2048},
            "input": {"media_types": ["image/jpeg", "image/png"]},
            "output": {"type": "object_detection"},
            "parameters": {
                "confidence": {"type": "number", "default": 0.4, "minimum": 0, "maximum": 1}
            },
        }, "cv-platform/yolo:dev"),
    ]
    for raw_manifest, image in definitions:
        manifest = AlgorithmManifest.model_validate(raw_manifest)
        container.algorithms.add(
            AlgorithmVersion.available(
                manifest,
                image,
                algorithm_id=uuid5(
                    NAMESPACE_URL,
                    f"cv-platform:{manifest.id}:{manifest.version}",
                ),
            )
        )
