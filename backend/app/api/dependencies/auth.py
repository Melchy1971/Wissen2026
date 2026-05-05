from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request

from app.core.errors import AdminRequiredApiError, ApiError, AuthRequiredApiError, WorkspaceAccessForbiddenApiError
from app.services.auth import AuthenticatedContext


@dataclass(frozen=True)
class RequestAuthContext:
    session_id: str
    user_id: str
    login: str
    display_name: str
    workspace_id: str
    role: str


def get_request_auth_context(request: Request) -> RequestAuthContext:
    context = getattr(request.state, "auth_context", None)
    if context is None:
        raise AuthRequiredApiError()
    if not isinstance(context, AuthenticatedContext):
        raise ApiError(message="Invalid auth context")
    return RequestAuthContext(
        session_id=context.session_id,
        user_id=context.user_id,
        login=context.login,
        display_name=context.display_name,
        workspace_id=context.workspace_id,
        role=context.role,
    )


def require_workspace_member(context: RequestAuthContext = Depends(get_request_auth_context)) -> RequestAuthContext:
    if not context.workspace_id:
        raise WorkspaceAccessForbiddenApiError()
    return context


def require_workspace_admin(context: RequestAuthContext = Depends(require_workspace_member)) -> RequestAuthContext:
    if context.role not in {"owner", "admin"}:
        raise AdminRequiredApiError()
    return context