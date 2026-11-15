"""
gui/widgets/panchang_info.py
Detailed Panchang with interactive Bikram Sambat Calendar, Sankalpa Shloka generator, and full daily panchang details.
"""
from __future__ import annotations
import sys, os
from typing import Callable, Optional
import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QScrollArea, QPushButton, QDateEdit, QComboBox, QSizePolicy
)
from PySide6.QtCore import QObject, QDate, QThread, Qt, Signal

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY)
from gui.utils.bs_calendar import (
    gregorian_to_bs, bs_to_gregorian, format_bs_date, to_nepali_digits,
    bs_month_length, BS_MONTHS_NE, BS_MONTHS_EN, get_today_bs
)

UNAVAILABLE = "—"
DAILY_PANCHANG_LOCATION = {
    "city": "Kathmandu",
    "latitude": 27.7172,
    "longitude": 85.3240,
    "timezone": 5.75,
}
SECTION_ORDER = ["samvat", "panchang", "sun_day", "special_day", "sunrise_planets"]
PANCHANG_PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]
PLANET_NAMES_EN = {name: name for name in PANCHANG_PLANET_ORDER}
PLANET_NAMES_NE = {"Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल", "Mercury": "बुध", "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"}
SIGN_NAMES_EN = {1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"}
SIGN_NAMES_NE = {1: "मेष", 2: "वृष", 3: "मिथुन", 4: "कर्कट", 5: "सिंह", 6: "कन्या", 7: "तुला", 8: "वृश्चिक", 9: "धनु", 10: "मकर", 11: "कुम्भ", 12: "मीन"}
SANSKRIT_WEEKDAYS = {
    "आइतबार": "भानु", "Sunday": "भानु",
    "सोमबार": "सोम", "Monday": "सोम",
    "मंगलबार": "भौम", "Tuesday": "भौम",
    "बुधबार": "सौम्य", "Wednesday": "सौम्य",
    "बिहीबार": "बृहस्पति", "Thursday": "बृहस्पति",
    "शुक्रबार": "भृगु", "Friday": "भृगु",
    "शनिबार": "स्थिर", "Saturday": "स्थिर",
}
SANSKRIT_SEASONS = {
    "वसन्त": "वसन्त", "Spring": "वसन्त",
    "ग्रीष्म": "ग्रीष्म", "Summer": "ग्रीष्म",
    "वर्षा": "वर्ष", "Monsoon": "वर्ष",
    "शरद": "शरद्", "Autumn": "शरद्",
    "हेमन्त": "हेमन्त", "Hemant": "हेमन्त",
    "शिशिर": "शिशिर", "Winter": "शिशिर",
}


def _sunrise_time(payload: dict) -> str:
    requested = payload.get("panchang_requested_day") if isinstance(payload, dict) else {}
    panchang = requested.get("panchang") if isinstance(requested, dict) else {}
    sunrise = panchang.get("sunrise") if isinstance(panchang, dict) else None
    value = sunrise.get("time") if isinstance(sunrise, dict) else sunrise
    text = str(value or "05:38").strip()
    parts = text.split(":")
    try:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
    except (IndexError, TypeError, ValueError):
        return "05:38:00"


def _read_siddhanta_from_settings() -> str:
    """Read calculation_siddhanta from QSettings (set by SettingsDialog)."""
    try:
        from PySide6.QtCore import QSettings
        s = QSettings("ShivramJyotish", "Desktop")
        return str(s.value("calculation_siddhanta", "DRIK") or "DRIK")
    except Exception:
        return "DRIK"


def daily_panchang_params(
    selected_date: datetime.date,
    ayanamsha_type: str = "LAHIRI",
    node_type: str = "MEAN",
    house_system: str = "WHOLE_SIGN",
    calculation_siddhanta: str = "DRIK",
) -> dict:
    """Build the civil-day request used by the Web Detailed Panchang."""
    return {
        "name": "Daily Panchang",
        "birth_date": selected_date.isoformat(),
        "birth_time": "12:00:00",
        **DAILY_PANCHANG_LOCATION,
        "ayanamsha_type": ayanamsha_type or "LAHIRI",
        "node_type": node_type or "MEAN",
        "house_system": house_system or "WHOLE_SIGN",
        "calculation_siddhanta": calculation_siddhanta or "DRIK",
    }


_DAILY_PANCHANG_CACHE: dict[tuple, dict] = {}


def calculate_daily_panchang(
    selected_date: datetime.date,
    ayanamsha_type: str = "LAHIRI",
    node_type: str = "MEAN",
    house_system: str = "WHOLE_SIGN",
    calculator: Optional[Callable[..., dict]] = None,
    calculation_siddhanta: str = "DRIK",
) -> dict:
    """Calculate the selected civil day, then recalculate planets at its sunrise."""
    cache_key = (selected_date.isoformat(), str(ayanamsha_type), str(node_type), str(house_system), str(calculation_siddhanta))
    if calculator is None and cache_key in _DAILY_PANCHANG_CACHE:
        return _DAILY_PANCHANG_CACHE[cache_key]

    if calculator is None:
        from gui.backend_bridge import calculate_chart
        calculator = calculate_chart
    noon_params = daily_panchang_params(selected_date, ayanamsha_type, node_type, house_system, calculation_siddhanta)
    day_result = calculator(**noon_params)
    sunrise_params = {
        **noon_params,
        "name": "Daily Panchang Sunrise Positions",
        "birth_time": _sunrise_time(day_result),
    }
    sunrise_result = calculator(**sunrise_params)
    merged = {**day_result, "planets": sunrise_result.get("planets") or []}
    merged["daily_panchang_context"] = {
        "report_type": "requested_day",
        "selected_date": selected_date.isoformat(),
        "location": dict(DAILY_PANCHANG_LOCATION),
        "noon_request": noon_params,
        "sunrise_request": sunrise_params,
        "calculation_siddhanta": calculation_siddhanta,
    }
    _DAILY_PANCHANG_CACHE[cache_key] = merged
    return merged


class DailyPanchangWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, selected_date: datetime.date, ayanamsha: str, node_type: str, house_system: str, calculation_siddhanta: str = "DRIK"):
        super().__init__()
        self._args = (selected_date, ayanamsha, node_type, house_system)
        self._siddhanta = calculation_siddhanta

    def run(self) -> None:
        try:
            self.finished.emit(calculate_daily_panchang(*self._args, calculation_siddhanta=self._siddhanta))
        except Exception as exc:
            self.error.emit(str(exc))


def _value(value):
    if isinstance(value, dict):
        return (
            value.get("time")
            or value.get("nepali")
            or value.get("name")
            or value.get("year")
            or UNAVAILABLE
        )
    return value if value not in (None, "") else UNAVAILABLE


def _samvat_value(value: object, language: str) -> str:
    if isinstance(value, dict):
        year_value = value.get("year")
        if year_value in (None, ""):
            return UNAVAILABLE
        year = str(year_value)
        era = str(value.get("era") or "").strip()
        if language == "ne":
            year = to_nepali_digits(year)
        return f"{year} ({era})" if era else year
    if value in (None, ""):
        return UNAVAILABLE
    text = str(value).strip()
    return to_nepali_digits(text) if language == "ne" else text


