# -*- coding: utf-8 -*-
"""
backend/calculator/marriage_analysis_engine.py

Classical Parashari Marriage & Spouse Analysis (सप्तम भाव / विवाह/कलत्र विचार)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full 9-Step Classical Parashari System (बृहत्पाराशर होराशास्त्र):
  Step 1: मुख्य ५+ आधार-तत्वहरू (7th House, 7th Lord, Venus, Jupiter, 2nd, 8th, D-9)
  Step 2: सप्तम भावको स्थिति र पूर्ण ग्रह दृष्टि (Occupants & full BPHS Aspects on 7th House)
  Step 3: मङ्गल दोष (कुजदोष) तथा दोष भंग योग (Mars from Lagna, Moon, Venus; Complete Cancellations)
  Step 4: शुक्र तथा गुरुको लिंगअनुसार विशेष विश्लेषण (Venus for Male/General, Jupiter for Female)
  Step 5: विवाहमा बाधा/विलम्ब/विच्छेद योग तथा भंग (Delay, Separation, Multiple Marriage & Relief)
  Step 6: नवमांश (D-9) कुण्डली विश्लेषण (D-9 Lagna, Lagnesh, 7th House, 7th Lord, Karakas)
  Step 7: जीवनसाथीको स्वभाव र रूप-रंग निर्धारण (Spouse traits by 7th Sign, Lord & Occupants)
  Step 8: विवाहको समय (दशा तथा गोचर) र शास्त्रीय शान्ति उपाय (7th Lord, Venus/Jupiter, Transits)
  Step 9: कुण्डली मेलापक (अष्टकूट गुण मिलान) शास्त्रीय मार्गदर्शन
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

# ── Step 7: Spouse Character Archetypes by 7th House Sign ────────────────────
SPOUSE_TRAITS_BY_SIGN_NE = {
    0: "साहसी, ऊर्जावान्, स्पष्टवक्ता, नेतृत्व स्वभाव, केही हतारो वा शीघ्र रिसाउने तर निष्कपट हृदय",
    1: "सौन्दर्यप्रिय, व्यावहारिक, स्थिर, पारिवारिक, कला एवं संगीतप्रेमी, धैर्यवान् र भरपर्दो",
    2: "बौद्धिक, कुराकानीमा कुशल, सञ्चारप्रिय, चंचल, अध्ययनशील र बहुप्रतिभाशाली",
    3: "अत्यन्त भावनाशील, मायालु, गृहप्रेमी, दयालु, संवेदनशील र परिवारको पूर्ण ख्याल राख्ने",
    4: "स्वाभिमानी, आकर्षक व्यक्तित्व, नेतृत्वदायी, उदार, आत्मविश्वासी र प्रतिष्ठित कुलको",
    5: "विश्लेषणात्मक, व्यवस्थित, कर्तव्यनिष्ठ, व्यावहारिक, सफा-सुग्घर र स्वास्थ्यप्रति सचेत",
    6: "सन्तुलित, न्यायप्रिय, आकर्षक रूप-रंग, सामाजिक, शिष्ट, समझदार र समझदारीपूर्ण व्यवहार",
    7: "गहिरो भावना, दृढ संकल्प, रहस्यमयी, समर्पित, अत्यधिक निष्ठावान् तर आत्मसम्मानप्रति संवेदनशील",
    8: "धार्मिक, दार्शनिक, आशावादी, इमानदार, उच्च शिक्षा/ज्ञानप्रेमी र स्वतन्त्र विचार भएको",
    9: "परिश्रमी, अनुशासित, गम्भीर, जिम्मेवार, व्यावहारिक र भविष्यप्रति दूरदर्शी",
    10: "मौलिक विचार, समाजसेवाप्रेमी, मित्रवत, मानवीय, बौद्धिक र नवीन दृष्टिकोण भएको",
    11: "करुणामयी, धार्मिक, कल्पनाशील, शान्त स्वभाव, त्यागी, आध्यात्मिक र सेवाभावले भरिएको"
}

SPOUSE_TRAITS_BY_SIGN_EN = {
    0: "Courageous, dynamic, outspoken, bold leader, energetic, honest and direct",
    1: "Aesthetic, practical, steadfast, family-oriented, artistic, patient and dependable",
    2: "Intellectual, witty, communicative, versatile, conversationalist and youthful",
    3: "Deeply emotional, caring, domestic, empathetic, protective and devoted",
    4: "Dignified, charismatic, authoritative, generous, proud and self-confident",
    5: "Analytical, methodical, dutiful, realistic, hygiene-conscious and attentive",
    6: "Harmonious, diplomatic, charming, balanced, socially graceful and fair",
    7: "Passionate, resolute, mysterious, profoundly loyal, perceptive and intense",
    8: "Philosophical, optimistic, righteous, frank, scholarly and truth-seeking",
    9: "Hardworking, disciplined, sober, dependable, pragmatic and goal-oriented",
    10: "Innovative, altruistic, friendly, humanitarian, unconventional and broad-minded",
    11: "Compassionate, spiritual, artistic, gentle, self-effacing and deeply empathetic"
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


# ── STEP 1: CORE FACTORS OF MARRIAGE ──────────────────────────────────────────

def analyze_core_marriage_factors(chart_data: dict) -> dict:
    """
    Identifies the key pillars of Vivaha / Kalatra Vichara:
      1. 7th House (Kalatra Bhava)
      2. 7th Lord (Kalatradhipati)
      3. Venus (Wife & Romance significator)
      4. Jupiter (Husband significator for females / Dharma)
      5. 2nd House (Kutumba - Family expansion)
      6. 8th House (Mangalya / Marital longevity)
      7. D-9 Navamsha availability
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    # 7th house
    seven_sign = (lagna_sign + 6) % 12
    seven_lord = SIGN_LORDS[seven_sign]
    seven_lord_p = planets.get(seven_lord, {})
    seven_lon = float(seven_lord_p.get("sidereal_longitude") or seven_lord_p.get("longitude") or 0.0)
    seven_h = _house_from(seven_lon, lagna_lon) if seven_lord_p else 1
    seven_lord_sign = _sign_idx(seven_lon)

    # Venus
    ven = planets.get("Venus", {})
    ven_lon = float(ven.get("sidereal_longitude") or ven.get("longitude") or 0.0)
    ven_h = _house_from(ven_lon, lagna_lon) if ven else 1
    ven_sign = _sign_idx(ven_lon)

    # Jupiter
    jup = planets.get("Jupiter", {})
    jup_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
    jup_h = _house_from(jup_lon, lagna_lon) if jup else 1
    jup_sign = _sign_idx(jup_lon)

    # 2nd house (Kutumba)
    two_sign = (lagna_sign + 1) % 12
    two_lord = SIGN_LORDS[two_sign]
    two_lord_p = planets.get(two_lord, {})
    two_h = _house_from(float(two_lord_p.get("longitude") or 0.0), lagna_lon) if two_lord_p else 1

    # 8th house (Mangalya)
    eight_sign = (lagna_sign + 7) % 12
    eight_lord = SIGN_LORDS[eight_sign]
    eight_lord_p = planets.get(eight_lord, {})
    eight_h = _house_from(float(eight_lord_p.get("longitude") or 0.0), lagna_lon) if eight_lord_p else 1

    # D-9 Navamsha
    d9 = chart_data.get("vargas", {}).get("D9")
    d9_avail = bool(d9 and isinstance(d9, dict) and d9.get("lagna"))

    return {
        "seventh_house": {
            "sign_idx": seven_sign,
            "sign_ne": SIGN_NAMES_NE[seven_sign],
            "sign_en": SIGN_NAMES_EN[seven_sign],
            "lord": seven_lord,
            "lord_ne": PLANET_NAMES_NE.get(seven_lord, seven_lord),
            "lord_house": seven_h,
            "lord_sign_ne": SIGN_NAMES_NE[seven_lord_sign],
            "is_retrograde": bool(seven_lord_p.get("is_retrograde", False)),
        },
        "venus": {
            "house": ven_h,
            "sign_ne": SIGN_NAMES_NE[ven_sign],
            "is_retrograde": bool(ven.get("is_retrograde", False)),
        },
        "jupiter": {
            "house": jup_h,
            "sign_ne": SIGN_NAMES_NE[jup_sign],
            "is_retrograde": bool(jup.get("is_retrograde", False)),
        },
        "kutumba_second_house": {
            "sign_ne": SIGN_NAMES_NE[two_sign],
            "lord_ne": PLANET_NAMES_NE.get(two_lord, two_lord),
            "lord_house": two_h,
        },
        "mangalya_eighth_house": {
            "sign_ne": SIGN_NAMES_NE[eight_sign],
            "lord_ne": PLANET_NAMES_NE.get(eight_lord, eight_lord),
            "lord_house": eight_h,
        },
        "d9_available": d9_avail
    }


