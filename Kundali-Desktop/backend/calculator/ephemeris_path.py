"""
backend/calculator/ephemeris_path.py

Central Swiss Ephemeris data-path configuration.

pyswisseph honours the SE_EPHE_PATH environment variable automatically when it
is imported, but the packaged desktop application ships its ephemeris data
beside the executable, so the path is never guaranteed to be present in the
environment at import time. Calling ``swe.set_ephe_path`` explicitly makes the
resolution deterministic and auditable.

The helper is intentionally defensive: when Swiss Ephemeris is unavailable, or
the directory does not exist, it is a no-op so the analytical fallback keeps
working exactly as before.
"""
from __future__ import annotations

import importlib
import os
from typing import Optional

try:  # Keep the analytical fallback usable before dependencies install.
    swe = importlib.import_module("swisseph")
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    swe = None


def resolve_ephemeris_path(explicit: Optional[str] = None) -> Optional[str]:
    """Return the first existing ephemeris directory, or ``None``.

    Resolution order mirrors desktop_main.py: an explicit argument wins, then
    ``SE_EPHE_PATH``. The repository root (where ``de421.bsp`` lives) is used as
    a final fallback so a source checkout still resolves deterministically.
    """
    candidates = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("SE_EPHE_PATH")
    if env:
        candidates.append(env)
    # Repository root: backend/calculator/ -> backend/ -> repo root
    candidates.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    for candidate in candidates:
        if candidate and os.path.isdir(candidate):
            return candidate
    return None


def configure_ephemeris_path(explicit: Optional[str] = None) -> Optional[str]:
    """Point Swiss Ephemeris at the resolved data directory.

    Returns the directory that was applied, or ``None`` when nothing changed.
    """
    directory = resolve_ephemeris_path(explicit)
    if swe is None or directory is None:
        return None
    try:
        swe.set_ephe_path(directory)
    except Exception:  # pragma: no cover - never let path setup break calculation
        return None
    return directory
