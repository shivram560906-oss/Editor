"""
backend/calculator/transit_analysis.py

Enhanced Transit (Gochar) Analysis Engine

Implements:
1. Tarabala for all planets from natal Moon nakshatra
2. Double Transit Theory (Jupiter + Saturn simultaneous transit)
3. Transit aspects to natal planets (Parashari aspects)
4. Transit planet dignity (sign-based strength)
5. Key event prediction triggers (marriage, job, travel, health)
"""
from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Tuple

from . import planetary_positions
from .sarvatobhadra import (
    get_nakshatra_index, get_nakshatra_pada, get_tarabala,
    check_vedha, calculate_chandrabala, NAKSHATRAS, TARA_NAMES
)

from .constants import (
    SIGN_LORDS, EXALTATION_SIGNS, DEBILITATION_SIGNS, OWN_SIGNS,
)
# Alias for backward compatibility within this file
EXALTATION = EXALTATION_SIGNS
DEBILITATION = DEBILITATION_SIGNS



# ── Parashari aspect houses (additional to 7th for all) ────────────────────
SPECIAL_ASPECTS = {
    "Mars":   [4, 7, 8],
    "Jupiter":[5, 7, 9],
    "Saturn": [3, 7, 10],
    "Rahu":   [5, 7, 9],
    "Ketu":   [5, 7, 9],
}

# ── Planet names in Nepali ─────────────────────────────────────────────────
PLANET_NE = {
    "Sun":"सूर्य","Moon":"चन्द्र","Mars":"मङ्गल","Mercury":"बुध",
    "Jupiter":"गुरु","Venus":"शुक्र","Saturn":"शनि","Rahu":"राहु","Ketu":"केतु"
}

# ── Key event triggers ─────────────────────────────────────────────────────
# Each event defines which houses Jupiter & Saturn should transit simultaneously
DOUBLE_TRANSIT_EVENTS = {
    "marriage": {
        "houses": [7, 2, 11],
        "ne": "विवाह सम्भावना",
        "en": "Marriage Possibility",
        "description_ne": "गुरु र शनिको ७, २, वा ११ घरमा युगपत् गोचर — विवाह सम्भावना",
        "description_en": "Jupiter and Saturn transiting 7th, 2nd, or 11th simultaneously",
    },
    "career": {
        "houses": [10, 6, 11],
        "ne": "करियर उन्नति",
        "en": "Career Advancement",
        "description_ne": "गुरु र शनिको १०, ६, वा ११ घरमा युगपत् गोचर — नोकरी/करियर सम्भावना",
        "description_en": "Jupiter and Saturn transiting 10th, 6th, or 11th simultaneously",
    },
    "children": {
        "houses": [5, 9, 1],
        "ne": "सन्तान सम्भावना",
        "en": "Children Possibility",
        "description_ne": "गुरु र शनिको ५, ९, वा १ घरमा युगपत् गोचर — सन्तान सम्भावना",
        "description_en": "Jupiter and Saturn transiting 5th, 9th, or 1st simultaneously",
    },
    "foreign_travel": {
        "houses": [12, 9, 3],
        "ne": "विदेश यात्रा",
        "en": "Foreign Travel",
        "description_ne": "गुरु र शनिको १२, ९, वा ३ घरमा युगपत् गोचर — विदेश यात्रा सम्भावना",
        "description_en": "Jupiter and Saturn transiting 12th, 9th, or 3rd simultaneously",
    },
    "health_concern": {
        "houses": [6, 8, 12],
        "ne": "स्वास्थ्य सावधानी",
        "en": "Health Caution",
        "description_ne": "गुरु र शनिको ६, ८, वा १२ घरमा युगपत् गोचर — स्वास्थ्य ध्यान दिनुपर्छ",
        "description_en": "Jupiter and Saturn transiting 6th, 8th, or 12th — health caution",
    },
}


def _sign_from_lon(longitude: float) -> int:
    """Return sign number (1-12) from longitude."""
    return int(longitude / 30.0) % 12 + 1


def _house_from_lagna(planet_sign: int, lagna_sign: int) -> int:
    """Return house number (1-12) of a planet given lagna sign."""
    return ((planet_sign - lagna_sign) % 12) + 1


def _planet_dignity(planet: str, sign: int) -> str:
    """Return dignity string for a planet in a sign."""
    if EXALTATION.get(planet) == sign:
        return "exalted"
    if DEBILITATION.get(planet) == sign:
        return "debilitated"
    if sign in OWN_SIGNS.get(planet, []):
        return "own_sign"
    return "neutral"