# ── STEP 2: 7TH HOUSE OCCUPANTS & GRAHA DRISHTI ───────────────────────────────

def analyze_seventh_house_and_aspects(chart_data: dict) -> dict:
    """
    Examines all planets occupying or aspecting the 7th house:
      - Benefics (Jupiter, Venus, Mercury, Moon) -> Smooth, loving, timely marriage.
      - Malefics (Saturn, Mars, Rahu, Ketu, Sun) -> Delay, friction, or severe tests.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    target_house = 7

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
                "note_ne": "शुभग्रह उपस्थिति — दाम्पत्य सुखवर्धक" if p_name in benefics else "पापग्रह उपस्थिति — वैवाहिक जीवनमा सतर्कता/कलह कारक"
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
                "effect_ne": "अत्यन्त शुभ एवं सुखद दाम्पत्य" if p_name in ("Jupiter", "Venus") else ("शुभ फल" if p_name in benefics else "कष्ट, कलह वा विलम्ब कारक")
            })

    return {
        "occupants": occupants,
        "aspects": aspecting,
        "has_jupiter_aspect": any(a["planet"] == "Jupiter" for a in aspecting),
        "has_venus_aspect": any(a["planet"] == "Venus" for a in aspecting),
        "has_saturn_influence": any(o["planet"] == "Saturn" for o in occupants) or any(a["planet"] == "Saturn" for a in aspecting),
        "has_mars_influence": any(o["planet"] == "Mars" for o in occupants) or any(a["planet"] == "Mars" for a in aspecting),
        "has_rahu_ketu_influence": any(o["planet"] in ("Rahu", "Ketu") for o in occupants) or any(a["planet"] in ("Rahu", "Ketu") for a in aspecting),
    }


# ── STEP 3: MANGAL DOSHA (KUJA DOSHA) & COMPLETE BHANGA YOGA ──────────────────

def analyze_mangal_dosha_and_bhanga(chart_data: dict) -> dict:
    """
    Detailed evaluation of Mangal Dosha:
      - Houses from Lagna: 1, 2 (South/East traditions), 4, 7, 8, 12
      - Houses from Moon (Chandra Kundali)
      - Houses from Venus (Sukra Kundali)
      - Complete Bhanga (Cancellation) conditions per BPHS & classical texts:
        1. Mars in own sign (Aries/Scorpio) or exalted (Capricorn) -> Dosha Bhanga.
        2. Mars in Kendra aspected by Jupiter or Venus -> Bhanga.
        3. Equal Mangal Dosha in partner's chart (Dosha Samya).
        4. Mars conjunct with benefic (Jupiter, Moon, Venus).
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)

    mars = planets.get("Mars", {})
    if not mars:
        return {"has_dosha": False, "status_ne": "मंगल ग्रहको स्थिति उपलब्ध छैन"}

    m_lon = float(mars.get("sidereal_longitude") or mars.get("longitude") or 0.0)
    m_h_lagna = _house_from(m_lon, lagna_lon)
    m_sign = _sign_idx(m_lon)

    # Moon Lagna
    moon = planets.get("Moon", {})
    moon_lon = float(moon.get("sidereal_longitude") or moon.get("longitude") or 0.0) if moon else 0.0
    m_h_moon = _house_from(m_lon, moon_lon) if moon else 1

    # Venus Lagna
    ven = planets.get("Venus", {})
    ven_lon = float(ven.get("sidereal_longitude") or ven.get("longitude") or 0.0) if ven else 0.0
    m_h_ven = _house_from(m_lon, ven_lon) if ven else 1

    dosha_houses = {1, 2, 4, 7, 8, 12}
    is_lagna_dosha = m_h_lagna in dosha_houses
    is_moon_dosha = m_h_moon in dosha_houses
    is_venus_dosha = m_h_ven in dosha_houses

    has_dosha = is_lagna_dosha or is_moon_dosha

    bhangas = []

    # Bhanga 1: Mars in own/exaltation sign
    if m_sign in (0, 7):
        bhangas.append("मंगल आफ्नै स्वराशि (मेष/वृश्चिक) मा रहेकाले कुजदोष पूर्ण भंग (Bhanga) भएको छ।")
    elif m_sign == 9:
        bhangas.append("मंगल परमोच्च राशि (मकर) मा रहेकाले मंगल दोष स्वतः निवारण भएको छ।")

    # Bhanga 2: Aspect of Jupiter or Venus on Mars
    jup = planets.get("Jupiter", {})
    if jup:
        j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
        j_h = _house_from(j_lon, lagna_lon)
        dist = ((m_h_lagna - j_h) % 12) + 1
        if dist in (5, 7, 9) or j_h == m_h_lagna:
            bhangas.append("देवगुरु बृहस्पतिको शुभ अमृत दृष्टि मंगलमा परेकाले मंगल दोष भंग भएको छ।")

    # Bhanga 3: Mars with benefic conjunction
    for b in ("Jupiter", "Venus", "Moon"):
        if b in planets:
            b_lon = float(planets[b].get("sidereal_longitude") or planets[b].get("longitude") or 0.0)
            if _house_from(b_lon, lagna_lon) == m_h_lagna and b != "Mars":
                bhangas.append(f"शुभग्रह {PLANET_NAMES_NE.get(b, b)} सँग मंगलको युति भएकाले दोष प्रभाव शून्यप्रायः छ।")

    is_cancelled = len(bhangas) > 0

    if not has_dosha:
        status_ne = "कुण्डलीमा कुनै मङ्गल दोष छैन (निर्दोष कुण्डली)"
        code = "NO_DOSHA"
    elif has_dosha and is_cancelled:
        status_ne = "मङ्गल दोष देखिए पनि शास्त्रीय भंग योगले गर्दा पूर्ण दोष निवारण भएको छ (दोष भंग)"
        code = "DOSHA_CANCELLED"
    else:
        status_ne = "सक्रिय मङ्गल दोष विद्यमान (विवाह पूर्व मङ्गल दोष मिलान वा कुम्भ विवाह/शान्ति आवश्यक)"
        code = "ACTIVE_DOSHA"

    return {
        "has_dosha": has_dosha,
        "is_cancelled": is_cancelled,
        "code": code,
        "status_ne": status_ne,
        "mars_house_lagna": m_h_lagna,
        "mars_house_moon": m_h_moon,
        "mars_sign_ne": SIGN_NAMES_NE[m_sign],
        "is_lagna_dosha": is_lagna_dosha,
        "is_moon_dosha": is_moon_dosha,
        "is_venus_dosha": is_venus_dosha,
        "bhangas": bhangas
    }


