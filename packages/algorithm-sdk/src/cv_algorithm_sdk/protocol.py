from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .enums import ResultType


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HealthResponse(ProtocolModel):
    status: Literal["ok", "degraded"]
    ready: bool


class MetadataResponse(ProtocolModel):
    schema_version: Literal["1.0"] = "1.0"
    algorithm_id: str
    version: str
    task_type: ResultType
    input_types: list[str] = Field(min_length=1)
    output_type: ResultType


class PredictInput(ProtocolModel):
    asset_uri: str = Field(min_length=1)


class PredictRequest(ProtocolModel):
    request_id: str = Field(min_length=1, max_length=128)
    input: PredictInput
    parameters: dict[str, Any] = Field(default_factory=dict)

