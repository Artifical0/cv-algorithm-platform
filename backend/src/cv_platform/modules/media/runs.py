from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from uuid import UUID, uuid4

from ...core.errors import ApplicationError
from ..tasks.application.service import TaskService
from ..assets.application.service import AssetService
from .service import InMemoryMediaSourceService
from .worker_gateway import MediaWorkerGateway
from ...core.project_context import DEFAULT_PROJECT_ID


class MediaRunStatus(StrEnum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MediaInferenceRun:
    id: UUID
    source_id: UUID
    algorithm_version_id: UUID
    status: MediaRunStatus
    frame_task_ids: tuple[UUID, ...]
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None
    project_id: UUID = DEFAULT_PROJECT_ID

    @classmethod
    def queued(
        cls,
        source_id: UUID,
        algorithm_version_id: UUID,
        project_id: UUID = DEFAULT_PROJECT_ID,
    ) -> "MediaInferenceRun":
        now = datetime.now(UTC)
        return cls(uuid4(), source_id, algorithm_version_id, MediaRunStatus.QUEUED, (), now, now, project_id=project_id)


class MediaRunService:
    def __init__(
        self,
        sources: InMemoryMediaSourceService,
        worker: MediaWorkerGateway,
    ) -> None:
        self._sources = sources
        self._worker = worker
        self._items: dict[UUID, MediaInferenceRun] = {}
        self._lock = RLock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cv-media-run")

    def create(
        self,
        source_id: UUID,
        algorithm_version_id: UUID,
        interval_seconds: float,
        max_frames: int,
        parameters: dict[str, object],
        tasks: TaskService,
        assets: AssetService,
        project_id: UUID = DEFAULT_PROJECT_ID,
    ) -> MediaInferenceRun:
        self._sources.get(source_id, project_id)
        run = MediaInferenceRun.queued(source_id, algorithm_version_id, project_id)
        with self._lock:
            self._items[run.id] = run
        self._executor.submit(
            self._execute,
            run.id,
            interval_seconds,
            max_frames,
            parameters,
            tasks,
            assets,
        )
        return run

    def get(self, run_id: UUID, project_id: UUID | None = None) -> MediaInferenceRun:
        with self._lock:
            run = self._items.get(run_id)
        if run is None or (project_id is not None and run.project_id != project_id):
            raise ApplicationError("MEDIA_RUN_NOT_FOUND", "媒体推理运行不存在", 404)
        return run

    def list(self, project_id: UUID | None = None) -> list[MediaInferenceRun]:
        with self._lock:
            return sorted(
                [item for item in self._items.values() if project_id is None or item.project_id == project_id],
                key=lambda item: item.created_at,
                reverse=True,
            )

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _execute(
        self,
        run_id: UUID,
        interval_seconds: float,
        max_frames: int,
        parameters: dict[str, object],
        tasks: TaskService,
        assets: AssetService,
    ) -> None:
        run = self.get(run_id)
        try:
            run = self._save(replace(run, status=MediaRunStatus.EXTRACTING))
            source = self._sources.get(run.source_id)
            frames = self._worker.extract(
                source.uri,
                interval_seconds,
                max_frames,
                run.id,
            )
            if not frames:
                raise ApplicationError("MEDIA_EMPTY", "媒体源没有可提取的画面", 422)
            task_ids = []
            for frame in frames:
                asset = assets.register_local_image(
                    str(frame["relative_path"]),
                    f"frame-{int(frame['index']):08d}.jpg",
                )
                task = tasks.create_task(
                    run.algorithm_version_id,
                    parameters,
                    asset_id=asset.id,
                )
                task_ids.append(task.id)
            self._save(
                replace(
                    run,
                    status=MediaRunStatus.RUNNING,
                    frame_task_ids=tuple(task_ids),
                )
            )
        except Exception as exc:
            self._save(
                replace(
                    run,
                    status=MediaRunStatus.FAILED,
                    error_message=str(exc),
                )
            )

    def refresh(self, run_id: UUID, tasks: TaskService) -> MediaInferenceRun:
        run = self.get(run_id)
        if run.status is not MediaRunStatus.RUNNING:
            return run
        frame_tasks = [tasks.get_task(task_id) for task_id in run.frame_task_ids]
        if any(task.status.value == "failed" for task in frame_tasks):
            return self._save(replace(run, status=MediaRunStatus.FAILED, error_message="帧任务失败"))
        if frame_tasks and all(task.status.value == "completed" for task in frame_tasks):
            return self._save(replace(run, status=MediaRunStatus.COMPLETED))
        return run

    def _save(self, run: MediaInferenceRun) -> MediaInferenceRun:
        run = replace(run, updated_at=datetime.now(UTC))
        with self._lock:
            self._items[run.id] = run
        return run
