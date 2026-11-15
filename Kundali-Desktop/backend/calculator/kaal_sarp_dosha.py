"""
Kaal Sarp Dosha (KSD) Detection Engine
======================================

Classical Jyotish concept: Kaal Sarp Dosha forms when ALL seven visible
grahas (Sun..Saturn) are hemmed between Rahu and Ketu on one side of the
Rahu-Ketu axis. The "serpent of time" (Rahu = head, Ketu = tail) wraps
the planets and can delay, obstruct, or frustrate the affairs ruled by
the houses in which the planets sit.

This engine detects:

1. Whether KSD is present (all grahas between Rahu and Ketu).
2. Which of the 12 classical KSD types applies (Anant, Kulik, Vasuki,
   Shankhpal, Padma, Mahapadma, Takshak, Karkotak, Shankhachur, Ghatak,
   Vishdhar, Sheshnag).
3. The affected houses and planets, with per-house narrative.
4. Severity (mild / moderate / severe / very severe) based on classical
   strengthening/weakening factors.
5. Remedies (worship, Rudrabhishek, mantra, charity) in both languages.

Input contract (matches the backend `planets` payload):
    planets: List[Dict] each with at least
        "name": "Sun"|"Moon"|"Mars"|"Mercury"|"Jupiter"|"Venus"|"Saturn"|"Rahu"|"Ketu"
        "sign_number": 1..12
        "longitude_in_sign": float (degrees 0..30)  [optional but recommended]
        "sidereal_longitude": float (0..360)         [optional but recommended]
        "house": int 1..12                           [optional for per-house effects]
    lagna_sign: int 1..12

Output: a dictionary usable directly by the frontend report component.
"""
from typing import Dict, List, Optional, Any

from .planet_names import get_planet_label

# ─────────────────────────────────────────────
# Constants & Lookup Tables
# ─────────────────────────────────────────────

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NODE_NAMES = {"Rahu": "Rahu", "Ketu": "Ketu"}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGNS_NE = [
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन",
]

# The 12 classical KSD types. The key is the nakshatra (or pada-range)
# occupied by Rahu at birth. `pada_start`/`pada_end` refer to Rahu's
# nakshatra pada (1-based). When Rahu is exactly on a nakshatra boundary,
# the earlier (lower) pada is used for classification.
KSD_TYPES: Dict[str, Dict[str, Any]] = {
    "anant": {
        "en": "Anant Kaal Sarp Dosha",
        "ne": "अनन्त कालसर्प दोष",
        "meaning_en": "Rahu in Revati nakshatra — the endless serpent.",
        "meaning_ne": "राहु रेवती नक्षत्रमा — अनन्त सर्प।",
        "nakshatras": ["Revati"],
    },
    "kulik": {
        "en": "Kulik Kaal Sarp Dosha",
        "ne": "कुलिक कालसर्प दोष",
        "meaning_en": "Rahu in Ashlesha nakshatra — the most feared KSD.",
        "meaning_ne": "राहु आश्लेषा नक्षत्रमा — सबैभन्दा भयानक कालसर्प।",
        "nakshatras": ["Ashlesha"],
    },
    "vasuki": {
        "en": "Vasuki Kaal Sarp Dosha",
        "ne": "वासुकि कालसर्प दोष",
        "meaning_en": "Rahu in Pushya nakshatra.",
        "meaning_ne": "राहु पुष्य नक्षत्रमा।",
        "nakshatras": ["Pushya"],
    },
    "shankhpal": {
        "en": "Shankhpal Kaal Sarp Dosha",
        "ne": "शंखपाल कालसर्प दोष",
        "meaning_en": "Rahu in Punarvasu nakshatra.",
        "meaning_ne": "राहु पुनर्वसु नक्षत्रमा।",
        "nakshatras": ["Punarvasu"],
    },
    "padma": {
        "en": "Padma Kaal Sarp Dosha",
        "ne": "पद्म कालसर्प दोष",
        "meaning_en": "Rahu in Magha nakshatra.",
        "meaning_ne": "राहु मघा नक्षत्रमा।",
        "nakshatras": ["Magha"],
    },
    "mahapadma": {
        "en": "Mahapadma Kaal Sarp Dosha",
        "ne": "महापद्म कालसर्प दोष",
        "meaning_en": "Rahu in Ardra nakshatra.",
        "meaning_ne": "राहु आर्द्रा नक्षत्रमा।",
        "nakshatras": ["Ardra"],
    },
    "takshak": {
        "en": "Takshak Kaal Sarp Dosha",
        "ne": "तक्षक कालसर्प दोष",
        "meaning_en": "Rahu in Anuradha nakshatra.",
        "meaning_ne": "राहु अनुराधा नक्षत्रमा।",
        "nakshatras": ["Anuradha"],
    },
    "karkotak": {
        "en": "Karkotak Kaal Sarp Dosha",
        "ne": "कार्कोटक कालसर्प दोष",
        "meaning_en": "Rahu in Shatabhisha nakshatra.",
        "meaning_ne": "राहु शतभिषा नक्षत्रमा।",
        "nakshatras": ["Shatabhisha"],
    },
    "shankhachur": {
        "en": "Shankhachur Kaal Sarp Dosha",
        "ne": "शंखचूड़ कालसर्प दोष",
        "meaning_en": "Rahu in Dhanishta nakshatra.",
        "meaning_ne": "राहु धनिष्ठा नक्षत्रमा।",
        "nakshatras": ["Dhanishta"],
    },
    "ghatak": {
        "en": "Ghatak Kaal Sarp Dosha",
        "ne": "घातक कालसर्प दोष",
        "meaning_en": "Rahu in Jyeshtha nakshatra.",
        "meaning_ne": "राहु ज्येष्ठा नक्षत्रमा।",
        "nakshatras": ["Jyeshtha"],
    },
    "vishdhar": {
        "en": "Vishdhar Kaal Sarp Dosha",
        "ne": "विषधर कालसर्प दोष",
        "meaning_en": "Rahu in Mula nakshatra.",
        "meaning_ne": "राहु मूल नक्षत्रमा।",
        "nakshatras": ["Mula"],
    },
    "sheshnag": {
        "en": "Sheshnag Kaal Sarp Dosha",
        "ne": "शेषनाग कालसर्प दोष",
        "meaning_en": "Rahu in Ashwini nakshatra.",
        "meaning_ne": "राहु अश्विनी नक्षत्रमा।",
        "nakshatras": ["Ashwini"],
    },
}

