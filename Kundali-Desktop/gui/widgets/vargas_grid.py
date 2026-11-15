"""
gui/widgets/vargas_grid.py

Displays:
1. VargasGridPage: Selector / Grid view for all 16 Divisional Charts (D1..D60).
2. SudarshanChakraPage: Side-by-side Rashi (Lagna), Moon, and Sun/Navamsha charts.
"""
from __future__ import annotations
import sys, os, math
from typing import Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QComboBox, QSplitter, QProgressBar,
    QSizePolicy, QGroupBox, QPushButton
)
from PySide6.QtCore import (
    Qt, QPointF, QRectF, QThread, Signal, QObject,
    QTimer, QPropertyAnimation, QEasingCurve, Property
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QRadialGradient

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY)
from gui.widgets.north_indian_chart import NorthIndianChartWidget, CHART_BG, CHART_LINE
from gui.utils.planet_colors import PLANET_ABBR, RASHI_NAMES

VARGA_NAMES = {
    "D1":  {"ne": "D1 - राशि कुण्डली (शरीर, क्षेत्र)", "en": "D1 - Rashi (General, Body)"},
    "D2":  {"ne": "D2 - होरा (धन, समृद्धि)", "en": "D2 - Hora (Wealth)"},
    "D3":  {"ne": "D3 - द्रेष्काण (दाजुभाइ, पराक्रम)", "en": "D3 - Drekkana (Siblings, Courage)"},
    "D4":  {"ne": "D4 - चतुर्थांश (भाग्य, अचल सम्पत्ति)", "en": "D4 - Chaturthamsha (Property, Assets)"},
    "D7":  {"ne": "D7 - सप्तमांंश (सन्तान, वंश)", "en": "D7 - Saptamsha (Children, Progeny)"},
    "D9":  {"ne": "D9 - नवांश (भाग्य, जीवनसाथी)", "en": "D9 - Navamsha (Spouse, Dharma)"},
    "D10": {"ne": "D10 - दशमांश (कर्म, करियर)", "en": "D10 - Dashamsha (Career, Profession)"},
    "D12": {"ne": "D12 - द्वादशांश (मातापिता, वंश)", "en": "D12 - Dwadamsha (Parents)"},
    "D16": {"ne": "D16 - षोडशांश (वाहन, सुख)", "en": "D16 - Shodashamsha (Vehicles, Comforts)"},
    "D20": {"ne": "D20 - विंशति-अंश (आध्यात्मिक)", "en": "D20 - Vimsamsha (Spiritual Progress)"},
    "D24": {"ne": "D24 - चतुर्विंशति (विद्या, ज्ञान)", "en": "D24 - Chaturvimsamsha (Education, Knowledge)"},
    "D27": {"ne": "D27 - सप्तविंशति (बल, सामर्थ्य)", "en": "D27 - Saptavimsamsha (Strengths)"},
    "D30": {"ne": "D30 - त्रिंशांश (अनिष्ट, संकट)", "en": "D30 - Trimsamsha (Evils, Misfortunes)"},
    "D40": {"ne": "D40 - खवेदांश (शुभ/अशुभ फल)", "en": "D40 - Khavedamsha (Auspicious Effects)"},
    "D45": {"ne": "D45 - अक्षवेदांश (चरित्र, आचरण)", "en": "D45 - Akshavedamsha (Character)"},
    "D60": {"ne": "D60 - षष्टि-अंश (पूर्वजन्म कर्म)", "en": "D60 - Shashtiamsha (Past Karma)"},
}

# ─── Inline style helpers (Light/White theme) ───────────────────────────────
_CARD  = f"background:#ffffff;border:1px solid #c7d8f5;border-radius:6px;padding:8px;"
_TITLE = f"color:#1e40af;font-size:13px;font-weight:700;"
_BODY  = f"color:{COLOR_TEXT_SECONDARY};font-size:12px;line-height:1.5;"
_GOOD  = "color:#15803d;font-size:12px;font-weight:600;"
_BAD   = "color:#b91c1c;font-size:12px;font-weight:600;"
_MUTED = f"color:{COLOR_TEXT_MUTED};font-size:11px;"


def _section_box(title: str, content_widget: QWidget) -> QGroupBox:
    box = QGroupBox(title)
    box.setStyleSheet(
        f"QGroupBox{{color:#1e40af;font-size:12px;font-weight:700;"
        f"background:#ffffff;border:1px solid #c7d8f5;border-radius:5px;margin-top:8px;padding-top:6px;}}"
        f"QGroupBox::title{{subcontrol-origin:margin;left:8px;padding:0 4px;background:#ffffff;}}"
    )
    lay = QVBoxLayout(box)
    lay.setContentsMargins(8, 4, 8, 6)
    lay.setSpacing(3)
    lay.addWidget(content_widget)
    return box


def _bullet_label(text: str, color: str = COLOR_TEXT_SECONDARY) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"color:{color};font-size:12px;")
    return lbl


# ─── Analysis Worker Thread ──────────────────────────────────────────────────
class _AnalysisWorker(QObject):
    finished = Signal(dict)
    error    = Signal(str)

    def __init__(self, chart_data: dict, varga_key: str):
        super().__init__()
        self._data = chart_data
        self._key  = varga_key

    def run(self):
        try:
            try:
                from backend.calculator.varga_analysis import analyze_varga
            except ImportError:
                from calculator.varga_analysis import analyze_varga
            result = analyze_varga(self._data, self._key)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ─── Analysis Panel Widget ───────────────────────────────────────────────────
