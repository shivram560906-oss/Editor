# -*- coding: utf-8 -*-
"""
gui/widgets/ayurdaya_page.py

Ayurdaya — Classical Longevity Analysis (पाराशर आयुर्दाय विस्तृत फलादेश)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full 7-Step Classical Parashari System (बृहत्पाराशर होराशास्त्र):
  Step 1: बालारिष्ट तथा भंग योग (Balarishta & Cancellation Check)
  Step 2: विधि-निर्णय (Method Selection Rule by Lagnesha)
  Step 3: पिण्डायु विधि (Pindayu with Haranas, Bharanas, and Lagna Ayus)
  Step 4: निसर्गायु विधि (Nisargayu with classical natural planetary years)
  Step 5: अंशायु विधि (Amshayu based on Navamshas traversed)
  Step 6: आयु श्रेणी (Alpayu 0-32, Madhyayu 32-70, Purnayu 70-120)
  Step 7: विंशोत्तरी मारक दशा समन्वय तथा शान्ति उपाय (Maraka Dasha & Remedies)

Aesthetic Design:
  Clean white background (#ffffff), high-contrast black typography,
  authoritative classical borders, and structured tables without cluttered boxes.
"""
from __future__ import annotations
import sys, os, datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QDateEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.backend_bridge import calculate_ayurdaya

# ── Life stage bar ────────────────────────────────────────────────────────────
LIFE_STAGES = [
    ("बाल्य (Bala)",       0,  12, "#10b981"),
    ("कुमार (Kumara)",    12,  25, "#3b82f6"),
    ("युवा (Yuva)",      25,  50, "#f59e0b"),
    ("प्रौढ/मध्य (Madhya)",50,  70, "#ea580c"),
    ("वृद्ध (Vriddha)",   70, 100, "#8b5cf6"),
    ("दीर्घ (Dirgha)",   100, 120, "#6366f1"),
]


class _LifeTimelineBar(QWidget):
    """Visual horizontal timeline showing current age vs estimated lifespan."""

    def __init__(self, age: float, est_span: float, parent=None):
        super().__init__(parent)
        self._age = max(0.0, age)
        self._est = max(10.0, min(120.0, est_span))
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_data(self, age: float, est_span: float):
        self._age = max(0.0, age)
        self._est = max(10.0, min(120.0, est_span))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        scale = W / 120.0

        # Background track
        p.fillRect(0, 0, W, H, QColor("#ffffff"))

        # Stage rectangles
        for label_ne, start, end, color in LIFE_STAGES:
            x0 = int(start * scale)
            x1 = int(end * scale)
            w_box = max(2, x1 - x0 - 2)
            p.setBrush(QBrush(QColor(color).lighter(145)))
            p.setPen(QPen(QColor(color), 1))
            p.drawRoundedRect(x0 + 1, 14, w_box, 20, 3, 3)

            if w_box > 45:
                p.setPen(QColor("#0f172a"))
                p.setFont(QFont("Segoe UI", 8, QFont.Bold))
                p.drawText(x0 + 2, 14, w_box, 20, Qt.AlignCenter, label_ne)

        # Estimated age line (Golden Amber)
        ex = int(self._est * scale)
        p.setPen(QPen(QColor("#b45309"), 3))
        p.drawLine(ex, 4, ex, H - 4)
        p.setPen(QColor("#b45309"))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(max(0, ex - 60), 0, 120, 14, Qt.AlignCenter, f"अनुमान: {self._est}y")

        # Current age marker (Red)
        ax = int(self._age * scale)
        p.setPen(QPen(QColor("#dc2626"), 3))
        p.drawLine(ax, 6, ax, H - 2)
        p.setPen(QColor("#dc2626"))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(max(0, ax - 50), H - 14, 100, 14, Qt.AlignCenter, f"वर्तमान: {self._age}y")

        p.end()


# ── Thin Separator ────────────────────────────────────────────────────────────
def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("QFrame { border: none; border-top: 1px solid #cbd5e1; margin: 10px 0; }")
    return line


