"""
gui/widgets/custom_dashboard.py

Customized Dashboard Widget — native PySide6 port of CustomDashboard.jsx.
Renders a configurable responsive grid of cards (Rashi, Navamsha, Dashamsha,
Planets, Dasha, Shadbala, Ashtakavarga, Yogas, Sade Sati, etc.).
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QGridLayout, QSizePolicy, QMenu,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY)
from gui.widgets.north_indian_chart import NorthIndianChartWidget
from gui.utils.planet_colors import rashi_name


DEFAULT_WIDGET_IDS = [
    "chart_rashi",
    "chart_navamsha",
    "chart_dashamsha",
    "report_planets",
    "report_complete_dasha",
    "report_shadbala",
    "report_ashtakavarga",
    "report_yogas",
    "report_sadesati_adhaiya",
]


class CustomDashboardPage(QWidget):
    """
    Configurable Dashboard displaying a grid of astrology cards.
    """
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._active_widgets = list(DEFAULT_WIDGET_IDS)
        self._build_ui()
        if data:
            self.refresh(data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header Control Bar
        hdr = QHBoxLayout()
        title = QLabel("✨ " + ("कस्टमाइज ड्यासबोर्ड (Custom Dashboard)" if self._is_ne else "Customized Dashboard"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 17px; font-weight: 700;")
        hdr.addWidget(title)
        hdr.addStretch()

        add_btn = QPushButton("➕ " + ("विजेट थप्नुहोस्" if self._is_ne else "Add Widget"))
        add_btn.setStyleSheet(f"background: {BG_TERTIARY}; color: {COLOR_GOLD}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 6px 12px; font-weight: 700;")
        add_btn.setMenu(self._build_add_menu())
        hdr.addWidget(add_btn)

        reset_btn = QPushButton("🔄 " + ("रिसेट गर्नुहोस्" if self._is_ne else "Reset Layout"))
        reset_btn.setStyleSheet(f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 6px 12px;")
        reset_btn.clicked.connect(self._reset_layout)
        hdr.addWidget(reset_btn)

        layout.addLayout(hdr)

        # Main Scroll Area containing Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll, 1)

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(14)
        scroll.setWidget(self._container)

    def _build_add_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet(f"background: {BG_SECONDARY}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {BORDER_COLOR};")

        available = [
            ("chart_rashi", "राशि कुण्डली (D1)"),
            ("chart_navamsha", "नवांश कुण्डली (D9)"),
            ("chart_dashamsha", "दशमांश कुण्डली (D10)"),
            ("report_planets", "ग्रह स्थिति विवरण"),
            ("report_complete_dasha", "सम्पूर्ण दशा तथा फलादेश"),
            ("report_shadbala", "षड्बल बल"),
            ("report_ashtakavarga", "अष्टकवर्ग"),
            ("report_yogas", "पराशर योग रिपोर्ट"),
            ("report_kaal_sarp_dosha", "कालसर्प दोष"),
            ("report_sadesati_adhaiya", "साढेसाती / अढैया"),
            ("report_panchang", "पञ्चाङ्ग विवरण"),
        ]
        for w_id, w_name in available:
            act = menu.addAction(w_name)
            act.triggered.connect(lambda checked=False, wid=w_id: self._add_widget(wid))
        return menu

    def _add_widget(self, wid: str):
        if wid not in self._active_widgets:
            self._active_widgets.append(wid)
            if self._data:
                self.refresh(self._data)

    def _remove_widget(self, wid: str):
        if wid in self._active_widgets:
            self._active_widgets.remove(wid)
            if self._data:
                self.refresh(self._data)

    def _reset_layout(self):
        self._active_widgets = list(DEFAULT_WIDGET_IDS)
        if self._data:
            self.refresh(self._data)

    def refresh(self, data: dict):
        self._data = data

        # Clear existing grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            lbl = QLabel("कुण्डली विवरण उपलब्ध छैन।" if self._is_ne else "No chart data available.")
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
            self._grid.addWidget(lbl, 0, 0)
            return

        row = 0
        col = 0
        max_cols = 3

        for wid in self._active_widgets:
            w_box = self._create_card_for_id(wid)
            if not w_box:
                continue

            # Determine column span
            col_span = 1
            if wid in ("report_planets", "report_complete_dasha", "report_sadesati_adhaiya"):
                col_span = 2 if (col + 2 <= max_cols) else 1

            self._grid.addWidget(w_box, row, col, 1, col_span)
            col += col_span
            if col >= max_cols:
                col = 0
                row += 1

    def _create_card_for_id(self, wid: str) -> Optional[QFrame]:
        card = QFrame()
        card.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        card.setMinimumHeight(280)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(6)

        # Card header with Title and Resize / Close controls
        chdr = QHBoxLayout()
        title_map = {
            "chart_rashi": ("राशि कुण्डली (D1)", "Rashi Chart (D1)"),
            "chart_navamsha": ("नवांश कुण्डली (D9)", "Navamsha (D9)"),
            "chart_dashamsha": ("दशमांश कुण्डली (D10)", "Dashamsha (D10)"),
            "report_planets": ("ग्रह स्थिति विवरण", "Planetary Positions"),
            "report_complete_dasha": ("सम्पूर्ण दशा तथा फलादेश", "Complete Dasha Report"),
            "report_shadbala": ("षड्बल विश्लेषण", "Shadbala Strengths"),
            "report_ashtakavarga": ("अष्टकवर्ग बिन्दु", "Ashtakavarga SAV"),
            "report_yogas": ("पराशर योग", "Parashara Yogas"),
            "report_kaal_sarp_dosha": ("कालसर्प दोष", "Kaal Sarp Dosha"),
            "report_sadesati_adhaiya": ("साढेसाती / अढैया", "Sade Sati Status"),
            "report_panchang": ("पञ्चाङ्ग विवरण", "Panchang Details"),
        }
        ne_t, en_t = title_map.get(wid, (wid, wid))
        t_lbl = QLabel(ne_t if self._is_ne else en_t)
        t_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 13px; font-weight: 700;")
        chdr.addWidget(t_lbl)
        chdr.addStretch()

        # Resize Height controls
        h_down = QPushButton("➖")
        h_down.setToolTip("उचाइ घटाउनुहोस् (Shrink Height)")
        h_down.setFixedSize(24, 22)
        h_down.setStyleSheet("font-size: 10px; padding: 0;")
        h_down.clicked.connect(lambda checked=False, c=card: c.setMinimumHeight(max(180, c.height() - 60)))
        chdr.addWidget(h_down)

        h_up = QPushButton("➕")
        h_up.setToolTip("उचाइ बढाउनुहोस् (Expand Height)")
        h_up.setFixedSize(24, 22)
        h_up.setStyleSheet("font-size: 10px; padding: 0;")
        h_up.clicked.connect(lambda checked=False, c=card: c.setMinimumHeight(c.height() + 60))
        chdr.addWidget(h_up)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none; font-weight: bold; background: transparent;")
        close_btn.clicked.connect(lambda checked=False, id=wid: self._remove_widget(id))
        chdr.addWidget(close_btn)
        cl.addLayout(chdr)

        # Card Content Widget
        if wid in ("chart_rashi", "chart_navamsha", "chart_dashamsha"):
            v_code = "D1" if wid == "chart_rashi" else ("D9" if wid == "chart_navamsha" else "D10")
            chart_w = NorthIndianChartWidget(self._data, v_code, self._lang, card)
            cl.addWidget(chart_w, 1)
        elif wid == "report_planets":
            from gui.widgets.planetary_info import PlanetaryInfoPage
            p_w = PlanetaryInfoPage(self._data, self._lang, card)
            cl.addWidget(p_w, 1)
        elif wid == "report_complete_dasha":
            from gui.widgets.complete_dasha import CompleteDashaPage
            d_w = CompleteDashaPage(self._data, self._lang, card)
            cl.addWidget(d_w, 1)
        elif wid == "report_shadbala":
            from gui.widgets.shadbala_widget import ShadbalaPage
            s_w = ShadbalaPage(self._data, self._lang, card)
            cl.addWidget(s_w, 1)
        elif wid == "report_ashtakavarga":
            from gui.widgets.ashtakavarga import AshtakavargaPage
            a_w = AshtakavargaPage(self._data, self._lang, card)
            cl.addWidget(a_w, 1)
        elif wid == "report_yogas":
            from gui.widgets.yoga_report import YogaReportPage
            y_w = YogaReportPage(self._data, self._lang, card)
            cl.addWidget(y_w, 1)
        elif wid == "report_kaal_sarp_dosha":
            from gui.widgets.kaal_sarp_dosha import KaalSarpDoshaPage
            ksd_w = KaalSarpDoshaPage(self._data, self._lang, card)
            cl.addWidget(ksd_w, 1)
        elif wid == "report_sadesati_adhaiya":
            from gui.widgets.sadesati import SadeSatiPage
            ss_w = SadeSatiPage(self._data, self._lang, card)
            cl.addWidget(ss_w, 1)
        elif wid == "report_panchang":
            from gui.widgets.panchang_info import PanchangInfoPage
            pc_w = PanchangInfoPage(self._data, self._lang, card)
            cl.addWidget(pc_w, 1)
        else:
            lbl = QLabel(wid)
            cl.addWidget(lbl, 1)

        return card