class VargaAnalysisPanel(QScrollArea):
    """Right-side panel showing full BPHS varga analysis."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._container.setStyleSheet("background:#ffffff;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        self.setWidget(self._container)
        self._show_loading()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_loading(self):
        self._clear()
        lbl = QLabel("⌛ विश्लेषण गर्दैछु…")
        lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:13px;background:transparent;")
        lbl.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(lbl)
        self._layout.addStretch()

    def load(self, chart_data: dict, varga_key: str):
        if not chart_data:
            self._show_no_data()
            return
        # analyze_varga() is a fast, pure, synchronous BPHS computation with no
        # I/O, so it is run inline rather than on a worker QThread. A QThread
        # that is still running when its page is garbage-collected, or when the
        # Qt application tears down, aborts the whole process natively
        # (0xC0000409) with "QThread: Destroyed while thread is still running".
        self._show_loading()
        try:
            try:
                from backend.calculator.varga_analysis import analyze_varga
            except ImportError:
                from calculator.varga_analysis import analyze_varga
            result = analyze_varga(chart_data, varga_key)
        except Exception as e:
            self._on_error(str(e))
            return
        self._on_done(result)

    def _show_no_data(self):
        self._clear()
        lbl = QLabel("कुण्डली डेटा उपलब्ध छैन।\nपहिले जन्म विवरण भर्नुस्।")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:13px;")
        lbl.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(lbl)
        self._layout.addStretch()

    def _on_error(self, msg: str):
        self._clear()
        lbl = QLabel(f"⚠ विश्लेषण गर्न सकिएन:\n{msg}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#b91c1c;font-size:12px;background:transparent;")
        self._layout.addWidget(lbl)
        self._layout.addStretch()

    def _on_done(self, result: dict):
        self._clear()
        self._render(result)

    def _render(self, r: dict):
        lay = self._layout

        # ── 1. Conclusion box (top, highlighted) — Light theme ──────────────
        conc_frame = QFrame()
        verdict_color = {
            "अत्यन्त शुभ": "#15803d",
            "मध्यम शुभ":   "#166534",
            "मिश्रित":     "#92400e",
            "कठिन":        "#b91c1c",
        }.get(r.get("verdict", ""), "#1e40af")
        verdict_bg = {
            "अत्यन्त शुभ": "#f0fdf4",
            "मध्यम शुभ":   "#dcfce7",
            "मिश्रित":     "#fefce8",
            "कठिन":        "#fff1f2",
        }.get(r.get("verdict", ""), "#eff6ff")
        verdict_border = {
            "अत्यन्त शुभ": "#86efac",
            "मध्यम शुभ":   "#4ade80",
            "मिश्रित":     "#fde047",
            "कठिन":        "#fca5a5",
        }.get(r.get("verdict", ""), "#93c5fd")
        conc_frame.setStyleSheet(
            f"background:{verdict_bg};border:2px solid {verdict_border};"
            f"border-radius:8px;padding:10px;"
        )
        conc_lay = QVBoxLayout(conc_frame)
        conc_lay.setContentsMargins(10, 8, 10, 8)
        conc_lay.setSpacing(4)
        verdict_lbl = QLabel(f"📌 निष्कर्ष: {r.get('verdict','')}")
        verdict_lbl.setStyleSheet(f"color:{verdict_color};font-size:13px;font-weight:700;background:transparent;")
        conc_lay.addWidget(verdict_lbl)
        conclusion_lbl = QLabel(r.get("conclusion", ""))
        conclusion_lbl.setWordWrap(True)
        conclusion_lbl.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:12px;background:transparent;")
        conc_lay.addWidget(conclusion_lbl)
        subject_lbl = QLabel(f"📚 विषय: {r.get('subject','')}")
        subject_lbl.setWordWrap(True)
        subject_lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:11px;background:transparent;")
        conc_lay.addWidget(subject_lbl)
        lay.addWidget(conc_frame)

        # ── 2. Shubha / Ashubha meter ────────────────────────────────────────
        meter_frame = QFrame()
        meter_frame.setStyleSheet("background:#ffffff;border:1px solid #c7d8f5;border-radius:6px;padding:8px;")
        meter_lay = QVBoxLayout(meter_frame)
        meter_lay.setContentsMargins(6, 6, 6, 6)
        meter_lay.setSpacing(4)
        sp = r.get("shubha_percent", 50)
        ap = r.get("ashubha_percent", 50)
        header_row = QHBoxLayout()
        hlbl = QLabel("⚖ शुभ/अशुभ अनुपात")
        hlbl.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:12px;font-weight:600;background:transparent;")
        header_row.addWidget(hlbl)
        header_row.addStretch()
        pct_lbl = QLabel(f"✅ {sp}%  शुभ   |   ❌ {ap}%  अशुभ")
        pct_lbl.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:12px;font-weight:700;background:transparent;")
        header_row.addWidget(pct_lbl)
        meter_lay.addLayout(header_row)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(sp)
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        bar.setStyleSheet(
            "QProgressBar{background:#fca5a5;border-radius:5px;border:none;}"
            "QProgressBar::chunk{background:#4ade80;border-radius:5px;}"
        )
        meter_lay.addWidget(bar)
        lay.addWidget(meter_frame)

        # ── 3. Lagna Info ────────────────────────────────────────────────────
        lagna_row = QHBoxLayout()
        lagna_row.setSpacing(8)
        for label, value in [
            ("लग्न राशि", r.get("lagna_sign_name", "")),
            ("लग्नेश",    r.get("lagna_lord_ne", "")),
        ]:
            f = QFrame()
            f.setStyleSheet("background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:6px;")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(6, 4, 6, 4)
            fl.setSpacing(1)
            ll = QLabel(label)
            ll.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:11px;background:transparent;")
            fl.addWidget(ll)
            vl = QLabel(value)
            vl.setStyleSheet("color:#1e40af;font-size:14px;font-weight:700;background:transparent;")
            fl.addWidget(vl)
            lagna_row.addWidget(f)
        lay.addLayout(lagna_row)

        # ── 4. Planet Analysis table ─────────────────────────────────────────
        planet_w = QWidget()
        planet_lay = QVBoxLayout(planet_w)
        planet_lay.setContentsMargins(0, 0, 0, 0)
        planet_lay.setSpacing(3)
        for pa in r.get("planet_analysis", []):
            row = QFrame()
            strength = pa.get("strength", "neutral")
            # Vargottama gets golden background override
            is_vargo = pa.get("is_vargottama", False)
            bg_color = "#fffbeb" if is_vargo else {
                "exalted":    "#f0fdf4",
                "own":        "#eff6ff",
                "debilitated":"#fff1f2",
                "neutral":    "#f8fafc",
            }.get(strength, "#f8fafc")
            border_color = "#f59e0b" if is_vargo else {
                "exalted":    "#86efac",
                "own":        "#93c5fd",
                "debilitated":"#fca5a5",
                "neutral":    "#e2e8f0",
            }.get(strength, "#e2e8f0")
            row.setStyleSheet(
                f"background:{bg_color};border:1px solid {border_color};"
                f"border-radius:4px;padding:4px 8px;"
            )
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(4, 2, 4, 2)
            row_lay.setSpacing(8)

            # Planet name + badges
            badges = ""
            if is_vargo:                       badges += " ✨"
            if pa.get("is_retrograde"):        badges += " ℞"
            if pa.get("is_combust"):           badges += " ☌"

            name_lbl = QLabel(pa.get("name_ne", "") + badges)
            name_lbl.setStyleSheet(f"color:{'#92400e' if is_vargo else COLOR_TEXT_PRIMARY};font-size:12px;font-weight:700;background:transparent;")
            name_lbl.setFixedWidth(72)
            row_lay.addWidget(name_lbl)
            sign_lbl = QLabel(f"-> {pa.get('sign_name','')}")
            sign_lbl.setStyleSheet(f"color:{COLOR_TEXT_SECONDARY};font-size:12px;background:transparent;")
            sign_lbl.setFixedWidth(64)
            row_lay.addWidget(sign_lbl)
            house_lbl = QLabel(pa.get("house_name", ""))
            house_lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:11px;background:transparent;")
            house_lbl.setFixedWidth(100)
            row_lay.addWidget(house_lbl)
            str_color = {
                "exalted":    "#15803d",
                "own":        "#1d4ed8",
                "debilitated":"#b91c1c",
                "neutral":    COLOR_TEXT_MUTED
            }.get(strength, COLOR_TEXT_MUTED)
            str_lbl = QLabel(pa.get("strength_ne", ""))
            str_lbl.setStyleSheet(f"color:{str_color};font-size:11px;font-weight:600;background:transparent;")
            row_lay.addWidget(str_lbl)
            row_lay.addStretch()
            htype_lbl = QLabel(pa.get("house_type",""))
            htype_lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:10px;background:transparent;")
            row_lay.addWidget(htype_lbl)
            # Vargottama tooltip
            if is_vargo:
                row.setToolTip("Vargottama: D1 = D9 rashI — BPHS maximum natural strength")
            planet_lay.addWidget(row)

        # Legend for badges
        legend_lbl = QLabel("  ✨ Vargottama (D1=D9)   ℞ Retrograde   ☌ Combust")
        legend_lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:10px;background:transparent;")
        planet_lay.addWidget(legend_lbl)
        lay.addWidget(_section_box("Graha Sthiti Vishleshan", planet_w))

        # ── 5. Shubha points ─────────────────────────────────────────────────
        if r.get("shubha_points"):
            sw = QWidget()
            sw.setStyleSheet("background:transparent;")
            sl = QVBoxLayout(sw)
            sl.setContentsMargins(0, 0, 0, 0)
            sl.setSpacing(2)
            for pt in r["shubha_points"]:
                sl.addWidget(_bullet_label(f"✅ {pt}", "#15803d"))
            lay.addWidget(_section_box("✨ शुभ प्रभावहरू", sw))

        # ── 6. Ashubha points ────────────────────────────────────────────────
        if r.get("ashubha_points"):
            aw = QWidget()
            aw.setStyleSheet("background:transparent;")
            al = QVBoxLayout(aw)
            al.setContentsMargins(0, 0, 0, 0)
            al.setSpacing(2)
            for pt in r["ashubha_points"]:
                al.addWidget(_bullet_label(f"❌ {pt}", "#b91c1c"))
            lay.addWidget(_section_box("⚠ अशुभ प्रभावहरू", aw))

        # ── 7. Yogas ─────────────────────────────────────────────────────────
        if r.get("yogas"):
            yw = QWidget()
            yw.setStyleSheet("background:transparent;")
            yl = QVBoxLayout(yw)
            yl.setContentsMargins(0, 0, 0, 0)
            yl.setSpacing(2)
            for yoga in r["yogas"]:
                yl.addWidget(_bullet_label(f"🔮 {yoga}", "#7c3aed"))
            lay.addWidget(_section_box("🌟 महत्त्वपूर्ण योगहरू (BPHS)", yw))

        # ── 8. Timing ────────────────────────────────────────────────────────
        if r.get("timing"):
            tw = QWidget()
            tw.setStyleSheet("background:transparent;")
            tl = QVBoxLayout(tw)
            tl.setContentsMargins(0, 0, 0, 0)
            tl.setSpacing(2)
            for t in r["timing"]:
                tl.addWidget(_bullet_label(f"🕐 {t}", "#1d4ed8"))
            lay.addWidget(_section_box("📅 दशा र समय-फल", tw))

        # ── 9. Remedies ──────────────────────────────────────────────────────
        if r.get("remedies"):
            rw = QWidget()
            rw.setStyleSheet("background:transparent;")
            rl = QVBoxLayout(rw)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(2)
            for rem in r["remedies"]:
                rl.addWidget(_bullet_label(f"{rem}", "#6d28d9"))
            lay.addWidget(_section_box("🙏 उपाय र सुझाव (BPHS आधारित)", rw))

        # ── 10. Purpose footer ───────────────────────────────────────────────
        purpose_lbl = QLabel(r.get("purpose", ""))
        purpose_lbl.setWordWrap(True)
        purpose_lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:11px;font-style:italic;background:transparent;")
        lay.addWidget(purpose_lbl)
        lay.addStretch()


# ─────────────────────────────────────────────────────────────────────────────
# Main Page
# ─────────────────────────────────────────────────────────────────────────────
class VargasGridPage(QWidget):
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header bar
        hdr = QHBoxLayout()
        title = QLabel("🌌 " + ("वर्ग कुण्डली समूह (Divisional Charts)" if self._is_ne else "Divisional Charts (Vargas)"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 17px; font-weight: 700;")
        hdr.addWidget(title)
        hdr.addStretch()

        hdr.addWidget(QLabel("वर्ग छान्नुहोस्:" if self._is_ne else "Select Varga:", self))
        self._combo = QComboBox()
        self._combo.setMinimumWidth(280)
        for vk, vn in VARGA_NAMES.items():
            self._combo.addItem(vn["ne"] if self._is_ne else vn["en"], vk)
        self._combo.currentIndexChanged.connect(self._on_varga_changed)
        hdr.addWidget(self._combo)
        layout.addLayout(hdr)

        # Content Splitter (Chart left + Analysis right)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("QSplitter::handle{background:#2a2a3a;border-radius:3px;}")

        # Left: chart
        self._chart_widget = NorthIndianChartWidget(self._data, "D1", self._lang, self)
        self._chart_widget.setMinimumWidth(300)
        splitter.addWidget(self._chart_widget)

        # Right: analysis panel (white background)
        self._analysis_panel = VargaAnalysisPanel(self)
        self._analysis_panel.setMinimumWidth(340)
        self._analysis_panel.setStyleSheet("background:#ffffff;border:1px solid #c7d8f5;border-radius:8px;")
        splitter.addWidget(self._analysis_panel)

        # Set initial sizes (chart 45%, analysis 55%)
        splitter.setSizes([420, 520])
        layout.addWidget(splitter, 1)

        # ── User Guide button (bottom of page) ──────────────────────────────
        # The guide text lives in the shared "मद्दत" User Guide dialog, so the
        # page keeps its full height and the guide never covers the content.
        _guide_btn = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn.setObjectName("vargaGuideBox")
        _guide_btn.setToolTip("वर्ग कुण्डली निर्देशिका" if self._is_ne else "Divisional charts guide")
        _guide_btn.setCursor(Qt.PointingHandCursor)
        _guide_btn.setStyleSheet(
            "QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; "
            "border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } "
            "QPushButton:hover { background: #bae6fd; }"
        )

        def _open_varga_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_varga_view")

        _guide_btn.clicked.connect(_open_varga_guide)
        layout.addWidget(_guide_btn)

        self._update_display("D1")

    def _on_varga_changed(self, idx: int):
        vk = self._combo.currentData() or "D1"
        self._update_display(vk)

    def _update_display(self, vkey: str):
        self._chart_widget.set_data(self._data, vkey)
        self._analysis_panel.load(self._data, vkey)

    def refresh(self, data: dict):
        self._data = data
        vk = self._combo.currentData() or "D1"
        self._chart_widget.set_data(data, vk)
        self._analysis_panel.load(data, vk)


# ─────────────────────────────────────────────────────────────────────────────
# Sudarshan Chakra (BPHS Chapter 74 - Upgraded)
# ─────────────────────────────────────────────────────────────────────────────
SUDARSHAN_RINGS = (
    {"key": "sun",   "en": "Sun Chart (Surya Lagna)",    "ne": "सूर्य कुण्डली (बाह्य/प्रतिष्ठा)", "color": "#dc2626"},
    {"key": "moon",  "en": "Moon Chart (Chandra Lagna)", "ne": "चन्द्र कुण्डली (मन/भावना)",        "color": "#2563eb"},
    {"key": "lagna", "en": "Lagna Chart (Tan Lagna)",    "ne": "लग्न कुण्डली (शरीर/भौतिक)",       "color": "#d97706"},
)


def _safe_sign(item: Any) -> int:
    if isinstance(item, dict):
        if item.get("sign_number"):
            return int(item["sign_number"])
        lon = float(item.get("sidereal_longitude", item.get("longitude", 0)) or 0)
        return (int(lon / 30.0) % 12) + 1
    elif isinstance(item, (int, float)):
        return int(item)
    return 1


def sudarshan_model(data: Optional[dict], language: str = "ne") -> dict:
    """Build the three-ring contract from actual natal signs with robust fallback extraction."""
    source = data if isinstance(data, dict) else {}
    planets_raw = list(source.get("planets", []))
    planets = []
    by_name = {}
    for p in planets_raw:
        if isinstance(p, dict) and p.get("name"):
            s_num = _safe_sign(p)
            p_clean = {**p, "sign_number": s_num}
            planets.append(p_clean)
            by_name[p["name"]] = p_clean

    sun_sign = _safe_sign(by_name.get("Sun", {})) if "Sun" in by_name else _safe_sign(source.get("lagna", {}))
    moon_sign = _safe_sign(by_name.get("Moon", {})) if "Moon" in by_name else _safe_sign(source.get("lagna", {}))
    lagna_sign = _safe_sign(source.get("lagna", {}))

    refs = {
        "sun":   sun_sign,
        "moon":  moon_sign,
        "lagna": lagna_sign,
    }
    rings = []
    for definition in SUDARSHAN_RINGS:
        ref_sign = refs[definition["key"]]
        houses = []
        for house in range(1, 13):
            sign = ((ref_sign - 1 + house - 1) % 12) + 1
            occupants = [planet for planet in planets if _safe_sign(planet) == sign]
            houses.append({"house": house, "sign": sign, "planets": occupants})
        rings.append({**definition, "label": definition[language], "reference_sign": ref_sign, "houses": houses})
    return {
        "identity": "sudarshan",
        "rings": rings,
        "planet_count": len(planets),
        "refs": refs,
        "palette": {"background": "#ffffff", "line": "#cbd5e1", "text": COLOR_TEXT_PRIMARY},
    }


class SudarshanChakraWidget(QWidget):
    """Visual concentric three-ring Sudarshan Chakra wheel with cosmic alignment animation."""

    def _get_rotation_progress(self) -> float:
        return self._rotation_progress

    def _set_rotation_progress(self, v: float):
        self._rotation_progress = max(0.0, min(1.0, float(v)))
        self.update()

    rotation_progress = Property(float, _get_rotation_progress, _set_rotation_progress)

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._model = sudarshan_model(data, language)
        self._rotation_progress: float = 1.0
        self._pulse_phase: float = 0.0
        self._anim: Optional[QPropertyAnimation] = None

        self.setMinimumSize(360, 360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolTip("सुदर्शन चक्र (डबल क्लिकले दिव्य रोटेसन पुनः देखाउँछ)" if language == "ne" else "Sudarshan Chakra (Double click to replay animation)")

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(30)
        self._pulse_timer.timeout.connect(self._on_pulse)
        self._pulse_timer.start()

        if data:
            QTimer.singleShot(60, self.play_animation)

    def _on_pulse(self):
        self._pulse_phase += 0.06
        if self._pulse_phase >= math.tau:
            self._pulse_phase -= math.tau
        self.update()

    def play_animation(self):
        if self._anim and self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()
        self._rotation_progress = 0.0
        anim = QPropertyAnimation(self, b"rotation_progress", self)
        anim.setDuration(900)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim = anim
        anim.start()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        self.play_animation()

    def showEvent(self, event):
        super().showEvent(event)
        if self._rotation_progress >= 0.99:
            self.play_animation()

    def set_data(self, data: Optional[dict]) -> None:
        self._model = sudarshan_model(data, self._lang)
        self.play_animation()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        side = min(self.width(), self.height())
        scale = side / 480.0
        cx, cy = self.width() / 2.0, self.height() / 2.0

        p = self._rotation_progress
        # Smooth radial expansion from 65% to 100%
        r_mult = 0.65 + 0.35 * p
        radii = (205 * r_mult, 145 * r_mult, 85 * r_mult)

        # Draw outer boundary circle
        painter.setPen(QPen(QColor("#cbd5e1"), max(1, int(1.5 * scale))))
        painter.drawEllipse(QPointF(cx, cy), 235 * scale * r_mult, 235 * scale * r_mult)

        # Radial spokes for 12 house sectors (rotate smoothly with progress)
        base_rot = (1.0 - p) * 40.0
        for degree in range(0, 360, 30):
            angle = math.radians(degree - 90 + base_rot)
            painter.drawLine(
                QPointF(cx + 28 * scale * math.cos(angle), cy + 28 * scale * math.sin(angle)),
                QPointF(cx + 235 * scale * r_mult * math.cos(angle), cy + 235 * scale * r_mult * math.sin(angle))
            )

        # Draw the 3 concentric rings with differential cosmic rotation
        # Outer: rotates from +60 to 0; Middle: rotates from -75 to 0; Inner: rotates from +45 to 0
        ring_rotations = (
            (1.0 - p) * 60.0,
            (1.0 - p) * -75.0,
            (1.0 - p) * 45.0,
        )

        r_names = RASHI_NAMES.get(self._lang, RASHI_NAMES.get("ne", []))
        for (ring, radius, r_rot) in zip(self._model["rings"], radii, ring_rotations):
            color = QColor(ring["color"])
            painter.setPen(QPen(color, max(2, int(2.5 * scale))))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius * scale, radius * scale)

            for cell in ring["houses"]:
                angle = math.radians(-105 - (cell["house"] - 1) * 30 + r_rot)
                text_radius = (radius - 24) * scale
                x = cx + text_radius * math.cos(angle)
                y = cy + text_radius * math.sin(angle)
                s_idx = (int(cell["sign"]) - 1) % 12
                sign_label = r_names[s_idx] if isinstance(r_names, list) and 0 <= s_idx < len(r_names) else str(cell["sign"])
                occupants = ",".join(
                    PLANET_ABBR.get(self._lang, PLANET_ABBR["en"]).get(p.get("name"), p.get("name", ""))
                    for p in cell["planets"]
                )

                # Sign text in ring color
                painter.setFont(QFont(["Nirmala UI", "Segoe UI Historic", "Mangal", "Noto Sans Devanagari"], max(7, int(8.5 * scale)), QFont.Bold))
                painter.setPen(color)
                painter.drawText(QRectF(x - 45 * scale, y - 14 * scale, 90 * scale, 16 * scale), Qt.AlignCenter, f"{sign_label} ({cell['sign']})")

                # Planet occupants text
                if occupants:
                    painter.setPen(QColor("#0f172a"))
                    painter.setFont(QFont(["Nirmala UI", "Segoe UI Historic", "Mangal", "Noto Sans Devanagari"], max(6, int(8 * scale)), QFont.Bold))
                    painter.drawText(QRectF(x - 45 * scale, y + 1 * scale, 90 * scale, 16 * scale), Qt.AlignCenter, occupants)

        # Central Golden Hub with pulsing cosmic aura
        pulse_factor = 0.5 + 0.5 * math.sin(self._pulse_phase)
        glow_r = (28 + 8 * pulse_factor) * scale
        glow = QRadialGradient(cx, cy, glow_r)
        glow.setColorAt(0.0, QColor(254, 240, 138, int(160 + 60 * pulse_factor)))
        glow.setColorAt(0.7, QColor(251, 191, 36, int(80 * pulse_factor)))
        glow.setColorAt(1.0, QColor(251, 191, 36, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        painter.setBrush(QBrush(QColor("#fefce8")))
        painter.setPen(QPen(QColor("#d97706"), max(2, int(2 * scale))))
        painter.drawEllipse(QPointF(cx, cy), 28 * scale, 28 * scale)

        painter.setPen(QColor("#b45309"))
        painter.setFont(QFont(["Nirmala UI", "Segoe UI Historic", "Mangal", "Noto Sans Devanagari"], max(7, int(8.5 * scale)), QFont.Bold))
        painter.drawText(
            QRectF(cx - 30 * scale, cy - 12 * scale, 60 * scale, 24 * scale),
            Qt.AlignCenter,
            "सुदर्शन" if self._lang == "ne" else "Center"
        )
        painter.end()


class SudarshanAnalysisPanel(QScrollArea):
    """Right-side comprehensive analysis panel for Sudarshan Chakra."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._container.setStyleSheet("background:#ffffff;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        self.setWidget(self._container)

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
                from backend.calculator.sudarshan_analysis import analyze_sudarshan_chakra
            except ImportError:
                from calculator.sudarshan_analysis import analyze_sudarshan_chakra
            res = analyze_sudarshan_chakra(chart_data, language)
            self._render(res, language)
        except Exception as e:
            lbl = QLabel(f"⚠ विश्लेषणमा त्रुटि: {e}")
            lbl.setStyleSheet("color:#b91c1c;font-size:12px;")
            self._layout.addWidget(lbl)
            self._layout.addStretch()

    def _render(self, r: dict, lang: str):
        lay = self._layout
        is_ne = lang == "ne"

        # ── 1. Top Conclusion Banner ─────────────────────────────────────────
        conc_frame = QFrame()
        conc_frame.setStyleSheet("background:#eff6ff;border:2px solid #93c5fd;border-radius:8px;padding:10px;")
        conc_lay = QVBoxLayout(conc_frame)
        conc_lay.setContentsMargins(8, 6, 8, 6)
        conc_lay.setSpacing(4)
        v_lbl = QLabel(f"📌 निष्कर्ष: {r.get('verdict','')}")
        v_lbl.setStyleSheet("color:#1d4ed8;font-size:13px;font-weight:700;background:transparent;")
        conc_lay.addWidget(v_lbl)
        c_lbl = QLabel(r.get("conclusion",""))
        c_lbl.setWordWrap(True)
        c_lbl.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:12px;background:transparent;")
        conc_lay.addWidget(c_lbl)
        lay.addWidget(conc_frame)

        # ── 2. Harmony Score Meter ───────────────────────────────────────────
        meter_frame = QFrame()
        meter_frame.setStyleSheet("background:#ffffff;border:1px solid #c7d8f5;border-radius:6px;padding:8px;")
        m_lay = QVBoxLayout(meter_frame)
        m_lay.setContentsMargins(6, 6, 6, 6)
        m_lay.setSpacing(4)
        hp = r.get("harmony_percent", 50)
        h_row = QHBoxLayout()
        h_title = QLabel("⚖ त्रि-दृष्टिकोण समन्वयता (Lagna + Moon + Sun)")
        h_title.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:12px;font-weight:600;background:transparent;")
        h_row.addWidget(h_title)
        h_row.addStretch()
        h_pct = QLabel(f"🌟 {hp}% समन्वय")
        h_pct.setStyleSheet("color:#15803d;font-size:12px;font-weight:700;background:transparent;")
        h_row.addWidget(h_pct)
        m_lay.addLayout(h_row)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(hp)
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        bar.setStyleSheet(
            "QProgressBar{background:#e2e8f0;border-radius:5px;border:none;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:5px;}"
        )
        m_lay.addWidget(bar)
        lay.addWidget(meter_frame)

        # ── 3. Reference Signs Summary ───────────────────────────────────────
        ref_row = QHBoxLayout()
        ref_row.setSpacing(6)
        badges = [
            ("लग्न (शरीर)", r.get("lagna_sign_name",""), "#d97706", "#fef3c7"),
            ("चन्द्र (मन)",  r.get("moon_sign_name",""),  "#2563eb", "#dbeafe"),
            ("सूर्य (आत्मा)",r.get("sun_sign_name",""),   "#dc2626", "#fee2e2"),
        ]
        for title, val, text_c, bg_c in badges:
            f = QFrame()
            f.setStyleSheet(f"background:{bg_c};border:1px solid {text_c};border-radius:6px;padding:4px;")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(4, 3, 4, 3)
            fl.setSpacing(1)
            tl = QLabel(title)
            tl.setStyleSheet(f"color:{text_c};font-size:10px;font-weight:600;background:transparent;")
            fl.addWidget(tl)
            vl = QLabel(f"{val} राशि")
            vl.setStyleSheet(f"color:{text_c};font-size:13px;font-weight:700;background:transparent;")
            fl.addWidget(vl)
            ref_row.addWidget(f)
        lay.addLayout(ref_row)

        # ── 4. Sudarshan Dasha (BPHS Ch. 74) ─────────────────────────────────
        sd = r.get("sudarshan_dasha", {})
        if sd:
            d_box = QFrame()
            d_box.setStyleSheet("background:#faf5ff;border:1px solid #d8b4fe;border-radius:6px;padding:8px;")
            dl = QVBoxLayout(d_box)
            dl.setContentsMargins(6, 6, 6, 6)
            dl.setSpacing(4)
            age_display = sd.get("current_age_year_ne") or f"{sd.get('current_age_year')}औँ वर्ष"
            d_title = QLabel(f"⏳ सुदर्शन चक्र दशा: {age_display} ➔ {sd.get('active_house_name')}")
            d_title.setStyleSheet("color:#7c3aed;font-size:12px;font-weight:700;background:transparent;")
            dl.addWidget(d_title)
            d_sum = QLabel(sd.get("summary",""))
            d_sum.setWordWrap(True)
            d_sum.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:11px;background:transparent;")
            dl.addWidget(d_sum)
            lay.addWidget(_section_box("📅 सुदर्शन चक्र दशा (वार्षिक चक्र - BPHS)", d_box))

        # ── 5. 12 Houses Tri-View Table ──────────────────────────────────────
        hw = QWidget()
        hw.setStyleSheet("background:transparent;")
        hl = QVBoxLayout(hw)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(4)

        for ha in r.get("houses_analysis", []):
            hf = QFrame()
            hf.setStyleSheet(
                "background:#f8fafc;border:1px solid #e2e8f0;border-radius:5px;padding:4px;"
            )
            h_lay = QVBoxLayout(hf)
            h_lay.setContentsMargins(6, 4, 6, 4)
            h_lay.setSpacing(3)

            top_h = QHBoxLayout()
            h_num_lbl = QLabel(ha.get("house_name",""))
            h_num_lbl.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:12px;font-weight:700;background:transparent;")
            top_h.addWidget(h_num_lbl)
            top_h.addStretch()

            v_badge = QLabel(ha.get("verdict",""))
            v_badge.setStyleSheet(f"color:{ha.get('verdict_color','#1e40af')};font-size:11px;font-weight:600;background:transparent;")
            top_h.addWidget(v_badge)
            h_lay.addLayout(top_h)

            tri_row = QHBoxLayout()
            tri_row.setSpacing(4)

            # Lagna View
            l_pl = ", ".join(ha.get("lagna_planets", [])) or "—"
            tri_row.addWidget(QLabel(f"• लग्न: <b>{ha.get('lagna_sign_name')}</b> ({l_pl})", styleSheet="color:#d97706;font-size:10px;background:transparent;"))

            # Moon View
            m_pl = ", ".join(ha.get("moon_planets", [])) or "—"
            tri_row.addWidget(QLabel(f"• चन्द्र: <b>{ha.get('moon_sign_name')}</b> ({m_pl})", styleSheet="color:#2563eb;font-size:10px;background:transparent;"))

            # Sun View
            s_pl = ", ".join(ha.get("sun_planets", [])) or "—"
            tri_row.addWidget(QLabel(f"• सूर्य: <b>{ha.get('sun_sign_name')}</b> ({s_pl})", styleSheet="color:#dc2626;font-size:10px;background:transparent;"))

            h_lay.addLayout(tri_row)
            hl.addWidget(hf)

        lay.addWidget(_section_box("📊 १२ भाव त्रि-कुण्डली तुलना (Lagna + Moon + Sun)", hw))

        # ── 6. Planets across 3 Reference Points ─────────────────────────────
        pw = QWidget()
        pw.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(pw)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(2)

        for pa in r.get("planets_analysis", []):
            pf = QFrame()
            pf.setStyleSheet("background:#ffffff;border:1px solid #e2e8f0;border-radius:4px;padding:3px 6px;")
            pfl = QHBoxLayout(pf)
            pfl.setContentsMargins(4, 2, 4, 2)
            pfl.setSpacing(6)

            p_lbl = QLabel(pa.get("name_ne",""))
            p_lbl.setFixedWidth(50)
            p_lbl.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:11px;font-weight:700;background:transparent;")
            pfl.addWidget(p_lbl)

            s_lbl = QLabel(f"({pa.get('sign_name','')})")
            s_lbl.setFixedWidth(55)
            s_lbl.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:10px;background:transparent;")
            pfl.addWidget(s_lbl)

            pfl.addWidget(QLabel(f"लग्नबाट: भाव {pa.get('house_from_lagna')}", styleSheet="color:#d97706;font-size:10px;background:transparent;"))
            pfl.addWidget(QLabel(f"चन्द्रबाट: भाव {pa.get('house_from_moon')}", styleSheet="color:#2563eb;font-size:10px;background:transparent;"))
            pfl.addWidget(QLabel(f"सूर्यबाट: भाव {pa.get('house_from_sun')}", styleSheet="color:#dc2626;font-size:10px;background:transparent;"))
            pfl.addStretch()

            pl.addWidget(pf)

        lay.addWidget(_section_box("🪐 ग्रहहरूको त्रि-लग्न स्थिति", pw))

        # ── 7. Remedies ──────────────────────────────────────────────────────
        if r.get("remedies"):
            rw = QWidget()
            rw.setStyleSheet("background:transparent;")
            rl = QVBoxLayout(rw)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(2)
            for rem in r["remedies"]:
                rl.addWidget(_bullet_label(f"• {rem}", "#15803d"))
            lay.addWidget(_section_box("🙏 सुदर्शन शान्ति तथा शुभ उपायहरू (BPHS)", rw))

        lay.addStretch()


