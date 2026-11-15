"""
gui/widgets/bhava_chalit.py

Bhava Chalit (भाव चलित कुण्डली) Page — Complete Classical Parashari & Shripati Padhati view.
Features:
  - Shripati Bhava Chalit Chart & BPHS Bhava Lagna Chart
  - Interactive North Indian Chart
  - 12 Houses Bhava Madhya, Arambha/Virama Sandhi, and Extent Table
  - Planet Rashi vs Bhava Chalit Shift Analysis Table
  - Pure White / Clean Light Theme (No Dark Backgrounds)
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QButtonGroup, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from gui.widgets.north_indian_chart import NorthIndianChartWidget
from gui.utils.planet_colors import (
    planet_color, planet_abbr, rashi_name,
    PLANET_ABBR, RASHI_NAMES
)

# ── Pure White / Light Theme Colors ──────────────────────────────────────────
COLOR_BG_PAGE       = "#ffffff"
COLOR_CARD_BG       = "#ffffff"
COLOR_CARD_BORDER   = "#e2e8f0"
COLOR_PRIMARY_GOLD  = "#b45309"
COLOR_ACCENT_BLUE   = "#2563eb"
COLOR_TEXT_MAIN     = "#0f172a"
COLOR_TEXT_MUTED    = "#64748b"
COLOR_ROW_ALT       = "#f8fafc"
COLOR_HIGHLIGHT_BG  = "#fef3c7"
COLOR_SHIFT_BADGE   = "#dc2626"
COLOR_STABLE_BADGE  = "#16a34a"

def _section_card(title: str, content_widget: QWidget, icon: str = "✦") -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {COLOR_CARD_BG};
            border: 1px solid {COLOR_CARD_BORDER};
            border-radius: 8px;
            padding: 8px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 8, 10, 10)
    lay.setSpacing(8)

    hdr = QHBoxLayout()
    hdr.setSpacing(6)
    ico_lbl = QLabel(icon)
    ico_lbl.setStyleSheet(f"color:{COLOR_PRIMARY_GOLD}; font-size:14px; font-weight:700; background:transparent;")
    hdr.addWidget(ico_lbl)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color:{COLOR_PRIMARY_GOLD}; font-size:13px; font-weight:700; background:transparent;")
    hdr.addWidget(title_lbl)
    hdr.addStretch()
    lay.addLayout(hdr)

    lay.addWidget(content_widget)
    return frame


class BhavaChalitAnalysisPanel(QWidget):
    """Right-side comprehensive analytical panel for Bhava Chalit."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{COLOR_BG_PAGE};")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(12)

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load(self, chart_data: Optional[dict], language: str = "ne"):
        self._clear()
        if not chart_data:
            lbl = QLabel("कुण्डली डाटा उपलब्ध छैन।\nकृपया पहिले जन्म विवरण भर्नुस्।")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:13px;")
            self._layout.addWidget(lbl)
            self._layout.addStretch()
            return

        try:
            try:
                from backend.calculator.bhava_chalit import analyze_bhava_chalit
            except ImportError:
                from calculator.bhava_chalit import analyze_bhava_chalit
            res = analyze_bhava_chalit(chart_data, language)
            self._render(res, language)
        except Exception as e:
            lbl = QLabel(f"⚠ विश्लेषणमा त्रुटि: {e}")
            lbl.setStyleSheet("color:#b91c1c;font-size:12px;")
            self._layout.addWidget(lbl)
            self._layout.addStretch()

    def _render(self, r: dict, lang: str):
        lay = self._layout
        is_ne = lang == "ne"

        # ── 1. Summary Card ──────────────────────────────────────────────────
        sum_box = QFrame()
        sum_box.setStyleSheet("background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:8px;")
        sl = QVBoxLayout(sum_box)
        sl.setContentsMargins(6, 6, 6, 6)
        sl.setSpacing(4)

        stitle = QLabel("📌 भाव चलित निष्कर्ष (Summary & Overview)")
        stitle.setStyleSheet("color:#b45309;font-size:12px;font-weight:700;background:transparent;")
        sl.addWidget(stitle)

        sdesc = QLabel(r.get("summary_ne" if is_ne else "summary_en", ""))
        sdesc.setWordWrap(True)
        sdesc.setStyleSheet(f"color:{COLOR_TEXT_MAIN};font-size:11px;line-height:1.5;background:transparent;")
        sl.addWidget(sdesc)

        # Quick stats badges
        sbadges = QHBoxLayout()
        sbadges.setSpacing(6)
        b1 = QLabel(f"चलित (सरेका ग्रह): <b>{r.get('shifted_count_ne' if is_ne else 'shifted_count')}</b>")
        b1.setStyleSheet("background:#fee2e2;color:#b91c1c;border:1px solid #f87171;border-radius:4px;padding:3px 6px;font-size:11px;")
        sbadges.addWidget(b1)

        b2 = QLabel(f"स्थिर (नचलेका): <b>{r.get('unshifted_count_ne' if is_ne else 'unshifted_count')}</b>")
        b2.setStyleSheet("background:#dcfce7;color:#15803d;border:1px solid #86efac;border-radius:4px;padding:3px 6px;font-size:11px;")
        sbadges.addWidget(b2)
        sbadges.addStretch()
        sl.addLayout(sbadges)

        lay.addWidget(sum_box)

        # ── 2. Planet Shift Analysis Table ───────────────────────────────────
        p_table = QTableWidget()
        p_table.setColumnCount(5)
        p_table.setHorizontalHeaderLabels([
            "ग्रह", "राशि / अंश", "राशि भाव", "चलित भाव", "चलित स्थिति"
        ] if is_ne else [
            "Planet", "Sign / Deg", "Rashi H", "Chalit H", "Shift Status"
        ])
        p_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        p_table.horizontalHeader().setStretchLastSection(True)
        p_table.verticalHeader().setVisible(False)
        p_table.setAlternatingRowColors(True)
        p_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                alternate-background-color: {COLOR_ROW_ALT};
                gridline-color: #e2e8f0;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 700;
                padding: 4px;
                border: 1px solid #e2e8f0;
            }}
        """)

        planets_data = r.get("planets", [])
        p_table.setRowCount(len(planets_data))
        for row_idx, p in enumerate(planets_data):
            p_name = p.get("name_ne" if is_ne else "name", "")
            sign_name = p.get("sign_name_ne" if is_ne else "sign_name_en", "")
            deg_str = p.get("longitude_dms_ne" if is_ne else "longitude_dms_en", "")
            r_h = str(p.get("rashi_house", ""))
            c_h = str(p.get("bhava_house", ""))
            shift_text = p.get("shift_text_ne" if is_ne else "shift_text_en", "")
            is_shifted = p.get("is_shifted", False)

            item_p = QTableWidgetItem(f" {p_name}")
            item_p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p_table.setItem(row_idx, 0, item_p)

            item_sign = QTableWidgetItem(f"{sign_name} ({deg_str})")
            p_table.setItem(row_idx, 1, item_sign)

            item_rh = QTableWidgetItem(f"{r_h}औँ भाव")
            item_rh.setTextAlignment(Qt.AlignCenter)
            p_table.setItem(row_idx, 2, item_rh)

            item_ch = QTableWidgetItem(f"{c_h}औँ भाव")
            item_ch.setTextAlignment(Qt.AlignCenter)
            if is_shifted:
                item_ch.setForeground(QColor("#b91c1c"))
                item_ch.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p_table.setItem(row_idx, 3, item_ch)

            item_st = QTableWidgetItem(shift_text)
            if is_shifted:
                item_st.setForeground(QColor("#b91c1c"))
                item_st.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:
                item_st.setForeground(QColor("#15803d"))
            p_table.setItem(row_idx, 4, item_st)

        p_table.setFixedHeight(min(320, len(planets_data) * 28 + 32))
        lay.addWidget(_section_card("🪐 ग्रह चलित विश्लेषण (Planetary Shift Analysis)", p_table, "🪐"))

        # ── 3. 12 Houses Cusp & Sandhi Table ─────────────────────────────────
        h_table = QTableWidget()
        h_table.setColumnCount(6)
        h_table.setHorizontalHeaderLabels([
            "भाव", "मध्य राशि (अंश)", "प्रारम्भ सन्धि", "मध्य", "समाप्ति सन्धि", "भावस्थ ग्रह"
        ] if is_ne else [
            "House", "Sign (Cusp)", "Start Sandhi", "Madhya", "End Sandhi", "Occupants"
        ])
        h_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        h_table.horizontalHeader().setStretchLastSection(True)
        h_table.verticalHeader().setVisible(False)
        h_table.setAlternatingRowColors(True)
        h_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                alternate-background-color: {COLOR_ROW_ALT};
                gridline-color: #e2e8f0;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 700;
                padding: 4px;
                border: 1px solid #e2e8f0;
            }}
        """)

        houses_data = r.get("houses", [])
        h_table.setRowCount(len(houses_data))
        for row_idx, h in enumerate(houses_data):
            h_name = h.get("house_name_ne" if is_ne else "house_name_en", "")
            sign_name = h.get("sign_name_ne" if is_ne else "sign_name_en", "")
            lord_name = h.get("lord_ne" if is_ne else "lord_en", "")
            start_str = h.get("start_sandhi_dms_ne" if is_ne else "start_sandhi_dms_en", "")
            madhya_str = h.get("madhya_dms_ne" if is_ne else "madhya_dms_en", "")
            end_str = h.get("end_sandhi_dms_ne" if is_ne else "end_sandhi_dms_en", "")
            
            occupants = [occ.get("name_ne" if is_ne else "name", "") for occ in h.get("occupants", [])]
            occ_str = ", ".join(occupants) if occupants else "—"

            item_h = QTableWidgetItem(f" {h_name}")
            item_h.setFont(QFont("Segoe UI", 9, QFont.Bold))
            h_table.setItem(row_idx, 0, item_h)

            item_sgn = QTableWidgetItem(f"{sign_name} ({lord_name})")
            h_table.setItem(row_idx, 1, item_sgn)

            item_st = QTableWidgetItem(start_str)
            h_table.setItem(row_idx, 2, item_st)

            item_md = QTableWidgetItem(madhya_str)
            item_md.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_md.setForeground(QColor("#2563eb"))
            h_table.setItem(row_idx, 3, item_md)

            item_en = QTableWidgetItem(end_str)
            h_table.setItem(row_idx, 4, item_en)

            item_occ = QTableWidgetItem(occ_str)
            if occupants:
                item_occ.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item_occ.setForeground(QColor("#b45309"))
            h_table.setItem(row_idx, 5, item_occ)

        h_table.setFixedHeight(min(380, len(houses_data) * 28 + 32))
        lay.addWidget(_section_card("📊 १२ भाव मध्य, सन्धि र विस्तार तालिका (Shripati Cusps)", h_table, "📊"))

        # ── 4. BPHS Bhava Lagna Details ──────────────────────────────────────
        bl = r.get("bhava_lagna", {})
        if bl:
            bl_box = QFrame()
            bl_box.setStyleSheet("background:#f8fafc;border:1px solid #cbd5e1;border-radius:6px;padding:8px;")
            bll = QVBoxLayout(bl_box)
            bll.setContentsMargins(6, 6, 6, 6)
            bll.setSpacing(4)

            bl_title = QLabel(f"🌟 भाव लग्न (BPHS Ch. 5): {bl.get('bhava_lagna_name_ne' if is_ne else 'bhava_lagna_name_en')} राशि")
            bl_title.setStyleSheet("color:#7c3aed;font-size:12px;font-weight:700;background:transparent;")
            bll.addWidget(bl_title)

            bl_text = QLabel(
                f"• सूर्योदय समय: <b>{bl.get('sunrise_time')}</b> | जन्म समय: <b>{bl.get('birth_time')}</b><br>"
                f"• सूर्योदय देखि जन्म सम्मको अन्तर: <b>{bl.get('diff_minutes_ne')} मिनेट</b><br>"
                f"• इष्ट घटी: <b>{bl.get('ishta_ghati_ne')} घटी</b> (घटी ÷ ५ = <b>{bl.get('offset_signs_ne')}</b> राशि विस्थापन)<br>"
                f"• जन्म लग्न (<b>{bl.get('birth_lagna_name_ne')}</b>) बाट {bl.get('offset_signs_ne')} राशि अगाडि गन्दा <b>भाव लग्न = {bl.get('bhava_lagna_name_ne')}</b> हुन आउँछ।"
            )
            bl_text.setWordWrap(True)
            bl_text.setStyleSheet(f"color:{COLOR_TEXT_MAIN};font-size:11px;line-height:1.5;background:transparent;")
            bll.addWidget(bl_text)
            lay.addWidget(_section_card("📖 विशेष भाव लग्न विवरण (BPHS Special Lagna)", bl_box, "📖"))

        # ── 5. Classical Rules & Principles ──────────────────────────────────
        rules_box = QFrame()
        rules_box.setStyleSheet("background:#f8fafc;border:1px solid #cbd5e1;border-radius:6px;padding:8px;")
        rl = QVBoxLayout(rules_box)
        rl.setContentsMargins(6, 6, 6, 6)
        rl.setSpacing(4)

        r_text = QLabel(
            "<b>शास्त्रीय सिद्धान्त र फलित नियम (श्रीपति पद्धति):</b><br>"
            "१. <b>भाव मध्यको महत्व:</b> जुन ग्रह भाव मध्यको जति नजिक हुन्छ, त्यसले सो भावको त्यति नै पूर्ण (१००%) फल प्रदान गर्दछ।<br>"
            "२. <b>भाव सन्धिको फल:</b> भाव आरम्भ वा समाप्ति सन्धिमा रहेका ग्रहहरूले नगण्य वा मिश्रित फल दिन्छन्।<br>"
            "३. <b>चलित स्थानान्तरण:</b> राशि कुण्डलीमा कुनै भावमा देखिए पनि यदि ग्रह अघिल्लो वा पछिल्लो भावको सन्धि पार गरिसकेको छ भने वास्तविक फलादेश भाव चलित कुण्डली अनुसार गरिन्छ।"
        )
        r_text.setWordWrap(True)
        r_text.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:11px;line-height:1.5;background:transparent;")
        rl.addWidget(r_text)
        lay.addWidget(_section_card("📜 शास्त्रीय नियम तथा मार्गदर्शन", rules_box, "📜"))

        lay.addStretch()