# Nakshatra metadata: 27 nakshatras, each 13°20′ of zodiacal longitude.
# nakshatra_number 0-based; start_longitude is sidereal zodiac position of nakshatra start.
NAKSHATRAS: List[Dict[str, Any]] = [
    {"name": "Ashwini",      "lord": "Ketu",   "start": 0.0},
    {"name": "Bharani",      "lord": "Venus",  "start": 13.333333},
    {"name": "Krittika",     "lord": "Sun",    "start": 26.666667},
    {"name": "Rohini",       "lord": "Moon",   "start": 40.0},
    {"name": "Mrigashira",   "lord": "Mars",   "start": 53.333333},
    {"name": "Ardra",        "lord": "Rahu",   "start": 66.666667},
    {"name": "Punarvasu",    "lord": "Jupiter","start": 80.0},
    {"name": "Pushya",       "lord": "Saturn", "start": 93.333333},
    {"name": "Ashlesha",     "lord": "Mercury","start": 106.666667},
    {"name": "Magha",        "lord": "Ketu",   "start": 120.0},
    {"name": "Purva Phalguni","lord": "Venus", "start": 133.333333},
    {"name": "Uttara Phalguni","lord": "Sun",  "start": 146.666667},
    {"name": "Hasta",        "lord": "Moon",   "start": 160.0},
    {"name": "Chitra",       "lord": "Mars",   "start": 173.333333},
    {"name": "Swati",        "lord": "Rahu",   "start": 186.666667},
    {"name": "Vishakha",     "lord": "Jupiter","start": 200.0},
    {"name": "Anuradha",     "lord": "Saturn", "start": 213.333333},
    {"name": "Jyeshtha",     "lord": "Mercury","start": 226.666667},
    {"name": "Mula",         "lord": "Ketu",   "start": 240.0},
    {"name": "Purva Ashadha","lord": "Venus",  "start": 253.333333},
    {"name": "Uttara Ashadha","lord": "Sun",   "start": 266.666667},
    {"name": "Shravana",     "lord": "Moon",   "start": 280.0},
    {"name": "Dhanishta",    "lord": "Mars",   "start": 293.333333},
    {"name": "Shatabhisha",  "lord": "Rahu",   "start": 306.666667},
    {"name": "Purva Bhadrapada","lord": "Jupiter","start": 320.0},
    {"name": "Uttara Bhadrapada","lord": "Saturn","start": 333.333333},
    {"name": "Revati",       "lord": "Mercury","start": 346.666667},
]

# Map KSD type key → the nakshatra(s) that trigger it.
TYPE_TO_NAKSHATRA: Dict[str, List[str]] = {k: v["nakshatras"] for k, v in KSD_TYPES.items()}
NAKSHATRA_TO_TYPE: Dict[str, str] = {}
for _type_key, _names in TYPE_TO_NAKSHATRA.items():
    for _n in _names:
        NAKSHATRA_TO_TYPE[_n] = _type_key

# Houses ruled by each graha (karakas / significations).
HOUSE_SIGNIFICATIONS: Dict[int, Dict[str, str]] = {
    1:  {"en": "Self, body, personality, life path", "ne": "स्वयं, शरीर, व्यक्तित्व, जीवन मार्ग"},
    2:  {"en": "Wealth, family, speech, resources", "ne": "धन, परिवार, वाणी, साधन"},
    3:  {"en": "Courage, siblings, communication, effort", "ne": "साहस, भाइबहिनी, संवाद, प्रयास"},
    4:  {"en": "Home, mother, property, peace of mind", "ne": "घर, आमा, सम्पत्ति, मानसिक शान्ति"},
    5:  {"en": "Intelligence, children, education, romance", "ne": "बुद्धि, सन्तान, शिक्षा, प्रेम"},
    6:  {"en": "Health, debts, enemies, service", "ne": "स्वास्थ्य, ऋण, शत्रु, सेवा"},
    7:  {"en": "Marriage, partnership, business, spouse", "ne": "विवाह, साझेदारी, व्यापार, जीवनसाथी"},
    8:  {"en": "Longevity, transformation, inheritance, occult", "ne": "आयु, रूपान्तरण, पैतृक सम्पत्ति, गूढ विद्या"},
    9:  {"en": "Fortune, dharma, father, higher learning", "ne": "भाग्य, धर्म, पिता, उच्च शिक्षा"},
    10: {"en": "Career, profession, status, authority", "ne": "करियर, पेशा, प्रतिष्ठा, अधिकार"},
    11: {"en": "Gains, income, friendships, fulfilment", "ne": "लाभ, आम्दानी, मित्रता, सन्तुष्टि"},
    12: {"en": "Losses, expenses, isolation, moksha", "ne": "हानि, खर्च, एकान्त, मोक्ष"},
}

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────

def _get_planet(planets: List[Dict], name: str) -> Optional[Dict]:
    """Return the planet dict by name (case-insensitive)."""
    for p in planets:
        if p.get("name", "").lower() == name.lower():
            return p
    return None


def _sign_of(planet: Optional[Dict]) -> Optional[int]:
    if not planet:
        return None
    sign = planet.get("sign_number")
    if sign is not None:
        return int(sign)
    return None


def _longitude_of(planet: Optional[Dict]) -> Optional[float]:
    """Prefer sidereal_longitude; fall back to sign+longitude_in_sign."""
    if not planet:
        return None
    sid = planet.get("sidereal_longitude")
    if sid is not None:
        return float(sid)
    sign = _sign_of(planet)
    deg_in_sign = planet.get("longitude_in_sign")
    if sign is not None and deg_in_sign is not None:
        return ((int(sign) - 1) * 30.0) + float(deg_in_sign)
    return None


def _house_of(planet: Optional[Dict]) -> Optional[int]:
    if not planet:
        return None
    house = planet.get("house")
    if house is not None:
        return int(house)
    return None


def _normalize_longitude(lon: float) -> float:
    """Normalise to 0..360."""
    lon = lon % 360.0
    if lon < 0:
        lon += 360.0
    return lon


