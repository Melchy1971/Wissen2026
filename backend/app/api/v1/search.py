from typing import Annotated, Iterator
from time import perf_counter

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import RequestAuthContext, require_workspace_member
from app.core.database import DatabaseConfigurationError
from app.core.errors import ApiError, InvalidQueryApiError, ServiceUnavailableApiError
from app.db.session import get_session
from app.observability.logging import bind_observability_context, log_event
from app.schemas.search import SearchChunkResult
from app.services.search_service import InvalidSearchQueryError, SearchService


router = APIRouter(prefix="/search", tags=["search"])


def get_search_service() -> Iterator[SearchService]:
    try:
        for session in get_session():
            yield SearchService.from_session(session)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.get("/chunks", response_model=list[SearchChunkResult])
def search_chunks(
    auth_context: Annotated[RequestAuthContext, Depends(require_workspace_member)],
    q: Annotated[str, Query(min_length=1)],
    service: Annotated[SearchService, Depends(get_search_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SearchChunkResult]:
    start_time = perf_counter()
    workspace_id = auth_context.workspace_id
    bind_observability_context(workspace_id=workspace_id)
    try:
        results = service.search_chunks(workspace_id=workspace_id, query=q, limit=limit, offset=offset, filters=None)
        log_event(
            "search_executed",
            workspace_id=workspace_id,
            duration_ms=int((perf_counter() - start_time) * 1000),
            status="completed",
        )
        return results
    except InvalidSearchQueryError as exc:
        log_event(
            "search_executed",
            workspace_id=workspace_id,
            duration_ms=int((perf_counter() - start_time) * 1000),
            status="failed",
            error_code="INVALID_QUERY",
        )
        raise InvalidQueryApiError(message=str(exc), details={"q": q, "workspace_id": workspace_id}) from exc
    except DatabaseConfigurationError as exc:
        log_event(
            "search_executed",
            workspace_id=workspace_id,
            duration_ms=int((perf_counter() - start_time) * 1000),
            status="failed",
            error_code="SERVICE_UNAVAILABLE",
        )
        raise ApiError(message=str(exc)) from exc
    except ServiceUnavailableApiError:
        log_event(
            "search_executed",
            workspace_id=workspace_id,
            duration_ms=int((perf_counter() - start_time) * 1000),
            status="failed",
            error_code="SERVICE_UNAVAILABLE",
        )
        raise