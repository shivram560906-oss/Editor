# -*- coding: utf-8 -*-
"""
backend/calculator/child_analysis_engine.py

Classical Parashari Child Analysis (पुत्र अध्याय / सन्तान विचार)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full 8-Step Classical Parashari System (बृहत्पाराशर होराशास्त्र):
  Step 1: मुख्य ५ आधार-तत्वहरू (5 Core Factors: 5th House, 5th Lord, Jupiter, 9th House/Lord, D-7)
  Step 2: पञ्चम भावको स्थिति र ग्रह दृष्टि (Occupants & full BPHS Aspects on 5th House)
  Step 3: बृहस्पति (गुरु) को विस्तृत स्थिति र बल (House, Dignity, Combustion, Retrograde, Affliction)
  Step 4: पुत्र-अरिष्ट तथा दोष भंग योग (Putra-Arishta / Obstacles & Benefic Cancellations)
  Step 5: सप्तमांश (D-7) कुण्डली विश्लेषण (D-7 Lagna, Lagnesh, 5th House, Jupiter)
  Step 6: सन्तान संख्या शास्त्रीय अनुमान (Child Count: Sign Modality & Benefic Associations)
  Step 7: सन्तान लिंग (पुत्र/पुत्री) प्रवृत्ति (Gender Tendency: Odd/Even Signs, Planetary Genders, D-7)
  Step 8: सन्तान प्राप्ति समय (दशा तथा गोचर) र शान्ति उपाय (Vimshottari Dasha, Jupiter Transit, Remedies)
"""
from __future__ import annotations
import math
import datetime
from typing import Dict, Any, List, Optional, Tuple

SIGN_NAMES_NE = [
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
]

SIGN_NAMES_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु", "Lagna": "लग्न"
}

# Sign Modality (चर / स्थिर / द्विस्वभाव)
# 0: Chara (Movable), 1: Sthira (Fixed), 2: Dwiswabhava (Dual)
SIGN_MODALITY = {
    0: "Chara", 1: "Sthira", 2: "Dwiswabhava", 3: "Chara",
    4: "Sthira", 5: "Dwiswabhava", 6: "Chara", 7: "Sthira",
    8: "Dwiswabhava", 9: "Chara", 10: "Sthira", 11: "Dwiswabhava"
}

MODALITY_NE = {
    "Chara": "चर राशि (Movable)",
    "Sthira": "स्थिर राशि (Fixed)",
    "Dwiswabhava": "द्विस्वभाव राशि (Dual)"
}

# Sign Gender: Odd signs (1, 3, 5, 7, 9, 11 - 0-indexed: 0, 2, 4, 6, 8, 10) = Male; Even = Female
# Planetary Gender (BPHS):
# Male: Sun, Mars, Jupiter
# Female: Moon, Venus, Rahu (some traditions female/shadow)
# Neutral / Eunuch: Mercury (female-leaning neuter), Saturn (male-leaning neuter), Ketu
PLANET_GENDERS = {
    "Sun": "Male", "Mars": "Male", "Jupiter": "Male",
    "Moon": "Female", "Venus": "Female",
    "Mercury": "Neutral", "Saturn": "Neutral", "Rahu": "Female", "Ketu": "Neutral"
}

EXALTATION_SIGNS = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6, "Rahu": 2, "Ketu": 8
}

DEBILITATION_SIGNS = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0, "Rahu": 8, "Ketu": 2
}

COMBUSTION_ORB = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0
}


def _sign_idx(lon: float) -> int:
    return int(lon / 30.0) % 12

def _house_from(planet_lon: float, lagna_lon: float) -> int:
    return ((_sign_idx(planet_lon) - _sign_idx(lagna_lon)) % 12) + 1

def _arc_dist(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2) % 360.0
    return 360.0 - diff if diff > 180.0 else diff

