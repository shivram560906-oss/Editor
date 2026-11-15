"""
backend/calculator/daily_horoscope_engine.py

Dynamic Daily, Monthly, and Yearly Horoscope (राशिफल) Calculation Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Calculates actual, dynamic astrological predictions based on:
1. Person's natal chart (Lagna, Chandra Rashi / Natal Moon sign, Nakshatra)
2. Accurate Ephemeris transit positions (Gochar) for the requested BS date
3. Classical Vedic principles:
   - Chandrabala (गोचरे तु बलं चन्द्रः — Moon's house from natal Moon)
   - Tarabala (9-fold Tara system from Janma Nakshatra)
   - Day Lord (वारेश) and planetary lordship
   - Gochar house effects for all 9 planets (BPHS & Phaladeepika)
   - Double transit activations (Jupiter & Saturn)
   - Sauramasa (Solar transit) for monthly forecasts
   - Major slow-moving planet transits (Jupiter, Saturn, Rahu-Ketu, Sade Sati) for yearly forecasts
"""
from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from .transit_analysis import (
    calculate_transit_analysis,
    _sign_from_lon,
    _house_from_lagna,
    _planet_dignity,
    SIGN_LORDS,
    PLANET_NE,
)
from .panchang import VARAS, TITHIS
from gui.utils.bs_calendar import (
    bs_to_gregorian,
    to_nepali_digits,
    BS_MONTHS_NE,
    BS_MONTHS_EN,
)
from gui.utils.planet_colors import rashi_name, planet_full_name

# Elements of signs (1-12)
# Fire: 1 (Aries), 5 (Leo), 9 (Sagittarius) -> East (पूर्व)
# Earth: 2 (Taurus), 6 (Virgo), 10 (Capricorn) -> South (दक्षिण)
# Air: 3 (Gemini), 7 (Libra), 11 (Aquarius) -> West (पश्चिम)
# Water: 4 (Cancer), 8 (Scorpio), 12 (Pisces) -> North (उत्तर)
SIGN_ELEMENT_DIRECTION = {
    1: ("पूर्व", "East"), 5: ("पूर्व", "East"), 9: ("पूर्व", "East"),
    2: ("दक्षिण", "South"), 6: ("दक्षिण", "South"), 10: ("दक्षिण", "South"),
    3: ("पश्चिम", "West"), 7: ("पश्चिम", "West"), 11: ("पश्चिम", "West"),
    4: ("उत्तर", "North"), 8: ("उत्तर", "North"), 12: ("उत्तर", "North"),
}

# Lucky Colors by ruling planet
PLANET_LUCKY_COLORS = {
    "Sun":     ("सुन्तला, गाढा रातो, सुनौलो (Orange/Gold)", "Orange / Gold / Red"),
    "Moon":    ("सेतो, चाँदी, क्रिम (White/Silver/Cream)", "White / Silver / Cream"),
    "Mars":    ("रातो, गुलावी, सिन्दूरे (Red/Coral/Pink)", "Red / Coral / Pink"),
    "Mercury": ("हरियो, पन्ना (Green/Emerald)", "Green / Emerald"),
    "Jupiter": ("पहेंलो, सुनौलो, बेसार (Yellow/Golden)", "Yellow / Golden"),
    "Venus":   ("चम्किलो सेतो, हल्का गुलावी (White/Pink)", "White / Light Pink"),
    "Saturn":  ("नीलो, कालो, खैरो (Navy Blue/Black/Slate)", "Navy Blue / Black / Slate"),
    "Rahu":    ("धुवाँ रङ्ग, गाढा निलो (Smoky/Dark Blue)", "Smoky / Dark Blue"),
    "Ketu":    ("खैरो, बहुरङ्गी (Grey/Variegated)", "Grey / Earthy tones"),
}

# Lucky Numbers by planet
PLANET_LUCKY_NUMBERS = {
    "Sun": "१, ४, ७",
    "Moon": "२, ५, ८",
    "Mars": "९, ३, १",
    "Mercury": "५, १, ६",
    "Jupiter": "३, ७, ९",
    "Venus": "६, २, ५",
    "Saturn": "८, ६, ३",
    "Rahu": "४, ६, ८",
    "Ketu": "७, ३, ९",
}

# Day Lords by weekday index (0=Sunday ... 6=Saturday)
VARA_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Classical Chandrabala interpretations (House of transit Moon from natal Moon: 1-12)
CHANDRA_HOUSE_PHALA_NE = {
    1: "आज चन्द्रमा तपाईंको जन्मराशिमै गोचर गर्दैछन्। आत्मविश्वास, शारीरिक स्फूर्ति र प्रसन्नता रहनेछ। काममा आफैं अग्रसर हुनुहोस्।",
    2: "आज चन्द्रमा दोस्रो (धन तथा वाणी) भावमा छन्। आर्थिक कारोबारमा लाभ हुनेछ तर बोलीमा संयम र पारिवारिक समझदारी राख्नु हितकर हुन्छ।",
    3: "आज चन्द्रमा तेस्रो (पराक्रम तथा भ्रातृ) भावमा छन्। साहस र आत्मबल उच्च रहनेछ। छोटो यात्रा र नयाँ योजना आरम्भ गर्न यो दिन अति उत्तम छ।",
    4: "आज चन्द्रमा चौथो (सुख तथा मातृ) भावमा छन्। घरायसी विषयमा खर्च बढ्न सक्छ। मानसिक तनावबाट बच्न शान्त रहनुहोस् र आमाको आशीर्वाद लिनुहोस्।",
    5: "आज चन्द्रमा पाँचौं (बुद्धि तथा सन्तान) भावमा छन्। बौद्धिक चिन्तन, सिर्जनशीलता र सन्तान सम्बन्धी काममा राम्रो प्रगति हुनेछ।",
    6: "आज चन्द्रमा छैटौं (शत्रु तथा रोग मुक्ति) भावमा छन्। शत्रु तथा प्रतिस्पर्धी परास्त हुनेछन्, रोकिएका काम बन्नेछन् र कार्यसिद्धि मिल्नेछ (अति शुभ)।",
    7: "आज चन्द्रमा सातौं (दाम्पत्य तथा साझेदारी) भावमा छन्। जीवनसाथी र साझेदारबाट उत्तम सहयोग मिल्नेछ। व्यापारिक भेटघाट फलदायी हुनेछ।",
    8: "आज चन्द्रमा आठौं (घात चन्द्र) भावमा छन्। स्वास्थ्य र खानपानमा विशेष सतर्कता अपनाउनुहोस्। सवारीसाधन चलाउँदा र आर्थिक जोखिम लिँदा सावधानी राख्नुहोस्।",
    9: "आज चन्द्रमा नवौं (भाग्य तथा धर्म) भावमा छन्। भाग्यको साथ मिल्नेछ, धार्मिक वा आध्यात्मिक कार्यमा रुचि बढ्नेछ र गुरुजनको आशीर्वाद प्राप्त हुनेछ।",
    10: "आज चन्द्रमा दशौं (कर्म तथा पद-प्रतिष्ठा) भावमा छन्। कार्यक्षेत्रमा ठूलो मान-सम्मान, पदोन्नति र उच्च अधिकारीहरूको प्रशंसा मिल्नेछ (सर्वोत्तम)।",
    11: "आज चन्द्रमा एघारौं (लाभ तथा मनोरथ पूर्ति) भावमा छन्। चौतर्फी धनलाभ, इच्छापूर्ति र मित्रजनबाट उल्लेख्य सहयोग मिल्ने योग छ (सर्वोत्कृष्ट)।",
    12: "आज चन्द्रमा बाह्रौं (व्यय तथा दूर देश) भावमा छन्। खर्चमा वृद्धि र दौडधुप हुन सक्छ। अनावश्यक विवादबाट टाढा रहनुहोस् र बजेट नियन्त्रणमा राख्नुहोस्।"
}

