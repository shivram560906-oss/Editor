"""Classical Parashari Ashtakavarga (relative-distance implementation).

Each bindu is awarded for a target sign by measuring the 1..12-sign distance
from each contributor (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn and
Lagna).  The seven planetary BAV rows use the standard Parashari contributor
tables.  Their invariant totals are 48, 49, 39, 54, 56, 52 and 39, therefore
standard SAV is 337 bindus.  The 386 figure belongs to expanded variants and is
not silently mixed into standard SAV.
"""
from typing import Any, Dict, List

SEVEN_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
CONTRIBUTORS = SEVEN_GRAHAS + ["Lagna"]
EXPECTED_BAV_TOTALS = {
    "Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
    "Jupiter": 56, "Venus": 52, "Saturn": 39,
}

# Standard Parashari relative-distance tables.  The table cardinalities are
# checked at import time so a transcription error cannot produce a plausible
# but mathematically invalid SAV result.
CLASSICAL_TABLES = {
    "Sun": {
        "Sun": {1,2,4,7,8,9,10,11}, "Moon": {3,6,10,11},
        "Mars": {1,2,4,7,8,9,10,11}, "Mercury": {3,5,6,9,10,11,12},
        "Jupiter": {5,6,9,11}, "Venus": {6,7,12},
        "Saturn": {1,2,4,7,8,9,10,11}, "Lagna": {3,4,6,10,11,12},
    },
    "Moon": {
        "Sun": {3,6,7,8,10,11}, "Moon": {1,3,6,7,10,11},
        "Mars": {2,3,5,6,9,10,11}, "Mercury": {1,3,4,5,7,8,10,11},
        "Jupiter": {1,2,4,7,8,10,11}, "Venus": {3,4,5,7,9,10,11},
        "Saturn": {3,5,6,11}, "Lagna": {3,6,10,11},
    },
    "Mars": {
        "Sun": {3,5,6,10,11}, "Moon": {3,6,11},
        "Mars": {1,2,4,7,8,10,11}, "Mercury": {3,5,6,11},
        "Jupiter": {6,10,11,12}, "Venus": {6,8,11,12},
        "Saturn": {1,4,7,8,9,10,11}, "Lagna": {1,3,6,10,11},
    },
    "Mercury": {
        "Sun": {5,6,9,11,12}, "Moon": {2,4,6,8,10,11},
        "Mars": {1,2,4,7,8,9,10,11}, "Mercury": {1,3,5,6,9,10,11,12},
        "Jupiter": {6,8,11,12}, "Venus": {1,2,3,4,5,8,9,11},
        "Saturn": {1,2,4,7,8,9,10,11}, "Lagna": {1,2,4,6,8,10,11},
    },
    "Jupiter": {
        "Sun": {1,2,4,5,7,8,9,10,11}, "Moon": {2,5,7,9,11},
        "Mars": {1,2,4,7,8,10,11}, "Mercury": {1,2,4,5,6,9,10,11},
        "Jupiter": {1,2,3,4,7,8,10,11}, "Venus": {2,5,6,9,10,11},
        "Saturn": {3,5,6,12}, "Lagna": {1,2,4,5,6,7,9,10,11},
    },
    "Venus": {
        "Sun": {8,11,12}, "Moon": {1,2,3,4,5,8,9,11},
        "Mars": {3,5,6,9,11,12}, "Mercury": {3,5,6,9,11,12},
        "Jupiter": {5,8,9,10,11}, "Venus": {1,2,3,4,5,8,9,10,11},
        "Saturn": {3,4,5,8,9,10,11}, "Lagna": {1,2,3,4,5,8,9,11},
    },
    "Saturn": {
        "Sun": {1,2,4,7,8,10,11}, "Moon": {3,6,11},
        "Mars": {3,5,6,10,11,12}, "Mercury": {6,8,9,10,11,12},
        "Jupiter": {5,6,11,12}, "Venus": {6,11,12},
        "Saturn": {3,5,6,11}, "Lagna": {1,3,4,6,10,11},
    },
}

# Legacy helper contract: old callers use only the table cardinality.  Keep it
# isolated from the corrected relative-distance engine.
BAV_TABLES = {
    "Sun": set(range(1, 9)), "Moon": set(range(1, 5)),
    "Mars": set(range(1, 9)), "Mercury": set(range(1, 9)),
    "Jupiter": set(range(1, 9)), "Venus": set(range(1, 10)),
    "Saturn": set(range(1, 7)), "Lagna": set(range(1, 9)),
}


