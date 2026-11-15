from pathlib import Path

import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from database.connection import engine
from database import models
from api.endpoints import router as api_router
from rate_limit import limiter
from logging_config import RequestLoggingMiddleware, configure_logging


def _build_cors_config():
    """Resolve CORS origins from centralised settings.

    Credentials are enabled when explicit origins are configured.
    """
    origins = settings.cors_origin_list
    allow_credentials = True
    return origins, allow_credentials


# Configure structured logging as early as possible.
configure_logging(debug=settings.DEBUG)

# Initialize Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Vedic Astrology Calculation Engine and Database Services",
    version=settings.APP_VERSION,
)

# Wire up rate limiting.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request/response logging (added before CORS so it sees all requests).
app.add_middleware(RequestLoggingMiddleware)

_cors_origins, _cors_credentials = _build_cors_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# Include the public calculation API.
app.include_router(api_router, prefix="/api")


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Parashari Jyotish Software API is running.",
        "version": settings.APP_VERSION,
    }


@app.get("/health/live")
def liveness():
    """Process liveness probe; it deliberately avoids external dependencies."""
    return {"status": "online", "version": settings.APP_VERSION}


@app.get("/health")
@app.get("/health/ready")
def readiness(response: Response):
    """Readiness probe covering the database and required ephemeris asset."""
    checks = {"database": "ok", "ephemeris": "ok"}

    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as exc:  # pragma: no cover - operational path
        checks["database"] = f"error: {exc.__class__.__name__}"

    ephemeris_candidates = (
        Path(__file__).resolve().parent.parent / "de421.bsp",
        Path(__file__).resolve().parent / "de421.bsp",
    )
    if not any(path.is_file() and path.stat().st_size > 0 for path in ephemeris_candidates):
        checks["ephemeris"] = "missing"

    is_ready = all(value == "ok" for value in checks.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "online" if is_ready else "degraded",
        "version": settings.APP_VERSION,
        "calculation_version": settings.CALCULATION_VERSION,
        "checks": checks,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