class SudarshanChakraPage(QWidget):
    """Upgraded Sudarshan Chakra Page with visual 3-ring wheel and comprehensive BPHS analysis."""
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data or {}
        self._lang = language
        self._is_ne = language == "ne"
        # Collapsed by default so the wheel + analysis splitter keeps the full page.
        self._guide_expanded = False
        # Own the normalized Sudarshan model on the page so tests and callers can
        # inspect the three reference rings without reaching into the child widget.
        self._model = sudarshan_model(self._data, self._lang)
        self._build_ui()

    def _build_ui(self):
        # Outer layout containing a dedicated scroll area so no content or guide is ever clipped
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        outer_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 32)
        layout.setSpacing(12)
        scroll.setWidget(container)

        # Header Title
        title_row = QHBoxLayout()
        title = QLabel("☸ " + ("सुदर्शन चक्र (Sudarshan Chakra)" if self._is_ne else "Sudarshan Chakra"))
        title.setObjectName("sudarshanTitle")
        title.setStyleSheet(f"color:{COLOR_GOLD};font-size:17px;font-weight:700;")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        subtitle = QLabel(
            "सूर्य, चन्द्र र लग्नबाट एउटै जन्म ग्रहस्थितिको तुलनात्मक त्रि-दृष्टिकोण विश्लेषण (BPHS Ch. 74)।" if self._is_ne else
            "Comparative tri-perspective view from Sun, Moon, and Ascendant according to BPHS Chapter 74."
        )
        subtitle.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:12px;")
        layout.addWidget(subtitle)

        # Splitter Layout (Left: Wheel + Legend, Right: Full Analysis Panel)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.setMinimumHeight(440)
        splitter.setStyleSheet("QSplitter::handle{background:#e2e8f0;border-radius:3px;}")

        # Left Container
        left_container = QWidget()
        left_container.setStyleSheet("background:#ffffff;border:1px solid #c7d8f5;border-radius:8px;")
        left_lay = QVBoxLayout(left_container)
        left_lay.setContentsMargins(10, 10, 10, 10)
        left_lay.setSpacing(8)

        self._chakra = SudarshanChakraWidget(self._data, self._lang, self)
        self._chakra.setObjectName("sudarshanChakra")
        left_lay.addWidget(self._chakra, 1)

        # Legend under wheel
        legend = QLabel()
        legend.setObjectName("sudarshanLegend")
        legend.setAlignment(Qt.AlignCenter)
        legend_text = (
            '<span style="color:#d97706;font-weight:bold;">● लग्न कुण्डली (भित्री)</span> &nbsp;|&nbsp; '
            '<span style="color:#2563eb;font-weight:bold;">● चन्द्र कुण्डली (मध्य)</span> &nbsp;|&nbsp; '
            '<span style="color:#dc2626;font-weight:bold;">● सूर्य कुण्डली (बाहिरी)</span>'
            if self._is_ne else
            '<span style="color:#d97706;font-weight:bold;">● Lagna (Inner)</span> &nbsp;|&nbsp; '
            '<span style="color:#2563eb;font-weight:bold;">● Moon (Middle)</span> &nbsp;|&nbsp; '
            '<span style="color:#dc2626;font-weight:bold;">● Sun (Outer)</span>'
        )
        legend.setText(legend_text)
        legend.setTextFormat(Qt.RichText)
        legend.setStyleSheet("font-size:11px;background:transparent;padding:4px;")
        left_lay.addWidget(legend)

        splitter.addWidget(left_container)

        # Right Container: Analysis Panel
        self._analysis_panel = SudarshanAnalysisPanel(self)
        self._analysis_panel.setStyleSheet("background:#ffffff;border:1px solid #c7d8f5;border-radius:8px;")
        self._analysis_panel.load(self._data, self._lang)
        splitter.addWidget(self._analysis_panel)

        # Initial ratio (Left 45%, Right 55%)
        splitter.setSizes([450, 550])
        layout.addWidget(splitter, 1)

        # ── User Guide button (bottom of page) ──────────────────────────────
        # The guide text lives in the shared "मद्दत" User Guide dialog, keeping
        # the Sudarshan Chakra wheel and analysis at full height.
        _guide_btn2 = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn2.setObjectName("SudarshanGuideBox")
        _guide_btn2.setToolTip("सुदर्शन चक्र निर्देशिका" if self._is_ne else "Sudarshan Chakra guide")
        _guide_btn2.setCursor(Qt.PointingHandCursor)
        _guide_btn2.setStyleSheet(
            "QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; "
            "border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } "
            "QPushButton:hover { background: #bae6fd; }"
        )

        def _open_sudarshan_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_sudarshan_view")

        _guide_btn2.clicked.connect(_open_sudarshan_guide)
        layout.addWidget(_guide_btn2)

    def refresh(self, data: dict):
        self._data = data or {}
        self._model = sudarshan_model(self._data, self._lang)
        self._chakra.set_data(self._data)
        self._analysis_panel.load(self._data, self._lang)