def _is_combust(p_name: str, p_lon: float, sun_lon: float) -> bool:
    if p_name in ("Sun", "Rahu", "Ketu"):
        return False
    orb = COMBUSTION_ORB.get(p_name, 12.0)
    return _arc_dist(p_lon, sun_lon) <= orb


# ── STEP 1: FIVE CORE FACTORS ─────────────────────────────────────────────────

def analyze_five_core_factors(chart_data: dict) -> dict:
    """
    Extracts the five fundamental pillars of Santana Vichara:
      1. 5th House (Sign, Lord)
      2. 5th Lord (House, Sign, Dignity)
      3. Jupiter (Child significator / Putra-karaka)
      4. 9th House & 9th Lord (Fortune of Children)
      5. D-7 Saptamsha summary
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    # 5th house
    five_sign = (lagna_sign + 4) % 12
    five_lord_name = SIGN_LORDS[five_sign]
    five_lord_data = planets.get(five_lord_name, {})
    five_lord_lon = float(five_lord_data.get("sidereal_longitude") or five_lord_data.get("longitude") or 0.0)
    five_lord_house = _house_from(five_lord_lon, lagna_lon) if five_lord_data else 1
    five_lord_sign = _sign_idx(five_lord_lon)

    # Jupiter
    jup_data = planets.get("Jupiter", {})
    jup_lon = float(jup_data.get("sidereal_longitude") or jup_data.get("longitude") or 0.0)
    jup_house = _house_from(jup_lon, lagna_lon) if jup_data else 1
    jup_sign = _sign_idx(jup_lon)

    # 9th house
    nine_sign = (lagna_sign + 8) % 12
    nine_lord_name = SIGN_LORDS[nine_sign]
    nine_lord_data = planets.get(nine_lord_name, {})
    nine_lord_lon = float(nine_lord_data.get("sidereal_longitude") or nine_lord_data.get("longitude") or 0.0)
    nine_lord_house = _house_from(nine_lord_lon, lagna_lon) if nine_lord_data else 1

    # D7 summary
    d7 = chart_data.get("vargas", {}).get("D7")
    d7_avail = bool(d7 and isinstance(d7, dict) and d7.get("lagna"))

    return {
        "fifth_house": {
            "sign_idx": five_sign,
            "sign_ne": SIGN_NAMES_NE[five_sign],
            "sign_en": SIGN_NAMES_EN[five_sign],
            "lord": five_lord_name,
            "lord_ne": PLANET_NAMES_NE.get(five_lord_name, five_lord_name),
            "lord_house": five_lord_house,
            "lord_sign_ne": SIGN_NAMES_NE[five_lord_sign],
        },
        "jupiter": {
            "house": jup_house,
            "sign_ne": SIGN_NAMES_NE[jup_sign],
            "is_retrograde": bool(jup_data.get("is_retrograde", False)),
        },
        "ninth_house": {
            "sign_ne": SIGN_NAMES_NE[nine_sign],
            "lord_ne": PLANET_NAMES_NE.get(nine_lord_name, nine_lord_name),
            "lord_house": nine_lord_house,
        },
        "d7_available": d7_avail
    }


# ── STEP 2: 5TH HOUSE OCCUPANTS & GRAHA DRISHTI ───────────────────────────────

def analyze_fifth_house_and_aspects(chart_data: dict) -> dict:
    """
    Examines all planets occupying or aspecting the 5th house according to Parashari Graha Drishti:
      - All planets: 7th aspect
      - Mars: 4th, 7th, 8th
      - Jupiter: 5th, 7th, 9th (Amrita Drishti)
      - Saturn: 3rd, 7th, 10th
      - Rahu/Ketu: 5th, 7th, 9th
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)

    target_house = 5
    occupants = []
    aspecting_planets = []

    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}

    for p_name, p_data in planets.items():
        lon = float(p_data.get("sidereal_longitude") or p_data.get("longitude") or 0.0)
        h = _house_from(lon, lagna_lon)

        # Occupant
        if h == target_house:
            occupants.append({
                "planet": p_name,
                "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
                "is_benefic": p_name in benefics,
                "note_ne": "शुभग्रह उपस्थिति (सन्तान सुखवर्धक)" if p_name in benefics else "पापग्रह उपस्थिति (बाधा/विलम्ब कारक)"
            })

        # Drishti (Aspect) distance from planet to 5th house
        dist = ((target_house - h) % 12) + 1  # 1-indexed house distance

        has_aspect = False
        aspect_type = ""

        # 7th aspect for all planets
        if dist == 7:
            has_aspect = True
            aspect_type = "७औँ पूर्ण दृष्टि"

        # Special aspects
        if p_name == "Mars" and dist in (4, 8):
            has_aspect = True
            aspect_type = f"{dist}औँ विशेष दृष्टि"
        elif p_name == "Jupiter" and dist in (5, 9):
            has_aspect = True
            aspect_type = f"{dist}औँ विशेष अमृत दृष्टि"
        elif p_name == "Saturn" and dist in (3, 10):
            has_aspect = True
            aspect_type = f"{dist}औँ विशेष दृष्टि"
        elif p_name in ("Rahu", "Ketu") and dist in (5, 9):
            has_aspect = True
            aspect_type = f"{dist}औँ दृष्टि"

        if has_aspect:
            aspecting_planets.append({
                "planet": p_name,
                "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
                "from_house": h,
                "aspect_type": aspect_type,
                "is_benefic": p_name in benefics,
                "effect_ne": "अत्यन्त शुभ (सन्तान सुख र रक्षा)" if p_name == "Jupiter" else ("शुभ फल" if p_name in benefics else "कष्ट वा विलम्ब कारक")
            })

    return {
        "occupants": occupants,
        "aspects": aspecting_planets,
        "has_jupiter_aspect": any(a["planet"] == "Jupiter" for a in aspecting_planets),
        "has_saturn_aspect": any(a["planet"] == "Saturn" for a in aspecting_planets),
        "has_mars_aspect": any(a["planet"] == "Mars" for a in aspecting_planets),
    }


