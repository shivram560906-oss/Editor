# -*- coding: utf-8 -*-
"""
gui/widgets/chart_comparison.py

Chart Comparison (Synastry) Widget.
Allows comparing two saved kundali charts side by side:
  - House positions compared
  - Common yoga combinations
  - Key differences highlighted
  - Compatibility summary
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QSplitter, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_GOLD, COLOR_ACCENT, COLOR_ERROR, COLOR_SUCCESS
)

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल",
    "Mercury": "बुध", "Jupiter": "बृहस्पति", "Venus": "शुक्र",
    "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
}
SIGN_NAMES_NE = [
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
]
SIGN_NAMES_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


def _sign_from_lon(lon: float) -> int:
    """Return 1-based sign number from longitude."""
    return int(lon / 30.0) % 12 + 1


def _get_planet_map(chart_data: dict) -> dict[str, dict]:
    """Extract planet name → {house, sign, lon} from chart payload."""
    planets = {}
    for p in (chart_data.get("planets") or []):
        if not isinstance(p, dict):
            continue
        name = p.get("name", "")
        lon = float(p.get("sidereal_longitude", p.get("longitude", 0)) or 0)
        house = int(p.get("house", 0) or 0)
        sign = _sign_from_lon(lon)
        planets[name] = {"house": house, "sign": sign, "lon": lon}
    return planets


class ChartComparisonWidget(QWidget):
    """Side-by-side comparison of two kundali charts."""

    def __init__(self, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._chart_a: Optional[dict] = None
        self._chart_b: Optional[dict] = None
        self._saved_records: list[dict] = []
        self._build_ui()
        self._load_saved_charts()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ── Header ──
        header = QLabel(
            "⚖️ कुण्डली तुलना (Chart Comparison)" if self._is_ne else "⚖️ Chart Comparison"
        )
        header.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {COLOR_GOLD}; "
            f"border-bottom: 2px solid {BORDER_COLOR}; padding-bottom: 8px;"
        )
        layout.addWidget(header)

        desc = QLabel(
            "दुई व्यक्तिको कुण्डली ग्रह स्थिति तुलना गर्नुहोस्।" if self._is_ne
            else "Compare planetary positions of two kundali charts side by side."
        )
        desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        # ── Chart selectors ──
        sel_frame = QFrame()
        sel_frame.setStyleSheet(
            f"QFrame {{ background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; "
            f"border-radius: 8px; padding: 4px; }}"
        )
        sel_layout = QGridLayout(sel_frame)
        sel_layout.setContentsMargins(14, 12, 14, 12)
        sel_layout.setSpacing(10)

        lbl_a = QLabel("📊 " + ("कुण्डली 'क'" if self._is_ne else "Chart A"))
        lbl_a.setStyleSheet(f"font-weight: 700; color: {COLOR_ACCENT};")
        sel_layout.addWidget(lbl_a, 0, 0)

        self._combo_a = QComboBox()
        self._combo_a.setMinimumWidth(220)
        sel_layout.addWidget(self._combo_a, 1, 0)

        lbl_b = QLabel("📊 " + ("कुण्डली 'ख'" if self._is_ne else "Chart B"))
        lbl_b.setStyleSheet(f"font-weight: 700; color: {COLOR_ERROR};")
        sel_layout.addWidget(lbl_b, 0, 1)

        self._combo_b = QComboBox()
        self._combo_b.setMinimumWidth(220)
        sel_layout.addWidget(self._combo_b, 1, 1)

        compare_btn = QPushButton(
            "🔍 तुलना गर्नुहोस् (Compare)" if self._is_ne else "🔍 Compare"
        )
        compare_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: #fff;
                border: none; border-radius: 6px;
                padding: 8px 20px; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
        """)
        compare_btn.clicked.connect(self._do_compare)
        sel_layout.addWidget(compare_btn, 1, 2)
        layout.addWidget(sel_frame)

        # ── Results area ──
        self._results_scroll = QScrollArea()
        self._results_scroll.setWidgetResizable(True)
        self._results_scroll.setStyleSheet("QScrollArea { border: none; }")
        self._results_widget = QWidget()
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(12)
        self._results_scroll.setWidget(self._results_widget)
        layout.addWidget(self._results_scroll, 1)

        # Initial placeholder
        placeholder = QLabel(
            "⬆️ माथिबाट दुई कुण्डली छनोट गरेर 'तुलना गर्नुहोस्' थिच्नुहोस्।" if self._is_ne
            else "⬆️ Select two charts above and click 'Compare'."
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 40px;")
        self._results_layout.addWidget(placeholder)
        self._results_layout.addStretch()

    def _load_saved_charts(self):
        """Load saved charts from database."""
        try:
            from gui.utils.chart_storage import list_charts
            self._saved_records = list_charts() or []
        except Exception:
            self._saved_records = []

        self._combo_a.clear()
        self._combo_b.clear()

        if not self._saved_records:
            placeholder = "— कुनै कुण्डली सेभ छैन —"
            self._combo_a.addItem(placeholder)
            self._combo_b.addItem(placeholder)
            return

        for rec in self._saved_records:
            label = f"{rec.get('name', '?')} — {rec.get('birth_date', '')[:10]}"
            self._combo_a.addItem(label, rec)
            self._combo_b.addItem(label, rec)

        # Default: select different charts if possible
        if self._combo_b.count() > 1:
            self._combo_b.setCurrentIndex(1)

    def _do_compare(self):
        """Fetch both charts, calculate, and show comparison."""
        rec_a = self._combo_a.currentData()
        rec_b = self._combo_b.currentData()

        if not isinstance(rec_a, dict) or not isinstance(rec_b, dict):
            QMessageBox.warning(
                self, "चेतावनी",
                "कुनै पनि कुण्डली चयन गर्नुहोस्।" if self._is_ne else "Please select charts first."
            )
            return

        if rec_a.get("id") == rec_b.get("id"):
            QMessageBox.information(
                self, "जानकारी",
                "एउटै कुण्डली दुवैतिर छनोट गरिएको छ। फरक कुण्डलीहरू छनोट गर्नुहोस्।"
                if self._is_ne else "Same chart selected for both. Please choose different charts."
            )
            return

        try:
            from gui.backend_bridge import calculate_chart
            self._chart_a = calculate_chart(dict(rec_a))
            self._chart_b = calculate_chart(dict(rec_b))
            name_a = rec_a.get("name", "क")
            name_b = rec_b.get("name", "ख")
            self._show_comparison(name_a, name_b)
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def _show_comparison(self, name_a: str, name_b: str):
        """Render comparison results."""
        # Clear previous results
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        planets_a = _get_planet_map(self._chart_a)
        planets_b = _get_planet_map(self._chart_b)

        sign_names = SIGN_NAMES_NE if self._is_ne else SIGN_NAMES_EN
        planet_labels = PLANET_NAMES_NE if self._is_ne else {}

        # ── Planetary Position Comparison Table ──
        section_lbl = QLabel(
            "🪐 ग्रह स्थिति तुलना (Planetary Positions)" if self._is_ne
            else "🪐 Planetary Position Comparison"
        )
        section_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; "
            f"border-bottom: 1px solid {BORDER_COLOR}; padding-bottom: 4px;"
        )
        self._results_layout.addWidget(section_lbl)

        table = QTableWidget()
        table.setColumnCount(5)
        headers = (
            ["ग्रह", f"{name_a} भाव", f"{name_a} राशि", f"{name_b} भाव", f"{name_b} राशि"]
            if self._is_ne else
            ["Planet", f"{name_a} House", f"{name_a} Sign", f"{name_b} House", f"{name_b} Sign"]
        )
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().setVisible(False)

        planet_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        table.setRowCount(len(planet_order))

        for row, planet in enumerate(planet_order):
            pa = planets_a.get(planet, {})
            pb = planets_b.get(planet, {})

            p_name = PLANET_NAMES_NE.get(planet, planet) if self._is_ne else planet
            same_house = pa.get("house") == pb.get("house")
            same_sign = pa.get("sign") == pb.get("sign")

            def _cell(text: str, highlight: bool = False) -> QTableWidgetItem:
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                if highlight:
                    item.setForeground(QColor("#16a34a"))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                return item

            sign_a = sign_names[pa["sign"] - 1] if pa.get("sign") else "—"
            sign_b = sign_names[pb["sign"] - 1] if pb.get("sign") else "—"

            table.setItem(row, 0, _cell(p_name))
            table.setItem(row, 1, _cell(str(pa.get("house") or "—"), same_house))
            table.setItem(row, 2, _cell(sign_a, same_sign))
            table.setItem(row, 3, _cell(str(pb.get("house") or "—"), same_house))
            table.setItem(row, 4, _cell(sign_b, same_sign))

        table.setFixedHeight(min(400, len(planet_order) * 32 + 40))
        self._results_layout.addWidget(table)

        # ── Compatibility Summary ──
        common_houses = sum(
            1 for p in planet_order
            if planets_a.get(p, {}).get("house") == planets_b.get(p, {}).get("house")
            and planets_a.get(p, {}).get("house")
        )
        common_signs = sum(
            1 for p in planet_order
            if planets_a.get(p, {}).get("sign") == planets_b.get(p, {}).get("sign")
            and planets_a.get(p, {}).get("sign")
        )
        score_pct = int((common_houses + common_signs) / (len(planet_order) * 2) * 100)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(
            f"QFrame {{ background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; "
            f"border-radius: 8px; padding: 4px; }}"
        )
        sl = QVBoxLayout(summary_frame)
        sl.setContentsMargins(16, 12, 16, 12)
        sl.setSpacing(6)

        sum_title = QLabel(
            "📊 तुलना सारांश" if self._is_ne else "📊 Comparison Summary"
        )
        sum_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};")
        sl.addWidget(sum_title)

        color = "#16a34a" if score_pct >= 60 else ("#ea580c" if score_pct >= 40 else "#dc2626")
        score_lbl = QLabel(f"मिलान स्कोर: {score_pct}%" if self._is_ne else f"Match Score: {score_pct}%")
        score_lbl.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {color};")
        sl.addWidget(score_lbl)

        details_lbl = QLabel(
            f"समान भाव: {common_houses}/9  |  समान राशि: {common_signs}/9"
            if self._is_ne else
            f"Common Houses: {common_houses}/9  |  Common Signs: {common_signs}/9"
        )
        details_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        sl.addWidget(details_lbl)

        note = QLabel(
            "नोट: यो स्कोर ग्रह भाव/राशि मिलानमा आधारित सामान्य सूचक हो।"
            if self._is_ne else
            "Note: Score is a general indicator based on house/sign alignment."
        )
        note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        note.setWordWrap(True)
        sl.addWidget(note)
        self._results_layout.addWidget(summary_frame)
        self._results_layout.addStretch()

    def refresh_charts(self):
        """Reload saved charts list."""
        self._load_saved_charts()
