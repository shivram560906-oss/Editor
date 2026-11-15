# -*- coding: utf-8 -*-
"""
gui/widgets/child_analysis.py

Child Analysis — Parashari Putra Adhyaya (पाराशर सन्तान विचार विस्तृत फलादेश)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full 8-Step Classical Parashari System (बृहत्पाराशर होराशास्त्र):
  Step 1: मुख्य ५ आधार-तत्वहरू (5 Core Factors: 5th House, 5th Lord, Jupiter, 9th House/Lord, D-7)
  Step 2: पञ्चम भावको स्थिति र ग्रह दृष्टि (Occupants & full BPHS Aspects on 5th House)
  Step 3: बृहस्पति (गुरु) को विस्तृत स्थिति र बल (House, Dignity, Combustion, Retrograde, Affliction)
  Step 4: पुत्र-अरिष्ट तथा दोष भंग योग (Putra-Arishta / Obstacles & Benefic Cancellations)
  Step 5: सप्तमांश (D-7) कुण्डली विश्लेषण (D-7 Lagna, Lagnesh, 5th House, Jupiter)
  Step 6: सन्तान संख्या शास्त्रीय अनुमान (Child Count: Sign Modality & Benefic Associations)
  Step 7: सन्तान लिंग (पुत्र/पुत्री) प्रवृत्ति (Gender Tendency: Odd/Even Signs, Planetary Genders, D-7)
  Step 8: सन्तान प्राप्ति समय (दशा तथा गोचर) र शान्ति उपाय (Vimshottari Dasha, Jupiter Transit, Remedies)

Design:
  Clean white background (#ffffff), high-contrast black typography,
  clear visual cards and tables, badges, and authentic remedies.
"""
from __future__ import annotations
import sys, os, datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.backend_bridge import calculate_child_analysis


SIGN_LORDS_MAP = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}


