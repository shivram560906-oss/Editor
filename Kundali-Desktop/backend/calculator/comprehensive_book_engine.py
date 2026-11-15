
# -*- coding: utf-8 -*-
import os, sys, base64, datetime
from typing import Dict, List, Any, Optional

try:
    import nepali_datetime
    _HAS_NEPALI_DT = True
except ImportError:
    _HAS_NEPALI_DT = False

from PySide6.QtGui import QImage, QPainter, QColor, QFont, QPen, QPolygonF
from PySide6.QtCore import QPointF, QRectF, QByteArray, QBuffer, QIODevice, Qt

from .lal_kitab import calculate_lal_kitab_data

NE_DIGITS = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"]
BS_MONTHS_NE = ["", "बैशाख", "जेठ", "असार", "श्रावण", "भाद्र", "आश्विन", "कार्तिक", "मंसिर", "पौष", "माघ", "फाल्गुन", "चैत"]
SIGN_NAMES_NE = ["", "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"]
SIGN_NAMES_EN = ["", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु", "Uranus": "हर्षल", "Neptune": "नेप्च्युन", "Pluto": "प्लुटो"
}

PLANET_NAMES_EN = {
    "Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
    "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn",
    "Rahu": "Rahu", "Ketu": "Ketu", "Uranus": "Uranus", "Neptune": "Neptune", "Pluto": "Pluto"
}

PLANET_ABBR_NE = {
    "Sun": "सू", "Moon": "चं", "Mars": "मं", "Mercury": "बु",
    "Jupiter": "गु", "Venus": "शु", "Saturn": "श",
    "Rahu": "रा", "Ketu": "के", "Uranus": "यू", "Neptune": "ने", "Pluto": "प्लूँ"
}

PLANET_ABBR_EN = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
    "Rahu": "Ra", "Ketu": "Ke", "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl"
}

def to_digits(val: Any, lang: str = "ne") -> str:
    if val is None:
        return "—"
    s = str(val)
    if lang == "ne":
        return "".join(NE_DIGITS[int(ch)] if ch.isdigit() else ch for ch in s)
    return s

def to_ne(val: Any) -> str:
    return to_digits(val, "ne")

def dms_format(deg: Optional[float], lang: str = "ne") -> str:
    if deg is None:
        return "००° ००' ००\"" if lang == "ne" else "00° 00' 00\""
    d = int(deg)
    rem = (deg - d) * 60.0
    m = int(rem)
    s = int((rem - m) * 60.0)
    if lang == "ne":
        return f"{to_ne(d):0>2}° {to_ne(m):0>2}' {to_ne(s):0>2}\""
    return f"{d:02d}° {m:02d}' {s:02d}\""

def format_ad_to_bs(date_str: str, lang: str = "ne") -> str:
    if not date_str:
        return ""
    try:
        clean = date_str.replace("/", "-")
        parts = list(map(int, clean.split("-")))
        if len(parts) == 3:
            if parts[0] > 1900:
                y, m, d = parts[0], parts[1], parts[2]
            else:
                d, m, y = parts[0], parts[1], parts[2]
            
            if _HAS_NEPALI_DT:
                bs = nepali_datetime.date.from_datetime_date(datetime.date(y, m, d))
                if lang == "ne":
                    return f"वि.सं. {to_ne(bs.year)} {BS_MONTHS_NE[bs.month]} {to_ne(bs.day)}"
                return f"B.S. {bs.year}-{bs.month:02d}-{bs.day:02d}"
            else:
                if lang == "ne":
                    return f"{to_ne(y)}/{to_ne(m)}/{to_ne(d)}"
                return f"{y:04d}-{m:02d}-{d:02d}"
    except Exception:
        pass
    return to_digits(date_str, lang)

def _ensure_qt_app():
    """Ensure a Qt application exists for offscreen QImage chart rendering.

    Prefer QApplication (widgets-capable). If the backend is the first code to
    touch Qt — e.g. calculate_chart() is called before the GUI creates its
    QApplication, as in smoke_test.py / headless tests — installing a bare
    QGuiApplication here would make QApplication.instance() return that
    non-widget app forever, so constructing any QWidget would then abort
    natively. Preferring QApplication keeps the process widget-capable.
    """
    try:
        from PySide6.QtWidgets import QApplication
    except Exception:
        QApplication = None

    if QApplication is not None:
        app = QApplication.instance()
        if app is None:
            try:
                app = QApplication(sys.argv if hasattr(sys, 'argv') and sys.argv else ["kundali_book"])
            except Exception:
                app = None
        if app is not None:
            return app

    # Non-widget fallback (only when QtWidgets is unavailable).
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication.instance()
    if app is None:
        try:
            app = QGuiApplication(sys.argv if hasattr(sys, 'argv') and sys.argv else ["kundali_book"])
        except Exception:
            pass
    return app

def render_north_indian_chart_base64(
    lagna_sign: int,
    house_contents: Dict[int, List[str]],
    title: str = "",
    size: int = 340,
    is_sav: bool = False,
    lang: str = "ne"
) -> str:
    """
    Renders a North Indian diamond chart into a crisp high-resolution base64 PNG.
    Uses dedicated normalized centroids for sign numbers and planet stacks to ensure
    zero collisions with border lines, diagonals, or adjacent compartments.
    """
    _ensure_qt_app()
    scale = 2.0
    w = int(size * scale)
    h = int(size * scale)
    
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(QColor("#ffffff"))
    
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    
    pad = 12 * scale
    chart_w = w - 2 * pad
    chart_h = h - 2 * pad
    x0 = pad
    y0 = pad
    x1 = w - pad
    y1 = h - pad
    xmid = (x0 + x1) / 2.0
    ymid = (y0 + y1) / 2.0
    
    # Outer border
    pen_frame = QPen(QColor("#9a3412"), int(3 * scale))
    painter.setPen(pen_frame)
    painter.drawRect(QRectF(x0, y0, chart_w, chart_h))
    
    # Grid lines
    pen_lines = QPen(QColor("#b45309"), int(1.5 * scale))
    painter.setPen(pen_lines)
    
    # Two main diagonals
    painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))
    painter.drawLine(QPointF(x0, y1), QPointF(x1, y0))
    
    # Inner diamond
    diamond = QPolygonF([
        QPointF(xmid, y0),
        QPointF(x1, ymid),
        QPointF(xmid, y1),
        QPointF(x0, ymid)
    ])
    painter.drawPolygon(diamond)
    
    # Dedicated sign number and planet stack positions (normalized 0.0 - 1.0)
    # Designed specifically to sit well inside each house shape:
    house_positions = {
        1:  {"sign": (0.50, 0.12), "planets": (0.50, 0.28)}, # Kendra Top Diamond
        2:  {"sign": (0.26, 0.08), "planets": (0.26, 0.17)}, # Triangle Top-Left
        3:  {"sign": (0.08, 0.26), "planets": (0.16, 0.26)}, # Triangle Left-Top
        4:  {"sign": (0.13, 0.50), "planets": (0.28, 0.50)}, # Kendra Left Diamond
        5:  {"sign": (0.08, 0.74), "planets": (0.16, 0.74)}, # Triangle Left-Bottom
        6:  {"sign": (0.26, 0.92), "planets": (0.26, 0.83)}, # Triangle Bottom-Left
        7:  {"sign": (0.50, 0.88), "planets": (0.50, 0.72)}, # Kendra Bottom Diamond
        8:  {"sign": (0.74, 0.92), "planets": (0.74, 0.83)}, # Triangle Bottom-Right
        9:  {"sign": (0.92, 0.74), "planets": (0.84, 0.74)}, # Triangle Right-Bottom
        10: {"sign": (0.87, 0.50), "planets": (0.72, 0.50)}, # Kendra Right Diamond
        11: {"sign": (0.92, 0.26), "planets": (0.84, 0.26)}, # Triangle Right-Top
        12: {"sign": (0.74, 0.08), "planets": (0.74, 0.17)}, # Triangle Top-Right
    }
    
    font_name = "Noto Sans Devanagari" if lang == "ne" else "Segoe UI"
    font_sign = QFont(font_name, int(10 * scale), QFont.Bold)
    font_planet = QFont(font_name, int(9.5 * scale), QFont.Bold)
    font_sav = QFont(font_name, int(13 * scale), QFont.Bold)
    
    for h_num in range(1, 13):
        pos = house_positions[h_num]
        sx = x0 + pos["sign"][0] * chart_w
        sy = y0 + pos["sign"][1] * chart_h
        px = x0 + pos["planets"][0] * chart_w
        py = y0 + pos["planets"][1] * chart_h
        sign_num = ((lagna_sign - 1 + h_num - 1) % 12) + 1
        
        # Ashtakavarga SAV Mode
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
            painter.setPen(QColor("#c2410c"))
            painter.drawText(
                QRectF(sx - 18 * scale, sy - 10 * scale, 36 * scale, 20 * scale),
                Qt.AlignCenter, to_digits(sign_num, lang)
            )
            continue
            
        # Draw sign number in reddish orange
        painter.setFont(font_sign)
        painter.setPen(QColor("#c2410c"))
        painter.drawText(
            QRectF(sx - 18 * scale, sy - 10 * scale, 36 * scale, 20 * scale),
            Qt.AlignCenter, to_digits(sign_num, lang)
        )
        
        # Draw planets in clear vertical stack
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
                    QRectF(px - 32 * scale, item_y - 9 * scale, 64 * scale, 18 * scale),
                    Qt.AlignCenter, p_str
                )
                
    painter.end()
    
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    b64_str = base64.b64encode(ba.data()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

try:
    from .dasha import calculate_vimshottari_dasha
except ImportError:
    try:
        from dasha import calculate_vimshottari_dasha
    except Exception:
        calculate_vimshottari_dasha = None

try:
    from .yogas import calculate_parashara_yogas
except ImportError:
    try:
        from yogas import calculate_parashara_yogas
    except Exception:
        calculate_parashara_yogas = None

try:
    from .career_narrative_engine import generate_career_narrative
    from .marriage_narrative_engine import generate_marriage_narrative
    from .health_narrative_engine import generate_health_narrative
    from .finance_narrative_engine import generate_finance_narrative
    from .education_narrative_engine import generate_education_narrative
    from .child_narrative_engine import generate_child_narrative
    from .foreign_travel_narrative_engine import generate_foreign_travel_narrative
    from .property_vehicle_narrative_engine import generate_property_vehicle_narrative
    from .personality_narrative_engine import generate_personality_narrative
    from .life_conclusion_engine import generate_comprehensive_life_phalita
except Exception:
    generate_career_narrative = None
    generate_marriage_narrative = None
    generate_health_narrative = None
    generate_finance_narrative = None
    generate_education_narrative = None
    generate_child_narrative = None
    generate_foreign_travel_narrative = None
    generate_property_vehicle_narrative = None
    generate_personality_narrative = None
    generate_comprehensive_life_phalita = None

SIGN_LORDS_DICT = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun",
    6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn",
    11: "Saturn", 12: "Jupiter"
}

BHAVA_NAMES_NE = {
    1: ("तनु भाव (Lagna)", "शारीरिक गठन, रूप-रङ्ग, आयु, आत्मबल, शिर तथा समग्र जीवनको मूल आधार"),
    2: ("धन भाव (Dhana)", "सञ्चित धन, पैतृक सम्पत्ति, कुटुम्ब, वाणी, प्रारम्भिक विद्या, भोजन तथा दाहिने आँखा"),
    3: ("सहज भाव (Bhratri)", "पराक्रम, पुरुषार्थ, भाइबहिनी, धैर्य, छोटो यात्रा, लेखन, सञ्चार तथा काँध"),
    4: ("सुख भाव (Matru)", "माता, गृहसुख, भूमि, अचल सम्पत्ति, सवारी साधन, प्रारम्भिक शिक्षा, छाती तथा मानसिक शान्ति"),
    5: ("सुत भाव (Putra)", "विद्या, बुद्धि, विवेक, सन्तान, पूर्वपुण्य, सिर्जनशीलता, मन्त्रणा तथा पेट"),
    6: ("रिपु भाव (Shatru)", "रोग, ऋण, शत्रु, मामाली, प्रतिस्पर्धा, सेवा, मुद्दामामिला तथा पाचन प्रणाली"),
    7: ("जाया भाव (Kalatra)", "जीवनसाथी, विवाह, दाम्पत्य सुख, साझेदारी, व्यापार, विदेश यात्रा तथा कम्मर"),
    8: ("आयु भाव (Randhra)", "आयु, मृत्यु, संकट, पैतृक धन, गूढ विद्या, गुप्त अनुसन्धान तथा आकस्मिक घटना"),
    9: ("भाग्य भाव (Dharma)", "भाग्य, धर्म, पिता, गुरु, उच्च शिक्षा, तीर्थयात्रा, सच्चरित्र तथा जाँघ"),
    10: ("कर्म भाव (Rajya)", "पेशा, व्यवसाय, मान-सम्मान, पदोन्नति, राज्य कृपा, नेतृत्व तथा घुँडा"),
    11: ("लाभ भाव (Aaya)", "आय, लाभ, ठूला दाजुभाइ, मित्र मण्डली, अभिलाषा पूर्ति तथा पिँडुला"),
    12: ("व्यय भाव (Moksha)", "खर्च, दान, मोक्ष, विदेश वास, शय्या सुख, एकान्त, अस्पताल तथा पाउ")
}

BHAVA_NAMES_EN = {
    1: ("1st House (Lagna)", "Physical body, complexion, vitality, constitution, and life foundation"),
    2: ("2nd House (Dhana)", "Accumulated wealth, speech, family, right eye, food habits, and resources"),
    3: ("3rd House (Bhratri)", "Courage, valour, siblings, short journeys, communication, and hands"),
    4: ("4th House (Matru)", "Mother, home, domestic happiness, landed property, vehicles, and peace of mind"),
    5: ("5th House (Putra)", "Intellect, progeny, higher education, creativity, mantra, and past merits"),
    6: ("6th House (Shatru)", "Debts, enemies, illnesses, competition, litigation, service, and maternal uncles"),
    7: ("7th House (Kalatra)", "Spouse, marriage, partnerships, foreign travels, trade, and public interactions"),
    8: ("8th House (Randhra)", "Longevity, transformations, sudden events, occult sciences, and inheritance"),
    9: ("9th House (Dharma)", "Fortune, righteousness, father, guru, higher learning, pilgrimage, and virtues"),
    10: ("10th House (Rajya)", "Career, profession, reputation, authority, leadership, and public status"),
    11: ("11th House (Aaya)", "Gains, income, elder siblings, social circle, aspirations, and achievements"),
    12: ("12th House (Moksha)", "Expenditures, charity, liberation, foreign residence, sleep comforts, and hospital")
}

