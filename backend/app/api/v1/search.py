from typing import Annotated, Iterator

from fastapi import APIRouter, Depends, Query

from app.core.database import DatabaseConfigurationError
from app.core.errors import ApiError, InvalidQueryApiError, ServiceUnavailableApiError
from app.db.session import get_session
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
    workspace_id: Annotated[str, Query(min_length=1)],
    q: Annotated[str, Query(min_length=1)],
    service: Annotated[SearchService, Depends(get_search_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SearchChunkResult]:
    try:
        return service.search_chunks(workspace_id=workspace_id, query=q, limit=limit, offset=offset, filters=None)
    except InvalidSearchQueryError as exc:
        raise InvalidQueryApiError(message=str(exc), details={"q": q, "workspace_id": workspace_id}) from exc
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc
    except ServiceUnavailableApiError:
        raise