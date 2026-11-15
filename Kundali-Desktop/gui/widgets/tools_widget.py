"""
gui/widgets/tools_widget.py

Interactive Tools & Reports:
- MarriageMatchingPage (Gun Milan)
- PrashnaChartPage (Horary Astrology)
- MuhurtaPage (Shubh Muhurta Finder)
- JanmapatrikaPage (Printable Chart Document)
- SettingsPage (App Configuration & Preferences)
- AllInOneReportPage (Complete Kundali Summary Report)
"""
from __future__ import annotations
import sys, os
import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QComboBox, QLineEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QDoubleSpinBox, QDateEdit,
    QMessageBox, QGridLayout, QDialog
)
from PySide6.QtCore import Qt, QDate, QSettings

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, COLOR_ERROR, BG_PRIMARY)
from gui.utils.planet_colors import rashi_name


class _ToolPage(QWidget):
    """Shared state and formatting helpers for calculation-backed tool pages."""
    def _message(self, text: str, error: bool = False) -> None:
        self._state.setText(text)
        self._state.setStyleSheet(f"color: {COLOR_ERROR if error else COLOR_TEXT_MUTED}; font-size: 13px;")

    def _number(self, value, default="—"):
        return default if value is None else str(value)



class MarriageMatchingPage(QWidget):
    """विवाह मिलान — नयाँ पूर्ण-सुविधा सम्पन्न widget तर्फ forward गर्ने wrapper।"""
    def __init__(self, language: str = "ne", parent=None):
        super().__init__(parent)
        from gui.widgets.marriage_matching_widget import MarriageMatchingWidget
        inner = MarriageMatchingWidget(language, parent=self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(inner)
        # expose _state for legacy compatibility
        self._state = inner._status





from gui.widgets.prashna_kundali_widget import PrashnaChartPage


class MuhurtaPage(_ToolPage):
    """Panchang & Shubh Muhurta Finder."""
    def __init__(self, language: str = "ne", parent=None):
        super().__init__(parent); self._is_ne = language == "ne"; self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(16, 12, 16, 12)
        root.addWidget(QLabel("⏰ " + ("शुभ मुहूर्त अन्वेषण" if self._is_ne else "Shubh Muhurta Finder")))
        box = QFrame(); box.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;"); form = QVBoxLayout(box)
        row = QHBoxLayout(); row.addWidget(QLabel("Date:")); self._date = QDateEdit(QDate.currentDate()); self._date.setCalendarPopup(True); row.addWidget(self._date)
        self._find = QPushButton("⏰ " + ("मुहूर्त खोज्नुहोस्" if self._is_ne else "Find Muhurta")); self._find.clicked.connect(self.calculate); row.addWidget(self._find); form.addLayout(row)
        self._state = QLabel(); form.addWidget(self._state); self._result = QTableWidget(0, 3); self._result.setHorizontalHeaderLabels(["Period", "Start", "End"]); self._result.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); form.addWidget(self._result); root.addWidget(box, 1)

    def calculate(self):
        try:
            from gui.backend_bridge import calculate_muhurta
            selected = self._date.date().toString("yyyy-MM-dd"); self._message("गणना हुँदैछ..." if self._is_ne else "Calculating...")
            result = calculate_muhurta(selected, 27.7172, 85.3240, 5.75); rows = []
            for key in ("choghadiya_day", "choghadiya_night"):
                for item in result.get(key, []): rows.append((item.get("name", {}).get("ne" if self._is_ne else "en", key), item.get("start", "—"), item.get("end", "—")))
            for key in ("hora_day", "hora_night"):
                for item in result.get(key, []): rows.append((item.get("lord", {}).get("ne" if self._is_ne else "en", key), item.get("start", "—"), item.get("end", "—")))
            for label, item in result.get("kaals", {}).items():
                if isinstance(item, dict):
                    rows.append((label.title(), item.get("start", "—"), item.get("end", "—")))
            self._result.setRowCount(len(rows))
            for row, values in enumerate(rows):
                for col, value in enumerate(values): self._result.setItem(row, col, QTableWidgetItem(str(value)))
            self._message("परिणाम तयार भयो।" if self._is_ne else "Result ready.")
        except Exception as exc:
            self._message(str(exc), True); self._result.setRowCount(0)