def build_child_analysis_model(payload: Optional[dict]) -> dict:
    if payload is None:
        return {"state": "no_chart"}
    if not isinstance(payload, dict) or not payload:
        return {"state": "empty"}
    if "error" in payload:
        return {"state": "error", "message": payload["error"]}
    lagna = payload.get("lagna")
    planets = payload.get("planets")
    if not isinstance(lagna, dict) or not isinstance(planets, list):
        return {"state": "empty"}
    lagna_sign = lagna.get("sign_number")
    if lagna_sign is None:
        lon = lagna.get("longitude")
        if lon is not None:
            lagna_sign = int(float(lon) / 30.0) % 12 + 1
        else:
            return {"state": "empty"}

    fifth_sign = (lagna_sign + 3) % 12 + 1
    fifth_lord = SIGN_LORDS_MAP[fifth_sign]

    p_dict = {p.get("name"): p for p in planets if isinstance(p, dict) and p.get("name")}
    fifth_lord_p = p_dict.get(fifth_lord, {})
    fl_house = fifth_lord_p.get("house")
    if fl_house is None and fifth_lord_p.get("longitude") is not None:
        fl_house = ((int(float(fifth_lord_p["longitude"]) / 30.0) - (lagna_sign - 1)) % 12) + 1
    fifth_lord_placement = {"house": fl_house or 1, "available": fl_house is not None}

    fifth_occupants = []
    for p in planets:
        if not isinstance(p, dict):
            continue
        h = p.get("house")
        if h is None and p.get("longitude") is not None:
            h = ((int(float(p["longitude"]) / 30.0) - (lagna_sign - 1)) % 12) + 1
        if h == 5:
            fifth_occupants.append(p.get("name", ""))

    jup = p_dict.get("Jupiter", {})
    jh = jup.get("house")
    if jh is None and jup.get("longitude") is not None:
        jh = ((int(float(jup["longitude"]) / 30.0) - (lagna_sign - 1)) % 12) + 1
    jupiter_placement = {
        "house": jh or 1,
        "retrograde": bool(jup.get("is_retrograde", False))
    }

    vargas = payload.get("vargas", {})
    d7 = vargas.get("D7") if isinstance(vargas, dict) else None
    d7_available = bool(d7 and isinstance(d7, dict) and d7.get("lagna"))
    d7_lagna_sign = None
    d7_fifth_sign = None
    d7_fifth_lord = None
    d7_fifth_lord_placement = {"available": False}
    d7_fifth_occupants = []
    d7_jupiter_placement = {}

    if d7_available:
        d7_lagna_sign = d7.get("lagna", {}).get("sign_number")
        if d7_lagna_sign is not None:
            d7_fifth_sign = (d7_lagna_sign + 3) % 12 + 1
            d7_fifth_lord = SIGN_LORDS_MAP[d7_fifth_sign]
            d7_planets = {p.get("name"): p for p in d7.get("planets", []) if isinstance(p, dict) and p.get("name")}
            d7_fl = d7_planets.get(d7_fifth_lord, {})
            d7_fl_h = d7_fl.get("house")
            d7_fifth_lord_placement = {"house": d7_fl_h, "available": d7_fl_h is not None}
            d7_fifth_occupants = [p.get("name") for p in d7.get("planets", []) if isinstance(p, dict) and p.get("house") == 5]
            d7_jup = d7_planets.get("Jupiter", {})
            d7_jupiter_placement = {"house": d7_jup.get("house")}

    dasha_list = payload.get("dasha") or payload.get("vimshottari_dasha") or []
    mahadasha_count = len([d for d in dasha_list if isinstance(d, dict)])
    antardasha_count = 0
    for d in dasha_list:
        if isinstance(d, dict):
            kids = d.get("children") or []
            antardasha_count += len([k for k in kids if isinstance(k, dict)])

    return {
        "state": "ready",
        "fifth_sign": fifth_sign,
        "fifth_lord": fifth_lord,
        "fifth_lord_placement": fifth_lord_placement,
        "fifth_occupants": fifth_occupants,
        "jupiter_placement": jupiter_placement,
        "d7_available": d7_available,
        "d7_lagna_sign": d7_lagna_sign,
        "d7_fifth_sign": d7_fifth_sign,
        "d7_fifth_lord": d7_fifth_lord,
        "d7_fifth_lord_placement": d7_fifth_lord_placement,
        "d7_fifth_occupants": d7_fifth_occupants,
        "d7_jupiter_placement": d7_jupiter_placement,
        "dasha": {
            "mahadasha_count": mahadasha_count,
            "antardasha_count": antardasha_count
        }
    }


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("QFrame { border: none; border-top: 1px solid #cbd5e1; margin: 8px 0; }")
    return line