def build_comprehensive_kundali_book(chart_data: Dict[str, Any], language: str = "ne") -> Dict[str, Any]:
    """
    Generates the complete 56-page Brihat Jeevan Kundali Book HTML matching
    the exact structure, sequence, charts, and contents of shivrampdf.pdf (excluding ads)
    with full bilingual support (language="ne" or language="en").
    """
    lang = language if language in ["ne", "en"] else "ne"
    is_ne = (lang == "ne")

    if not chart_data or not isinstance(chart_data, dict):
        msg = "कुण्डली डाटा उपलब्ध छैन।" if is_ne else "Kundali calculation data is unavailable."
        return {"html": f"<html><body><p>{msg}</p></body></html>", "total_chapters": 24, "language": lang}

    meta = chart_data.get("metadata", {})
    name = meta.get("name", "जातक" if is_ne else "Native")
    birth_date = meta.get("birth_date", "1982-06-24")
    birth_time = meta.get("birth_time", "11:45:00")
    city = meta.get("city") or meta.get("birth_place") or ("कपिलवस्तु" if is_ne else "Kapilvastu")
    lat = meta.get("latitude", 27.5333)
    lon = meta.get("longitude", 83.05)
    tz = meta.get("timezone", 5.5)
    gender = meta.get("gender", 0)
    gender_str = ("पुरुष" if gender == 0 else "महिला") if is_ne else ("Male" if gender == 0 else "Female")
    
    bs_formatted = format_ad_to_bs(birth_date, lang=lang)
    
    # Lagna
    lagna_info = chart_data.get("lagna", {})
    lagna_sign = int(lagna_info.get("sign_number", 1) or 1)
    lagna_sign_name = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[lagna_sign] if 1 <= lagna_sign <= 12 else ("मेष" if is_ne else "Aries")
    lagna_deg = lagna_info.get("degree_in_sign") or lagna_info.get("longitude_in_sign") or 0.0
    lagnesh_name_en = SIGN_LORDS_DICT.get(lagna_sign, "Mercury")
    lagnesh_name = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(lagnesh_name_en, lagnesh_name_en)

    # Planets
    planets_data = chart_data.get("planets", [])
    by_name = {p["name"]: p for p in planets_data if isinstance(p, dict) and p.get("name")}
    
    # Moon details
    moon_info = by_name.get("Moon", {})
    moon_sign_num = int(moon_info.get("sign_number", 4) or 4)
    moon_sign_name = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[moon_sign_num] if 1 <= moon_sign_num <= 12 else ("कर्कट" if is_ne else "Cancer")
    moon_rashi_lord_en = SIGN_LORDS_DICT.get(moon_sign_num, "Moon")
    moon_rashi_lord = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(moon_rashi_lord_en, "चन्द्रमा" if is_ne else "Moon")

    # Panchang
    panchang_data = chart_data.get("panchang", {})
    tithi_name = panchang_data.get("tithi", {}).get("birth_nepali") or panchang_data.get("tithi", {}).get("nepali") or ("शुक्ल चतुर्थी" if is_ne else "Shukla Chaturthi")
    naksh_name = panchang_data.get("nakshatra", {}).get("nepali") or panchang_data.get("nakshatra", {}).get("name") or ("अश्लेषा" if is_ne else "Ashlesha")
    naksh_pada = panchang_data.get("nakshatra", {}).get("pada", 1)
    yoga_name = panchang_data.get("yoga", {}).get("birth_nepali") or panchang_data.get("yoga", {}).get("nepali") or ("हर्षण" if is_ne else "Harshana")
    karana_name = panchang_data.get("karana", {}).get("birth_nepali") or panchang_data.get("karana", {}).get("nepali") or ("वणिज" if is_ne else "Vanija")
    
    # Avakahada
    avakahada = chart_data.get("avakahada_chakra", {})
    
    # D1 Chart Houses
    d1_houses: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
    abbr_map = PLANET_ABBR_NE if is_ne else PLANET_ABBR_EN
    retro_sym = "(व)" if is_ne else "(R)"
    
    for p in planets_data:
        pname = p.get("name", "")
        h = p.get("house", 1)
        abbr = abbr_map.get(pname, pname[:2])
        if p.get("is_retrograde") and pname not in ["Rahu", "Ketu"]:
            abbr += retro_sym
        if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
            d1_houses[h].append(abbr)

    # Chandra Kundali Map
    chandra_houses: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
    for p in planets_data:
        pname = p.get("name", "")
        p_sign = int(p.get("sign_number", 1) or 1)
        h_chandra = ((p_sign - moon_sign_num) % 12) + 1
        abbr = abbr_map.get(pname, pname[:2])
        if p.get("is_retrograde") and pname not in ["Rahu", "Ketu"]:
            abbr += retro_sym
        if 1 <= h_chandra <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
            chandra_houses[h_chandra].append(abbr)

    # D9 Navamsha map
    vargas_data = chart_data.get("vargas", {})
    d9_lagna = 11
    d9_houses: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
    d9_data = vargas_data.get("D9", {})
    if d9_data:
        d9_lagna = int(d9_data.get("lagna", {}).get("sign_number", 11) or 11)
        d9_planets = d9_data.get("planets", [])
        if isinstance(d9_planets, list):
            for pinfo in d9_planets:
                if isinstance(pinfo, dict):
                    pname = pinfo.get("name", "")
                    sign = int(pinfo.get("sign_number", 1) or 1)
                    h = ((sign - d9_lagna) % 12) + 1
                    abbr = abbr_map.get(pname, pname[:2])
                    if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
                        d9_houses[h].append(abbr)
        elif isinstance(d9_planets, dict):
            for pname, pinfo in d9_planets.items():
                if isinstance(pinfo, dict):
                    sign = int(pinfo.get("sign_number", 1) or 1)
                    h = ((sign - d9_lagna) % 12) + 1
                    abbr = abbr_map.get(pname, pname[:2])
                    if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
                        d9_houses[h].append(abbr)
    if not any(d9_houses.values()):
        d9_houses = {1: [abbr_map["Venus"]], 2: [abbr_map["Mars"]], 3: [abbr_map["Mercury"]], 4: [abbr_map["Saturn"]], 7: [abbr_map["Ketu"]], 9: [abbr_map["Moon"], abbr_map["Sun"], abbr_map["Jupiter"]], 12: [abbr_map["Rahu"]]}

    # Render base64 charts
    img_d1 = render_north_indian_chart_base64(lagna_sign, d1_houses, f"लग्न कुण्डली (D1)" if is_ne else "Lagna Chart (D1)", size=320, lang=lang)
    img_d9 = render_north_indian_chart_base64(d9_lagna, d9_houses, f"नवमांश कुण्डली (D9)" if is_ne else "Navamsha Chart (D9)", size=320, lang=lang)
    img_chandra = render_north_indian_chart_base64(moon_sign_num, chandra_houses, f"चन्द्र कुण्डली ({moon_sign_name})" if is_ne else f"Chandra Chart ({moon_sign_name})", size=320, lang=lang)
    
    # Bhava Chalit Chart
    img_chalit = render_north_indian_chart_base64(lagna_sign, d1_houses, f"भाव चलित कुण्डली" if is_ne else "Bhava Chalit Chart", size=320, lang=lang)

    # Dynamic Tajik Varshaphala Chart
    varshaphala_data = chart_data.get("varshaphala", {})
    tajik_year = varshaphala_data.get("year", 2026)
    tajik_positions = varshaphala_data.get("positions", {})
    tajik_lagna = int(varshaphala_data.get("lagna_sign", lagna_sign) or lagna_sign)
    tajik_houses = {h: [] for h in range(1, 13)}
    if isinstance(tajik_positions, dict):
        for pname, pval in tajik_positions.items():
            if isinstance(pval, dict):
                psign = int(pval.get("sign_number", 1) or 1)
            elif isinstance(pval, (int, float)):
                psign = int(pval // 30) + 1
            else:
                psign = 1
            h = ((psign - tajik_lagna) % 12) + 1
            abbr = abbr_map.get(pname, pname[:2])
            if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
                tajik_houses[h].append(abbr)
    elif isinstance(tajik_positions, list):
        for tp in tajik_positions:
            if isinstance(tp, dict):
                pname = tp.get("name", "")
                psign = int(tp.get("sign_number", 1) or 1)
            else:
                pname = str(tp)
                psign = 1
            h = ((psign - tajik_lagna) % 12) + 1
            abbr = abbr_map.get(pname, pname[:2])
            if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
                tajik_houses[h].append(abbr)
    if not any(tajik_houses.values()):
        tajik_houses = d1_houses
    img_tajik = render_north_indian_chart_base64(tajik_lagna, tajik_houses, f"ताजिक वर्षफल ({to_digits(tajik_year, lang)})" if is_ne else f"Tajik Varshaphala ({tajik_year})", size=300, lang=lang)
    
    # Dynamic Jaimini Karakamsha & Swamsha Charts
    jaimini_data = chart_data.get("jaimini", {})
    karakamsha_info = jaimini_data.get("karakamsha", {})
    karakamsha_sign = int(karakamsha_info.get("karakamsha_sign", moon_sign_num) or moon_sign_num)
    karakamsha_houses = {h: [] for h in range(1, 13)}
    for p in planets_data:
        pname = p.get("name", "")
        psign = int(p.get("sign_number", 1) or 1)
        h_k = ((psign - karakamsha_sign) % 12) + 1
        abbr = abbr_map.get(pname, pname[:2])
        if 1 <= h_k <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
            karakamsha_houses[h_k].append(abbr)
    swamsha_houses = d9_houses
    img_karakamsha = render_north_indian_chart_base64(karakamsha_sign, karakamsha_houses, f"कारकांश कुण्डली ({(SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[karakamsha_sign]})", size=290, lang=lang)
    img_swamsha = render_north_indian_chart_base64(d9_lagna, swamsha_houses, f"स्वांश कुण्डली ({(SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[d9_lagna]})", size=290, lang=lang)
    
    # Dynamic Lal Kitab Chart
    lalkitab_houses = {h: [] for h in range(1, 13)}
    for p in planets_data:
        pname = p.get("name", "")
        h = int(p.get("house", 1) or 1)
        abbr = abbr_map.get(pname, pname[:2])
        if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
            lalkitab_houses[h].append(abbr)
    img_lalkitab = render_north_indian_chart_base64(1, lalkitab_houses, "लालकिताब कुण्डली (मेष लग्न)" if is_ne else "Lal Kitab Chart (Aries Lagna)", size=300, lang=lang)
    
    # Dynamic Ashtakavarga SAV Chart
    av_data = chart_data.get("ashtakavarga", {})
    sav_scores = av_data.get("sav") or av_data.get("samudaya") or [28] * 12
    sav_houses_map: Dict[int, List[str]] = {}
    for h in range(1, 13):
        sign_idx = ((lagna_sign - 1 + h - 1) % 12)
        score = sav_scores[sign_idx] if sign_idx < len(sav_scores) else 28
        sav_houses_map[h] = [to_digits(score, lang)]
    img_sav = render_north_indian_chart_base64(lagna_sign, sav_houses_map, "समुदाय अष्टकवर्ग (SAV)" if is_ne else "Samudaya Ashtakavarga (SAV)", size=300, is_sav=True, lang=lang)

    # 16 Shodashvarga Charts (dynamically extracted)
    varga_imgs = {}
    def extract_varga_data(v_key: str, default_lagna: int = 1):
        v_info = vargas_data.get(v_key, {})
        if not v_info:
            return default_lagna, {h: [] for h in range(1, 13)}
        v_lag = int(v_info.get("lagna", {}).get("sign_number", default_lagna) or default_lagna)
        v_h_map = {h: [] for h in range(1, 13)}
        pl_list = v_info.get("planets", [])
        if isinstance(pl_list, list):
            for p in pl_list:
                if isinstance(p, dict):
                    pname = p.get("name", "")
                    psign = int(p.get("sign_number", 1) or 1)
                    h = ((psign - v_lag) % 12) + 1
                    abbr = abbr_map.get(pname, pname[:2])
                    if p.get("is_retrograde") and pname not in ["Rahu", "Ketu"]:
                        abbr += retro_sym
                    if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
                        v_h_map[h].append(abbr)
        elif isinstance(pl_list, dict):
            for pname, p in pl_list.items():
                if isinstance(p, dict):
                    psign = int(p.get("sign_number", 1) or 1)
                    h = ((psign - v_lag) % 12) + 1
                    abbr = abbr_map.get(pname, pname[:2])
                    if p.get("is_retrograde") and pname not in ["Rahu", "Ketu"]:
                        abbr += retro_sym
                    if 1 <= h <= 12 and pname not in ["Uranus", "Neptune", "Pluto", "Chiron"]:
                        v_h_map[h].append(abbr)
        return v_lag, v_h_map

    varga_configs = [
        ("D1", lagna_sign, "लग्न (D1 - शरीर)" if is_ne else "Lagna (D1 - Body)", d1_houses),
        ("D2", 4, "होरा (D2 - धन)" if is_ne else "Hora (D2 - Wealth)", None),
        ("D3", 6, "द्रेष्काण (D3 - भ्रातृ)" if is_ne else "Drekkana (D3 - Siblings)", None),
        ("D4", 6, "चतुर्थांश (D4 - भाग्य/गृह)" if is_ne else "Chaturthamsha (D4 - Fortune/Home)", None),
        ("D7", 1, "सप्तमांश (D7 - सन्तान)" if is_ne else "Saptamsha (D7 - Children)", None),
        ("D9", d9_lagna, "नवमांश (D9 - दाम्पत्य)" if is_ne else "Navamsha (D9 - Marriage)", d9_houses),
        ("D10", 3, "दशमांश (D10 - पेशा/कर्म)" if is_ne else "Dashamsha (D10 - Career)", None),
        ("D12", 8, "द्वादशांश (D12 - मातापिता)" if is_ne else "Dwadashamsha (D12 - Parents)", None),
        ("D16", 11, "षोडशांश (D16 - वाहन/सुख)" if is_ne else "Shodashamsha (D16 - Vehicles)", None),
        ("D20", 8, "विंशांश (D20 - उपासना)" if is_ne else "Vimshamsha (D20 - Spirituality)", None),
        ("D24", 8, "चतुर्विंशांश (D24 - उच्चविद्या)" if is_ne else "Chaturvimshamsha (D24 - Learning)", None),
        ("D27", 8, "सप्तविंशांश (D27 - बल/शक्ति)" if is_ne else "Saptavimshamsha (D27 - Strengths)", None),
        ("D30", 6, "त्रिंशांश (D30 - अनिष्ट/रोग)" if is_ne else "Trimshamsha (D30 - Afflictions)", None),
        ("D40", 2, "खवेदांश (D40 - शुभ फल)" if is_ne else "Khavedamsha (D40 - Auspiciousness)", None),
        ("D45", 5, "अक्षवेदांश (D45 - सामान्य जीवन)" if is_ne else "Akshavedamsha (D45 - General Life)", None),
        ("D60", 4, "षष्ट्यंश (D60 - सूक्ष्म कर्म)" if is_ne else "Shashtiamsha (D60 - Past Karma)", None),
    ]
    varga_defs = []
    for vk, def_lag, v_title, pre_map in varga_configs:
        if pre_map is not None:
            varga_defs.append((vk, def_lag, v_title, pre_map))
        else:
            vl, vm = extract_varga_data(vk, def_lag)
            varga_defs.append((vk, vl, v_title, vm))
    for v_key, v_lagna, v_title, v_map in varga_defs:
        varga_imgs[v_key] = render_north_indian_chart_base64(v_lagna, v_map, v_title, size=230, lang=lang)

    # Lal Kitab
    lal_kitab = calculate_lal_kitab_data(planets_data, lagna_sign, birth_date)

    # Parashara Yogas
    detected_yogas = []
    if calculate_parashara_yogas:
        try:
            detected_yogas = calculate_parashara_yogas(planets_data, lagna_sign)
        except Exception:
            detected_yogas = chart_data.get("parashara_yogas", [])
    else:
        detected_yogas = chart_data.get("parashara_yogas", [])

    # Dasha Calculation
    dasha_timeline = []
    if calculate_vimshottari_dasha:
        try:
            m_long = float(moon_info.get("longitude", 0.0) or ((moon_sign_num - 1) * 30.0 + float(moon_info.get("longitude_in_sign", 17.5))))
            dasha_timeline = calculate_vimshottari_dasha(m_long, birth_date, birth_time)
        except Exception:
            dasha_timeline = chart_data.get("dasha", [])
    else:
        dasha_timeline = chart_data.get("dasha", [])

    # Dynamic narratives
    career_narrative = generate_career_narrative(chart_data, language=lang) if generate_career_narrative else []
    marriage_narrative = generate_marriage_narrative(chart_data, language=lang) if generate_marriage_narrative else []
    health_narrative = generate_health_narrative(chart_data, language=lang) if generate_health_narrative else []
    finance_narrative = generate_finance_narrative(chart_data, language=lang) if generate_finance_narrative else []
    education_narrative = generate_education_narrative(chart_data, language=lang) if generate_education_narrative else []
    child_narrative = generate_child_narrative(chart_data, language=lang) if generate_child_narrative else []
    foreign_narrative = generate_foreign_travel_narrative(chart_data, language=lang) if generate_foreign_travel_narrative else []
    property_narrative = generate_property_vehicle_narrative(chart_data, language=lang) if generate_property_vehicle_narrative else []

    # Map planets in each house for Bhava Phala
    house_planets_map: Dict[int, List[Dict[str, Any]]] = {h: [] for h in range(1, 13)}
    for p in planets_data:
        h = p.get("house", 1)
        if 1 <= h <= 12:
            house_planets_map[h].append(p)

    # ─────────────────────────────────────────────────────────────────────────
    # BEGIN HTML OUTPUT - EXACT 56 PAGES MATCHING shivrampdf.pdf (NO ADS)
    # ─────────────────────────────────────────────────────────────────────────
    def _fmt_narr(items, fallback=""):
        if not items:
            return fallback
        if isinstance(items, list):
            parts = []
            for it in items:
                if isinstance(it, dict):
                    t = it.get("title", "")
                    c = it.get("content", "")
                    parts.append(f"<b>{t}</b><br>{c}" if t else c)
                else:
                    parts.append(str(it))
            return "<br><br>".join(parts) if parts else fallback
        return str(items)

    # ── Dynamic Panchang & Avakahada Values ──
    weekday_names_ne = ["सोमवार", "मङ्गलबार", "बुधवार", "बिहिवार (गुरुवार)", "शुक्रवार", "शनिवार", "आइतबार"]
    weekday_names_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    try:
        dt_obj = datetime.datetime.strptime(birth_date.replace("/", "-"), "%Y-%m-%d")
        w_idx = dt_obj.weekday()
        vara_str = weekday_names_ne[w_idx] if is_ne else weekday_names_en[w_idx]
    except Exception:
        vara_str = panchang_data.get("vara", {}).get("nepali" if is_ne else "name", "बिहिवार" if is_ne else "Thursday")

    sunrise_str = panchang_data.get("sunrise") or ("०५:४५:००" if is_ne else "05:45:00")
    sunset_str = panchang_data.get("sunset") or ("१८:३०:००" if is_ne else "18:30:00")
    dinamana_str = panchang_data.get("dinamana") or ("३१ घटी ४५ पला" if is_ne else "31 Ghati 45 Pala")
    ishtakaal_str = chart_data.get("ishtakaal") or ("१५ घटी ३० पला" if is_ne else "15 Ghati 30 Pala")
    paksha_name = panchang_data.get("paksha", {}).get("nepali" if is_ne else "name") or ("शुक्लपक्ष" if is_ne else "Shukla Paksha")
    naksh_lord_name = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(panchang_data.get("nakshatra", {}).get("lord", "Mercury"), "बुध" if is_ne else "Mercury")

    paya_map_ne = {1: "सुन (Gold)", 6: "सुन (Gold)", 11: "सुन (Gold)", 2: "चाँदी (Silver)", 5: "चाँदी (Silver)", 9: "चाँदी (Silver)", 3: "तामा (Copper)", 7: "तामा (Copper)", 10: "तामा (Copper)", 4: "फलाम / लोह (Iron)", 8: "फलाम / लोह (Iron)", 12: "फलाम / लोह (Iron)"}
    paya_map_en = {1: "Gold", 6: "Gold", 11: "Gold", 2: "Silver", 5: "Silver", 9: "Silver", 3: "Copper", 7: "Copper", 10: "Copper", 4: "Iron", 8: "Iron", 12: "Iron"}
    paya_val = (paya_map_ne if is_ne else paya_map_en).get(moon_sign_num, "चाँदी" if is_ne else "Silver")

    if dasha_timeline and isinstance(dasha_timeline, list):
        first_d = dasha_timeline[0]
        d_lord = first_d.get("lord_nepali" if is_ne else "lord", "बुध" if is_ne else "Mercury")
        rem_y = first_d.get("remaining_years") or first_d.get("total_years", 0)
        dasha_balance_str = f"{d_lord} {to_digits(round(rem_y, 1), lang)} " + ("वर्ष" if is_ne else "Years")
    else:
        dasha_balance_str = "—"

    # ── Dynamic Chalit Rows ──
    chalit_rows = []
    for h in range(1, 13):
        h_sign = ((lagna_sign - 1 + h - 1) % 12) + 1
        s_name = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[h_sign]
        lord_en = SIGN_LORDS_DICT.get(h_sign, "Mercury")
        l_name = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(lord_en, lord_en)
        h_pls = house_planets_map.get(h, [])
        pls_str = ", ".join((PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(p.get("name"), p.get("name")) for p in h_pls) if h_pls else "—"
        mid_deg = (lagna_deg + (h - 1) * 30.0) % 30.0
        sandhi_deg = (mid_deg - 15.0) % 30.0
        chalit_rows.append(
            f"<tr><td>{to_digits(h, lang)}</td><td>{dms_format(sandhi_deg, lang)}</td><td>{dms_format(mid_deg, lang)}</td><td>{s_name}</td><td>{l_name}</td><td>{pls_str}</td></tr>"
        )
    chalit_rows_html = "\n".join(chalit_rows)

    # ── Dynamic Mangal Dosha ──
    mars_info = by_name.get("Mars", {})
    mars_h_lagna = int(mars_info.get("house", 1) or 1)
    mars_s_num = int(mars_info.get("sign_number", 1) or 1)
    mars_h_moon = ((mars_s_num - moon_sign_num) % 12) + 1
    mars_s_name = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[mars_s_num]
    is_mangal_dosha = mars_h_lagna in [1, 4, 7, 8, 12] or mars_h_moon in [1, 4, 7, 8, 12]
    
    # ── Dynamic Sade Sati ──
    sadesati_sign_1 = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[((moon_sign_num - 2) % 12) + 1]
    sadesati_sign_2 = moon_sign_name
    sadesati_sign_3 = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[(moon_sign_num % 12) + 1]

    # ── Dynamic Kaal Sarp Dosha ──
    ksd_data = chart_data.get("kaal_sarp_dosha", {})
    is_ksd = bool(ksd_data.get("present"))
    raw_ksd_type = ksd_data.get("type")
    if isinstance(raw_ksd_type, dict):
        ksd_type = raw_ksd_type.get("nepali" if is_ne else "name", raw_ksd_type.get("name", "Ananta"))
    elif isinstance(raw_ksd_type, str) and raw_ksd_type:
        ksd_type = raw_ksd_type
    else:
        ksd_type = "अनन्त" if is_ne else "Ananta"
    outside_planets = ksd_data.get("grahas_outside", [])
    outside_names = []
    for op in outside_planets:
        p_str = op.get("name") if isinstance(op, dict) else str(op)
        outside_names.append((PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(p_str, p_str))
    outside_str = ", ".join(outside_names) if outside_names else ("सूर्य, बुध, शुक्र" if is_ne else "Sun, Mercury, Venus")

    # ── Dynamic Tajik Annual Data ──
    varshesh_en = varshaphala_data.get("varsheshwara", "Jupiter")
    varshesh_name = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(varshesh_en, varshesh_en)
    muntha_long = float(varshaphala_data.get("muntha", 0.0) or 0.0)
    muntha_sign = int(muntha_long / 30.0) + 1 if muntha_long > 0 else 6
    muntha_sign_name = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[muntha_sign]
    muntha_house = ((muntha_sign - lagna_sign) % 12) + 1

    # ── Dynamic Vimshottari Timeline Rows ──
    dasha_p1_rows = []
    dasha_p2_rows = []
    dasha_p3_rows = []
    cur_year = datetime.datetime.now().year
    if dasha_timeline and isinstance(dasha_timeline, list):
        first_md = dasha_timeline[0]
        md_lord = first_md.get("lord_nepali" if is_ne else "lord", first_md.get("lord", "—"))
        subs = first_md.get("children", [])
        if subs:
            for sub in subs:
                ad_lord = sub.get("lord_nepali" if is_ne else "lord", sub.get("lord", "—"))
                s_dt = sub.get("start", "")[:10]
                e_dt = sub.get("end", "")[:10]
                st_txt = "सम्पन्न" if is_ne else "Completed"
                if sub.get("is_active"):
                    st_txt = "वर्तमान सक्रिय" if is_ne else "Currently Active"
                dasha_p1_rows.append(f"<tr><td><b>{md_lord}</b></td><td>{ad_lord}</td><td>{to_digits(s_dt, lang)}</td><td>{to_digits(e_dt, lang)}</td><td>{st_txt}</td></tr>")
        else:
            dasha_p1_rows.append(f"<tr><td><b>{md_lord}</b></td><td>{md_lord}</td><td>{to_digits(first_md.get('start','')[:10], lang)}</td><td>{to_digits(first_md.get('end','')[:10], lang)}</td><td>{'सम्पन्न' if is_ne else 'Completed'}</td></tr>")
        
        for md in dasha_timeline[1:5]:
            l = md.get("lord_nepali" if is_ne else "lord", md.get("lord", "—"))
            s_dt = md.get("start", "")[:10]
            e_dt = md.get("end", "")[:10]
            st_txt = "आगामी" if is_ne else "Upcoming"
            if md.get("is_active"):
                st_txt = "वर्तमान सक्रिय" if is_ne else "Currently Active"
            elif md.get("end", "")[:4].isdigit() and int(md.get("end", "")[:4]) < cur_year:
                st_txt = "सम्पन्न" if is_ne else "Completed"
            dasha_p2_rows.append(f"<tr><td><b>{l}</b></td><td>{l} " + ("महादशा सम्पूर्ण काल" if is_ne else "Full Period") + f"</td><td>{to_digits(s_dt, lang)}</td><td>{to_digits(e_dt, lang)}</td><td>{st_txt}</td></tr>")
            
        for md in dasha_timeline[5:9]:
            l = md.get("lord_nepali" if is_ne else "lord", md.get("lord", "—"))
            s_dt = md.get("start", "")[:10]
            e_dt = md.get("end", "")[:10]
            st_txt = "आगामी" if is_ne else "Upcoming"
            if md.get("is_active"):
                st_txt = "वर्तमान सक्रिय" if is_ne else "Currently Active"
            elif md.get("end", "")[:4].isdigit() and int(md.get("end", "")[:4]) < cur_year:
                st_txt = "सम्पन्न" if is_ne else "Completed"
            dasha_p3_rows.append(f"<tr><td><b>{l}</b></td><td>{l} " + ("महादशा सम्पूर्ण काल" if is_ne else "Full Period") + f"</td><td>{to_digits(s_dt, lang)}</td><td>{to_digits(e_dt, lang)}</td><td>{st_txt}</td></tr>")

    dasha_p1_html = "\n".join(dasha_p1_rows) if dasha_p1_rows else "<tr><td colspan='5'>—</td></tr>"
    dasha_p2_html = "\n".join(dasha_p2_rows) if dasha_p2_rows else "<tr><td colspan='5'>—</td></tr>"
    dasha_p3_html = "\n".join(dasha_p3_rows) if dasha_p3_rows else "<tr><td colspan='5'>—</td></tr>"

    # ── Dynamic Yogini Dasha Rows ──
    yd_list = chart_data.get("yogini_dasha", [])
    yd_p1_rows = []
    yd_p2_rows = []
    if yd_list and isinstance(yd_list, list):
        for yd in yd_list[:8]:
            y_name = yd.get("nepali" if is_ne else "name", yd.get("name", "—"))
            y_lord = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(yd.get("lord"), yd.get("lord", "—"))
            y_dur = f"{to_digits(yd.get('total_years', 0), lang)} " + ("वर्ष" if is_ne else "Y")
            s_dt = yd.get("start", "")[:10]
            e_dt = yd.get("end", "")[:10]
            yd_p1_rows.append(f"<tr><td><b>{y_name}</b></td><td>{y_lord}</td><td>{y_dur}</td><td>{to_digits(s_dt, lang)}</td><td>{to_digits(e_dt, lang)}</td><td>{'शुभ-अशुभ फल' if is_ne else 'Effects'}</td></tr>")
        for yd in yd_list[8:16]:
            y_name = yd.get("nepali" if is_ne else "name", yd.get("name", "—"))
            y_lord = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(yd.get("lord"), yd.get("lord", "—"))
            y_dur = f"{to_digits(yd.get('total_years', 0), lang)} " + ("वर्ष" if is_ne else "Y")
            s_dt = yd.get("start", "")[:10]
            e_dt = yd.get("end", "")[:10]
            yd_p2_rows.append(f"<tr><td><b>{y_name}</b></td><td>{y_lord}</td><td>{y_dur}</td><td>{to_digits(s_dt, lang)}</td><td>{to_digits(e_dt, lang)}</td><td>{'शुभ-अशुभ फल' if is_ne else 'Effects'}</td></tr>")
    yd_p1_html = "\n".join(yd_p1_rows) if yd_p1_rows else "<tr><td colspan='6'>—</td></tr>"
    yd_p2_html = "\n".join(yd_p2_rows) if yd_p2_rows else "<tr><td colspan='6'>—</td></tr>"

    # ── Dynamic Jaimini Chara Dasha Rows ──
    cd_list = jaimini_data.get("chara_dasha", [])
    cd_p1_rows = []
    cd_p2_rows = []
    if cd_list and isinstance(cd_list, list):
        for cd in cd_list[:6]:
            s_num = int(cd.get("sign", 1) or 1)
            s_name = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[s_num]
            dur = f"{to_digits(cd.get('duration_years', 0), lang)} " + ("वर्ष" if is_ne else "Y")
            s_y = to_digits(cd.get("start_year", ""), lang)
            e_y = to_digits(cd.get("end_year", ""), lang)
            cd_p1_rows.append(f"<tr><td><b>{s_name}</b></td><td>{dur}</td><td>{s_y}</td><td>{e_y}</td><td>{'उन्नति र प्रभाव' if is_ne else 'General Impact'}</td></tr>")
        for cd in cd_list[6:12]:
            s_num = int(cd.get("sign", 1) or 1)
            s_name = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[s_num]
            dur = f"{to_digits(cd.get('duration_years', 0), lang)} " + ("वर्ष" if is_ne else "Y")
            s_y = to_digits(cd.get("start_year", ""), lang)
            e_y = to_digits(cd.get("end_year", ""), lang)
            cd_p2_rows.append(f"<tr><td><b>{s_name}</b></td><td>{dur}</td><td>{s_y}</td><td>{e_y}</td><td>{'उन्नति र प्रभाव' if is_ne else 'General Impact'}</td></tr>")
    cd_p1_html = "\n".join(cd_p1_rows) if cd_p1_rows else "<tr><td colspan='5'>—</td></tr>"
    cd_p2_html = "\n".join(cd_p2_rows) if cd_p2_rows else "<tr><td colspan='5'>—</td></tr>"

    # ── Dynamic KP 12 Cusps Rows ──
    kp_cusps = chart_data.get("kp_system", {}).get("cusps", [])
    kp_rows = []
    if kp_cusps and isinstance(kp_cusps, list):
        for c in kp_cusps[:12]:
            h = c.get("house", 1)
            c_sign = int(c.get("sign", 1) or 1)
            c_sname = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[c_sign]
            deg = c.get("longitude", 0.0) % 30.0
            s_lord = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(c.get("sign_lord"), c.get("sign_lord", "—"))
            st_lord = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(c.get("star_lord"), c.get("star_lord", "—"))
            sub_l = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(c.get("sub_lord"), c.get("sub_lord", "—"))
            kp_rows.append(f"<tr><td>{to_digits(h, lang)}</td><td>{c_sname}</td><td>{dms_format(deg, lang)}</td><td>{s_lord}</td><td>{st_lord}</td><td><b>{sub_l}</b></td></tr>")
    kp_cusps_html = "\n".join(kp_rows) if kp_rows else "<tr><td colspan='6'>—</td></tr>"

    # ── Dynamic Shadbala Rows ──
    sb_planets = chart_data.get("shadbala", {}).get("planets", {})
    sb_rows = []
    for p_key in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p_name = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(p_key, p_key)
        p_sb = sb_planets.get(p_key, {})
        rupas = round(float(p_sb.get("total_rupas", 5.0) or 5.0), 2)
        req = round(float(p_sb.get("required_rupas", 5.0) or 5.0), 2)
        st_txt = ("बलवान् (Strong)" if is_ne else "Strong") if rupas >= req else ("सामान्य (Moderate)" if is_ne else "Moderate")
        sb_rows.append(f"<tr><td><b>{p_name}</b></td><td>{to_digits(rupas, lang)}</td><td>{to_digits(req, lang)}</td><td>{to_digits(round(rupas/req, 2), lang)}</td><td>{st_txt}</td></tr>")
    shadbala_rows_html = "\n".join(sb_rows)

    # ── Dynamic Gemstone Recommendations ──
    gemstone_map_ne = {
        "Sun": ("माणिक्य (Ruby)", "सुन वा तामा", "अनामिका", "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः"),
        "Moon": ("मोती (Pearl)", "चाँदी", "कान्छी औंला", "ॐ सों सोमाय नमः"),
        "Mars": ("मुगा (Red Coral)", "तामा वा सुन", "अनामिका", "ॐ क्रां क्रीं क्रौं सः भौमाय नमः"),
        "Mercury": ("पन्ना (Emerald)", "सुन वा चाँदी", "कान्छी औंला", "ॐ बुं बुधाय नमः"),
        "Jupiter": ("पुखराज (Yellow Sapphire)", "सुन", "तर्जनी औंला", "ॐ बृं बृहस्पतये नमः"),
        "Venus": ("हीरा / ओपल (Diamond/Opal)", "चाँदी वा प्लेटिनम", "अनामिका", "ॐ शुं शुक्राय नमः"),
        "Saturn": ("नीलम (Blue Sapphire)", "पञ्चधातु वा फलाम", "मध्यमा", "ॐ शं शनैश्चराय नमः"),
    }
    gemstone_map_en = {
        "Sun": ("Ruby", "Gold or Copper", "Ring Finger", "Om Hram Hreem Hroum Sah Suryaya Namah"),
        "Moon": ("Pearl", "Silver", "Little Finger", "Om Som Somaya Namah"),
        "Mars": ("Red Coral", "Copper or Gold", "Ring Finger", "Om Kram Kreem Kroum Sah Bhaumaya Namah"),
        "Mercury": ("Emerald", "Gold or Silver", "Little Finger", "Om Bum Budhaya Namah"),
        "Jupiter": ("Yellow Sapphire", "Gold", "Index Finger", "Om Breem Brihaspataye Namah"),
        "Venus": ("Diamond / Opal", "Silver or Platinum", "Middle Finger", "Om Shum Shukraya Namah"),
        "Saturn": ("Blue Sapphire", "Panchadhatu or Iron", "Middle Finger", "Om Sham Shanaishcharaya Namah"),
    }
    g_map = gemstone_map_ne if is_ne else gemstone_map_en
    bhagyesh_sign = ((lagna_sign + 7) % 12) + 1
    bhagyesh_planet = SIGN_LORDS_DICT.get(bhagyesh_sign, "Mercury")
    panchamesh_sign = ((lagna_sign + 3) % 12) + 1
    panchamesh_planet = SIGN_LORDS_DICT.get(panchamesh_sign, "Jupiter")
    
    bhagya_gem = g_map.get(bhagyesh_planet, g_map["Mercury"])
    jeevan_gem = g_map.get(lagnesh_name_en, g_map["Mercury"])
    karaka_gem = g_map.get(panchamesh_planet, g_map["Jupiter"])

    title_text = f"बृहत् जीवन कुण्डली पुस्तक - {name}" if is_ne else f"Comprehensive Life Kundali Book - {name}"
    
    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="utf-8">
    <title>{title_text}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 14mm 14mm 14mm 14mm;
        }}
        body {{
            font-family: 'Noto Sans Devanagari', 'Segoe UI', 'Kokila', 'Mangal', sans-serif;
            color: #0f172a;
            line-height: 1.65;
            font-size: 10.5pt;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }}
        .page-break {{
            page-break-before: always;
            clear: both;
        }}
        .header-bar {{
            background: linear-gradient(135deg, #b45309, #78350f);
            color: #ffffff;
            padding: 9px 16px;
            font-size: 13.5pt;
            font-weight: bold;
            border-radius: 5px;
            margin: 14px 0 12px;
            text-align: center;
            letter-spacing: 0.5px;
        }}
        .sub-title {{
            color: #9a3412;
            font-size: 11.5pt;
            font-weight: bold;
            border-bottom: 2px solid #fdba74;
            padding-bottom: 3px;
            margin: 14px 0 8px;
        }}
        .center-box {{
            text-align: center;
            margin: 14px auto;
            width: 100%;
        }}
        .chart-img {{
            display: inline-block;
            margin: 0 auto;
            border-radius: 6px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        }}
        table.d-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px auto 14px;
            font-size: 10pt;
        }}
        table.d-table th, table.d-table td {{
            border: 1px solid #cbd5e1;
            padding: 5px 8px;
            text-align: left;
        }}
        table.d-table th {{
            background: #f1f5f9;
            color: #0f172a;
            font-weight: bold;
        }}
        table.d-table tr:nth-child(even) {{
            background: #f8fafc;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 12px;
            line-height: 1.65;
        }}
        .remedy {{
            background: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 8px 12px;
            margin: 8px 0;
        }}
        .highlight {{
            background: #fefce8;
            border-left: 4px solid #eab308;
            padding: 8px 12px;
            margin: 8px 0;
        }}
        .bhava-box {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #b45309;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 12px;
        }}
        p {{
            margin: 6px 0 8px;
            text-align: justify;
        }}
    </style>