class JanmapatrikaPage(QWidget):
    """जन्मपत्रिका — पूर्ण-सुविधा सम्पन्न JanmapatrikaPage (janmapatrika_widget) तर्फ forward गर्ने wrapper।"""
    def __init__(self, data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        from gui.widgets.janmapatrika_widget import JanmapatrikaPage as _RealJanmapatrika
        self._inner = _RealJanmapatrika(data, language, parent=self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._inner)

    def refresh(self, data: dict):
        if hasattr(self._inner, "refresh"):
            self._inner.refresh(data)


class AllInOneReportPage(QWidget):
    """Complete summary report of all chart calculations in one unified view."""
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        if data:
            self.refresh(data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("📑 " + ("सबै-एकै प्रतिवेदन (All-In-One Complete Report)" if self._is_ne else "All-In-One Complete Report"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 800;")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll, 1)

        container = QWidget()
        self._c_layout = QVBoxLayout(container)
        self._c_layout.setContentsMargins(0, 0, 0, 0)
        self._c_layout.setSpacing(14)
        scroll.setWidget(container)

    def refresh(self, data: dict):
        self._data = data
        while self._c_layout.count():
            item = self._c_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            empty_lbl = QLabel("कुण्डली डाटा उपलब्ध छैन। पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne else "No chart data. Please calculate a chart first.")
            empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 20px;")
            self._c_layout.addWidget(empty_lbl)
            return

        meta = data.get("metadata", {})
        planets = data.get("planets", [])
        lagna = data.get("lagna", {})
        panchang = data.get("panchang", {})
        yogas = data.get("parashara_yogas", [])
        shadbala = data.get("shadbala", {})
        ksd = data.get("kaal_sarp_dosha", {})
        dasha_list = data.get("dasha", [])

        # ── 1. जातक विवरण (Birth & Basic Info Card) ──
        c1 = QFrame()
        c1.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        l1 = QVBoxLayout(c1)
        l1.setContentsMargins(16, 14, 16, 14)
        t1 = QLabel("👤 " + ("जातक तथा पञ्चाङ्ग विवरण" if self._is_ne else "Native & Birth Panchang Details"))
        t1.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        l1.addWidget(t1)

        moon = next((p for p in planets if p.get("name") == "Moon"), {})
        rashi = moon.get("sign_name", "—")
        nak = panchang.get("nakshatra", {}).get("name", "—") if isinstance(panchang.get("nakshatra"), dict) else str(panchang.get("nakshatra") or "—")
        tithi = panchang.get("tithi", {}).get("name", "—") if isinstance(panchang.get("tithi"), dict) else str(panchang.get("tithi") or "—")

        grid = QGridLayout()
        grid.setSpacing(8)
        fields = [
            ("नाम (Name):", meta.get("name", "—")),
            ("जन्म मिति (Date):", f"{meta.get('birth_date', '—')} {meta.get('birth_time', '')}"),
            ("स्थान (Place):", f"{meta.get('city', '—')} ({meta.get('latitude', 0):.2f}°N, {meta.get('longitude', 0):.2f}°E)"),
            ("लग्न (Ascendant):", lagna.get("sign_name", "—")),
            ("चन्द्र राशि (Moon Sign):", rashi),
            ("जन्म नक्षत्र (Nakshatra):", nak),
            ("तिथि (Tithi):", tithi),
            ("अयनांश (Ayanamsha):", f"{meta.get('ayanamsha_type', 'LAHIRI')} ({meta.get('ayanamsha_value', 0):.4f}°)"),
        ]
        for idx, (lbl, val) in enumerate(fields):
            r, c = divmod(idx, 2)
            lbl_w = QLabel(f"<b>{lbl}</b>")
            lbl_w.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
            val_w = QLabel(str(val))
            val_w.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
            row_box = QHBoxLayout()
            row_box.addWidget(lbl_w)
            row_box.addWidget(val_w)
            row_box.addStretch()
            grid.addLayout(row_box, r, c)
        l1.addLayout(grid)
        self._c_layout.addWidget(c1)

        # ── 2. ग्रह स्थिति तालिका (Planetary Positions Table) ──
        c2 = QFrame()
        c2.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        l2 = QVBoxLayout(c2)
        l2.setContentsMargins(16, 14, 16, 14)
        t2 = QLabel("🪐 " + ("ग्रह स्थिति तथा भाव (Planetary Positions)" if self._is_ne else "Planetary Positions & Signs"))
        t2.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        l2.addWidget(t2)

        p_tbl = QTableWidget()
        p_tbl.setRowCount(len(planets))
        p_tbl.setColumnCount(6)
        p_tbl.setHorizontalHeaderLabels([
            "ग्रह (Planet)", "राशि (Sign)", "अंश (Degree)", "भाव (House)", "अवस्था (Motion)", "सम्बन्ध (Dignity)"
        ])
        p_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        p_tbl.setStyleSheet(f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; gridline-color: {BORDER_COLOR};")

        for r_idx, p in enumerate(planets):
            p_name = p.get("name_nepali" if self._is_ne else "name", p.get("name", ""))
            p_sign = p.get("sign_name", "—")
            p_deg = f"{p.get('longitude_in_sign', 0.0):.2f}°"
            p_house = str(p.get("house", "—"))
            motion = "वक्री (R)" if p.get("is_retrograde") else "मार्गी (D)"
            dignity = p.get("dignity", "—")
            if p.get("is_combust"):
                motion += " अस्त"

            p_tbl.setItem(r_idx, 0, QTableWidgetItem(p_name))
            p_tbl.setItem(r_idx, 1, QTableWidgetItem(p_sign))
            p_tbl.setItem(r_idx, 2, QTableWidgetItem(p_deg))
            p_tbl.setItem(r_idx, 3, QTableWidgetItem(p_house))
            p_tbl.setItem(r_idx, 4, QTableWidgetItem(motion))
            p_tbl.setItem(r_idx, 5, QTableWidgetItem(dignity))
        p_tbl.setMaximumHeight(min(320, 36 * len(planets) + 36))
        l2.addWidget(p_tbl)
        self._c_layout.addWidget(c2)

        # ── 3. सक्रिय दशा (Active Dasha Card) ──
        c3 = QFrame()
        c3.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        l3 = QVBoxLayout(c3)
        l3.setContentsMargins(16, 14, 16, 14)
        t3 = QLabel("⏳ " + ("वर्तमान सक्रिय विंशोत्तरी दशा (Active Dasha Period)" if self._is_ne else "Active Vimshottari Dasha"))
        t3.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        l3.addWidget(t3)

        active_md = next((d for d in dasha_list if d.get("is_active")), None)
        if active_md:
            md_name = active_md.get("lord_nepali" if self._is_ne else "lord", active_md.get("lord", ""))
            ad_list = active_md.get("children", [])
            active_ad = next((ad for ad in ad_list if ad.get("is_active")), None)
            ad_name = active_ad.get("lord_nepali" if self._is_ne else "lord", active_ad.get("lord", "")) if active_ad else "—"

            d_info = QLabel(
                f"• <b>सक्रिय महादशा:</b> {md_name} ({active_md.get('start_bs', active_md.get('start', ''))} देखि {active_md.get('end_bs', active_md.get('end', ''))})<br>"
                f"• <b>सक्रिय अन्तर्दशा:</b> {ad_name} " + (f"({active_ad.get('start_bs', active_ad.get('start', ''))} देखि {active_ad.get('end_bs', active_ad.get('end', ''))})" if active_ad else "")
            )
            d_info.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; line-height: 1.6;")
            l3.addWidget(d_info)
        else:
            l3.addWidget(QLabel("दशा विवरण गणना भएको छैन।"))
        self._c_layout.addWidget(c3)

        # ── 4. योग तथा दोष सारांश (Yogas & Doshas Summary) ──
        c4 = QFrame()
        c4.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        l4 = QVBoxLayout(c4)
        l4.setContentsMargins(16, 14, 16, 14)
        t4 = QLabel("⭐ " + ("मुख्य पराशरीय योग तथा विशेष स्थिति (Yogas & Doshas)" if self._is_ne else "Key Yogas & Doshas"))
        t4.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        l4.addWidget(t4)

        yoga_names = [y.get("name_nepali" if self._is_ne else "name", y.get("name", "")) for y in yogas[:8]]
        y_text = "<b>उपस्थित मुख्य योगहरू:</b> " + (", ".join(yoga_names) if yoga_names else "सामान्य")
        if ksd.get("has_dosha"):
            y_text += f"<br>⚠️ <b>कालसर्प दोष:</b> {ksd.get('dosha_type_ne' if self._is_ne else 'dosha_type', 'उपस्थित')} ({ksd.get('description', '')[:100]}...)"
        else:
            y_text += "<br>✅ <b>कालसर्प दोष:</b> कुनै कालसर्प दोष छैन।"

        y_lbl = QLabel(y_text)
        y_lbl.setWordWrap(True)
        y_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; line-height: 1.6;")
        l4.addWidget(y_lbl)
        self._c_layout.addWidget(c4)

        # ── 5. निष्कर्ष (पूर्ण फलित) — evidence-based life reading ──────────
        # Rendered from backend/calculator/life_conclusion_engine.py, which only
        # reads already-calculated payload fields. Never fabricates a date.
        self._add_life_conclusion(data)

    def _add_life_conclusion(self, data: dict) -> None:
        """Append the निष्कर्ष (पुर्ण फलित) reading to the All-In-One report."""
        card = QFrame()
        card.setStyleSheet(
            f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(12)

        title = QLabel("📖 " + (
            "निष्कर्ष (पूर्ण फलित)" if self._is_ne else "Life Conclusion (Phalita)"
        ))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        lay.addWidget(title)

        try:
            try:
                from backend.calculator.life_conclusion_engine import (
                    generate_comprehensive_life_phalita,
                )
            except ImportError:
                from calculator.life_conclusion_engine import (
                    generate_comprehensive_life_phalita,
                )
            report = generate_comprehensive_life_phalita(data, self._lang)
        except Exception as exc:
            # A reporting page must degrade gracefully, never crash the All-In-One view.
            err = QLabel(
                ("निष्कर्ष निर्माण गर्न सकिएन: " if self._is_ne else "Could not build reading: ")
                + str(exc)
            )
            err.setWordWrap(True)
            err.setStyleSheet(f"color: {COLOR_ERROR}; font-size: 12px;")
            lay.addWidget(err)
            self._c_layout.addWidget(card)
            return

        chapters = report.get("chapters") or []
        if not chapters:
            note = QLabel(report.get("message") or (
                "फलित उपलब्ध छैन।" if self._is_ne else "No reading available."
            ))
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
            lay.addWidget(note)
            self._c_layout.addWidget(card)
            return

        # Compact reading: chapter title + body, with its provenance line.
        for chapter in chapters:
            unavailable = bool(chapter.get("unavailable"))
            title_text = chapter.get("title", "")
            if unavailable:
                title_text += ("  (गणना नभएको)" if self._is_ne else "  (not calculated)")
            head = QLabel(title_text)
            head.setStyleSheet(
                f"color: {COLOR_TEXT_PRIMARY if unavailable else COLOR_GOLD};"
                f"font-size: 13px; font-weight: 700;"
            )
            head.setWordWrap(True)
            lay.addWidget(head)

            body = QLabel(chapter.get("body", chapter.get("content", "")))
            body.setWordWrap(True)
            body.setTextFormat(Qt.RichText)
            body.setStyleSheet(
                f"color: {COLOR_TEXT_MUTED if unavailable else COLOR_TEXT_PRIMARY};"
                f"font-size: 12.5px; line-height: 1.65;"
            )
            lay.addWidget(body)

            sources = chapter.get("sources") or []
            if sources:
                source_text = ", ".join(str(s) for s in sources)
                prov = QLabel(
                    f"स्रोत: {source_text}" if self._is_ne else f"Sources: {source_text}"
                )
                prov.setWordWrap(True)
                prov.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 11px;")
                lay.addWidget(prov)

        foot = QLabel(
            "<i>" + (report.get("footnote_ne") or report.get("footnote_en", "")) + "</i>"
        )
        foot.setWordWrap(True)
        foot.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11.5px;")
        lay.addWidget(foot)

        self._c_layout.addWidget(card)


class SettingsPage(QWidget):
    """App Settings & Preferences with true QSettings persistence."""
    def __init__(self, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        title = QLabel("⚙️ " + ("ज्योतिष तथा सफ्टवेयर सेटिङ (Settings)" if self._is_ne else "Application Settings & Preferences"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 800;")
        layout.addWidget(title)

        box = QFrame()
        box.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(18, 16, 18, 16)
        bl.setSpacing(14)

        s = QSettings("ShivramJyotish", "Desktop")
        saved_lang = s.value("language", self._lang)
        saved_ayan = s.value("ayanamsha", "LAHIRI")

        # Language
        l_row = QHBoxLayout()
        lbl_lang = QLabel("भाषा (Application Language):")
        lbl_lang.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
        l_row.addWidget(lbl_lang)
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("नेपाली (Nepali)", "ne")
        self._lang_combo.addItem("English", "en")
        if saved_lang == "en":
            self._lang_combo.setCurrentIndex(1)
        else:
            self._lang_combo.setCurrentIndex(0)
        l_row.addWidget(self._lang_combo)
        l_row.addStretch()
        bl.addLayout(l_row)

        # Ayanamsha
        a_row = QHBoxLayout()
        lbl_ayan = QLabel("अयनांश (Default Ayanamsha):")
        lbl_ayan.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
        a_row.addWidget(lbl_ayan)
        self._ayan_combo = QComboBox()
        ayan_options = [
            ("Lahiri / Chitrapaksha (चित्रपक्षीय लाहिरी - मानक)", "LAHIRI"),
            ("Raman (रामन अयनांश)", "RAMAN"),
            ("Krishnamurti / KP (के.पी. अयनांश)", "KP"),
            ("Yukteshwar (युक्तेश्वर)", "YUKTESHWAR"),
            ("Sayana / Tropical (सायन / पश्चिमी)", "SAYANA"),
        ]
        for label, val in ayan_options:
            self._ayan_combo.addItem(label, val)

        idx = next((i for i, (_, v) in enumerate(ayan_options) if v == saved_ayan), 0)
        self._ayan_combo.setCurrentIndex(idx)
        a_row.addWidget(self._ayan_combo)
        a_row.addStretch()
        bl.addLayout(a_row)

        # Save Button
        btn_box = QHBoxLayout()
        save_btn = QPushButton("💾 " + ("सेटिङ सुरक्षित गर्नुहोस् (Save Settings)" if self._is_ne else "Save Settings"))
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_GOLD};
                color: #000;
                font-size: 13px;
                font-weight: 700;
                padding: 8px 20px;
                border-radius: 6px;
                border: 1px solid #b45309;
            }}
            QPushButton:hover {{
                background: #f59e0b;
            }}
        """)
        save_btn.clicked.connect(self._handle_save)
        btn_box.addWidget(save_btn)
        btn_box.addStretch()
        bl.addLayout(btn_box)

        layout.addWidget(box)

        # ── Database backup (local SQLite) ──────────────────────────────────
        backup_box = QFrame()
        backup_box.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        bkl = QVBoxLayout(backup_box)
        bkl.setContentsMargins(18, 16, 18, 16)
        bkl.setSpacing(10)

        backup_title = QLabel("🗄️ " + ("डाटाबेस ब्याकअप" if self._is_ne else "Database Backup"))
        backup_title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        bkl.addWidget(backup_title)

        backup_desc = QLabel(
            "कुण्डली, खाता तथा सेटिङ सुरक्षित राख्न डाटाबेसको प्रतिलिपि बनाउनुहोस्। "
            "ब्याकअप सफ्टवेयरको डाटा फोल्डरभित्र `backups` मा रहन्छ।"
            if self._is_ne else
            "Create a copy of the database that holds charts and settings. "
            "Backups are stored in the `backups` folder inside the app data directory."
        )
        backup_desc.setWordWrap(True)
        backup_desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; line-height: 1.5;")
        bkl.addWidget(backup_desc)

        backup_row = QHBoxLayout()
        backup_row.addStretch()
        backup_btn = QPushButton(
            "💾 अहिले ब्याकअप बनाउनुहोस्" if self._is_ne else "💾 Back Up Now"
        )
        backup_btn.setStyleSheet(
            f"background: {COLOR_ACCENT}; color: #fff; font-size: 12px; "
            f"font-weight: 700; padding: 7px 16px; border-radius: 6px;"
        )
        backup_btn.clicked.connect(self._handle_backup)
        backup_row.addWidget(backup_btn)
        bkl.addLayout(backup_row)

        layout.addWidget(backup_box)

        # ── Reminder settings (system tray alerts) ──────────────────────────
        rem_box = QFrame()
        rem_box.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        rl = QVBoxLayout(rem_box)
        rl.setContentsMargins(18, 16, 18, 16)
        rl.setSpacing(10)

        rem_title = QLabel("⏰ " + ("रिमाइन्डर सेटिङ (पञ्चाङ्ग / मुहूर्त / पर्व सूचना)" if self._is_ne else "Reminder Settings (Panchang / Muhurta / Festival alerts)"))
        rem_title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        rl.addWidget(rem_title)

        rem_desc = QLabel(("सिस्टम ट्रेमा रहेर दैनिक पञ्चाङ्ग डाइजेस्ट, राहुकाल / गुलिका / यमगण्ड, "
                           "शुभ चौघडीया र एकादशी / पूर्णिमा / पर्वको सूचना दिन्छ।"
                           if self._is_ne else
                           "Stays in the system tray and alerts daily panchang digest, "
                           "Rahu Kaal / Gulika / Yamaganda, good choghadiya, and "
                           "Ekadashi / Purnima / festivals."))
        rem_desc.setWordWrap(True)
        rem_desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; line-height: 1.5;")
        rl.addWidget(rem_desc)

        rem_row = QHBoxLayout()
        rem_row.addStretch()
        rem_btn = QPushButton("⚙ " + ("रिमाइन्डर सेटिङ खोल्नुहोस्" if self._is_ne else "Open Reminder Settings"))
        rem_btn.setStyleSheet(f"background: {COLOR_ACCENT}; color: #fff; font-size: 12px; font-weight: 700; padding: 7px 16px; border-radius: 6px;")
        rem_btn.clicked.connect(self._open_reminder_settings)
        rem_row.addWidget(rem_btn)
        rl.addLayout(rem_row)

        layout.addWidget(rem_box, 1)

    def _handle_save(self):
        new_lang = self._lang_combo.currentData()
        new_ayan = self._ayan_combo.currentData()

        s = QSettings("ShivramJyotish", "Desktop")
        s.setValue("language", new_lang)
        s.setValue("ayanamsha", new_ayan)

        # Notify main window if available
        win = self.window()
        if hasattr(win, "_ayanamsha"):
            win._ayanamsha = new_ayan
        if hasattr(win, "_change_language") and new_lang != self._lang:
            win._change_language(new_lang)

        QMessageBox.information(
            self,
            "सफलता" if self._is_ne else "Saved",
            "सेटिङ सफलतापूर्वक सुरक्षित भयो।" if self._is_ne else "Settings saved successfully."
        )

    # ── Reminder settings dialog ──────────────────────────────────────────
    def _handle_backup(self):
        """Create an on-demand, consistent backup of the local database."""
        try:
            from gui.paths import backup_database
            target = backup_database(manual=True)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "ब्याकअप त्रुटि" if self._is_ne else "Backup Error",
                (
                    "डाटाबेस ब्याकअप बनाउन सकिएन:\n" if self._is_ne
                    else "Could not create the database backup:\n"
                ) + str(exc),
            )
            return
        QMessageBox.information(
            self,
            "ब्याकअप सुरक्षित भयो" if self._is_ne else "Backup Created",
            (
                f"डाटाबेसको प्रतिलिपि सुरक्षित भयो:\n{target}" if self._is_ne
                else f"Database backup created:\n{target}"
            ),
        )

    def _open_reminder_settings(self) -> None:
        """Open the system-tray reminder configuration dialog.

        Persists the values to QSettings immediately, then pushes them to the
        live ReminderService (attached to the main window by desktop_main) so
        the tray menu / digest refresh without waiting for the next tick.
        """
        try:
            from gui.reminder_service import ReminderSettingsDialog
        except Exception as exc:  # defensive — module must not break Settings page
            QMessageBox.warning(self, "Reminders",
                                f"रिमाइन्डर सेटिङ लोड गर्न सकिएन।\n{exc}" if self._is_ne
                                else f"Could not load reminder settings.\n{exc}")
            return

        dialog = ReminderSettingsDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.values()

        # 1) Persist directly (works even if the live service is not attached).
        s = QSettings("ShivramJyotish", "Desktop")
        s.setValue("reminders/enabled", bool(values["enabled"]))
        s.setValue("reminders/digest_time", str(values["digest_time"]))
        s.setValue("reminders/rahu_kaal", bool(values["rahu"]))
        s.setValue("reminders/choghadiya", bool(values["choghadiya"]))
        s.setValue("reminders/festivals", bool(values["festivals"]))
        s.setValue("reminders/upcoming_days", int(values["upcoming"]))
        s.setValue("reminders/latitude", float(values["latitude"]))
        s.setValue("reminders/longitude", float(values["longitude"]))
        s.setValue("reminders/timezone", float(values["timezone"]))

        # 2) Push to the live service so tray menu / digest update immediately.
        service = getattr(self.window(), "_reminder_service", None)
        if service is not None and hasattr(service, "update_settings"):
            service.update_settings(values)

        QMessageBox.information(
            self,
            "Reminders",
            ("रिमाइन्डर सेटिङ सुरक्षित भयो।" if self._is_ne
             else "Reminder settings saved."),
        )
