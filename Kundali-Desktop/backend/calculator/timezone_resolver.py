"""Offline city and historical timezone resolution.

The curated city list remains the authoritative coordinate source.  IANA
``zoneinfo`` supplies date-specific civil offsets when a city has a known
zone identifier; callers can still use the legacy numeric offset unchanged.
"""

from __future__ import annotations

import datetime as _datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, Optional

from cities_data import CITIES


# Country defaults cover the curated dataset. City-specific zones handle
# countries spanning multiple IANA regions.
_COUNTRY_ZONES = {
    "Nepal": "Asia/Kathmandu",
    "India": "Asia/Kolkata",
    "Bangladesh": "Asia/Dhaka",
    "Pakistan": "Asia/Karachi",
    "Sri Lanka": "Asia/Colombo",
    "Bhutan": "Asia/Thimphu",
    "Myanmar": "Asia/Yangon",
    "Thailand": "Asia/Bangkok",
    "Malaysia": "Asia/Kuala_Lumpur",
    "Singapore": "Asia/Singapore",
    "Indonesia": "Asia/Jakarta",
    "China": "Asia/Shanghai",
    "Taiwan": "Asia/Taipei",
    "Japan": "Asia/Tokyo",
    "South Korea": "Asia/Seoul",
    "Philippines": "Asia/Manila",
    "Vietnam": "Asia/Ho_Chi_Minh",
    "UAE": "Asia/Dubai",
    "Saudi Arabia": "Asia/Riyadh",
    "Qatar": "Asia/Qatar",
    "Kuwait": "Asia/Kuwait",
    "Bahrain": "Asia/Bahrain",
    "Oman": "Asia/Muscat",
    "Jordan": "Asia/Amman",
    "Lebanon": "Asia/Beirut",
    "Israel": "Asia/Jerusalem",
    "Iraq": "Asia/Baghdad",
    "Iran": "Asia/Tehran",
    "Turkey": "Europe/Istanbul",
    "UK": "Europe/London",
    "Ireland": "Europe/Dublin",
    "France": "Europe/Paris",
    "Germany": "Europe/Berlin",
    "Italy": "Europe/Rome",
    "Spain": "Europe/Madrid",
    "Portugal": "Europe/Lisbon",
    "Netherlands": "Europe/Amsterdam",
    "Belgium": "Europe/Brussels",
    "Austria": "Europe/Vienna",
    "Switzerland": "Europe/Zurich",
    "Sweden": "Europe/Stockholm",
    "Norway": "Europe/Oslo",
    "Denmark": "Europe/Copenhagen",
    "Finland": "Europe/Helsinki",
    "Poland": "Europe/Warsaw",
    "Czech Republic": "Europe/Prague",
    "Hungary": "Europe/Budapest",
    "Greece": "Europe/Athens",
    "Russia": "Europe/Moscow",
    "USA": "America/New_York",
    "Canada": "America/Toronto",
    "Mexico": "America/Mexico_City",
    "Brazil": "America/Sao_Paulo",
    "Argentina": "America/Argentina/Buenos_Aires",
    "Chile": "America/Santiago",
    "Peru": "America/Lima",
    "Colombia": "America/Bogota",
    "Egypt": "Africa/Cairo",
    "Kenya": "Africa/Nairobi",
    "South Africa": "Africa/Johannesburg",
    "Nigeria": "Africa/Lagos",
    "Ethiopia": "Africa/Addis_Ababa",
    "Morocco": "Africa/Casablanca",
    "Australia": "Australia/Sydney",
    "New Zealand": "Pacific/Auckland",
}

