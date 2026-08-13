from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from uuid import UUID, uuid4

from ...core.errors import ApplicationError
from ...core.project_context import DEFAULT_PROJECT_ID


class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    name: str
    description: str
    created_by: UUID
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ProjectMembership:
    project_id: UUID
    user_id: UUID
    role: ProjectRole
    joined_at: datetime


class InMemoryProjectService:
    def __init__(self, admin_user_id: UUID) -> None:
        now = datetime.now(UTC)
        self._projects = {
            DEFAULT_PROJECT_ID: Project(
                DEFAULT_PROJECT_ID,
                "默认项目",
                "本地无数据库模式的默认工作空间",
                admin_user_id,
                now,
            )
        }
        self._memberships = {
            (DEFAULT_PROJECT_ID, admin_user_id): ProjectMembership(
                DEFAULT_PROJECT_ID,
                admin_user_id,
                ProjectRole.OWNER,
                now,
            )
        }
        self._lock = RLock()

    def create(self, name: str, description: str, user_id: UUID) -> Project:
        project = Project(uuid4(), name.strip(), description.strip(), user_id, datetime.now(UTC))
        with self._lock:
            self._projects[project.id] = project
            self._memberships[(project.id, user_id)] = ProjectMembership(
                project.id, user_id, ProjectRole.OWNER, project.created_at
            )
        return project

    def list_for_user(self, user_id: UUID) -> list[tuple[Project, ProjectMembership]]:
        with self._lock:
            memberships = [
                membership
                for membership in self._memberships.values()
                if membership.user_id == user_id
            ]
            return sorted(
                [(self._projects[item.project_id], item) for item in memberships],
                key=lambda item: item[0].created_at,
            )

    def first_project_id(self, user_id: UUID) -> UUID | None:
        projects = self.list_for_user(user_id)
        return projects[0][0].id if projects else None

    def add_member(
        self,
        project_id: UUID,
        actor_id: UUID,
        user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMembership:
        self.require_access(project_id, actor_id, write=True, owner_only=True)
        membership = ProjectMembership(project_id, user_id, role, datetime.now(UTC))
        with self._lock:
            self._memberships[(project_id, user_id)] = membership
        return membership

    def list_members(self, project_id: UUID, actor_id: UUID) -> list[ProjectMembership]:
        self.require_access(project_id, actor_id)
        with self._lock:
            return [
                item for item in self._memberships.values() if item.project_id == project_id
            ]

    def require_access(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        write: bool = False,
        owner_only: bool = False,
    ) -> ProjectMembership:
        with self._lock:
            membership = self._memberships.get((project_id, user_id))
        if membership is None:
            raise ApplicationError("PROJECT_FORBIDDEN", "无权访问该项目", 403)
        if owner_only and membership.role is not ProjectRole.OWNER:
            raise ApplicationError("PROJECT_FORBIDDEN", "需要项目所有者权限", 403)
        if write and membership.role is ProjectRole.VIEWER:
            raise ApplicationError("PROJECT_READ_ONLY", "项目访客只有读取权限", 403)
        return membership
