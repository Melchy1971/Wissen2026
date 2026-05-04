from fastapi import APIRouter

from app.core.config import settings
from app.core.database import DatabaseConfigurationError, check_database_connection
from app.core.errors import ServiceUnavailableApiError

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@router.get("/health/db")
def database_health() -> dict[str, str]:
    try:
        check_database_connection()
    except DatabaseConfigurationError as exc:
        raise ServiceUnavailableApiError(message=str(exc)) from exc
    except Exception as exc:
        raise ServiceUnavailableApiError(message="Database connection check failed") from exc

    return {"status": "ok"}