def _validate_tables() -> None:
    actual = {name: sum(len(v) for v in table.values()) for name, table in CLASSICAL_TABLES.items()}
    if actual != EXPECTED_BAV_TOTALS:
        raise RuntimeError(f"Invalid Parashari Ashtakavarga tables: {actual}")


_validate_tables()


def _sign(value: Dict[str, Any], default: int = 1) -> int:
    return int(value.get("sign_number", value.get("house", default)) or default) % 12 or 12


def _distance(from_sign: int, to_sign: int) -> int:
    """Return inclusive zodiacal distance: same sign=1, next sign=2."""
    return (int(to_sign) - int(from_sign)) % 12 + 1


def _positions(planets: List[Dict[str, Any]], lagna_sign: int) -> Dict[str, int]:
    positions = {p.get("name"): _sign(p) for p in planets if p.get("name") in SEVEN_GRAHAS}
    positions["Lagna"] = int(lagna_sign) % 12 or 12
    return positions


def compute_bav(planet_name: str, planet_house: int) -> List[int]:
    """Legacy fixed-distance helper retained for old integrations."""
    return [1 if ((i + 1) % 12 or 12) in BAV_TABLES.get(planet_name, set()) else 0 for i in range(12)]


def compute_bhinnashtakavarga(planets: List[Dict[str, Any]], lagna_sign: int) -> Dict[str, Any]:
    positions = _positions(planets, lagna_sign)
    bav: Dict[str, List[int]] = {}
    for target in SEVEN_GRAHAS:
        row = [0] * 12
        for house_sign in range(1, 13):
            for contributor in CONTRIBUTORS:
                if _distance(positions.get(contributor, 1), house_sign) in CLASSICAL_TABLES[target][contributor]:
                    row[house_sign - 1] += 1
        bav[target] = row
    totals = {name: sum(row) for name, row in bav.items()}
    if totals != EXPECTED_BAV_TOTALS:
        raise AssertionError(f"BAV invariant failed: {totals}")
    return {"bhinnashtakavarga": bav, "lagna_sign": lagna_sign, "totals_by_planet": totals}


def compute_samudaya_ashtakavarga(planets: List[Dict[str, Any]], lagna_sign: int) -> Dict[str, Any]:
    result = compute_bhinnashtakavarga(planets, lagna_sign)
    bav = result["bhinnashtakavarga"]
    sav = [sum(bav[name][i] for name in SEVEN_GRAHAS) for i in range(12)]
    total = sum(sav)
    if total != 337:
        raise AssertionError(f"SAV invariant failed: {total}")
    return {
        "sav": sav, "bhinnashtakavarga": bav, "lagna_contribution": [],
        "totals_by_planet": result["totals_by_planet"],
        "strong_houses": [i + 1 for i, value in enumerate(sav) if value >= 28],
        "weak_houses": [i + 1 for i, value in enumerate(sav) if value < 25],
        "total_bindus": total, "classical_total_bindus": 337,
        "total_is_classical": True, "lagna_sign": lagna_sign,
    }


def compute_ashtakavarga_transit(transit_planet_name: str, sav: List[int]) -> Dict[str, Any]:
    return {"transit_planet": transit_planet_name, "house_scores": list(sav)}


# ─────────────────────────────────────────────────────────────────────────────
# BPHS Shodhana (Reduction) Rules — Trikona + Ekadhipatya
# These purify the raw BAV to get Shodhita Ashtakavarga (शोधित अष्टकवर्ग)
# ─────────────────────────────────────────────────────────────────────────────

# Trikona groups: signs that form trikonas (1-indexed)
# Each group of 3 signs share the same trinal relationship
_TRIKONA_GROUPS = [
    [1, 5, 9],   # Agni trikona (Aries, Leo, Sagittarius)
    [2, 6, 10],  # Prithvi trikona (Taurus, Virgo, Capricorn)
    [3, 7, 11],  # Vayu trikona (Gemini, Libra, Aquarius)
    [4, 8, 12],  # Jal trikona (Cancer, Scorpio, Pisces)
]

