"""Jaimini astrology: chara karakas, rashi drishti, padas and Chara Dasha."""
from __future__ import annotations

from typing import Any, Dict, List

from .vargas import get_varga_sign

GRAHAS_7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
KARAKAS_7 = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka"]
KARAKAS_8 = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka", "Pitृkaraka"]
MOVABLE = {1, 4, 7, 10}
FIXED = {2, 5, 8, 11}
DUAL = {3, 6, 9, 12}
SIGN_LORD = {1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"}


def _longitude(planet: Dict[str, Any]) -> float:
    return float(planet.get("sidereal_longitude", planet.get("longitude", 0.0)) or 0.0) % 360.0


def _sign(longitude: float) -> int:
    return int(longitude % 360.0 // 30.0) + 1


def calculate_chara_karakas(planets: List[Dict[str, Any]], use_eight: bool = False) -> Dict[str, str]:
    """Assign degrees-in-sign from highest to lowest; Rahu is reverse-counted."""
    allowed = set(GRAHAS_7 + (["Rahu"] if use_eight else []))
    scores = []
    for planet in planets:
        name = str(planet.get("name", ""))
        if name not in allowed:
            continue
        degrees = _longitude(planet) % 30.0
        score = 30.0 - degrees if name == "Rahu" else degrees
        scores.append((score, name))
    scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
    labels = KARAKAS_8 if use_eight else KARAKAS_7
    return {label: name for label, (_, name) in zip(labels, scores)}


def sign_aspects(sign: int) -> List[int]:
    """Return classical Jaimini rashi drishti, excluding adjacent signs."""
    sign = ((int(sign) - 1) % 12) + 1
    if sign in MOVABLE:
        return sorted(FIXED - {sign % 12 + 1})
    if sign in FIXED:
        return sorted(MOVABLE - {((sign - 2) % 12) + 1})
    return sorted(DUAL - {sign})


def calculate_sign_aspects(planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_planet = {}
    by_sign = {sign: sign_aspects(sign) for sign in range(1, 13)}
    for planet in planets:
        if planet.get("name") in GRAHAS_7 + ["Rahu", "Ketu"]:
            sign = _sign(_longitude(planet))
            by_planet[str(planet["name"])] = {"from_sign": sign, "aspected_signs": by_sign[sign]}
    return {"by_sign": by_sign, "by_planet": by_planet}


def _inclusive_distance(start: int, end: int) -> int:
    return (end - start) % 12 + 1


def arudha_pada(house_sign: int, lord_sign: int) -> int:
    """Project lord-to-house distance again, applying the 1/7 exception.
    
    पाराशर अनुसार:
    - Pada यदि house_sign मा पर्यो → 10th स्थानबाट गन्ने
    - Pada यदि 7th मा पर्यो → 10th स्थानबाट गन्ने
    """
    distance = _inclusive_distance(house_sign, lord_sign)
    pada = (lord_sign - 1 + distance - 1) % 12 + 1
    # 7th from house_sign (Saptama = house_sign + 6, mod 12)
    seventh_from_house = (house_sign - 1 + 6) % 12 + 1
    if pada == house_sign or pada == seventh_from_house:
        # Move 10 places forward from pada (10th from pada)
        pada = (pada - 1 + 9) % 12 + 1
    return pada


def calculate_arudhas(planets: List[Dict[str, Any]], lagna_sign: int) -> Dict[str, int]:
    positions = {str(p.get("name")): _sign(_longitude(p)) for p in planets}
    result = {}
    for house in range(1, 13):
        house_sign = (lagna_sign + house - 2) % 12 + 1
        lord = SIGN_LORD[house_sign]
        result[f"A{house}"] = arudha_pada(house_sign, positions.get(lord, house_sign))
    result["Arudha_Lagna"] = result["A1"]
    result["Upapada"] = result["A12"]
    return result


def calculate_karakamsha(planets: List[Dict[str, Any]], use_eight: bool = False) -> Dict[str, Any]:
    karakas = calculate_chara_karakas(planets, use_eight)
    atmakaraka = karakas.get("Atmakaraka")
    planet = next((p for p in planets if p.get("name") == atmakaraka), None)
    navamsha = get_varga_sign("D9", _longitude(planet)) if planet else None
    return {"atmakaraka": atmakaraka, "karakamsha_sign": navamsha}


def calculate_chara_dasha(lagna_sign: int, start_year: int, cycles: int = 12) -> List[Dict[str, Any]]:
    """Generate sign periods using odd-sign forward/even-sign reverse sequence.
    
    पाराशरीय Jaimini Chara Dasha:
    विषम Lagna → आगाडि, सम Lagna → पछाडि।
    प्रत्येक राशिको Years = राशिबाट राशि स्वामी सम्मको राशिसम्मको दूरी - 1
    (राशि स्वामीको दोस्रो घर exaltation वा own sign माम्ले पनि अलग नियम)
    """
    forward = lagna_sign % 2 == 1
    sequence = [((lagna_sign - 1 + (i if forward else -i)) % 12) + 1 for i in range(12)]
    # Sign lord to their primary own/exalted sign (lower-numbered for dual ownership)
    SIGN_LORD_PRIMARY = {
        "Mars": 1,     # Aries (primary)
        "Venus": 2,    # Taurus (primary)
        "Mercury": 3,  # Gemini (primary)
        "Moon": 4,     # Cancer
        "Sun": 5,      # Leo
        "Jupiter": 9,  # Sagittarius (primary for Jupiter)
        "Saturn": 10,  # Capricorn (primary for Saturn)
    }
    cursor = float(start_year)
    result = []
    for sign in sequence[:max(1, min(cycles, 12))]:
        lord = SIGN_LORD[sign]
        lord_sign = SIGN_LORD_PRIMARY.get(lord, sign)
        years = max(1, _inclusive_distance(sign, lord_sign) - 1)
        result.append({"sign": sign, "lord": lord, "start_year": cursor,
                       "end_year": cursor + years, "duration_years": years})
        cursor += years
    return result


def calculate_jaimini(planets: List[Dict[str, Any]], lagna_sign: int, birth_year: int, use_eight_karakas: bool = False) -> Dict[str, Any]:
    return {"karaka_scheme": 8 if use_eight_karakas else 7, "chara_karakas": calculate_chara_karakas(planets, use_eight_karakas), "sign_aspects": calculate_sign_aspects(planets), "arudhas": calculate_arudhas(planets, lagna_sign), "karakamsha": calculate_karakamsha(planets, use_eight_karakas), "chara_dasha": calculate_chara_dasha(lagna_sign, birth_year)}
