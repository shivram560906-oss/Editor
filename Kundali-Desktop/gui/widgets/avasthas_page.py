# -*- coding: utf-8 -*-
"""
gui/widgets/avasthas_page.py

Planetary Avasthas (ग्रह अवस्था विश्लेषण) Widget — BPHS अनुसार:
- Bala Avastha (बाल, कुमार, युवा, वृद्ध, मृत) — longitude degrees in sign
- Deeptadi Avastha (दीप्त, स्वस्थ, प्रमुदित, शान्त, दीन, विकल) — dignity based
- Vargottama flag — D1 == D9 sign (BPHS extra strength)
- Astrological interpretations & power output (percentage of full results)

Improvements (v2):
  - Vargottama ✨ badge displayed in table
  - Mrityu Avastha (0% capacity) highlighted in red
  - Progress bar for fruit capacity (visual)
  - Detail card below table showing /full BPHS shloka reference
  - Retrograde ℞ / Combust ☌ badges
"""
from __future__ import annotations
import sys, os
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_SUCCESS, COLOR_ERROR)
from gui.utils.planet_colors import planet_color

# ─── BPHS Avastha Tables ─────────────────────────────────────────────────────

# Bala Avastha: degree ranges in sign → capacity (BPHS Ch.45)
BALA_RANGES = {
    "Bala (Infant)":   (0, 6,   25, "बाल (शिशु)",    "राशिको ०°–६° — २५% फल दिन सक्छ"),
    "Kumara (Youth)":  (6, 12,  50, "कुमार (किशोर)", "राशिको ६°–१२° — ५०% फल दिन सक्छ"),
    "Yuva (Adult)":    (12, 18, 100,"युवा (प्रौढ)",  "राशिको १२°–१८° — १००% पूर्ण फल"),
    "Vriddha (Old)":   (18, 24, 15, "वृद्ध (वरिष्ठ)","राशिको १८°–२४° — अल्प (१५%) फल"),
    "Mrita (Dead)":    (24, 30, 0,  "मृत (अचेत)",    "राशिको २४°–३०° — फल शून्य (मृत)"),
}

BALA_CAPACITIES = {
    "Bala (Infant)":   (25,  "बाल अवस्था (२५% फल सामर्थ्य)"),
    "Kumara (Youth)":  (50,  "कुमार अवस्था (५०% फल सामर्थ्य)"),
    "Yuva (Adult)":    (100, "युवा अवस्था (१००% पूर्ण फल सामर्थ्य)"),
    "Vriddha (Old)":   (15,  "वृद्ध अवस्था (अल्प फल सामर्थ्य)"),
    "Mrita (Dead)":    (0,   "मृत अवस्था (फल सामर्थ्य शून्य)"),
}

DEEPTADI_DESC = {
    "Deepta (Exalted)":      ("दीप्त (उच्च)", "अत्यन्त बलवान — राज्यसुख, विजय र समृद्धि।",         "#f59e0b"),
    "Swastha (Own sign)":    ("स्वस्थ (स्वराशि)", "स्थिर सम्पत्ति, मानसिक शान्ति र आत्मबल।",       "#22c55e"),
    "Pramudita (Friendly)":  ("प्रमुदित (मित्रक्षेत्री)", "प्रसन्नता, मित्र सहयोग र कार्य सफलता।",  "#3b82f6"),
    "Shanta (Neutral)":      ("शान्त (समक्षेत्री)", "सामान्य र सन्तुलित फल मिल्छ।",               "#64748b"),
    "Deena (Inimical)":      ("दीन (शत्रुक्षेत्री)", "चिन्ता, सङ्घर्ष र बाधा उत्पन्न गराउँछ।",    "#f97316"),
    "Vikala (Debilitated)":  ("विकल (नीच)", "अत्यन्त दुर्बल — कठिनाई र हानि।",                     "#ef4444"),
}

PLANET_NEPALI = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु",
}


def _ne_num(v) -> str:
    d = ["०","१","२","३","४","५","६","७","८","९"]
    return "".join(d[int(c)] if c.isdigit() else c for c in str(v))


