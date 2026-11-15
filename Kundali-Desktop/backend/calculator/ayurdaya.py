# -*- coding: utf-8 -*-
"""
backend/calculator/ayurdaya.py

Classical Parashari Ayurdaya (Longevity) Engine — बृहत्पाराशर होराशास्त्र आयुर्दाय अध्याय
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Implements the authentic 7-step BPHS longevity determination:
  Step 1: Balarishta Yogas & Balarishta Bhanga (Infant mortality vs cancellation)
  Step 2: Method Selection Rule (Lagnesha strength/house: Pindayu, Amshayu, Nisargayu)
  Step 3: Pindayu Method (Deep exaltation arc, Shatrukshetra, Astangata,
          Chakrapata/Vyayadi, Krurodaya Haranas, Vakra Bharana, Lagna Ayus)
  Step 4: Nisargayu Method (Natural planetary years: Sun 20, Moon 1, Mars 2,
          Mercury 9, Jupiter 18, Venus 20, Saturn 50)
  Step 5: Amshayu Method (Navamsha-based elapsed degrees, Chara/Sthira/Dwiswabhava)
  Step 6: Longevity Classification (Alpayu 0-32, Madhyayu 32-70, Purnayu 70-120)
  Step 7: Vimshottari Maraka Dasha Alignment (2nd/7th lords, 8th lord, sensitive windows)
"""
from __future__ import annotations
import math
import datetime
from typing import Dict, Any, List, Optional, Tuple

# ── Classical Planetary Constants ─────────────────────────────────────────────
PINDAYU_MAX_YEARS = {
    "Sun": 19.0, "Moon": 25.0, "Mars": 15.0, "Mercury": 12.0,
    "Jupiter": 15.0, "Venus": 21.0, "Saturn": 20.0
}

NISARGAYU_MAX_YEARS = {
    "Sun": 20.0, "Moon": 1.0, "Mars": 2.0, "Mercury": 9.0,
    "Jupiter": 18.0, "Venus": 20.0, "Saturn": 50.0
}

# Deep exaltation longitudes (BPHS / Phaladeepika)
EXALTATION_DEGREES = {
    "Sun": 10.0,       # Aries 10°
    "Moon": 33.0,      # Taurus 3°
    "Mars": 298.0,     # Capricorn 28°
    "Mercury": 165.0,  # Virgo 15°
    "Jupiter": 95.0,   # Cancer 5°
    "Venus": 357.0,    # Pisces 27°
    "Saturn": 200.0,   # Libra 20°
}

DEBILITATION_DEGREES = {
    name: (deg + 180.0) % 360.0 for name, deg in EXALTATION_DEGREES.items()
}

# Natural Friends & Enemies (BPHS Naisargika Sambandha)
NATURAL_FRIENDS = {
    "Sun":     {"Moon", "Mars", "Jupiter"},
    "Moon":    {"Sun", "Mercury"},
    "Mars":    {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus":   {"Mercury", "Saturn"},
    "Saturn":  {"Mercury", "Venus"},
}

NATURAL_ENEMIES = {
    "Sun":     {"Venus", "Saturn"},
    "Moon":    set(),
    "Mars":    {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus":   {"Sun", "Moon"},
    "Saturn":  {"Sun", "Moon", "Mars"},
}

SIGN_LORDS = [
    "Mars",     # Aries (0)
    "Venus",    # Taurus (1)
    "Mercury",  # Gemini (2)
    "Moon",     # Cancer (3)
    "Sun",      # Leo (4)
    "Mercury",  # Virgo (5)
    "Venus",    # Libra (6)
    "Mars",     # Scorpio (7)
    "Jupiter",  # Sagittarius (8)
    "Saturn",   # Capricorn (9)
    "Saturn",   # Aquarius (10)
    "Jupiter",  # Pisces (11)
]

SIGN_NAMES_NE = [
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
]

SIGN_NAMES_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु", "Lagna": "लग्न"
}

# Combustion limit in degrees from Sun (BPHS)
COMBUSTION_ORB = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,  # 12° if retrograde
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0
}


# ── Helper Utilities ──────────────────────────────────────────────────────────

def _sign_idx(lon: float) -> int:
    return int(lon / 30.0) % 12

def _house_from(planet_lon: float, lagna_lon: float) -> int:
    return ((_sign_idx(planet_lon) - _sign_idx(lagna_lon)) % 12) + 1