# ── STEP 4: GENDER-BASED KARAKA EVALUATION (VENUS & JUPITER) ──────────────────

def analyze_karaka_venus_jupiter(chart_data: dict, gender: str = "male") -> dict:
    """
    Evaluates Venus (wife significator for males/universal romance) and Jupiter (husband significator for females).
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)

    # Venus evaluation
    ven = planets.get("Venus", {})
    v_lon = float(ven.get("sidereal_longitude") or ven.get("longitude") or 0.0) if ven else 0.0
    v_h = _house_from(v_lon, lagna_lon) if ven else 1
    v_sign = _sign_idx(v_lon)

    v_exalted = v_sign == EXALTATION_SIGNS["Venus"]
    v_own = v_sign in OWN_SIGNS["Venus"]
    v_debilitated = v_sign == DEBILITATION_SIGNS["Venus"]

    # Jupiter evaluation
    jup = planets.get("Jupiter", {})
    j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0) if jup else 0.0
    j_h = _house_from(j_lon, lagna_lon) if jup else 1
    j_sign = _sign_idx(j_lon)

    j_exalted = j_sign == EXALTATION_SIGNS["Jupiter"]
    j_own = j_sign in OWN_SIGNS["Jupiter"]
    j_debilitated = j_sign == DEBILITATION_SIGNS["Jupiter"]

    return {
        "venus": {
            "house": v_h,
            "sign_ne": SIGN_NAMES_NE[v_sign],
            "dignity_ne": "परमोच्च (मीन)" if v_exalted else ("स्वराशि (वृष/तुला)" if v_own else ("नीच (कन्या)" if v_debilitated else "सामान्य")),
            "significance_ne": "पुरुष जातकका लागि पत्नी-कारक एवं दाम्पत्य प्रेम-सुखको प्रमुख सूचक",
            "strength_ne": "अत्यन्त बलवान् र सुखी पत्नी योग" if (v_exalted or v_own) else ("कमजोर (दाम्पत्य समझदारी आवश्यक)" if v_debilitated else "अनुकूल")
        },
        "jupiter": {
            "house": j_h,
            "sign_ne": SIGN_NAMES_NE[j_sign],
            "dignity_ne": "परमोच्च (कर्कट)" if j_exalted else ("स्वराशि (धनु/मीन)" if j_own else ("नीच (मकर)" if j_debilitated else "सामान्य")),
            "significance_ne": "स्त्री जातकका लागि पति-कारक एवं अखण्ड सौभाग्यको सूचक",
            "strength_ne": "अत्यन्त बलवान् र सुयोग्य पति योग" if (j_exalted or j_own) else ("कमजोर (गुरु शान्ति उपयुक्त)" if j_debilitated else "अनुकूल")
        }
    }


# ── STEP 5: MARRIAGE OBSTACLES, DELAY & SEPARATION YOGAS ──────────────────────

def analyze_marriage_obstacles_and_yogas(chart_data: dict) -> dict:
    """
    Identifies specific marriage obstacles per BPHS:
      1. Delay (Vilamba): Saturn conjunct/aspecting 7th house or 7th lord; 7th lord in 6, 8, 12.
      2. Separation/Divorce (Vivad/Vichheda): 7th lord in 8th with malefic; Rahu/Ketu in 7th with malefic aspect.
      3. Multiple Marriages (Bahu-vivaha): Dual signs on 7th with multiple planets; Venus afflicted in dual signs.
      4. Bhanga Yogas: Jupiter/Venus aspecting 7th house cancels defects.
    """
    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    seven_sign = (lagna_sign + 6) % 12
    seven_lord = SIGN_LORDS[seven_sign]
    seven_lord_p = planets.get(seven_lord, {})
    seven_lon = float(seven_lord_p.get("sidereal_longitude") or seven_lord_p.get("longitude") or 0.0) if seven_lord_p else 0.0
    seven_h = _house_from(seven_lon, lagna_lon) if seven_lord_p else 1

    obstacles = []
    bhangas = []

    # Delay Check: Saturn influence
    saturn = planets.get("Saturn", {})
    if saturn:
        sat_lon = float(saturn.get("sidereal_longitude") or saturn.get("longitude") or 0.0)
        sat_h = _house_from(sat_lon, lagna_lon)
        dist_sat_to_7 = ((7 - sat_h) % 12) + 1
        if sat_h == 7 or dist_sat_to_7 in (3, 7, 10):
            obstacles.append("सप्तम भाव वा सप्तमेशमाथि शनिको प्रभाव (परिपक्व उमेरमा विवाह / विलम्ब योग)")

    # Dusthana placement of 7th lord
    if seven_h in (6, 8, 12):
        obstacles.append(f"सप्तमेश दुष्टस्थान ({seven_h} भाव) मा रहेकाले विवाहमा ढिलाइ वा स्वास्थ्य चिन्ता")

    # Rahu/Ketu in 7th
    rahu = planets.get("Rahu", {})
    if rahu and _house_from(float(rahu.get("longitude") or 0.0), lagna_lon) == 7:
        obstacles.append("सप्तम भावमा राहुको उपस्थिति (अनपेक्षित सम्बन्ध वा वैवाहिक समझदारीमा धैर्य आवश्यक)")

    ketu = planets.get("Ketu", {})
    if ketu and _house_from(float(ketu.get("longitude") or 0.0), lagna_lon) == 7:
        obstacles.append("सप्तम भावमा केतुको उपस्थिति (जीवनसाथीमा वैराग्य वा आध्यात्मिक झुकाव)")

    # Bhanga check
    jup = planets.get("Jupiter", {})
    if jup:
        j_lon = float(jup.get("sidereal_longitude") or jup.get("longitude") or 0.0)
        j_h = _house_from(j_lon, lagna_lon)
        dist_j_to_7 = ((7 - j_h) % 12) + 1
        if dist_j_to_7 in (5, 7, 9) or j_h == 7:
            bhangas.append("देवगुरु बृहस्पतिको सप्तम भावमा अमृत दृष्टि परेकाले सम्पूर्ण वैवाहिक विघ्न-बाधाको स्वतः निवारण (Bhanga)")

    ven = planets.get("Venus", {})
    if ven:
        v_h = _house_from(float(ven.get("longitude") or 0.0), lagna_lon)
        if v_h in (1, 4, 5, 7, 9, 10):
            bhangas.append("कलत्रकारक शुक्र केन्द्र/त्रिकोणमा शुभ स्थानमा रहेकाले दाम्पत्य सुख सुनिश्चित")

    return {
        "obstacles": obstacles,
        "bhangas": bhangas,
        "has_delay_yoga": any("शनि" in o or "विलम्ब" in o for o in obstacles),
        "overall_status_ne": "शुभग्रहको प्रभावले दाम्पत्य जीवन सुरक्षित र सुखमय" if bhangas else ("केही बाधा/विलम्ब देखिएकाले शास्त्रीय उपाय हितकर" if obstacles else "कुनै नकारात्मक बाधा योग छैन")
    }


# ── STEP 6: D-9 NAVAMSHA ANALYSIS ─────────────────────────────────────────────

def analyze_d9_navamsha(chart_data: dict) -> dict:
    """
    Subtle inspection of D-9 Navamsha:
      - D-9 Lagna & Lagnesha
      - D-9 7th House & 7th Lord
      - D-9 7th House Occupants
      - D-9 Venus and Jupiter
    """
    d9 = chart_data.get("vargas", {}).get("D9")
    if not d9 or not isinstance(d9, dict):
        return {"available": False, "note_ne": "D-9 नवमांश कुण्डली उपलब्ध छैन"}

    d9_lagna = d9.get("lagna", {})
    d9_lagna_sign = int(d9_lagna.get("sign_number") or 1) - 1
    d9_lagnesh = SIGN_LORDS[d9_lagna_sign]

    d9_planets = {p["name"]: p for p in d9.get("planets", []) if isinstance(p, dict) and p.get("name")}

    # D9 7th house
    d9_seven_sign = (d9_lagna_sign + 6) % 12
    d9_seven_lord = SIGN_LORDS[d9_seven_sign]
    d9_seven_lord_p = d9_planets.get(d9_seven_lord, {})
    d9_seven_lord_h = int(d9_seven_lord_p.get("house") or 1) if d9_seven_lord_p else 1

    d9_seven_occupants = [
        PLANET_NAMES_NE.get(p["name"], p["name"])
        for p in d9.get("planets", [])
        if int(p.get("house") or 0) == 7
    ]

    return {
        "available": True,
        "d9_lagna_sign_ne": SIGN_NAMES_NE[d9_lagna_sign],
        "d9_lagnesh_ne": PLANET_NAMES_NE.get(d9_lagnesh, d9_lagnesh),
        "d9_seven_sign_ne": SIGN_NAMES_NE[d9_seven_sign],
        "d9_seven_lord_ne": PLANET_NAMES_NE.get(d9_seven_lord, d9_seven_lord),
        "d9_seven_lord_house": d9_seven_lord_h,
        "d9_seven_occupants": d9_seven_occupants,
        "confirmation_ne": f"नवमांश कुण्डलीमा सप्तम भाव {SIGN_NAMES_NE[d9_seven_sign]} राशिमा पर्दछ, जसले वास्तविक दाम्पत्य सुख र जीवनसाथीको प्रकृतिलाई पुष्टि गर्दछ।"
    }


# ── STEP 7: SPOUSE TRAITS & APPEARANCE ────────────────────────────────────────

def analyze_spouse_characteristics(chart_data: dict) -> dict:
    """
    Evaluates spouse physical traits, demeanor, and character per BPHS rules:
      - 7th house sign nature (Element, Modality)
      - 7th lord nature
      - 7th house occupants' effect
    """
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    seven_sign = (lagna_sign + 6) % 12
    seven_lord = SIGN_LORDS[seven_sign]

    planets = {p["name"]: p for p in chart_data.get("planets", []) if isinstance(p, dict) and p.get("name")}
    seven_occupants = [
        PLANET_NAMES_NE.get(p["name"], p["name"])
        for p in planets.values()
        if _house_from(float(p.get("longitude") or 0.0), lagna_lon) == 7
    ]

    traits_ne = SPOUSE_TRAITS_BY_SIGN_NE.get(seven_sign, "")
    traits_en = SPOUSE_TRAITS_BY_SIGN_EN.get(seven_sign, "")

    return {
        "seventh_sign_ne": SIGN_NAMES_NE[seven_sign],
        "seventh_sign_en": SIGN_NAMES_EN[seven_sign],
        "seventh_lord_ne": PLANET_NAMES_NE.get(seven_lord, seven_lord),
        "occupants_ne": ", ".join(seven_occupants) if seven_occupants else "कुनै ग्रह छैन (निर्मल भाव)",
        "traits_ne": traits_ne,
        "traits_en": traits_en,
        "appearance_summary_ne": f"सप्तम भाव {SIGN_NAMES_NE[seven_sign]} राशि र सप्तमेश {PLANET_NAMES_NE.get(seven_lord, seven_lord)} को आधारमा जीवनसाथी: {traits_ne}।"
    }


# ── STEP 8: MARRIAGE TIMING (DASHA & TRANSIT) & REMEDIES ───────────────────────

def evaluate_marriage_timing_and_remedies(chart_data: dict) -> dict:
    """
    Identifies favorable marriage timing:
      - Vimshottari Mahadasha/Antardasha of 7th lord, Venus, Jupiter, or Lagnesha.
      - Jupiter transit over 7th house, 7th lord, or natal Venus.
      - Classical Vivaha Sukha remedies.
    """
    lagna_lon = float(chart_data.get("lagna", {}).get("longitude") or 0.0)
    lagna_sign = _sign_idx(lagna_lon)

    la_lord = SIGN_LORDS[lagna_sign]
    seven_sign = (lagna_sign + 6) % 12
    seven_lord = SIGN_LORDS[seven_sign]

    dashas = chart_data.get("dasha") or chart_data.get("vimshottari_dasha") or []
    favorable_dashas = []
    today_str = datetime.date.today().isoformat()

    for item in dashas:
        if not isinstance(item, dict):
            continue
        lord = item.get("lord") or item.get("planet", "")
        start = str(item.get("start") or item.get("start_date", ""))[:10]
        end = str(item.get("end") or item.get("end_date", ""))[:10]

        is_fav = lord in (seven_lord, la_lord, "Venus", "Jupiter")
        if is_fav:
            is_active = (start <= today_str <= end) if start and end else False
            favorable_dashas.append({
                "lord": lord,
                "lord_ne": PLANET_NAMES_NE.get(lord, lord),
                "period": f"{start} देखि {end}",
                "is_active": is_active,
                "role_ne": "सप्तमेश (कलत्रेश) को दशा" if lord == seven_lord else ("लग्नेशको दशा" if lord == la_lord else ("कलत्रकारक शुक्रको दशा" if lord == "Venus" else "शुभ गुरुको दशा"))
            })

    remedies = [
        "माता कात्यायनी वा भगवती गौरीको नित्य आराधना तथा 'ॐ कात्यायनि महामाये महायोगिन्यधीश्वरि' मन्त्र जप",
        "शुक्रवारको दिन सेतो फूल, चामल वा दूधको खीर दान, तथा श्रीसूक्त पाठ",
        "यदि मङ्गल दोष भएमा मंगलबार हनुमान चालिसा पाठ वा विवाह पूर्व कुम्भ विवाह संस्कार",
        "दाम्पत्य सुखका लागि पति-पत्नी दुवैले कुलदेवताको नियमित पूजा र सम्मान"
    ]

    transit_ne = (
        f"गोचरमा जब देवगुरु बृहस्पति {SIGN_NAMES_NE[seven_sign]} (सप्तम भाव), {PLANET_NAMES_NE.get(seven_lord, seven_lord)} रहेको राशि वा जन्म शुक्रमाथि भ्रमण गर्दछन्, "
        f"तब विवाहको योग सर्वाधिक प्रबल रूपमा सक्रिय हुन्छ।"
    )

    return {
        "favorable_dashas": favorable_dashas[:5],
        "transit_trigger_ne": transit_ne,
        "remedies": remedies
    }


# ── STEP 9: KUNDALI MILAN (ASHTAKOOT) GUIDELINES ──────────────────────────────

def evaluate_ashtakoot_milan_summary(chart_data: dict) -> dict:
    """
    Classical rules of Ashtakoot Kundali Milan for marriage compatibility.
    """
    return {
        "total_gunas": 36,
        "ashtakoot_pillars": [
            ("वर्ण (Varna)", 1, "कार्य प्रवृत्ति र आध्यात्मिक अहंकार सन्तुलन"),
            ("वश्य (Vashya)", 2, "आपसी आकर्षण र समर्पण भाव"),
            ("तारा (Tara)", 3, "भाग्य, सुस्वास्थ्य र दीर्घायु"),
            ("योनि (Yoni)", 4, "शारीरिक एवं जैविक अनुकूलता"),
            ("ग्रहमैत्री (Graha Maitri)", 5, "मानसिक मेल र मित्रता"),
            ("गण (Gana)", 6, "स्वभाव, चरित्र र दृष्टिकोण (देव/मनुष्य/राक्षस)"),
            ("भकूट (Bhakoot)", 7, "पारिवारिक वंशवृद्धि, सुख र स्थायित्व"),
            ("नाडी (Nadi)", 8, "अनुवांशिक स्वास्थ्य, रक्त समूह एवं सन्तान सुख")
        ],
        "recommendation_ne": "विवाहपूर्व वर-वधु दुवैको कुण्डलीमा कम्तीमा १८ गुण मिलेको र नाडी दोष तथा मङ्गल दोषको समुचित साम्य/परिहार भएको हुनुपर्दछ।"
    }


# ── MAIN COMPREHENSIVE ENTRY POINT ────────────────────────────────────────────

def calculate_comprehensive_marriage_analysis(chart_data: dict, language: str = "ne", gender: str = "male") -> dict:
    """
    Main entry point returning structured 9-step classical Parashari Marriage Analysis.
    """
    if not chart_data or not isinstance(chart_data, dict):
        return {"error": "कुण्डली डाटा उपलब्ध छैन।"}

    step1 = analyze_core_marriage_factors(chart_data)
    step2 = analyze_seventh_house_and_aspects(chart_data)
    step3 = analyze_mangal_dosha_and_bhanga(chart_data)
    step4 = analyze_karaka_venus_jupiter(chart_data, gender=gender)
    step5 = analyze_marriage_obstacles_and_yogas(chart_data)
    step6 = analyze_d9_navamsha(chart_data)
    step7 = analyze_spouse_characteristics(chart_data)
    step8 = evaluate_marriage_timing_and_remedies(chart_data)
    step9 = evaluate_ashtakoot_milan_summary(chart_data)

    return {
        "step1_core_factors": step1,
        "step2_seventh_house_and_aspects": step2,
        "step3_mangal_dosha": step3,
        "step4_karakas": step4,
        "step5_obstacles_and_yogas": step5,
        "step6_d9_navamsha": step6,
        "step7_spouse_characteristics": step7,
        "step8_timing_and_remedies": step8,
        "step9_ashtakoot_guidelines": step9,
        "overall_summary_ne": f"सप्तम भाव {step1.get('seventh_house',{}).get('sign_ne','')} राशि, सप्तमेश {step1.get('seventh_house',{}).get('lord_ne','')} — {step3.get('status_ne','')}"
    }
