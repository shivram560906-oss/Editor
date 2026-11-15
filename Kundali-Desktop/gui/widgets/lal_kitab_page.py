# -*- coding: utf-8 -*-
"""
gui/widgets/lal_kitab_page.py

Lal Kitab (लाल किताब) Analysis Page Widget.
Redesigned v2: larger fonts, no unnecessary boxes, narrative planet readings,
35-year dasha cycle, BPHS Lal Kitab upayas from live chart data.
"""
from __future__ import annotations
import sys, os
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_SUCCESS, COLOR_ERROR)
from gui.utils.planet_colors import planet_color

_PLANET_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु",
}

# Lal Kitab House significations (permanent signs)
_HOUSE_SIG_NE = {
    1: "आत्म, स्वास्थ्य, व्यक्तित्व (मेष स्वाभाविक घर)",
    2: "धन, परिवार, वाणी (वृष स्वाभाविक घर)",
    3: "साहस, भाइ, छोटो यात्रा (मिथुन घर)",
    4: "माता, भूमि, घर (कर्कट घर)",
    5: "सन्तान, बुद्धि, प्रेम (सिंह घर)",
    6: "शत्रु, रोग, सेवा (कन्या घर)",
    7: "विवाह, साझेदारी (तुला घर)",
    8: "मृत्यु, रहस्य, ससुराली (वृश्चिक घर)",
    9: "भाग्य, धर्म, पिता (धनु घर)",
    10: "कर्म, यश, सरकार (मकर घर)",
    11: "लाभ, मित्र, आय (कुम्भ घर)",
    12: "व्यय, विदेश, मोक्ष (मीन घर)",
}

# Lal Kitab planet in house readings — concise authoritative texts
_PHAL_NE = {
    ("Sun", 1): "लग्नमा सूर्य — आत्मबल, नेतृत्व शक्ति र सरकारी पक्षमा अनुकूल। पिताको स्वास्थ्यमा सावधानी।",
    ("Sun", 4): "सूर्य चतुर्थमा — माताको सुखमा बाधा, घरेलु मामिलामा द्वन्द्व सम्भव। घरमा जलको सदुपयोग।",
    ("Sun", 7): "सूर्य सप्तममा — विवाहमा अहंकारको टकराव। साझेदारमा उग्र स्वभाव। सूर्यको उपाय महत्त्वपूर्ण।",
    ("Moon", 4): "चन्द्र चतुर्थमा — मातृ सुख, घरसुख उत्तम। भूमि-सम्पत्ति लाभ। मनोबल बलियो।",
    ("Moon", 8): "चन्द्र अष्टममा — मन अस्थिर, माताको कष्ट, पानीसँग सावधान।",
    ("Mars", 1): "मङ्गल लग्नमा — साहस, ऊर्जा प्रचुर। जमिनसँग सम्बन्ध शुभ। भाइसँग सहयोग।",
    ("Mars", 7): "सप्तममा मङ्गल — वैवाहिक जीवनमा तनाव। मङ्गल दोष विचार गर्नुहोस्।",
    ("Mercury", 1): "बुध लग्नमा — बुद्धि तीव्र, व्यापारमा सफलता। वाक्चातुर्य उत्कृष्ट।",
    ("Mercury", 7): "बुध सप्तममा — व्यापारिक साझेदारीमा चतुर। बौद्धिक जीवनसाथी।",
    ("Jupiter", 1): "गुरु लग्नमा — जीवन शुभ, ज्ञान र धनको प्राप्ति। उत्तम व्यक्तित्व।",
    ("Jupiter", 6): "गुरु षष्ठमा — शत्रुविजय, रोगजय। सेवा क्षेत्रमा उन्नति।",
    ("Jupiter", 8): "गुरु अष्टममा — धार्मिक प्रवृत्ति, विरासत लाभ सम्भव।",
    ("Venus", 1): "शुक्र लग्नमा — सौन्दर्य, कला र भौतिक सुखको प्राप्ति।",
    ("Venus", 7): "शुक्र सप्तममा — विवाह सुखद, जीवनसाथी सुन्दर र कलाप्रिय।",
    ("Saturn", 1): "शनि लग्नमा — जीवनमा कठिनाइ तर दृढ परिश्रमले सफलता।",
    ("Saturn", 7): "शनि सप्तममा — विवाह ढिलो वा कठिन। जीवनसाथी अनुशासित।",
    ("Saturn", 10): "शनि दशममा — करियरमा स्थायित्व। उच्च पद धीरे-धीरे प्राप्त।",
    ("Rahu", 4): "राहु चतुर्थमा — घरेलु अशान्ति, माताको स्वास्थ्य। भूमि विवाद सम्भव।",
    ("Rahu", 9): "राहु नवममा — भाग्य विदेशमा। धार्मिक मतभेद। अचानक परिवर्तन।",
    ("Ketu", 4): "केतु चतुर्थमा — माताको कष्ट, घरमा रहस्यमय घटना।",
    ("Ketu", 12): "केतु द्वादशमा — मोक्ष मार्गको संकेत। आध्यात्मिक उन्नति।",
}

