# -*- coding: utf-8 -*-
"""
gui/widgets/planetary_ingress_page.py

Planetary Ingress (गोचर राशि परिवर्तन क्यालेन्डर) Widget:
- Sidereal sign transition schedule for Sun, Mars, Jupiter, Saturn, Rahu, Ketu, Mercury, Venus
- Filter by planet or year
- Displays exact transit entry date & time (Nepal Time), direction (Direct/Retrograde), from sign -> to sign
"""
from __future__ import annotations
import sys, os
import datetime as dt
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QPushButton, QSpinBox
)
from PySide6.QtCore import Qt

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY)
from gui.utils.planet_colors import planet_color


class PlanetaryIngressPage(QWidget):
    """Interactive transit / ingress calendar widget."""

    def __init__(self, data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._all_events = []
        self._build_ui()
        self.load_year(dt.date.today().year)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        # Header Bar with Year & Planet Selector
        hdr = QHBoxLayout()
        title = QLabel("🪐 " + ("ग्रह गोचर राशि परिवर्तन क्यालेन्डर (Transit Ingress)" if self._is_ne else "Planetary Transit & Ingress Calendar"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 800;")
        hdr.addWidget(title)
        hdr.addStretch()

        # Year selector
        hdr.addWidget(QLabel("वर्ष (Year):" if self._is_ne else "Year:"))
        self._year_spin = QSpinBox()
        self._year_spin.setRange(1900, 2100)
        self._year_spin.setValue(dt.date.today().year)
        self._year_spin.setStyleSheet(f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; padding: 4px 8px; border: 1px solid {BORDER_COLOR}; border-radius: 4px;")
        hdr.addWidget(self._year_spin)

        # Planet filter
        hdr.addWidget(QLabel("ग्रह (Planet):" if self._is_ne else "Planet:"))
        self._planet_combo = QComboBox()
        self._planet_combo.addItem("सबै ग्रहहरू (All Planets)" if self._is_ne else "All Planets", "ALL")
        planets_list = [
            ("बृहस्पति / गुरु (Jupiter)", "Jupiter"),
            ("शनि (Saturn)", "Saturn"),
            ("राहु (Rahu)", "Rahu"),
            ("केतु (Ketu)", "Ketu"),
            ("सूर्य (Sun)", "Sun"),
            ("मङ्गल (Mars)", "Mars"),
            ("शुक्र (Venus)", "Venus"),
            ("बुध (Mercury)", "Mercury"),
        ]
        for l, v in planets_list:
            self._planet_combo.addItem(l, v)
        self._planet_combo.currentIndexChanged.connect(self._apply_filter)
        hdr.addWidget(self._planet_combo)

        # Refresh / calculate button
        btn_calc = QPushButton("🔄 " + ("गणना गर्नुहोस्" if self._is_ne else "Refresh"))
        btn_calc.setCursor(Qt.PointingHandCursor)
        btn_calc.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_GOLD}; color: #000; font-weight: 700;
                padding: 6px 14px; border-radius: 6px;
            }}
            QPushButton:hover {{ background: #f59e0b; }}
        """)
        btn_calc.clicked.connect(lambda: self.load_year(self._year_spin.value()))
        hdr.addWidget(btn_calc)

        layout.addLayout(hdr)

        # Info Box
        info = QLabel(
            "स्वीस इफेमेरिस (Swiss Ephemeris Drik Ganita) द्वारा गणना गरिएको चित्रपक्षीय लाहिरी अयनांश अनुसार "
            "ग्रहहरू कुन मिति र समयमा कुन राशिबाट कुन राशिमा प्रवेश गर्छन् र मार्गी वा वक्री अवस्था के रहन्छ भन्ने विवरण।"
            if self._is_ne else
            "Calculated with high precision Swiss Ephemeris (Chitrapaksha Lahiri Ayanamsha) showing exact transit dates, times, and direct/retrograde motions."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; padding: 4px 0;")
        layout.addWidget(info)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ग्रह (Planet)",
            "प्रवेश मिति तथा समय (Date & Time)",
            "पूर्व राशि (From Sign)",
            "प्रवेश राशि (To Sign)",
            "गति (Motion)",
            "ज्योतिषीय प्रभाव (Astrological Note)"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background: {BG_SECONDARY};
                color: {COLOR_TEXT_PRIMARY};
                gridline-color: {BORDER_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background: {BG_TERTIARY};
                color: {COLOR_GOLD};
                font-weight: 700;
                padding: 6px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        layout.addWidget(self._table, 1)

    def refresh(self, data: dict):
        self._data = data

    def load_year(self, year: int):
        try:
            from calculator.planetary_ingress import calculate_planetary_ingresses
            start_date = dt.date(year, 1, 1)
            end_date = dt.date(year, 12, 31)
            res = calculate_planetary_ingresses(start_date, end_date, ayanamsha_type="LAHIRI")
            self._all_events = res.get("events", [])
            self._apply_filter()
        except Exception as e:
            self._table.setRowCount(1)
            self._table.setItem(0, 0, QTableWidgetItem(f"गणना त्रुटि: {e}"))

    def _apply_filter(self):
        selected_planet = self._planet_combo.currentData()
        filtered = [e for e in self._all_events if selected_planet == "ALL" or e.get("planet") == selected_planet]

        self._table.setRowCount(len(filtered))
        for r_idx, ev in enumerate(filtered):
            pname = ev.get("planet_ne" if self._is_ne else "planet", ev.get("planet", ""))
            raw_time = ev.get("at", "")
            # Format time
            time_str = raw_time.replace("T", " ")[:19]
            from_s = ev.get("from_sign_ne" if self._is_ne else "from_sign_en", "")
            to_s = ev.get("to_sign_ne" if self._is_ne else "to_sign_en", "")
            direction = "मार्गी (Direct)" if ev.get("direction") == "direct" else "वक्री (Retrograde)"

            note = f"{pname} {to_s} राशिमा प्रवेश"
            if ev.get("direction") == "retrograde":
                note += " (वक्री अवस्थामा पुनः प्रवेश)"

            self._table.setItem(r_idx, 0, QTableWidgetItem(pname))
            self._table.setItem(r_idx, 1, QTableWidgetItem(time_str))
            self._table.setItem(r_idx, 2, QTableWidgetItem(from_s))
            self._table.setItem(r_idx, 3, QTableWidgetItem(to_s))
            self._table.setItem(r_idx, 4, QTableWidgetItem(direction))
            self._table.setItem(r_idx, 5, QTableWidgetItem(note))