# ── STEP 3: JUPITER (PUTRA-KARAKA) ANALYSIS ───────────────────────────────────

def analyze_jupiter_karaka(chart_data: dict) -> dict:
    """
    Evaluates Jupiter's strength, dignity, combustion, retrograde, and malefic affliction.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    sun = planets.get("Sun", {})
    sun_lon = float(sun.get("sidereal_longitude") or sun.get("longitude") or 0.0)

    jup = planets.get("Jupiter", {})
    if not jup:
        return {"status_ne": "गुरुको विवरण उपलब्ध छैन", "score": 50}

    j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
    j_house = _house_from(j_lon, lagna_lon)
    j_sign = _sign_idx(j_lon)

    is_exalted = j_sign == EXALTATION_SIGNS["Jupiter"]
    is_own = j_sign in (8, 11)  # Sag, Pisces
    is_debilitated = j_sign == DEBILITATION_SIGNS["Jupiter"]
    is_retro = bool(jup.get("is_retrograde", False))
    is_combust = _is_combust("Jupiter", j_lon, sun_lon)

    # Check malefic aspect on Jupiter
    afflictions = []
    for m in ("Saturn", "Mars", "Rahu", "Ketu"):
        if m in planets:
            m_lon = float(planets[m].get("sidereal_longitude") or planets[m].get("longitude") or 0.0)
            m_h = _house_from(m_lon, lagna_lon)
            dist = ((j_house - m_h) % 12) + 1
            is_aspecting = (dist == 7) or (m == "Mars" and dist in (4, 8)) or (m == "Saturn" and dist in (3, 10))
            if m_h == j_house:
                afflictions.append(f"{PLANET_NAMES_NE.get(m, m)} सँग युति")
            elif is_aspecting:
                afflictions.append(f"{PLANET_NAMES_NE.get(m, m)} को {dist}औँ दृष्टि")

    # Dignity string
    if is_exalted:
        dignity_ne = "परमोच्च (कर्कट राशि) — अत्यन्त बलवान्"
    elif is_own:
        dignity_ne = "स्वराशि (धनु/मीन) — बलवान्"
    elif is_debilitated:
        dignity_ne = "नीच राशि (मकर) — निर्बल"
    else:
        dignity_ne = f"{SIGN_NAMES_NE[j_sign]} राशिमा सामान्य"

    # Strength evaluation
    strength = "बलवान् (Strong)"
    if is_debilitated or is_combust:
        strength = "निर्बल / पीडित (Afflicted)"
    elif is_exalted or is_own or j_house in (1, 4, 5, 9, 10):
        strength = "अत्यन्त बलवान् र शुभ (Highly Auspicious)"

    return {
        "house": j_house,
        "sign_ne": SIGN_NAMES_NE[j_sign],
        "dignity_ne": dignity_ne,
        "is_retrograde": is_retro,
        "is_combust": is_combust,
        "afflictions": afflictions,
        "strength_ne": strength,
        "retrograde_note_ne": "गुरु वक्री हुनुले सन्तान प्राप्तिमा केही विलम्ब वा अतिरिक्त प्रयासको शास्त्रीय संकेत गर्दछ।" if is_retro else "",
        "combust_note_ne": "गुरु सूर्यद्वारा अस्तङ्गत रहेकाले सन्तान सुखका लागि गुरु शान्ति र मन्त्र जप शुभ हुन्छ।" if is_combust else ""
    }


# ── STEP 4: PUTRA-ARISHTA & BHANGA YOGAS ───────────────────────────────────────

def evaluate_putra_arishta_and_bhanga(chart_data: dict) -> dict:
    """
    Evaluates obstacles (Putra-Arishta, Sarpa Dosha, Santana Badha) and benefic cancellations (Bhanga Yogas).
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    five_sign = (lagna_sign + 4) % 12
    five_lord = SIGN_LORDS[five_sign]
    five_lord_data = planets.get(five_lord, {})
    five_lord_lon = float(five_lord_data.get("sidereal_longitude") or five_lord_data.get("longitude") or 0.0)
    five_lord_house = _house_from(five_lord_lon, lagna_lon) if five_lord_data else 1
    five_lord_sign = _sign_idx(five_lord_lon)

    jup_data = planets.get("Jupiter", {})
    jup_lon = float(jup_data.get("sidereal_longitude") or jup_data.get("longitude") or 0.0)
    jup_house = _house_from(jup_lon, lagna_lon) if jup_data else 1

    obstacles = []
    bhangas = []

    # 1. 5th lord in Dusthana (6, 8, 12)
    if five_lord_house in (6, 8, 12):
        obstacles.append(f"पञ्चमेश {PLANET_NAMES_NE.get(five_lord, five_lord)} दुष्टस्थान ({five_lord_house} भाव) मा रहेकाले सन्तान सुखमा बाधा वा विलम्ब")

    # 2. 5th lord debilitated
    if five_lord_sign == DEBILITATION_SIGNS.get(five_lord, -1):
        obstacles.append(f"पञ्चमेश {PLANET_NAMES_NE.get(five_lord, five_lord)} नीच राशिमा निर्बल अवस्थामा छ")

    # 3. Rahu/Ketu in 5th house (Sarpa Dosha / Naga Dosha hint)
    rahu = planets.get("Rahu", {})
    if rahu and _house_from(float(rahu.get("longitude") or 0.0), lagna_lon) == 5:
        obstacles.append("पञ्चम भावमा राहुको उपस्थिति (नाग/सर्प सम्बन्धी बाधा योगको शास्त्रीय संकेत)")

    ketu = planets.get("Ketu", {})
    if ketu and _house_from(float(ketu.get("longitude") or 0.0), lagna_lon) == 5:
        obstacles.append("पञ्चम भावमा केतुको उपस्थिति (गर्भधारणमा चिकित्सा सतर्कता आवश्यक)")

    # ── Bhanga (Cancellations) ──
    # A. Jupiter aspects 5th house
    dist_jup_to_5 = ((5 - jup_house) % 12) + 1
    if dist_jup_to_5 in (5, 7, 9) or jup_house == 5:
        bhangas.append("सन्तानकारक देवगुरु बृहस्पतिको पञ्चम भावमा अमृत दृष्टि परेकाले सम्पूर्ण बाधा दोष निवारण (Bhanga)")

    # B. Venus in Kendra / Trikona
    ven = planets.get("Venus", {})
    if ven:
        v_h = _house_from(float(ven.get("longitude") or 0.0), lagna_lon)
        if v_h in (1, 4, 5, 9, 10):
            bhangas.append(f"दैत्यगुरु शुक्र शुभ स्थान ({v_h} भाव) मा बलवान् रहेकाले वंश वृद्धि योग")

    # C. 5th lord strong in Kendra/Trikona
    if five_lord_house in (1, 4, 5, 7, 9, 10) and five_lord_sign != DEBILITATION_SIGNS.get(five_lord, -1):
        bhangas.append(f"पञ्चमेश {PLANET_NAMES_NE.get(five_lord, five_lord)} केन्द्र/त्रिकोण ({five_lord_house} भाव) मा बलवान् रहेकाले सन्तान सुख सुनिश्चित")

    has_defect = len(obstacles) > 0
    is_cancelled = len(bhangas) > 0

    if not has_defect:
        status_ne = "पुत्र-अरिष्ट वा सन्तान बाधा योग छैन (उत्तम सन्तान योग)"
        code = "NO_OBSTACLE"
    elif has_defect and is_cancelled:
        status_ne = "बाधा योग देखिए पनि शुभग्रहको प्रभावले पूर्ण भंग भएको छ (दोष निवारण)"
        code = "OBSTACLE_CANCELLED"
    else:
        status_ne = "सन्तान प्राप्तिमा केही बाधा/विलम्ब योग विद्यमान (शान्ति उपाय आवश्यक)"
        code = "ACTIVE_OBSTACLE"

    return {
        "code": code,
        "status_ne": status_ne,
        "has_defect": has_defect,
        "is_cancelled": is_cancelled,
        "obstacles": obstacles,
        "bhangas": bhangas
    }


