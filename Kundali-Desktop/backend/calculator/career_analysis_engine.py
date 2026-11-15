# -*- coding: utf-8 -*-
"""
backend/calculator/career_analysis_engine.py

Classical Parashari Career & Profession Analysis (दशम भाव / व्यवसाय/जीविका निर्णय)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full 8-Step Classical Parashari System (बृहत्पाराशर होराशास्त्र):
  Step 1: मुख्य आधार-तत्वहरू (Core Factors: 10th House, 10th Lord, Lagna, D-10, 2nd, 11th, 6th)
  Step 2: दशम भावको स्थिति र पूर्ण ग्रह दृष्टि (Occupants & full BPHS Aspects on 10th House)
  Step 3: कर्माधिपति सिद्धान्त (12 Zodiac Signs classical career archetypes)
  Step 4: कर्मकारक सूर्यको विशेष विश्लेषण (Sun Dignity, House, Directional Strength & Leadership)
  Step 5: ग्रहीय पेशा-संकेत (Planetary Influences: Sun to Ketu on 10th House & 10th Lord)
  Step 6: स्वतन्त्र व्यवसाय वा नोकरी निर्णय (Independent Business vs Job/Service Determination)
  Step 7: दशांश कुण्डली (D-10 Dasamsa) सूक्ष्म विश्लेषण (D-10 Lagna, 10th House, Strongest Planet)
  Step 8: व्यवसाय परिवर्तन तथा सफलताको समय (दशा तथा गोचर) र कर्म शान्ति उपाय
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

# ── Step 3: BPHS 12 Zodiac Sign Career Archetypes ─────────────────────────────
SIGN_PROFESSIONS_NE = {
    0: "सेना, पुलिस, शल्यचिकित्सा, इन्जिनियरिङ, खेलकुद, धातु वा अग्नि सम्बन्धी उद्यम",
    1: "बैंकिङ, वित्त, कृषि, सौन्दर्य/कला, खाद्य उद्योग, विलासिता सम्बन्धी व्यापार",
    2: "सञ्चार, लेखन, पत्रकारिता, बिक्री, दलाली, सफ्टवेयर, जनसम्पर्क",
    3: "खाद्य व्यवसाय, होटल, जलजहाज/तरल पदार्थ, गृह-सम्बन्धी, नर्सिङ, समाजसेवा",
    4: "प्रशासन, राजनीति, नेतृत्व, सरकारी सेवा, व्यवस्थापन, औषधि क्षेत्र",
    5: "लेखा, चिकित्सा, अनुसन्धान, विश्लेषण, व्यापार, तथ्याङ्क व्यवस्थापन",
    6: "न्याय, कूटनीति, फेसन, साझेदारी व्यवसाय, परामर्श, कला-सौन्दर्य",
    7: "अनुसन्धान, गोप्य सेवा, शल्यचिकित्सा, बीमा, खानी, रहस्य-ज्योतिष",
    8: "शिक्षा, कानून, धर्म, अन्तर्राष्ट्रिय यात्रा, अध्यापन, दार्शनिक कार्य",
    9: "खानी, निर्माण, श्रमप्रधान उद्योग, प्रशासन, कृषि, संगठनात्मक कार्य",
    10: "प्रविधि, समाजसेवा, नवीन अनुसन्धान, विद्युतीय/वैज्ञानिक क्षेत्र, नेटवर्क",
    11: "आध्यात्म, चिकित्सा, कला, समुद्र सम्बन्धी, आयात-निर्यात, कल्याणकारी कार्य"
}

SIGN_PROFESSIONS_EN = {
    0: "Military, police, surgery, engineering, sports, defense, metal industries",
    1: "Banking, finance, agriculture, arts, food industry, luxury commerce",
    2: "Media, journalism, publishing, communication, sales, tech, public relations",
    3: "Hospitality, catering, water/liquids, real estate, nursing, healthcare",
    4: "Government administration, politics, corporate executive, medicine, leadership",
    5: "Accounting, medical diagnostics, audit, analysis, data management, trade",
    6: "Judiciary, diplomacy, fashion, partnerships, law, arbitration, design",
    7: "Investigation, research, intelligence, surgery, insurance, occult sciences",
    8: "Higher education, jurisprudence, religion, international affairs, academia",
    9: "Mining, heavy construction, industrial labor, engineering, public works",
    10: "Technology, networking, social welfare, innovation, electricity/electronics",
    11: "Spirituality, healthcare, creative arts, marine industry, international NGOs"
}

# ── Step 5: BPHS Planetary Profession Archetypes ──────────────────────────────
PLANET_PROFESSIONS_NE = {
    "Sun": "प्रशासन, सरकारी सेवा, राजनीति, नेतृत्व, चिकित्सा (विशेषतः हड्डी/आँखा), ऊर्जा तथा स्वर्ण क्षेत्र",
    "Moon": "जनसम्पर्क, खाद्य/पेय व्यवसाय, नर्सिङ, होटल, यात्रा, तरल पदार्थ सम्बन्धी व्यापार, दुग्ध व्यवसाय",
    "Mars": "सेना, पुलिस, इन्जिनियरिङ, शल्यचिकित्सा, खेलकुद, घर-जग्गा, धातु तथा अग्निमय व्यवसाय",
    "Mercury": "लेखा, वाणिज्य, लेखन, पत्रकारिता, ब्रोकिङ, गणित, प्रविधि, सञ्चार, प्रकाशन",
    "Jupiter": "शिक्षा, कानून, परामर्श, धर्म-आध्यात्म, वित्तीय सल्लाहकार, न्यायाधीश, मन्त्रालय",
    "Venus": "कला, फेसन, सौन्दर्य, मनोरञ्जन, होटल, गहना, सिनेमा, सौन्दर्य प्रसाधन, डिजाइन",
    "Saturn": "श्रमप्रधान कार्य, खानी, निर्माण, कृषि, फलाम/इस्पात, तेल, लामो समय लाग्ने अनुसन्धान",
    "Rahu": "विदेशी सम्बन्ध, प्रविधि, गैर-परम्परागत पेशा, राजनीति (आकस्मिक उन्नति), उड्डयन, आयात-निर्यात",
    "Ketu": "अनुसन्धान, आध्यात्म, गोप्य कार्य, वैकल्पिक चिकित्सा, मोक्ष-सम्बन्धी क्षेत्र, कम्प्युटर कोडिङ"
}

PLANET_PROFESSIONS_EN = {
    "Sun": "Public administration, civil service, politics, executive leadership, ophthalmology/orthopedics, energy/gold",
    "Moon": "Public relations, food/beverage, nursing, hospitality, travel, dairy, liquid commodities",
    "Mars": "Military, policing, civil/mechanical engineering, surgery, athletics, real estate, metallurgy",
    "Mercury": "Accounting, commerce, writing, journalism, stockbroking, mathematics, IT/software, telecom",
    "Jupiter": "Education, jurisprudence, corporate consulting, theology, wealth advisory, judiciary, policy",
    "Venus": "Creative arts, fashion, beauty, entertainment, luxury hospitality, jewelry, media, aesthetics",
    "Saturn": "Heavy industries, mining, construction, agriculture, iron/steel, petroleum, deep labor",
    "Rahu": "Foreign affairs, emerging tech, unconventional careers, sudden politics, aviation, import-export",
    "Ketu": "Scientific research, metaphysics, intelligence/crypto, alternative medicine, spiritual guidance"
}

EXALTATION_SIGNS = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6, "Rahu": 1, "Ketu": 7
}

DEBILITATION_SIGNS = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0, "Rahu": 7, "Ketu": 1
}

OWN_SIGNS = {
    "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
    "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10], "Rahu": [10], "Ketu": [8]
}


def _sign_idx(lon: float) -> int:
    return int(lon / 30.0) % 12


def _house_from(planet_lon: float, lagna_lon: float) -> int:
    return ((_sign_idx(planet_lon) - _sign_idx(lagna_lon)) % 12) + 1


def _arc_dist(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2) % 360.0
    return 360.0 - diff if diff > 180.0 else diff


# ── STEP 1: CORE FACTORS OF CAREER & LIVELIHOOD ───────────────────────────────

def analyze_core_career_factors(chart_data: dict) -> dict:
    """
    Identifies the key pillars of Karma / Livelihood analysis:
      1. 10th House (Sign, Lord, Occupants)
      2. Lagna & Lagnesha (Native's stamina, natural orientation)
      3. 2nd House (Dhana / Liquid Wealth accumulated from work)
      4. 11th House (Labha / Profits & Income)
      5. 6th House (Seva / Employment & Competitive Service)
      6. D-10 Dasamsa availability
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    # Lagnesha
    lagna_lord_name = SIGN_LORDS[lagna_sign]
    lagna_lord_p = planets.get(lagna_lord_name, {})
    la_lon = float(lagna_lord_p.get("sidereal_longitude") or lagna_lord_p.get("longitude") or 0.0)
    la_h = _house_from(la_lon, lagna_lon) if lagna_lord_p else 1

    # 10th house
    ten_sign = (lagna_sign + 9) % 12
    ten_lord_name = SIGN_LORDS[ten_sign]
    ten_lord_p = planets.get(ten_lord_name, {})
    ten_lon = float(ten_lord_p.get("sidereal_longitude") or ten_lord_p.get("longitude") or 0.0)
    ten_h = _house_from(ten_lon, lagna_lon) if ten_lord_p else 1
    ten_lord_sign = _sign_idx(ten_lon)

    # 2nd house (Dhana)
    two_sign = (lagna_sign + 1) % 12
    two_lord_name = SIGN_LORDS[two_sign]
    two_lord_p = planets.get(two_lord_name, {})
    two_h = _house_from(float(two_lord_p.get("longitude") or 0.0), lagna_lon) if two_lord_p else 1

    # 6th house (Service / Employment)
    six_sign = (lagna_sign + 5) % 12
    six_lord_name = SIGN_LORDS[six_sign]
    six_lord_p = planets.get(six_lord_name, {})
    six_h = _house_from(float(six_lord_p.get("longitude") or 0.0), lagna_lon) if six_lord_p else 1

    # 11th house (Labha / Gains)
    eleven_sign = (lagna_sign + 10) % 12
    eleven_lord_name = SIGN_LORDS[eleven_sign]
    eleven_lord_p = planets.get(eleven_lord_name, {})
    eleven_h = _house_from(float(eleven_lord_p.get("longitude") or 0.0), lagna_lon) if eleven_lord_p else 1

    # D-10 summary
    d10 = chart_data.get("vargas", {}).get("D10")
    d10_available = bool(d10 and isinstance(d10, dict) and d10.get("lagna"))

    return {
        "tenth_house": {
            "sign_idx": ten_sign,
            "sign_ne": SIGN_NAMES_NE[ten_sign],
            "sign_en": SIGN_NAMES_EN[ten_sign],
            "lord": ten_lord_name,
            "lord_ne": PLANET_NAMES_NE.get(ten_lord_name, ten_lord_name),
            "lord_house": ten_h,
            "lord_sign_ne": SIGN_NAMES_NE[ten_lord_sign],
            "is_retrograde": bool(ten_lord_p.get("is_retrograde", False)),
        },
        "lagna": {
            "sign_ne": SIGN_NAMES_NE[lagna_sign],
            "lord_ne": PLANET_NAMES_NE.get(lagna_lord_name, lagna_lord_name),
            "lord_house": la_h,
        },
        "wealth_and_service": {
            "second_lord_ne": PLANET_NAMES_NE.get(two_lord_name, two_lord_name),
            "second_house_sign_ne": SIGN_NAMES_NE[two_sign],
            "sixth_lord_ne": PLANET_NAMES_NE.get(six_lord_name, six_lord_name),
            "sixth_house_sign_ne": SIGN_NAMES_NE[six_sign],
            "eleventh_lord_ne": PLANET_NAMES_NE.get(eleven_lord_name, eleven_lord_name),
            "eleventh_house_sign_ne": SIGN_NAMES_NE[eleven_sign],
        },
        "d10_available": d10_available
    }


# ── STEP 2: 10TH HOUSE OCCUPANTS & GRAHA DRISHTI ──────────────────────────────

def analyze_tenth_house_and_aspects(chart_data: dict) -> dict:
    """
    Examines all planets in or aspecting the 10th house according to Parashari Graha Drishti.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    target_house = 10

    occupants = []
    aspecting = []

    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}

    for p_name, p_data in planets.items():
        lon = float(p_data.get("sidereal_longitude") or p_data.get("longitude") or 0.0)
        h = _house_from(lon, lagna_lon)

        if h == target_house:
            occupants.append({
                "planet": p_name,
                "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
                "is_benefic": p_name in benefics,
                "note_ne": "दशम भावमा अवस्थित — कार्यक्षेत्रमा प्रत्यक्ष प्रभाव"
            })

        dist = ((target_house - h) % 12) + 1
        has_aspect = False
        aspect_type = ""

        if dist == 7:
            has_aspect = True
            aspect_type = "७औँ पूर्ण दृष्टि"
        if p_name == "Mars" and dist in (4, 8):
            has_aspect = True
            aspect_type = f"{dist}औँ विशेष दृष्टि"
        elif p_name == "Jupiter" and dist in (5, 9):
            has_aspect = True
            aspect_type = f"{dist}औँ अमृत दृष्टि"
        elif p_name == "Saturn" and dist in (3, 10):
            has_aspect = True
            aspect_type = f"{dist}औँ विशेष दृष्टि"
        elif p_name in ("Rahu", "Ketu") and dist in (5, 9):
            has_aspect = True
            aspect_type = f"{dist}औँ दृष्टि"

        if has_aspect:
            aspecting.append({
                "planet": p_name,
                "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
                "from_house": h,
                "aspect_type": aspect_type,
                "is_benefic": p_name in benefics,
                "effect_ne": "शुभ एवं सम्मानित पेशा" if p_name in benefics else "कडा परिश्रम वा प्रशासनिक/चुनौतीपूर्ण कार्य"
            })

    return {
        "occupants": occupants,
        "aspects": aspecting,
        "has_sun_influence": any(o["planet"] == "Sun" for o in occupants) or any(a["planet"] == "Sun" for a in aspecting),
        "has_jupiter_influence": any(o["planet"] == "Jupiter" for o in occupants) or any(a["planet"] == "Jupiter" for a in aspecting),
        "has_saturn_influence": any(o["planet"] == "Saturn" for o in occupants) or any(a["planet"] == "Saturn" for a in aspecting),
    }


# ── STEP 3: KARMADHIPATI RASHI ARCHETYPE ──────────────────────────────────────

def analyze_karmadhipati_sign(chart_data: dict) -> dict:
    """
    Evaluates the 10th house zodiac sign archetype per classical BPHS rules.
    """
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)
    ten_sign = (lagna_sign + 9) % 12

    professions_ne = SIGN_PROFESSIONS_NE.get(ten_sign, "")
    professions_en = SIGN_PROFESSIONS_EN.get(ten_sign, "")

    return {
        "sign_idx": ten_sign,
        "sign_ne": SIGN_NAMES_NE[ten_sign],
        "sign_en": SIGN_NAMES_EN[ten_sign],
        "professions_ne": professions_ne,
        "professions_en": professions_en,
        "element_ne": ["अग्नि तत्त्व (ऊर्जा, नेतृत्व)", "पृथ्वी तत्त्व (स्थिरता, वाणिज्य)", "वायु तत्त्व (सञ्चार, विचार)", "जल तत्त्व (भावना, सेवा)"][ten_sign % 4]
    }


# ── STEP 4: SUN (KARMA-KARAKA) ANALYSIS ───────────────────────────────────────

def analyze_sun_karmakaraka(chart_data: dict) -> dict:
    """
    Evaluates the Sun as the universal significator of authority, government, and career.
    In the 10th house, the Sun enjoys Digbala (highest directional strength).
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    sun = planets.get("Sun", {})

    if not sun:
        return {"status_ne": "सूर्यको विवरण उपलब्ध छैन", "leadership_score": 50}

    s_lon = float(sun.get("sidereal_longitude") or sun.get("longitude") or 0.0)
    s_h = _house_from(s_lon, lagna_lon)
    s_sign = _sign_idx(s_lon)

    is_exalted = s_sign == EXALTATION_SIGNS["Sun"]
    is_own = s_sign in OWN_SIGNS["Sun"]
    is_debilitated = s_sign == DEBILITATION_SIGNS["Sun"]
    has_digbala = (s_h == 10)

    # Afflictions on Sun
    afflictions = []
    for m in ("Saturn", "Rahu", "Ketu"):
        if m in planets:
            m_lon = float(planets[m].get("sidereal_longitude") or planets[m].get("longitude") or 0.0)
            m_h = _house_from(m_lon, lagna_lon)
            dist = ((s_h - m_h) % 12) + 1
            if m_h == s_h:
                afflictions.append(f"{PLANET_NAMES_NE.get(m, m)} सँग युति (ग्रहण वा संघर्ष योग)")
            elif (dist == 7) or (m == "Saturn" and dist in (3, 10)):
                afflictions.append(f"{PLANET_NAMES_NE.get(m, m)} को दृष्टि")

    if is_exalted:
        dignity_ne = "परमोच्च (मेष राशि) — शीर्ष प्रशासनिक एवं राजयोग"
    elif is_own:
        dignity_ne = "स्वराशि (सिंह राशि) — पूर्ण नेतृत्व एवं आत्मबल"
    elif is_debilitated:
        dignity_ne = "नीच राशि (तुला राशि) — सत्ता/वरिष्ठसँग संघर्ष"
    else:
        dignity_ne = f"{SIGN_NAMES_NE[s_sign]} राशिमा सामान्य"

    digbala_note_ne = "सूर्य दशम भावमा दिग्बली (Digbala) भएकाले प्रशासनिक, सरकारी वा उच्च व्यावसायिक प्रतिष्ठाको प्रबल योग।" if has_digbala else ""

    return {
        "house": s_h,
        "sign_ne": SIGN_NAMES_NE[s_sign],
        "dignity_ne": dignity_ne,
        "has_digbala": has_digbala,
        "digbala_note_ne": digbala_note_ne,
        "afflictions": afflictions,
        "leadership_status_ne": (
            "अत्यन्त उच्च (प्रशासनिक तथा राजकीय नेतृत्व सम्भव)"
            if (is_exalted or is_own or has_digbala) and not afflictions
            else ("मध्यम एवं सबल" if not is_debilitated else "संघर्षपूर्ण (आत्मबल र धैर्य आवश्यक)")
        )
    }


# ── STEP 5: PLANETARY PROFESSION INFLUENCES ───────────────────────────────────

def analyze_planetary_profession_influences(chart_data: dict) -> dict:
    """
    Synthesizes planetary professions based on occupants, 10th lord, and strong aspects.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    ten_sign = (lagna_sign + 9) % 12
    ten_lord = SIGN_LORDS[ten_sign]

    influences = []

    # 1. 10th lord influence
    influences.append({
        "planet": ten_lord,
        "planet_ne": PLANET_NAMES_NE.get(ten_lord, ten_lord),
        "source": "दशमेश (10th Lord)",
        "fields_ne": PLANET_PROFESSIONS_NE.get(ten_lord, ""),
        "fields_en": PLANET_PROFESSIONS_EN.get(ten_lord, ""),
    })

    # 2. 10th house occupants
    for p_name, p_data in planets.items():
        lon = float(p_data.get("sidereal_longitude") or p_data.get("longitude") or 0.0)
        if _house_from(lon, lagna_lon) == 10 and p_name != ten_lord:
            influences.append({
                "planet": p_name,
                "planet_ne": PLANET_NAMES_NE.get(p_name, p_name),
                "source": "दशमस्थ ग्रह (Occupant)",
                "fields_ne": PLANET_PROFESSIONS_NE.get(p_name, ""),
                "fields_en": PLANET_PROFESSIONS_EN.get(p_name, ""),
            })

    return {
        "primary_lord_fields_ne": PLANET_PROFESSIONS_NE.get(ten_lord, ""),
        "all_influences": influences
    }


# ── STEP 6: BUSINESS VS SERVICE (INDEPENDENT VS EMPLOYMENT) ───────────────────

def evaluate_business_vs_service(chart_data: dict) -> dict:
    """
    Decides between independent business/entrepreneurship and service/job:
      - 6th house (Service / Employment): Strong 6th lord/house points to employment.
      - 10th lord conjunct/aspecting Lagna lord -> Independent entrepreneurship.
      - 10th lord in 6th -> Service oriented.
      - 10th lord in 7th / 10th / 1st / 11th -> Business / Self-employment favored.
      - 5-9-10 relationship (Rajayoga): High executive post or enterprise owner.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    la_lord = SIGN_LORDS[lagna_sign]
    ten_sign = (lagna_sign + 9) % 12
    ten_lord = SIGN_LORDS[ten_sign]
    six_sign = (lagna_sign + 5) % 12
    six_lord = SIGN_LORDS[six_sign]
    seven_sign = (lagna_sign + 6) % 12
    seven_lord = SIGN_LORDS[seven_sign]

    la_p = planets.get(la_lord, {})
    la_h = _house_from(float(la_p.get("longitude") or 0.0), lagna_lon) if la_p else 1

    ten_p = planets.get(ten_lord, {})
    ten_h = _house_from(float(ten_p.get("longitude") or 0.0), lagna_lon) if ten_p else 1

    business_score = 0
    service_score = 0
    reasons = []

    # 1. 10th lord connection with Lagnesha
    if la_h == ten_h or la_lord == ten_lord:
        business_score += 3
        reasons.append("दशमेश र लग्नेशको घनिष्ठ सम्बन्ध (स्वतन्त्र कार्य एवं नेतृत्व क्षमता प्रबल)")
    elif abs(la_h - ten_h) == 6:  # 7th aspect between them
        business_score += 2
        reasons.append("दशमेश र लग्नेशको परस्पर पूर्ण दृष्टि (व्यापार तथा साझेदारी अनुकूल)")

    # 2. 10th lord placement
    if ten_h in (1, 7, 10, 11):
        business_score += 2
        reasons.append(f"दशमेश शुभ स्थान ({ten_h} भाव) मा रहेकाले स्वतन्त्र व्यवसाय अनुकूल")
    elif ten_h in (6, 8, 12):
        service_score += 3
        reasons.append(f"दशमेश {ten_h} भावमा रहेकाले नोकरी, सेवा वा संस्थागत कार्य उपयुक्त")

    # 3. 6th house (Service) vs 7th house (Trade)
    six_occ = [p for p in planets.values() if _house_from(float(p.get("longitude") or 0.0), lagna_lon) == 6]
    seven_occ = [p for p in planets.values() if _house_from(float(p.get("longitude") or 0.0), lagna_lon) == 7]

    if len(six_occ) > len(seven_occ):
        service_score += 1
        reasons.append("छैटौं भाव (सेवा भाव) मा ग्रहहरूको उपस्थिति")
    elif len(seven_occ) > 0:
        business_score += 1
        reasons.append("सप्तम भाव (व्यापार भाव) मा ग्रहहरूको उपस्थिति")

    # 4. Benefic 11th house
    eleven_p = planets.get(SIGN_LORDS[(lagna_sign + 10) % 12], {})
    if eleven_p:
        el_h = _house_from(float(eleven_p.get("longitude") or 0.0), lagna_lon)
        if el_h in (1, 5, 9, 10, 11):
            business_score += 1
            reasons.append("एकादशेश (लाभेश) बलवान् भएकाले व्यावसायिक नाफाको बलियो सम्भावना")

    if business_score > service_score + 1:
        category = "स्वतन्त्र व्यवसाय / उद्यम (Business / Self-Employed)"
        code = "BUSINESS_FAVORED"
        verdict_ne = "कुण्डलीमा स्वतन्त्र व्यापार, उद्योग, वा आफ्नै नेतृत्वमा व्यवसाय गर्ने योग बढी बलवान् छ।"
    elif service_score > business_score:
        category = "नोकरी / सेवा / संस्थागत पेशा (Job / Service / Corporate)"
        code = "SERVICE_FAVORED"
        verdict_ne = "कुण्डलीमा सरकारी वा संगठित संस्थामा नोकरी, सेवा तथा परामर्शमूलक कार्य बढी सुरक्षित र सफल रहने योग छ।"
    else:
        category = "मिश्रित (पेशा र व्यवसाय दुवै अनुकूल — Hybrid / Both)"
        code = "BALANCED"
        verdict_ne = "जातकले जागिरबाट अनुभव बटुली पछि स्वतन्त्र व्यवसाय वा साइड-बिजनेस गर्दा दुवै क्षेत्रमा सफलता पाउने योग छ।"

    return {
        "code": code,
        "category_ne": category,
        "verdict_ne": verdict_ne,
        "business_score": business_score,
        "service_score": service_score,
        "reasons": reasons
    }


# ── STEP 7: D-10 DASAMSA ANALYSIS ─────────────────────────────────────────────

def analyze_d10_dasamsa(chart_data: dict) -> dict:
    """
    Subtle inspection of D-10 Dasamsa:
      - D-10 Lagna & Lagnesha
      - D-10 10th House & 10th Lord
      - Strongest planet in D-10 confirming the career field
    """
    d10 = chart_data.get("vargas", {}).get("D10")
    if not d10 or not isinstance(d10, dict):
        return {"available": False, "note_ne": "D-10 दशांश कुण्डली उपलब्ध छैन"}

    d10_lagna = d10.get("lagna", {})
    d10_lagna_sign = int(d10_lagna.get("sign_number") or 1) - 1
    d10_lagnesh = SIGN_LORDS[d10_lagna_sign]

    d10_planets = {p["name"]: p for p in d10.get("planets", []) if isinstance(p, dict) and p.get("name")}

    # D10 10th house
    d10_ten_sign = (d10_lagna_sign + 9) % 12
    d10_ten_lord = SIGN_LORDS[d10_ten_sign]
    d10_ten_lord_p = d10_planets.get(d10_ten_lord, {})
    d10_ten_lord_house = int(d10_ten_lord_p.get("house") or 1) if d10_ten_lord_p else 1

    d10_ten_occupants = [
        PLANET_NAMES_NE.get(p["name"], p["name"])
        for p in d10.get("planets", [])
        if int(p.get("house") or 0) == 10
    ]

    # Find strongest planet in D-10 in Kendra/Trikona (1, 4, 5, 7, 9, 10)
    d10_strong_planets = [
        PLANET_NAMES_NE.get(p["name"], p["name"])
        for p in d10.get("planets", [])
        if int(p.get("house") or 0) in (1, 4, 5, 7, 9, 10)
    ]

    return {
        "available": True,
        "d10_lagna_sign_ne": SIGN_NAMES_NE[d10_lagna_sign],
        "d10_lagnesh_ne": PLANET_NAMES_NE.get(d10_lagnesh, d10_lagnesh),
        "d10_tenth_sign_ne": SIGN_NAMES_NE[d10_ten_sign],
        "d10_tenth_lord_ne": PLANET_NAMES_NE.get(d10_ten_lord, d10_ten_lord),
        "d10_tenth_lord_house": d10_ten_lord_house,
        "d10_tenth_occupants": d10_ten_occupants,
        "d10_strong_planets": d10_strong_planets[:3],
        "confirmation_ne": f"दशांश कुण्डलीमा {d10_ten_occupants[0] if d10_ten_occupants else PLANET_NAMES_NE.get(d10_ten_lord, d10_ten_lord)} को प्रभावले कार्यक्षेत्रको सफलता पुष्टि गर्दछ।"
    }


# ── STEP 8: CAREER TIMING (DASHA & TRANSIT) & REMEDIES ─────────────────────────

def evaluate_career_timing_and_remedies(chart_data: dict) -> dict:
    """
    Evaluates career progression timing:
      - 10th lord, Lagnesha, Sun dasha/antardashas
      - Jupiter & Saturn transit effects
      - Classical remedies for career obstacles
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    la_lord = SIGN_LORDS[lagna_sign]
    ten_sign = (lagna_sign + 9) % 12
    ten_lord = SIGN_LORDS[ten_sign]

    dashas = chart_data.get("dasha") or chart_data.get("vimshottari_dasha") or []
    favorable_dashas = []
    today_str = datetime.date.today().isoformat()

    for item in dashas:
        if not isinstance(item, dict):
            continue
        lord = item.get("lord") or item.get("planet", "")
        start = str(item.get("start") or item.get("start_date", ""))[:10]
        end = str(item.get("end") or item.get("end_date", ""))[:10]

        is_fav = lord in (ten_lord, la_lord, "Sun", "Jupiter")
        if is_fav:
            is_active = (start <= today_str <= end) if start and end else False
            favorable_dashas.append({
                "lord": lord,
                "lord_ne": PLANET_NAMES_NE.get(lord, lord),
                "period": f"{start} देखि {end}",
                "is_active": is_active,
                "role_ne": "दशमेश (कर्मेश) को दशा" if lord == ten_lord else ("लग्नेशको दशा" if lord == la_lord else ("कर्मकारक सूर्यको दशा" if lord == "Sun" else "देवगुरुको शुभ दशा"))
            })

    remedies = [
        f"दशमेश {PLANET_NAMES_NE.get(ten_lord, ten_lord)} को नियमित मन्त्र जप तथा सम्बन्धित वारमा दान",
        "नित्य बिहान सूर्यलाई तामाको लोटाबाट जल अर्पण (अर्घ्य) र आदित्य हृदय स्तोत्र पाठ",
        "कार्यस्थलमा इमानदारी, समयपालन र कर्म-अनुशासन (यो नै सबैभन्दा ठूलो ग्रहीय शान्ति हो)",
        "यदि शनि वा राहुको बाधक दृष्टि भए शनिबार पिपलमा जल र हनुमान चालिसा पाठ"
    ]

    transit_ne = (
        f"गोचरमा जब देवगुरु बृहस्पति {SIGN_NAMES_NE[ten_sign]} (दशम भाव) वा {PLANET_NAMES_NE.get(ten_lord, ten_lord)} रहेको राशिमा भ्रमण गर्दछन्, "
        f"तब करियरमा पदोन्नति, नयाँ अवसर र ठूलो प्रतिष्ठा प्राप्त हुन्छ। शनिको गोचरले नयाँ जिम्मेवारी र कार्यको पुनर्संरचना ल्याउँछ।"
    )

    return {
        "favorable_dashas": favorable_dashas[:5],
        "transit_trigger_ne": transit_ne,
        "remedies": remedies
    }


# ── MAIN COMPREHENSIVE ENTRY POINT ────────────────────────────────────────────

def calculate_comprehensive_career_analysis(chart_data: dict, language: str = "ne") -> dict:
    """
    Main entry point returning structured 8-step classical Parashari Career & Livelihood Analysis.
    """
    if not chart_data or not isinstance(chart_data, dict):
        return {"error": "कुण्डली डाटा उपलब्ध छैन।"}

    step1 = analyze_core_career_factors(chart_data)
    step2 = analyze_tenth_house_and_aspects(chart_data)
    step3 = analyze_karmadhipati_sign(chart_data)
    step4 = analyze_sun_karmakaraka(chart_data)
    step5 = analyze_planetary_profession_influences(chart_data)
    step6 = evaluate_business_vs_service(chart_data)
    step7 = analyze_d10_dasamsa(chart_data)
    step8 = evaluate_career_timing_and_remedies(chart_data)

    return {
        "step1_core_factors": step1,
        "step2_tenth_house_and_aspects": step2,
        "step3_karmadhipati_sign": step3,
        "step4_sun_karmakaraka": step4,
        "step5_planetary_influences": step5,
        "step6_business_vs_service": step6,
        "step7_d10_dasamsa": step7,
        "step8_timing_and_remedies": step8,
        "overall_summary_ne": f"दशम भाव {step3.get('sign_ne','')} राशि र दशमेश {step1.get('tenth_house',{}).get('lord_ne','')} को आधारमा {step6.get('category_ne','')}"
    }
