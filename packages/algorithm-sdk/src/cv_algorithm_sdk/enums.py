try:
    from enum import StrEnum
except ImportError:  # Python 3.10 compatibility for prebuilt CUDA images.
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)


class ResultType(StrEnum):
    OBJECT_DETECTION = "object_detection"
    CLASSIFICATION = "classification"
    SEGMENTATION = "segmentation"
    OCR = "ocr"
    POSE_ESTIMATION = "pose_estimation"


class DeviceType(StrEnum):
    CPU = "cpu"
    GPU = "gpu"
    AUTO = "auto"


class AlgorithmStatus(StrEnum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    BUILDING = "building"
    TESTING = "testing"
    AVAILABLE = "available"
    DISABLED = "disabled"
    FAILED = "failed"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    PREPARING = "preparing"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
