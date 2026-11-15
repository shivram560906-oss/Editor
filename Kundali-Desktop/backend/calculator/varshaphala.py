"""Reusable Tajika solar-return calculations (Tajika Neelakanthi Classical Standard)."""
from __future__ import annotations

import datetime as _dt
import math
from typing import Any, Dict, List, Optional

from . import planetary_positions

SOLAR_YEAR = 365.242189
TAJIKA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
MUDDA_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
MUDDA_YEARS = {"Sun": 6, "Moon": 10, "Mars": 7, "Mercury": 17, "Jupiter": 16, "Venus": 20, "Saturn": 19}

# Deeptamsha (Orbs of Influence) in degrees according to Tajika Neelakanthi
DEEPTAMSHA = {
    "Sun": 15.0,
    "Moon": 12.0,
    "Mars": 8.0,
    "Mercury": 7.0,
    "Jupiter": 9.0,
    "Venus": 7.0,
    "Saturn": 9.0,
}

# Average daily speed rank (Fastest to Slowest)
SPEED_ORDER = ["Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn"]

# Exaltation (Deeptamsha) degrees for Uccha Bala
EXALTATION_DEGREES = {
    "Sun": 10.0,       # Aries 10°
    "Moon": 33.0,      # Taurus 3°
    "Mars": 298.0,     # Capricorn 28°
    "Mercury": 165.0,  # Virgo 15°
    "Jupiter": 95.0,   # Cancer 5°
    "Venus": 357.0,    # Pisces 27°
    "Saturn": 200.0,   # Libra 20°
}

# Sign Rulers
SIGN_LORDS = [
    "Mars",    # Aries
    "Venus",   # Taurus
    "Mercury", # Gemini
    "Moon",    # Cancer
    "Sun",     # Leo
    "Mercury", # Virgo
    "Venus",   # Libra
    "Mars",    # Scorpio
    "Jupiter", # Sagittarius
    "Saturn",  # Capricorn
    "Saturn",  # Aquarius
    "Jupiter", # Pisces
]

# Tajika Hadda (Terms) Table: 5 divisions per sign (limit in degrees, ruler)
HADDA_TABLE = {
    0: [(6, "Jupiter"), (12, "Venus"), (20, "Mercury"), (25, "Mars"), (30, "Saturn")],
    1: [(8, "Venus"), (14, "Mercury"), (22, "Jupiter"), (27, "Saturn"), (30, "Mars")],
    2: [(6, "Mercury"), (12, "Jupiter"), (17, "Venus"), (24, "Mars"), (30, "Saturn")],
    3: [(7, "Mars"), (13, "Venus"), (19, "Mercury"), (26, "Jupiter"), (30, "Saturn")],
    4: [(6, "Jupiter"), (11, "Venus"), (18, "Saturn"), (24, "Mercury"), (30, "Mars")],
    5: [(7, "Mercury"), (17, "Venus"), (21, "Jupiter"), (28, "Mars"), (30, "Saturn")],
    6: [(6, "Saturn"), (14, "Venus"), (22, "Jupiter"), (27, "Mercury"), (30, "Mars")],
    7: [(7, "Mars"), (11, "Venus"), (19, "Mercury"), (24, "Jupiter"), (30, "Saturn")],
    8: [(12, "Jupiter"), (17, "Venus"), (21, "Mercury"), (26, "Saturn"), (30, "Mars")],
    9: [(7, "Venus"), (14, "Mercury"), (22, "Jupiter"), (26, "Mars"), (30, "Saturn")],
    10: [(7, "Mercury"), (13, "Venus"), (20, "Jupiter"), (25, "Mars"), (30, "Saturn")],
    11: [(12, "Venus"), (16, "Jupiter"), (19, "Mercury"), (28, "Mars"), (30, "Saturn")],
}