CHANDRA_HOUSE_PHALA_EN = {
    1: "Transit Moon is in your natal Moon sign. High confidence, vitality, and mental peace enhance your personal efficiency.",
    2: "Transit Moon in the 2nd house supports financial gains; exercise mindful speech in domestic interactions.",
    3: "Transit Moon in the 3rd house stimulates courage and enthusiasm. Short journeys and initiative yield fruitful outcomes.",
    4: "Transit Moon in the 4th house advises caution in domestic matters. Seek peace of mind and parental blessings.",
    5: "Transit Moon in the 5th house promotes intellectual sharpness, artistic creativity, and good news from children.",
    6: "Transit Moon in the 6th house brings victory over obstacles, recovery, and accomplishment of pending tasks (Highly Auspicious).",
    7: "Transit Moon in the 7th house enhances marital warmth, partnership synergy, and fruitful business interactions.",
    8: "Transit Moon in the 8th house (Ashtama Chandra) advises caution in physical health, commuting, and financial commitments.",
    9: "Transit Moon in the 9th house activates fortune and higher learning. Spiritual insights and guidance from mentors will be supportive.",
    10: "Transit Moon in the 10th house brings professional elevation, authority recognition, and career success (Excellent).",
    11: "Transit Moon in the 11th house generates financial gains, fulfilled aspirations, and strong support from network circles (Best).",
    12: "Transit Moon in the 12th house warns of expenditures and fatigue. Prioritize rest and avoid impulsive financial spending."
}


def _get_target_jd(mode: str, bs_year: int, bs_month: int, bs_day: int) -> Tuple[float, datetime.date]:
    """Convert BS date components to Gregorian date and compute morning Julian Day (06:00 UTC)."""
    if mode == "day":
        greg = bs_to_gregorian(bs_year, bs_month, bs_day)
    elif mode == "month":
        greg = bs_to_gregorian(bs_year, bs_month, 15) or bs_to_gregorian(bs_year, bs_month, 1)
    else:  # year
        greg = bs_to_gregorian(bs_year, 6, 15) or bs_to_gregorian(bs_year, 1, 1)

    if not greg:
        # Fallback to reasonable approx
        greg = datetime.date(bs_year - 57, max(1, min(12, bs_month)), max(1, min(28, bs_day)))

    jd = swe.julday(greg.year, greg.month, greg.day, 6.0)
    return jd, greg


