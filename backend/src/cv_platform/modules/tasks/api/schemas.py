from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cv_algorithm_sdk import AlgorithmResult, TaskStatus


class CreateTaskRequest(BaseModel):
    algorithm_version_id: UUID | None = None
    algorithm_key: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    asset_id: UUID | None = None
    asset_uri: str | None = Field(default=None, min_length=1, max_length=2_048)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_input(self) -> "CreateTaskRequest":
        if self.asset_id is None and self.asset_uri is None:
            raise ValueError("asset_id is required")
        if self.algorithm_version_id is None and self.algorithm_key is None:
            raise ValueError("algorithm_version_id or algorithm_key is required")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    algorithm_version_id: UUID
    asset_id: UUID | None
    parameters: dict[str, Any]
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancelled_by: str | None
    container_id: str | None
    error_code: str | None
    error_message: str | None
    retry_of: UUID | None
    project_id: UUID


class TaskResultResponse(BaseModel):
    task_id: UUID
    result: AlgorithmResult


class ResultArchiveRequest(BaseModel):
    task_ids: list[UUID] = Field(min_length=1, max_length=100)
