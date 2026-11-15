# Kundali-Desktop FastAPI engine (Render Docker service).
#
# Build context: repository root.
# Render settings:
#   Language:            Docker
#   Dockerfile Path:     Kundali-Desktop/backend/Dockerfile
#   Health Check Path:   /health/live
#
# The editor's server.js proxies /api/kundali/* here when
# KUNDALI_BACKEND_URL is set (for example https://shivram-kundali.onrender.com).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Run without root. /app stays writable for the SQLite database.
RUN groupadd --system app && useradd --system --gid app --home /app app \
    && mkdir -p /app/data \
    && chown -R app:app /app

# Install Python dependencies first for layer caching. Every pinned package
# ships a manylinux wheel, so no compiler is needed.
COPY Kundali-Desktop/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# API source and the JPL ephemeris used by skyfield.
COPY Kundali-Desktop/backend/ ./backend/
COPY Kundali-Desktop/de421.bsp ./de421.bsp

# Backend modules reuse these pure-Python GUI helpers (location cascade,
# Nepali dates and planet labels). They import no PySide6, so the API image
# stays small.
COPY Kundali-Desktop/gui/__init__.py ./gui/__init__.py
COPY Kundali-Desktop/gui/utils/__init__.py ./gui/utils/__init__.py
COPY Kundali-Desktop/gui/utils/location_data.py ./gui/utils/location_data.py
COPY Kundali-Desktop/gui/utils/bs_calendar.py ./gui/utils/bs_calendar.py
COPY Kundali-Desktop/gui/utils/planet_colors.py ./gui/utils/planet_colors.py

RUN chown -R app:app /app

WORKDIR /app/backend
USER app

EXPOSE 8000

# Render supplies PORT. main.py creates the SQLite tables on import, so a
# fresh container needs no migration step.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
