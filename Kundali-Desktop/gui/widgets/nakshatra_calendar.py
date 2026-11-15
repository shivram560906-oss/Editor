# -*- coding: utf-8 -*-
"""
gui/widgets/nakshatra_calendar.py

Nakshatra Calendar — Monthly View
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Shows current month's day-by-day table:
  Date (AD/BS) | Tithi | Nakshatra | Yoga | Karana | Vara | Auspicious?

Highlights today. Click any row for full panchang detail popup.
"""
from __future__ import annotations
import sys, os, datetime, calendar
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QMessageBox, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QBrush

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_GOLD, COLOR_ACCENT, COLOR_ERROR, COLOR_SUCCESS
)

# ── Constants ─────────────────────────────────────────────────────────────────
WEEKDAY_NE = ["सोम", "मङ्गल", "बुध", "बिहि", "शुक्र", "शनि", "आइत"]
WEEKDAY_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

MONTH_NE = ["जनवरी","फेब्रुअरी","मार्च","अप्रिल","मे","जुन",
            "जुलाई","अगस्ट","सेप्टेम्बर","अक्टोबर","नोभेम्बर","डिसेम्बर"]

NAKSHATRA_NE = [
    "अश्विनी","भरणी","कृत्तिका","रोहिणी","मृगशिरा","आर्द्रा","पुनर्वसु","पुष्य","आश्लेषा",
    "मघा","पूर्वाफाल्गुनी","उत्तराफाल्गुनी","हस्त","चित्रा","स्वाति","विशाखा","अनुराधा","ज्येष्ठा",
    "मूल","पूर्वाषाढा","उत्तराषाढा","श्रवण","धनिष्ठा","शतभिषा","पूर्वाभाद्रपद","उत्तराभाद्रपद","रेवती"
]
NAKSHATRA_EN = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha",
    "Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

TITHI_NE = [
    "प्रतिपदा","द्वितीया","तृतीया","चतुर्थी","पञ्चमी","षष्ठी","सप्तमी","अष्टमी",
    "नवमी","दशमी","एकादशी","द्वादशी","त्रयोदशी","चतुर्दशी","पूर्णिमा/अमावस्या"
]


def _nakshatra_from_moon_lon(lon: float, lang: str) -> str:
    """Calculate nakshatra from Moon's sidereal longitude."""
    idx = int(lon * 27 / 360) % 27
    return NAKSHATRA_NE[idx] if lang == "ne" else NAKSHATRA_EN[idx]


def _tithi_from_sun_moon(sun: float, moon: float, lang: str) -> str:
    diff = (moon - sun) % 360
    tithi_num = int(diff / 12)
    if lang == "ne":
        if tithi_num < len(TITHI_NE):
            return TITHI_NE[tithi_num]
    names_en = [
        "Pratipadā","Dvitīyā","Tṛtīyā","Caturthi","Pañcami","Ṣaṣṭhi","Saptami","Aṣṭami",
        "Navami","Daśami","Ekādaśī","Dvādaśī","Trayodaśī","Caturdaśī","Pūrṇimā/Amāvāsyā"
    ]
    return names_en[min(tithi_num, 14)]


# ── Background worker ─────────────────────────────────────────────────────────

class _CalWorker(QThread):
    """Load panchang data for each day of the month in background."""
    row_ready = Signal(int, dict)   # (row_index, data_dict)
    done      = Signal()

    def __init__(self, year: int, month: int, lat: float, lon: float, tz: float, lang: str):
        super().__init__()
        self._year, self._month = year, month
        self._lat, self._lon, self._tz = lat, lon, tz
        self._lang = lang

    def run(self):
        backend = os.path.join(_ROOT, "backend")
        if backend not in sys.path:
            sys.path.insert(0, backend)
        try:
            from calculator.reminder_panchang import get_daily_digest
        except Exception:
            get_daily_digest = None

        days_in_month = calendar.monthrange(self._year, self._month)[1]
        for day in range(1, days_in_month + 1):
            date = datetime.date(self._year, self._month, day)
            row = day - 1
            data: dict = {"date": date}
            try:
                if get_daily_digest:
                    digest = get_daily_digest(
                        date, latitude=self._lat, longitude=self._lon,
                        timezone=self._tz, language=self._lang,
                    )
                    t_d = digest.get("tithi", {})
                    n_d = digest.get("nakshatra", {})
                    y_d = digest.get("yoga", {})
                    w_d = digest.get("weekday", {})
                    data["tithi"]     = t_d.get("nepali") or t_d.get("name", "—")
                    data["nakshatra"] = n_d.get("nepali") or n_d.get("name", "—")
                    data["yoga"]      = y_d.get("nepali") or y_d.get("name", "—")
                    data["vara"]      = w_d.get("nepali" if self._lang == "ne" else "english", "—")
                    data["sunrise"]   = digest.get("sunrise", "—")
                    data["sunset"]    = digest.get("sunset", "—")
                    raw_fest = digest.get("festivals") or []
                    data["festivals"] = [
                        f[0] if isinstance(f, (list, tuple)) else str(f)
                        for f in raw_fest
                    ]
                else:
                    data["tithi"] = data["nakshatra"] = data["yoga"] = "—"
                    wd = date.weekday()
                    data["vara"] = (WEEKDAY_NE if self._lang == "ne" else WEEKDAY_EN)[wd]
                    data["sunrise"] = data["sunset"] = "—"
                    data["festivals"] = []
            except Exception:
                data["tithi"] = data["nakshatra"] = data["yoga"] = data["vara"] = "—"
                data["sunrise"] = data["sunset"] = "—"
                data["festivals"] = []
            self.row_ready.emit(row, data)
        self.done.emit()


