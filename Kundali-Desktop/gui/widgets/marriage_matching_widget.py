# -*- coding: utf-8 -*-
"""
gui/widgets/marriage_matching_widget.py

विवाह मिलान (Marriage Matching) — पूर्ण रूपमा नेपाली भाषामा:
- जन्म कुण्डली विवरण फाराम (वर र वधू दुवैका लागि नयाँ कुण्डली जस्तै पूर्ण र स्पष्ट फाराम)
- कम्प्युटरको कुनै पनि स्थानबाट कुण्डली फाइल अपलोड/खोल्ने सुविधा (JSON, XML, QCK, JHD)
- नयाँ भरेको कुण्डलीलाई छुट्टाछुट्टै सुरक्षित (Save to Database) गर्ने सुविधा
- सहेजिएका कुण्डलीहरूबाट छनोट गर्ने सुविधा
- अष्टकूट गुण मिलान (३६ गुण)
- मंगल दोष विश्लेषण (लग्न कुण्डली D1 र चन्द्र कुण्डली दुवैबाट)
- सानो इनपुट, ठुलो एवं विस्तृत आउटपुट
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, Property, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QLinearGradient
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class GunaScoreGauge(QWidget):
    """Clean, animated visual progress bar for Ashtakoot Guna Milan (0 to 36)."""
    def __init__(self, score: float, max_score: float = 36.0, color: str = "#16a34a", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._target_score = float(score)
        self._max_score = float(max_score) if max_score > 0 else 36.0
        self._color = QColor(color)
        self._current_val = 0.0
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._anim = QPropertyAnimation(self, b"progressValue", self)
        self._anim.setDuration(450)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(self._target_score)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        QTimer.singleShot(60, self._anim.start)

    def _get_val(self) -> float:
        return self._current_val

    def _set_val(self, v: float):
        self._current_val = v
        self.update()

    progressValue = Property(float, _get_val, _set_val)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        radius = h / 2.0

        # Background track
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#e2e8f0"))
        p.drawRoundedRect(0, 0, w, h, radius, radius)

        # Fill track
        pct = max(0.0, min(1.0, self._current_val / self._max_score))
        if pct > 0.0:
            fill_w = max(h, w * pct)
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0.0, self._color.lighter(125))
            grad.setColorAt(1.0, self._color)
            p.setBrush(grad)
            p.drawRoundedRect(0, 0, fill_w, h, radius, radius)

        # Text label
        p.setPen(QColor("#ffffff") if pct > 0.35 else QColor("#1e293b"))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        text = f"{self._current_val:.1f} / {self._max_score:.0f} गुण  ({int(pct * 100)}%)"
        p.drawText(QRectF(14, 0, w - 28, h), Qt.AlignVCenter | (Qt.AlignLeft if pct > 0.35 else Qt.AlignRight), text)
        p.end()

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.backend_bridge import (
    convert_ad_to_bs,
    convert_bs_to_ad,
    get_all_cities,
)
from gui.theme import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER_COLOR,
    COLOR_ERROR,
    COLOR_GOLD,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from gui.utils.bs_calendar import (
    BS_MONTHS_NE,
    gregorian_to_bs,
    to_nepali_digits,
)
from gui.utils.chart_storage import list_charts, save_chart
from gui.utils.location_data import (
    NEPAL_PROVINCE_NE,
    countries,
    district_metadata,
    districts_for_region,
    enrich_cities,
    filtered_cities,
    regions_for_country,
)
from gui.utils.nepali_date_input import (
    BS_MONTHS,
    normalize_birth_time,
    to_english_digits,
)
from gui.widgets.smart_nepali_date_dropdown import SmartNepaliDateDropdown

# ── Nepali Lookup Tables ──────────────────────────────────────────────────────
_RASHI_NE = {
    1: "मेष", 2: "वृष", 3: "मिथुन", 4: "कर्कट",
    5: "सिंह", 6: "कन्या", 7: "तुला", 8: "वृश्चिक",
    9: "धनु", 10: "मकर", 11: "कुम्भ", 12: "मीन",
}
_NAKSHATRA_NE = [
    "", "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
    "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी",
    "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल",
    "पूर्वाषाढा", "उत्तराषाढा", "श्रवण", "धनिष्ठा", "शतभिषा",
    "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती",
]

_KOOTAS = [
    ("वर्ण",        "varna",       1, "कार्यप्रवृत्ति / सामाजिक स्वभाव र अहंकार मेल"),
    ("वश्य",        "vasya",       2, "पारस्परिक आकर्षण / प्रभाव तथा नियन्त्रण"),
    ("तारा",        "tara",        3, "भाग्य, आयु, स्वास्थ्य र कल्याण"),
    ("योनि",        "yoni",        4, "शारीरिक अनुकूलता, जैविक सुख र आकर्षण"),
    ("ग्रह मैत्री", "grah_maitri", 5, "मानसिक सामञ्जयता, विचार र मित्रता"),
    ("गण",          "gana",        6, "स्वभाव, व्यवहार र जीवनशैली अनुकूलता"),
    ("भकूट",        "bhakut",      7, "प्रेम, दाम्पत्य सुख, वंश वृद्धि र समृद्धि"),
    ("नाडी",        "nadi",        8, "स्वास्थ्य, आनुवंशिकता (Genes) र सन्तान सुख"),
]


def _score_color(got: float, mx: float) -> str:
    if mx == 0:
        return COLOR_TEXT_MUTED
    pct = got / mx * 100
    if pct >= 78:
        return "#22c55e"
    if pct >= 55:
        return "#f59e0b"
    return "#ef4444"


def julian_day_to_gregorian(jd: float) -> tuple[str, str]:
    """Convert Julian Day float to Gregorian (YYYY-MM-DD, HH:MM:SS)."""
    import math
    jd_adj = jd + 0.5
    Z = math.floor(jd_adj)
    F = jd_adj - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = math.floor((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - math.floor(alpha / 4)
    B = A + 1524
    C = math.floor((B - 122.1) / 365.25)
    D = math.floor(365.25 * C)
    E = math.floor((B - D) / 30.6001)
    day = int(B - D - math.floor(30.6001 * E))
    month = int(E - 1 if E < 14 else E - 13)
    year = int(C - 4716 if month > 2 else C - 4715)
    total_seconds = round(F * 86400)
    hour = int(total_seconds // 3600)
    minute = int((total_seconds % 3600) // 60)
    second = int(total_seconds % 60)
    return f"{year:04d}-{month:02d}-{day:02d}", f"{hour:02d}:{minute:02d}:{second:02d}"


def _load_chart_file(path: str) -> Dict[str, Any]:
    """Universal chart file loader for JSON, XML, QCK, and JHD files."""
    file_base = os.path.splitext(os.path.basename(path))[0].strip()

    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # Search across common top-level nesting
                for sub_key in ("metadata", "params", "chart_data", "birth_data", "kundali", "data", "birth_info"):
                    if sub_key in data and isinstance(data[sub_key], dict):
                        merged = dict(data[sub_key])
                        merged.update({k: v for k, v in data.items() if k != sub_key})
                        data = merged
                # Normalize keys
                if "birthDate" in data and "birth_date" not in data:
                    data["birth_date"] = data["birthDate"]
                if "birthTime" in data and "birth_time" not in data:
                    data["birth_time"] = data["birthTime"]
                if "birthPlace" in data and "city" not in data:
                    data["city"] = data["birthPlace"]
                if "birth_place" in data and "city" not in data:
                    data["city"] = data["birth_place"]
                if "lat" in data and "latitude" not in data:
                    data["latitude"] = data["lat"]
                if "lon" in data and "longitude" not in data:
                    data["longitude"] = data["lon"]
                if "tz" in data and "timezone" not in data:
                    data["timezone"] = data["tz"]
                if not data.get("name") or str(data.get("name")).lower() in ("chart", "unknown", "untitled"):
                    data["name"] = file_base or "कुण्डली"
                return data

    with open(path, "rb") as f:
        raw_bytes = f.read()

    text = None
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin1"):
        try:
            t = raw_bytes.decode(enc)
            if t.strip():
                text = t
                break
        except Exception:
            pass

    if text is None:
        text = raw_bytes.decode("utf-8", errors="replace")
    text = text.strip()

    # JHD format
    if not text.startswith("<") and path.lower().endswith(".jhd"):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) >= 7:
            m = int(lines[0])
            d = int(lines[1])
            y = int(lines[2])
            t_dec = float(lines[3])
            thour = int(t_dec)
            tmin = int((t_dec - thour) * 60)
            tsec = int(round(((t_dec - thour) * 60 - tmin) * 60))
            btime = f"{thour:02d}:{tmin:02d}:{tsec:02d}"
            tz = abs(float(lines[4]))
            lon = abs(float(lines[5]))
            lat = float(lines[6])
            name = lines[7] if (len(lines) > 7 and lines[7].strip()) else file_base
            return {
                "name": name,
                "birth_date": f"{y:04d}-{m:02d}-{d:02d}",
                "birth_time": btime,
                "latitude": lat,
                "longitude": lon,
                "timezone": tz,
                "city": "",
                "gender": 0,
                "ayanamsha_type": "LAHIRI",
            }

    if text.startswith("<?xml"):
        end_idx = text.find("?>")
        if end_idx != -1:
            text = text[end_idx + 2:].strip()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(text)
    el = root.find("BirthInfo")
    if el is None:
        el = root.find("birthinfo")
    if el is None:
        el = root

    tag_map = {child.tag.lower(): (child.text or "").strip() for child in el.iter() if child.tag}
    for child in root:
        if child.tag and child.tag.lower() not in tag_map:
            tag_map[child.tag.lower()] = (child.text or "").strip()

    raw_bdate = tag_map.get("birthdate") or tag_map.get("birth_date") or tag_map.get("date") or ""
    bdate = ""
    btime = "12:00:00"

    # Check if raw_bdate is a Julian Day float
    is_jd = False
    if raw_bdate:
        try:
            jd_val = float(raw_bdate)
            if jd_val > 1000000:
                bdate, btime = julian_day_to_gregorian(jd_val)
                is_jd = True
        except Exception:
            pass

    if not is_jd:
        if raw_bdate:
            bdate = raw_bdate
        raw_btime = tag_map.get("birthtime") or tag_map.get("birth_time") or tag_map.get("time") or ""
        if raw_btime:
            btime = raw_btime

    if not bdate:
        # A matching chart with an invented birth date would produce a real
        # looking 36-guna score for a person the file never described.
        raise ValueError("The chart file contains no birth date, so matching cannot be computed.")

    fname = tag_map.get("firstname", "")
    lname = tag_map.get("lastname", "")
    full = f"{fname} {lname}".strip()
    name_from_tag = tag_map.get("name") or tag_map.get("fullname") or full or ""

    if not name_from_tag or name_from_tag.lower() in ("chart", "unknown", "untitled", "kundali", "birthinfo"):
        name = file_base or "कुण्डली"
    else:
        name = name_from_tag

    try:
        lat = float(tag_map.get("latitude") or tag_map.get("lat") or 27.7172)
    except Exception:
        lat = 27.7172

    try:
        lon = abs(float(tag_map.get("longitude") or tag_map.get("lon") or 85.3240))
    except Exception:
        lon = 85.3240

    try:
        tz = abs(float(tag_map.get("timezone") or tag_map.get("tz") or 5.75))
    except Exception:
        tz = 5.75

    city = tag_map.get("city") or tag_map.get("birth_place") or tag_map.get("place") or ""
    try:
        gender = int(tag_map.get("gender") or 0)
    except Exception:
        gender = 0

    return {
        "name": name,
        "birth_date": bdate,
        "birth_time": btime,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "city": city,
        "gender": gender,
        "ayanamsha_type": tag_map.get("ayanamsha_type") or tag_map.get("ayanamsha") or "LAHIRI",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Person Birth Details Form Panel (नयाँ जन्म कुण्डली फाराम)
# ══════════════════════════════════════════════════════════════════════════════
class PersonChartInputPanel(QFrame):
    """
    वर वा वधूको लागि पूर्ण एवं मानक जन्म विवरण फाराम।
    - नाम, लिङ्ग
    - वि.सं. र ई.सं. दुवै पात्रो मोड
    - जन्म समय (घण्टा, मिनेट, सेकेन्ड)
    - देश, प्रदेश, जिल्ला, सहर/स्थान (Lat/Lon/TZ अटो-फिल)
    - बाह्य फाइलबाट कुण्डली खोल्ने (Upload)
    - यस कुण्डलीलाई डाटाबेसमा सुरक्षित (Save) गर्ने
    """

    chart_loaded = Signal()

    def __init__(self, prefix: str, title: str, icon: str, default_gender: int = 0, parent=None):
        super().__init__(parent)
        self._prefix = prefix
        self._title = title
        self._icon = icon
        self._default_gender = default_gender
        self._calendar_mode = "BS"
        self._cities = enrich_cities(get_all_cities())
        self._syncing_dates = False

        self._build_ui()
        self._populate_locations()
        self._init_defaults()

    def _build_ui(self):
        self.setStyleSheet(f"""
            PersonChartInputPanel {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            QLineEdit, QComboBox {{
                background: #ffffff;
                color: #111111;
                border: 1px solid #9ca3af;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 12px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1.5px solid #0284c7;
            }}
            QComboBox QAbstractItemView {{
                background: #ffffff;
                color: #111111;
                selection-background-color: #0284c7;
                selection-color: #ffffff;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        # ── Top Bar: Title & Action Buttons ──────────────────────────────────
        top_hbox = QHBoxLayout()
        title_lbl = QLabel(f"{self._icon} <b>{self._title}</b>")
        title_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 14px; font-weight: 800; border: none;")
        top_hbox.addWidget(title_lbl)
        top_hbox.addStretch()

        # Clear / Reset button
        self._clear_btn = QPushButton("🧹 खाली गर्नुहोस्")
        self._clear_btn.setToolTip("फाराम खाली गरी नयाँ विवरण भर्नुहोस्")
        self._clear_btn.setStyleSheet(
            f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 600;"
            f"border: 1px solid {BORDER_COLOR}; border-radius: 4px; padding: 3px 8px;"
        )
        self._clear_btn.clicked.connect(self.reset_form)
        top_hbox.addWidget(self._clear_btn)

        # File upload / open button
        self._open_btn = QPushButton("📁 फाइल खोल्नुहोस्")
        self._open_btn.setToolTip("कम्प्युटरबाट कुण्डली फाइल (.json, .xml, .jhd) खोल्नुहोस्")
        self._open_btn.setStyleSheet(
            f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: 600;"
            f"border: 1px solid {BORDER_COLOR}; border-radius: 4px; padding: 3px 8px;"
        )
        self._open_btn.clicked.connect(self._on_open_file)
        top_hbox.addWidget(self._open_btn)

        # Save to DB button
        self._save_btn = QPushButton("💾 कुण्डली सुरक्षित")
        self._save_btn.setToolTip("यो भरेको विवरणलाई पछि पुनः प्रयोग गर्न डाटाबेसमा सेभ गर्नुहोस्")
        self._save_btn.setStyleSheet(
            "background: #0284c7; color: #ffffff; font-size: 11px; font-weight: 700;"
            "border: none; border-radius: 4px; padding: 3px 8px;"
        )
        self._save_btn.clicked.connect(self._on_save_chart)
        top_hbox.addWidget(self._save_btn)

        layout.addLayout(top_hbox)

        # ── Saved Charts Quick Selector ──────────────────────────────────────
        saved_row = QHBoxLayout()
        saved_lbl = QLabel("सहेजिएको कुण्डली:")
        saved_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; border: none;")
        saved_row.addWidget(saved_lbl)

        self._saved_combo = QComboBox()
        self._saved_combo.setStyleSheet("font-size: 11px; padding: 2px 4px;")
        self._saved_combo.currentIndexChanged.connect(self._on_saved_selected)
        saved_row.addWidget(self._saved_combo, 1)
        layout.addLayout(saved_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"border: none; border-top: 1px solid {BORDER_COLOR};")
        layout.addWidget(sep1)

        # ── Grid Form ────────────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)

        # 1. Name & Gender
        grid.addWidget(self._flabel("नाम (Name):"), 0, 0)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("पुरा नाम लेख्नुहोस्")
        grid.addWidget(self._name_edit, 0, 1, 1, 3)

        # Gender radio group
        grid.addWidget(self._flabel("लिङ्ग (Gender):"), 1, 0)
        gender_box = QHBoxLayout()
        self._gender_group = QButtonGroup(self)
        self._rb_male = QRadioButton("पुरुष (Male)")
        self._rb_female = QRadioButton("महिला (Female)")
        self._rb_other = QRadioButton("अन्य (Other)")
        for rb in (self._rb_male, self._rb_female, self._rb_other):
            rb.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px;")
            gender_box.addWidget(rb)
            self._gender_group.addButton(rb)

        if self._default_gender == 1:
            self._rb_female.setChecked(True)
        else:
            self._rb_male.setChecked(True)
        grid.addLayout(gender_box, 1, 1, 1, 3)

        # 2. Calendar Selector (BS / AD)
        grid.addWidget(self._flabel("पात्रो (Calendar):"), 2, 0)
        cal_box = QHBoxLayout()
        self._cal_group = QButtonGroup(self)
        self._rb_bs = QRadioButton("वि.सं. (BS)")
        self._rb_ad = QRadioButton("ई.सं. (AD)")
        self._rb_bs.setChecked(True)
        for rb in (self._rb_bs, self._rb_ad):
            rb.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
            cal_box.addWidget(rb)
            self._cal_group.addButton(rb)
        self._rb_bs.toggled.connect(self._on_calendar_toggled)
        grid.addLayout(cal_box, 2, 1, 1, 3)

        # 3. Date Inputs (BS & AD)
        grid.addWidget(self._flabel("जन्म मिति:"), 3, 0)
        self._date_container = QWidget()
        date_lay = QHBoxLayout(self._date_container)
        date_lay.setContentsMargins(0, 0, 0, 0)
        date_lay.setSpacing(4)

        # BS Dropdowns
        self._bs_year_cb = SmartNepaliDateDropdown("year", minimum=1970, maximum=2099)
        self._bs_month_cb = SmartNepaliDateDropdown("month")
        self._bs_day_cb = SmartNepaliDateDropdown("day")
        self._bs_year_cb.valueChanged.connect(self._sync_bs_to_ad)
        self._bs_month_cb.valueChanged.connect(self._sync_bs_to_ad)
        self._bs_day_cb.valueChanged.connect(self._sync_bs_to_ad)

        date_lay.addWidget(self._bs_year_cb, 2)
        date_lay.addWidget(self._bs_month_cb, 2)
        date_lay.addWidget(self._bs_day_cb, 2)

        # AD Input
        self._ad_edit = QLineEdit()
        self._ad_edit.setPlaceholderText("YYYY-MM-DD")
        self._ad_edit.textEdited.connect(self._sync_ad_to_bs)
        self._ad_edit.hide()
        date_lay.addWidget(self._ad_edit, 6)

        grid.addWidget(self._date_container, 3, 1, 1, 3)

        # Live Date Conversion Label
        self._conv_lbl = QLabel("")
        self._conv_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 11px; font-style: italic; border: none;")
        grid.addWidget(self._conv_lbl, 4, 1, 1, 3)

        # 4. Birth Time (HH:MM:SS)
        grid.addWidget(self._flabel("जन्म समय:"), 5, 0)
        time_hbox = QHBoxLayout()
        time_hbox.setSpacing(4)
        self._time_edit = QLineEdit("12:00:00")
        self._time_edit.setPlaceholderText("HH:MM:SS (24 घण्टा)")
        time_hbox.addWidget(self._time_edit, 2)
        grid.addLayout(time_hbox, 5, 1, 1, 3)

        # 5. Location Hierarchy
        grid.addWidget(self._flabel("देश (Country):"), 6, 0)
        self._country_cb = QComboBox()
        self._country_cb.currentIndexChanged.connect(self._on_country_changed)
        grid.addWidget(self._country_cb, 6, 1, 1, 3)

        grid.addWidget(self._flabel("प्रदेश / जिल्ला:"), 7, 0)
        prov_dist_box = QHBoxLayout()
        prov_dist_box.setSpacing(4)
        self._region_cb = QComboBox()
        self._region_cb.currentIndexChanged.connect(self._on_region_changed)
        prov_dist_box.addWidget(self._region_cb, 1)

        self._dist_cb = QComboBox()
        self._dist_cb.currentIndexChanged.connect(self._on_district_changed)
        prov_dist_box.addWidget(self._dist_cb, 1)
        grid.addLayout(prov_dist_box, 7, 1, 1, 3)

        grid.addWidget(self._flabel("सहर / स्थान:"), 8, 0)
        self._city_cb = QComboBox()
        self._city_cb.setEditable(True)
        self._city_cb.currentIndexChanged.connect(self._on_city_changed)
        grid.addWidget(self._city_cb, 8, 1, 1, 3)

        # 6. Coordinates (Lat, Lon, TZ)
        grid.addWidget(self._flabel("अक्षांश / देशान्तर:"), 9, 0)
        coords_box = QHBoxLayout()
        coords_box.setSpacing(4)
        self._lat_edit = QLineEdit("27.7172")
        self._lat_edit.setPlaceholderText("Lat")
        self._lon_edit = QLineEdit("85.3240")
        self._lon_edit.setPlaceholderText("Lon")
        self._tz_edit = QLineEdit("5.75")
        self._tz_edit.setPlaceholderText("TZ")
        coords_box.addWidget(self._lat_edit, 1)
        coords_box.addWidget(self._lon_edit, 1)
        coords_box.addWidget(QLabel("समयक्षेत्र:"), 0)
        coords_box.addWidget(self._tz_edit, 1)
        grid.addLayout(coords_box, 9, 1, 1, 3)

        layout.addLayout(grid)

        # Status note on panel
        self._panel_status = QLabel("")
        self._panel_status.setStyleSheet("font-size: 11px; border: none;")
        layout.addWidget(self._panel_status)

    def _flabel(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: 600; border: none;")
        return lbl

    def _init_defaults(self):
        # Default to 2056-01-01 BS (~ 1999-04-14 AD)
        self._bs_year_cb.setValue(2056)
        self._bs_month_cb.setValue(1)
        self._bs_day_cb.setValue(1)
        self._sync_bs_to_ad()

    # ── Calendar & Date Synchronization ───────────────────────────────────────
    def _on_calendar_toggled(self):
        if self._rb_bs.isChecked():
            self._calendar_mode = "BS"
            self._bs_year_cb.show()
            self._bs_month_cb.show()
            self._bs_day_cb.show()
            self._ad_edit.hide()
            self._sync_bs_to_ad()
        else:
            self._calendar_mode = "AD"
            self._bs_year_cb.hide()
            self._bs_month_cb.hide()
            self._bs_day_cb.hide()
            self._ad_edit.show()
            self._sync_ad_to_bs()

    def _sync_bs_to_ad(self):
        if self._syncing_dates:
            return
        self._syncing_dates = True
        try:
            by = self._bs_year_cb.value()
            bm = self._bs_month_cb.value()
            bd = self._bs_day_cb.value()
            ad_res = convert_bs_to_ad(by, bm, bd)
            if ad_res and "ad_date" in ad_res:
                ad_str = ad_res["ad_date"]
                self._ad_edit.setText(ad_str)
                m_name = BS_MONTHS_NE[bm - 1] if 1 <= bm <= 12 else str(bm)
                self._conv_lbl.setText(f"ई.सं. (AD): {ad_str}  |  वि.सं.: {to_nepali_digits(by)} {m_name} {to_nepali_digits(bd)}")
        except Exception:
            pass
        finally:
            self._syncing_dates = False

    def _sync_ad_to_bs(self):
        if self._syncing_dates:
            return
        self._syncing_dates = True
        try:
            ad_text = self._ad_edit.text().strip()
            parts = ad_text.split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                bs_res = None
                try:
                    bs_res = convert_ad_to_bs(y, m, d)
                except Exception:
                    pass
                if not bs_res or "year" not in bs_res:
                    bs_res = gregorian_to_bs(y, m, d)
                if bs_res and "year" in bs_res:
                    by = int(bs_res["year"])
                    bm = int(bs_res["month"])
                    bd = int(bs_res["day"])
                    self._bs_year_cb.setValue(by)
                    self._bs_month_cb.setValue(bm)
                    self._bs_day_cb.setValue(bd)
                    m_name = BS_MONTHS_NE[bm - 1] if 1 <= bm <= 12 else str(bm)
                    self._conv_lbl.setText(
                        f"वि.सं. (BS): {to_nepali_digits(by)} {m_name} {to_nepali_digits(bd)}  |  ई.सं.: {ad_text}"
                    )
        except Exception:
            pass
        finally:
            self._syncing_dates = False

    # ── Location Hierarchies ──────────────────────────────────────────────────
    def _populate_locations(self):
        self._country_cb.blockSignals(True)
        self._country_cb.clear()
        try:
            country_list = countries(self._cities)
        except TypeError:
            country_list = countries()
        for c in country_list:
            lbl = c.get("label", c.get("name", str(c))) if isinstance(c, dict) else str(c)
            val = c.get("value", c.get("name", str(c))) if isinstance(c, dict) else str(c)
            self._country_cb.addItem(lbl, val)
        self._country_cb.setCurrentIndex(0)  # Nepal
        self._country_cb.blockSignals(False)
        self._on_country_changed()

    def _on_country_changed(self):
        country_val = self._country_cb.currentData() or "Nepal"
        try:
            regions = regions_for_country(country_val, self._cities)
        except TypeError:
            regions = regions_for_country(country_val)
        self._region_cb.blockSignals(True)
        self._region_cb.clear()
        self._region_cb.addItem("— सबै प्रदेश / क्षेत्र —", None)
        for r in regions:
            lbl = r.get("label", str(r)) if isinstance(r, dict) else str(r)
            val = r.get("value", str(r)) if isinstance(r, dict) else str(r)
            self._region_cb.addItem(lbl, val)
        self._region_cb.setCurrentIndex(0)
        self._region_cb.blockSignals(False)
        self._on_region_changed()

    def _on_region_changed(self):
        country_val = self._country_cb.currentData() or "Nepal"
        region_val = self._region_cb.currentData()
        try:
            districts = districts_for_region(country_val, region_val, self._cities)
        except TypeError:
            districts = districts_for_region(country_val, region_val)
        self._dist_cb.blockSignals(True)
        self._dist_cb.clear()
        self._dist_cb.addItem("— सबै जिल्ला —", None)
        for d in districts:
            lbl = d.get("label", str(d)) if isinstance(d, dict) else str(d)
            val = d.get("value", str(d)) if isinstance(d, dict) else str(d)
            self._dist_cb.addItem(lbl, val)
        self._dist_cb.setCurrentIndex(0)
        self._dist_cb.blockSignals(False)
        self._on_district_changed()

    def _on_district_changed(self):
        country_val = self._country_cb.currentData() or "Nepal"
        region_val = self._region_cb.currentData()
        district_val = self._dist_cb.currentData()

        # यदि जिल्ला चयन गरियो भने सोही जिल्लाको वास्तविक अक्षांश, देशान्तर र समयक्षेत्र स्वतः भर्ने
        meta = None
        if district_val:
            try:
                meta = district_metadata(country_val, district_val)
            except TypeError:
                meta = district_metadata(district_val)
            if meta:
                lat_val = meta.get("lat") if meta.get("lat") is not None else meta.get("latitude")
                lon_val = meta.get("lon") if meta.get("lon") is not None else meta.get("longitude")
                tz_val = meta.get("tz") if meta.get("tz") is not None else meta.get("timezone", 5.75)
                if lat_val is not None:
                    self._lat_edit.setText(str(lat_val))
                if lon_val is not None:
                    self._lon_edit.setText(str(lon_val))
                if tz_val is not None:
                    self._tz_edit.setText(str(tz_val))

        try:
            c_list = filtered_cities(self._cities, country_val, region_val, district_val)
        except Exception:
            c_list = []
        self._city_cb.blockSignals(True)
        self._city_cb.clear()

        dist_label = (meta.get("name_ne") or district_val) if meta else (district_val or "सहर/स्थान")
        if district_val:
            self._city_cb.addItem(f"— {dist_label} (जिल्ला स्वतः लागू) —", None)
        else:
            self._city_cb.addItem("— सहर/स्थान छान्नुहोस् वा लेख्नुहोस् —", None)

        for c in c_list:
            self._city_cb.addItem(c.get("name", ""), c)
        self._city_cb.setCurrentIndex(0)
        self._city_cb.blockSignals(False)

    def _on_city_changed(self):
        c_data = self._city_cb.currentData()
        if isinstance(c_data, dict):
            lat_v = c_data.get("lat") or c_data.get("latitude")
            lon_v = c_data.get("lon") or c_data.get("longitude")
            tz_v = c_data.get("tz") or c_data.get("timezone")
            if lat_v is not None:
                self._lat_edit.setText(str(lat_v))
            if lon_v is not None:
                self._lon_edit.setText(str(lon_v))
            if tz_v is not None:
                self._tz_edit.setText(str(tz_v))

    # ── Saved Charts Management ───────────────────────────────────────────────
    def refresh_saved_list(self, charts: list):
        self._saved_combo.blockSignals(True)
        self._saved_combo.clear()
        self._saved_combo.addItem("— सहेजिएको कुण्डली छान्नुहोस् —", None)
        for c in charts:
            label = f"{c.get('name', 'बेनामी')} ({c.get('birth_date', '')}, {c.get('birth_place') or c.get('city', '')})"
            self._saved_combo.addItem(label, c)
        self._saved_combo.setCurrentIndex(0)
        self._saved_combo.blockSignals(False)

    def _on_saved_selected(self, idx: int):
        data = self._saved_combo.currentData()
        if data and isinstance(data, dict):
            self.load_from_dict(data)
            self._panel_status.setText("✅ सहेजिएको कुण्डली सफलतापूर्वक लोड भयो।")
            self._panel_status.setStyleSheet("color: #16a34a; font-size: 11px; border: none;")

    # ── File Upload / Open ────────────────────────────────────────────────────
    def _on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"{self._title} — कुण्डली फाइल खोल्नुहोस्",
            "",
            "All Supported Chart Files (*.json *.xml *.qck *.jhd);;JSON Files (*.json);;XML / QCK Files (*.xml *.qck);;Jagannatha Hora (*.jhd);;All Files (*)"
        )
        if not path:
            return
        try:
            params = _load_chart_file(path)
            self.load_from_dict(params)
            fname = os.path.basename(path)
            pname = params.get("name") or self._name_edit.text() or "कुण्डली"
            self._panel_status.setText(f"✅ '{pname}' को डेटा फाइलबाट लोड भयो ({fname})")
            self._panel_status.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: bold; border: none;")
        except Exception as e:
            QMessageBox.critical(self, "फाइल त्रुटि", f"कुण्डली फाइल खोल्न सकिएन:\n{e}")

    # ── Save Chart to Database ────────────────────────────────────────────────
    def _on_save_chart(self):
        params = self.collect_params()
        if not params:
            return
        try:
            rec_id = save_chart(params)
            self._panel_status.setText(f"💾 कुण्डली सुरक्षित भयो! (ID: {rec_id})")
            self._panel_status.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: bold; border: none;")
            QMessageBox.information(
                self,
                "कुण्डली सुरक्षित",
                f"<b>{params.get('name')}</b> को कुण्डली सफलतापूर्वक डाटाबेसमा सुरक्षित भयो!\n\nयो कुण्डली अब एपका अन्य सबै पेजहरूमा प्रयोग गर्न सकिन्छ।"
            )
            self.chart_loaded.emit()
        except Exception as e:
            QMessageBox.critical(self, "सुरक्षित गर्न सकिएन", f"डाटाबेसमा सुरक्षित गर्दा त्रुटि:\n{e}")

    # ── Reset / Clear Form ───────────────────────────────────────────────────
    def reset_form(self):
        """फाराम खाली गरी नयाँ विवरण भर्न तयार गर्ने।"""
        self._name_edit.clear()
        if self._default_gender == 1:
            self._rb_female.setChecked(True)
        elif self._default_gender == 2:
            self._rb_other.setChecked(True)
        else:
            self._rb_male.setChecked(True)
        self._rb_bs.setChecked(True)
        self._calendar_mode = "BS"
        self._bs_year_cb.show()
        self._bs_month_cb.show()
        self._bs_day_cb.show()
        self._ad_edit.hide()
        self._init_defaults()
        self._time_edit.setText("12:00:00")
        self._populate_locations()
        self._saved_combo.blockSignals(True)
        self._saved_combo.setCurrentIndex(0)
        self._saved_combo.blockSignals(False)
        self._panel_status.setText("🧹 फाराम खाली गरियो। नयाँ विवरण भर्न वा फाइल खोल्न सक्नुहुन्छ।")
        self._panel_status.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 11px; border: none;")

    # ── Load from Dictionary ──────────────────────────────────────────────────
    def load_from_dict(self, d: Dict[str, Any]):
        if not d or not isinstance(d, dict):
            return

        # 1. Unnest if wrapped in metadata, chart_data, params, etc.
        for sub_key in ("metadata", "params", "chart_data", "birth_data", "kundali", "data", "birth_info"):
            if sub_key in d and isinstance(d[sub_key], dict):
                merged = dict(d[sub_key])
                merged.update({k: v for k, v in d.items() if k != sub_key})
                d = merged

        # 2. Extract Name
        name_val = (
            d.get("name") or d.get("Name") or d.get("full_name") or d.get("FullName")
            or d.get("client_name") or d.get("person_name") or ""
        )
        self._name_edit.setText(str(name_val))

        # 3. Extract Gender
        gender = d.get("gender") if d.get("gender") is not None else d.get("Gender")
        if gender is not None:
            g_str = str(gender).lower().strip()
            if g_str in ("1", "female", "f", "महिला", "स्त्री", "girl", "woman"):
                self._rb_female.setChecked(True)
            elif g_str in ("2", "other", "o", "अन्य"):
                self._rb_other.setChecked(True)
            else:
                self._rb_male.setChecked(True)
        else:
            if self._default_gender == 1:
                self._rb_female.setChecked(True)
            else:
                self._rb_male.setChecked(True)

        # 4. Extract Birth Time
        raw_time = (
            d.get("birth_time") or d.get("BirthTime") or d.get("time") or d.get("Time")
            or d.get("tob") or d.get("TOB") or "12:00:00"
        )
        time_clean = str(raw_time).strip()
        time_norm = normalize_birth_time(time_clean)
        self._time_edit.setText(time_norm or time_clean or "12:00:00")

        # 5. Extract Birth Date
        raw_date = (
            d.get("birth_date") or d.get("BirthDate") or d.get("date") or d.get("Date")
            or d.get("dob") or d.get("DOB") or "2000-01-01"
        )
        # Normalize date separators
        clean_date = str(raw_date).strip().split("T")[0].split(" ")[0].replace("/", "-").replace(".", "-")
        dp = clean_date.split("-")
        if len(dp) == 3:
            if len(dp[0]) == 4:
                bdate = f"{int(dp[0]):04d}-{int(dp[1]):02d}-{int(dp[2]):02d}"
            elif len(dp[2]) == 4:
                bdate = f"{int(dp[2]):04d}-{int(dp[0]):02d}-{int(dp[1]):02d}"
            else:
                bdate = f"{int(dp[0]):04d}-{int(dp[1]):02d}-{int(dp[2]):02d}"
        else:
            bdate = "2000-01-01"

        self._ad_edit.setText(bdate)

        # Check if BS date is explicitly supplied
        bs_y = d.get("bs_year") or d.get("bsYear") or d.get("year_bs")
        bs_m = d.get("bs_month") or d.get("bsMonth") or d.get("month_bs")
        bs_d = d.get("bs_day") or d.get("bsDay") or d.get("day_bs")
        bs_date_str = d.get("bs_date") or d.get("bsDate") or d.get("nepali_date")

        by, bm, bd = 2056, 1, 1
        if bs_y and bs_m and bs_d:
            by, bm, bd = int(bs_y), int(bs_m), int(bs_d)
        elif bs_date_str and "-" in str(bs_date_str):
            bsp = str(bs_date_str).strip().replace("/", "-").split("-")
            if len(bsp) == 3:
                by, bm, bd = int(bsp[0]), int(bsp[1]), int(bsp[2])
        else:
            parts = bdate.split("-")
            if len(parts) == 3:
                try:
                    y, m, d_num = int(parts[0]), int(parts[1]), int(parts[2])
                    bs_res = None
                    try:
                        bs_res = convert_ad_to_bs(y, m, d_num)
                    except Exception:
                        pass
                    if not bs_res or "year" not in bs_res:
                        bs_res = gregorian_to_bs(y, m, d_num)
                    if bs_res and "year" in bs_res:
                        by = int(bs_res["year"])
                        bm = int(bs_res["month"])
                        bd = int(bs_res["day"])
                except Exception:
                    pass

        self._syncing_dates = True
        try:
            self._bs_year_cb.setValue(by)
            self._bs_month_cb.setValue(bm)
            self._bs_day_cb.setValue(bd)
            m_name = BS_MONTHS_NE[bm - 1] if 1 <= bm <= 12 else str(bm)
            self._conv_lbl.setText(
                f"वि.सं. (BS): {to_nepali_digits(by)} {m_name} {to_nepali_digits(bd)}  |  ई.सं.: {bdate}"
            )
        finally:
            self._syncing_dates = False

        # 6. Extract Location
        country = d.get("country") or d.get("Country") or "Nepal"
        region = d.get("region") or d.get("Region") or d.get("province") or d.get("Province") or d.get("state") or d.get("State")
        district = d.get("district") or d.get("District")
        city = (
            d.get("city") or d.get("City") or d.get("birth_place") or d.get("BirthPlace")
            or d.get("place") or d.get("Place") or d.get("pob") or d.get("POB") or ""
        )

        if not district and country == "Nepal" and city:
            from gui.utils.location_data import NEPAL_CITY_DISTRICTS, province_for_district
            district = NEPAL_CITY_DISTRICTS.get(str(city).strip())
            if district and not region:
                region = province_for_district(district)

        if not region and district and country == "Nepal":
            from gui.utils.location_data import province_for_district
            region = province_for_district(district)

        # Set Country
        c_idx = self._country_cb.findData(country)
        if c_idx >= 0:
            self._country_cb.blockSignals(True)
            self._country_cb.setCurrentIndex(c_idx)
            self._country_cb.blockSignals(False)

        # Populate and set Region
        try:
            regions = regions_for_country(country, self._cities)
        except TypeError:
            regions = regions_for_country(country)
        self._region_cb.blockSignals(True)
        self._region_cb.clear()
        self._region_cb.addItem("— सबै प्रदेश / क्षेत्र —", None)
        for r in regions:
            lbl = r.get("label", str(r)) if isinstance(r, dict) else str(r)
            val = r.get("value", str(r)) if isinstance(r, dict) else str(r)
            self._region_cb.addItem(lbl, val)
        if region:
            r_idx = self._region_cb.findData(region)
            if r_idx >= 0:
                self._region_cb.setCurrentIndex(r_idx)
        else:
            self._region_cb.setCurrentIndex(0)
        self._region_cb.blockSignals(False)

        # Populate and set District
        region_val = self._region_cb.currentData()
        try:
            districts = districts_for_region(country, region_val, self._cities)
        except TypeError:
            districts = districts_for_region(country, region_val)
        self._dist_cb.blockSignals(True)
        self._dist_cb.clear()
        self._dist_cb.addItem("— सबै जिल्ला —", None)
        for dist_item in districts:
            lbl = dist_item.get("label", str(dist_item)) if isinstance(dist_item, dict) else str(dist_item)
            val = dist_item.get("value", str(dist_item)) if isinstance(dist_item, dict) else str(dist_item)
            self._dist_cb.addItem(lbl, val)
        if district:
            d_idx = self._dist_cb.findData(district)
            if d_idx >= 0:
                self._dist_cb.setCurrentIndex(d_idx)
        else:
            self._dist_cb.setCurrentIndex(0)
        self._dist_cb.blockSignals(False)

        # Populate and set City
        district_val = self._dist_cb.currentData()
        meta = None
        if district_val:
            try:
                meta = district_metadata(country, district_val)
            except Exception:
                meta = None

        try:
            c_list = filtered_cities(self._cities, country, region_val, district_val)
        except Exception:
            c_list = []
        self._city_cb.blockSignals(True)
        self._city_cb.clear()
        dist_label = (meta.get("name_ne") or district_val) if meta else (district_val or "सहर/स्थान")
        if district_val:
            self._city_cb.addItem(f"— {dist_label} (जिल्ला स्वतः लागू) —", None)
        else:
            self._city_cb.addItem("— सहर/स्थान छान्नुहोस् वा लेख्नुहोस् —", None)
        for c in c_list:
            self._city_cb.addItem(c.get("name", ""), c)
        if city:
            self._city_cb.setEditText(str(city))
        else:
            self._city_cb.setCurrentIndex(0)
        self._city_cb.blockSignals(False)

        # 7. Coordinates
        lat = d.get("latitude") if d.get("latitude") is not None else d.get("lat")
        if lat is None:
            lat = d.get("Latitude") or d.get("Lat")
        lon = d.get("longitude") if d.get("longitude") is not None else d.get("lon")
        if lon is None:
            lon = d.get("Longitude") or d.get("Lon") or d.get("lng") or d.get("Lng")
        tz = d.get("timezone") if d.get("timezone") is not None else d.get("tz")
        if tz is None:
            tz = d.get("TimeZone") or d.get("Tz")

        if lat is not None:
            self._lat_edit.setText(str(lat))
        elif meta and "lat" in meta:
            self._lat_edit.setText(str(meta["lat"]))

        if lon is not None:
            self._lon_edit.setText(str(lon))
        elif meta and "lon" in meta:
            self._lon_edit.setText(str(meta["lon"]))

        if tz is not None:
            self._tz_edit.setText(str(tz))
        elif meta and "tz" in meta:
            self._tz_edit.setText(str(meta["tz"]))

    # ── Collect & Validate Parameters ─────────────────────────────────────────
    def collect_params(self) -> Optional[Dict[str, Any]]:
        name = self._name_edit.text().strip()
        if not name:
            self._panel_status.setText(f"❌ {self._title}को 'नाम' भर्नुहोस्!")
            self._panel_status.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: bold; border: none;")
            return None

        # Ensure AD birth_date is valid
        ad_date = self._ad_edit.text().strip()
        if not ad_date:
            self._sync_bs_to_ad()
            ad_date = self._ad_edit.text().strip()

        try:
            parts = ad_date.split("-")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            datetime.date(y, m, d)
            birth_date = f"{y:04d}-{m:02d}-{d:02d}"
        except Exception:
            self._panel_status.setText("❌ जन्म मिति YYYY-MM-DD हुनुपर्छ।")
            self._panel_status.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: bold; border: none;")
            return None

        # Birth time
        time_raw = self._time_edit.text().strip()
        birth_time = normalize_birth_time(time_raw)
        if not birth_time:
            birth_time = "12:00:00"

        country_val = self._country_cb.currentData() or "Nepal"
        region_val = self._region_cb.currentData()
        district_val = self._dist_cb.currentData()

        meta = None
        if district_val:
            try:
                meta = district_metadata(country_val, district_val)
            except TypeError:
                meta = district_metadata(district_val)

        city = self._city_cb.currentText().strip()
        # यदि सहर/स्थान खालि भएमा वा प्रम्प्ट मात्र भएमा जिल्लाको नाम प्रयोग गर्ने
        if not city or "छान्नुहोस्" in city or city.startswith("—") or "ऐच्छिक" in city or "लागू" in city:
            if meta:
                city = meta.get("name_ne") or meta.get("name") or district_val
            elif district_val:
                city = district_val
            else:
                city = "काठमाडौं"

        # यदि अक्षांश/देशान्तर खालि छ भने जिल्लाको प्रयोग गर्ने
        if meta:
            lat_str = self._lat_edit.text().strip()
            lon_str = self._lon_edit.text().strip()
            tz_str = self._tz_edit.text().strip()
            if not lat_str:
                lat_v = meta.get("lat") or meta.get("latitude")
                if lat_v is not None:
                    lat = float(lat_v)
                    self._lat_edit.setText(str(lat))
            if not lon_str:
                lon_v = meta.get("lon") or meta.get("longitude")
                if lon_v is not None:
                    lon = float(lon_v)
                    self._lon_edit.setText(str(lon))
            if not tz_str:
                tz_v = meta.get("tz") or meta.get("timezone", 5.75)
                if tz_v is not None:
                    tz = float(tz_v)
                    self._tz_edit.setText(str(tz))

        try:
            lat = float(self._lat_edit.text().strip() or (meta.get("lat") if meta else 27.7172))
            lon = float(self._lon_edit.text().strip() or (meta.get("lon") if meta else 85.3240))
            tz = float(self._tz_edit.text().strip() or (meta.get("tz") if meta else 5.75))
        except ValueError:
            self._panel_status.setText("❌ अक्षांश, देशान्तर र समयक्षेत्र संख्या हुनुपर्छ।")
            self._panel_status.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: bold; border: none;")
            return None

        gender = 1 if self._rb_female.isChecked() else (2 if self._rb_other.isChecked() else 0)

        self._panel_status.setText("")
        return {
            "name": name,
            "gender": gender,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "city": city,
            "birth_place": city,
            "country": country_val,
            "region": region_val,
            "district": district_val,
            "ayanamsha_type": "LAHIRI",
            "calculation_siddhanta": "DRIK",
            "house_system": "WHOLE_SIGN",
            "node_type": "MEAN",
        }


# ══════════════════════════════════════════════════════════════════════════════
# Main Marriage Matching Page (विवाह मिलान मुख्य विजेट)
# ══════════════════════════════════════════════════════════════════════════════
class MarriageMatchingWidget(QWidget):
    """
    विवाह मिलान — अष्टकूट गुण मिलान, मंगल दोष (D1 + चन्द्र कुण्डली), सहेजिएको वा फाइलबाट अपलोड।
    """

    def __init__(self, language: str = "ne", parent=None):
        super().__init__(parent)
        self._saved_charts: list = []
        self._build_ui()
        self.reload_saved_charts()

    def reload_saved_charts(self):
        try:
            self._saved_charts = list_charts()
        except Exception:
            self._saved_charts = []
        self._boy_panel.refresh_saved_list(self._saved_charts)
        self._girl_panel.refresh_saved_list(self._saved_charts)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Full Page Unified Scroll Area ─────────────────────────────────────
        self._page_scroll = QScrollArea()
        self._page_scroll.setWidgetResizable(True)
        self._page_scroll.setFrameShape(QFrame.NoFrame)
        self._page_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {BG_PRIMARY}; }}")

        self._page_container = QWidget()
        self._page_container.setStyleSheet(f"background: {BG_PRIMARY}; color: {COLOR_TEXT_PRIMARY};")
        root = QVBoxLayout(self._page_container)
        root.setContentsMargins(14, 12, 14, 28)
        root.setSpacing(10)

        self._page_scroll.setWidget(self._page_container)
        main_layout.addWidget(self._page_scroll)

        # Header Title & Top Controls
        hdr_box = QHBoxLayout()
        hdr_lbl = QLabel("💑 विवाह मिलान — अष्टकूट ३६ गुण तथा मंगल दोष विश्लेषण")
        hdr_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 19px; font-weight: 800; border: none;")
        hdr_box.addWidget(hdr_lbl)
        hdr_box.addStretch()

        # Toggle Forms Button (Hide/Show Input Panels)
        self._toggle_forms_btn = QPushButton("🔼 इनपुट फाराम लुकाउनुहोस्")
        self._toggle_forms_btn.setToolTip("फाराम लुकाएर सम्पूर्ण नतिजा ठूलो स्क्रिनमा हेर्नुहोस्")
        self._toggle_forms_btn.setStyleSheet(
            f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 700;"
            f"border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 4px 12px;"
        )
        self._toggle_forms_btn.clicked.connect(self._toggle_forms)
        hdr_box.addWidget(self._toggle_forms_btn)

        # Refresh saved charts button
        ref_btn = QPushButton("🔄 सहेजिएका कुण्डली ताजा गर्नुहोस्")
        ref_btn.setStyleSheet(
            f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 600;"
            f"border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 4px 12px;"
        )
        ref_btn.clicked.connect(self.reload_saved_charts)
        hdr_box.addWidget(ref_btn)

        root.addLayout(hdr_box)

        # ── Collapsible Forms Container (Dual Panels for Boy & Girl) ─────────
        self._forms_container = QWidget()
        forms_vb = QVBoxLayout(self._forms_container)
        forms_vb.setContentsMargins(0, 0, 0, 0)
        forms_vb.setSpacing(10)

        panels_hbox = QHBoxLayout()
        panels_hbox.setSpacing(10)

        self._boy_panel = PersonChartInputPanel("boy", "वर (केटा) को जन्म कुण्डली विवरण", "👦", default_gender=0)
        self._boy_panel.chart_loaded.connect(self.reload_saved_charts)
        panels_hbox.addWidget(self._boy_panel, 1)

        self._girl_panel = PersonChartInputPanel("girl", "वधू (केटी) को जन्म कुण्डली विवरण", "👧", default_gender=1)
        self._girl_panel.chart_loaded.connect(self.reload_saved_charts)
        panels_hbox.addWidget(self._girl_panel, 1)

        forms_vb.addLayout(panels_hbox)
        root.addWidget(self._forms_container)

        # ── Calculate Compatibility Action Bar ────────────────────────────────
        act_box = QHBoxLayout()
        self._calc_btn = QPushButton("🧮  विवाह गुण मिलान तथा मंगल दोष गणना गर्नुहोस्")
        self._calc_btn.setFixedHeight(38)
        self._calc_btn.setCursor(Qt.PointingHandCursor)
        self._calc_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_GOLD};
                color: #000000;
                font-size: 14px;
                font-weight: 800;
                border-radius: 6px;
                padding: 6px 20px;
            }}
            QPushButton:hover {{
                background: #facc15;
            }}
        """)
        self._calc_btn.clicked.connect(self._calculate)
        act_box.addWidget(self._calc_btn, 1)
        root.addLayout(act_box)

        self._status = QLabel("वर र वधूको विवरण भरी वा फाइल खोल्नुहोस् अनि 'गुण मिलान गणना' थिच्नुहोस्।")
        self._status.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; border: none;")
        root.addWidget(self._status)

        # ── Large Output Results Container (Flows naturally in page scroll) ────
        self._out_w = QWidget()
        self._out_vb = QVBoxLayout(self._out_w)
        self._out_vb.setContentsMargins(0, 4, 0, 8)
        self._out_vb.setSpacing(12)

        root.addWidget(self._out_w)

    def _toggle_forms(self):
        is_vis = self._forms_container.isVisible()
        self._forms_container.setVisible(not is_vis)
        if is_vis:
            self._toggle_forms_btn.setText("🔽 इनपुट फाराम देखाउनुहोस् (Show Form)")
        else:
            self._toggle_forms_btn.setText("🔼 इनपुट फाराम लुकाउनुहोस् (Hide Form)")

    def _clear_out(self):
        while self._out_vb.count():
            item = self._out_vb.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_section(self, title: str, body: QWidget, border_color: str = None):
        sec = QFrame()
        bc = border_color or BORDER_COLOR
        sec.setStyleSheet(f"""
            QFrame {{
                background: {BG_SECONDARY};
                border: 1px solid {bc};
                border-radius: 8px;
            }}
        """)
        vb = QVBoxLayout(sec)
        vb.setContentsMargins(14, 10, 14, 12)
        vb.setSpacing(8)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {border_color or COLOR_GOLD}; font-size: 15px; font-weight: 800; border: none;")
        vb.addWidget(t_lbl)
        vb.addWidget(body)
        self._out_vb.addWidget(sec)

    def _hrow(self, label_text: str, value_text: str, lw: int = 220, bold_val: bool = False, color_val: str = None) -> QWidget:
        row = QWidget()
        row.setStyleSheet("border: none;")
        hb = QHBoxLayout(row)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(6)
        l = QLabel(label_text)
        l.setFixedWidth(lw)
        l.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; border: none;")
        v = QLabel(value_text)
        v.setWordWrap(True)
        v.setStyleSheet(f"color: {color_val or COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: {'700' if bold_val else '400'}; border: none;")
        hb.addWidget(l)
        hb.addWidget(v, 1)
        return row

    def _get_nakshatra_idx(self, chart: dict) -> int:
        for p in chart.get("planets", []):
            if p.get("name") == "Moon":
                lon = float(p.get("sidereal_longitude") or p.get("longitude", 0))
                return int(lon / (360 / 27)) % 27 + 1
        return 0

    # ── Calculation Engine ────────────────────────────────────────────────────
    def _calculate(self):
        self._clear_out()
        boy_p = self._boy_panel.collect_params()
        if not boy_p:
            return
        girl_p = self._girl_panel.collect_params()
        if not girl_p:
            return

        self._status.setText("🔄 गुण मिलान एवं मंगल दोष गणना हुँदैछ...")
        try:
            from gui.backend_bridge import calculate_chart, calculate_marriage_match

            compat_res = calculate_marriage_match(boy_p, girl_p)["compatibility"]
            a = compat_res.get("ashtakoot", {})

            _keys = ("name", "birth_date", "birth_time", "latitude", "longitude", "timezone", "city", "ayanamsha_type")
            boy_chart = calculate_chart(**{k: v for k, v in boy_p.items() if k in _keys})
            girl_chart = calculate_chart(**{k: v for k, v in girl_p.items() if k in _keys})

        except Exception as exc:
            self._status.setText(f"❌ गणना त्रुटि: {exc}")
            self._status.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: bold; border: none;")
            return

        score = a.get("total_score", 0)
        mx = a.get("max_score", 36)
        sc_color = _score_color(score, mx)
        b_name = boy_p.get("name", "वर")
        g_name = girl_p.get("name", "वधू")

        # ── 1. Overall Result Banner ──────────────────────────────────────────
        res_w = QWidget()
        res_w.setStyleSheet("border: none;")
        rb = QVBoxLayout(res_w)
        rb.setContentsMargins(0, 0, 0, 0)
        rb.setSpacing(6)

        score_lbl = QLabel(f"कुल प्राप्ताङ्क: {to_nepali_digits(score)} / {to_nepali_digits(mx)}")
        score_lbl.setStyleSheet(f"color: {sc_color}; font-size: 28px; font-weight: 900; border: none;")
        rb.addWidget(score_lbl)

        gauge = GunaScoreGauge(score, mx, sc_color)
        rb.addWidget(gauge)

        rec_lbl = QLabel(f"✦ <b>शास्त्रीय सुझाव:</b> {compat_res.get('recommendation', '')}")
        rec_lbl.setWordWrap(True)
        rec_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; border: none;")
        rb.addWidget(rec_lbl)

        self._add_section("📊  समग्र विवाह मिलान परिणाम", res_w, sc_color)

        # ── 2. Ashtakoot Table ────────────────────────────────────────────────
        details = a.get("details", {})
        tbl = QTableWidget(len(_KOOTAS), 6)
        tbl.setHorizontalHeaderLabels([
            "कूट (Koota)", f"वर ({b_name})", f"वधू ({g_name})",
            "प्राप्त गुण", "अधिकतम गुण", "के हेरिन्छ (महत्व / विषय)"
        ])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(f"""
            QTableWidget {{
                background: {BG_TERTIARY};
                color: {COLOR_TEXT_PRIMARY};
                font-size: 13px;
                gridline-color: {BORDER_COLOR};
                border: none;
            }}
            QHeaderView::section {{
                background: {BG_SECONDARY};
                color: {COLOR_GOLD};
                font-weight: 700;
                padding: 6px;
                border: 1px solid {BORDER_COLOR};
            }}
            QTableWidget::item:alternate {{
                background: rgba(255,255,255,0.03);
            }}
        """)
        tbl.setFixedHeight(len(_KOOTAS) * 34 + 44)

        for row, (label, key, mx_k, desc) in enumerate(_KOOTAS):
            dt = details.get(f"{key}_detail")
            got = a.get(key, 0)
            clr = _score_color(got, mx_k)

            boy_val = str(dt.get("boy", "—") if isinstance(dt, dict) else (dt or "—"))
            girl_val = str(dt.get("girl", "—") if isinstance(dt, dict) else (dt or "—"))

            tbl.setItem(row, 0, QTableWidgetItem(label))
            tbl.setItem(row, 1, QTableWidgetItem(boy_val))
            tbl.setItem(row, 2, QTableWidgetItem(girl_val))

            score_item = QTableWidgetItem(f"{to_nepali_digits(got)}")
            score_item.setForeground(QColor(clr))
            f = score_item.font()
            f.setBold(True)
            score_item.setFont(f)
            tbl.setItem(row, 3, score_item)
            tbl.setItem(row, 4, QTableWidgetItem(f"{to_nepali_digits(mx_k)}"))
            
            desc_item = QTableWidgetItem(desc)
            desc_item.setForeground(QColor(COLOR_TEXT_MUTED))
            tbl.setItem(row, 5, desc_item)

        self._add_section("🔢  अष्टकूट गुण विवरण तालिका (36 Gun Table)", tbl)

        # ── 3. Dosha Testing (दोष परीक्षण) ───────────────────────────────────
        dosha_w = QWidget()
        dosha_w.setStyleSheet("border: none;")
        dvb = QVBoxLayout(dosha_w)
        dvb.setContentsMargins(0, 0, 0, 0)
        dvb.setSpacing(6)

        nadi_d = a.get("nadi_dosha", False)
        bhakut_d = a.get("bhakut_dosha", False)
        gana_c = a.get("gana_conflict", False)
        yoni_c = a.get("yoni_conflict", "अनुकूल")
        tara_c = a.get("tara_conflict", False)
        tara_val = a.get("tara", 3)

        nadi_txt = "🔴 छ (नाडी दोष उपस्थित — वंश/स्वास्थ्यमा विचारणीय)" if nadi_d else "✅ छैन (अनुकूल)"
        nadi_clr = COLOR_ERROR if nadi_d else "#22c55e"

        bhakut_txt = "🔴 छ (भकूट दोष उपस्थित — दाम्पत्य/आर्थिक विचारणीय)" if bhakut_d else "✅ छैन (अनुकूल)"
        bhakut_clr = COLOR_ERROR if bhakut_d else "#22c55e"

        gana_txt = "🔴 छ (देव/राक्षस वा नर/राक्षस विरोध)" if gana_c else "✅ छैन (अनुकूल)"
        gana_clr = COLOR_ERROR if gana_c else "#22c55e"

        if yoni_c == "शत्रु":
            yoni_txt = "🔴 शत्रु योनि (परस्पर विरोध)"
            yoni_clr = COLOR_ERROR
        elif yoni_c == "सामान्य":
            yoni_txt = "🟡 सामान्य (मध्यम)"
            yoni_clr = "#f59e0b"
        else:
            yoni_txt = "✅ अनुकूल (मित्र वा समान)"
            yoni_clr = "#22c55e"

        if tara_c:
            tara_txt = "🔴 अनुपयुक्त (अशुभ तारा)"
            tara_clr = COLOR_ERROR
        elif tara_val == 1.5:
            tara_txt = "🟡 मध्यम (एकतर्फी शुभ तारा)"
            tara_clr = "#f59e0b"
        else:
            tara_txt = "✅ अनुकूल (शुभ तारा)"
            tara_clr = "#22c55e"

        dvb.addWidget(self._hrow("नाडी दोष:", nadi_txt, 140, bold_val=True, color_val=nadi_clr))
        dvb.addWidget(self._hrow("भकूट दोष:", bhakut_txt, 140, bold_val=True, color_val=bhakut_clr))
        dvb.addWidget(self._hrow("गण विरोध:", gana_txt, 140, bold_val=True, color_val=gana_clr))
        dvb.addWidget(self._hrow("योनि सम्बन्ध:", yoni_txt, 140, bold_val=True, color_val=yoni_clr))
        dvb.addWidget(self._hrow("तारा अनुकूलता:", tara_txt, 140, bold_val=True, color_val=tara_clr))

        self._add_section("🛡️  दोष परीक्षण एवं कूट विरोध विश्लेषण", dosha_w, COLOR_GOLD)

        # ── 4. Bhakut Mahadosh Alert ──────────────────────────────────────────
        if a.get("bhakut_mahadosh"):
            bm_box = QWidget()
            bm_box.setStyleSheet("border: none;")
            bml = QVBoxLayout(bm_box)
            bml.setContentsMargins(0, 0, 0, 0)
            bm_text = (
                "⚠️ <b>भकूट महादोष:</b> " + a.get("bhakut_mahadosh_note", "")
                + "<br/><br/><i>भकूट दोषले दाम्पत्य जीवनमा आर्थिक कठिनाइ, स्वास्थ्य समस्या वा मतभेद निम्त्याउन सक्छ। यसको शान्ति एवं ज्योतिषीय परामर्श लिनु उपयुक्त हुन्छ।</i>"
            )
            bm_lbl = QLabel(bm_text)
            bm_lbl.setWordWrap(True)
            bm_lbl.setStyleSheet(f"color: {COLOR_ERROR}; font-size: 13px; border: none;")
            bml.addWidget(bm_lbl)
            self._add_section("🔴  भकूट महादोष चेतावनी", bm_box, COLOR_ERROR)

        # ── 4. Mangal Dosha (D1 Lagna + Chandra Kundali) ──────────────────────
        boy_d1_mangal = compat_res.get("boy_mangal_dosh", {})
        girl_d1_mangal = compat_res.get("girl_mangal_dosh", {})

        # Compute Moon Chart Mangal Dosha directly
        def _mangal_moon(chart):
            msign, mars_sign = None, None
            for p in chart.get("planets", []):
                if p.get("name") == "Moon":
                    msign = int(p.get("sign_number", 0))
                if p.get("name") == "Mars":
                    mars_sign = int(p.get("sign_number", 0))
            if not msign or not mars_sign:
                return {"has_mangal": False, "house": None, "cancel": False}
            h_from_moon = ((mars_sign - msign) % 12) + 1
            has_d = h_from_moon in [1, 4, 7, 8, 12]
            can = mars_sign in [1, 8, 10]
            return {"has_mangal": has_d and not can, "house": h_from_moon, "cancel": can}

        boy_moon_m = _mangal_moon(boy_chart)
        girl_moon_m = _mangal_moon(girl_chart)

        mangal_w = QWidget()
        mangal_w.setStyleSheet("border: none;")
        mvb = QVBoxLayout(mangal_w)
        mvb.setContentsMargins(0, 0, 0, 0)
        mvb.setSpacing(6)

        def _fmt_mangal(d1: dict, mn: dict, person_lbl: str):
            pw = QWidget()
            pw.setStyleSheet("border: none;")
            pvb = QVBoxLayout(pw)
            pvb.setContentsMargins(0, 0, 0, 0)
            pvb.setSpacing(3)

            # D1
            d1_has = d1.get("has_mangal_dosh", False)
            d1_h = d1.get("mars_house", "?")
            d1_cancel = d1.get("cancellation_possible", False)
            if not d1_has:
                d1_t = "✅ मंगल दोष छैन"
                d1_c = "#22c55e"
            elif d1_cancel:
                d1_t = f"⚠️ मंगल दोष (निरसन सम्भव) — {to_nepali_digits(d1_h)} औं भाव"
                d1_c = "#f59e0b"
            else:
                d1_t = f"🔴 मंगल दोष छ — {to_nepali_digits(d1_h)} औं भाव"
                d1_c = "#ef4444"

            # Moon
            m_has = mn.get("has_mangal", False)
            m_h = mn.get("house", "?")
            m_cancel = mn.get("cancel", False)
            if not m_has:
                mn_t = "✅ मंगल दोष छैन"
                mn_c = "#22c55e"
            elif m_cancel:
                mn_t = f"⚠️ मंगल दोष (निरसन सम्भव) — चन्द्रबाट {to_nepali_digits(m_h)} औं भाव"
                mn_c = "#f59e0b"
            else:
                mn_t = f"🔴 मंगल दोष छ — चन्द्रबाट {to_nepali_digits(m_h)} औं भाव"
                mn_c = "#ef4444"

            pvb.addWidget(self._hrow(f"{person_lbl} — लग्न कुण्डली (D1):", d1_t, 240, bold_val=True, color_val=d1_c))
            pvb.addWidget(self._hrow(f"{person_lbl} — चन्द्र कुण्डली:", mn_t, 240, bold_val=True, color_val=mn_c))
            return pw

        mvb.addWidget(_fmt_mangal(boy_d1_mangal, boy_moon_m, f"👦 {b_name}"))

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border: none; border-top: 1px solid {BORDER_COLOR};")
        mvb.addWidget(sep)

        mvb.addWidget(_fmt_mangal(girl_d1_mangal, girl_moon_m, f"👧 {g_name}"))

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"border: none; border-top: 1px solid {BORDER_COLOR};")
        mvb.addWidget(sep2)

        # Comparative summary
        b_any = boy_d1_mangal.get("has_mangal_dosh") or boy_moon_m.get("has_mangal")
        g_any = girl_d1_mangal.get("has_mangal_dosh") or girl_moon_m.get("has_mangal")
        if b_any and g_any:
            m_concl = "✅ दुवैमा मंगल दोष — परस्पर निरसन हुन्छ (विवाहका लागि दोष निवारण भएको मानिन्छ)।"
            m_clr = "#22c55e"
        elif b_any or g_any:
            m_concl = "⚠️ केवल एक पक्षमा मंगल दोष — विवाह पूर्व मंगल शान्ति वा विशेष ज्योतिषीय विचार आवश्यक।"
            m_clr = "#f59e0b"
        else:
            m_concl = "✅ दुवै पक्षमा मंगल दोष छैन — दाम्पत्यका लागि सर्वथा अनुकूल।"
            m_clr = "#22c55e"

        concl_lbl = QLabel(f"<b>मंगल दोष समग्र निष्कर्ष:</b> {m_concl}")
        concl_lbl.setWordWrap(True)
        concl_lbl.setStyleSheet(f"color: {m_clr}; font-size: 13px; border: none; padding-top: 4px;")
        mvb.addWidget(concl_lbl)

        self._add_section("🔥  मंगल दोष विश्लेषण (D1 लग्न + चन्द्र कुण्डली दुवैबाट)", mangal_w, "#f59e0b")

        # ── 5. Moon Sign and Nakshatra Details ────────────────────────────────
        boy_moon = a.get("boy_moon_sign", 0)
        girl_moon = a.get("girl_moon_sign", 0)
        boy_nak = self._get_nakshatra_idx(boy_chart)
        girl_nak = self._get_nakshatra_idx(girl_chart)

        moon_w = QWidget()
        moon_w.setStyleSheet("border: none;")
        moon_vb = QVBoxLayout(moon_w)
        moon_vb.setContentsMargins(0, 0, 0, 0)
        moon_vb.setSpacing(4)

        moon_vb.addWidget(self._hrow(f"👦 {b_name} — चन्द्र राशि:", _RASHI_NE.get(boy_moon, str(boy_moon)), bold_val=True))
        moon_vb.addWidget(self._hrow(f"👦 {b_name} — जन्म नक्षत्र:", _NAKSHATRA_NE[boy_nak] if 0 < boy_nak <= 27 else "—", bold_val=True))
        moon_vb.addWidget(self._hrow(f"👧 {g_name} — चन्द्र राशि:", _RASHI_NE.get(girl_moon, str(girl_moon)), bold_val=True))
        moon_vb.addWidget(self._hrow(f"👧 {g_name} — जन्म नक्षत्र:", _NAKSHATRA_NE[girl_nak] if 0 < girl_nak <= 27 else "—", bold_val=True))

        self._add_section("🌙  चन्द्र राशि एवं जन्म नक्षत्र विवरण", moon_w)

        # ── 6. Dosha Remedies and Vedic Shanti ────────────────────────────────
        alerts = compat_res.get("dosha_alerts", [])
        if alerts:
            al_w = QWidget()
            al_w.setStyleSheet("border: none;")
            al_l = QVBoxLayout(al_w)
            al_l.setContentsMargins(0, 0, 0, 0)
            al_l.setSpacing(6)
            for alt in alerts:
                c_lbl = QLabel(f"⚠️ <b>{alt['dosha']} ({alt['severity']}):</b> {alt['remedy']}")
                c_lbl.setWordWrap(True)
                c_lbl.setStyleSheet("background: #fef2f2; color: #991b1b; padding: 8px 12px; border-radius: 6px; border: 1px solid #fecaca; font-size: 13px;")
                al_l.addWidget(c_lbl)
            self._add_section("🛡️  दोष निवारण तथा वैदिक शान्ति उपायहरू", al_w, "#dc2626")

        # ── 7. Planetary Synastry Harmony ────────────────────────────────────
        syn = compat_res.get("synastry", [])
        if syn:
            syn_w = QWidget()
            syn_w.setStyleSheet("border: none;")
            syn_l = QVBoxLayout(syn_w)
            syn_l.setContentsMargins(0, 0, 0, 0)
            syn_l.setSpacing(6)
            for s_item in syn:
                s_lbl = QLabel(f"✨ <b>{s_item['pair']}:</b> {s_item['nepali']}")
                s_lbl.setWordWrap(True)
                s_lbl.setStyleSheet("background: #f0fdf4; color: #166534; padding: 8px 12px; border-radius: 6px; border: 1px solid #bbf7d0; font-size: 13px;")
                syn_l.addWidget(s_lbl)
            self._add_section("🌌  ग्रह सिनेस्ट्री एवं भावनात्मक सामञ्जस्य (Synastry)", syn_w, "#16a34a")

        self._out_vb.addStretch(1)
        self._status.setText("✅ विवाह गुण मिलान तथा मंगल दोष गणना सम्पन्न भयो।")