_CITY_ZONES = {
    # USA - Pacific
    "Los Angeles": "America/Los_Angeles", "San Francisco": "America/Los_Angeles",
    "San Diego": "America/Los_Angeles", "San Jose": "America/Los_Angeles",
    "Sacramento": "America/Los_Angeles", "Oakland": "America/Los_Angeles",
    "Fremont": "America/Los_Angeles", "Sunnyvale": "America/Los_Angeles",
    "Santa Clara": "America/Los_Angeles", "Irvine": "America/Los_Angeles",
    "Long Beach": "America/Los_Angeles", "Fresno": "America/Los_Angeles",
    "Bakersfield": "America/Los_Angeles", "Anaheim": "America/Los_Angeles",
    "Riverside": "America/Los_Angeles", "Seattle": "America/Los_Angeles",
    "Bellevue": "America/Los_Angeles", "Redmond": "America/Los_Angeles",
    "Tacoma": "America/Los_Angeles", "Spokane": "America/Los_Angeles",
    "Portland (Oregon)": "America/Los_Angeles", "Eugene": "America/Los_Angeles",
    "Salem (Oregon)": "America/Los_Angeles", "Las Vegas": "America/Los_Angeles",
    "Reno": "America/Los_Angeles", "Henderson": "America/Los_Angeles",

    # USA - Mountain
    "Denver": "America/Denver", "Colorado Springs": "America/Denver",
    "Aurora": "America/Denver", "Boulder": "America/Denver",
    "Salt Lake City": "America/Denver", "Provo": "America/Denver",
    "Phoenix": "America/Phoenix", "Tucson": "America/Phoenix",
    "Mesa": "America/Phoenix", "Chandler": "America/Phoenix",
    "Scottsdale": "America/Phoenix", "Albuquerque": "America/Denver",
    "Santa Fe": "America/Denver", "El Paso": "America/Denver",
    "Boise": "America/Boise", "Billings": "America/Denver",
    "Cheyenne": "America/Denver",

    # USA - Central
    "Chicago": "America/Chicago", "Naperville": "America/Chicago",
    "Houston": "America/Chicago", "Dallas": "America/Chicago",
    "Fort Worth": "America/Chicago", "Austin": "America/Chicago",
    "San Antonio": "America/Chicago", "Plano": "America/Chicago",
    "Irving": "America/Chicago", "Frisco": "America/Chicago",
    "Minneapolis": "America/Chicago", "St. Paul": "America/Chicago",
    "Milwaukee": "America/Chicago", "Madison": "America/Chicago",
    "St. Louis": "America/Chicago", "Kansas City": "America/Chicago",
    "Nashville": "America/Chicago", "Memphis": "America/Chicago",
    "New Orleans": "America/Chicago", "Baton Rouge": "America/Chicago",
    "Oklahoma City": "America/Chicago", "Tulsa": "America/Chicago",
    "Omaha": "America/Chicago", "Lincoln": "America/Chicago",
    "Des Moines": "America/Chicago", "Cedar Rapids": "America/Chicago",
    "Wichita": "America/Chicago", "Little Rock": "America/Chicago",
    "Jackson": "America/Chicago", "Birmingham (USA)": "America/Chicago",
    "Fargo": "America/Chicago", "Sioux Falls": "America/Chicago",

    # USA - Eastern
    "New York": "America/New_York", "Brooklyn": "America/New_York",
    "Queens": "America/New_York", "Buffalo": "America/New_York",
    "Albany": "America/New_York", "Boston": "America/New_York",
    "Cambridge": "America/New_York", "Worcester": "America/New_York",
    "Philadelphia": "America/New_York", "Pittsburgh": "America/New_York",
    "Allentown": "America/New_York", "Washington DC": "America/New_York",
    "Baltimore": "America/New_York", "Richmond": "America/New_York",
    "Virginia Beach": "America/New_York", "Norfolk": "America/New_York",
    "Arlington": "America/New_York", "Atlanta": "America/New_York",
    "Augusta": "America/New_York", "Savannah": "America/New_York",
    "Miami": "America/New_York", "Orlando": "America/New_York",
    "Tampa": "America/New_York", "Jacksonville": "America/New_York",
    "Fort Lauderdale": "America/New_York", "Tallahassee": "America/New_York",
    "Charlotte": "America/New_York", "Raleigh": "America/New_York",
    "Durham": "America/New_York", "Greensboro": "America/New_York",
    "Columbia": "America/New_York", "Charleston": "America/New_York",
    "Detroit": "America/New_York", "Grand Rapids": "America/New_York",
    "Ann Arbor": "America/New_York", "Columbus": "America/New_York",
    "Cleveland": "America/New_York", "Cincinnati": "America/New_York",
    "Indianapolis": "America/Indiana/Indianapolis", "Fort Wayne": "America/Indiana/Indianapolis",
    "Louisville": "America/Kentucky/Louisville", "Lexington": "America/New_York",
    "Jersey City": "America/New_York", "Newark": "America/New_York",
    "Edison": "America/New_York", "Hartford": "America/New_York",
    "New Haven": "America/New_York", "Providence": "America/New_York",
    "Portland (Maine)": "America/New_York", "Manchester (NH)": "America/New_York",
    "Burlington": "America/New_York", "Wilmington": "America/New_York",
    "Charleston (WV)": "America/New_York",

    # USA - Alaska & Hawaii
    "Anchorage": "America/Anchorage", "Fairbanks": "America/Anchorage",
    "Juneau": "America/Juneau", "Honolulu": "Pacific/Honolulu",
    "Maui (Kahului)": "Pacific/Honolulu",

    # Canada
    "Toronto": "America/Toronto", "Mississauga": "America/Toronto",
    "Brampton": "America/Toronto", "Ottawa": "America/Toronto",
    "Hamilton": "America/Toronto", "Kitchener": "America/Toronto",
    "London (Canada)": "America/Toronto", "Montreal": "America/Toronto",
    "Quebec City": "America/Toronto", "Laval": "America/Toronto",
    "Vancouver": "America/Vancouver", "Surrey": "America/Vancouver",
    "Burnaby": "America/Vancouver", "Victoria": "America/Vancouver",
    "Calgary": "America/Edmonton", "Edmonton": "America/Edmonton",
    "Winnipeg": "America/Winnipeg", "Saskatoon": "America/Regina",
    "Regina": "America/Regina", "Halifax": "America/Halifax",
    "St. John's": "America/St_Johns",

    # Australia
    "Sydney": "Australia/Sydney", "Melbourne": "Australia/Melbourne",
    "Brisbane": "Australia/Brisbane", "Perth": "Australia/Perth",
    "Adelaide": "Australia/Adelaide", "Gold Coast": "Australia/Brisbane",
    "Canberra": "Australia/Sydney", "Newcastle (Australia)": "Australia/Sydney",
    "Wollongong": "Australia/Sydney", "Hobart": "Australia/Hobart",
    "Darwin": "Australia/Darwin",

    # Indonesia
    "Bali (Denpasar)": "Asia/Makassar",
}


