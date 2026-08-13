from contextlib import asynccontextmanager

from fastapi import FastAPI

from .algorithm import DetectionAlgorithm
from .protocol import HealthResponse, MetadataResponse, PredictRequest
from .results import AlgorithmResult


def create_algorithm_app(algorithm: DetectionAlgorithm) -> FastAPI:
    """Expose an algorithm through the platform's standard HTTP contract."""

    state = {"ready": False}

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        algorithm.load()
        state["ready"] = True
        yield
        state["ready"] = False

    app = FastAPI(
        title=algorithm.manifest.name,
        version=algorithm.manifest.version,
        lifespan=lifespan,
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", ready=state["ready"])

    @app.get("/metadata", response_model=MetadataResponse)
    def metadata() -> MetadataResponse:
        manifest = algorithm.manifest
        return MetadataResponse(
            algorithm_id=manifest.id,
            version=manifest.version,
            task_type=manifest.task_type,
            input_types=manifest.input.media_types,
            output_type=manifest.output.type,
        )

    @app.post("/predict", response_model=AlgorithmResult)
    def predict(request: PredictRequest) -> AlgorithmResult:
        return algorithm.predict(request)

    return app