# ── Main Widget ───────────────────────────────────────────────────────────────

class NakshatraCalendarPage(QWidget):
    """Monthly Nakshatra / Panchang calendar table."""

    COL_DATE      = 0
    COL_VARA      = 1
    COL_TITHI     = 2
    COL_NAKSHATRA = 3
    COL_YOGA      = 4
    COL_SUNRISE   = 5
    COL_FESTIVAL  = 6

    HEADERS_NE = ["मिति","वार","तिथि","नक्षत्र","योग","सूर्योदय","पर्व / विशेष"]
    HEADERS_EN = ["Date","Vara","Tithi","Nakshatra","Yoga","Sunrise","Festivals"]

    def __init__(self, language: str = "ne", lat: float = 27.7172,
                 lon: float = 85.324, tz: float = 5.75, parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._lat, self._lon, self._tz = lat, lon, tz
        self._today = datetime.date.today()
        self._cur_year  = self._today.year
        self._cur_month = self._today.month
        self._worker: Optional[_CalWorker] = None
        self._row_data: dict[int, dict] = {}
        self._build_ui()
        self._load_month()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ── Header ──
        hdr = QHBoxLayout()
        title = QLabel("🌙 " + ("नक्षत्र पञ्चाङ्ग क्यालेन्डर" if self._is_ne else "Nakshatra Panchang Calendar"))
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLOR_GOLD};")
        hdr.addWidget(title)
        hdr.addStretch()

        # Month/year navigation
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(30, 30)
        self._prev_btn.clicked.connect(self._prev_month)
        self._prev_btn.setStyleSheet(self._nav_btn_ss())
        hdr.addWidget(self._prev_btn)

        self._month_lbl = QLabel()
        self._month_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; min-width: 150px;")
        self._month_lbl.setAlignment(Qt.AlignCenter)
        hdr.addWidget(self._month_lbl)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(30, 30)
        self._next_btn.clicked.connect(self._next_month)
        self._next_btn.setStyleSheet(self._nav_btn_ss())
        hdr.addWidget(self._next_btn)

        today_btn = QPushButton("🏠" + (" आज" if self._is_ne else " Today"))
        today_btn.setFixedHeight(30)
        today_btn.clicked.connect(self._go_today)
        today_btn.setStyleSheet(self._nav_btn_ss())
        hdr.addWidget(today_btn)
        layout.addLayout(hdr)

        # ── Table ──
        headers = self.HEADERS_NE if self._is_ne else self.HEADERS_EN
        self._table = QTableWidget()
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(self.COL_DATE, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(self.COL_VARA, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(self.COL_SUNRISE, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR};
                border-radius: 8px; gridline-color: {BORDER_COLOR};
                color: {COLOR_TEXT_PRIMARY}; font-size: 12px;
            }}
            QHeaderView::section {{
                background: {BG_TERTIARY}; color: {COLOR_GOLD};
                font-weight: 700; padding: 6px; border: none;
                border-bottom: 1px solid {BORDER_COLOR};
            }}
            QTableWidget::item:alternate {{ background: {BG_TERTIARY}; }}
            QTableWidget::item:selected {{ background: {COLOR_ACCENT}; color: #fff; }}
        """)
        self._table.cellDoubleClicked.connect(self._on_row_click)
        layout.addWidget(self._table, 1)

        # Status
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        layout.addWidget(self._status_lbl)

    def _nav_btn_ss(self):
        return f"""
            QPushButton {{
                background: {BG_TERTIARY}; border: 1px solid {BORDER_COLOR};
                border-radius: 6px; padding: 4px 10px; color: {COLOR_TEXT_PRIMARY}; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {COLOR_GOLD}; color: {COLOR_GOLD}; }}
        """

    def _update_month_label(self):
        if self._is_ne:
            self._month_lbl.setText(f"{MONTH_NE[self._cur_month - 1]} {self._cur_year}")
        else:
            self._month_lbl.setText(f"{calendar.month_name[self._cur_month]} {self._cur_year}")

    def _prev_month(self):
        if self._cur_month == 1:
            self._cur_month, self._cur_year = 12, self._cur_year - 1
        else:
            self._cur_month -= 1
        self._load_month()

    def _next_month(self):
        if self._cur_month == 12:
            self._cur_month, self._cur_year = 1, self._cur_year + 1
        else:
            self._cur_month += 1
        self._load_month()

    def _go_today(self):
        self._cur_year  = self._today.year
        self._cur_month = self._today.month
        self._load_month()

    def _load_month(self):
        self._update_month_label()
        days = calendar.monthrange(self._cur_year, self._cur_month)[1]
        self._table.setRowCount(days)
        self._row_data.clear()
        # Pre-fill date column
        for day in range(1, days + 1):
            d = datetime.date(self._cur_year, self._cur_month, day)
            date_str = d.strftime("%d %b") if not self._is_ne else f"{day}"
            self._set_cell(day - 1, self.COL_DATE, date_str)
            self._highlight_today(day - 1, d)
        self._status_lbl.setText("⏳ " + ("लोड हुँदैछ..." if self._is_ne else "Loading..."))
        # Stop previous worker
        if self._worker and self._worker.isRunning():
            self._worker.quit()
        self._worker = _CalWorker(
            self._cur_year, self._cur_month, self._lat, self._lon, self._tz, self._lang
        )
        self._worker.row_ready.connect(self._on_row_ready)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _set_cell(self, row: int, col: int, text: str, color: Optional[str] = None):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        if color:
            item.setForeground(QBrush(QColor(color)))
        self._table.setItem(row, col, item)

    def _highlight_today(self, row: int, date: datetime.date):
        if date == self._today:
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item:
                    item.setBackground(QBrush(QColor(COLOR_GOLD).darker(80)))
                    item.setForeground(QBrush(QColor("#fff")))

    def _on_row_ready(self, row: int, data: dict):
        self._row_data[row] = data
        date: datetime.date = data["date"]
        wd = date.weekday()
        vara = data.get("vara") or (WEEKDAY_NE if self._is_ne else WEEKDAY_EN)[wd]
        tithi     = data.get("tithi", "—")
        nakshatra = data.get("nakshatra", "—")
        yoga      = data.get("yoga", "—")
        sunrise   = data.get("sunrise", "—")
        festivals = ", ".join(data.get("festivals") or []) or "—"

        date_str  = date.strftime("%d %b") if not self._is_ne else f"{date.day}"
        self._set_cell(row, self.COL_DATE,      date_str)
        self._set_cell(row, self.COL_VARA,      vara,      "#60a5fa" if wd == 6 else None)
        self._set_cell(row, self.COL_TITHI,     tithi)
        self._set_cell(row, self.COL_NAKSHATRA, nakshatra, COLOR_GOLD)
        self._set_cell(row, self.COL_YOGA,      yoga)
        self._set_cell(row, self.COL_SUNRISE,   sunrise)
        self._set_cell(row, self.COL_FESTIVAL,  festivals, COLOR_SUCCESS if festivals != "—" else None)
        self._highlight_today(row, date)

    def _on_done(self):
        self._status_lbl.setText(
            "✅ " + (f"{self._cur_month}/{self._cur_year} लोड भयो।"
                     if self._is_ne else f"{calendar.month_name[self._cur_month]} {self._cur_year} loaded.")
        )

    def _on_row_click(self, row: int, col: int):
        data = self._row_data.get(row)
        if not data:
            return
        date: datetime.date = data["date"]
        lines = [
            f"📅 {'मिति' if self._is_ne else 'Date'}: {date}",
            f"🌙 {'नक्षत्र' if self._is_ne else 'Nakshatra'}: {data.get('nakshatra','—')}",
            f"🌑 {'तिथि' if self._is_ne else 'Tithi'}: {data.get('tithi','—')}",
            f"⚡ {'योग' if self._is_ne else 'Yoga'}: {data.get('yoga','—')}",
            f"🌅 {'सूर्योदय' if self._is_ne else 'Sunrise'}: {data.get('sunrise','—')}",
            f"🌆 {'सूर्यास्त' if self._is_ne else 'Sunset'}: {data.get('sunset','—')}",
            f"🪔 {'पर्व' if self._is_ne else 'Festivals'}: {', '.join(data.get('festivals') or ['—'])}",
        ]
        QMessageBox.information(self, str(date), "\n".join(lines))
