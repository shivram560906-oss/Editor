# -*- coding: utf-8 -*-
"""
gui/widgets/traditional_cheena_a4.py

Traditional Nepali Janmapatrika (चिना) A4 PDF Document & Print Engine.
Generates an authentic, beautifully styled, 4-page traditional Nepali Cheena
with auspicious red/gold borders, Sanskrit verses, high-resolution D1/D9 charts,
Avakahada Chakra, planetary longitudes, Ashtakavarga, Dasha systems, and remedies.

Supports:
  1. Pixel-perfect A4 Portrait PDF export (High-Resolution vector quality).
  2. Direct print via Windows print dialog.
  3. Interactive multi-page desktop preview with zoom and page selection.
"""
from __future__ import annotations

import base64
import datetime
import html
import os
import sys
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QByteArray, QBuffer, QEventLoop, QIODevice, QMarginsF, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor, QFont, QGuiApplication, QImage, QPageLayout, QPageSize,
    QPainter, QPen, QPolygonF, QTextDocument
)
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except Exception:
    HAS_WEBENGINE = False

try:
    import fitz
    HAS_FITZ = True
except Exception:
    HAS_FITZ = False


_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import COLOR_GOLD, BG_SECONDARY, BORDER_COLOR, COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED
from gui.utils.bs_calendar import gregorian_to_bs, BS_MONTHS_NE, to_nepali_digits

NE_DIGITS = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"]
SIGN_NAMES_NE = ["", "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"]

PLANET_NAMES_NE = {
    "Lagna": "लग्न", "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
}

PLANET_ABBR_NE = {
    "Sun": "सू", "Moon": "चं", "Mars": "मं", "Mercury": "बु",
    "Jupiter": "गु", "Venus": "शु", "Saturn": "श",
    "Rahu": "रा", "Ketu": "के"
}

def to_ne_digits(val: Any) -> str:
    """Convert any number or string with digits to Nepali Devanagari numerals."""
    if val is None:
        return "—"
    s = str(val)
    return "".join(NE_DIGITS[int(ch)] if ch.isdigit() else ch for ch in s)

def dms_format_ne(deg_val: Optional[float]) -> str:
    """Format decimal degrees into Nepali Degree-Minute-Second (००° ००' ००\")."""
    if deg_val is None:
        return "००° ००' ००\""
    d = int(deg_val)
    rem = abs(deg_val - d) * 60.0
    m = int(rem)
    s = int((rem - m) * 60.0)
    return f"{to_ne_digits(f'{d:02d}')}° {to_ne_digits(f'{m:02d}')}' {to_ne_digits(f'{s:02d}')}\""

def to_nepali_place_name(place: Optional[str]) -> str:
    """Format birth/office place into clean Nepali text, translating known English locations."""
    if not place:
        return "कपिलवस्तु, नेपाल"
    p = str(place).strip()
    name_map = {
        "Kapilvastu": "कपिलवस्तु",
        "Kathmandu": "काठमाडौं",
        "Lalitpur": "ललितपुर",
        "Bhaktapur": "भक्तपुर",
        "Pokhara": "पोखरा",
        "Kaski": "कास्की",
        "Chitwan": "चितवन",
        "Bharatpur": "भरतपुर",
        "Rupandehi": "रूपन्देही",
        "Butwal": "बुटवल",
        "Bhairahawa": "भैरहवा",
        "Lumbini": "लुम्बिनी",
        "Taulihawa": "तौलिहवा",
        "Biratnagar": "विराटनगर",
        "Dharan": "धरान",
        "Nepalgunj": "नेपालगञ्ज",
        "Dang": "दाङ",
        "Surkhet": "सुर्खेत",
        "Dhangadhi": "धनगढी",
        "Hetauda": "हेटौंडा",
        "Janakpur": "जनकपुर",
        "Birgunj": "वीरगञ्ज",
        "Palpa": "पाल्पा",
        "Gulmi": "गुल्मी",
        "Arghakhanchi": "अर्घाखाँची",
        "Gorkha": "गोरखा",
        "Baglung": "बागलुङ",
    }
    clean_p = p.replace(", Nepal", "").replace(",नेपाल", "").strip()
    if clean_p in name_map:
        return f"{name_map[clean_p]}, नेपाल"
    if "नेपाल" in p:
        return p
    if any("\u0900" <= ch <= "\u097f" for ch in p):
        return f"{p}, नेपाल"
    return f"{p}, नेपाल"

def _ensure_qt_gui_app():
    """Ensure a Qt application exists for offscreen QImage chart rendering.

    Prefer QApplication (widgets-capable). If this module is the first code to
    touch Qt — e.g. it is imported/used before the GUI creates its QApplication,
    as in smoke_test.py / headless tests — installing a bare QGuiApplication here
    would make QApplication.instance() return that non-widget app forever, so
    constructing any QWidget would then abort natively. Preferring QApplication
    keeps the process widget-capable.
    """
    try:
        from PySide6.QtWidgets import QApplication
    except Exception:
        QApplication = None

    if QApplication is not None:
        app = QApplication.instance()
        if app is None:
            try:
                app = QApplication(sys.argv if hasattr(sys, "argv") and sys.argv else ["cheena_a4"])
            except Exception:
                app = None
        if app is not None:
            return app

    # Non-widget fallback (only when QtWidgets is unavailable).
    app = QGuiApplication.instance()
    if app is None:
        try:
            app = QGuiApplication(sys.argv if hasattr(sys, "argv") and sys.argv else ["cheena_a4"])
        except Exception:
            pass
    return app

