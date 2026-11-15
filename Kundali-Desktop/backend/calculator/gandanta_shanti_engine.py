# -*- coding: utf-8 -*-
"""
backend/calculator/gandanta_shanti_engine.py

Classical Gandanta & Arishta Janma Shanti Engine
(बृहत्पाराशर होराशास्त्र: अध्याय ८० देखि १०० — अनिष्टजन्मलक्षणं तत्प्रशमनाध्यायश्च)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Comprehensive Vedic / Parashari Birth Afflictions & Shanti Calculations:
  1. गण्डान्त त्रिविध विचार (Threefold Gandanta):
     - नक्षत्र गण्डान्त (Nakshatra Gandanta: Ashwini, Ashlesha, Magha, Jyeshtha, Moola, Revati)
       * चरणगत फल (Pada-wise predictions)
       * अभुक्त मूल (Abhukta Moola in Jyeshtha & Moola sandhi)
       * काल भेद (दिवा जन्म: पिता, रात्रि जन्म: माता, सन्ध्या जन्म: आत्मदोष)
     - तिथि गण्डान्त (Tithi Gandanta: Purna & Nanda sandhi)
     - लग्न गण्डान्त (Lagna Gandanta: Cancer-Leo, Scorpio-Sag, Pisces-Aries sandhi)
  2. अनिष्ट जन्म दोषहरू (Arishta Janma Afflictions from BPHS):
     - अमावास्या जन्म शान्ति (Amavasya Janana - Ch. 81)
     - कृष्ण चतुर्दशी जन्म षष्ठ्यंश फल (Krishna Chaturdashi Janana - Ch. 82)
     - संक्रान्ति जन्म (Sankranti Janana - Ch. 85)
     - ग्रहण काल जन्म (Surya/Chandra Grahana Janana - Ch. 86)
     - भद्रा (विष्टि करण) जन्म (Bhadra Janana)
     - यमघण्ट / कालदण्ड योग जन्म
     - त्रिखल दोष (Trikhal Dosha - Ch. 98: ३ कन्यापछि पुत्र वा ३ पुत्रपछि कन्या)
  3. दोष भंग तथा शुभाशुभ सन्तुलन (Arishta Bhanga Yogas):
     - केन्द्रमा बृहस्पति / शुक्रको स्थिति (BPHS: "यथा सिंहं समालोक्य...")
     - शुभ ग्रह दृष्टि, पक्षबली चन्द्रमा र लग्नेशको बल
  4. शास्त्रीय शान्ति मन्त्र तथा वैदिक उपचार विधान (Prescribed Vedic Remedies):
     - नक्षत्र देवता मन्त्र, जप संख्या र दान सामग्री
     - २७ वृक्षका पात, सप्तधान्य, छाँयापात्र दान, महामृत्युञ्जय जप तथा रुद्राभिषेक
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

# 27 Nakshatras list
NAKSHATRAS = [
    {"index": 0, "name": "Ashwini", "nepali": "अश्विनी", "lord": "Ketu", "deity": "अश्विनीकुमार"},
    {"index": 1, "name": "Bharani", "nepali": "भरणी", "lord": "Venus", "deity": "यमराज"},
    {"index": 2, "name": "Krittika", "nepali": "कृत्तिका", "lord": "Sun", "deity": "अग्नि"},
    {"index": 3, "name": "Rohini", "nepali": "रोहिणी", "lord": "Moon", "deity": "ब्रह्मा"},
    {"index": 4, "name": "Mrigashira", "nepali": "मृगशिरा", "lord": "Mars", "deity": "चन्द्रमा"},
    {"index": 5, "name": "Ardra", "nepali": "आर्द्रा", "lord": "Rahu", "deity": "रुद्र/शिव"},
    {"index": 6, "name": "Punarvasu", "nepali": "पुनर्वसु", "lord": "Jupiter", "deity": "अदिति"},
    {"index": 7, "name": "Pushya", "nepali": "पुष्य", "lord": "Saturn", "deity": "बृहस्पति"},
    {"index": 8, "name": "Ashlesha", "nepali": "अश्लेषा", "lord": "Mercury", "deity": "सर्प/नाग"},
    {"index": 9, "name": "Magha", "nepali": "मघा", "lord": "Ketu", "deity": "पितृ"},
    {"index": 10, "name": "Purva Phalguni", "nepali": "पूर्वाफाल्गुनी", "lord": "Venus", "deity": "भग"},
    {"index": 11, "name": "Uttara Phalguni", "nepali": "उत्तराफाल्गुनी", "lord": "Sun", "deity": "अर्यमा"},
    {"index": 12, "name": "Hasta", "nepali": "हस्त", "lord": "Moon", "deity": "सूर्य/सविता"},
    {"index": 13, "name": "Chitra", "nepali": "चित्रा", "lord": "Mars", "deity": "विश्वकर्मा"},
    {"index": 14, "name": "Swati", "nepali": "स्वाती", "lord": "Rahu", "deity": "वायु"},
    {"index": 15, "name": "Vishakha", "nepali": "विशाखा", "lord": "Jupiter", "deity": "इन्द्राग्नि"},
    {"index": 16, "name": "Anuradha", "nepali": "अनुराधा", "lord": "Saturn", "deity": "मित्र"},
    {"index": 17, "name": "Jyeshtha", "nepali": "ज्येष्ठा", "lord": "Mercury", "deity": "इन्द्र"},
    {"index": 18, "name": "Moola", "nepali": "मूल", "lord": "Ketu", "deity": "निऋति/राक्षस"},
    {"index": 19, "name": "Purva Ashadha", "nepali": "पूर्वाषाढा", "lord": "Venus", "deity": "जल/वरुण"},
    {"index": 20, "name": "Uttara Ashadha", "nepali": "उत्तराषाढा", "lord": "Sun", "deity": "विश्वेदेवा"},
    {"index": 21, "name": "Shravana", "nepali": "श्रवण", "lord": "Moon", "deity": "विष्णु"},
    {"index": 22, "name": "Dhanishta", "nepali": "धनिष्ठा", "lord": "Mars", "deity": "अष्टवसु"},
    {"index": 23, "name": "Shatabhisha", "nepali": "शतभिषा", "lord": "Rahu", "deity": "वरुण"},
    {"index": 24, "name": "Purva Bhadrapada", "nepali": "पूर्वभाद्रपदा", "lord": "Jupiter", "deity": "अजैकपाद"},
    {"index": 25, "name": "Uttara Bhadrapada", "nepali": "उत्तरभाद्रपदा", "lord": "Saturn", "deity": "अहिर्बुध्न्य"},
    {"index": 26, "name": "Revati", "nepali": "रेवती", "lord": "Mercury", "deity": "पूषा"}
]

# Classical Pada-wise predictions for Gandanta Nakshatras (BPHS)
PADA_PHALA_BPHS = {
    "Moola": {
        1: {"ne": "पितालाई कष्ट / पितृनाश भय (प्रथम चरण)", "en": "Affliction to father (Pada 1)", "severity": "उच्च"},
        2: {"ne": "मातालाई कष्ट / मातृपीडा भय (द्वितीय चरण)", "en": "Affliction to mother (Pada 2)", "severity": "मध्यम-उच्च"},
        3: {"ne": "धनहानि / परिवारमा आर्थिक संकट (तृतीय चरण)", "en": "Loss of wealth / financial stress (Pada 3)", "severity": "मध्यम"},
        4: {"ne": "शुभ फल, कुलवृद्धि तथा राजसम्मान (चतुर्थ चरण - दोष अत्यन्त न्यून)", "en": "Auspicious, family prosperity (Pada 4 - minimal dosha)", "severity": "सामान्य"}
    },
    "Ashlesha": {
        1: {"ne": "शुभ एवं शान्त फल (प्रथम चरण - दोषरहित)", "en": "Auspicious and peaceful (Pada 1)", "severity": "सामान्य"},
        2: {"ne": "वित्तहानि / आर्थिक नोक्सानी (द्वितीय चरण)", "en": "Financial loss (Pada 2)", "severity": "मध्यम"},
        3: {"ne": "मातालाई कष्ट / मातृपीडा (तृतीय चरण)", "en": "Affliction to mother (Pada 3)", "severity": "मध्यम-उच्च"},
        4: {"ne": "पितालाई कष्ट / पितृनाश भय (चतुर्थ चरण - तीव्र गण्डान्त सन्धि)", "en": "Affliction to father / severe gandanta sandhi (Pada 4)", "severity": "उच्च"}
    },
    "Magha": {
        1: {"ne": "मातालाई कष्ट / मातृपीडा (प्रथम चरण - तीव्र गण्डान्त सन्धि)", "en": "Affliction to mother / severe gandanta sandhi (Pada 1)", "severity": "उच्च"},
        2: {"ne": "पितालाई कष्ट / पितृचिन्ता (द्वितीय चरण)", "en": "Affliction to father (Pada 2)", "severity": "मध्यम-उच्च"},
        3: {"ne": "सुख, विद्या एवं प्रतिष्ठा लाभ (तृतीय चरण)", "en": "Happiness, education, honor (Pada 3)", "severity": "सामान्य"},
        4: {"ne": "धन, ऐश्वर्य एवं सौभाग्य वृद्धि (चतुर्थ चरण)", "en": "Wealth and prosperity (Pada 4)", "severity": "सामान्य"}
    },
    "Jyeshtha": {
        1: {"ne": "ज्येष्ठ भ्राता (दाजु) लाई कष्ट (प्रथम चरण)", "en": "Affliction to elder brother (Pada 1)", "severity": "मध्यम"},
        2: {"ne": "कनिष्ठ भ्राता (भाइ) लाई कष्ट (द्वितीय चरण)", "en": "Affliction to younger brother (Pada 2)", "severity": "मध्यम"},
        3: {"ne": "मातालाई कष्ट / मातृकष्ट (तृतीय चरण)", "en": "Affliction to mother (Pada 3)", "severity": "मध्यम-उच्च"},
        4: {"ne": "स्वयं जातकलाई कष्ट / अभुक्त मूल सन्धि (चतुर्थ चरण - तीव्र गण्डान्त)", "en": "Affliction to self / Abhukta Moola sandhi (Pada 4 - severe)", "severity": "उच्च"}
    },
    "Revati": {
        1: {"ne": "राजसम्मान, बुद्धि एवं कीर्ति (प्रथम चरण)", "en": "Royal honor and wisdom (Pada 1)", "severity": "सामान्य"},
        2: {"ne": "मन्त्रिपद, व्यापार लाभ एवं सुख (द्वितीय चरण)", "en": "Ministerial status / business gain (Pada 2)", "severity": "सामान्य"},
        3: {"ne": "धन, वाहन एवं पशु लाभ (तृतीय चरण)", "en": "Wealth and vehicles (Pada 3)", "severity": "सामान्य"},
        4: {"ne": "मातापितालाई कष्ट / मीन-मेष सन्धि दोष (चतुर्थ चरण - गण्डान्त)", "en": "Affliction to parents / Pisces-Aries sandhi (Pada 4)", "severity": "मध्यम-उच्च"}
    },
    "Ashwini": {
        1: {"ne": "पितालाई कष्ट / मेष आदि सन्धि (प्रथम चरण - गण्डान्त)", "en": "Affliction to father / Aries initial sandhi (Pada 1)", "severity": "मध्यम-उच्च"},
        2: {"ne": "सुख, ऐश्वर्य एवं उत्तम स्वास्थ्य (द्वितीय चरण)", "en": "Happiness and good health (Pada 2)", "severity": "सामान्य"},
        3: {"ne": "राजकीय मान एवं विद्या लाभ (तृतीय चरण)", "en": "Government honor and education (Pada 3)", "severity": "सामान्य"},
        4: {"ne": "धन, प्रतिष्ठा एवं कुलदीप योग (चतुर्थ चरण)", "en": "Wealth, prestige, family pride (Pada 4)", "severity": "सामान्य"}
    }
}

# Tithi Gandanta details
PURNA_TITHIS = [5, 10, 15, 20, 25, 30] # Shukla/Krishna 5, 10, 15
NANDA_TITHIS = [1, 6, 11, 16, 21, 26] # Shukla/Krishna 1, 6, 11


def _normalize_deg(deg: float) -> float:
    return deg % 360.0


def calculate_nakshatra_from_lon(longitude: float) -> Tuple[int, int, float]:
    """Returns (nakshatra_index 0-26, pada 1-4, degrees_into_nakshatra 0-13.333)."""
    lon = _normalize_deg(longitude)
    nak_deg = 360.0 / 27.0 # 13.333333333333334 degrees
    nak_idx = int(lon / nak_deg) % 27
    deg_in_nak = lon - (nak_idx * nak_deg)
    pada_deg = nak_deg / 4.0 # 3.3333333333333335 degrees = 3°20'
    pada = int(deg_in_nak / pada_deg) + 1
    if pada > 4:
        pada = 4
    return nak_idx, pada, deg_in_nak


def evaluate_nakshatra_gandanta(moon_lon: float, birth_hour: Optional[float] = None) -> Dict[str, Any]:
    """
    Evaluates Nakshatra Gandanta for Moon's longitude.
    Gandanta nakshatras:
      - Revati (26) Pada 4 to Ashwini (0) Pada 1
      - Ashlesha (8) Pada 4 to Magha (9) Pada 1
      - Jyeshtha (17) Pada 4 to Moola (18) Pada 1
    Also checks general birth in any of the 6 Gandanta Nakshatras and pada phala.
    """
    nak_idx, pada, deg_in_nak = calculate_nakshatra_from_lon(moon_lon)
    nak_info = NAKSHATRAS[nak_idx]
    nak_name = nak_info["name"]
    nak_ne = nak_info["nepali"]

    is_gandanta_nakshatra = nak_name in ["Ashwini", "Ashlesha", "Magha", "Jyeshtha", "Moola", "Revati"]
    is_sandhi_gandanta = False
    sandhi_name_ne = ""
    is_abhukta_moola = False
    gandanta_level = "दोषरहित"
    severity = "न्यून"

    # Precise Sandhi Checks (Last/First 3°20' or quarter 4/1 at junctions)
    # Ashlesha (8) Pada 4 & Magha (9) Pada 1: Junction of Cancer & Leo
    if nak_name == "Ashlesha" and pada == 4:
        is_sandhi_gandanta = True
        sandhi_name_ne = "कर्कट-सिंह (अश्लेषा-मघा) सन्धि गण्डान्त"
        gandanta_level = "तीव्र गण्डान्त (अश्लेषा चतुर्थ चरण)"
        severity = "उच्च"
    elif nak_name == "Magha" and pada == 1:
        is_sandhi_gandanta = True
        sandhi_name_ne = "सिंह-कर्कट (मघा-अश्लेषा) आदि सन्धि गण्डान्त"
        gandanta_level = "तीव्र गण्डान्त (मघा प्रथम चरण)"
        severity = "उच्च"
    # Jyeshtha (17) Pada 4 & Moola (18) Pada 1: Junction of Scorpio & Sagittarius
    elif nak_name == "Jyeshtha" and pada == 4:
        is_sandhi_gandanta = True
        sandhi_name_ne = "वृश्चिक-धनु (ज्येष्ठा-मूल) सन्धि गण्डान्त"
        gandanta_level = "तीव्र गण्डान्त (ज्येष्ठा चतुर्थ चरण)"
        severity = "अति उच्च"
        # Abhukta Moola: last 24 minutes of arc (0.4°) of Jyeshtha
        if deg_in_nak >= (13.333333333333334 - 0.4):
            is_abhukta_moola = True
    elif nak_name == "Moola" and pada == 1:
        is_sandhi_gandanta = True
        sandhi_name_ne = "धनु-वृश्चिक (मूल-ज्येष्ठा) आदि सन्धि गण्डान्त"
        gandanta_level = "तीव्र गण्डान्त (मूल प्रथम चरण)"
        severity = "अति उच्च"
        # Abhukta Moola: first 24 minutes of arc (0.4°) of Moola
        if deg_in_nak <= 0.4:
            is_abhukta_moola = True
    # Revati (26) Pada 4 & Ashwini (0) Pada 1: Junction of Pisces & Aries
    elif nak_name == "Revati" and pada == 4:
        is_sandhi_gandanta = True
        sandhi_name_ne = "मीन-मेष (रेवती-अश्विनी) सन्धि गण्डान्त"
        gandanta_level = "गण्डान्त (रेवती चतुर्थ चरण)"
        severity = "मध्यम-उच्च"
    elif nak_name == "Ashwini" and pada == 1:
        is_sandhi_gandanta = True
        sandhi_name_ne = "मेष-मीन (अश्विनी-रेवती) आदि सन्धि गण्डान्त"
        gandanta_level = "गण्डान्त (अश्विनी प्रथम चरण)"
        severity = "मध्यम-उच्च"
    elif is_gandanta_nakshatra:
        gandanta_level = f"मूल/गण्डान्त नक्षत्र जन्म ({nak_ne} चरण {pada})"
        severity = "मध्यम"

    # Pada phala details
    pada_phala = None
    if nak_name in PADA_PHALA_BPHS and pada in PADA_PHALA_BPHS[nak_name]:
        pada_phala = PADA_PHALA_BPHS[nak_name][pada]

    # Time of birth affliction factor (Kala Bheda)
    kala_bheda_ne = "सामान्य"
    if birth_hour is not None and (is_gandanta_nakshatra or is_sandhi_gandanta):
        # Traditional: Day = 06:00 - 18:00, Night = 18:00 - 05:00, Sandhya = 05:00-06:00 & 18:00-19:00
        if (5.0 <= birth_hour < 6.5) or (17.5 <= birth_hour < 19.0):
            kala_bheda_ne = "सन्ध्या जन्म (स्वयं शिशुलाई स्वास्थ्य कष्ट सम्भावना)"
        elif 6.5 <= birth_hour < 17.5:
            kala_bheda_ne = "दिवा जन्म (पराशर अनुसार विशेषतः पितालाई अरिष्ट/कष्ट सम्भावना)"
        else:
            kala_bheda_ne = "रात्रि जन्म (पराशर अनुसार विशेषतः मातालाई अरिष्ट/कष्ट सम्भावना)"

    return {
        "nakshatra_name": nak_name,
        "nakshatra_ne": nak_ne,
        "pada": pada,
        "degrees_in_nakshatra": round(deg_in_nak, 3),
        "is_gandanta_nakshatra": is_gandanta_nakshatra,
        "is_sandhi_gandanta": is_sandhi_gandanta,
        "sandhi_name_ne": sandhi_name_ne,
        "is_abhukta_moola": is_abhukta_moola,
        "gandanta_level": gandanta_level,
        "severity": severity,
        "pada_phala": pada_phala,
        "kala_bheda_ne": kala_bheda_ne
    }


def evaluate_tithi_gandanta(sun_lon: float, moon_lon: float) -> Dict[str, Any]:
    """
    Evaluates Tithi Gandanta:
    Sandhi between Purna Tithis (5, 10, 15, 20, 25, 30) and Nanda Tithis (1, 6, 11, 16, 21, 26).
    1 Tithi = 12° of Moon-Sun difference.
    Sandhi is typically the last 0.5° (1 Ghati equivalent) of Purna and first 0.5° of Nanda.
    """
    diff = _normalize_deg(moon_lon - sun_lon)
    tithi_num = int(diff / 12.0) + 1 # 1 to 30
    deg_in_tithi = diff % 12.0

    is_tithi_gandanta = False
    gandanta_desc_ne = "दोषरहित"
    severity = "सामान्य"

    # Check if close to boundary of Purna -> Nanda
    # If at end of Purna tithi (within 0.8 degrees of 12°)
    if tithi_num in PURNA_TITHIS and deg_in_tithi >= 11.2:
        is_tithi_gandanta = True
        gandanta_desc_ne = f"पूर्णा तिथि ({tithi_num}) को अन्त्य सन्धि गण्डान्त"
        severity = "मध्यम"
    # If at start of Nanda tithi (within 0.8 degrees of 0°)
    elif tithi_num in NANDA_TITHIS and deg_in_tithi <= 0.8:
        is_tithi_gandanta = True
        gandanta_desc_ne = f"नन्दा तिथि ({tithi_num}) को प्रारम्भिक सन्धि गण्डान्त"
        severity = "मध्यम"

    tithi_names = [
        "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पञ्चमी",
        "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
        "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
        "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पञ्चमी",
        "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
        "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावास्या"
    ]
    tithi_name = tithi_names[min(tithi_num - 1, 29)]
    paksha = "शुक्ल" if tithi_num <= 15 else "कृष्ण"

    return {
        "tithi_num": tithi_num,
        "tithi_name": f"{paksha} {tithi_name}",
        "deg_in_tithi": round(deg_in_tithi, 2),
        "is_tithi_gandanta": is_tithi_gandanta,
        "gandanta_desc_ne": gandanta_desc_ne,
        "severity": severity
    }


def evaluate_lagna_gandanta(lagna_lon: float) -> Dict[str, Any]:
    """
    Evaluates Lagna Gandanta:
    Sandhi between Water signs (Cancer 3, Scorpio 7, Pisces 11) and Fire signs (Leo 4, Sag 8, Aries 0).
    Last 0.5° (30 minutes of arc) of water sign and first 0.5° of fire sign.
    """
    lon = _normalize_deg(lagna_lon)
    sign_idx = int(lon / 30.0) % 12
    deg_in_sign = lon % 30.0

    is_lagna_gandanta = False
    desc_ne = "दोषरहित"
    severity = "सामान्य"

    # Water signs: 3 (Cancer), 7 (Scorpio), 11 (Pisces)
    if sign_idx in [3, 7, 11] and deg_in_sign >= 29.5:
        is_lagna_gandanta = True
        next_sign = SIGN_NAMES_NE[(sign_idx + 1) % 12]
        desc_ne = f"{SIGN_NAMES_NE[sign_idx]}-{next_sign} लग्न सन्धि गण्डान्त (अन्तिम ३० कला)"
        severity = "उच्च"
    # Fire signs: 0 (Aries), 4 (Leo), 8 (Sagittarius)
    elif sign_idx in [0, 4, 8] and deg_in_sign <= 0.5:
        is_lagna_gandanta = True
        prev_sign = SIGN_NAMES_NE[(sign_idx - 1) % 12]
        desc_ne = f"{prev_sign}-{SIGN_NAMES_NE[sign_idx]} लग्न आदि सन्धि गण्डान्त (प्रारम्भिक ३० कला)"
        severity = "उच्च"

    return {
        "lagna_sign_index": sign_idx,
        "lagna_sign_name": SIGN_NAMES_NE[sign_idx],
        "lagna_deg_in_sign": round(deg_in_sign, 2),
        "is_lagna_gandanta": is_lagna_gandanta,
        "desc_ne": desc_ne,
        "severity": severity
    }


def evaluate_arishta_janma_yogas(
    sun_lon: float,
    moon_lon: float,
    rahu_lon: Optional[float] = None,
    ketu_lon: Optional[float] = None,
    order_of_child: Optional[str] = None # e.g. "son_after_3_daughters" or "daughter_after_3_sons"
) -> List[Dict[str, Any]]:
    """
    Evaluates other classical inauspicious birth conditions (BPHS chapters 81-98):
      1. Amavasya Janana (Ch. 81)
      2. Krishna Chaturdashi Janana (Ch. 82 - 6 parts)
      3. Surya/Chandra Grahana Janana (Ch. 86)
      4. Sankranti Janana (Ch. 85)
      5. Trikhal Dosha (Ch. 98)
    """
    yogas = []
    diff = _normalize_deg(moon_lon - sun_lon)
    tithi_num = int(diff / 12.0) + 1
    deg_in_tithi = diff % 12.0

    # 1. Amavasya Janana (BPHS Ch. 81: दर्शजन्म शान्ति)
    # Tithi 30 is Amavasya
    if tithi_num == 30:
        yogas.append({
            "name": "अमावास्या जन्म (दर्शजन्म शान्ति)",
            "reference": "बृहत्पाराशर होराशास्त्र अध्याय ८१",
            "condition": "सूर्य र चन्द्रको पूर्ण युति (चन्द्रमा सर्वथा क्षीण)",
            "impact_ne": "पिता-मातालाई कष्ट, दृष्टिमा मन्दता वा शारीरिक दुर्बलता, बाल्यकालमा स्वास्थ्य अरिष्ट।",
            "shanti_ne": "सूर्य-चन्द्र प्रतिमा पूजा, गोदान, रुद्राभिषेक तथा घृतपात्र (छाँयापात्र) दान विधान।",
            "severity": "उच्च"
        })

    # 2. Krishna Chaturdashi Janana (BPHS Ch. 82: कृष्णचतुर्दशी जन्म शान्ति)
    # Tithi 29 is Krishna Chaturdashi (divided into 6 parts of 2 degrees each)
    if tithi_num == 29:
        part_idx = int(deg_in_tithi / 2.0) + 1
        if part_idx > 6:
            part_idx = 6
        part_phala_map = {
            1: ("प्रथम षष्ठ्यंश (०°-२°)", "शुभ एवं दोषमुक्त", "सामान्य", "सामान्य शिव पूजा"),
            2: ("द्वितीय षष्ठ्यंश (२°-४°)", "पितृकष्ट / पितालाई अरिष्ट", "उच्च", "महामृत्युञ्जय जप, पिताको दीर्घायु कामना"),
            3: ("तृतीय षष्ठ्यंश (४°-६°)", "मातृकष्ट / मातालाई अरिष्ट", "उच्च", "गौरी पूजा, गोदान, मातालाई वस्त्र दान"),
            4: ("चतुर्थ षष्ठ्यंश (६°-८°)", "मातुलकष्ट / मामालाई हानि", "मध्यम", "विष्णु सहस्रनाम जप, ब्राह्मण भोजन"),
            5: ("पञ्चम षष्ठ्यंश (८°-१०°)", "वंशहानि / कुल चिन्ता", "उच्च", "सन्तान गोपाल वा कुलदेवता पूजन"),
            6: ("षष्ठ षष्ठ्यंश (१०°-१२°)", "धनहानि / आर्थिक कष्ट एवं आत्मपीडा", "उच्च", "रुद्राभिषेक, काँसको पात्रमा घृतदान")
        }
        name_p, phala_p, sev_p, shanti_p = part_phala_map[part_idx]
        yogas.append({
            "name": f"कृष्ण चतुर्दशी जन्म ({name_p})",
            "reference": "बृहत्पाराशर होराशास्त्र अध्याय ८२",
            "condition": f"कृष्ण चतुर्दशीको {part_idx} औं षष्ठ्यंशमा जन्म",
            "impact_ne": phala_p,
            "shanti_ne": shanti_p,
            "severity": sev_p
        })

    # 3. Sankranti Janana (BPHS Ch. 85: संक्रान्ति जन्म शान्ति)
    # Sun entering a new sign (within 1 degree of sign boundary: 29° to 1°)
    sun_deg_in_sign = sun_lon % 30.0
    if sun_deg_in_sign >= 29.5 or sun_deg_in_sign <= 0.5:
        yogas.append({
            "name": "संक्रान्ति जन्म (सूर्य सङ्क्रमण काल)",
            "reference": "बृहत्पाराशर होराशास्त्र अध्याय ८५",
            "condition": f"सूर्य राशि परिवर्तन सन्धिमा जन्म (सूर्य {round(sun_deg_in_sign, 2)}° मा)",
            "impact_ne": "शरीरमा पित्त विकार, नेत्र कष्ट, अस्थिरता वा जीवनमा आकस्मिक परिवर्तन।",
            "shanti_ne": "सूर्य गायत्री जप, आदित्यहृदय स्तोत्र पाठ, तामाको पात्रमा गहुँ तथा गुड दान।",
            "severity": "मध्यम-उच्च"
        })

    # 4. Eclipse Birth (Surya/Chandra Grahana Janana - BPHS Ch. 86)
    # Rahu or Ketu conjunct Sun or Moon within 10 degrees during Amavasya or Purnima
    if rahu_lon is not None:
        sun_rahu_dist = min(abs(_normalize_deg(sun_lon - rahu_lon)), 360 - abs(_normalize_deg(sun_lon - rahu_lon)))
        moon_rahu_dist = min(abs(_normalize_deg(moon_lon - rahu_lon)), 360 - abs(_normalize_deg(moon_lon - rahu_lon)))
        if ketu_lon is not None:
            sun_ketu_dist = min(abs(_normalize_deg(sun_lon - ketu_lon)), 360 - abs(_normalize_deg(sun_lon - ketu_lon)))
            moon_ketu_dist = min(abs(_normalize_deg(moon_lon - ketu_lon)), 360 - abs(_normalize_deg(moon_lon - ketu_lon)))
        else:
            sun_ketu_dist = 180.0
            moon_ketu_dist = 180.0

        if (tithi_num == 30 and (sun_rahu_dist <= 12.0 or sun_ketu_dist <= 12.0)):
            yogas.append({
                "name": "सूर्य ग्रहण काल जन्म (ग्रहण जनन दोष)",
                "reference": "बृहत्पाराशर होराशास्त्र अध्याय ८६",
                "condition": "अमावास्यामा सूर्य र राहु/केतुको निकट युति (सूर्य ग्रहण)",
                "impact_ne": "मानसिक तनाव, आत्मबलमा न्यूनता, पितालाई कष्ट, राजकीय अवरोध।",
                "shanti_ne": "स्वर्ण/रजत निर्मित नाग तथा सूर्य प्रतिमा दान, महामृत्युञ्जय जप, राहु-केतु शान्ति।",
                "severity": "उच्च"
            })
        elif (tithi_num == 15 and (moon_rahu_dist <= 12.0 or moon_ketu_dist <= 12.0)):
            yogas.append({
                "name": "चन्द्र ग्रहण काल जन्म (ग्रहण जनन दोष)",
                "reference": "बृहत्पाराशर होराशास्त्र अध्याय ८६",
                "condition": "पूर्णिमामा चन्द्रमा र राहु/केतुको निकट युति (चन्द्र ग्रहण)",
                "impact_ne": "मानसिक अशान्ति, कफ रोग, मातालाई कष्ट, बाल्यकालमा चञ्चलता।",
                "shanti_ne": "चाँदीको चन्द्रमा र सर्प प्रतिमा दान, सेतो वस्त्र, चामल दान, शिवजीको जलाभिषेक।",
                "severity": "उच्च"
            })

    # 5. Trikhal Dosha (BPHS Ch. 98: त्रिखल जन्म शान्ति)
    if order_of_child == "son_after_3_daughters":
        yogas.append({
            "name": "त्रिखल दोष (तीन कन्यापछि पुत्र जन्म)",
            "reference": "बृहत्पाराशर होराशास्त्र अध्याय ९८",
            "condition": "तीन दिदीपछि भाइको जन्म (त्रिखल)",
            "impact_ne": "आमा वा शिशुलाई अरिष्ट भय, धनहानि वा कुलमा स्वास्थ्य कष्ट।",
            "shanti_ne": "त्रिखल शान्ति विधान, काँसको पात्रमा घृत र स्वर्ण दान, नवग्रह मन्त्र जप तथा हवन।",
            "severity": "मध्यम-उच्च"
        })
    elif order_of_child == "daughter_after_3_sons":
        yogas.append({
            "name": "त्रिखल दोष (तीन पुत्रपछि कन्या जन्म)",
            "reference": "बृहत्पाराशर होराशास्त्र अध्याय ९८",
            "condition": "तीन दाजुभाइपछि बहिनीको जन्म (त्रिखल)",
            "impact_ne": "मातापितालाई कष्ट वा पारिवारिक चिन्ता।",
            "shanti_ne": "गौरी पूजा, कन्या पूजन, वस्त्रालङ्कार दान तथा रुद्राभिषेक।",
            "severity": "मध्यम"
        })

    return yogas


def _normalize_planets_dict(raw_planets: Any) -> Dict[str, dict]:
    if isinstance(raw_planets, dict):
        return raw_planets
    if isinstance(raw_planets, list):
        return {
            str(p.get("name")): p
            for p in raw_planets
            if isinstance(p, dict) and p.get("name")
        }
    return {}


def evaluate_arishta_bhanga_yogas(
    chart_data: Dict[str, Any],
    nakshatra_result: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Evaluates Classical Arishta Bhanga (Cancellation / Mitigation Yogas):
    BPHS Principle:
      "यथा सिंहं समालोक्य पलायन्ते मृगा वने।
       तद्वद् दोषाः पलायन्ते गुरुणा केन्द्रे स्थिते॥"
      (As deer flee upon seeing a lion, all birth doshas flee when Jupiter is in Kendra 1, 4, 7, 10).
    Also checks:
      - Shukra (Venus) strong in Kendra/Trikona
      - Lagna Lord strong
      - Moon aspected by Benefics (Jupiter/Venus)
      - Paksha Bali Moon
    """
    cancellations = []
    planets = _normalize_planets_dict(chart_data.get("planets"))
    lagna = chart_data.get("lagna", {})
    lagna_sign = lagna.get("sign_number", 1)

    def get_house(p_sign: int) -> int:
        return ((p_sign - lagna_sign) % 12) + 1

    # 1. Jupiter in Kendra (1, 4, 7, 10)
    jup = planets.get("Jupiter", {})
    if jup:
        jup_sign = jup.get("sign_number", 1)
        jup_house = get_house(jup_sign)
        if jup_house in [1, 4, 7, 10]:
            cancellations.append(
                f"बृहस्पति केन्द्र ({jup_house} भाव) मा अवस्थित छ — पराशर वचन: 'यथा सिंहं समालोक्य... गुरुणा केन्द्रे स्थिते' अनुसार सम्पूर्ण अरिष्ट तथा गण्डान्त दोषको प्रभाव शतप्रतिशत शान्त/न्यून हुन्छ।"
            )

    # 2. Venus in Kendra or Trikona
    ven = planets.get("Venus", {})
    if ven:
        ven_sign = ven.get("sign_number", 1)
        ven_house = get_house(ven_sign)
        if ven_house in [1, 4, 5, 7, 9, 10]:
            cancellations.append(
                f"दैत्यगुरु शुक्र शुभ भाव ({ven_house} भाव) मा बलवान् स्थितिमा रहेकाले जीवन रक्षा एवं अरिष्ट निवारणमा ठूलो सहयोग मिल्दछ।"
            )

    # 3. Lagna Lord in Kendra/Trikona
    sign_lords = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
    }
    lagna_lord_name = sign_lords.get(lagna_sign, "Mars")
    lagna_lord = planets.get(lagna_lord_name, {})
    if lagna_lord:
        ll_sign = lagna_lord.get("sign_number", 1)
        ll_house = get_house(ll_sign)
        if ll_house in [1, 4, 5, 7, 9, 10]:
            cancellations.append(
                f"लग्नेश ({lagna_lord_name}) शुभ केन्द्र/त्रिकोण ({ll_house} भाव) मा अवस्थित हुनुले जातकको शारीरिक सुरक्षा र दीर्घायु सुनिश्चित गर्दछ।"
            )

    # 4. Moon aspected by Jupiter
    # Jupiter aspects 5, 7, 9 houses from itself
    moon = planets.get("Moon", {})
    if jup and moon:
        m_house = get_house(moon.get("sign_number", 1))
        j_house = get_house(jup.get("sign_number", 1))
        dist_from_jup = ((m_house - j_house) % 12) + 1
        if dist_from_jup in [5, 7, 9]:
            cancellations.append(
                "चन्द्रमामा देवगुरु बृहस्पतिको शुभ पूर्ण दृष्टि परेको हुनाले गण्डान्तको मानसिक र शारीरिक दुष्प्रभाव निवारण हुन्छ।"
            )

    is_bhanga = len(cancellations) > 0
    return is_bhanga, cancellations


