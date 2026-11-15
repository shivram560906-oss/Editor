"""
backend/calculator/bhava_chalit.py

Comprehensive Parashari & Shripati Bhava Chalit calculation engine.
Calculates:
  1. 12 Bhava Madhyas (centers) and Sandhis (boundaries: Arambha & Virama)
  2. Planet Chalit placements and Rashi-vs-Chalit Shift Analysis
  3. BPHS Bhava Lagna (Special Lagna) calculations
  4. Classical Astrological interpretations of planetary shifts
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple

SIGN_NAMES_NE = [
    "", "मेष", "वृष", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
]

SIGN_NAMES_EN = [
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    1: ("Mars", "मङ्गल"),
    2: ("Venus", "शुक्र"),
    3: ("Mercury", "बुध"),
    4: ("Moon", "चन्द्र"),
    5: ("Sun", "सूर्य"),
    6: ("Mercury", "बुध"),
    7: ("Venus", "शुक्र"),
    8: ("Mars", "मङ्गल"),
    9: ("Jupiter", "बृहस्पति"),
    10: ("Saturn", "शनि"),
    11: ("Saturn", "शनि"),
    12: ("Jupiter", "बृहस्पति"),
}

BHAVA_NAMES_NE = [
    "",
    "१. प्रथम (तनु भाव / लग्न)",
    "२. द्वितीय (धन / कुटुम्ब भाव)",
    "३. तृतीय (सहज / पराक्रम भाव)",
    "४. चतुर्थ (सुख / बन्धु / मातृ भाव)",
    "५. पञ्चम (सुत / विद्या / बुद्धि भाव)",
    "६. षष्ठ (रिपु / रोग / ऋण भाव)",
    "७. सप्तम (कलत्र / जाया / साझेदारी भाव)",
    "८. अष्टम (आयु / मृत्यु / रन्ध्र भाव)",
    "९. नवम (भाग्य / धर्म भाव)",
    "१०. दशम (कर्म / राज्य / पिता भाव)",
    "११. एकादश (आय / लाभ भाव)",
    "१२. द्वादश (व्यय / मोक्ष भाव)",
]

BHAVA_NAMES_EN = [
    "",
    "1st (Tanu / Ascendant)",
    "2nd (Dhana / Wealth)",
    "3rd (Sahaja / Siblings)",
    "4th (Sukha / Mother/Home)",
    "5th (Putra / Intellect/Children)",
    "6th (Shatru / Obstacles/Debts)",
    "7th (Kalatra / Spouse/Partnership)",
    "8th (Ayur / Longevity/Transformation)",
    "9th (Bhagya / Fortune/Dharma)",
    "10th (Karma / Career/Status)",
    "11th (Labha / Gains/Income)",
    "12th (Vyaya / Loss/Moksha)",
]

PLANET_NAMES_NE = {
    "Sun": "सूर्य",
    "Moon": "चन्द्र",
    "Mars": "मङ्गल",
    "Mercury": "बुध",
    "Jupiter": "बृहस्पति",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु",
    "Uranus": "अरुण",
    "Neptune": "वरुण",
    "Pluto": "यम",
}

NEPALI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")

def to_nepali_digits(n: Any) -> str:
    return str(n).translate(NEPALI_DIGITS)

def format_dms(deg_float: float, in_sign: bool = True) -> str:
    """Format float degrees to Deg° Min' Sec\" format."""
    deg_val = deg_float % 30.0 if in_sign else deg_float % 360.0
    d = int(deg_val)
    rem_m = (deg_val - d) * 60.0
    m = int(rem_m)
    s = int(round((rem_m - m) * 60.0))
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    return f"{d:02d}° {m:02d}' {s:02d}\""

def format_dms_ne(deg_float: float, in_sign: bool = True) -> str:
    s = format_dms(deg_float, in_sign)
    return s.translate(NEPALI_DIGITS)


