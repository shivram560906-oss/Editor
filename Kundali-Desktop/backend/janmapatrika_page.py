# -*- coding: utf-8 -*-
"""Exact desktop Janmapatrika page renderer used by the web editor.

The page is produced by the PySide6 ``JanmapatrikaPage`` inside a short-lived
worker process.  The worker approach keeps Qt out of the FastAPI process: Qt
must own its GUI thread, and a crash in a widget or font backend can never
take the calculation API down with it.

Rendered pages are cached by a hash of the complete chart payload plus a
renderer version.  The same file can therefore be served to the builder and
the Timeline without re-running Qt.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Dict, Tuple

JP_RENDER_VERSION = "2026-11-16.1"
_MAX_CACHE_FILES = 32
_RENDER_TIMEOUT_SECONDS = 240
_CACHE_LOCK = threading.Lock()

_BACKEND_DIR = Path(__file__).resolve().parent
_RENDERER = _BACKEND_DIR / "janmapatrika_render.py"


def _cache_dir() -> Path:
    override = (os.environ.get("JANMAPATRIKA_CACHE_DIR") or "").strip()
    base = Path(override) if override else Path(tempfile.gettempdir()) / "shivram-janmapatrika-pages"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _png_size(png: bytes) -> Tuple[int, int]:
    if len(png) < 24 or png[:8] != b"\x89PNG\r\n\x1a\n" or png[12:16] != b"IHDR":
        raise RuntimeError("renderer returned an invalid PNG")
    width, height = struct.unpack(">II", png[16:24])
    if not width or not height:
        raise RuntimeError("renderer returned an empty PNG")
    return int(width), int(height)


def _prune_cache(directory: Path, keep: int = _MAX_CACHE_FILES) -> None:
    try:
        files = sorted(
            (p for p in directory.glob("*.png") if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in files[keep:]:
            try:
                old.unlink()
            except OSError:
                pass
    except OSError:
        pass


def _run_renderer(data: dict, output_path: Path, scale: float) -> str:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    if sys.platform.startswith("linux"):
        env.setdefault("QT_QPA_PLATFORM", "offscreen")

    payload = json.dumps({"data": data, "scale": scale}, ensure_ascii=False).encode("utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, str(_RENDERER), str(output_path)],
            input=payload,
            cwd=str(_BACKEND_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_RENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Janmapatrika page render timed out after {_RENDER_TIMEOUT_SECONDS}s"
        ) from exc

    if proc.returncode != 0:
        detail = (proc.stderr or b"").decode("utf-8", "replace").strip()
        if not detail:
            detail = (proc.stdout or b"").decode("utf-8", "replace").strip()
        raise RuntimeError(detail[-1600:] or f"renderer exited with code {proc.returncode}")

    output = (proc.stdout or b"").decode("utf-8", "replace").strip()
    return output.splitlines()[-1] if output else ""


def render_janmapatrika_page(data: dict, scale: float = 2.0) -> Tuple[bytes, int, int]:
    """Return ``(png_bytes, pixel_width, pixel_height)`` for the desktop page."""
    try:
        fingerprint = json.dumps(
            {
                "renderer": JP_RENDER_VERSION,
                "scale": float(scale),
                "data": data,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"chart payload is not JSON serialisable: {exc}") from exc

    key = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    directory = _cache_dir()
    target = directory / f"{key}.png"

    with _CACHE_LOCK:
        if target.is_file():
            try:
                png = target.read_bytes()
                width, height = _png_size(png)
                return png, width, height
            except (OSError, RuntimeError):
                try:
                    target.unlink()
                except OSError:
                    pass

        tmp = directory / f".{key}.{os.getpid()}.tmp.png"
        try:
            _run_renderer(data, tmp, scale)
            if not tmp.is_file() or tmp.stat().st_size < 1024:
                raise RuntimeError("renderer did not produce a Janmapatrika PNG")
            os.replace(tmp, target)
            png = target.read_bytes()
            width, height = _png_size(png)
            _prune_cache(directory)
            return png, width, height
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass
