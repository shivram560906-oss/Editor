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

# Qt runtime libraries and Devanagari fonts for the exact desktop
# Janmapatrika page renderer (QtWidgets + QTextDocument + QPainter).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libegl1 libxkbcommon0 libfontconfig1 libfreetype6 \
    libdbus-1-3 libglib2.0-0 \
    fonts-noto-core fonts-noto-extra fonts-deva \
    && rm -rf /var/lib/apt/lists/*

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
# Nepali dates and planet labels).
COPY Kundali-Desktop/gui/__init__.py ./gui/__init__.py
COPY Kundali-Desktop/gui/theme.py ./gui/theme.py
COPY Kundali-Desktop/gui/utils/__init__.py ./gui/utils/__init__.py
COPY Kundali-Desktop/gui/utils/location_data.py ./gui/utils/location_data.py
COPY Kundali-Desktop/gui/utils/bs_calendar.py ./gui/utils/bs_calendar.py
COPY Kundali-Desktop/gui/utils/planet_colors.py ./gui/utils/planet_colors.py

# The authoritative desktop Janmapatrika page. The render worker imports this
# widget exactly as the desktop app does; the editing pipeline stays SVG.
COPY Kundali-Desktop/gui/widgets/__init__.py ./gui/widgets/__init__.py
COPY Kundali-Desktop/gui/widgets/janmapatrika_widget.py ./gui/widgets/janmapatrika_widget.py
COPY Kundali-Desktop/gui/widgets/north_indian_chart.py ./gui/widgets/north_indian_chart.py
COPY Kundali-Desktop/gui/widgets/shadbala_bar_widget.py ./gui/widgets/shadbala_bar_widget.py

RUN chown -R app:app /app

WORKDIR /app/backend
USER app

EXPOSE 8000

# Render supplies PORT. main.py creates the SQLite tables on import, so a
# fresh container needs no migration step.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
