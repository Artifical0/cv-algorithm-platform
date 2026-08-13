import httpx
from pydantic import TypeAdapter, ValidationError

from cv_algorithm_sdk import AlgorithmResult

from ....core.errors import ApplicationError
from ...instances.domain.models import RuntimeInstance


result_adapter = TypeAdapter(AlgorithmResult)


class HttpAlgorithmPredictionGateway:
    def __init__(self, timeout_seconds: float) -> None:
        self._timeout = timeout_seconds

    def predict(
        self,
        instance: RuntimeInstance,
        request_id: str,
        asset_uri: str,
        parameters: dict[str, object],
    ) -> AlgorithmResult:
        try:
            response = httpx.post(
                f"{instance.endpoint}/predict",
                json={
                    "request_id": request_id,
                    "input": {"asset_uri": asset_uri},
                    "parameters": parameters,
                },
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise ApplicationError("PREDICTION_TIMEOUT", "算法推理超时", 504) from exc
        except httpx.HTTPError as exc:
            raise ApplicationError("ALGORITHM_UNAVAILABLE", "无法连接算法容器", 502) from exc
        if response.is_error:
            raise ApplicationError(
                "PREDICTION_FAILED",
                f"算法容器返回 HTTP {response.status_code}",
                502,
            )
        try:
            return result_adapter.validate_python(response.json())
        except (ValueError, ValidationError) as exc:
            raise ApplicationError(
                "RESULT_SCHEMA_INVALID",
                "算法返回结果不符合平台 Result 1.0 协议",
                502,
            ) from exc
