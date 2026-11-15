# -*- coding: utf-8 -*-
"""
gui/widgets/vimshopaka_bala_page.py

Shodashavarga Vimshopaka Bala — 16-Divisional Chart Strength
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vimshopaka Bala is the weighted strength of a planet based on its
placement in the 16 divisional charts (D1–D60).

Each varga has a fixed weight (out of 20 total).
A planet scores 1 point for each varga where it's in its own/exalted sign,
proportionally less for friend/neutral signs.

Displays:
  - Table: Planet × Varga with colour-coded scores
  - Bar chart: Total Vimshopaka per planet
  - Interpretation: Strong / Moderate / Weak
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont, QPainter, QPen

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_GOLD, COLOR_ACCENT, COLOR_SUCCESS, COLOR_ERROR
)

# ── Varga weights (Parashara — Shodashavargas) ───────────────────────────────
VARGAS = [
    ("D1",  "राशि",       3.5),
    ("D2",  "होरा",       1.0),
    ("D3",  "द्रेष्काण",  1.0),
    ("D4",  "चतुर्थांश",  0.5),
    ("D7",  "सप्तांश",    0.5),
    ("D9",  "नवांश",      3.0),
    ("D10", "दशांश",      0.5),
    ("D12", "द्वादशांश",  0.5),
    ("D16", "षोडशांश",   2.0),
    ("D20", "विंशांश",    0.5),
    ("D24", "चतुर्विंशांश",0.5),
    ("D27", "सप्तविंशांश", 0.5),
    ("D30", "त्रिंशांश",   1.0),
    ("D40", "खवेदांश",    0.5),
    ("D45", "अक्षवेदांश", 0.5),
    ("D60", "षष्टिांश",  4.0),
]

PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
PLANET_NE = {
    "Sun":"सूर्य","Moon":"चन्द्र","Mars":"मङ्गल","Mercury":"बुध",
    "Jupiter":"बृहस्पति","Venus":"शुक्र","Saturn":"शनि","Rahu":"राहु","Ketu":"केतु"
}

# Presentation only. The dignity->score mapping itself is an astrology rule and
# lives in backend/calculator/vimshopaka.py, never here (PROJECT_RULES.md 3.1).
def _rating_color(score: float) -> str:
    """Colour band for a Vimshopaka total out of 20."""
    if score >= 15:
        return COLOR_GOLD
    if score >= 10:
        return COLOR_SUCCESS
    if score >= 6:
        return "#f59e0b"
    if score >= 3:
        return "#f97316"
    return COLOR_ERROR


class VimshopakaBalaPage(QWidget):
    """Shodashavarga Vimshopaka Bala strength table."""

    def __init__(self, chart_data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data
        self._build_ui()
        if chart_data:
            self._load(chart_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        title = QLabel("⚖️ " + ("षोडशवर्ग विंशोपक बल" if self._is_ne else "Shodashavarga Vimshopaka Bala"))
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_GOLD};")
        layout.addWidget(title)

        desc = QLabel(
            "प्रत्येक ग्रहको षोडश वर्गहरूमा स्थितिको भारित बल (२० अंकमध्ये)।"
            if self._is_ne else
            "Weighted planetary strength across 16 divisional charts (out of 20)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        # Main table: planets as rows, vargas as columns + total
        headers = (["ग्रह"] if self._is_ne else ["Planet"]) + \
                  [v[0] for v in VARGAS] + \
                  (["कुल (२०)"] if self._is_ne else ["Total (/20)"]) + \
                  (["स्थिति"] if self._is_ne else ["Rating"])

        self._table = QTableWidget(len(PLANETS), len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 100)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR};
                border-radius: 8px; gridline-color: {BORDER_COLOR};
                color: {COLOR_TEXT_PRIMARY}; font-size: 11px;
            }}
            QHeaderView::section {{
                background: {BG_TERTIARY}; color: {COLOR_GOLD};
                font-weight: 700; padding: 5px; border: none;
                border-bottom: 1px solid {BORDER_COLOR};
            }}
            QTableWidget::item:selected {{ background: {COLOR_ACCENT}; color: #fff; }}
        """)

        # Populate planet names
        for row, planet in enumerate(PLANETS):
            name = PLANET_NE.get(planet, planet) if self._is_ne else planet
            item = QTableWidgetItem(name)
            item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            item.setForeground(QBrush(QColor(COLOR_GOLD)))
            self._table.setItem(row, 0, item)

        layout.addWidget(self._table, 1)

        # Placeholder message
        self._placeholder = QLabel(
            "⚠️ कुण्डली लोड गर्नुहोस् — तब Vimshopaka Bala देखिनेछ।"
            if self._is_ne else
            "⚠️ Load a chart — Vimshopaka Bala will appear here."
        )
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; padding: 20px;")
        layout.addWidget(self._placeholder)

    def refresh(self, chart_data: dict):
        self._chart_data = chart_data
        self._load(chart_data)

    def _load(self, chart_data: dict):
        """Render the engine's Vimshopaka payload. This page computes nothing.

        Every number displayed here comes from ``backend/calculator/vimshopaka.py``
        via the ``vimshopaka_bala`` key of the chart payload.  When the engine
        reports a cell as unavailable the page shows an em-dash; it never
        substitutes a score of its own.
        """
        self._placeholder.hide()
        payload = (chart_data or {}).get("vimshopaka_bala")
        if not isinstance(payload, dict):
            payload = {}

        grahas = payload.get("planets") if isinstance(payload.get("planets"), dict) else {}
        varga_ids = [v[0] for v in VARGAS]
        total_col = len(varga_ids) + 1
        placeholder = "—"

        for row, planet in enumerate(PLANETS):
            entry = grahas.get(planet) if isinstance(grahas.get(planet), dict) else None
            cells = entry.get("vargas") if entry and isinstance(entry.get("vargas"), dict) else {}

            for col_off, varga_id in enumerate(varga_ids):
                col = col_off + 1
                cell = cells.get(varga_id) if isinstance(cells.get(varga_id), dict) else None
                if not cell or not cell.get("available"):
                    item = QTableWidgetItem(placeholder)
                    item.setForeground(QBrush(QColor(COLOR_TEXT_MUTED)))
                    item.setToolTip("Vimshopaka Bala उपलब्ध छैन / unavailable")
                else:
                    weight = float(cell.get("weight", 0.0))
                    weighted = float(cell.get("weighted", 0.0))
                    item = QTableWidgetItem(f"{weighted:.1f}")
                    if weighted >= weight * 0.9:
                        item.setForeground(QBrush(QColor(COLOR_SUCCESS)))
                    elif weighted >= weight * 0.5:
                        item.setForeground(QBrush(QColor(COLOR_GOLD)))
                    else:
                        item.setForeground(QBrush(QColor(COLOR_ERROR)))
                    item.setToolTip(
                        f"{varga_id}: sign {cell.get('sign')} · {cell.get('relation')}"
                    )
                item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row, col, item)

            # Total column — only present when the engine resolved every varga.
            available = bool(entry and entry.get("available"))
            total = entry.get("total") if available else None
            rating = (entry.get("rating") or {}) if available else {}

            if total is None:
                t_item = QTableWidgetItem(placeholder)
                t_item.setForeground(QBrush(QColor(COLOR_TEXT_MUTED)))
                t_item.setToolTip("कुल बल उपलब्ध छैन / total unavailable")
                label = placeholder
            else:
                total = round(min(float(total), float(payload.get("max_total", 20.0))), 2)
                t_item = QTableWidgetItem(f"{total:.1f}")
                t_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                label = (rating.get("ne") if self._is_ne else rating.get("en")) or placeholder
                t_item.setForeground(QBrush(QColor(_rating_color(total))))
            t_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, total_col, t_item)

            r_item = QTableWidgetItem(label)
            r_item.setTextAlignment(Qt.AlignCenter)
            r_item.setForeground(QBrush(QColor(
                _rating_color(total) if total is not None else COLOR_TEXT_MUTED)))
            self._table.setItem(row, total_col + 1, r_item)
