from abc import ABC, abstractmethod

from .manifest import AlgorithmManifest
from .protocol import PredictRequest
from .results import AlgorithmResult


class DetectionAlgorithm(ABC):
    """Stable interface implemented by object-detection algorithm containers."""

    def __init__(self, manifest: AlgorithmManifest) -> None:
        self.manifest = manifest

    def load(self) -> None:
        """Load model resources. Override when the algorithm requires initialization."""

    @abstractmethod
    def predict(self, request: PredictRequest) -> AlgorithmResult:
        """Run inference and return a schema-validated result."""
