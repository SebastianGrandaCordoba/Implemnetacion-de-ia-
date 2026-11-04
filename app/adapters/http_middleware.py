"""HTTP middleware: correlates logs between the Spring backend and this service."""

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("fairteam.http")
HEADER = "X-Request-ID"
_SAFE_ID = re.compile(r"[A-Za-z0-9._-]{8,64}")


def request_id_from(value: str | None) -> str:
    """Reuses a well-formed incoming id, otherwise creates one, so ids are never attacker-shaped."""
    if value and _SAFE_ID.fullmatch(value):
        return value
    return uuid.uuid4().hex


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request_id_from(request.headers.get(HEADER))
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers[HEADER] = request_id
        response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.0f}"
        if request.url.path != "/health":
            logger.info("%s %s -> %s in %.0fms [%s]", request.method, request.url.path,
                        response.status_code, elapsed_ms, request_id)
        return response