class BhavaChalitPage(QWidget):
    """
    Main page for Bhava Chalit Chart.
    Left: NorthIndianChartWidget displaying the Bhava Chalit Chart.
    Right: BhavaChalitAnalysisPanel with 12 Houses, Cusps, and Planet Shifts.
    """

    def __init__(self, chart_data: Optional[dict] = None, language: str = "ne",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data
        self._mode = "SHRIPATI"  # "SHRIPATI" or "BHAVA_LAGNA"

        self.setStyleSheet(f"background-color: {COLOR_BG_PAGE};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # ── Header Bar ───────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        title_lbl = QLabel("☯ भाव चलित कुण्डली (Bhava Chalit Chart)" if self._is_ne else "☯ Bhava Chalit Chart")
        title_lbl.setStyleSheet(f"color:{COLOR_PRIMARY_GOLD}; font-size:16px; font-weight:700;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()

        # Chart Switcher Buttons
        btn_grp = QButtonGroup(self)
        self._btn_shripati = QPushButton("श्रीपति भाव चलित" if self._is_ne else "Shripati Chalit")
        self._btn_bhava_lagna = QPushButton("भाव लग्न चक्र" if self._is_ne else "Bhava Lagna")
        for b in (self._btn_shripati, self._btn_bhava_lagna):
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("""
                QPushButton {
                    background: #f1f5f9;
                    color: #334155;
                    border: 1px solid #cbd5e1;
                    border-radius: 5px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background: #2563eb;
                    color: #ffffff;
                    border-color: #1d4ed8;
                }
            """)
            btn_grp.addButton(b)
            hdr.addWidget(b)

        self._btn_shripati.setChecked(True)
        self._btn_shripati.clicked.connect(lambda: self._set_chart_mode("SHRIPATI"))
        self._btn_bhava_lagna.clicked.connect(lambda: self._set_chart_mode("BHAVA_LAGNA"))

        main_layout.addLayout(hdr)

        # ── Splitter Layout: Left Chart, Right Analysis Panel ─────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLOR_CARD_BORDER};
                width: 2px;
            }}
        """)

        # Left Container (Chart)
        left_container = QWidget()
        left_container.setStyleSheet(f"background:{COLOR_BG_PAGE};")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(6)

        self._chart_title = QLabel("श्रीपति भाव चलित चक्र" if self._is_ne else "Shripati Bhava Chalit Chart")
        self._chart_title.setAlignment(Qt.AlignCenter)
        self._chart_title.setStyleSheet(f"color:{COLOR_ACCENT_BLUE}; font-size:13px; font-weight:700;")
        left_layout.addWidget(self._chart_title)

        self._chart_widget = NorthIndianChartWidget(
            chart_data=self._build_chalit_chart_data(chart_data),
            varga="D1",
            language=self._language,
            parent=self
        )
        self._chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self._chart_widget, 1)

        # Chart hint footer
        hint_lbl = QLabel(
            "सूचना: यस चक्रमा ग्रहहरू राशि भावमा नभई वास्तविक भाव चलित (Shripati Bhava) अनुसार प्रदर्शित छन्।"
            if self._is_ne else
            "Note: Planets in this chart are placed according to true Shripati Bhava Chalit house cusps."
        )
        hint_lbl.setWordWrap(True)
        hint_lbl.setAlignment(Qt.AlignCenter)
        hint_lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED}; font-size:10px; font-style:italic;")
        left_layout.addWidget(hint_lbl)

        splitter.addWidget(left_container)

        # Right Container (Analysis Panel in Scroll Area)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLOR_BG_PAGE};
            }}
        """)
        self._analysis_panel = BhavaChalitAnalysisPanel()
        self._analysis_panel.load(chart_data, language)
        scroll.setWidget(self._analysis_panel)

        splitter.addWidget(scroll)
        splitter.setSizes([460, 540])

        main_layout.addWidget(splitter, 1)

        # ── User Guide button (at the bottom; opens the shared guide dialog) ───
        # No inline guide box is rendered here, so the chart keeps the full page.
        _guide_btn = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn.setObjectName("bhavaChalitGuideBox")
        _guide_btn.setToolTip("भाव चलित निर्देशिका" if self._is_ne else "Bhava Chalit guide")
        _guide_btn.setCursor(Qt.PointingHandCursor)
        _guide_btn.setStyleSheet(
            "QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; "
            "border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } "
            "QPushButton:hover { background: #bae6fd; }"
        )

        def _open_bhava_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_bhava_chalit")

        _guide_btn.clicked.connect(_open_bhava_guide)
        main_layout.addWidget(_guide_btn)

    def _build_chalit_chart_data(self, data: Optional[dict]) -> Optional[dict]:
        """Prepare chart_data with planets mapped to their Bhava Chalit houses."""
        if not data or not isinstance(data, dict):
            return data
        
        # In Shripati Chalit mode:
        # lagna sign stays the same as birth lagna, but each planet's house is set to bhava_house
        houses_dict = data.get("houses", {})
        placements = houses_dict.get("placements", {})
        
        planets_list = data.get("planets", [])
        chalit_planets = []
        for p in planets_list:
            p_copy = dict(p)
            bhava_h = p.get("bhava_house") or placements.get(p.get("name")) or p.get("house", 1)
            p_copy["house"] = bhava_h
            chalit_planets.append(p_copy)

        chalit_data = dict(data)
        chalit_data["planets"] = chalit_planets
        return chalit_data

    def _build_bhava_lagna_chart_data(self, data: Optional[dict]) -> Optional[dict]:
        """Prepare chart_data with BPHS Bhava Lagna as the Ascendant."""
        if not data or not isinstance(data, dict):
            return data
        
        try:
            try:
                from backend.calculator.bhava_chalit import analyze_bhava_chalit
            except ImportError:
                from calculator.bhava_chalit import analyze_bhava_chalit
            res = analyze_bhava_chalit(data, self._language)
            bl = res.get("bhava_lagna", {})
            bl_sign = bl.get("bhava_lagna_sign", 1)
        except Exception:
            bl_sign = 1

        planets_list = data.get("planets", [])
        bl_planets = []
        for p in planets_list:
            p_copy = dict(p)
            p_sign = int(p.get("sign_number", 1))
            p_copy["house"] = ((p_sign - bl_sign + 12) % 12) + 1
            bl_planets.append(p_copy)

        bl_data = dict(data)
        bl_data["lagna"] = {
            **data.get("lagna", {}),
            "sign_number": bl_sign,
            "longitude_in_sign": 15.0,
        }
        bl_data["planets"] = bl_planets
        return bl_data

    def _set_chart_mode(self, mode: str):
        self._mode = mode
        if mode == "SHRIPATI":
            self._chart_title.setText("श्रीपति भाव चलित चक्र" if self._is_ne else "Shripati Bhava Chalit Chart")
            self._chart_widget.set_data(self._build_chalit_chart_data(self._chart_data), "D1")
        else:
            self._chart_title.setText("भाव लग्न चक्र (BPHS Special Lagna)" if self._is_ne else "Bhava Lagna Chart (BPHS)")
            self._chart_widget.set_data(self._build_bhava_lagna_chart_data(self._chart_data), "D1")

    def set_data(self, chart_data: Optional[dict]):
        self._chart_data = chart_data
        self._set_chart_mode(self._mode)
        self._analysis_panel.load(chart_data, self._language)
