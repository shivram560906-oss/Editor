"""Structured request/response logging middleware.

Logs every HTTP request with method, path, status, duration and client IP in a
parseable format. In production this pairs well with a JSON log collector or
Sentry. Uses the standard library ``logging`` module so no extra dependency is
required.
"""
from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("jyotish.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a request-id and log each request's lifecycle."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        start = time.perf_counter()

        # Make the id available to handlers / error responses if needed.
        request.state.request_id = request_id

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request error method=%s path=%s request_id=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.1f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


def configure_logging(debug: bool = False) -> None:
    """Configure root logging once at startup.

    Idempotent: re-calling it will not duplicate handlers.
    """
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()
    if not any(getattr(h, "_jyotish_configured", False) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handler._jyotish_configured = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    root.setLevel(level)