def _does_transit_aspect_natal(transit_house: int, natal_house: int, planet: str) -> bool:
    """
    Check if transit planet in transit_house aspects natal planet in natal_house.
    Using Parashari whole-sign aspects.
    """
    diff = (natal_house - transit_house) % 12 + 1
    aspects = SPECIAL_ASPECTS.get(planet, [7])
    if 7 not in aspects:
        aspects = [7] + list(aspects)
    return diff in aspects


def calculate_transit_analysis(
    natal_data: Dict[str, Any],
    transit_jd: Optional[float] = None,
    language: str = "ne",
) -> Dict[str, Any]:
    """
    Main transit analysis: compute current/given-date transits vs natal chart.
    
    Args:
        natal_data: Full chart payload from backend_bridge.calculate_chart()
        transit_jd: Julian Day for transit (defaults to today)
        language: "ne" or "en"
    
    Returns:
        Complete transit analysis dict
    """
    is_ne = language == "ne"
    
    # ── Get today's JD if not provided ─────────────────────────────────────
    if transit_jd is None:
        today = datetime.date.today()
        transit_jd = 2451544.5 + (today - datetime.date(2000, 1, 1)).days
    
    # ── Get natal planet positions ─────────────────────────────────────────
    natal_planets = {p["name"]: p for p in (natal_data.get("planets") or []) if isinstance(p, dict)}
    natal_moon = natal_planets.get("Moon", {})
    natal_moon_lon = float(natal_moon.get("sidereal_longitude", natal_moon.get("longitude", 0)) or 0)
    natal_moon_sign = _sign_from_lon(natal_moon_lon)
    
    # Lagna (Ascendant) sign. The canonical chart payload exposes
    # lagna["longitude"]; older draft payloads used "sidereal_longitude".
    # Accept both so the lagna sign never silently defaults to Aries.
    lagna_block = natal_data.get("lagna") or natal_data.get("ascendant") or {}
    lagna_lon = float(
        lagna_block.get("sidereal_longitude", lagna_block.get("longitude", 0)) or 0
    )
    if lagna_lon == 0:
        # Try from metadata
        lagna_lon = float(natal_data.get("lagna_degree", 0) or 0)
    lagna_sign = _sign_from_lon(lagna_lon) or 1

    # ── Calculate transit positions via Swiss Ephemeris ────────────────────
    # The canonical payload nests the ayanamsha under metadata.
    metadata = natal_data.get("metadata") or {}
    ayanamsha_val = float(
        natal_data.get("ayanamsha_value", metadata.get("ayanamsha_value", 23.85)) or 23.85
    )
    
    transit_tropical = planetary_positions.get_swiss_positions(transit_jd, node_type="MEAN")
    if transit_tropical is None:
        T = (transit_jd - 2451545.0) / 36525.0
        transit_tropical = planetary_positions.get_all_tropical_positions(T, transit_jd)
    
    # Convert to sidereal
    transit_sidereal: Dict[str, float] = {}
    for pname, pos_tuple in transit_tropical.items():
        tropical_lon = pos_tuple[0] if isinstance(pos_tuple, (tuple, list)) else float(pos_tuple)
        sidereal_lon = (tropical_lon - ayanamsha_val) % 360.0
        transit_sidereal[pname] = sidereal_lon
    
    # ── Tarabala for all transit planets ───────────────────────────────────
    janma_nak_idx = get_nakshatra_index(natal_moon_lon)
    janma_nak = NAKSHATRAS[janma_nak_idx]
    
    tarabala_results = {}
    for pname, slon in transit_sidereal.items():
        transit_nak_idx = get_nakshatra_index(slon)
        transit_nak = NAKSHATRAS[transit_nak_idx]
        tara = get_tarabala(janma_nak_idx, transit_nak_idx)
        vedha = check_vedha(janma_nak_idx, transit_nak_idx)
        transit_sign = _sign_from_lon(slon)
        dignity = _planet_dignity(pname, transit_sign)
        transit_house = _house_from_lagna(transit_sign, lagna_sign)
        
        tarabala_results[pname] = {
            "transit_longitude": round(slon, 4),
            "transit_sign": transit_sign,
            "transit_house": transit_house,
            "transit_nakshatra_idx": transit_nak_idx,
            "transit_nakshatra_en": transit_nak["en"],
            "transit_nakshatra_ne": transit_nak["ne"],
            "dignity": dignity,
            "tarabala": tara,
            "vedha": vedha,
            "planet_ne": PLANET_NE.get(pname, pname),
            "overall_auspicious": tara["is_auspicious"] and not vedha["is_vedha"] and dignity != "debilitated",
        }
    
    # ── Chandrabala ────────────────────────────────────────────────────────
    current_moon_sign = _sign_from_lon(transit_sidereal.get("Moon", 0))
    chandrabala = calculate_chandrabala(natal_moon_sign, current_moon_sign)
    
    # ── Transit aspects to natal planets ──────────────────────────────────
    transit_aspects: List[Dict[str, Any]] = []
    for transit_planet, tdata in tarabala_results.items():
        t_house = tdata["transit_house"]
        for natal_planet_name, natal_p in natal_planets.items():
            natal_sign = _sign_from_lon(float(natal_p.get("sidereal_longitude", natal_p.get("longitude", 0)) or 0))
            natal_house = _house_from_lagna(natal_sign, lagna_sign)
            if _does_transit_aspect_natal(t_house, natal_house, transit_planet):
                transit_aspects.append({
                    "transit_planet": transit_planet,
                    "transit_planet_ne": PLANET_NE.get(transit_planet, transit_planet),
                    "transit_house": t_house,
                    "natal_planet": natal_planet_name,
                    "natal_planet_ne": PLANET_NE.get(natal_planet_name, natal_planet_name),
                    "natal_house": natal_house,
                    "is_auspicious": tdata["overall_auspicious"],
                })
    
    # ── Double Transit Theory ──────────────────────────────────────────────
    jupiter_house = tarabala_results.get("Jupiter", {}).get("transit_house", 0)
    saturn_house = tarabala_results.get("Saturn", {}).get("transit_house", 0)
    
    double_transit_triggers: List[Dict[str, Any]] = []
    for event_key, event_info in DOUBLE_TRANSIT_EVENTS.items():
        houses = event_info["houses"]
        jup_in_event = jupiter_house in houses
        sat_in_event = saturn_house in houses
        if jup_in_event and sat_in_event:
            double_transit_triggers.append({
                "event": event_key,
                "event_ne": event_info["ne"],
                "event_en": event_info["en"],
                "description_ne": event_info["description_ne"],
                "description_en": event_info["description_en"],
                "jupiter_house": jupiter_house,
                "saturn_house": saturn_house,
                "strength": "strong" if jupiter_house == saturn_house else "moderate",
            })
    
    # ── Summary ────────────────────────────────────────────────────────────
    auspicious_count = sum(1 for p in tarabala_results.values() if p["overall_auspicious"])
    total_planets = len(tarabala_results)
    
    moon_tara_num = tarabala_results.get("Moon", {}).get("tarabala", {}).get("tara_number", 0)
    moon_warning = moon_tara_num in (1, 3, 7)
    
    overall_score = 0
    if chandrabala["is_auspicious"]:
        overall_score += 3
    if not moon_warning:
        overall_score += 2
    overall_score += min(auspicious_count, 4)
    if double_transit_triggers:
        overall_score += 1
    
    return {
        "transit_jd": transit_jd,
        "janma_nakshatra": {
            "index": janma_nak_idx,
            "en": janma_nak["en"],
            "ne": janma_nak["ne"],
            "lord": janma_nak["lord"],
        },
        "natal_moon_sign": natal_moon_sign,
        "lagna_sign": lagna_sign,
        "planet_transits": tarabala_results,
        "chandrabala": chandrabala,
        "transit_aspects": transit_aspects,
        "double_transit_triggers": double_transit_triggers,
        "summary": {
            "overall_score": overall_score,
            "overall_quality_ne": "अति शुभ" if overall_score >= 8 else "शुभ" if overall_score >= 6 else "मध्यम" if overall_score >= 4 else "अशुभ",
            "overall_quality_en": "Very Auspicious" if overall_score >= 8 else "Auspicious" if overall_score >= 6 else "Moderate" if overall_score >= 4 else "Inauspicious",
            "auspicious_planets_count": auspicious_count,
            "total_planets_analyzed": total_planets,
            "moon_tara_warning": moon_warning,
            "chandrabala_ok": chandrabala["is_auspicious"],
            "double_transit_events": len(double_transit_triggers),
        },
    }
