# -*- coding: utf-8 -*-
"""Render the real desktop Janmapatrika page to a PNG.

The editor must show the same page the PySide6 desktop app shows.  That page
is built from QWidgets, QTextDocument tables and QPainter charts, so the only
faithful renderer is the desktop page itself.  This worker is started as a
separate process by the API; it imports the GUI module, renders the page with
an offscreen Qt platform and writes a PNG.

Input (stdin):  {"data": <chart payload>, "scale": 2.0}
Argv:           <output.png>
Stdout:         one JSON line with the rendered pixel/logical size.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import traceback

_IS_LINUX = sys.platform.startswith("linux")

# The API image is headless.  Set the platform before importing PySide6.
if _IS_LINUX and not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
if _IS_LINUX and not os.environ.get("XDG_RUNTIME_DIR"):
    try:
        _runtime = tempfile.mkdtemp(prefix="janmapatrika-qt-")
        os.chmod(_runtime, 0o700)
        os.environ["XDG_RUNTIME_DIR"] = _runtime
    except OSError:
        pass
os.environ.setdefault("QT_LOGGING_RULES", "qt.text.font.db=false")

# Make the repository's gui package importable when this file is launched
# from Kundali-Desktop/backend (the Docker WORKDIR).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _settle(app, page, seconds: float = 2.0) -> None:
    """Let the page finish its first layout and chart animations."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)

    # Activate every layout that owns the document paper, then wait until the
    # natural document height is stable.  The widget starts at a short height
    # and grows once the prose and dasha tables have been measured; rendering
    # too early cuts the page in half.
    page._paper.ensurePolished()
    page._paper_layout.activate()
    page._paper_grid.activate()
    app.processEvents()

    last = -1
    stable = 0
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        app.processEvents()
        height = page._doc_wrapper.height()
        if height == last and height >= 1200:
            stable += 1
        else:
            stable = 0
        last = height
        if stable >= 6:
            break
        time.sleep(0.05)

    page._paper.ensurePolished()
    page._paper_layout.activate()
    page._paper_grid.activate()
    app.processEvents()


def render(data: dict, output_path: str, scale: float = 2.0) -> dict:
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtWidgets import QApplication

    from gui.widgets.janmapatrika_widget import JanmapatrikaPage

    app = QApplication.instance() or QApplication([])
    page = JanmapatrikaPage(data)
    page.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    page.resize(720, 1600)
    page.show()
    _settle(app, page)

    logical_w = max(1, int(page._doc_wrapper.width()))
    logical_h = max(1, int(page._doc_wrapper.height()))

    # A very long dasha table should still produce a usable bitmap rather than
    # exhausting memory on the free API instance.
    pixel_scale = max(1.0, min(2.0, float(scale)))
    if logical_h * pixel_scale > 20000:
        pixel_scale = max(1.0, 20000.0 / logical_h)

    image = QImage(
        max(1, int(round(logical_w * pixel_scale))),
        max(1, int(round(logical_h * pixel_scale))),
        QImage.Format.Format_ARGB32,
    )
    image.fill(0xFFFFFFFF)

    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        page._scene.render(
            painter,
            QRectF(0, 0, image.width(), image.height()),
            QRectF(0, 0, logical_w, logical_h),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
    finally:
        painter.end()

    if not image.save(output_path, "PNG"):
        raise RuntimeError("Qt could not write the Janmapatrika PNG")

    result = {
        "width": image.width(),
        "height": image.height(),
        "logical_width": logical_w,
        "logical_height": logical_h,
        "scale": pixel_scale,
    }

    try:
        page.hide()
        page.deleteLater()
        app.processEvents()
    except Exception:
        pass
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: janmapatrika_render.py <output.png>", file=sys.stderr)
        return 2

    output_path = sys.argv[1]
    try:
        raw = sys.stdin.buffer.read()
        payload = json.loads(raw.decode("utf-8"))
        data = payload.get("data") if isinstance(payload, dict) and "data" in payload else payload
        if not isinstance(data, dict):
            raise ValueError("chart payload must be a JSON object")
        scale = float(payload.get("scale", 2.0)) if isinstance(payload, dict) else 2.0
        result = render(data, output_path, scale=scale)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        traceback.print_exc()
        print(f"janmapatrika render failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
