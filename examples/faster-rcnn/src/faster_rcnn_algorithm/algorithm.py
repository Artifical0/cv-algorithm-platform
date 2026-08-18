from cv_algorithm_sdk import (
    AlgorithmIdentity,
    Detection,
    DetectionAlgorithm,
    ImageMetadata,
    ObjectDetectionData,
    ObjectDetectionResult,
    PredictRequest,
    TimingMetadata,
)

from .predictor import Predictor, StubPredictor, TorchvisionPredictor
from .settings import FasterRcnnSettings


class FasterRcnnAlgorithm(DetectionAlgorithm):
    def __init__(self, manifest, settings: FasterRcnnSettings, predictor: Predictor | None = None):
        super().__init__(manifest)
        self._predictor = predictor or self._build_predictor(settings)

    @staticmethod
    def _build_predictor(settings: FasterRcnnSettings) -> Predictor:
        if settings.mode == "stub":
            return StubPredictor()
        if settings.mode != "torchvision":
            raise ValueError("CV_FASTER_RCNN_MODE must be torchvision or stub")
        return TorchvisionPredictor(
            settings.config_path,
            settings.weights_path,
            settings.data_root,
            settings.device,
            settings.allow_partial_weights,
        )

    def load(self) -> None:
        self._predictor.load()

    def predict(self, request: PredictRequest) -> ObjectDetectionResult:
        parameters = self.manifest.resolve_parameters(request.parameters)
        prediction = self._predictor.predict(
            request.input.asset_uri,
            float(parameters["confidence"]),
            float(parameters["nms_threshold"]),
            int(parameters["max_detections"]),
            float(parameters["min_box_area"]),
        )
        return ObjectDetectionResult(
            request_id=request.request_id,
            algorithm=AlgorithmIdentity(id=self.manifest.id, version=self.manifest.version),
            input=ImageMetadata(width=prediction.width, height=prediction.height),
            timing=TimingMetadata(
                preprocess_ms=prediction.preprocess_ms,
                inference_ms=prediction.inference_ms,
                postprocess_ms=prediction.postprocess_ms,
            ),
            data=ObjectDetectionData(
                detections=[
                    Detection(label=item.label, score=item.score, bbox=item.bbox)
                    for item in prediction.detections
                ]
            ),
        )