def _date_derived_values(date_value: Optional[datetime.date], bs: Optional[dict], sun: dict, language: str) -> dict:
    """Derive calendar labels from the selected date and calculated sunrise Sun."""
    is_ne = language == "ne"
    shaka = date_value.year - 78 if date_value is not None else None
    sun_sign = sun.get("sign_number") if isinstance(sun, dict) else None
    try:
        sun_sign = int(sun_sign)
    except (TypeError, ValueError):
        sun_sign = None
    ayana = None
    if sun_sign is not None:
        ayana = (
            ("उत्तरायण" if is_ne else "Uttarayan")
            if sun_sign >= 10 or sun_sign <= 3
            else ("दक्षिणायन" if is_ne else "Dakshinayan")
        )
    month = bs.get("month") if isinstance(bs, dict) else None
    seasons = (
        ["वसन्त", "ग्रीष्म", "ग्रीष्म", "वर्षा", "वर्षा", "शरद", "शरद", "हेमन्त", "हेमन्त", "शिशिर", "शिशिर", "वसन्त"]
        if is_ne
        else ["Spring", "Summer", "Summer", "Monsoon", "Monsoon", "Autumn", "Autumn", "Hemant", "Hemant", "Winter", "Winter", "Spring"]
    )
    season = seasons[month - 1] if isinstance(month, int) and 1 <= month <= 12 else UNAVAILABLE
    shaka_text = UNAVAILABLE if shaka is None else (to_nepali_digits(shaka) if is_ne else str(shaka))
    return {"shaka": shaka_text, "shaka_raw": shaka, "ayana": ayana or UNAVAILABLE, "season": season}


def _localized(item: dict, language: str, *, birth: bool = False):
    if not isinstance(item, dict):
        return _value(item)
    if birth:
        key = "birth_nepali" if language == "ne" else "birth_name"
        if item.get(key):
            return item[key]
    key = "nepali" if language == "ne" else "name"
    return item.get(key) or item.get("name") or UNAVAILABLE


def _limb_value(item: dict, language: str) -> str:
    # For karana in SURYA_SIDDHANTA mode, use the pre-formatted 3-part Patro string.
    if isinstance(item, dict):
        full_key = "full_nepali" if language == "ne" else "full_name"
        full_val = item.get(full_key)
        if full_val:
            return str(full_val)
    name = _localized(item, language)
    end = item.get("end_time") if isinstance(item, dict) else None
    next_name = ""
    if isinstance(item, dict):
        next_name = item.get("next_nepali" if language == "ne" else "next_name") or item.get("next_name") or ""
    if end and next_name:
        time_str = str(end)[:5]
        time_disp = to_nepali_digits(time_str) if language == "ne" else time_str
        suffix = f"{time_disp} {'बजेपछि' if language == 'ne' else 'after'} {next_name}"
        return f"{name}, {suffix}"
    return str(name)


def _planet_position(planet: dict) -> str:
    try:
        sign = max(0, int(planet.get("sign_number", 1)) - 1)
        longitude = float(planet.get("longitude_in_sign", 0))
        degree = int(longitude)
        minute_float = (longitude - degree) * 60
        minute = int(minute_float)
        second = round((minute_float - minute) * 60)
        s_str = to_nepali_digits(f"{sign:02d}")
        d_str = to_nepali_digits(f"{degree:02d}")
        m_str = to_nepali_digits(f"{minute:02d}")
        sec_str = to_nepali_digits(f"{second:02d}")
        return f"{s_str}|{d_str}|{m_str}|{sec_str}"
    except (TypeError, ValueError):
        return UNAVAILABLE


def _dict_or_str_val(obj, key="nepali", fallback=""):
    if isinstance(obj, dict):
        return obj.get(key) or obj.get("name") or fallback
    if isinstance(obj, str) and obj:
        return obj
    return fallback


def _sankalpa_limb_str(item: dict, limb_type: str) -> str:
    """Format limb with transition time if present (e.g. एकादशी, २८:३४ बजे उपरान्त द्वादशीत्तिथौ)."""
    if not isinstance(item, dict):
        base = str(item or "")
        suffix_map = {"tithi": "त्तिथौ", "nakshatra": " नक्षत्रे", "yoga": " योगे", "karana": " करणे"}
        return f"{base}{suffix_map.get(limb_type, '')}"

    name = item.get("nepali") or item.get("name") or ""
    if limb_type == "tithi":
        name = name.replace(" (Pratipada)", "").replace("Pratipada", "").strip()
        if name in ("प्रतिपदा", "प्रतिप"):
            name = "प्रतिप"

    end_time = item.get("end_time")
    next_name = item.get("next_nepali") or item.get("next_name") or ""
    if next_name and limb_type == "tithi":
        next_name = next_name.replace(" (Pratipada)", "").replace("Pratipada", "").strip()
        if next_name in ("प्रतिपदा", "प्रतिप"):
            next_name = "प्रतिप"

    if end_time and next_name:
        time_ne = to_nepali_digits(str(end_time)[:5])
        if limb_type == "tithi":
            return f"{name}, {time_ne} बजे उपरान्त {next_name}त्तिथौ"
        elif limb_type == "nakshatra":
            return f"{name}, {time_ne} बजे उपरान्त {next_name} नक्षत्रे"
        elif limb_type == "yoga":
            return f"{name}, {time_ne} बजे उपरान्त {next_name} योगे"
        elif limb_type == "karana":
            return f"{name}, {time_ne} बजे उपरान्त {next_name} करणे"

    suffix_map = {"tithi": "त्तिथौ", "nakshatra": " नक्षत्रे", "yoga": " योगे", "karana": " करणे"}
    return f"{name}{suffix_map.get(limb_type, '')}"