# Lal Kitab standard upayas per planet
_UPAYAS_NE = {
    "Sun": [
        "आइतबार बिहान सूर्यलाई जलार्घ्य चढाउनुहोस् (तामाको भाँडोमा)।",
        "गहुँ, गुड, तामाको वस्तु दान गर्नुहोस्।",
        "पिताको सेवा र आदर गर्नुहोस्।",
        "ॐ घृणि सूर्याय नमः — दैनिक १०८ पटक जप।",
    ],
    "Moon": [
        "सोमबार चन्द्रमालाई दूध, चाँदी र चामलको दान गर्नुहोस्।",
        "माताको सेवा र आदर गर्नुहोस्।",
        "पानीमा बगाउने वस्तु नष्ट नगर्नुहोस्।",
        "ॐ सों सोमाय नमः — दैनिक जप।",
    ],
    "Mars": [
        "मङ्गलबार मिठाई र रातो वस्तु दान गर्नुहोस्।",
        "भाइबहिनीको सहयोग गर्नुहोस्।",
        "मासाहार घटाउनुहोस् — शाकाहार शुभ।",
        "हनुमान चालिसा नियमित पाठ गर्नुहोस्।",
    ],
    "Mercury": [
        "बुधबार हरियो वस्तु (मुंग, तोरी) दान गर्नुहोस्।",
        "बुवा वा दाजुको सल्लाह लिनुहोस्।",
        "नदी किनारमा हरियो वस्तु राख्नुहोस्।",
        "ॐ बुं बुधाय नमः — दैनिक जप।",
    ],
    "Jupiter": [
        "बिहीबार पहेँलो वस्तु, चना दाल र हल्दी दान गर्नुहोस्।",
        "गुरु वा ज्येष्ठ व्यक्तिको आदर र सेवा गर्नुहोस्।",
        "मन्दिरमा पीपलको पूजा गर्नुहोस्।",
        "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः — जप।",
    ],
    "Venus": [
        "शुक्रबार सेतो वस्तु, दही र मिठाई दान गर्नुहोस्।",
        "गाईलाई रोटी खुवाउनुहोस्।",
        "स्त्री सम्मान र सहयोग गर्नुहोस्।",
        "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः — जप।",
    ],
    "Saturn": [
        "शनिबार कालो तिल, सरसों तेल र काला वस्तु दान गर्नुहोस्।",
        "मजदुर वर्गलाई सहयोग गर्नुहोस्।",
        "पीपल वृक्षमा जल चढाउनुहोस्।",
        "ॐ शं शनैश्चराय नमः — दैनिक जप।",
    ],
    "Rahu": [
        "बुधबार साँझ कोइला, नरिवल र कालो वस्तु दान गर्नुहोस्।",
        "बाजेनानीको सेवा गर्नुहोस्।",
        "श्मशान घाटमा श्रद्धाञ्जली अर्पण गर्नुहोस्।",
        "ॐ रां राहवे नमः — जप।",
    ],
    "Ketu": [
        "मङ्गलबार सुन, नारिवल र कम्बल दान गर्नुहोस्।",
        "कुकुरलाई खाना खुवाउनुहोस्।",
        "देवतालाई फूल र धूप चढाउनुहोस्।",
        "ॐ कें केतवे नमः — जप।",
    ],
}


