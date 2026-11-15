"""
Parashari Drishti (Graha Drishti) Engine — BPHS अनुसार
==========================================================

पाराशर ज्योतिष शास्त्रमा ग्रह दृष्टि (Planetary Aspects):

• सबै ग्रह:    7th house मा पूर्ण दृष्टि (100%)
• मङ्गल (Mars): 4th, 7th, 8th हाउसमा पूर्ण दृष्टि (100%)
• गुरु (Jupiter): 5th, 7th, 9th हाउसमा पूर्ण दृष्टि (100%)
• शनि (Saturn):  3rd, 7th, 10th हाउसमा पूर्ण दृष्टि (100%)

केही आचार्यहरू राहु/केतुलाई 5th, 7th, 9th दृष्टि दिन्छन् (Rahu-style).
यो engine ले ती सबैलाई handle गर्छ।

Usage:
    from calculator.drishti import get_aspects_on_house, does_planet_aspect_planet

Functions:
    get_aspects_on_house(aspector_name, aspector_house, target_house) -> bool
    get_aspect_strength(aspector_name, aspector_house, target_house) -> float
    get_all_aspects(planets) -> Dict[str, List[Dict]]
    does_planet_aspect_planet(aspector, target) -> bool
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Classical Parashari Aspect Tables
# ─────────────────────────────────────────────────────────────────────────────

# Standard 7th-house aspect (all planets, 100% strength)
UNIVERSAL_ASPECT = {7}

# Special additional aspects — house distances from the planet's position
# BPHS: Mars gets 4th and 8th in addition to 7th
# BPHS: Jupiter gets 5th and 9th in addition to 7th
# BPHS: Saturn gets 3rd and 10th in addition to 7th
SPECIAL_ASPECTS: Dict[str, set] = {
    "Mars":    {4, 8},
    "Jupiter": {5, 9},
    "Saturn":  {3, 10},
    # Rahu/Ketu — Jupiter-style aspects (school-dependent; Parashar school)
    "Rahu":    {5, 9},
    "Ketu":    {5, 9},
}

# Full aspect houses per planet (universal + special)
FULL_ASPECTS: Dict[str, set] = {
    planet: UNIVERSAL_ASPECT | SPECIAL_ASPECTS.get(planet, set())
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
}

# Aspect strength in percentage — BPHS gives partial fractions for some aspects
# in the Drishti Bala table. For house-based yoga detection we use 100% for all
# aspects listed in FULL_ASPECTS (partial-strength aspects like 3/4, 1/2, 1/4
# strength are for Drishti Bala only, not for yoga condition checks).
ASPECT_STRENGTH_PCT: Dict[str, Dict[int, float]] = {
    # Standard: all aspects 100%
    "Sun":     {7: 100.0},
    "Moon":    {7: 100.0},
    "Mercury": {7: 100.0},
    "Venus":   {7: 100.0},
    "Mars":    {4: 100.0, 7: 100.0, 8: 100.0},
    "Jupiter": {5: 100.0, 7: 100.0, 9: 100.0},
    "Saturn":  {3: 100.0, 7: 100.0, 10: 100.0},
    "Rahu":    {5: 100.0, 7: 100.0, 9: 100.0},
    "Ketu":    {5: 100.0, 7: 100.0, 9: 100.0},
}


def _house_distance(from_house: int, to_house: int) -> int:
    """Return 1-based zodiacal distance (1=same sign, 7=opposite).

    Following the standard Parashari convention: same house = 1, next = 2, … 7 = opposite.
    """
    return ((int(to_house) - int(from_house)) % 12) + 1


def does_planet_aspect_house(aspector_name: str, aspector_house: int, target_house: int) -> bool:
    """Return True if `aspector_name` in `aspector_house` aspects `target_house`.

    Implements full Parashari special-aspect rules. Both houses are 1-indexed (1..12).

    Args:
        aspector_name: Planet name (e.g. \"Mars\", \"Jupiter\").
        aspector_house: The house the aspecting planet occupies (1-12).
        target_house: The house being checked for aspect (1-12).

    Returns:
        True if the planet aspects the target house.
    """
    dist = _house_distance(aspector_house, target_house)
    aspects = FULL_ASPECTS.get(aspector_name, UNIVERSAL_ASPECT)
    return dist in aspects


def get_aspect_strength(aspector_name: str, aspector_house: int, target_house: int) -> float:
    """Return the aspect strength (0.0–100.0) of a planet on a target house.

    Returns 0.0 if the planet does not aspect the house.
    Returns 100.0 for any confirmed full aspect (Parashari standard).
    """
    dist = _house_distance(aspector_house, target_house)
    strength_table = ASPECT_STRENGTH_PCT.get(aspector_name, {7: 100.0})
    return strength_table.get(dist, 0.0)


def does_planet_aspect_planet(
    aspector: Dict[str, Any],
    target: Dict[str, Any],
) -> bool:
    """Return True if `aspector` planet aspects `target` planet.

    Both dicts must have a \"name\" key and a \"house\" key (1-12).

    Args:
        aspector: Planet dict with at least {\"name\": str, \"house\": int}.
        target: Planet dict with at least {\"name\": str, \"house\": int}.

    Returns:
        True if the aspector has a Parashari aspect on the target's house.
    """
    if not aspector or not target:
        return False
    a_house = aspector.get("house")
    t_house = target.get("house")
    if a_house is None or t_house is None:
        return False
    return does_planet_aspect_house(aspector["name"], int(a_house), int(t_house))


def get_all_aspects(planets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Compute all Parashari aspects for a list of planet dicts.

    Returns a dict keyed by aspector planet name, each value being a list of
    aspect records: [{\"target\": str, \"target_house\": int, \"strength\": float}].

    Args:
        planets: List of planet dicts, each with \"name\" and \"house\" keys.

    Returns:
        Dict mapping each planet name to its list of aspect targets.
    """
    result: Dict[str, List[Dict[str, Any]]] = {}
    for aspector in planets:
        a_name = aspector.get("name", "")
        a_house = aspector.get("house")
        if not a_name or a_house is None:
            continue
        aspects_list: List[Dict[str, Any]] = []
        for target in planets:
            t_name = target.get("name", "")
            t_house = target.get("house")
            if t_name == a_name or t_house is None:
                continue
            strength = get_aspect_strength(a_name, int(a_house), int(t_house))
            if strength > 0.0:
                aspects_list.append({
                    "target": t_name,
                    "target_house": int(t_house),
                    "strength": strength,
                })
        result[a_name] = aspects_list
    return result


def planets_are_related(
    planet_a: Optional[Dict[str, Any]],
    planet_b: Optional[Dict[str, Any]],
    lagna_sign: int,
) -> bool:
    """Return True if two planets are in conjunction, mutual exchange, or mutual aspect.

    This is the core Yoga-relation check used by detect_raja_yoga and similar
    functions to implement the full Parashari rule: planets are said to be in
    relationship (sambandha) if they:
      1. Occupy the same house (conjunction/yutti)
      2. Are in mutual sign exchange (parivartana)
      3. Aspect each other (drishti sambandha)

    Args:
        planet_a: Planet dict with \"name\", \"house\", \"sign_number\" keys.
        planet_b: Planet dict with \"name\", \"house\", \"sign_number\" keys.
        lagna_sign: Lagna sign number (1-12) for mutual-exchange calculation.

    Returns:
        True if any of the three relation types is satisfied.
    """
    if not planet_a or not planet_b:
        return False
    ha = planet_a.get("house")
    hb = planet_b.get("house")
    if ha is None or hb is None:
        return False

    # 1. Conjunction — same house
    if ha == hb:
        return True

    # 2. Mutual exchange (parivartana) — each in the other's sign
    from .yogas import SIGN_LORDS
    sa = planet_a.get("sign_number", 0)
    sb = planet_b.get("sign_number", 0)
    lagna_based_a_expected_sign = ((lagna_sign - 1 + ha - 1) % 12) + 1
    lagna_based_b_expected_sign = ((lagna_sign - 1 + hb - 1) % 12) + 1
    a_in_b_sign = (SIGN_LORDS.get(sb) == planet_a["name"])
    b_in_a_sign = (SIGN_LORDS.get(sa) == planet_b["name"])
    if a_in_b_sign and b_in_a_sign:
        return True

    # 3. Mutual aspect — a aspects b OR b aspects a
    if does_planet_aspect_planet(planet_a, planet_b):
        return True
    if does_planet_aspect_planet(planet_b, planet_a):
        return True

    return False
