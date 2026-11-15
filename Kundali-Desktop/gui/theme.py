"""
gui/theme.py

Qt StyleSheet theme — matching Classic Desktop Astrology Software (default)
and optional Cosmic Dark theme.

Classic Desktop Light Theme colors (matching user screenshot):
- Primary Background: #dce6f5 (Soft periwinkle/blue)
- Secondary Background: #ffffff (Pure white)
- Header Bar Background: #1d4ed8 (Classic Cobalt Blue)
- Container Borders: #2563eb (Royal Blue)
- Text Color: #0f172a (Dark navy/black)
"""
from __future__ import annotations

# ── Classic Light Theme tokens (Default - matching user screenshot) ────────
BG_PRIMARY       = "#dbe5f6"
BG_SECONDARY     = "#f0f5fc"
BG_TERTIARY      = "#ffffff"

COLOR_TEXT_PRIMARY   = "#0f172a"
COLOR_TEXT_SECONDARY = "#334155"
COLOR_TEXT_MUTED     = "#64748b"

COLOR_GOLD       = "#1d4ed8"   # Royal Blue header accent
COLOR_ACCENT     = "#2563eb"
COLOR_SUCCESS    = "#16a34a"
COLOR_ERROR      = "#dc2626"
COLOR_WARNING    = "#ea580c"

BORDER_COLOR     = "#3b82f6"
CARD_BG          = "#ffffff"
CARD_BG_HOVER    = "#eff6ff"
INPUT_BG         = "#ffffff"
INPUT_BORDER     = "#93c5fd"
INPUT_FOCUS      = "#2563eb"

SIDEBAR_BG       = "#e2e8f0"
SIDEBAR_BORDER   = "#cbd5e1"
SIDEBAR_ITEM_HOVER = "#cbd5e1"
SIDEBAR_ITEM_ACTIVE = "#93c5fd"

# ── Planet colors (Standard Classic palette) ──────────────────────────────
PLANET_COLORS = {
    "Sun":     "#dc2626",   # Red
    "Moon":    "#2563eb",   # Blue
    "Mars":    "#b91c1c",   # Dark Red
    "Mercury": "#16a34a",   # Green
    "Jupiter": "#d97706",   # Yellow/Gold
    "Venus":   "#c026d3",   # Pink/Magenta
    "Saturn":  "#475569",   # Dark Grey/Black
    "Rahu":    "#4f46e5",   # Indigo
    "Ketu":    "#7c3aed",   # Purple
}


def build_stylesheet(theme_mode: str = "classic") -> str:
    """Return the complete Qt StyleSheet string for the application."""
    if theme_mode == "dark":
        return _build_dark_stylesheet()
    return _build_classic_stylesheet()


def _build_classic_stylesheet() -> str:
    """Classic Desktop Astrology Software Theme (matching screenshot)."""
    return f"""
/* ═══════════════════════════════════════════════════════
   SHIVRAM JYOTISH — CLASSIC DESKTOP THEME (Light Blue)
   ═══════════════════════════════════════════════════════ */

QMainWindow, QDialog, QWidget {{
    background-color: #dbe5f6;
    color: #0f172a;
    font-family: "Segoe UI", "Noto Sans Devanagari", "Arial", sans-serif;
    font-size: 12px;
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: #e2e8f0;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: #93c5fd;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #2563eb;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: #e2e8f0;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: #93c5fd;
    border-radius: 5px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #2563eb;
}}

/* ── Cards / Container Frames (Matching Screenshot Box Style) ── */
QFrame#Card, QFrame#ContainerBox {{
    background-color: #ffffff;
    border: 2px solid #2563eb;
    border-radius: 6px;
}}
QFrame#CardHeader {{
    background-color: #1d4ed8;
    color: #ffffff;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 4px 10px;
}}
QLabel#CardTitle {{
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
}}

/* ── Top Ribbon ── */
#BirthRibbon {{
    background-color: #f8fafc;
    border-bottom: 2px solid #2563eb;
    min-height: 44px;
    padding: 2px 14px;
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: #ffffff;
    border: 1px solid #93c5fd;
    border-radius: 4px;
    color: #0f172a;
    padding: 6px 10px;
    font-size: 12px;
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 2px solid #1d4ed8;
}}

/* ── Combobox ── */
QComboBox {{
    background-color: #ffffff;
    border: 1px solid #93c5fd;
    border-radius: 4px;
    color: #0f172a;
    padding: 4px 10px;
    min-height: 28px;
}}
QComboBox:focus {{
    border: 2px solid #1d4ed8;
}}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #2563eb;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}}

/* ── Buttons ── */
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ffffff, stop:1 #e2e8f0);
    border: 1px solid #93c5fd;
    border-radius: 4px;
    color: #0f172a;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 14px;
    min-height: 26px;
}}
QPushButton:hover {{
    background: #dbeafe;
    border-color: #1d4ed8;
    color: #1d4ed8;
}}
QPushButton:pressed {{
    background: #bfdbfe;
}}
QPushButton#PrimaryBtn {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
    border: 1px solid #1e40af;
    color: #ffffff;
    font-weight: 700;
}}
QPushButton#PrimaryBtn:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3b82f6, stop:1 #2563eb);
}}
QPushButton#SidebarItem {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 4px;
    color: #334155;
    text-align: left;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#SidebarItem:hover {{
    background: #cbd5e1;
    color: #0f172a;
    border-left: 3px solid #2563eb;
}}
QPushButton#SidebarItem[active="true"] {{
    background: #93c5fd;
    color: #1e3a8a;
    font-weight: 700;
    border-left: 3px solid #1d4ed8;
}}

/* ── Menu Bar ── */
QMenuBar {{
    background-color: #f1f5f9;
    color: #0f172a;
    border-bottom: 2px solid #2563eb;
    font-size: 12px;
    font-weight: 600;
    padding: 2px;
}}
QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}
QMenu {{
    background-color: #ffffff;
    border: 1px solid #2563eb;
    color: #0f172a;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}
QMenu::separator {{
    background: #cbd5e1;
    height: 1px;
    margin: 4px 8px;
}}

/* ── Tables ── */
QTableWidget, QTableView {{
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    gridline-color: #cbd5e1;
    color: #0f172a;
    border: 1px solid #93c5fd;
    font-size: 12px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}}
QHeaderView::section {{
    background-color: #dbeafe;
    color: #1e40af;
    font-weight: 700;
    padding: 6px 8px;
    border: 1px solid #93c5fd;
}}

/* ── Status Bar ── */
QStatusBar {{
    background-color: #f1f5f9;
    color: #475569;
    border-top: 1px solid #cbd5e1;
    font-size: 11px;
}}
"""


def _build_dark_stylesheet() -> str:
    """Optional Cosmic Dark Theme."""
    return f"""
QMainWindow, QDialog, QWidget {{
    background-color: #080711;
    color: #f3f4f6;
    font-family: "Segoe UI", "Noto Sans Devanagari", sans-serif;
    font-size: 13px;
}}
QMenuBar {{ background-color: #121024; color: #f3f4f6; border-bottom: 1px solid #2d2b4e; }}
QMenuBar::item:selected {{ background-color: #261e4e; color: #d4af37; }}
QMenu {{ background-color: #121024; border: 1px solid #2d2b4e; color: #f3f4f6; }}
QMenu::item:selected {{ background-color: #261e4e; color: #d4af37; }}
"""


def apply_theme(app, mode: str = "classic") -> None:
    """Apply theme to QApplication."""
    app.setStyleSheet(build_stylesheet(mode))