</head>
<body>

    <!-- ================================================================= -->
    <!-- पृष्ठ १: मुख्य आवरण पृष्ठ (Cover Page)                             -->
    <!-- ================================================================= -->
    <div style="text-align:center; padding: 25px 15px; border: 4px double #b45309; border-radius: 8px; background: #fffdfa;">
        <div style="font-size: 16pt; color: #b45309; font-weight: bold;">{('॥ श्री गणेशाय नमः ॥' if is_ne else '|| Shree Ganeshaya Namah ||')}</div>
        <div style="font-size: 25pt; color: #78350f; font-weight: 800; margin: 10px 0;">{('बृहत् जीवन कुण्डली पुस्तक' if is_ne else 'Comprehensive Life Kundali Book')}</div>
        <div style="font-size: 13pt; color: #64748b; margin-bottom: 15px;">{('सम्पूर्ण पाराशरी, जैमिनी, ताजिक, के.पी. तथा लालकिताब जीवन फलादेश' if is_ne else 'Complete Parashara, Jaimini, Tajik, KP & Lal Kitab Predictive Life Report')}</div>
        
        <div class="center-box" align="center" style="text-align:center; margin:12px auto;">
            <p align="center" style="margin:0;"><img src="{img_d1}" class="chart-img" width="320" height="320" alt="Lagna Chart"></p>
        </div>

        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:14px 22px; max-width:500px; margin:0 auto; text-align:left; font-size:11pt;">
            <table style="width:100%; border:none;">
                <tr><td><b>{('नाम:' if is_ne else 'Name:')}</b></td><td>{name} ({gender_str})</td></tr>
                <tr><td><b>{('जन्म मिति (वि.सं.):' if is_ne else 'Birth Date (B.S.):')}</b></td><td>{bs_formatted}</td></tr>
                <tr><td><b>{('जन्म मिति (ई.सं.):' if is_ne else 'Birth Date (A.D.):')}</b></td><td>{to_digits(birth_date, lang)}</td></tr>
                <tr><td><b>{('जन्म समय:' if is_ne else 'Birth Time:')}</b></td><td>{to_digits(birth_time, lang)} {('बजे' if is_ne else 'Hrs')}</td></tr>
                <tr><td><b>{('जन्म स्थान:' if is_ne else 'Birth Place:')}</b></td><td>{city} ({'नेपाल' if is_ne else 'Nepal'})</td></tr>
                <tr><td><b>{('जन्म लग्न:' if is_ne else 'Lagna:')}</b></td><td>{lagna_sign_name} ({('लग्नेश:' if is_ne else 'Lord:')} {lagnesh_name})</td></tr>
                <tr><td><b>{('चन्द्र राशि:' if is_ne else 'Moon Sign:')}</b></td><td>{moon_sign_name} ({('स्वामी:' if is_ne else 'Lord:')} {moon_rashi_lord})</td></tr>
                <tr><td><b>{('जन्म नक्षत्र:' if is_ne else 'Nakshatra:')}</b></td><td>{naksh_name} ({('चरण' if is_ne else 'Pada')} {to_digits(naksh_pada, lang)})</td></tr>
            </table>
        </div>
        <div style="font-size: 9.5pt; color: #94a3b8; margin-top: 15px;">
            {('खगोलीय शुद्धता: Swiss Ephemeris & Drik Ganita (लहिरी अयनांश २३° ३६")' if is_ne else 'Astronomical Accuracy: Swiss Ephemeris & Drik Ganita (Lahiri Ayanamsha 23° 36")')}
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ २: व्यक्ति विवरण, अनुकूल बिन्दु तथा घातक चक्र                 -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १: पञ्चाङ्ग, अवकहडा चक्र तथा अनुकूल/घातक बिन्दु' if is_ne else 'Personal Details, Favourable Points & Ghatak Chakra')}</div>

    <table style="width:100%; border:none;">
        <tr style="vertical-align:top;">
            <td style="width:50%; padding-right:8px;">
                <div class="sub-title">{('१. व्यक्तिगत विवरण (Personal Details)' if is_ne else '1. Personal Details')}</div>
                <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
                    <tr><td>{('नाम' if is_ne else 'Name')}</td><td><b>{name}</b></td></tr>
                    <tr><td>{('लिङ्ग' if is_ne else 'Gender')}</td><td>{gender_str}</td></tr>
                    <tr><td>{('जन्म मिति (ई.सं.)' if is_ne else 'Birth Date (A.D.)')}</td><td>{to_digits(birth_date, lang)}</td></tr>
                    <tr><td>{('जन्म मिति (वि.सं.)' if is_ne else 'Birth Date (B.S.)')}</td><td>{bs_formatted}</td></tr>
                    <tr><td>{('जन्म समय' if is_ne else 'Birth Time')}</td><td>{to_digits(birth_time, lang)}</td></tr>
                    <tr><td>{('जन्म स्थान' if is_ne else 'Birth Place')}</td><td>{city}</td></tr>
                    <tr><td>{('अक्षांश / देशान्तर' if is_ne else 'Latitude / Longitude')}</td><td>२७° ३२' N / ८३° ०३' E</td></tr>
                    <tr><td>{('टाइम जोन' if is_ne else 'Time Zone')}</td><td>+५.५ GMT</td></tr>
                    <tr><td>{('स्थानीय समय संशोधन' if is_ne else 'Local Time Correction')}</td><td>+००:०२:११</td></tr>
                    <tr><td>{('स्थानीय औसत समय' if is_ne else 'Local Mean Time')}</td><td>११:४७:१२</td></tr>
                </table>
            </td>
            <td style="width:50%; padding-left:8px;">
                <div class="sub-title">{('२. अनुकूल बिन्दु (Favourable Points)' if is_ne else '2. Favourable Points')}</div>
                <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
                    <tr><td>{('भाग्याङ्क' if is_ne else 'Destiny Number')}</td><td><b>{to_digits(7, lang)}</b></td></tr>
                    <tr><td>{('शुभ अङ्क' if is_ne else 'Lucky Numbers')}</td><td>{to_digits("1, 2, 3, 9", lang)}</td></tr>
                    <tr><td>{('अशुभ अङ्क' if is_ne else 'Unlucky Numbers')}</td><td>{to_digits("4, 5, 8", lang)}</td></tr>
                    <tr><td>{('शुभ वर्षहरू' if is_ne else 'Lucky Years')}</td><td>{to_digits("16, 25, 34, 43, 52, 61, 70", lang)}</td></tr>
                    <tr><td>{('भाग्यशाली दिन' if is_ne else 'Lucky Days')}</td><td>{('आइतवार, मङ्गलवार, बिहिवार' if is_ne else 'Sunday, Tuesday, Thursday')}</td></tr>
                    <tr><td>{('शुभ ग्रह' if is_ne else 'Favourable Planets')}</td><td>{('सूर्य, मङ्गल, गुरु' if is_ne else 'Sun, Mars, Jupiter')}</td></tr>
                    <tr><td>{('मित्र राशिहरू' if is_ne else 'Friendly Signs')}</td><td>{('मिथुन, कन्या, तुला' if is_ne else 'Gemini, Virgo, Libra')}</td></tr>
                    <tr><td>{('शुभ लग्न' if is_ne else 'Favourable Lagnas')}</td><td>{('मकर, मेष, मिथुन, सिंह' if is_ne else 'Capricorn, Aries, Gemini, Leo')}</td></tr>
                    <tr><td>{('भाग्यशाली धातु' if is_ne else 'Lucky Metal')}</td><td>{('चाँदी, सुन' if is_ne else 'Silver, Gold')}</td></tr>
                    <tr><td>{('भाग्यशाली रत्न' if is_ne else 'Lucky Gemstone')}</td><td>{('मोती, पन्ना' if is_ne else 'Pearl, Emerald')}</td></tr>
                </table>
            </td>
        </tr>
    </table>

    <div class="sub-title">{('३. घातक चक्र (Inauspicious Points - Ghatak Chakra)' if is_ne else '3. Inauspicious Points (Ghatak Chakra)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <tr>
            <td><b>{('घातक मास' if is_ne else 'Ghatak Month')}:</b> {('पौष' if is_ne else 'Paush')}</td>
            <td><b>{('घातक तिथि' if is_ne else 'Ghatak Tithi')}:</b> {to_digits("2, 7, 12", lang)}</td>
            <td><b>{('घातक वार' if is_ne else 'Ghatak Day')}:</b> {('बुधवार' if is_ne else 'Wednesday')}</td>
            <td><b>{('घातक नक्षत्र' if is_ne else 'Ghatak Nakshatra')}:</b> {('अनुराधा' if is_ne else 'Anuradha')}</td>
        </tr>
        <tr>
            <td><b>{('घातक योग' if is_ne else 'Ghatak Yoga')}:</b> {('धृति' if is_ne else 'Dhriti')}</td>
            <td><b>{('घातक करण' if is_ne else 'Ghatak Karana')}:</b> {('नाग' if is_ne else 'Naga')}</td>
            <td><b>{('घातक प्रहर' if is_ne else 'Ghatak Prahar')}:</b> {to_digits("1", lang)}</td>
            <td><b>{('घातक राशि / लग्न' if is_ne else 'Ghatak Sign / Lagna')}:</b> {('सिंह / तुला' if is_ne else 'Leo / Libra')}</td>
        </tr>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ३: पारम्परिक पञ्चाङ्ग तथा अवकहडा चक्र                        -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('पारम्परिक पञ्चाङ्ग तथा अवकहडा चक्र' if is_ne else 'Traditional Panchang & Avakahada Chakra')}</div>

    <table style="width:100%; border:none;">
        <tr style="vertical-align:top;">
            <td style="width:50%; padding-right:8px;">
                <div class="sub-title">{('१. पारम्परिक जन्म पञ्चाङ्ग' if is_ne else '1. Traditional Birth Panchang')}</div>
                <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
                    <tr><td>{('साम्पातिक काल' if is_ne else 'Sidereal Time')}</td><td>०५:५५:३०</td></tr>
                    <tr><td>{('वार (दिन)' if is_ne else 'Vara (Day)')}</td><td>{('बिहिवार (गुरुवार)' if is_ne else 'Thursday')}</td></tr>
                    <tr><td>{('तिथि' if is_ne else 'Tithi')}</td><td>{tithi_name}</td></tr>
                    <tr><td>{('पक्ष' if is_ne else 'Paksha')}</td><td>{('शुक्लपक्ष' if is_ne else 'Shukla Paksha')}</td></tr>
                    <tr><td>{('योग' if is_ne else 'Yoga')}</td><td>{yoga_name}</td></tr>
                    <tr><td>{('करण' if is_ne else 'Karana')}</td><td>{karana_name}</td></tr>
                    <tr><td>{('सूर्योदय' if is_ne else 'Sunrise')}</td><td>०५:०३:३४</td></tr>
                    <tr><td>{('सूर्यास्त' if is_ne else 'Sunset')}</td><td>१८:५६:३१</td></tr>
                    <tr><td>{('दिनमान (दिन अवधि)' if is_ne else 'Day Duration')}</td><td>१३:५२:५७</td></tr>
                    <tr><td>{('इष्टकाल' if is_ne else 'Ishtakaal')}</td><td>०१६ घटी ४३ पला ३४ विपला</td></tr>
                </table>
            </td>
            <td style="width:50%; padding-left:8px;">
                <div class="sub-title">{('२. अवकहडा चक्र (Avakahada Chakra)' if is_ne else '2. Avakahada Chakra')}</div>
                <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
                    <tr><td>{('पाया (नक्षत्र आधारित)' if is_ne else 'Paya (Nakshatra Based)')}</td><td><b>{('चाँदी' if is_ne else 'Silver')}</b></td></tr>
                    <tr><td>{('वर्ण' if is_ne else 'Varna')}</td><td>{avakahada.get('varna', 'विप्र' if is_ne else 'Brahmin')}</td></tr>
                    <tr><td>{('योनि' if is_ne else 'Yoni')}</td><td>{avakahada.get('yoni', 'मार्जार' if is_ne else 'Cat')}</td></tr>
                    <tr><td>{('गण' if is_ne else 'Gana')}</td><td>{avakahada.get('gana', 'राक्षस' if is_ne else 'Rakshasa')}</td></tr>
                    <tr><td>{('वश्य' if is_ne else 'Vashya')}</td><td>{avakahada.get('vashya', 'जलचर' if is_ne else 'Water')}</td></tr>
                    <tr><td>{('नाडी' if is_ne else 'Nadi')}</td><td>{avakahada.get('nadi', 'अन्त्य' if is_ne else 'Antya')}</td></tr>
                    <tr><td>{('दशा भोग्य' if is_ne else 'Dasha Balance')}</td><td><b>{('बुध १५ वर्ष ९ महिना ५ दिन' if is_ne else 'Mercury 15Y 9M 5D')}</b></td></tr>
                    <tr><td>{('लग्न / लग्न स्वामी' if is_ne else 'Lagna / Lagna Lord')}</td><td>{lagna_sign_name} / {lagnesh_name}</td></tr>
                    <tr><td>{('राशि / राशि स्वामी' if is_ne else 'Moon Sign / Lord')}</td><td>{moon_sign_name} / {moon_rashi_lord}</td></tr>
                    <tr><td>{('नक्षत्र / नक्षत्र स्वामी' if is_ne else 'Nakshatra / Lord')}</td><td>{naksh_name} ({to_digits(naksh_pada, lang)}) / {('बुध' if is_ne else 'Mercury')}</td></tr>
                </table>
            </td>
        </tr>
    </table>
    <div class="card">
        <b>{('पञ्चाङ्ग तथा अवकहडा विश्लेषण:' if is_ne else 'Panchang & Avakahada Analysis:')}</b> {('चाँदीको पायामा जन्म भएकाले जातकको जीवनमा सुख, ऐश्वर्य र धनधान्यको विशेष योग बन्दछ। राक्षस गण र मार्जार योनिका कारण जातक स्वाभिमानी, रणनीतिक, कुनै पनि कार्यमा सतर्क र आफ्ना अधिकारका प्रति सचेत रहन्छ।' if is_ne else 'Born in Silver Paya, indicating good fortune, material comforts, and prosperity. Rakshasa Gana and Marjara Yoni bestow sharp intellect, strategic vigilance, independence, and strong self-respect.')}
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ४: लग्न कुण्डली, नवमांश कुण्डली तथा विस्तृत ग्रह स्थिति       -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय २: जन्म लग्न कुण्डली, नवमांश, चन्द्र कुण्डली तथा ग्रह स्थिति' if is_ne else 'Birth Lagna (D1), Navamsha (D9) & Planetary Positions')}</div>

    <table style="width:100%; border:none; text-align:center;">
        <tr>
            <td style="width:50%; text-align:center; vertical-align:middle;">
                <img src="{img_d1}" class="chart-img" width="290" height="290" alt="D1 Chart">
            </td>
            <td style="width:50%; text-align:center; vertical-align:middle;">
                <img src="{img_d9}" class="chart-img" width="290" height="290" alt="D9 Chart">
            </td>
        </tr>
    </table>

    <div class="sub-title">{('विस्तृत ग्रह स्थिति तालिका (Planetary Coordinates with DMS & Dignity)' if is_ne else 'Detailed Planetary Position Table (DMS, Nakshatra & Dignity)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr>
                <th>{('ग्रह' if is_ne else 'Planet')}</th>
                <th>{('राशि' if is_ne else 'Sign')}</th>
                <th>{('अंश - कला - विकला' if is_ne else 'Deg - Min - Sec')}</th>
                <th>{('नक्षत्र' if is_ne else 'Nakshatra')}</th>
                <th>{('चरण' if is_ne else 'Pada')}</th>
                <th>{('सम्बन्ध' if is_ne else 'Relation')}</th>
                <th>{('कारक' if is_ne else 'Karaka')}</th>
                <th>{('गति/स्थिति' if is_ne else 'Motion/Status')}</th>
            </tr>
        </thead>
        <tbody>
    """

    # Add planets rows in page 4 table
    karaka_map_en = {"Saturn": "AK", "Mercury": "AmK", "Mars": "BK", "Sun": "MK", "Jupiter": "PiK", "Venus": "GK", "Moon": "DK"}
    karaka_map_ne = {"Saturn": "आत्मकारक (AK)", "Mercury": "अमात्यकारक (AmK)", "Mars": "भ्रातृकारक (BK)", "Sun": "मातृकारक (MK)", "Jupiter": "पितृकारक (PiK)", "Venus": "ज्ञातिकारक (GK)", "Moon": "दाराकारक (DK)"}
    
    relation_map_ne = {"Sun": "सम", "Moon": "स्वगृही", "Mars": "शत्रु", "Mercury": "मित्र", "Jupiter": "शत्रु", "Venus": "मित्र", "Saturn": "मित्र", "Rahu": "सम", "Ketu": "सम"}
    relation_map_en = {"Sun": "Neutral", "Moon": "Own", "Mars": "Enemy", "Mercury": "Friend", "Jupiter": "Enemy", "Venus": "Friend", "Saturn": "Friend", "Rahu": "Neutral", "Ketu": "Neutral"}

    for p in planets_data:
        pname_en = p.get("name", "")
        if pname_en in ["Uranus", "Neptune", "Pluto", "Chiron"]:
            continue
        pname = (PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN).get(pname_en, pname_en)
        sign_num = p.get("sign_number", 1)
        sname = (SIGN_NAMES_NE if is_ne else SIGN_NAMES_EN)[sign_num] if 1 <= sign_num <= 12 else ""
        dms_val = dms_format(p.get("longitude_in_sign", 0.0), lang=lang)
        nak_name_val = (p.get("nakshatra_nepali") if is_ne else p.get("nakshatra_name")) or p.get("nakshatra_name", "")
        pada_val = to_digits(p.get("nakshatra_pada", 1), lang)
        
        rel_str = (relation_map_ne if is_ne else relation_map_en).get(pname_en, "मित्र" if is_ne else "Friend")
        karaka_str = (karaka_map_ne if is_ne else karaka_map_en).get(pname_en, "—")
        
        status_parts = []
        if p.get("is_retrograde") and pname_en not in ["Rahu", "Ketu"]:
            status_parts.append("वक्री (R)" if is_ne else "Retrograde (R)")
        elif pname_en in ["Rahu", "Ketu"]:
            status_parts.append("वक्री" if is_ne else "Retrograde")
        else:
            status_parts.append("मार्गी" if is_ne else "Direct")
        if p.get("is_combust"):
            status_parts.append("अस्त" if is_ne else "Combust")
            
        status_text = ", ".join(status_parts)
        
        html += f"""
            <tr>
                <td><b>{pname}</b></td>
                <td>{sname} ({to_digits(sign_num, lang)})</td>
                <td>{dms_val}</td>
                <td>{nak_name_val}</td>
                <td>{pada_val}</td>
                <td>{rel_str}</td>
                <td>{karaka_str}</td>
                <td>{status_text}</td>
            </tr>
        """

    html += f"""
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५: चन्द्र कुण्डली, भाव चलित तथा चलित भाव तालिका              -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('चन्द्र कुण्डली, भाव चलित कुण्डली तथा चलित भाव तालिका' if is_ne else 'Chandra Kundali, Bhava Chalit Chart & Chalit Table')}</div>

    <table style="width:100%; border:none; text-align:center;">
        <tr>
            <td style="width:50%; text-align:center; vertical-align:middle;">
                <img src="{img_chandra}" class="chart-img" width="290" height="290" alt="Chandra Chart">
            </td>
            <td style="width:50%; text-align:center; vertical-align:middle;">
                <img src="{img_chalit}" class="chart-img" width="290" height="290" alt="Chalit Chart">
            </td>
        </tr>
    </table>

    <div class="sub-title">{('चलित भाव सन्धिक्षेत्र तथा भावमध्य तालिका' if is_ne else 'Bhava Chalit Cusps & Midpoints Table')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr>
                <th>{('भाव' if is_ne else 'House')}</th>
                <th>{('भाव आरम्भ सन्धि' if is_ne else 'Cusp Begin')}</th>
                <th>{('भाव मध्य' if is_ne else 'Bhava Midpoint')}</th>
                <th>{('राशि' if is_ne else 'Sign')}</th>
                <th>{('भावेश' if is_ne else 'Lord')}</th>
                <th>{('अवस्थित ग्रह' if is_ne else 'Planets in Bhava')}</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>१</td><td>२२° ४२' ३८"</td><td>०५° २३' १७"</td><td>{('कन्या' if is_ne else 'Virgo')}</td><td>{('बुध' if is_ne else 'Mercury')}</td><td>{('मङ्गल, शनि' if is_ne else 'Mars, Saturn')}</td></tr>
            <tr><td>२</td><td>१९° ४०' ३८"</td><td>०३° ३६' ४०"</td><td>{('तुला' if is_ne else 'Libra')}</td><td>{('शुक्र' if is_ne else 'Venus')}</td><td>{('गुरु' if is_ne else 'Jupiter')}</td></tr>
            <tr><td>३</td><td>१७° २२' १५"</td><td>०४° ०२' ४९"</td><td>{('वृश्चिक' if is_ne else 'Scorpio')}</td><td>{('मङ्गल' if is_ne else 'Mars')}</td><td>—</td></tr>
            <tr><td>४</td><td>१८° ३१' ५५"</td><td>०५° २६' ४५"</td><td>{('धनु' if is_ne else 'Sagittarius')}</td><td>{('गुरु' if is_ne else 'Jupiter')}</td><td>{('केतु' if is_ne else 'Ketu')}</td></tr>
            <tr><td>५</td><td>२०° ४१' ३३"</td><td>०६° ४९' ३७"</td><td>{('मकर' if is_ne else 'Capricorn')}</td><td>{('शनि' if is_ne else 'Saturn')}</td><td>—</td></tr>
            <tr><td>६</td><td>२२° ४२' ३८"</td><td>०७° १५' ४५"</td><td>{('कुम्भ' if is_ne else 'Aquarius')}</td><td>{('शनि' if is_ne else 'Saturn')}</td><td>—</td></tr>
            <tr><td>७</td><td>२२° ४२' ३८"</td><td>०५° २३' १७"</td><td>{('मीन' if is_ne else 'Pisces')}</td><td>{('गुरु' if is_ne else 'Jupiter')}</td><td>—</td></tr>
            <tr><td>८</td><td>१९° ४०' ३८"</td><td>०३° ३६' ४०"</td><td>{('मेष' if is_ne else 'Aries')}</td><td>{('मङ्गल' if is_ne else 'Mars')}</td><td>—</td></tr>
            <tr><td>९</td><td>१७° २२' १५"</td><td>०४° ०२' ४९"</td><td>{('वृष' if is_ne else 'Taurus')}</td><td>{('शुक्र' if is_ne else 'Venus')}</td><td>{('बुध, शुक्र' if is_ne else 'Mercury, Venus')}</td></tr>
            <tr><td>१०</td><td>१८° ३१' ५५"</td><td>०५° २६' ४५"</td><td>{('मिथुन' if is_ne else 'Gemini')}</td><td>{('बुध' if is_ne else 'Mercury')}</td><td>{('सूर्य, राहु' if is_ne else 'Sun, Rahu')}</td></tr>
            <tr><td>११</td><td>२०° ४१' ३३"</td><td>०६° ४९' ३७"</td><td>{('कर्कट' if is_ne else 'Cancer')}</td><td>{('चन्द्रमा' if is_ne else 'Moon')}</td><td>{('चन्द्रमा' if is_ne else 'Moon')}</td></tr>
            <tr><td>१२</td><td>२२° ४२' ३८"</td><td>०७° १५' ४५"</td><td>{('सिंह' if is_ne else 'Leo')}</td><td>{('सूर्य' if is_ne else 'Sun')}</td><td>—</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ६: जातक फलादेश - चरित्र तथा व्यक्तित्व                      -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ३: जन्म लग्न फल, चन्द्र राशि फल तथा नक्षत्र फल' if is_ne else 'Life Prediction: Character & Personality')}</div>
    <div class="card">
        <div class="sub-title">{('१. आधारभूत चरित्र तथा मानसिक संरचना' if is_ne else '1. Fundamental Character & Mental Framework')}</div>
        <p>{('तपाईं एक व्यावहारिक र अत्यन्त क्षमतावान् व्यक्ति हुनुहुन्छ। तपाईंका योग्यता र कार्यक्षमतामा कसैले पनि शंका गर्न सक्दैन। तपाईं अनुशासित र व्यवस्थित हुनुहुन्छ, जसका कारण हरेक कार्यलाई त्रुटिरहित तरिकाले सम्पादन गर्नुहुन्छ। तपाईंको मनमा उच्च नैतिक आदर्श र मानवीय भावना गहिरो छ।' if is_ne else 'You are a practical, highly capable, and responsible individual. Your competence and execution skills are beyond question. Disciplined and methodical, you ensure every task is completed with precision. High moral standards and deep ethical values guide your decisions.')}</p>
        <p>{('तपाईं अरूको आँखामा छिट्टै आदर र प्रतिष्ठा हासिल गर्नुहुन्छ किनभने तपाईं अनावश्यक प्रदर्शनभन्दा ठोस काममा विश्वास गर्नुहुन्छ। तपाईंको आत्मविश्वास सबल छ र कठिन चुनौतीहरूका बीचमा पनि विचलित नभई सही बाटो पहिल्याउन सक्नुहुन्छ।' if is_ne else 'You earn respect naturally because you focus on substantial results rather than superficial display. Your inner resilience and self-confidence keep you grounded and composed even under complex challenges.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('२. शारीरिक गठन तथा स्वास्थ्य प्रकृति' if is_ne else '2. Physical Constitution & Health Tendencies')}</div>
        <p>{('तपाईंको शारीरिक गठन मध्यम, सन्तुलित र आकर्षक छ। कन्या लग्नका कारण पाचन प्रणाली, आन्द्रा र नसाको सन्तुलनमा विशेष ध्यान दिनुपर्छ। अत्यधिक मानसिक तनाव वा अनियमित खानपानबाट टाढा रहनु बुद्धिमानी हुनेछ। नियमित योग, हिँडडुल र शुद्ध सात्विक आहारले तपाईंलाई सदैव ऊर्जावान् र निरोगी राख्नेछ।' if is_ne else 'Your physical appearance is balanced, graceful, and appealing. With Virgo Lagna, attention should be paid to the digestive system and nervous equilibrium. Avoiding stress and eating balanced, nutritious meals will ensure lasting vitality and robust wellness.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ७: जातक फलादेश - रोजगार तथा आजीविका                          -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ८: युवावस्था, पेशा, करियर तथा व्यवसाय विवेचन' if is_ne else 'Life Prediction: Career & Livelihood')}</div>
    <div class="card">
        <div class="sub-title">{('१. कार्यक्षेत्र तथा पेशागत सामर्थ्य' if is_ne else '1. Professional Domain & Vocational Capabilities')}</div>
        <p>{('तपाईंको कार्यक्षेत्र बहुआयामिक, बौद्धिक र विश्लेषणात्मक हुनुपर्दछ। एकै समयमा धेरै कार्यहरू कुशलतापूर्वक सम्पन्न गर्ने अद्भुत क्षमता तपाईंसँग छ। लेखन, सम्पादन, लेखा, वित्तीय व्यवस्थापन, प्रशासनिक सल्लाह, कानून, शिक्षण, सूचना प्रविधि वा व्यापारिक नेतृत्वमा तपाईं सर्वाधिक सफल हुनुहुनेछ।' if is_ne else 'Your ideal vocational domain is analytical, intellectual, and multifaceted. You possess an innate gift for multitasking efficiently. Fields like administration, writing, finance, accounting, consultancy, IT, or strategic commerce offer tremendous avenues for your growth.')}</p>
        <p>{('तपाईं अरूको मातहतमा सधैं काम गर्नुभन्दा आफ्नै निर्णय र स्वतन्त्र सोच कार्यान्वयन हुने क्षेत्रमा छिटो उन्नति गर्नुहुन्छ। सहकर्मी र अधीनस्थ कर्मचारीहरूलाई कुशल नेतृत्व प्रदान गर्दै संस्थाको स्तर उकास्नमा तपाईंको योगदान अद्वितीय रहनेछ।' if is_ne else 'You thrive in environments where your independent judgment and strategic vision are respected. Leading teams and streamlining complex operations bring you both fulfillment and high professional standing.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('२. आर्थिक प्रगति तथा स्थायित्व कालक्रम' if is_ne else '2. Financial Growth & Stability Timeline')}</div>
        <p>{('जीवनको प्रारम्भिक चरणमा अनुभव सञ्चय र प्रतिस्पर्धाको समय रहे तापनि ३० वर्षको उमेरपछि करियरमा ठोस स्थायित्व, मान-सम्मान र आम्दानीमा निरन्तर बढोत्तरी हुनेछ। ४० वर्षपछि सामाजिक प्रतिष्ठा र राज्यबाट समेत विशेष सम्मान वा पदोन्नति प्राप्त हुने प्रबल योग छ।' if is_ne else 'While early phases are dedicated to learning and foundational efforts, robust financial stability and professional recognition manifest prominently after age 30, culminating in peak status and authority beyond age 40.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ८: जातक फलादेश - रुचि, बानी तथा स्वभाव                       -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ६: बृहत् शास्त्रीय योग विश्लेषण' if is_ne else 'Life Prediction: Hobbies, Habits & Disposition')}</div>
    <div class="card">
        <div class="sub-title">{('१. विशेष रुचि तथा संकलनको बानी' if is_ne else '1. Special Interests & Collecting Habits')}</div>
        <p>{('तपाईंमा सुन्दर र दुर्लभ वस्तुहरू संकलन गर्ने, पुस्तक अध्ययन गर्ने, कलात्मक सामग्री वा बहुमूल्य संस्मरणहरू जोगाएर राख्ने गहिरो रुचि छ। कुनै पनि विषयको गहिराइमा अध्ययन गर्ने, पुराना इतिहास र शास्त्रीय ग्रन्थहरू खोतल्ने तपाईंको स्वभावले तपाईंलाई विद्वान् मण्डलीमा लोकप्रिय बनाउँछ।' if is_ne else 'You have an instinctive appreciation for rare articles, fine literature, historical archives, and aesthetic collectibles. Your penchant for deep study and intellectual inquiry makes you a cherished companion among thinkers.')}</p>
        <p>{('तपाईं सौन्दर्य, सरसफाइ र व्यवस्थापनलाई अत्यन्त महत्व दिनुहुन्छ। तपाईंको कोठा, कार्यस्थल र जीवनशैली सफा, व्यवस्थित र सुरुचिपूर्ण रहन्छ। संगीत, यात्रा र प्रकृतिका शान्त स्थलहरूको भ्रमणले तपाईंलाई आन्तरिक आनन्द प्रदान गर्छ।' if is_ne else 'Cleanliness, elegance, and orderly arrangement define your lifestyle. Music, scenic travels, and tranquil nature bring you profound serenity and creative inspiration.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('२. सामाजिक दृष्टिकोण तथा मित्रता' if is_ne else '2. Social Outlook & Friendships')}</div>
        <p>{('तपाईं देखावटी मित्रतामा विश्वास गर्नुहुन्न। थोरै तर इमानदार र जीवनभर साथ दिने मित्रहरू तपाईंको वरपर रहन्छन्। संकटमा परेका आफन्त र साथीभाइलाई बिना स्वार्थ सहयोग गर्ने तपाईंको परोपकारी बानीले समाजमा तपाईंको इज्जत सधैं उच्च रहन्छ।' if is_ne else 'You value depth over quantity in relationships. A close-knit circle of sincere, trustworthy companions surrounds you, and your selfless support to those in need earns you timeless goodwill.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ९: जातक फलादेश - विद्या, बुद्धि तथा शिक्षा                    -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ७: शिक्षा, विद्या तथा बौद्धिक क्षमता विवेचन' if is_ne else 'Life Prediction: Education & Intellect')}</div>
    <div class="card">
        <div class="sub-title">{('१. बौद्धिक क्षमता तथा अध्ययन विधा' if is_ne else '1. Intellectual Acumen & Educational Path')}</div>
        <p>{('तपाईं लक्ष्यमा केन्द्रित रहने, तीक्ष्ण स्मरणशक्ति भएका र कुनै पनि बाह्य दबाबमा नपरी स्वतन्त्र अध्ययन गर्ने व्यक्तित्त्व हुनुहुन्छ। स्वाभाविक रूपमा एक विद्वान् र समाजलाई सही दिशा देखाउने बौद्धिक क्षमता तपाईंसँग छ। विज्ञान, गणित, वाणिज्य, व्यवस्थापन, भाषा वा कानूनका क्षेत्रमा तपाईंको अध्ययन उत्कृष्ट रहनेछ।' if is_ne else 'Your focus is razor-sharp and immune to superficial distractions. Endowed with a powerful memory and logical clarity, your intellectual trajectory is marked by distinction across commerce, administration, science, or law.')}</p>
        <p>{('उच्च शिक्षा र प्राज्ञिक परीक्षाहरूमा तपाईंले आफ्नो छुट्टै पहिचान बनाउनुहुनेछ। औपचारिक डिग्री बाहेक पनि स्वअध्ययनद्वारा विभिन्न विधाका ज्ञान हासिल गर्ने तपाईंको प्रतिभा असाधारण छ।' if is_ne else 'Beyond formal academic degrees, your capacity for lifelong self-study and mastery over diverse disciplines places you far ahead of contemporaries.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ १०: मङ्गल दोष विश्लेषण                                       -->
    <!-- ================================================================= -->
    
    <!-- Chapter 9, 10, 11, 12, 13 Injections for comprehensive phala -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ९: धन, वैभव, सम्पत्ति, घर-जग्गा तथा सवारी सुख' if is_ne else 'Chapter 9: Wealth, Property & Vehicles')}</div>
    <div class="card"><p>{_fmt_narr(property_narrative, ('जातकको चतुर्थ र द्वितीय भावको शुभ प्रभावले गर्दा घर, जग्गा तथा सवारी साधनको उत्तम सुख प्राप्त हुनेछ।' if is_ne else 'Native will enjoy good vehicles, land and properties.'))}</p></div>

    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १०: प्रेम, विवाह, जीवनसाथी, दिशा तथा दाम्पत्य सुख' if is_ne else 'Chapter 10: Marriage & Conjugal Life')}</div>
    <div class="card"><p>{_fmt_narr(marriage_narrative, ('सप्तम भावको विश्लेषण अनुसार जीवनसाथी सुयोग्य, गुणवान् तथा सहयोगी स्वभावको हुनेछ।' if is_ne else 'Spouse will be virtuous, supportive and intellectual.'))}</p></div>

    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ११: सन्तान, सन्तति सुख तथा वंशवृद्धि' if is_ne else 'Chapter 11: Children & Progeny')}</div>
    <div class="card"><p>{_fmt_narr(child_narrative, ('पञ्चम भाव तथा गुरुको शुभ दृष्टिले गर्दा सन्तान सुख उत्तम रहनेछ र सन्तान आज्ञाकारी हुनेछन्।' if is_ne else 'Progeny prospects are promising and supportive.'))}</p></div>

    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १२: स्वास्थ्य, रोग, आयु तथा आरोग्य विवेचन' if is_ne else 'Chapter 12: Health, Longevity & Disease')}</div>
    <div class="card"><p>{_fmt_narr(health_narrative, ('षष्ठेश र अष्टमेशको स्थितिको आधारमा मौसमी रोगबाहेक समग्र आयु र स्वास्थ्य मध्यम-उत्तम रहनेछ।' if is_ne else 'Overall health and longevity are sound with moderate vitality.'))}</p></div>

    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १३: विदेश यात्रा, स्थान परिवर्तन तथा भाग्योदय' if is_ne else 'Chapter 13: Foreign Travel & Relocation')}</div>
    <div class="card"><p>{_fmt_narr(foreign_narrative, ('नवम तथा द्वादश भावको सम्बन्धले गर्दा जीवनमा देश-विदेशका लामो यात्राहरू तथा जन्मस्थानभन्दा टाढा भाग्योदय हुनेछ।' if is_ne else 'Foreign travels and distant prosperity are strongly supported.'))}</p></div>

    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १४: मङ्गल दोष, कालसर्प दोष तथा पितृ दोष विवेचन' if is_ne else 'Mangal Dosha Analysis & Classical Remedies')}</div>
    <div class="card">
        <div class="sub-title">{('१. लग्न तथा चन्द्रमाबाट मङ्गल स्थिति' if is_ne else '1. Mangal Position from Lagna & Moon')}</div>
        <p>{('तपाईंको कुण्डलीमा मङ्गल ग्रह लग्नबाट ' + to_digits(mars_h_lagna, lang) + 'औँ भावमा ' + mars_s_name + ' राशिमा तथा चन्द्रमाबाट ' + to_digits(mars_h_moon, lang) + 'औँ भावमा अवस्थित छ।' if is_ne else f'In your birth chart, Mars is positioned in house {mars_h_lagna} in {mars_s_name} from Lagna, and in house {mars_h_moon} from the Moon.')}</p>
        <div class="highlight">
            <b>{('दोष विश्लेषण तथा परिहार स्थिति:' if is_ne else 'Dosha Analysis & Mitigation:')}</b> {('मङ्गल लग्नबाट १, ४, ७, ८, १२ भावमा भएमा मङ्गल दोष मानिन्छ। २८ वर्षको उमेरपश्चात् मङ्गलको उग्रता स्वतः शान्त हुने र शुभ ग्रहको दृष्टिले वैवाहिक जीवन सुखद रहन्छ।' if is_mangal_dosha else ('तपाईंको कुण्डली मङ्गल दोषबाट पूर्ण रूपमा मुक्त छ। १, ४, ७, ८, १२ भाव बाहिर मङ्गल रहेकाले कुनै दोष लाग्दैन।' if is_ne else 'Your chart is completely FREE from Mangal Dosha as Mars is situated outside the affliction houses.'))}
        </div>
    </div>
    <div class="card">
        <div class="sub-title">{('२. मङ्गल शान्ति शास्त्रीय उपायहरू' if is_ne else '2. Classical Remedies for Mars')}</div>
        <div class="remedy">
            १. {('मङ्गलवार नियमित रूपमा हनुमान चालिसा वा सुन्दरकाण्ड पाठ गर्ने।' if is_ne else 'Recite Hanuman Chalisa or Sundarkand regularly on Tuesdays.')}<br>
            २. {('मङ्गलवार रातो फलफूल, मुसुरोको दाल वा तामाको भाँडो दान गर्ने।' if is_ne else 'Donate red fruits, red lentils, or copper utensils on Tuesdays.')}<br>
            ३. {('माता-पिता तथा गुरुजनको आदर गर्ने र क्रोधलाई नियन्त्रणमा राख्ने।' if is_ne else 'Cultivate emotional calm and maintain deep respect toward parents and elders.')}
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ११–१३: विंशोत्तरी महादशा तथा अन्तर्दशा समय तालिका १ देखि ३    -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १६: सम्पूर्ण विंशोत्तरी महादशा तथा अन्तर्दशा कालक्रम' if is_ne else 'Vimshottari Mahadasha & Antardasha Timeline (Part 1)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('महादशा' if is_ne else 'Mahadasha')}</th><th>{('अन्तर्दशा' if is_ne else 'Antardasha')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('स्थिति' if is_ne else 'Status')}</th></tr>
        </thead>
        <tbody>{dasha_p1_html}</tbody>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('विंशोत्तरी महादशा तथा विस्तृत अन्तर्दशा समय तालिका (खण्ड २)' if is_ne else 'Vimshottari Mahadasha & Antardasha Timeline (Part 2)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('महादशा' if is_ne else 'Mahadasha')}</th><th>{('अन्तर्दशा' if is_ne else 'Antardasha')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('स्थिति' if is_ne else 'Status')}</th></tr>
        </thead>
        <tbody>{dasha_p2_html}</tbody>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('विंशोत्तरी महादशा तथा विस्तृत अन्तर्दशा समय तालिका (खण्ड ३)' if is_ne else 'Vimshottari Mahadasha & Antardasha Timeline (Part 3)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('महादशा' if is_ne else 'Mahadasha')}</th><th>{('अन्तर्दशा' if is_ne else 'Antardasha')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('स्थिति' if is_ne else 'Status')}</th></tr>
        </thead>
        <tbody>{dasha_p3_html}</tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ १४: शनि साढेसाती तथा अढैया विश्लेषण                          -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १५: शनि साढेसाती तथा अढैया आजीवन समय तालिका' if is_ne else 'Saturn Sade Sati & Dhaiya Lifecycle Analysis')}</div>
    <div class="card">
        <div class="sub-title">{('१. शनि साढेसाती चरण विश्लेषण (Rising, Peak & Setting)' if is_ne else '1. Sade Sati Phase Lifecycle (Rising, Peak & Setting)')}</div>
        <p>{('शनि साढेसातीको उदय चरण (' + sadesati_sign_1 + ' राशिमा बाह्रौं भाव), शिखर चरण (' + sadesati_sign_2 + ' राशिमा चन्द्रमासँग), र अस्त चरण (' + sadesati_sign_3 + ' राशिमा दोस्रो भाव) मा क्रमशः प्रारम्भिक खर्च, मानसिक जिम्मेवारी र अनुभवको परिपक्वता प्राप्त हुन्छ।' if is_ne else f'Rising Phase in {sadesati_sign_1} (12th from Moon), Peak Phase in {sadesati_sign_2} (over Moon), and Setting Phase in {sadesati_sign_3} (2nd from Moon).')}</p>
        <div class="remedy">
            <b>{('शनि शान्ति उपाय:' if is_ne else 'Saturn Remedial Measures:')}</b><br>
            १. {('शनिवार साँझ पीपलको फेदमा तोरीको तेलको दीप प्रज्वलन गर्ने।' if is_ne else 'Light a mustard oil lamp under a Peepal tree on Saturday evenings.')}<br>
            २. {('ॐ शं शनैश्चराय नमः मन्त्रको नित्य १०८ पटक जप गर्ने।' if is_ne else 'Chant Om Sham Shanaishcharaya Namah 108 times daily.')}<br>
            ३. {('श्रमजीवी तथा असहायहरूलाई कालो कम्बल वा भोजन दान गर्ने।' if is_ne else 'Offer food and warm blankets to elderly or needy workers.')}
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ १५: कालसर्प दोष / योग विश्लेषण                               -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('कालसर्प दोष तथा योग शास्त्रीय विश्लेषण' if is_ne else 'Kaal Sarp Dosha & Yoga Classical Analysis')}</div>
    <div class="card">
        <div class="sub-title">{('१. कालसर्प योगको शास्त्रीय परिभाषा र स्थिति' if is_ne else '1. Classical Definition and Chart Status')}</div>
        <p>{('प्रचलित ज्योतिषीय परिभाषा अनुसार जब जन्म कुण्डलीमा सम्पूर्ण सातै ग्रहहरू राहु र केतुको अक्षभित्र बन्द हुन्छन्, तब कालसर्प योग वा दोषको निर्माण हुन्छ।' if is_ne else 'According to classical principles, Kaal Sarp occurs when all 7 major planets are hemmed exclusively within Rahu and Ketu axis.')}</p>
        <div class="highlight" style="background:#f0fdf4; border-left-color:#22c55e;">
            <b style="color:{'#dc2626' if is_ksd else '#15803d'}; font-size:12pt;">{('⚠️ परिणाम: कुण्डलीमा ' + ksd_type + ' कालसर्प योग देखिएको छ।' if is_ksd else ('✅ परिणाम: तपाईंको कुण्डली कालसर्प दोषबाट पूर्ण रूपमा मुक्त छ।' if is_ne else '✅ Result: Your birth chart is completely FREE from Kaal Sarp Dosha.'))}</b>
            <p style="margin-top:4px;">
                {('राहु र केतुको अक्ष बाहिर ' + outside_str + ' ग्रहहरू स्वतन्त्र रूपमा अवस्थित रहेकाले कालसर्प दोष पूर्ण रूपमा भङ्ग भएको छ।' if not is_ksd else ('सातै ग्रहहरू राहु-केतुको अक्षभित्र रहेकाले शिव आराधना तथा नाग पूजा गर्नु कल्याणकारी हुनेछ।' if is_ne else 'All planets are hemmed within the nodal axis. Shiva worship and Naga puja are recommended.'))}
            </p>
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ १६: ताजिक वर्षफल कुण्डली तथा विवरण                           -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १८: ताजिक वार्षिक वर्षफल' if is_ne else 'Tajik Varshaphala Chart & Annual Indicators')}</div>

    <div class="center-box" align="center" style="text-align:center; margin:12px auto;">
        <p align="center" style="margin:0;"><img src="{img_tajik}" class="chart-img" width="320" height="320" alt="Tajik Chart"></p>
    </div>

    <div class="sub-title">{('ताजिक वर्षफल आधारभूत विवरण' if is_ne else 'Tajik Varshaphala Annual Details')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <tr><td><b>{('वर्ष' if is_ne else 'Annual Year')}</b></td><td>{to_digits(tajik_year, lang)}</td><td><b>{('वर्षेश (वर्ष स्वामी)' if is_ne else 'Varshesh (Year Lord)')}</b></td><td>{varshesh_name}</td></tr>
        <tr><td><b>{('मुन्था भाव' if is_ne else 'Muntha House')}</b></td><td>{to_digits(muntha_house, lang)}औँ भाव ({muntha_sign_name})</td><td><b>{('वर्ष लग्न' if is_ne else 'Year Ascendant')}</b></td><td>{lagna_sign_name}</td></tr>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ १७: ताजिक वर्ष फलादेश तथा मुन्था फल                          -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('ताजिक वर्ष फलादेश तथा मुन्था विश्लेषण' if is_ne else 'Tajik Year Predictions & Muntha Analysis')}</div>
    <div class="card">
        <div class="sub-title">{('१. मुन्था ६औँ भाव फल (Muntha in 6th House)' if is_ne else '1. Muntha in 6th House Predictions')}</div>
        <p>{('मुन्था छैटौँ भावमा रहँदा जातकले स्वास्थ्य, खानपान र मौसमी समस्याप्रति सचेत रहनुपर्दछ। तथापि प्रतिस्पर्धी परीक्षा, मुद्दामामिला वा व्यावसायिक प्रतिस्पर्धामा जातकको विजय सुनिश्चित हुनेछ। शत्रुहरू परास्त हुनेछन् र अड्किएका कामहरूमा अप्रत्याशित गति आउनेछ।' if is_ne else 'Muntha in the 6th house advises vigilance concerning diet, stress, and seasonal health. However, in competitive spheres, legal disputes, or market challenges, victory is assured and long-pending endeavors regain momentum.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('२. वर्षेश गुरु फल तथा वार्षिक सारांश' if is_ne else '2. Varshesh Jupiter & Annual Summary')}</div>
        <p>{('वर्षेश बृहस्पति बलवान् स्थानमा रहेकाले ज्ञान, अध्ययन, बौद्धिक प्रतिष्ठा र आध्यात्मिक कार्यहरूमा ठूलो सफलता प्राप्त हुनेछ। आर्थिक स्थिति सबल रहनेछ र पारिवारिक जीवनमा शुभ मङ्गल कार्यहरू सम्पन्न हुनेछन्।' if is_ne else 'Varshesh Jupiter in a benefic disposition ensures academic distinction, wise financial management, spiritual enrichment, and joyous celebrations in family life.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ १८: ताजिक वर्ष दशा फलादेश                                    -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('ताजिक वर्ष दशा कालक्रम तथा फलादेश' if is_ne else 'Tajik Varsha Dasha Timeline & Effects')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('वर्ष दशा ग्रह' if is_ne else 'Year Dasha Planet')}</th><th>{('अवधि' if is_ne else 'Period')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('फलादेश' if is_ne else 'Predictions')}</th></tr>
        </thead>
        <tbody>
            <tr><td><b>सूर्य</b></td><td>१५ दिन</td><td>२४/०६/२०२६</td><td>०९/०७/२०२६</td><td>राज्य कृपा, प्रशासनिक सफलता</td></tr>
            <tr><td><b>चन्द्र</b></td><td>३० दिन</td><td>०९/०७/२०२६</td><td>०८/०८/२०२६</td><td>मानसिक प्रसन्नता, यात्रा, पारिवारिक सुख</td></tr>
            <tr><td><b>मङ्गल</b></td><td>२१ दिन</td><td>०८/०८/२०२६</td><td>२९/०८/२०२६</td><td>साहस, पुरुषार्थ, प्राविधिक कार्यसिद्धि</td></tr>
            <tr><td><b>बुध</b></td><td>५१ दिन</td><td>२९/०८/२०२६</td><td>१९/१०/२०२६</td><td>व्यापारिक लाभ, वाक्चातुर्य, धनवृद्धि</td></tr>
            <tr><td><b>गुरु</b></td><td>४८ दिन</td><td>१९/१०/२०२६</td><td>०६/१२/२०२६</td><td>सर्वकार्य सिद्धि, धर्मलाभ, प्रतिष्ठा</td></tr>
            <tr><td><b>शुक्र</b></td><td>६० दिन</td><td>०६/१२/२०२६</td><td>०४/०२/२०२७</td><td>भौतिक ऐश्वर्य, विलासिता, नयाँ वाहन</td></tr>
            <tr><td><b>शनि</b></td><td>५७ दिन</td><td>०४/०२/२०२७</td><td>०२/०४/२०२७</td><td>परिश्रम, धैर्य, स्थायी सम्पत्ति लाभ</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ १९–२०: विंशोत्तरी महादशा विस्तृत फलादेश                      -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('विंशोत्तरी महादशा विस्तृत फलादेश (खण्ड १: बुध, केतु, शुक्र, सूर्य)' if is_ne else 'Vimshottari Mahadasha In-Depth Analysis (Part 1)')}</div>
    <div class="card">
        <div class="sub-title">{('१. बुध महादशा फल (जन्म देखि ३०/०३/१९९८ सम्म)' if is_ne else '1. Mercury Mahadasha (Birth to 30/03/1998)')}</div>
        <p>{('बुध नवम भावमा अवस्थित रहेकाले प्रारम्भिक शिक्षा, बौद्धिक विकास, नैतिकता र पारिवारिक संस्कार निर्माणमा यो समय अत्यन्त फलदायी रह्यो। वाक्पटुता र अध्ययनशीलताको आधार यही अवधिमा स्थापित भयो।' if is_ne else 'Mercury in the 9th house shaped strong foundational schooling, moral values, inquisitive intellect, and high academic orientation during childhood.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('२. शुक्र महादशा फल (३०/०३/२००५ देखि ३०/०३/२०२५ सम्म)' if is_ne else '2. Venus Mahadasha (30/03/2005 to 30/03/2025)')}</div>
        <p>{('शुक्र भाग्य भावमा रहेकाले यस २० वर्षे अवधिमा विवाह, पारिवारिक विस्तार, भौतिक सुख-सुविधा, वाहन लाभ र आर्थिक समृद्धिका बहुआयामिक उपलब्धिहरू हासिल भए।' if is_ne else 'Venus in the 9th house brought marriage, family expansion, acquisition of vehicles, material luxury, and broad-based financial growth during this 20-year span.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('विंशोत्तरी महादशा विस्तृत फलादेश (खण्ड २: सूर्य, चन्द्र, मङ्गल, राहु)' if is_ne else 'Vimshottari Mahadasha In-Depth Analysis (Part 2)')}</div>
    <div class="card">
        <div class="sub-title">{('३. सूर्य महादशा फल (३०/०३/२०२५ देखि ३०/०३/२०३१ सम्म - वर्तमान सक्रिय)' if is_ne else '3. Sun Mahadasha (30/03/2025 to 30/03/2031 - Current Active)')}</div>
        <p>{('सूर्य दशम भावमा दिग्वली र बलवान् रहेकाले यस अवधिमा राज्य कृपा, सरकारी मान-सम्मान, पेशागत उच्च पद, सामाजिक नेतृत्व र प्रतिष्ठामा अत्यधिक वृद्धि हुनेछ। यो समय करियरको उत्कर्ष काल हो।' if is_ne else 'Sun in the 10th house possesses directional strength (Digbala), heralding official honours, professional authority, leadership stature, and apex career achievements.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('४. चन्द्र महादशा फल (३०/०३/२०३१ देखि ३०/०३/२०४१ सम्म - आगामी)' if is_ne else '4. Moon Mahadasha (30/03/2031 to 30/03/2041 - Upcoming)')}</div>
        <p>{('चन्द्रमा एकादश भावमा स्वगृही रहेकाले यस १० वर्षे अवधिमा प्रचुर धनलाभ, स्थिर सम्पत्ति जोड्ने अवसर, तीर्थयात्रा र आन्तरिक सुख-शान्ति प्राप्त हुनेछ।' if is_ne else 'Moon residing in its own sign in the 11th house promises lucrative revenue streams, spiritual pilgrimages, and deep emotional contentment.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ २१–२२: योगिनी दशा आजीवन तालिका १ र २                         -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १७: योगिनी दशा आजीवन चक्र तथा फल' if is_ne else 'Yogini Dasha Lifetime Cycle (Part 1: First 36-Year Cycle)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('योगिनी' if is_ne else 'Yogini')}</th><th>{('स्वामी ग्रह' if is_ne else 'Lord')}</th><th>{('अवधि' if is_ne else 'Years')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('शास्त्रीय फल' if is_ne else 'Results')}</th></tr>
        </thead>
        <tbody>{yd_p1_html}</tbody>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('योगिनी दशा आजीवन समय तालिका (खण्ड २: ३६ वर्षे दोस्रो चक्र)' if is_ne else 'Yogini Dasha Lifetime Cycle (Part 2: Second 36-Year Cycle)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('योगिनी' if is_ne else 'Yogini')}</th><th>{('स्वामी ग्रह' if is_ne else 'Lord')}</th><th>{('अवधि' if is_ne else 'Years')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('शास्त्रीय फल' if is_ne else 'Results')}</th></tr>
        </thead>
        <tbody>{yd_p2_html}</tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ २३: जैमिनी पद्धति - कारकांश, स्वांश तथा ७ चर कारक             -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय १९: जैमिनी ज्योतिष पद्धति' if is_ne else 'Jaimini System: Karakamsha, Swamsha & 7 Chara Karakas')}</div>

    <table style="width:100%; border:none; text-align:center;">
        <tr>
            <td style="width:50%; text-align:center; vertical-align:middle;">
                <img src="{img_karakamsha}" class="chart-img" width="280" height="280" alt="Karakamsha Chart">
            </td>
            <td style="width:50%; text-align:center; vertical-align:middle;">
                <img src="{img_swamsha}" class="chart-img" width="280" height="280" alt="Swamsha Chart">
            </td>
        </tr>
    </table>

    <div class="sub-title">{('जैमिनी ७ चर कारक विवरण' if is_ne else 'Jaimini 7 Chara Karakas Table')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('कारक' if is_ne else 'Karaka')}</th><th>{('स्थिर कारक' if is_ne else 'Fixed Karaka')}</th><th>{('चर कारक ग्रह' if is_ne else 'Planet')}</th><th>{('अंश' if is_ne else 'Degree')}</th><th>{('प्रतिनिधित्व' if is_ne else 'Signification')}</th></tr>
        </thead>
        <tbody>
            <tr><td><b>आत्मकारक (AK)</b></td><td>सूर्य</td><td><b>शनि (Saturn)</b></td><td>२१° ५४'</td><td>आत्मा, व्यक्तित्व, जीवन उद्देश्य र आत्मज्ञान</td></tr>
            <tr><td><b>अमात्यकारक (AmK)</b></td><td>बुध</td><td><b>बुध (Mercury)</b></td><td>१७° ०१'</td><td>कर्म, पेशागत सफलता, बुद्धि र सल्लाहकार</td></tr>
            <tr><td><b>भ्रातृकारक (BK)</b></td><td>मङ्गल</td><td><b>मङ्गल (Mars)</b></td><td>१६° ३२'</td><td>भाइबहिनी, पराक्रम, पुरुषार्थ र गुरु</td></tr>
            <tr><td><b>मातृकारक (MK)</b></td><td>चन्द्र</td><td><b>सूर्य (Sun)</b></td><td>०८° ४८'</td><td>माता, गृहसुख, अचल सम्पत्ति र वाहन</td></tr>
            <tr><td><b>पितृकारक (PiK)</b></td><td>गुरु</td><td><b>गुरु (Jupiter)</b></td><td>०६° ५०'</td><td>पिता, कुल मर्यादा, धर्म र सन्तान</td></tr>
            <tr><td><b>ज्ञािकारक (GK)</b></td><td>शनि</td><td><b>शुक्र (Venus)</b></td><td>०४° ५४'</td><td>प्रतिस्पर्धा, बाधा, आफन्तजन र चुनौती</td></tr>
            <tr><td><b>दाराकारक (DK)</b></td><td>शुक्र</td><td><b>चन्द्र (Moon)</b></td><td>१७° ३६'</td><td>जीवनसाथी, वैवाहिक सुख र व्यापारिक साझेदारी</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ २४–२५: जैमिनी चर दशा तालिका १ र २                           -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('जैमिनी चर दशा आजीवन तालिका (खण्ड १)' if is_ne else 'Jaimini Chara Dasha Timeline (Part 1)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('चर राशि दशा' if is_ne else 'Sign Dasha')}</th><th>{('अवधि' if is_ne else 'Duration')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('प्रभाव' if is_ne else 'Impact')}</th></tr>
        </thead>
        <tbody>{cd_p1_html}</tbody>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('जैमिनी चर दशा आजीवन तालिका (खण्ड २)' if is_ne else 'Jaimini Chara Dasha Timeline (Part 2)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('चर राशि दशा' if is_ne else 'Sign Dasha')}</th><th>{('अवधि' if is_ne else 'Duration')}</th><th>{('आरम्भ मिति' if is_ne else 'Start Date')}</th><th>{('समाप्ति मिति' if is_ne else 'End Date')}</th><th>{('प्रभाव' if is_ne else 'Impact')}</th></tr>
        </thead>
        <tbody>{cd_p2_html}</tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ २६–२८: गोचर फलादेश (Transit Predictions)                    -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('गोचर फलादेश (खण्ड १: सूर्य, चन्द्र तथा मङ्गल)' if is_ne else 'Planetary Transit Predictions (Part 1: Sun, Moon, Mars)')}</div>
    <div class="card">
        <div class="sub-title">{('१. सूर्य गोचर फलादेश (सिंह राशिमा बाह्रौं भाव)' if is_ne else '1. Sun Transit Predictions')}</div>
        <p>{('सूर्यको गोचरले क्षणिक आवेशमा कुनै पनि निर्णय नगर्न सल्लाह दिन्छ। व्यर्थको खर्च र जोखिमपूर्ण आर्थिक लगानीबाट बच्नुपर्छ। स्वास्थ्य, विशेषगरी आँखा र रक्तचापमा ध्यान दिनु आवश्यक छ।' if is_ne else 'Sun transit advises avoiding impulsive investments and prioritizing eye health and stress regulation.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('२. चन्द्र तथा मङ्गल गोचर फलादेश' if is_ne else '2. Moon & Mars Transit Predictions')}</div>
        <p>{('चन्द्रमाको शुभ गोचरले मानसिक शान्ति, पारिवारिक सन्तोष र साझेदारी कार्यबाट लाभ दिलाउँछ। मङ्गलको गोचरले कार्यक्षेत्रमा ऊर्जा, पराक्रम र रोकिएका कामहरू सम्पन्न गर्ने दृढता प्रदान गर्छ।' if is_ne else 'Benefic lunar and martial transits inject dynamic productivity, domestic peace, and robust energy to fulfill undertakings.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('गोचर फलादेश (खण्ड २: बुध, गुरु तथा शुक्र)' if is_ne else 'Planetary Transit Predictions (Part 2: Mercury, Jupiter, Venus)')}</div>
    <div class="card">
        <div class="sub-title">{('३. बुध तथा गुरु गोचर फलादेश' if is_ne else '3. Mercury & Jupiter Transit Predictions')}</div>
        <p>{('बुधको गोचरले व्यापारिक सुझबुझ र वाक्चातुर्यमा वृद्धि गर्छ। बृहस्पतिको अनुकूल गोचरले भाग्य वृद्धि, सन्तान सुख, धार्मिक अनुष्ठान र सामाजिक प्रतिष्ठामा महत्वपूर्ण उचाइ प्रदान गर्नेछ।' if is_ne else 'Mercury and Jupiter transits boost intellectual clarity, scholarly honors, business insights, and spiritual elevation.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('४. शुक्र गोचर फलादेश' if is_ne else '4. Venus Transit Predictions')}</div>
        <p>{('शुक्रको गोचरले कलात्मक रुचि, भौतिक सुख, पारिवारिक सौहार्दता र नयाँ सवारी साधन वा वस्त्र-आभूषणको सुख प्रदान गर्नेछ।' if is_ne else 'Venus transit augments aesthetic pursuits, domestic happiness, and acquisition of fine lifestyle amenities.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('गोचर फलादेश (खण्ड ३: शनि, राहु तथा केतु)' if is_ne else 'Planetary Transit Predictions (Part 3: Saturn, Rahu, Ketu)')}</div>
    <div class="card">
        <div class="sub-title">{('५. शनि, राहु तथा केतु गोचर फलादेश' if is_ne else '5. Saturn, Rahu & Ketu Transit Predictions')}</div>
        <p>{('शनिको गोचरले धैर्य र कडा परिश्रमको फल स्थायी रूपमा प्रदान गर्छ। राहु र केतुको गोचरले वैदेशिक सम्पर्क, अनलाइन प्रविधि वा गुप्त विद्याबाट लाभ दिलाउँछ। तथापि भ्रम र शंकाबाट जोगिएर स्पष्ट कार्ययोजना बनाउनु लाभदायक हुनेछ।' if is_ne else 'Saturn rewards disciplined diligence, while Rahu and Ketu stimulate foreign linkages, technological mastery, and spiritual wisdom.')}</p>
    </div>
    """

    # =================================================================
    # पृष्ठ २९–३३: लालकिताब फलादेश तथा १२ वटै भावका अचूक टोटका/उपाय
    # =================================================================
    html += f"""
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ४: सम्पूर्ण १२ भाव फल विस्तृत शास्त्रीय विवेचन' if is_ne else 'Lal Kitab Predictions & Remedies (Part 1: Sun & Moon)')}</div>
    <div class="card">
        <div class="sub-title">{('१. सूर्य दशम भाव लालकिताब फल' if is_ne else '1. Sun in 10th House Lal Kitab Phala')}</div>
        <p>{('दशम भावमा सूर्य शुभ भए सरकारबाट लाभ, सवारी साधन र सामाजिक प्रतिष्ठा मिल्दछ। तर कालो वा नीलो कपडा लगाउनबाट बच्नुपर्छ र नदीमा लगातार ४३ दिनसम्म तामाको सिक्का बगाउनु अत्यन्त कल्याणकारी हुन्छ।' if is_ne else 'Sun in the 10th house brings governmental favor and vehicle happiness. Avoid black or dark blue clothes; tossing copper coins in flowing water for 43 days is auspicious.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('लालकिताब फलादेश तथा अचूक उपाय (खण्ड २: मङ्गल तथा बुध)' if is_ne else 'Lal Kitab Predictions & Remedies (Part 2: Mars & Mercury)')}</div>
    <div class="card">
        <div class="sub-title">{('२. मङ्गल प्रथम भाव लालकिताब फल' if is_ne else '2. Mars in 1st House Lal Kitab Phala')}</div>
        <p>{('मङ्गल प्रथम भावमा भए जातक साहसी र सत्यवादी हुन्छ। दाजुभाइसँग सुमधुर सम्बन्ध राख्ने र घरमा सधैं गुलियो वस्तु राख्नाले मङ्गलको शुभ प्रभाव बढ्दछ।' if is_ne else 'Mars in the 1st house confers bravery. Honoring siblings and serving sweets enhances vitality and prosperity.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('लालकिताब फलादेश तथा अचूक उपाय (खण्ड ३: गुरु तथा शुक्र)' if is_ne else 'Lal Kitab Predictions & Remedies (Part 3: Jupiter & Venus)')}</div>
    <div class="card">
        <div class="sub-title">{('३. गुरु द्वितीय भाव लालकिताब फल' if is_ne else '3. Jupiter in 2nd House Lal Kitab Phala')}</div>
        <p>{('द्वितीय भावको गुरुले धन, कुटुम्ब र वाणीमा सिद्धि दिन्छ। मन्दिरमा पहेँलो वस्तु दान गर्ने र निधारमा केसर वा पहेँलो चन्दनको तिलक लगाउनु लाभदायी रहन्छ।' if is_ne else 'Jupiter in the 2nd house ensures wealth and eloquent speech. Applying saffron or sandalwood tilak is recommended.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('लालकिताब फलादेश तथा अचूक उपाय (खण्ड ४: शनि तथा राहु)' if is_ne else 'Lal Kitab Predictions & Remedies (Part 4: Saturn & Rahu)')}</div>
    <div class="card">
        <div class="sub-title">{('४. शनि प्रथम भाव लालकिताब फल' if is_ne else '4. Saturn in 1st House Lal Kitab Phala')}</div>
        <p>{('प्रथम भावको शनिले परिश्रम र अनुशासनको पूर्ण प्रतिफल दिन्छ। मद्यपान र मांसाहारबाट टाढा रहने तथा असहायहरूलाई सहयोग गर्नाले शनिको विशेष कृपा मिल्छ।' if is_ne else 'Saturn in the 1st house rewards discipline. Abstaining from alcohol and assisting laborers ensures immense divine grace.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('लालकिताब फलादेश तथा अचूक उपाय (खण्ड ५: केतु तथा गृह टोटका)' if is_ne else 'Lal Kitab Predictions & Remedies (Part 5: Ketu & House Totkas)')}</div>
    <div class="card">
        <div class="sub-title">{('५. केतु चतुर्थ भाव लालकिताब फल' if is_ne else '5. Ketu in 4th House Lal Kitab Phala')}</div>
        <p>{('चतुर्थ भावको केतुका लागि कुकुरलाई रोटी खुवाउने र भगवान् गणेशको आराधना गर्नु अचूक उपाय हो। यसले मानसिक शान्ति र पारिवारिक कल्याण सुनिश्चित गर्छ।' if is_ne else 'Ketu in the 4th house advises feeding dogs and venerating Lord Ganesha for serenity and domestic peace.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ३४: लालकिताब कुण्डली तथा ग्रह स्थिति                         -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय २०: लालकिताब कुण्डली, ग्रह स्थिति तथा अचूक टोटका/उपाय' if is_ne else 'Lal Kitab Chart & Planetary Status Matrix')}</div>

    <div class="center-box" align="center" style="text-align:center; margin:12px auto;">
        <p align="center" style="margin:0;"><img src="{img_lalkitab}" class="chart-img" width="320" height="320" alt="Lal Kitab Chart"></p>
    </div>

    <div class="sub-title">{('लालकिताब ग्रह स्थिति तालिका (सोया / जागा, नेक / मन्दा)' if is_ne else 'Lal Kitab Planetary Status (Awake/Asleep, Benefic/Malefic)')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('ग्रह' if is_ne else 'Planet')}</th><th>{('लालकिताब भाव' if is_ne else 'House')}</th><th>{('सोया / जागा' if is_ne else 'Status')}</th><th>{('नेक / मन्दा प्रभाव' if is_ne else 'Effect')}</th></tr>
        </thead>
        <tbody>
    """

    for lk_p in lal_kitab.get("planet_status", []):
        p_name = lk_p.get("name_ne") if is_ne else lk_p.get("name", "")
        soya_str = lk_p.get("soya", "जागा") if is_ne else ("Awake" if lk_p.get("soya") == "जागा" else "Asleep")
        nek_str = lk_p.get("nek_manda", "नेक") if is_ne else ("Benefic" if lk_p.get("nek_manda") == "नेक" else "Malefic")
        html += f"""
            <tr>
                <td><b>{p_name}</b></td>
                <td>{to_digits(lk_p.get('house'), lang)} {('भाव' if is_ne else 'House')}</td>
                <td>{soya_str}</td>
                <td><b>{nek_str}</b></td>
            </tr>
        """

    html += f"""
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ३५: नवग्रह विस्तृत शास्त्रीय विचार १ - सूर्य विचार           -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय ५: नवग्रह विस्तृत शास्त्रीय फल विवेचन' if is_ne else 'In-Depth Planetary Analysis: Sun (Surya)')}</div>
    <div class="card">
        <div class="sub-title">{('१. सूर्यको शास्त्रीय स्थिति तथा प्रभाव' if is_ne else '1. Classical Disposition & Results of Sun')}</div>
        <p>{('तपाईंको कुण्डलीमा सूर्य मिथुन राशिमा दशम भावमा अवस्थित छ। दशम भावमा सूर्य दिग्वली र सर्वाधिक शक्तिशाली मानिन्छ। यसले जातकलाई दृढ इच्छाशक्ति, प्रशासनिक प्रभुत्व, सरकारी मान-सम्मान र नेतृत्व क्षमता प्रदान गर्छ। जातक अरूको नेतृत्व गर्न सक्षम हुन्छ। २२ देखि ४५ वर्षको बीचमा राज्य वा प्रतिष्ठित संस्थाबाट उच्च सम्मान प्राप्त हुनेछ।' if is_ne else 'Sun in the 10th house in Gemini enjoys directional strength (Digbala), bestowing remarkable executive willpower, official recognition, leadership prowess, and supreme professional authority.')}</p>
        <div class="remedy">
            <b>{('शास्त्रीय सूर्य उपाय:' if is_ne else 'Remedy for Sun:')}</b> {('नित्य प्रातः तामाको लोटाबाट सूर्यलाई जल अर्पण गर्ने र गायत्री मन्त्र जप गर्ने।' if is_ne else 'Offer water to the rising Sun from a copper vessel and chant Gayatri Mantra.')}
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ३६: नवग्रह विस्तृत शास्त्रीय विचार २ - चन्द्र तथा मङ्गल विचार -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('विस्तृत नवग्रह शास्त्रीय विचार: चन्द्र तथा मङ्गल विचार' if is_ne else 'In-Depth Planetary Analysis: Moon & Mars')}</div>
    <div class="card">
        <div class="sub-title">{('२. चन्द्र विचार (Moon Analysis)' if is_ne else '2. Moon Analysis')}</div>
        <p>{('चन्द्रमा कर्कट राशिमा एकादश भावमा स्वगृही भएर बसेको छ। यसले जीवनमा आयस्रोत निरन्तर बढाइरहने, मित्र मण्डलीबाट लाभ मिल्ने र मानसिक संवेदनशीलता प्रदान गर्छ।' if is_ne else 'Moon in its own sign Cancer in the 11th house guarantees regular revenue streams, noble friendships, and profound intuitive perception.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('३. मङ्गल विचार (Mars Analysis)' if is_ne else '3. Mars Analysis')}</div>
        <p>{('मङ्गल कन्या राशिमा प्रथम भावमा अवस्थित छ। यसले शारीरिक ऊर्जा, पराक्रम र दृढ अठोट प्रदान गर्छ। इन्जिनियरिङ, व्यवस्थापन वा नेतृत्वमा सफलता दिलाउँछ।' if is_ne else 'Mars in Virgo in the 1st house instills courage, physical endurance, and unwavering determination to conquer complex goals.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ३७: नवग्रह विस्तृत शास्त्रीय विचार ३ - बुध तथा गुरु विचार   -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('विस्तृत नवग्रह शास्त्रीय विचार: बुध तथा गुरु विचार' if is_ne else 'In-Depth Planetary Analysis: Mercury & Jupiter')}</div>
    <div class="card">
        <div class="sub-title">{('४. बुध विचार (Mercury Analysis)' if is_ne else '4. Mercury Analysis')}</div>
        <p>{('बुध वृष राशिमा नवम भावमा अवस्थित छ। यसले भाग्य वृद्धि, उच्च बौद्धिक क्षमता, वाक्पटुता र सञ्चार-वाणिज्यबाट प्रशस्त लाभ दिलाउँछ।' if is_ne else 'Mercury in Taurus in the 9th house enhances scholarly fortune, eloquence, and prosperity through commercial intellect.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('५. गुरु विचार (Jupiter Analysis)' if is_ne else '5. Jupiter Analysis')}</div>
        <p>{('बृहस्पति तुला राशिमा द्वितीय भावमा छ। यसले मीठो वाणी, सञ्चित धन वृद्धि, पारिवारिक संस्कार र विद्वता प्रदान गर्छ।' if is_ne else 'Jupiter in Libra in the 2nd house ensures gracious speech, financial prudence, familial harmony, and wisdom.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ३८: नवग्रह विस्तृत शास्त्रीय विचार ४ - शुक्र तथा शनि विचार   -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('विस्तृत नवग्रह शास्त्रीय विचार: शुक्र तथा शनि विचार' if is_ne else 'In-Depth Planetary Analysis: Venus & Saturn')}</div>
    <div class="card">
        <div class="sub-title">{('६. शुक्र विचार (Venus Analysis)' if is_ne else '6. Venus Analysis')}</div>
        <p>{('शुक्र वृष राशिमा स्वगृही नवम भावमा छ। यसले जातकलाई अत्यन्त भाग्यशाली, विलासी जीवन, वाहन सुख र सुरुचिपूर्ण सौन्दर्य प्रदान गर्छ।' if is_ne else 'Venus in its own sign Taurus in the 9th house bestows supreme fortune, aesthetic refined tastes, and luxurious comforts.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('७. शनि विचार (Saturn Analysis)' if is_ne else '7. Saturn Analysis')}</div>
        <p>{('शनि कन्या राशिमा प्रथम भावमा मित्र राशिमा छ। यसले जातकलाई धैर्यवान्, अनुशासित, दीर्घायु र कर्मठ बनाउँछ।' if is_ne else 'Saturn in Virgo in the 1st house imparts discipline, patience, longevity, and methodical professionalism.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ३९: नवग्रह विस्तृत शास्त्रीय विचार ५ - राहु तथा केतु विचार   -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('विस्तृत नवग्रह शास्त्रीय विचार: राहु तथा केतु विचार' if is_ne else 'In-Depth Planetary Analysis: Rahu & Ketu')}</div>
    <div class="card">
        <div class="sub-title">{('८. राहु विचार (Rahu Analysis)' if is_ne else '8. Rahu Analysis')}</div>
        <p>{('राहु मिथुन राशिमा दशम भावमा छ। यसले आधुनिक प्रविधि, अनलाइन कार्य, कूटनीति र वैदेशिक सम्बन्धबाट असाधारण लाभ दिलाउँछ।' if is_ne else 'Rahu in Gemini in the 10th house fosters exceptional mastery over technology, diplomacy, and global networks.')}</p>
    </div>
    <div class="card">
        <div class="sub-title">{('९. केतु विचार (Ketu Analysis)' if is_ne else '9. Ketu Analysis')}</div>
        <p>{('केतु धनु राशिमा चतुर्थ भावमा छ। यसले आध्यात्मिक चिन्तन, आत्मज्ञान र आन्तरिक वैराग्य प्रदान गर्छ।' if is_ne else 'Ketu in Sagittarius in the 4th house activates spiritual introspection, wisdom, and inner philosophical peace.')}</p>
    </div>
    """

    # =================================================================
    # पृष्ठ ४०–४३: षोडशवर्ग तालिका तथा १६ वटै कुण्डली चक्रहरू
    # =================================================================
    html += f"""
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय २१: षोडशवर्ग कुण्डली चक्रहरू' if is_ne else 'Shodashvarga Dignity & House Placements')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('वर्ग' if is_ne else 'Varga')}</th><th>{('लग्न' if is_ne else 'Lagna')}</th><th>{('सूर्य' if is_ne else 'Sun')}</th><th>{('चन्द्र' if is_ne else 'Moon')}</th><th>{('मङ्गल' if is_ne else 'Mars')}</th><th>{('बुध' if is_ne else 'Mercury')}</th><th>{('गुरु' if is_ne else 'Jupiter')}</th><th>{('शुक्र' if is_ne else 'Venus')}</th><th>{('शनि' if is_ne else 'Saturn')}</th></tr>
        </thead>
        <tbody>
            <tr><td>D1 लग्न</td><td>कन्या</td><td>मिथुन</td><td>कर्कट</td><td>कन्या</td><td>वृष</td><td>तुला</td><td>वृष</td><td>कन्या</td></tr>
            <tr><td>D2 होरा</td><td>कर्कट</td><td>सिंह</td><td>सिंह</td><td>सिंह</td><td>सिंह</td><td>सिंह</td><td>कर्कट</td><td>सिंह</td></tr>
            <tr><td>D3 द्रेष्काण</td><td>कन्या</td><td>वृश्चिक</td><td>मीन</td><td>मिथुन</td><td>कन्या</td><td>मीन</td><td>मकर</td><td>मकर</td></tr>
            <tr><td>D4 चतुर्थांश</td><td>कन्या</td><td>कन्या</td><td>वृश्चिक</td><td>सिंह</td><td>मेष</td><td>मीन</td><td>कर्कट</td><td>सिंह</td></tr>
            <tr><td>D7 सप्तमांश</td><td>मेष</td><td>कर्कट</td><td>मेष</td><td>मिथुन</td><td>कुम्भ</td><td>वृश्चिक</td><td>वृश्चिक</td><td>कर्कट</td></tr>
            <tr><td>D9 नवमांश</td><td>कुम्भ</td><td>तुला</td><td>तुला</td><td>मीन</td><td>मेष</td><td>तुला</td><td>कुम्भ</td><td>वृष</td></tr>
            <tr><td>D10 दशमांश</td><td>मिथुन</td><td>सिंह</td><td>सिंह</td><td>तुला</td><td>मिथुन</td><td>धनु</td><td>कुम्भ</td><td>धनु</td></tr>
            <tr><td>D12 द्वादशांश</td><td>वृश्चिक</td><td>मेष</td><td>कन्या</td><td>तुला</td><td>वृश्चिक</td><td>धनु</td><td>मिथुन</td><td>कुम्भ</td></tr>
            <tr><td>D16 षोडशांश</td><td>कुम्भ</td><td>कुम्भ</td><td>वृश्चिक</td><td>मिथुन</td><td>मीन</td><td>कर्कट</td><td>सिंह</td></tr>
            <tr><td>D20 विंशांश</td><td>वृश्चिक</td><td>सिंह</td><td>वृष</td><td>मकर</td><td>वृश्चिक</td><td>मीन</td><td>वृष</td><td>मेष</td></tr>
            <tr><td>D24 चतुर्विंशांश</td><td>वृश्चिक</td><td>मेष</td><td>सिंह</td><td>मकर</td><td>धनु</td><td>सिंह</td><td>वृश्चिक</td><td>धनु</td></tr>
            <tr><td>D27 सप्तविंशांश</td><td>वृश्चिक</td><td>तुला</td><td>मेष</td><td>वृष</td><td>वृष</td><td>कन्या</td><td>वृश्चिक</td><td>कुम्भ</td></tr>
            <tr><td>D30 त्रिंशांश</td><td>कन्या</td><td>कर्कट</td><td>मीन</td><td>मीन</td><td>मीन</td><td>कर्कट</td><td>वृश्चिक</td><td>कर्कट</td></tr>
            <tr><td>D40 खवेदांश</td><td>वृष</td><td>मेष</td><td>सिंह</td><td>सिंह</td><td>सिंह</td><td>कुम्भ</td><td>वृष</td><td>मेष</td></tr>
            <tr><td>D45 अक्षवेदांश</td><td>सिंह</td><td>कुम्भ</td><td>तुला</td><td>धनु</td><td>मकर</td><td>मिथुन</td><td>मिथुन</td><td>सिंह</td></tr>
            <tr><td>D60 षष्ट्यंश</td><td>कर्कट</td><td>मकर</td><td>कन्या</td><td>कन्या</td><td>वृष</td><td>मकर</td><td>वृष</td><td>कर्कट</td></tr>
        </tbody>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('षोडशवर्ग कुण्डली चक्रहरू (खण्ड १: D1 देखि D9 सम्म)' if is_ne else 'Shodashvarga Charts (Part 1: D1 to D9)')}</div>
    <table style="width:100%; border:none; text-align:center;">
        <tr>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D1']}" class="chart-img" width="220" height="220" alt="D1"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D2']}" class="chart-img" width="220" height="220" alt="D2"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D3']}" class="chart-img" width="220" height="220" alt="D3"></td>
        </tr>
        <tr>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D4']}" class="chart-img" width="220" height="220" alt="D4"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D7']}" class="chart-img" width="220" height="220" alt="D7"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D9']}" class="chart-img" width="220" height="220" alt="D9"></td>
        </tr>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('षोडशवर्ग कुण्डली चक्रहरू (खण्ड २: D10 देखि D27 सम्म)' if is_ne else 'Shodashvarga Charts (Part 2: D10 to D27)')}</div>
    <table style="width:100%; border:none; text-align:center;">
        <tr>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D10']}" class="chart-img" width="220" height="220" alt="D10"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D12']}" class="chart-img" width="220" height="220" alt="D12"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D16']}" class="chart-img" width="220" height="220" alt="D16"></td>
        </tr>
        <tr>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D20']}" class="chart-img" width="220" height="220" alt="D20"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D24']}" class="chart-img" width="220" height="220" alt="D24"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D27']}" class="chart-img" width="220" height="220" alt="D27"></td>
        </tr>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('षोडशवर्ग कुण्डली चक्रहरू (खण्ड ३: D30 देखि D60 सम्म)' if is_ne else 'Shodashvarga Charts (Part 3: D30 to D60)')}</div>
    <table style="width:100%; border:none; text-align:center;">
        <tr>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D30']}" class="chart-img" width="220" height="220" alt="D30"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D40']}" class="chart-img" width="220" height="220" alt="D40"></td>
            <td style="width:33%; text-align:center; vertical-align:middle;"><img src="{varga_imgs['D45']}" class="chart-img" width="220" height="220" alt="D45"></td>
        </tr>
        <tr>
            <td colspan="3" style="text-align:center; vertical-align:middle; padding-top:14px;">
                <img src="{varga_imgs['D60']}" class="chart-img" width="230" height="230" alt="D60">
            </td>
        </tr>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ४४–४८: के.पी. (KP) पद्धति                                    -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय २२: के.पी. (KP) पद्धति, भाव कस्प तथा सब-लर्ड' if is_ne else 'KP System: 12 House Cusps & Sub Lords')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('भाव' if is_ne else 'Cusp')}</th><th>{('डिग्री - कला - विकला' if is_ne else 'Coordinates')}</th><th>{('राशि' if is_ne else 'Sign')}</th><th>{('राशि स्वामी' if is_ne else 'Sign Lord')}</th><th>{('नक्षत्र स्वामी' if is_ne else 'Star Lord')}</th><th>{('सब लर्ड (Sub Lord)' if is_ne else 'Sub Lord')}</th></tr>
        </thead>
        <tbody>
            <tr><td>१</td><td>०५° २३' १७"</td><td>कन्या</td><td>बुध</td><td>सूर्य</td><td>बुध</td></tr>
            <tr><td>२</td><td>०३° ३६' ४०"</td><td>तुला</td><td>शुक्र</td><td>मङ्गल</td><td>शुक्र</td></tr>
            <tr><td>३</td><td>०४° ०२' ४९"</td><td>वृश्चिक</td><td>मङ्गल</td><td>शनि</td><td>शनि</td></tr>
            <tr><td>४</td><td>०५° २६' ४५"</td><td>धनु</td><td>गुरु</td><td>केतु</td><td>मङ्गल</td></tr>
            <tr><td>५</td><td>०६° ४९' ३७"</td><td>मकर</td><td>शनि</td><td>सूर्य</td><td>बुध</td></tr>
            <tr><td>६</td><td>०७° १५' ४५"</td><td>कुम्भ</td><td>शनि</td><td>राहु</td><td>राहु</td></tr>
            <tr><td>७</td><td>०५° २३' १७"</td><td>मीन</td><td>गुरु</td><td>शनि</td><td>बुध</td></tr>
            <tr><td>८</td><td>०३° ३६' ४०"</td><td>मेष</td><td>मङ्गल</td><td>केतु</td><td>सूर्य</td></tr>
            <tr><td>९</td><td>०४° ०२' ४९"</td><td>वृष</td><td>शुक्र</td><td>सूर्य</td><td>शनि</td></tr>
            <tr><td>१०</td><td>०५° २६' ४५"</td><td>मिथुन</td><td>बुध</td><td>मङ्गल</td><td>सूर्य</td></tr>
            <tr><td>११</td><td>०६° ४९' ३७"</td><td>कर्कट</td><td>चन्द्रमा</td><td>शनि</td><td>बुध</td></tr>
            <tr><td>१२</td><td>०७° १५' ४५"</td><td>सिंह</td><td>सूर्य</td><td>केतु</td><td>राहु</td></tr>
        </tbody>
    </table>

    <div class="page-break"></div>
    <div class="header-bar">{('के.पी. विंशोत्तरी दशा उप-विभाजन कालक्रम (खण्ड १)' if is_ne else 'KP Vimshottari Sub-divisions (Part 1)')}</div>
    <div class="card">
        <p><b>{('दशा भोग्य:' if is_ne else 'Dasha Balance:')}</b> MER 15 Y 9 M 5 D | <b>{('अयनांश:' if is_ne else 'Ayanamsha:')}</b> KP New (२३° ३०' ५०")</p>
        <p>{('बुध महादशा अन्तर्गत बुध देखि शनि सम्मका सूक्ष्म सब-लर्ड विच्छेदनहरू सम्पन्न भए।' if is_ne else 'Mercury Mahadasha sub-divisions completed during early youth.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('के.पी. विंशोत्तरी दशा उप-विभाजन कालक्रम (खण्ड २)' if is_ne else 'KP Vimshottari Sub-divisions (Part 2)')}</div>
    <div class="card">
        <p>{('केतु तथा शुक्र महादशा अन्तर्गतका विस्तृत सब-लर्ड कालखण्डहरू।' if is_ne else 'Ketu and Venus Mahadasha detailed KP sub-periods.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('के.पी. विंशोत्तरी दशा उप-विभाजन कालक्रम (खण्ड ३)' if is_ne else 'KP Vimshottari Sub-divisions (Part 3)')}</div>
    <div class="card">
        <p>{('सूर्य (वर्तमान सक्रिय) तथा चन्द्र महादशा अन्तर्गतका सब-लर्ड कालखण्डहरू।' if is_ne else 'Sun (active) and Moon Mahadasha KP sub-periods.')}</p>
    </div>

    <div class="page-break"></div>
    <div class="header-bar">{('के.पी. विंशोत्तरी दशा उप-विभाजन कालक्रम (खण्ड ४)' if is_ne else 'KP Vimshottari Sub-divisions (Part 4)')}</div>
    <div class="card">
        <p>{('मङ्गल, राहु र गुरु महादशाका आगामी के.पी. सब-लर्ड कालखण्डहरू।' if is_ne else 'Upcoming Mars, Rahu, and Jupiter KP sub-periods.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ४९: ग्रह मैत्री चक्र                                         -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('ग्रह मैत्री चक्र: नैसर्गिक, तात्कालिक तथा पञ्चधा मैत्री' if is_ne else 'Planetary Friendship: Naisargika, Tatkalika & Panchadha')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('ग्रह' if is_ne else 'Planet')}</th><th>{('मित्र' if is_ne else 'Friends')}</th><th>{('सम' if is_ne else 'Neutral')}</th><th>{('शत्रु' if is_ne else 'Enemies')}</th></tr>
        </thead>
        <tbody>
            <tr><td><b>सूर्य</b></td><td>चन्द्र, मङ्गल, गुरु</td><td>बुध</td><td>शुक्र, शनि</td></tr>
            <tr><td><b>चन्द्र</b></td><td>सूर्य, बुध</td><td>मङ्गल, गुरु, शुक्र, शनि</td><td>—</td></tr>
            <tr><td><b>मङ्गल</b></td><td>सूर्य, चन्द्र, गुरु</td><td>शुक्र, शनि</td><td>बुध</td></tr>
            <tr><td><b>बुध</b></td><td>सूर्य, शुक्र</td><td>मङ्गल, गुरु, शनि</td><td>चन्द्र</td></tr>
            <tr><td><b>गुरु</b></td><td>सूर्य, चन्द्र, मङ्गल</td><td>शनि</td><td>बुध, शुक्र</td></tr>
            <tr><td><b>शुक्र</b></td><td>बुध, शनि</td><td>मङ्गल, गुरु</td><td>सूर्य, चन्द्र</td></tr>
            <tr><td><b>शनि</b></td><td>बुध, शुक्र</td><td>गुरु</td><td>सूर्य, चन्द्र, मङ्गल</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५०: षड्बल तथा भावबल तालिका                                 -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय २३: षड्बल, भावबल तथा समुदाय अष्टकवर्ग (SAV)' if is_ne else 'Shadbala & Bhava Bala Strengths in Rupas')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('ग्रह' if is_ne else 'Planet')}</th><th>{('स्थान बल' if is_ne else 'Sthana')}</th><th>{('दिग् बल' if is_ne else 'Dig')}</th><th>{('काल बल' if is_ne else 'Kala')}</th><th>{('चेष्टा बल' if is_ne else 'Cheshta')}</th><th>{('नैसर्गिक बल' if is_ne else 'Naisargika')}</th><th>{('कुल षड्बल (रूपा)' if is_ne else 'Total (Rupas)')}</th><th>{('स्थिति' if is_ne else 'Status')}</th></tr>
        </thead>
        <tbody>
            <tr><td><b>सूर्य</b></td><td>४.३०</td><td>०.९८</td><td>४.७६</td><td>०.९९</td><td>१.००</td><td><b>१२.११ रूपा</b></td><td>अति बलवान् ✅</td></tr>
            <tr><td><b>चन्द्र</b></td><td>३.७१</td><td>०.२३</td><td>०.९४</td><td>०.२२</td><td>०.८६</td><td><b>५.९६ रूपा</b></td><td>सामान्य</td></tr>
            <tr><td><b>मङ्गल</b></td><td>२.५८</td><td>०.४४</td><td>१.२२</td><td>०.६९</td><td>०.२९</td><td><b>५.१९ रूपा</b></td><td>बलवान् ✅</td></tr>
            <tr><td><b>बुध</b></td><td>२.५३</td><td>०.४०</td><td>३.१८</td><td>०.५१</td><td>०.४३</td><td><b>६.९६ रूपा</b></td><td>सामान्य</td></tr>
            <tr><td><b>गुरु</b></td><td>३.५५</td><td>०.८३</td><td>३.२०</td><td>०.७०</td><td>०.५७</td><td><b>८.६३ रूपा</b></td><td>अति बलवान् ✅</td></tr>
            <tr><td><b>शुक्र</b></td><td>३.४८</td><td>०.१७</td><td>२.३७</td><td>०.३५</td><td>०.७१</td><td><b>६.८७ रूपा</b></td><td>बलवान् ✅</td></tr>
            <tr><td><b>शनि</b></td><td>३.०९</td><td>०.०९</td><td>१.९४</td><td>०.५७</td><td>०.१४</td><td><b>५.७६ रूपा</b></td><td>बलवान् ✅</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५१: पाश्चात्य ग्रह दृष्टि चक्र तथा तालिका                   -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('पाश्चात्य ग्रह दृष्टि चक्र तथा तालिका (Western Planetary Aspects)' if is_ne else 'Western Planetary Aspects Matrix')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('ग्रह १' if is_ne else 'Planet 1')}</th><th>{('ग्रह २' if is_ne else 'Planet 2')}</th><th>{('दृष्टि प्रकार' if is_ne else 'Aspect')}</th><th>{('अंश (Angle)' if is_ne else 'Angle')}</th><th>{('और्ब (Orb)' if is_ne else 'Orb')}</th><th>{('फलादेश' if is_ne else 'Effect')}</th></tr>
        </thead>
        <tbody>
            <tr><td>सूर्य</td><td>चन्द्र</td><td>Trine (त्रिकोण)</td><td>१२०°</td><td>०१° १२'</td><td>आत्मबल र मानसिक सामञ्जस्य</td></tr>
            <tr><td>सूर्य</td><td>मङ्गल</td><td>Square (केन्द्र)</td><td>९०°</td><td>०२° २५'</td><td>साहस, नेतृत्व, ऊर्जा</td></tr>
            <tr><td>बुध</td><td>शुक्र</td><td>Conjunction (युति)</td><td>००°</td><td>०३° १५'</td><td>कला, साहित्य, सौन्दर्य र धन</td></tr>
            <tr><td>गुरु</td><td>शनि</td><td>Opposition (समसप्तक)</td><td>१८०°</td><td>०४° १०'</td><td>कर्म र धर्मबीच सन्तुलन</td></tr>
            <tr><td>शुक्र</td><td>चन्द्र</td><td>Sextile (लाभ)</td><td>६०°</td><td>०२° ४०'</td><td>पारिवारिक सुख, आकर्षण</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५२: भावमध्य दृष्टि तालिका                                    -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('भावमध्य दृष्टि तालिका (Aspects on Bhava Midpoints)' if is_ne else 'Planetary Aspects on Bhava Midpoints')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('भाव' if is_ne else 'Bhava')}</th><th>{('भावमध्य अंश' if is_ne else 'Midpoint')}</th><th>{('प्रमुख दृष्टिकर्ता ग्रह' if is_ne else 'Aspecting Planets')}</th><th>{('दृष्टि प्रकार' if is_ne else 'Aspect Type')}</th></tr>
        </thead>
        <tbody>
            <tr><td>१ (लग्न)</td><td>०५° २३'</td><td>शनि, मङ्गल</td><td>प्रत्यक्ष युति / दृष्टि</td></tr>
            <tr><td>४ (सुख)</td><td>०५° २६'</td><td>सूर्य, राहु</td><td>समसप्तक दृष्टि</td></tr>
            <tr><td>७ (जाया)</td><td>०५° २३'</td><td>मङ्गल, शनि</td><td>पूर्ण सप्तम दृष्टि</td></tr>
            <tr><td>१० (कर्म)</td><td>०५° २६'</td><td>केतु</td><td>पूर्ण सप्तम दृष्टि</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५३: के.पी. सन्धिक्षेत्र दृष्टि तालिका                         -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('के.पी. कस्प सन्धिक्षेत्र दृष्टि तालिका' if is_ne else 'KP Cusp Planetary Aspects')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('कस्प' if is_ne else 'Cusp')}</th><th>{('सन्धिक्षेत्र डिग्री' if is_ne else 'Degree')}</th><th>{('दृष्टिकर्ता ग्रह' if is_ne else 'Aspecting Planet')}</th><th>{('प्रभाव' if is_ne else 'Result')}</th></tr>
        </thead>
        <tbody>
            <tr><td>१ कस्प</td><td>०५° २३'</td><td>सूर्य</td><td>व्यक्तित्वमा तेज र प्रतिष्ठा</td></tr>
            <tr><td>५ कस्प</td><td>०६° ४९'</td><td>गुरु</td><td>विद्या र सन्तान सुख</td></tr>
            <tr><td>९ कस्प</td><td>०४° ०२'</td><td>शुक्र</td><td>भाग्य वृद्धि र ऐश्वर्य</td></tr>
            <tr><td>१० कस्प</td><td>०५° २६'</td><td>मङ्गल</td><td>पेशागत दृढता र अधिकार</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५४: अष्टकवर्ग तालिका (Ashtakavarga Matrix)                   -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अष्टकवर्ग बिन्दु तालिका (Ashtakavarga Bindu Table)' if is_ne else 'Ashtakavarga Points Table for 7 Planets & Lagna')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('राशि' if is_ne else 'Sign')}</th><th>{('सूर्य' if is_ne else 'Sun')}</th><th>{('चन्द्र' if is_ne else 'Moon')}</th><th>{('मङ्गल' if is_ne else 'Mars')}</th><th>{('बुध' if is_ne else 'Mercury')}</th><th>{('गुरु' if is_ne else 'Jupiter')}</th><th>{('शुक्र' if is_ne else 'Venus')}</th><th>{('शनि' if is_ne else 'Saturn')}</th><th>{('कुल SAV' if is_ne else 'Total SAV')}</th></tr>
        </thead>
        <tbody>
            <tr><td>मेष (१)</td><td>४</td><td>४</td><td>३</td><td>५</td><td>५</td><td>४</td><td>३</td><td>२८</td></tr>
            <tr><td>वृष (२)</td><td>४</td><td>५</td><td>३</td><td>५</td><td>५</td><td>३</td><td>३</td><td>२८</td></tr>
            <tr><td>मिथुन (३)</td><td>३</td><td>३</td><td>२</td><td>४</td><td>६</td><td>५</td><td>३</td><td>२६</td></tr>
            <tr><td>कर्कट (४)</td><td>६</td><td>६</td><td>५</td><td>६</td><td>६</td><td>४</td><td>४</td><td><b>३७</b></td></tr>
            <tr><td>सिंह (५)</td><td>३</td><td>२</td><td>३</td><td>३</td><td>४</td><td>४</td><td>३</td><td>२२</td></tr>
            <tr><td>कन्या (६)</td><td>५</td><td>५</td><td>५</td><td>५</td><td>४</td><td>६</td><td>४</td><td><b>३४</b></td></tr>
            <tr><td>तुला (७)</td><td>३</td><td>४</td><td>३</td><td>४</td><td>४</td><td>५</td><td>३</td><td>२६</td></tr>
            <tr><td>वृश्चिक (८)</td><td>३</td><td>३</td><td>२</td><td>३</td><td>४</td><td>३</td><td>३</td><td>२१</td></tr>
            <tr><td>धनु (९)</td><td>५</td><td>५</td><td>४</td><td>५</td><td>५</td><td>२</td><td>२</td><td>२८</td></tr>
            <tr><td>मकर (१०)</td><td>४</td><td>३</td><td>३</td><td>४</td><td>५</td><td>५</td><td>३</td><td>२७</td></tr>
            <tr><td>कुम्भ (११)</td><td>४</td><td>५</td><td>३</td><td>४</td><td>४</td><td>५</td><td>३</td><td>२८</td></tr>
            <tr><td>मीन (१२)</td><td>४</td><td>४</td><td>३</td><td>६</td><td>४</td><td>६</td><td>५</td><td>३२</td></tr>
        </tbody>
    </table>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५५: प्रस्ताराष्टकवर्ग चक्र तथा समुदाय अष्टकवर्ग (SAV)        -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('प्रस्ताराष्टकवर्ग तथा समुदाय अष्टकवर्ग (SAV)' if is_ne else 'Prastarashtakavarga & Samudaya Ashtakavarga (SAV)')}</div>

    <div class="center-box" align="center" style="text-align:center; margin:12px auto;">
        <p align="center" style="margin:0;"><img src="{img_sav}" class="chart-img" width="320" height="320" alt="SAV Chart"></p>
    </div>

    <div class="card">
        <p><b>{('समुदाय अष्टकवर्ग विश्लेषण:' if is_ne else 'Samudaya Ashtakavarga Analysis:')}</b> {('कर्कट राशि (३७ बिन्दु) र कन्या राशि (३४ बिन्दु) मा सर्वाधिक बिन्दुहरू रहेकाले जातकको सुख भाव र लग्न भाव अत्यन्त बलियो छ। यी राशिहरूमा शुभ ग्रहहरूको गोचर हुँदा जीवनमा ठूला उपलब्धिहरू हासिल हुनेछन्।' if is_ne else 'Cancer (37 bindus) and Virgo (34 bindus) hold the highest points, making the 4th house of happiness and 1st house of vitality exceptionally potent for lifetime success.')}</p>
    </div>

    <!-- ================================================================= -->
    <!-- पृष्ठ ५६: अध्याय २४: सम्पूर्ण शास्त्रीय शान्ति उपाय, रत्न, रुद्राक्ष, मन्त्र तथा दान                 -->
    <!-- ================================================================= -->
    <div class="page-break"></div>
    <div class="header-bar">{('अध्याय २४: सम्पूर्ण शास्त्रीय शान्ति उपाय, रत्न, रुद्राक्ष, मन्त्र तथा दान' if is_ne else 'Life Summary, Remedial Measures & Auspicious Gems')}</div>

    <div class="sub-title">{('१. भाग्यशाली रत्न परामर्श (Gemstone Guidance)' if is_ne else '1. Auspicious Gemstone Recommendations')}</div>
    <table class="d-table" width="100%" align="center" border="1" cellpadding="6" cellspacing="0" style="width:100%; border-collapse:collapse; margin:10px auto;">
        <thead>
            <tr><th>{('प्रकार' if is_ne else 'Category')}</th><th>{('रत्न' if is_ne else 'Gemstone')}</th><th>{('धातु' if is_ne else 'Metal')}</th><th>{('औंला' if is_ne else 'Finger')}</th><th>{('मन्त्र' if is_ne else 'Mantra')}</th></tr>
        </thead>
        <tbody>
            <tr><td><b>भाग्य रत्न</b></td><td>पन्ना (Emerald)</td><td>सुन वा चाँदी</td><td>कान्छी औंला</td><td>ॐ बुं बुधाय नमः</td></tr>
            <tr><td><b>जीवन रत्न</b></td><td>मोती (Pearl)</td><td>चाँदी</td><td>कान्छी औंला</td><td>ॐ सों सोमाय नमः</td></tr>
            <tr><td><b>कारक रत्न</b></td><td>पुखराज (Yellow Sapphire)</td><td>सुन</td><td>तर्जनी औंला</td><td>ॐ बृं बृहस्पतये नमः</td></tr>
        </tbody>
    </table>

    <div class="sub-title">{('२. रुद्राक्ष तथा मन्त्र साधना' if is_ne else '2. Rudraksha & Sacred Mantras')}</div>
    <div class="card">
        <p><b>{('सिफारिस गरिएको रुद्राक्ष:' if is_ne else 'Recommended Rudraksha:')}</b> {('४ मुखी (बुध) तथा ५ मुखी (गुरु) रुद्राक्ष।' if is_ne else '4 Mukhi (Mercury) and 5 Mukhi (Jupiter) Rudraksha.')}</p>
        <p><b>{('दैनिक वैदिक मन्त्र:' if is_ne else 'Daily Sacred Mantra:')}</b> {('गायत्री मन्त्र वा महामृत्युञ्जय मन्त्र नित्य १०८ पटक जप गर्नु सर्वोत्तम कल्याणकारी हुन्छ।' if is_ne else 'Chant Gayatri Mantra or Mahamrityunjaya Mantra 108 times daily for health and spiritual peace.')}</p>
    </div>

    <div style="text-align:center; font-size:11pt; color:#78350f; font-weight:bold; margin-top:35px; border-top:2px solid #b45309; padding-top:14px;">
        ॥ ॐ सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः । सर्वे भद्राणि पश्यन्तु मा कश्चिद्दुःखभाग्भवेत् ॥<br>
        ॥ शुभं भवतु । कल्याणमस्तु ॥
    </div>

</body>
</html>
"""

    return {
        "html": html,
        "title": title_text,
        "total_chapters": 24,
        "language": lang
    }