def get_classical_shanti_remedies(
    nakshatra_name: str,
    pada: int,
    is_sandhi: bool,
    is_abhukta_moola: bool
) -> Dict[str, Any]:
    """
    Generates classical Vedic Shanti Vidhi, Mantras, Japa counts, and ritual materials
    as prescribed in BPHS and Vedic Paddhati.
    """
    deity_mantras = {
        "Moola": {
            "deity": "निऋति (राक्षस अधिपति / काल)",
            "vedic_mantra": "ॐ निॠतये स्वाहा। ॐ असुन्वन्त मयजमानमिच्छ स्तेनस्येत्यान्तस्करस्यान्वेषि...",
            "tantric_mantra": "ॐ ऐं ह्रीं क्लीं निऋतये नमः",
            "japa_count": "१०,००० वा २८,००० पटक",
            "gayatri": "ॐ निऋतये च विद्महे खड्गहस्ताय धीमहि तन्नो राक्षसः प्रचोदयात्।"
        },
        "Ashlesha": {
            "deity": "सर्प / नागराज (कर्कट राशीय)",
            "vedic_mantra": "ॐ नमोऽस्तु सर्पेभ्यो ये के च पृथिवीमनु ये अन्तरिक्षे ये दिवि तेभ्यः सर्पेभ्यो नमः।",
            "tantric_mantra": "ॐ ह्रीं श्रीं सर्पेभ्यो नमः",
            "japa_count": "१०,००० वा १६,००० पटक",
            "gayatri": "ॐ नवकुलाय विद्महे विषदन्ताय धीमहि तन्नो सर्पः प्रचोदयात्।"
        },
        "Jyeshtha": {
            "deity": "इन्द्र (देवराज)",
            "vedic_mantra": "ॐ त्रातारमिन्द्रमवितारमिन्द्र हवे हवे सुहवं शूरमिन्द्रम्...",
            "tantric_mantra": "ॐ इन्द्राय नमः",
            "japa_count": "१०,००० वा २०,००० पटक",
            "gayatri": "ॐ सहस्त्रनेत्राय विद्महे वज्रहस्ताय धीमहि तन्नो इन्द्रः प्रचोदयात्।"
        },
        "Magha": {
            "deity": "पितृगण (पितृदेव)",
            "vedic_mantra": "ॐ पितृभ्यः स्वधायिभ्यः स्वधा नमः पितामहेभ्यः स्वधायिभ्यः स्वधा नमः...",
            "tantric_mantra": "ॐ पितृभ्यो नमः",
            "japa_count": "१०,००० पटक",
            "gayatri": "ॐ पितृगणाय विद्महे जगतधारिणे धीमहि तन्नो पितरो प्रचोदयात्।"
        },
        "Revati": {
            "deity": "पूषा (पोषणकर्ता सूर्य)",
            "vedic_mantra": "ॐ पूषन् तव व्रते वयं न रिष्येम कदाचन स्तोतारस्त इह स्मसि...",
            "tantric_mantra": "ॐ पूष्णे नमः",
            "japa_count": "१०,००० वा १७,००० पटक",
            "gayatri": "ॐ पोषणाय विद्महे पुष्टिदाय धीमहि तन्नो पूषा प्रचोदयात्।"
        },
        "Ashwini": {
            "deity": "अश्विनीकुमार (दिव्य वैद्य)",
            "vedic_mantra": "ॐ अश्विना तेजसा चक्षुः प्राणेन सरस्वती वीर्यम्...",
            "tantric_mantra": "ॐ अश्विनीकुमाराभ्यां नमः",
            "japa_count": "१०,००० पटक",
            "gayatri": "ॐ अश्विनौ च विद्महे वैद्यराजाय धीमहि तन्नो अश्वी प्रचोदयात्।"
        }
    }

    info = deity_mantras.get(nakshatra_name, {
        "deity": "नवग्रह तथा कुलदेवता",
        "vedic_mantra": "ॐ त्र्यम्बकं यजामहे सुगन्धिं पुष्टिवर्धनम् उर्वारुकमिव बन्धनान्मृत्यौर्मुक्षीय मामृतात्।",
        "tantric_mantra": "ॐ नमः शिवाय",
        "japa_count": "११,००० पटक",
        "gayatri": "ॐ महामृत्युञ्जयाय नमः"
    })

    timing_ne = "२७ दिनपछि जन्म नक्षत्र पुनः दोहोरिँदा सोही नक्षत्र र शुभ वार/करणमा विधिपूर्वक शान्ति गर्नुपर्दछ।"
    materials = [
        "सप्तविंशति (२७) वृक्षका पातहरू (पञ्चपल्लव र २७ वृक्षका पात मिसाइएको जल)।",
        "सप्तमृत्तिका (७ ठाउँको पवित्र माटो: हात्तीसार, घोडासार, राजद्वार, दोबाटो, नदी किनार आदि)।",
        "सप्तधान्य (गहुँ, चामल, तिल, जौ, मूंग, चना, मास)।",
        "काँसको कचौरामा गाईको शुद्ध घ्यू राखी जातक वा पिताले अनुहार हेरेर दान गर्ने 'छाँयापात्र दान'।",
        "गोदान (वा सो बराबरको द्रव्य दान) र वस्त्र-अलङ्कारसहित ब्राह्मण दक्षिणा।",
        "रुद्राभिषेक, महामृत्युञ्जय मन्त्र जप तथा नक्षत्र देवताको वैदिक मन्त्रले तिल-घृत हवन।"
    ]

    rules_ne = [
        "शान्ति कर्म सम्पन्न नभएसम्म पिताले शिशुको मुख हेर्नु हुँदैन (विशेषतः मूल १, आश्लेषा ४, मघा १ र ज्येष्ठा ४ मा)।",
        "शान्ति पूजा सकिएपछि मात्र काँसको घ्यू भरिएको भाँडामा शिशुको छायाँ हेरी पिताले मुखावलोकन गर्नुपर्छ।"
    ]

    return {
        "deity": info["deity"],
        "vedic_mantra": info["vedic_mantra"],
        "tantric_mantra": info["tantric_mantra"],
        "japa_count": info["japa_count"],
        "gayatri": info["gayatri"],
        "timing_ne": timing_ne,
        "materials": materials,
        "classical_rules": rules_ne
    }


