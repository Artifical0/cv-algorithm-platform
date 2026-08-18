from dataclasses import replace
from uuid import NAMESPACE_URL, uuid5

from cv_algorithm_sdk import AlgorithmManifest

from .container import ApplicationContainer
from ..modules.algorithms.domain.entities import AlgorithmVersion


def seed_demo_data(container: ApplicationContainer) -> None:
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
                "confidence": {
                    "type": "number", "default": 0.5, "minimum": 0, "maximum": 1,
                    "step": 0.01, "title": "置信度阈值",
                    "description": "仅保留得分不低于该值的检测框",
                },
                "nms_threshold": {
                    "type": "number", "default": 0.5, "minimum": 0, "maximum": 1,
                    "step": 0.01, "title": "NMS 重叠阈值",
                    "description": "数值越低，重叠目标框过滤越严格",
                },
                "max_detections": {
                    "type": "integer", "default": 100, "minimum": 1, "maximum": 300,
                    "step": 1, "title": "最大检测数量",
                    "description": "单张图片最多返回的目标框数量",
                },
                "min_box_area": {
                    "type": "number", "default": 0, "minimum": 0, "maximum": 1_000_000,
                    "step": 1, "title": "最小框面积",
                    "description": "过滤面积小于该像素值的目标框，0 表示不过滤",
                },
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
                "confidence": {
                    "type": "number", "default": 0.4, "minimum": 0, "maximum": 1,
                    "step": 0.01, "title": "置信度阈值",
                    "description": "仅保留得分不低于该值的检测框",
                },
                "iou_threshold": {
                    "type": "number", "default": 0.45, "minimum": 0, "maximum": 1,
                    "step": 0.01, "title": "NMS IoU 阈值",
                    "description": "控制重叠检测框的合并强度",
                },
                "max_detections": {
                    "type": "integer", "default": 300, "minimum": 1, "maximum": 1000,
                    "step": 1, "title": "最大检测数量",
                    "description": "单张图片最多返回的目标框数量",
                },
                "image_size": {
                    "type": "integer", "default": 640, "minimum": 320, "maximum": 1280,
                    "step": 32, "title": "推理输入尺寸",
                    "description": "较大尺寸有利于小目标，但会增加显存和推理时间",
                },
                "agnostic_nms": {
                    "type": "boolean", "default": False, "title": "类别无关 NMS",
                    "description": "开启后，不同类别的重叠框也会互相抑制",
                },
            },
        }, "cv-platform/yolo:dev"),
    ]
    for raw_manifest, image in definitions:
        manifest = AlgorithmManifest.model_validate(raw_manifest)
        algorithm_id = uuid5(
            NAMESPACE_URL,
            f"cv-platform:{manifest.id}:{manifest.version}",
        )
        existing = container.algorithms.get(algorithm_id)
        if existing is None:
            container.algorithms.add(
                AlgorithmVersion.available(
                    manifest,
                    image,
                    algorithm_id=algorithm_id,
                )
            )
        else:
            container.algorithms.save(replace(existing, manifest=manifest, image=image))
