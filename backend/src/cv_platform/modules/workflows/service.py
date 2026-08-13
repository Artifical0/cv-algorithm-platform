from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from threading import Event, RLock
from time import sleep
from uuid import UUID

from ...core.errors import ApplicationError
from ..algorithms.domain.repositories import AlgorithmRepository
from cv_algorithm_sdk import TaskStatus

from ..tasks.application.service import TaskService
from .domain import (
    Workflow,
    WorkflowMode,
    WorkflowNode,
    WorkflowRun,
    WorkflowRunStatus,
)
from ...core.project_context import DEFAULT_PROJECT_ID


class InMemoryWorkflowService:
    def __init__(self, algorithms: AlgorithmRepository) -> None:
        self._algorithms = algorithms
        self._items: dict[UUID, Workflow] = {}
        self._runs: dict[UUID, WorkflowRun] = {}
        self._cancel_events: dict[UUID, Event] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cv-workflow")
        self._lock = RLock()

    def create(
        self,
        name: str,
        mode: WorkflowMode,
        nodes: list[WorkflowNode],
        project_id: UUID = DEFAULT_PROJECT_ID,
        actor: str = "local-admin",
    ) -> Workflow:
        self._validate(nodes)
        if any(
            self._algorithms.get(node.algorithm_version_id).project_id != project_id
            for node in nodes
        ):
            raise ApplicationError("ALGORITHM_NOT_FOUND", "工作流引用的算法不存在", 404)
        workflow = Workflow.create(name.strip(), mode, nodes, project_id, actor)
        with self._lock:
            self._items[workflow.id] = workflow
        return workflow

    def list(self, project_id: UUID | None = None) -> list[Workflow]:
        with self._lock:
            return sorted(
                [item for item in self._items.values() if project_id is None or item.project_id == project_id],
                key=lambda item: item.created_at,
                reverse=True,
            )

    def get(self, workflow_id: UUID, project_id: UUID | None = None) -> Workflow:
        with self._lock:
            workflow = self._items.get(workflow_id)
        if workflow is None or (project_id is not None and workflow.project_id != project_id):
            raise ApplicationError("WORKFLOW_NOT_FOUND", "算法工作流不存在", 404)
        return workflow

    def start(
        self,
        workflow_id: UUID,
        asset_id: UUID,
        tasks: TaskService,
        project_id: UUID = DEFAULT_PROJECT_ID,
    ) -> WorkflowRun:
        self.get(workflow_id, project_id)
        run = WorkflowRun.queued(workflow_id, asset_id, project_id)
        with self._lock:
            self._runs[run.id] = run
            self._cancel_events[run.id] = Event()
        self._executor.submit(self._execute, run.id, tasks)
        return run

    def get_run(self, run_id: UUID, project_id: UUID | None = None) -> WorkflowRun:
        with self._lock:
            run = self._runs.get(run_id)
        if run is None or (project_id is not None and run.project_id != project_id):
            raise ApplicationError("WORKFLOW_RUN_NOT_FOUND", "工作流运行不存在", 404)
        return run

    def list_runs(self, project_id: UUID | None = None) -> list[WorkflowRun]:
        with self._lock:
            return sorted(
                [item for item in self._runs.values() if project_id is None or item.project_id == project_id],
                key=lambda item: item.created_at,
                reverse=True,
            )

    def cancel(self, run_id: UUID, tasks: TaskService) -> WorkflowRun:
        run = self.get_run(run_id)
        with self._lock:
            event = self._cancel_events.setdefault(run_id, Event())
            event.set()
        for task_id in run.node_tasks.values():
            task = tasks.get_task(task_id)
            if task.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
                tasks.cancel(task_id)
        return self._update_run(run, WorkflowRunStatus.CANCELLED)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _execute(self, run_id: UUID, tasks: TaskService) -> None:
        run = self.get_run(run_id)
        workflow = self.get(run.workflow_id)
        run = self._update_run(run, WorkflowRunStatus.RUNNING)
        pending = {node.id: node for node in workflow.nodes}
        completed: set[str] = set()
        try:
            while pending:
                if self._cancel_events[run_id].is_set():
                    return
                ready = [
                    node
                    for node in pending.values()
                    if set(node.depends_on).issubset(completed)
                ]
                if workflow.mode is WorkflowMode.SEQUENTIAL:
                    ready = ready[:1]
                node_tasks = {
                    node.id: tasks.create_task(
                        node.algorithm_version_id,
                        node.parameters,
                        asset_id=run.asset_id,
                    )
                    for node in ready
                }
                run = replace(
                    run,
                    node_tasks={
                        **run.node_tasks,
                        **{node_id: task.id for node_id, task in node_tasks.items()},
                    },
                    updated_at=datetime.now(UTC),
                )
                with self._lock:
                    self._runs[run.id] = run
                terminal = set()
                while len(terminal) < len(node_tasks):
                    if self._cancel_events[run_id].is_set():
                        return
                    for node_id, task in node_tasks.items():
                        current = tasks.get_task(task.id)
                        if current.status in {TaskStatus.FAILED, TaskStatus.CANCELLED}:
                            raise RuntimeError(
                                current.error_message or f"workflow node {node_id} failed"
                            )
                        if current.status is TaskStatus.COMPLETED:
                            terminal.add(node_id)
                    if len(terminal) < len(node_tasks):
                        sleep(0.25)
                for node_id in terminal:
                    completed.add(node_id)
                    pending.pop(node_id)
            self._update_run(run, WorkflowRunStatus.COMPLETED)
        except Exception as exc:
            self._update_run(run, WorkflowRunStatus.FAILED, str(exc))

    def _update_run(
        self,
        run: WorkflowRun,
        status: WorkflowRunStatus,
        error_message: str | None = None,
    ) -> WorkflowRun:
        updated = replace(
            run,
            status=status,
            error_message=error_message,
            updated_at=datetime.now(UTC),
        )
        with self._lock:
            self._runs[updated.id] = updated
        return updated

    def _validate(self, nodes: list[WorkflowNode]) -> None:
        if not nodes or len(nodes) > 32:
            raise ApplicationError("WORKFLOW_INVALID", "工作流需要 1 到 32 个节点")
        node_ids = [node.id for node in nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ApplicationError("WORKFLOW_INVALID", "工作流节点 ID 必须唯一")
        dependencies = {node.id: set(node.depends_on) for node in nodes}
        if any(not values.issubset(node_ids) for values in dependencies.values()):
            raise ApplicationError("WORKFLOW_INVALID", "工作流依赖节点不存在")
        if any(node.id in dependencies[node.id] for node in nodes):
            raise ApplicationError("WORKFLOW_INVALID", "工作流节点不能依赖自身")
        pending = {key: set(value) for key, value in dependencies.items()}
        while pending:
            ready = {key for key, values in pending.items() if not values}
            if not ready:
                raise ApplicationError("WORKFLOW_CYCLE", "工作流存在循环依赖")
            pending = {
                key: values - ready
                for key, values in pending.items()
                if key not in ready
            }
        for node in nodes:
            algorithm = self._algorithms.get(node.algorithm_version_id)
            if algorithm is None:
                raise ApplicationError("ALGORITHM_NOT_FOUND", "工作流引用的算法不存在", 404)
            try:
                algorithm.manifest.resolve_parameters(node.parameters)
            except ValueError as exc:
                raise ApplicationError("PARAMETER_INVALID", str(exc)) from exc
