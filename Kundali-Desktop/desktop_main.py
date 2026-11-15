# -*- coding: utf-8 -*-
"""
desktop_main.py

Native PySide6 entry point for Shivram Jyotish Desktop Application.

Startup sequence:
  1. High-DPI / platform attributes (must be set before QApplication)
  2. QApplication creation
  3. Splash screen
  4. Font loading (Noto Serif Devanagari / Inter)
  5. Ephemeris pre-warm (de421.bsp) in background thread
  6. Main window creation (JyotishMainWindow)
  7. ReminderService attachment
  8. Event loop
"""

from __future__ import annotations

import os
import sys
import threading
import traceback

# ── 0. Ensure repo root is on sys.path so all imports resolve ──────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── 1. Qt high-DPI attributes — MUST happen before QApplication ───────────
import logging
import os

os.environ.setdefault("QT_LOGGING_RULES", "qt.text.font.db=false")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap, QFont, QFontDatabase, QIcon

# High-DPI scaling is on by default in PySide6 >= 6.4; no setAttribute needed.

logging.getLogger("PySide6").setLevel(logging.WARNING)


# ── helpers ────────────────────────────────────────────────────────────────

def _load_fonts() -> None:
    """Register bundled or system Devanagari / Latin fonts."""
    font_dirs = [
        os.path.join(_ROOT, "public", "fonts"),
        os.path.join(_ROOT, "frontend", "public", "fonts"),
        os.path.join(_ROOT, "gui", "resources", "fonts"),
    ]
    extensions = (".ttf", ".otf")
    loaded = 0
    for d in font_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if fname.lower().endswith(extensions):
                fid = QFontDatabase.addApplicationFont(os.path.join(d, fname))
                if fid >= 0:
                    loaded += 1
    # Fallback: nothing to do — Qt will use system fonts


def _prewarm_ephemeris() -> None:
    """Warm the Swiss Ephemeris data path so the first chart is faster.

    The sunrise/sunset calculations in ``panchang.py`` use the bundled
    ``de421.bsp`` through pyswisseph, not astropy.  The previous version of
    this function imported astropy, which is not a declared dependency, so the
    import always failed and the prewarm silently did nothing.
    """
    try:
        from backend.calculator.ephemeris_path import configure_ephemeris_path
    except Exception:
        return
    try:
        import swisseph as swe
    except Exception:
        return                                   # analytical engine: nothing to warm
    try:
        # Point pyswisseph at the bundled de421.bsp, then touch one body so the
        # ephemeris files are parsed before the first chart is requested.
        from backend.calculator.ephemeris_path import configure_ephemeris_path
        configure_ephemeris_path()
        swe.calc_ut(2451545.0, swe.SUN, swe.FLG_SWIEPH)
    except Exception:
        return                                   # non-critical: loads lazily on demand


def _make_splash(app: QApplication) -> QSplashScreen | None:
    """Create and show a splash screen if an image is available."""
    candidates = [
        os.path.join(_ROOT, "public", "splash.png"),
        os.path.join(_ROOT, "public", "splash.jpg"),
        os.path.join(_ROOT, "frontend", "public", "splash.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
                splash.show()
                app.processEvents()
                return splash
    return None


def main() -> int:
    """Application entry point — returns exit code."""

    app = QApplication(sys.argv)
    app.setApplicationName("ShivramJyotish")
    app.setOrganizationName("ShivramJyotish")
    app.setOrganizationDomain("shivramjyotish.local")

    # ── Load settings and apply theme BEFORE creating window ───────────────
    from PySide6.QtCore import QSettings
    settings = QSettings("ShivramJyotish", "Desktop")
    language = settings.value("language", "ne")
    ayanamsha = settings.value("ayanamsha", "LAHIRI")
    theme_mode = settings.value("theme_mode", "classic")

    # ── Apply theme early so splash and window use correct theme ───────────
    try:
        from gui.theme import apply_theme
        apply_theme(app, theme_mode)
    except Exception:
        pass

    # ── Splash ────────────────────────────────────────────────────────────
    splash = _make_splash(app)

    # ── Fonts ─────────────────────────────────────────────────────────────
    _load_fonts()

    # Set a sensible default application font - use system fonts that work well on Windows
    default_font = QFont("Segoe UI", 11)
    default_font.setStyleHint(QFont.SansSerif)
    app.setFont(default_font)

    # ── Ephemeris pre-warm (background) ───────────────────────────────────
    t = threading.Thread(target=_prewarm_ephemeris, daemon=True)
    t.start()

    # ── Database schema ─────────────────────────────────────────────────────
    # Run Alembic before the main window is built.  The desktop app used to
    # rely on Base.metadata.create_all(), which cannot add a column to an
    # existing table, so a model change left older installations with a stale
    # schema and "no such column" errors at runtime.  A failure is reported but
    # never blocks startup.
    try:
        from gui.paths import configure as _configure_desktop_environment
        _configure_desktop_environment()
        from gui.paths import run_migrations
        _migration_error = run_migrations()
        if _migration_error:
            print(f"[schema] migration warning: {_migration_error}")
        else:
            print("[schema] database is up to date")
    except Exception as exc:
        print(f"[schema] migration skipped: {exc}")

    # ── Main window ───────────────────────────────────────────────────────
    try:
        from gui.app import JyotishMainWindow
    except ImportError as exc:
        if splash:
            splash.close()
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Could not load main application module:\n\n{exc}\n\n"
            "Please ensure all dependencies are installed:\n"
            "  pip install -r requirements-native.txt",
        )
        return 1

    window = JyotishMainWindow(language=language, ayanamsha=ayanamsha)

    # ── Window icon ───────────────────────────────────────────────────────
    icon_dirs = [
        os.path.join(_ROOT, "public"),
        os.path.join(_ROOT, "frontend", "public"),
    ]
    for d in icon_dirs:
        for name in ("favicon.ico", "favicon.svg", "favicon.png"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                window.setWindowIcon(QIcon(p))
                break

    # ── ReminderService ───────────────────────────────────────────────────
    try:
        from gui.reminder_service import ReminderService
        reminder_service = ReminderService(parent=window)
        reminder_service.start()
        window._reminder_service = reminder_service  # type: ignore[attr-defined]
    except Exception:
        pass  # reminder is optional — don't crash if it fails

    window.show()

    if splash:
        splash.finish(window)

    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
