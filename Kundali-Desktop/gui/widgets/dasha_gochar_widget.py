# -*- coding: utf-8 -*-
"""
gui/widgets/dasha_gochar_widget.py
Comprehensive Dasha-Gochar Monthly Chart & Timeline Widget
Features:
- "📈 दशा तथा गोचर समयरेखा" shows pure continuous planetary trajectory lines across the 12 signs.
- "📅 दशा-गोचर मासिक चार्ट" shows the Jagannatha Hora style monthly transit grid chart.
- Mode switcher allows toggling between both seamlessly.
- Interactive Date Click: Clicking any date (गते) moves the selection line and updates the active day immediately.
- Full-Width Responsive Layout: Auto-expands to fill the entire window width with zero wasted empty space.
"""
from __future__ import annotations
import sys
import os
import math
import datetime
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QScrollArea, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QPainterPath)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.utils.planet_colors import PLANET_ABBR, RASHI_NAMES, to_nepali_digits
from gui.utils.bs_calendar import gregorian_to_bs, BS_MONTHS_NE

# ── Planet definitions ───────────────────────────────────────────────────────
PLANETS_ALL = [
    {"id": "Sun",     "ne": "सू", "en": "Su", "color": "#e53e3e"},
    {"id": "Moon",    "ne": "चं", "en": "Mo", "color": "#1a202c"},
    {"id": "Mars",    "ne": "मं", "en": "Ma", "color": "#dd6b20"},
    {"id": "Mercury", "ne": "बु", "en": "Me", "color": "#276749"},
    {"id": "Jupiter", "ne": "गु", "en": "Ju", "color": "#b7791f"},
    {"id": "Venus",   "ne": "शु", "en": "Ve", "color": "#d53f8c"},
    {"id": "Saturn",  "ne": "श",  "en": "Sa", "color": "#4c51bf"},
    {"id": "Rahu",    "ne": "रा", "en": "Ra", "color": "#6b7280"},
    {"id": "Ketu",    "ne": "के", "en": "Ke", "color": "#92400e"},
]

# ── Sidereal Longitude Calculations (Lahiri) ─────────────────────────────────
def _gregorian_to_jd(y: int, m: int, d: int) -> float:
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5

