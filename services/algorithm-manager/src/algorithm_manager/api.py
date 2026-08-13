from datetime import datetime

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field

from .application.service import InstanceService
from .domain.models import AlgorithmInstance, ContainerSpec, InstanceStatus


class EnsureInstanceRequest(BaseModel):
    algorithm_version_id: str = Field(min_length=1)
    algorithm_key: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    image: str = Field(min_length=1)
    container_name: str = Field(pattern=r"^cv-algorithm-[a-z0-9-]+$")
    internal_port: int = Field(default=8000, ge=1, le=65535)
    device: str = Field(default="cpu", pattern=r"^(cpu|gpu|auto)$")
    memory_mb: int = Field(default=1024, ge=256)
    cpu_count: float = Field(default=1, ge=0.1, le=64)
    gpu_device_ids: list[str] = Field(default_factory=list, max_length=32)

    def to_spec(self) -> ContainerSpec:
        data = self.model_dump()
        data["gpu_device_ids"] = tuple(data["gpu_device_ids"])
        return ContainerSpec(**data)


class InstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    algorithm_version_id: str
    image: str
    container_name: str
    endpoint: str
    status: InstanceStatus
    device: str
    created_at: datetime
    updated_at: datetime
    error: str | None
    last_used_at: datetime | None
    gpu_device_ids: list[str]

    @classmethod
    def from_entity(cls, instance: AlgorithmInstance) -> "InstanceResponse":
        return cls.model_validate(instance)


class EnsureReplicasRequest(EnsureInstanceRequest):
    replicas: int = Field(ge=0, le=100)


def build_router(get_service: object) -> APIRouter:
    router = APIRouter(prefix="/instances", tags=["instances"])

    @router.get("", response_model=list[InstanceResponse])
    def list_instances(service: InstanceService = Depends(get_service)) -> list[InstanceResponse]:
        return [InstanceResponse.from_entity(item) for item in service.list_instances()]

    @router.post("/ensure", response_model=InstanceResponse)
    def ensure_instance(
        payload: EnsureInstanceRequest,
        service: InstanceService = Depends(get_service),
    ) -> InstanceResponse:
        return InstanceResponse.from_entity(service.ensure_running(payload.to_spec()))

    @router.post("/replicas/ensure", response_model=list[InstanceResponse])
    def ensure_replicas(
        payload: EnsureReplicasRequest,
        service: InstanceService = Depends(get_service),
    ) -> list[InstanceResponse]:
        data = payload.model_dump(exclude={"replicas"})
        data["gpu_device_ids"] = tuple(data["gpu_device_ids"])
        instances = service.ensure_replicas(ContainerSpec(**data), payload.replicas)
        return [InstanceResponse.from_entity(item) for item in instances]

    @router.post("/{instance_id}/stop", response_model=InstanceResponse)
    def stop_instance(
        instance_id: str,
        service: InstanceService = Depends(get_service),
    ) -> InstanceResponse:
        return InstanceResponse.from_entity(service.stop(instance_id))

    @router.delete("/{instance_id}", status_code=204)
    def remove_instance(
        instance_id: str,
        service: InstanceService = Depends(get_service),
    ) -> Response:
        service.remove(instance_id)
        return Response(status_code=204)

    @router.get("/{instance_id}/logs", response_model=list[str])
    def instance_logs(
        instance_id: str,
        tail: int = 200,
        service: InstanceService = Depends(get_service),
    ) -> list[str]:
        return service.logs(instance_id, tail)

    @router.post("/{instance_id}/touch", response_model=InstanceResponse)
    def touch_instance(
        instance_id: str,
        service: InstanceService = Depends(get_service),
    ) -> InstanceResponse:
        return InstanceResponse.from_entity(service.touch(instance_id))

    return router