def _get_nakshatra(sidereal_longitude: float) -> Dict[str, Any]:
    """Return nakshatra info {index, name, pada, lord} for a sidereal longitude."""
    lon = _normalize_longitude(sidereal_longitude)
    idx = int(lon // (360.0 / 27.0)) % 27
    naks = NAKSHATRAS[idx]
    pada = int((lon % (360.0 / 27.0)) // (360.0 / 27.0 / 4.0)) + 1
    return {
        "index": idx,
        "name": naks["name"],
        "pada": pada,
        "lord": naks["lord"],
        "longitude": round(lon, 4),
    }


def _detect_ksd_type(rahu_longitude: float) -> Dict[str, Any]:
    """Classify the KSD type from Rahu's nakshatra."""
    naks = _get_nakshatra(rahu_longitude)
    type_key = NAKSHATRA_TO_TYPE.get(naks["name"], "anant")
    info = KSD_TYPES[type_key]
    return {
        "type_key": type_key,
        "name_en": info["en"],
        "name_ne": info["ne"],
        "meaning_en": info["meaning_en"],
        "meaning_ne": info["meaning_ne"],
        "rahu_nakshatra": naks["name"],
        "rahu_pada": naks["pada"],
        "rahu_longitude": naks["longitude"],
    }


def _is_between(a_lon: float, b_lon: float, x_lon: float) -> bool:
    """
    Return True if x_lon lies on the forward arc from a_lon to b_lon in
    zodiacal order (inclusive of endpoints for safety).
    """
    a_lon = _normalize_longitude(a_lon)
    b_lon = _normalize_longitude(b_lon)
    x_lon = _normalize_longitude(x_lon)
    if a_lon == b_lon:
        # Degenerate axis — treat as impossible for KSD, return False.
        return False
    span = (b_lon - a_lon) % 360.0
    if span <= 180.0:
        # a → b forward arc (covers exact 180° node axis)
        return (x_lon - a_lon) % 360.0 <= span
    else:
        # b → a forward arc (wraps through 0)
        span_rev = (a_lon - b_lon) % 360.0
        return (x_lon - b_lon) % 360.0 <= span_rev


def _axis_arc_contains(rahu_lon: float, ketu_lon: float, target_lon: float) -> bool:
    """
    Classical KSD definition: all seven grahas lie on the 180° arc from Rahu
    to Ketu in zodiacal order (Rahu -> Ketu forward direction). Since Rahu
    and Ketu are always exactly opposite, this is equivalent to requiring
    0 < delta < 180 where delta = (target - rahu) mod 360. Grahas exactly
    on a node (delta == 0) are excluded.
    """
    delta = (_normalize_longitude(target_lon) - _normalize_longitude(rahu_lon)) % 360.0
    return 0.0 < delta < 180.0


# ─────────────────────────────────────────────
# Severity & Remedies
# ─────────────────────────────────────────────

def _severity(affected_houses: List[int], planets_in_ksd: List[Dict], type_key: str) -> Dict[str, Any]:
    """
    Classical severity weighting:
      - Kulik, Ghatak, Shankhachur are the most feared types.
      - Affected Kendra (1/4/7/10) and Trikona (1/5/9) houses weigh heavier.
      - Kendra with its own lord afflicted is more serious.
    """
    kendra = {1, 4, 7, 10}
    trikona = {1, 5, 9}
    dusthana = {6, 8, 12}

    high_types = {"kulik", "ghatak", "shankhachur", "anant"}
    score = 0
    score += 3 if type_key in high_types else 0
    for h in affected_houses:
        if h in kendra:
            score += 2
        elif h in trikona:
            score += 2
        elif h in dusthana:
            score += 1
        else:
            score += 1

    # 5th house affliction (children) is traditionally heavy.
    if 5 in affected_houses:
        score += 1

    if score >= 9:
        label_en, label_ne, rank = "Very Severe", "अति गम्भीर", 4
    elif score >= 7:
        label_en, label_ne, rank = "Severe", "गम्भीर", 3
    elif score >= 5:
        label_en, label_ne, rank = "Moderate", "मध्यम", 2
    else:
        label_en, label_ne, rank = "Mild", "हल्का", 1

    return {
        "rank": rank,
        "label_en": label_en,
        "label_ne": label_ne,
        "score": score,
        "factors": {
            "type_weight": 3 if type_key in high_types else 0,
            "kendra_trikona_houses": len([h for h in affected_houses if h in kendra or h in trikona]),
            "dusthana_houses": len([h for h in affected_houses if h in dusthana]),
        },
    }


REMEDIES: List[Dict[str, str]] = [
    {
        "en": "Worship Lord Shiva and perform Rudrabhishek on Mondays, especially during Shravan month.",
        "ne": "सोमबार, विशेष गरी श्रावण महिनामा, भगवान शिवको पूजा र रुद्राभिषेक गर्नुहोस्।",
    },
    {
        "en": "Chant the Rahu mantra 'Om Ram Rahave Namah' (108 times daily) and the Ketu mantra 'Om Kem Ketave Namah'.",
        "ne": "दैनिक १०८ पटक 'ॐ रां राहवे नमः' र 'ॐ कें केतवे नमः' मन्त्र जप गर्नुहोस्।",
    },
    {
        "en": "Offer prayers to Nag Devta and donate food, clothes, and blankets to the needy.",
        "ne": "नाग देवताको पूजा गर्नुहोस् र खाद्यान्न, कपडा, कम्बल दान गर्नुहोस्।",
    },
    {
        "en": "On Saturdays, visit a temple of Lord Hanuman and offer oil; keep fast or perform charity.",
        "ne": "शनिबार हनुमान मन्दिर गई तेल चढाउनुहोस्; व्रत वा दान गर्नुहोस्।",
    },
    {
        "en": "Wear or keep a Nag (serpent) motif or snake-related Yantra only after expert guidance.",
        "ne": "विशेषज्ञको सल्लाहपछि मात्र नाग मोटिफ वा सर्प-सम्बन्धी यन्त्र धारण गर्नुहोस्।",
    },
    {
        "en": "Meditate, maintain ethical conduct, and avoid unnecessary fear — KSD results depend on overall chart strength and dasha.",
        "ne": "ध्यान गर्नुहोस्, सदाचार पालन गर्नुहोस्, अनावश्यक भयबाट बच्नुहोस् — कालसर्पको फल समग्र कुण्डली बल र दशामा निर्भर हुन्छ।",
    },
]

# ─────────────────────────────────────────────
# Main API
# ─────────────────────────────────────────────

def calculate_kaal_sarp_dosha(
    planets: List[Dict],
    lagna_sign: Optional[int] = 1,
    language: str = "ne",
) -> Dict[str, Any]:
    """
    Detect Kaal Sarp Dosha for a natal chart.

    Args:
        planets: list of planet dicts (see module docstring).
        lagna_sign: 1..12 sign number of the ascendant.
        language: "ne" or "en" for the headline narrative (data is bilingual).

    Returns:
        dict with keys:
          present (bool), rahu, ketu, grahas_in_ksd, grahas_outside,
          type, severity, affected_houses, house_details,
          narrative_en, narrative_ne, remedies, references, disclaimer.
    """
    rahu = _get_planet(planets, "Rahu")
    ketu = _get_planet(planets, "Ketu")
    rahu_lon = _longitude_of(rahu)
    ketu_lon = _longitude_of(ketu)

    result: Dict[str, Any] = {
        "present": False,
        "rahu": None,
        "ketu": None,
        "grahas_in_ksd": [],
        "grahas_outside": [],
        "type": None,
        "severity": None,
        "affected_houses": [],
        "house_details": [],
        "narrative_en": "",
        "narrative_ne": "",
        "remedies": REMEDIES,
        "references": [
            "BPHS — Brihat Parashara Hora Shastra",
            "Saravali — Kalidas",
            "Phala Deepika",
        ],
        "disclaimer": {
            "en": "Kaal Sarp Dosha is one of many factors in a chart. A favourable lagna, strong planets, and good dasha can reduce its effects. Please consult a qualified astrologer for a complete assessment.",
            "ne": "कालसर्प दोष कुण्डलीको धेरै पक्षमध्ये एक मात्र हो। शुभ लग्न, बलियो ग्रह र राम्रो दशाले यसको प्रभाव घटाउन सक्छ। पूर्ण मूल्याङ्कनका लागि योग्य ज्योतिषीसँग परामर्श गर्नुहोस्।",
        },
    }

    if rahu_lon is None or ketu_lon is None:
        result["narrative_en"] = "Rahu/Ketu positions are unavailable; Kaal Sarp Dosha cannot be computed."
        result["narrative_ne"] = "राहु/केतुको स्थिति उपलब्ध छैन; कालसर्प दोष गणना गर्न सकिँदैन।"
        return result

    # Attach node details.
    result["rahu"] = {
        "name": "Rahu",
        "sign_number": _sign_of(rahu),
        "longitude": round(rahu_lon, 4),
        "nakshatra": _get_nakshatra(rahu_lon),
    }
    result["ketu"] = {
        "name": "Ketu",
        "sign_number": _sign_of(ketu),
        "longitude": round(ketu_lon, 4),
        "nakshatra": _get_nakshatra(ketu_lon),
    }

    # Determine which grahas lie between Rahu and Ketu (forward arc).
    lagna_sign = int(lagna_sign or 1)
    grahas_in: List[Dict] = []
    grahas_out: List[Dict] = []
    for gname in GRAHAS:
        g = _get_planet(planets, gname)
        if g is None:
            continue
        glon = _longitude_of(g)
        if glon is None:
            continue
        gsign = _sign_of(g)
        ghouse = _house_of(g)
        if ghouse is None and gsign is not None:
            # Whole-sign house fallback when explicit house is missing.
            ghouse = ((int(gsign) - int(lagna_sign)) % 12) + 1
        entry = {
            "name": gname,
            "sign_number": gsign,
            "longitude": round(glon, 4),
            "house": ghouse,
            "nakshatra": _get_nakshatra(glon),
        }
        if _axis_arc_contains(rahu_lon, ketu_lon, glon):
            grahas_in.append(entry)
        else:
            grahas_out.append(entry)

    result["grahas_in_ksd"] = grahas_in
    result["grahas_outside"] = grahas_out

    # KSD present only when ALL seven grahas are between the nodes.
    if len(grahas_in) == 7:
        result["present"] = True
        # Classify type from Rahu nakshatra.
        result["type"] = _detect_ksd_type(rahu_lon)

        # Affected houses = houses occupied by the seven grahas (unique).
        affected_houses = sorted({g["house"] for g in grahas_in if g["house"]})
        result["affected_houses"] = affected_houses

        # Severity.
        result["severity"] = _severity(affected_houses, grahas_in, result["type"]["type_key"])

        # House details.
        house_details: List[Dict[str, Any]] = []
        for h in affected_houses:
            planets_here = [g["name"] for g in grahas_in if g["house"] == h]
            sig = HOUSE_SIGNIFICATIONS.get(h, {"en": "", "ne": ""})
            house_details.append({
                "house": h,
                "sign_number": ((int(lagna_sign) - 1 + h - 1) % 12) + 1,
                "planets": planets_here,
                "signification_en": sig["en"],
                "signification_ne": sig["ne"],
            })
        result["house_details"] = house_details

        # Narratives.
        type_name_en = result["type"]["name_en"]
        type_name_ne = result["type"]["name_ne"]
        severity_en = result["severity"]["label_en"]
        severity_ne = result["severity"]["label_ne"]
        affected_str = ", ".join(f"H{h}" for h in affected_houses)
        affected_str_ne = ", ".join(f"{h}औं" for h in affected_houses)

        result["narrative_en"] = (
            f"Your chart shows {type_name_en} ({severity_en}). All seven grahas are hemmed "
            f"between Rahu and Ketu, covering houses {affected_str}. These houses experience "
            "delays, obstacles, or cyclic ups and downs, but the effect varies with dasha and "
            "overall chart strength."
        )
        result["narrative_ne"] = (
            f"तपाईंको कुण्डलीमा {type_name_ne} ({severity_ne}) देखिन्छ। सबै सात ग्रह राहु र केतुको "
            f"बीचमा छन्, जसले {affected_str_ne} भावलाई असर गर्छ। यी भावहरूमा ढिलाइ, बाधा वा चक्रीय "
            "उतार-चढ़ाव आउन सक्छ, तर फल दशा र समग्र कुण्डली बलमा निर्भर गर्दछ।"
        )
    else:
        result["present"] = False
        outside_names = ", ".join(g["name"] for g in grahas_out)
        result["narrative_en"] = (
            f"No Kaal Sarp Dosha is present. {len(grahas_out)} of the seven grahas "
            f"({outside_names}) are outside the Rahu–Ketu axis, so the serpent does not "
            "hem all the planets."
        )
        result["narrative_ne"] = (
            f"कालसर्प दोष छैन। सात मध्ये {len(grahas_out)} ग्रह ({', '.join(_ne_name(g['name']) for g in grahas_out)}) "
            "राहु-केतु अक्ष बाहिर छन्, त्यसैले सर्पले सबै ग्रहलाई घेरेको छैन।"
        )

    return result


def _ne_name(name: str) -> str:
    """Nepali label for a planet name."""
    return get_planet_label(name, "ne")


# Public convenience
def detect(planets: List[Dict], lagna_sign: Optional[int] = 1, language: str = "ne") -> Dict[str, Any]:
    """Alias for calculate_kaal_sarp_dosha."""
    return calculate_kaal_sarp_dosha(planets, lagna_sign=lagna_sign, language=language)
