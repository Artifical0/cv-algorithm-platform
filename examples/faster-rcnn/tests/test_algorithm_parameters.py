from pathlib import Path

from cv_algorithm_sdk import PredictRequest, load_manifest
from faster_rcnn_algorithm.algorithm import FasterRcnnAlgorithm
from faster_rcnn_algorithm.predictor import Prediction


class RecordingPredictor:
    def __init__(self) -> None:
        self.arguments: tuple[object, ...] | None = None

    def load(self) -> None:
        return None

    def predict(
        self,
        asset_uri: str,
        confidence: float,
        nms_threshold: float,
        max_detections: int,
        min_box_area: float,
    ) -> Prediction:
        self.arguments = (
            asset_uri,
            confidence,
            nms_threshold,
            max_detections,
            min_box_area,
        )
        return Prediction(32, 24, 0, 1, 0, [])


def test_runtime_parameters_are_forwarded_to_predictor() -> None:
    manifest = load_manifest(Path(__file__).parents[1] / "manifest.yaml")
    predictor = RecordingPredictor()
    algorithm = FasterRcnnAlgorithm(manifest, None, predictor)

    algorithm.predict(
        PredictRequest(
            request_id="parameter-test",
            input={"asset_uri": "/data/test.jpg"},
            parameters={
                "confidence": 0.7,
                "nms_threshold": 0.3,
                "max_detections": 25,
                "min_box_area": 64,
            },
        )
    )

    assert predictor.arguments == ("/data/test.jpg", 0.7, 0.3, 25, 64.0)
