from threading import RLock
from uuid import UUID

from ..domain.entities import AlgorithmVersion, BuildJob


class InMemoryAlgorithmRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, AlgorithmVersion] = {}
        self._lock = RLock()

    def add(self, algorithm: AlgorithmVersion) -> None:
        with self._lock:
            if any(
                item.project_id == algorithm.project_id
                and item.manifest.id == algorithm.manifest.id
                and item.manifest.version == algorithm.manifest.version
                for item in self._items.values()
            ):
                raise ValueError("algorithm version already exists in project")
            self._items[algorithm.id] = algorithm

    def list(self) -> list[AlgorithmVersion]:
        with self._lock:
            return sorted(self._items.values(), key=lambda item: item.created_at)

    def get(self, algorithm_id: UUID) -> AlgorithmVersion | None:
        with self._lock:
            return self._items.get(algorithm_id)

    def find_version(self, key: str, version: str) -> AlgorithmVersion | None:
        with self._lock:
            return next(
                (
                    item
                    for item in self._items.values()
                    if item.manifest.id == key and item.manifest.version == version
                ),
                None,
            )

    def save(self, algorithm: AlgorithmVersion) -> None:
        with self._lock:
            if algorithm.id not in self._items:
                raise KeyError(f"algorithm does not exist: {algorithm.id}")
            self._items[algorithm.id] = algorithm

    def delete(self, algorithm_id: UUID) -> None:
        with self._lock:
            self._items.pop(algorithm_id, None)


class InMemoryBuildJobRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, BuildJob] = {}
        self._lock = RLock()

    def add(self, job: BuildJob) -> None:
        with self._lock:
            self._items[job.id] = job

    def save(self, job: BuildJob) -> None:
        with self._lock:
            self._items[job.id] = job

    def get(self, job_id: UUID) -> BuildJob | None:
        with self._lock:
            return self._items.get(job_id)