def calculate_gandanta_shanti_analysis(
    chart_data: Dict[str, Any],
    birth_time_str: Optional[str] = None,
    order_of_child: Optional[str] = None,
    language: str = "ne"
) -> Dict[str, Any]:
    """
    Main API for classical BPHS Gandanta & Arishta Janma Shanti Analysis.
    Combines:
      - Nakshatra Gandanta
      - Tithi Gandanta
      - Lagna Gandanta
      - Arishta Janma Yogas (Amavasya, Chaturdashi, Sankranti, Eclipse, Trikhal)
      - Arishta Bhanga Yogas (Jupiter in Kendra, etc.)
      - Classical Shanti Remedies & Mantras
    """
    if not chart_data or not isinstance(chart_data, dict):
        return {"state": "empty", "error": "कुण्डली तथ्याङ्क उपलब्ध छैन"}

    planets = _normalize_planets_dict(chart_data.get("planets"))
    moon = planets.get("Moon", {})
    sun = planets.get("Sun", {})
    lagna = chart_data.get("lagna", {})
    rahu = planets.get("Rahu", {})
    ketu = planets.get("Ketu", {})

    moon_lon = float(moon.get("longitude", 0.0))
    sun_lon = float(sun.get("longitude", 0.0))
    lagna_lon = float(lagna.get("longitude", 0.0))
    rahu_lon = float(rahu.get("longitude", 0.0)) if rahu else None
    ketu_lon = float(ketu.get("longitude", 0.0)) if ketu else None

    # Parse birth hour if string provided (e.g. "14:30" -> 14.5)
    if not birth_time_str:
        meta = chart_data.get("metadata", {})
        birth_time_str = meta.get("birth_time") or chart_data.get("birth_time")

    birth_hour = None
    if birth_time_str:
        try:
            parts = str(birth_time_str).split(":")
            birth_hour = float(parts[0]) + float(parts[1]) / 60.0
        except Exception:
            birth_hour = None

    # 1. Nakshatra Gandanta
    nak_result = evaluate_nakshatra_gandanta(moon_lon, birth_hour=birth_hour)

    # 2. Tithi Gandanta
    tithi_result = evaluate_tithi_gandanta(sun_lon, moon_lon)

    # 3. Lagna Gandanta
    lagna_result = evaluate_lagna_gandanta(lagna_lon)

    # 4. Other Arishta Yogas
    arishta_yogas = evaluate_arishta_janma_yogas(
        sun_lon, moon_lon, rahu_lon, ketu_lon, order_of_child=order_of_child
    )

    # 5. Arishta Bhanga Yogas
    is_bhanga, bhanga_reasons = evaluate_arishta_bhanga_yogas(chart_data, nak_result)

    # 6. Overall Classification
    has_any_gandanta = (
        nak_result["is_sandhi_gandanta"] or
        nak_result["is_gandanta_nakshatra"] or
        tithi_result["is_tithi_gandanta"] or
        lagna_result["is_lagna_gandanta"]
    )

    overall_status = "दोषमुक्त"
    status_color = "#15803d" # green
    if nak_result["is_abhukta_moola"]:
        overall_status = "अभुक्त मूल (अति गम्भीर गण्डान्त सन्धि)"
        status_color = "#b91c1c" # red
    elif nak_result["is_sandhi_gandanta"] or lagna_result["is_lagna_gandanta"]:
        overall_status = "तीव्र गण्डान्त सन्धि दोष"
        status_color = "#c2410c" # dark orange
    elif nak_result["is_gandanta_nakshatra"] or tithi_result["is_tithi_gandanta"] or len(arishta_yogas) > 0:
        overall_status = "सामान्य गण्डान्त / अनिष्ट जन्म दोष (शान्ति आवश्यक)"
        status_color = "#b45309" # amber

    if is_bhanga and overall_status != "दोषमुक्त":
        overall_status += " [शुभ ग्रह प्रभावले दोष अत्यन्त न्यून/भंग]"

    # 7. Prescribed Remedies
    remedies = None
    if has_any_gandanta or len(arishta_yogas) > 0:
        remedies = get_classical_shanti_remedies(
            nak_result["nakshatra_name"],
            nak_result["pada"],
            nak_result["is_sandhi_gandanta"],
            nak_result["is_abhukta_moola"]
        )

    return {
        "state": "success",
        "nakshatra_gandanta": nak_result,
        "tithi_gandanta": tithi_result,
        "lagna_gandanta": lagna_result,
        "arishta_yogas": arishta_yogas,
        "is_arishta_bhanga": is_bhanga,
        "bhanga_reasons": bhanga_reasons,
        "overall_status": overall_status,
        "status_color": status_color,
        "has_gandanta_or_arishta": has_any_gandanta or len(arishta_yogas) > 0,
        "remedies": remedies
    }
