"""
gui/widgets/visual_graphs.py

Astro Visual Graphs — Shadbala Strengths Bar Graph and Ashtakavarga Radar/Spider Chart.
Native PySide6 implementation using Matplotlib / QPainter with 3D aesthetic and scientific styling.
"""
from __future__ import annotations
import sys, os
from typing import Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY)

try:
    import matplotlib
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    # Ensure Devanagari font support on Windows
    matplotlib.rcParams["font.sans-serif"] = [
        "Nirmala UI", "Mangal", "Segoe UI", "Noto Sans Devanagari",
        "DejaVu Sans", "Arial", "sans-serif"
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    import matplotlib.patches as mpatches
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
PLANET_NEP_NAMES = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल",
    "Mercury": "बुध", "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि"
}
RASHI_NEP_NAMES = [
    "मेष (1)", "वृष (2)", "मिथुन (3)", "कर्क (4)",
    "सिंह (5)", "कन्या (6)", "तुला (7)", "वृश्चिक (8)",
    "धनु (9)", "मकर (10)", "कुम्भ (11)", "मीन (12)"
]
RASHI_ENG_NAMES = [
    "Aries (1)", "Taurus (2)", "Gemini (3)", "Cancer (4)",
    "Leo (5)", "Virgo (6)", "Libra (7)", "Scorpio (8)",
    "Sagittarius (9)", "Capricorn (10)", "Aquarius (11)", "Pisces (12)"
]
COMPONENT_NEP_NAMES = {
    "sthana": "स्थान बल",
    "dig": "दिग् बल",
    "kala": "काल बल",
    "cheshta": "चेष्टा बल",
    "naisargika": "नैसर्गिक बल",
    "drik": "दृक् बल"
}
MIN_REQUIRED_VIRUPAS = {
    "Sun": 390.0, "Moon": 360.0, "Mars": 300.0, "Mercury": 420.0,
    "Jupiter": 390.0, "Venus": 330.0, "Saturn": 300.0,
}
COMPONENT_KEYS = ("sthana", "dig", "kala", "cheshta", "naisargika", "drik")


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def build_visual_graphs_model(data: Optional[dict]) -> dict:
    """Extract graph series exclusively from the authoritative backend payload."""
    if not isinstance(data, dict):
        return {"state": "no_chart", "shadbala": [], "breakdown": [], "sav": []}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"]), "shadbala": [], "breakdown": [], "sav": []}

    shadbala_root = data.get("shadbala")
    planet_data = shadbala_root.get("planets") if isinstance(shadbala_root, dict) else None
    shadbala = []
    breakdown = []
    if isinstance(planet_data, dict):
        for name in PLANETS:
            item = planet_data.get(name)
            if not isinstance(item, dict):
                continue
            actual = _number(item.get("total_shashtiamsa"))
            if actual is None:
                rupas = _number(item.get("total_rupas"))
                actual = rupas * 60.0 if rupas is not None else None
            if actual is not None:
                shadbala.append({
                    "name": name,
                    "actual": actual,
                    "minimum": MIN_REQUIRED_VIRUPAS[name],
                    "ratio": actual / MIN_REQUIRED_VIRUPAS[name],
                })

            components = item.get("components")
            values = {}
            if isinstance(components, dict):
                for key in COMPONENT_KEYS:
                    component = components.get(key)
                    value = _number(component.get("shashtiamsa")) if isinstance(component, dict) else None
                    if value is not None:
                        values[key] = value
            if len(values) == len(COMPONENT_KEYS):
                breakdown.append({"name": name, **values, "total": sum(values.values())})

    ashtakavarga = data.get("ashtakavarga")
    sav_raw = ashtakavarga.get("sav") if isinstance(ashtakavarga, dict) else None
    sav = [_number(value) for value in sav_raw] if isinstance(sav_raw, list) and len(sav_raw) == 12 else []
    if sav and any(value is None for value in sav):
        sav = []

    state = "ready" if shadbala or sav or breakdown else "empty"
    return {"state": state, "shadbala": shadbala, "breakdown": breakdown, "sav": sav}