def _is_combust(p_name: str, p_lon: float, sun_lon: float) -> bool:
    if p_name in ("Sun", "Rahu", "Ketu"):
        return False
    orb = COMBUSTION_ORB.get(p_name, 12.0)
    diff = abs((p_lon - sun_lon + 180.0) % 360.0 - 180.0)
    return diff <= orb

def _is_enemy_sign(planet: str, sign_idx: int) -> bool:
    lord = SIGN_LORDS[sign_idx]
    if lord == planet:
        return False
    return lord in NATURAL_ENEMIES.get(planet, set())

def _arc_distance(lon1: float, lon2: float) -> float:
    """Shortest distance in degrees between two longitudes."""
    diff = abs(lon1 - lon2) % 360.0
    return 360.0 - diff if diff > 180.0 else diff

def _pindayu_raw_contribution(planet: str, lon: float, max_years: float) -> float:
    """
    Classical Parashari arc formula from Deep Debilitation (Neecha) to Deep Exaltation (Uccha):
    At Uccha = max_years.
    At Neecha = max_years / 2.
    Proportionally between them: Years = (max_years / 2) * (1 + arc_from_neecha / 180.0).
    """
    neecha_deg = DEBILITATION_DEGREES[planet]
    # Arc traversed from neecha point moving forward towards uccha
    arc_from_neecha = (lon - neecha_deg) % 360.0
    if arc_from_neecha > 180.0:
        arc_from_neecha = 360.0 - arc_from_neecha  # Distance from neecha point (0 to 180)
    factor = 0.5 + 0.5 * (arc_from_neecha / 180.0)
    return max_years * factor


# ── STEP 1: BALARISHTA & BALARISHTA BHANGA ───────────────────────────────────

