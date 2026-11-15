# -*- coding: utf-8 -*-
"""
gui/widgets/dasha_visual_calendar.py

Dasha–Antardasha Visual Timeline Calendar
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Draws an interactive, colour-coded Gantt-style timeline of
Vimshottari Dasha and Antardasha periods.

Features:
  • Horizontal bar chart — one bar per Maha-Dasha
  • Nested Antardasha bars (visible on hover / click)
  • Current position marker (red vertical line = today)
  • Click any bar → shows period details + planet info
  • Zoom: life-span / 10-year / selected Mahadasha
  • Export as PNG
"""
from __future__ import annotations
import sys, os, datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QSizePolicy, QApplication,
    QToolTip, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QRect, QTimer, Signal, QPoint, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QPainterPath, QPixmap
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED, COLOR_GOLD, COLOR_ACCENT, COLOR_ERROR
)

# ── Dasha planet colours ──────────────────────────────────────────────────────
DASHA_COLORS = {
    "Sun":     "#f97316",
    "Moon":    "#60a5fa",
    "Mars":    "#ef4444",
    "Rahu":    "#8b5cf6",
    "Jupiter": "#f59e0b",
    "Saturn":  "#64748b",
    "Mercury": "#22c55e",
    "Ketu":    "#6b7280",
    "Venus":   "#ec4899",
}

PLANET_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Rahu": "राहु",
    "Jupiter": "बृहस्पति", "Saturn": "शनि", "Mercury": "बुध",
    "Ketu": "केतु", "Venus": "शुक्र"
}


def _to_date(s: str) -> Optional[datetime.date]:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(s[:10], fmt).date()
        except Exception:
            pass
    return None


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ── Timeline canvas ───────────────────────────────────────────────────────────