# ── STEP 5: D-7 SAPTAMSHA ANALYSIS ────────────────────────────────────────────

def analyze_d7_saptamsha(chart_data: dict) -> dict:
    """
    Detailed inspection of D-7 Saptamsha:
      - D-7 Lagna & Lagnesha
      - D-7 5th House & 5th Lord
      - D-7 Jupiter placement
    """
    d7 = chart_data.get("vargas", {}).get("D7")
    if not d7 or not isinstance(d7, dict):
        return {"available": False, "note_ne": "D-7 सप्तांश कुण्डली उपलब्ध छैन"}

    d7_lagna = d7.get("lagna", {})
    d7_lagna_sign = int(d7_lagna.get("sign_number") or 1) - 1
    d7_lagnesh_name = SIGN_LORDS[d7_lagna_sign]

    d7_planets = {p["name"]: p for p in d7.get("planets", []) if isinstance(p, dict) and p.get("name")}

    # D7 5th house
    d7_five_sign = (d7_lagna_sign + 4) % 12
    d7_five_lord = SIGN_LORDS[d7_five_sign]
    d7_five_lord_p = d7_planets.get(d7_five_lord, {})
    d7_five_lord_house = int(d7_five_lord_p.get("house") or 1) if d7_five_lord_p else 1

    # D7 5th house occupants
    d7_five_occupants = [
        PLANET_NAMES_NE.get(p["name"], p["name"])
        for p in d7.get("planets", [])
        if int(p.get("house") or 0) == 5
    ]

    # D7 Jupiter
    d7_jup = d7_planets.get("Jupiter", {})
    d7_jup_house = int(d7_jup.get("house") or 1) if d7_jup else 1

    # Evaluation
    is_d7_strong = d7_five_lord_house in (1, 4, 5, 7, 9, 10, 11) and d7_jup_house in (1, 4, 5, 7, 9, 10, 11)

    return {
        "available": True,
        "d7_lagna_sign_ne": SIGN_NAMES_NE[d7_lagna_sign],
        "d7_lagnesh_ne": PLANET_NAMES_NE.get(d7_lagnesh_name, d7_lagnesh_name),
        "d7_fifth_sign_ne": SIGN_NAMES_NE[d7_five_sign],
        "d7_fifth_lord_ne": PLANET_NAMES_NE.get(d7_five_lord, d7_five_lord),
        "d7_fifth_lord_house": d7_five_lord_house,
        "d7_fifth_occupants": d7_five_occupants,
        "d7_jupiter_house": d7_jup_house,
        "strength_ne": "सप्तांश कुण्डलीमा सन्तान सुख अत्यन्त अनुकूल र पुष्टिकारक" if is_d7_strong else "सप्तांश कुण्डलीमा मध्यम फल (सामान्य प्रयास आवश्यक)"
    }


