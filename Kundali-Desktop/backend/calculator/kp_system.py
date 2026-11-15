"""Krishnamurti Paddhati stellar subdivisions and significators."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from . import houses

VIMSHOTTARI = [("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)]
SIGN_LORD = {1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"}
NAKSHATRA_SIZE = 360.0 / 27.0


def _subdivision(offset: float, span: float, start_index: int) -> Tuple[str, int, float]:
    cursor = 0.0
    for step in range(9):
        idx = (start_index + step) % 9
        lord, years = VIMSHOTTARI[idx]
        width = span * years / 120.0
        if offset < cursor + width or step == 8:
            return lord, idx, (offset - cursor) / width
        cursor += width
    return VIMSHOTTARI[start_index][0], start_index, 0.0


def stellar_lords(longitude: float) -> Dict[str, Any]:
    """Return KP sign, star, sub and sub-sub lords for a longitude."""
    longitude = float(longitude) % 360.0
    nak_index = int(longitude / NAKSHATRA_SIZE)
    star_index = nak_index % 9
    nak_offset = longitude - nak_index * NAKSHATRA_SIZE
    sub_lord, sub_index, fraction = _subdivision(nak_offset, NAKSHATRA_SIZE, star_index)
    sub_span = NAKSHATRA_SIZE * VIMSHOTTARI[sub_index][1] / 120.0
    sub_sub_lord, _, _ = _subdivision(fraction * sub_span, sub_span, sub_index)
    sign = int(longitude // 30.0) + 1
    return {"longitude": longitude, "sign": sign, "sign_lord": SIGN_LORD[sign], "nakshatra_number": nak_index + 1, "star_lord": VIMSHOTTARI[star_index][0], "sub_lord": sub_lord, "sub_sub_lord": sub_sub_lord}


def _house_of(longitude: float, cusp_longitudes: List[float]) -> int:
    return houses.get_bhava_chalit_placements({"point": longitude}, cusp_longitudes)["point"]


def calculate_significators(planets: List[Dict[str, Any]], cusp_longitudes: List[float]) -> Dict[str, Any]:
    occupied: Dict[int, List[str]] = {house: [] for house in range(1, 13)}
    details = {}
    for planet in planets:
        name = str(planet.get("name"))
        longitude = float(planet.get("sidereal_longitude", 0.0)) % 360.0
        house = _house_of(longitude, cusp_longitudes)
        occupied[house].append(name)
        details[name] = {**stellar_lords(longitude), "house": house}
    by_house = {}
    for number, cusp in enumerate(cusp_longitudes, 1):
        cusp_lords = stellar_lords(cusp)
        lord = cusp_lords["sign_lord"]
        by_house[number] = {"cusp": cusp_lords, "occupants": occupied[number], "house_lord": lord, "significators": sorted(set(occupied[number] + [lord] + [name for name, data in details.items() if data["star_lord"] in occupied[number]]))}
    return {"planets": details, "houses": by_house}


def calculate_kp_system(jd: float, latitude: float, longitude: float, ayanamsha_value: float, planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    tropical_cusps = houses.calculate_house_cusps(jd, latitude, longitude, "PLACIDUS")
    sidereal_cusps = [(value - ayanamsha_value) % 360.0 for value in tropical_cusps]
    return {"house_system": "PLACIDUS", "cusps": [{"house": i + 1, **stellar_lords(cusp)} for i, cusp in enumerate(sidereal_cusps)], "significators": calculate_significators(planets, sidereal_cusps)}
