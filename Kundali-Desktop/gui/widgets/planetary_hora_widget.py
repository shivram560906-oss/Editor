# -*- coding: utf-8 -*-
"""
gui/widgets/planetary_hora_widget.py

Real-time Planetary Hour (Hora) Widget
- Current Hora lord at a glance
- Full 24-hour Hora schedule table
- Auto-refreshes every minute via QTimer
"""
from __future__ import annotations
import datetime
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_GOLD, COLOR_ACCENT, COLOR_ERROR
)

# ── Hora lords in order (starting from Sunrise on Sunday) ─────────────────────
# Weekday (Sun=0, Mon=1, ..., Sat=6) and Hora sequence
HORA_SEQUENCE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
WEEKDAY_FIRST_HORA = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
                      4: "Jupiter", 5: "Venus", 6: "Saturn"}  # Sunday=0

PLANET_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल",
    "Mercury": "बुध", "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि"
}
PLANET_EMOJI = {
    "Sun": "☀️", "Moon": "🌙", "Mars": "♂️",
    "Mercury": "☿", "Jupiter": "♃", "Venus": "♀️", "Saturn": "♄"
}
PLANET_COLOR = {
    "Sun": "#dc2626", "Moon": "#2563eb", "Mars": "#b91c1c",
    "Mercury": "#16a34a", "Jupiter": "#d97706", "Venus": "#c026d3", "Saturn": "#475569"
}
HORA_NATURE = {
    "Sun": ("शुभ", "Good"), "Moon": ("शुभ", "Good"), "Jupiter": ("शुभ", "Good"),
    "Venus": ("शुभ", "Good"), "Mercury": ("मध्यम", "Neutral"),
    "Mars": ("अशुभ", "Inauspicious"), "Saturn": ("अशुभ", "Inauspicious")
}


def _get_hora_lord(weekday: int, hora_index: int) -> str:
    """Get hora lord for given weekday (Sun=0) and hora index (0-23)."""
    first_lord = WEEKDAY_FIRST_HORA.get(weekday, "Sun")
    start_idx = HORA_SEQUENCE.index(first_lord)
    return HORA_SEQUENCE[(start_idx + hora_index) % 7]


def _calculate_horas(latitude: float, longitude: float,
                     timezone: float, target_date: datetime.date) -> list[dict]:
    """
    Calculate all 24 Hora periods for a given date and location.
    Returns list of dicts with start, end, lord, nature.
    Falls back to equal 1-hour Horas if sunrise/sunset calc fails.
    """
    try:
        from backend.calculator import panchang as _p
        # Try to get sunrise/sunset from panchang
        import sys, os
        backend = os.path.join(_ROOT, "backend")
        if backend not in sys.path:
            sys.path.insert(0, backend)
        from calculator.panchang import get_sunrise_sunset
        data = get_sunrise_sunset(target_date, latitude, longitude, timezone)
        sunrise_str = data.get("sunrise") or data.get("sunrise_time")
        sunset_str = data.get("sunset") or data.get("sunset_time")

        def _parse_time(s: str) -> Optional[datetime.time]:
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.datetime.strptime(s, fmt).time()
                except Exception:
                    pass
            return None

        sr = _parse_time(str(sunrise_str)) if sunrise_str else None
        ss = _parse_time(str(sunset_str)) if sunset_str else None
    except Exception:
        sr, ss = None, None

    # Default sunrise/sunset if calc fails
    if sr is None:
        sr = datetime.time(6, 0)
    if ss is None:
        ss = datetime.time(18, 0)

    # Build hora periods
    weekday = target_date.weekday()
    # Python weekday: Mon=0..Sun=6 → convert to Sun=0..Sat=6
    weekday_sun0 = (weekday + 1) % 7

    base = datetime.datetime.combine(target_date, sr)
    sunrise_dt = datetime.datetime.combine(target_date, sr)
    sunset_dt = datetime.datetime.combine(target_date, ss)
    next_sunrise_dt = sunrise_dt + datetime.timedelta(days=1)

    day_minutes = (sunset_dt - sunrise_dt).total_seconds() / 60
    night_minutes = (next_sunrise_dt - sunset_dt).total_seconds() / 60

    day_hora = day_minutes / 12
    night_hora = night_minutes / 12

    horas = []
    hora_idx = 0
    # Day horas (12)
    t = sunrise_dt
    for i in range(12):
        lord = _get_hora_lord(weekday_sun0, hora_idx)
        end = t + datetime.timedelta(minutes=day_hora)
        nature_ne, nature_en = HORA_NATURE.get(lord, ("—", "—"))
        horas.append({
            "start": t,
            "end": end,
            "lord": lord,
            "period": "दिन" if True else "Day",
            "nature_ne": nature_ne,
            "nature_en": nature_en,
        })
        t = end
        hora_idx += 1

    # Night horas (12)
    t = sunset_dt
    for i in range(12):
        lord = _get_hora_lord(weekday_sun0, hora_idx)
        end = t + datetime.timedelta(minutes=night_hora)
        nature_ne, nature_en = HORA_NATURE.get(lord, ("—", "—"))
        horas.append({
            "start": t,
            "end": end,
            "lord": lord,
            "period": "रात",
            "nature_ne": nature_ne,
            "nature_en": nature_en,
        })
        t = end
        hora_idx += 1

    return horas


