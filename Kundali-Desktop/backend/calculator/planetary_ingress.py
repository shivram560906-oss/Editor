"""Sidereal planetary sign-ingress calculations for transit reports.

This module is deliberately independent of a natal chart. It scans geocentric
positions, detects every 30-degree sidereal boundary crossing (including
retrograde re-entry), and refines each crossing to approximately one second.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Tuple

from . import ayanamsha, julian, planetary_positions

REPORT_PLANETS = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
TRANSIT_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
SIGN_NAMES_EN = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
SIGN_NAMES_NE = ("मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन")
PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल", "Mercury": "बुध",
    "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु",
}
NEPAL_OFFSET_HOURS = 5.75
SCAN_STEP_DAYS = 0.25
PLANET_SCAN_STEP_DAYS = {
    "Moon": 0.25, "Sun": 1.0, "Mercury": 0.25, "Venus": 0.25,
    "Mars": 0.5, "Jupiter": 1.0, "Saturn": 1.0, "Rahu": 2.0, "Ketu": 2.0,
}
REFINEMENT_DAYS = 1.0 / 86400.0
CURRENT_INGRESS_LOOKBACK_DAYS = 6 * 365.25


def _date_to_jd(value: dt.date) -> float:
    return julian.datetime_to_jd(value.year, value.month, value.day, 0, 0, 0.0, NEPAL_OFFSET_HOURS)


def _jd_to_datetime(jd_value: float, offset_hours: float = NEPAL_OFFSET_HOURS) -> dt.datetime:
    """Convert UT Julian day to an aware fixed-offset local datetime."""
    unix_seconds = (jd_value - 2440587.5) * 86400.0
    utc_value = dt.datetime.fromtimestamp(unix_seconds, tz=dt.timezone.utc)
    return utc_value.astimezone(dt.timezone(dt.timedelta(hours=offset_hours)))


def _sidereal_positions(jd_value: float, ayanamsha_type: str, node_type: str) -> Dict[str, float]:
    centuries = julian.jd_to_julian_centuries(jd_value)
    tropical = planetary_positions.get_all_tropical_positions(centuries, jd=jd_value, node_type=node_type)
    aya = ayanamsha.get_ayanamsha(ayanamsha_type, centuries)
    return {name: (float(values[0]) - aya) % 360.0 for name, values in tropical.items() if name in TRANSIT_PLANETS}


def _sign(longitude: float) -> int:
    return int(longitude // 30.0) % 12


def _signed_motion(before: float, after: float) -> float:
    return (after - before + 180.0) % 360.0 - 180.0


def _refine_crossing(
    planet: str,
    lower_jd: float,
    upper_jd: float,
    old_sign: int,
    ayanamsha_type: str,
    node_type: str,
) -> float:
    """Bisect the first instant at which the planet no longer occupies old_sign."""
    lo, hi = lower_jd, upper_jd
    while hi - lo > REFINEMENT_DAYS:
        middle = (lo + hi) / 2.0
        longitude = _sidereal_positions(middle, ayanamsha_type, node_type)[planet]
        if _sign(longitude) == old_sign:
            lo = middle
        else:
            hi = middle
    return hi


def _event(planet: str, jd_value: float, ayanamsha_type: str, node_type: str) -> Dict[str, Any]:
    epsilon = 2.0 / 1440.0
    before = _sidereal_positions(jd_value - epsilon, ayanamsha_type, node_type)[planet]
    after = _sidereal_positions(jd_value + epsilon, ayanamsha_type, node_type)[planet]
    from_sign = _sign(before)
    to_sign = _sign(after)
    direction = "direct" if _signed_motion(before, after) >= 0 else "retrograde"
    local_time = _jd_to_datetime(jd_value)
    return {
        "planet": planet,
        "planet_ne": PLANET_NAMES_NE[planet],
        "from_sign": from_sign + 1,
        "from_sign_en": SIGN_NAMES_EN[from_sign],
        "from_sign_ne": SIGN_NAMES_NE[from_sign],
        "to_sign": to_sign + 1,
        "to_sign_en": SIGN_NAMES_EN[to_sign],
        "to_sign_ne": SIGN_NAMES_NE[to_sign],
        "direction": direction,
        "at": local_time.isoformat(timespec="seconds"),
        "julian_day": round(jd_value, 8),
    }


def _find_current_sign_ingresses(
    start_jd: float,
    initial: Dict[str, float],
    ayanamsha_type: str,
    node_type: str,
) -> Dict[str, Dict[str, Any]]:
    """Find when every planet entered the sign occupied at the report boundary."""
    unresolved = set(REPORT_PLANETS)
    ingresses: Dict[str, Dict[str, Any]] = {}
    upper_jd = start_jd
    upper_positions = dict(initial)
    earliest_jd = start_jd - CURRENT_INGRESS_LOOKBACK_DAYS

    while unresolved and upper_jd > earliest_jd:
        lower_jd = max(upper_jd - SCAN_STEP_DAYS, earliest_jd)
        lower_positions = _sidereal_positions(lower_jd, ayanamsha_type, node_type)
        for planet in tuple(unresolved):
            lower_sign = _sign(lower_positions[planet])
            upper_sign = _sign(upper_positions[planet])
            if lower_sign != upper_sign:
                crossing = _refine_crossing(
                    planet, lower_jd, upper_jd, lower_sign, ayanamsha_type, node_type
                )
                ingresses[planet] = _event(planet, crossing, ayanamsha_type, node_type)
                unresolved.remove(planet)
        upper_jd = lower_jd
        upper_positions = lower_positions

    return ingresses


def _scan_planet_events(
    planet: str,
    start_jd: float,
    end_jd: float,
    ayanamsha_type: str,
    node_type: str,
) -> List[Dict[str, Any]]:
    """Scan one planet only, preserving true direct/retrograde ingress order."""
    events: List[Dict[str, Any]] = []
    cursor = start_jd
    scan_step = PLANET_SCAN_STEP_DAYS[planet]
    previous = _sidereal_positions(cursor, ayanamsha_type, node_type)[planet]
    while cursor < end_jd:
        next_jd = min(cursor + scan_step, end_jd)
        current = _sidereal_positions(next_jd, ayanamsha_type, node_type)[planet]
        old_sign = _sign(previous)
        if old_sign != _sign(current):
            crossing = _refine_crossing(
                planet, cursor, next_jd, old_sign, ayanamsha_type, node_type
            )
            events.append(_event(planet, crossing, ayanamsha_type, node_type))
        cursor = next_jd
        previous = current
    return events


def _planet_search_days(planet: str, record_count: int) -> float:
    """Return a conservative scan span for the requested number of transitions."""
    typical_days = {
        "Moon": 3.5, "Sun": 40.0, "Mercury": 55.0, "Venus": 75.0,
        "Mars": 110.0, "Jupiter": 460.0, "Saturn": 1100.0,
        "Rahu": 650.0, "Ketu": 650.0,
    }
    return max(45.0, typical_days[planet] * (record_count + 2))


def calculate_planetary_transition_window(
    reference_date: dt.date,
    planet: str,
    before: int = 3,
    after: int = 3,
    ayanamsha_type: str = "LAHIRI",
    node_type: str = "MEAN",
) -> Dict[str, Any]:
    """Return a small chronological occupancy window around ``reference_date``.

    Counts are deliberately cursor-like rather than a hard date range. A client can
    increase either count to reveal older/newer records without loading a century of
    lunar transitions. Serial numbers are anchored to the current row and therefore
    remain stable when records are prepended or appended.
    """
    if planet not in TRANSIT_PLANETS:
        raise ValueError("planet is not supported")
    if not 0 <= before <= 100 or not 0 <= after <= 100:
        raise ValueError("before and after must be between 0 and 100")

    reference_jd = _date_to_jd(reference_date)
    wanted_before = before + 1  # Includes the ingress beginning the active row.
    backward_days = _planet_search_days(planet, wanted_before)
    forward_days = _planet_search_days(planet, after + 1)

    previous_events: List[Dict[str, Any]] = []
    for _ in range(8):
        previous_events = _scan_planet_events(
            planet, reference_jd - backward_days, reference_jd,
            ayanamsha_type, node_type,
        )
        if len(previous_events) >= wanted_before:
            break
        backward_days *= 2

    next_events: List[Dict[str, Any]] = []
    for _ in range(8):
        next_events = _scan_planet_events(
            planet, reference_jd, reference_jd + forward_days,
            ayanamsha_type, node_type,
        )
        if len(next_events) >= after + 1:
            break
        forward_days *= 2

    previous_events = previous_events[-wanted_before:]
    next_events = next_events[:after + 1]
    boundaries = previous_events + next_events
    transitions: List[Dict[str, Any]] = []
    active_index = max(0, len(previous_events) - 1)
    for index, (entry, exit_event) in enumerate(zip(boundaries, boundaries[1:])):
        sign_index = int(entry["to_sign"]) - 1
        transitions.append({
            "serial": index - active_index,
            "planet": planet,
            "planet_ne": PLANET_NAMES_NE[planet],
            "sign": sign_index + 1,
            "sign_en": SIGN_NAMES_EN[sign_index],
            "sign_ne": SIGN_NAMES_NE[sign_index],
            "start": entry["at"],
            "end": exit_event["at"],
            "entry_direction": entry["direction"],
            "next_sign": int(exit_event["to_sign"]),
            "next_sign_en": exit_event["to_sign_en"],
            "next_sign_ne": exit_event["to_sign_ne"],
            "is_current": index == active_index,
        })

    current = next((item for item in transitions if item["is_current"]), None)
    return {
        "planet": planet,
        "planet_ne": PLANET_NAMES_NE[planet],
        "reference_date": reference_date.isoformat(),
        "timezone": "Asia/Kathmandu",
        "ayanamsha_type": str(ayanamsha_type).upper(),
        "node_type": str(node_type).upper(),
        "ephemeris": "SWISS" if planetary_positions.swe is not None else "ANALYTICAL_FALLBACK",
        "requested_before": before,
        "requested_after": after,
        "has_more_before": len(previous_events) >= wanted_before,
        "has_more_after": len(next_events) >= after + 1,
        "unavailable_before_reason": None if previous_events else "Older ephemeris data is unavailable",
        "unavailable_after_reason": None if next_events else "Newer ephemeris data is unavailable",
        "current": current,
        "transitions": transitions,
    }


def calculate_planetary_ingresses(
    start_date: dt.date,
    end_date: dt.date,
    ayanamsha_type: str = "LAHIRI",
    node_type: str = "MEAN",
) -> Dict[str, Any]:
    """Return all non-lunar sidereal sign periods and ingress events in a date range."""
    if end_date <= start_date:
        raise ValueError("end_date must be after start_date")
    try:
        five_year_limit = start_date.replace(year=start_date.year + 5)
    except ValueError:
        five_year_limit = start_date.replace(year=start_date.year + 5, day=28)
    if end_date > five_year_limit:
        raise ValueError("date range cannot exceed five years")

    start_jd = _date_to_jd(start_date)
    end_jd = _date_to_jd(end_date)
    initial = _sidereal_positions(start_jd, ayanamsha_type, node_type)
    current_ingresses = _find_current_sign_ingresses(
        start_jd, initial, ayanamsha_type, node_type
    )
    previous_longitudes = dict(initial)
    events: List[Dict[str, Any]] = []
    cursor = start_jd

    while cursor < end_jd:
        next_jd = min(cursor + SCAN_STEP_DAYS, end_jd)
        current = _sidereal_positions(next_jd, ayanamsha_type, node_type)
        for planet in REPORT_PLANETS:
            old_sign = _sign(previous_longitudes[planet])
            new_sign = _sign(current[planet])
            if old_sign != new_sign:
                crossing = _refine_crossing(planet, cursor, next_jd, old_sign, ayanamsha_type, node_type)
                events.append(_event(planet, crossing, ayanamsha_type, node_type))
        cursor = next_jd
        previous_longitudes = current

    events.sort(key=lambda item: (item["julian_day"], REPORT_PLANETS.index(item["planet"])))
    periods: List[Dict[str, Any]] = []
    for planet in REPORT_PLANETS:
        planet_events = [item for item in events if item["planet"] == planet]
        current_ingress = current_ingresses.get(planet)
        period_start_jd = (
            float(current_ingress["julian_day"]) if current_ingress else start_jd
        )
        sign_index = _sign(initial[planet])
        started_before_range = True
        ingress_direction = (
            str(current_ingress["direction"]) if current_ingress else None
        )
        for ingress in planet_events:
            period_end_jd = float(ingress["julian_day"])
            periods.append({
                "planet": planet,
                "planet_ne": PLANET_NAMES_NE[planet],
                "sign": sign_index + 1,
                "sign_en": SIGN_NAMES_EN[sign_index],
                "sign_ne": SIGN_NAMES_NE[sign_index],
                "start": _jd_to_datetime(period_start_jd).isoformat(timespec="seconds"),
                "end": _jd_to_datetime(period_end_jd).isoformat(timespec="seconds"),
                "start_boundary": started_before_range,
                "end_boundary": False,
                "entry_direction": ingress_direction,
            })
            period_start_jd = period_end_jd
            sign_index = int(ingress["to_sign"]) - 1
            ingress_direction = str(ingress["direction"])
            started_before_range = False
        periods.append({
            "planet": planet,
            "planet_ne": PLANET_NAMES_NE[planet],
            "sign": sign_index + 1,
            "sign_en": SIGN_NAMES_EN[sign_index],
            "sign_ne": SIGN_NAMES_NE[sign_index],
            "start": _jd_to_datetime(period_start_jd).isoformat(timespec="seconds"),
            "end": _jd_to_datetime(end_jd).isoformat(timespec="seconds"),
            "start_boundary": started_before_range,
            "end_boundary": True,
            "entry_direction": ingress_direction,
        })

    periods.sort(key=lambda item: (item["start"], REPORT_PLANETS.index(item["planet"])))
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timezone": "Asia/Kathmandu",
        "timezone_offset": NEPAL_OFFSET_HOURS,
        "ayanamsha_type": str(ayanamsha_type).upper(),
        "node_type": str(node_type).upper(),
        "ephemeris": "SWISS" if planetary_positions.swe is not None else "ANALYTICAL_FALLBACK",
        "excluded_planets": ["Moon"],
        "planets": list(REPORT_PLANETS),
        "current_ingresses": current_ingresses,
        "events": events,
        "periods": periods,
    }
