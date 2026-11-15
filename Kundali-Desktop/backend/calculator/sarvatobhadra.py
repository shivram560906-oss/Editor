"""
backend/calculator/sarvatobhadra.py

Sarvatobhadra Chakra (सर्वतोभद्र चक्र) Calculator

A 9x9 grid used in Vedic astrology for determining auspiciousness of
directions, timing events, and transit analysis. Integrates:
- 27 Nakshatras, 7 Weekdays, 30 Tithis
- Tarabala, Chandrabala, Vedha detection

Used for: travel, business, muhurta, natal transit vedha.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

NAKSHATRAS = [
    {"idx": 0,  "en": "Ashwini",      "ne": "अश्विनी",    "lord": "Ketu"},
    {"idx": 1,  "en": "Bharani",      "ne": "भरणी",       "lord": "Venus"},
    {"idx": 2,  "en": "Krittika",     "ne": "कृत्तिका",   "lord": "Sun"},
    {"idx": 3,  "en": "Rohini",       "ne": "रोहिणी",     "lord": "Moon"},
    {"idx": 4,  "en": "Mrigashira",   "ne": "मृगशिरा",    "lord": "Mars"},
    {"idx": 5,  "en": "Ardra",        "ne": "आर्द्रा",    "lord": "Rahu"},
    {"idx": 6,  "en": "Punarvasu",    "ne": "पुनर्वसु",   "lord": "Jupiter"},
    {"idx": 7,  "en": "Pushya",       "ne": "पुष्य",      "lord": "Saturn"},
    {"idx": 8,  "en": "Ashlesha",     "ne": "आश्लेषा",    "lord": "Mercury"},
    {"idx": 9,  "en": "Magha",        "ne": "मघा",        "lord": "Ketu"},
    {"idx": 10, "en": "Purva Phalguni","ne": "पूर्वाफाल्गुनी","lord": "Venus"},
    {"idx": 11, "en": "Uttara Phalguni","ne": "उत्तराफाल्गुनी","lord": "Sun"},
    {"idx": 12, "en": "Hasta",        "ne": "हस्त",       "lord": "Moon"},
    {"idx": 13, "en": "Chitra",       "ne": "चित्रा",     "lord": "Mars"},
    {"idx": 14, "en": "Swati",        "ne": "स्वाती",     "lord": "Rahu"},
    {"idx": 15, "en": "Vishakha",     "ne": "विशाखा",     "lord": "Jupiter"},
    {"idx": 16, "en": "Anuradha",     "ne": "अनुराधा",    "lord": "Saturn"},
    {"idx": 17, "en": "Jyeshtha",     "ne": "ज्येष्ठा",   "lord": "Mercury"},
    {"idx": 18, "en": "Mula",         "ne": "मूल",        "lord": "Ketu"},
    {"idx": 19, "en": "Purva Ashadha","ne": "पूर्वाषाढा", "lord": "Venus"},
    {"idx": 20, "en": "Uttara Ashadha","ne": "उत्तराषाढा","lord": "Sun"},
    {"idx": 21, "en": "Shravana",     "ne": "श्रवण",      "lord": "Moon"},
    {"idx": 22, "en": "Dhanishtha",   "ne": "धनिष्ठा",    "lord": "Mars"},
    {"idx": 23, "en": "Shatabhisha",  "ne": "शतभिषा",     "lord": "Rahu"},
    {"idx": 24, "en": "Purva Bhadrapada","ne": "पूर्वाभाद्रपद","lord": "Jupiter"},
    {"idx": 25, "en": "Uttara Bhadrapada","ne": "उत्तराभाद्रपद","lord": "Saturn"},
    {"idx": 26, "en": "Revati",       "ne": "रेवती",      "lord": "Mercury"},
]

VEDHA_PAIRS = {
    0:14, 1:13, 2:12, 3:11, 4:10, 5:9, 6:8,
    14:0, 13:1, 12:2, 11:3, 10:4, 9:5, 8:6,
    15:26, 16:25, 17:24, 18:23, 19:22, 20:21,
    26:15, 25:16, 24:17, 23:18, 22:19, 21:20,
}

TARA_NAMES = {
    1: {"en": "Janma",       "ne": "जन्म",        "type": "neutral"},
    2: {"en": "Sampat",      "ne": "सम्पत",        "type": "good"},
    3: {"en": "Vipat",       "ne": "विपत",         "type": "bad"},
    4: {"en": "Kshema",      "ne": "क्षेम",        "type": "good"},
    5: {"en": "Pratyak",     "ne": "प्रत्यक",      "type": "bad"},
    6: {"en": "Sadhaka",     "ne": "साधक",         "type": "good"},
    7: {"en": "Vadha",       "ne": "वध",           "type": "bad"},
    8: {"en": "Mitra",       "ne": "मित्र",        "type": "good"},
    9: {"en": "Paramamitra", "ne": "परममित्र",     "type": "good"},
}

VARA_LORDS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
VARA_NE = ["आइतवार","सोमवार","मङ्गलवार","बुधवार","बिहीवार","शुक्रवार","शनिवार"]
VARA_EN = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]


def get_nakshatra_index(sidereal_longitude: float) -> int:
    return int(sidereal_longitude / (360.0 / 27)) % 27


def get_nakshatra_pada(sidereal_longitude: float) -> int:
    nak_size = 360.0 / 27
    return int((sidereal_longitude % nak_size) / (nak_size / 4)) + 1


def get_tarabala(janma_nak_idx: int, transit_nak_idx: int) -> Dict[str, Any]:
    diff = (transit_nak_idx - janma_nak_idx) % 27
    tara_num = (diff % 9) + 1
    tara_info = TARA_NAMES.get(tara_num, {"en": "Unknown", "ne": "अज्ञात", "type": "neutral"})
    return {
        "tara_number": tara_num,
        "tara_en": tara_info["en"],
        "tara_ne": tara_info["ne"],
        "type": tara_info["type"],
        "distance": diff,
        "is_auspicious": tara_info["type"] == "good",
    }


def check_vedha(natal_nak_idx: int, transit_nak_idx: int) -> Dict[str, Any]:
    vedha_nak = VEDHA_PAIRS.get(natal_nak_idx)
    is_vedha = (transit_nak_idx == vedha_nak) or (transit_nak_idx == natal_nak_idx)
    return {
        "is_vedha": is_vedha,
        "vedha_nakshatra_idx": vedha_nak,
        "vedha_nakshatra": NAKSHATRAS[vedha_nak]["en"] if vedha_nak is not None else None,
        "description_ne": "वेध छ — अशुभ" if is_vedha else "वेध छैन — शुभ",
        "description_en": "Vedha — inauspicious" if is_vedha else "No vedha — auspicious",
    }


def calculate_chandrabala(natal_moon_sign: int, current_moon_sign: int) -> Dict[str, Any]:
    AUSPICIOUS = {1, 3, 6, 7, 10, 11}
    distance = ((current_moon_sign - natal_moon_sign) % 12) + 1
    is_auspicious = distance in AUSPICIOUS
    score_map = {1:5,3:5,6:5,7:4,10:4,11:4,2:2,4:3,5:2,8:2,9:3,12:3}
    return {
        "natal_moon_sign": natal_moon_sign,
        "current_moon_sign": current_moon_sign,
        "distance_from_natal": distance,
        "chandrabala_score": score_map.get(distance, 3),
        "is_auspicious": is_auspicious,
        "description_ne": "चन्द्रबल शुभ" if is_auspicious else "चन्द्रबल अशुभ",
        "description_en": "Chandrabala auspicious" if is_auspicious else "Chandrabala inauspicious",
    }


def calculate_transit_tarabala_for_all_planets(
    natal_moon_longitude: float,
    transit_positions: Dict[str, float],
) -> Dict[str, Any]:
    janma_nak_idx = get_nakshatra_index(natal_moon_longitude)
    janma_pada = get_nakshatra_pada(natal_moon_longitude)
    janma_nak = NAKSHATRAS[janma_nak_idx]
    results = {
        "janma_nakshatra": {
            "index": janma_nak_idx,
            "en": janma_nak["en"],
            "ne": janma_nak["ne"],
            "lord": janma_nak["lord"],
            "pada": janma_pada,
            "longitude": round(natal_moon_longitude, 4),
        },
        "planet_tarabala": {},
    }
    for planet_name, transit_lon in transit_positions.items():
        transit_nak_idx = get_nakshatra_index(transit_lon)
        transit_nak = NAKSHATRAS[transit_nak_idx]
        tarabala = get_tarabala(janma_nak_idx, transit_nak_idx)
        vedha = check_vedha(janma_nak_idx, transit_nak_idx)
        results["planet_tarabala"][planet_name] = {
            "transit_nakshatra_idx": transit_nak_idx,
            "transit_nakshatra_en": transit_nak["en"],
            "transit_nakshatra_ne": transit_nak["ne"],
            "transit_nakshatra_lord": transit_nak["lord"],
            "transit_longitude": round(transit_lon, 4),
            "tarabala": tarabala,
            "vedha": vedha,
            "overall_auspicious": tarabala["is_auspicious"] and not vedha["is_vedha"],
        }
    return results


def calculate_sarvatobhadra_for_date(
    natal_moon_longitude: float,
    natal_moon_sign: int,
    transit_positions: Dict[str, float],
    current_moon_sign: int,
    weekday: int,
) -> Dict[str, Any]:
    tarabala_data = calculate_transit_tarabala_for_all_planets(natal_moon_longitude, transit_positions)
    chandrabala_data = calculate_chandrabala(natal_moon_sign, current_moon_sign)
    auspicious_count = sum(1 for p in tarabala_data["planet_tarabala"].values() if p["overall_auspicious"])
    total_planets = len(tarabala_data["planet_tarabala"])
    vara_lord = VARA_LORDS[weekday % 7]
    moon_tara = tarabala_data["planet_tarabala"].get("Moon", {})
    moon_tara_num = moon_tara.get("tarabala", {}).get("tara_number", 0)
    moon_warning = moon_tara_num in (1, 3, 7)
    overall_score = 0
    if chandrabala_data["is_auspicious"]:
        overall_score += 3
    if not moon_warning:
        overall_score += 2
    overall_score += min(auspicious_count, 4)
    return {
        "janma_nakshatra": tarabala_data["janma_nakshatra"],
        "planet_tarabala": tarabala_data["planet_tarabala"],
        "chandrabala": chandrabala_data,
        "vara": {"weekday": weekday, "lord": vara_lord, "ne": VARA_NE[weekday%7], "en": VARA_EN[weekday%7]},
        "summary": {
            "overall_score": overall_score,
            "overall_quality_ne": "शुभ" if overall_score >= 6 else "मध्यम" if overall_score >= 4 else "अशुभ",
            "overall_quality_en": "Auspicious" if overall_score >= 6 else "Moderate" if overall_score >= 4 else "Inauspicious",
            "auspicious_planets": auspicious_count,
            "total_planets": total_planets,
            "moon_in_warning_tara": moon_warning,
            "chandrabala_ok": chandrabala_data["is_auspicious"],
        },
    }
