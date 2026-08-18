from __future__ import annotations

from threading import RLock

from ..domain.models import AlgorithmInstance


class InMemoryInstanceRepository:
    def __init__(self) -> None:
        self._items: dict[str, AlgorithmInstance] = {}
        self._lock = RLock()

    def list(self) -> list[AlgorithmInstance]:
        with self._lock:
            return sorted(self._items.values(), key=lambda item: item.created_at, reverse=True)

    def get(self, instance_id: str) -> AlgorithmInstance | None:
        with self._lock:
            return self._items.get(instance_id)

    def find_by_algorithm(self, algorithm_version_id: str) -> AlgorithmInstance | None:
        with self._lock:
            candidates = [
                item
                for item in self._items.values()
                if item.algorithm_version_id == algorithm_version_id
            ]
            healthy = [item for item in candidates if item.status.value == "healthy"]
            if healthy:
                return min(healthy, key=lambda item: item.last_used_at or item.updated_at)
            return candidates[0] if candidates else None

    def find_all_by_algorithm(self, algorithm_version_id: str) -> list[AlgorithmInstance]:
        with self._lock:
            return [
                item
                for item in self._items.values()
                if item.algorithm_version_id == algorithm_version_id
            ]

    def save(self, instance: AlgorithmInstance) -> None:
        with self._lock:
            self._items[instance.id] = instance

    def delete(self, instance_id: str) -> None:
        with self._lock:
            self._items.pop(instance_id, None)