class AstroVisualGraphsPage(QWidget):
    """Visual Analytics for Shadbala & Ashtakavarga with 3D/scientific aesthetics."""
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
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        # Header Title
        title = QLabel("📊 " + ("अष्टकवर्ग र षड्बल भिजुअल ग्राफहरू (3D Scientific Visual Graphs)" if self._is_ne else "Ashtakavarga & Shadbala Visual Analytics"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel(
            "ग्रहहरूको सामर्थ्य (षड्बल) र १२ राशिको शक्ति विन्दु (सर्वअष्टकवर्ग) को विस्तृत वैज्ञानिक ३D ग्राफिकल विश्लेषण।"
            if self._is_ne else
            "High-precision 3D scientific visualization of planetary potencies (Shadbala) and sign points (Ashtakavarga)."
        )
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; margin-bottom: 2px;")
        layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll, 1)

        # ── User Guide button (at the bottom; opens the shared guide dialog) ───
        # No inline guide box is rendered here, so the graphs keep the full page.
        _guide_btn = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn.setObjectName("visualGraphsGuideBox")
        _guide_btn.setToolTip("भिजुअल ग्राफ निर्देशिका" if self._is_ne else "Visual graphs guide")
        _guide_btn.setCursor(Qt.PointingHandCursor)
        _guide_btn.setStyleSheet(
            "QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; "
            "border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } "
            "QPushButton:hover { background: #bae6fd; }"
        )

        def _open_visual_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_visual_graphs_view")

        _guide_btn.clicked.connect(_open_visual_guide)
        layout.addWidget(_guide_btn)

        container = QWidget()
        container.setStyleSheet("background: #ffffff;")
        self._c_layout = QVBoxLayout(container)
        self._c_layout.setContentsMargins(0, 0, 4, 0)
        self._c_layout.setSpacing(16)
        scroll.setWidget(container)

    def refresh(self, data: dict):
        self._data = data
        self._model = build_visual_graphs_model(data)
        while self._c_layout.count():
            item = self._c_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._model["state"] != "ready":
            messages = {
                "no_chart": ("कुण्डली गणना गर्नुहोस्।", "Calculate a chart first."),
                "empty": ("ग्राफका लागि गणना डेटा उपलब्ध छैन।", "No calculated graph data is available."),
                "error": ("गणना डेटा लोड गर्न सकिएन।", "Calculation data could not be loaded."),
            }
            ne, en = messages.get(self._model["state"], messages["empty"])
            lbl = QLabel(ne if self._is_ne else en)
            lbl.setObjectName("visualGraphsState")
            lbl.setStyleSheet("color: #64748b; font-size: 14px; padding: 24px; text-align: center;")
            self._c_layout.addWidget(lbl)
            return

        if not HAS_MPL:
            lbl = QLabel("Matplotlib लाइब्रेरी उपलब्ध छैन।" if self._is_ne else "Matplotlib library is missing.")
            lbl.setStyleSheet("color: #ef4444; font-size: 13px;")
            self._c_layout.addWidget(lbl)
            return

        # ── 1. 3D-Enhanced Shadbala Strength Bar Chart ──────────────────────────
        if self._model["shadbala"]:
            card1 = QFrame()
            card1.setStyleSheet("background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;")
            cl1 = QVBoxLayout(card1)
            cl1.setContentsMargins(16, 16, 16, 16)
            cl1.setSpacing(10)

            t1 = QLabel("⚡ " + ("षड्बल ग्रह सामर्थ्य ग्राफ (3D Shadbala Strength & Benchmark Virupas)" if self._is_ne else "Shadbala Planetary Strengths (3D Virupas)"))
            t1.setStyleSheet("color: #7c3d00; font-size: 16px; font-weight: 700;")
            cl1.addWidget(t1)

            sub1 = QLabel("निलो/रंगीन बार = वास्तविक बल (Actual Virupas) | रातो ड्यास रेखा = आवश्यक न्यूनतम बल (Minimum Required)")
            sub1.setStyleSheet("color: #64748b; font-size: 12px;")
            cl1.addWidget(sub1)

            summary = self._model["shadbala"]
            p_names_en = [item["name"] for item in summary]
            p_labels = [PLANET_NEP_NAMES.get(name, name) if self._is_ne else name for name in p_names_en]
            values = [item["actual"] for item in summary]
            min_req = [item["minimum"] for item in summary]
            ratios = [item["ratio"] for item in summary]

            palette = {
                "Sun": "#e65100", "Moon": "#0284c7", "Mars": "#dc2626",
                "Mercury": "#059669", "Jupiter": "#d97706", "Venus": "#db2777", "Saturn": "#4f46e5"
            }
            colors = [palette.get(name, "#2563eb") for name in p_names_en]

            fig1, ax1 = plt.subplots(figsize=(9, 4.2), dpi=110, facecolor="#ffffff")
            ax1.set_facecolor("#fafbfc")

            x_pos = np.arange(len(p_labels))
            bar_width = 0.48

            # 3D Depth / Shadow effect for each bar
            for i, (x, val, col) in enumerate(zip(x_pos, values, colors)):
                # Shadow bar
                ax1.bar(x + 0.02, val, width=bar_width, color="#000000", alpha=0.08, zorder=2)
                # Front primary bar
                bar = ax1.bar(x, val, width=bar_width, color=col, edgecolor="#ffffff", linewidth=1.2, zorder=3, alpha=0.92)
                
                # 3D Bevel Highlight cap
                ax1.bar(x, min(val * 0.04, 15), bottom=val - min(val * 0.04, 15), width=bar_width, color="#ffffff", alpha=0.35, zorder=4)

                # Value label on top of bar with Ratio badge
                ratio_pct = ratios[i] * 100.0
                status_color = "#16a34a" if ratio_pct >= 100.0 else "#dc2626"
                ax1.text(
                    x, val + 14,
                    f"{val:.1f} V\n({ratio_pct:.0f}%)",
                    ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold",
                    color=status_color, zorder=5
                )

            # Minimum requirement step line with markers
            ax1.plot(
                x_pos, min_req,
                color="#dc2626", linestyle="--", linewidth=2.0,
                marker="D", markersize=6, markerfacecolor="#ffffff", markeredgecolor="#dc2626", markeredgewidth=2,
                label="आवश्यक न्यूनतम (Min Required)" if self._is_ne else "Min Required Threshold",
                zorder=6
            )

            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(p_labels, fontsize=11, fontweight="bold", color="#1e293b")
            ax1.set_ylabel("शष्ट्यंश / विरुपा (Virupas)" if self._is_ne else "Virupas", fontsize=10, fontweight="bold", color="#475569")
            ax1.set_ylim(0, max(max(values), max(min_req)) * 1.25)

            ax1.grid(axis="y", color="#e2e8f0", linestyle="--", linewidth=0.8, alpha=0.8, zorder=1)
            ax1.set_axisbelow(True)

            for spine in ax1.spines.values():
                spine.set_color("#cbd5e1")
                spine.set_linewidth(1)

            ax1.legend(loc="upper right", framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)
            fig1.tight_layout()

            canvas1 = FigureCanvas(fig1)
            canvas1.setMinimumHeight(380)
            cl1.addWidget(canvas1)
            self._c_layout.addWidget(card1)

        # ── 2. 3D-Enhanced Ashtakavarga SAV Radar/Spider Chart ──────────────────
        if self._model["sav"]:
            card2 = QFrame()
            card2.setStyleSheet("background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;")
            cl2 = QVBoxLayout(card2)
            cl2.setContentsMargins(16, 16, 16, 16)
            cl2.setSpacing(10)

            t2 = QLabel("🕸️ " + ("सर्वअष्टकवर्ग १२ राशि शक्ति चक्र (3D Ashtakavarga SAV Radar Chart)" if self._is_ne else "Ashtakavarga 12-Sign Energy Radar (3D SAV)"))
            t2.setStyleSheet("color: #7c3d00; font-size: 16px; font-weight: 700;")
            cl2.addWidget(t2)

            sub2 = QLabel("औसत रेखा = २८ विन्दु (२८ भन्दा माथि = शुभ/सबल क्षेत्र, २८ भन्दा मुनि = कमजोर क्षेत्र)")
            sub2.setStyleSheet("color: #64748b; font-size: 12px;")
            cl2.addWidget(sub2)

            sav = self._model["sav"]
            num_vars = 12
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            sav_plot = sav + [sav[0]]
            angles += [angles[0]]

            fig2, ax2 = plt.subplots(figsize=(7.5, 6.2), dpi=110, subplot_kw=dict(polar=True), facecolor="#ffffff")
            ax2.set_facecolor("#fafbfc")

            # Offset first angle to top (North)
            ax2.set_theta_offset(np.pi / 2)
            ax2.set_theta_direction(-1)

            # Circular / Polygon grid
            rashi_names = RASHI_NEP_NAMES if self._is_ne else RASHI_ENG_NAMES
            ax2.set_xticks(angles[:-1])
            ax2.set_xticklabels(rashi_names, fontsize=10, fontweight="bold", color="#1e293b")

            # Shaded concentric threshold rings
            ax2.set_rlabel_position(22.5)
            max_val = max(max(sav), 38)
            ax2.set_ylim(0, max_val + 5)
            ax2.set_yticks([15, 20, 28, 35, 40])
            ax2.set_yticklabels(["15", "20", "28 (औसत)", "35", "40"], fontsize=8, color="#64748b")
            ax2.grid(color="#cbd5e1", linestyle="--", linewidth=0.8, alpha=0.9)

            # Average Benchmark Circle (28 points)
            avg_angles = np.linspace(0, 2 * np.pi, 100)
            ax2.plot(avg_angles, [28] * 100, color="#ef4444", linestyle="--", linewidth=1.6, label="औसत विन्दु २८ (Avg 28)", zorder=3)

            # 3D Gradient/Layered Fill for SAV polygon
            ax2.fill(angles, sav_plot, color="#3b82f6", alpha=0.22, zorder=2)
            ax2.plot(angles, sav_plot, color="#1d4ed8", linewidth=2.8, linestyle="solid", marker="o", markersize=6, markerfacecolor="#f59e0b", markeredgecolor="#1d4ed8", markeredgewidth=1.5, zorder=4, label="सर्वअष्टकवर्ग विन्दु (SAV Points)")

            # Add numeric value badges on each vertex
            for ang, val in zip(angles[:-1], sav):
                badge_col = "#15803d" if val >= 28 else "#b91c1c"
                ax2.annotate(
                    f"{int(val)}",
                    xy=(ang, val),
                    xytext=(0, 7),
                    textcoords="offset points",
                    ha="center", va="center",
                    fontsize=9.5, fontweight="bold",
                    color=badge_col,
                    bbox=dict(boxstyle="circle,pad=0.2", facecolor="#ffffff", edgecolor=badge_col, alpha=0.9, linewidth=1.2),
                    zorder=5
                )

            ax2.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)
            fig2.tight_layout()

            canvas2 = FigureCanvas(fig2)
            canvas2.setMinimumHeight(440)
            cl2.addWidget(canvas2)
            self._c_layout.addWidget(card2)

        # ── 3. 3D-Enhanced Stacked Shadbala Component Breakdown ────────────────
        if self._model["breakdown"]:
            card3 = QFrame()
            card3.setStyleSheet("background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;")
            cl3 = QVBoxLayout(card3)
            cl3.setContentsMargins(16, 16, 16, 16)
            cl3.setSpacing(10)

            t3 = QLabel("🔬 " + ("षड्बल ६ घटक विस्तृत विभाजन (3D Stacked Component Breakdown)" if self._is_ne else "Shadbala 6-Fold Component Composition"))
            t3.setStyleSheet("color: #7c3d00; font-size: 16px; font-weight: 700;")
            cl3.addWidget(t3)

            sub3 = QLabel("प्रत्येक ग्रहको ६ प्रकारका बलहरूको अनुपात (स्थान, दिग्, काल, चेष्टा, नैसर्गिक, दृक् बल)")
            sub3.setStyleSheet("color: #64748b; font-size: 12px;")
            cl3.addWidget(sub3)

            rows = self._model["breakdown"]
            p_names_en = [row["name"] for row in rows]
            p_labels = [PLANET_NEP_NAMES.get(name, name) if self._is_ne else name for name in p_names_en]
            
            fig3, ax3 = plt.subplots(figsize=(9, 4.6), dpi=110, facecolor="#ffffff")
            ax3.set_facecolor("#fafbfc")

            x_pos = np.arange(len(p_labels))
            bar_width = 0.52
            bottoms = np.zeros(len(rows))

            component_colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
            
            for key, color in zip(COMPONENT_KEYS, component_colors):
                values = np.array([row[key] for row in rows])
                label_ne = COMPONENT_NEP_NAMES.get(key, key.title()) if self._is_ne else key.title()
                
                # Stacked bar with border
                ax3.bar(
                    x_pos, values,
                    bottom=bottoms,
                    label=label_ne,
                    color=color,
                    edgecolor="#ffffff",
                    linewidth=1.0,
                    width=bar_width,
                    alpha=0.92,
                    zorder=3
                )
                bottoms += values

            # Total on top of stacked bar
            for x, tot in zip(x_pos, bottoms):
                ax3.text(
                    x, tot + 8,
                    f"{tot:.0f}",
                    ha="center", va="bottom",
                    fontsize=9.5, fontweight="bold",
                    color="#1e293b", zorder=5
                )

            ax3.set_xticks(x_pos)
            ax3.set_xticklabels(p_labels, fontsize=11, fontweight="bold", color="#1e293b")
            ax3.set_ylabel("शष्ट्यंश विन्दु (Total Points)", fontsize=10, fontweight="bold", color="#475569")
            ax3.set_ylim(0, max(bottoms) * 1.18)

            ax3.grid(axis="y", color="#e2e8f0", linestyle="--", linewidth=0.8, alpha=0.8, zorder=1)
            ax3.set_axisbelow(True)

            for spine in ax3.spines.values():
                spine.set_color("#cbd5e1")
                spine.set_linewidth(1)

            ax3.legend(
                loc="upper center", bbox_to_anchor=(0.5, 1.15),
                ncol=6, framealpha=0.95, facecolor="#ffffff", edgecolor="#cbd5e1",
                fontsize=8.5
            )
            fig3.tight_layout()

            canvas3 = FigureCanvas(fig3)
            canvas3.setMinimumHeight(400)
            cl3.addWidget(canvas3)
            self._c_layout.addWidget(card3)