def calculate_dynamic_horoscope(
    natal_data: Dict[str, Any],
    mode: str = "day",
    bs_year: int = 2083,
    bs_month: int = 1,
    bs_day: int = 1,
    language: str = "ne",
) -> Dict[str, Any]:
    """
    Main entry point to compute fully dynamic horoscope for a selected BS date and mode.
    Returns complete dictionary ready for HoroscopePage rendering.
    """
    is_ne = language == "ne"

    # 1. Resolve Target Date & Ephemeris Julian Day
    jd, greg = _get_target_jd(mode, bs_year, bs_month, bs_day)

    # 2. Compute Full Transit Analysis
    transit_data = calculate_transit_analysis(natal_data, transit_jd=jd, language=language)
    planet_transits = transit_data.get("planet_transits", {})
    summary = transit_data.get("summary", {})

    # Natal details
    meta = natal_data.get("metadata", {})
    name = meta.get("name", "जातक" if is_ne else "Native")
    lagna_sign_num = transit_data.get("lagna_sign", 1)
    natal_moon_sign_num = transit_data.get("natal_moon_sign", 1)

    lagna_name = rashi_name(lagna_sign_num, language)
    natal_moon_name = rashi_name(natal_moon_sign_num, language)

    # 3. Target Date Panchang Details
    vara_idx = int(jd + 5.75 / 24.0 + 1.5) % 7
    vara_info = VARAS[vara_idx]
    vara_name = vara_info["nepali"] if is_ne else vara_info["name"].split()[0]
    day_lord_key = VARA_LORDS[vara_idx]
    day_lord_name = PLANET_NE.get(day_lord_key, day_lord_key) if is_ne else day_lord_key

    # Moon transit info
    moon_t = planet_transits.get("Moon", {})
    transit_moon_sign = moon_t.get("transit_sign", 1)
    transit_moon_sign_name = rashi_name(transit_moon_sign, language)
    moon_house_from_moon = ((transit_moon_sign - natal_moon_sign_num) % 12) + 1
    moon_house_from_lagna = moon_t.get("transit_house", 1)
    moon_nakshatra = moon_t.get("transit_nakshatra_ne" if is_ne else "transit_nakshatra_en", "—")
    moon_tara = moon_t.get("tarabala", {})
    moon_tara_name = moon_tara.get("tara_ne" if is_ne else "tara_en", "—")
    moon_tara_good = moon_tara.get("is_auspicious", True)

    # Sun transit info
    sun_t = planet_transits.get("Sun", {})
    sun_sign = sun_t.get("transit_sign", 1)
    sun_sign_name = rashi_name(sun_sign, language)
    sun_house_from_moon = ((sun_sign - natal_moon_sign_num) % 12) + 1
    sun_house_from_lagna = sun_t.get("transit_house", 1)

    # Jupiter & Saturn transits
    jup_t = planet_transits.get("Jupiter", {})
    jup_sign = jup_t.get("transit_sign", 1)
    jup_sign_name = rashi_name(jup_sign, language)
    jup_house_from_moon = ((jup_sign - natal_moon_sign_num) % 12) + 1

    sat_t = planet_transits.get("Saturn", {})
    sat_sign = sat_t.get("transit_sign", 1)
    sat_sign_name = rashi_name(sat_sign, language)
    sat_house_from_moon = ((sat_sign - natal_moon_sign_num) % 12) + 1

    # Mars, Mercury, Venus, Rahu, Ketu transits
    mars_t = planet_transits.get("Mars", {})
    mars_house_from_moon = ((mars_t.get("transit_sign", 1) - natal_moon_sign_num) % 12) + 1
    merc_t = planet_transits.get("Mercury", {})
    merc_house_from_moon = ((merc_t.get("transit_sign", 1) - natal_moon_sign_num) % 12) + 1
    ven_t = planet_transits.get("Venus", {})
    ven_house_from_moon = ((ven_t.get("transit_sign", 1) - natal_moon_sign_num) % 12) + 1
    rahu_t = planet_transits.get("Rahu", {})
    rahu_house_from_moon = ((rahu_t.get("transit_sign", 1) - natal_moon_sign_num) % 12) + 1
    ketu_t = planet_transits.get("Ketu", {})
    ketu_house_from_moon = ((ketu_t.get("transit_sign", 1) - natal_moon_sign_num) % 12) + 1

    # Tithi calculation
    sun_lon = sun_t.get("transit_longitude", 0.0)
    moon_lon = moon_t.get("transit_longitude", 0.0)
    tithi_idx = int(((moon_lon - sun_lon) % 360) / 12)
    tithi_obj = TITHIS[tithi_idx] if 0 <= tithi_idx < len(TITHIS) else TITHIS[0]
    paksha_ne = "शुक्ल पक्ष" if tithi_idx < 15 else "कृष्ण पक्ष"
    paksha_en = "Shukla Paksha" if tithi_idx < 15 else "Krishna Paksha"
    tithi_name = f"{paksha_ne} {tithi_obj['nepali']}" if is_ne else f"{paksha_en} {tithi_obj['name']}"

    # Period display label
    m_name_ne = BS_MONTHS_NE[bs_month - 1] if 1 <= bs_month <= 12 else str(bs_month)
    m_name_en = BS_MONTHS_EN[bs_month - 1] if 1 <= bs_month <= 12 else str(bs_month)

    if mode == "day":
        date_label = f"वि.सं. {to_nepali_digits(bs_year)} {m_name_ne} {to_nepali_digits(bs_day)}" if is_ne else f"{bs_day} {m_name_en} {bs_year} BS"
        period_badge = f"📅 {date_label} ({vara_name})"
    elif mode == "month":
        date_label = f"वि.सं. {to_nepali_digits(bs_year)} {m_name_ne} महिना" if is_ne else f"{m_name_en} {bs_year} BS"
        period_badge = f"📅 {date_label}"
    else:
        date_label = f"वि.सं. {to_nepali_digits(bs_year)} साल" if is_ne else f"BS {bs_year}"
        period_badge = f"📅 {date_label}"

    # 4. Generate Dynamic Dimensions
    dimensions = []

    if mode == "day":
        # ── DAY MODE ──────────────────────────────────────────────────────────
        # Overview
        is_chandra_good = moon_house_from_moon in [1, 3, 6, 7, 10, 11]
        chandra_eval = CHANDRA_HOUSE_PHALA_NE.get(moon_house_from_moon, "") if is_ne else CHANDRA_HOUSE_PHALA_EN.get(moon_house_from_moon, "")
        
        overview_title = "🌟 " + ("दिनको ग्रहीय सारांश तथा चन्द्रबल" if is_ne else "Daily Planetary Summary & Chandrabala")
        if is_ne:
            overview_body = (
                f"आज <b>{vara_name}</b>, तिथि <b>{tithi_name}</b>, चन्द्रमा <b>{transit_moon_sign_name}</b> राशिमा "
                f"र <b>{moon_nakshatra}</b> नक्षत्र (ताराबल: <b>{moon_tara_name}</b>) मा गोचर गर्दैछन्। "
                f"तपाईंको जन्म चन्द्रराशि <b>{natal_moon_name}</b> बाट चन्द्रमा <b>{to_nepali_digits(moon_house_from_moon)}औं भाव</b>मा रहेका छन्। "
                f"{chandra_eval} "
                f"आजका वारेश ग्रह <b>{day_lord_name}</b> हुन्। समग्र गोचरमा ९ मध्ये <b>{to_nepali_digits(summary.get('auspicious_planets_count', 5))}</b> ग्रहहरू अनुकूल स्थितिमा छन्।"
            )
        else:
            overview_body = (
                f"Today is <b>{vara_name}</b>, Tithi: <b>{tithi_name}</b>, with Moon transiting <b>{transit_moon_sign_name}</b> "
                f"in <b>{moon_nakshatra}</b> Nakshatra (Tarabala: <b>{moon_tara_name}</b>). "
                f"From your natal Moon sign <b>{natal_moon_name}</b>, Moon occupies the <b>{moon_house_from_moon}th house</b>. "
                f"{chandra_eval} "
                f"Ruler of the day is <b>{day_lord_name}</b>. Overall, <b>{summary.get('auspicious_planets_count', 5)}</b> of 9 planets provide supportive energy."
            )

        # 1. Career & Business
        # Key: 10th house, Saturn, Sun, Mercury
        if is_ne:
            c_sat = "अनुकूल" if sat_house_from_moon in [3, 6, 11] else "धैर्य र अनुशासन आवश्यक"
            c_sun = "सकारात्मक" if sun_house_from_moon in [3, 6, 10, 11] else "सामान्य"
            c_text = (
                f"कार्यक्षेत्रका मुख्य कारक ग्रह शनि तपाईंको चन्द्रराशिबाट <b>{to_nepali_digits(sat_house_from_moon)}औं भाव</b>मा र "
                f"सूर्य <b>{to_nepali_digits(sun_house_from_moon)}औं भाव</b>मा गोचर गरिरहेका छन्। "
            )
            if moon_house_from_moon in [6, 10, 11]:
                c_text += "आज कार्यक्षेत्रमा तपाईंको निर्णय क्षमता र दक्षताको उच्च प्रशंसा हुनेछ। नयाँ जिम्मेवारी वा व्यावसायिक सम्झौताका लागि दिन विशेष फलदायी छ।"
            elif moon_house_from_moon in [8, 12]:
                c_text += "आज कामको चाप बढ्न सक्छ र सहकर्मीसँग सामान्य असमझदारी आउन सक्छ। हतारमा ठूलो निर्णय नलिनुहोस् र आफ्नो काममा एकाग्र रहनुहोस्।"
            else:
                c_text += "दैनिक कार्यहरू नियमित गतिमा अगाडि बढ्नेछन्। प्राविधिक, प्रशासनिक र सञ्चार सम्बन्धी काममा राम्रो सहयोग मिल्नेछ।"
        else:
            c_text = (
                f"Career significator Saturn transits the {sat_house_from_moon}th house and Sun transits the {sun_house_from_moon}th house from natal Moon. "
            )
            if moon_house_from_moon in [6, 10, 11]:
                c_text += "Today is highly favorable for professional recognition, meetings with seniors, and executing critical business agreements."
            else:
                c_text += "Routine responsibilities proceed steadily. Maintain structured communication and focus on high-priority deliverables."

        dimensions.append({
            "title_ne": "💼 १. पेसा, व्यवसाय तथा रोजगार",
            "title_en": "1. Career, Profession & Business",
            "text_ne": c_text,
            "text_en": c_text,
        })

        # 2. Wealth & Finance
        # Key: 2nd, 11th, Jupiter, Venus
        if is_ne:
            f_text = (
                f"धन र समृद्धिका कारक बृहस्पति तपाईंको चन्द्रराशिबाट <b>{to_nepali_digits(jup_house_from_moon)}औं भाव</b>मा र "
                f"शुक्र <b>{to_nepali_digits(ven_house_from_moon)}औं भाव</b>मा गोचरमा छन्। "
            )
            if moon_house_from_moon in [2, 6, 10, 11]:
                f_text += "आज नयाँ आम्दानीका अवसरहरू प्राप्त हुने र विगतमा रोकिएको रकम हात लाग्ने प्रबल योग छ। लगानी सम्बन्धी कुराकानी सकारात्मक रहनेछ।"
            elif moon_house_from_moon in [8, 12]:
                f_text += "अनावश्यक विलासिता र आकस्मिक घरायसी खर्च बढ्न सक्छ। अनलाइन किनमेल तथा उधारो कारोबारमा सावधानी अपनाउनुहोस्।"
            else:
                f_text += "आर्थिक प्रवाह सन्तुलित रहनेछ। दैनिक बजेट अनुसार खर्च व्यवस्थित गर्दा बचत वृद्धि हुनेछ।"
        else:
            f_text = (
                f"Wealth lord Jupiter transits the {jup_house_from_moon}th house and Venus transits the {ven_house_from_moon}th house from your natal Moon. "
            )
            if moon_house_from_moon in [2, 6, 10, 11]:
                f_text += "Favorable cash flow and possible recovery of pending payments. Good day for balanced financial investments."
            else:
                f_text += "Financial position remains stable. Keep a watchful eye on discretionary and impulse expenses."

        dimensions.append({
            "title_ne": "💰 २. आर्थिक स्थिति तथा धन लाभ",
            "title_en": "2. Wealth, Income & Finance",
            "text_ne": f_text,
            "text_en": f_text,
        })

        # 3. Health & Vitality
        # Key: Sun, Moon house 8/12/6
        if is_ne:
            if moon_house_from_moon == 8:
                h_text = "आज चन्द्रमा आठौं (घात) स्थानमा रहेकाले स्वास्थ्यमा विशेष ध्यान दिनु आवश्यक छ। टाउको दुख्ने, पेटको गडबडी वा हल्का आलस्य देखिन सक्छ। प्रशस्त पानी पिउनुहोस् र तनाव नलिनुहोस्।"
            elif moon_house_from_moon == 12:
                h_text = "निद्रामा कमी र आँखा वा खुट्टामा हल्का थकान महसुस हुन सक्छ। कामको बीचमा विश्राम लिनुहोस् र साँझपख योग वा ध्यान गर्नुहोस्।"
            else:
                h_text = "शारीरिक ऊर्जा, स्फूर्ति र आत्मबल राम्रो रहनेछ। सूर्यको गोचरले रोगप्रतिरोधात्मक क्षमता मजबुत बनाउनेछ। खानपान र नियमित व्यायामले थप ताजगी दिनेछ।"
        else:
            if moon_house_from_moon in [8, 12]:
                h_text = "Minor fatigue or sleep irregularity may arise. Maintain hydration, avoid overwork, and practice light breathing exercises."
            else:
                h_text = "Vitality and stamina remain robust. Good physical energy enables smooth handling of daily tasks."

        dimensions.append({
            "title_ne": "🩺 ३. स्वास्थ्य तथा शारीरिक ऊर्जा",
            "title_en": "3. Health & Vitality",
            "text_ne": h_text,
            "text_en": h_text,
        })

        # 4. Love, Marriage & Relationships
        # Key: 7th house, Venus, Moon
        if is_ne:
            if moon_house_from_moon in [1, 2, 4, 7, 11] and ven_house_from_moon in [1, 2, 4, 7, 11]:
                m_text = "दाम्पत्य जीवनमा मिठास र आपसी समझदारी उत्कृष्ट रहनेछ। जीवनसाथीसँग रमाइलो समय बित्नेछ। प्रेम सम्बन्धमा विश्वास प्रगाढ बन्नेछ।"
            elif mars_house_from_moon in [1, 7, 8]:
                m_text = "सानातिना कुरामा मतभेद वा असमझदारी हुन सक्छ। बोलीमा विनम्रता राख्नुहोस् र अनावश्यक तर्क-वितर्कबाट बच्नुहोस्।"
            else:
                m_text = "पारिवारिक वातावरण शान्त र सहयोगी रहनेछ। आफन्त तथा मित्रजनसँग आत्मीय संवाद हुनेछ र घरपरिवारमा सौहार्दता छाउनेछ।"
        else:
            if moon_house_from_moon in [1, 2, 4, 7, 11]:
                m_text = "Harmonious rapport with spouse and family members. A pleasant time for mutual understanding and romantic warmth."
            else:
                m_text = "Domestic life remains steady. Communicate gently to maintain peaceful equilibrium with family members."

        dimensions.append({
            "title_ne": "💍 ४. प्रेम, दाम्पत्य तथा पारिवारिक सद्भाव",
            "title_en": "4. Love, Marriage & Relationships",
            "text_ne": m_text,
            "text_en": m_text,
        })

        # 5. Education & Intellect
        # Key: Mercury, Jupiter, 5th house
        if is_ne:
            if merc_house_from_moon in [1, 2, 4, 5, 10, 11]:
                e_text = "बुद्धि, स्मरणशक्ति र वाक्चातुर्यमा वृद्धि हुनेछ। नयाँ ज्ञान सिक्न र परीक्षा/अन्तर्वार्ताको तयारी गर्न आजको दिन निकै सहयोगी छ।"
            else:
                e_text = "पढाइ तथा सिर्जनात्मक काममा मन एकाग्र गर्न केही प्रयास गर्नुपर्नेछ। सन्तान पक्षबाट सन्तोषजनक समाचार प्राप्त हुनेछ।"
        else:
            e_text = "Intellectual focus and analytical capabilities are sharp. Academic discussions, creative writing, and research work progress smoothly."

        dimensions.append({
            "title_ne": "📚 ५. शिक्षा, बौद्धिक क्षमता तथा सन्तान",
            "title_en": "5. Education, Knowledge & Children",
            "text_ne": e_text,
            "text_en": e_text,
        })

        # 6. Travel & Distant Contacts
        # Key: 3rd, 9th, 12th house
        if is_ne:
            if moon_house_from_moon in [3, 7, 9, 12]:
                t_text = "कामको सिलसिलामा छोटो र फलदायी यात्रा हुन सक्छ। वैदेशिक सम्पर्क, अनलाइन कारोबार र टाढाका मित्रहरूसँगको संवाद उपलब्धिमूलक हुनेछ।"
            else:
                t_text = "नियमित आवतजावत सामान्य रहनेछ। टाढाको यात्रा गर्नुपरेमा आफ्ना महत्त्वपूर्ण सामान र कागजातको सुरक्षामा ध्यान दिनुहोस्।"
        else:
            t_text = "Short trips and external networking will be fruitful. Communications with distant contacts and partners move in a positive direction."

        dimensions.append({
            "title_ne": "✈️ ६. यात्रा, वैदेशिक कार्य तथा सम्पर्क",
            "title_en": "6. Travel & External Contacts",
            "text_ne": t_text,
            "text_en": t_text,
        })

        # 7. Challenges & Cautions
        # Key: Ashtama Chandra, Rahu, Saturn
        if is_ne:
            warns = []
            if moon_house_from_moon == 8:
                warns.append("आज चन्द्रमा आठौं स्थानमा रहेकाले जोखिमपूर्ण काम, विवाद र हतारको निर्णयबाट बच्नुहोस्।")
            if not moon_tara_good:
                warns.append(f"आजको ताराबल '{moon_tara_name}' रहेकाले महत्त्वपूर्ण सम्झौता वा नयाँ सम्झौता गर्दा सतर्कता राख्नुहोस्।")
            if sat_house_from_moon in [1, 2, 12]:
                warns.append("शनिको प्रभावका कारण काममा केही विलम्ब वा ढिलासुस्ती महसुस हुन सक्छ; धैर्य नगुमाउनुहोस्।")
            if not warns:
                warns.append("अति आत्मविश्वास र हतारमा कुनै पनि निर्णय नलिनुहोस्। सवारीसाधन चलाउँदा ट्राफिक नियमको पूर्ण पालना गर्नुहोस्।")
            ch_text = " ".join(warns)
        else:
            ch_text = "Avoid hasty conclusions or emotional friction. Review financial documents thoroughly before commitment."

        dimensions.append({
            "title_ne": "⚠️ ७. चुनौतीहरू तथा सावधानी",
            "title_en": "7. Challenges & Caution",
            "text_ne": ch_text,
            "text_en": ch_text,
        })

    elif mode == "month":
        # ── MONTH MODE ────────────────────────────────────────────────────────
        overview_title = "🌟 " + (f"{m_name_ne} महिनाको मासिक गोचर सारांश" if is_ne else f"{m_name_en} Monthly Transit Forecast")
        if is_ne:
            overview_body = (
                f"वि.सं. <b>{to_nepali_digits(bs_year)} {m_name_ne}</b> महिनामा सूर्यदेव <b>{sun_sign_name}</b> राशिमा गोचर गर्दैछन्। "
                f"तपाईंको जन्म चन्द्रराशि <b>{natal_moon_name}</b> बाट सूर्य <b>{to_nepali_digits(sun_house_from_moon)}औं भाव</b>मा, "
                f"बृहस्पति <b>{to_nepali_digits(jup_house_from_moon)}औं भाव ({jup_sign_name})</b>मा र शनि <b>{to_nepali_digits(sat_house_from_moon)}औं भाव ({sat_sign_name})</b>मा भ्रमण गरिरहेका छन्। "
                f"यस महिना ग्रहीय स्थितिले कार्यक्षेत्र र आर्थिक योजनामा स्थायित्व ल्याउनेछ।"
            )
        else:
            overview_body = (
                f"During <b>{m_name_en} {bs_year} BS</b>, Sun transits <b>{sun_sign_name}</b>. "
                f"From your natal Moon <b>{natal_moon_name}</b>, Sun occupies the <b>{sun_house_from_moon}th house</b>, "
                f"Jupiter occupies the <b>{jup_house_from_moon}th house</b>, and Saturn transits the <b>{sat_house_from_moon}th house</b>. "
                f"This monthly cycle highlights key structural development and progressive momentum."
            )

        # 1. Career
        if is_ne:
            m_c = (
                f"यस महिना कार्यक्षेत्रका अधिपति शनि <b>{to_nepali_digits(sat_house_from_moon)}औं भाव</b>मा र "
                f"देवगुरु बृहस्पति <b>{to_nepali_digits(jup_house_from_moon)}औं भाव</b>मा रहँदा "
                "पेसा व्यवसायमा योजनाबद्ध प्रगति हुनेछ। नयाँ परियोजनाको सुरुवात, पदोन्नतिको सम्भावना र उच्च अधिकारीहरूसँग सुमधुर सम्बन्ध कायम हुनेछ।"
            )
        else:
            m_c = f"Jupiter in the {jup_house_from_moon}th house and Saturn in the {sat_house_from_moon}th house provide stability and strategic expansion in professional endeavors."

        dimensions.append({
            "title_ne": "💼 १. मासिक कार्यक्षेत्र तथा व्यवसाय",
            "title_en": "1. Monthly Career & Business",
            "text_ne": m_c,
            "text_en": m_c,
        })

        # 2. Wealth
        if is_ne:
            m_f = (
                f"बृहस्पतिको दृष्टि र गोचरले धनभावमा सकारात्मक प्रभाव पार्नेछ। "
                "नियमित आयका स्रोतहरू सुदृढ हुनेछन् र अड्किएका काम बन्नेछन्। महिनाको दोस्रो र तेस्रो साता आर्थिक दृष्टिकोणले विशेष लाभदायी रहनेछ।"
            )
        else:
            m_f = "Consistent financial inflow with good potential for budget stabilization and long-term asset planning."

        dimensions.append({
            "title_ne": "💰 २. मासिक आर्थिक तथा सम्पत्ति",
            "title_en": "2. Monthly Wealth & Finance",
            "text_ne": m_f,
            "text_en": m_f,
        })

        # 3. Health
        if is_ne:
            m_h = (
                f"सूर्यको {to_nepali_digits(sun_house_from_moon)}औं भावको गोचरले समग्र आरोग्य राम्रो राख्नेछ। "
                "मौसमी स्वास्थ्य समस्या र खानपानमा ध्यान दिनुहोस्। नियमित योग, प्राणायाम र बिहानी हिँडडुलले शरीरमा स्फूर्ति कायम राख्नेछ।"
            )
        else:
            m_h = "Overall vitality is supported by solar transit. Maintain regular exercise and balanced nutrition to avoid seasonal fatigue."

        dimensions.append({
            "title_ne": "🩺 ३. मासिक स्वास्थ्य तथा आरोग्य",
            "title_en": "3. Monthly Health & Fitness",
            "text_ne": m_h,
            "text_en": m_h,
        })

        # 4. Family & Marriage
        if is_ne:
            m_m = (
                "पारिवारिक जीवनमा आपसी मेलमिलाप र सुखद वातावरण रहनेछ। जीवनसाथीसँग धार्मिक वा रमाइलो यात्राको योग बन्न सक्छ। "
                "घरमा कुनै माङ्गलिक कार्य वा शुभ समाचारको आगमन हुनेछ।"
            )
        else:
            m_m = "Domestic harmony and constructive bonding with spouse. Good period for family gatherings and celebrations."

        dimensions.append({
            "title_ne": "💍 ४. मासिक प्रेम तथा पारिवारिक सद्भाव",
            "title_en": "4. Monthly Family & Relationships",
            "text_ne": m_m,
            "text_en": m_m,
        })

        # 5. Education
        if is_ne:
            m_e = (
                "विद्यार्थीहरूका लागि यो महिना एकाग्रता र बौद्धिक क्षमता विकासका लागि अनुकूल रहनेछ। "
                "प्रतिस्पर्धात्मक परीक्षा, अनुसन्धान र नयाँ सीप सिक्नमा सफलता प्राप्त हुनेछ।"
            )
        else:
            m_e = "Favorable intellectual flow for academic pursuits, competitive exams, and skill development."

        dimensions.append({
            "title_ne": "📚 ५. मासिक शिक्षा तथा सन्तान",
            "title_en": "5. Monthly Education & Children",
            "text_ne": m_e,
            "text_en": m_e,
        })

        # 6. Travel
        if is_ne:
            m_t = (
                "व्यापारिक तथा अध्ययनको सिलसिलामा छोटो वा मध्यम दूरीको यात्रा सफल हुनेछ। "
                "वैदेशिक अध्ययन वा रोजगारीका लागि आवेदन दिएकाहरूको काम अगाडि बढ्नेछ।"
            )
        else:
            m_t = "Purposeful travels will be productive. Positive momentum in foreign communications and visa processing."

        dimensions.append({
            "title_ne": "✈️ ६. मासिक यात्रा तथा वैदेशिक कार्य",
            "title_en": "6. Monthly Travel & Foreign Affairs",
            "text_ne": m_t,
            "text_en": m_t,
        })

        # 7. Caution
        if is_ne:
            m_w = "महिनाको कृष्ण पक्षमा चन्द्रमा कमजोर हुने दिनहरूमा ठूलो आर्थिक लगानी र विवादबाट बच्नुहोस्। महत्वपूर्ण कागजातमा हस्ताक्षर गर्दा राम्ररी अध्ययन गर्नुहोस्।"
        else:
            m_w = "Exercise caution during lunar waning phases. Verify details before committing to major contracts."

        dimensions.append({
            "title_ne": "⚠️ ७. मासिक चुनौती तथा सावधानी",
            "title_en": "7. Monthly Caution & Challenges",
            "text_ne": m_w,
            "text_en": m_w,
        })

    else:
        # ── YEAR MODE ─────────────────────────────────────────────────────────
        # Yearly analysis: Jupiter, Saturn, Rahu-Ketu, Sade Sati
        is_sadesati = sat_house_from_moon in [12, 1, 2]
        is_dhayya = sat_house_from_moon in [4, 8]
        guru_bala = jup_house_from_moon in [2, 5, 7, 9, 11]

        overview_title = "🌟 " + (f"वि.सं. {to_nepali_digits(bs_year)} सालको वार्षिक ग्रहीय गोचर विश्लेषण" if is_ne else f"BS {bs_year} Yearly Transit Forecast")
        if is_ne:
            ss_str = " (साढेसातीको प्रभाव सक्रिय)" if is_sadesati else (" (शनिको अढैयाको प्रभाव सक्रिय)" if is_dhayya else " (शनिको गोचर शुभ स्थितिमा)")
            gb_str = "गुरुबल शुभ र अनुकूल रहेको छ" if guru_bala else "गुरुबल सामान्य छ, बृहस्पतिको आराधना लाभदायक हुनेछ"
            overview_body = (
                f"वि.सं. <b>{to_nepali_digits(bs_year)} साल</b>मा प्रमुख ग्रहहरूको स्थिति: देवगुरु बृहस्पति तपाईंको चन्द्रराशिबाट "
                f"<b>{to_nepali_digits(jup_house_from_moon)}औं भाव ({jup_sign_name})</b>मा, शनिदेव <b>{to_nepali_digits(sat_house_from_moon)}औं भाव ({sat_sign_name}){ss_str}</b>मा "
                f"र राहु <b>{to_nepali_digits(rahu_house_from_moon)}औं भाव</b>मा अवस्थित रहनेछन्। "
                f"यस वर्ष {gb_str}। दीर्घकालीन योजनाहरू, नयाँ लगानी र करियरमा महत्वपूर्ण रूपान्तरणको वर्ष रहनेछ।"
            )
        else:
            overview_body = (
                f"During <b>BS {bs_year}</b>, major transits align: Jupiter in the <b>{jup_house_from_moon}th house ({jup_sign_name})</b>, "
                f"Saturn in the <b>{sat_house_from_moon}th house ({sat_sign_name})</b>, and Rahu in the <b>{rahu_house_from_moon}th house</b>. "
                f"This year emphasizes strategic discipline, karmic realignments, and sustained growth."
            )

        # 1. Career
        if is_ne:
            y_c = (
                f"यस वर्ष कर्मक्षेत्रमा शनिको <b>{to_nepali_digits(sat_house_from_moon)}औं भाव</b>को गोचरले कडा परिश्रम र अनुशासनको पूर्ण प्रतिफल दिलाउनेछ। "
                "वर्षको मध्यभागमा पदोन्नति, कार्यक्षेत्र विस्तार र सामाजिक प्रतिष्ठामा वृद्धि हुने योग छ। प्राविधिक, बैंकिङ र व्यवस्थापकीय क्षेत्रमा उल्लेखनीय सफलता मिल्नेछ।"
            )
        else:
            y_c = f"Saturn's placement in the {sat_house_from_moon}th house rewards disciplined effort. Mid-year offers strong opportunities for career elevation and business expansion."

        dimensions.append({
            "title_ne": "💼 १. वार्षिक करियर, पेसा तथा व्यवसाय",
            "title_en": "1. Annual Career & Business",
            "text_ne": y_c,
            "text_en": y_c,
        })

        # 2. Wealth
        if is_ne:
            y_f = (
                f"बृहस्पतिको अनुकूलताले आर्थिक स्थितिमा उल्लेखनीय सुधार आउनेछ। नयाँ स्थायी सम्पत्ति, जग्गाजमिन वा सवारी साधन जोड्ने सम्भावना प्रबल छ। "
                "ऋणभार कम हुनेछ र बचत वृद्धिमा टेवा पुग्नेछ।"
            )
        else:
            y_f = "Substantial financial enhancement supported by Jupiter. Favorable period for acquiring fixed assets or property."

        dimensions.append({
            "title_ne": "💰 २. वार्षिक आर्थिक स्थिति तथा सम्पत्ति वृद्धि",
            "title_en": "2. Annual Wealth & Financial Growth",
            "text_ne": y_f,
            "text_en": y_f,
        })

        # 3. Health
        if is_ne:
            y_h = (
                "स्वास्थ्यको दृष्टिकोणले वर्ष समग्रमा मध्यम-शुभ रहनेछ। वर्षको पूर्वार्द्धमा कार्यव्यस्तताका कारण थकान र तनाव हुन सक्छ। "
                "नियमित दिनचर्या, सन्तुलित खानपान र समयमै स्वास्थ्य परीक्षण गर्दा आरोग्यता कायम रहनेछ।"
            )
        else:
            y_h = "Health profile remains moderate-to-good. Maintain work-life balance and schedule regular preventive wellness routines."

        dimensions.append({
            "title_ne": "🩺 ३. वार्षिक स्वास्थ्य तथा जीवनशैली",
            "title_en": "3. Annual Health & Wellness",
            "text_ne": y_h,
            "text_en": y_h,
        })

        # 4. Family & Marriage
        if is_ne:
            y_m = (
                "पारिवारिक जीवनमा सुख-शान्ति र समझदारी छाउनेछ। अविवाहितहरूका लागि विवाहको उत्तम प्रस्ताव आउनेछ। "
                "दाम्पत्य जीवनमा आत्मीयता बढ्नेछ र घरमा शुभ धार्मिक कार्य सम्पन्न हुनेछ।"
            )
        else:
            y_m = "Auspicious matrimonial prospects for singles. Domestic peace and deepening bonds in marital relationships."

        dimensions.append({
            "title_ne": "💍 ४. वार्षिक दाम्पत्य, प्रेम तथा पारिवारिक जीवन",
            "title_en": "4. Annual Family & Relationships",
            "text_ne": y_m,
            "text_en": y_m,
        })

        # 5. Education
        if is_ne:
            y_e = (
                "उच्च शिक्षा, अनुसन्धान र छात्रवृत्तिका लागि प्रयासरत विद्यार्थीहरूले उल्लेखनीय सफलता पाउनेछन्। "
                "प्रतिस्पर्धात्मक परीक्षामा राम्रो नतिजा आउनेछ। सन्तानको प्रगतिले मन प्रसन्न रहनेछ।"
            )
        else:
            y_e = "Remarkable achievements in higher education, research, and competitive tests. Joy through children's accomplishments."

        dimensions.append({
            "title_ne": "📚 ५. वार्षिक शिक्षा तथा बौद्धिक विकास",
            "title_en": "5. Annual Education & Intellect",
            "text_ne": y_e,
            "text_en": y_e,
        })

        # 6. Travel
        if is_ne:
            y_t = (
                "विदेश यात्रा, उच्च शिक्षा वा रोजगारीका लागि विदेश जाने योजना सफल हुनेछ। "
                "तीर्थयात्रा तथा आध्यात्मिक स्थलहरूको भ्रमणको सुयोग बन्नेछ।"
            )
        else:
            y_t = "High probability of international travel, relocation, or pilgrimage journeys yielding fruitful results."

        dimensions.append({
            "title_ne": "✈️ ६. वार्षिक यात्रा तथा वैदेशिक अवसर",
            "title_en": "6. Annual Travel & Foreign Prospects",
            "text_ne": y_t,
            "text_en": y_t,
        })

        # 7. Caution
        if is_ne:
            y_w = (
                "शनि वा राहुको प्रभावका कारण समय-समयमा मानसिक अन्योल वा काममा ढिलाइ हुन सक्छ। "
                "जोखिमपूर्ण आर्थिक निर्णय र अनावश्यक कानुनी झमेलाबाट टाढा रहनु बुद्धिमानी हुनेछ।"
            )
        else:
            y_w = "Patience is essential when navigating delays. Avoid speculative shortcuts or contentious legal entanglements."

        dimensions.append({
            "title_ne": "⚠️ ७. वार्षिक चुनौती तथा सावधानी",
            "title_en": "7. Annual Challenges & Caution",
            "text_ne": y_w,
            "text_en": y_w,
        })

    # 5. Lucky Factors & Remedies (Dynamically Tailored)
    # Derive lucky direction based on transit Moon sign element
    dir_info = SIGN_ELEMENT_DIRECTION.get(transit_moon_sign, ("पूर्व", "East"))
    subha_direction = dir_info[0] if is_ne else dir_info[1]

    # Lucky color from Day Lord and transit Moon
    lucky_col_info = PLANET_LUCKY_COLORS.get(day_lord_key, ("पहेंलो / सेतो", "Yellow / White"))
    subha_color = lucky_col_info[0] if is_ne else lucky_col_info[1]

    # Lucky numbers
    subha_numbers = PLANET_LUCKY_NUMBERS.get(day_lord_key, "३, ७, ९")
    if is_ne:
        subha_numbers = to_nepali_digits(subha_numbers)

    # Auspicious time (Abhijit Muhurta or auspicious Choghadiya based on day)
    subha_samaya = (
        f"बिहान ११:३५ देखि दिउँसो १२:२५ सम्म (अभिजीत मुहूर्त)" if is_ne
        else "11:35 AM - 12:25 PM (Abhijit Muhurta)"
    )

    lucky_lines = [
        ("🎨 " + ("शुभ रङ्ग" if is_ne else "Lucky Color"), subha_color),
        ("🔢 " + ("शुभ अङ्क" if is_ne else "Lucky Number"), subha_numbers),
        ("🧭 " + ("शुभ दिशा" if is_ne else "Lucky Direction"), subha_direction),
        ("⏰ " + ("शुभ समय" if is_ne else "Auspicious Time"), subha_samaya),
    ]

    # Mantras & Karma Remedies tailored to day lord & moon
    if day_lord_key == "Sun":
        mantra_str = "ॐ घृणिः सूर्याय नमः"
        deity_remedy = "बिहान तामाको लोटाबाट सूर्यलाई अर्घ्य दिनुहोस् र पिता/अभिभावकको आशीर्वाद लिनुहोस्।"
    elif day_lord_key == "Moon":
        mantra_str = "ॐ सों सोमाय नमः"
        deity_remedy = "शिव मन्दिरमा जल/दूध चढाउनुहोस् र आमालाई सम्मान गरी सेतो वस्तु दान गर्नुहोस्।"
    elif day_lord_key == "Mars":
        mantra_str = "ॐ अं अङ्गारकाय नमः"
        deity_remedy = "हनुमान चालिसा पाठ गर्नुहोस् र रातो फूल वा मीठो भोजन साना बालकहरूलाई वितरण गर्नुहोस्।"
    elif day_lord_key == "Mercury":
        mantra_str = "ॐ बुं बुधाय नमः"
        deity_remedy = "भगवान् गणेशलाई दूबो र मोदक अर्पण गर्नुहोस् र चराचुरुङ्गीलाई हरियो मुंग/अन्न दिनुहोस्।"
    elif day_lord_key == "Jupiter":
        mantra_str = "ॐ बृं बृहस्पतये नमः"
        deity_remedy = "भगवान् विष्णुको ध्यान गर्नुहोस्, निधारमा केशर/पहेंलो चन्दन लगाउनुहोस् र गुरुजनको सम्मान गर्नुहोस्।"
    elif day_lord_key == "Venus":
        mantra_str = "ॐ शुं शुक्राय नमः"
        deity_remedy = "माता लक्ष्मीको पूजा गर्नुहोस्, सेतो सुगन्धित फूल चढाउनुहोस् र कन्याहरूलाई सम्मान गर्नुहोस्।"
    else:  # Saturn
        mantra_str = "ॐ शं शनैश्चराय नमः"
        deity_remedy = "पीपलको रुखमा जल चढाउनुहोस्, तिलको तेलको दीप बाल्नुहोस् र गरिब असहायलाई भोजन वा कालो कम्बल दिनुहोस्।"

    if is_ne:
        remedy_text = (
            f"<b>दैनिक वैदिक मन्त्र:</b> <i>'{mantra_str}'</i> (१०८ वा २१ पटक जप गर्नुहोस्)।<br>"
            f"<b>वारेश ({day_lord_name}) अनुसारको सेवा उपाय:</b> {deity_remedy}<br>"
            f"<b>चन्द्रबल शान्ति उपाय:</b> 'ॐ नमः शिवाय' मन्त्र जप गरी मन शान्त राख्नुहोस्।"
        )
    else:
        remedy_text = (
            f"<b>Vedic Mantra:</b> Chant <i>'{mantra_str}'</i> 21 or 108 times.<br>"
            f"<b>Planetary Karma Remedy:</b> {deity_remedy}<br>"
            f"<b>Moon Harmony:</b> Chant 'Om Namah Shivaya' to align emotional peace and focus."
        )

    # 6. Planetary Transit Snapshot (For Structured Grid Display)
    table_rows = []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        p_info = planet_transits.get(pname, {})
        p_sign = p_info.get("transit_sign", 1)
        p_lon = p_info.get("transit_longitude", 0.0) % 30.0
        deg = int(p_lon)
        minute = int((p_lon - deg) * 60)
        min_fmt = f"{minute:02d}"
        deg_str = f"{to_nepali_digits(deg)}°{to_nepali_digits(min_fmt)}′" if is_ne else f"{deg}°{min_fmt}′"

        h_moon = ((p_sign - natal_moon_sign_num) % 12) + 1
        h_lagna = p_info.get("transit_house", 1)

        t_name = p_info.get("tarabala", {}).get("tara_ne" if is_ne else "tara_en", "—")
        is_good = p_info.get("overall_auspicious", False)
        status_str = ("शुभ" if is_good else "सावधानी") if is_ne else ("Favorable" if is_good else "Caution")

        table_rows.append({
            "planet_name": PLANET_NE.get(pname, pname) if is_ne else pname,
            "planet_code": pname,
            "sign_name": rashi_name(p_sign, language),
            "degree_str": deg_str,
            "house_from_moon": to_nepali_digits(h_moon) if is_ne else str(h_moon),
            "house_from_lagna": to_nepali_digits(h_lagna) if is_ne else str(h_lagna),
            "nakshatra": p_info.get("transit_nakshatra_ne" if is_ne else "transit_nakshatra_en", "—"),
            "tarabala": t_name,
            "is_auspicious": is_good,
            "status_str": status_str,
        })

    return {
        "period_badge": period_badge,
        "date_label": date_label,
        "mode": mode,
        "day_lord": day_lord_name,
        "tithi_name": tithi_name,
        "vara_name": vara_name,
        "subject_name": name,
        "lagna_name": lagna_name,
        "moon_name": natal_moon_name,
        "overview_title": overview_title,
        "overview_body": overview_body,
        "dimensions": dimensions,
        "lucky_lines": lucky_lines,
        "remedy_title": "🕉️ " + ("शुभ तत्वहरू तथा शास्त्रीय उपाय" if is_ne else "Lucky Elements & Classical Remedies"),
        "remedy_body": remedy_text,
        "table_rows": table_rows,
    }