def build_sankalpa_shloka(data: dict, bs: dict, date_val: datetime.date) -> str:
    """Generate traditional Sanskrit Sankalpa Shloka dynamically from panchang."""
    p = data.get("panchang_requested_day", {}).get("panchang") or data.get("panchang") or {}
    
    # Location
    location_str = "नेपालदेशे लुम्बिनीप्रदेशे कपिलवस्तु मण्डले तौलिहवा नगरे"
    
    # Samvat & Shaka
    bs_year = to_nepali_digits(bs.get("year", 2083))
    shaka_year = to_nepali_digits(date_val.year - 78)
    
    # Samvatsara
    samvatsara_name = _dict_or_str_val(p.get("samvatsara"), fallback="रौद्र")
    
    # Ayana
    sun = next((item for item in (data.get("planets") or []) if item.get("name") == "Sun"), {})
    sun_sign = int(sun.get("sign_number", 1)) if sun.get("sign_number") else 5
    ayana = "दक्षिणायने" if 4 <= sun_sign <= 9 else "उत्तरायणे"
    
    # Season & Month
    bs_month_idx = bs.get("month", 5)
    month_names = ["वैशाख", "ज्येष्ठ", "आषाढ", "श्रावण", "भाद्र", "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन", "चैत्र"]
    bs_month_name = month_names[bs_month_idx - 1] if 1 <= bs_month_idx <= 12 else "भाद्र"
    
    season_map = {1: "वसन्त", 2: "ग्रीष्म", 3: "ग्रीष्म", 4: "वर्ष", 5: "वर्ष", 6: "शरद्", 7: "शरद्", 8: "हेमन्त", 9: "हेमन्त", 10: "शिशिर", 11: "शिशिर", 12: "वसन्त"}
    season_name = season_map.get(bs_month_idx, "वर्ष")
    
    # Limbs
    tithi_obj = p.get("tithi") or {}
    paksha_raw = _dict_or_str_val(tithi_obj, "paksha_nepali", fallback="शुक्ल")
    paksha = "शुक्ल" if "शुक्ल" in str(paksha_raw) else "कृष्ण"
    
    tithi_part = _sankalpa_limb_str(tithi_obj, "tithi")
    vara_name = _dict_or_str_val(p.get("vara"), fallback="आइतबार")
    vara_sanskrit = SANSKRIT_WEEKDAYS.get(vara_name, "भानु") + "वासरे"
    nakshatra_part = _sankalpa_limb_str(p.get("nakshatra") or {}, "nakshatra")
    yoga_part = _sankalpa_limb_str(p.get("yoga") or {}, "yoga")
    karana_part = _sankalpa_limb_str(p.get("karana") or {}, "karana")
    
    shloka = (
        "ॐ विष्णुर्विष्णुर्विष्णुः।<br>"
        f"अद्य श्रीब्रह्मणो द्वितीयपरार्धे श्रीश्वेतवाराहकल्पे वैवस्वतमन्वन्तरे अष्टाविंशतितमे कलियुगे कलिप्रथमचरणे जम्बूद्वीपे भारतवर्षे भरतखण्डे आर्यावर्तैकदेशे {location_str}<br>"
        f"श्रीविक्रमसंवत् <b style='color:#7c3d00;'>{bs_year}</b> तमे वर्षे श्रीशालिवाहनशके <b style='color:#7c3d00;'>{shaka_year}</b> तमे वर्षे, श्रीविक्रमानुसारिणि प्रभवादिषष्टिसंवत्सराणां मध्ये <b style='color:#7c3d00;'>{samvatsara_name}</b> नाम संवत्सरे, <b style='color:#7c3d00;'>{ayana}</b>, <b style='color:#7c3d00;'>{season_name}र्तौ</b>, <b style='color:#7c3d00;'>{bs_month_name}मासे</b>, <b style='color:#7c3d00;'>{paksha}पक्षे</b>, <b style='color:#7c3d00;'>{tithi_part}</b>, <b style='color:#7c3d00;'>{vara_sanskrit}</b>, <b style='color:#7c3d00;'>{nakshatra_part}</b>, <b style='color:#7c3d00;'>{yoga_part}</b>, <b style='color:#7c3d00;'>{karana_part}</b>,<br>"
        "एवं गुणविशेषणविशिष्टायां शुभपुण्यतिथौ ममोपात्तसमस्तदुरितक्षयद्वारा श्रीपरमेश्वरप्रीत्यर्थं पान्चायन पुजन कर्म करिष्ये॥"
    )
    return shloka