def analyze_bhava_chalit(chart_data: dict, language: str = "ne") -> dict:
    """
    Perform deep Shripati Bhava Chalit and BPHS Bhava Lagna analysis.
    """
    is_ne = language == "ne"
    if not chart_data or not isinstance(chart_data, dict):
        return {}

    lagna_info = chart_data.get("lagna", {})
    lagna_sidereal = float(lagna_info.get("longitude", 0.0))
    lagna_sign_num = int(lagna_info.get("sign_number", 1))
    planets_list = chart_data.get("planets", [])

    # 1. Fetch or compute Shripati Cusps & Boundaries
    houses_dict = chart_data.get("houses", {})
    cusps = houses_dict.get("cusps", [])
    boundaries = houses_dict.get("boundaries", [])
    bhava_placements = houses_dict.get("placements", {})

    # If cusps not provided in chart_data, compute default Equal/Whole Sign or Shripati
    if len(cusps) != 12:
        try:
            from backend.calculator.houses import calculate_house_cusps, calculate_bhava_boundaries, get_bhava_chalit_placements
        except ImportError:
            from calculator.houses import calculate_house_cusps, calculate_bhava_boundaries, get_bhava_chalit_placements
        
        meta = chart_data.get("metadata", {})
        jd = float(meta.get("julian_date", 2451545.0))
        lat = float(meta.get("latitude", 27.7172))
        lon = float(meta.get("longitude", 85.3240))
        aya_val = float(chart_data.get("ayanamsha_val", 23.79))
        
        try:
            trop_cusps = calculate_house_cusps(jd, lat, lon, "SHRIPATI")
            cusps = [(c - aya_val) % 360.0 for c in trop_cusps]
        except Exception:
            start = math.floor(lagna_sidereal / 30.0) * 30.0
            cusps = [(start + i * 30.0) % 360.0 for i in range(12)]
        
        boundaries = calculate_bhava_boundaries(cusps)
        planet_longs = {p["name"]: float(p.get("sidereal_longitude", 0.0)) for p in planets_list}
        bhava_placements = get_bhava_chalit_placements(planet_longs, cusps)

    # 2. Build 12 Houses Analysis List
    houses_analysis = []
    for i in range(12):
        house_idx = i + 1
        cusp_deg = cusps[i] % 360.0
        start_sandhi, end_sandhi = boundaries[i]
        start_sandhi = start_sandhi % 360.0
        end_sandhi = end_sandhi % 360.0

        # Sign of Bhava Madhya
        madhya_sign_num = int(cusp_deg / 30.0) % 12 + 1
        madhya_sign_ne = SIGN_NAMES_NE[madhya_sign_num]
        madhya_sign_en = SIGN_NAMES_EN[madhya_sign_num]
        lord_en, lord_ne = SIGN_LORDS.get(madhya_sign_num, ("", ""))

        # Start and End Sandhi Signs
        start_sign_num = int(start_sandhi / 30.0) % 12 + 1
        start_sign_ne = SIGN_NAMES_NE[start_sign_num]
        end_sign_num = int(end_sandhi / 30.0) % 12 + 1
        end_sign_ne = SIGN_NAMES_NE[end_sign_num]

        # House Span (extent in degrees)
        span_deg = (end_sandhi - start_sandhi) % 360.0

        # Occupant planets in this Bhava
        occupants = []
        for p in planets_list:
            p_name = p.get("name", "")
            if p_name in ("Uranus", "Neptune", "Pluto", "Chiron"):
                continue
            p_bhava = p.get("bhava_house") or bhava_placements.get(p_name)
            if p_bhava == house_idx:
                p_rashi_h = p.get("house", 1)
                is_shifted = (p_rashi_h != p_bhava)
                p_ne = PLANET_NAMES_NE.get(p_name, p_name)
                occupants.append({
                    "name": p_name,
                    "name_ne": p_ne,
                    "rashi_house": p_rashi_h,
                    "bhava_house": p_bhava,
                    "is_shifted": is_shifted,
                    "is_retrograde": p.get("is_retrograde", False),
                    "is_combust": p.get("is_combust", False),
                    "sign_name": p.get("sign_name", ""),
                    "longitude_dms": format_dms(float(p.get("sidereal_longitude", 0.0))),
                })

        houses_analysis.append({
            "house": house_idx,
            "house_name_ne": BHAVA_NAMES_NE[house_idx],
            "house_name_en": BHAVA_NAMES_EN[house_idx],
            "sign_num": madhya_sign_num,
            "sign_name_ne": madhya_sign_ne,
            "sign_name_en": madhya_sign_en,
            "lord_en": lord_en,
            "lord_ne": lord_ne,
            "madhya_deg": cusp_deg,
            "madhya_dms_ne": format_dms_ne(cusp_deg),
            "madhya_dms_en": format_dms(cusp_deg),
            "start_sandhi_deg": start_sandhi,
            "start_sandhi_dms_ne": f"{start_sign_ne} {format_dms_ne(start_sandhi)}",
            "start_sandhi_dms_en": f"{SIGN_NAMES_EN[start_sign_num]} {format_dms(start_sandhi)}",
            "end_sandhi_deg": end_sandhi,
            "end_sandhi_dms_ne": f"{end_sign_ne} {format_dms_ne(end_sandhi)}",
            "end_sandhi_dms_en": f"{SIGN_NAMES_EN[end_sign_num]} {format_dms(end_sandhi)}",
            "span_deg": round(span_deg, 2),
            "span_str_ne": f"{to_nepali_digits(round(span_deg, 2))}°",
            "span_str_en": f"{round(span_deg, 2)}°",
            "occupants": occupants,
            "occupant_count": len(occupants),
        })

    # 3. Planet Shift Analysis
    planets_shift_analysis = []
    shifted_count = 0
    unshifted_count = 0

    for p in planets_list:
        p_name = p.get("name", "")
        if p_name in ("Uranus", "Neptune", "Pluto", "Chiron"):
            continue
        
        p_long = float(p.get("sidereal_longitude", 0.0))
        p_sign_num = int(p.get("sign_number") or (int(p_long / 30.0) % 12 + 1))
        rashi_h = p.get("house") or (((p_sign_num - lagna_sign_num + 12) % 12) + 1)
        bhava_h = p.get("bhava_house") or bhava_placements.get(p_name) or rashi_h
        
        is_shifted = (rashi_h != bhava_h)
        if is_shifted:
            shifted_count += 1
        else:
            unshifted_count += 1

        # Shift direction
        diff = (bhava_h - rashi_h)
        if diff == -1 or diff == 11:
            direction = "backward"
            dir_ne = f"१ भाव पछाडि ({to_nepali_digits(rashi_h)}म बाट {to_nepali_digits(bhava_h)}म मा सरेको)"
            dir_en = f"1 House Back (from H{rashi_h} to H{bhava_h})"
            effect_ne = f"यस ग्रहले राशि चक्रमा {rashi_h}औँ भावको राशिमा रहे तापनि वास्तविक फल भने {bhava_h}औँ भावको दिनेछ। यसले {bhava_h}औँ भावको कार्यक्षेत्र र कारकत्वलाई सक्रिय बनाउँछ।"
        elif diff == 1 or diff == -11:
            direction = "forward"
            dir_ne = f"१ भाव अगाडि ({to_nepali_digits(rashi_h)}म बाट {to_nepali_digits(bhava_h)}म मा सरेको)"
            dir_en = f"1 House Forward (from H{rashi_h} to H{bhava_h})"
            effect_ne = f"यस ग्रहले राशि चक्रमा {rashi_h}औँ भावमा देखिए पनि भाव चलित अनुसार {bhava_h}औँ भावमा सरेकाले फल दिँदा {bhava_h}औँ भावको विषयमा बढी प्रभाव पार्नेछ।"
        else:
            direction = "same"
            dir_ne = f"अपरिवर्तित ({to_nepali_digits(rashi_h)}म भाव)"
            dir_en = f"Unchanged (House {rashi_h})"
            effect_ne = f"यस ग्रहको राशि भाव र भाव चलित दुवै समान ({to_nepali_digits(rashi_h)}म भाव) रहेकाले यसले पूर्ण रूपमा {to_nepali_digits(rashi_h)}म भावकै स्पष्ट र स्थिर फल प्रदान गर्नेछ।"

        planets_shift_analysis.append({
            "name": p_name,
            "name_ne": PLANET_NAMES_NE.get(p_name, p_name),
            "sign_num": p_sign_num,
            "sign_name_ne": SIGN_NAMES_NE[p_sign_num],
            "sign_name_en": SIGN_NAMES_EN[p_sign_num],
            "longitude_dms_ne": format_dms_ne(p_long),
            "longitude_dms_en": format_dms(p_long),
            "rashi_house": rashi_h,
            "bhava_house": bhava_h,
            "is_shifted": is_shifted,
            "direction": direction,
            "shift_text_ne": dir_ne,
            "shift_text_en": dir_en,
            "effect_ne": effect_ne,
            "is_retrograde": p.get("is_retrograde", False),
            "is_combust": p.get("is_combust", False),
        })

    # 4. BPHS Bhava Lagna Calculation
    panchang_data = chart_data.get("panchang", {})
    sunrise_str = panchang_data.get("sunrise", "06:00")
    if isinstance(sunrise_str, dict):
        sunrise_str = sunrise_str.get("time", "06:00")
    birth_time_str = chart_data.get("metadata", {}).get("birth_time", "12:00:00")

    def time_to_minutes(s: str) -> int:
        try:
            parts = str(s).split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return 360

    b_min = time_to_minutes(birth_time_str)
    sr_min = time_to_minutes(sunrise_str)
    diff_min = b_min - sr_min
    if diff_min < 0:
        diff_min += 1440

    ishta_ghati = diff_min / 24.0
    bhava_lagna_offset = math.floor(ishta_ghati / 5.0)
    bhava_lagna_sign = ((lagna_sign_num - 1 + bhava_lagna_offset) % 12) + 1
    bhava_lagna_name_ne = SIGN_NAMES_NE[bhava_lagna_sign]
    bhava_lagna_name_en = SIGN_NAMES_EN[bhava_lagna_sign]

    bhava_lagna_details = {
        "sunrise_time": sunrise_str,
        "birth_time": birth_time_str,
        "diff_minutes": diff_min,
        "diff_minutes_ne": to_nepali_digits(diff_min),
        "ishta_ghati": round(ishta_ghati, 2),
        "ishta_ghati_ne": to_nepali_digits(round(ishta_ghati, 2)),
        "offset_signs": bhava_lagna_offset,
        "offset_signs_ne": to_nepali_digits(bhava_lagna_offset),
        "remainder_ghati": round(ishta_ghati % 5.0, 2),
        "remainder_ghati_ne": to_nepali_digits(round(ishta_ghati % 5.0, 2)),
        "birth_lagna_sign": lagna_sign_num,
        "birth_lagna_name_ne": SIGN_NAMES_NE[lagna_sign_num],
        "bhava_lagna_sign": bhava_lagna_sign,
        "bhava_lagna_name_ne": bhava_lagna_name_ne,
        "bhava_lagna_name_en": bhava_lagna_name_en,
    }

    # 5. Overall Synthesis / Conclusion
    shifted_planets_names = [p["name_ne"] for p in planets_shift_analysis if p["is_shifted"]]
    if shifted_planets_names:
        summary_ne = f"यस कुण्डलीमा {to_nepali_digits(len(shifted_planets_names))} वटा ग्रहहरू ({', '.join(shifted_planets_names)}) राशि कुण्डलीको तुलनामा भाव चलितमा स्थान परिवर्तन (चलित) भएका छन्। फलादेश गर्दा यिनको प्रभाव वास्तविक चलित भाव अनुसार विश्लेषण गर्नुपर्दछ।"
        summary_en = f"In this chart, {len(shifted_planets_names)} planet(s) ({', '.join([p['name'] for p in planets_shift_analysis if p['is_shifted']])}) have shifted house positions from the Rashi chart into adjacent Bhava Chalit cusps."
    else:
        summary_ne = "यस कुण्डलीका सबै ग्रहहरू राशि कुण्डली र भाव चलित दुवैमा एउटै भावमा स्थिर छन् (कुनै पनि ग्रहको भाव परिवर्तन भएको छैन)।"
        summary_en = "All planets in this chart remain in identical houses in both the Rashi and Bhava Chalit charts."

    return {
        "houses": houses_analysis,
        "planets": planets_shift_analysis,
        "shifted_count": shifted_count,
        "shifted_count_ne": to_nepali_digits(shifted_count),
        "unshifted_count": unshifted_count,
        "unshifted_count_ne": to_nepali_digits(unshifted_count),
        "bhava_lagna": bhava_lagna_details,
        "summary_ne": summary_ne,
        "summary_en": summary_en,
        "lagna_sign_ne": SIGN_NAMES_NE[lagna_sign_num],
        "lagna_sign_en": SIGN_NAMES_EN[lagna_sign_num],
    }
