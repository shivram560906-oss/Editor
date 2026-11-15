# -*- coding: utf-8 -*-
"""
Nepali Festival Engine - Calculates and manages Nepali festivals, holidays,
and auspicious dates (साइत) based on traditional Nepali calendar (Bikram Sambat).

This module is fully offline. It uses the bundled authoritative data from
reminder_panchang (FESTIVALS_BS) for fixed BS festivals and the panchang
engine for tithi-based observances (ekadashi, purnima, amavasya).

No network requests are made. All calculations happen locally using the
bundled astronomical engine and the nepali_datetime library.
"""
from __future__ import annotations

import datetime
import math
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from . import julian, panchang
from . import reminder_panchang


# ── Festival data (authoritative, bundled with the engine) ───────────────────
FESTIVALS_BS = dict(reminder_panchang.FESTIVALS_BS)
TITHI_OBSERVANCES = dict(reminder_panchang.TITHI_OBSERVANCES)

# ── Government/public holidays (fixed BS dates, authoritative source) ───────
GOVERNMENT_HOLIDAYS = {
    (1, 1): "Bikram Sambat New Year",
    (1, 9): "Mata Tirtha Aunsi",
    (1, 15): "Prithvi Jayanti",
    (2, 15): "Sita Puja / Sita Vivah",
    (3, 15): "Mohi (Asare Purnima)",
    (4, 15): "Janai Purnima",
    (4, 16): "Krishna Janmashtami",
    (5, 1): "Rishi Panchami",
    (5, 11): "Gai Jatra",
    (5, 15): "Haribodhini Ekadashi",
    (6, 1): "Indra Jatra",
    (6, 9): "Ghatasthapana",
    (6, 10): "Fulpati",
    (6, 15): "Vijaya Dashami (Teej)",
    (6, 16): "Kojagrat Purnima",
    (7, 1): "Yamapanchak Begins",
    (7, 2): "Kag Tihar",
    (7, 3): "Kukur Tihar",
    (7, 4): "Laxmi Puja",
    (7, 5): "Govardhan Puja",
    (7, 6): "Bhai Tika",
    (7, 15): "Dhanya Purnima",
    (8, 1): "Maghe Sankranti / Maghi",
    (8, 8): "Basant Panchami (Saraswati Puja)",
    (9, 5): "Maha Shivaratri",
    (9, 15): "Holi",
    (10, 8): "Chaite Dashain",
    (10, 12): "Guthi Parva",
    (11, 1): "Baisakhe Sankranti",
    (12, 1): "Jethe Sankranti",
}

# ── Auspicious days (traditional, recurring by BS date) ──────────────────────
SAIYIT_AUSPICIOUS = [
    {
        "name": "Saptami",
        "meaning": "Weekday (7th day of fortnight)",
        "use": "General rituals, prayers",
    },
    {
        "name": "Shravani",
        "meaning": "Day of Goddess Sita worship",
        "use": "Prayer, meditation",
    },
    {
        "name": "Uttarayana",
        "meaning": "Northern movement of Sun (mid-April)",
        "use": "Auspicious for travel, business",
    },
    {
        "name": "Maha Shivaratri",
        "meaning": "Great Shiva Festival",
        "use": "Very strong auspiciousness",
    },
    {
        "name": "Vijayadashami",
        "meaning": "Victory of Good over Evil",
        "use": "Strong auspiciousness",
    },
]


def _to_nepali_digits(value) -> str:
    """Convert ASCII digits in a value to Devanagari (Nepali) digits."""
    digits = "०१२३४५६७८९"
    return "".join(digits[int(ch)] if ch.isdigit() else ch for ch in str(value))


def _format_bs_date(bs: Optional[Tuple[int, int, int]], language: str = "en") -> str:
    """Format a (year, month, day) BS tuple as a readable date string."""
    if not bs:
        return ""
    year, month, day = bs
    if language == "ne":
        months = reminder_panchang.BS_MONTHS_NE
        return f"{_to_nepali_digits(day)} {months[month - 1]} {_to_nepali_digits(year)}"
    months = reminder_panchang.BS_MONTHS_EN
    return f"{day} {months[month - 1]} {year}"


def _bs_date(ad: datetime.date) -> Optional[Tuple[int, int, int]]:
    """Return (year, month, day) in Bikram Sambat, or None when unavailable."""
    try:
        import nepali_datetime
        bs = nepali_datetime.date.from_datetime_date(ad)
        return (bs.year, bs.month, bs.day)
    except Exception:
        return None