def _lahiri(jd: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    return 23.85 + 50.3 * T / 3600.0 + (0.000271 * T * T) / 3600.0

def _sidereal_lon(planet_id: str, jd: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    lon = {
        "Sun":     (280.46646 + 36000.76983 * T) % 360,
        "Moon":    (218.3165  + 481267.8813 * T) % 360,
        "Mars":    (355.433   + 19140.2993  * T) % 360,
        "Mercury": (252.251   + 149472.674  * T) % 360,
        "Jupiter": (34.351    + 3034.906    * T) % 360,
        "Venus":   (181.979   + 58517.815   * T) % 360,
        "Saturn":  (50.077    + 1222.114    * T) % 360,
        "Rahu":    (125.045   - 1934.136    * T + 360000) % 360,
        "Ketu":    (305.045   - 1934.136    * T + 360000) % 360,
    }.get(planet_id, 0)
    return (lon - _lahiri(jd) + 3600) % 360

def _get_dasha_at(dasha_data: list, target: datetime.date) -> dict:
    for maha in (dasha_data or []):
        try:
            ms = datetime.date.fromisoformat(maha["start"][:10])
            me = datetime.date.fromisoformat(maha["end"][:10])
        except Exception:
            continue
        if not (ms <= target <= me):
            continue
        for antar in maha.get("children", []):
            try:
                as_ = datetime.date.fromisoformat(antar["start"][:10])
                ae  = datetime.date.fromisoformat(antar["end"][:10])
            except Exception:
                continue
            if not (as_ <= target <= ae):
                continue
            for pratya in antar.get("children", []):
                try:
                    ps = datetime.date.fromisoformat(pratya["start"][:10])
                    pe = datetime.date.fromisoformat(pratya["end"][:10])
                except Exception:
                    continue
                if ps <= target <= pe:
                    return {"ma": maha["lord"], "ad": antar["lord"], "pa": pratya["lord"]}
            return {"ma": maha["lord"], "ad": antar["lord"], "pa": None}
        return {"ma": maha["lord"], "ad": None, "pa": None}
    return {}


ROW_H  = 22
HDR_H  = 38
LEFT_W = 210
LABEL_W = 32

# ── Left Panel (Dasha List with Clickable Date Selection) ────────────────────
class DashaLeftPanel(QWidget):
    daySelected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._lang = "ne"
        self._selected_day = 1
        self.setFixedWidth(LEFT_W)
        self.setCursor(Qt.PointingHandCursor)

    def set_data(self, rows: list, lang: str, selected_day: int):
        self._rows = rows
        self._lang = lang
        self._selected_day = selected_day
        self.setFixedHeight(HDR_H + len(rows) * ROW_H)
        self.update()

    def set_selected_day(self, d: int):
        self._selected_day = d
        self.update()

    def mousePressEvent(self, event):
        y = event.pos().y()
        if y >= HDR_H:
            idx = int((y - HDR_H) // ROW_H)
            if 0 <= idx < len(self._rows):
                clicked_day = self._rows[idx]["d"]
                self.daySelected.emit(clicked_day)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        is_ne = self._lang == "ne"
        abbr = PLANET_ABBR.get(self._lang, PLANET_ABBR["ne"])

        # Header background
        p.fillRect(0, 0, LEFT_W, HDR_H, QColor("#e0f2fe"))
        p.setPen(QPen(QColor("#94a3b8"), 1))
        p.drawLine(0, HDR_H - 1, LEFT_W, HDR_H - 1)
        p.drawLine(LEFT_W - 1, 0, LEFT_W - 1, self.height())

        f_hdr = QFont("Segoe UI", 9)
        f_hdr.setBold(True)
        p.setFont(f_hdr)
        p.setPen(QColor("#0369a1"))

        # Columns
        p.drawText(QRectF(0, 0, 38, HDR_H), Qt.AlignCenter, "गते" if is_ne else "BS")
        p.drawText(QRectF(38, 0, 36, HDR_H), Qt.AlignCenter, "वार" if is_ne else "Day")
        p.drawText(QRectF(74, 0, LEFT_W - 76, HDR_H), Qt.AlignCenter, "महा · अन्तर् · प्रत्य" if is_ne else "MD · AD · PD")

        p.setPen(QPen(QColor("#cbd5e1"), 1))
        p.drawLine(38, 0, 38, self.height())
        p.drawLine(74, 0, 74, self.height())

        f_row = QFont("Segoe UI", 9)
        p.setFont(f_row)

        for i, row in enumerate(self._rows):
            y = HDR_H + i * ROW_H
            is_today = row.get("is_today", False)
            is_selected = row.get("d") == self._selected_day

            # Row background
            if is_selected:
                bg = QColor("#fef3c7")  # Highlighted selected day
            elif is_today:
                bg = QColor("#ecfdf5")
            elif i % 2 == 1:
                bg = QColor("#f8fafc")
            else:
                bg = QColor("#ffffff")
            p.fillRect(0, y, LEFT_W, ROW_H, bg)

            p.setPen(QPen(QColor("#e2e8f0"), 1))
            p.drawLine(0, y + ROW_H - 1, LEFT_W, y + ROW_H - 1)

            # Active selection left bar
            if is_selected:
                p.fillRect(0, y, 4, ROW_H, QColor("#d97706"))

            # Date (BS)
            bs_day = row.get("bs_day", str(row["d"]))
            f_day = QFont("Segoe UI", 9)
            f_day.setBold(is_selected or is_today)
            p.setFont(f_day)
            p.setPen(QColor("#b45309" if is_selected else ("#047857" if is_today else "#0f172a")))
            p.drawText(QRectF(0, y, 38, ROW_H), Qt.AlignCenter, bs_day)

            # Day of week
            day_names_ne = ["आइत", "सोम", "मंग", "बुध", "बिही", "शुक्र", "शनि"]
            day_name = day_names_ne[row["date"].weekday()] if is_ne else row["date"].strftime("%a")
            p.setPen(QColor("#64748b"))
            p.setFont(f_row)
            p.drawText(QRectF(38, y, 36, ROW_H), Qt.AlignCenter, day_name)

            # Dasha sequence
            d = row.get("dasha", {})
            ma_id = d.get("ma")
            ad_id = d.get("ad")
            pa_id = d.get("pa")

            if ma_id:
                x_pos = 80
                ma_color = next((pl["color"] for pl in PLANETS_ALL if pl["id"] == ma_id), "#0f172a")
                p.setPen(QColor(ma_color))
                f_d = QFont("Segoe UI", 9)
                f_d.setBold(True)
                p.setFont(f_d)
                ma_str = abbr.get(ma_id, ma_id[:2])
                p.drawText(QRectF(x_pos, y, 30, ROW_H), Qt.AlignVCenter | Qt.AlignLeft, ma_str)
                x_pos += 26

                if ad_id:
                    p.setPen(QColor("#94a3b8"))
                    p.drawText(QRectF(x_pos, y, 8, ROW_H), Qt.AlignCenter, "-")
                    x_pos += 8

                    ad_color = next((pl["color"] for pl in PLANETS_ALL if pl["id"] == ad_id), "#0f172a")
                    p.setPen(QColor(ad_color))
                    ad_str = abbr.get(ad_id, ad_id[:2])
                    p.drawText(QRectF(x_pos, y, 30, ROW_H), Qt.AlignVCenter | Qt.AlignLeft, ad_str)
                    x_pos += 26

                    if pa_id:
                        p.setPen(QColor("#94a3b8"))
                        p.drawText(QRectF(x_pos, y, 8, ROW_H), Qt.AlignCenter, "-")
                        x_pos += 8

                        pa_color = next((pl["color"] for pl in PLANETS_ALL if pl["id"] == pa_id), "#0f172a")
                        p.setPen(QColor(pa_color))
                        pa_str = abbr.get(pa_id, pa_id[:2])
                        p.drawText(QRectF(x_pos, y, 30, ROW_H), Qt.AlignVCenter | Qt.AlignLeft, pa_str)
            else:
                p.setPen(QColor("#94a3b8"))
                p.drawText(QRectF(80, y, 80, ROW_H), Qt.AlignVCenter | Qt.AlignLeft, "—")

        p.end()


# ── Right Panel: Responsive Transit Chart (Supports both Grid & Line Modes) ──
class ResponsiveTransitChart(QWidget):
    daySelected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._lang = "ne"
        self._selected_day = 1
        self._view_mode = "grid"  # "grid" or "timeline"
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

    def set_data(self, rows: list, lang: str, selected_day: int, view_mode: str = "grid"):
        self._rows = rows
        self._lang = lang
        self._selected_day = selected_day
        self._view_mode = view_mode
        self.setFixedHeight(HDR_H + len(rows) * ROW_H)
        self.update()

    def set_selected_day(self, d: int):
        self._selected_day = d
        self.update()

    def set_view_mode(self, mode: str):
        self._view_mode = mode
        self.update()

    def mousePressEvent(self, event):
        y = event.pos().y()
        if y >= HDR_H:
            idx = int((y - HDR_H) // ROW_H)
            if 0 <= idx < len(self._rows):
                clicked_day = self._rows[idx]["d"]
                self.daySelected.emit(clicked_day)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        is_ne = self._lang == "ne"
        rashi_names = RASHI_NAMES.get(self._lang, RASHI_NAMES["ne"])
        abbr = PLANET_ABBR.get(self._lang, PLANET_ABBR["ne"])

        total_w = self.width()
        total_h = HDR_H + len(self._rows) * ROW_H

        col_w = max(52.0, (total_w - LABEL_W) / 12.0)

        # ── १. राशि पृष्ठभूमि (Rashi Backgrounds) ──
        for r in range(12):
            x = LABEL_W + r * col_w
            bg = QColor("#fee2e2" if r % 2 == 0 else "#e0f2fe")
            p.fillRect(QRectF(x, HDR_H, col_w, total_h - HDR_H), bg)

        # ── २. बायाँ दिन स्तम्भ ──
        p.fillRect(0, HDR_H, LABEL_W, total_h - HDR_H, QColor("#f1f5f9"))

        # ── ३. ग्रिड रेखाहरू (Day Separators & Column Lines) ──
        for i in range(len(self._rows) + 1):
            y = HDR_H + i * ROW_H
            p.setPen(QPen(QColor("#cbd5e1"), 0.75))
            p.drawLine(0, y, total_w, y)

        for r in range(13):
            x = LABEL_W + r * col_w
            p.setPen(QPen(QColor("#cbd5e1"), 1))
            p.drawLine(x, 0, x, total_h)

        # ── ४. शीर्ष स्तम्भ शीर्षक (Header Bar: 12 Rashis) ──
        p.fillRect(0, 0, total_w, HDR_H, QColor("#e0f2fe"))
        p.fillRect(0, 0, LABEL_W, HDR_H, QColor("#bae6fd"))

        p.setPen(QPen(QColor("#94a3b8"), 1))
        p.drawLine(0, HDR_H - 1, total_w, HDR_H - 1)
        p.drawLine(LABEL_W, 0, LABEL_W, total_h)

        f_hdr = QFont("Segoe UI", 9)
        f_hdr.setBold(True)
        p.setFont(f_hdr)
        p.setPen(QColor("#0369a1"))

        p.drawText(QRectF(0, 0, LABEL_W, HDR_H), Qt.AlignCenter, "गते" if is_ne else "BS")

        for r in range(12):
            x = LABEL_W + r * col_w
            r_name = rashi_names[r]
            p.drawText(QRectF(x, 0, col_w, HDR_H), Qt.AlignCenter, r_name)

        # ── ५. बायाँ दिन नम्बर (Day Digits) ──
        f_day = QFont("Segoe UI", 8)
        p.setFont(f_day)
        p.setPen(QColor("#475569"))
        for i, row in enumerate(self._rows):
            y = HDR_H + i * ROW_H
            is_selected = row.get("d") == self._selected_day
            bs_day = row.get("bs_day", str(row["d"]))
            if is_selected:
                p.fillRect(0, y, LABEL_W, ROW_H, QColor("#fef3c7"))
                p.setPen(QColor("#b45309"))
                f_sel = QFont("Segoe UI", 8)
                f_sel.setBold(True)
                p.setFont(f_sel)
            else:
                p.setPen(QColor("#475569"))
                p.setFont(f_day)
            p.drawText(QRectF(0, y, LABEL_W - 4, ROW_H), Qt.AlignRight | Qt.AlignVCenter, bs_day)

        # ── ६. मोड १: 📅 मासिक ग्रिड चार्ट (Monthly Grid Chart) ──
        if self._view_mode == "grid":
            f_p = QFont("Segoe UI", 8)
            f_p.setBold(True)
            p.setFont(f_p)

            for i, row in enumerate(self._rows):
                y = HDR_H + i * ROW_H
                is_selected = row.get("d") == self._selected_day

                planets_data = row.get("planets", {})
                rashi_planets: Dict[int, list] = {r: [] for r in range(12)}
                for pid, pinfo in planets_data.items():
                    r = pinfo.get("rashi", 0)
                    rashi_planets[r].append((pid, pinfo))

                for r, p_list in rashi_planets.items():
                    if not p_list:
                        continue
                    x_base = LABEL_W + r * col_w
                    p_count = len(p_list)
                    slot_w = col_w / max(1, p_count)

                    for idx, (pid, pinfo) in enumerate(p_list):
                        p_color_hex = next((pl["color"] for pl in PLANETS_ALL if pl["id"] == pid), "#0f172a")
                        p.setPen(QPen(QColor(p_color_hex), 1))
                        p_abbr_str = abbr.get(pid, pid[:2])
                        deg_val = pinfo.get("deg", 0)
                        deg_str = f"{to_nepali_digits(int(deg_val))}°" if is_ne else f"{int(deg_val)}°"

                        if slot_w >= 32:
                            disp_text = f"{p_abbr_str} {deg_str}"
                        else:
                            disp_text = p_abbr_str

                        p.drawText(QRectF(x_base + idx * slot_w, y, slot_w, ROW_H), Qt.AlignCenter, disp_text)

        # ── ७. मोड २: 📈 समय रेखा ग्राफ (Timeline Trajectory Polylines) ──
        else:
            for planet in PLANETS_ALL:
                pid = planet["id"]
                p_color = QColor(planet["color"])
                p_abbr_str = abbr.get(pid, pid[:2])

                points: List[Tuple[float, float, int, float, int]] = []
                for i, row in enumerate(self._rows):
                    p_info = row.get("planets", {}).get(pid, {})
                    rashi = p_info.get("rashi", 0)
                    deg = p_info.get("deg", 0.0)

                    px = LABEL_W + rashi * col_w + (deg / 30.0) * col_w
                    py = HDR_H + (i + 0.5) * ROW_H
                    points.append((px, py, rashi, deg, i))

                if len(points) < 2:
                    continue

                segments: List[List[Tuple[float, float, int, float, int]]] = [[]]
                for idx, pt in enumerate(points):
                    if idx == 0:
                        segments[-1].append(pt)
                    else:
                        prev_pt = points[idx - 1]
                        if abs(pt[0] - prev_pt[0]) > col_w * 6:
                            segments.append([pt])
                        else:
                            segments[-1].append(pt)

                pen = QPen(p_color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)

                for seg in segments:
                    if len(seg) >= 2:
                        path = QPainterPath()
                        path.moveTo(seg[0][0], seg[0][1])
                        for pt in seg[1:]:
                            path.lineTo(pt[0], pt[1])
                        p.drawPath(path)

                f_lbl = QFont("Segoe UI", 8)
                f_lbl.setBold(True)
                p.setFont(f_lbl)

                for idx, pt in enumerate(points):
                    is_first = idx == 0
                    rashi_changed = idx > 0 and points[idx - 1][2] != pt[2]
                    if is_first or rashi_changed:
                        badge_x = pt[0] - 8
                        badge_y = pt[1] - 8
                        p.setPen(Qt.NoPen)
                        p.setBrush(QBrush(QColor("#ffffff")))
                        p.drawEllipse(QRectF(badge_x - 1, badge_y - 1, 18, 18))

                        p.setBrush(QBrush(p_color))
                        p.drawEllipse(QRectF(badge_x, badge_y, 16, 16))

                        p.setPen(QColor("#ffffff"))
                        p.drawText(QRectF(badge_x - 2, badge_y - 2, 20, 20), Qt.AlignCenter, p_abbr_str)

        # ── ८. चयनित दिन वा आजको रेखा (Selection Marker) ──
        for i, row in enumerate(self._rows):
            if row.get("d") == self._selected_day:
                sy = HDR_H + (i + 0.5) * ROW_H
                p.setPen(QPen(QColor("#d97706"), 2.0, Qt.SolidLine))
                p.drawLine(0, sy, total_w, sy)

                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(QColor("#d97706")))
                p.drawRoundedRect(QRectF(2, sy - 9, 28, 18), 3, 3)
                p.setPen(QColor("#ffffff"))
                f_sel = QFont("Segoe UI", 8)
                f_sel.setBold(True)
                p.setFont(f_sel)
                p.drawText(QRectF(2, sy - 9, 28, 18), Qt.AlignCenter, "गते")
                break

        p.end()


# ── Main Page Component ──────────────────────────────────────────────────────
class DashaGocharPage(QWidget):
    def __init__(self, data: Optional[dict], language: str = "ne", default_mode: str = "grid", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._view_year  = datetime.date.today().year
        self._view_month = datetime.date.today().month
        self._selected_day = datetime.date.today().day
        self._view_mode = default_mode  # "grid" for monthly chart, "timeline" for transit timeline
        self._row_data = []

        self._build_ui()
        if data:
            self.refresh(data)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QFrame.NoFrame)
        main_scroll.setStyleSheet("QScrollArea { background: #ffffff; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: #ffffff; color: #0f172a;")
        self._page_layout = QVBoxLayout(container)
        self._page_layout.setContentsMargins(24, 16, 24, 30)
        self._page_layout.setSpacing(14)

        # ── १. शीर्ष शीर्षक एवं भ्यू स्विचर ──
        hdr = QHBoxLayout()
        page_title_str = "📈 दशा तथा गोचर समयरेखा (Timeline)" if self._view_mode == "timeline" else "📅 दशा-गोचर मासिक चार्ट (Monthly Chart)"
        self._title_lbl = QLabel(page_title_str)
        self._title_lbl.setStyleSheet("color: #0f172a; font-size: 20px; font-weight: 800;")
        hdr.addWidget(self._title_lbl)
        hdr.addStretch()

        # View Mode Toggle Buttons
        mode_frame = QFrame()
        mode_frame.setStyleSheet("background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 2px;")
        mode_hbox = QHBoxLayout(mode_frame)
        mode_hbox.setContentsMargins(2, 2, 2, 2)
        mode_hbox.setSpacing(4)

        self._grid_btn = QPushButton("📅 मासिक चार्ट (Grid)")
        self._grid_btn.setCheckable(True)
        self._grid_btn.setChecked(self._view_mode == "grid")
        self._grid_btn.setStyleSheet("""
            QPushButton {
                background: #0284c7; color: white; border: none; border-radius: 4px; padding: 5px 12px; font-weight: bold; font-size: 13px;
            }
            QPushButton:!checked {
                background: transparent; color: #334155;
            }
        """)
        self._grid_btn.clicked.connect(lambda: self._switch_mode("grid"))
        mode_hbox.addWidget(self._grid_btn)

        self._line_btn = QPushButton("📈 समय रेखा (Timeline)")
        self._line_btn.setCheckable(True)
        self._line_btn.setChecked(self._view_mode == "timeline")
        self._line_btn.setStyleSheet("""
            QPushButton {
                background: #0284c7; color: white; border: none; border-radius: 4px; padding: 5px 12px; font-weight: bold; font-size: 13px;
            }
            QPushButton:!checked {
                background: transparent; color: #334155;
            }
        """)
        self._line_btn.clicked.connect(lambda: self._switch_mode("timeline"))
        mode_hbox.addWidget(self._line_btn)

        hdr.addWidget(mode_frame)
        self._page_layout.addLayout(hdr)

        sub_title = QLabel(
            "प्रत्येक दिनको सक्रिय विंशोत्तरी दशा (महादशा, अन्तर्दशा, प्रत्यन्तर) र ९ वटै ग्रहहरूको तात्कालिक राशि गोचर स्थिति। कुनै पनि गतेमा क्लिक गरी सो दिनको प्रभाव हेर्न सक्नुहुन्छ।"
        )
        sub_title.setWordWrap(True)
        sub_title.setStyleSheet("font-size: 13px; color: #475569; margin-bottom: 2px;")
        self._page_layout.addWidget(sub_title)

        # ── २. महिना नेभिगेसन, ग्रह संकेत एवं चयनित दिन ब्यानर ──
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 14px;")
        nav_vbox = QVBoxLayout(nav_frame)
        nav_vbox.setSpacing(8)

        nav_row1 = QHBoxLayout()
        self._prev_btn = QPushButton("◀ अघिल्लो महिना")
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.setStyleSheet("background: #0284c7; color: white; border-radius: 4px; padding: 6px 14px; font-weight: bold; font-size: 13px;")
        self._prev_btn.clicked.connect(self._prev_month)
        nav_row1.addWidget(self._prev_btn)

        self._month_label = QLabel("")
        self._month_label.setAlignment(Qt.AlignCenter)
        self._month_label.setMinimumWidth(160)
        self._month_label.setStyleSheet("color: #0f172a; font-size: 16px; font-weight: 800;")
        nav_row1.addWidget(self._month_label)

        self._next_btn = QPushButton("पछिल्लो महिना ▶")
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setStyleSheet("background: #0284c7; color: white; border-radius: 4px; padding: 6px 14px; font-weight: bold; font-size: 13px;")
        self._next_btn.clicked.connect(self._next_month)
        nav_row1.addWidget(self._next_btn)

        nav_row1.addStretch()

        # Planet Legend
        legend_lbl = QLabel("<b>ग्रह संकेत:</b>")
        legend_lbl.setStyleSheet("font-size: 12px; color: #334155; margin-right: 4px;")
        nav_row1.addWidget(legend_lbl)

        for planet in PLANETS_ALL:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {planet['color']}; font-size: 13px;")
            abbr = planet["ne"] if self._is_ne else planet["en"]
            abbr_lbl = QLabel(abbr)
            abbr_lbl.setStyleSheet(f"color: {planet['color']}; font-size: 11px; font-weight: 800; margin-right: 6px;")
            nav_row1.addWidget(dot)
            nav_row1.addWidget(abbr_lbl)

        nav_vbox.addLayout(nav_row1)

        # Selected Date Info Bar
        self._status_bar = QLabel("")
        self._status_bar.setStyleSheet("background: #fef3c7; border: 1px solid #f59e0b; border-radius: 4px; padding: 5px 10px; font-size: 13px; color: #92400e; font-weight: 600;")
        nav_vbox.addWidget(self._status_bar)

        self._page_layout.addWidget(nav_frame)

        # ── ३. मुख्य चार्ट कन्टेनर (Full Width Responsive) ──
        chart_outer = QFrame()
        chart_outer.setStyleSheet("background: white; border: 1.5px solid #cbd5e1; border-radius: 8px;")
        chart_outer_layout = QHBoxLayout(chart_outer)
        chart_outer_layout.setContentsMargins(0, 0, 0, 0)
        chart_outer_layout.setSpacing(0)

        self._dasha_panel = DashaLeftPanel()
        self._dasha_panel.daySelected.connect(self._on_day_selected)

        self._transit_chart = ResponsiveTransitChart()
        self._transit_chart.daySelected.connect(self._on_day_selected)

        chart_outer_layout.addWidget(self._dasha_panel)
        chart_outer_layout.addWidget(self._transit_chart, 1)

        self._page_layout.addWidget(chart_outer)

        # ── ४. प्रयोगकर्ता निर्देशिका ──
        self._build_interpretation_guide(self._page_layout)

        main_scroll.setWidget(container)
        main_layout.addWidget(main_scroll)

    def _switch_mode(self, mode: str):
        self._view_mode = mode
        self._grid_btn.setChecked(mode == "grid")
        self._line_btn.setChecked(mode == "timeline")
        self._transit_chart.set_view_mode(mode)
        page_title_str = "📈 दशा तथा गोचर समयरेखा (Timeline)" if mode == "timeline" else "📅 दशा-गोचर मासिक चार्ट (Monthly Chart)"
        self._title_lbl.setText(page_title_str)

    def _on_day_selected(self, day: int):
        self._selected_day = day
        self._dasha_panel.set_selected_day(day)
        self._transit_chart.set_selected_day(day)
        self._update_status_bar()

    def _update_status_bar(self):
        if not self._row_data:
            return
        row = next((r for r in self._row_data if r["d"] == self._selected_day), self._row_data[0])
        bs = row.get("bs")
        bs_str = f"वि.सं. {to_nepali_digits(bs['year'])}/{to_nepali_digits(bs['month'])}/{to_nepali_digits(bs['day'])}" if bs else str(row["date"])
        day_names_ne = ["आइतबार", "सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"]
        w_day = day_names_ne[row["date"].weekday()] if self._is_ne else row["date"].strftime("%A")

        d = row.get("dasha", {})
        abbr = PLANET_ABBR.get(self._lang, PLANET_ABBR["ne"])
        ma = abbr.get(d.get("ma", ""), "-")
        ad = abbr.get(d.get("ad", ""), "-")
        pa = abbr.get(d.get("pa", ""), "-")

        self._status_bar.setText(
            f"📍 <b>चयनित मिति:</b> {bs_str} ({w_day}) &nbsp;|&nbsp; "
            f"<b>दशा प्रभाव:</b> महादशा: <b>{ma}</b> &nbsp;·&nbsp; अन्तर्दशा: <b>{ad}</b> &nbsp;·&nbsp; प्रत्यन्तर: <b>{pa}</b> &nbsp;&nbsp; <i>(अन्य गतेमा क्लिक गरी परिवर्तन गर्न सक्नुहुन्छ)</i>"
        )

    def _build_interpretation_guide(self, parent_layout: QVBoxLayout):
        # Bottom-pinned guide button only. The guide text itself lives in the
        # shared "मद्दत" User Guide dialog, so the chart keeps the full page.
        _guide_btn = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn.setObjectName("dashaGocharGuideBox")
        _guide_btn.setToolTip("दशा-गोचर निर्देशिका" if self._is_ne else "Dasha-Gochar guide")
        _guide_btn.setCursor(Qt.PointingHandCursor)
        _guide_btn.setStyleSheet(
            "QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; "
            "border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } "
            "QPushButton:hover { background: #bae6fd; }"
        )

        def _open_dasha_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_dasha_gochar_view")

        _guide_btn.clicked.connect(_open_dasha_guide)
        parent_layout.addWidget(_guide_btn)

    def refresh(self, data: dict) -> None:
        self._data = data
        self._rebuild_month_view()

    def _rebuild_month_view(self):
        if not self._data:
            return

        y, m = self._view_year, self._view_month
        days_in_month = (datetime.date(y + (m // 12), (m % 12) + 1, 1) - datetime.date(y, m, 1)).days

        today = datetime.date.today()
        bs1   = gregorian_to_bs(y, m, 1)
        bs_end = gregorian_to_bs(y, m, days_in_month)
        if bs1:
            if bs1.get("month") == (bs_end or {}).get("month"):
                m_label = f"{BS_MONTHS_NE[bs1['month']-1]} {to_nepali_digits(bs1['year'])}"
            else:
                m_label = (f"{BS_MONTHS_NE[bs1['month']-1]}–"
                           f"{BS_MONTHS_NE[(bs_end or bs1)['month']-1]} "
                           f"{to_nepali_digits(bs1['year'])}")
        else:
            import calendar
            m_label = f"{calendar.month_abbr[m]} {y}"
        self._month_label.setText(m_label)

        rows = []
        dasha_data = self._data.get("dasha", [])
        for d in range(1, days_in_month + 1):
            date = datetime.date(y, m, d)
            jd   = _gregorian_to_jd(y, m, d)
            bs   = gregorian_to_bs(y, m, d)
            bs_day = to_nepali_digits(bs["day"]) if bs else str(d)

            dasha = _get_dasha_at(dasha_data, date)

            planets = {}
            for planet in PLANETS_ALL:
                lon = _sidereal_lon(planet["id"], jd)
                planets[planet["id"]] = {
                    "lon":   lon,
                    "rashi": int(lon / 30) % 12,
                    "deg":   lon % 30,
                }

            rows.append({
                "d":        d,
                "date":     date,
                "bs":       bs,
                "bs_day":   bs_day,
                "is_today": date == today,
                "dasha":    dasha,
                "planets":  planets,
            })

        self._row_data = rows
        if self._selected_day > days_in_month:
            self._selected_day = 1

        self._dasha_panel.set_data(rows, self._lang, self._selected_day)
        self._transit_chart.set_data(rows, self._lang, self._selected_day, self._view_mode)
        self._update_status_bar()

    def _prev_month(self):
        if self._view_month == 1:
            self._view_year -= 1
            self._view_month = 12
        else:
            self._view_month -= 1
        self._rebuild_month_view()

    def _next_month(self):
        if self._view_month == 12:
            self._view_year += 1
            self._view_month = 1
        else:
            self._view_month += 1
        self._rebuild_month_view()
