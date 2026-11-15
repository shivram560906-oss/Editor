# -*- coding: utf-8 -*-
"""
gui/widgets/janmapatrika_widget.py

Traditional Nepalese Janmapatrika (कुण्डली निर्माण) Document View for Desktop App.
Matches the traditional layout, sacred motifs, colors, font styling, and exact data fields of Janmapatrika.jsx.
"""
from __future__ import annotations
import datetime
import html
import math
import sys, os
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QTextEdit,
    QFrame, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QSizePolicy, QGridLayout, QApplication,
    QGraphicsView, QGraphicsScene
)
from PySide6.QtCore import Qt, QPoint, QRect, QRectF, QMarginsF, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QPageLayout, QPageSize, QRegion, QTextCursor, QTextDocument

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Website Janmapatrika visual reference expressed in stable desktop pixels.
_MM = 96.0 / 25.4
_PAPER_WIDTH = round(148 * _MM)
_PROSE_WIDTH = round(112 * _MM)
_JP_PAPER = "#f1f8eb"
_JP_PAPER_DEEP = "#e6f1df"
_JP_RED = "#9b183c"
_JP_GREEN = "#087329"
_JP_BLUE = "#101453"
_JP_GOLD = "#9a7a12"
_JP_BLACK = "#171717"
_JP_GRAY = "#5f625b"

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED)
from gui.utils.planet_colors import rashi_name
from gui.widgets.north_indian_chart import NorthIndianChartWidget
from gui.utils.bs_calendar import gregorian_to_bs

SIGN_NAMES_NE = {
    1: "मेष", 2: "वृष", 3: "मिथुन", 4: "कर्कट", 5: "सिंह", 6: "कन्या",
    7: "तुला", 8: "वृश्चिक", 9: "धनु", 10: "मकर", 11: "कुम्भ", 12: "मीन"
}

PLANET_NAMES_NE = {
    "Lagna": "लग्न", "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल",
    "Mercury": "बुध", "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु"
}

UNAVAILABLE = "उपलब्ध छैन"
# Correct Vimshottari classical order: Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury
VIMSHOTTARI_ORDER = [
    ("Ketu", "केतु", 7), ("Venus", "शुक्र", 20), ("Sun", "सूर्य", 6),
    ("Moon", "चन्द्र", 10), ("Mars", "मङ्गल", 7), ("Rahu", "राहु", 18),
    ("Jupiter", "गुरु", 16), ("Saturn", "शनि", 19), ("Mercury", "बुध", 17),
]
YOGINI_ORDER = [
    ("Mangala", "मङ्गला", 1), ("Pingala", "पिङ्गला", 2),
    ("Dhanya", "धान्या", 3), ("Bhramari", "भ्रामरी", 4),
    ("Bhadrika", "भद्रिका", 5), ("Ulka", "उल्का", 6),
    ("Siddha", "सिद्धा", 7), ("Sankata", "संकटा", 8),
]
GREGORIAN_MONTHS_NE = [
    "जनवरी", "फेब्रुवरी", "मार्च", "अप्रिल", "मे", "जुन",
    "जुलाई", "अगस्ट", "सेप्टेम्बर", "अक्टुबर", "नोभेम्बर", "डिसेम्बर",
]


