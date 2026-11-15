"""
backend/calculator/reminder_panchang.py

Lightweight daily Panchang / Muhurta / Festival provider for the desktop
reminder service (system tray alerts).

Publishes:
  - get_daily_digest(date, latitude, longitude, timezone, language)
      -> full daily panchang + muhurta periods + festival/observance names
  - get_upcoming_events(date, days, latitude, longitude, timezone, language)
      -> list of notable events within the next N days (ekadashi, purnima,
         amavasya, sankranti, fixed BS festivals)

Uses the same authoritative backend engine (panchang.calculate_panchang and
muhurta.calculate_muhurta) so the alerts agree exactly with the on-screen
reports.  Results are cached by civil date + location to keep the reminder
tick cheap.
"""
from __future__ import annotations

import math
from datetime import date as _date, datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

from . import julian, muhurta, panchang

# ── Nepali digit helpers ─────────────────────────────────────────────────────
_NE_DIGITS = "०१२३४५६७८९"

BS_MONTHS_NE = [
    "बैशाख", "जेठ", "अषाढ", "श्रावण", "भाद्र", "आश्विन",
    "कार्तिक", "मंसिर", "पौष", "माघ", "फाल्गुन", "चैत",
]
BS_MONTHS_EN = [
    "Baisakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra",
]


def to_nepali_digits(value) -> str:
    """Convert every ASCII digit in ``value`` to a Devanagari (Nepali) digit."""
    return "".join(_NE_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(value))


def _format_bs_date(bs: Optional[tuple], language: str = "ne") -> str:
    """Format a (year, month, day) BS tuple as a readable date string."""
    if not bs:
        return ""
    y, m, d = bs
    if language == "ne":
        month_name = BS_MONTHS_NE[m - 1] if 1 <= m <= 12 else to_nepali_digits(m)
        return f"{to_nepali_digits(d)} {month_name} {to_nepali_digits(y)}"
    month_name = BS_MONTHS_EN[m - 1] if 1 <= m <= 12 else str(m)
    return f"{d} {month_name} {y}"


# ── Fixed BS festivals (month, day) → (Nepali, English) ─────────────────────
# Approximate fixed civil festivals in the Bikram Sambat calendar.  Tithi-based
# events (ekadashi, purnima, amavasya) are computed dynamically from panchang.
FESTIVALS_BS: Dict[tuple, tuple[str, str]] = {
    (1, 1):   ("नयाँ वर्ष (नेपाली)", "Nepali New Year"),
    (1, 9):   ("मातातीर्थ औंसी", "Mata Tirtha Aunsi"),
    (1, 15):  ("पृथ्वी जयन्ती", "Prithvi Jayanti"),
    (2, 15):  ("सीता पूजा / सीता विवाह", "Sita Puja"),
    (3, 15):  ("मोही (असारे पूर्णिमा)", "Mohi (Asare Purnima)"),
    (4, 15):  ("जनैपूर्णिमा", "Janai Purnima"),
    (4, 16):  ("कृष्ण जन्माष्टमी", "Krishna Janmashtami"),
    (5, 1):   ("ऋषि पञ्चमी", "Rishi Panchami"),
    (5, 11):  ("गाईजात्रा", "Gai Jatra"),
    (5, 15):  ("हरिबोधिनी एकादशी", "Haribodhini Ekadashi"),
    (6, 1):   ("इन्द्रजात्रा", "Indra Jatra"),
    (6, 9):   ("घटस्थापना", "Ghatasthapana"),
    (6, 10):  ("फूलपाती", "Fulpati"),
    (6, 15):  ("विजयादशमी (दशैं)", "Vijaya Dashami"),
    (6, 16):  ("कोजाग्रत पूर्णिमा", "Kojagrat Purnima"),
    (7, 1):   ("यमपञ्चक (तिहार) सुरु", "Yamapanchak begins"),
    (7, 2):   ("काग तिहार", "Kag Tihar"),
    (7, 3):   ("कुकुर तिहार", "Kukur Tihar"),
    (7, 4):   ("लक्ष्मी पूजा", "Laxmi Puja"),
    (7, 5):   ("गोवर्धन पूजा", "Govardhan Puja"),
    (7, 6):   ("भाइटीका", "Bhai Tika"),
    (7, 15):  ("धान्य पूर्णिमा", "Dhanya Purnima"),
    (8, 1):   ("माघे संक्रान्ति / माघी", "Maghe Sankranti"),
    (8, 8):   ("वसन्त पञ्चमी (सरस्वती पूजा)", "Basant Panchami"),
    (9, 5):   ("महाशिवरात्रि", "Maha Shivaratri"),
    (9, 15):  ("होली", "Holi"),
    (10, 8):  ("चैते दशैं", "Chaite Dashain"),
    (10, 12): ("गुठी पर्व", "Guthi Parva"),
    (11, 1):  ("वैशाखे संक्रान्ति", "Baisakhe Sankranti"),
    (12, 1):  ("जेठे संक्रान्ति", "Jethe Sankranti"),
}

