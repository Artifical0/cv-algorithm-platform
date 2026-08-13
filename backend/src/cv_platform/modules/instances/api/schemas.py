from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..domain.models import RuntimeInstance


class RuntimeInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    algorithm_version_id: str
    image: str
    container_name: str
    endpoint: str
    status: str
    device: str
    created_at: datetime
    updated_at: datetime
    error: str | None
    last_used_at: datetime | None
    node_id: str
    gpu_device_ids: list[str]

    @classmethod
    def from_entity(cls, instance: RuntimeInstance) -> "RuntimeInstanceResponse":
        return cls.model_validate(instance)
