"""
gui/widgets/jaimini_kp.py

Jaimini Analysis & KP System Widgets — v2.
Larger fonts, narrative interpretations, no unnecessary boxes.
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY)
from gui.utils.planet_colors import rashi_name

# ── Jaimini Karaka meanings ───────────────────────────────────────────────────
_KARAKA_NE = {
    "Atmakaraka":     ("आत्मकारक", "आत्मा, मुख्य जीवन उद्देश्य र स्वयं (BPHS Ch.32)।"),
    "Amatyakaraka":   ("अमात्यकारक", "मंत्री — करियर, उच्च पद, व्यावसायिक जीवन।"),
    "Bhratrukaraka":  ("भ्रातृकारक", "भाइ, सहकर्मी, साहस, साहसिक कार्य।"),
    "Matrukaraka":    ("मातृकारक", "माता, घर, भूमि, शिक्षाको आधार।"),
    "Pitrukaraka":    ("पितृकारक", "पिता, भाग्य, धर्म, गुरुको प्रभाव।"),
    "Putrakaraka":    ("पुत्रकारक", "सन्तान, बुद्धि, पूर्वजन्म पुण्य।"),
    "Jnatikaraka":    ("ज्ञातिकारक", "परिवार, रिश्तेदार, रोग, शत्रु।"),
    "Darakaraka":     ("दाराकारक", "जीवनसाथी, विवाह, दाम्पत्य जीवन।"),
}
_KARAKA_EN = {
    "Atmakaraka":     ("Atmakaraka", "Soul — primary life purpose and self (BPHS Ch.32)."),
    "Amatyakaraka":   ("Amatyakaraka", "Minister — career, authority and professional life."),
    "Bhratrukaraka":  ("Bhratrukaraka", "Siblings, colleagues, courage and bold endeavours."),
    "Matrukaraka":    ("Matrukaraka", "Mother, home, land and educational foundation."),
    "Pitrukaraka":    ("Pitrukaraka", "Father, fortune, dharma and teacher's influence."),
    "Putrakaraka":    ("Putrakaraka", "Children, intellect and past-life merit."),
    "Jnatikaraka":    ("Jnatikaraka", "Extended family, illness and competition."),
    "Darakaraka":     ("Darakaraka", "Spouse, marriage and conjugal life."),
}


def _heading(layout, text, size=18, gold=True):
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color: {COLOR_GOLD if gold else COLOR_TEXT_PRIMARY}; font-size: {size}px; "
        f"font-weight: 700; border-left: 5px solid {COLOR_GOLD}; padding: 8px 0 6px 12px;")
    layout.addWidget(lbl)


def _para(layout, text, bold=False, color=None, size=16):
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.RichText)
    lbl.setStyleSheet(
        f"color: {color or COLOR_TEXT_PRIMARY}; font-size: {size}px; "
        f"font-weight: {'700' if bold else '400'}; line-height: 1.75; padding: 2px 0;")
    layout.addWidget(lbl)


def _sep(layout, border=BORDER_COLOR):
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"border: none; border-top: 1px solid {border}; margin: 8px 0;")
    layout.addWidget(f)


def _table(layout, headers: list, rows: list, size=15):
    tbl = QTableWidget()
    tbl.setRowCount(len(rows))
    tbl.setColumnCount(len(headers))
    tbl.setHorizontalHeaderLabels(headers)
    tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tbl.horizontalHeader().setStyleSheet(
        f"QHeaderView::section {{ background: {BG_TERTIARY}; color: {COLOR_GOLD}; "
        f"font-weight: 700; font-size: {size}px; padding: 6px; }}")
    tbl.setStyleSheet(
        f"QTableWidget {{ background: {BG_SECONDARY}; color: {COLOR_TEXT_PRIMARY}; "
        f"gridline-color: {BORDER_COLOR}; font-size: {size}px; border: none; }} "
        f"QTableWidget::item {{ padding: 5px; }}")
    tbl.verticalHeader().setDefaultSectionSize(30)
    tbl.setAlternatingRowColors(True)
    tbl.verticalHeader().setVisible(False)
    for r_idx, row in enumerate(rows):
        for c_idx, cell in enumerate(row):
            tbl.setItem(r_idx, c_idx, QTableWidgetItem(str(cell)))
    tbl.setMaximumHeight(min(480, 32 * len(rows) + 38))
    layout.addWidget(tbl)
    return tbl


class JaiminiPage(QWidget):
    """Jaimini Astrology Analysis — Chara Karakas, Arudhas, Karakamsha. v2."""

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
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        title = QLabel("🔯 " + (
            "जैमिनी ज्योतिष विश्लेषण" if self._is_ne else "Jaimini Astrology Analysis"))
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

    def refresh(self, data: dict):
        self._data = data
        while self._c.count():
            item = self._c.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        jdata = data.get("jaimini", {}) if data else {}
        if not jdata:
            _para(self._c,
                "जैमिनी तथ्याङ्क उपलब्ध छैन। कुण्डली पुनः गणना गर्नुहोस्।"
                if self._is_ne else "Jaimini data unavailable. Recalculate the chart.",
                color=COLOR_TEXT_MUTED)
            return

        # ── BPHS Intro ───────────────────────────────────────────────────
        _para(self._c,
            "जैमिनी सूत्र (Jaimini Sutras) अनुसार चर-कारकहरू ग्रहको देशान्तर अनुसार "
            "निर्धारण हुन्छन् — सर्वोच्च देशान्तर वाला ग्रह आत्मकारक, अर्को अमात्यकारक, "
            "क्रमशः दाराकारकसम्म पुग्दछ। राहु-केतुलाई बाहेक राखेर ७ ग्रह लिइन्छ।"
            if self._is_ne else
            "Per Jaimini Sutras, Chara Karakas are determined by the degrees of planets "
            "within their signs — the planet with the highest degree becomes Atmakaraka, "
            "next Amatyakaraka, down to Darakaraka. Rahu-Ketu are excluded.",
            size=16)
        _sep(self._c)

        # ── 1. Chara Karakas ─────────────────────────────────────────────
        _heading(self._c, "🌟 " + (
            "चर कारकहरू (Chara Karakas)" if self._is_ne else "Chara Karakas"))

        ck = jdata.get("chara_karakas", {})
        if isinstance(ck, dict) and ck:
            rows = []
            for kname, kinfo in ck.items():
                planet  = kinfo.get("planet", kinfo) if isinstance(kinfo, dict) else str(kinfo)
                deg_fmt = kinfo.get("degree_fmt", "—") if isinstance(kinfo, dict) else "—"
                if self._is_ne:
                    k_label, k_meaning = _KARAKA_NE.get(kname, (kname, ""))
                else:
                    k_label, k_meaning = _KARAKA_EN.get(kname, (kname, ""))
                rows.append([k_label, planet, deg_fmt, k_meaning])

            _table(self._c,
                ["कारक" if self._is_ne else "Karaka",
                 "ग्रह" if self._is_ne else "Planet",
                 "देशान्तर" if self._is_ne else "Degree",
                 "अर्थ" if self._is_ne else "Signification"],
                rows)

            # Highlight AK and AmK
            ak_planet = ck.get("Atmakaraka", {})
            ak_name   = ak_planet.get("planet", "—") if isinstance(ak_planet, dict) else str(ak_planet)
            amk       = ck.get("Amatyakaraka", {})
            amk_name  = amk.get("planet", "—") if isinstance(amk, dict) else str(amk)
            _para(self._c,
                f"<b>आत्मकारक:</b> {ak_name} — जीवनको मुख्य उद्देश्य र आत्माको इच्छा।  "
                f"<b>अमात्यकारक:</b> {amk_name} — करियर र व्यावसायिक भाग्यको संकेतक।"
                if self._is_ne else
                f"<b>Atmakaraka:</b> {ak_name} — core life purpose and soul desire.  "
                f"<b>Amatyakaraka:</b> {amk_name} — career and professional destiny.",
                bold=False, color=COLOR_GOLD, size=16)
        else:
            _para(self._c, "चर कारक तथ्याङ्क उपलब्ध छैन।" if self._is_ne
                  else "Chara karaka data unavailable.", color=COLOR_TEXT_MUTED)

        _sep(self._c)

        # ── 2. Arudha Padas ──────────────────────────────────────────────
        _heading(self._c, "🌀 " + (
            "आरूढ पदहरू (Arudha Padas)" if self._is_ne else "Arudha Padas"))
        _para(self._c,
            "आरूढ पद (Arudha Lagna) — समाजमा कसरी देखिन्छ सो व्यक्तिको सार्वजनिक छवि "
            "हो। AL भाव र त्यसको कारक ग्रहले बाह्य जगतमा व्यक्तिको पहिचान निर्धारण गर्दछ।"
            if self._is_ne else
            "The Arudha (especially AL, Arudha Lagna) represents the public image — "
            "how others perceive the person in the material world.",
            size=15)

        arudhas = jdata.get("arudhas", {})
        if isinstance(arudhas, dict) and arudhas:
            rows = []
            for aname, asign in arudhas.items():
                sign_label = str(asign)
                rows.append([aname, sign_label])
            _table(self._c,
                ["पद (Pada)" if self._is_ne else "Pada",
                 "राशि (Sign)" if self._is_ne else "Sign"],
                rows)
        else:
            _para(self._c, "आरूढ तथ्याङ्क उपलब्ध छैन।" if self._is_ne
                  else "Arudha data unavailable.", color=COLOR_TEXT_MUTED)

        # ── 3. Karakamsha ────────────────────────────────────────────────
        _sep(self._c)
        km = jdata.get("karakamsha")
        if km:
            _heading(self._c, "⭐ " + (
                "काराकांश (Karakamsha)" if self._is_ne else "Karakamsha"))
            _para(self._c,
                f"काराकांश राशि: <b>{km}</b> — आत्मकारकको नवांश राशि। "
                "यसले जीवनका आध्यात्मिक, शैक्षिक र भाग्यशाली दिशा देखाउँछ।"
                if self._is_ne else
                f"Karakamsha Rashi: <b>{km}</b> — the navamsha sign of the Atmakaraka. "
                "It reveals the spiritual, educational and karmic direction of life.",
                size=16, color=COLOR_GOLD)

        self._c.addStretch()


class KPSystemPage(QWidget):
    """Krishnamurti Paddhati (KP System) Analysis — v2."""

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
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        title = QLabel("🔮 " + (
            "के.पी. पद्धति (KP System) विश्लेषण"
            if self._is_ne else "KP System Analysis"))
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

    def refresh(self, data: dict):
        self._data = data
        while self._c.count():
            item = self._c.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        kpdata = data.get("kp_system", {}) if data else {}
        if not kpdata:
            _para(self._c,
                "KP पद्धति तथ्याङ्क उपलब्ध छैन।" if self._is_ne
                else "KP System data unavailable.",
                color=COLOR_TEXT_MUTED)
            return

        # Intro
        _para(self._c,
            "KP पद्धति (Krishnamurti Paddhati) मा नक्षत्र स्वामी (Star Lord) र उप-स्वामी "
            "(Sub Lord) ले घटनाको सटीकता निर्धारण गर्दछन्। प्रत्येक भावको उप-स्वामी "
            "त्यस भावको प्रश्नको उत्तर दिन्छ।"
            if self._is_ne else
            "In KP System, the Sub Lord of each house cusp is the primary significator "
            "for predicting whether the house's themes will fructify.",
            size=16)
        _sep(self._c)

        # ── KP Cusps Table ───────────────────────────────────────────────
        _heading(self._c, "📐 " + (
            "KP भाव मध्य तथा उप-स्वामी (KP Cusps & Sub Lords)"
            if self._is_ne else "KP Cusps & Sub Lords"))

        cusps = kpdata.get("cusps", [])
        if cusps:
            rows = []
            for c in cusps:
                if not isinstance(c, dict):
                    continue
                rows.append([
                    str(c.get("house", "—")),
                    str(c.get("degree_fmt", c.get("degree", "—"))),
                    str(c.get("sign_lord", "—")),
                    str(c.get("star_lord", "—")),
                    str(c.get("sub_lord", "—")),
                ])
            _table(self._c,
                ["भाव" if self._is_ne else "House",
                 "अक्षांश" if self._is_ne else "Degree",
                 "राशि स्वामी" if self._is_ne else "Sign Lord",
                 "नक्षत्र स्वामी" if self._is_ne else "Star Lord",
                 "उप स्वामी" if self._is_ne else "Sub Lord"],
                rows)
        else:
            _para(self._c, "KP cusp तथ्याङ्क उपलब्ध छैन।" if self._is_ne
                  else "KP cusp data unavailable.", color=COLOR_TEXT_MUTED)

        # Significators
        _sep(self._c)
        sigs = kpdata.get("significators", {})
        if isinstance(sigs, dict) and sigs:
            _heading(self._c, "⚡ " + (
                "भाव संकेतक (House Significators)"
                if self._is_ne else "House Significators"))
            for house, planets in sigs.items():
                pl_str = ", ".join(planets) if isinstance(planets, list) else str(planets)
                _para(self._c,
                    f"<b>भाव {house}:</b>  {pl_str}" if self._is_ne
                    else f"<b>House {house}:</b>  {pl_str}",
                    size=16)

        self._c.addStretch()
