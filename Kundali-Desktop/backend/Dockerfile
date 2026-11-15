# ── Backend Dockerfile ──────────────────────────────────────────────
# FastAPI + Uvicorn server for the Vedic astrology backend.
# The de421.bsp ephemeris file is large (~17 MB) and lives at the repo
# root; it is copied in so planetary calculations work offline.
FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Run the API without root privileges. The data directory remains writable for
# local SQLite deployments while application source stays read-only at runtime.
RUN groupadd --system app && useradd --system --gid app --home /app app \
    && mkdir -p /app/data \
    && chown -R app:app /app

# System deps (none required beyond slim base for this project).
# Install Python dependencies first for better layer caching.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source.
COPY backend/ ./backend/

# Copy the ephemeris file used by skyfield/planetary_positions.
COPY de421.bsp ./de421.bsp
RUN chown -R app:app /app

WORKDIR /app/backend
USER app

EXPOSE 8000

# Run Alembic migrations on startup, then launch uvicorn.
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