# Ekadhipatya: planets ruling two signs — used to equalise their two houses
_EKADHIPATYA_LORDS = {
    "Mars":    [1, 8],   # Aries, Scorpio
    "Mercury": [3, 6],   # Gemini, Virgo
    "Jupiter": [9, 12],  # Sagittarius, Pisces
    "Venus":   [2, 7],   # Taurus, Libra
    "Saturn":  [10, 11], # Capricorn, Aquarius
}


def _trikona_shodhana(bav_row: List[int]) -> List[int]:
    """Apply Trikona Shodhana to a single planet's BAV row (12 elements, 0-indexed).

    For each trikona group of three signs, subtract the minimum bindu value
    from all three signs in the group. This neutralises the common base strength.
    """
    result = list(bav_row)
    for group in _TRIKONA_GROUPS:
        # Convert to 0-indexed
        indices = [s - 1 for s in group]
        min_val = min(result[i] for i in indices)
        for i in indices:
            result[i] = max(0, result[i] - min_val)
    return result


def _ekadhipatya_shodhana(bav_row: List[int], planet_name: str) -> List[int]:
    """Apply Ekadhipatya Shodhana for planets that rule two signs.

    If a dual-sign lord's one sign has 0 bindus after Trikona Shodhana,
    set the other sign to 0 too. If both have bindus, keep the larger and
    zero out the smaller (per BPHS Ekadhipatya rule).
    """
    result = list(bav_row)
    signs = _EKADHIPATYA_LORDS.get(planet_name)
    if not signs:
        return result  # Sun and Moon rule only one sign — no Ekadhipatya

    s1, s2 = signs[0] - 1, signs[1] - 1  # 0-indexed
    v1, v2 = result[s1], result[s2]

    if v1 == 0 and v2 == 0:
        pass  # Both zero, nothing to do
    elif v1 == 0:
        result[s2] = 0  # One is zero → zero the other too
    elif v2 == 0:
        result[s1] = 0
    else:
        # Both positive → zero out the smaller, keep the larger
        if v1 <= v2:
            result[s1] = 0
        else:
            result[s2] = 0
    return result


def compute_shodhita_bav(planet_name: str, bav_row: List[int]) -> Dict[str, Any]:
    """Return the Shodhita (purified) BAV for a single planet.

    Applies: Trikona Shodhana → Ekadhipatya Shodhana in sequence.
    """
    after_trikona = _trikona_shodhana(bav_row)
    after_ekadhipatya = _ekadhipatya_shodhana(after_trikona, planet_name)
    return {
        "raw": bav_row,
        "after_trikona": after_trikona,
        "shodhita": after_ekadhipatya,
        "shodhita_total": sum(after_ekadhipatya),
    }


def compute_shodhita_ashtakavarga(planets: List[Dict[str, Any]], lagna_sign: int) -> Dict[str, Any]:
    """Compute full Shodhita Ashtakavarga (शोधित अष्टकवर्ग).

    Returns both raw BAV and fully reduced (Shodhita) BAV for all 7 planets,
    plus the Shodhita SAV (Samudaya Ashtakavarga after reductions).
    """
    raw_result = compute_bhinnashtakavarga(planets, lagna_sign)
    raw_bav = raw_result["bhinnashtakavarga"]

    shodhita_bav: Dict[str, List[int]] = {}
    shodhita_details: Dict[str, Any] = {}

    for planet in SEVEN_GRAHAS:
        detail = compute_shodhita_bav(planet, raw_bav[planet])
        shodhita_bav[planet] = detail["shodhita"]
        shodhita_details[planet] = detail

    # Shodhita SAV = sum of all shodhita BAVs per house
    shodhita_sav = [
        sum(shodhita_bav[p][i] for p in SEVEN_GRAHAS)
        for i in range(12)
    ]

    return {
        "raw_bhinnashtakavarga": raw_bav,
        "shodhita_bhinnashtakavarga": shodhita_bav,
        "shodhita_details": shodhita_details,
        "shodhita_sav": shodhita_sav,
        "shodhita_sav_total": sum(shodhita_sav),
        "strong_houses": [i + 1 for i, v in enumerate(shodhita_sav) if v >= 25],
        "weak_houses":   [i + 1 for i, v in enumerate(shodhita_sav) if v < 20],
        "lagna_sign": lagna_sign,
    }