def render_traditional_chart_base64(
    lagna_sign: int,
    house_contents: Dict[int, List[str]],
    title: str = "",
    size: int = 340,
    is_sav: bool = False
) -> str:
    """
    Renders an authentic North Indian diamond chart into a crisp high-resolution base64 PNG.
    Features traditional crimson/vermilion frame, bold sign numbers, and centered planet tags.
    """
    _ensure_qt_gui_app()
    scale = 2.0
    w = int(size * scale)
    h = int(size * scale)

    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(QColor("#fffdfa"))

    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    pad = 12 * scale
    chart_w = w - 2 * pad
    chart_h = h - 2 * pad
    x0, y0 = pad, pad
    x1, y1 = w - pad, h - pad
    xmid, ymid = (x0 + x1) / 2.0, (y0 + y1) / 2.0

    # Outer traditional double frame
    pen_outer = QPen(QColor("#881337"), int(3 * scale))
    painter.setPen(pen_outer)
    painter.drawRect(QRectF(x0, y0, chart_w, chart_h))

    pen_inner_gold = QPen(QColor("#b45309"), int(1.5 * scale))
    painter.setPen(pen_inner_gold)
    painter.drawRect(QRectF(x0 + 3 * scale, y0 + 3 * scale, chart_w - 6 * scale, chart_h - 6 * scale))

    # Grid diagonals
    painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))
    painter.drawLine(QPointF(x0, y1), QPointF(x1, y0))

    # Center diamond
    diamond = QPolygonF([
        QPointF(xmid, y0),
        QPointF(x1, ymid),
        QPointF(xmid, y1),
        QPointF(x0, ymid)
    ])
    painter.drawPolygon(diamond)

    # House centroids (normalized 0.0 - 1.0)
    house_positions = {
        1:  {"sign": (0.50, 0.12), "planets": (0.50, 0.28)},
        2:  {"sign": (0.26, 0.08), "planets": (0.26, 0.17)},
        3:  {"sign": (0.08, 0.26), "planets": (0.16, 0.26)},
        4:  {"sign": (0.13, 0.50), "planets": (0.28, 0.50)},
        5:  {"sign": (0.08, 0.74), "planets": (0.16, 0.74)},
        6:  {"sign": (0.26, 0.92), "planets": (0.26, 0.83)},
        7:  {"sign": (0.50, 0.88), "planets": (0.50, 0.72)},
        8:  {"sign": (0.74, 0.92), "planets": (0.74, 0.83)},
        9:  {"sign": (0.92, 0.74), "planets": (0.84, 0.74)},
        10: {"sign": (0.87, 0.50), "planets": (0.72, 0.50)},
        11: {"sign": (0.92, 0.26), "planets": (0.84, 0.26)},
        12: {"sign": (0.74, 0.08), "planets": (0.74, 0.17)},
    }

    font_sign = QFont("Noto Sans Devanagari", int(10 * scale), QFont.Bold)
    font_planet = QFont("Noto Sans Devanagari", int(9.5 * scale), QFont.Bold)
    font_sav = QFont("Noto Sans Devanagari", int(13 * scale), QFont.Bold)

    for h_num in range(1, 13):
        pos = house_positions[h_num]
        sx = x0 + pos["sign"][0] * chart_w
        sy = y0 + pos["sign"][1] * chart_h
        px = x0 + pos["planets"][0] * chart_w
        py = y0 + pos["planets"][1] * chart_h
        sign_num = ((lagna_sign - 1 + h_num - 1) % 12) + 1

        if is_sav:
            items = house_contents.get(h_num, [])
            val_str = items[0] if items else "०"
            painter.setFont(font_sav)
            painter.setPen(QColor("#1e3a8a"))
            painter.drawText(
                QRectF(px - 28 * scale, py - 14 * scale, 56 * scale, 28 * scale),
                Qt.AlignCenter, val_str
            )
            painter.setFont(font_sign)
            painter.setPen(QColor("#9a3412"))
            painter.drawText(
                QRectF(sx - 18 * scale, sy - 10 * scale, 36 * scale, 20 * scale),
                Qt.AlignCenter, to_ne_digits(sign_num)
            )
            continue

        # Draw sign number in traditional crimson
        painter.setFont(font_sign)
        painter.setPen(QColor("#9a3412"))
        painter.drawText(
            QRectF(sx - 18 * scale, sy - 10 * scale, 36 * scale, 20 * scale),
            Qt.AlignCenter, to_ne_digits(sign_num)
        )

        # Draw planets in vertical stack
        planets = house_contents.get(h_num, [])
        if planets:
            painter.setFont(font_planet)
            painter.setPen(QColor("#0f172a"))
            line_h = 16 * scale
            total_h = len(planets) * line_h
            start_y = py - (total_h / 2.0) + (line_h / 2.0)

            for i, p_str in enumerate(planets):
                item_y = start_y + i * line_h
                painter.drawText(
                    QRectF(px - 34 * scale, item_y - 9 * scale, 68 * scale, 18 * scale),
                    Qt.AlignCenter, p_str
                )

    painter.end()

    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    b64_str = base64.b64encode(ba.data()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def generate_traditional_cheena_html(data: Dict[str, Any], language: str = "ne") -> str:
    """
    Constructs the complete 4-page A4 Traditional Nepali Janmapatrika HTML document.
    """
    meta = data.get("metadata", {})
    panchang = data.get("panchang", {})
    avakahada = data.get("avakahada_chakra", {})
    lagna = data.get("lagna", {})
    planets = data.get("planets", [])
    vargas = data.get("vargas", {})
    dasha = data.get("dasha", [])
    ashtottari = data.get("ashtottari_dasha", [])
    yogini = data.get("yogini_dasha", [])
    ashtakavarga = data.get("ashtakavarga", {})
    remedies = data.get("remedies", {})

    # Basic identity
    name = meta.get("name") or meta.get("full_name") or "जातक"
    gender_raw = meta.get("gender")
    if gender_raw is None:
        gender_raw = meta.get("sex", 0)
    g_str = str(gender_raw).lower().strip()
    is_female = g_str in ("1", "female", "f", "महिला", "स्त्री", "girl", "daughter", "पुत्री")
    lbl = str(meta.get("gender_label", "")).strip().lower()
    if lbl in ("female", "महिला", "स्त्री", "पुत्री"):
        is_female = True
    elif lbl in ("male", "पुरुष", "पुत्र", "बालक"):
        is_female = False
    gender_label = "पुत्री" if is_female else "पुत्र"

    father = meta.get("father_name") or "—"
    mother = meta.get("mother_name") or "—"
    gotra = meta.get("gotra") or "—"
    birth_place = to_nepali_place_name(meta.get("birth_place") or meta.get("city") or "कपिलवस्तु, नेपाल")
    center_raw = meta.get("center_address") or meta.get("office_address")
    if not center_raw or "kathmandu" in str(center_raw).lower() or "काठमाडौं" in str(center_raw):
        center_place = "कपिलवस्तु, नेपाल"
    else:
        center_place = to_nepali_place_name(center_raw)

    # Dates: Priority to BS date from ribbon/metadata if present
    b_date_str = str(meta.get("birth_date", "2000-01-01"))[:10]
    b_time_str = str(meta.get("birth_time", "12:00:00"))

    bs_meta = meta.get("birth_date_bs") or meta.get("bs_date") or meta.get("date_bs")
    bs_dict = data.get("bs") or meta.get("bs")

    bs_str = ""
    if bs_meta:
        cleaned_bs = str(bs_meta).strip()
        if not cleaned_bs.startswith("वि.सं."):
            bs_str = f"वि.सं. {to_ne_digits(cleaned_bs)}"
        else:
            bs_str = to_ne_digits(cleaned_bs)
        if "गते" not in bs_str and any(m in bs_str for m in BS_MONTHS_NE):
            bs_str += " गते"
    elif isinstance(bs_dict, dict) and bs_dict.get("year"):
        try:
            m_num = int(bs_dict.get("month", 1))
            m_name = BS_MONTHS_NE[m_num - 1] if 1 <= m_num <= 12 else ""
            bs_str = f"वि.सं. {to_ne_digits(bs_dict.get('year'))} {m_name} {to_ne_digits(bs_dict.get('day'))} गते"
        except Exception:
            pass

    if not bs_str:
        bs_str = f"वि.सं. {to_ne_digits(b_date_str)}"
        try:
            dt_val = datetime.date.fromisoformat(b_date_str)
            bs_info = gregorian_to_bs(dt_val.year, dt_val.month, dt_val.day)
            if bs_info:
                m_num = int(bs_info.get("month", 1))
                m_name = BS_MONTHS_NE[m_num - 1] if 1 <= m_num <= 12 else ""
                bs_str = f"वि.सं. {to_ne_digits(bs_info.get('year'))} {m_name} {to_ne_digits(bs_info.get('day'))} गते"
        except Exception:
            pass

    ad_str = f"ई.सं. {to_ne_digits(b_date_str)}"
    time_str = f"{to_ne_digits(b_time_str[:5])} बजे"

    # Panchanga details
    samvat_val = panchang.get("samvatsara")
    if isinstance(samvat_val, dict):
        samvat_str = samvat_val.get("nepali") or samvat_val.get("name") or "कालयुक्त"
    else:
        samvat_str = str(samvat_val or "कालयुक्त")

    tithi_dict = panchang.get("tithi") or {}
    if isinstance(tithi_dict, dict):
        tithi_name = tithi_dict.get("birth_nepali") or tithi_dict.get("nepali") or "शुक्ल पक्ष"
        paksha_name = tithi_dict.get("paksha_nepali") or ("शुक्ल पक्ष" if "शुक्ल" in str(tithi_name) else "कृष्ण पक्ष")
    else:
        tithi_name = str(tithi_dict)
        paksha_name = "शुक्ल पक्ष"

    vara_dict = panchang.get("vara") or {}
    if isinstance(vara_dict, dict):
        vara_name = vara_dict.get("nepali") or vara_dict.get("name") or "सोमवार"
    else:
        vara_name = str(vara_dict or "सोमवार")

    nakshatra_dict = panchang.get("nakshatra") or {}
    if isinstance(nakshatra_dict, dict):
        nakshatra_name = nakshatra_dict.get("nepali") or nakshatra_dict.get("name") or "रोहिणी"
        pada_num = nakshatra_dict.get("pada") or 1
    else:
        nakshatra_name = str(nakshatra_dict or "रोहिणी")
        pada_num = 1

    yoga_dict = panchang.get("yoga") or {}
    if isinstance(yoga_dict, dict):
        yoga_name = yoga_dict.get("birth_nepali") or yoga_dict.get("nepali") or "शुभ"
    else:
        yoga_name = str(yoga_dict or "शुभ")

    karana_dict = panchang.get("karana") or {}
    if isinstance(karana_dict, dict):
        karana_name = karana_dict.get("birth_nepali") or karana_dict.get("nepali") or "बव"
    else:
        karana_name = str(karana_dict or "बव")

    sunrise_val = panchang.get("sunrise") or {}
    sunrise_time = sunrise_val.get("time", "०६:००") if isinstance(sunrise_val, dict) else str(sunrise_val or "०६:००")
    sunset_val = panchang.get("sunset") or {}
    sunset_time = sunset_val.get("time", "१८:१५") if isinstance(sunset_val, dict) else str(sunset_val or "१८:१५")

    # Avakahada Details
    name_akshara = avakahada.get("name_akshara") or "—"
    paya = avakahada.get("paya") or "स्वर्ण"
    varna = avakahada.get("varna") or "क्षत्रिय"
    vashya = avakahada.get("vashya") or "चतुष्पद"
    tara = avakahada.get("tara") or "जन्म"
    yoni = avakahada.get("yoni") or "सर्प"
    gana = avakahada.get("gana") or "मनुष्य"
    nadi = avakahada.get("nadi") or "अन्त्य"
    tatva = avakahada.get("tatva") or "पृथ्वी"
    chandra_rashi = avakahada.get("chandra_rashi") or "वृष"
    rashi_lord = avakahada.get("rashi_lord") or "शुक्र"

    # Lagna & D1 Chart
    lagna_sign = int(lagna.get("sign_number") or 1)
    lagna_deg = lagna.get("longitude_in_sign", 0.0)

    # Build D1 House contents
    d1_houses: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
    retro_sym = "(व)"
    for p in planets:
        pname = p.get("name", "")
        h = p.get("house", 1)
        abbr = PLANET_ABBR_NE.get(pname, pname[:2])
        if p.get("is_retrograde") and pname not in ("Rahu", "Ketu"):
            abbr += retro_sym
        if 1 <= h <= 12 and pname not in ("Uranus", "Neptune", "Pluto", "Chiron"):
            d1_houses[h].append(abbr)

    # Build D9 Navamsha House contents
    d9_lagna = 1
    d9_houses: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
    d9_data = vargas.get("D9", {})
    if d9_data:
        d9_lagna = int(d9_data.get("lagna", {}).get("sign_number") or 1)
        d9_planets = d9_data.get("planets", [])
        if isinstance(d9_planets, list):
            for pinfo in d9_planets:
                if isinstance(pinfo, dict):
                    pname = pinfo.get("name", "")
                    sign = int(pinfo.get("sign_number") or 1)
                    h = ((sign - d9_lagna) % 12) + 1
                    abbr = PLANET_ABBR_NE.get(pname, pname[:2])
                    if 1 <= h <= 12 and pname not in ("Uranus", "Neptune", "Pluto", "Chiron"):
                        d9_houses[h].append(abbr)
        elif isinstance(d9_planets, dict):
            for pname, pinfo in d9_planets.items():
                if isinstance(pinfo, dict):
                    sign = int(pinfo.get("sign_number") or 1)
                    h = ((sign - d9_lagna) % 12) + 1
                    abbr = PLANET_ABBR_NE.get(pname, pname[:2])
                    if 1 <= h <= 12 and pname not in ("Uranus", "Neptune", "Pluto", "Chiron"):
                        d9_houses[h].append(abbr)

    # Build Chandra Kundali
    moon_p = next((p for p in planets if p.get("name") == "Moon"), {})
    moon_sign_num = int(moon_p.get("sign_number") or lagna_sign)
    chandra_houses: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
    for p in planets:
        pname = p.get("name", "")
        p_sign = int(p.get("sign_number") or 1)
        h_chandra = ((p_sign - moon_sign_num) % 12) + 1
        abbr = PLANET_ABBR_NE.get(pname, pname[:2])
        if p.get("is_retrograde") and pname not in ("Rahu", "Ketu"):
            abbr += retro_sym
        if 1 <= h_chandra <= 12 and pname not in ("Uranus", "Neptune", "Pluto", "Chiron"):
            chandra_houses[h_chandra].append(abbr)

    # Build Charts as Base64 images
    img_d1 = render_traditional_chart_base64(lagna_sign, d1_houses, "जन्म कुण्डली (D1)", size=300)
    img_d9 = render_traditional_chart_base64(d9_lagna, d9_houses, "नवमांश कुण्डली (D9)", size=300)
    img_chandra = render_traditional_chart_base64(moon_sign_num, chandra_houses, "चन्द्र कुण्डली", size=270)
    img_chalit = render_traditional_chart_base64(lagna_sign, d1_houses, "भाव चलित कुण्डली", size=270)

    # SAV Ashtakavarga Chart
    sav_scores = ashtakavarga.get("samudaya", {}).get("scores", []) or [28] * 12
    sav_houses: Dict[int, List[str]] = {}
    for h_num in range(1, 13):
        sign_idx = ((lagna_sign - 1 + h_num - 1) % 12)
        score = sav_scores[sign_idx] if sign_idx < len(sav_scores) else 28
        sav_houses[h_num] = [to_ne_digits(score)]
    img_sav = render_traditional_chart_base64(lagna_sign, sav_houses, "समुदाय अष्टकवर्ग", size=270, is_sav=True)

    # Planet Table Rows
    planet_rows_html = []
    for p in planets:
        pname = p.get("name", "")
        if pname in ("Uranus", "Neptune", "Pluto", "Chiron"):
            continue
        p_ne = PLANET_NAMES_NE.get(pname, pname)
        s_num = int(p.get("sign_number") or 1)
        s_ne = SIGN_NAMES_NE[s_num] if 1 <= s_num <= 12 else "—"
        deg_str = dms_format_ne(p.get("longitude_in_sign", 0.0))
        nak_name = p.get("nakshatra") or "—"
        pada = p.get("nakshatra_pada") or "१"
        state_list = []
        if p.get("is_retrograde") and pname not in ("Rahu", "Ketu"):
            state_list.append("वक्री")
        if p.get("is_combust"):
            state_list.append("अस्त")
        exalt = str(p.get("exaltation_state", "")).lower()
        if "exalted" in exalt:
            state_list.append("उच्च")
        elif "debilitated" in exalt:
            state_list.append("नीच")
        state_str = ", ".join(state_list) if state_list else "मार्गी / सामान्य"

        planet_rows_html.append(f"""
        <tr>
            <td style="font-weight: bold; color: #881337;">{p_ne}</td>
            <td>{s_ne}</td>
            <td>{deg_str}</td>
            <td>{nak_name} (चरण {to_ne_digits(pada)})</td>
            <td>{to_ne_digits(p.get('house', '—'))}</td>
            <td>{state_str}</td>
        </tr>
        """)

    # Vimshottari Table Rows (up to 9 mahadashas)
    vimshottari_rows_html = []
    for node in dasha[:9]:
        lord = node.get("lord_nepali") or PLANET_NAMES_NE.get(node.get("lord", ""), node.get("lord", ""))
        yrs = to_ne_digits(node.get("total_years", "—"))
        s_bs = to_ne_digits(node.get("start_bs") or str(node.get("start", ""))[:10])
        e_bs = to_ne_digits(node.get("end_bs") or str(node.get("end", ""))[:10])
        vimshottari_rows_html.append(f"""
        <tr>
            <td style="font-weight: bold; color: #881337;">{lord}</td>
            <td>{yrs} वर्ष</td>
            <td>{s_bs}</td>
            <td>{e_bs}</td>
        </tr>
        """)

    # Ashtottari Table Rows
    ashtottari_rows_html = []
    for node in ashtottari[:8]:
        lord = node.get("lord_nepali") or PLANET_NAMES_NE.get(node.get("lord", ""), node.get("lord", ""))
        yrs = to_ne_digits(node.get("total_years", "—"))
        s_bs = to_ne_digits(node.get("start_bs") or str(node.get("start", ""))[:10])
        e_bs = to_ne_digits(node.get("end_bs") or str(node.get("end", ""))[:10])
        ashtottari_rows_html.append(f"""
        <tr>
            <td style="font-weight: bold; color: #1e3a8a;">{lord}</td>
            <td>{yrs} वर्ष</td>
            <td>{s_bs}</td>
            <td>{e_bs}</td>
        </tr>
        """)

    # Yogini Table Rows
    yogini_rows_html = []
    for node in yogini[:8]:
        y_name = node.get("nepali") or node.get("name", "—")
        yrs = to_ne_digits(node.get("total_years", "—"))
        s_bs = to_ne_digits(node.get("start_bs") or str(node.get("start", ""))[:10])
        e_bs = to_ne_digits(node.get("end_bs") or str(node.get("end", ""))[:10])
        yogini_rows_html.append(f"""
        <tr>
            <td style="font-weight: bold; color: #166534;">{y_name}</td>
            <td>{yrs} वर्ष</td>
            <td>{s_bs}</td>
            <td>{e_bs}</td>
        </tr>
        """)

    # Remedies Section
    gem_recs = remedies.get("gemstones", {})
    life_stone = gem_recs.get("life_stone", {}).get("gemstone_ne", "माणिक्य वा उपयुक्त रत्न")
    lucky_stone = gem_recs.get("lucky_stone", {}).get("gemstone_ne", "पन्ना वा पुखराज")
    punya_stone = gem_recs.get("punya_stone", {}).get("gemstone_ne", "मुक्ता वा मूङ्गा")
    rudraksha_info = remedies.get("rudraksha", {})
    rec_rudraksha = rudraksha_info.get("primary", {}).get("name_ne", "पञ्चमुखी रुद्राक्ष")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>नेपाली परम्परागत जन्मपत्रिका - {html.escape(name)}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 10mm;
        }}
        body {{
            font-family: 'Noto Serif Devanagari', 'Mangal', 'Kokila', serif;
            margin: 0;
            padding: 0;
            background-color: #f7f3ea;
            color: #1a1a1a;
            font-size: 13px;
            line-height: 1.4;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        .cheena-page {{
            page-break-after: always;
            box-sizing: border-box;
            width: 190mm;
            min-height: 275mm;
            margin: 0 auto 20px auto;
            padding: 14mm 14mm 12mm 14mm;
            background: #fffefb;
            border: 3px double #881337;
            position: relative;
        }}
        .inner-border {{
            border: 1px solid #b45309;
            padding: 10px;
            min-height: 250mm;
            box-sizing: border-box;
        }}
        .corner-ornament {{
            position: absolute;
            font-size: 16px;
            color: #881337;
            font-weight: bold;
        }}
        .top-left {{ top: 18mm; left: 18mm; }}
        .top-right {{ top: 18mm; right: 18mm; }}
        .bottom-left {{ bottom: 16mm; left: 18mm; }}
        .bottom-right {{ bottom: 16mm; right: 18mm; }}
        
        .header-section {{
            text-align: center;
            margin-bottom: 8px;
        }}
        .om-symbol {{
            font-size: 32px;
            color: #881337;
            font-weight: bold;
            line-height: 1;
            margin-bottom: 2px;
        }}
        .ganesh-title {{
            font-size: 20px;
            color: #881337;
            font-weight: 800;
            margin-bottom: 4px;
        }}
        .shloka {{
            font-size: 12px;
            color: #b45309;
            font-style: italic;
            font-weight: 600;
            line-height: 1.5;
            margin-bottom: 8px;
        }}
        .patrika-title {{
            background: #881337;
            color: #ffffff;
            font-size: 15px;
            font-weight: bold;
            padding: 4px 12px;
            display: inline-block;
            border-radius: 4px;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        table.grid-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
            font-size: 12px;
        }}
        table.grid-table th, table.grid-table td {{
            border: 1px solid #d4af37;
            padding: 5px 8px;
            text-align: left;
        }}
        table.grid-table th {{
            background: #fdf6e7;
            color: #881337;
            font-weight: bold;
        }}
        
        .section-header {{
            background: #fbf0d8;
            border-left: 4px solid #881337;
            padding: 4px 8px;
            font-size: 13px;
            font-weight: bold;
            color: #881337;
            margin: 10px 0 6px 0;
        }}
        
        .charts-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            text-align: center;
        }}
        .chart-box {{
            flex: 1;
            text-align: center;
            padding: 4px;
        }}
        .chart-box img {{
            max-width: 250px;
            height: auto;
            border: 1px solid #b45309;
            background: #ffffff;
        }}
        .chart-caption {{
            font-size: 12px;
            font-weight: bold;
            color: #881337;
            margin-top: 4px;
        }}
        
        .footer-blessing {{
            text-align: center;
            margin-top: 15px;
            font-weight: bold;
            color: #881337;
            font-size: 13px;
            border-top: 1px dashed #b45309;
            padding-top: 8px;
        }}
        .signature-block {{
            display: flex;
            justify-content: space-between;
            margin-top: 25px;
            padding: 0 20px;
            font-size: 12px;
        }}
    </style>
    </head>
    <body>

    <!-- ==================== पृष्ठ १ : मुख्य जन्मपत्रिका ==================== -->
    <div class="cheena-page">
        <div class="inner-border">
            <span class="corner-ornament top-left">卐</span>
            <span class="corner-ornament top-right">卐</span>
            <span class="corner-ornament bottom-left">卐</span>
            <span class="corner-ornament bottom-right">卐</span>

            <div class="header-section">
                <div class="om-symbol">ॐ</div>
                <div class="ganesh-title">॥ श्री गणेशाय नमः ॥ श्रीमङ्गलमूर्तये नमः ॥</div>
                <div class="shloka">
                    आदित्याद्या ग्रहासर्वे सनक्षत्राः सराशयः ।<br>
                    कुर्वन्तु मङ्गलं तस्य यस्यैषा जन्मपत्रिका ॥
                </div>
                <div class="patrika-title">॥ स्वस्ति श्री जन्मपत्रिका (चिना) ॥</div>
            </div>

            <!-- जन्म तथा पञ्चाङ्ग विवरण -->
            <table class="grid-table">
                <tr>
                    <th width="20%">नाम:</th>
                    <td width="30%"><b>{html.escape(name)}</b> ({gender_label})</td>
                    <th width="20%">जन्म मिति:</th>
                    <td width="30%"><b>{bs_str}</b><br><small>{ad_str}</small></td>
                </tr>
                <tr>
                    <th>पिताको नाम:</th>
                    <td>{html.escape(father)}</td>
                    <th>जन्म समय:</th>
                    <td><b>{time_str}</b> (स्थानीय समय)</td>
                </tr>
                <tr>
                    <th>माताको नाम:</th>
                    <td>{html.escape(mother)}</td>
                    <th>जन्म स्थान:</th>
                    <td>{html.escape(birth_place)}</td>
                </tr>
                <tr>
                    <th>गोत्र:</th>
                    <td>{html.escape(gotra)}</td>
                    <th>सूर्योदय / सूर्यास्त:</th>
                    <td>सूर्योदय: {sunrise_time} | सूर्यास्त: {sunset_time}</td>
                </tr>
                <tr>
                    <th>संवत्सर:</th>
                    <td>{samvat_str} संवत्सर ({paksha_name})</td>
                    <th>तिथि / वार:</th>
                    <td><b>{tithi_name}</b> / <b>{vara_name}</b></td>
                </tr>
                <tr>
                    <th>नक्षत्र:</th>
                    <td><b>{nakshatra_name}</b> (चरण {to_ne_digits(pada_num)})</td>
                    <th>योग / करण:</th>
                    <td>योग: {yoga_name} | करण: {karana_name}</td>
                </tr>
            </table>

            <!-- अवकहडा चक्र तालिका -->
            <div class="section-header">॥ अवकहडा चक्र (जन्म तत्त्व) ॥</div>
            <table class="grid-table" style="text-align: center;">
                <tr style="background: #fdf6e7;">
                    <th>नामाक्षर</th>
                    <th>पाया</th>
                    <th>वर्ण</th>
                    <th>वश्य</th>
                    <th>तारा</th>
                    <th>योनि</th>
                    <th>गण</th>
                    <th>नाडी</th>
                    <th>चन्द्र राशि</th>
                </tr>
                <tr>
                    <td><b>{name_akshara}</b></td>
                    <td>{paya}</td>
                    <td>{varna}</td>
                    <td>{vashya}</td>
                    <td>{tara}</td>
                    <td>{yoni}</td>
                    <td>{gana}</td>
                    <td>{nadi}</td>
                    <td><b>{chandra_rashi}</b> ({rashi_lord})</td>
                </tr>
            </table>

            <!-- D1 & D9 Charts Side by Side -->
            <div class="section-header">॥ जन्म कुण्डली (D1) एवं नवमांश कुण्डली (D9) ॥</div>
            <table width="100%" style="border: none; text-align: center; margin-top: 6px;">
                <tr>
                    <td align="center" width="50%" style="border: none;">
                        <img src="{img_d1}" width="240" style="border: 2px solid #881337; border-radius: 4px;">
                        <div class="chart-caption">जन्म लग्न कुण्डली (D1) — {SIGN_NAMES_NE[lagna_sign]} लग्न</div>
                    </td>
                    <td align="center" width="50%" style="border: none;">
                        <img src="{img_d9}" width="240" style="border: 2px solid #881337; border-radius: 4px;">
                        <div class="chart-caption">नवमांश कुण्डली (D9) — {SIGN_NAMES_NE[d9_lagna]} लग्न</div>
                    </td>
                </tr>
            </table>

            <div class="footer-blessing">
                सदैव द्विजाशीर्वादैर्दीर्घमायुर्भूयात् ॥ (पृष्ठ १ / ४)
            </div>
        </div>
    </div>

    <!-- ==================== पृष्ठ २ : ग्रह स्थिति एवं भाव चक्र ==================== -->
    <div class="cheena-page">
        <div class="inner-border">
            <div class="header-section" style="margin-bottom: 4px;">
                <div class="patrika-title">॥ ग्रह स्थिति एवं भाव चक्र ॥</div>
            </div>

            <!-- ग्रह स्पष्ट तालिका -->
            <div class="section-header">॥ स्पष्ट ग्रह स्थिति तालिका (Planetary Longitudes) ॥</div>
            <table class="grid-table" style="text-align: center;">
                <tr style="background: #fdf6e7;">
                    <th>ग्रह</th>
                    <th>राशि</th>
                    <th>स्पष्ट भोगांश</th>
                    <th>नक्षत्र एवं चरण</th>
                    <th>भाव</th>
                    <th>अवस्था / गति</th>
                </tr>
                {"".join(planet_rows_html)}
            </table>

            <!-- चन्द्र कुण्डली एवं समुदाय अष्टकवर्ग -->
            <div class="section-header">॥ चन्द्र कुण्डली एवं समुदाय अष्टकवर्ग (SAV) ॥</div>
            <table width="100%" style="border: none; text-align: center; margin-top: 6px;">
                <tr>
                    <td align="center" width="50%" style="border: none;">
                        <img src="{img_chandra}" width="230" style="border: 2px solid #881337; border-radius: 4px;">
                        <div class="chart-caption">चन्द्र कुण्डली (Moon Chart) — {chandra_rashi} राशि</div>
                    </td>
                    <td align="center" width="50%" style="border: none;">
                        <img src="{img_sav}" width="230" style="border: 2px solid #881337; border-radius: 4px;">
                        <div class="chart-caption">समुदाय अष्टकवर्ग (SAV - ३३७ बिन्दु चक्र)</div>
                    </td>
                </tr>
            </table>

            <!-- अष्टकवर्ग बिन्दु तालिका -->
            <div class="section-header" style="margin-top: 10px;">॥ द्वादश भाव अष्टकवर्ग बिन्दु तालिका ॥</div>
            <table class="grid-table" style="text-align: center;">
                <tr style="background: #fdf6e7;">
                    {"".join(f"<th>{SIGN_NAMES_NE[i][:3]}</th>" for i in range(1, 13))}
                    <th>कुल</th>
                </tr>
                <tr>
                    {"".join(f"<td><b>{to_ne_digits(sav_scores[i-1])}</b></td>" for i in range(1, 13))}
                    <td style="font-weight: bold; color: #881337;">३३७</td>
                </tr>
            </table>

            <div class="footer-blessing">
                शुभम् भवतु कल्याणम् ॥ (पृष्ठ २ / ४)
            </div>
        </div>
    </div>

    <!-- ==================== पृष्ठ ३ : दशा चक्र विवरण ==================== -->
    <div class="cheena-page">
        <div class="inner-border">
            <div class="header-section" style="margin-bottom: 4px;">
                <div class="patrika-title">॥ त्रि-दशा चक्र विवरण ॥</div>
            </div>

            <!-- विंशोत्तरी महादशा -->
            <div class="section-header">१. विंशोत्तरी महादशा तालिका (१२० वर्ष चक्र)</div>
            <table class="grid-table" style="text-align: center;">
                <tr style="background: #fdf6e7;">
                    <th>महादशा स्वामी</th>
                    <th>अवधि</th>
                    <th>प्रारम्भ मिति</th>
                    <th>समाप्ति मिति</th>
                </tr>
                {"".join(vimshottari_rows_html)}
            </table>

            <!-- अष्टोत्तरी महादशा -->
            <div class="section-header" style="margin-top: 12px;">२. अष्टोत्तरी महादशा तालिका (१०८ वर्ष चक्र)</div>
            <table class="grid-table" style="text-align: center;">
                <tr style="background: #fdf6e7;">
                    <th>दशा स्वामी</th>
                    <th>अवधि</th>
                    <th>प्रारम्भ मिति</th>
                    <th>समाप्ति मिति</th>
                </tr>
                {"".join(ashtottari_rows_html)}
            </table>

            <!-- योगिनी महादशा -->
            <div class="section-header" style="margin-top: 12px;">३. योगिनी महादशा तालिका (३६ वर्ष चक्र)</div>
            <table class="grid-table" style="text-align: center;">
                <tr style="background: #fdf6e7;">
                    <th>योगिनी</th>
                    <th>अवधि</th>
                    <th>प्रारम्भ मिति</th>
                    <th>समाप्ति मिति</th>
                </tr>
                {"".join(yogini_rows_html)}
            </table>

            <div class="footer-blessing">
                दशाफलं ग्रहाधीनं तस्मात् सर्वं शुभं भवेत् ॥ (पृष्ठ ३ / ४)
            </div>
        </div>
    </div>

    <!-- ==================== पृष्ठ ४ : शुभ तत्त्व, रत्न तथा आशीर्वचन ==================== -->
    <div class="cheena-page">
        <div class="inner-border">
            <div class="header-section" style="margin-bottom: 4px;">
                <div class="patrika-title">॥ शुभ तत्त्व, रत्न-उपचार एवं आशीर्वचन ॥</div>
            </div>

            <!-- शुभ तत्त्व परामर्श -->
            <div class="section-header">॥ जीवनोपयोगी शुभ तत्त्वहरू (Auspicious Elements) ॥</div>
            <table class="grid-table">
                <tr>
                    <th width="25%">इष्ट देवता:</th>
                    <td width="75%"><b>भगवान् विष्णु / शिवजी तथा कुलदेवताको नित्य उपासना</b></td>
                </tr>
                <tr>
                    <th>अनुकूल भाग्य रत्न:</th>
                    <td><b>{life_stone}</b> (जीवन रक्षा एवं आरोग्य) | <b>{lucky_stone}</b> (भाग्य वृद्धि)</td>
                </tr>
                <tr>
                    <th>विद्या / सन्तान रत्न:</th>
                    <td><b>{punya_stone}</b> (ज्ञान, बुद्धि एवं सन्तान सुख)</td>
                </tr>
                <tr>
                    <th>अनुशंसित रुद्राक्ष:</th>
                    <td><b>{rec_rudraksha}</b> (शान्ति, एकाग्रता एवं दीर्घायु)</td>
                </tr>
                <tr>
                    <th>शुभ वार / दिशा:</th>
                    <td>वार: <b>{vara_name} एवं गुरुवार</b> | दिशा: <b>पूर्व एवं उत्तर दिशा</b></td>
                </tr>
                <tr>
                    <th>कल्याणकारी मन्त्र:</th>
                    <td><b>ॐ नमो भगवते वासुदेवाय</b> अथवा <b>ॐ नमः शिवाय</b> (नित्य १०८ पटक जप)</td>
                </tr>
            </table>

            <!-- शास्त्रीय मङ्गल आशीर्वचन -->
            <div class="section-header" style="margin-top: 14px;">॥ शास्त्रीय आशीर्वचन श्लोक ॥</div>
            <div style="text-align: center; padding: 14px; background: #fffbf0; border: 1px solid #d4af37; border-radius: 6px; margin: 10px 0;">
                <p style="font-size: 14px; color: #881337; font-weight: bold; line-height: 1.8; margin: 0;">
                    आयुर्द्रविणमारोग्यं पुत्रलाभो भवेत्सदा ।<br>
                    सर्वसम्पत्करं नित्यं भवतु तव मङ्गलम् ॥<br>
                    धर्मे मतिर्भवतु तावकमस्तु कीर्तिः ।<br>
                    सद्धर्ममार्गगमनं सुकृतं सदाऽस्तु ॥
                </p>
                <div style="margin-top: 8px; font-size: 12px; color: #b45309; font-weight: 600;">
                    ॥ सदैव द्विजाशीर्वादैर्दीर्घमायुर्भूयात् ॥
                </div>
            </div>

            <!-- कार्यालय एवं प्रमाणीकरण -->
            <div style="margin-top: 25px; border-top: 2px double #881337; padding-top: 12px;">
                <table width="100%" style="border: none; font-size: 12px;">
                    <tr>
                        <td width="55%" style="border: none; vertical-align: top;">
                            <b style="color: #881337; font-size: 13px;">शिवराम ज्योतिष अनुसन्धान केन्द्र</b><br>
                            कम्प्युटरकृत शास्त्रीय पराशरी कुण्डली विश्लेषण<br>
                            {html.escape(center_place)}
                        </td>
                        <td width="45%" style="border: none; text-align: center; vertical-align: top;">
                            <br><br>
                            ............................................................<br>
                            <b>ज्योतिषी प्रमाणीकरण / हस्ताक्षर</b><br>
                            <small style="color: #666;">(मुहर तथा आधिकारिक दस्तखत)</small>
                        </td>
                    </tr>
                </table>
            </div>

            <div class="footer-blessing" style="margin-top: 30px;">
                ॥ इति श्री परम्परागत नेपाली जन्मपत्रिका शुभा सम्पूर्णा ॥ (पृष्ठ ४ / ४)
            </div>
        </div>
    </div>

    </body>
    </html>
    """
    return html_content


class TraditionalCheenaA4Page(QWidget):
    """
    Native PySide6 Traditional Nepali Janmapatrika (चिना) A4 Document Widget.
    Provides full 4-page interactive viewing, one-click A4 PDF export, and direct printing.
    """

    def __init__(self, data: Optional[Dict[str, Any]], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data or {}
        self._language = language
        self._is_ne = language == "ne"
        self._zoom = 100
        self._current_html = ""
        self._build_ui()
        if self._data:
            self.refresh(self._data)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # Top Action Bar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        title = QLabel("📜 " + ("नेपाली परम्परागत जन्मपत्रिका (चिना) — A4" if self._is_ne else "Nepali Traditional Cheena (A4)"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 17px; font-weight: 700;")
        toolbar.addWidget(title)

        toolbar.addStretch(1)

        # Print Button
        print_btn = QPushButton("🖨️ " + ("A4 प्रिन्ट गर्नुहोस्" if self._is_ne else "Print Cheena"))
        print_btn.setStyleSheet(
            "QPushButton { background: #087329; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px; } "
            "QPushButton:hover { background: #065a20; }"
        )
        print_btn.clicked.connect(self._handle_print)
        toolbar.addWidget(print_btn)

        # PDF Export Button
        pdf_btn = QPushButton("📥 " + ("A4 PDF एक्सपोर्ट गर्नुहोस्" if self._is_ne else "Export A4 PDF"))
        pdf_btn.setStyleSheet(
            "QPushButton { background: #881337; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px; } "
            "QPushButton:hover { background: #70102e; }"
        )
        pdf_btn.clicked.connect(self._handle_export_pdf)
        toolbar.addWidget(pdf_btn)

        # Zoom buttons
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(zoom_out_btn)

        self._zoom_lbl = QLabel("100%")
        self._zoom_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: bold; min-width: 45px; text-align: center;")
        toolbar.addWidget(self._zoom_lbl)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(zoom_in_btn)

        main_layout.addLayout(toolbar)

        # Viewer Area
        if HAS_WEBENGINE:
            self._viewer = QWebEngineView()
            self._has_webengine = True
        else:
            self._viewer = QTextBrowser()
            self._viewer.setOpenExternalLinks(False)
            self._viewer.setStyleSheet(
                f"QTextBrowser {{ background-color: #e5e7eb; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 12px; }}"
            )
            self._has_webengine = False
        main_layout.addWidget(self._viewer, 1)

    def refresh(self, data: Dict[str, Any]):
        self._data = data or {}
        if not self._data:
            empty_msg = (
                f"<div style='text-align:center; padding: 40px; color:{COLOR_TEXT_MUTED}; font-size:16px; font-family:sans-serif;'>"
                + ("कुण्डली गणना गर्नुहोस्।" if self._is_ne else "Calculate a chart to view Janmapatrika.")
                + "</div>"
            )
            self._viewer.setHtml(empty_msg)
            return

        self._current_html = generate_traditional_cheena_html(self._data, self._language)
        self._viewer.setHtml(self._current_html)

    def _zoom_in(self):
        if self._zoom < 200:
            self._zoom += 15
            if getattr(self, "_has_webengine", False) and hasattr(self._viewer, "setZoomFactor"):
                self._viewer.setZoomFactor(self._zoom / 100.0)
            elif hasattr(self._viewer, "zoomIn"):
                self._viewer.zoomIn(1)
            self._zoom_lbl.setText(f"{self._zoom}%")

    def _zoom_out(self):
        if self._zoom > 50:
            self._zoom -= 15
            if getattr(self, "_has_webengine", False) and hasattr(self._viewer, "setZoomFactor"):
                self._viewer.setZoomFactor(self._zoom / 100.0)
            elif hasattr(self._viewer, "zoomOut"):
                self._viewer.zoomOut(1)
            self._zoom_lbl.setText(f"{self._zoom}%")

    def _get_document_stem(self) -> str:
        meta = self._data.get("metadata", {})
        name = meta.get("full_name") or meta.get("name") or "janmapatrika"
        clean = "".join(c for c in str(name) if c.isalnum() or c in (" ", "-", "_")).strip()
        return clean or "janmapatrika"

    def _handle_print(self):
        if not self._current_html:
            QMessageBox.warning(self, "सूचना", "पहिले कुण्डली गणना गर्नुहोस्।")
            return

        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            printer = QPrinter(QPrinter.HighResolution)
            printer.setDocName(f"Cheena_{self._get_document_stem()}")
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter)

            dlg = QPrintDialog(printer, self)
            if dlg.exec() != QPrintDialog.Accepted:
                return

            if getattr(self, "_has_webengine", False) and hasattr(self._viewer, "page") and HAS_FITZ:
                import tempfile
                temp_pdf = os.path.join(
                    tempfile.gettempdir(),
                    f"cheena_print_{os.getpid()}_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
                )
                layout = QPageLayout(
                    QPageSize(QPageSize.A4),
                    QPageLayout.Portrait,
                    QMarginsF(0, 0, 0, 0)
                )
                loop = QEventLoop()
                def on_temp_pdf_done(p, ok):
                    loop.quit()

                self._viewer.page().pdfPrintingFinished.connect(on_temp_pdf_done)
                self._viewer.page().printToPdf(temp_pdf, layout)
                loop.exec()
                try:
                    self._viewer.page().pdfPrintingFinished.disconnect(on_temp_pdf_done)
                except Exception:
                    pass

                pdf_doc = fitz.open(temp_pdf)
                painter = QPainter(printer)
                target_rect = printer.pageLayout().paintRectPixels(printer.resolution())
                for i, page in enumerate(pdf_doc):
                    if i > 0:
                        printer.newPage()
                    pix = page.get_pixmap(dpi=200)
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                    painter.drawImage(target_rect, img)
                painter.end()
                pdf_doc.close()
                try:
                    os.remove(temp_pdf)
                except Exception:
                    pass
            else:
                doc = QTextDocument()
                doc.setHtml(self._current_html)
                doc.print_(printer)

            QMessageBox.information(self, "सफलता", "नेपाली चिना सफलतापूर्वक प्रिन्ट पठाइयो।")
        except Exception as e:
            QMessageBox.critical(self, "प्रिन्ट त्रुटि", f"प्रिन्ट गर्न सकिएन:\n{e}")

    def _handle_export_pdf(self):
        if not self._current_html:
            QMessageBox.warning(self, "सूचना", "पहिले कुण्डली गणना गर्नुहोस्।")
            return

        default_name = f"Nepali_Cheena_{self._get_document_stem()}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "नेपाली परम्परागत चिना A4 PDF सेभ गर्नुहोस्" if self._is_ne else "Save Nepali Cheena A4 PDF",
            default_name,
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            if getattr(self, "_has_webengine", False) and hasattr(self._viewer, "page"):
                layout = QPageLayout(
                    QPageSize(QPageSize.A4),
                    QPageLayout.Portrait,
                    QMarginsF(0, 0, 0, 0)
                )
                loop = QEventLoop()
                err_flag = []
                def on_pdf_done(p, ok):
                    if not ok:
                        err_flag.append("Export failed")
                    loop.quit()

                self._viewer.page().pdfPrintingFinished.connect(on_pdf_done)
                self._viewer.page().printToPdf(file_path, layout)
                loop.exec()
                try:
                    self._viewer.page().pdfPrintingFinished.disconnect(on_pdf_done)
                except Exception:
                    pass

                if err_flag:
                    raise RuntimeError("Chromium PDF export did not complete successfully.")
            else:
                from PySide6.QtPrintSupport import QPrinter
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QPageSize(QPageSize.A4))
                printer.setPageOrientation(QPageLayout.Portrait)
                printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Millimeter)

                doc = QTextDocument()
                doc.setHtml(self._current_html)
                doc.print_(printer)

            QMessageBox.information(
                self,
                "सफलता" if self._is_ne else "Success",
                f"नेपाली परम्परागत चिना (A4 PDF) सफलतापूर्वक सेभ गरियो:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "PDF त्रुटि", f"PDF फाइल बनाउन सकिएन:\n{e}")

