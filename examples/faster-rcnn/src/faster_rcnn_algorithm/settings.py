import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FasterRcnnSettings:
    mode: str
    config_path: Path
    weights_path: Path
    data_root: Path
    device: str
    allow_partial_weights: bool

    @classmethod
    def from_environment(cls, base_dir: Path) -> "FasterRcnnSettings":
        return cls(
            mode=os.getenv("CV_FASTER_RCNN_MODE", "torchvision"),
            config_path=Path(
                os.getenv("CV_FASTER_RCNN_CONFIG", str(base_dir / "model-config.yaml"))
            ),
            weights_path=Path(os.getenv("CV_FASTER_RCNN_WEIGHTS", "/models/model.pth")),
            data_root=Path(os.getenv("CV_FASTER_RCNN_DATA_ROOT", "/data")),
            device=os.getenv("CV_FASTER_RCNN_DEVICE", "auto"),
            allow_partial_weights=os.getenv(
                "CV_FASTER_RCNN_ALLOW_PARTIAL_WEIGHTS", "false"
            ).lower()
            == "true",
        )
