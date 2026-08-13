import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class YoloSettings:
    mode: str
    weights_path: Path
    data_root: Path
    device: str

    @classmethod
    def from_environment(cls) -> "YoloSettings":
        return cls(
            mode=os.getenv("CV_YOLO_MODE", "ultralytics"),
            weights_path=Path(os.getenv("CV_YOLO_WEIGHTS", "/models/model.pt")),
            data_root=Path(os.getenv("CV_YOLO_DATA_ROOT", "/data")),
            device=os.getenv("CV_YOLO_DEVICE", "auto"),
        )