class ChildAnalysisPage(QWidget):
    """Full 8-step Classical Parashari Child Analysis page."""

    def __init__(self, data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self.setObjectName("lifeAnalysisDocumentPage")
        self._language = language
        self._is_ne = language == "ne"
        self._chart_data = data
        self._build_ui()
        if data:
            self._compute(data)

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; color: #0f172a; }
            QScrollArea { border: none; background-color: #ffffff; }
            QLabel { background: transparent; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(12)

        # ── Header ──
        hdr_box = QHBoxLayout()
        title = QLabel(
            "सन्तान विचार (पुत्र अध्याय) — पूर्ण विस्तृत फलादेश"
            if self._is_ne else
            "Child Potential and Reading — Classical Parashari Analysis"
        )
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #0f172a;")
        hdr_box.addWidget(title)
        hdr_box.addStretch()

        recalc_btn = QPushButton("🔄 " + ("ताजा गर्नुस्" if self._is_ne else "Refresh"))
        recalc_btn.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8; color: #ffffff; border: none;
                border-radius: 6px; padding: 7px 16px; font-size: 13px; font-weight: 700;
            }
            QPushButton:hover { background-color: #1e40af; }
        """)
        recalc_btn.clicked.connect(lambda: self._compute(self._chart_data))
        hdr_box.addWidget(recalc_btn)
        outer.addLayout(hdr_box)

        sub_title = QLabel(
            "बृहत्पाराशर होराशास्त्र अनुसार पञ्चम भाव, दृष्टि, गुरुबल, पुत्र-अरिष्ट र भंग, D-7 सप्तांश, संख्या, लिंग प्रवृत्ति तथा दशा-गोचर समय"
            if self._is_ne else
            "BPHS Classical 8-Step System: 5th House, Graha Drishti, Jupiter, Arishta & Bhanga, D-7, Count, Gender & Timing"
        )
        sub_title.setStyleSheet("color: #475569; font-size: 13px; font-weight: 500;")
        outer.addWidget(sub_title)
        outer.addWidget(_divider())

        # ── Scroll Area for 8 steps ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._content = QWidget()
        self._content.setStyleSheet("background-color: #ffffff;")
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(4, 4, 4, 16)
        self._lay.setSpacing(16)
        scroll.setWidget(self._content)
        outer.addWidget(scroll, 1)

        # Placeholder
        self._empty_lbl = QLabel(
            "कृपया पहिले कुण्डली गणना वा लोड गर्नुहोस्।"
            if self._is_ne else
            "Calculate a chart to view Child Analysis."
        )
        self._empty_lbl.setObjectName("childAnalysisState")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 600; padding: 50px;")
        self._lay.addWidget(self._empty_lbl)

    def refresh(self, data: Optional[dict]):
        self._chart_data = data
        self._compute(data)

    def _clear(self):
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _compute(self, data: Optional[dict]):
        self._clear()
        if not data:
            self._lay.addWidget(self._empty_lbl)
            return

        try:
            res = calculate_child_analysis(data, language=self._language)
        except Exception as exc:
            err = QLabel(f"गणनामा त्रुटि: {exc}")
            err.setStyleSheet("color: #dc2626; font-size: 14px; padding: 20px;")
            self._lay.addWidget(err)
            return

        is_ne = self._is_ne
        meta = data.get("metadata", {})
        name_str = meta.get("name") or ("जातक" if is_ne else "Native")

        # ── Overall Banner ──
        overall = res.get("overall_verdict_ne", "")
        b_box = QLabel(f"✨ <b>{'समग्र सन्तान योग निष्कर्ष' if is_ne else 'Overall Summary'}:</b> {overall}")
        b_box.setStyleSheet("background: #eff6ff; border-left: 5px solid #2563eb; color: #1e3a8a; font-size: 14px; font-weight: bold; padding: 12px 16px; border-radius: 4px;")
        self._lay.addWidget(b_box)

        # ── चरण १: मुख्य ५ आधार-तत्वहरू ──
        s1 = res.get("step1_core_factors", {})
        fh = s1.get("fifth_house", {})
        jup_f = s1.get("jupiter", {})
        nh = s1.get("ninth_house", {})

        s1_title = QLabel("चरण १: सन्तान विचारका मुख्य ५ आधार-तत्वहरू" if is_ne else "1. Astrological Foundation of Child Yoga")
        s1_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s1_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s1_title)

        c_text = (
            f"• <b>पञ्चम भाव (सन्तान भाव):</b> {fh.get('sign_ne','')} राशि  |  <b>पञ्चमेश:</b> {fh.get('lord_ne','')} ({fh.get('lord_house','')} भाव, {fh.get('lord_sign_ne','')} राशि)<br>"
            f"• <b>सन्तानकारक बृहस्पति (गुरु):</b> {jup_f.get('house','')} भाव ({jup_f.get('sign_ne','')} राशि)  {'(वक्री)' if jup_f.get('is_retrograde') else ''}<br>"
            f"• <b>नवम भाव (भाग्य भाव):</b> {nh.get('sign_ne','')} राशि  |  <b>नवमेश:</b> {nh.get('lord_ne','')} ({nh.get('lord_house','')} भाव)<br>"
            f"• <b>सप्तांश कुण्डली (D-7):</b> {'उपलब्ध र सूक्ष्म रूपमा विश्लेषित' if s1.get('d7_available') else 'सामान्य'}"
        )
        c_lbl = QLabel(c_text)
        c_lbl.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 14px; font-size: 13px; color: #0f172a;")
        self._lay.addWidget(c_lbl)
        self._lay.addWidget(_divider())

        # ── चरण २: पञ्चम भाव र ग्रह दृष्टि ──
        s2 = res.get("step2_fifth_house_and_aspects", {})
        s2_title = QLabel("चरण २: पञ्चम भावको स्थिति र पूर्ण ग्रह दृष्टि (Graha Drishti)" if is_ne else "Step 2: 5th House Occupants & Planetary Aspects")
        s2_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s2_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s2_title)

        occ_list = s2.get("occupants", [])
        if occ_list:
            occ_str = ", ".join([f"{o.get('planet_ne','')} ({o.get('note_ne','')})" for o in occ_list])
            self._lay.addWidget(QLabel(f"<b>पञ्चम भावमा अवस्थित ग्रह:</b> {occ_str}"))
        else:
            self._lay.addWidget(QLabel("<b>पञ्चम भावमा अवस्थित ग्रह:</b> कुनै ग्रह छैन (शुद्ध भाव)"))

        # Aspects table
        aspects = s2.get("aspects", [])
        if aspects:
            asp_table = QTableWidget()
            asp_table.setColumnCount(4)
            asp_table.setHorizontalHeaderLabels([
                "दृष्टि दिने ग्रह (Planet)", "दृष्टिको स्थान (From House)", "दृष्टि प्रकार (Aspect Type)", "प्रभाव (Astrological Effect)"
            ])
            asp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            asp_table.verticalHeader().setVisible(False)
            asp_table.setStyleSheet("""
                QTableWidget { border: 1px solid #cbd5e1; background: #ffffff; gridline-color: #e2e8f0; font-size: 12px; }
                QHeaderView::section { background: #f1f5f9; color: #0f172a; font-weight: bold; border: 1px solid #cbd5e1; padding: 6px; }
            """)
            asp_table.setRowCount(len(aspects))
            for r, asp in enumerate(aspects):
                asp_table.setItem(r, 0, QTableWidgetItem(asp.get("planet_ne", "")))
                asp_table.setItem(r, 1, QTableWidgetItem(f"{asp.get('from_house','')} भाव"))
                asp_table.setItem(r, 2, QTableWidgetItem(asp.get("aspect_type", "")))
                eff_item = QTableWidgetItem(asp.get("effect_ne", ""))
                if asp.get("planet") == "Jupiter":
                    eff_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
                asp_table.setItem(r, 3, eff_item)
            asp_table.setFixedHeight(min(180, 45 + len(aspects) * 35))
            self._lay.addWidget(asp_table)
        else:
            self._lay.addWidget(QLabel("<i>पञ्चम भावमा कुनै प्रत्यक्ष विशेष दृष्टि परेको छैन।</i>"))

        self._lay.addWidget(_divider())

        # ── चरण ३: सन्तानकारक गुरुको विश्लेषण ──
        s3 = res.get("step3_jupiter_karaka", {})
        s3_title = QLabel("चरण ३: सन्तानकारक बृहस्पति (गुरु) को विस्तृत स्थिति" if is_ne else "Step 3: Jupiter (Putra-Karaka) Evaluation")
        s3_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s3_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s3_title)

        retro_note = s3.get('retrograde_note_ne', '')
        combust_note = s3.get('combust_note_ne', '')
        retro_str = f"<br><span style='color: #b45309;'>• {retro_note}</span>" if retro_note else ""
        combust_str = f"<br><span style='color: #dc2626;'>• {combust_note}</span>" if combust_note else ""

        j_card = QLabel(
            f"<b>गुरुको भाव र राशि:</b> {s3.get('house','')} भाव ({s3.get('sign_ne','')} राशि)<br>"
            f"<b>राशिबल / मर्यादा:</b> <span style='color: #1d4ed8;'><b>{s3.get('dignity_ne','')}</b></span><br>"
            f"<b>समग्र कारक बल:</b> <span style='font-size: 14px; color: #15803d;'><b>{s3.get('strength_ne','')}</b></span>"
            f"{retro_str}{combust_str}"
        )
        j_card.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 14px; font-size: 13px;")
        self._lay.addWidget(j_card)
        self._lay.addWidget(_divider())

        # ── चरण ४: पुत्र-अरिष्ट तथा दोष भंग योग ──
        s4 = res.get("step4_arishta_and_bhanga", {})
        s4_title = QLabel("चरण ४: पुत्र-अरिष्ट योग तथा दोष भंग योग" if is_ne else "Step 4: Putra-Arishta & Cancellation (Bhanga) Yogas")
        s4_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s4_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s4_title)

        s4_code = s4.get("code", "")
        bg_col = "#f0fdf4" if s4_code in ("NO_OBSTACLE", "OBSTACLE_CANCELLED") else "#fef2f2"
        border_col = "#22c55e" if s4_code in ("NO_OBSTACLE", "OBSTACLE_CANCELLED") else "#ef4444"
        text_col = "#15803d" if s4_code in ("NO_OBSTACLE", "OBSTACLE_CANCELLED") else "#b91c1c"

        s4_banner = QLabel(f"<b>स्थिति:</b> {s4.get('status_ne', '')}")
        s4_banner.setStyleSheet(f"background: {bg_col}; border-left: 5px solid {border_col}; color: {text_col}; font-size: 14px; font-weight: bold; padding: 10px 14px; border-radius: 4px;")
        self._lay.addWidget(s4_banner)

        obs = s4.get("obstacles", [])
        bhn = s4.get("bhangas", [])
        if obs or bhn:
            ar_box = QVBoxLayout()
            ar_box.setSpacing(4)
            if obs:
                ar_box.addWidget(QLabel("<b>• देखिएका बाधा कारकहरू:</b> " + " | ".join(obs)))
            if bhn:
                ar_box.addWidget(QLabel("<b>• रक्षाकारी भंग योगहरू:</b> " + " | ".join(bhn)))
            w_ar = QWidget()
            w_ar.setLayout(ar_box)
            w_ar.setStyleSheet("font-size: 12px; color: #334155; padding-left: 10px;")
            self._lay.addWidget(w_ar)

        self._lay.addWidget(_divider())

        # ── चरण ५: सप्तमांश (D-7) कुण्डली ──
        s5 = res.get("step5_d7_saptamsha", {})
        s5_title = QLabel("चरण ५: सप्तमांश (D-7 Saptamsha) कुण्डली विश्लेषण" if is_ne else "Step 5: D-7 Saptamsha Kundali Analysis")
        s5_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s5_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s5_title)

        if s5.get("available"):
            d7_occ_str = ", ".join(s5.get("d7_fifth_occupants", [])) or "कुनै छैन"
            d7_text = (
                f"• <b>सप्तमांश लग्न:</b> {s5.get('d7_lagna_sign_ne','')}  |  <b>सप्तमांश लग्नेश:</b> {s5.get('d7_lagnesh_ne','')}<br>"
                f"• <b>सप्तमांश पञ्चम भाव:</b> {s5.get('d7_fifth_sign_ne','')}  |  <b>पञ्चमेश:</b> {s5.get('d7_fifth_lord_ne','')} ({s5.get('d7_fifth_lord_house','')} भावमा)<br>"
                f"• <b>सप्तमांश पञ्चम भावका ग्रह:</b> {d7_occ_str}  |  <b>सप्तमांशमा गुरु:</b> {s5.get('d7_jupiter_house','')} भावमा<br>"
                f"• <b>D-7 सूक्ष्म निष्कर्ष:</b> <span style='color: #15803d; font-weight: bold;'>{s5.get('strength_ne','')}</span>"
            )
            d7_card = QLabel(d7_text)
            d7_card.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 14px; font-size: 13px; color: #0f172a;")
            self._lay.addWidget(d7_card)
        else:
            self._lay.addWidget(QLabel("<i>D-7 सप्तमांश कुण्डली गणना उपलब्ध हुन सकेन।</i>"))

        self._lay.addWidget(_divider())

        # ── चरण ६ & ७: सन्तान संख्या र लिंग प्रवृत्ति ──
        s6 = res.get("step6_child_count", {})
        s7 = res.get("step7_gender_tendency", {})

        s67_title = QLabel("चरण ६ र ७: सन्तान संख्या तथा लिंग (पुत्र/पुत्री) प्रवृत्ति" if is_ne else "Steps 6 & 7: Child Count & Gender Tendency")
        s67_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s67_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s67_title)

        c67_row = QHBoxLayout()
        c67_row.setSpacing(16)

        # Count card
        count_box = QVBoxLayout()
        c_card = QLabel(
            f"<b>अनुमानित सन्तान संख्या:</b> <span style='font-size: 16px; color: #15803d;'><b>{s6.get('estimated_range_ne','')}</b></span><br>"
            f"<span style='color: #475569;'>गुरुको राशि स्वभाव: {s6.get('modality_ne','')} ({s6.get('jupiter_sign_ne','')})</span><br>"
            f"<span style='color: #334155;'>{s6.get('description_ne','')}</span>"
        )
        c_card.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 14px; font-size: 13px;")
        count_box.addWidget(c_card)
        c67_row.addLayout(count_box)

        # Gender card
        gender_box = QVBoxLayout()
        g_card = QLabel(
            f"<b>सन्तान लिंग प्रवृत्ति:</b> <span style='font-size: 15px; color: #7c3aed;'><b>{s7.get('tendency_ne','')}</b></span><br>"
            f"<span style='color: #475569;'>पञ्चम राशि: {s7.get('fifth_sign_gender_ne','')} | पञ्चमेश: {s7.get('fifth_lord_gender_ne','')}</span><br>"
            f"<span style='font-size: 11px; color: #64748b;'><i>{s7.get('disclaimer_ne','')}</i></span>"
        )
        g_card.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 14px; font-size: 13px;")
        gender_box.addWidget(g_card)
        c67_row.addLayout(gender_box)

        self._lay.addLayout(c67_row)
        self._lay.addWidget(_divider())

        # ── चरण ८: सन्तान प्राप्ति समय र उपाय ──
        s8 = res.get("step8_timing_and_remedies", {})
        s8_title = QLabel("चरण ८: सन्तान प्राप्तिको समय (दशा तथा गोचर) र शान्ति उपाय" if is_ne else "4. Child Life Timeline by Dasha")
        s8_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s8_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s8_title)

        # Transit note
        tr_lbl = QLabel(f"🌐 <b>गोचर सक्रियता:</b> {s8.get('key_transit_trigger_ne','')}")
        tr_lbl.setStyleSheet("background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; font-size: 13px; color: #14532d; border-radius: 4px;")
        self._lay.addWidget(tr_lbl)

        # Favorable Dashas
        fav_d = s8.get("favorable_dashas", [])
        if fav_d:
            d_strs = [f"• <b>{d.get('lord_ne','')}</b> ({d.get('role_ne','')}): {d.get('period','')} {'[सक्रिय]' if d.get('is_active') else ''}" for d in fav_d]
            d_lbl = QLabel("<b>अनुकूल विंशोत्तरी दशा सन्दर्भ:</b><br>" + "<br>".join(d_strs))
            d_lbl.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #0f172a;")
            self._lay.addWidget(d_lbl)

        # Remedies
        remedies = s8.get("remedies", [])
        if remedies:
            r_title = QLabel("🪔 <b>शास्त्रीय सन्तान प्राप्ति तथा रक्षा उपाय:</b>" if is_ne else "6. Remedies & Guidance")
            r_title.setStyleSheet("font-size: 14px; color: #1e3a8a; margin-top: 6px;")
            self._lay.addWidget(r_title)
            r_box = QVBoxLayout()
            r_box.setSpacing(4)
            for r in remedies:
                r_box.addWidget(QLabel(f"✓ {r}"))
            w_rem = QWidget()
            w_rem.setLayout(r_box)
            w_rem.setStyleSheet("font-size: 13px; color: #15803d; font-weight: 600; padding-left: 8px;")
            self._lay.addWidget(w_rem)

        self._lay.addWidget(_divider())

        # Classical Disclaimer
        disc = QLabel(
            "📜 <i>शास्त्रीय उद्घोष: बृहत्पाराशर होराशास्त्र अनुसार सन्तान विचार पूर्वजन्मको प्रारब्ध र कर्मफलको ज्योतिषीय विवेचना हो। यसको उद्देश्य सन्तान गोपाल जप, गुरु/सूर्य शान्ति तथा पारिवारिक कल्याणका लागि मार्गदर्शन गर्नु हो।</i>"
        )
        disc.setWordWrap(True)
        disc.setStyleSheet("color: #64748b; font-size: 12px; padding: 8px 12px; background: #f8fafc; border-radius: 4px;")
        self._lay.addWidget(disc)
