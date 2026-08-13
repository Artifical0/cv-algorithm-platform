from uuid import UUID

from fastapi import Request

from .errors import ApplicationError


def project_id_from(request: Request) -> UUID:
    project_id = getattr(request.state, "project_id", None)
    if not isinstance(project_id, UUID):
        raise ApplicationError("PROJECT_REQUIRED", "缺少项目上下文", 400)
    return project_id