def first_value(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in {"—", "?", UNAVAILABLE}:
            return text
    return UNAVAILABLE


class JustifiedDocumentWidget(QWidget):
    """Passive rich-text surface whose full document height expands the page."""

    def __init__(self, content: str, width: int, parent=None):
        super().__init__(parent)
        self._width = int(width)
        self._document = QTextDocument(self)
        self._document.setDocumentMargin(0)
        self._document.setDefaultStyleSheet(
            f"body, div {{ color:{_JP_BLACK}; font-family:'Noto Serif Devanagari','Noto Sans Devanagari','Mangal','Kokila',serif; "
            "font-size:12pt; font-weight:600; line-height:150%; margin:0; }}"
        )
        self._document.setHtml(
            f"<div style=\"color:{_JP_BLACK}; font-family:'Noto Serif Devanagari','Mangal',serif; "
            f"font-size:12pt; font-weight:600;\">{content}</div>"
        )
        cursor = QTextCursor(self._document)
        cursor.select(QTextCursor.SelectionType.Document)
        block_format = cursor.blockFormat()
        block_format.setAlignment(Qt.AlignJustify)
        cursor.setBlockFormat(block_format)

        # Width is authoritative; the resulting wrapped layout determines the content height.
        self._document.setTextWidth(float(self._width))
        document_height = self._document.documentLayout().documentSize().height()
        self._height = max(1, math.ceil(document_height) + 2)
        self.setFixedWidth(self._width)
        self.setMinimumHeight(self._height)
        self.setMaximumHeight(16777215)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def sizeHint(self) -> QSize:
        return QSize(self._width, self._height)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setClipRect(self.rect())
        self._document.drawContents(
            painter,
            QRectF(0, 0, float(self._width), float(self._height)),
        )


def nepali_digits(num_str: Any) -> str:
    s = str(num_str if num_str is not None else "")
    table = str.maketrans("0123456789", "०१२३४५६७८९")
    return s.translate(table)

def format_degree(value: Any) -> str:
    try:
        val = float(value)
        deg = int(abs(val))
        min_float = (abs(val) - deg) * 60.0
        minutes = int(min_float)
        seconds = int(round((min_float - minutes) * 60.0))
        return f"{deg}°{minutes:02d}′{seconds:02d}″"
    except Exception:
        return UNAVAILABLE


def _time_seconds(value: Any) -> Optional[int]:
    try:
        parts = [int(float(part)) for part in str(value).strip().split(":")]
        if len(parts) < 2:
            return None
        return parts[0] * 3600 + parts[1] * 60 + (parts[2] if len(parts) > 2 else 0)
    except (TypeError, ValueError):
        return None


def format_ghati(start_time: Any, end_time: Any) -> str:
    start = _time_seconds(start_time)
    end = _time_seconds(end_time)
    if start is None or end is None:
        return UNAVAILABLE
    elapsed = end - start
    if elapsed < 0:
        elapsed += 24 * 3600
    total_vipala = round(elapsed / 0.4)
    ghati, remainder = divmod(total_vipala, 3600)
    pala, vipala = divmod(remainder, 60)
    return f"{ghati:02d}:{pala:02d}:{vipala:02d}"


def _nested_name(value: Any) -> str:
    if isinstance(value, dict):
        return first_value(value.get("nepali"), value.get("name"), value.get("time"))
    return first_value(value)


def nepali_place_name(value: Any) -> str:
    text = first_value(value)
    if text == UNAVAILABLE:
        return text
    if "(" in text and ")" in text:
        inside = text.rsplit("(", 1)[1].split(")", 1)[0].strip()
        if any("ऀ" <= char <= "ॿ" for char in inside):
            return inside
    city = text.split(",", 1)[0].strip()
    city = city.rsplit(" - P", 1)[0].strip()
    return city or UNAVAILABLE


def _coordinate(value: Any, positive: str, negative: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return UNAVAILABLE
    degrees = int(abs(number))
    minutes_float = (abs(number) - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)
    return nepali_digits(f'{degrees}°{minutes:02d}\'{seconds:02d}"{negative if number < 0 else positive}')


def _timezone(metadata: dict) -> str:
    try:
        offset = float(metadata.get("timezone"))
    except (TypeError, ValueError):
        return first_value(metadata.get("timezone_id"))
    sign = "+" if offset >= 0 else "−"
    absolute = abs(offset)
    hours = int(absolute)
    minutes = round((absolute - hours) * 60)
    return nepali_digits(f"{sign}{hours:02d}:{minutes:02d}")


def build_janmapatrika_model(data: dict) -> dict:
    metadata = data.get("metadata") or {}
    panchang = data.get("panchang") or {}
    daily = ((data.get("panchang_requested_day") or {}).get("panchang") or {})
    lagna = data.get("lagna") or {}
    planets = data.get("planets") or []
    moon = next((p for p in planets if p.get("name") == "Moon"), {})
    sun = next((p for p in planets if p.get("name") == "Sun"), {})
    navamsha = ((data.get("vargas") or {}).get("D9") or {})
    birth_date = first_value(metadata.get("birth_date"))
    calendar = {"ad": UNAVAILABLE, "year": UNAVAILABLE, "month": UNAVAILABLE, "day": UNAVAILABLE,
                "shaka": UNAVAILABLE, "bs": UNAVAILABLE}
    try:
        ad = datetime.date.fromisoformat(birth_date)
        bs = gregorian_to_bs(ad.year, ad.month, ad.day)
        calendar.update({
            "ad": nepali_digits(birth_date), "year": nepali_digits(ad.year),
            "month": GREGORIAN_MONTHS_NE[ad.month - 1], "day": nepali_digits(ad.day),
            "shaka": nepali_digits(ad.year - 78),
            "bs": nepali_digits(bs["year"] if bs else UNAVAILABLE),
        })
    except (ValueError, TypeError):
        pass
    tithi = panchang.get("tithi") or {}
    nakshatra = panchang.get("nakshatra") or {}
    yoga = panchang.get("yoga") or {}
    karana = panchang.get("karana") or {}
    daily_tithi = daily.get("tithi") or {}
    daily_nakshatra = daily.get("nakshatra") or {}
    daily_yoga = daily.get("yoga") or {}
    daily_karana = daily.get("karana") or {}
    sunrise = first_value((daily.get("sunrise") or {}).get("time") if isinstance(daily.get("sunrise"), dict) else daily.get("sunrise"),
                          (panchang.get("sunrise") or {}).get("time") if isinstance(panchang.get("sunrise"), dict) else panchang.get("sunrise"))
    sunset = first_value((daily.get("sunset") or {}).get("time") if isinstance(daily.get("sunset"), dict) else daily.get("sunset"),
                         (panchang.get("sunset") or {}).get("time") if isinstance(panchang.get("sunset"), dict) else panchang.get("sunset"))
    local_time = first_value(metadata.get("local_birth_time"), metadata.get("birth_time"))
    try:
        sun_sign = int(sun.get("sign_number") or 0)
    except (TypeError, ValueError):
        sun_sign = 0
    seasons = ["वसन्त", "वसन्त", "ग्रीष्म", "ग्रीष्म", "वर्षा", "वर्षा", "शरद", "शरद", "हेमन्त", "हेमन्त", "शिशिर", "शिशिर"]
    ayana = "उत्तरायण" if sun_sign >= 10 or 1 <= sun_sign <= 3 else ("दक्षिणायन" if sun_sign else UNAVAILABLE)
    season = seasons[sun_sign - 1] if 1 <= sun_sign <= 12 else _nested_name(panchang.get("ritu"))
    paksha = first_value(tithi.get("paksha_nepali"), tithi.get("paksha"))
    if paksha != UNAVAILABLE:
        paksha = paksha.removesuffix("पक्ष").strip()
    moon_longitude = moon.get("sidereal_longitude")
    nak_elapsed = UNAVAILABLE
    if isinstance(moon_longitude, (int, float)):
        progress = (moon_longitude % (360 / 27)) / (360 / 27)
        total = round(progress * 60 * 3600)
        ghati, remainder = divmod(total, 3600)
        pala, vipala = divmod(remainder, 60)
        nak_elapsed = f"{ghati:02d}:{pala:02d}:{vipala:02d}"
    try:
        gender = int(metadata.get("gender") or 0)
    except (TypeError, ValueError):
        gender = 0
    avakahada = data.get("avakahada_chakra") or {}
    return {
        "metadata": metadata, "calendar": calendar,
        "full_name": (metadata.get("full_name") or metadata.get("name") or "").strip(),
        "father": first_value(metadata.get("father_name")), "mother": first_value(metadata.get("mother_name")),
        "gotra": first_value(metadata.get("gotra")), "spouse": first_value(metadata.get("spouse_name")),
        "family": first_value(metadata.get("family_details")), "country": first_value(metadata.get("country")),
        "place": nepali_place_name(first_value(metadata.get("birth_place"), metadata.get("city"))),
        "gender_label": "पुत्री" if gender == 1 else "पुत्र",
        "name_akshara": first_value(avakahada.get("name_akshara"), avakahada.get("namaakshar")),
        "nakshatra_pada": first_value(nakshatra.get("pada"), avakahada.get("pada"), avakahada.get("charan")),
        "gana": first_value(avakahada.get("gana")), "yoni": first_value(avakahada.get("yoni")),
        "viryoni": first_value(avakahada.get("viryoni")), "nadi": first_value(avakahada.get("nadi")),
        "varna": first_value(avakahada.get("varna")), "vashya": first_value(avakahada.get("vashya")),
        "asana": first_value(avakahada.get("asana")), "varga": first_value(avakahada.get("varga")),
        "shatru_varga": first_value(avakahada.get("shatru_varga")),
        "samvatsara": _nested_name(panchang.get("samvatsara")), "ayana": ayana, "season": season,
        "masa": first_value(_nested_name(panchang.get("lunar_month")), _nested_name(daily.get("lunar_month")), _nested_name(panchang.get("masa")), calendar["month"]),
        "paksha": paksha, "vara": first_value(_nested_name(panchang.get("vara")), _nested_name(panchang.get("day"))),
        "sunrise_tithi": _nested_name(daily_tithi), "birth_tithi": first_value(tithi.get("birth_nepali"), tithi.get("birth_name"), tithi.get("nepali"), tithi.get("name")),
        "sunrise_nakshatra": _nested_name(daily_nakshatra), "birth_nakshatra": _nested_name(nakshatra),
        "sunrise_yoga": _nested_name(daily_yoga), "birth_yoga": first_value(yoga.get("birth_nepali"), yoga.get("birth_name"), yoga.get("nepali"), yoga.get("name")),
        "sunrise_karana": _nested_name(daily_karana), "birth_karana": first_value(karana.get("birth_nepali"), karana.get("birth_name"), karana.get("nepali"), karana.get("name")),
        "tithi_end": format_ghati(sunrise, daily_tithi.get("end_time")), "nakshatra_end": format_ghati(sunrise, daily_nakshatra.get("end_time")),
        "yoga_end": format_ghati(sunrise, daily_yoga.get("end_time")), "karana_end": format_ghati(sunrise, daily_karana.get("end_time")),
        "nakshatra_elapsed": first_value(nakshatra.get("elapsed"), nakshatra.get("bhukta_ghati"), nak_elapsed),
        "nakshatra_total": first_value(nakshatra.get("bhabhoga"), nakshatra.get("bhoga_ghati"), "60:00:00" if nak_elapsed != UNAVAILABLE else None),
        "sunrise": sunrise, "sunset": sunset, "local_time": local_time, "ishta_kala": format_ghati(sunrise, local_time),
        "lagna_sign": SIGN_NAMES_NE.get(int(lagna.get("sign_number") or 0), UNAVAILABLE),
        "lagna_degree": format_degree(first_value(lagna.get("longitude_in_sign"), lagna.get("degree_in_sign"))),
        "moon_sign": SIGN_NAMES_NE.get(int(moon.get("sign_number") or 0), UNAVAILABLE),
        "navamsha_sign": SIGN_NAMES_NE.get(int((navamsha.get("lagna") or {}).get("sign_number") or 0), UNAVAILABLE),
        "solar_month": SIGN_NAMES_NE.get(sun_sign, UNAVAILABLE),
        "solar_days": nepali_digits(math.floor(float(sun.get("longitude_in_sign"))) + 1) if sun.get("longitude_in_sign") is not None else UNAVAILABLE,
        "latitude": _coordinate(metadata.get("latitude"), "उ.", "द."), "longitude": _coordinate(metadata.get("longitude"), "पू.", "प."),
        "timezone": _timezone(metadata),
    }


def compose_janmapatrika_prose(model: dict) -> str:
    def value(key: str) -> str:
        text = html.escape(nepali_digits(model.get(key, UNAVAILABLE)))
        return f'<span style="color:#9b183c;font-weight:800;border-bottom:1px dotted #5f625b;">{text}</span>'

    def calendar_value(key: str) -> str:
        text = html.escape(nepali_digits(model["calendar"].get(key, UNAVAILABLE)))
        return f'<span style="color:#9b183c;font-weight:800;border-bottom:1px dotted #5f625b;">{text}</span>'

    # राशीको नाम: यदि बक्स खाली छ भने "........." देखाउने
    rashi_naam = model.get("full_name") or ""
    if rashi_naam:
        rashi_naam_span = (
            f'<span style="color:#9b183c;font-weight:800;border-bottom:1px dotted #5f625b;">'
            f'{html.escape(rashi_naam)}</span>'
        )
    else:
        rashi_naam_span = (
            '<span style="color:#9b183c;font-weight:800;border-bottom:1px dotted #5f625b;">'
            '.........</span>'
        )

    return (
        f'अस्य श्रीमन्नृपतिवीरविक्रमादित्यराज्यतः श्रीशालिवाहनीय शकः {calendar_value("shaka")} '
        f'श्रीवीरविक्रमादित्य संवत् {calendar_value("bs")} ईसवीय सन् {calendar_value("ad")} '
        f'अत्रास्मिन् वर्षे {value("samvatsara")} नाम संवत्सरे श्रीसूर्य {value("ayana")} {value("season")} ऋतौ अथ चान्द्रमानेन {value("masa")} मासे {value("paksha")} पक्षे {value("vara")} वासरे '
        f'सूर्योदयकालीन {value("sunrise_tithi")} तिथौ घट्यादिः {value("tithi_end")} जन्म तिथौ {value("birth_tithi")} तिथिः। सूर्योदयकालीन {value("sunrise_nakshatra")} नक्षत्रस्य समाप्तिघट्यादिः {value("nakshatra_end")} '
        f'जन्मनक्षत्रं {value("birth_nakshatra")} तस्य जन्मसमये भुक्तघट्यादिः {value("nakshatra_elapsed")} भभोगघट्यादिः {value("nakshatra_total")} सूर्योदयकालीन {value("sunrise_yoga")} योगस्य समाप्तिघट्यादिः {value("yoga_end")} '
        f'जन्मयोगः {value("birth_yoga")} सूर्योदयकालीन {value("sunrise_karana")} करणस्य समाप्तिघट्यादिः {value("karana_end")} जन्मकरणं {value("birth_karana")} इति पञ्चाङ्गम् ॥<br><br>'
        f'अथ सौरमानेन {value("solar_month")} मासे सूर्यसंक्रमाद् गतदिनानि {value("solar_days")} तदनुसारम् ईसवीयमासः {calendar_value("month")} तारिका {calendar_value("day")} '
        f'अत्र {value("vara")} वासरे स्थानीय जन्मसमयः {value("local_time")} श्रीसूर्योदयादिष्टकालघट्यादिः {value("ishta_kala")} तदा जन्मसमये {value("lagna_sign")} राशौ लग्नोदयः {value("lagna_degree")} अंशात्मकः {value("navamsha_sign")} नवमांशके '
        f'{value("moon_sign")} राशिगते चन्द्रमसि एवंविधे पञ्चाङ्गशुद्धे देशे {value("country")} प्रान्तान्तर्गत {value("place")} मण्डले तदन्तर्गत जन्मस्थाने {value("place")} यत्र अक्षांशः {value("latitude")} देशान्तरः {value("longitude")} '
        f'मानकसमय {value("timezone")} स्थानीय जन्मसमयः {value("local_time")} निवसतः {value("gotra")} गोत्रोत्पन्न श्रीमतः {value("father")} तस्य कुलोचितविवाहितायां भार्यायां श्रीमती {value("mother")} नाम्नी देव्यां गर्भस्थ {value("gender_label")} रत्नमजीजनत्। '
        f'नामाक्षरः {value("name_akshara")} चरणः {value("nakshatra_pada")} इष्टकालः {value("ishta_kala")} सूर्योदयः {value("sunrise")} सूर्यास्तः {value("sunset")} '
        f'योनिः {value("yoni")} विर्योनिः {value("viryoni")} नाडी {value("nadi")} गणः {value("gana")} वश्यः {value("vashya")} आसनम् {value("asana")} वर्णः {value("varna")} वर्गः {value("varga")} शत्रुवर्गः {value("shatru_varga")}। '
        f'शुभनाम श्री {rashi_naam_span} इति प्रतिष्ठितम्।'
    )


class JanmapatrikaPage(QWidget):
    """Native PySide6 Traditional Janmapatrika (कुण्डली निर्माण) Document Widget."""
    def __init__(self, data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        if data:
            self.refresh(data)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)

        # Top Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 6px 12px;
            }}
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(12)

        tb_title = QLabel("📜 " + ("जन्मपत्रिका (कुण्डली निर्माण)" if self._is_ne else "Janmapatrika Document"))
        tb_title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 16px; font-weight: 700;")
        tb_layout.addWidget(tb_title)

        tb_layout.addStretch()

        self._zoom_out_btn = QPushButton("-")
        self._zoom_reset_btn = QPushButton("100%")
        self._zoom_in_btn = QPushButton("+")
        for button in (self._zoom_out_btn, self._zoom_reset_btn, self._zoom_in_btn):
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(30)
            button.setStyleSheet(
                f"QPushButton {{ color:{COLOR_GOLD}; background:rgba(212,175,55,0.15); "
                f"border:1px solid {COLOR_GOLD}; border-radius:5px; padding:3px 10px; font-weight:700; }}"
                f"QPushButton:hover {{ background:rgba(212,175,55,0.3); }}"
            )
        self._zoom_out_btn.setToolTip("Zoom out")
        self._zoom_in_btn.setToolTip("Zoom in")
        self._zoom_reset_btn.setToolTip("Reset zoom")
        self._zoom_out_btn.clicked.connect(lambda: self._set_zoom(self._zoom - 0.1))
        self._zoom_in_btn.clicked.connect(lambda: self._set_zoom(self._zoom + 0.1))
        self._zoom_reset_btn.clicked.connect(lambda: self._set_zoom(1.0))
        tb_layout.addWidget(QLabel("🔍"))
        tb_layout.addWidget(self._zoom_out_btn)
        tb_layout.addWidget(self._zoom_reset_btn)
        tb_layout.addWidget(self._zoom_in_btn)

        print_btn = QPushButton("🖨️ " + ("प्रिन्ट गर्नुहोस्" if self._is_ne else "Print Janmapatrika"))
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_GOLD};
                color: #000;
                font-size: 12px;
                font-weight: 700;
                padding: 6px 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: #e5be38;
            }}
        """)
        print_btn.clicked.connect(self._print_patrika)
        tb_layout.addWidget(print_btn)

        pdf_btn = QPushButton("📄 " + ("PDF निर्यात" if self._is_ne else "Export PDF"))
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(212,175,55,0.15);
                color: {COLOR_GOLD};
                border: 1px solid {COLOR_GOLD};
                font-size: 12px;
                font-weight: 700;
                padding: 6px 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: rgba(212,175,55,0.3);
            }}
        """)
        pdf_btn.clicked.connect(self._export_pdf)
        tb_layout.addWidget(pdf_btn)

        main_layout.addWidget(toolbar)
        self._zoom = 1.0

        # Graphics view scales the complete paper (text, charts and tables) together.
        self._view = QGraphicsView()
        self._view.setObjectName("janmapatrikaZoomView")
        self._view.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self._view.setTransformationAnchor(QGraphicsView.NoAnchor)
        self._view.setResizeAnchor(QGraphicsView.NoAnchor)
        self._view.setStyleSheet("QGraphicsView { border: none; background: transparent; }")
        self._scene = QGraphicsScene(self._view)
        self._view.setScene(self._scene)
        main_layout.addWidget(self._view, 1)

        # Keep a real QWidget wrapper so existing document descendants remain discoverable.
        self._doc_wrapper = QWidget()
        self._doc_wrapper_layout = QVBoxLayout(self._doc_wrapper)
        self._doc_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        self._doc_wrapper_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        # Paper shell mirrors the website's 148mm sheet and framed green paper.
        self._paper = QFrame()
        self._paper.setObjectName("paperFrame")
        self._paper.setFixedWidth(_PAPER_WIDTH)
        self._paper.setStyleSheet(f"""
            #paperFrame {{
                background: {_JP_PAPER};
                border: 1px solid {_JP_GREEN};
                color: {_JP_BLACK};
            }}
        """)
        
        self._paper_grid = QGridLayout(self._paper)
        self._paper_grid.setContentsMargins(round(4.5 * _MM), round(4.5 * _MM), round(4.5 * _MM), round(4.5 * _MM))
        self._paper_grid.setHorizontalSpacing(0)
        self._paper_grid.setVerticalSpacing(0)
        
        sw_style = f"color: {_JP_RED}; background: {_JP_PAPER}; font-size: 13px; font-weight: 700; padding: 2px;"
        
        self.sw_top = QLabel("卐  · " * 22 + "卐")
        self.sw_top.setAlignment(Qt.AlignCenter)
        self.sw_top.setStyleSheet(sw_style)
        
        self.sw_bot = QLabel("卐  · " * 22 + "卐")
        self.sw_bot.setAlignment(Qt.AlignCenter)
        self.sw_bot.setStyleSheet(sw_style)
        
        self.sw_left = QLabel("<br>·<br>".join(["卐"] * 30))
        self.sw_left.setAlignment(Qt.AlignCenter)
        self.sw_left.setFixedWidth(round(3 * _MM))
        self.sw_left.setStyleSheet(sw_style)
        
        self.sw_right = QLabel("<br>·<br>".join(["卐"] * 30))
        self.sw_right.setAlignment(Qt.AlignCenter)
        self.sw_right.setFixedWidth(round(3 * _MM))
        self.sw_right.setStyleSheet(sw_style)
        
        self._inner_paper = QFrame()
        self._inner_paper.setObjectName("innerPaper")
        self._inner_paper.setStyleSheet(
            f"#innerPaper {{ background: {_JP_PAPER}; border: 2px solid {_JP_GREEN}; }}"
        )
        
        self._paper_layout = QVBoxLayout(self._inner_paper)
        self._paper_layout.setContentsMargins(round(9 * _MM), round(10.5 * _MM), round(9 * _MM), round(10.5 * _MM))
        self._paper_layout.setSpacing(round(5 * _MM))
        
        self._paper_grid.addWidget(self.sw_top, 0, 0, 1, 3)
        self._paper_grid.addWidget(self.sw_left, 1, 0)
        self._paper_grid.addWidget(self._inner_paper, 1, 1)
        self._paper_grid.addWidget(self.sw_right, 1, 2)
        self._paper_grid.addWidget(self.sw_bot, 2, 0, 1, 3)

        self._doc_wrapper_layout.addWidget(self._paper)
        # Keep the document outside QGraphicsScene until its complete natural
        # height is known. Embedding an empty wrapper first makes the proxy
        # constrain later rich-text/chart layouts to its initial short height.
        self._document_proxy = None
        self._paper_proxy = None
        self._set_zoom(1.0)

    def _set_zoom(self, value: float) -> None:
        """Set document zoom while preserving the paper's print dimensions."""
        self._zoom = max(0.6, min(2.0, round(float(value), 2)))
        if self._paper_proxy is not None:
            self._paper_proxy.setScale(self._zoom)
            self._scene.setSceneRect(self._paper_proxy.sceneBoundingRect().adjusted(-20, -20, 20, 20))
        if hasattr(self, "_zoom_reset_btn"):
            self._zoom_reset_btn.setText(f"{round(self._zoom * 100)}%")
            self._zoom_out_btn.setEnabled(self._zoom > 0.6)
            self._zoom_in_btn.setEnabled(self._zoom < 2.0)

    def refresh(self, data: dict):
        self._data = data
        self._refresh_restored(data)
        self._paper_layout.invalidate()
        self._paper_layout.activate()
        self._inner_paper.setMinimumHeight(self._paper_layout.sizeHint().height())
        self._paper_grid.invalidate()
        self._paper_grid.activate()
        natural_height = max(1, self._paper.sizeHint().height())
        self._paper.setMinimumHeight(natural_height)
        self._paper.resize(_PAPER_WIDTH, natural_height)
        self._doc_wrapper.setMinimumSize(_PAPER_WIDTH, natural_height)
        self._doc_wrapper.resize(_PAPER_WIDTH, natural_height)
        self._doc_wrapper_layout.activate()
        if self._document_proxy is None:
            self._document_proxy = self._scene.addWidget(self._doc_wrapper)
            self._paper_proxy = self._document_proxy
        else:
            self._document_proxy.resize(_PAPER_WIDTH, natural_height)
        self._set_zoom(self._zoom)

    def _clear_paper(self) -> None:
        while self._paper_layout.count():
            item = self._paper_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout is not None:
                while child_layout.count():
                    child = child_layout.takeAt(0)
                    if child.widget() is not None:
                        child.widget().deleteLater()

    def _rich_label(self, content: str, *, centered: bool = False) -> QLabel:
        label = QLabel(content)
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setAlignment((Qt.AlignHCenter if centered else Qt.AlignLeft) | Qt.AlignTop)
        label.setStyleSheet(
            f"font-family:'Noto Serif Devanagari','Noto Sans Devanagari','Mangal','Kokila',serif;"
            f"color:{_JP_BLACK}; font-size:12pt; font-weight:600; background:transparent;"
        )
        return label

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            f"color:{_JP_RED}; font-family:'Noto Serif Devanagari','Noto Sans Devanagari','Mangal','Kokila',serif;"
            "font-size:12pt;font-weight:800;margin-top:8px;background:transparent;"
        )
        return label

    @staticmethod
    def _planet_table_html(data: dict) -> str:
        lagna = data.get("lagna") or {}
        planets = data.get("planets") or []
        rows = [("लग्न", lagna)] + [
            (PLANET_NAMES_NE.get(name, name), next((p for p in planets if p.get("name") == name), {}))
            for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        ]
        body = []
        for name, item in rows:
            if not item:
                continue
            status = []
            if item.get("is_retrograde"):
                status.append("वक्री")
            if item.get("is_combust"):
                status.append("अस्त")
            if item.get("exaltation_state") == "exalted":
                status.append("उच्च")
            elif item.get("exaltation_state") == "debilitated":
                status.append("नीच")
            sign = SIGN_NAMES_NE.get(int(item.get("sign_number") or 0), UNAVAILABLE)
            degree = format_degree(first_value(item.get("longitude_in_sign"), item.get("degree_in_sign")))
            body.append(f"<tr><td><b>{html.escape(name)}</b></td><td>{sign}</td><td>{nepali_digits(degree)}</td><td>{', '.join(status) or '—'}</td></tr>")
        return ("<table width='100%' cellspacing='0' cellpadding='1' style='border-collapse:collapse;font-size:13pt;line-height:1.05;' border='1'>"
                "<tr style='color:#9b183c;background:#e6f1df;font-weight:800;'><td width='18%'>ग्रह</td><td width='20%'>राशि</td><td width='38%'>स्पष्ट</td><td width='24%'>स्थिति</td></tr>"
                + "".join(body) + "</table>")

    @staticmethod
    def _dasha_spec(periods: list) -> tuple[list[tuple[str, str, int]], str]:
        """Return the classical cycle and first-column heading for the payload."""
        first = periods[0] if periods else {}
        is_yogini = bool(first.get("yogini") or first.get("yogini_nepali")) or (
            bool(first.get("name") or first.get("nepali"))
            and not first.get("lord_nepali")
        )
        return (YOGINI_ORDER, "योगिनी") if is_yogini else (VIMSHOTTARI_ORDER, "ग्रह")

    @staticmethod
    def _dasha_lord(node: dict) -> str:
        # Normalized Yogini nodes expose the Yogini name in ``lord`` while
        # legacy Yogini nodes keep the planetary lord there.  Prefer the
        # identity that belongs to the active cycle.
        if node.get("yogini"):
            return first_value(node.get("yogini"), node.get("name"))
        if not node.get("lord_nepali") and (node.get("name") or node.get("nepali")):
            return first_value(node.get("name"), node.get("nepali"))
        return first_value(node.get("lord"), node.get("name"))

    @staticmethod
    def _dasha_nepali(node: dict) -> str:
        return first_value(
            node.get("lord_nepali"), node.get("nepali"),
            node.get("lord"), node.get("name"),
        )

    @staticmethod
    def _dasha_nodes(period: dict, children_key: Optional[str]) -> list:
        """Return the best available sub-period list for this payload version."""
        for key in (children_key, "antardashas", "children"):
            if not key:
                continue
            nodes = period.get(key) if isinstance(period, dict) else None
            if isinstance(nodes, list) and nodes:
                return nodes
        return []

    @staticmethod
    def _dasha_cycle_from(lord_name: str, spec: list[tuple[str, str, int]]) -> list[str]:
        names = [item[0] for item in spec]
        start = names.index(lord_name) if lord_name in names else 0
        return names[start:] + names[:start]

    @staticmethod
    def _ordered_dasha_cycle(periods: list, spec: list[tuple[str, str, int]]) -> list[dict]:
        """Keep one cycle, beginning with the birth-time lord/yogini."""
        if not periods:
            return []
        first_name = JanmapatrikaPage._dasha_lord(periods[0])
        names = [item[0] for item in spec]
        start = names.index(first_name) if first_name in names else 0
        expected = names[start:] + names[:start]
        remaining = list(periods)
        ordered = []
        for name in expected:
            match = next((node for node in remaining if JanmapatrikaPage._dasha_lord(node) == name), None)
            if match is not None:
                ordered.append(match)
                remaining.remove(match)
        return ordered or periods[:len(spec)]

    @staticmethod
    def _elapsed_age(start_value: Any, end_value: Any) -> str:
        """Format completed age between two ISO dates as years and months."""
        try:
            start = datetime.date.fromisoformat(str(start_value)[:10])
            end = datetime.date.fromisoformat(str(end_value)[:10])
        except (TypeError, ValueError):
            return "—"
        months = (end.year - start.year) * 12 + end.month - start.month
        if end.day < start.day:
            months -= 1
        years, months = divmod(max(0, months), 12)
        parts = [f"{nepali_digits(years)} वर्ष"]
        if months:
            parts.append(f"{nepali_digits(months)} महिना")
        return "<br>".join(parts)

    @staticmethod
    def _calendar_age_parts(start_value: Any, end_value: Any) -> Optional[tuple[int, int, int]]:
        """Return the exact calendar difference as (years, months, days)."""
        try:
            start = datetime.date.fromisoformat(str(start_value)[:10])
            end = datetime.date.fromisoformat(str(end_value)[:10])
        except (TypeError, ValueError):
            return None
        if end <= start:
            return (0, 0, 0)
        years = end.year - start.year
        months = end.month - start.month
        days = end.day - start.day
        if days < 0:
            months -= 1
            previous_month_end = end.replace(day=1) - datetime.timedelta(days=1)
            days += previous_month_end.day
        if months < 0:
            years -= 1
            months += 12
        return max(0, years), max(0, months), max(0, days)

    @staticmethod
    def _dasha_cell_value(start_value: Any, end_value: Any) -> str:
        """Format a cumulative remaining-age cell.

        A period shorter than one complete month keeps its days instead of
        collapsing to ``० वर्ष``; ordinary periods print whole years and
        months only.  Every value is measured from the native's birth, so the
        display never accumulates rounding errors from earlier cells.
        """
        parts = JanmapatrikaPage._calendar_age_parts(start_value, end_value)
        if parts is None:
            return "—"
        years, months, days = parts
        if years == 0 and months == 0:
            return f"{nepali_digits(days)} दिन"
        rendered = [f"{nepali_digits(years)} वर्ष"]
        if months:
            rendered.append(f"{nepali_digits(months)} महिना")
        return "<br>".join(rendered)

    @staticmethod
    def _dasha_timeline(periods: list) -> list[dict]:
        """Return every calculated period in chronological order.

        ``_ordered_dasha_cycle`` deliberately keeps one classical cycle for
        the compact Mahadasha table.  The antardasha timeline must instead
        keep every cycle returned by the engine -- for Yogini that means all
        three 36-year cycles, not only the first one.
        """
        def start_key(period: dict) -> tuple[int, str]:
            try:
                value = datetime.date.fromisoformat(str(period.get("start"))[:10])
            except (TypeError, ValueError):
                return (1, "")
            return (0, value.isoformat())

        return sorted(
            (period for period in periods if isinstance(period, dict)),
            key=start_key,
        )

    @staticmethod
    def _expand_link_html() -> str:
        """Small in-table control that reveals the next three data rows."""
        return (
            f"<a href='expand' style='color:{_JP_RED};text-decoration:none;"
            f"font-weight:700;border:1px solid {_JP_RED};"
            "padding:0 3px;'>+</a>"
        )

    @staticmethod
    def _dasha_table_html(periods: list, *, children_key: Optional[str] = None,
                          visible_rows: Optional[int] = None,
                          show_more: bool = False) -> str:
        """Render a classical dasha grid constrained to the document width."""
        if not periods:
            return ""
        spec, heading = JanmapatrikaPage._dasha_spec(periods)
        cycle = JanmapatrikaPage._ordered_dasha_cycle(periods, spec)
        duration_by_name = {name: years for name, _, years in spec}
        if children_key:
            timeline = JanmapatrikaPage._dasha_timeline(periods)
            birth_start = timeline[0].get("start") if timeline else None
            try:
                birth_date = datetime.date.fromisoformat(str(birth_start)[:10])
            except (TypeError, ValueError):
                birth_date = None

            # Rotate the column headers so they start from the birth Mahadasha
            # lord and follow the classical cycle from that point.  This way the
            # first data row's own antardasha always appears in the first
            # data column, matching the traditional table layout.
            birth_lord = (
                JanmapatrikaPage._dasha_lord(timeline[0]) if timeline else None
            )
            names_in_spec = [name for name, _, _ in spec]
            if birth_lord and birth_lord in names_in_spec:
                rot = names_in_spec.index(birth_lord)
                rotated_spec = spec[rot:] + spec[:rot]
            else:
                rotated_spec = spec

            headers = [(name, nepali) for name, nepali, _ in rotated_spec]
            column_width = max(1, 100 // (len(headers) + 1))
            cell = f"<td width='{column_width}%'>"
            header_cells = "".join(
                cell + html.escape(nepali) + "</td>" for _, nepali in headers
            )

            # Build lookup: nepali name → English spec name (for Yogini nodes
            # whose _dasha_lord may return a Nepali string from some backends)
            nepali_to_spec = {nepali: name for name, nepali, _ in spec}

            rows = []
            for period in timeline:
                nodes = JanmapatrikaPage._dasha_nodes(period, children_key)
                if not nodes:
                    continue

                # Build a dict keyed by the antardasha lord's canonical name
                node_by_lord: dict = {}
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    lord_key = JanmapatrikaPage._dasha_lord(node)
                    # Normalise Nepali-keyed Yogini nodes to spec English names
                    lord_key = nepali_to_spec.get(lord_key, lord_key)
                    node_by_lord.setdefault(lord_key, node)

                values = []
                has_visible = False
                for lord, _ in headers:
                    node = node_by_lord.get(lord)
                    value = "—"
                    if node is not None:
                        # For the birth (partial) Mahadasha: antardashas that
                        # ended before birth are pre-birth → show "—".
                        is_before_birth = node.get("is_before_birth", False)
                        if is_before_birth:
                            values.append("—")
                            continue
                        try:
                            end = datetime.date.fromisoformat(
                                str(node.get("end"))[:10]
                            )
                        except (TypeError, ValueError):
                            end = None
                        if end is not None and (
                            birth_date is None or end > birth_date
                        ):
                            value = JanmapatrikaPage._dasha_cell_value(
                                birth_date, end
                            )
                            has_visible = True
                    values.append(value)
                if has_visible:
                    rows.append(values)

            if not rows:
                return ""
            shown = rows[:visible_rows] if visible_rows is not None else rows

            body = []
            for row_index, values in enumerate(shown):
                cells = list(values)
                if (
                    show_more
                    and visible_rows is not None
                    and row_index == len(shown) - 1
                    and len(shown) < len(rows)
                ):
                    cells[-1] = (
                        f"{cells[-1]}<br>{JanmapatrikaPage._expand_link_html()}"
                    )
                body.append(
                    f"<tr>{cell}बाँकी उमेर</td>"
                    + "".join(cell + value + "</td>" for value in cells)
                    + "</tr>"
                )
            return (
                "<table width='100%' cellspacing='0' cellpadding='2' "
                "style='border-collapse:collapse;font-size:9px;"
                "text-align:center;' border='1'>"
                "<tr style='background:#e6f1df;font-weight:700;'>"
                f"{cell}दशा</td>{header_cells}</tr>"
                + "".join(body)
                + "</table>"
            )

        columns = cycle[:len(spec)]
        column_width = max(1, 100 // (len(columns) + 1))
        cell = f"<td width='{column_width}%'>"
        header = "".join(
            cell + html.escape(first_value(node.get("lord_nepali"), node.get("nepali"), node.get("lord"), node.get("name"))) + "</td>"
            for node in columns
        )
        years = "".join(
            cell + f"{nepali_digits(first_value(node.get('total_years'), duration_by_name.get(JanmapatrikaPage._dasha_lord(node))))} वर्ष</td>"
            for node in columns
        )
        birth_start = columns[0].get("start") if columns else None
        remaining = "".join(
            cell + JanmapatrikaPage._elapsed_age(birth_start, node.get("end")) + "</td>"
            for node in columns
        )
        return (
            "<table width='100%' cellspacing='0' cellpadding='1' "
            "style='border-collapse:collapse;font-size:9px;text-align:center;' border='1'>"
            f"<tr>{cell}{heading}</td>" + header + "</tr>"
            f"<tr>{cell}वर्ष</td>" + years + "</tr>"
            f"<tr>{cell}बाँकी उमेर</td>" + remaining + "</tr></table>"
        )

    def _set_table_label_html(self, label: QLabel, content: str) -> None:
        """Set rich-text table HTML and reserve the height it needs when wrapped.

        ``QLabel.heightForWidth`` does not account for rich-text tables that
        reflow at the document width, so a wrapped table can be clipped at the
        bottom.  Measure the real document and keep enough vertical space.
        """
        label.setText(content)
        width = label.width()
        if width <= 100:
            width = _PROSE_WIDTH
        else:
            # During construction the label may still report a wider default
            # size than the paper column it will finally occupy.  Never
            # measure wider than the document column, or the reserved height
            # is too small once the layout applies the real width and the
            # last table row or its ``+`` link is clipped.
            width = min(width, _PROSE_WIDTH)
        document = QTextDocument()
        document.setDefaultFont(label.font())
        document.setHtml(content)
        document.setTextWidth(max(1, width))
        label.setMinimumHeight(int(math.ceil(document.size().height())) + 8)

    def _dasha_section_widget(self, title: str, periods: list, *, children_key: Optional[str] = None) -> Optional[QFrame]:
        """Build one compact table and optional incremental +/- controls."""
        spec, _ = self._dasha_spec(periods)
        if children_key:
            max_rows = sum(
                1
                for period in self._dasha_timeline(periods)
                if self._dasha_nodes(period, children_key)
            )
        else:
            max_rows = len(self._ordered_dasha_cycle(periods, spec))
        if not max_rows:
            return None
        section = QFrame()
        section.setStyleSheet(f"QFrame {{ background: transparent; color: {_JP_BLACK}; }}")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self._section_label(title))
        table_label = QLabel()
        table_label.setWordWrap(True)
        table_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        table_label.setMinimumWidth(0)
        table_label.setStyleSheet(
            f"color:{_JP_RED}; font-family:'Noto Serif Devanagari','Mangal',serif; "
            "font-size:11pt; font-weight:600; background:transparent;"
        )
        layout.addWidget(table_label)
        if children_key:
            state = {"rows": min(3, max_rows)}
            controls = QHBoxLayout()
            controls.setContentsMargins(0, 0, 0, 0)
            controls.addStretch()
            minus = QPushButton("-")
            plus = QPushButton("+")
            for button in (minus, plus):
                button.setFixedSize(24, 24)
                button.setStyleSheet(
                    f"QPushButton {{ color:{_JP_RED}; background:{_JP_PAPER}; "
                    f"border:1px solid {_JP_RED}; border-radius:12px; font-size:14px; }}"
                )
            def render() -> None:
                self._set_table_label_html(
                    table_label,
                    self._dasha_table_html(
                        periods,
                        children_key=children_key,
                        visible_rows=state["rows"],
                        show_more=state["rows"] < max_rows,
                    ),
                )
                minus.setEnabled(state["rows"] > min(3, max_rows))
                plus.setEnabled(state["rows"] < max_rows)

            def expand(_value: object = None) -> None:
                if state["rows"] < max_rows:
                    state["rows"] = min(max_rows, state["rows"] + 3)
                    render()

            def collapse() -> None:
                state["rows"] = max(min(3, max_rows), state["rows"] - 3)
                render()

            table_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            table_label.setOpenExternalLinks(False)
            table_label.linkActivated.connect(expand)
            plus.clicked.connect(expand)
            minus.clicked.connect(collapse)
            controls.addWidget(minus)
            controls.addWidget(plus)
            layout.addLayout(controls)
            render()
        else:
            self._set_table_label_html(table_label, self._dasha_table_html(periods))
        return section

    def _chart_frame(self, data: dict, varga: str, title: str) -> QFrame:
        frame = QFrame()
        frame.setMinimumHeight(220)
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        frame.setStyleSheet(f"background:{_JP_PAPER};border:1px solid #8db1e5;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(3, 3, 3, 3)
        heading = QLabel(title)
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet(f"color:{_JP_RED};font-weight:800;font-family:'Noto Serif Devanagari','Mangal',serif;")
        layout.addWidget(heading)
        chart = NorthIndianChartWidget(data, varga, self._lang)
        chart.setFixedSize(200, 190)
        chart.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        chart.setToolTip("")
        layout.addWidget(chart, 0, Qt.AlignCenter)
        return frame

    def _refresh_restored(self, data: dict) -> None:
        self._clear_paper()
        model = build_janmapatrika_model(data)
        sacred = self._rich_label(
            f"<div style='text-align:center;font-family:serif;font-size:12pt;font-weight:800;line-height:1.5;'>"
            f"<div style='color:{_JP_RED};font-size:30px;'>ॐ</div>"
            f"<div style='color:{_JP_RED};font-size:22px;'>श्री गणेशाय नमः</div><br>"
            f"<span style='color:{_JP_BLUE};'>श्रीमङ्गलमूर्तये नमः</span><br>"
            f"<span style='color:{_JP_GOLD};'>आदित्याद्या ग्रहासर्वे सनक्षत्राः सराशयः ॥<br>"
            f"कुर्वन्तुमङ्गल तस्य यस्यैषा जन्मपत्रिका॥</span></div>", centered=True)
        self._paper_layout.addWidget(sacred)
        prose_widget = JustifiedDocumentWidget(
            compose_janmapatrika_prose(model), _PROSE_WIDTH
        )
        self._paper_layout.addWidget(prose_widget, 0, Qt.AlignHCenter)
        blessing = self._rich_label(
            f"<div style='text-align:center;color:{_JP_RED};font-size:12pt;font-weight:800;'>"
            "सदैव द्विजाशीर्वादैर्दीर्घमायुर्भूयात् ॥</div>", centered=True
        )
        self._paper_layout.addWidget(blessing, 0, Qt.AlignHCenter)

        charts = QHBoxLayout()
        charts.setContentsMargins(0, 0, 0, 0)
        charts.setSpacing(6)
        charts.addWidget(self._chart_frame(data, "D1", "जन्म कुण्डली (D1)"))
        charts.addWidget(self._chart_frame(data, "Moon", "चन्द्र कुण्डली"))
        self._paper_layout.addLayout(charts)
        self._paper_layout.addWidget(self._section_label("ग्रह स्थिति तालिका"))
        planet_table = self._rich_label(self._planet_table_html(data))
        planet_table.setStyleSheet(
            f"font-family:'Noto Serif Devanagari','Noto Sans Devanagari','Mangal','Kokila',serif;"
            f"color:{_JP_BLACK}; font-size:12pt; font-weight:600; background:transparent;"
        )
        self._paper_layout.addWidget(planet_table)
        dasha_sections = [
            ("विंशोत्तरी महादशा चक्रम्", data.get("dasha") or [], None),
            ("विंशोत्तरी अन्तरदशा चक्रम्", data.get("dasha") or [], "antardashas"),
            ("योगिनी महादशा चक्रम्", data.get("yogini_dasha") or [], None),
            ("योगिनी अन्तरदशा चक्रम्", data.get("yogini_dasha") or [], "antardashas"),
        ]
        for title, periods, children_key in dasha_sections:
            section = self._dasha_section_widget(title, periods, children_key=children_key)
            if section is not None:
                self._paper_layout.addWidget(section)
        if model["family"] != UNAVAILABLE or model["spouse"] != UNAVAILABLE:
            self._paper_layout.addWidget(self._rich_label(
                f"<div style='text-align:center;'><b>परिवारको विवरण:</b> {html.escape(model['family'])} &nbsp; "
                f"<b>पति वा पत्नी:</b> {html.escape(model['spouse'])} ॥</div>"))
        self._paper_layout.addWidget(self._rich_label(
            f"<div style='text-align:center;color:{_JP_RED};font-size:12pt;font-weight:800;'>॥ इति जन्मपत्रिका ॥</div>", centered=True))
        # Publish the complete natural document height before the paper is
        # attached to the graphics scene. This prevents the proxy from using
        # the wrapper's initial short height and stacking later sections over
        # the prose/charts.
        self._paper_layout.invalidate()
        self._paper_layout.activate()
        self._inner_paper.setMinimumHeight(self._paper_layout.sizeHint().height())
        self._paper_grid.invalidate()
        self._paper_grid.activate()
        self._paper.setMinimumHeight(self._paper_grid.sizeHint().height())
        return
        
        # Legacy renderer retained below temporarily for source-history comparison.
        # It is unreachable because the restored renderer above is authoritative.
        while self._paper_layout.count():
            item = self._paper_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        meta = data.get("metadata", {})
        panchang = data.get("panchang", {})
        avakahada = data.get("avakahada_chakra", {})
        lagna = data.get("lagna", {})
        planets = data.get("planets", [])
        dasha = data.get("dasha", [])

        # Ganesh Header
        ganesh_box = QVBoxLayout()
        om_lbl = QLabel("ॐ")
        om_lbl.setAlignment(Qt.AlignCenter)
        om_lbl.setStyleSheet("color: #9b183c; font-size: 32px; font-weight: 700; font-family: 'Georgia', serif;")
        ganesh_box.addWidget(om_lbl)

        ganesh_lbl = QLabel("श्रीमङ्गलमूर्त्तये नमः<br><span style='font-size:16px;'>आदित्याद्या ग्रहासर्वे सनक्षत्राः सराशयः ॥<br>कुर्वन्तुमङ्गल तस्य यस्यैषा जन्मपत्रिका ॥</span>")
        ganesh_lbl.setAlignment(Qt.AlignCenter)
        ganesh_lbl.setStyleSheet("color: #9b183c; font-size: 20px; font-weight: 700; font-family: 'Noto Serif Devanagari', 'Mangal', serif; line-height: 1.5;")
        ganesh_box.addWidget(ganesh_lbl)

        patrika_title = QLabel("जन्मपत्रिका (JANMAPATRIKA)")
        patrika_title.setAlignment(Qt.AlignCenter)
        patrika_title.setStyleSheet("color: #087329; font-size: 20px; font-weight: 800; letter-spacing: 1px; margin-top: 4px;")
        ganesh_box.addWidget(patrika_title)

        self._paper_layout.addLayout(ganesh_box)

        # Divider line
        div1 = QFrame()
        div1.setFrameShape(QFrame.HLine)
        div1.setStyleSheet("background: #087329; max-height: 2px;")
        self._paper_layout.addWidget(div1)

        name = meta.get("name", "—")
        bd = str(meta.get("birth_date", "—"))
        bt = str(meta.get("birth_time", "—"))
        city = meta.get("city") or meta.get("birth_place") or "—"
        lat = meta.get("latitude", 0)
        lon = meta.get("longitude", 0)
        tz = meta.get("timezone", 5.75)
        ayanamsha = meta.get("ayanamsha_type", "LAHIRI")

        moon = next((p for p in planets if p.get("name") == "Moon"), {})
        sun = next((p for p in planets if p.get("name") == "Sun"), {})

        shaka = nepali_digits(panchang.get("shaka_samvat", "उपलब्ध छैन"))
        vikram = nepali_digits(panchang.get("vikram_samvat", "उपलब्ध छैन"))
        samvatsara = panchang.get("samvatsara", "उपलब्ध छैन")
        ayana = panchang.get("ayana", "उपलब्ध छैन")
        ritu = panchang.get("ritu", "उपलब्ध छैन")
        masa = panchang.get("masa", "उपलब्ध छैन")
        paksha = panchang.get("paksha", "उपलब्ध छैन")
        tithi_ne = panchang.get("tithi", {}).get("nepali", "उपलब्ध छैन")
        day_ne = panchang.get("day", {}).get("nepali", "उपलब्ध छैन")
        nakshatra_ne = panchang.get("nakshatra", {}).get("nepali", "उपलब्ध छैन")
        yoga_ne = panchang.get("yoga", {}).get("nepali", "उपलब्ध छैन")
        karana_ne = panchang.get("karana", {}).get("nepali", "उपलब्ध छैन")
        ishta_kala = nepali_digits(panchang.get("ishta_kala", "उपलब्ध छैन"))
        sunrise = nepali_digits(panchang.get("sunrise", "उपलब्ध छैन"))
        sunset = nepali_digits(panchang.get("sunset", "उपलब्ध छैन"))
        lagna_sign = SIGN_NAMES_NE.get(lagna.get('sign_number', 1), "उपलब्ध छैन")
        lagna_deg = nepali_digits(format_degree(lagna.get('degree', 0)))
        moon_sign = SIGN_NAMES_NE.get(moon.get('sign_number', 1), "उपलब्ध छैन")

        charan = nepali_digits(avakahada.get("charan", "उपलब्ध छैन"))
        namaakshar = avakahada.get("namaakshar", "उपलब्ध छैन")
        varna = avakahada.get("varna", "उपलब्ध छैन")
        yoni = avakahada.get("yoni", "उपलब्ध छैन")
        gana = avakahada.get("gana", "उपलब्ध छैन")
        nadi = avakahada.get("nadi", "उपलब्ध छैन")
        varga = avakahada.get("varga", "उपलब्ध छैन")

        birth_year_ad = nepali_digits(bd[:4]) if bd != "—" else "उपलब्ध छैन"

        info_html = f"""
        <div style="text-align: justify; text-justify: inter-word; line-height: 2.2; font-size: 15px; color: #9b183c; font-weight: bold; font-family: 'Noto Serif Devanagari', 'Mangal', serif;">
        श्रीशालिवाहनीय शकः <span style="color: #087329;">{shaka}</span> श्रीवीरविक्रमादित्य संवत् <span style="color: #087329;">{vikram}</span> ईसवीय सन् <span style="color: #087329;">{birth_year_ad}</span> अत्रास्मिन् वर्षे <span style="color: #087329;">{samvatsara}</span> नाम संवत्सरे श्रीसूर्य <span style="color: #087329;">{ayana}</span> <span style="color: #087329;">{ritu}</span> ऋतौ अथ चान्द्रमानेन <span style="color: #087329;">{masa}</span> मासे <span style="color: #087329;">{paksha}</span> पक्ष <span style="color: #087329;">{day_ne}</span> वासरे <span style="color: #087329;">{tithi_ne}</span> तिथौ घट्यादिः <span style="color: #087329;">उपलब्ध छैन</span> घडी <span style="color: #087329;">उपलब्ध छैन</span> पला पर <span style="color: #087329;">{tithi_ne}</span> जन्म तिथौ <span style="color: #087329;">{nakshatra_ne}</span> नक्षत्रे घट्यादिः <span style="color: #087329;">उपलब्ध छैन</span> पर <span style="color: #087329;">{nakshatra_ne}</span> जन्म नक्षत्रस्य जन्म समये भुक्त घट्यादिः <span style="color: #087329;">उपलब्ध छैन</span> भभोग घट्यादिः <span style="color: #087329;">उपलब्ध छैन</span> प्रसंगादय <span style="color: #087329;">{yoga_ne}</span> योगे घट्यादिः <span style="color: #087329;">उपलब्ध छैन</span> घडी <span style="color: #087329;">उपलब्ध छैन</span> पला पर <span style="color: #087329;">{yoga_ne}</span> जन्म योगे तात्कालिक <span style="color: #087329;">{karana_ne}</span> करणे इति पञ्चाङ्ग ॥<br><br>
        अथ सौरमानेन मासोत्तमे <span style="color: #087329;">उपलब्ध छैन</span> मासे सूर्यसंक्रमादगतदिनेषु <span style="color: #087329;">उपलब्ध छैन</span> तदनुसार (ईसवीय मास <span style="color: #087329;">उपलब्ध छैन</span> तारिका: <span style="color: #087329;">उपलब्ध छैन</span> ) अत्र <span style="color: #087329;">{day_ne}</span> वासरे प्रमाणिक <span style="color: #087329;">{nepali_digits(bt)}</span> प्रवादनसमये स्थानीय समयानुसारेन श्रीसूर्योदयादिष्ट इष्टकाल घट्यादिः: <span style="color: #087329;">{ishta_kala}</span> घडी <span style="color: #087329;">उपलब्ध छैन</span> पला तदा जन्मसमये <span style="color: #087329;">{lagna_sign}</span> लग्नोदय <span style="color: #087329;">{lagna_deg}</span> राशि <span style="color: #087329;">उपलब्ध छैन</span> मीन नवमांशके <span style="color: #087329;">{moon_sign}</span> राशिगते चन्द्रमसि एवं विधे पञ्चाङ्ग शुद्धे देशे नेपाल प्रान्तार्न्तगत <span style="color: #087329;">{city}</span> मण्डले तदन्तर्गत स्थाने जन्मस्थान <span style="color: #087329;">{city}</span> यत्राक्षांश <span style="color: #087329;">{nepali_digits(lat)}°उ.</span> देशान्तरः <span style="color: #087329;">{nepali_digits(lon)}°पू.</span> मानक समय <span style="color: #087329;">{tz}</span> स्थानीय जन्मसमय <span style="color: #087329;">{nepali_digits(bt)}</span> निवसतः ............. <span style="color: #087329;">उपलब्ध छैन</span> गोत्रोत्पन्न श्रीमतः तस्य कुलोचित विवाहिता भार्यायां श्रीमती <span style="color: #087329;">उपलब्ध छैन</span> नाम्नीदेव्यां गर्भस्थ प्रथम <span style="color: #087329;">{name}</span> पुत्र रत्नमजीजनत् ।<br><br>
        नामाक्षरः <span style="color: #087329;">{namaakshar}</span> चरण: <span style="color: #087329;">{charan}</span> गण: <span style="color: #087329;">{gana}</span> इष्टकाल: <span style="color: #087329;">{ishta_kala}</span> सूर्योदय: <span style="color: #087329;">{sunrise}</span> सूर्यास्त: <span style="color: #087329;">{sunset}</span> अस्य होराशास्त्र प्रमाणेन <span style="color: #087329;">{nakshatra_ne}</span> नक्षत्रस्य <span style="color: #087329;">{charan}</span> चरणतेन <span style="color: #087329;">{namaakshar}</span> काराक्षरस्य <span style="color: #087329;">{yoni}</span> योनी <span style="color: #087329;">{nadi}</span> नाडी <span style="color: #087329;">{gana}</span> गण <span style="color: #087329;">{varga}</span> वर्ग जलचर प्रेतः आसन <span style="color: #087329;">{varna}</span> क्षत्रिय वर्णात्मक श्री <span style="color: #087329;">{name}</span> इति चिरञ्जीव शुभनाम प्रतिष्ठितं सचदेवद्विजाशीर्वादैर्दीर्घमायुर्भूयात् ।<br><br>
        <span style="color: #087329;">{moon_sign}</span> राशेर्घात तिथ्यादय :- <span style="color: #087329;">उपलब्ध छैन</span> तिथयः <span style="color: #087329;">उपलब्ध छैन</span> वासर: <span style="color: #087329;">उपलब्ध छैन</span> नक्षत्रः <span style="color: #087329;">उपलब्ध छैन</span> योगः <span style="color: #087329;">उपलब्ध छैन</span> करणः <span style="color: #087329;">उपलब्ध छैन</span> प्रहर : <span style="color: #087329;">{moon_sign}</span> पुरुष घात राशि : <span style="color: #087329;">उपलब्ध छैन</span> घात मासः ।<br>
        <div style="text-align: center; margin-top: 10px;">॥ इति जन्मपत्रिका ॥</div>
        </div>
        """
        info_widget = QLabel()
        info_widget.setWordWrap(True)
        info_widget.setText(info_html)
        self._paper_layout.addWidget(info_widget)

        # Section 3: Kundali Charts (D1 & Moon Side-by-Side)
        sec3_lbl = QLabel("🪐 ३. जन्म राशि कुण्डली (D1) र चन्द्र कुण्डली")
        sec3_lbl.setStyleSheet("color: #9b183c; font-size: 14px; font-weight: 700; margin-top: 6px;")
        self._paper_layout.addWidget(sec3_lbl)

        charts_box = QHBoxLayout()
        charts_box.setSpacing(16)

        # D1 Chart Box
        d1_box = QFrame()
        d1_box.setStyleSheet("background: #ffffff; border: 1px solid #087329; border-radius: 6px; padding: 6px;")
        d1_l = QVBoxLayout(d1_box)
        d1_title = QLabel("लग्न (राशि) कुण्डली — D1")
        d1_title.setAlignment(Qt.AlignCenter)
        d1_title.setStyleSheet("color: #087329; font-size: 13px; font-weight: 700;")
        d1_l.addWidget(d1_title)

        d1_widget = NorthIndianChartWidget(data, "D1", self._lang)
        d1_widget.setFixedSize(340, 270)
        d1_l.addWidget(d1_widget, 0, Qt.AlignCenter)
        charts_box.addWidget(d1_box)

        # Moon Chart Box
        moon_box = QFrame()
        moon_box.setStyleSheet("background: #ffffff; border: 1px solid #087329; border-radius: 6px; padding: 6px;")
        moon_l = QVBoxLayout(moon_box)
        moon_title = QLabel("चन्द्र कुण्डली")
        moon_title.setAlignment(Qt.AlignCenter)
        moon_title.setStyleSheet("color: #087329; font-size: 13px; font-weight: 700;")
        moon_l.addWidget(moon_title)

        moon_widget = NorthIndianChartWidget(data, "Moon", self._lang)
        moon_widget.setFixedSize(340, 270)
        moon_l.addWidget(moon_widget, 0, Qt.AlignCenter)
        charts_box.addWidget(moon_box)

        self._paper_layout.addLayout(charts_box)

        # Section 4: Planetary Positions Table
        sec4_lbl = QLabel("☿ ४. स्पष्ट ग्रह स्थिति तालिका (Planetary Longitudes & Details)")
        sec4_lbl.setStyleSheet("color: #9b183c; font-size: 14px; font-weight: 700; margin-top: 6px;")
        self._paper_layout.addWidget(sec4_lbl)

        planet_rows = []
        # Lagna row
        lagna_sign = SIGN_NAMES_NE.get(lagna.get("sign_number", 1), "—")
        lagna_deg = format_degree(lagna.get("longitude_in_sign", lagna.get("degree_in_sign", 0)))
        planet_rows.append(f"""
        <tr style="background: #fdf8f5; border-bottom: 1px solid #e0c8c8;">
            <td style="padding: 5px;"><b>लग्न (Ascendant)</b></td>
            <td style="padding: 5px;">{lagna_sign}</td>
            <td style="padding: 5px;">{nepali_digits(lagna_deg)}</td>
            <td style="padding: 5px;">—</td>
            <td style="padding: 5px;">—</td>
        </tr>
        """)

        planet_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        for p_name in planet_order:
            p = next((pl for pl in planets if pl.get("name") == p_name), None)
            if not p:
                continue
            name_ne = PLANET_NAMES_NE.get(p_name, p_name)
            s_name = SIGN_NAMES_NE.get(p.get("sign_number", 1), "—")
            long_deg = format_degree(p.get("longitude_in_sign", 0))
            
            st_list = []
            if p.get("is_retrograde"): st_list.append("वक्री")
            if p.get("is_combust"): st_list.append("अस्त")
            exalt = p.get("exaltation_state")
            if exalt == "exalted": st_list.append("उच्च")
            elif exalt == "debilitated": st_list.append("नीच")
            status_str = ", ".join(st_list) if st_list else "मार्गी (सामान्य)"

            nak = p.get("nakshatra", "—")

            planet_rows.append(f"""
            <tr style="border-bottom: 1px solid #e0c8c8;">
                <td style="padding: 5px;"><b>{name_ne} ({p_name})</b></td>
                <td style="padding: 5px;">{s_name}</td>
                <td style="padding: 5px;">{nepali_digits(long_deg)}</td>
                <td style="padding: 5px;">{nak}</td>
                <td style="padding: 5px;">{status_str}</td>
            </tr>
            """)

        planet_table_html = f"""
        <table width="100%" cellpadding="6" cellspacing="0" style="border: 1px solid #9b183c; border-collapse: collapse; background: #ffffff; font-size: 12px; text-align: center;">
            <tr style="background: #fdf0ec; color: #9b183c; font-weight: bold; border-bottom: 1px solid #9b183c;">
                <td width="22%">ग्रह (Planet)</td>
                <td width="18%">राशि (Sign)</td>
                <td width="20%">स्पष्ट अंश (Degree)</td>
                <td width="22%">नक्षत्र (Nakshatra)</td>
                <td width="18%">स्थिति (Status)</td>
            </tr>
            {"".join(planet_rows)}
        </table>
        """
        p_tbl_widget = QLabel()
        p_tbl_widget.setWordWrap(True)
        p_tbl_widget.setText(planet_table_html)
        self._paper_layout.addWidget(p_tbl_widget)

        # Section 5: Vimshottari Dasha Summary Table
        sec5_lbl = QLabel("⌛ ५. विंशोत्तरी महादशा विवरण (Vimshottari Dasha Summary)")
        sec5_lbl.setStyleSheet("color: #9b183c; font-size: 14px; font-weight: 700; margin-top: 6px;")
        self._paper_layout.addWidget(sec5_lbl)

        dasha_cells = []
        for d in dasha[:9]:
            lord = d.get("lord", "")
            lord_ne = PLANET_NAMES_NE.get(lord, lord)
            end_date = d.get("end", "—")
            is_p = d.get("is_partial", False)
            p_str = " (जन्मकालीन भोग्य)" if is_p else ""
            dasha_cells.append(f"""
            <td style="border: 1px solid #087329; padding: 6px; text-align: center; font-size: 11px; background: {'#fff8f0' if is_p else '#ffffff'};">
                <b>{lord_ne}</b>{p_str}<br>
                <span style="color: #087329; font-weight: bold;">{nepali_digits(end_date)} सम्म</span>
            </td>
            """)

        dasha_table_html = f"""
        <table width="100%" cellpadding="4" cellspacing="0" style="border: 1px solid #087329; border-collapse: collapse; font-size: 11px;">
            <tr>
                {"".join(dasha_cells[:5])}
            </tr>
            <tr>
                {"".join(dasha_cells[5:])}
            </tr>
        </table>
        """
        d_tbl_widget = QLabel()
        d_tbl_widget.setWordWrap(True)
        d_tbl_widget.setText(dasha_table_html)
        self._paper_layout.addWidget(d_tbl_widget)

        # Footer Note
        footer_note = QLabel("शिवराम ज्योतिष सफ्टवेयरद्वारा निर्मित आधिकारिक जन्मकुण्डली प्रतिवेदन")
        footer_note.setAlignment(Qt.AlignCenter)
        footer_note.setStyleSheet("color: #5f625b; font-size: 11px; font-weight: bold; margin-top: 8px;")
        self._paper_layout.addWidget(footer_note)

    def _configure_printer(self, printer) -> None:
        printer.setPageSize(QPageSize(QPageSize.A4))
        layout = printer.pageLayout()
        layout.setOrientation(QPageLayout.Portrait)
        layout.setMargins(QMarginsF(10, 10, 10, 10))
        printer.setPageLayout(layout)

    def _render_to_printer(self, printer) -> int:
        """Render the complete graphics scene, including the embedded paper."""
        self._paper.ensurePolished()
        self._paper_layout.activate()
        self._paper_grid.activate()
        QApplication.processEvents()
        if self._paper_proxy is None:
            raise RuntimeError("Janmapatrika document is not ready for printing")

        # The scene contains the wrapper proxy, which owns the complete paper
        # widget tree. Export at 100%, independent of the viewing zoom, then
        # restore the user's zoom after printing/PDF generation.
        previous_zoom = self._zoom
        self._paper_proxy.setScale(1.0)
        wrapper_width = max(1, self._doc_wrapper.width())
        wrapper_height = max(1, self._doc_wrapper.height())
        self._paper_proxy.setPos(0, 0)
        self._scene.setSceneRect(0, 0, wrapper_width, wrapper_height)
        QApplication.processEvents()

        target = printer.pageLayout().paintRectPixels(printer.resolution())
        scale = target.width() / wrapper_width
        logical_page_height = max(1, int(target.height() / scale))
        pages = max(1, math.ceil(wrapper_height / logical_page_height))
        painter = QPainter(printer)
        if not painter.isActive():
            self._set_zoom(previous_zoom)
            raise RuntimeError("Printer painter could not be started")
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        try:
            for page in range(pages):
                if page and not printer.newPage():
                    raise RuntimeError("Printer could not create a new page")
                source_top = page * logical_page_height
                source_page_height = min(logical_page_height, wrapper_height - source_top)
                source_rect = QRectF(0, source_top, wrapper_width, source_page_height)
                painter.save()
                painter.setClipRect(target)
                # QGraphicsScene maps the proxy and every child chart/label
                # into printer coordinates without rasterising the document.
                self._scene.render(
                    painter,
                    QRectF(target.left(), target.top(), target.width(), target.height()),
                    source_rect,
                    Qt.KeepAspectRatio,
                )
                painter.restore()
                QApplication.processEvents()
        finally:
            painter.end()
            self._set_zoom(previous_zoom)
        return pages

    def _document_file_stem(self) -> str:
        """Return a filesystem-safe filename based on the entered person's name."""
        metadata = (self._data or {}).get("metadata") or {}
        name = first_value(metadata.get("full_name"), metadata.get("name"), "janmapatrika")
        safe_name = "".join(
            character for character in str(name)
            if character.isalnum() or character in {" ", "-", "_"}
        ).strip()
        return safe_name or "janmapatrika"

    def _print_patrika(self):
        try:
            from PySide6.QtPrintSupport import QPrintDialog, QPrinter
            printer = QPrinter(QPrinter.HighResolution)
            printer.setDocName(self._document_file_stem())
            self._configure_printer(printer)
            dlg = QPrintDialog(printer, self)
            if dlg.exec() == QPrintDialog.Accepted:
                self._render_to_printer(printer)
                QMessageBox.information(self, "प्रिन्ट", "जन्मपत्रिका सफलतापूर्वक प्रिन्ट गरियो।")
        except Exception as e:
            QMessageBox.warning(self, "प्रिन्ट त्रुटि", f"प्रिन्ट गर्न सकिएन: {e}")

    def _export_pdf(self):
        try:
            from PySide6.QtPrintSupport import QPrinter
            default_name = f"{self._document_file_stem()}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Janmapatrika PDF", default_name, "PDF Files (*.pdf)"
            )
            if file_path:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setDocName(self._document_file_stem())
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                self._configure_printer(printer)
                self._render_to_printer(printer)
                QMessageBox.information(self, "PDF", f"PDF फाइल यहाँ सुरक्षित गरियो:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "PDF त्रुटि", f"PDF फाइल बनाउन सकिएन: {e}")
