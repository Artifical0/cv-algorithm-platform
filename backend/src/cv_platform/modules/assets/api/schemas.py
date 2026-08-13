from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_name: str
    sha256: str
    media_type: str
    width: int
    height: int
    size_bytes: int
    created_at: datetime
    owner_id: str
    project_id: UUID


class BatchUploadResponse(BaseModel):
    assets: list[AssetResponse]