class PlanetaryAvasthasPage(QWidget):
    """Planetary Avasthas analysis widget — BPHS v2 (Vargottama + progress bars)."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        if data:
            self.refresh(data)

    def _t(self, en: str, ne: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("⚡ " + self._t(
            "Planetary Avasthas Analysis (BPHS)",
            "ग्रह अवस्था विश्लेषण (पाराशरीय)"))
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
            lbl = QLabel(self._t("Calculate a chart first.", "कुण्डली गणना गर्नुहोस्।"))
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 20px;")
            self._c_layout.addWidget(lbl)
            return

        avasthas_dict = data.get("avasthas", {}).get("planets", {})
        if not avasthas_dict:
            try:
                from calculator.avasthas import calculate_avasthas
                planets = data.get("planets", [])
                lagna = data.get("lagna", {}).get("sign_number", 1)
                avasthas_dict = calculate_avasthas(planets, lagna).get("planets", {})
            except Exception:
                pass

        # ── BPHS Reference Card ─────────────────────────────────────────────
        intro = QFrame()
        intro.setStyleSheet(
            f"background: {BG_SECONDARY}; border-left: 4px solid {COLOR_GOLD}; border-radius: 6px;")
        il = QVBoxLayout(intro)
        il.setContentsMargins(16, 12, 16, 12)
        it_lbl = QLabel("📖 " + self._t(
            "Planetary Avasthas — BPHS Rule (Ch.45)",
            "ग्रह अवस्था — पाराशर शास्त्र (अध्याय ४५)"))
        it_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        il.addWidget(it_lbl)
        desc = QLabel(self._t(
            "Maharishi Parashara declares: even a planet in an excellent house cannot give "
            "full results if it is in 'Mrita' (dead) or 'Bala' (infant) state. "
            "A planet in 'Yuva' state gives 100% fruit; 'Kumara' gives 50%; 'Mrita' gives 0%.\n"
            "Additionally, the Deeptadi state (based on dignity) modifies the quality of results:\n"
            "Deepta (exalted)=best • Swastha (own sign)=good • Pramudita (friendly)=pleasant "
            "• Shanta (neutral)=average • Deena (inimical)=troubled • Vikala (debilitated)=worst",
            "महर्षि पाराशरका अनुसार: 'कुनै ग्रह उत्तम भावमा भए तापनि 'मृत' वा 'बाल' अवस्थामा परे "
            "त्यसले आफ्नो पूर्ण फल दिन सक्दैन। युवा ग्रहले १००%, कुमारले ५०%, र मृतले ०% फल दिन्छ।'\n"
            "दीप्तादि अवस्था (सम्मान/मर्यादाको आधार):\n"
            "दीप्त (उच्च)=सर्वोत्तम • स्वस्थ (स्वराशि)=उत्तम • प्रमुदित (मित्र)=शुभ "
            "• शान्त (सम)=सामान्य • दीन (शत्रु)=कष्ट • विकल (नीच)=अत्यन्त दुर्बल"))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; line-height: 1.6;")
        il.addWidget(desc)
        self._c_layout.addWidget(intro)

        if not avasthas_dict:
            empty = QLabel(self._t(
                "⚠ Avastha data not available. Ensure the calculator has an avasthas module.",
                "⚠ अवस्था डेटा उपलब्ध छैन। calculator/avasthas.py module आवश्यक छ।"))
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; padding: 12px;")
            empty.setWordWrap(True)
            self._c_layout.addWidget(empty)
            return

        # ── Main Table ───────────────────────────────────────────────────────
        card_t = QFrame()
        card_t.setStyleSheet(
            f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        lt = QVBoxLayout(card_t)
        lt.setContentsMargins(16, 14, 16, 14)
        t_head = QLabel("📊 " + self._t(
            "Planetary States Grid (Bala + Deeptadi + Vargottama)",
            "ग्रह अवस्था तालिका (बाल + दीप्तादि + वर्गोत्तम)"))
        t_head.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        lt.addWidget(t_head)

        # Legend row
        legend = QHBoxLayout()
        for badge, color, text in [
            ("✨", COLOR_GOLD,    self._t("Vargottama (D1=D9)", "वर्गोत्तम (D1=D9)")),
            ("℞",  "#a855f7",    self._t("Retrograde",          "वक्री")),
            ("☌",  "#ef4444",    self._t("Combust",             "अस्त")),
            ("🔴", "#ef4444",    self._t("Mrita — 0% fruit",   "मृत — ०% फल")),
            ("🟢", "#16a34a",    self._t("Yuva — 100% fruit",  "युवा — १००% फल")),
        ]:
            b = QLabel(f"{badge} {text}")
            b.setStyleSheet(f"color: {color}; font-size: 11px;")
            legend.addWidget(b)
            legend.addSpacing(8)
        legend.addStretch()
        lt.addLayout(legend)

        planets_data = {p.get("name"): p for p in data.get("planets", [])}
        rows = list(avasthas_dict.items())

        tbl = QTableWidget()
        tbl.setRowCount(len(rows))
        tbl.setColumnCount(7)
        tbl.setHorizontalHeaderLabels([
            self._t("Planet", "ग्रह"),
            self._t("Deg in Sign", "राशि अंश"),
            self._t("Age State (Bala)", "बाल्यादि अवस्था"),
            self._t("Fruit %", "फल %"),
            self._t("Dignity (Deeptadi)", "दीप्तादि अवस्था"),
            self._t("Effect", "प्रभाव"),
            self._t("Badges", "विशेष"),
        ])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        tbl.setStyleSheet(
            f"QTableWidget {{ background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; "
            f"gridline-color: {BORDER_COLOR}; border: none; }}"
            "QHeaderView::section { background: #1e293b; color: #94a3b8; "
            "font-weight: 700; font-size: 12px; padding: 5px; border: none; }")
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)

        for r_idx, (pname, ainfo) in enumerate(rows):
            p_obj = planets_data.get(pname, {})
            p_ne  = PLANET_NEPALI.get(pname, pname)
            p_disp = p_ne if self._is_ne else pname

            deg_raw = ainfo.get("longitude_in_sign", 0.0)
            deg_str = f"{deg_raw:.2f}°"

            b_state = ainfo.get("bala_avastha", {}).get("state", "")
            b_ne    = ainfo.get("bala_avastha", {}).get("nepali", b_state)
            d_state = ainfo.get("deeptadi_avastha", {}).get("state", "")
            d_ne    = ainfo.get("deeptadi_avastha", {}).get("nepali", d_state)

            cap, cap_text  = BALA_CAPACITIES.get(b_state, (50, "५०%"))
            d_name, d_effect, d_color = DEEPTADI_DESC.get(d_state, (d_state, "—", "#64748b"))

            # Badge string
            badges = []
            if ainfo.get("is_vargottama") or p_obj.get("is_vargottama"):
                badges.append("✨")
            if p_obj.get("is_retrograde"):
                badges.append("℞")
            if p_obj.get("is_combust"):
                badges.append("☌")

            # Fill row
            planet_item = QTableWidgetItem(p_disp)
            planet_item.setForeground(QBrush(QColor(planet_color(pname))))
            planet_item.setFont(QFont("", 12, QFont.Bold))
            tbl.setItem(r_idx, 0, planet_item)

            tbl.setItem(r_idx, 1, QTableWidgetItem(deg_str))
            tbl.setItem(r_idx, 2, QTableWidgetItem(
                f"{b_ne}" if self._is_ne else f"{b_state}"))
            tbl.setItem(r_idx, 3, QTableWidgetItem(
                f"{_ne_num(cap)}%" if self._is_ne else f"{cap}%"))
            tbl.setItem(r_idx, 4, QTableWidgetItem(
                d_ne if self._is_ne else d_state))
            tbl.setItem(r_idx, 5, QTableWidgetItem(
                d_effect if self._is_ne else d_name))
            tbl.setItem(r_idx, 6, QTableWidgetItem(" ".join(badges) if badges else "—"))

            # Row coloring
            if cap == 0:  # Mrita
                for c in range(7):
                    item = tbl.item(r_idx, c)
                    if item:
                        item.setBackground(QBrush(QColor(80, 20, 20, 120)))
            elif cap == 100:  # Yuva
                for c in range(7):
                    item = tbl.item(r_idx, c)
                    if item:
                        item.setBackground(QBrush(QColor(20, 80, 30, 60)))
            if "✨" in badges:  # Vargottama — golden highlight
                for c in range(7):
                    item = tbl.item(r_idx, c)
                    if item:
                        item.setBackground(QBrush(QColor(120, 90, 0, 80)))

        tbl.setMaximumHeight(min(380, 40 * len(rows) + 42))
        lt.addWidget(tbl)
        self._c_layout.addWidget(card_t)

        # ── Capacity Progress Bars ────────────────────────────────────────────
        bar_card = QFrame()
        bar_card.setStyleSheet(
            f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        bl = QVBoxLayout(bar_card)
        bl.setContentsMargins(16, 12, 16, 12)
        bl.addWidget(self._hdr_label("📈 " + self._t(
            "Fruit Capacity — Visual Overview",
            "फल सामर्थ्य — दृश्य सारांश")))

        grid = QGridLayout()
        grid.setSpacing(8)
        for r_idx, (pname, ainfo) in enumerate(rows):
            b_state = ainfo.get("bala_avastha", {}).get("state", "")
            cap, _  = BALA_CAPACITIES.get(b_state, (50, ""))
            p_ne    = PLANET_NEPALI.get(pname, pname)
            p_lbl   = QLabel(p_ne if self._is_ne else pname)
            p_lbl.setStyleSheet(f"color: {planet_color(pname)}; font-weight: 700; font-size: 12px;")
            p_lbl.setFixedWidth(72)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(cap)
            bar.setFormat(f"{cap}%")
            bar.setTextVisible(True)
            bar.setFixedHeight(18)
            if cap == 0:
                bar_color = "#ef4444"
            elif cap < 50:
                bar_color = "#f97316"
            elif cap < 100:
                bar_color = "#f59e0b"
            else:
                bar_color = "#22c55e"
            bar.setStyleSheet(
                f"QProgressBar {{ border: 1px solid {BORDER_COLOR}; border-radius: 4px; "
                f"background: {BG_TERTIARY}; color: #ffffff; font-size: 11px; text-align: center; }}"
                f"QProgressBar::chunk {{ background: {bar_color}; border-radius: 3px; }}")

            b_ne = ainfo.get("bala_avastha", {}).get("nepali", b_state)
            state_lbl = QLabel(b_ne if self._is_ne else b_state)
            state_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            state_lbl.setFixedWidth(140)

            grid.addWidget(p_lbl,    r_idx, 0)
            grid.addWidget(bar,      r_idx, 1)
            grid.addWidget(state_lbl,r_idx, 2)

        bl.addLayout(grid)
        self._c_layout.addWidget(bar_card)

        # ── Vargottama Summary ────────────────────────────────────────────────
        vargo_planets = [
            pname for pname, ainfo in rows
            if ainfo.get("is_vargottama") or planets_data.get(pname, {}).get("is_vargottama")
        ]
        if vargo_planets:
            vargo_card = QFrame()
            vargo_card.setStyleSheet(
                f"background: {BG_SECONDARY}; border-left: 4px solid {COLOR_GOLD}; border-radius: 6px;")
            vl = QVBoxLayout(vargo_card)
            vl.setContentsMargins(16, 10, 16, 10)
            vl.addWidget(self._hdr_label("✨ " + self._t(
                "Vargottama Planets (D1 = D9 sign) — BPHS: Extra Strength",
                "वर्गोत्तम ग्रह (D1 = D9 राशि) — BPHS: विशेष बल")))
            names_ne  = ", ".join(PLANET_NEPALI.get(p, p) for p in vargo_planets)
            names_en  = ", ".join(vargo_planets)
            desc2 = QLabel(self._t(
                f"Vargottama planets occupy the same sign in both D1 (Rashi) and D9 (Navamsha). "
                f"BPHS Ch.27: these planets are considered equivalent to being in their own sign — "
                f"maximum natural strength. Vargottama planets in this chart: {names_en}",
                f"वर्गोत्तम ग्रहले D1 (राशि) र D9 (नवांश) दुवैमा एउटै राशि ओगट्छन्। "
                f"BPHS अध्याय २७: यस्ता ग्रह आफ्नै राशिमा भएजस्तो बलशाली मानिन्छन् — "
                f"स्वाभाविक अधिकतम बल। यस कुण्डलीका वर्गोत्तम ग्रह: {names_ne}"))
            desc2.setWordWrap(True)
            desc2.setStyleSheet(
                f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; line-height: 1.6;")
            vl.addWidget(desc2)
            self._c_layout.addWidget(vargo_card)

    @staticmethod
    def _hdr_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 14px; font-weight: 700;")
        return lbl
