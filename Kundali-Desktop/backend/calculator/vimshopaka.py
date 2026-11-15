# -*- coding: utf-8 -*-
"""
backend/calculator/vimshopaka.py

Shodashavarga Vimshopaka Bala — the authoritative calculation engine.

Vimshopaka Bala scores a graha's dignity across the sixteen divisional charts
and weights each varga, producing a total out of twenty.  This used to live
inside ``gui/widgets/vimshopaka_bala_page.py``; moving it here follows
PROJECT_RULES.md 3.1 ("astrology formulas never live in the GUI").  It also
removes that widget's fabricated "0.5 neutral" fallback, which printed a
confident-looking total for a varga that had never been calculated.

Per-varga rule (classical): the graha is scored by its dignity in the sign it
occupies in that divisional chart.

    exaltation / own sign ....... full score
    friendly sign .............. 3/4
    neutral sign ............... 1/2
    hostile sign ............... 1/4
    debilitation ............... 0

Each graha's total is the sum of ``score * varga_weight`` over the sixteen
divisions, and the weights sum to exactly 20.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .constants import (
    DEBILITATION_SIGNS,
    EXALTATION_SIGNS,
    OWN_SIGNS,
    PLANET_NAMES_EN,
    PLANET_NAMES_NE,
    SIGN_LORDS,
)
from .marriage_matching import PLANET_NATURAL_RELATION
from .vargas import get_varga_sign

# ── Shodashavarga weights (Parashari); these sum to 20.0 ─────────────────────
VIMSHOPAKA_VARGAS: List[tuple] = [
    ("D1", 3.5), ("D2", 1.0), ("D3", 1.0), ("D4", 0.5),
    ("D7", 0.5), ("D9", 3.0), ("D10", 0.5), ("D12", 0.5),
    ("D16", 2.0), ("D20", 0.5), ("D24", 0.5), ("D27", 0.5),
    ("D30", 1.0), ("D40", 0.5), ("D45", 0.5), ("D60", 4.0),
]

VIMSHOPAKA_MAX_TOTAL = round(sum(weight for _, weight in VIMSHOPAKA_VARGAS), 3)

# Grahas in report order (nodes included, as the desktop page always showed).
VIMSHOPAKA_GRAHAS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]

# Score assigned to each dignity level.
SCORE_BY_RELATION = {
    "exalted": 1.0,
    "own": 1.0,
    "friend": 0.75,
    "neutral": 0.5,
    "enemy": 0.25,
    "debilitated": 0.0,
}

# Thresholds for the rating shown in the UI (highest band first).
RATING_BANDS = (
    (15.0, "अत्यन्त बलिष्ठ", "Extremely Strong"),
    (10.0, "बलिष्ठ", "Strong"),
    (6.0, "मध्यम", "Moderate"),
    (3.0, "कमजोर", "Weak"),
    (0.0, "अत्यन्त कमजोर", "Very Weak"),
)


def _relation(planet: str, sign: int) -> str:
    """Dignity of ``planet`` in the 1-indexed ``sign``.

    Nodes have no exaltation or own signs, so they are scored purely by
    natural friendship with the sign lord.
    """
    if EXALTATION_SIGNS.get(planet) == sign:
        return "exalted"
    if sign in OWN_SIGNS.get(planet, []):
        return "own"
    if DEBILITATION_SIGNS.get(planet) == sign:
        return "debilitated"
    lord = SIGN_LORDS.get(sign)
    natural = PLANET_NATURAL_RELATION.get(planet, {}).get(lord)
    if natural == "F":
        return "friend"
    if natural == "E":
        return "enemy"
    return "neutral"


def _rating(total: float) -> Dict[str, str]:
    """Label for a total out of 20."""
    for threshold, label_ne, label_en in RATING_BANDS:
        if total >= threshold:
            return {"ne": label_ne, "en": label_en}
    return {"ne": RATING_BANDS[-1][1], "en": RATING_BANDS[-1][2]}


def _longitude(planet: Dict[str, Any]) -> Optional[float]:
    """Sidereal longitude from a payload planet, or None when absent."""
    for key in ("sidereal_longitude", "longitude"):
        raw = planet.get(key)
        if raw is None or isinstance(raw, (dict, list, tuple, set)):
            continue
        try:
            return float(raw) % 360.0
        except (TypeError, ValueError):
            continue
    return None


def _varga_list() -> List[Dict[str, Any]]:
    return [{"id": vid, "weight": weight} for vid, weight in VIMSHOPAKA_VARGAS]


def _empty_result(reason: str) -> Dict[str, Any]:
    """An explicit unavailable state - never a fabricated total."""
    return {
        "status": "unavailable",
        "reason": reason,
        "vargas": _varga_list(),
        "max_total": VIMSHOPAKA_MAX_TOTAL,
        "planets": {},
    }


def calculate_vimshopaka_bala(planets: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Vimshopaka Bala for every graha, or an explicit unavailable state.

    A graha with no resolvable longitude, or a varga whose sign cannot be
    resolved, is reported unavailable for that cell.  No neutral value is
    substituted for missing data.
    """
    usable = [p for p in (planets or []) if isinstance(p, dict)]
    if not usable:
        return _empty_result("No planetary positions were supplied.")

    by_name: Dict[str, Dict[str, Any]] = {}
    for planet in usable:
        name = planet.get("name")
        if name in VIMSHOPAKA_GRAHAS and name not in by_name:
            by_name[name] = planet

    result_planets: Dict[str, Any] = {}
    any_available = False

    for name in VIMSHOPAKA_GRAHAS:
        entry: Dict[str, Any] = {
            "name_en": PLANET_NAMES_EN.get(name, name),
            "name_ne": PLANET_NAMES_NE.get(name, name),
            "available": False,
            "vargas": {},
            "total": None,
            "rating": None,
        }
        source = by_name.get(name)
        longitude = _longitude(source) if source else None
        if longitude is not None:
            per_varga: Dict[str, Any] = {}
            total = 0.0
            resolved_all = True
            for varga_id, weight in VIMSHOPAKA_VARGAS:
                try:
                    sign = int(get_varga_sign(varga_id, longitude))
                except (TypeError, ValueError):
                    sign = 0
                if not 1 <= sign <= 12:
                    resolved_all = False
                    per_varga[varga_id] = {"available": False, "weight": weight}
                    continue
                relation = _relation(name, sign)
                score = SCORE_BY_RELATION[relation]
                per_varga[varga_id] = {
                    "available": True,
                    "sign": sign,
                    "relation": relation,
                    "score": score,
                    "weight": weight,
                    "weighted": round(score * weight, 3),
                }
                total += score * weight
            entry["vargas"] = per_varga
            if resolved_all:
                total = round(total, 3)
                entry["available"] = True
                entry["total"] = total
                entry["rating"] = _rating(total)
                any_available = True
        result_planets[name] = entry

    if not any_available:
        return _empty_result("No graha had a resolvable sidereal longitude.")

    return {
        "status": "ready",
        "reason": None,
        "vargas": _varga_list(),
        "max_total": VIMSHOPAKA_MAX_TOTAL,
        "planets": result_planets,
    }
