# -*- coding: utf-8 -*-
"""Native combined Birth Panchang and Avakahada report."""
from __future__ import annotations

import datetime as _datetime
from typing import Any, Optional

from PySide6.QtCore import QMarginsF, QPoint, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMenu, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QToolButton,
    QVBoxLayout, QWidget,
)

from gui.theme import (
    BG_SECONDARY, BG_TERTIARY, BORDER_COLOR, COLOR_ERROR, COLOR_GOLD,
    COLOR_TEXT_MUTED, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
)
from gui.utils.bs_calendar import format_bs_date, gregorian_to_bs, to_nepali_digits

UNAVAILABLE = "—"


class _HoverToolButton(QToolButton):
    """QToolButton whose dropdown menu also opens when hovered."""

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        if self.menu() is not None:
            self.showMenu()

_SIGN_NAMES = {
    "en": {1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"},
    "ne": {1: "मेष", 2: "वृष", 3: "मिथुन", 4: "कर्कट", 5: "सिंह", 6: "कन्या", 7: "तुला", 8: "वृश्चिक", 9: "धनु", 10: "मकर", 11: "कुम्भ", 12: "मीन"},
}
_WEEKDAYS = {
    "en": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    "ne": ("सोमबार", "मंगलबार", "बुधबार", "बिहिबार", "शुक्रबार", "शनिबार", "आइतबार"),
}
_MONTHS_NE = ("बैशाख", "जेठ", "अषाढ", "श्रावण", "भाद्र", "आश्विन", "कार्तिक", "मंसिर", "पौष", "माघ", "फाल्गुन", "चैत")
_FIELD_GROUPS = (
    (("nakshatra", "Nakshatra", "नक्षत्र"), ("pada", "Pada", "पाद"), ("rashi", "Rashi", "राशि"), ("rashi_lord", "Rashi Lord", "राशि स्वामी"), ("name_akshara", "Name Akshara", "नामाक्षर")),
    (("yoni", "Yoni", "योनि"), ("viryoni", "Vair Yoni", "वैर योनि"), ("gana", "Gana", "गण"), ("nadi", "Nadi", "नाडी")),
    (("varna", "Varna", "वर्ण"), ("vashya", "Vashya", "वश्य"), ("varga", "Varga", "वर्ग"), ("shatru_varga", "Shatru Varga", "शत्रु वर्ग")),
    (("element", "Element", "तत्व"), ("asana", "Asana", "आसन"), ("paksha", "Paksha", "पक्ष"), ("bhayaat", "Bhayaat", "भयात")),
)


def _value(value: Any) -> str:
    if value is None or value == "" or isinstance(value, (dict, list, tuple, set)):
        return UNAVAILABLE
    return str(value)


def _birth_bs_date(bs: Optional[dict], language: str) -> str:
    if not bs:
        return UNAVAILABLE
    if language != "ne":
        return format_bs_date(bs, language)
    try:
        month = _MONTHS_NE[int(bs["month"]) - 1]
        return f"{to_nepali_digits(bs['year'])} {month} {to_nepali_digits(bs['day'])}"
    except (KeyError, TypeError, ValueError, IndexError):
        return UNAVAILABLE


def _nested(value: Any, language: str = "ne") -> str:
    if isinstance(value, dict):
        return _value(value.get("nepali" if language == "ne" else "name") or value.get("name") or value.get("nepali") or value.get("time"))
    return _value(value)


def _time(value: Any) -> str:
    text = _value(value)
    if text == UNAVAILABLE:
        return text
    parts = text.split(":")
    if len(parts) < 2:
        return text
    try:
        return f"{int(float(parts[0])):02d}:{int(float(parts[1])):02d}:{int(float(parts[2])) if len(parts) > 2 else 0:02d}"
    except (TypeError, ValueError):
        return text


def _dms(value: Any, direction: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return UNAVAILABLE
    absolute = abs(number)
    degrees = int(absolute)
    minutes_float = (absolute - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)
    sign = direction[0] if number >= 0 else direction[1]
    return f"{degrees}°{minutes:02d}′{seconds:02d}″ {sign}"


def _gmt(local_time: Any, timezone: Any) -> str:
    text = _value(local_time)
    try:
        parts = [float(x) for x in text.split(":")]
        total = parts[0] * 60 + parts[1] - float(timezone) * 60
        total %= 1440
        return f"{int(total // 60):02d}:{int(total % 60):02d}:{int(parts[2]) if len(parts) > 2 else 0:02d}"
    except (ValueError, TypeError, IndexError):
        return UNAVAILABLE


def _offset(value: Any, language: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return UNAVAILABLE
    sign = "+" if number >= 0 else "-"
    absolute = abs(number)
    hours = int(absolute)
    minutes = round((absolute - hours) * 60)
    suffix = " घण्टा" if language == "ne" else " hrs"
    return f"{sign}{hours:02d}:{minutes:02d}{suffix}"


def _degree(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return UNAVAILABLE
    degrees = int(number)
    minutes_float = (number - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        degrees += 1
    return f"{degrees}°{minutes}′{seconds}″"


def _time_seconds(value: Any) -> Optional[float]:
    text = _value(value)
    if text == UNAVAILABLE:
        return None
    try:
        parts = [float(part) for part in text.split(":")]
    except (TypeError, ValueError):
        return None
    if len(parts) < 2:
        return None
    return parts[0] * 3600 + parts[1] * 60 + (parts[2] if len(parts) > 2 else 0)


def _ghati_duration_from_seconds(seconds: Any, language: str) -> str:
    try:
        total_seconds = float(seconds)
    except (TypeError, ValueError):
        return UNAVAILABLE
    total_vipala = round(total_seconds / 0.4)
    ghati, remainder = divmod(total_vipala, 3600)
    pala, vipala = divmod(remainder, 60)
    result = f"{ghati:02d}:{pala:02d}:{vipala:02d}"
    return to_nepali_digits(result) if language == "ne" else result


def _ghati_from_sunrise(end_time: Any, sunrise: Any, language: str) -> str:
    end_seconds = _time_seconds(end_time)
    sunrise_seconds = _time_seconds(sunrise)
    if end_seconds is None or sunrise_seconds is None:
        return UNAVAILABLE
    return _ghati_duration_from_seconds((end_seconds - sunrise_seconds) % 86400, language)


def _limb_end(value: Any, sunrise: Any, language: str) -> str:
    end_time = _time(value)
    if end_time == UNAVAILABLE:
        return UNAVAILABLE
    ghati = _ghati_from_sunrise(end_time, sunrise, language)
    if ghati == UNAVAILABLE:
        return end_time
    return f"{end_time} {'बजे' if language == 'ne' else 'hrs'} ({ghati} {'घटी' if language == 'ne' else 'ghati'})"


def _ayanamsha(value: Any, ayanamsha_type: Any) -> str:
    degree = _degree(value)
    if degree == UNAVAILABLE:
        return degree
    return f"{degree} ({_value(ayanamsha_type) if _value(ayanamsha_type) != UNAVAILABLE else 'LAHIRI'})"


def _row(key: str, en: str, ne: str, value: Any) -> dict:
    return {"key": key, "label": ne, "label_en": en, "value": _value(value)}


def _full_age(birth_date: Optional[_datetime.date], language: str) -> str:
    if not birth_date:
        return UNAVAILABLE
    today = _datetime.date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    if days < 0:
        previous_month = today.replace(day=1) - _datetime.timedelta(days=1)
        days += previous_month.day
        months -= 1
    if months < 0:
        months += 12
        years -= 1
    if language == "ne":
        return f"{to_nepali_digits(years)} वर्ष {to_nepali_digits(months)} महिना {to_nepali_digits(days)} दिन"
    return f"{years} years {months} months {days} days"


def _dasha_ribbon_value(period: dict, language: str) -> str:
    if not period:
        return UNAVAILABLE
    lord = period.get("lord_nepali" if language == "ne" else "lord") or period.get("lord")
    start = period.get("start_bs") or period.get("start")
    end = period.get("end_bs") or period.get("end")
    if not lord:
        return UNAVAILABLE
    if start and end:
        value = f"{lord} ({start} - {end})"
        return to_nepali_digits(value) if language == "ne" else value
    return _value(lord)


def _ghati_pala_vipala(value: Any) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return UNAVAILABLE
    ghati = int(amount)
    pala_float = (amount - ghati) * 60
    pala = int(pala_float)
    vipala = round((pala_float - pala) * 60)
    if vipala == 60:
        vipala = 0
        pala += 1
    if pala == 60:
        pala = 0
        ghati += 1
    return f"{ghati:02d}:{pala:02d}:{vipala:02d}"


def build_birth_panchang_model(data: Optional[dict], language: str = "ne", gender: int = 0) -> dict:
    """Normalize the existing calculation payload for the combined Web report."""
    is_ne = language == "ne"
    unavailable_message = "केही जन्म पञ्चाङ्ग मानहरू उपलब्ध छैनन्।" if is_ne else "Some birth panchang values are unavailable."
    if data is None or data == {}:
        return {"state": "no_chart", "message": "कृपया पहिले कुण्डली गणना गर्नुहोस्।" if is_ne else "Please calculate a chart first.", "sections": []}
    if not isinstance(data, dict) or data.get("error"):
        return {"state": "error", "message": _value(data.get("error")) if isinstance(data, dict) and data.get("error") else ("जन्म पञ्चाङ्ग विवरण पढ्न सकिएन।" if is_ne else "The birth panchang payload could not be read."), "sections": []}

    meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    panchang = data.get("panchang") if isinstance(data.get("panchang"), dict) else {}
    requested = data.get("panchang_requested_day") if isinstance(data.get("panchang_requested_day"), dict) else {}
    daily = requested.get("panchang") if isinstance(requested.get("panchang"), dict) else {}
    chakra = data.get("avakahada_chakra") if isinstance(data.get("avakahada_chakra"), dict) else {}
    if (not chakra or not chakra.get("rashi") or chakra.get("rashi") == UNAVAILABLE) and isinstance(panchang, dict):
        nak_obj = panchang.get("nakshatra") or {}
        nak_idx = nak_obj.get("index")
        pada_val = nak_obj.get("pada") or 1
        nak_name = nak_obj.get("nepali") or nak_obj.get("name")
        if nak_idx is not None:
            try:
                from backend.calculator.avakahada_chakra import calculate_avakahada_chakra
                computed = calculate_avakahada_chakra(nak_idx, pada_val, nakshatra_name=nak_name)
                chakra = {**computed, **chakra}
            except Exception:
                try:
                    from calculator.avakahada_chakra import calculate_avakahada_chakra
                    computed = calculate_avakahada_chakra(nak_idx, pada_val, nakshatra_name=nak_name)
                    chakra = {**computed, **chakra}
                except Exception:
                    pass

    lagna = data.get("lagna") if isinstance(data.get("lagna"), dict) else {}
    planets = data.get("planets") if isinstance(data.get("planets"), list) else []
    moon = next((p for p in planets if isinstance(p, dict) and p.get("name") == "Moon"), {})
    sun = next((p for p in planets if isinstance(p, dict) and p.get("name") == "Sun"), {})
    date_text = _value(meta.get("birth_date"))
    birth_date = None
    try:
        birth_date = _datetime.date.fromisoformat(date_text)
    except ValueError:
        pass
    bs = gregorian_to_bs(birth_date.year, birth_date.month, birth_date.day) if birth_date else None
    birth_time = _time(meta.get("birth_time"))
    weekday = _WEEKDAYS[language][birth_date.weekday()] if birth_date else UNAVAILABLE
    sunrise = _nested((daily.get("sunrise") or panchang.get("sunrise")), language)
    birth_seconds = _time_seconds(birth_time)
    sunrise_seconds = _time_seconds(sunrise)
    ishtakala = _ghati_duration_from_seconds((birth_seconds - sunrise_seconds) % 86400, language) if birth_seconds is not None and sunrise_seconds is not None else None
    sunset = _nested((daily.get("sunset") or panchang.get("sunset")), language)
    tithi = panchang.get("tithi") or {}
    nak = panchang.get("nakshatra") or {}
    yoga = panchang.get("yoga") or {}
    karana = panchang.get("karana") or {}
    daily_tithi = daily.get("tithi") or {}
    daily_nak = daily.get("nakshatra") or {}
    daily_yoga = daily.get("yoga") or {}
    daily_karana = daily.get("karana") or {}
    moon_sign = _SIGN_NAMES[language].get(moon.get("sign_number"), chakra.get("rashi", UNAVAILABLE))
    lagna_sign = _SIGN_NAMES[language].get(lagna.get("sign_number"), UNAVAILABLE)
    try:
        nakshatra_size = 360.0 / 27.0
        elapsed_degrees = float(moon.get("sidereal_longitude")) % nakshatra_size
        moon_speed = float(moon.get("speed") or 13.1763)
        derived_bhayaat = _ghati_pala_vipala((elapsed_degrees / nakshatra_size) * 60.0)
        bhabhog = _ghati_pala_vipala(60.0 * (nakshatra_size / moon_speed) if moon_speed > 0 else 60.0)
    except (TypeError, ValueError):
        derived_bhayaat = UNAVAILABLE
        bhabhog = UNAVAILABLE
    element = {1: "अग्नि" if is_ne else "Fire", 2: "पृथ्वी" if is_ne else "Earth", 3: "वायु" if is_ne else "Air", 4: "जल" if is_ne else "Water"}.get(((moon.get("sign_number") or 4) - 1) % 4 + 1, UNAVAILABLE)
    labels = lambda en, ne: ne if is_ne else en
    sections = []
    sections.append({"key": "birth_details", "title": labels("Birth Details", "जन्म विवरण"), "rows": [
        _row("gender", "Gender", "लिङ्ग", "Female" if gender == 1 and not is_ne else "स्त्री" if gender == 1 else "Male" if not is_ne else "पुरुष"),
        _row("name", "Name", "नाम", meta.get("name") or meta.get("full_name")), _row("birth_date_bs", "Birth Date (BS)", "जन्म मिति (वि.सं.)", _birth_bs_date(bs, language)), _row("birth_date_ad", "Birth Date (AD)", "जन्म मिति (ई.सं.)", date_text), _row("weekday", "Weekday", "जन्म वार", weekday), _row("birth_time", "Birth Time", "जन्म समय", birth_time), _row("ishtakala", "Ishtakala", "इष्टकाल", ishtakala), _row("place", "Birth Place", "जन्म स्थान", meta.get("city") or meta.get("birth_place")), _row("country", "Country", "देश", meta.get("country")),
    ]})
    sections.append({"key": "geographic", "title": labels("Geographic Details", "भौगोलिक विवरण"), "rows": [_row("latitude", "Latitude", "अक्षांश", _dms(meta.get("latitude"), "NS")), _row("longitude", "Longitude", "देशान्तर", _dms(meta.get("longitude"), "EW")), _row("timezone", "Time Zone", "समय क्षेत्र", _offset(meta.get("timezone"), language)), _row("gmt", "GMT Time", "जी.एम.टी. समय", _gmt(birth_time, meta.get("timezone"))), _row("local_time", "Local Time", "स्थानीय समय", birth_time), _row("lagna", "Ascendant", "लग्न राशि", lagna_sign), _row("lagna_degree", "Ascendant Degree", "लग्न अंश", _degree(lagna.get("longitude_in_sign")))]})
    sun_sign_number = sun.get("sign_number")
    ayana = ("उत्तरायण" if is_ne else "Uttarayan") if sun_sign_number and (sun_sign_number >= 10 or sun_sign_number <= 3) else ("दक्षिणायन" if is_ne else "Dakshinayan") if sun_sign_number else None
    season_names = ("वसन्त", "वसन्त", "ग्रीष्म", "ग्रीष्म", "वर्षा", "वर्षा", "शरद", "शरद", "हेमन्त", "हेमन्त", "शिशिर", "शिशिर")
    bs_month = bs.get("month") if bs else None
    season = season_names[(bs_month - 1) % 12] if isinstance(bs_month, int) else None
    sections.append({"key": "samvat", "title": labels("Samvat and Season", "संवत् तथा ऋतु विवरण"), "rows": [_row("vikram", "Vikram Samvat", "विक्रम संवत्", bs.get("year") if bs else None), _row("month", "Month", "महिना", _MONTHS_NE[bs_month - 1] if isinstance(bs_month, int) and 1 <= bs_month <= 12 else None), _row("shaka", "Shaka Samvat", "शक संवत्", (birth_date.year + 78) if birth_date else None), _row("samvatsara", "Samvatsara", "संवत्सर", panchang.get("samvatsara")), _row("ayana", "Solar Ayana", "सूर्य अयन", ayana), _row("season", "Season", "ऋतु", season), _row("paksha", "Paksha", "पक्ष", tithi.get("paksha_nepali" if is_ne else "paksha")), _row("weekday_calendar", "Weekday", "वार", weekday), _row("month_type", "Month Type", "महिना प्रकार", panchang.get("month_type_nepali" if is_ne else "month_type"))]})
    chakra_rows = []
    for group in _FIELD_GROUPS:
        for key, en, ne in group:
            if key == "nakshatra": value = nak.get("nepali" if is_ne else "name") or chakra.get("nakshatra")
            elif key == "pada": value = chakra.get("pada") or nak.get("pada")
            elif key == "paksha": value = tithi.get("paksha_nepali" if is_ne else "paksha")
            elif key == "element": value = element
            elif key == "bhayaat": value = chakra.get("bhayaat") or derived_bhayaat
            else: value = chakra.get(key)
            chakra_rows.append(_row(key, en, ne, value))
    sections.append({"key": "avakahada", "title": labels("Avakahada Chakra", "अवकहडा चक्र"), "rows": chakra_rows})
    def limb_rows(key, en, ne, daily_obj, birth_obj):
        end_time = daily_obj.get("end_time") or birth_obj.get("end_time")
        # For karana, prefer the pre-formatted 3-part Patro string (full_nepali / full_name)
        sunrise_val = daily_obj.get("full_nepali" if is_ne else "full_name") or _nested(daily_obj, language)
        return [
            _row(key + "_birth", "Birth " + en, "जन्मकालीन " + ne, birth_obj.get("birth_nepali" if is_ne else "birth_name") or _nested(birth_obj, language)),
            _row(key + "_sunrise", "Sunrise " + en, "सूर्योदयकालीन " + ne, sunrise_val),
            _row(key + "_end", en + " End", ne + " समाप्ति", _limb_end(end_time, sunrise, language)),
        ]
    sections.append({"key": "panchanga", "title": labels("Panchanga - Five Limbs", "पञ्चाङ्ग - पञ्च अङ्ग"), "rows": limb_rows("tithi", "Tithi", "तिथि", daily_tithi, tithi) + limb_rows("nakshatra", "Nakshatra", "नक्षत्र", daily_nak, nak) + limb_rows("yoga", "Yoga", "योग", daily_yoga, yoga) + limb_rows("karana", "Karana", "करण", daily_karana, karana)})
    # Use NST-standard daily panchang values for sun/dinman (panchang_requested_day uses Kathmandu coords)
    dinman_val = daily.get("dinman") or daily.get("day_duration") or panchang.get("day_duration")
    dinman_ghati = daily.get("dinman_ghati_nepali") if is_ne else daily.get("dinman_ghati")
    dinman_display = f"{dinman_ghati} ({dinman_val})" if dinman_ghati else dinman_val
    sunset_nst = _nested((daily.get("sunset") or panchang.get("sunset")), language)
    sections.append({"key": "sun_moon", "title": labels("Sun and Moon Details", "सूर्य तथा चन्द्र विवरण"), "rows": [_row("sunrise", "Sunrise", "सूर्योदय", sunrise), _row("sunset", "Sunset", "सूर्यास्त", sunset_nst), _row("day_duration", "Day Duration", "दिन अवधि", dinman_display), _row("sun_sign", "Sun Sign", "सूर्य राशि", _SIGN_NAMES[language].get(sun.get("sign_number"))), _row("sun_degree", "Sun Degree", "सूर्य अंश", _degree(sun.get("longitude_in_sign"))), _row("moon_sign", "Moon Sign", "चन्द्र राशि", moon_sign), _row("moon_nakshatra", "Moon Nakshatra", "चन्द्र नक्षत्र", nak.get("nepali" if is_ne else "name")), _row("moon_pada", "Moon Pada", "चन्द्र चरण", nak.get("pada")), _row("bhayaat_moon", "Bhayaat", "भयात", chakra.get("bhayaat") or derived_bhayaat), _row("bhabhog", "Bhabhog", "भभोग", bhabhog)]})
    dasha_list = data.get("dasha") if isinstance(data.get("dasha"), list) else []
    active_dasha = next((d for d in dasha_list if isinstance(d, dict) and d.get("is_active")), {})
    active_antar = next((d for d in (active_dasha.get("children") or []) if isinstance(d, dict) and d.get("is_active")), {})
    dasha_lord = active_dasha.get("lord_nepali" if is_ne else "lord") or active_dasha.get("lord")
    dasha_end = active_dasha.get("end_bs") or active_dasha.get("end")
    dasha_remaining = f"{dasha_lord} {'महादशा' if is_ne else 'Mahadasha'} - {dasha_end}" if dasha_lord and dasha_end else dasha_end
    sections.append({"key": "dasha", "title": labels("Dasha Details", "दशा विवरण"), "rows": [_row("birth_mahadasha", "Birth Mahadasha", "जन्मकालीन महादशा", dasha_lord), _row("birth_antardasha", "Birth Antardasha", "जन्मकालीन अन्तर्दशा", active_antar.get("lord_nepali" if is_ne else "lord") or active_antar.get("lord")), _row("mahadasha_end", "Mahadasha End", "महादशा समाप्ति", dasha_remaining), _row("ayanamsha", "Ayanamsha", "अयनांश", _ayanamsha(meta.get("ayanamsha_value"), meta.get("ayanamsha_type")))]})
    for section in sections:
        for row in section["rows"]:
            row["label"] = row["label"] if is_ne else row["label_en"]
            if is_ne:
                row["value"] = to_nepali_digits(row["value"])
    missing = [row["key"] for section in sections for row in section["rows"] if row["value"] == UNAVAILABLE]
    full_age = meta.get("full_age") or _full_age(birth_date, language)
    if is_ne:
        full_age = to_nepali_digits(full_age)
    return {
        "state": "incomplete" if missing else "ready",
        "message": "",
        "sections": sections,
        "missing": missing,
        "metadata": {
            **meta,
            "full_age": full_age,
        },
        "ribbon": {
            "mahadasha": _dasha_ribbon_value(active_dasha, language),
            "antardasha": _dasha_ribbon_value(active_antar, language),
        },
    }


def compose_birth_panchang_text(model: dict) -> str:
    lines = []
    for section in model.get("sections", []):
        lines.append(section["title"])
        lines.extend(f"{row['label']}: {row['value']}" for row in section["rows"])
        lines.append("")
    return "\n".join(lines).rstrip()


class BirthPanchangDetailsPage(QWidget):
    """Combined Birth Panchang and Avakahada report with report-only output."""

    _BLUE = "#1659b7"
    _BLUE_DEEP = "#0c3f8f"
    _PAGE = "#f3f6fa"
    _SURFACE = "#ffffff"
    _TEXT = "#172033"
    _MUTED = "#5c667a"
    _BORDER = "#d9e1ec"
    _GOLD = "#b98208"
    _TOP_ROW_LABEL_WIDTH = 112

    def __init__(self, data: Optional[dict] = None, language: str = "ne", gender: int = 0, parent=None):
        super().__init__(parent)
        self._language, self._gender = language, gender
        self._model = {}
        self._frames = {}
        self._build_ui()
        self.refresh(data)

    @property
    def state(self):
        return self._model.get("state", "error")

    @property
    def report_text(self):
        return compose_birth_panchang_text(self._model)

    def _label(self, en: str, ne: str) -> str:
        return ne if self._language == "ne" else en

    def _build_ui(self):
        self.setObjectName("birthPanchangPage")
        self.setStyleSheet(f"""
            QWidget#birthPanchangPage {{ background: {self._PAGE}; color: {self._TEXT}; }}
            QFrame#birthPanchangSection {{ background: {self._SURFACE}; border: 1px solid {self._BORDER}; border-radius: 8px; }}
            QScrollArea#birthPanchangRibbon {{ background: {self._SURFACE}; border-bottom: 1px solid {self._BORDER}; }}
            QWidget#birthPanchangRibbonContent {{ background: {self._SURFACE}; }}
            QLabel#birthPanchangEyebrow {{ color: {self._BLUE}; font-size: 13px; font-weight: 700; }}
            QLabel#birthPanchangTitle {{ color: {self._TEXT}; font-size: 24px; font-weight: 700; }}
            QLabel#birthPanchangSectionTitle {{ color: {self._BLUE_DEEP}; font-size: 17px; font-weight: 700; padding-bottom: 6px; }}
            QLabel#birthPanchangBoxTitle {{ background: {self._BLUE}; color: #ffffff; font-size: 15px; font-weight: 700; padding: 6px 10px; border-radius: 4px; }}
            QLabel#birthPanchangFieldLabel {{ color: {self._MUTED}; font-size: 14px; font-weight: 600; padding: 3px 0; }}
            QLabel#birthPanchangFieldValue {{ color: {self._TEXT}; font-size: 17px; font-weight: 700; padding: 3px 0; }}
            QLabel#birthPanchangState {{ padding: 10px; border-radius: 5px; font-size: 16px; }}
            QPushButton#birthPanchangAction {{ background: {self._SURFACE}; color: {self._BLUE_DEEP}; border: 1px solid {self._BORDER}; border-radius: 5px; padding: 7px 14px; font-weight: 600; font-size: 15px; }}
            QPushButton#birthPanchangAction:hover {{ background: #e8f1ff; }}
            QToolButton#birthPanchangReminderButton {{ background: #fff7e0; color: {self._GOLD}; border: 1px solid #e8d5a0; border-radius: 5px; padding: 7px 14px; font-weight: 700; font-size: 15px; }}
            QToolButton#birthPanchangReminderButton:hover {{ background: #ffedb8; border-color: {self._GOLD}; }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 18); root.setSpacing(10)

        header = QHBoxLayout(); header.setSpacing(12)
        heading_box = QVBoxLayout(); heading_box.setSpacing(1)
        eyebrow = QLabel(self._label("ASTROLOGICAL DETAILS AND ANALYSIS", "ज्योतिषीय विवरण र विश्लेषण")); eyebrow.setObjectName("birthPanchangEyebrow")
        title = QLabel(self._label("Birth Panchang", "जन्म पञ्चाङ्ग")); title.setObjectName("birthPanchangTitle")
        heading_box.addWidget(eyebrow); heading_box.addWidget(title); header.addLayout(heading_box); header.addStretch(1)
        root.addLayout(header)

        self._ribbon = QScrollArea(); self._ribbon.setObjectName("birthPanchangRibbon"); self._ribbon.setWidgetResizable(False); self._ribbon.setFrameShape(QFrame.NoFrame); self._ribbon.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); self._ribbon.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._ribbon_content = QWidget(); self._ribbon_content.setObjectName("birthPanchangRibbonContent")
        self._ribbon_layout = QHBoxLayout(self._ribbon_content); self._ribbon_layout.setContentsMargins(12, 8, 12, 8); self._ribbon_layout.setSpacing(14)
        self._ribbon.setWidget(self._ribbon_content); root.addWidget(self._ribbon)

        toolbar = QHBoxLayout(); toolbar.setSpacing(7)
        report_title = QLabel(self._label("Birth Panchang and Avakahada Chakra", "जन्म पञ्चाङ्ग तथा अवकहडा चक्र")); report_title.setObjectName("birthPanchangSectionTitle"); toolbar.addWidget(report_title)
        toolbar.addStretch(1)
        self._reminder_button = self._build_reminder_menu_button()
        toolbar.addWidget(self._reminder_button)
        toolbar.addStretch(1)
        self._copy_button = self._action_button(self._label("Copy", "प्रतिलिपि"), self.copy_report, self._label("Copy report", "प्रतिवेदन प्रतिलिपि गर्नुहोस्"))
        self._pdf_button = self._action_button(self._label("Save PDF", "PDF सुरक्षित गर्नुहोस्"), self.export_pdf, self._label("Save report as PDF", "प्रतिवेदन PDF मा सुरक्षित गर्नुहोस्"))
        self._print_button = self._action_button(self._label("Print", "प्रिन्ट"), self.print_report, self._label("Print report", "प्रतिवेदन प्रिन्ट गर्नुहोस्"))
        for button in (self._copy_button, self._pdf_button, self._print_button): toolbar.addWidget(button)
        root.addLayout(toolbar)

        self._state = QLabel(); self._state.setObjectName("birthPanchangState"); self._state.setWordWrap(True); root.addWidget(self._state)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); scroll.setStyleSheet("QScrollArea { background: transparent; }")
        self._container = QWidget(); self._grid = QGridLayout(self._container); self._grid.setContentsMargins(0, 0, 0, 0); self._grid.setHorizontalSpacing(10); self._grid.setVerticalSpacing(10)
        scroll.setWidget(self._container); root.addWidget(scroll, 1)

    def _action_button(self, text, handler, tooltip):
        button = QPushButton(text); button.setObjectName("birthPanchangAction"); button.setToolTip(tooltip); button.clicked.connect(handler); return button

    def _build_reminder_menu_button(self) -> QToolButton:
        """Small centered button whose hover opens the reminder dropdown menu.

        Options open the same dialogs used by the system-tray reminder
        service (today's digest / upcoming events / settings), so in-app
        behaviour always agrees with the tray.
        """
        is_ne = self._language == "ne"
        button = _HoverToolButton()
        button.setObjectName("birthPanchangReminderButton")
        button.setText("🔔 " + ("रिमाइन्डर" if is_ne else "Reminder"))
        button.setToolTip(
            "आजको पञ्चाङ्ग, आगामी पर्व र रिमाइन्डर सेटिङ हेर्न यहाँ क्लिक गर्नुहोस्"
            if is_ne else
            "Hover / click to view today's panchang, upcoming festivals and reminder settings"
        )
        button.setPopupMode(QToolButton.InstantPopup)
        button.setCursor(Qt.PointingHandCursor)

        menu = QMenu(button)
        menu.setObjectName("birthPanchangReminderMenu")
        menu.setStyleSheet(f"""
            QMenu {{ background: #ffffff; border: 1px solid {self._BORDER}; border-radius: 6px; padding: 4px; }}
            QMenu::item {{ padding: 6px 14px; border-radius: 4px; color: {self._TEXT}; }}
            QMenu::item:selected {{ background: #e8f1ff; color: {self._BLUE_DEEP}; }}
        """)
        act_digest = menu.addAction("📅 " + ("आजको पञ्चाङ्ग (Today's Digest)" if is_ne else "Today's Panchang Digest"))
        act_digest.triggered.connect(lambda: self._open_reminder_action("digest"))
        act_events = menu.addAction("🪔 " + ("आगामी पर्व / व्रत (Upcoming Events)" if is_ne else "Upcoming Festivals / Vrats"))
        act_events.triggered.connect(lambda: self._open_reminder_action("events"))
        menu.addSeparator()
        act_settings = menu.addAction("⚙ " + ("रिमाइन्डर सेटिङ (Reminder Settings)" if is_ne else "Reminder Settings"))
        act_settings.triggered.connect(lambda: self._open_reminder_action("settings"))
        button.setMenu(menu)
        return button

    def _open_reminder_action(self, action: str) -> None:
        """Forward a dropdown action to the live reminder service if attached."""
        service = getattr(self.window(), "_reminder_service", None)
        if service is None or not hasattr(service, "open_reminder_panel"):
            QMessageBox.information(
                self,
                "Reminders",
                "रिमाइन्डर सेवा सक्रिय छैन। एप पुनः सुरु गरेर फेरि प्रयास गर्नुहोस्।"
                if self._language == "ne" else
                "The reminder service is not active. Restart the app and try again.",
            )
            return
        service.open_reminder_panel(action)

    def _render_ribbon(self):
        while self._ribbon_layout.count():
            item = self._ribbon_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if self.state in ("no_chart", "error"):
            self._ribbon.setVisible(False); return
        values = {row["key"]: row["value"] for section in self._model.get("sections", []) for row in section["rows"]}
        meta = self._model.get("metadata", {})
        dasha = self._model.get("ribbon", {})
        fields = [
            ("Name", "नाम", meta.get("name") or values.get("name")),
            ("Birth Date (BS)", "जन्म मिति (वि.सं.)", values.get("birth_date_bs")),
            ("Birth Time", "जन्म समय", values.get("birth_time")),
            ("Birth Place", "जन्म स्थान", values.get("place")),
            ("Full Age", "पूर्ण उमेर", meta.get("full_age")),
            ("Gender", "लिङ्ग", values.get("gender")),
            ("Active Mahadasha", "सक्रिय महादशा", dasha.get("mahadasha") or values.get("birth_mahadasha")),
            ("Active Antardasha", "सक्रिय अन्तर्दशा", dasha.get("antardasha") or values.get("birth_antardasha")),
        ]
        for index, (en, ne, value) in enumerate(fields):
            holder = QVBoxLayout(); holder.setSpacing(2)
            label = QLabel(self._label(en, ne)); label.setObjectName("birthPanchangFieldLabel"); label.setAlignment(Qt.AlignHCenter)
            content = QLabel(_value(value)); content.setObjectName("birthPanchangFieldValue"); content.setWordWrap(True); content.setAlignment(Qt.AlignHCenter)
            holder.addWidget(label); holder.addWidget(content)
            cell = QWidget(); cell.setLayout(holder); cell.setMinimumWidth(120); self._ribbon_layout.addWidget(cell)
            if index < len(fields) - 1:
                line = QFrame(); line.setFrameShape(QFrame.VLine); line.setStyleSheet(f"color: {self._BORDER};"); self._ribbon_layout.addWidget(line)
        self._ribbon_layout.addStretch(1)
        self._ribbon_content.setMinimumWidth(max(self.width(), 8 * 120 + 7 * 15 + 24))
        self._ribbon_content.adjustSize(); self._ribbon.setVisible(True)

    def _section_frame(self, section):
        frame = QFrame(); frame.setObjectName("birthPanchangSection")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(frame); layout.setContentsMargins(10, 8, 10, 10); layout.setSpacing(6)
        heading = QLabel(section["title"]); heading.setObjectName("birthPanchangBoxTitle"); heading.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed); layout.addWidget(heading)
        rows = QGridLayout(); rows.setHorizontalSpacing(8); rows.setVerticalSpacing(1)
        rows.setColumnMinimumWidth(0, self._TOP_ROW_LABEL_WIDTH)
        rows.setColumnStretch(0, 0); rows.setColumnStretch(1, 1)
        compact_labels = section.get("key") in ("birth_details", "geographic", "samvat", "avakahada")
        for row_index, row in enumerate(section["rows"]):
            label = QLabel(row["label"])
            label.setObjectName("birthPanchangFieldLabel")
            label.setWordWrap(True)
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            if compact_labels:
                label.setMinimumWidth(self._TOP_ROW_LABEL_WIDTH)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value = QLabel(row["value"])
            value.setObjectName(f"birthPanchangValue_{row['key']}")
            value.setWordWrap(True)
            value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid_row = row_index * 2
            rows.addWidget(label, grid_row, 0); rows.addWidget(value, grid_row, 1)
            if row_index < len(section["rows"]) - 1:
                divider = QFrame(); divider.setFrameShape(QFrame.HLine); divider.setStyleSheet(f"color: {self._BORDER};"); rows.addWidget(divider, grid_row + 1, 0, 1, 2)
        layout.addLayout(rows); return frame

    def _rebuild_grid(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        sections = {section["key"]: section for section in self._model.get("sections", [])}
        order = ("birth_details", "geographic", "samvat", "avakahada", "panchanga", "sun_moon", "dasha")
        self._frames = {key: self._section_frame(sections[key]) for key in order if key in sections}
        for column, key in enumerate(("birth_details", "geographic", "samvat", "avakahada")):
            if key in self._frames: self._grid.addWidget(self._frames[key], 0, column)
        self._grid.setRowStretch(0, 1)
        for column, key in enumerate(("panchanga", "sun_moon", "dasha")):
            if key in self._frames: self._grid.addWidget(self._frames[key], 1, column)
        for column in range(4): self._grid.setColumnStretch(column, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_grid"):
            narrow = self.width() < 980
            for index, key in enumerate(("birth_details", "geographic", "samvat", "avakahada")):
                frame = self._frames.get(key)
                if frame: self._grid.addWidget(frame, index if narrow else 0, 0 if narrow else index)
            for index, key in enumerate(("panchanga", "sun_moon", "dasha")):
                frame = self._frames.get(key)
                if frame: self._grid.addWidget(frame, (4 + index) if narrow else 1, 0 if narrow else index)

    def refresh(self, data):
        self._model = build_birth_panchang_model(data, self._language, self._gender)
        message = self._model.get("message", "")
        if self.state in ("no_chart", "error") and message:
            self._state.setText(message)
            self._state.setVisible(True)
            color = COLOR_ERROR if self.state == "error" else self._BORDER
            self._state.setStyleSheet(f"background: {self._SURFACE}; border: 1px solid {color}; color: {COLOR_ERROR if self.state == 'error' else self._MUTED};")
        else:
            self._state.setText("")
            self._state.setVisible(False)
        self._copy_button.setEnabled(bool(self.report_text)); self._pdf_button.setEnabled(self.state not in ("no_chart", "error")); self._print_button.setEnabled(self.state not in ("no_chart", "error"))
        self._model.setdefault("metadata", (data or {}).get("metadata", {}) if isinstance(data, dict) else {})
        self._model.setdefault("ribbon", {})
        self._render_ribbon(); self._rebuild_grid()

    def copy_report(self):
        if self.report_text:
            QApplication.clipboard().setText(self.report_text)

    def _configure_printer(self, printer):
        from PySide6.QtGui import QPageLayout, QPageSize
        printer.setPageSize(QPageSize(QPageSize.A4)); layout = printer.pageLayout(); layout.setOrientation(QPageLayout.Portrait); layout.setMargins(QMarginsF(10, 10, 10, 10)); printer.setPageLayout(layout)

    def _render_to_printer(self, printer):
        self._container.ensurePolished(); self._container.adjustSize()
        target = printer.pageLayout().paintRectPixels(printer.resolution()); source_width = max(1, self._container.width()); source_height = max(1, self._container.height()); scale = target.width() / source_width; page_height = max(1, int(target.height() / scale)); pages = max(1, (source_height + page_height - 1) // page_height)
        painter = QPainter(printer)
        if not painter.isActive(): raise RuntimeError("Printer painter could not be started")
        try:
            for page in range(pages):
                if page and not printer.newPage(): raise RuntimeError("Printer could not create a new page")
                painter.save(); painter.setClipRect(target); painter.translate(target.left(), target.top() - page * page_height * scale); painter.scale(scale, scale); self._container.render(painter, QPoint(0, 0)); painter.restore()
        finally: painter.end()
        return pages

    def print_report(self):
        try:
            from PySide6.QtPrintSupport import QPrintDialog, QPrinter
            printer = QPrinter(QPrinter.HighResolution); self._configure_printer(printer); dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.Accepted: self._render_to_printer(printer)
        except Exception as exc:
            QMessageBox.warning(self, self._label("Print error", "प्रिन्ट त्रुटि"), str(exc))

    def export_pdf(self):
        try:
            from PySide6.QtPrintSupport import QPrinter
            path, _ = QFileDialog.getSaveFileName(self, self._label("Save Birth Panchang PDF", "जन्म पञ्चाङ्ग PDF सुरक्षित गर्नुहोस्"), "birth-panchang.pdf", "PDF Files (*.pdf)")
            if path:
                printer = QPrinter(QPrinter.HighResolution); printer.setOutputFormat(QPrinter.PdfFormat); printer.setOutputFileName(path); self._configure_printer(printer); self._render_to_printer(printer)
        except Exception as exc:
            QMessageBox.warning(self, self._label("PDF error", "PDF त्रुटि"), str(exc))