def check_balarishta_and_bhanga(chart_data: dict) -> dict:
    """
    Evaluates Balarishta (infant/childhood mortality indicators) and Balarishta Bhanga (cancellations).
    Returns detailed findings, status, and cancellation summary.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)
    lagnesh_name = SIGN_LORDS[lagna_sign]
    lagnesh = planets.get(lagnesh_name, {})

    moon = planets.get("Moon", {})
    sun = planets.get("Sun", {})
    moon_lon = float(moon.get("sidereal_longitude") or moon.get("longitude") or 0.0)
    sun_lon = float(sun.get("sidereal_longitude") or sun.get("longitude") or 0.0)
    moon_house = _house_from(moon_lon, lagna_lon)

    malefics = ["Saturn", "Mars", "Rahu", "Ketu"]
    benefics = ["Jupiter", "Venus"]

    arishta_reasons = []
    bhanga_reasons = []

    # 1. Moon in Dusthana (6, 8, 12)
    if moon_house in (6, 8, 12):
        # Check if aspected or conjoined with malefic
        moon_afflicted = False
        for m in malefics:
            if m in planets:
                m_lon = float(planets[m].get("sidereal_longitude") or planets[m].get("longitude") or 0.0)
                if _house_from(m_lon, lagna_lon) == moon_house or _arc_distance(moon_lon, m_lon) < 15.0:
                    moon_afflicted = True
                    break
        if moon_afflicted:
            arishta_reasons.append(f"चन्द्रमा {moon_house} भावमा पापग्रहसँग युत वा दृष्ट छ (Moon afflicted in dusthana {moon_house})")
        else:
            arishta_reasons.append(f"चन्द्रमा {moon_house} भावमा अवस्थित छ (Moon in dusthana {moon_house})")

    # 2. Malefics in Kendras (1, 4, 7, 10) and 8th without benefic aspect
    kendra_malefics = []
    for m in malefics:
        if m in planets:
            m_lon = float(planets[m].get("sidereal_longitude") or planets[m].get("longitude") or 0.0)
            h = _house_from(m_lon, lagna_lon)
            if h in (1, 4, 7, 10, 8):
                kendra_malefics.append(f"{PLANET_NAMES_NE.get(m, m)} ({h} भाव)")
    if len(kendra_malefics) >= 2:
        arishta_reasons.append(f"केन्द्र वा अष्टममा एकाधिक पापग्रह: {', '.join(kendra_malefics)}")

    # 3. Lagnesha weak/combust in Dusthana
    if lagnesh:
        l_lon = float(lagnesh.get("sidereal_longitude") or lagnesh.get("longitude") or 0.0)
        l_house = _house_from(l_lon, lagna_lon)
        if l_house in (6, 8, 12):
            arishta_reasons.append(f"लग्नेश {PLANET_NAMES_NE.get(lagnesh_name, lagnesh_name)} दुष्टस्थान ({l_house} भाव) मा कमजोर छ")
        if _is_combust(lagnesh_name, l_lon, sun_lon):
            arishta_reasons.append(f"लग्नेश {PLANET_NAMES_NE.get(lagnesh_name, lagnesh_name)} सूर्यद्वारा अस्तङ्गत छ (Lagnesha combust)")

    # ── Check Balarishta Bhanga (Cancellations) ──
    # A. Jupiter in Kendra from Lagna
    jup = planets.get("Jupiter", {})
    if jup:
        j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
        j_h = _house_from(j_lon, lagna_lon)
        if j_h in (1, 4, 7, 10):
            bhanga_reasons.append(f"बलवान देवगुरु बृहस्पति केन्द्र ({j_h} भाव) मा रहेकाले सर्वदोष निवारण (Jupiter in Kendra cancels Balarishta)")

    # B. Venus in Kendra / Trikona
    ven = planets.get("Venus", {})
    if ven:
        v_lon = float(ven.get("sidereal_longitude") or ven.get("longitude") or 0.0)
        v_h = _house_from(v_lon, lagna_lon)
        if v_h in (1, 4, 5, 9, 10) and not _is_combust("Venus", v_lon, sun_lon):
            bhanga_reasons.append(f"शुक्र बलवान भई शुभ स्थान ({v_h} भाव) मा बसेको छ (Benefic Venus well placed)")

    # C. Gajakesari Yoga (Jupiter in Kendra from Moon)
    if jup and moon:
        j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
        jm_h = ((_sign_idx(j_lon) - _sign_idx(moon_lon)) % 12) + 1
        if jm_h in (1, 4, 7, 10):
            bhanga_reasons.append(f"चन्द्र-बृहस्पति केन्द्र युति/दृष्टिले 'गजकेसरी योग' बनेको छ (Gajakesari Yoga protects life)")

    # D. Lagnesha in Kendra/Trikona exalted or own sign
    if lagnesh:
        l_lon = float(lagnesh.get("sidereal_longitude") or lagnesh.get("longitude") or 0.0)
        l_h = _house_from(l_lon, lagna_lon)
        l_sign = _sign_idx(l_lon)
        if l_h in (1, 4, 5, 7, 9, 10) and (SIGN_LORDS[l_sign] == lagnesh_name or l_sign == _sign_idx(EXALTATION_DEGREES.get(lagnesh_name, 0))):
            bhanga_reasons.append(f"लग्नेश {PLANET_NAMES_NE.get(lagnesh_name, lagnesh_name)} केन्द्र/त्रिकोणमा स्वगृह वा उच्च राशिमा बलवान छ (Lagnesha strong in Kendra/Trikona)")

    has_arishta = len(arishta_reasons) > 0
    is_cancelled = len(bhanga_reasons) > 0

    if not has_arishta:
        status_ne = "बालारिष्ट दोष छैन (शुभ)"
        status_code = "NO_ARISHTA"
    elif has_arishta and is_cancelled:
        status_ne = "बालारिष्ट दोष पूर्ण रूपले भंग भएको छ (शुभ रक्षा)"
        status_code = "ARISHTA_CANCELLED"
    else:
        status_ne = "बालारिष्ट योग विद्यमान छ — शान्ति तथा रक्षा आवश्यक"
        status_code = "ACTIVE_ARISHTA"

    return {
        "status_code": status_code,
        "status_ne": status_ne,
        "has_arishta": has_arishta,
        "is_cancelled": is_cancelled,
        "arishta_reasons": arishta_reasons,
        "bhanga_reasons": bhanga_reasons
    }


# ── STEP 2: METHOD SELECTION RULE ─────────────────────────────────────────────

def determine_primary_method(chart_data: dict) -> dict:
    """
    Classical Parashari rule based on Lagnesha's placement & dignity:
      - Kendra (1, 4, 7, 10) or Trikona (5, 9) and strong -> PINDAYU (पिण्डायु)
      - Upachaya (3, 6, 10, 11), especially 3 & 11 -> AMSHAYU (अंशायु)
      - Dusthana (6, 8, 12) or weak in enemy sign -> NISARGAYU (निसर्गायु)
      - Mixed/ambiguous -> MADHYAYU (मध्यायु / औसत तुलना)
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)
    lagnesh_name = SIGN_LORDS[lagna_sign]
    lagnesh = planets.get(lagnesh_name, {})

    if not lagnesh:
        return {
            "method": "Pindayu",
            "method_ne": "पिण्डायु विधि",
            "reason_ne": "सामान्य स्थिति अनुसार पिण्डायु विधि उपयुक्त छ।"
        }

    l_lon = float(lagnesh.get("sidereal_longitude") or lagnesh.get("longitude") or 0.0)
    h = _house_from(l_lon, lagna_lon)
    s_idx = _sign_idx(l_lon)
    is_own = SIGN_LORDS[s_idx] == lagnesh_name
    is_exalted = s_idx == _sign_idx(EXALTATION_DEGREES.get(lagnesh_name, 0))
    is_debilitated = s_idx == _sign_idx(DEBILITATION_DEGREES.get(lagnesh_name, 0))
    is_enemy = _is_enemy_sign(lagnesh_name, s_idx)

    p_ne = PLANET_NAMES_NE.get(lagnesh_name, lagnesh_name)

    if h in (1, 4, 5, 7, 9, 10) and (is_own or is_exalted or not is_enemy):
        return {
            "method": "Pindayu",
            "method_ne": "पिण्डायु विधि (Pindayu)",
            "reason_ne": f"लग्नेश {p_ne} केन्द्र वा त्रिकोण ({h} भाव) मा बलवान रहेकाले पाराशर नियम अनुसार 'पिण्डायु' मुख्य विधि हो।"
        }
    elif h in (3, 11) or (h in (6, 10) and not is_debilitated):
        return {
            "method": "Amshayu",
            "method_ne": "अंशायु विधि (Amshayu)",
            "reason_ne": f"लग्नेश {p_ne} उपचय भाव ({h} भाव) मा रहेकाले शास्त्र अनुसार 'अंशायु' मुख्य विधि हो।"
        }
    elif h in (6, 8, 12) or is_debilitated:
        return {
            "method": "Nisargayu",
            "method_ne": "निसर्गायु विधि (Nisargayu)",
            "reason_ne": f"लग्नेश {p_ne} दुष्टस्थान वा निर्बल अवस्थामा रहेकाले शास्त्र अनुसार 'निसर्गायु' मुख्य विधि हो।"
        }
    else:
        return {
            "method": "Comparative",
            "method_ne": "मध्यायु / तीनवटै विधिको तुलना (Comparative)",
            "reason_ne": f"लग्नेश {p_ne} को मिश्रित स्थिति भएकाले तीनवटै विधि (पिण्डायु, अंशायु, निसर्गायु) को तुलनात्मक अध्ययन उचित हुन्छ।"
        }


