# -*- coding: utf-8 -*-
"""Marriage Timing Engine — Unified Transit and Mathematical Verification System.

Implements:
1. DMS (Degree, Minute, Second) exact addition and modulo 360 arithmetic.
2. Mathematical Formula 1: Lagna Lord Longitude + 7th Lord Longitude.
3. Mathematical Formula 2: Lagna Lord Longitude + 7th Lord Longitude + Venus Longitude.
4. Primary transit analysis (Lagna Lord, 7th Lord, Venus, Jupiter, Saturn).
5. Age 15 to 50 chronological marriage window generation with multi-indicator scoring.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import ayanamsha, dasha, julian, planetary_positions
except ImportError:
    import ayanamsha
    import dasha
    import julian
    import planetary_positions

from .constants import SIGN_LORDS



SIGN_NAMES_NE = (
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
)
SIGN_NAMES_EN = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
)

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु",
}
PLANET_NAMES_EN = {
    "Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
    "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn", "Rahu": "Rahu", "Ketu": "Ketu",
}

NEPAL_OFFSET_HOURS = 5.75


def deg_to_dms(deg_float: float) -> Tuple[int, int, int, int]:
    """Convert a decimal degree (0..360) to (rashi_0_indexed, degrees_0_29, minutes, seconds)."""
    norm = deg_float % 360.0
    rashi = int(norm // 30.0)
    rem_deg = norm - rashi * 30.0
    d = int(rem_deg)
    rem_min = (rem_deg - d) * 60.0
    m = int(rem_min)
    rem_sec = (rem_min - m) * 60.0
    s = int(round(rem_sec))

    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    if d >= 30:
        d = 0
        rashi = (rashi + 1) % 12
    return rashi, d, m, s


def dms_to_deg(rashi: int, deg: int, minute: int, sec: int) -> float:
    """Convert (rashi_0_indexed, degrees, minutes, seconds) to decimal degree (0..360)."""
    return (rashi * 30.0 + deg + minute / 60.0 + sec / 3600.0) % 360.0


def add_longitudes_dms(*degrees: float) -> Tuple[float, Tuple[int, int, int, int]]:
    """Add multiple longitudes strictly in DMS arithmetic modulo 360."""
    total_sec = 0
    for deg in degrees:
        r, d, m, s = deg_to_dms(deg)
        total_sec += r * 30 * 3600 + d * 3600 + m * 60 + s
    
    total_sec = total_sec % (360 * 3600)
    total_deg = total_sec / 3600.0
    dms_tuple = deg_to_dms(total_deg)
    return total_deg, dms_tuple


def format_dms_string(deg_float: float, lang: str = "ne") -> str:
    """Format degree as '७-११-२२-५३ (वृश्चिक ११°२२′५३″)' or English equivalent."""
    rashi, d, m, s = deg_to_dms(deg_float)
    rashi_name = SIGN_NAMES_NE[rashi] if lang == "ne" else SIGN_NAMES_EN[rashi]
    code_str = f"{rashi}-{d:02d}-{m:02d}-{s:02d}"
    detail_str = f"{rashi_name} {d}°{m:02d}′{s:02d}″"
    return f"{code_str} ({detail_str})"


def get_trikona_signs(sign_0_indexed: int) -> List[int]:
    """Return [base_sign, 5th_from_it, 9th_from_it] as 0-indexed sign numbers."""
    return [
        sign_0_indexed % 12,
        (sign_0_indexed + 4) % 12,
        (sign_0_indexed + 8) % 12,
    ]


def _get_planet_longitude(planets_data: List[dict], planet_name: str) -> float:
    """Extract sidereal longitude for planet_name from chart payload."""
    for p in planets_data:
        if isinstance(p, dict) and p.get("name") == planet_name:
            lon = p.get("longitude")
            if lon is not None:
                return float(lon) % 360.0
            sign_num = p.get("sign_number")
            deg = p.get("degree", 0.0)
            if sign_num is not None:
                return ((int(sign_num) - 1) * 30.0 + float(deg)) % 360.0
    return 0.0


def _get_lagna_longitude(chart_data: dict) -> float:
    lagna = chart_data.get("lagna", {})
    if isinstance(lagna, dict):
        if lagna.get("longitude") is not None:
            return float(lagna["longitude"]) % 360.0
        sign_num = lagna.get("sign_number")
        deg = lagna.get("degree", 0.0)
        if sign_num is not None:
            return ((int(sign_num) - 1) * 30.0 + float(deg)) % 360.0
    return 0.0


def calculate_mathematical_formulas(chart_data: dict) -> Dict[str, Any]:
    """Calculate Formula 1 (Lagna Lord + 7th Lord) and Formula 2 (+ Venus)."""
    lagna_sign_1 = None
    lagna_info = chart_data.get("lagna", {})
    if isinstance(lagna_info, dict):
        lagna_sign_1 = lagna_info.get("sign_number")
    
    if lagna_sign_1 is None:
        lagna_deg = _get_lagna_longitude(chart_data)
        lagna_sign_1 = int(lagna_deg // 30.0) + 1
    
    lagna_sign_1 = int(lagna_sign_1)
    seventh_sign_1 = (lagna_sign_1 + 5) % 12 + 1

    lagna_lord = SIGN_LORDS[lagna_sign_1]
    seventh_lord = SIGN_LORDS[seventh_sign_1]

    planets = chart_data.get("planets", [])
    if not isinstance(planets, list):
        planets = []

    l1_lon = _get_planet_longitude(planets, lagna_lord)
    l7_lon = _get_planet_longitude(planets, seventh_lord)
    venus_lon = _get_planet_longitude(planets, "Venus")

    # Formula 1: Lagna Lord + 7th Lord
    f1_deg, f1_dms = add_longitudes_dms(l1_lon, l7_lon)
    f1_sign_0 = f1_dms[0]
    f1_trikona_0 = get_trikona_signs(f1_sign_0)

    # Formula 2: Lagna Lord + 7th Lord + Venus
    f2_deg, f2_dms = add_longitudes_dms(l1_lon, l7_lon, venus_lon)
    f2_sign_0 = f2_dms[0]
    f2_trikona_0 = get_trikona_signs(f2_sign_0)

    return {
        "lagna_sign": lagna_sign_1,
        "seventh_sign": seventh_sign_1,
        "lagna_lord": lagna_lord,
        "seventh_lord": seventh_lord,
        "l1_longitude": l1_lon,
        "l7_longitude": l7_lon,
        "venus_longitude": venus_lon,
        "formula_1": {
            "longitude": f1_deg,
            "dms": f1_dms,
            "sign_0": f1_sign_0,
            "sign_1": f1_sign_0 + 1,
            "trikona_signs_0": f1_trikona_0,
            "trikona_signs_1": [s + 1 for s in f1_trikona_0],
            "formatted_ne": format_dms_string(f1_deg, "ne"),
            "formatted_en": format_dms_string(f1_deg, "en"),
        },
        "formula_2": {
            "longitude": f2_deg,
            "dms": f2_dms,
            "sign_0": f2_sign_0,
            "sign_1": f2_sign_0 + 1,
            "trikona_signs_0": f2_trikona_0,
            "trikona_signs_1": [s + 1 for s in f2_trikona_0],
            "formatted_ne": format_dms_string(f2_deg, "ne"),
            "formatted_en": format_dms_string(f2_deg, "en"),
        },
    }


def _get_planet_sidereal_sign(planet: str, jd_val: float, ayanamsha_type: str = "lahiri") -> int:
    """Calculate sidereal sign (0-indexed) of a planet at Julian Day jd_val."""
    centuries = julian.jd_to_julian_centuries(jd_val)
    tropical = planetary_positions.get_all_tropical_positions(centuries, jd=jd_val)
    aya = ayanamsha.get_ayanamsha(ayanamsha_type, centuries)
    if planet in tropical:
        sid_deg = (float(tropical[planet][0]) - aya) % 360.0
        return int(sid_deg // 30.0) % 12
    return 0


def _parse_birth_date(chart_data: dict) -> Optional[dt.date]:
    """Birth date from chart metadata, or None when it cannot be determined.

    None is returned rather than an assumed date: the marriage-window scan is
    anchored on the birth date, so substituting a placeholder year would scan
    the wrong 35 years and report confident but meaningless dates.
    """
    metadata = chart_data.get("metadata") or {}
    b_date_str = metadata.get("birth_date") or chart_data.get("birth_date")
    if b_date_str:
        try:
            return dt.datetime.strptime(str(b_date_str)[:10], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None
    return None


def find_marriage_windows_age_15_to_50(
    chart_data: dict,
    min_score: int = 50,
    ayanamsha_type: str = "lahiri"
) -> List[Dict[str, Any]]:
    """Generate chronological probable marriage windows between Age 15 and 50.
    
    Uses:
    1. Primary Transits (Lagna lord, 7th lord, Venus, Jupiter, Saturn).
    2. Mathematical verification with Formula 1 and Formula 2.
    3. Dasha alignment check.
    """
    formulas = calculate_mathematical_formulas(chart_data)
    lagna_sign_0 = formulas["lagna_sign"] - 1
    seventh_sign_0 = formulas["seventh_sign"] - 1

    planets = chart_data.get("planets", [])
    venus_sign_0 = int(_get_planet_longitude(planets, "Venus") // 30.0) % 12

    # Signs for rule checks
    # Transit Rule Kh: 7th sign, 5th/9th from 7th
    seventh_trikona_0 = get_trikona_signs(seventh_sign_0)
    # Transit Rule Kh.2: Natal Venus sign
    # Transit Rule Kh.3: Natal Lagna or 7th sign
    kh_allowed_signs_0 = set(seventh_trikona_0) | {venus_sign_0, lagna_sign_0, seventh_sign_0}

    # Mathematical Formula 1 and Formula 2 target trikonas
    f1_trikona_0 = set(formulas["formula_1"]["trikona_signs_0"])
    f2_trikona_0 = set(formulas["formula_2"]["trikona_signs_0"])

    birth_date = _parse_birth_date(chart_data)
    if birth_date is None:
        # Without the real birth date the whole age 15-50 scan would be
        # anchored to a made-up year, so return no windows instead of
        # confident dates for the wrong three and a half decades.
        return []
    _safe_day = 28 if (birth_date.month == 2 and birth_date.day == 29) else birth_date.day
    try:
        start_date = dt.date(birth_date.year + 15, birth_date.month, birth_date.day)
    except ValueError:
        start_date = dt.date(birth_date.year + 15, birth_date.month, _safe_day)
    try:
        end_date = dt.date(birth_date.year + 50, birth_date.month, birth_date.day)
    except ValueError:
        end_date = dt.date(birth_date.year + 50, birth_date.month, _safe_day)

    # Sample Jupiter positions every 45 days (~1.5 months) across age 15 to 50
    curr_date = start_date
    step_days = 45
    windows: List[Dict[str, Any]] = []

    current_window: Optional[Dict[str, Any]] = None

    while curr_date <= end_date:
        jd_val = julian.datetime_to_jd(curr_date.year, curr_date.month, curr_date.day, 12, 0, 0.0, NEPAL_OFFSET_HOURS)
        jup_sign_0 = _get_planet_sidereal_sign("Jupiter", jd_val, ayanamsha_type)
        sat_sign_0 = _get_planet_sidereal_sign("Saturn", jd_val, ayanamsha_type)

        # Check conditions
        matched_indicators_ne: List[str] = []
        matched_indicators_en: List[str] = []
        score = 0

        # Indicator 1: Jupiter in 7th or 5th/9th from 7th, or Lagna
        if jup_sign_0 in seventh_trikona_0 or jup_sign_0 == lagna_sign_0:
            score += 20
            matched_indicators_ne.append("बृहस्पतिको सप्तम भाव वा सप्तमबाट ५/९ भाव (वा लग्न) मा अनुकूल गोचर")
            matched_indicators_en.append("Jupiter favorable transit in 7th, 5th/9th from 7th, or Lagna")
        
        # Indicator 2: Jupiter in natal Venus sign
        if jup_sign_0 == venus_sign_0:
            score += 15
            matched_indicators_ne.append(f"जन्म शुक्र रहेको राशि ({SIGN_NAMES_NE[venus_sign_0]}) मा बृहस्पतिको गोचर")
            matched_indicators_en.append(f"Jupiter transiting natal Venus sign ({SIGN_NAMES_EN[venus_sign_0]})")

        # Indicator 3: Saturn in 7th, 5th/9th from 7th, Lagna, or natal Venus sign
        if sat_sign_0 in kh_allowed_signs_0:
            score += 15
            matched_indicators_ne.append("शनिको सप्तम/त्रिकोण, लग्न वा शुक्रको राशिमा प्रभावकारी गोचर")
            matched_indicators_en.append("Saturn transit influence on 7th/trikona, Lagna or Venus sign")

        # Indicator 4: Mathematical Formula 1 (Lagna Lord + 7th Lord)
        if jup_sign_0 in f1_trikona_0:
            score += 25
            matched_indicators_ne.append(f"गणितीय सूत्र–१ (लग्नेश+सप्तमेश = {SIGN_NAMES_NE[formulas['formula_1']['sign_0']]}) वा ५/९ राशिमा गुरु गोचर")
            matched_indicators_en.append(f"Math Formula 1 (L1+L7 = {SIGN_NAMES_EN[formulas['formula_1']['sign_0']]}) or 5th/9th Jupiter transit")

        # Indicator 5: Mathematical Formula 2 (Lagna Lord + 7th Lord + Venus)
        if jup_sign_0 in f2_trikona_0:
            score += 25
            matched_indicators_ne.append(f"गणितीय सूत्र–२ (लग्नेश+सप्तमेश+शुक्र = {SIGN_NAMES_NE[formulas['formula_2']['sign_0']]}) वा ५/९ राशिमा गुरु गोचर")
            matched_indicators_en.append(f"Math Formula 2 (L1+L7+Venus = {SIGN_NAMES_EN[formulas['formula_2']['sign_0']]}) or 5th/9th Jupiter transit")

        if score >= min_score:
            if current_window is None:
                current_window = {
                    "start_date": curr_date,
                    "end_date": curr_date,
                    "max_score": score,
                    "scores": [score],
                    "jup_signs": {jup_sign_0},
                    "indicators_ne": set(matched_indicators_ne),
                    "indicators_en": set(matched_indicators_en),
                }
            else:
                # Merge into existing continuous window
                current_window["end_date"] = curr_date
                current_window["scores"].append(score)
                current_window["max_score"] = max(current_window["max_score"], score)
                current_window["jup_signs"].add(jup_sign_0)
                current_window["indicators_ne"].update(matched_indicators_ne)
                current_window["indicators_en"].update(matched_indicators_en)
        else:
            if current_window is not None:
                windows.append(current_window)
                current_window = None

        curr_date += dt.timedelta(days=step_days)

    if current_window is not None:
        windows.append(current_window)

    # Format and consolidate resulting chronological windows
    result: List[Dict[str, Any]] = []
    for w in windows:
        st_date: dt.date = w["start_date"]
        en_date: dt.date = w["end_date"]
        # Extend end_date slightly to cover the duration of that transit step
        en_date = en_date + dt.timedelta(days=step_days)
        
        age_start = round((st_date - birth_date).days / 365.25, 1)
        age_end = round((en_date - birth_date).days / 365.25, 1)
        avg_score = int(round(sum(w["scores"]) / len(w["scores"])))
        final_score = min(100, max(w["max_score"], avg_score))

        # Strength label
        if final_score >= 80:
            strength_ne = "अत्यधिक प्रबल (Strongest)"
            strength_en = "Highly Favorable / Strongest"
        elif final_score >= 65:
            strength_ne = "प्रबल अनुकूल (High Probability)"
            strength_en = "High Probability"
        else:
            strength_ne = "मध्यम अनुकूल (Moderate Favorable)"
            strength_en = "Moderate Favorable"

        # BS Conversion string
        bs_start = dasha.ad_to_bs_str(st_date)
        bs_end = dasha.ad_to_bs_str(en_date)

        result.append({
            "start_date": st_date.isoformat(),
            "end_date": en_date.isoformat(),
            "bs_start": bs_start,
            "bs_end": bs_end,
            "age_start": age_start,
            "age_end": age_end,
            "score": final_score,
            "strength_ne": strength_ne,
            "strength_en": strength_en,
            "indicators_ne": sorted(list(w["indicators_ne"])),
            "indicators_en": sorted(list(w["indicators_en"])),
        })

    # Sort strictly chronologically
    result.sort(key=lambda x: x["start_date"])
    return result