# ── STEP 6: SANTANA SANKHYA (CHILD COUNT ESTIMATION) ──────────────────────────

def estimate_child_count(chart_data: dict) -> dict:
    """
    Traditional BPHS guidelines for estimating child count tendencies:
      - Jupiter's sign modality:
        - Chara (Movable): High fertility / Higher count (3 or more)
        - Dwiswabhava (Dual): Medium fertility (2 to 3)
        - Sthira (Fixed): Limited fertility (1 to 2)
      - Benefic aspects/conjunctions with 5th house increase probability.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    jup = planets.get("Jupiter", {})
    j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
    j_sign = _sign_idx(j_lon)
    modality = SIGN_MODALITY[j_sign]

    # Count benefic influences on 5th house
    five_sign = (lagna_sign + 4) % 12
    benefic_count = 0
    for b in ("Jupiter", "Venus", "Mercury", "Moon"):
        if b in planets:
            b_lon = float(planets[b].get("sidereal_longitude") or planets[b].get("longitude") or 0.0)
            b_h = _house_from(b_lon, lagna_lon)
            if b_h == 5:
                benefic_count += 1

    if modality == "Chara":
        est_range = "२ देखि ३ (वा सोभन्दा बढी)"
        desc = f"सन्तानकारक गुरु {MODALITY_NE[modality]}मा रहेकाले शास्त्रीय रूपमा बहु-सन्तान सुखको अनुकूल संकेत मिल्दछ।"
    elif modality == "Dwiswabhava":
        est_range = "२ (मध्यम सन्तान योग)"
        desc = f"सन्तानकारक गुरु {MODALITY_NE[modality]}मा रहेकाले सामान्यतया दुई सन्तानको सन्तुलित योग रहने शास्त्रीय मान्यता छ।"
    else:
        est_range = "१ देखि २"
        desc = f"सन्तानकारक गुरु {MODALITY_NE[modality]}मा रहेकाले सीमित संख्या (१ वा २) सन्तान योगको संकेत गर्दछ।"

    return {
        "modality_ne": MODALITY_NE[modality],
        "jupiter_sign_ne": SIGN_NAMES_NE[j_sign],
        "estimated_range_ne": est_range,
        "benefic_factor_ne": f"पञ्चम भावमा {benefic_count} शुभग्रहको उपस्थिति",
        "description_ne": desc
    }


# ── STEP 7: GENDER TENDENCY (SANTANA LINGA) ───────────────────────────────────

def evaluate_gender_tendency(chart_data: dict) -> dict:
    """
    Evaluates traditional planetary gender inclinations (पुत्र / पुत्री ऊर्जा प्रवृत्ति):
      - 5th house sign: Odd (1, 3, 5, 7, 9, 11) = Male (पुत्र); Even = Female (पुत्री)
      - 5th lord gender: Sun/Mars/Jup = Male; Moon/Ven = Female
      - Jupiter sign gender: Odd = Male; Even = Female
      - D-7 Lagna sign gender
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    five_sign = (lagna_sign + 4) % 12
    five_lord = SIGN_LORDS[five_sign]

    jup = planets.get("Jupiter", {})
    j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
    j_sign = _sign_idx(j_lon)

    male_points = 0
    female_points = 0

    # 1. 5th house sign
    is_five_odd = (five_sign % 2 == 0)  # 0=Aries (1st, odd)
    if is_five_odd:
        male_points += 1
        five_sign_gender = "पुरुष राशि (Odd Sign)"
    else:
        female_points += 1
        five_sign_gender = "स्त्री राशि (Even Sign)"

    # 2. 5th lord
    lord_gen = PLANET_GENDERS.get(five_lord, "Neutral")
    if lord_gen == "Male":
        male_points += 1
        lord_gen_ne = "पुरुष ग्रह"
    elif lord_gen == "Female":
        female_points += 1
        lord_gen_ne = "स्त्री ग्रह"
    else:
        lord_gen_ne = "सम/नपुंसक ग्रह"

    # 3. Jupiter sign
    is_jup_odd = (j_sign % 2 == 0)
    if is_jup_odd:
        male_points += 1
    else:
        female_points += 1

    # 4. D7 Lagna sign
    d7 = chart_data.get("vargas", {}).get("D7")
    d7_lagna_sign = int(d7.get("lagna", {}).get("sign_number") or 1) - 1 if d7 else 0
    if d7_lagna_sign % 2 == 0:
        male_points += 1
    else:
        female_points += 1

    if male_points > female_points:
        tendency_ne = "प्रथम सन्तानमा पुत्र (बालक) योगको बलियो शास्त्रीय सम्भावना"
        summary_code = "MALE_INCLINED"
    elif female_points > male_points:
        tendency_ne = "प्रथम सन्तानमा पुत्री (कन्या) योगको बलियो शास्त्रीय सम्भावना"
        summary_code = "FEMALE_INCLINED"
    else:
        tendency_ne = "पुत्र तथा पुत्री दुवै सन्तान सुखको समान र सन्तुलित सम्भावना"
        summary_code = "BALANCED"

    return {
        "code": summary_code,
        "tendency_ne": tendency_ne,
        "fifth_sign_gender_ne": five_sign_gender,
        "fifth_lord_gender_ne": f"{PLANET_NAMES_NE.get(five_lord, five_lord)} ({lord_gen_ne})",
        "male_score": male_points,
        "female_score": female_points,
        "disclaimer_ne": "शास्त्रीय सूचना: यो कुनै चिकित्सा वा गर्भलिंग परीक्षण होइन; यो केवल जन्मकुण्डलीका ग्रहीय ऊर्जा र प्रवृत्तिको परम्परागत ज्योतिषीय अध्ययन मात्र हो।"
    }


