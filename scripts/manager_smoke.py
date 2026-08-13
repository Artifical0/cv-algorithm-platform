from algorithm_manager.application.service import InstanceService
from algorithm_manager.domain.models import AlgorithmInstance, ContainerSpec, InstanceStatus
from algorithm_manager.infrastructure.memory_repository import InMemoryInstanceRepository


class Runtime:
    def __init__(self) -> None:
        self.created = 0
        self.removed = []

    def discover(self):
        return []

    def create(self, spec):
        self.created += 1
        return f"container-{self.created}", f"http://{spec.container_name}:8000"

    def start(self, _):
        return None

    def stop(self, _):
        return None

    def remove(self, instance_id):
        self.removed.append(instance_id)

    def is_healthy(self, _):
        return True

    def probe_health(self, _):
        return True

    def list_gpus(self):
        return []

    def logs(self, _, tail=200):
        return []


runtime = Runtime()
service = InstanceService(InMemoryInstanceRepository(), runtime)
spec = ContainerSpec(
    algorithm_version_id="smoke-version",
    algorithm_key="smoke-algorithm",
    image="cv-platform/smoke:latest",
    container_name="cv-algorithm-smoke",
)
assert len(service.ensure_replicas(spec, 3)) == 3
assert len(service.ensure_replicas(spec, 1)) == 1
assert runtime.created == 3 and len(runtime.removed) == 2
print("manager smoke tests passed")
