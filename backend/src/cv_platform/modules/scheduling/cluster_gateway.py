from dataclasses import dataclass, replace
from threading import RLock

from psycopg.types.json import Jsonb

from ...core.database import Database
from ...core.errors import ApplicationError
from ..instances.domain.models import RuntimeInstance, RuntimeRequest
from ..instances.infrastructure.http_gateway import HttpAlgorithmManagerGateway


@dataclass(frozen=True, slots=True)
class RuntimeNode:
    id: str
    name: str
    manager_url: str
    enabled: bool = True


class ClusterAlgorithmManagerGateway:
    def __init__(
        self,
        default_manager_url: str,
        database: Database | None = None,
    ) -> None:
        self._database = database
        self._nodes: dict[str, RuntimeNode] = {
            "local": RuntimeNode("local", "Local Docker Node", default_manager_url)
        }
        self._instance_routes: dict[str, str] = {}
        self._lock = RLock()
        if self._database is not None:
            with self._database.connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO runtime_nodes (
                        id, name, manager_url, enabled, metadata, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, now(), now())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        manager_url = EXCLUDED.manager_url,
                        updated_at = now()
                    """,
                    ("local", "Local Docker Node", default_manager_url, True, Jsonb({})),
                )

    def register_node(self, node: RuntimeNode) -> RuntimeNode:
        if not node.manager_url.startswith(("http://", "https://")):
            raise ApplicationError("NODE_INVALID", "节点 Manager URL 必须使用 HTTP(S)")
        if self._database is None:
            with self._lock:
                self._nodes[node.id] = node
        else:
            with self._database.connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO runtime_nodes (
                        id, name, manager_url, enabled, metadata, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, now(), now())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        manager_url = EXCLUDED.manager_url,
                        enabled = EXCLUDED.enabled,
                        updated_at = now()
                    """,
                    (node.id, node.name, node.manager_url, node.enabled, Jsonb({})),
                )
        return node

    def list_nodes(self) -> list[RuntimeNode]:
        if self._database is None:
            with self._lock:
                return list(self._nodes.values())
        with self._database.connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT id, name, manager_url, enabled FROM runtime_nodes ORDER BY id")
            return [
                RuntimeNode(
                    id=str(row["id"]),
                    name=str(row["name"]),
                    manager_url=str(row["manager_url"]),
                    enabled=bool(row["enabled"]),
                )
                for row in cursor.fetchall()
            ]

    def list_instances(self) -> list[RuntimeInstance]:
        instances = []
        for node in self._enabled_nodes():
            try:
                node_instances = self._gateway(node).list_instances()
                instances.extend(node_instances)
                with self._lock:
                    for instance in node_instances:
                        self._instance_routes[instance.id] = node.id
            except ApplicationError:
                continue
        return instances

    def ensure_running(self, request: RuntimeRequest) -> RuntimeInstance:
        current = [
            instance
            for instance in self.list_instances()
            if instance.algorithm_version_id == request.algorithm_version_id
            and instance.status == "healthy"
        ]
        if current:
            selected = min(
                current,
                key=lambda item: item.last_used_at or item.updated_at,
            )
            return self._gateway_for_instance(selected.id).ensure_running(request)
        candidates = []
        for node in self._enabled_nodes():
            gateway = self._gateway(node)
            try:
                instances = gateway.list_instances()
                gpus = gateway.list_gpus()
            except ApplicationError:
                continue
            best_gpu = max(
                gpus,
                key=lambda gpu: int(gpu.get("memory_total_mb", 0))
                - int(gpu.get("memory_used_mb", 0)),
                default=None,
            )
            free_gpu_memory = (
                int(best_gpu.get("memory_total_mb", 0))
                - int(best_gpu.get("memory_used_mb", 0))
                if best_gpu
                else 0
            )
            if request.device == "gpu" and not gpus:
                continue
            score = free_gpu_memory - len(instances) * 1024
            candidates.append((score, node, gateway, best_gpu))
        if not candidates:
            raise ApplicationError("RUNTIME_NODE_UNAVAILABLE", "没有可用算法运行节点", 503)
        _, node, gateway, best_gpu = max(candidates, key=lambda item: item[0])
        scheduled_request = request
        if request.device in {"gpu", "auto"} and best_gpu is not None:
            scheduled_request = replace(
                request,
                gpu_device_ids=(str(best_gpu["index"]),),
            )
        elif request.device == "auto":
            scheduled_request = replace(request, device="cpu", gpu_device_ids=())
        instance = gateway.ensure_running(scheduled_request)
        with self._lock:
            self._instance_routes[instance.id] = node.id
        return instance

    def ensure_replicas(
        self, request: RuntimeRequest, replicas: int
    ) -> list[RuntimeInstance]:
        if not 0 <= replicas <= 100:
            raise ApplicationError("REPLICA_COUNT_INVALID", "副本数必须在 0 到 100 之间")
        candidates = []
        for node in self._enabled_nodes():
            gateway = self._gateway(node)
            try:
                node_instances = gateway.list_instances()
                gpus = gateway.list_gpus()
            except ApplicationError:
                continue
            if request.device == "gpu" and not gpus:
                continue
            free_gpu_memory = max(
                (
                    int(gpu.get("memory_total_mb", 0))
                    - int(gpu.get("memory_used_mb", 0))
                    for gpu in gpus
                ),
                default=0,
            )
            gpu_ids = tuple(
                str(gpu["index"])
                for gpu in sorted(
                    gpus,
                    key=lambda item: int(item.get("memory_total_mb", 0))
                    - int(item.get("memory_used_mb", 0)),
                    reverse=True,
                )
            )
            current_count = sum(
                item.algorithm_version_id == request.algorithm_version_id
                and item.status == "healthy"
                for item in node_instances
            )
            candidates.append((node, gateway, free_gpu_memory, current_count, gpu_ids))
        if not candidates:
            if replicas == 0:
                return []
            raise ApplicationError("RUNTIME_NODE_UNAVAILABLE", "没有可用算法运行节点", 503)

        targets = {node.id: 0 for node, _, _, _, _ in candidates}
        for _ in range(replicas):
            node, _, free_memory, current_count, _ = max(
                candidates,
                key=lambda item: (
                    free_memory_score(item[2], targets[item[0].id], request.memory_mb),
                    item[3] - targets[item[0].id],
                ),
            )
            targets[node.id] += 1

        result = []
        for node, gateway, _, _, gpu_ids in candidates:
            scheduled_request = (
                replace(request, gpu_device_ids=gpu_ids)
                if request.device in {"gpu", "auto"} and gpu_ids
                else replace(request, device="cpu", gpu_device_ids=())
                if request.device == "auto"
                else request
            )
            node_instances = gateway.ensure_replicas(
                scheduled_request,
                targets[node.id],
            )
            result.extend(node_instances)
            with self._lock:
                for instance in node_instances:
                    self._instance_routes[instance.id] = node.id
        return result

    def stop(self, instance_id: str) -> RuntimeInstance:
        return self._gateway_for_instance(instance_id).stop(instance_id)

    def remove(self, instance_id: str) -> None:
        self._gateway_for_instance(instance_id).remove(instance_id)
        with self._lock:
            self._instance_routes.pop(instance_id, None)

    def logs(self, instance_id: str, tail: int = 200) -> list[str]:
        return self._gateway_for_instance(instance_id).logs(instance_id, tail)

    def list_gpus(self) -> list[dict[str, object]]:
        gpus = []
        for node in self._enabled_nodes():
            try:
                for gpu in self._gateway(node).list_gpus():
                    gpus.append({**gpu, "node_id": node.id, "node_name": node.name})
            except ApplicationError:
                continue
        return gpus

    def touch(self, instance_id: str) -> RuntimeInstance:
        return self._gateway_for_instance(instance_id).touch(instance_id)

    def _enabled_nodes(self) -> list[RuntimeNode]:
        return [node for node in self.list_nodes() if node.enabled]

    def _gateway(self, node: RuntimeNode) -> HttpAlgorithmManagerGateway:
        return HttpAlgorithmManagerGateway(node.manager_url, node_id=node.id)

    def _gateway_for_instance(self, instance_id: str) -> HttpAlgorithmManagerGateway:
        with self._lock:
            node_id = self._instance_routes.get(instance_id)
        node = next((item for item in self.list_nodes() if item.id == node_id), None)
        if node is None:
            self.list_instances()
            with self._lock:
                node_id = self._instance_routes.get(instance_id)
            node = next((item for item in self.list_nodes() if item.id == node_id), None)
        if node is None:
            raise ApplicationError("INSTANCE_NOT_FOUND", "算法实例不存在", 404)
        return self._gateway(node)


def free_memory_score(free_memory_mb: int, assigned: int, replica_memory_mb: int) -> int:
    """Prefer nodes that retain the most estimated GPU memory after assignment."""
    if free_memory_mb == 0:
        return -assigned
    return free_memory_mb - assigned * replica_memory_mb