class LalKitabPage(QWidget):
    """Lal Kitab comprehensive analysis, readings, upayas and 35-year dasha cycles. v2."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        if data:
            self.refresh(data)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _add_heading(self, layout, text: str, size: int = 18):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: {COLOR_GOLD}; font-size: {size}px; font-weight: 700; "
            f"border-left: 5px solid {COLOR_GOLD}; padding: 8px 0 6px 12px;")
        layout.addWidget(lbl)

    def _add_para(self, layout, text: str, bold=False, color=None, size=16):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet(
            f"color: {color or COLOR_TEXT_PRIMARY}; font-size: {size}px; "
            f"font-weight: {'700' if bold else '400'}; line-height: 1.75; padding: 2px 0;")
        layout.addWidget(lbl)

    def _sep(self, layout):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet(
            f"border: none; border-top: 1px solid {BORDER_COLOR}; margin: 8px 0;")
        layout.addWidget(f)

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        title = QLabel("📕 " + (
            "लाल किताब विश्लेषण तथा अचुक उपायहरू"
            if self._is_ne else "Lal Kitab Analysis & Classical Remedies"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 22px; font-weight: 800;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll, 1)

        container = QWidget()
        self._c = QVBoxLayout(container)
        self._c.setContentsMargins(0, 4, 0, 20)
        self._c.setSpacing(6)
        scroll.setWidget(container)

    # ── data ────────────────────────────────────────────────────────────────

    def refresh(self, data: dict):
        self._data = data
        while self._c.count():
            item = self._c.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            self._add_para(self._c,
                "पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne
                else "Calculate a chart first.",
                color=COLOR_TEXT_MUTED, size=16)
            return

        lal_data = data.get("lal_kitab")
        if not lal_data:
            try:
                from calculator.lal_kitab import calculate_lal_kitab_data
                planets  = data.get("planets", [])
                lagna    = data.get("lagna", {}).get("sign_number", 1)
                birth_dt = data.get("metadata", {}).get("birth_date", "1990-01-01")
                lal_data = calculate_lal_kitab_data(planets, lagna, birth_dt)
                data["lal_kitab"] = lal_data
            except Exception as e:
                self._add_para(self._c, f"लाल किताब गणना त्रुटि: {e}", color=COLOR_ERROR)
                return

        # ── Introduction ─────────────────────────────────────────────────
        self._add_para(self._c,
            "लाल किताब अनुसार १२ भावहरू मेषदेखि मीनसम्म स्थायी घरका रूपमा लिइन्छ। "
            "ग्रहको सुतेको (सोया) वा ब्युँझिएको (जगा) अवस्था, किस्मत जगाउने ग्रह र "
            "मन्दा ग्रहका लागि सरल घरेलु कर्म-सुधार उपायहरू विशेष महत्त्व राख्दछन्।"
            if self._is_ne else
            "Lal Kitab considers houses 1-12 as permanent natural signs (Mesha-Meena). "
            "Sleeping (Soya) vs. Awake (Jaga) status, luck-activating planets and "
            "simple karmic remedies (Upayas) are its central pillars.",
            size=16)

        self._sep(self._c)

        # ── Per-planet narrative from live data ─────────────────────────
        planets = data.get("planets", [])
        rows    = lal_data.get("planet_status", []) if lal_data else []

        self._add_heading(self._c,
            "🪐 " + ("ग्रह अवस्था र फलादेश" if self._is_ne else "Planet Status & Readings"))

        # Build a quick lookup from planet name → planet data dict
        planet_map = {p.get("name"): p for p in planets}

        for r in rows:
            pname_key = r.get("name", "")
            pname_ne  = _PLANET_NE.get(pname_key, pname_key)
            pname     = pname_ne if self._is_ne else pname_key
            house     = r.get("house", "—")
            soya      = r.get("soya", "")
            nek       = r.get("nek_manda", "")
            kismat    = r.get("kismat_jagane", "")
            pdata     = planet_map.get(pname_key, {})

            # Badge row
            badge_parts = []
            if soya:
                badge_parts.append(soya)
            if nek:
                badge_parts.append(nek)
            if kismat and kismat not in ("होइन", "No", "False", "false"):
                badge_parts.append("✨ किस्मत जगाउने" if self._is_ne else "✨ Luck Activator")
            if pdata.get("is_vargottama"):
                badge_parts.append("वर्गोत्तम ✨")
            if pdata.get("is_retrograde"):
                badge_parts.append("वक्री ℞")

            badge_color = COLOR_SUCCESS if "जगा" in soya or "Awake" in soya else COLOR_ERROR
            badge_str   = "  |  ".join(badge_parts) if badge_parts else "—"

            self._add_para(self._c,
                f"<b>{pname}  ({house} {'औं भाव' if self._is_ne else 'th House'})</b>"
                f"  <span style='color:{badge_color}'>{badge_str}</span>",
                size=17)

            # Reading from dictionary
            reading = _PHAL_NE.get((pname_key, int(house) if str(house).isdigit() else 0))
            if not reading:
                reading = r.get("phal", "")
            if reading:
                self._add_para(self._c, f"• {reading}", size=15)

            # Upayas
            upayas = _UPAYAS_NE.get(pname_key, r.get("upayas", []))
            if upayas:
                upaya_html = "<b>🛡 " + ("लाल किताब उपायहरू:" if self._is_ne else "Lal Kitab Remedies:") + "</b><br>"
                upaya_html += "<br>".join(f"  ✓ {u}" for u in upayas[:4])
                self._add_para(self._c, upaya_html, color="#38bdf8", size=15)

            self._sep(self._c)

        # ── 35-Year Dasha Cycle ──────────────────────────────────────────
        dasha_cycles = lal_data.get("dasha_cycles", []) if lal_data else []
        if dasha_cycles:
            self._add_heading(self._c,
                "⏳ " + ("३५ वर्षे लाल किताब महादशा चक्र" if self._is_ne
                          else "35-Year Lal Kitab Dasha Cycle"))
            tbl = QTableWidget()
            cols = 4
            tbl.setRowCount(min(35, len(dasha_cycles)))
            tbl.setColumnCount(cols)
            tbl.setHorizontalHeaderLabels([
                "महादशा स्वामी" if self._is_ne else "Dasha Lord",
                "वर्ष" if self._is_ne else "Years",
                "सुरु" if self._is_ne else "Start",
                "समाप्ति" if self._is_ne else "End",
            ])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tbl.horizontalHeader().setStyleSheet(
                f"QHeaderView::section {{ background: {BG_TERTIARY}; "
                f"color: {COLOR_GOLD}; font-weight: 700; font-size: 15px; padding: 6px; }}")
            tbl.setStyleSheet(
                f"QTableWidget {{ background: {BG_SECONDARY}; color: {COLOR_TEXT_PRIMARY}; "
                f"gridline-color: {BORDER_COLOR}; font-size: 15px; }} "
                f"QTableWidget::item {{ padding: 5px; }}")
            tbl.verticalHeader().setDefaultSectionSize(32)
            tbl.setAlternatingRowColors(True)
            for i, c in enumerate(dasha_cycles[:35]):
                lord_ne = c.get("lord_ne", _PLANET_NE.get(c.get("lord", ""), c.get("lord", "")))
                lord    = lord_ne if self._is_ne else c.get("lord", "")
                tbl.setItem(i, 0, QTableWidgetItem(lord))
                tbl.setItem(i, 1, QTableWidgetItem(f"{c.get('years', 0)} {'वर्ष' if self._is_ne else 'yr'}"))
                tbl.setItem(i, 2, QTableWidgetItem(str(c.get("start_date", "—"))))
                tbl.setItem(i, 3, QTableWidgetItem(str(c.get("end_date", "—"))))
            tbl.setMaximumHeight(min(500, 34 * tbl.rowCount() + 40))
            self._c.addWidget(tbl)

        self._c.addStretch()
