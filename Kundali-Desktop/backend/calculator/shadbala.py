"""Parashari Shadbala in Shashtiamsa and Rupa units.

The public result keeps the application's historical snake_case fields while
also exposing each classical sub-component.  One Rupa is 60 Shashtiamsas.
Optional birth-time/location arguments enable the temporal components; when
not supplied, deterministic chart-derived fallbacks are used.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
EXALTATION_DEGREES = {
    "Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0,
    "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0,
}
DEBILITATION_DEGREES = {name: (value + 180.0) % 360.0 for name, value in EXALTATION_DEGREES.items()}
DIG_BALA_HOUSE = {"Sun": 10, "Moon": 4, "Mars": 10, "Mercury": 1, "Jupiter": 1, "Venus": 4, "Saturn": 7}
NATURAL_SHASHTIAMSA = {"Sun": 60.0, "Moon": 51.43, "Mars": 17.14, "Mercury": 25.71, "Jupiter": 34.29, "Venus": 42.86, "Saturn": 8.57}
REQUIRED_RUPAS = {"Sun": 5.0, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}
MALE = {"Sun", "Mars", "Jupiter"}
DIURNAL = {"Sun", "Jupiter", "Venus"}

# ── Ayana Bala support (BPHS Shadbala) ───────────────────────────────────────
# Core rule: each degree of declination measured away from the equator counts
# five Shashtiamsas.  The value is the sum of the Parakrama (northern) and
# Vikala (southern) portions, so it is a derived classical quantity rather than
# a single 60-shashtiamsa unit.
#
# Known limitation, kept explicit on purpose: how this sum is normalised into a
# single Bala unit varies between schools.  This module reports the raw
# classical value and flags it approximate instead of imposing a clamp that
# would saturate most grahas at a flat maximum and hide real variation.
AYANA_PER_DEGREE = 5.0
OBLIQUITY_DEGREES = 23.45
AYANA_IS_APPROXIMATE = True
_SWISS_BODY_ATTR = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MARS", "Mercury": "MERCURY",
    "Jupiter": "JUPITER", "Venus": "VENUS", "Saturn": "SATURN",
}


def _declination(name: str, jd: Optional[float]) -> Optional[float]:
    """Equatorial declination of a graha in degrees, or None when unavailable.

    Routed through ``planetary_positions`` so the value honours the module-level
    Swiss handle.  When that handle is disabled the caller correctly receives
    None (an unavailable state) instead of an engine-dependent number.
    """
    if jd is None or name not in _SWISS_BODY_ATTR:
        return None
    try:
        from . import planetary_positions
    except ImportError:                     # pragma: no cover - direct-module use
        try:
            import planetary_positions
        except ImportError:
            return None
    return planetary_positions.get_swiss_declination(jd, _SWISS_BODY_ATTR[name])


def _ayana(name: str, jd: Optional[float]) -> Optional[float]:
    """Parakrama/Vikala Ayana Bala in Shashtiamsa, or None when unavailable.

    This replaces a former hardcoded ``30.0`` that added the same points to
    every graha regardless of birth date, and therefore inflated each graha's
    total Shadbala by a constant amount.
    """
    decl = _declination(name, jd)
    if decl is None:
        return None
    decl = max(-OBLIQUITY_DEGREES, min(OBLIQUITY_DEGREES, decl))
    return round(abs(decl) * AYANA_PER_DEGREE, 3)


def _long(p: Dict[str, Any]) -> float:
    return float(p.get("sidereal_longitude", p.get("longitude", 0.0)) or 0.0) % 360.0


def _house(p: Dict[str, Any]) -> int:
    return ((int(p.get("house", 1) or 1) - 1) % 12) + 1


def _sign(p: Dict[str, Any]) -> int:
    return int(p.get("sign_number", int(_long(p) // 30) + 1) or 1) % 12 or 12


def _cyclic_distance(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _component(points: Dict[str, float]) -> Dict[str, Any]:
    shashtiamsa = round(sum(points.values()), 3)
    return {"shashtiamsa": shashtiamsa, "rupa": round(shashtiamsa / 60.0, 3), **{k: round(v, 3) for k, v in points.items()}}


def _uchcha(name: str, longitude: float) -> float:
    # Classical Uchcha Bala is angular distance from the debilitation point / 3.
    return _cyclic_distance(longitude, DEBILITATION_DEGREES[name]) / 3.0


def _dignity_points(name: str, sign: int) -> float:
    own = {"Sun": {5}, "Moon": {4}, "Mars": {1, 8}, "Mercury": {3, 6}, "Jupiter": {9, 12}, "Venus": {2, 7}, "Saturn": {10, 11}}
    exalt = int(EXALTATION_DEGREES[name] // 30) + 1
    debil = int(DEBILITATION_DEGREES[name] // 30) + 1
    if sign == exalt:
        return 45.0
    if sign in own[name]:
        return 30.0
    if sign == debil:
        return 3.75
    return 7.5


def _saptavargiya(name: str, p: Dict[str, Any]) -> float:
    """Seven-varga dignity score; callers may provide precomputed varga points."""
    supplied = p.get("saptavargiya_bala")
    if supplied is not None:
        return max(0.0, min(210.0, float(supplied)))
    # D1 plus six divisional sign entries when available.  A neutral fallback
    # is preferable to inventing divisional positions from house numbers.
    varga_signs = p.get("varga_signs") or {}
    signs = [int(v) for v in varga_signs.values() if v is not None]
    if not signs:
        signs = [_sign(p)]
    return sum(_dignity_points(name, sign) / 3.0 for sign in signs[:7])


def _sthana(name: str, p: Dict[str, Any]) -> Dict[str, Any]:
    longitude = _long(p)
    sign = _sign(p)
    uchcha = _uchcha(name, longitude)
    saptavargiya = _saptavargiya(name, p)
    # Kendradi: kendra 60, panaphara 30, apoklima 15.
    house = _house(p)
    kendradi = 60.0 if house in (1, 4, 7, 10) else 30.0 if house in (2, 5, 8, 11) else 15.0
    # Ojhayugma: odd/even sign strength according to planetary sex.
    odd_sign = sign % 2 == 1
    ojhayugma = 15.0 if ((name in MALE) == odd_sign) else 0.0
    # Drekkana Bala: first/second/third decanate according to sex.
    decan = int((_long(p) % 30.0) // 10.0)
    drekkana = 15.0 if ((decan == 0 and name in MALE) or (decan == 1 and name not in MALE) or (decan == 2 and name in MALE)) else 0.0
    return _component({"uchcha": uchcha, "saptavargiya": saptavargiya, "ojhayugma": ojhayugma, "kendradi": kendradi, "drekkana": drekkana})


def _dig(name: str, house: int) -> Dict[str, Any]:
    # House centres are 30 degrees apart; seventh from the point of maximum is 0.
    distance = min((house - DIG_BALA_HOUSE[name]) % 12, (DIG_BALA_HOUSE[name] - house) % 12)
    shashtiamsa = max(0.0, 60.0 - distance * 10.0)
    return _component({"dig": shashtiamsa})


def _is_day(jd: Optional[float], sunrise_jd: Optional[float], sunset_jd: Optional[float]) -> Optional[bool]:
    """True during day, False during night, or None when it cannot be decided.

    Returning None (instead of assuming day) keeps Natonnata, Tribhaga and Hora
    Bala out of the total when sunrise/sunset are unavailable, rather than
    silently scoring every graha as though it were daytime.
    """
    if jd is not None and sunrise_jd is not None and sunset_jd is not None:
        return sunrise_jd <= jd < sunset_jd
    return None


def _kala(name: str, planets: List[Dict[str, Any]], jd: Optional[float], sunrise_jd: Optional[float], sunset_jd: Optional[float], weekday: Optional[int]) -> Dict[str, Any]:
    day = _is_day(jd, sunrise_jd, sunset_jd)
    sun_long = next((_long(p) for p in planets if p.get("name") == "Sun"), 0.0)
    moon_long = next((_long(p) for p in planets if p.get("name") == "Moon"), 0.0)

    # ── Natonnata Bala (Diurnal/Nocturnal) ────────────────────────────────
    # दिनमा: सूर्य, गुरु, शुक्र → 60; रातमा: चन्द्र, मङ्गल, शनि → 60
    # Omitted (not zeroed, not assumed) when the day/night state is unknown.
    natonnata: Optional[float] = None
    if day is True:
        natonnata = 60.0 if name in DIURNAL else 0.0
    elif day is False:
        natonnata = 60.0 if name not in DIURNAL else 0.0

    # ── Paksha Bala (proportional) — BPHS अनुसार वास्तविक proportional ────────────
    # Moonबाट Sun को कोणीय दूरी (0–360°)
    moon_sun_diff = (moon_long - sun_long) % 360.0
    # Shukla Paksha (0–180): benefics लाई बढ़्दो, Krishna (180–360): malefics लाई बढ़्दो
    natural_malefic = name in {"Sun", "Mars", "Saturn"}
    if not natural_malefic:  # Benefic: Jupiter, Venus, Mercury, Moon
        # Shukla = 0→180° → proportional 0–60
        paksha = min(60.0, moon_sun_diff / 3.0) if moon_sun_diff <= 180.0 else max(0.0, (360.0 - moon_sun_diff) / 3.0)
    else:  # Malefic: max strength in Krishna Paksha
        paksha = min(60.0, (360.0 - moon_sun_diff) / 3.0) if moon_sun_diff > 180.0 else max(0.0, moon_sun_diff / 3.0)

    # ── Tribhaga Bala — BPHS अनुसार correct lords ————————————————————————
    # दिनको ३ भाग: 1st→Mercury, 2nd→Sun, 3rd→Saturn
    # रातको ३ भाग: 1st→Moon, 2nd→Venus, 3rd→Mars
    tribhaga = 0.0
    if jd is not None and sunrise_jd is not None and sunset_jd is not None:
        if day:
            span = (sunset_jd - sunrise_jd) / 3.0
            if span > 0:
                third = int((jd - sunrise_jd) / span)
                day_lords = ["Mercury", "Sun", "Saturn"]
                if name == day_lords[min(third, 2)]:
                    tribhaga = 60.0
        else:
            night_start = sunset_jd
            night_end = sunrise_jd + 1.0  # अर्कोदय अगाडि
            span = (night_end - night_start) / 3.0
            if span > 0:
                third = int((jd - night_start) / span)
                night_lords = ["Moon", "Venus", "Mars"]
                if name == night_lords[min(third, 2)]:
                    tribhaga = 60.0

    # ── Vara Bala (वारेश्वर) ────────────────────────────────────────────────────
    vara = 45.0 if weekday is not None and name == ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"][weekday % 7] else 0.0

    # ── Hora Bala — ग्रहले आफ्नो Hora मा हुंदा 60 शष्टिांश ────────────────────────────
    # Hora गणना: Kala Chakra Hora lords (Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars — speed order)
    hora = 0.0
    if jd is not None and sunrise_jd is not None and sunset_jd is not None:
        HORA_SEQUENCE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
        if day:
            day_duration = sunset_jd - sunrise_jd
            if day_duration > 0:
                elapsed_horas = (jd - sunrise_jd) / (day_duration / 12.0)
                weekday_num = int(jd + 1.5) % 7  # 0=Sun
                start_lord = [0, 2, 4, 6, 1, 3, 5][weekday_num]  # Day lord index
                hora_lord_idx = (start_lord + int(elapsed_horas)) % 7
                if HORA_SEQUENCE[hora_lord_idx] == name:
                    hora = 60.0

    # ── Ayana Bala — BPHS Parakrama/Vikala, derived from the graha's declination.
    # It is omitted (not defaulted to a constant) when the declination is
    # unavailable, so the Kala Bala total never carries a fabricated point.
    ayana = _ayana(name, jd)
    points: Dict[str, float] = {"paksha": paksha, "tribhaga": tribhaga,
                                "varsha_masa": 0.0, "vara": vara, "hora": hora}
    # Only include a component when it was actually determined; an omitted key
    # means "unavailable", which is honest, whereas 0.0 would assert weakness.
    if natonnata is not None:
        points["natonnata"] = natonnata
    if ayana is not None:
        points["ayana"] = ayana
    component = _component(points)
    component["natonnata_available"] = natonnata is not None
    component["ayana_available"] = ayana is not None
    component["ayana_approximate"] = AYANA_IS_APPROXIMATE
    return component


def _cheshta(name: str, p: Dict[str, Any]) -> Dict[str, Any]:
    """Classical BPHS 8-state Cheshta Bala based on planetary speed.

    BPHS States (Avastha) and their Shashtiamsa values:
      1. Vakra (वक्र / Retrograde)          → 60
      2. Anuvakra (अनुवक्र / Slow retro)    → 30
      3. Vikal (विकल / Stationary)           → 15
      4. Manda (मन्द / Slow direct)          → 15
      5. Mandatara (मन्दतर / Very slow)      → 30
      6. Sama (सम / Mean speed)              → 7.5
      7. Cheshta (चेष्टा / Fast direct)      → 45
      8. Aticheshta (अतिचेष्टा / Very fast)  → 60

    Sun and Moon are never retrograde; their Cheshta Bala uses
    a special combust/phase-based rule from BPHS.
    """
    if name == "Sun":
        # Sun's Cheshta: 45 normally, 30 if combust (itself)
        value = 30.0 if p.get("is_combust") else 45.0
    elif name == "Moon":
        # Moon's Cheshta: based on distance from Sun (phase)
        # Full Moon zone → stronger; New Moon → weaker
        value = 45.0  # Default; refined if speed data present
        speed = p.get("speed_longitude") or p.get("daily_motion")
        if speed is not None:
            speed = float(speed)
            # Moon average speed ≈ 13.17°/day
            if speed >= 15.0:
                value = 60.0   # Aticheshta — very fast
            elif speed >= 13.17:
                value = 45.0   # Cheshta — above average
            elif speed >= 12.0:
                value = 30.0   # Mandatara
            else:
                value = 15.0   # Manda / slow
    else:
        # For the 5 true planets: use speed + retrograde flag
        is_retro = bool(p.get("is_retrograde"))
        speed = p.get("speed_longitude") or p.get("daily_motion")

        # Mean/average daily speeds (degrees/day)
        MEAN_SPEEDS = {
            "Mars":    0.524, "Mercury": 1.383, "Jupiter": 0.083,
            "Venus":   1.200, "Saturn":  0.034,
        }
        mean_speed = abs(MEAN_SPEEDS.get(name, 1.0))

        if speed is not None:
            speed_val = float(speed)
            abs_speed = abs(speed_val)

            if is_retro:
                # Retrograde states
                if abs_speed > mean_speed * 1.5:
                    value = 60.0   # Vakra — full retrograde speed
                else:
                    value = 30.0   # Anuvakra — slow retrograde
            elif abs_speed <= 0.001:
                value = 15.0       # Vikal — stationary
            elif abs_speed < mean_speed * 0.5:
                value = 15.0       # Manda — very slow
            elif abs_speed < mean_speed * 0.85:
                value = 30.0       # Mandatara — below average
            elif abs_speed <= mean_speed * 1.15:
                value = 7.5        # Sama — mean speed
            elif abs_speed <= mean_speed * 1.5:
                value = 45.0       # Cheshta — above average
            else:
                value = 60.0       # Aticheshta — very fast
        else:
            # Fallback when speed not available: retrograde=60, direct=30
            value = 60.0 if is_retro else 30.0

    return _component({"cheshta": value})




def _naisargika(name: str) -> Dict[str, Any]:
    return _component({"naisargika": NATURAL_SHASHTIAMSA[name]})


def _drik(p: Dict[str, Any], planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    value = 0.0
    house = _house(p)
    benefic = {"Jupiter", "Venus", "Mercury", "Moon"}
    for other in planets:
        oname = other.get("name")
        if oname not in GRAHAS or oname == p.get("name"):
            continue
        distance = (_house(other) - house) % 12 + 1
        aspects = {7}
        if oname == "Mars": aspects |= {4, 8}
        if oname == "Jupiter": aspects |= {5, 9}
        if oname == "Saturn": aspects |= {3, 10}
        if distance in aspects:
            value += 15.0 if oname in benefic else -15.0
    return _component({"drik": max(-60.0, min(60.0, value))})


def calculate_shadbala(planets: List[Dict[str, Any]], lagna_sign: int, jd: Optional[float] = None, sunrise_jd: Optional[float] = None, sunset_jd: Optional[float] = None, weekday: Optional[int] = None) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for p in planets:
        name = p.get("name")
        if name not in GRAHAS:
            continue
        components = {
            "sthana": _sthana(name, p), "dig": _dig(name, _house(p)),
            "kala": _kala(name, planets, jd, sunrise_jd, sunset_jd, weekday),
            "cheshta": _cheshta(name, p), "naisargika": _naisargika(name),
            "drik": _drik(p, planets),
        }
        total_shashtiamsa = sum(components[key]["shashtiamsa"] for key in components)
        total_rupas = total_shashtiamsa / 60.0
        results[name] = {
            "sthana_bala": round(components["sthana"]["rupa"], 3),
            "dig_bala": round(components["dig"]["rupa"], 3),
            "kala_bala": round(components["kala"]["rupa"], 3),
            "cheshta_bala": round(components["cheshta"]["rupa"], 3),
            "naisargika_bala": round(components["naisargika"]["rupa"], 3),
            "drik_bala": round(components["drik"]["rupa"], 3),
            "components": components,
            "total_shashtiamsa": round(total_shashtiamsa, 3),
            "total_rupas": round(total_rupas, 3),
            "required_rupas": REQUIRED_RUPAS[name],
            "is_strong": total_rupas >= REQUIRED_RUPAS[name],
        }
    ranking = sorted(results, key=lambda name: results[name]["total_rupas"], reverse=True)
    return {"planets": results, "ranking": ranking, "strongest": ranking[0] if ranking else None, "weakest": ranking[-1] if ranking else None}
