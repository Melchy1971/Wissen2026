from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.logging import reset_observability_context, set_observability_context


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("x-correlation-id") or str(uuid4())
        request.state.correlation_id = correlation_id
        request.state.request_started_at = perf_counter()
        token = set_observability_context(correlation_id=correlation_id)
        try:
            response = await call_next(request)
        finally:
            reset_observability_context(token)

        response.headers["x-correlation-id"] = correlation_id
        return response