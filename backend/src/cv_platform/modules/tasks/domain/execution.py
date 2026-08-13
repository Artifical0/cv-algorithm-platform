from typing import Protocol

from cv_algorithm_sdk import AlgorithmResult

from ...instances.domain.models import RuntimeInstance


class AlgorithmPredictionGateway(Protocol):
    def predict(
        self,
        instance: RuntimeInstance,
        request_id: str,
        asset_uri: str,
        parameters: dict[str, object],
    ) -> AlgorithmResult: ...


class TaskQueue(Protocol):
    def submit(self, task_id: str) -> None: ...

    def cancel(self, task_id: str) -> None: ...

    def shutdown(self) -> None: ...