# ── STEP 3: PINDAYU CALCULATION WITH HARANAS & LAGNA AYUS ─────────────────────

def calculate_pindayu(chart_data: dict) -> dict:
    """
    Full Parashara Pindayu computation:
      - Raw years from Deep Exaltation - Debilitation Arc
      - Vakra Bharana (Triple if retrograde)
      - Shatrukshetra Harana (1/3 deduction if in enemy sign, unless retrograde)
      - Astangata Harana (1/2 deduction if combust, exempt for Venus and Saturn)
      - Chakrapata / Vyayadi Harana (12th to 7th houses reduction)
      - Krurodaya Harana (Malefic rising in Lagna)
      - Lagna Ayurdaya (Years from Lagna degrees)
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    sun = planets.get("Sun", {})
    sun_lon = float(sun.get("sidereal_longitude") or sun.get("longitude") or 0.0)

    planet_results = []
    total_planet_years = 0.0

    # 1. Calculate each planet's years
    for p_name, max_yrs in PINDAYU_MAX_YEARS.items():
        p_data = planets.get(p_name, {})
        if not p_data:
            continue
        lon = float(p_data.get("sidereal_longitude") or p_data.get("longitude") or 0.0)
        is_retro = bool(p_data.get("is_retrograde", False))
        h = _house_from(lon, lagna_lon)
        s_idx = _sign_idx(lon)

        # Raw arc years
        raw_yrs = _pindayu_raw_contribution(p_name, lon, max_yrs)
        curr_yrs = raw_yrs

        # Vakra Bharana (Retrograde triples years, capped at max_years * 3)
        vakra_added = 0.0
        if is_retro and p_name not in ("Sun", "Moon"):
            vakra_added = curr_yrs * 2.0  # Triples total: curr_yrs + 2*curr_yrs = 3*curr_yrs
            curr_yrs += vakra_added

        # Harana 1: Shatrukshetra (1/3 deduction if in enemy sign, unless retrograde)
        shatru_ded = 0.0
        if _is_enemy_sign(p_name, s_idx) and not is_retro:
            shatru_ded = curr_yrs * (1.0 / 3.0)
            curr_yrs -= shatru_ded

        # Harana 2: Astangata (1/2 deduction if combust, exempt for Venus and Saturn)
        astangata_ded = 0.0
        if p_name not in ("Venus", "Saturn") and _is_combust(p_name, lon, sun_lon):
            astangata_ded = curr_yrs * 0.5
            curr_yrs -= astangata_ded

        # Harana 3: Chakrapata / Vyayadi Harana (Planets in houses 12, 11, 10, 9, 8, 7)
        # Benefic fractions: 12th: 1/2, 11th: 1/4, 10th: 1/6, 9th: 1/8, 8th: 1/10, 7th: 1/12
        # Malefic fractions: 12th: 1, 11th: 1/2, 10th: 1/3, 9th: 1/4, 8th: 1/5, 7th: 1/6
        is_malefic = p_name in ("Sun", "Mars", "Saturn")
        chakrapata_fraction = 0.0
        if h == 12:
            chakrapata_fraction = 1.0 if is_malefic else 0.5
        elif h == 11:
            chakrapata_fraction = 0.5 if is_malefic else 0.25
        elif h == 10:
            chakrapata_fraction = (1.0 / 3.0) if is_malefic else (1.0 / 6.0)
        elif h == 9:
            chakrapata_fraction = 0.25 if is_malefic else 0.125
        elif h == 8:
            chakrapata_fraction = 0.2 if is_malefic else 0.1
        elif h == 7:
            chakrapata_fraction = (1.0 / 6.0) if is_malefic else (1.0 / 12.0)

        chakrapata_ded = curr_yrs * chakrapata_fraction
        curr_yrs -= chakrapata_ded

        final_planet_yrs = max(0.1, curr_yrs)
        total_planet_years += final_planet_yrs

        planet_results.append({
            "planet": p_name,
            "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
            "sign": SIGN_NAMES_NE[s_idx],
            "house": h,
            "raw_years": round(raw_yrs, 2),
            "vakra_added": round(vakra_added, 2),
            "shatru_ded": round(shatru_ded, 2),
            "astangata_ded": round(astangata_ded, 2),
            "chakrapata_ded": round(chakrapata_ded, 2),
            "final_years": round(final_planet_yrs, 2)
        })

    # 2. Krurodaya Harana (Malefic in Lagna deducts proportion of rising sign)
    krurodaya_ded = 0.0
    lagna_deg_in_sign = lagna_lon % 30.0
    lagna_fraction = lagna_deg_in_sign / 30.0
    lagna_malefics = [p for p in ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
                      if p in planets and _house_from(float(planets[p].get("longitude") or 0.0), lagna_lon) == 1]
    if lagna_malefics:
        # Deduct proportion of total planetary years
        krurodaya_ded = total_planet_years * (lagna_fraction * 0.25)
        total_planet_years = max(10.0, total_planet_years - krurodaya_ded)

    # 3. Lagna Ayurdaya (Lagna itself contributes years based on Navamshas traversed)
    # BPHS: Each Navamsha (3°20') gives 1 year, or Lagna Sign + Degrees gives up to 12 years (1 yr per sign).
    lagna_years = (lagna_lon % 30.0) / 30.0 * 1.0 + (_sign_idx(lagna_lon)) * 1.0  # Up to 12 years
    lagna_years = round(min(lagna_years, 12.0), 2)

    total_pindayu = min(120.0, total_planet_years + lagna_years)

    return {
        "total_years": round(total_pindayu, 2),
        "planet_years": round(total_planet_years, 2),
        "lagna_years": lagna_years,
        "krurodaya_ded": round(krurodaya_ded, 2),
        "breakdown": planet_results
    }


# ── STEP 4: NISARGAYU CALCULATION ─────────────────────────────────────────────

def calculate_nisargayu(chart_data: dict) -> dict:
    """
    Classical Parashari Nisargayu:
      Base natural years: Sun: 20, Moon: 1, Mars: 2, Mercury: 9, Jupiter: 18, Venus: 20, Saturn: 50.
      Each planet's years are adjusted by its Uccha/Neecha arc and Haranas (similar to Pindayu).
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    sun = planets.get("Sun", {})
    sun_lon = float(sun.get("sidereal_longitude") or sun.get("longitude") or 0.0)

    breakdown = []
    total_planet_years = 0.0

    for p_name, base_yrs in NISARGAYU_MAX_YEARS.items():
        p_data = planets.get(p_name, {})
        if not p_data:
            continue
        lon = float(p_data.get("sidereal_longitude") or p_data.get("longitude") or 0.0)
        h = _house_from(lon, lagna_lon)
        s_idx = _sign_idx(lon)

        raw = _pindayu_raw_contribution(p_name, lon, base_yrs)
        curr = raw

        # Combustion check
        if p_name not in ("Venus", "Saturn") and _is_combust(p_name, lon, sun_lon):
            curr *= 0.5

        # Shatrukshetra check
        if _is_enemy_sign(p_name, s_idx):
            curr *= (2.0 / 3.0)

        final_yrs = max(0.05, curr)
        total_planet_years += final_yrs
        breakdown.append({
            "planet": p_name,
            "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
            "base_years": base_yrs,
            "final_years": round(final_yrs, 2)
        })

    lagna_years = round(((lagna_lon % 30.0) / 30.0 * 1.0) + (_sign_idx(lagna_lon) * 1.0), 2)
    total_nisargayu = min(120.0, total_planet_years + lagna_years)

    return {
        "total_years": round(total_nisargayu, 2),
        "planet_years": round(total_planet_years, 2),
        "lagna_years": lagna_years,
        "breakdown": breakdown
    }


