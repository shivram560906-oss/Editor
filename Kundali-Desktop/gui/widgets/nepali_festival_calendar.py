# -*- coding: utf-8 -*-
"""
gui/widgets/nepali_festival_calendar.py

Nepali Patro-style Bikram Sambat Monthly Calendar
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A premium, full-featured BS monthly calendar widget modelled after
nepalipatro.com.np.  Replaces the earlier lightweight festival-list widget.

Layout (top to bottom):
  A) Top toolbar   - month heading, navigation arrows, year/month picker,
                     search box, "Jump to today" CTA.
  B) Weekday header row (Sun-Sat, Nepali + English).
  C) Calendar grid (5-6 rows x 7 cols).  Each cell shows:
       - Tithi name (top, small red text)
       - BS date number (large, blue or red for Sat/holiday)
       - AD date badge (top-right circle)
       - Event / holiday text (below date number)
       - Today highlight (orange cell, white text)
  D) Bottom action bar - 4 pill buttons.

Data sources:
  - nepali_datetime  - BS<->AD conversion, month lengths
  - api-nepalicalendar.leapcell.app - PRIMARY: tithi, nakshatra, festivals, holidays (full month in one request)
  - NepaliFestivalEngine - fallback for festivals, government holidays
"""
from __future__ import annotations

import datetime
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import (
    Qt, QSize, Signal, Slot, QThread, QObject,
)
from PySide6.QtGui import (
    QColor, QFont, QFontDatabase, QPainter,
    QPen, QBrush, QCursor,
)
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QTextBrowser, QVBoxLayout, QWidget,
)

