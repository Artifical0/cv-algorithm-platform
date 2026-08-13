from dataclasses import dataclass

from ..modules.algorithms.infrastructure.memory_repository import InMemoryAlgorithmRepository
from ..modules.algorithms.infrastructure.memory_repository import InMemoryBuildJobRepository
from ..modules.algorithms.infrastructure.package_storage import AlgorithmPackageStorage
from ..modules.algorithms.infrastructure.manager_build_gateway import ManagerBuildGateway
from ..modules.algorithms.infrastructure.local_build_queue import LocalBuildQueue
from ..modules.assets.infrastructure.local_storage import LocalAssetStorage
from ..modules.assets.infrastructure.memory_repository import InMemoryAssetRepository
from ..modules.scheduling.cluster_gateway import ClusterAlgorithmManagerGateway
from ..modules.tasks.infrastructure.memory_repository import InMemoryTaskRepository
from ..modules.tasks.infrastructure.http_prediction_gateway import (
    HttpAlgorithmPredictionGateway,
)
from ..modules.tasks.infrastructure.local_queue import LocalTaskQueue
from ..modules.instances.application.service import RuntimeInstanceService
from ..modules.comparisons.infrastructure.memory_repository import (
    InMemoryComparisonRepository,
)
from ..modules.security.service import (
    InMemoryAuditLog,
    LocalAuthService,
    SlidingWindowRateLimiter,
)
from ..modules.media.service import InMemoryMediaSourceService
from ..modules.media.worker_gateway import MediaWorkerGateway
from ..modules.media.runs import MediaRunService
from ..modules.media.storage import LocalVideoStorage
from ..modules.workflows.service import InMemoryWorkflowService
from ..modules.operations.service import OperationsService
from ..modules.projects.service import InMemoryProjectService
from .config import get_settings


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    algorithms: InMemoryAlgorithmRepository
    build_jobs: InMemoryBuildJobRepository
    package_storage: AlgorithmPackageStorage
    build_gateway: ManagerBuildGateway
    build_queue: LocalBuildQueue
    assets: InMemoryAssetRepository
    asset_storage: LocalAssetStorage
    tasks: InMemoryTaskRepository
    algorithm_manager: ClusterAlgorithmManagerGateway
    task_queue: LocalTaskQueue
    comparisons: InMemoryComparisonRepository
    auth: LocalAuthService
    audit_log: InMemoryAuditLog
    rate_limiter: SlidingWindowRateLimiter
    media_sources: InMemoryMediaSourceService
    media_worker: MediaWorkerGateway
    media_runs: MediaRunService
    video_storage: LocalVideoStorage
    workflows: InMemoryWorkflowService
    operations: OperationsService
    projects: InMemoryProjectService


def build_container() -> ApplicationContainer:
    settings = get_settings()
    algorithms = InMemoryAlgorithmRepository()
    build_jobs = InMemoryBuildJobRepository()
    assets = InMemoryAssetRepository()
    tasks = InMemoryTaskRepository()
    media_sources = InMemoryMediaSourceService()
    media_worker = MediaWorkerGateway(settings.media_worker_url)
    manager = ClusterAlgorithmManagerGateway(settings.algorithm_manager_url)
    build_gateway = ManagerBuildGateway(settings.algorithm_manager_url)
    build_queue = LocalBuildQueue(algorithms, build_jobs, build_gateway)
    instances = RuntimeInstanceService(algorithms, manager)
    task_queue = LocalTaskQueue(
        tasks,
        algorithms,
        assets,
        instances,
        HttpAlgorithmPredictionGateway(settings.prediction_timeout_seconds),
        settings.task_worker_count,
    )
    auth = LocalAuthService(
        settings.admin_username,
        settings.admin_password,
        settings.session_ttl_seconds,
    )
    return ApplicationContainer(
        algorithms=algorithms,
        build_jobs=build_jobs,
        package_storage=AlgorithmPackageStorage(
            settings.package_root,
            settings.max_package_bytes,
            settings.max_package_extracted_bytes,
            settings.max_package_files,
        ),
        build_gateway=build_gateway,
        build_queue=build_queue,
        assets=assets,
        asset_storage=LocalAssetStorage(
            settings.storage_root,
            settings.algorithm_data_root,
            settings.max_upload_bytes,
            settings.max_image_pixels,
        ),
        tasks=tasks,
        algorithm_manager=manager,
        task_queue=task_queue,
        comparisons=InMemoryComparisonRepository(),
        auth=auth,
        audit_log=InMemoryAuditLog(),
        rate_limiter=SlidingWindowRateLimiter(
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        ),
        media_sources=media_sources,
        media_worker=media_worker,
        media_runs=MediaRunService(media_sources, media_worker),
        video_storage=LocalVideoStorage(
            settings.storage_root,
            settings.max_video_upload_bytes,
        ),
        workflows=InMemoryWorkflowService(algorithms),
        operations=OperationsService(algorithms, tasks, instances),
        projects=InMemoryProjectService(auth.initial_admin_id),
    )