# Tithi-based observances (tithi index 1-30, paksha from panchang).
# Ekadashi: Shukla 11 / Krishna 26; Purnima 15; Amavasya 30.
TITHI_OBSERVANCES: Dict[int, tuple[str, str]] = {
    8:  ("अष्टमी व्रत", "Ashtami Vrat"),
    11: ("एकादशी व्रत", "Ekadashi Vrat"),
    26: ("एकादशी व्रत", "Ekadashi Vrat"),
}

WEEKDAYS_NE = ["आइतबार", "सोमबार", "मङ्गलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"]
WEEKDAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


# ── Cached calculation helpers ───────────────────────────────────────────────

@lru_cache(maxsize=16)
def _cached_panchang(
    year: int, month: int, day: int, lat: float, lon: float, tz: float, ayanamsha: str
) -> Dict[str, Any]:
    """Full panchang for the local civil date (evaluated at local sunrise)."""
    jd_noon = julian.datetime_to_jd(year, month, day, 12, 0, 0, tz)
    sunrise_jd = panchang.calculate_sunrise_jd(jd_noon, lat, lon, tz)
    sun_sid, moon_sid = panchang._sidereal_longitudes(sunrise_jd, ayanamsha)
    return panchang.calculate_panchang(
        sunrise_jd, sun_sid, moon_sid,
        latitude=lat, longitude=lon, timezone=tz,
        sunrise_jd=sunrise_jd, ayanamsha_type=ayanamsha,
    )


@lru_cache(maxsize=16)
def _cached_muhurta(
    year: int, month: int, day: int, lat: float, lon: float, tz: float
) -> Dict[str, Any]:
    """Choghadiya / Hora / inauspicious periods for the local civil date."""
    jd_noon = julian.datetime_to_jd(year, month, day, 12, 0, 0, tz)
    return muhurta.calculate_muhurta(jd_noon, lat, lon, tz)


def _bs_date(ad: _date) -> Optional[tuple]:
    """Return (year, month, day) in Bikram Sambat, or None when unavailable."""
    try:
        import nepali_datetime
        bs = nepali_datetime.date.from_datetime_date(ad)
        return (bs.year, bs.month, bs.day)
    except Exception:
        return None


def _lunar_month_name(panchang_data: Dict[str, Any]) -> str:
    """Best-effort Nepali lunar month name for the current tithi cycle."""
    month_val = panchang_data.get("lunar_month")
    if isinstance(month_val, dict):
        return str(month_val.get("nepali") or month_val.get("name") or "")
    return str(month_val or "")


def _festivals_for(ad: _date, panchang_data: Dict[str, Any]) -> List[tuple[str, str]]:
    """Return list of (nepali, english) observance names for the day."""
    results: List[tuple[str, str]] = []
    bs = _bs_date(ad)
    if bs and bs[:2] in FESTIVALS_BS:
        results.append(FESTIVALS_BS[bs[:2]])

    tithi = panchang_data.get("tithi", {})
    tithi_idx = tithi.get("index")
    paksha = (tithi.get("paksha") or "").lower()
    if tithi_idx:
        tithi_idx = int(tithi_idx)
        if paksha == "waxing" and tithi_idx == 15:
            results.append(("पूर्णिमा", "Purnima (Full Moon)"))
        elif paksha == "waning" and tithi_idx == 30:
            results.append(("अमावस्या", "Amavasya (New Moon)"))
        elif tithi_idx in TITHI_OBSERVANCES:
            results.append(TITHI_OBSERVANCES[tithi_idx])

    # Deduplicate while preserving order.
    seen = set()
    unique: List[tuple[str, str]] = []
    for pair in results:
        if pair not in seen:
            seen.add(pair)
            unique.append(pair)
    return unique


# ── Public API ───────────────────────────────────────────────────────────────

