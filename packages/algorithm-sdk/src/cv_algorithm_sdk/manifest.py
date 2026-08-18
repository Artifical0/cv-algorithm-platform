from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import DeviceType, ResultType


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RuntimeSpec(StrictModel):
    framework: str = Field(min_length=1, max_length=64)
    device: DeviceType = DeviceType.AUTO
    min_memory_mb: int = Field(default=512, ge=128, le=262_144)


class InputSpec(StrictModel):
    media_types: list[str] = Field(min_length=1)


class OutputSpec(StrictModel):
    type: ResultType


class NumberParameter(StrictModel):
    type: Literal["number"]
    default: float
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=256)

    @model_validator(mode="after")
    def validate_range(self) -> "NumberParameter":
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot be greater than maximum")
        if self.minimum is not None and self.default < self.minimum:
            raise ValueError("default cannot be below minimum")
        if self.maximum is not None and self.default > self.maximum:
            raise ValueError("default cannot be above maximum")
        return self


class IntegerParameter(StrictModel):
    type: Literal["integer"]
    default: int
    minimum: int | None = None
    maximum: int | None = None
    step: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=256)

    @model_validator(mode="after")
    def validate_range(self) -> "IntegerParameter":
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot be greater than maximum")
        if self.minimum is not None and self.default < self.minimum:
            raise ValueError("default cannot be below minimum")
        if self.maximum is not None and self.default > self.maximum:
            raise ValueError("default cannot be above maximum")
        return self


class BooleanParameter(StrictModel):
    type: Literal["boolean"]
    default: bool
    title: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=256)


class StringParameter(StrictModel):
    type: Literal["string"]
    default: str
    options: list[str] | None = None
    title: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=256)


ParameterSpec = Annotated[
    NumberParameter | IntegerParameter | BooleanParameter | StringParameter,
    Field(discriminator="type"),
]


class AlgorithmManifest(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    description: str = Field(default="", max_length=1_000)
    task_type: ResultType
    runtime: RuntimeSpec
    input: InputSpec
    output: OutputSpec
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result_type(self) -> "AlgorithmManifest":
        if self.task_type != self.output.type:
            raise ValueError("task_type must match output.type")
        return self

    def resolve_parameters(self, supplied: dict[str, Any]) -> dict[str, Any]:
        """Apply defaults and validate runtime values against the declared contract."""
        unknown = set(supplied) - set(self.parameters)
        if unknown:
            raise ValueError(f"unknown parameters: {', '.join(sorted(unknown))}")

        resolved: dict[str, Any] = {}
        for name, spec in self.parameters.items():
            value = supplied.get(name, spec.default)
            if spec.type == "number":
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"{name} must be a number")
                value = float(value)
                if spec.minimum is not None and value < spec.minimum:
                    raise ValueError(f"{name} cannot be below {spec.minimum}")
                if spec.maximum is not None and value > spec.maximum:
                    raise ValueError(f"{name} cannot exceed {spec.maximum}")
            elif spec.type == "integer":
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError(f"{name} must be an integer")
                if spec.minimum is not None and value < spec.minimum:
                    raise ValueError(f"{name} cannot be below {spec.minimum}")
                if spec.maximum is not None and value > spec.maximum:
                    raise ValueError(f"{name} cannot exceed {spec.maximum}")
            elif spec.type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"{name} must be a boolean")
            elif spec.type == "string":
                if not isinstance(value, str):
                    raise ValueError(f"{name} must be a string")
                if spec.options is not None and value not in spec.options:
                    raise ValueError(f"{name} must be one of: {', '.join(spec.options)}")
            resolved[name] = value
        return resolved


def load_manifest(path: str | Path) -> AlgorithmManifest:
    manifest_path = Path(path)
    raw: Any = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return AlgorithmManifest.model_validate(raw)
