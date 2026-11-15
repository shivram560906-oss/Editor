# -*- coding: utf-8 -*-
"""
backend/calculator/constants.py

केन्द्रीय स्थिरांक तालिका — सबै Calculator Modules ले यहाँबाट Import गर्नुपर्छ।
सबै sign numbers 1-indexed छन् (1=मेष, ..., 12=मीन)।

Single source of truth for:
  - SIGN_LORDS
  - EXALTATION_SIGNS / DEBILITATION_SIGNS
  - OWN_SIGNS
  - NATURAL_BENEFICS / NATURAL_MALEFICS
  - PLANET_NAMES_NE / EN
  - SIGN_NAMES_NE / EN
"""

# ─────────────────────────────────────────────────────────────────────────────
# Sign Names (1-indexed: 1=Aries ... 12=Pisces)
# ─────────────────────────────────────────────────────────────────────────────

SIGN_NAMES_NE = {
    1: "मेष", 2: "वृष", 3: "मिथुन", 4: "कर्कट", 5: "सिंह", 6: "कन्या",
    7: "तुला", 8: "वृश्चिक", 9: "धनु", 10: "मकर", 11: "कुम्भ", 12: "मीन",
}

SIGN_NAMES_EN = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo",
    7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn",
    11: "Aquarius", 12: "Pisces",
}

# ─────────────────────────────────────────────────────────────────────────────
# Sign Lords / Rashi Swami (1-indexed)
# Standard BPHS / Parashari rulership
# ─────────────────────────────────────────────────────────────────────────────

SIGN_LORDS = {
    1: "Mars",     # मेष
    2: "Venus",    # वृष
    3: "Mercury",  # मिथुन
    4: "Moon",     # कर्कट
    5: "Sun",      # सिंह
    6: "Mercury",  # कन्या
    7: "Venus",    # तुला
    8: "Mars",     # वृश्चिक
    9: "Jupiter",  # धनु
    10: "Saturn",  # मकर
    11: "Saturn",  # कुम्भ
    12: "Jupiter", # मीन
}

# ─────────────────────────────────────────────────────────────────────────────
# Exaltation Signs (उच्च राशि) — 1-indexed, BPHS standard
# ─────────────────────────────────────────────────────────────────────────────

EXALTATION_SIGNS = {
    "Sun":     1,   # मेष
    "Moon":    2,   # वृष
    "Mars":    10,  # मकर
    "Mercury": 6,   # कन्या
    "Jupiter": 4,   # कर्कट
    "Venus":   12,  # मीन
    "Saturn":  7,   # तुला
    "Rahu":    3,   # मिथुन (Parashari traditional)
    "Ketu":    9,   # धनु
}

# ─────────────────────────────────────────────────────────────────────────────
# Debilitation Signs (नीच राशि) — 1-indexed
# ─────────────────────────────────────────────────────────────────────────────

DEBILITATION_SIGNS = {
    "Sun":     7,   # तुला
    "Moon":    8,   # वृश्चिक
    "Mars":    4,   # कर्कट
    "Mercury": 12,  # मीन
    "Jupiter": 10,  # मकर
    "Venus":   6,   # कन्या
    "Saturn":  1,   # मेष
    "Rahu":    9,   # धनु
    "Ketu":    3,   # मिथुन
}

# ─────────────────────────────────────────────────────────────────────────────
# Own Signs (स्वगृह) — 1-indexed
# ─────────────────────────────────────────────────────────────────────────────

OWN_SIGNS = {
    "Sun":     [5],
    "Moon":    [4],
    "Mars":    [1, 8],
    "Mercury": [3, 6],
    "Jupiter": [9, 12],
    "Venus":   [2, 7],
    "Saturn":  [10, 11],
}

# ─────────────────────────────────────────────────────────────────────────────
# Natural Benefics & Malefics
# ─────────────────────────────────────────────────────────────────────────────

NATURAL_BENEFICS = ["Moon", "Mercury", "Jupiter", "Venus"]
NATURAL_MALEFICS = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]

# ─────────────────────────────────────────────────────────────────────────────
# Planet Names — Nepali & English
# ─────────────────────────────────────────────────────────────────────────────

PLANET_NAMES_NE = {
    "Sun":     "सूर्य",
    "Moon":    "चन्द्र",
    "Mars":    "मङ्गल",
    "Mercury": "बुध",
    "Jupiter": "बृहस्पति",
    "Venus":   "शुक्र",
    "Saturn":  "शनि",
    "Rahu":    "राहु",
    "Ketu":    "केतु",
    "Lagna":   "लग्न",
}

PLANET_NAMES_EN = {
    "Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
    "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn",
    "Rahu": "Rahu", "Ketu": "Ketu",
}

# ─────────────────────────────────────────────────────────────────────────────
# House Classifications
# ─────────────────────────────────────────────────────────────────────────────

KENDRA_HOUSES   = [1, 4, 7, 10]   # केन्द्र भाव
TRIKONA_HOUSES  = [1, 5, 9]       # त्रिकोण भाव
DUSTHANA_HOUSES = [6, 8, 12]      # दुस्थान भाव
UPACHAYA_HOUSES = [3, 6, 10, 11]  # उपचय भाव

# ─────────────────────────────────────────────────────────────────────────────
# Parashari Special Aspects (special drishti beyond 7th)
# ─────────────────────────────────────────────────────────────────────────────

SPECIAL_ASPECTS = {
    "Mars":    [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn":  [3, 7, 10],
    "Rahu":    [5, 7, 9],
    "Ketu":    [5, 7, 9],
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────

def sign_lord(sign_1indexed: int) -> str:
    """Return the lord of a sign given 1-indexed sign number (1-12)."""
    return SIGN_LORDS.get(sign_1indexed, "Mars")


def sign_lord_from_0idx(sign_0indexed: int) -> str:
    """Return the lord of a sign given 0-indexed sign number (0-11)."""
    return SIGN_LORDS.get(sign_0indexed + 1, "Mars")


def is_exalted(planet_name: str, sign_1indexed: int) -> bool:
    """True if the planet is exalted in the given 1-indexed sign."""
    return EXALTATION_SIGNS.get(planet_name) == sign_1indexed


def is_debilitated(planet_name: str, sign_1indexed: int) -> bool:
    """True if the planet is debilitated in the given 1-indexed sign."""
    return DEBILITATION_SIGNS.get(planet_name) == sign_1indexed


def is_own_sign(planet_name: str, sign_1indexed: int) -> bool:
    """True if the planet is in its own sign (1-indexed)."""
    return sign_1indexed in OWN_SIGNS.get(planet_name, [])