# ── STEP 5: AMSHAYU CALCULATION ───────────────────────────────────────────────

def calculate_amshayu(chart_data: dict) -> dict:
    """
    Classical Parashari Amshayu (Navamsha-based):
      Each planet contributes years equal to the number of Navamshas traversed.
      Total Navamshas in zodiac = 108.
      Each Navamsha traversed from Aries (or sign) gives 1 year + fractional months/days.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    sun = planets.get("Sun", {})
    sun_lon = float(sun.get("sidereal_longitude") or sun.get("longitude") or 0.0)

    breakdown = []
    total_years = 0.0

    # 7 classical planets
    for p_name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        p_data = planets.get(p_name, {})
        if not p_data:
            continue
        lon = float(p_data.get("sidereal_longitude") or p_data.get("longitude") or 0.0)
        s_idx = _sign_idx(lon)
        h = _house_from(lon, lagna_lon)

        # Navamshas traversed in sign = (lon % 30) / (30/9) -> 0 to 9
        # Navamsha index 0 to 8 gives base years
        nav_arc = (lon % 30.0) / (30.0 / 9.0)
        base_nav_years = nav_arc

        # If exalted, multiplied by 3; if in own navamsha, doubled
        curr = base_nav_years
        if _arc_distance(lon, EXALTATION_DEGREES.get(p_name, 0.0)) < 15.0:
            curr *= 3.0

        # Astangata reduction
        if p_name not in ("Venus", "Saturn") and _is_combust(p_name, lon, sun_lon):
            curr *= 0.5

        final_yrs = max(0.1, curr)
        total_years += final_yrs

        breakdown.append({
            "planet": p_name,
            "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
            "nav_years": round(final_yrs, 2)
        })

    # Lagna Navamshas
    lagna_nav_yrs = round((lagna_lon % 30.0) / (30.0 / 9.0), 2)
    total_amshayu = min(120.0, total_years + lagna_nav_yrs)

    return {
        "total_years": round(total_amshayu, 2),
        "planet_years": round(total_years, 2),
        "lagna_years": lagna_nav_yrs,
        "breakdown": breakdown
    }


# ── STEP 6: LONGEVITY CATEGORIZATION ──────────────────────────────────────────

def classify_longevity(estimated_years: float) -> dict:
    """
    Classifies lifespan into classical BPHS categories:
      अल्पायु (Alpayu): 0 – 32 years
      मध्यायु (Madhyayu): 32 – 70 years
      पूर्णायु (Purnayu): 70 – 120 years
    """
    if estimated_years <= 32.0:
        cat_ne = "अल्पायु (Alpayu — ० देखि ३२ वर्ष)"
        cat_code = "ALPAYU"
        desc_ne = "जातकको आयु ३२ वर्षभित्र अल्पायु श्रेणीमा पर्छ। आयु रक्षाका लागि महामृत्युञ्जय जप, रुद्राभिषेक तथा ग्रहशान्ति उपाय शास्त्रीय रूपमा अनिवार्य मानिन्छ।"
    elif estimated_years <= 70.0:
        cat_ne = "मध्यायु (Madhyayu — ३२ देखि ७० वर्ष)"
        cat_code = "MADHYAYU"
        desc_ne = "जातकको आयु ३२ देखि ७० वर्षको मध्यायु श्रेणीमा पर्छ। सामान्य स्वस्थ जीवन तथा मध्यकालमा मारक दशाको प्रभावमा सावधानी आवश्यक हुन्छ।"
    else:
        cat_ne = "पूर्णायु / दीर्घायु (Purnayu — ७० देखि १२० वर्ष)"
        cat_code = "PURNAYU"
        desc_ne = "जातकको आयु ७० वर्षभन्दा माथि पूर्णायु श्रेणीमा पर्छ। कुण्डलीमा लग्नेश र अष्टमेशको शुभ प्रभावले दीर्घ जीवनको शास्त्रीय संकेत गर्दछ।"

    return {
        "code": cat_code,
        "category_ne": cat_ne,
        "description_ne": desc_ne
    }


# ── STEP 7: MARAKA DASHA & SENSITIVE PERIODS ──────────────────────────────────

def evaluate_maraka_periods(chart_data: dict, estimated_years: float) -> dict:
    """
    Cross-checks the calculated longevity against Vimshottari Dasha:
      - Identifies 2nd and 7th lords (Marakeshas - मारकेश)
      - Identifies planets in 2nd and 7th houses
      - Identifies 8th and 12th lords
      - Finds Dasha periods occurring around the estimated lifespan window
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    # 2nd and 7th lords (Marakeshas)
    second_sign = (lagna_sign + 1) % 12
    seventh_sign = (lagna_sign + 6) % 12
    eighth_sign = (lagna_sign + 7) % 12
    twelfth_sign = (lagna_sign + 11) % 12

    maraka_lord_2 = SIGN_LORDS[second_sign]
    maraka_lord_7 = SIGN_LORDS[seventh_sign]
    lord_8 = SIGN_LORDS[eighth_sign]
    lord_12 = SIGN_LORDS[twelfth_sign]

    # Planets in 2nd and 7th
    planets_in_2 = []
    planets_in_7 = []
    planets_in_8 = []
    for p_name, p_data in planets.items():
        if p_name in ("Rahu", "Ketu"):
            continue
        lon = float(p_data.get("sidereal_longitude") or p_data.get("longitude") or 0.0)
        h = _house_from(lon, lagna_lon)
        if h == 2:
            planets_in_2.append(PLANET_NAMES_NE.get(p_name, p_name))
        elif h == 7:
            planets_in_7.append(PLANET_NAMES_NE.get(p_name, p_name))
        elif h == 8:
            planets_in_8.append(PLANET_NAMES_NE.get(p_name, p_name))

    maraka_summary = {
        "maraka_lord_2": PLANET_NAMES_NE.get(maraka_lord_2, maraka_lord_2),
        "maraka_lord_7": PLANET_NAMES_NE.get(maraka_lord_7, maraka_lord_7),
        "lord_8": PLANET_NAMES_NE.get(lord_8, lord_8),
        "lord_12": PLANET_NAMES_NE.get(lord_12, lord_12),
        "planets_in_2": planets_in_2,
        "planets_in_7": planets_in_7,
        "planets_in_8": planets_in_8,
    }

    # Match with Dasha timeline
    dob_str = str((chart_data.get("metadata") or {}).get("birth_date") or "")
    dob_year = int(dob_str[:4]) if dob_str[:4].isdigit() else None

    # Without a real birth year the maraka window cannot be located on the
    # timeline.  Report an explicit unavailable state instead of assuming a 1990
    # birth and printing a confident-looking year range for a wrong chart.
    if dob_year is None:
        target_cal_year = None
        target_window = (0, -1)          # empty window: no dasha can overlap
    else:
        target_cal_year = dob_year + int(round(estimated_years))
        target_window = (target_cal_year - 4, target_cal_year + 4)

    sensitive_dashas = []
    dashas = chart_data.get("dasha") or chart_data.get("vimshottari_dasha") or []
    for item in dashas:
        if not isinstance(item, dict):
            continue
        lord = item.get("lord") or item.get("planet", "")
        start_yr = int(str(item.get("start") or item.get("start_date", "1900"))[:4])
        end_yr = int(str(item.get("end") or item.get("end_date", "2100"))[:4])

        # If period overlaps the target window
        if not (end_yr < target_window[0] or start_yr > target_window[1]):
            is_marak = lord in (maraka_lord_2, maraka_lord_7, lord_8, lord_12)
            sensitive_dashas.append({
                "lord": lord,
                "lord_ne": PLANET_NAMES_NE.get(lord, item.get("lord_nepali", lord)),
                "period": f"{start_yr} – {end_yr}",
                "is_maraka": is_marak,
                "note_ne": "मारक दशाधिपति" if is_marak else "सामान्य दशा"
            })

    return {
        "maraka_info": maraka_summary,
        "target_calendar_year": target_cal_year,
        "target_window_available": target_cal_year is not None,
        "target_window_ne": (
            f"ई.सं. {target_window[0]} – {target_window[1]}"
            if target_cal_year is not None
            else "जन्म मिति उपलब्ध नभएकाले मारक वर्ष उपलब्ध छैन"
        ),
        "sensitive_dashas": sensitive_dashas,
        "remedies_ne": [
            "महामृत्युञ्जय मन्त्रको नित्य वा सवालाख जप र हवन",
            "भगवान् शिवको रुद्राभिषेक तथा जलार्पण",
            "मारक ग्रहको प्रिय वस्तु (कालो तिल, फलाम, वस्त्र) शनिवार वा मङ्गलवार दान",
            "आयुर्वृद्धि हेतु मङ्गलमय गौ-सेवा वा दीन-दुःखीलाई भोजन दान"
        ]
    }


