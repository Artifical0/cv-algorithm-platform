from threading import RLock
from uuid import UUID

from ..domain.entities import InferenceTask


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, InferenceTask] = {}
        self._lock = RLock()

    def add(self, task: InferenceTask) -> None:
        with self._lock:
            self._items[task.id] = task

    def save(self, task: InferenceTask) -> None:
        with self._lock:
            if task.id not in self._items:
                raise KeyError(f"task does not exist: {task.id}")
            self._items[task.id] = task

    def list(self) -> list[InferenceTask]:
        with self._lock:
            return sorted(self._items.values(), key=lambda item: item.created_at, reverse=True)

    def get(self, task_id: UUID) -> InferenceTask | None:
        with self._lock:
            return self._items.get(task_id)