@lru_cache(maxsize=64)
def _cached_panchang(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    timezone: float,
    ayanamsha_type: str,
) -> Dict[str, Any]:
    """Full panchang for the local civil date (evaluated at local sunrise)."""
    jd_noon = julian.datetime_to_jd(year, month, day, 12, 0, 0, timezone)
    sunrise_jd = panchang.calculate_sunrise_jd(jd_noon, latitude, longitude, timezone)
    sun_sid, moon_sid = panchang._sidereal_longitudes(sunrise_jd, ayanamsha_type)
    return panchang.calculate_panchang(
        sunrise_jd,
        sun_sid,
        moon_sid,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        sunrise_jd=sunrise_jd,
        ayanamsha_type=ayanamsha_type,
    )


def _festivals_for(ad: datetime.date, panchang_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return list of festival/observance dictionaries for the day."""
    results: List[Dict[str, str]] = []
    bs = _bs_date(ad)
    if bs and bs[1:] in FESTIVALS_BS:
        nepali, english = FESTIVALS_BS[bs[1:]]
        results.append({
            "name": english,
            "name_ne": nepali,
            "category": "festival",
            "date_bs": _format_bs_date(bs, "ne"),
            "date_bs_en": _format_bs_date(bs, "en"),
        })

    tithi = panchang_data.get("tithi", {})
    tithi_idx = tithi.get("index")
    paksha = str(tithi.get("paksha") or "").lower()
    if tithi_idx:
        tithi_idx = int(tithi_idx)
        if paksha == "waxing" and tithi_idx == 15:
            results.append({
                "name": "Purnima (Full Moon)",
                "name_ne": "पूर्णिमा",
                "category": "observance",
                "date_bs": _format_bs_date(bs, "ne"),
                "date_bs_en": _format_bs_date(bs, "en"),
            })
        elif paksha == "waning" and tithi_idx == 30:
            results.append({
                "name": "Amavasya (New Moon)",
                "name_ne": "औंसी",
                "category": "observance",
                "date_bs": _format_bs_date(bs, "ne"),
                "date_bs_en": _format_bs_date(bs, "en"),
            })
        elif tithi_idx in TITHI_OBSERVANCES:
            nepali, english = TITHI_OBSERVANCES[tithi_idx]
            results.append({
                "name": english,
                "name_ne": nepali,
                "category": "observance",
                "date_bs": _format_bs_date(bs, "ne"),
                "date_bs_en": _format_bs_date(bs, "en"),
            })

    # Deduplicate while preserving order.
    seen = set()
    unique: List[Dict[str, str]] = []
    for item in results:
        key = (item["name"], item["category"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


class NepaliFestivalEngine:
    """Engine for calculating and managing Nepali festivals, holidays,
    and auspicious dates (साइत). Fully offline; no network dependencies."""

    def __init__(self, location: str = "Kathmandu", latitude: float = 27.7172, longitude: float = 85.3240, timezone: float = 5.75, ayanamsha_type: str = "LAHIRI"):
        """Initialize the festival engine with optional location."""
        self.location = location
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.timezone = float(timezone)
        self.ayanamsha_type = str(ayanamsha_type or "LAHIRI").upper()
        self._cache: Dict[str, Any] = {}

    def get_daily_festivals(self, ad_date: datetime.date | str) -> List[Dict[str, str]]:
        """
        Return all festivals and observances for a given civil date.

        Args:
            ad_date: Gregorian date (datetime.date or YYYY-MM-DD string)

        Returns:
            List of festival dictionaries with name, name_ne, category,
            date_bs, date_bs_en
        """
        if isinstance(ad_date, str):
            ad_date = datetime.date.fromisoformat(ad_date[:10])
        panchang_data = _cached_panchang(
            ad_date.year,
            ad_date.month,
            ad_date.day,
            self.latitude,
            self.longitude,
            self.timezone,
            self.ayanamsha_type,
        )
        return _festivals_for(ad_date, panchang_data)

    def get_festivals_for_year(self, biksam_year: int) -> List[Dict[str, Any]]:
        """
        Return festivals occurring in a given Bikram Sambat year.

        Args:
            biksam_year: Bikram Sambat year (e.g., 2083 for 2026)

        Returns:
            List of festival dictionaries with name, name_ne, date_bs,
            date_bs_en, category
        """
        festivals: List[Dict[str, Any]] = []
        for (month, day), (nepali, english) in sorted(FESTIVALS_BS.items()):
            if month == 1 and day == 1:
                continue
            bs = (biksam_year, month, day)
            try:
                ad = __import__("nepali_datetime").date(*bs).to_datetime_date()
            except Exception:
                continue
            festivals.append({
                "name": english,
                "name_ne": nepali,
                "date": ad.isoformat(),
                "date_bs": _format_bs_date(bs, "ne"),
                "date_bs_en": _format_bs_date(bs, "en"),
                "category": "festival",
                "source": "fixed_bs",
            })
        festivals.sort(key=lambda x: (x["date"], x["name"]))
        return festivals

    def get_government_holidays(self, biksam_year: int) -> List[Dict[str, Any]]:
        """
        Get government/public holidays for a given Bikram Sambat year.

        Args:
            biksam_year: Bikram Sambat year

        Returns:
            List of holiday dictionaries with name, date, date_bs, date_bs_en,
            observance
        """
        holidays: List[Dict[str, Any]] = []
        for (month, day), name in sorted(GOVERNMENT_HOLIDAYS.items()):
            bs = (biksam_year, month, day)
            try:
                ad = __import__("nepali_datetime").date(*bs).to_datetime_date()
            except Exception:
                continue
            holidays.append({
                "name": name,
                "date": ad.isoformat(),
                "date_bs": _format_bs_date(bs, "ne"),
                "date_bs_en": _format_bs_date(bs, "en"),
                "observance": "Public Holiday",
            })
        holidays.sort(key=lambda x: (x["date"], x["name"]))
        return holidays

    def get_auspicious_days(self, biksam_year: int) -> List[Dict[str, Any]]:
        """
        Get auspicious days (साइत) for a given Bikram Sambat year.

        Args:
            biksam_year: Bikram Sambat year

        Returns:
            List of auspicious day dictionaries
        """
        del biksam_year
        return [dict(item) for item in SAIYIT_AUSPICIOUS]

    def calculate_auspicious_day(self, biksam_year: int, day_of_month: int) -> Optional[str]:
        """
        Determine if a given day of month is auspicious (साइत).

        Args:
            biksam_year: Bikram Sambat year
            day_of_month: Day number (1-31)

        Returns:
            Name of auspicious day or None if not auspicious
        """
        auspicious_days = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29]
        if day_of_month in auspicious_days:
            return f"{_to_nepali_digits(day_of_month)}.{_to_nepali_digits(biksam_year)} - Auspicious Day"
        return None

    def get_upcoming_events(
        self,
        start_ad_date: datetime.date | str,
        days: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        List notable events in the next ``days`` days.

        Args:
            start_ad_date: Starting civil date
            days: Number of days to scan forward

        Returns:
            List of event dictionaries sorted by date
        """
        if isinstance(start_ad_date, str):
            start_ad_date = datetime.date.fromisoformat(start_ad_date[:10])
        events: List[Dict[str, Any]] = []
        seen: set = set()
        for offset in range(1, days + 1):
            ad = start_ad_date + datetime.timedelta(days=offset)
            festivals = self.get_daily_festivals(ad)
            for festival in festivals:
                key = (ad.isoformat(), festival["name"])
                if key in seen:
                    continue
                seen.add(key)
                festival = dict(festival)
                festival["date"] = ad.isoformat()
                festival["in_days"] = offset
                events.append(festival)
        events.sort(key=lambda x: (x["date"], x["name"]))
        return events[:40]

    def get_festival_info(self, biksam_year: int) -> Dict[str, Any]:
        """
        Get detailed festival information for a given year.

        Args:
            biksam_year: Bikram Sambat year

        Returns:
            Dictionary with festivals, holidays, and auspicious days info
        """
        return {
            "year": biksam_year,
            "festivals": self.get_festivals_for_year(biksam_year),
            "government_holidays": self.get_government_holidays(biksam_year),
            "auspicious_days": self.get_auspicious_days(biksam_year),
        }


def initialize_festival_engine(location: str = "Kathmandu") -> NepaliFestivalEngine:
    """Factory function to create and initialize the festival engine."""
    return NepaliFestivalEngine(location=location)