# ── MAIN COMPREHENSIVE ENTRY POINT ────────────────────────────────────────────

def calculate_comprehensive_ayurdaya(chart_data: dict, language: str = "ne") -> dict:
    """
    Main controller for 7-step classical Parashari Ayurdaya reading.
    Returns complete structured data for UI rendering.
    """
    if not chart_data or not isinstance(chart_data, dict):
        return {"error": "कुण्डली डाटा उपलब्ध छैन।"}

    # 1. Balarishta check
    balarishta = check_balarishta_and_bhanga(chart_data)

    # 2. Method selection
    method_decision = determine_primary_method(chart_data)

    # 3. Pindayu
    pindayu = calculate_pindayu(chart_data)

    # 4. Nisargayu
    nisargayu = calculate_nisargayu(chart_data)

    # 5. Amshayu
    amshayu = calculate_amshayu(chart_data)

    # Primary method estimate vs Average
    prim_name = method_decision.get("method")
    if prim_name == "Pindayu":
        primary_val = pindayu["total_years"]
    elif prim_name == "Amshayu":
        primary_val = amshayu["total_years"]
    elif prim_name == "Nisargayu":
        primary_val = nisargayu["total_years"]
    else:
        primary_val = round((pindayu["total_years"] + amshayu["total_years"] + nisargayu["total_years"]) / 3.0, 1)

    avg_val = round((pindayu["total_years"] + amshayu["total_years"] + nisargayu["total_years"]) / 3.0, 1)
    min_val = min(pindayu["total_years"], amshayu["total_years"], nisargayu["total_years"])
    max_val = max(pindayu["total_years"], amshayu["total_years"], nisargayu["total_years"])

    # If Balarishta is active and not cancelled, classical rule sets lifespan under 8-12
    if balarishta.get("has_arishta") and not balarishta.get("is_cancelled"):
        effective_estimate = min(12.0, primary_val)
    else:
        effective_estimate = primary_val

    # 6. Longevity category
    classification = classify_longevity(effective_estimate)

    # 7. Maraka Dasha alignment
    maraka_eval = evaluate_maraka_periods(chart_data, effective_estimate)

    return {
        "step1_balarishta": balarishta,
        "step2_method_selection": method_decision,
        "step3_pindayu": pindayu,
        "step4_nisargayu": nisargayu,
        "step5_amshayu": amshayu,
        "step6_classification": classification,
        "step7_maraka_dasha": maraka_eval,
        "summary": {
            "primary_method": prim_name,
            "primary_method_ne": method_decision.get("method_ne"),
            "primary_years": round(effective_estimate, 1),
            "average_years": avg_val,
            "range_min": round(min_val, 1),
            "range_max": round(max_val, 1),
        },
        "disclaimer_ne": "शास्त्रीय उद्घोष: ज्योतिष शास्त्रमा आयुको गणना सम्भाव्य कर्मफल र दशा प्रभाव जान्न तथा महामृत्युञ्जय जप, शान्ति र आयुर्वृद्धि उपाय गर्नका लागि मात्र गरिन्छ। जीवन र मृत्युको पूर्ण रहस्य केवल ईश्वराधीन छ।"
    }