# ── Main Page ─────────────────────────────────────────────────────────────────

class AyurdayaPage(QWidget):
    """Full 7-step Classical Parashari Ayurdaya page."""

    def __init__(self, chart_data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data
        self._build_ui()
        if chart_data:
            self._compute(chart_data)

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
        title = QLabel("आयुर्दाय अध्याय — पूर्ण विस्तृत फलादेश" if self._is_ne else "Classical Ayurdaya — Longevity Analysis")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #0f172a;")
        hdr_box.addWidget(title)
        hdr_box.addStretch()

        recalc_btn = QPushButton("🔄 " + ("पुनः गणना" if self._is_ne else "Recalculate"))
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
            "बृहत्पाराशर होराशास्त्र अनुसार बालारिष्ट, विधि-निर्णय, पिण्डायु, निसर्गायु, अंशायु तथा मारक दशा समन्वय"
            if self._is_ne else
            "Complete 7-Step BPHS Method: Balarishta, Selection Rule, Pindayu, Nisargayu, Amshayu & Maraka Dasha"
        )
        sub_title.setStyleSheet("color: #475569; font-size: 13px; font-weight: 500;")
        outer.addWidget(sub_title)
        outer.addWidget(_divider())

        # ── Scroll Area for 7 steps ──
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
            "कृपया कुण्डली लोड गर्नुहोस् वा गणना गर्नुहोस्।"
            if self._is_ne else
            "Please calculate or load a horoscope chart first."
        )
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 600; padding: 50px;")
        self._lay.addWidget(self._empty_lbl)

    def refresh(self, chart_data: dict):
        self._chart_data = chart_data
        self._compute(chart_data)

    def _clear(self):
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _compute(self, chart_data: Optional[dict]):
        self._clear()
        if not chart_data:
            self._lay.addWidget(self._empty_lbl)
            return

        try:
            res = calculate_ayurdaya(chart_data, language=self._lang)
        except Exception as exc:
            err = QLabel(f"गणनामा त्रुटि: {exc}")
            err.setStyleSheet("color: #dc2626; font-size: 14px; padding: 20px;")
            self._lay.addWidget(err)
            return

        is_ne = self._is_ne
        meta = chart_data.get("metadata", {})
        dob_str = str(meta.get("birth_date") or "1990-01-01")
        try:
            dob = datetime.datetime.strptime(dob_str[:10], "%Y-%m-%d").date()
        except Exception:
            dob = datetime.date(1990, 1, 1)
        age = round((datetime.date.today() - dob).days / 365.25, 1)

        summary = res.get("summary", {})
        prim_years = summary.get("primary_years", 75.0)

        # ── Person & Age Ribbon ──
        p_row = QHBoxLayout()
        name_str = meta.get("name") or ("जातक" if is_ne else "Native")
        info_lbl = QLabel(
            f"👤 <b>{'जातक' if is_ne else 'Native'}:</b> {name_str}    |    "
            f"📅 <b>{'जन्म मिति' if is_ne else 'Birth Date'}:</b> {dob}    |    "
            f"⏳ <b>{'वर्तमान उमेर' if is_ne else 'Current Age'}:</b> {age} {'वर्ष' if is_ne else 'years'}"
        )
        info_lbl.setStyleSheet("font-size: 14px; color: #0f172a; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 14px;")
        p_row.addWidget(info_lbl)
        self._lay.addLayout(p_row)

        # ── चरण १: बालारिष्ट र भंग योग ──
        s1 = res.get("step1_balarishta", {})
        s1_title = QLabel("चरण १: बालारिष्ट तथा बालारिष्ट भंग योग परीक्षण" if is_ne else "Step 1: Balarishta & Cancellation Check")
        s1_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s1_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s1_title)

        s1_status = s1.get("status_code", "")
        bg_col = "#f0fdf4" if s1_status in ("NO_ARISHTA", "ARISHTA_CANCELLED") else "#fef2f2"
        border_col = "#22c55e" if s1_status in ("NO_ARISHTA", "ARISHTA_CANCELLED") else "#ef4444"
        text_col = "#15803d" if s1_status in ("NO_ARISHTA", "ARISHTA_CANCELLED") else "#b91c1c"

        s1_banner = QLabel(f"<b>स्थिति:</b> {s1.get('status_ne', '')}")
        s1_banner.setStyleSheet(f"background: {bg_col}; border-left: 5px solid {border_col}; color: {text_col}; font-size: 14px; font-weight: bold; padding: 10px 14px; border-radius: 4px;")
        self._lay.addWidget(s1_banner)

        reasons = s1.get("arishta_reasons", [])
        bhangas = s1.get("bhanga_reasons", [])
        if reasons or bhangas:
            r_box = QVBoxLayout()
            r_box.setSpacing(4)
            if reasons:
                r_box.addWidget(QLabel("<b>• देखिएका अरिष्ट योग:</b> " + " | ".join(reasons)))
            if bhangas:
                r_box.addWidget(QLabel("<b>• रक्षाकारी भंग योग:</b> " + " | ".join(bhangas)))
            w_r = QWidget()
            w_r.setLayout(r_box)
            w_r.setStyleSheet("font-size: 12px; color: #334155; padding-left: 10px;")
            self._lay.addWidget(w_r)

        self._lay.addWidget(_divider())

        # ── चरण २: विधि-निर्णय ──
        s2 = res.get("step2_method_selection", {})
        s2_title = QLabel("चरण २: शास्त्रीय विधि-निर्णय (Method Selection Rule)" if is_ne else "Step 2: Method Selection Rule")
        s2_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s2_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s2_title)

        s2_lbl = QLabel(
            f"<b>सिफारिस गरिएको मुख्य विधि:</b> <span style='color: #1d4ed8;'>{s2.get('method_ne','')}</span><br>"
            f"<b>शास्त्रीय आधार:</b> {s2.get('reason_ne','')}"
        )
        s2_lbl.setStyleSheet("font-size: 13px; color: #0f172a; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 14px;")
        self._lay.addWidget(s2_lbl)
        self._lay.addWidget(_divider())

        # ── चरण ३: पिण्डायु विस्तृत गणना तालिका ──
        s3 = res.get("step3_pindayu", {})
        s3_title = QLabel("चरण ३: पिण्डायु विधि — पूर्ण गणितीय शोधन (Pindayu Calculation)" if is_ne else "Step 3: Pindayu Calculation")
        s3_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s3_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s3_title)

        kruro_str = f"  -  क्रूरोदय हरण: {s3.get('krurodaya_ded', 0)} वर्ष" if s3.get('krurodaya_ded', 0) > 0 else ""
        pind_summary = QLabel(
            f"<b>पिण्डायु कुल वर्ष:</b> <span style='font-size: 16px; color: #1d4ed8;'><b>{s3.get('total_years', 0)} वर्ष</b></span> "
            f"(ग्रह आयु: {s3.get('planet_years', 0)} वर्ष  +  लग्न आयु: {s3.get('lagna_years', 0)} वर्ष{kruro_str})"
        )
        pind_summary.setStyleSheet("font-size: 13px; color: #0f172a;")
        self._lay.addWidget(pind_summary)

        # Table for Pindayu
        p_table = QTableWidget()
        p_table.setColumnCount(8)
        p_table.setHorizontalHeaderLabels([
            "ग्रह (Planet)", "राशि (Sign)", "भाव (House)", "आधारभूत (Raw)",
            "वक्री वृद्धि (Vakra)", "शत्रु हरण (Enemy)", "अस्तङ्गत (Combust)", "अन्तिम वर्ष (Net)"
        ])
        p_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        p_table.verticalHeader().setVisible(False)
        p_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #cbd5e1; background: #ffffff; gridline-color: #e2e8f0; font-size: 12px;
            }
            QHeaderView::section {
                background: #f1f5f9; color: #0f172a; font-weight: bold; border: 1px solid #cbd5e1; padding: 6px;
            }
        """)

        breakdown = s3.get("breakdown", [])
        p_table.setRowCount(len(breakdown) + 1)
        for r, row in enumerate(breakdown):
            p_table.setItem(r, 0, QTableWidgetItem(row.get("planet_ne", "")))
            p_table.setItem(r, 1, QTableWidgetItem(row.get("sign", "")))
            p_table.setItem(r, 2, QTableWidgetItem(f"{row.get('house', '')} भाव"))
            p_table.setItem(r, 3, QTableWidgetItem(f"{row.get('raw_years', 0)}y"))
            p_table.setItem(r, 4, QTableWidgetItem(f"+{row.get('vakra_added', 0)}y" if row.get("vakra_added", 0) > 0 else "—"))
            p_table.setItem(r, 5, QTableWidgetItem(f"-{row.get('shatru_ded', 0)}y" if row.get("shatru_ded", 0) > 0 else "—"))
            p_table.setItem(r, 6, QTableWidgetItem(f"-{row.get('astangata_ded', 0)}y" if row.get("astangata_ded", 0) > 0 else "—"))
            net_item = QTableWidgetItem(f"{row.get('final_years', 0)} वर्ष")
            net_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p_table.setItem(r, 7, net_item)

        # Lagna row
        last_r = len(breakdown)
        p_table.setItem(last_r, 0, QTableWidgetItem("लग्न (Lagna)"))
        p_table.setItem(last_r, 1, QTableWidgetItem("—"))
        p_table.setItem(last_r, 2, QTableWidgetItem("१ भाव"))
        p_table.setItem(last_r, 3, QTableWidgetItem(f"{s3.get('lagna_years', 0)}y"))
        p_table.setItem(last_r, 4, QTableWidgetItem("—"))
        p_table.setItem(last_r, 5, QTableWidgetItem("—"))
        p_table.setItem(last_r, 6, QTableWidgetItem("—"))
        lagna_net = QTableWidgetItem(f"{s3.get('lagna_years', 0)} वर्ष")
        lagna_net.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p_table.setItem(last_r, 7, lagna_net)

        p_table.setFixedHeight(270)
        self._lay.addWidget(p_table)
        self._lay.addWidget(_divider())

        # ── चरण ४ & ५: निसर्गायु तथा अंशायु तुलना ──
        s4 = res.get("step4_nisargayu", {})
        s5 = res.get("step5_amshayu", {})
        s45_title = QLabel("चरण ४ र ५: निसर्गायु तथा अंशायु विधि (Nisargayu & Amshayu)" if is_ne else "Steps 4 & 5: Nisargayu & Amshayu")
        s45_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s45_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s45_title)

        methods_row = QHBoxLayout()
        methods_row.setSpacing(16)

        # Nisargayu card
        nisa_box = QVBoxLayout()
        nisa_lbl = QLabel(
            f"<b>निसर्गायु विधि:</b> <span style='font-size: 16px; color: #15803d;'><b>{s4.get('total_years', 0)} वर्ष</b></span><br>"
            f"<span style='color: #475569;'>प्राकृतिक पिण्ड: सूर्य २०, चन्द्र १, मङ्गल २, बुध ९, गुरु १८, शुक्र २०, शनि ५० वर्ष</span>"
        )
        nisa_lbl.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 14px; font-size: 13px;")
        nisa_box.addWidget(nisa_lbl)
        methods_row.addLayout(nisa_box)

        # Amshayu card
        amsh_box = QVBoxLayout()
        amsh_lbl = QLabel(
            f"<b>अंशायु विधि:</b> <span style='font-size: 16px; color: #7c3aed;'><b>{s5.get('total_years', 0)} वर्ष</b></span><br>"
            f"<span style='color: #475569;'>नवांश (D9) भुक्त अंश तथा नवांश चक्र अनुपात अनुसार</span>"
        )
        amsh_lbl.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 14px; font-size: 13px;")
        amsh_box.addWidget(amsh_lbl)
        methods_row.addLayout(amsh_box)

        self._lay.addLayout(methods_row)
        self._lay.addWidget(_divider())

        # ── चरण ६: आयु श्रेणी तथा समयरेखा ──
        s6 = res.get("step6_classification", {})
        s6_title = QLabel("चरण ६: शास्त्रीय आयु श्रेणी तथा जीवन समयरेखा" if is_ne else "Step 6: Longevity Classification & Timeline")
        s6_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s6_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s6_title)

        cat_lbl = QLabel(
            f"<b>आयु श्रेणी:</b> <span style='font-size: 16px; color: #b45309;'><b>{s6.get('category_ne', '')}</b></span><br>"
            f"<b>फलादेश:</b> {s6.get('description_ne', '')}"
        )
        cat_lbl.setStyleSheet("background: #fefce8; border-left: 5px solid #eab308; border-radius: 4px; padding: 10px 14px; font-size: 13px; color: #713f12;")
        self._lay.addWidget(cat_lbl)

        # Timeline bar
        timeline = _LifeTimelineBar(age, prim_years)
        self._lay.addWidget(timeline)
        self._lay.addWidget(_divider())

        # ── चरण ७: विंशोत्तरी मारक दशा समन्वय तथा शान्ति ──
        s7 = res.get("step7_maraka_dasha", {})
        s7_title = QLabel("चरण ७: विंशोत्तरी मारक दशा समन्वय तथा शान्ति उपाय" if is_ne else "Step 7: Maraka Dasha & Remedial Measures")
        s7_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s7_title.setStyleSheet("color: #1e3a8a;")
        self._lay.addWidget(s7_title)

        m_info = s7.get("maraka_info", {})
        maraka_str = (
            f"<b>द्वितीयाधिपति (२ भाव):</b> {m_info.get('maraka_lord_2','')}    |    "
            f"<b>सप्तमाधिपति (७ भाव):</b> {m_info.get('maraka_lord_7','')}    |    "
            f"<b>अष्टमाधिपति (८ भाव):</b> {m_info.get('lord_8','')}    |    "
            f"<b>द्वादशाधिपति (१२ भाव):</b> {m_info.get('lord_12','')}"
        )
        m_lbl = QLabel(maraka_str)
        m_lbl.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 12px; font-size: 12px; color: #0f172a;")
        self._lay.addWidget(m_lbl)

        sensitive = s7.get("sensitive_dashas", [])
        if sensitive:
            d_list = [f"• {d.get('lord_ne','')}: {d.get('period','')} ({d.get('note_ne','')})" for d in sensitive]
            d_lbl = QLabel(f"<b>अनुमानित संवेदनशील समय ({s7.get('target_window_ne','')}):</b><br>" + "<br>".join(d_list))
            d_lbl.setStyleSheet("background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #0f172a;")
            self._lay.addWidget(d_lbl)

        # Remedies
        remedies = s7.get("remedies_ne", [])
        if remedies:
            rem_title = QLabel("🪔 <b>शास्त्रीय आयुर्वृद्धि तथा रक्षा उपाय:</b>")
            rem_title.setStyleSheet("font-size: 14px; color: #1e3a8a; margin-top: 6px;")
            self._lay.addWidget(rem_title)
            rem_box = QVBoxLayout()
            rem_box.setSpacing(4)
            for r in remedies:
                rem_box.addWidget(QLabel(f"✓ {r}"))
            w_rem = QWidget()
            w_rem.setLayout(rem_box)
            w_rem.setStyleSheet("font-size: 13px; color: #15803d; font-weight: 600; padding-left: 8px;")
            self._lay.addWidget(w_rem)

        self._lay.addWidget(_divider())

        # ── Classical Disclaimer ──
        disc_lbl = QLabel(f"📜 <i>{res.get('disclaimer_ne', '')}</i>")
        disc_lbl.setWordWrap(True)
        disc_lbl.setStyleSheet("color: #64748b; font-size: 12px; padding: 8px 12px; background: #f8fafc; border-radius: 4px;")
        self._lay.addWidget(disc_lbl)
