from typing import Protocol
from uuid import UUID

from .entities import InferenceTask


class TaskRepository(Protocol):
    def add(self, task: InferenceTask) -> None: ...

    def save(self, task: InferenceTask) -> None: ...

    def list(self) -> list[InferenceTask]: ...

    def get(self, task_id: UUID) -> InferenceTask | None: ...