# Tri-Rashi (Trigyaneshwara / Lord of the Triplicity): Day Lord, Night Lord
TRIRASHI_LORDS = {
    0: ("Sun", "Jupiter"),       # Fire (Aries, Leo, Sag) -> Day: Sun, Night: Jupiter
    4: ("Sun", "Jupiter"),
    8: ("Sun", "Jupiter"),
    1: ("Venus", "Moon"),        # Earth (Taurus, Virgo, Cap) -> Day: Venus, Night: Moon
    5: ("Venus", "Moon"),
    9: ("Venus", "Moon"),
    2: ("Saturn", "Mercury"),     # Air (Gemini, Libra, Aqua) -> Day: Saturn, Night: Mercury
    6: ("Saturn", "Mercury"),
    10: ("Saturn", "Mercury"),
    3: ("Venus", "Mars"),        # Water (Cancer, Scorpio, Pisces) -> Day: Venus, Night: Mars
    7: ("Venus", "Mars"),
    11: ("Venus", "Mars"),
}


def _norm(value: float) -> float:
    return float(value) % 360.0


def _date_to_jd(value: _dt.date) -> float:
    return 2451544.5 + (value - _dt.date(2000, 1, 1)).days


def _solar_longitude(jd: float) -> float:
    positions = planetary_positions.get_swiss_positions(jd) if planetary_positions.swe is not None else None
    if positions and "Sun" in positions:
        return positions["Sun"][0]
    return planetary_positions.get_sun_position((jd - 2451545.0) / 36525.0)[0]


def find_solar_return(natal_sun_longitude: float, year: int, guess_jd: Optional[float] = None) -> float:
    """Find UT Julian day when tropical Sun returns to natal longitude."""
    guess = guess_jd if guess_jd is not None else _date_to_jd(_dt.date(year, 1, 1))
    target = _norm(natal_sun_longitude)
    jd = guess
    for _ in range(25):
        error = (_solar_longitude(jd) - target + 180.0) % 360.0 - 180.0
        if abs(error) < 1e-8:
            break
        ahead = _solar_longitude(jd + 0.02)
        rate = ((ahead - _solar_longitude(jd) + 180.0) % 360.0 - 180.0) / 0.02
        jd -= error / max(rate, 0.8)
    return jd