def get_daily_digest(
    day: _date,
    latitude: float = 27.7172,
    longitude: float = 85.3240,
    timezone: float = 5.75,
    language: str = "ne",
    ayanamsha_type: str = "LAHIRI",
) -> Dict[str, Any]:
    """
    Return a complete daily digest for a civil date:
      panchang, muhurta, festivals, sunrise/sunset, weekday.
    """
    is_ne = language == "ne"
    pc = _cached_panchang(
        day.year, day.month, day.day,
        float(latitude), float(longitude), float(timezone), ayanamsha_type,
    )
    mh = _cached_muhurta(
        day.year, day.month, day.day,
        float(latitude), float(longitude), float(timezone),
    )

    weekday_idx = day.weekday()  # Monday=0
    weekday = {
        "index": (weekday_idx + 1) % 7,
        "nepali": WEEKDAYS_NE[(weekday_idx + 1) % 7],
        "english": WEEKDAYS_EN[(weekday_idx + 1) % 7],
    }

    festivals = _festivals_for(day, pc)

    # Inauspicious periods (Rahu Kaal, Gulika, Yamaganda) from muhurta.
    kaals = mh.get("kaals", {})
    inauspicious = []
    for key in ("rahu_kaal", "gulika", "yamaganda"):
        item = kaals.get(key)
        if isinstance(item, dict):
            inauspicious.append({
                "key": key,
                "label_ne": {
                    "rahu_kaal": "राहुकाल", "gulika": "गुलिका", "yamaganda": "यमगण्ड",
                }.get(key, key),
                "label_en": key.replace("_", " ").title(),
                "start": to_nepali_digits(item.get("start", "—")) if is_ne else item.get("start", "—"),
                "end": to_nepali_digits(item.get("end", "—")) if is_ne else item.get("end", "—"),
            })

    # Good muhurta periods today (Amrit / Shubh / Labh choghadiya).
    good_periods = []
    for key in ("choghadiya_day", "choghadiya_night"):
        for item in mh.get(key, []):
            name = item.get("name", {})
            if name.get("type") in ("good",):
                good_periods.append({
                    "name_ne": name.get("ne", ""),
                    "name_en": name.get("en", ""),
                    "start": to_nepali_digits(item.get("start", "—")) if is_ne else item.get("start", "—"),
                    "end": to_nepali_digits(item.get("end", "—")) if is_ne else item.get("end", "—"),
                })

    sunrise = pc.get("sunrise", {}).get("time", "—")
    sunset = pc.get("sunset", {}).get("time", "—")

    bs = _bs_date(day)
    return {
        "date": day.isoformat(),
        "date_bs": _format_bs_date(bs, "ne"),
        "date_bs_en": _format_bs_date(bs, "en"),
        "weekday": weekday,
        "sunrise": to_nepali_digits(sunrise) if is_ne else sunrise,
        "sunset": to_nepali_digits(sunset) if is_ne else sunset,
        "day_duration": pc.get("day_duration", "—"),
        "tithi": pc.get("tithi", {}),
        "nakshatra": pc.get("nakshatra", {}),
        "yoga": pc.get("yoga", {}),
        "karana": pc.get("karana", {}),
        "lunar_month": _lunar_month_name(pc),
        "samvatsara": pc.get("samvatsara", ""),
        "nepal_samvat": pc.get("nepal_samvat", {}),
        "festivals": festivals,
        "inauspicious_periods": inauspicious,
        "good_periods": good_periods[:6],
        "summary_ne": _digest_summary(pc, festivals, is_ne=True, day=day),
        "summary_en": _digest_summary(pc, festivals, is_ne=False, day=day),
    }


def get_upcoming_events(
    start_day: _date,
    days: int = 15,
    latitude: float = 27.7172,
    longitude: float = 85.3240,
    timezone: float = 5.75,
    language: str = "ne",
    ayanamsha_type: str = "LAHIRI",
) -> List[Dict[str, Any]]:
    """
    List notable events in the next `days` days (exclusive of today unless
    explicitly included).  Today's observance list is returned by
    get_daily_digest(); this scans forward for ekadashi / purnima / amavasya
    / fixed festivals / sankranti.
    """
    events: List[Dict[str, Any]] = []
    seen_days: Dict[str, int] = {}
    for offset in range(1, days + 1):
        d = start_day + timedelta(days=offset)
        pc = _cached_panchang(
            d.year, d.month, d.day,
            float(latitude), float(longitude), float(timezone), ayanamsha_type,
        )
        festivals = _festivals_for(d, pc)
        if not festivals:
            continue
        for ne, en in festivals:
            key = (d.isoformat(), ne)
            if key in seen_days:
                continue
            seen_days[key] = offset
            bs = _bs_date(d)
            events.append({
                "date": d.isoformat(),
                "date_bs": _format_bs_date(bs, "ne"),
                "date_bs_en": _format_bs_date(bs, "en"),
                "in_days": offset,
                "in_days_ne": to_nepali_digits(offset),
                "name_ne": ne,
                "name_en": en,
                "tithi": pc.get("tithi", {}).get("nepali", ""),
            })
    events.sort(key=lambda e: (e["date"], e["name_ne"]))
    return events[:40]


def clear_cache() -> None:
    """Drop cached digests (e.g. after ayanamsha setting change)."""
    _cached_panchang.cache_clear()
    _cached_muhurta.cache_clear()


# ── Internal helpers ─────────────────────────────────────────────────────────

def _digest_summary(
    pc: Dict[str, Any],
    festivals: List[tuple[str, str]],
    is_ne: bool,
    day: Optional[_date] = None,
) -> str:
    tithi = pc.get("tithi", {})
    nak = pc.get("nakshatra", {})
    if is_ne:
        tithi_n = tithi.get("nepali", "")
        nak_n = nak.get("nepali", "")
        fest = " · ".join(n for n, _ in festivals)
        parts = [f"तिथि: {tithi_n}, नक्षत्र: {nak_n}"]
        if day is not None:
            bs = _bs_date(day)
            if bs:
                parts.append(_format_bs_date(bs, "ne"))
        return " · ".join(parts) + (f" · {fest}" if fest else "")
    tithi_e = tithi.get("name", "")
    nak_e = nak.get("name", "")
    fest = " · ".join(e for _, e in festivals)
    parts = [f"Tithi: {tithi_e}, Nakshatra: {nak_e}"]
    if day is not None:
        bs = _bs_date(day)
        if bs:
            parts.append(_format_bs_date(bs, "en"))
    return " · ".join(parts) + (f" · {fest}" if fest else "")
