# -*- coding: utf-8 -*-
"""
gui/widgets/remedies_page.py

Gemstones, Rudraksha & Vedic Remedies (रत्न, रुद्राक्ष तथा वैदिक उपचार) Widget
Displays:
  - Recommended Gemstones (Life Stone, Lucky Stone, Knowledge/Punya Stone, Yogakaraka Stone)
  - Strict Forbidden Gemstone warnings (6/8/12 lords) and incompatible combinations
  - Rudraksha recommendations (1-14 Mukhi based on Lagnesha, 9th lord, afflicted grahas)
  - Vedic, Tantrik, and Gayatri Mantras with target Japa counts
  - Planetary Charity (Daan), Fasting (Vrata), and Yantras
"""

from __future__ import annotations
import sys
import os
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QPushButton, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    COLOR_GOLD, BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_ACCENT
)
from backend.calculator.remedies import calculate_remedies


class RemediesPage(QWidget):
    """Vedic Gemstones, Rudraksha & Remedies Page."""

    def __init__(self, data: Optional[Dict[str, Any]], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"

        self._active_tab = 0  # 0: Gemstones, 1: Rudraksha, 2: Mantras, 3: Charity & Fasting
        self._tab_buttons: List[QPushButton] = []

        self._build_ui()
        if data:
            self.refresh(data)

    def _t(self, en: str, ne: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(14)

        # Header Title
        header = QHBoxLayout()
        title_icon = QLabel("💎")
        title_icon.setStyleSheet("font-size: 26px;")
        header.addWidget(title_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        main_title = QLabel(self._t("Gemstones, Rudraksha & Vedic Remedies", "रत्न, रुद्राक्ष तथा वैदिक उपचार परामर्श"))
        main_title.setStyleSheet(f"font-size: 19px; font-weight: bold; color: {COLOR_GOLD};")
        sub_title = QLabel(self._t(
            "Classical Parashari astrological remedial measures based on your horoscope",
            "बृहत्पाराशर होराशास्त्र अनुसार कुण्डलीका अनुकूल रत्न, रुद्राक्ष, मन्त्र, दान तथा यन्त्र"
        ))
        sub_title.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        title_col.addWidget(main_title)
        title_col.addWidget(sub_title)
        header.addLayout(title_col)
        header.addStretch()

        root_layout.addLayout(header)

        # Navigation Switcher Tabs
        tabs_bar = QHBoxLayout()
        tabs_bar.setSpacing(8)

        tab_defs = [
            ("💎 " + self._t("Gemstones", "रत्न सिफारिस"), 0),
            ("📿 " + self._t("Rudraksha", "रुद्राक्ष परामर्श"), 1),
            ("🕉️ " + self._t("Mantras & Japa", "मन्त्र तथा जप"), 2),
            ("🎁 " + self._t("Charity & Fasting", "दान, व्रत र यन्त्र"), 3),
        ]

        self._tab_buttons.clear()
        for label, idx in tab_defs:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            btn.clicked.connect(lambda checked=False, i=idx: self._switch_tab(i))
            tabs_bar.addWidget(btn)
            self._tab_buttons.append(btn)

        tabs_bar.addStretch()
        root_layout.addLayout(tabs_bar)

        # Content Stack Widget inside Scroll Area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ background: {BG_SECONDARY}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {BORDER_COLOR}; border-radius: 4px; min-height: 20px; }}
        """)

        self._stack = QStackedWidget()

        # Build sub-pages
        self._page_gemstones = QWidget()
        self._page_rudraksha = QWidget()
        self._page_mantras = QWidget()
        self._page_charity = QWidget()

        self._stack.addWidget(self._page_gemstones)
        self._stack.addWidget(self._page_rudraksha)
        self._stack.addWidget(self._page_mantras)
        self._stack.addWidget(self._page_charity)

        self._scroll.setWidget(self._stack)
        root_layout.addWidget(self._scroll, 1)

        self._update_tab_button_styles()

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        self._stack.setCurrentIndex(idx)
        self._update_tab_button_styles()

    def _update_tab_button_styles(self):
        for i, btn in enumerate(self._tab_buttons):
            if i == self._active_tab:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLOR_GOLD};
                        color: #111827;
                        border: none;
                        border-radius: 6px;
                        padding: 0 16px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {BG_SECONDARY};
                        color: {COLOR_TEXT_SECONDARY};
                        border: 1px solid {BORDER_COLOR};
                        border-radius: 6px;
                        padding: 0 16px;
                    }}
                    QPushButton:hover {{
                        background: {BG_TERTIARY};
                        color: {COLOR_TEXT_PRIMARY};
                    }}
                """)

    def refresh(self, data: Dict[str, Any]):
        self._data = data
        remedies = data.get("remedies")
        if not remedies:
            # Derive dynamically if missing
            planets = data.get("planets", [])
            lagna_sign = (data.get("lagna") or {}).get("sign_number", 1)
            dasha = data.get("dasha", [])
            remedies = calculate_remedies(planets, lagna_sign, dasha_data=dasha, language=self._lang)

        self._render_gemstones_tab(remedies)
        self._render_rudraksha_tab(remedies)
        self._render_mantras_tab(remedies)
        self._render_charity_tab(remedies)

    # ─────────────────────────────────────────────────────────────────────────
    # Tab 1: Gemstones
    # ─────────────────────────────────────────────────────────────────────────
    def _render_gemstones_tab(self, remedies: Dict[str, Any]):
        # Clear existing layout
        if self._page_gemstones.layout():
            QWidget().setLayout(self._page_gemstones.layout())

        layout = QVBoxLayout(self._page_gemstones)
        layout.setContentsMargins(0, 4, 0, 16)
        layout.setSpacing(16)

        # Section 1: Recommended Gemstones Cards Grid
        grid = QGridLayout()
        grid.setSpacing(14)

        rec_gems = remedies.get("recommended_gemstones", [])
        for i, gem in enumerate(rec_gems):
            card = self._create_gemstone_card(gem)
            row = i // 2
            col = i % 2
            grid.addWidget(card, row, col)

        layout.addLayout(grid)

        # Section 2: Conflict warnings if any
        conflicts = remedies.get("conflict_warnings", [])
        if conflicts:
            conflict_box = QFrame()
            conflict_box.setStyleSheet(f"""
                QFrame {{
                    background: rgba(239, 68, 68, 0.12);
                    border: 1px solid {COLOR_ERROR};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            c_lay = QVBoxLayout(conflict_box)
            c_lay.setSpacing(6)
            c_title = QLabel("⚠️ " + self._t("Hostile Gemstone Combination Alert", "विरोधी रत्न संयोजन चेतावनी"))
            c_title.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold; font-size: 13px;")
            c_lay.addWidget(c_title)
            for warn in conflicts:
                lbl = QLabel(f"• {warn}")
                lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px;")
                lbl.setWordWrap(True)
                c_lay.addWidget(lbl)
            layout.addWidget(conflict_box)

        # Section 3: Forbidden Gemstones Box
        forbidden = remedies.get("forbidden_gemstones", [])
        if forbidden:
            forbid_box = QFrame()
            forbid_box.setStyleSheet(f"""
                QFrame {{
                    background: {BG_SECONDARY};
                    border: 1px solid #7f1d1d;
                    border-radius: 8px;
                    padding: 14px;
                }}
            """)
            f_lay = QVBoxLayout(forbid_box)
            f_lay.setSpacing(8)

            f_hdr = QHBoxLayout()
            f_icon = QLabel("🛑")
            f_icon.setStyleSheet("font-size: 16px;")
            f_title = QLabel(self._t(
                "Strictly Prohibited Gemstones for this Horoscope (निषेध)",
                "यस कुण्डलीका लागि निषेधित तथा हानिकारक रत्नहरू (कदापि नलगाउनु होला)"
            ))
            f_title.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold; font-size: 14px;")
            f_hdr.addWidget(f_icon)
            f_hdr.addWidget(f_title)
            f_hdr.addStretch()
            f_lay.addLayout(f_hdr)

            desc = QLabel(self._t(
                "Wearing gemstones of 6th, 8th, or 12th house lords activates debt, illness, accidents, and financial drains:",
                "कुण्डलीमा त्रिक भाव (६, ८ वा १२ भाव) का स्वामी ग्रहहरूको रत्न लगाउँदा रोग, ऋण, मुद्दा-मामिला वा आर्थिक क्षति बढ्ने हुनाले निम्न रत्नहरू निषेध गरिएको छ:"
            ))
            desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
            desc.setWordWrap(True)
            f_lay.addWidget(desc)

            for item in forbidden:
                row_widget = QWidget()
                r_lay = QHBoxLayout(row_widget)
                r_lay.setContentsMargins(4, 2, 4, 2)

                p_badge = QLabel(f"❌ {item.get('gemstone')} ({item.get('planet')})")
                p_badge.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold; font-size: 12px; min-width: 170px;")
                r_lay.addWidget(p_badge)

                reason = QLabel(item.get("reason", ""))
                reason.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
                reason.setWordWrap(True)
                r_lay.addWidget(reason, 1)

                f_lay.addWidget(row_widget)

            layout.addWidget(forbid_box)

        # Section 4: General Guidelines
        guidelines = remedies.get("general_guidelines", [])
        if guidelines:
            guide_box = QFrame()
            guide_box.setStyleSheet(f"""
                QFrame {{
                    background: {BG_SECONDARY};
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            g_lay = QVBoxLayout(guide_box)
            g_title = QLabel("📜 " + self._t("Important Rules for Wearing Gemstones", "रत्न धारण सम्बन्धी महत्वपूर्ण शास्त्रीय नियम"))
            g_title.setStyleSheet(f"color: {COLOR_GOLD}; font-weight: bold; font-size: 13px;")
            g_lay.addWidget(g_title)
            for rule in guidelines:
                r_lbl = QLabel(f"• {rule}")
                r_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
                r_lbl.setWordWrap(True)
                g_lay.addWidget(r_lbl)
            layout.addWidget(guide_box)

    def _create_gemstone_card(self, gem: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 14px;
            }}
            QFrame:hover {{
                border: 1px solid {COLOR_GOLD};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Category Header
        top_row = QHBoxLayout()
        cat_name = QLabel(gem.get("category_name", ""))
        cat_name.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 14px; font-weight: bold;")
        top_row.addWidget(cat_name)

        planet_badge = QLabel(f" {gem.get('planet')} ")
        planet_badge.setStyleSheet(f"""
            background: {BG_TERTIARY};
            color: {COLOR_ACCENT};
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 6px;
        """)
        top_row.addStretch()
        top_row.addWidget(planet_badge)
        layout.addLayout(top_row)

        # Gemstone Name Main
        gem_name = QLabel(gem.get("gemstone", ""))
        gem_name.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(gem_name)

        # Upratna
        upratna = gem.get("upratna")
        if upratna:
            u_lbl = QLabel(f"• {self._t('Alternative/Sub-stone', 'उपरत्न')}: {upratna}")
            u_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            layout.addWidget(u_lbl)

        # Key specs grid
        specs_grid = QGridLayout()
        specs_grid.setContentsMargins(0, 4, 0, 4)
        specs_grid.setHorizontalSpacing(10)
        specs_grid.setVerticalSpacing(4)

        specs = [
            (self._t("Metal", "धातु"), gem.get("metal", "")),
            (self._t("Finger", "औंला"), gem.get("finger", "")),
            (self._t("Auspicious Time", "शुभ समय"), gem.get("day", "")),
            (self._t("Min Weight", "तौल"), gem.get("min_weight", "")),
        ]

        for idx, (label, val) in enumerate(specs):
            row = idx // 2
            col = (idx % 2) * 2

            l_lbl = QLabel(f"{label}:")
            l_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 500;")
            v_lbl.setWordWrap(True)

            specs_grid.addWidget(l_lbl, row, col)
            specs_grid.addWidget(v_lbl, row, col + 1)

        layout.addLayout(specs_grid)

        # Beej Mantra Box
        mantra_box = QFrame()
        mantra_box.setStyleSheet(f"""
            background: {BG_PRIMARY};
            border-radius: 6px;
            padding: 6px 10px;
        """)
        m_lay = QVBoxLayout(mantra_box)
        m_lay.setContentsMargins(6, 6, 6, 6)
        m_lay.setSpacing(2)

        m_title = QLabel(f"ॐ {self._t('Beej Mantra', 'बीज मन्त्र')} ({gem.get('jap_count', '')}):")
        m_title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 10px; font-weight: bold;")
        m_txt = QLabel(gem.get("beej_mantra", ""))
        m_txt.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")

        m_lay.addWidget(m_title)
        m_lay.addWidget(m_txt)
        layout.addWidget(mantra_box)

        # Benefits
        benefit = gem.get("benefit", "")
        if benefit:
            b_lbl = QLabel(f"✨ {benefit}")
            b_lbl.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 11px;")
            b_lbl.setWordWrap(True)
            layout.addWidget(b_lbl)

        return card

    # ─────────────────────────────────────────────────────────────────────────
    # Tab 2: Rudraksha
    # ─────────────────────────────────────────────────────────────────────────
    def _render_rudraksha_tab(self, remedies: Dict[str, Any]):
        if self._page_rudraksha.layout():
            QWidget().setLayout(self._page_rudraksha.layout())

        layout = QVBoxLayout(self._page_rudraksha)
        layout.setContentsMargins(0, 4, 0, 16)
        layout.setSpacing(14)

        intro = QLabel(self._t(
            "Rudraksha beads carry cosmic electrical impulses that harmonize damaged or afflicted chakras and planetary energies without negative side-effects:",
            "रुद्राक्ष साक्षात् भगवान् शिवको अश्रुबाट उत्पन्न भएको महा-कवच हो। यसले कुण्डलीका पीडित ग्रहको नकारात्मक प्रभाव हटाई आध्यात्मिक र भौतिक रक्षा प्रदान गर्छ:"
        ))
        intro.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        rud_list = remedies.get("rudraksha_recommendations", [])
        grid = QGridLayout()
        grid.setSpacing(14)

        for i, rud in enumerate(rud_list):
            card = self._create_rudraksha_card(rud)
            row = i // 2
            col = i % 2
            grid.addWidget(card, row, col)

        layout.addLayout(grid)

        # Wearing procedure
        vidhi_box = QFrame()
        vidhi_box.setStyleSheet(f"""
            QFrame {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        v_lay = QVBoxLayout(vidhi_box)
        v_title = QLabel("📿 " + self._t("Rudraksha Wearing Procedure (धारण विधि)", "रुद्राक्ष धारण विधि"))
        v_title.setStyleSheet(f"color: {COLOR_GOLD}; font-weight: bold; font-size: 13px;")
        v_lay.addWidget(v_title)

        v_text = QLabel(self._t(
            "1. Wear in silk/cotton red, yellow, or white thread, or cap with silver/gold.\n"
            "2. Wear on Monday morning, Shukla Paksha, or on Shivaratri/Pradosh.\n"
            "3. Clean with raw milk and holy water (Gangajal), offer sandalwood paste and white flowers, chant 'Om Namah Shivaya' 108 times before wearing.",
            "१. रातो वा पहेंलो धागोमा, वा चाँदी/सुनको पाता लगाएर घाँटी वा पाखुरामा धारण गर्नुहोस्।\n"
            "२. कुनै पनि सोमबार, शुक्ल पक्षको त्रयोदशी (प्रदोष) वा शिवरात्रिका दिन बिहान धारण गर्नु उत्तम हुन्छ।\n"
            "३. काँचो दूध र गंगाजलले शुद्ध गरी चन्दन-फूल चढाई 'ॐ नमः शिवाय' मन्त्र १०८ पटक जप गरेर मात्र धारण गर्नुहोस्।"
        ))
        v_text.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        v_text.setWordWrap(True)
        v_lay.addWidget(v_text)

        layout.addWidget(vidhi_box)

    def _create_rudraksha_card(self, rud: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel(rud.get("title", ""))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-weight: bold; font-size: 12px;")
        header.addWidget(title)
        header.addStretch()

        planet_badge = QLabel(rud.get("planet", ""))
        planet_badge.setStyleSheet(f"""
            background: {BG_TERTIARY};
            color: {COLOR_ACCENT};
            border-radius: 4px;
            font-size: 10px;
            padding: 2px 6px;
        """)
        header.addWidget(planet_badge)
        layout.addLayout(header)

        mukhi_name = QLabel(rud.get("mukhi", ""))
        mukhi_name.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(mukhi_name)

        deity = QLabel(f"👑 {self._t('Presiding Deity', 'अधिष्ठात्री देवता')}: {rud.get('deity', '')}")
        deity.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(deity)

        benefit = rud.get("benefit", "")
        if benefit:
            b_lbl = QLabel(f"✨ {benefit}")
            b_lbl.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 11px;")
            b_lbl.setWordWrap(True)
            layout.addWidget(b_lbl)

        mantra = rud.get("mantra")
        if mantra:
            m_lbl = QLabel(f"🕉️ {self._t('Wearing Mantra', 'धारण मन्त्र')}: {mantra}")
            m_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 11px; font-weight: bold;")
            layout.addWidget(m_lbl)

        return card

    # ─────────────────────────────────────────────────────────────────────────
    # Tab 3: Mantras & Japa
    # ─────────────────────────────────────────────────────────────────────────
    def _render_mantras_tab(self, remedies: Dict[str, Any]):
        if self._page_mantras.layout():
            QWidget().setLayout(self._page_mantras.layout())

        layout = QVBoxLayout(self._page_mantras)
        layout.setContentsMargins(0, 4, 0, 16)
        layout.setSpacing(12)

        info_lbl = QLabel(self._t(
            "Planetary Mantras (ग्रह शान्ति मन्त्र) soothe malefic energies, awaken dormant strengths, and bestow divine grace:",
            "वैदिक तथा तान्त्रिक मन्त्रको नियमित जपले अशुभ ग्रहका दोषहरू शान्त भई जीवनमा शान्ति, स्वास्थ्य र समृद्धि प्राप्त हुन्छ:"
        ))
        info_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(info_lbl)

        table = QTableWidget()
        table.setColumnCount(5)
        headers = [
            self._t("Planet", "ग्रह"),
            self._t("Beej Mantra", "तान्त्रिक बीज मन्त्र"),
            self._t("Gayatri Mantra", "ग्रह गायत्री मन्त्र"),
            self._t("Simple Mantra", "सामान्य मन्त्र"),
            self._t("Target Japa", "जप संख्या"),
        ]
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_SECONDARY};
                gridline-color: {BORDER_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {BG_TERTIARY};
                color: {COLOR_GOLD};
                font-weight: bold;
                padding: 6px;
                border: none;
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)

        mc_list = remedies.get("mantras_and_charity", [])
        table.setRowCount(len(mc_list))

        for row, item in enumerate(mc_list):
            p_item = QTableWidgetItem(item.get("planet", ""))
            p_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            p_item.setForeground(QBrush(QColor(COLOR_GOLD)))
            table.setItem(row, 0, p_item)

            table.setItem(row, 1, QTableWidgetItem(item.get("beej_mantra", "")))
            table.setItem(row, 2, QTableWidgetItem(item.get("gayatri_mantra", "")))
            table.setItem(row, 3, QTableWidgetItem(item.get("simple_mantra", "")))

            jap_item = QTableWidgetItem(item.get("jap_count", ""))
            jap_item.setForeground(QBrush(QColor(COLOR_SUCCESS)))
            table.setItem(row, 4, jap_item)

        table.setMinimumHeight(400)
        layout.addWidget(table)

    # ─────────────────────────────────────────────────────────────────────────
    # Tab 4: Charity & Fasting & Yantras
    # ─────────────────────────────────────────────────────────────────────────
    def _render_charity_tab(self, remedies: Dict[str, Any]):
        if self._page_charity.layout():
            QWidget().setLayout(self._page_charity.layout())

        layout = QVBoxLayout(self._page_charity)
        layout.setContentsMargins(0, 4, 0, 16)
        layout.setSpacing(14)

        info = QLabel(self._t(
            "Planetary Charity (Daan) dissipates negative karma, while Fasting (Vrata) purifies body and mind:",
            "ग्रहहरूको अनिष्ट फल नाश गर्न दान सामग्री, व्रत र यन्त्र स्थापनाको महत्वपूर्ण भूमिका हुन्छ:"
        ))
        info.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(info)

        table = QTableWidget()
        table.setColumnCount(5)
        headers = [
            self._t("Planet", "ग्रह"),
            self._t("Donation Items", "दान सामग्री"),
            self._t("Recipient", "दान पाउने योग्य पात्र"),
            self._t("Fasting Day & Method", "व्रत बार तथा विधि"),
            self._t("Yantra", "पूजनीय यन्त्र"),
        ]
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_SECONDARY};
                gridline-color: {BORDER_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {BG_TERTIARY};
                color: {COLOR_GOLD};
                font-weight: bold;
                padding: 6px;
                border: none;
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)

        mc_list = remedies.get("mantras_and_charity", [])
        table.setRowCount(len(mc_list))

        for row, item in enumerate(mc_list):
            p_item = QTableWidgetItem(item.get("planet", ""))
            p_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            p_item.setForeground(QBrush(QColor(COLOR_GOLD)))
            table.setItem(row, 0, p_item)

            table.setItem(row, 1, QTableWidgetItem(item.get("charity_items", "")))
            table.setItem(row, 2, QTableWidgetItem(item.get("charity_recipient", "")))
            table.setItem(row, 3, QTableWidgetItem(item.get("fasting_day", "")))

            y_item = QTableWidgetItem(item.get("yantra", ""))
            y_item.setForeground(QBrush(QColor(COLOR_ACCENT)))
            table.setItem(row, 4, y_item)

        table.setMinimumHeight(400)
        layout.addWidget(table)