def build_panchang_model(data: Optional[dict], language: str = "ne") -> dict:
    """Build the Web-aligned daily report from the selected date and calculation payload."""
    is_ne = language == "ne"
    if data is None:
        return {"state": "no_chart", "message": "कुण्डली गणना गर्नुहोस्।" if is_ne else "Calculate a chart to view Panchang.", "sections": []}
    if not isinstance(data, dict):
        return {"state": "error", "message": "अमान्य पञ्चाङ्ग विवरण।" if is_ne else "Invalid Panchang data.", "sections": []}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"]), "sections": []}
    requested_day = data.get("panchang_requested_day")
    if requested_day is not None and not isinstance(requested_day, dict):
        return {"state": "error", "message": "अमान्य पञ्चाङ्ग विवरण।" if is_ne else "Invalid Panchang data.", "sections": []}
    p = (requested_day or {}).get("panchang") or data.get("panchang")
    if p is None:
        return {"state": "empty", "message": "पञ्चाङ्ग उपलब्ध छैन।" if is_ne else "Panchang is not available.", "sections": []}
    if not isinstance(p, dict):
        return {"state": "error", "message": "अमान्य पञ्चाङ्ग विवरण।" if is_ne else "Invalid Panchang data.", "sections": []}
    meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    daily_context = data.get("daily_panchang_context") if isinstance(data.get("daily_panchang_context"), dict) else {}
    selected_date = str(daily_context.get("selected_date") or meta.get("birth_date") or UNAVAILABLE)
    ad_date = selected_date
    bs_date = UNAVAILABLE
    date_value = None
    bs = None
    try:
        date_value = datetime.date.fromisoformat(selected_date[:10])
        ad_date = date_value.strftime("%d %b %Y")
        bs = gregorian_to_bs(date_value.year, date_value.month, date_value.day)
        if bs:
            bs_date = format_bs_date(bs, language)
    except (TypeError, ValueError):
        pass
    tithi = p.get("tithi") if isinstance(p.get("tithi"), dict) else {}
    vara = p.get("vara") if isinstance(p.get("vara"), dict) else {}
    planets = data.get("planets") if isinstance(data.get("planets"), list) else []
    sun = next((item for item in planets if isinstance(item, dict) and item.get("name") == "Sun"), {})
    moon = next((item for item in planets if isinstance(item, dict) and item.get("name") == "Moon"), {})
    moon_sign = p.get("moon_sign") if isinstance(p.get("moon_sign"), dict) else {}
    if not moon_sign:
        try:
            moon_sign_number = int(moon.get("sign_number"))
        except (TypeError, ValueError):
            moon_sign_number = None
        if moon_sign_number in SIGN_NAMES_EN:
            moon_sign = {
                "name": SIGN_NAMES_EN[moon_sign_number],
                "nepali": SIGN_NAMES_NE[moon_sign_number],
            }
    derived = _date_derived_values(date_value, bs if isinstance(bs, dict) else None, sun, language)
    labels = {
        "samvat": "संवत् विवरण" if is_ne else "Samvat Details",
        "panchang": "पञ्चाङ्ग" if is_ne else "Panchang (Five Limbs)",
        "sun_day": "सूर्य तथा दिनमान" if is_ne else "Sun & Day Duration",
        "special_day": "दिन विशेष" if is_ne else "Special Day",
        "sunrise_planets": "सूर्योदयकालीन स्पष्टग्रह" if is_ne else "Planetary Positions at Sunrise",
    }
    
    sections = [
        {"key": "samvat", "title": labels["samvat"], "accent": "#1d4ed8", "rows": [
            {"key": "bs_date", "label": "वि.सं." if is_ne else "Bikram Sambat", "value": bs_date},
            {"key": "ad_date", "label": "इ.सन्" if is_ne else "AD Date", "value": ad_date},
            {"key": "shaka", "label": "शक संवत्" if is_ne else "Shaka Samvat", "value": derived["shaka"]},
            {"key": "nepal_samvat", "label": "नेपाल संवत्" if is_ne else "Nepal Samvat", "value": _samvat_value(p.get("nepal_samvat"), language)},
            {"key": "samvatsara", "label": "संवत्सर" if is_ne else "Samvatsara", "value": _localized(p.get("samvatsara"), language)},
            {"key": "ayana", "label": "अयन" if is_ne else "Ayana", "value": derived["ayana"]},
            {"key": "season", "label": "ऋतु" if is_ne else "Season", "value": derived["season"]},
            {"key": "weekday", "label": "वार" if is_ne else "Weekday", "value": _localized(vara, language)},
            {"key": "paksha", "label": "पक्ष" if is_ne else "Paksha", "value": tithi.get("paksha_nepali" if is_ne else "paksha") or tithi.get("paksha") or UNAVAILABLE},
        ]},
        {"key": "panchang", "title": labels["panchang"], "accent": "#7c3aed", "rows": [
            {"key": "tithi", "label": "तिथि" if is_ne else "Tithi", "value": _limb_value(tithi, language)},
            {"key": "nakshatra", "label": "नक्षत्र" if is_ne else "Nakshatra", "value": _limb_value(p.get("nakshatra") or {}, language)},
            {"key": "yoga", "label": "योग" if is_ne else "Yoga", "value": _limb_value(p.get("yoga") or {}, language)},
            {"key": "karana", "label": "करण" if is_ne else "Karana", "value": _limb_value(p.get("karana") or {}, language)},
            {"key": "moon_sign", "label": "चन्द्रराशि" if is_ne else "Moon Sign", "value": _localized(moon_sign, language)},
        ]},
        {"key": "sun_day", "title": labels["sun_day"], "accent": "#ea580c", "rows": [
            {"key": "day_duration", "label": "दिनमान" if is_ne else "Day Duration", "value": (
                f"{to_nepali_digits(p.get('dinman_ghati', '')) if is_ne else p.get('dinman_ghati', '')} "
                f"({_value(p.get('dinman'))})"
                if p.get('dinman_ghati') else _value(p.get('dinman') or p.get('day_duration'))
            )},
            {"key": "sunrise", "label": "सूर्योदय" if is_ne else "Sunrise", "value": _value(p.get("sunrise"))},
            {"key": "sunset", "label": "सूर्यास्त" if is_ne else "Sunset", "value": _value(p.get("sunset"))},
        ]},
    ]
    anandadi = p.get("anandadi_yoga")
    if anandadi:
        sections[1]["rows"].append({"key": "anandadi_yoga", "label": "योग (आनन्दादि)" if is_ne else "Yoga (Anandadi)", "value": _localized(anandadi, language)})
    special = p.get("din_vishesh") or p.get("special_day") or p.get("special_note")
    if special:
        sections.append({"key": "special_day", "title": labels["special_day"], "accent": "#db2777", "rows": [{"key": "special_day", "label": labels["special_day"], "value": str(special)}]})
    # Detect if we are in SURYA_SIDDHANTA mode (has pre-formatted planetary_positions dict)
    ss_positions = p.get("planetary_positions") if isinstance(p.get("planetary_positions"), dict) else None
    is_ss_mode = ss_positions is not None

    planet_rows = []
    names = PLANET_NAMES_NE if is_ne else PLANET_NAMES_EN
    if is_ss_mode:
        # Use Surya Siddhanta's own formatted positions (authoritative source)
        ss_planet_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        for name in ss_planet_order:
            pp = ss_positions.get(name)
            if pp and isinstance(pp, dict):
                formatted = pp.get("formatted") if is_ne else pp.get("formatted_en", pp.get("formatted"))
                label = names.get(name, name)
                planet_rows.append({"key": name.lower(), "label": label, "value": str(formatted or UNAVAILABLE)})
    else:
        for name in PANCHANG_PLANET_ORDER:
            planet = next((item for item in planets if isinstance(item, dict) and item.get("name") == name), None)
            if planet:
                planet_rows.append({"key": name.lower(), "label": names[name], "value": _planet_position(planet)})

    if planet_rows:
        # Use pre-formatted Kranti/Belantar strings from panchang (in SS mode these are Nepali formatted)
        kranti_fmt = p.get("kranti") or p.get("velantara")
        belantar_fmt = p.get("belantar") or p.get("velantara")
        # belantar key takes priority for equation of time, kranti is declination
        kranti_fmt = p.get("kranti")
        belantar_fmt = p.get("belantar") or p.get("velantara")
        if kranti_fmt:
            planet_rows.append({"key": "declination", "label": "क्रान्ति" if is_ne else "Declination", "value": str(kranti_fmt)})
        elif p.get("sun_declination") is not None:
            decl_raw = p.get("sun_declination")
            planet_rows.append({"key": "declination", "label": "क्रान्ति" if is_ne else "Declination", "value": str(decl_raw)})
        if belantar_fmt:
            planet_rows.append({"key": "equation_of_time", "label": "वेलान्तर" if is_ne else "Equation of Time", "value": str(belantar_fmt)})
        elif p.get("equation_of_time") is not None:
            eot_raw = p.get("equation_of_time")
            planet_rows.append({"key": "equation_of_time", "label": "वेलान्तर" if is_ne else "Equation of Time", "value": str(eot_raw)})
        sections.append({"key": "sunrise_planets", "title": labels["sunrise_planets"], "accent": "#16a34a", "columns": ["Planet", "Sign|Deg|Min|Sec"], "rows": planet_rows})
    
    # Generate Sankalpa Shloka
    sankalpa = build_sankalpa_shloka(data, bs or {"year": 2083, "month": 5, "day": 7}, date_value or datetime.date.today())
    
    return {"state": "ready", "message": "", "sections": sections, "bs": bs, "date_value": date_value, "sankalpa": sankalpa, "panchang": p}