# ---- Path bootstrap -------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BACKEND = os.path.join(_ROOT, "backend")
for _p in (_ROOT, _BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gui.utils.bs_calendar import (
    BS_MONTHS_EN, BS_MONTHS_NE, bs_month_length, bs_to_gregorian,
    get_today_bs, gregorian_to_bs, to_nepali_digits,
)

try:
    from calculator.nepali_festival_engine import NepaliFestivalEngine
except Exception:
    NepaliFestivalEngine = None  # type: ignore

try:
    from calculator.nepalicalendar_api import get_month_data, parse_month_data, generate_fallback_month
except Exception:
    get_month_data = None  # type: ignore
    parse_month_data = None  # type: ignore
    generate_fallback_month = None  # type: ignore

logger = logging.getLogger(__name__)

# ---- Nepali month names (colloquial, matching nepalipatro.com.np) ---------
_BS_MONTHS_COLLOQUIAL_NE = [
    "\u092c\u0948\u0936\u093e\u0916", "\u091c\u0947\u0920", "\u0905\u0938\u093e\u0930", "\u0938\u093e\u0909\u0928", "\u092d\u0926\u094c", "\u0905\u0938\u094b\u091c",
    "\u0915\u093e\u0930\u094d\u0924\u093f\u0915", "\u092e\u0902\u0938\u093f\u0930", "\u092a\u0941\u0937", "\u092e\u093e\u0918", "\u092b\u093e\u0917\u0941\u0928", "\u091a\u0948\u0924",
]

_AD_MONTH_NAMES_EN = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

_WEEKDAYS_NE = [
    "\u0906\u0907\u0924\u092c\u093e\u0930", "\u0938\u094b\u092e\u092c\u093e\u0930", "\u092e\u0902\u0917\u0932\u092c\u093e\u0930",
    "\u092c\u0941\u0927\u092c\u093e\u0930", "\u092c\u093f\u0939\u0940\u092c\u093e\u0930", "\u0936\u0941\u0915\u094d\u0930\u092c\u093e\u0930", "\u0936\u0928\u093f\u092c\u093e\u0930",
]
_WEEKDAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# ---- Colour palette -------------------------------------------------------
_C_BG          = "#ffffff"
_C_TOOLBAR_BG  = "#ffffff"
_C_HEADER_BG   = "#f0f4ff"
_C_GRID_BORDER = "#e0e4ec"
_C_TEXT_DARK   = "#1a2040"
_C_TEXT_MUTED  = "#7a8aaa"
_C_BLUE_DATE   = "#1a3580"    # Normal BS date number
_C_RED_DATE    = "#d32f2f"    # Saturday / public holiday date number
_C_TITHI       = "#c0392b"    # Tithi label text
_C_EVENT_HOL   = "#d32f2f"    # Holiday event text
_C_EVENT_NRM   = "#374060"    # Normal event text
_C_TODAY_BG    = "#e85000"    # Today cell background (orange)
_C_TODAY_TEXT  = "#ffffff"    # Today cell all text
_C_SAT_BG      = "#fff5f5"    # Saturday cell tint
_C_HOL_BORDER  = "#f5504a"    # Left border accent on holiday cells
_C_AD_BADGE_BG = "#e8ecf5"    # AD date circle background
_C_AD_BADGE_FG = "#6070a0"    # AD date circle text
_C_CTA_BG      = "#e85000"    # "Today" button background
_C_CTA_FG      = "#ffffff"
_C_MUHURTA     = "#007b80"
_C_CONVERTER   = "#007b80"
_C_HOLIDAYS    = "#2e7d32"
_C_FEEDBACK    = "#c0392b"


def _ne_month_name(month_idx: int) -> str:
    if 1 <= month_idx <= 12:
        return _BS_MONTHS_COLLOQUIAL_NE[month_idx - 1]
    return str(month_idx)


def _ad_span_for_bs_month(bs_year: int, bs_month: int) -> str:
    first = bs_to_gregorian(bs_year, bs_month, 1)
    total = bs_month_length(bs_year, bs_month) or 30
    last  = bs_to_gregorian(bs_year, bs_month, total)
    if not first:
        return ""
    if last and last.month != first.month:
        return (
            f"{_AD_MONTH_NAMES_EN[first.month - 1]}/{_AD_MONTH_NAMES_EN[last.month - 1]}"
            f" {last.year}"
        )
    return f"{_AD_MONTH_NAMES_EN[first.month - 1]} {first.year}"


# --------------------------------------------------------------------------
#  Background data loader
# --------------------------------------------------------------------------

class _MonthDataWorker(QObject):
    """Loads panchang + festival data for every day in a BS month.
    
    Primary source: api-nepalicalendar.leapcell.app (full month in one request)
    Fallback: NepaliFestivalEngine for festivals/holidays
    Fallback 2: Local calculation (generate_fallback_month)

    The payload carries ``_source`` so the page can state where the data came
    from instead of presenting a fallback as if it were the primary source
    (PROJECT_RULES §3.2 - never present data as authoritative when it is not).
    """

    finished = Signal(int, dict)

    def __init__(self, request_id: int, bs_year: int, bs_month: int, engine) -> None:
        super().__init__()
        self._request_id = request_id
        self._year   = bs_year
        self._month  = bs_month
        self._engine = engine

    def run(self) -> None:
        result: Dict[int, Dict[str, Any]] = {}
        
        # Try primary API first
        api_data = None
        if get_month_data:
            try:
                api_data = get_month_data(self._year, self._month, use_cache=True)
            except Exception as e:
                logger.warning("Festival calendar: API fetch failed for %s-%s: %s",
                               self._year, self._month, e)
        
        if api_data and parse_month_data:
            # Parse API response
            try:
                parsed = parse_month_data(api_data)
                for day, data in parsed.items():
                    ad = data.get("ad")
                    if not ad:
                        continue
                    weekday = (ad.weekday() + 1) % 7
                    
                    # Get festivals from API
                    festivals = data.get("festivals", [])
                    
                    # Also try NepaliFestivalEngine as supplement
                    if self._engine:
                        try:
                            engine_fests = self._engine.get_daily_festivals(ad) or []
                            # Merge, avoiding duplicates by name
                            existing_names = {f.get("name_ne") or f.get("name", "") for f in festivals}
                            for ef in engine_fests:
                                ename = ef.get("name_ne") or ef.get("name", "")
                                if ename and ename not in existing_names:
                                    festivals.append(ef)
                                    existing_names.add(ename)
                        except Exception:
                            pass
                    
                    is_holiday = data.get("is_holiday", False)
                    # Also check festivals for holiday type
                    if not is_holiday:
                        is_holiday = any(f.get("type") == "holiday" for f in festivals)
                    
                    result[day] = {
                        "ad":          ad,
                        "weekday":     weekday,
                        "is_saturday": weekday == 6,
                        "festivals":   festivals,
                        "tithi_name":  data.get("tithi_name", ""),
                        "nakshatra_name": data.get("nakshatra_name", ""),
                        "yoga_name":   data.get("yoga_name", ""),
                        "karana_name": data.get("karana_name", ""),
                        "is_holiday":  is_holiday,
                        "sunrise":     data.get("sunrise", ""),
                        "sunset":      data.get("sunset", ""),
                        "rahu_kaal":   data.get("rahu_kaal", ""),
                        "choghadiya":  data.get("choghadiya", ""),
                        "panchang":    {},  # Keep for compatibility
                        # Provenance: shown in the page so a fallback is never
                        # presented as if it came from the primary source.
                        "_source": "nepalicalendar API",
                    }
                self.finished.emit(self._request_id, result)
                return
            except Exception as e:
                logger.warning("Festival calendar: API parse failed for %s-%s: %s",
                               self._year, self._month, e)
                # Fall through to fallback
        
        # Fallback: Use NepaliFestivalEngine + local calculation
        logger.info("Festival calendar: using the local engine for %s-%s",
                    self._year, self._month)
        total = bs_month_length(self._year, self._month) or 30
        fallback_month = {}
        if generate_fallback_month:
            try:
                fallback_month = generate_fallback_month(self._year, self._month) or {}
            except Exception:
                fallback_month = {}
        for day in range(1, total + 1):
            ad = bs_to_gregorian(self._year, self._month, day)
            if not ad:
                continue

            festivals: List[Dict[str, Any]] = []
            if self._engine:
                try:
                    festivals = self._engine.get_daily_festivals(ad) or []
                except Exception:
                    pass

            tithi_name = ""
            nakshatra_name = ""
            yoga_name = ""
            karana_name = ""
            
            fb = fallback_month.get(day, {})
            tithi_name = fb.get("tithi_name", "")
            nakshatra_name = fb.get("nakshatra_name", "")
            yoga_name = fb.get("yoga_name", "")
            karana_name = fb.get("karana_name", "")

            weekday = (ad.weekday() + 1) % 7   # 0=Sun, 6=Sat
            is_holiday = any(str(f.get("type", "")).lower() in ("holiday", "public_holiday", "government") for f in festivals)

            result[day] = {
                "ad":          ad,
                "weekday":     weekday,
                "is_saturday": weekday == 6,
                "festivals":   festivals,
                "tithi_name":  tithi_name,
                "nakshatra_name": nakshatra_name,
                "yoga_name":   yoga_name,
                "karana_name": karana_name,
                "is_holiday":  is_holiday,
                "sunrise":     "",
                "sunset":      "",
                "rahu_kaal":   fb.get("rahu_kaal", ""),
                "choghadiya":  fb.get("choghadiya", ""),
                # Provenance: this month came from the local engine, not the API.
                "_source": "स्थानीय इन्जिन (local engine)",
                "panchang":    {},
            }
        self.finished.emit(self._request_id, result)

    @Slot()
    def run_safely(self) -> None:
        """Keep the GUI responsive and always notify it, even if a source fails."""
        try:
            self.run()
        except Exception as exc:
            logger.warning("Calendar data load failed for %s-%s: %s",
                           self._year, self._month, exc)
            self.finished.emit(self._request_id, {})


# --------------------------------------------------------------------------
#  Single calendar cell widget (custom-painted for performance)
# --------------------------------------------------------------------------

# Devanagari font availability, resolved lazily on first paint.  QFontDatabase
# needs a live QGuiApplication; probing at import time aborts the process when
# this module is imported before the QApplication exists (test collection,
# standalone tooling).
_DEVA_FONT_CACHE: Optional[bool] = None


def _deva_font_available() -> bool:
    """True when a Devanagari-capable font family is installed."""
    global _DEVA_FONT_CACHE
    if _DEVA_FONT_CACHE is None:
        try:
            _DEVA_FONT_CACHE = any(
                "devanagari" in f.lower() or "noto sans" in f.lower()
                for f in QFontDatabase.families()
            )
        except Exception:
            _DEVA_FONT_CACHE = False
    return _DEVA_FONT_CACHE


class _CalCell(QWidget):
    """One day cell in the 7-column calendar grid."""

    clicked = Signal(int)   # BS day number

    _MIN_H = 86

    def __init__(self, bs_day: int, parent=None) -> None:
        super().__init__(parent)
        self.bs_day           = bs_day
        self.ad_day           = 0
        self.ad_month_label   = ""    # e.g. "Oct" when AD month rolls over
        self.tithi_name       = ""
        self.is_today         = False
        self.is_saturday      = False
        self.is_holiday       = False
        self.events: List[str] = []
        self.setMinimumHeight(self._MIN_H)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def update_data(
        self,
        ad_date: datetime.date,
        tithi_name: str,
        is_today: bool,
        is_saturday: bool,
        is_holiday: bool,
        events: List[str],
        ad_month_changed: bool,
    ) -> None:
        self.ad_day          = ad_date.day
        self.ad_month_label  = _AD_MONTH_NAMES_EN[ad_date.month - 1] if ad_month_changed else ""
        self.tithi_name      = tithi_name
        self.is_today        = is_today
        self.is_saturday     = is_saturday
        self.is_holiday      = is_holiday
        self.events          = events
        self.setToolTip(", ".join(events) if events else "")
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.bs_day)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r  = self.rect()
        W  = r.width()
        H  = r.height()
        PAD = 5

        # ---- Background --------------------------------------------------
        if self.is_today:
            bg = QColor(_C_TODAY_BG)
        elif self.is_saturday:
            bg = QColor(_C_SAT_BG)
        else:
            bg = QColor(_C_BG)
        p.fillRect(r, bg)

        # ---- Border ------------------------------------------------------
        if self.is_holiday and not self.is_today:
            p.fillRect(0, 0, 3, H, QColor(_C_HOL_BORDER))
        border_pen = QPen(QColor(_C_TODAY_BG).darker(110) if self.is_today else QColor(_C_GRID_BORDER), 0.8)
        p.setPen(border_pen)
        p.drawRect(r.adjusted(0, 0, -1, -1))

        # Hover tint
        if not self.is_today and self.underMouse():
            p.fillRect(r.adjusted(1, 1, -1, -1), QColor(0, 0, 0, 14))

        # ---- AD date badge (top-right circle) ----------------------------
        BADGE = 18
        bx = W - BADGE - PAD
        by = PAD
        if self.ad_day > 0:
            badge_bg = QColor(_C_TODAY_TEXT) if self.is_today else QColor(_C_AD_BADGE_BG)
            p.setBrush(QBrush(badge_bg))
            p.setPen(Qt.NoPen)
            p.drawEllipse(bx, by, BADGE, BADGE)
            badge_fg = QColor(_C_TODAY_BG) if self.is_today else QColor(_C_AD_BADGE_FG)
            p.setPen(badge_fg)
            if self.ad_month_label:
                ad_font = QFont("Segoe UI", 6)
                p.setFont(ad_font)
                label = f"{self.ad_month_label} {self.ad_day}"
                p.drawText(bx - 12, by, BADGE + 18, BADGE, Qt.AlignCenter, label)
            else:
                ad_font = QFont("Segoe UI", 8, QFont.Bold)
                p.setFont(ad_font)
                p.drawText(bx, by, BADGE, BADGE, Qt.AlignCenter, str(self.ad_day))

        # ---- Tithi name (top-left, tiny red) -----------------------------
        if self.tithi_name:
            tithi_fg = QColor(_C_TODAY_TEXT) if self.is_today else QColor(_C_TITHI)
            p.setPen(tithi_fg)
            t_font = QFont("Noto Sans Devanagari", 6) if _deva_font_available() else QFont("Segoe UI", 6)
            p.setFont(t_font)
            t_rect = r.adjusted(PAD, PAD, -(BADGE + PAD * 2 + 4), 0)
            t_rect.setHeight(13)
            p.drawText(t_rect, Qt.AlignLeft | Qt.AlignVCenter, self.tithi_name)

        # ---- Large BS date number ----------------------------------------
        if self.is_today:
            date_fg = QColor(_C_TODAY_TEXT)
        elif self.is_saturday or self.is_holiday:
            date_fg = QColor(_C_RED_DATE)
        else:
            date_fg = QColor(_C_BLUE_DATE)
        p.setPen(date_fg)
        num_pt = max(16, min(26, H // 3))
        n_font = (QFont("Noto Sans Devanagari", num_pt, QFont.Bold) if _deva_font_available()
                  else QFont("Segoe UI", num_pt, QFont.Bold))
        p.setFont(n_font)
        num_str  = to_nepali_digits(self.bs_day)
        num_rect = r.adjusted(PAD, 15, -(BADGE + PAD * 2 + 4), 0)
        num_rect.setHeight(num_pt + 8)
        p.drawText(num_rect, Qt.AlignLeft | Qt.AlignVCenter, num_str)

        # ---- Events / holiday text ---------------------------------------
        if self.events:
            ev_y = num_rect.bottom() + 2
            ev_rect = r.adjusted(PAD, ev_y, -PAD, -PAD)
            if ev_rect.height() >= 8:
                ev_pt = 6
                ev_font = (QFont("Noto Sans Devanagari", ev_pt) if _deva_font_available()
                           else QFont("Segoe UI", ev_pt))
                p.setFont(ev_font)
                if self.is_today:
                    ev_fg = QColor(_C_TODAY_TEXT)
                elif self.is_holiday or self.is_saturday:
                    ev_fg = QColor(_C_EVENT_HOL)
                else:
                    ev_fg = QColor(_C_EVENT_NRM)
                p.setPen(ev_fg)
                p.drawText(ev_rect,
                           Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                           " \u2022 ".join(self.events))

        p.end()


# --------------------------------------------------------------------------
#  Year/Month picker dialog
# --------------------------------------------------------------------------

class _YearMonthPickerDialog(QDialog):
    selected = Signal(int, int)

    def __init__(self, current_year: int, current_month: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("\u0935\u0930\u094d\u0937 \u0930 \u092e\u0939\u093f\u0928\u093e \u091b\u0928\u094c\u091f")
        self.setModal(True)
        self.setFixedSize(310, 180)
        self.setStyleSheet("QDialog{background:#fff;} QComboBox{min-height:30px;font-size:13px;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(14)

        title = QLabel("\u0935\u0930\u094d\u0937 \u0930 \u092e\u0939\u093f\u0928\u093e \u091b\u0928\u094c\u091f")
        title.setStyleSheet(f"font-size:15px;font-weight:700;color:{_C_BLUE_DATE};")
        lay.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(10)
        self._year_cb = QComboBox()
        for y in range(1990, 2101):
            self._year_cb.addItem(to_nepali_digits(y), y)
        idx = self._year_cb.findData(current_year)
        if idx >= 0:
            self._year_cb.setCurrentIndex(idx)
        row.addWidget(self._year_cb, 2)
        self._month_cb = QComboBox()
        for i, name in enumerate(_BS_MONTHS_COLLOQUIAL_NE, 1):
            self._month_cb.addItem(name, i)
        idx = self._month_cb.findData(current_month)
        if idx >= 0:
            self._month_cb.setCurrentIndex(idx)
        row.addWidget(self._month_cb, 3)
        lay.addLayout(row)

        btn_row = QHBoxLayout()
        cancel = QPushButton("\u0930\u0926\u094d\u0926 \u0917\u0930\u094d\u0928\u0941\u0939\u094b\u0938\u094d")
        cancel.setStyleSheet("background:#e8ecf5;border:none;border-radius:6px;padding:8px 14px;")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("\u0920\u0940\u0915 \u091b")
        ok.setStyleSheet(f"background:{_C_CTA_BG};color:#fff;border:none;border-radius:6px;padding:8px 20px;font-weight:700;")
        ok.clicked.connect(self._accept)
        btn_row.addWidget(cancel)
        btn_row.addStretch()
        btn_row.addWidget(ok)
        lay.addLayout(btn_row)

    def _accept(self):
        self.selected.emit(self._year_cb.currentData(), self._month_cb.currentData())
        self.accept()


# --------------------------------------------------------------------------
#  Day detail dialog (panchang popup)
# --------------------------------------------------------------------------

class _DayDetailDialog(QDialog):
    def __init__(self, bs_year: int, bs_month: int, bs_day: int,
                 day_data: Dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(
            f"{_ne_month_name(bs_month)} {to_nepali_digits(bs_day)}, {to_nepali_digits(bs_year)}"
        )
        self.setModal(True)
        self.setMinimumSize(390, 480)
        self.setStyleSheet("QDialog{background:#fff;} QTextBrowser{border:none;background:#f7f8fa;font-size:13px;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        bs_str = f"{_ne_month_name(bs_month)} {to_nepali_digits(bs_day)}, {to_nepali_digits(bs_year)}"
        ad: Optional[datetime.date] = day_data.get("ad")
        ad_str = ad.strftime("%d %b %Y") if ad else ""
        hdr = QLabel(f"<b>{bs_str}</b><br/><span style='color:#7a8aaa;font-size:12px;'>{ad_str}</span>")
        hdr.setStyleSheet("font-size:17px;color:#1a3580;")
        lay.addWidget(hdr)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color:#e0e4ec;")
        lay.addWidget(sep)

        # Panchang rows - use new API data structure
        rows: List[Tuple[str, str]] = []
        for k, v in [
            ("\u0924\u093f\u0925\u093f",   day_data.get("tithi_name", "")),
            ("\u0928\u0915\u094d\u0937\u0924\u094d\u0930", day_data.get("nakshatra_name", "")),
            ("\u092f\u094b\u0917",          day_data.get("yoga_name", "")),
            ("\u0915\u0930\u0923",          day_data.get("karana_name", "")),
            ("\u0938\u0942\u0930\u094d\u092f\u094b\u0926\u092f", day_data.get("sunrise", "")),
            ("\u0938\u0942\u0930\u094d\u092f\u093e\u0938\u094d\u0924", day_data.get("sunset", "")),
            ("\u0930\u093e\u0939\u0941 \u0915\u093e\u0932", day_data.get("rahu_kaal") or day_data.get("rahu_kala", "")),
            ("\u091a\u094b\u0918\u0921\u093c\u093f\u092f\u093e", day_data.get("choghadiya", "")),
        ]:
            if v:
                rows.append((k, str(v)))

        body = QTextBrowser()
        body.setOpenExternalLinks(False)
        if rows:
            html = "".join(
                f"<tr><td style='color:#7a8aaa;padding:4px 10px 4px 0;white-space:nowrap;'>"
                f"<b>{k}</b></td><td style='padding:4px 0;color:#1a2040;'>{v}</td></tr>"
                for k, v in rows
            )
        else:
            html = "<tr><td colspan='2' style='color:#7a8aaa;'>पञ्चाङ्ग विवरण उपलब्ध छैन (API पहुँच बाहिर)</td></tr>"
        body.setHtml(f"<table cellspacing='0' cellpadding='0'>{html}</table>")
        lay.addWidget(body, 1)

        festivals = day_data.get("festivals", [])
        if festivals:
            sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
            sep2.setStyleSheet("color:#e0e4ec;")
            lay.addWidget(sep2)
            ev_title = QLabel("\U0001f4c5 \u0915\u093e\u0930\u094d\u092f\u0915\u094d\u0930\u092e \u0924\u0925\u093e \u092a\u0930\u094d\u0935\u0939\u0930\u0942")
            ev_title.setStyleSheet(f"font-size:13px;font-weight:700;color:{_C_BLUE_DATE};")
            lay.addWidget(ev_title)
            for fest in festivals:
                name_ne = fest.get("name_ne") or fest.get("name", "")
                name_en = fest.get("name", "")
                cat     = fest.get("category", "")
                color   = _C_EVENT_HOL if cat in ("festival", "holiday") else _C_EVENT_NRM
                lbl     = QLabel(
                    f"<span style='color:{color};'>\u2022 {name_ne}</span>"
                    + (f"<br/><span style='color:#9aa0b8;font-size:11px;'>&nbsp;&nbsp;{name_en}</span>"
                       if name_en and name_en != name_ne else "")
                )
                lbl.setTextFormat(Qt.RichText)
                lbl.setWordWrap(True)
                lay.addWidget(lbl)

        close_btn = QPushButton("\u092c\u0928\u094d\u0926 \u0917\u0930\u094d\u0928\u0941\u0939\u094b\u0938\u094d")
        close_btn.setStyleSheet(
            f"background:{_C_BLUE_DATE};color:#fff;border:none;border-radius:6px;"
            "padding:9px 24px;font-weight:700;font-size:13px;"
        )
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        lay.addLayout(btn_row)


# --------------------------------------------------------------------------
#  Main calendar widget  (NepaliFestivalCalendarPage)
# --------------------------------------------------------------------------

class NepaliFestivalCalendarPage(QWidget):
    """
    Nepali Patro-style full monthly BS calendar.

    This class replaces the earlier simple grid implementation with a fully
    featured design matching nepalipatro.com.np:

      - Custom-painted cells with tithi, large BS numeral, AD badge, events
      - Today highlighted in orange; Saturdays tinted red
      - Background QThread loads panchang + festival data per month
      - Year/month picker dialog (BS 2000-2100)
      - Inline date converter and government holidays list dialogs
      - Bottom action bar with 4 pill shortcut buttons
    """

    # Bottom action-bar geometry.  The four shortcut pills must stay fully
    # visible even on short laptop screens, so the bar keeps its natural height
    # (44px pill + padding + separator) and the scrollable grid above it absorbs
    # all of the vertical slack instead.
    _PILL_H           = 44
    _ACTION_BAR_PAD   = 8
    _ACTION_BAR_MIN_H = _PILL_H + 2 * _ACTION_BAR_PAD + 1   # + 1px top border

    def __init__(self, language: str = "ne", parent=None) -> None:
        super().__init__(parent)
        self._lang   = language
        self._is_ne  = language == "ne"
        self._engine = NepaliFestivalEngine() if NepaliFestivalEngine else None

        today_bs = get_today_bs() or {"year": 2083, "month": 6, "day": 9}
        self._today_y = int(today_bs["year"])
        self._today_m = int(today_bs["month"])
        self._today_d = int(today_bs["day"])
        self._view_y  = self._today_y
        self._view_m  = self._today_m

        self._month_data: Dict[int, Dict[str, Any]] = {}
        self._loading = False
        self._request_id = 0
        self._thread: Optional[QThread] = None
        self._worker: Optional[_MonthDataWorker] = None
        self._cells: Dict[int, _CalCell] = {}

        self._build_ui()
        self._load_month_data()

    # ---- UI construction -------------------------------------------------

    def _build_ui(self) -> None:
        self.setStyleSheet(
            f"background:{_C_BG};"
            "font-family:'Segoe UI','Noto Sans Devanagari',sans-serif;"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_weekday_header())

        grid_scroll = QScrollArea()
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setStyleSheet("QScrollArea{border:none;background:#fff;}")
        self._grid_container = QWidget()
        self._grid_container.setStyleSheet(f"background:{_C_BG};")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(0)
        for c in range(7):
            self._grid_layout.setColumnStretch(c, 1)
        grid_scroll.setWidget(self._grid_container)
        root.addWidget(grid_scroll, 1)

        self._loading_lbl = QLabel("\u0921\u093e\u091f\u093e \u0932\u094b\u0921 \u0939\u0941\u0901\u0926\u0948\u091b\u2026")
        self._loading_lbl.setAlignment(Qt.AlignCenter)
        self._loading_lbl.setStyleSheet(f"color:{_C_TEXT_MUTED};font-size:14px;padding:40px;")
        self._loading_lbl.setVisible(False)
        root.addWidget(self._loading_lbl)

        # Provenance line: shows whether the month came from the primary API or
        # from the local fallback engine (hidden until data arrives).
        self._source_lbl = QLabel("")
        self._source_lbl.setStyleSheet(
            f"color:{_C_TEXT_MUTED};font-size:11px;padding:0 4px 4px 4px;"
        )
        self._source_lbl.setVisible(False)
        root.addWidget(self._source_lbl)

        # Stretch 0: the action bar keeps its own height at the bottom of the
        # page, while the grid scroll area above it takes the remaining space.
        # This ordering is what keeps the four shortcut pills visible when the
        # window is short (small laptop screens).
        self._action_bar = self._build_action_bar()
        root.addWidget(self._action_bar)

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(
            f"QFrame{{background:{_C_TOOLBAR_BG};border-bottom:2px solid {_C_GRID_BORDER};}}"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)

        left = QHBoxLayout()
        left.setSpacing(8)

        self._month_lbl = QLabel()
        self._month_lbl.setStyleSheet(
            f"font-size:20px;font-weight:800;color:{_C_BLUE_DATE};"
            "font-family:'Noto Sans Devanagari','Segoe UI',sans-serif;"
        )
        left.addWidget(self._month_lbl)

        self._ad_span_lbl = QLabel()
        self._ad_span_lbl.setStyleSheet(f"font-size:12px;color:{_C_TEXT_MUTED};")
        left.addWidget(self._ad_span_lbl)

        picker_btn = QPushButton("\u0935\u0930\u094d\u0937 \u0930 \u092e\u0939\u093f\u0928\u093e \u091b\u0928\u094c\u091f")
        picker_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{_C_BLUE_DATE};"
            "font-size:11px;text-decoration:underline;padding:0 2px;}}"
            "QPushButton:hover{color:#c94200;}"
        )
        picker_btn.setCursor(QCursor(Qt.PointingHandCursor))
        picker_btn.clicked.connect(self._open_picker)
        left.addWidget(picker_btn)

        self._prev_btn = self._make_nav_btn("\u2039", self._go_prev)
        self._next_btn = self._make_nav_btn("\u203a", self._go_next)
        left.addWidget(self._prev_btn)
        left.addWidget(self._next_btn)
        lay.addLayout(left)
        lay.addStretch()

        right = QHBoxLayout()
        right.setSpacing(8)
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText(
            "\u0915\u093e\u0930\u094d\u092f\u0915\u094d\u0930\u092e \u0916\u094b\u091c\u094d\u0928\u0941\u0939\u094b\u0938\u094d"
        )
        self._search_box.setFixedWidth(200)
        self._search_box.setStyleSheet(
            f"QLineEdit{{border:1px solid {_C_GRID_BORDER};border-radius:18px;"
            f"padding:5px 14px;font-size:12px;background:#f4f6fb;color:{_C_TEXT_DARK};}}"
            f"QLineEdit:focus{{border-color:{_C_BLUE_DATE};background:#fff;}}"
        )
        self._search_box.returnPressed.connect(self._do_search)
        right.addWidget(self._search_box)

        today_btn = QPushButton("\U0001f4c5 \u0906\u091c\u0915\u094b \u092e\u093f\u0924\u093f")
        today_btn.setStyleSheet(
            f"QPushButton{{background:{_C_CTA_BG};color:{_C_CTA_FG};"
            "border:none;border-radius:18px;padding:7px 18px;font-size:12px;font-weight:700;}}"
            "QPushButton:hover{background:#c94200;}"
        )
        today_btn.setCursor(QCursor(Qt.PointingHandCursor))
        today_btn.clicked.connect(self._go_today)
        right.addWidget(today_btn)
        lay.addLayout(right)
        return bar

    def _make_nav_btn(self, text: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(32, 32)
        btn.setStyleSheet(
            f"QPushButton{{background:{_C_HEADER_BG};color:{_C_BLUE_DATE};"
            f"border:1px solid {_C_GRID_BORDER};border-radius:16px;"
            "font-size:20px;font-weight:700;padding:0;}}"
            f"QPushButton:hover{{background:{_C_BLUE_DATE};color:#fff;}}"
        )
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.clicked.connect(slot)
        return btn

    def _build_weekday_header(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(f"background:{_C_HEADER_BG};border-bottom:1px solid {_C_GRID_BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        for i, (ne, en) in enumerate(zip(_WEEKDAYS_NE, _WEEKDAYS_EN)):
            is_sat    = (i == 6)
            ne_color  = _C_RED_DATE if is_sat else _C_TEXT_DARK
            en_color  = _C_RED_DATE if is_sat else _C_TEXT_MUTED
            col_w     = QWidget()
            right_sep = f"border-right:1px solid {_C_GRID_BORDER};" if i < 6 else ""
            col_w.setStyleSheet(f"background:transparent;{right_sep}")
            col_lay   = QVBoxLayout(col_w)
            col_lay.setContentsMargins(4, 6, 4, 6)
            col_lay.setSpacing(1)
            ne_lbl = QLabel(ne)
            ne_lbl.setAlignment(Qt.AlignCenter)
            ne_lbl.setStyleSheet(
                f"font-size:12px;font-weight:700;color:{ne_color};"
                "font-family:'Noto Sans Devanagari','Segoe UI',sans-serif;"
            )
            col_lay.addWidget(ne_lbl)
            en_lbl = QLabel(en)
            en_lbl.setAlignment(Qt.AlignCenter)
            en_lbl.setStyleSheet(f"font-size:9px;color:{en_color};")
            col_lay.addWidget(en_lbl)
            lay.addWidget(col_w, 1)
        return bar

    def _build_action_bar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(
            f"background:{_C_BG};border-top:1px solid {_C_GRID_BORDER};"
        )
        # Stretch factor 0 in _build_ui() plus this minimum keeps the four
        # shortcut pills at full height; the grid scroll area shrinks first.
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bar.setMinimumHeight(self._ACTION_BAR_MIN_H)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, self._ACTION_BAR_PAD, 12, self._ACTION_BAR_PAD)
        lay.setSpacing(10)

        def pill(label: str, bg: str, tip: str = "") -> QPushButton:
            b = QPushButton(label)
            b.setStyleSheet(
                f"QPushButton{{background:{bg};color:#fff;border:none;"
                "border-radius:8px;padding:10px 12px;font-size:11px;font-weight:700;"
                "font-family:'Noto Sans Devanagari','Segoe UI',sans-serif;}}"
                "QPushButton:hover{filter:brightness(0.88);}"
            )
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setFixedHeight(self._PILL_H)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            if tip:
                b.setToolTip(tip)
            return b

        m_btn = pill(
            "\U0001f550 \u0936\u0941\u092d \u0938\u093e\u0907\u0924 \u0924\u0925\u093e \u092e\u0941\u0939\u0942\u0930\u094d\u0924",
            _C_MUHURTA, "Auspicious time / Muhurat finder"
        )
        m_btn.clicked.connect(lambda: self._action_clicked("muhurta"))
        lay.addWidget(m_btn)

        c_btn = pill(
            "\U0001f501 \u092e\u093f\u0924\u093f \u092a\u0930\u093f\u0935\u0930\u094d\u0924\u0928",
            _C_CONVERTER, "BS <-> AD Date converter"
        )
        c_btn.clicked.connect(lambda: self._action_clicked("converter"))
        lay.addWidget(c_btn)

        h_btn = pill(
            "\U0001f4cb \u0938\u0930\u0915\u093e\u0930\u0940 \u092c\u093f\u0926\u093e\u0939\u0930\u0942",
            _C_HOLIDAYS, "Government holidays list"
        )
        h_btn.clicked.connect(lambda: self._action_clicked("holidays"))
        lay.addWidget(h_btn)

        f_btn = pill(
            "\U0001f4ac \u092a\u094d\u0930\u0924\u093f\u0915\u094d\u0930\u093f\u092f\u093e \u0930 \u0938\u0941\u091d\u093e\u0935\u0939\u0930\u0942",
            _C_FEEDBACK, "Feedback & suggestions"
        )
        f_btn.clicked.connect(lambda: self._action_clicked("feedback"))
        lay.addWidget(f_btn)
        return bar

    # ---- Data loading ----------------------------------------------------

    def _load_month_data(self) -> None:
        self._request_id += 1
        request_id = self._request_id
        self._loading = True
        # Paint the date grid immediately; events and Panchang fill in when ready.
        self._month_data = {}
        self._render_grid()
        self._loading_lbl.setVisible(False)
        self._thread = QThread(self)
        self._worker = _MonthDataWorker(request_id, self._view_y, self._view_m, self._engine)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run_safely)
        # Connect directly to a QObject slot so Qt queues widget work onto the GUI thread.
        self._worker.finished.connect(self._on_data_loaded)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @Slot(int, dict)
    def _on_data_loaded(self, request_id: int, data: Dict[int, Dict[str, Any]]) -> None:
        if request_id != self._request_id:
            return
        self._month_data = data
        self._loading    = False
        self._loading_lbl.setVisible(False)
        # Provenance: the worker records whether the month came from the primary
        # API or from the local fallback engine.  Show it instead of silently
        # presenting fallback data as authoritative (PROJECT_RULES 3.2).
        sources = {day.get("_source") for day in data.values() if day.get("_source")}
        if sources:
            self._source_lbl.setText(
                ("स्रोत: " if self._is_ne else "Source: ") + ", ".join(sorted(sources))
            )
            self._source_lbl.setVisible(True)
        self._render_grid()

    # ---- Grid rendering --------------------------------------------------

    def _render_grid(self) -> None:
        self._cells.clear()
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._month_lbl.setText(
            f"{_ne_month_name(self._view_m)} {to_nepali_digits(self._view_y)}"
        )
        self._ad_span_lbl.setText(
            f"| {_ad_span_for_bs_month(self._view_y, self._view_m)}"
        )

        first_ad = bs_to_gregorian(self._view_y, self._view_m, 1)
        if not first_ad:
            return
        weekday_start = (first_ad.weekday() + 1) % 7   # 0=Sun
        total_days    = bs_month_length(self._view_y, self._view_m) or 30

        # Build a set of government holiday day-numbers for this month
        gov_hol_days: set = set()
        if self._engine:
            try:
                for h in self._engine.get_government_holidays(self._view_y):
                    ad_holiday = datetime.date.fromisoformat(str(h.get("date", ""))[:10])
                    bs_holiday = gregorian_to_bs(ad_holiday.year, ad_holiday.month, ad_holiday.day)
                    if bs_holiday and bs_holiday["year"] == self._view_y and bs_holiday["month"] == self._view_m:
                        gov_hol_days.add(bs_holiday["day"])
            except Exception:
                pass

        # Leading empty spacers
        row, col = 0, weekday_start
        for c in range(weekday_start):
            sp = QWidget()
            sp.setStyleSheet(
                f"background:{_C_BG};border:0.5px solid {_C_GRID_BORDER};"
            )
            sp.setMinimumHeight(_CalCell._MIN_H)
            self._grid_layout.addWidget(sp, row, c)

        prev_ad_month = first_ad.month

        for day in range(1, total_days + 1):
            info = self._month_data.get(day, {})
            ad: Optional[datetime.date] = info.get("ad") or bs_to_gregorian(self._view_y, self._view_m, day)
            if not ad:
                col += 1
                if col > 6:
                    col = 0; row += 1
                continue

            is_today    = (
                self._view_y == self._today_y and
                self._view_m == self._today_m and
                day == self._today_d
            )
            is_saturday = info.get("is_saturday", (ad.weekday() + 1) % 7 == 6)
            festivals   = info.get("festivals", [])

            is_holiday  = (
                day in gov_hol_days or
                bool(info.get("is_holiday")) or
                any(str(f.get("type", f.get("category", ""))).lower() in ("holiday", "public_holiday", "government") for f in festivals)
            )

            ev_names: List[str] = []
            for f in festivals:
                nm = f.get("name_ne") or f.get("name", "")
                if nm and nm not in ev_names:
                    ev_names.append(nm)
            ev_names = ev_names[:2]

            ad_month_changed = (ad.month != prev_ad_month)
            prev_ad_month    = ad.month

            cell = _CalCell(day, self._grid_container)
            cell.update_data(
                ad_date          = ad,
                tithi_name       = info.get("tithi_name", ""),
                is_today         = is_today,
                is_saturday      = is_saturday,
                is_holiday       = is_holiday,
                events           = ev_names,
                ad_month_changed = ad_month_changed,
            )
            cell.clicked.connect(self._on_cell_clicked)
            self._cells[day] = cell
            self._grid_layout.addWidget(cell, row, col)

            col += 1
            if col > 6:
                col = 0; row += 1

        # Complete the final week and keep the calendar at five rows minimum.
        filled = weekday_start + total_days
        row_count = max(5, (filled + 6) // 7)
        for slot in range(filled, row_count * 7):
            r, c = divmod(slot, 7)
            spacer = QWidget(self._grid_container)
            spacer.setStyleSheet(f"background:{_C_BG};border:0.5px solid {_C_GRID_BORDER};")
            spacer.setMinimumHeight(_CalCell._MIN_H)
            self._grid_layout.addWidget(spacer, r, c)

    # ---- Navigation ------------------------------------------------------

    def _go_prev(self) -> None:
        if self._view_m == 1:
            self._view_y -= 1; self._view_m = 12
        else:
            self._view_m -= 1
        self._load_month_data()

    def _go_next(self) -> None:
        if self._view_m == 12:
            self._view_y += 1; self._view_m = 1
        else:
            self._view_m += 1
        self._load_month_data()

    def _go_today(self) -> None:
        self._view_y = self._today_y
        self._view_m = self._today_m
        self._load_month_data()

    def _open_picker(self) -> None:
        dlg = _YearMonthPickerDialog(self._view_y, self._view_m, self)
        dlg.selected.connect(self._on_picker_selected)
        dlg.exec()

    def _on_picker_selected(self, year: int, month: int) -> None:
        self._view_y = year
        self._view_m = month
        self._load_month_data()

    # ---- Search ----------------------------------------------------------

    def _do_search(self) -> None:
        query = self._search_box.text().strip().lower()
        if not query:
            return
        found = False
        for day, cell in self._cells.items():
            if query in " ".join(cell.events).lower():
                found = True
                self._on_cell_clicked(day)
                break
        if not found:
            QMessageBox.information(
                self, "\u0916\u094b\u091c",
                f'"{self._search_box.text()}" \u092d\u0947\u091f\u093f\u090f\u0928\u0964'
            )

    # ---- Cell click -> day detail dialog ---------------------------------

    def _on_cell_clicked(self, day: int) -> None:
        data = self._month_data.get(day, {})
        if not data:
            ad = bs_to_gregorian(self._view_y, self._view_m, day)
            data = {
                "ad": ad,
                "festivals": [],
                "tithi_name": "",
                "nakshatra_name": "",
                "yoga_name": "",
                "karana_name": "",
                "sunrise": "",
                "sunset": "",
            }
        _DayDetailDialog(self._view_y, self._view_m, day, data, self).exec()

    # ---- Action bar ------------------------------------------------------

    def _action_clicked(self, action: str) -> None:
        if action == "muhurta":
            w = self.window()
            if hasattr(w, "_navigate"):
                w._navigate("muhurta_finder")
            else:
                QMessageBox.information(self, "\u0936\u0941\u092d \u092e\u0941\u0939\u0942\u0930\u094d\u0924",
                    "\u092e\u0941\u0939\u0942\u0930\u094d\u0924 \u092b\u093e\u0907\u0923\u094d\u0921\u0930 \u0916\u094b\u0932\u094d\u0928\u0941\u0939\u094b\u0938\u094d\u0964")
        elif action == "converter":
            self._show_date_converter()
        elif action == "holidays":
            self._show_holidays_list()
        elif action == "feedback":
            QMessageBox.information(
                self,
                "\u092a\u094d\u0930\u0924\u093f\u0915\u094d\u0930\u093f\u092f\u093e",
                "\u092a\u094d\u0930\u0924\u093f\u0915\u094d\u0930\u093f\u092f\u093e \u0930 \u0938\u0941\u091d\u093e\u0935\u0939\u0930\u0942\u0915\u094b \u0932\u093e\u0917\u093f \u0927\u0928\u094d\u092f\u0935\u093e\u0926!\n"
                "\u0915\u0943\u092a\u092f\u093e GitHub Issues \u0935\u093e \u0908\u092e\u0947\u0932 \u092e\u093e\u0930\u094d\u092b\u0924 \u092a\u0920\u093e\u0909\u0928\u0941\u0939\u094b\u0938\u094d\u0964"
            )

    def _show_date_converter(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("\u092e\u093f\u0924\u093f \u092a\u0930\u093f\u0935\u0930\u094d\u0924\u0928  BS <-> AD")
        dlg.setFixedSize(350, 280)
        dlg.setStyleSheet("background:#fff;font-size:13px;")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        title = QLabel("\U0001f501 \u092e\u093f\u0924\u093f \u092a\u0930\u093f\u0935\u0930\u094d\u0924\u0928")
        title.setStyleSheet(f"font-size:15px;font-weight:700;color:{_C_BLUE_DATE};")
        lay.addWidget(title)

        lay.addWidget(QLabel("BS \u092e\u093f\u0924\u093f \u0932\u0947\u0916\u094d\u0928\u0941\u0939\u094b\u0938\u094d (\u0935\u0930\u094d\u0937-\u092e\u0939\u093f\u0928\u093e-\u0926\u093f\u0928):"))
        bs_inp = QLineEdit()
        bs_inp.setPlaceholderText("\u0968\u0966\u096b\u0969-\u0966\u096d-\u0966\u096f")
        bs_inp.setStyleSheet(f"border:1px solid {_C_GRID_BORDER};border-radius:6px;padding:6px;")
        lay.addWidget(bs_inp)

        result_lbl = QLabel()
        result_lbl.setTextFormat(Qt.RichText)
        result_lbl.setWordWrap(True)
        lay.addWidget(result_lbl)

        def convert():
            raw = bs_inp.text().strip()
            raw_en = "".join(
                str("\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f".index(c))
                if c in "\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f" else c
                for c in raw
            )
            parts = raw_en.replace("/", "-").split("-")
            if len(parts) == 3:
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    ad = bs_to_gregorian(y, m, d)
                    if ad:
                        result_lbl.setText(
                            f"<b style='color:{_C_BLUE_DATE};'>AD: {ad.strftime('%d %B %Y')}</b>"
                        )
                    else:
                        result_lbl.setText("<span style='color:red;'>\u0905\u092e\u093e\u0928\u094d\u092f \u092e\u093f\u0924\u093f\u0964</span>")
                except Exception:
                    result_lbl.setText("<span style='color:red;'>\u0905\u092e\u093e\u0928\u094d\u092f \u0907\u0928\u092a\u0941\u091f\u0964</span>")
            else:
                result_lbl.setText("<span style='color:red;'>\u0935\u0930\u094d\u0937-\u092e\u0939\u093f\u0928\u093e-\u0926\u093f\u0928 \u0922\u093e\u0901\u091a\u092e\u093e \u0932\u0947\u0916\u094d\u0928\u0941\u0939\u094b\u0938\u094d\u0964</span>")

        conv_btn = QPushButton("\u092a\u0930\u093f\u0935\u0930\u094d\u0924\u0928 \u0917\u0930\u094d\u0928\u0941\u0939\u094b\u0938\u094d")
        conv_btn.setStyleSheet(
            f"background:{_C_BLUE_DATE};color:#fff;border:none;border-radius:6px;padding:8px 16px;"
        )
        conv_btn.clicked.connect(convert)
        lay.addWidget(conv_btn)
        lay.addStretch()

        close = QPushButton("\u092c\u0928\u094d\u0926")
        close.setStyleSheet("background:#e8ecf5;border:none;border-radius:6px;padding:7px 14px;")
        close.clicked.connect(dlg.accept)
        brow = QHBoxLayout()
        brow.addStretch()
        brow.addWidget(close)
        lay.addLayout(brow)
        dlg.exec()

    def _show_holidays_list(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(
            f"\u0938\u0930\u0915\u093e\u0930\u0940 \u092c\u093f\u0926\u093e\u0939\u0930\u0942 {to_nepali_digits(self._view_y)}"
        )
        dlg.setFixedSize(420, 480)
        dlg.setStyleSheet("background:#fff;")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        title = QLabel(
            f"\U0001f4cb \u0938\u0930\u0915\u093e\u0930\u0940 \u092c\u093f\u0926\u093e\u0939\u0930\u0942 \u2014 {to_nepali_digits(self._view_y)}"
        )
        title.setStyleSheet(f"font-size:15px;font-weight:700;color:{_C_HOLIDAYS};")
        lay.addWidget(title)

        body = QTextBrowser()
        body.setStyleSheet("border:none;background:#f7f8fa;font-size:12px;")

        holidays: List[Dict[str, Any]] = []
        if self._engine:
            try:
                holidays = self._engine.get_government_holidays(self._view_y)
            except Exception:
                pass

        if holidays:
            rows = "".join(
                f"<tr><td style='padding:5px 8px;color:{_C_TEXT_MUTED};'>{h.get('date_bs', '')}</td>"
                f"<td style='padding:5px 8px;color:{_C_BLUE_DATE};font-weight:600;'>{h.get('name', '')}</td></tr>"
                for h in holidays
            )
            body.setHtml(f"<table cellspacing='0' cellpadding='0' width='100%'>{rows}</table>")
        else:
            body.setPlainText(
                "\u0938\u0930\u0915\u093e\u0930\u0940 \u092c\u093f\u0926\u093e\u0939\u0930\u0942 \u092d\u0947\u091f\u093f\u090f\u0928\u0964"
            )
        lay.addWidget(body, 1)

        close = QPushButton("\u092c\u0928\u094d\u0926 \u0917\u0930\u094d\u0928\u0941\u0939\u094b\u0938\u094d")
        close.setStyleSheet(
            f"background:{_C_BLUE_DATE};color:#fff;border:none;border-radius:6px;padding:8px 16px;font-weight:700;"
        )
        close.clicked.connect(dlg.accept)
        brow = QHBoxLayout()
        brow.addStretch()
        brow.addWidget(close)
        lay.addLayout(brow)
        dlg.exec()