class DashaTimelineCanvas(QWidget):
    """Custom painted Gantt timeline."""

    period_clicked = Signal(dict)  # emits the clicked period dict

    ROW_H        = 36
    LABEL_W      = 100
    MARGIN_TOP   = 30
    MARGIN_BOT   = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self._periods: list[dict] = []
        self._start_date: Optional[datetime.date] = None
        self._end_date:   Optional[datetime.date] = None
        self._today = datetime.date.today()
        self._hover_idx: int = -1
        self._lang = "ne"
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_data(self, periods: list[dict], lang: str):
        self._periods = periods
        self._lang = lang
        if periods:
            d0 = _to_date(periods[0].get("start_date", ""))
            d1 = _to_date(periods[-1].get("end_date", ""))
            self._start_date = d0
            self._end_date   = d1
        h = self.MARGIN_TOP + len(periods) * self.ROW_H + self.MARGIN_BOT + 10
        self.setMinimumHeight(max(200, h))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        chart_x0 = self.LABEL_W + 8
        chart_w  = w - chart_x0 - 12

        # Background — clean white
        painter.fillRect(self.rect(), QColor("#ffffff"))

        if not self._periods or not self._start_date or not self._end_date:
            painter.setPen(QColor("#64748b"))
            painter.setFont(QFont("Segoe UI", 13, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "कृपया पहिले कुण्डली गणना वा लोड गर्नुहोस्।" if self._lang == "ne" else "Please calculate or load a horoscope chart first.")
            painter.end()
            return

        total_days = (self._end_date - self._start_date).days or 1

        def date_to_x(d: datetime.date) -> float:
            return chart_x0 + chart_w * (d - self._start_date).days / total_days

        # Year grid lines
        painter.setPen(QPen(QColor("#cbd5e1"), 1, Qt.DotLine))
        year = self._start_date.year
        while True:
            try:
                grid_date = datetime.date(year, 1, 1)
            except Exception:
                break
            if grid_date > self._end_date:
                break
            if grid_date >= self._start_date:
                gx = date_to_x(grid_date)
                painter.drawLine(int(gx), self.MARGIN_TOP, int(gx), self.height() - self.MARGIN_BOT)
                painter.setPen(QColor("#64748b"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.drawText(int(gx) + 2, self.MARGIN_TOP - 4, str(year))
                painter.setPen(QPen(QColor("#cbd5e1"), 1, Qt.DotLine))
            year += 1

        # Dasha bars
        for i, period in enumerate(self._periods):
            y = self.MARGIN_TOP + i * self.ROW_H
            sd = _to_date(period.get("start_date", ""))
            ed = _to_date(period.get("end_date", ""))
            planet = period.get("planet", "")
            color  = QColor(DASHA_COLORS.get(planet, "#888"))

            # Label
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.setPen(QColor("#0f172a"))
            name = PLANET_NE.get(planet, planet) if self._lang == "ne" else planet
            painter.drawText(2, y + 2, self.LABEL_W - 4, self.ROW_H - 4, Qt.AlignVCenter | Qt.AlignRight, name)

            if not sd or not ed:
                continue

            x0 = date_to_x(max(sd, self._start_date))
            x1 = date_to_x(min(ed, self._end_date))
            bar_w = max(4.0, x1 - x0)

            # Gradient bar
            grad = QLinearGradient(QPointF(x0, y + 4), QPointF(x0, y + self.ROW_H - 4))
            grad.setColorAt(0, color.lighter(130))
            grad.setColorAt(1, color)
            painter.setBrush(QBrush(grad))

            if i == self._hover_idx:
                painter.setPen(QPen(QColor(COLOR_GOLD), 2))
            else:
                painter.setPen(Qt.NoPen)

            path = QPainterPath()
            path.addRoundedRect(x0, y + 4, bar_w, self.ROW_H - 8, 5, 5)
            painter.drawPath(path)

            # Period label inside bar
            if bar_w > 60:
                years = round((ed - sd).days / 365.25, 1)
                bar_label = f"{years}yr" if self._lang != "ne" else f"{years}वर्ष"
                painter.setPen(QColor("#fff"))
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(int(x0) + 4, y + 4, int(bar_w) - 8, self.ROW_H - 8,
                                 Qt.AlignVCenter | Qt.AlignLeft, bar_label)

        # Today marker
        if self._start_date <= self._today <= self._end_date:
            tx = date_to_x(self._today)
            painter.setPen(QPen(QColor(COLOR_ERROR), 2))
            painter.drawLine(int(tx), self.MARGIN_TOP - 8, int(tx), self.height() - self.MARGIN_BOT)
            painter.setPen(QColor(COLOR_ERROR))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(int(tx) + 3, self.MARGIN_TOP - 10, "आज" if self._lang == "ne" else "Today")

        painter.end()

    def mouseMoveEvent(self, event):
        y = event.pos().y()
        idx = (y - self.MARGIN_TOP) // self.ROW_H
        if 0 <= idx < len(self._periods):
            if idx != self._hover_idx:
                self._hover_idx = idx
                self.update()
            period = self._periods[idx]
            planet = period.get("planet", "")
            name = PLANET_NE.get(planet, planet) if self._lang == "ne" else planet
            sd = period.get("start_date", "")[:10]
            ed = period.get("end_date", "")[:10]
            tip = f"{name}: {sd} → {ed}"
            QToolTip.showText(event.globalPosition().toPoint(), tip, self)
        else:
            self._hover_idx = -1
            self.update()

    def mousePressEvent(self, event):
        y = event.pos().y()
        idx = (y - self.MARGIN_TOP) // self.ROW_H
        if 0 <= idx < len(self._periods):
            self.period_clicked.emit(self._periods[idx])


# ── Main Page ─────────────────────────────────────────────────────────────────

class DashaVisualCalendarPage(QWidget):
    """Full Dasha Visual Calendar page."""

    def __init__(self, chart_data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data
        self._build_ui()
        if chart_data:
            self._load_data()

    def _build_ui(self):
        self.setStyleSheet("background-color: #ffffff;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header
        hdr_row = QHBoxLayout()
        title = QLabel("📅 " + ("दशा भिजुअल क्यालेन्डर (Vimshottari Dasha Timeline)" if self._is_ne else "Dasha Visual Calendar (Vimshottari Timeline)"))
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e3a8a; background: transparent;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()

        export_btn = QPushButton("🖼 " + ("PNG सुरक्षित गर्नुस्" if self._is_ne else "Export PNG"))
        export_btn.setToolTip("Export timeline as PNG image")
        export_btn.setFixedHeight(34)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #94a3b8;
                border-radius: 6px;
                padding: 6px 14px;
                color: #0f172a;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                border-color: #1d4ed8;
                color: #1d4ed8;
                background-color: #f8fafc;
            }
        """)
        export_btn.clicked.connect(self._export_png)
        hdr_row.addWidget(export_btn)
        layout.addLayout(hdr_row)

        # Detail panel
        self._detail_lbl = QLabel(
            "📌 " + ("कुनै पनि दशा बार (Bar) मा क्लिक गर्नुहोस् — त्यसको विस्तृत विवरण र अन्तर्दशाहरू यहाँ देखिनेछ।"
                     if self._is_ne else "Click any Dasha bar to see its detailed duration and Antardashas.")
        )
        self._detail_lbl.setStyleSheet("""
            QLabel {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 12px 14px;
                font-size: 13px;
                color: #334155;
            }
        """)
        self._detail_lbl.setWordWrap(True)
        layout.addWidget(self._detail_lbl)

        # Scroll + canvas
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: 1px solid #cbd5e1; border-radius: 8px; background: #ffffff; }")
        self._canvas = DashaTimelineCanvas()
        self._canvas.period_clicked.connect(self._on_period_clicked)
        self._scroll.setWidget(self._canvas)
        layout.addWidget(self._scroll, 1)

        # Legend
        legend_row = QHBoxLayout()
        legend_row.addWidget(QLabel("🔴 " + ("आज (Today)" if self._is_ne else "Today")))
        for planet, color in DASHA_COLORS.items():
            dot = QFrame()
            dot.setFixedSize(14, 14)
            dot.setStyleSheet(f"background: {color}; border-radius: 7px;")
            legend_row.addWidget(dot)
            name = PLANET_NE.get(planet, planet) if self._is_ne else planet
            lbl = QLabel(name)
            lbl.setStyleSheet("color: #0f172a; font-size: 12px; font-weight: 600; background: transparent;")
            legend_row.addWidget(lbl)
        legend_row.addStretch()
        layout.addLayout(legend_row)

    def _load_data(self):
        if not self._chart_data:
            return
        try:
            backend = os.path.join(_ROOT, "backend")
            if backend not in sys.path:
                sys.path.insert(0, backend)
            # Try to get dasha from chart_data directly
            dasha_data = (
                self._chart_data.get("vimshottari_dasha")
                or self._chart_data.get("dasha")
                or []
            )
            periods = []
            if isinstance(dasha_data, list):
                for item in dasha_data:
                    if isinstance(item, dict) and (item.get("lord") or item.get("planet")):
                        # Normalise to common shape
                        norm = {
                            "planet":     item.get("lord") or item.get("planet", ""),
                            "planet_ne":  item.get("lord_nepali") or item.get("planet_ne", ""),
                            "start_date": item.get("start") or item.get("start_date", ""),
                            "end_date":   item.get("end")   or item.get("end_date",   ""),
                            "start_bs":   item.get("start_bs", ""),
                            "end_bs":     item.get("end_bs", ""),
                            "total_years":item.get("total_years", 0),
                            "is_active":  item.get("is_active", False),
                            "children":   item.get("children", []),
                        }
                        periods.append(norm)
            self._canvas.set_data(periods, self._lang)
        except Exception as exc:
            self._detail_lbl.setText(f"Error: {exc}")

    def refresh(self, chart_data: dict):
        self._chart_data = chart_data
        self._load_data()

    def _on_period_clicked(self, period: dict):
        planet = period.get("planet", "")
        name = PLANET_NE.get(planet, planet) if self._is_ne else planet
        if not name:
            name = period.get("planet_ne", planet)
        sd = (period.get("start_date") or "")[:10]
        ed = (period.get("end_date")   or "")[:10]
        s_bs = period.get("start_bs", "")
        e_bs = period.get("end_bs", "")
        bs_str = f"  |  🇳🇵 वि.सं.: {s_bs} देखि {e_bs}" if (s_bs and e_bs) else ""

        years = period.get("total_years") or round((
            (_to_date(ed) - _to_date(sd)).days
            if _to_date(sd) and _to_date(ed) else 0
        ) / 365.25, 2)
        today = datetime.date.today()
        is_active = _to_date(sd) and _to_date(ed) and _to_date(sd) <= today <= _to_date(ed)
        active_tag = " ✅ सक्रिय महादशा (Active Mahadasha)" if is_active else ""

        lines = [
            f"🪐 {'दशाधिपति' if self._is_ne else 'Dasha Lord'}: {name}{active_tag}",
            f"📅 {'अवधि' if self._is_ne else 'Duration'}: {sd} देखि {ed} ({years} {'वर्ष' if self._is_ne else 'years'}){bs_str}",
        ]

        # Antardashas breakdown if available
        children = period.get("children", [])
        if children:
            sub_strs = []
            for ch in children:
                ch_p = ch.get("lord", "")
                ch_name = PLANET_NE.get(ch_p, ch.get("lord_nepali", ch_p)) if self._is_ne else ch_p
                ch_sd = (ch.get("start") or "")[:10]
                ch_ed = (ch.get("end") or "")[:10]
                ch_bs = f" ({ch.get('start_bs','')} - {ch.get('end_bs','')})" if ch.get("start_bs") else ""
                ch_act = " 🟢" if ch.get("is_active") else ""
                sub_strs.append(f"• {ch_name}: {ch_sd} → {ch_ed}{ch_bs}{ch_act}")
            lines.append("📋 " + ("अन्तर्दशाहरू (Antardashas):" if self._is_ne else "Antardashas:"))
            lines.append("   " + "\n   ".join(sub_strs))

        self._detail_lbl.setText("\n".join(lines))
        border_col = DASHA_COLORS.get(planet, "#1d4ed8")
        self._detail_lbl.setStyleSheet(f"""
            QLabel {{
                background-color: #ffffff;
                border: 2px solid {border_col};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 13px;
                color: #0f172a;
                font-weight: 600;
            }}
        """)

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Dasha Calendar", "dasha_calendar.png", "PNG (*.png)"
        )
        if path:
            pixmap = self._canvas.grab()
            pixmap.save(path)
            QMessageBox.information(self, "Export", f"Saved: {path}")