class PanchangInfoPage(QWidget):
    def __init__(
        self,
        data: Optional[dict] = None,
        language: str = "ne",
        parent=None,
        *,
        auto_calculate: bool = False,
        show_initial_data: bool = True,
        ayanamsha_type: str = "LAHIRI",
        node_type: str = "MEAN",
        house_system: str = "WHOLE_SIGN",
    ):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._ayanamsha = str(ayanamsha_type or "LAHIRI")
        self._node_type = str(node_type or "MEAN")
        self._house_system = str(house_system or "WHOLE_SIGN")
        # Read calculation siddhanta from QSettings (user preference set in SettingsDialog)
        self._calculation_siddhanta = _read_siddhanta_from_settings()
        self._daily_thread: Optional[QThread] = None
        self._daily_worker: Optional[DailyPanchangWorker] = None
        self._auto_calculation_pending = auto_calculate
        self._selected_bs_year = 2083
        self._selected_bs_month = 6
        self._selected_bs_day = 3
        self._updating_calendar = False
        self._build_ui()
        self.refresh(data if show_initial_data else None)
        # Trigger auto-calculation if requested (e.g., for report_panchang view)
        if auto_calculate:
            self._trigger_date_calculation()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 10, 14, 10)
        root_layout.setSpacing(12)

        # ── Title & Hidden/Compatibility controls (required by existing tests) ──
        self._date_edit = QDateEdit(QDate.currentDate())
        self._date_edit.setObjectName("dailyPanchangDate")
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setVisible(False)
        self._date_edit.dateChanged.connect(self._on_qdate_changed)
        root_layout.addWidget(self._date_edit)

        self._bs_date_label = QLabel()
        self._bs_date_label.setObjectName("dailyPanchangBsDate")
        self._bs_date_label.setVisible(False)
        root_layout.addWidget(self._bs_date_label)

        self._today_button = QPushButton("आज" if self._is_ne else "Today")
        self._today_button.setObjectName("dailyPanchangToday")
        self._today_button.setVisible(False)
        self._today_button.clicked.connect(self._select_today)
        root_layout.addWidget(self._today_button)

        self._calculate_button = QPushButton("पञ्चाङ्ग हेर्नुहोस्" if self._is_ne else "Show Panchang")
        self._calculate_button.setObjectName("dailyPanchangCalculate")
        self._calculate_button.setVisible(False)
        self._calculate_button.clicked.connect(self.calculate_selected_date)
        root_layout.addWidget(self._calculate_button)

        # ── Scroll Area for Calendar + Panchang Report ────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        root_layout.addWidget(scroll, 1)

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet(f"background: {BG_PRIMARY};")
        self._main_layout = QVBoxLayout(self._scroll_content)
        self._main_layout.setContentsMargins(0, 0, 4, 0)
        self._main_layout.setSpacing(14)
        scroll.setWidget(self._scroll_content)

        # ── 1. BIKRAM SAMBAT CALENDAR CARD ───────────────────────────────────
        self._cal_card = QFrame()
        self._cal_card.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; }")
        cal_box = QVBoxLayout(self._cal_card)
        cal_box.setContentsMargins(14, 10, 14, 10)
        cal_box.setSpacing(8)

        # Top Bar: Title, Year Dropdown, Month Dropdown, Location
        cal_top = QHBoxLayout()
        
        cal_title_box = QVBoxLayout()
        cal_title_box.setSpacing(1)
        cal_title = QLabel("बिक्रम सम्बत क्यालेन्डर" if self._is_ne else "Bikram Sambat Calendar")
        cal_title.setStyleSheet("color: #1d4ed8; font-size: 14px; font-weight: 700;")
        self._cal_header_lbl = QLabel("२०८३ भाद्र")
        self._cal_header_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        cal_title_box.addWidget(cal_title)
        cal_title_box.addWidget(self._cal_header_lbl)
        cal_top.addLayout(cal_title_box)
        cal_top.addStretch(1)

        # Year Combo
        cal_top.addWidget(QLabel("वर्ष" if self._is_ne else "Year"))
        self._year_combo = QComboBox()
        self._year_combo.setStyleSheet("QComboBox { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 5px; padding: 2px 6px; font-weight: 600; font-size: 12px; min-width: 70px; }")
        for y in range(2000, 2095):
            self._year_combo.addItem(to_nepali_digits(y) if self._is_ne else str(y), y)
        self._year_combo.currentIndexChanged.connect(self._on_year_month_changed)
        cal_top.addWidget(self._year_combo)

        # Month Combo
        cal_top.addWidget(QLabel("महिना" if self._is_ne else "Month"))
        self._month_combo = QComboBox()
        self._month_combo.setStyleSheet("QComboBox { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 5px; padding: 2px 6px; font-weight: 600; font-size: 12px; min-width: 80px; }")
        months = BS_MONTHS_NE if self._is_ne else BS_MONTHS_EN
        for idx, m_name in enumerate(months, 1):
            self._month_combo.addItem(m_name, idx)
        self._month_combo.currentIndexChanged.connect(self._on_year_month_changed)
        cal_top.addWidget(self._month_combo)

        # Location label
        self._loc_label = QLabel("स्थान: Kathmandu")
        self._loc_label.setStyleSheet("color: #64748b; font-size: 11.5px; padding-left: 8px;")
        cal_top.addWidget(self._loc_label)

        cal_box.addLayout(cal_top)

        # Weekday Headers (7 columns: आइत, सोम, मंगल, बुध, बिहि, शुक्र, शनि)
        days_header = QHBoxLayout()
        days_header.setSpacing(4)
        weekdays = ["आइत", "सोम", "मंगल", "बुध", "बिहि", "शुक्र", "शनि"] if self._is_ne else ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for wd in weekdays:
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #475569; font-size: 11.5px; font-weight: 700; padding: 2px 0;")
            days_header.addWidget(lbl, 1)
        cal_box.addLayout(days_header)

        # Grid for Calendar Days
        self._days_grid_widget = QWidget()
        self._days_grid = QGridLayout(self._days_grid_widget)
        self._days_grid.setContentsMargins(0, 0, 0, 0)
        self._days_grid.setSpacing(4)
        cal_box.addWidget(self._days_grid_widget)

        # Bottom Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)
        
        dot_today = QLabel("🟢 " + ("आज" if self._is_ne else "Today"))
        dot_today.setStyleSheet("font-size: 11px; color: #16a34a; font-weight: 600;")
        legend_layout.addWidget(dot_today)

        dot_sel = QLabel("🔵 " + ("चयनित मिति" if self._is_ne else "Selected Date"))
        dot_sel.setStyleSheet("font-size: 11px; color: #1d4ed8; font-weight: 600;")
        legend_layout.addWidget(dot_sel)
        legend_layout.addStretch(1)
        cal_box.addLayout(legend_layout)

        self._main_layout.addWidget(self._cal_card)

        # ── 2. PANCHANG REPORT CARD ──────────────────────────────────────────
        self._report_card = QFrame()
        self._report_card.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }")
        self._report_box = QVBoxLayout(self._report_card)
        self._report_box.setContentsMargins(16, 14, 16, 16)
        self._report_box.setSpacing(12)

        # Report Header Bar: Title + Selected Date + Today Button
        rep_top = QHBoxLayout()
        rep_title_box = QVBoxLayout()
        rep_title_box.setSpacing(1)
        rep_title = QLabel("पञ्चाङ्ग रिपोर्ट" if self._is_ne else "Panchang Report")
        rep_title.setStyleSheet("color: #1d4ed8; font-size: 16px; font-weight: 700;")
        self._rep_subtitle = QLabel("चयनित मिति: August 23, 2026 — २०८३ भाद्र ७")
        self._rep_subtitle.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600;")
        rep_title_box.addWidget(rep_title)
        rep_title_box.addWidget(self._rep_subtitle)
        rep_top.addLayout(rep_title_box)
        rep_top.addStretch(1)

        self._today_action_btn = QPushButton("आजको पञ्चाङ्ग" if self._is_ne else "Today's Panchang")
        self._today_action_btn.setStyleSheet("""
            QPushButton {
                background: #fef08a; color: #854d0e; border: 1px solid #fde047;
                border-radius: 14px; font-weight: 700; font-size: 12px; padding: 5px 14px;
            }
            QPushButton:hover { background: #fde047; }
        """)
        self._today_action_btn.clicked.connect(self._select_today)
        rep_top.addWidget(self._today_action_btn)
        self._report_box.addLayout(rep_top)

        # ── Row 1, Col 0: Date Details & Sun Box ──
        self._date_banner = QFrame()
        self._date_banner.setObjectName("panchangSection_date_sun")
        self._date_banner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._date_banner.setStyleSheet("""
            QFrame#panchangSection_date_sun {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-top: 4px solid #eab308;
                border-radius: 8px;
            }
        """)
        banner_layout = QVBoxLayout(self._date_banner)
        banner_layout.setContentsMargins(12, 10, 12, 10)
        banner_layout.setSpacing(6)

        date_heading = QLabel("मिति तथा सूर्योदय" if self._is_ne else "Date & Sun Details")
        date_heading.setStyleSheet("color: #a16207; font-size: 13.5px; font-weight: 700; padding-bottom: 2px;")
        banner_layout.addWidget(date_heading)

        # Middle Date & Badge
        mid_row = QHBoxLayout()
        mid_row.setSpacing(8)

        self._day_badge = QFrame()
        self._day_badge.setStyleSheet("QFrame { background: #fef08a; border: 1px solid #fde047; border-radius: 6px; min-width: 48px; max-width: 48px; min-height: 44px; }")
        badge_box = QVBoxLayout(self._day_badge)
        badge_box.setContentsMargins(2, 2, 2, 2)
        badge_box.setSpacing(0)
        self._badge_num = QLabel("७")
        self._badge_num.setAlignment(Qt.AlignCenter)
        self._badge_num.setStyleSheet("font-size: 17px; font-weight: 800; color: #713f12; border: none;")
        self._badge_day = QLabel("आइतबार")
        self._badge_day.setAlignment(Qt.AlignCenter)
        self._badge_day.setStyleSheet("font-size: 9px; font-weight: 700; color: #854d0e; border: none;")
        badge_box.addWidget(self._badge_num)
        badge_box.addWidget(self._badge_day)
        mid_row.addWidget(self._day_badge)

        mid_box = QVBoxLayout()
        mid_box.setSpacing(1)
        self._banner_bs = QLabel("भाद्र ७, २०८३")
        self._banner_bs.setStyleSheet("font-size: 12.5px; font-weight: 700; color: #1d4ed8; border: none;")
        self._banner_ad = QLabel("August 23, 2026")
        self._banner_ad.setStyleSheet("font-size: 11px; font-weight: 600; color: #475569; border: none;")
        self._banner_nepal_samvat = QLabel("ने.सं. ११४६ (तछलागा)")
        self._banner_nepal_samvat.setStyleSheet("font-size: 11px; color: #64748b; border: none;")
        self._banner_paksha_tithi = QLabel("शुक्लपक्ष एकादशी")
        self._banner_paksha_tithi.setStyleSheet("font-size: 11px; font-weight: 600; color: #0284c7; border: none;")
        mid_box.addWidget(self._banner_bs)
        mid_box.addWidget(self._banner_ad)
        mid_box.addWidget(self._banner_nepal_samvat)
        mid_box.addWidget(self._banner_paksha_tithi)
        mid_row.addLayout(mid_box, 1)
        banner_layout.addLayout(mid_row)

        # Sun times bar
        sun_line = QFrame()
        sun_line.setStyleSheet("QFrame { background: #fefce8; border: 1px solid #fef08a; border-radius: 5px; }")
        sun_layout = QHBoxLayout(sun_line)
        sun_layout.setContentsMargins(6, 4, 6, 4)
        sun_layout.setSpacing(6)
        self._banner_sunrise = QLabel("☀ सूर्योदय ०५:३८")
        self._banner_sunrise.setStyleSheet("font-size: 11px; font-weight: 600; color: #b45309; border: none;")
        self._banner_sunset = QLabel("🌅 सूर्यास्त १८:३४")
        self._banner_sunset.setStyleSheet("font-size: 11px; font-weight: 600; color: #dc2626; border: none;")
        sun_layout.addWidget(self._banner_sunrise)
        sun_layout.addStretch(1)
        sun_layout.addWidget(self._banner_sunset)
        banner_layout.addWidget(sun_line)
        banner_layout.addStretch(1)

        # ── Row 1, Col 1: Sankalpa Shloka Card ──
        self._sankalpa_card = QFrame()
        self._sankalpa_card.setObjectName("panchangSection_sankalpa")
        self._sankalpa_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._sankalpa_card.setStyleSheet("""
            QFrame#panchangSection_sankalpa {
                background: #fdfaf3;
                border: 1px solid #f3e8d2;
                border-top: 4px solid #d97706;
                border-radius: 8px;
            }
        """)
        sankalpa_box = QVBoxLayout(self._sankalpa_card)
        sankalpa_box.setContentsMargins(12, 10, 12, 10)
        sankalpa_box.setSpacing(4)

        sankalpa_title = QLabel("📜 दैनिक संकल्प श्लोक" if self._is_ne else "Daily Sankalpa Shloka")
        sankalpa_title.setStyleSheet("color: #92400e; font-size: 13.5px; font-weight: 700; padding-bottom: 2px;")
        sankalpa_box.addWidget(sankalpa_title)

        self._sankalpa_text = QLabel()
        self._sankalpa_text.setWordWrap(True)
        self._sankalpa_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._sankalpa_text.setStyleSheet("color: #1e293b; font-size: 12.5px; line-height: 1.65; border: none;")
        sankalpa_box.addWidget(self._sankalpa_text, 1)
        sankalpa_box.addStretch(1)

        # ── 2 Rows x 3 Columns Layout Grid ──
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(0, 2, 0, 0)
        self._grid.setHorizontalSpacing(10)
        self._grid.setVerticalSpacing(10)
        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 1)
        self._grid.setColumnStretch(2, 1)
        self._grid.setRowStretch(0, 1)
        self._grid.setRowStretch(1, 1)
        self._report_box.addWidget(self._container)

        self._main_layout.addWidget(self._report_card)

        # ── User Guide button (at the bottom; opens the shared guide dialog) ───
        # No inline guide box is rendered here, so the panchang keeps the full page.
        _guide_btn = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn.setObjectName("panchangGuideBox")
        _guide_btn.setToolTip("दैनिक पञ्चाङ्ग निर्देशिका" if self._is_ne else "Daily Panchang guide")
        _guide_btn.setCursor(Qt.PointingHandCursor)
        _guide_btn.setStyleSheet(
            "QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; "
            "border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } "
            "QPushButton:hover { background: #bae6fd; }"
        )

        def _open_panchang_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_panchang_view")

        _guide_btn.clicked.connect(_open_panchang_guide)
        self._main_layout.addWidget(_guide_btn)

        # State label
        self._state_label = QLabel("")
        self._state_label.setObjectName("panchangState")
        self._state_label.setAlignment(Qt.AlignCenter)
        self._state_label.setStyleSheet("color: #64748b; font-size: 14px; padding: 20px;")
        self._main_layout.addWidget(self._state_label)

        # Initialize to current date without launching background thread
        today_bs = get_today_bs() or {"year": 2083, "month": 5, "day": 7}
        self._set_calendar_bs(today_bs["year"], today_bs["month"], today_bs["day"], trigger_calc=False)

    def _on_year_month_changed(self):
        if self._updating_calendar:
            return
        y = self._year_combo.currentData()
        m = self._month_combo.currentData()
        if y and m:
            self._selected_bs_year = y
            self._selected_bs_month = m
            max_days = bs_month_length(y, m) or 30
            if self._selected_bs_day > max_days:
                self._selected_bs_day = max_days
            self._render_calendar_grid()
            self._trigger_date_calculation()

    def _select_today(self):
        today_bs = get_today_bs() or {"year": 2083, "month": 5, "day": 7}
        self._set_calendar_bs(today_bs["year"], today_bs["month"], today_bs["day"], trigger_calc=True)

    def _set_calendar_bs(self, y: int, m: int, d: int, trigger_calc: bool = True):
        self._updating_calendar = True
        self._selected_bs_year = y
        self._selected_bs_month = m
        self._selected_bs_day = d
        
        # Sync dropdowns
        idx_y = self._year_combo.findData(y)
        if idx_y >= 0:
            self._year_combo.setCurrentIndex(idx_y)
        idx_m = self._month_combo.findData(m)
        if idx_m >= 0:
            self._month_combo.setCurrentIndex(idx_m)
        
        greg = bs_to_gregorian(y, m, d)
        if greg:
            self._date_edit.blockSignals(True)
            self._date_edit.setDate(QDate(greg.year, greg.month, greg.day))
            self._date_edit.blockSignals(False)
            bs = {"year": y, "month": m, "day": d}
            prefix = "वि.सं." if self._is_ne else "BS"
            self._bs_date_label.setText(f"{prefix} {format_bs_date(bs, self._lang)}")

        self._updating_calendar = False
        self._render_calendar_grid()
        if trigger_calc:
            self._trigger_date_calculation()

    def _on_qdate_changed(self, qdate: QDate):
        bs = gregorian_to_bs(qdate.year(), qdate.month(), qdate.day())
        if bs and not self._updating_calendar:
            self._set_calendar_bs(bs["year"], bs["month"], bs["day"], trigger_calc=False)
        prefix = "वि.सं." if self._is_ne else "BS"
        self._bs_date_label.setText(f"{prefix} {format_bs_date(bs, self._lang)}" if bs else f"{prefix} {UNAVAILABLE}")

    def _trigger_date_calculation(self):
        greg = bs_to_gregorian(self._selected_bs_year, self._selected_bs_month, self._selected_bs_day)
        if greg:
            self._updating_calendar = True
            self._date_edit.blockSignals(True)
            self._date_edit.setDate(QDate(greg.year, greg.month, greg.day))
            self._date_edit.blockSignals(False)
            bs = {"year": self._selected_bs_year, "month": self._selected_bs_month, "day": self._selected_bs_day}
            prefix = "वि.सं." if self._is_ne else "BS"
            self._bs_date_label.setText(f"{prefix} {format_bs_date(bs, self._lang)}")
            self._updating_calendar = False
            self.calculate_selected_date()

    def _render_calendar_grid(self):
        # Clear existing buttons
        while self._days_grid.count():
            item = self._days_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        y = self._selected_bs_year
        m = self._selected_bs_month
        sel_d = self._selected_bs_day

        m_name = BS_MONTHS_NE[m - 1] if self._is_ne else BS_MONTHS_EN[m - 1]
        self._cal_header_lbl.setText(f"{to_nepali_digits(y) if self._is_ne else y} {m_name}")

        first_ad = bs_to_gregorian(y, m, 1)
        if not first_ad:
            return

        # Sunday = 0, Monday = 1 ... Saturday = 6
        weekday_start = (first_ad.weekday() + 1) % 7
        total_days = bs_month_length(y, m) or 30
        today_bs = get_today_bs() or {}

        # Render blank spacers
        for i in range(weekday_start):
            spacer = QLabel()
            self._days_grid.addWidget(spacer, 0, i)

        curr_row = 0
        curr_col = weekday_start

        for d in range(1, total_days + 1):
            is_selected = (d == sel_d)
            is_today = (today_bs.get("year") == y and today_bs.get("month") == m and today_bs.get("day") == d)

            btn = QPushButton(to_nepali_digits(d) if self._is_ne else str(d))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.setMinimumHeight(28)
            btn.setMaximumHeight(32)

            if is_selected:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #fde047; color: #713f12; border: 1.5px solid #eab308;
                        border-radius: 6px; font-weight: 800; font-size: 12.5px; padding: 2px 0;
                    }
                """)
            elif is_today:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #dcfce7; color: #166534; border: 1.2px solid #22c55e;
                        border-radius: 6px; font-weight: 700; font-size: 12px; padding: 2px 0;
                    }
                    QPushButton:hover { background: #bbf7d0; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #f8fafc; color: #1e293b; border: 1px solid #e2e8f0;
                        border-radius: 6px; font-weight: 600; font-size: 12px; padding: 2px 0;
                    }
                    QPushButton:hover { background: #f1f5f9; border-color: #cbd5e1; }
                """)

            btn.clicked.connect(lambda checked=False, day_num=d: self._on_day_clicked(day_num))
            self._days_grid.addWidget(btn, curr_row, curr_col)

            curr_col += 1
            if curr_col > 6:
                curr_col = 0
                curr_row += 1

    def _on_day_clicked(self, day_num: int):
        self._selected_bs_day = day_num
        self._render_calendar_grid()
        self._trigger_date_calculation()

    def _set_loading(self, loading: bool):
        self._today_action_btn.setEnabled(not loading)
        if loading:
            self._state_label.setVisible(True)
            self._state_label.setText("गणना हुँदैछ..." if self._is_ne else "Calculating detailed Panchang...")
            self.state = "loading"
        else:
            self._state_label.setVisible(False)

    def activate(self):
        """Start default daily calculation when page is navigated to.
        Also re-reads calculation_siddhanta from QSettings so siddhanta changes take effect immediately.
        """
        # Re-read siddhanta from QSettings so changes in SettingsDialog are picked up
        prev_siddhanta = self._calculation_siddhanta
        self._calculation_siddhanta = _read_siddhanta_from_settings()
        siddhanta_changed = self._calculation_siddhanta != prev_siddhanta
        if not self._auto_calculation_pending and not siddhanta_changed:
            return
        if self._auto_calculation_pending:
            self._auto_calculation_pending = False
        self.calculate_selected_date()

    def calculate_selected_date(self):
        # NOTE: The daily Panchang calculation used to run on a worker QThread
        # whose ``finished`` -> ``quit`` connection is queued to the main
        # thread.  With no running main-thread event loop (e.g. headless
        # tests) ``quit()`` never executes, so the QThread outlives its page
        # and the Qt application and aborts the whole process natively with
        # 0xC0000409 ("QThread: Destroyed while thread '' is still running").
        # ``calculate_daily_panchang`` is a fast, pure, synchronous ephemeris
        # computation with no I/O, so it is executed inline instead.
        self._stop_daily_thread()
        greg = bs_to_gregorian(self._selected_bs_year, self._selected_bs_month, self._selected_bs_day)
        if not greg:
            qdate = self._date_edit.date()
            greg = datetime.date(qdate.year(), qdate.month(), qdate.day())

        # Re-read siddhanta from QSettings in case user changed it since page was built
        self._calculation_siddhanta = _read_siddhanta_from_settings()

        # Instant cache hit — 0 ms response
        cache_key = (greg.isoformat(), str(self._ayanamsha), str(self._node_type), str(self._house_system), str(self._calculation_siddhanta))
        if cache_key in _DAILY_PANCHANG_CACHE:
            self._set_loading(False)
            self.refresh(_DAILY_PANCHANG_CACHE[cache_key])
            return

        self._set_loading(True)
        try:
            data = calculate_daily_panchang(greg, self._ayanamsha, self._node_type, self._house_system,
                                            calculation_siddhanta=self._calculation_siddhanta)
        except Exception as exc:  # pragma: no cover - defensive
            self._on_daily_error(str(exc))
            return
        self._on_daily_finished(data)

    def _stop_daily_thread(self) -> None:
        """Join and dispose of any previously created daily worker thread.

        Defensive only: no thread is started any more, but if an older
        instance (or a subclass) left one running it must be stopped before
        teardown, otherwise Qt aborts the process natively (0xC0000409).
        """
        thread = self._daily_thread
        if thread is not None:
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(3000)
            except RuntimeError:
                # Underlying C++ object already deleted.
                pass
        self._clear_daily_worker()

    def _on_daily_finished(self, data: dict):
        self._set_loading(False)
        self.refresh(data)

    def _on_daily_error(self, message: str):
        self._set_loading(False)
        self.refresh({"error": message})

    def _clear_daily_worker(self):
        if self._daily_worker is not None:
            self._daily_worker.deleteLater()
        if self._daily_thread is not None:
            self._daily_thread.deleteLater()
        self._daily_worker = None
        self._daily_thread = None

    def _section_frame(self, section: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName(f"panchangSection_{section['key']}")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setStyleSheet(f"""
            QFrame#{frame.objectName()} {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-top: 4px solid {section['accent']};
                border-radius: 8px;
            }}
        """)
        box = QVBoxLayout(frame)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(2)

        heading = QLabel(section["title"])
        heading.setStyleSheet(f"color: {section['accent']}; font-size: 13.5px; font-weight: 700; padding-bottom: 3px;")
        box.addWidget(heading)

        for index, row in enumerate(section["rows"]):
            line = QFrame()
            line.setStyleSheet(f"QFrame {{ border: none; border-top: {'none' if index == 0 else '1px solid #f1f5f9'}; }}")
            row_layout = QHBoxLayout(line)
            row_layout.setContentsMargins(2, 3, 2, 3)
            label = QLabel(row["label"])
            label.setMinimumWidth(100)
            label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; border: none;")
            value = QLabel(str(row["value"]))
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value.setStyleSheet("color: #1e293b; font-size: 11.5px; font-weight: 600; border: none;")
            row_layout.addWidget(label)
            row_layout.addWidget(value, 1)
            box.addWidget(line)
        box.addStretch(1)
        return frame

    def refresh(self, data: Optional[dict]):
        self._data = data
        self.model = build_panchang_model(data, self._lang)
        self.state = self.model["state"]

        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w and w not in (self._date_banner, self._sankalpa_card):
                w.deleteLater()

        ready = self.state == "ready"
        self._container.setVisible(ready)
        self._date_banner.setVisible(ready)
        self._sankalpa_card.setVisible(ready)
        self._state_label.setVisible(not ready)
        self._state_label.setText(self.model["message"])

        if not ready:
            return

        # Update Header & Banner
        bs = self.model.get("bs") or {"year": self._selected_bs_year, "month": self._selected_bs_month, "day": self._selected_bs_day}
        date_val = self.model.get("date_value") or datetime.date.today()
        p = self.model.get("panchang") or {}

        bs_month_name = BS_MONTHS_NE[bs.get("month", 1) - 1] if self._is_ne else BS_MONTHS_EN[bs.get("month", 1) - 1]
        bs_str = f"{bs_month_name} {to_nepali_digits(bs.get('day', 1))}, {to_nepali_digits(bs.get('year', 2083))}"
        ad_str = date_val.strftime("%B %d, %Y")

        self._rep_subtitle.setText(f"चयनित मिति: {ad_str} — {bs_str}")
        self._badge_num.setText(to_nepali_digits(bs.get("day", 1)) if self._is_ne else str(bs.get("day", 1)))
        
        vara_text = _localized(p.get("vara") or {}, self._lang)
        self._badge_day.setText(vara_text)

        self._banner_ad.setText(ad_str)
        self._banner_bs.setText(bs_str)
        
        nepal_samvat = _samvat_value(p.get("nepal_samvat"), self._lang)
        self._banner_nepal_samvat.setText(f"ने.सं. {nepal_samvat}" if nepal_samvat != UNAVAILABLE else "")
        
        tithi_obj = p.get("tithi") or {}
        paksha = tithi_obj.get("paksha_nepali") or tithi_obj.get("paksha") or ""
        tithi_name = tithi_obj.get("nepali") or tithi_obj.get("name") or ""
        self._banner_paksha_tithi.setText(f"{paksha} {tithi_name}".strip())

        sunrise_val = _value(p.get("sunrise"))
        sunset_val = _value(p.get("sunset"))
        self._banner_sunrise.setText(f"☀ सूर्योदय {sunrise_val}")
        self._banner_sunset.setText(f"🌅 सूर्यास्त {sunset_val}")

        # Update Sankalpa Shloka
        self._sankalpa_text.setText(self.model.get("sankalpa", ""))

        # ── Arrange 6 boxes into 2 rows x 3 columns ──
        # Row 0:
        # Col 0: मिति तथा सूर्य विवरण
        self._grid.addWidget(self._date_banner, 0, 0)
        # Col 1: दैनिक संकल्प श्लोक
        self._grid.addWidget(self._sankalpa_card, 0, 1)

        sec_map = {s["key"]: s for s in self.model.get("sections", [])}
        
        # Col 2: संवत् विवरण
        if "samvat" in sec_map:
            self._grid.addWidget(self._section_frame(sec_map["samvat"]), 0, 2)
            
        # Row 1:
        # Col 0: पञ्चाङ्ग
        if "panchang" in sec_map:
            self._grid.addWidget(self._section_frame(sec_map["panchang"]), 1, 0)
        # Col 1: सूर्य र दिनमान
        if "sun_day" in sec_map:
            self._grid.addWidget(self._section_frame(sec_map["sun_day"]), 1, 1)
        # Col 2: सूर्योदयकालीन स्पष्टग्रह
        if "sunrise_planets" in sec_map:
            self._grid.addWidget(self._section_frame(sec_map["sunrise_planets"]), 1, 2)