class PlanetaryHoraWidget(QWidget):
    """
    Real-time Planetary Hora (Hour) Widget.
    Shows current hora lord + full day schedule.
    """

    def __init__(self, language: str = "ne", latitude: float = 27.7172,
                 longitude: float = 85.3240, timezone: float = 5.75, parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._latitude = latitude
        self._longitude = longitude
        self._timezone = timezone
        self._horas: list[dict] = []
        self._build_ui()
        self._refresh()

        # Auto-refresh every 60 seconds
        self._timer = QTimer(self)
        self._timer.setInterval(60_000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ── Header ──
        header = QLabel("🕐 " + ("ग्रह होरा (Planetary Hora)" if self._is_ne else "Planetary Hora"))
        header.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {COLOR_GOLD}; "
            f"border-bottom: 2px solid {BORDER_COLOR}; padding-bottom: 8px;"
        )
        layout.addWidget(header)

        desc = QLabel(
            "वर्तमान ग्रह होरा र दिनभरको होरा तालिका।" if self._is_ne
            else "Current planetary hour and full-day Hora schedule."
        )
        desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        # ── Current Hora Card ──
        self._current_card = QFrame()
        self._current_card.setObjectName("Card")
        self._current_card.setStyleSheet(f"""
            QFrame {{
                background: {BG_TERTIARY};
                border: 2px solid {COLOR_ACCENT};
                border-radius: 12px;
                padding: 4px;
            }}
        """)
        card_layout = QVBoxLayout(self._current_card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(6)

        current_title = QLabel("🌟 " + ("हालको होरा" if self._is_ne else "Current Hora"))
        current_title.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_MUTED}; font-weight: 600;")
        card_layout.addWidget(current_title)

        self._current_lord_lbl = QLabel("—")
        self._current_lord_lbl.setStyleSheet(
            "font-size: 36px; font-weight: 900; color: #1d4ed8;"
        )
        card_layout.addWidget(self._current_lord_lbl)

        self._current_time_lbl = QLabel("—")
        self._current_time_lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SECONDARY};")
        card_layout.addWidget(self._current_time_lbl)

        self._current_nature_lbl = QLabel("—")
        self._current_nature_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600;")
        card_layout.addWidget(self._current_nature_lbl)

        layout.addWidget(self._current_card)

        # ── Hora Table ──
        table_label = QLabel("📋 " + ("आजको सम्पूर्ण होरा तालिका" if self._is_ne else "Today's Full Hora Schedule"))
        table_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(table_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._table_widget = QWidget()
        self._table_grid = QGridLayout(self._table_widget)
        self._table_grid.setSpacing(1)
        self._table_grid.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._table_widget)
        layout.addWidget(scroll, 1)

        # Last updated label
        self._updated_lbl = QLabel("")
        self._updated_lbl.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_MUTED};")
        self._updated_lbl.setAlignment(Qt.AlignRight)
        layout.addWidget(self._updated_lbl)

    def _refresh(self):
        """Recalculate horas and update UI."""
        today = datetime.date.today()
        self._horas = _calculate_horas(self._latitude, self._longitude, self._timezone, today)
        self._update_current()
        self._rebuild_table()
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self._updated_lbl.setText(
            f"अन्तिम अपडेट: {now_str}" if self._is_ne else f"Last updated: {now_str}"
        )

    def _update_current(self):
        """Update the current hora card."""
        now = datetime.datetime.now()
        current = None
        for h in self._horas:
            if h["start"] <= now < h["end"]:
                current = h
                break

        if current is None:
            self._current_lord_lbl.setText("—")
            self._current_time_lbl.setText("")
            self._current_nature_lbl.setText("")
            return

        lord = current["lord"]
        emoji = PLANET_EMOJI.get(lord, "🪐")
        name = (PLANET_NE.get(lord, lord) if self._is_ne else lord)
        color = PLANET_COLOR.get(lord, COLOR_ACCENT)

        self._current_lord_lbl.setText(f"{emoji} {name}")
        self._current_lord_lbl.setStyleSheet(
            f"font-size: 36px; font-weight: 900; color: {color};"
        )

        start_s = current["start"].strftime("%H:%M")
        end_s = current["end"].strftime("%H:%M")
        self._current_time_lbl.setText(
            f"समय: {start_s} — {end_s}" if self._is_ne else f"Time: {start_s} — {end_s}"
        )

        nature = current["nature_ne"] if self._is_ne else current["nature_en"]
        nat_color = "#16a34a" if "शुभ" in nature or "Good" in nature else (
            "#ea580c" if "मध्यम" in nature or "Neutral" in nature else "#dc2626"
        )
        self._current_nature_lbl.setText(
            f"प्रकृति: {nature}" if self._is_ne else f"Nature: {nature}"
        )
        self._current_nature_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {nat_color};")

    def _rebuild_table(self):
        """Rebuild the hora schedule table."""
        # Clear old widgets
        while self._table_grid.count():
            item = self._table_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        now = datetime.datetime.now()
        headers = (
            ["#", "समय", "ग्रह", "अवधि", "प्रकृति"] if self._is_ne
            else ["#", "Time", "Planet", "Period", "Nature"]
        )

        for col, h in enumerate(headers):
            lbl = QLabel(h)
            lbl.setStyleSheet(
                f"background: {COLOR_ACCENT}; color: white; font-weight: 700; "
                f"font-size: 12px; padding: 6px 10px;"
            )
            lbl.setAlignment(Qt.AlignCenter)
            self._table_grid.addWidget(lbl, 0, col)

        for row, hora in enumerate(self._horas, 1):
            is_active = hora["start"] <= now < hora["end"]
            bg = "#dbeafe" if is_active else (BG_SECONDARY if row % 2 == 0 else BG_TERTIARY)
            lord = hora["lord"]
            nature = hora["nature_ne"] if self._is_ne else hora["nature_en"]
            planet_name = PLANET_NE.get(lord, lord) if self._is_ne else lord
            emoji = PLANET_EMOJI.get(lord, "")
            color = PLANET_COLOR.get(lord, COLOR_TEXT_PRIMARY)
            period = hora["period"] if self._is_ne else ("Day" if hora["period"] == "दिन" else "Night")

            cells = [
                str(row),
                f"{hora['start'].strftime('%H:%M')} — {hora['end'].strftime('%H:%M')}",
                f"{emoji} {planet_name}",
                period,
                nature,
            ]
            cell_styles = [None, None, f"color: {color}; font-weight: 700;", None, None]

            for col, (text, extra_style) in enumerate(zip(cells, cell_styles)):
                lbl = QLabel(text)
                lbl.setAlignment(Qt.AlignCenter)
                base_style = f"background: {bg}; padding: 5px 8px; font-size: 12px;"
                if is_active:
                    base_style += f" font-weight: 700; border-left: 3px solid {COLOR_ACCENT};"
                if extra_style:
                    base_style += f" {extra_style}"
                lbl.setStyleSheet(base_style)
                self._table_grid.addWidget(lbl, row, col)

    def update_location(self, latitude: float, longitude: float, timezone: float):
        """Update location and refresh."""
        self._latitude = latitude
        self._longitude = longitude
        self._timezone = timezone
        self._refresh()