def _city_zone(city: dict[str, Any]) -> Optional[str]:
    return _CITY_ZONES.get(city["name"]) or _COUNTRY_ZONES.get(city["country"])


def _find_city(query: Optional[str]) -> Optional[dict[str, Any]]:
    needle = (query or "").strip().casefold()
    if not needle:
        return None
    for city in CITIES:
        if city["name"].casefold() == needle:
            return city
    for city in CITIES:
        if needle in city["name"].casefold() or needle in city["country"].casefold():
            return city
    return None


def enrich_city(city: dict[str, Any]) -> dict[str, Any]:
    """Return an additive API-safe city record with timezone provenance."""
    zone = _city_zone(city)
    return {
        "name": city["name"], "country": city["country"],
        "latitude": city["lat"], "longitude": city["lon"],
        "timezone": city["tz"], "timezone_id": zone,
        "standard_timezone": city["tz"],
        "dst_supported": bool(zone), "source": "curated_offline",
    }


def resolve_timezone(
    birth_date: str,
    birth_time: str,
    numeric_offset: float,
    timezone_id: Optional[str] = None,
    city: Optional[str] = None,
) -> dict[str, Any]:
    """Resolve the effective offset while preserving numeric fallback behavior."""
    zone_id = timezone_id or (_city_zone(_find_city(city)) if _find_city(city) else None)
    result = {
        "timezone": float(numeric_offset), "timezone_id": zone_id,
        "standard_timezone": float(numeric_offset), "dst_offset": 0.0,
        "is_dst": False, "timezone_source": "numeric_fallback",
        "timezone_resolution": "legacy_numeric_offset",
    }
    if not zone_id:
        return result
    try:
        zone = ZoneInfo(zone_id)
    except (ZoneInfoNotFoundError, ValueError):
        return result
    date = _datetime.date.fromisoformat(birth_date)
    parts = [int(float(part)) for part in birth_time.split(":")]
    local = _datetime.datetime(date.year, date.month, date.day, *parts, tzinfo=zone)
    offset = local.utcoffset() or _datetime.timedelta(0)
    dst = local.dst() or _datetime.timedelta(0)
    standard = offset - dst
    result.update({
        "timezone": offset.total_seconds() / 3600.0,
        "standard_timezone": standard.total_seconds() / 3600.0,
        "dst_offset": dst.total_seconds() / 3600.0,
        "is_dst": bool(dst), "timezone_source": "offline_zoneinfo",
        "timezone_resolution": "historical_iana_rules",
    })
    return result


def search_cities(query: str, limit: int = 20) -> list[dict[str, Any]]:
    needle = (query or "").strip().casefold()
    if not needle:
        return []
    return [enrich_city(city) for city in CITIES
            if needle in city["name"].casefold() or needle in city["country"].casefold()][:max(1, min(limit, 100))]