# ── STEP 8: TIMING (DASHA & TRANSIT) & REMEDIES ───────────────────────────────

def evaluate_conception_timing(chart_data: dict) -> dict:
    """
    Determines favorable child-bearing timing:
      - Vimshottari Mahadasha/Antardasha of 5th lord & Jupiter
      - Transit of Jupiter over 5th house, 5th lord, or natal Jupiter
      - Classical remedial measures (Santan Gopal Mantra, Guru Shanti)
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    five_sign = (lagna_sign + 4) % 12
    five_lord = SIGN_LORDS[five_sign]

    dashas = chart_data.get("dasha") or chart_data.get("vimshottari_dasha") or []
    favorable_dashas = []

    today_str = datetime.date.today().isoformat()

    for item in dashas:
        if not isinstance(item, dict):
            continue
        lord = item.get("lord") or item.get("planet", "")
        start = str(item.get("start") or item.get("start_date", ""))[:10]
        end = str(item.get("end") or item.get("end_date", ""))[:10]

        is_fav = lord in (five_lord, "Jupiter", "Venus")
        if is_fav:
            is_active = (start <= today_str <= end) if start and end else False
            favorable_dashas.append({
                "lord": lord,
                "lord_ne": PLANET_NAMES_NE.get(lord, lord),
                "period": f"{start} देखि {end}",
                "is_active": is_active,
                "role_ne": "पञ्चमेशको दशा" if lord == five_lord else ("सन्तानकारक गुरुको दशा" if lord == "Jupiter" else "शुभ शुक्रको दशा")
            })

    remedies = [
        "सन्तान गोपाल मन्त्रको नित्य १०८ पटक जप: 'ॐ क्लीं देवकीसुत गोविन्द वासुदेव जगत्पते। देहि मे तनयं कृष्ण त्वामहं शरणं गतः॥'",
        "गुरुवारको दिन भगवान् विष्णुको पूजा, पहेँलो चन्दन, चनाको दाल र लड्डु अर्पण वा दान",
        "यदि राहु/केतुको बाधा देखिएमा नागपञ्चमी वा मङ्गलबार नवनाग स्तोत्र पाठ तथा रुद्राभिषेक",
        "कुलदेवता र पितृहरूको प्रसन्नताका लागि नियमित श्राद्ध, तर्पण वा गौ-सेवा"
    ]

    return {
        "favorable_dashas": favorable_dashas[:5],
        "key_transit_trigger_ne": f"गोचरमा जब देवगुरु बृहस्पति {SIGN_NAMES_NE[five_sign]} (पञ्चम भाव) वा {PLANET_NAMES_NE.get(five_lord, five_lord)} रहेको राशिमा भ्रमण गर्दछन्, तब सन्तान योग सर्वाधिक प्रबल रूपमा सक्रिय हुन्छ।",
        "remedies": remedies
    }


# ── MAIN COMPREHENSIVE ENTRY POINT ────────────────────────────────────────────

def calculate_comprehensive_child_analysis(chart_data: dict, language: str = "ne") -> dict:
    """
    Main entry point returning structured 8-step classical Parashari Child Analysis.
    """
    if not chart_data or not isinstance(chart_data, dict):
        return {"error": "कुण्डली डाटा उपलब्ध छैन।"}

    step1 = analyze_five_core_factors(chart_data)
    step2 = analyze_fifth_house_and_aspects(chart_data)
    step3 = analyze_jupiter_karaka(chart_data)
    step4 = evaluate_putra_arishta_and_bhanga(chart_data)
    step5 = analyze_d7_saptamsha(chart_data)
    step6 = estimate_child_count(chart_data)
    step7 = evaluate_gender_tendency(chart_data)
    step8 = evaluate_conception_timing(chart_data)

    return {
        "step1_core_factors": step1,
        "step2_fifth_house_and_aspects": step2,
        "step3_jupiter_karaka": step3,
        "step4_arishta_and_bhanga": step4,
        "step5_d7_saptamsha": step5,
        "step6_child_count": step6,
        "step7_gender_tendency": step7,
        "step8_timing_and_remedies": step8,
        "overall_verdict_ne": (
            "कुण्डलीमा सन्तान सुख अत्यन्त शुभ र प्रबल छ।"
            if step4.get("code") in ("NO_OBSTACLE", "OBSTACLE_CANCELLED")
            else "कुण्डलीमा सन्तान प्राप्तिमा केही विलम्ब योग छ, जसका लागि शास्त्रीय उपाय प्रभावकारी रहनेछ।"
        )
    }