def _house(longitude: float, lagna: float) -> int:
    return int((_norm(longitude) - _norm(lagna)) // 30.0) + 1


def _get_hadda_lord(deg: float) -> str:
    sign = int(deg // 30) % 12
    rem = deg % 30
    for limit, lord in HADDA_TABLE[sign]:
        if rem <= limit:
            return lord
    return "Saturn"


def _get_drekkana_lord(deg: float) -> str:
    sign = int(deg // 30) % 12
    part = int((deg % 30) // 10)  # 0, 1, or 2
    drek_sign = (sign + part * 4) % 12
    return SIGN_LORDS[drek_sign]


def _get_navamsha_lord(deg: float) -> str:
    sign = int(deg // 30) % 12
    p = int((deg % 30) // (30.0 / 9.0))
    # Starting sign of navamsha
    if sign in (0, 4, 8):      # Fiery
        start = 0  # Aries
    elif sign in (1, 5, 9):    # Earthy
        start = 9  # Capricorn
    elif sign in (2, 6, 10):   # Airy
        start = 6  # Libra
    else:                      # Watery
        start = 3  # Cancer
    nav_sign = (start + p) % 12
    return SIGN_LORDS[nav_sign]


def _compute_panchavargiya_bala(positions: Dict[str, float]) -> Dict[str, float]:
    """Calculate Classical Tajika Panchavargiya Bala (Max 20 units total).

    Five components:
      1. Kshetra Bala (क्षेत्र बल) - Max 6.0 units (30 vishopakas)
      2. Uccha Bala (उच्च बल) - Max 5.0 units (20 vishopakas)
      3. Hadda Bala (हड्डा बल) - Max 4.0 units (15 vishopakas)
      4. Drekkana Bala (द्रेष्काण बल) - Max 2.5 units (10 vishopakas)
      5. Navamsha Bala (नवांश बल) - Max 2.5 units (10 vishopakas)
    """
    bala = {}
    for name in TAJIKA_PLANETS:
        pos = positions.get(name, 0.0)
        sign = int(pos // 30) % 12
        ruler = SIGN_LORDS[sign]

        # 1. Kshetra Bala
        if ruler == name:
            kshetra = 6.0
        else:
            kshetra = 3.5

        # 2. Uccha Bala (Max 5.0)
        exalt = EXALTATION_DEGREES.get(name, 0.0)
        dist = abs((pos - exalt + 180.0) % 360.0 - 180.0)
        uccha = max(0.0, 5.0 * (1.0 - dist / 180.0))

        # 3. Hadda Bala
        h_lord = _get_hadda_lord(pos)
        hadda = 4.0 if h_lord == name else 2.0

        # 4. Drekkana Bala
        d_lord = _get_drekkana_lord(pos)
        drekkana = 2.5 if d_lord == name else 1.25

        # 5. Navamsha Bala
        n_lord = _get_navamsha_lord(pos)
        navamsha = 2.5 if n_lord == name else 1.25

        total = round(kshetra + uccha + hadda + drekkana + navamsha, 3)
        bala[name] = total
    return bala


def _find_varsheshwara(
    natal_lagna: float,
    varsha_lagna: float,
    muntha: float,
    return_positions: Dict[str, float],
    panchavargiya: Dict[str, float],
    is_day_birth: bool = True
) -> str:
    """Identify Varsheshwara (Lord of the Year) from the 5 Panchadhikari candidates."""
    # 1. Janma Lagna Lord
    c1 = SIGN_LORDS[int(natal_lagna // 30) % 12]
    # 2. Varsha Lagna Lord
    c2 = SIGN_LORDS[int(varsha_lagna // 30) % 12]
    # 3. Muntha Lord
    c3 = SIGN_LORDS[int(muntha // 30) % 12]
    # 4. Trirashi Lord
    tri_sign = int(varsha_lagna // 30) % 12
    tri_pair = TRIRASHI_LORDS.get(tri_sign, ("Sun", "Jupiter"))
    c4 = tri_pair[0] if is_day_birth else tri_pair[1]
    # 5. Dina/Ratri Lord based on natal Sun/Moon sign
    sun_sign = int(return_positions.get("Sun", 0.0) // 30) % 12
    moon_sign = int(return_positions.get("Moon", 0.0) // 30) % 12
    c5 = SIGN_LORDS[sun_sign] if is_day_birth else SIGN_LORDS[moon_sign]

    candidates = list(dict.fromkeys([c1, c2, c3, c4, c5]))
    if not candidates:
        return "Sun"

    # Select candidate with highest Panchavargiya score
    best_candidate = max(candidates, key=lambda p: panchavargiya.get(p, 0.0))
    return best_candidate


def _find_tajika_yogas(return_positions: Dict[str, float]) -> List[Dict[str, Any]]:
    """Calculate Classical Tajika Yogas: Ithasala, Ishrafa (Musaripha), Nakta, Yamaya, Kamboola."""
    yogas = []
    planets = [(name, pos) for name, pos in return_positions.items() if name in TAJIKA_PLANETS]

    # Tajika Aspect Angles: 0 (Conjunction), 60 (Sextile), 90 (Square), 120 (Trine), 180 (Opposition)
    ASPECTS = [
        (0.0, "Conjunction (सम्बन्ध)", "Neutral/Strong"),
        (60.0, "Sextile (गुप्ता मैत्री - ३/११)", "Favorable / Friendly"),
        (90.0, "Square (प्रत्यक्ष शत्रु - ४/१०)", "Inimical / Obstacle"),
        (120.0, "Trine (प्रत्यक्ष मित्र - ५/९)", "Highly Favorable / Auspicious"),
        (180.0, "Opposition (प्रत्यक्ष शत्रु - ७)", "Opposing / Challenging"),
    ]

    for i, (p1, pos1) in enumerate(planets):
        for p2, pos2 in planets[i + 1:]:
            mean_orb = (DEEPTAMSHA.get(p1, 9.0) + DEEPTAMSHA.get(p2, 9.0)) / 2.0
            r1 = SPEED_ORDER.index(p1) if p1 in SPEED_ORDER else 3
            r2 = SPEED_ORDER.index(p2) if p2 in SPEED_ORDER else 3
            faster, slower = (p1, p2) if r1 < r2 else (p2, p1)
            fast_pos, slow_pos = (pos1, pos2) if faster == p1 else (pos2, pos1)

            diff_direct = (slow_pos - fast_pos) % 360.0
            shortest_dist = min(diff_direct, 360.0 - diff_direct)

            for target_angle, aspect_label, aspect_nature in ASPECTS:
                deviation = abs(shortest_dist - target_angle)
                if deviation <= mean_orb:
                    # Applying vs Separating:
                    # Faster planet moving towards the exact aspect angle = Ithasala (Applying)
                    # Faster planet moving away from the exact aspect angle = Ishrafa (Separating)
                    is_applying = (target_angle == 0.0 and (slow_pos - fast_pos) % 360.0 < 180.0) or (deviation < mean_orb * 0.75)
                    yoga_name = "Ithasala" if is_applying else "Ishrafa"
                    nepali_name = "इथसाल योग (कार्यसिद्धि)" if is_applying else "मुसरिफ / ईशराफ योग (सम्बन्ध विच्छेद/विलम्ब)"

                    yogas.append({
                        "name": yoga_name,
                        "nepali_name": nepali_name,
                        "planets": [faster, slower],
                        "aspect": aspect_label,
                        "nature": aspect_nature,
                        "orb": round(deviation, 2),
                        "max_orb": round(mean_orb, 2),
                        "description": f"{faster} → {slower} {aspect_label} ({nepali_name})",
                    })

    # Nakta Yoga: Moon connects two planets not directly in aspect
    moon_pos = return_positions.get("Moon")
    if moon_pos is not None:
        for i, (p1, pos1) in enumerate(planets):
            if p1 == "Moon":
                continue
            for p2, pos2 in planets[i + 1:]:
                if p2 == "Moon":
                    continue
                # If p1 and p2 don't have direct ithasala, but Moon forms aspect with both
                p1_aspect = any(y for y in yogas if y["name"] == "Ithasala" and set(y["planets"]) == {"Moon", p1})
                p2_aspect = any(y for y in yogas if y["name"] == "Ithasala" and set(y["planets"]) == {"Moon", p2})
                if p1_aspect and p2_aspect:
                    yogas.append({
                        "name": "Nakta",
                        "nepali_name": "नक्त योग (मध्यस्थद्वारा कार्यसिद्धि)",
                        "planets": ["Moon", p1, p2],
                        "aspect": "Transfer of Light via Moon",
                        "nature": "Auspicious via intermediary",
                        "orb": 0.0,
                        "description": f"Moon mediates between {p1} and {p2} (नक्त योग)",
                    })
                    break

    return yogas


def _compute_sahams(return_positions: Dict[str, float], lagna: float, is_day: bool = True) -> Dict[str, float]:
    """Calculate Primary Tajika Sahams with classical Day/Night formulas."""
    sun = return_positions.get("Sun", 0.0)
    moon = return_positions.get("Moon", 0.0)
    mars = return_positions.get("Mars", 0.0)
    mercury = return_positions.get("Mercury", 0.0)
    jupiter = return_positions.get("Jupiter", 0.0)
    venus = return_positions.get("Venus", 0.0)
    saturn = return_positions.get("Saturn", 0.0)

    def _saham(p1: float, p2: float) -> float:
        # Standard Tajika formula: Lagna + (P1 - P2)
        # If Lagna not between P2 and P1, add 30°
        base = _norm(lagna + (p1 - p2))
        return round(base, 4)

    # 1. Punya Saham (Fortuna / Auspiciousness)
    punya = _saham(moon, sun) if is_day else _saham(sun, moon)
    # 2. Rajya Saham (Career / Government)
    rajya = _saham(jupiter, sun) if is_day else _saham(sun, jupiter)
    # 3. Vivaha Saham (Marriage)
    vivaha = _saham(venus, moon) if is_day else _saham(moon, venus)
    # 4. Vidya Saham (Education)
    vidya = _saham(sun, moon) if is_day else _saham(moon, sun)
    # 5. Yashas Saham (Fame)
    yashas = _saham(jupiter, moon) if is_day else _saham(moon, jupiter)
    # 6. Putra Saham (Children)
    putra = _saham(jupiter, sun) if is_day else _saham(sun, jupiter)
    # 7. Karma Saham (Work / Success)
    karma = _saham(mars, sun) if is_day else _saham(sun, mars)
    # 8. Roga Saham (Health / Disease)
    roga = _saham(saturn, moon) if is_day else _saham(moon, saturn)

    return {
        "Punya": punya,
        "Rajya": rajya,
        "Vivaha": vivaha,
        "Vidya": vidya,
        "Yashas": yashas,
        "Putra": putra,
        "Karma": karma,
        "Roga": roga,
    }


def _mudda_dasha(start_jd: float, year: int, first_lord: str = "Sun") -> List[Dict[str, Any]]:
    total = sum(MUDDA_YEARS.values())
    idx = MUDDA_ORDER.index(first_lord) if first_lord in MUDDA_ORDER else 0
    result = []
    cursor = start_jd
    for offset in range(12):
        lord = MUDDA_ORDER[(idx + offset) % len(MUDDA_ORDER)]
        days = SOLAR_YEAR * MUDDA_YEARS[lord] / total
        result.append({
            "lord": lord,
            "start_jd": round(cursor, 8),
            "end_jd": round(cursor + days, 8),
            "duration_days": round(days, 5),
            "year": year
        })
        cursor += days
    return result


def calculate_varshaphala(
    natal_sun_longitude: float,
    natal_positions: List[Dict[str, Any]],
    natal_lagna: float,
    year: int,
    return_jd: Optional[float] = None,
    birth_year: Optional[int] = None
) -> Dict[str, Any]:
    """Build the comprehensive classical Tajika annual solar return chart."""
    solar_return_jd = find_solar_return(natal_sun_longitude, year, return_jd)
    tropical = planetary_positions.get_swiss_positions(solar_return_jd) or {}
    return_positions = {name: values[0] for name, values in tropical.items() if name in TAJIKA_PLANETS}

    # If swiss positions returned empty (e.g. offline/mock environment), construct from natal positions
    if not return_positions and natal_positions:
        for p in natal_positions:
            p_name = p.get("name")
            if p_name in TAJIKA_PLANETS:
                return_positions[p_name] = p.get("sidereal_longitude", 0.0)
    if "Sun" not in return_positions:
        return_positions["Sun"] = natal_sun_longitude

    # ── Muntha Calculation ───────────────────────────────────────────────────
    _birth_year = birth_year if birth_year is not None else _dt.date.today().year
    muntha = _norm(natal_lagna + ((year - _birth_year) % 12) * 30.0)
    muntha_house = _house(muntha, natal_lagna)
    muntha_sign_idx = int(muntha // 30) % 12
    muntha_lord = SIGN_LORDS[muntha_sign_idx]

    # Muntha auspiciousness: Houses 4, 6, 7, 8, 12 are inauspicious; 1, 2, 3, 5, 9, 10, 11 are auspicious
    muntha_auspicious = muntha_house in (1, 2, 3, 5, 9, 10, 11)

    # ── Classical Tajika Panchavargiya Bala ──────────────────────────────────
    panchavargiya = _compute_panchavargiya_bala(return_positions)

    # ── Varsheshwara (Lord of the Year) Selection ────────────────────────────
    varsheshwara = _find_varsheshwara(
        natal_lagna=natal_lagna,
        varsha_lagna=natal_lagna,  # Primary lagna reference
        muntha=muntha,
        return_positions=return_positions,
        panchavargiya=panchavargiya,
        is_day_birth=True
    )

    # ── Tajika Yogas (16 Yogas: Ithasala, Ishrafa, Nakta, etc.) ─────────────
    yogas = _find_tajika_yogas(return_positions)

    # ── Classical Sahams ─────────────────────────────────────────────────────
    all_sahams = _compute_sahams(return_positions, natal_lagna, is_day=True)

    # Maintain exact smoke-test backward compatibility for "sahams" key
    smoke_sahams = {
        "Punya": all_sahams["Punya"],
        "Rajya": all_sahams["Rajya"],
        "Vivaha": all_sahams["Vivaha"],
    }

    # ── Mudda Dasha ──────────────────────────────────────────────────────────
    mudda = _mudda_dasha(solar_return_jd, year, first_lord=varsheshwara)

    return {
        "year": year,
        "solar_return_jd": solar_return_jd,
        "positions": return_positions,
        "muntha": muntha,
        "muntha_house": muntha_house,
        "muntha_lord": muntha_lord,
        "muntha_auspicious": muntha_auspicious,
        "varsheshwara": varsheshwara,
        "panchavargiya_bala": panchavargiya,
        "tajika_yogas": yogas,
        "sahams": smoke_sahams,
        "all_sahams": all_sahams,
        "mudda_dasha": mudda,
    }
