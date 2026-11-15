"""
backend/calculator/varga_analysis.py

बृहत् पाराशर होरा शास्त्र (BPHS) अनुसार वर्ग कुण्डली विश्लेषण।
प्रत्येक वर्ग कुण्डलीको लागि:
  - निष्कर्ष (एक वाक्य)
  - विस्तृत विश्लेषण (शुभ/अशुभ, समय, उपाय)
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .constants import SIGN_LORDS

# ─────────────────────────────────────────────────────────────────────────────
# Constants: BPHS Sign Properties
# ─────────────────────────────────────────────────────────────────────────────

SIGN_NAMES_NE = {
    1: "मेष", 2: "वृष", 3: "मिथुन", 4: "कर्क",
    5: "सिंह", 6: "कन्या", 7: "तुला", 8: "वृश्चिक",
    9: "धनु", 10: "मकर", 11: "कुम्भ", 12: "मीन"
}
SIGN_NATURE = {
    # (element, mobility, gender)
    1:  ("Agni", "Chara",    "M"),  2:  ("Prithvi", "Sthira",  "F"),
    3:  ("Vayu", "Dwiswabha","M"),  4:  ("Jal",    "Chara",    "F"),
    5:  ("Agni", "Sthira",   "M"),  6:  ("Prithvi","Dwiswabha","F"),
    7:  ("Vayu", "Chara",    "M"),  8:  ("Jal",    "Sthira",   "F"),
    9:  ("Agni", "Dwiswabha","M"),  10: ("Prithvi","Chara",    "F"),
    11: ("Vayu", "Sthira",   "M"),  12: ("Jal",    "Dwiswabha","F"),
}

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल",
    "Mercury": "बुध", "Jupiter": "गुरु", "Venus": "शुक्र",
    "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
}

# BPHS Exaltation / Debilitation
EXALTATION  = {"Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
                "Jupiter": 4, "Venus": 12, "Saturn": 7}
DEBILITATION = {"Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
                 "Jupiter": 10, "Venus": 6, "Saturn": 1}

# Natural benefics / malefics (BPHS)
NAT_BENEFICS  = {"Jupiter", "Venus", "Mercury", "Moon"}
NAT_MALEFICS  = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# BPHS Kendra, Trikona, Dusthana, Upachaya houses
KENDRA   = {1, 4, 7, 10}
TRIKONA  = {1, 5, 9}
DUSTHANA = {6, 8, 12}
UPACHAYA = {3, 6, 10, 11}

HOUSE_NAMES_NE = {
    1: "प्रथम भाव", 2: "द्वितीय भाव", 3: "तृतीय भाव", 4: "चतुर्थ भाव",
    5: "पञ्चम भाव", 6: "षष्ठ भाव", 7: "सप्तम भाव", 8: "अष्टम भाव",
    9: "नवम भाव", 10: "दशम भाव", 11: "एकादश भाव", 12: "द्वादश भाव"
}

# ─────────────────────────────────────────────────────────────────────────────
# Varga metadata: subject, positive indicators, negative indicators, remedies
# ─────────────────────────────────────────────────────────────────────────────
VARGA_META = {
    "D1": {
        "subject_ne": "शरीर, स्वास्थ्य, सामान्य जीवन, व्यक्तित्व",
        "key_houses": [1, 5, 9],
        "key_planets": ["Sun", "Moon", "Jupiter", "Lagna Lord"],
        "purpose_ne": "राशि कुण्डली जीवनको सम्पूर्ण पक्षको मूल दर्पण हो।",
    },
    "D2": {
        "subject_ne": "धन, सम्पत्ति, आर्थिक स्थिति, खाना-पिना",
        "key_houses": [2, 11],
        "key_planets": ["Jupiter", "Venus", "Moon"],
        "purpose_ne": "होरा कुण्डली धन सम्पदाको विश्लेषणका लागि प्रयोग गरिन्छ।",
    },
    "D3": {
        "subject_ne": "दाजुभाइ, साहस, पराक्रम, छोटो यात्रा",
        "key_houses": [3, 11],
        "key_planets": ["Mars", "Mercury"],
        "purpose_ne": "द्रेष्काण कुण्डली भाइबहिनी र साहसिकता देखाउँछ।",
    },
    "D4": {
        "subject_ne": "अचल सम्पत्ति, घर-जग्गा, वाहन, सुख",
        "key_houses": [4, 12],
        "key_planets": ["Moon", "Venus", "Mars"],
        "purpose_ne": "चतुर्थांश कुण्डली भूमि-भवन र स्थायी सम्पत्ति देखाउँछ।",
    },
    "D7": {
        "subject_ne": "सन्तान, वंश, प्रजनन क्षमता",
        "key_houses": [5, 9],
        "key_planets": ["Jupiter", "Moon"],
        "purpose_ne": "सप्तमांश कुण्डली सन्तान र वंश परम्पराको जानकारी दिन्छ।",
    },
    "D9": {
        "subject_ne": "भाग्य, धर्म, जीवनसाथी, आत्मशक्ति",
        "key_houses": [1, 7, 9],
        "key_planets": ["Jupiter", "Venus", "Sun"],
        "purpose_ne": "नवांश कुण्डली भाग्य र जीवनसाथीको मुख्य कारक हो।",
    },
    "D10": {
        "subject_ne": "कर्म, व्यवसाय, पद-प्रतिष्ठा, सामाजिक स्थान",
        "key_houses": [1, 10],
        "key_planets": ["Sun", "Saturn", "Mercury"],
        "purpose_ne": "दशमांश कुण्डली करियर र व्यावसायिक सफलता देखाउँछ।",
    },
    "D12": {
        "subject_ne": "माता-पिता, पूर्वज, वंश",
        "key_houses": [4, 9],
        "key_planets": ["Sun", "Moon", "Jupiter"],
        "purpose_ne": "द्वादशांश कुण्डली माता-पिता र पूर्वजको स्थितिको विश्लेषण गर्दछ।",
    },
    "D16": {
        "subject_ne": "वाहन, सुख-सुविधा, ऐश-आराम",
        "key_houses": [4, 1],
        "key_planets": ["Venus", "Moon"],
        "purpose_ne": "षोडशांश कुण्डली वाहन सुख र भौतिक आराम देखाउँछ।",
    },
    "D20": {
        "subject_ne": "आध्यात्मिक साधना, धर्म-कर्म, परमार्थ",
        "key_houses": [9, 12, 1],
        "key_planets": ["Jupiter", "Ketu", "Saturn"],
        "purpose_ne": "विंशांश कुण्डली आध्यात्मिक प्रगति र धार्मिक कार्यको विश्लेषण गर्दछ।",
    },
    "D24": {
        "subject_ne": "शिक्षा, ज्ञान, विद्या, बुद्धि",
        "key_houses": [4, 5, 9],
        "key_planets": ["Mercury", "Jupiter"],
        "purpose_ne": "चतुर्विंशांश कुण्डली शिक्षा र ज्ञानको विश्लेषण गर्दछ।",
    },
    "D27": {
        "subject_ne": "शारीरिक बल, मानसिक क्षमता, प्रतिरोध शक्ति",
        "key_houses": [1, 3, 6, 10],
        "key_planets": ["Mars", "Sun"],
        "purpose_ne": "सप्तविंशांश कुण्डली शारीरिक र मानसिक बल देखाउँछ।",
    },
    "D30": {
        "subject_ne": "दुर्भाग्य, संकट, रोग-व्याधि, शत्रु",
        "key_houses": [6, 8, 12],
        "key_planets": ["Saturn", "Mars", "Rahu", "Ketu"],
        "purpose_ne": "त्रिंशांश कुण्डली जीवनका कष्ट, रोग र विपत्तिको जानकारी दिन्छ।",
    },
    "D40": {
        "subject_ne": "मातृपक्ष, शुभ/अशुभ फल, आधारभूत भाग्य",
        "key_houses": [1, 4],
        "key_planets": ["Moon", "Venus"],
        "purpose_ne": "खवेदांश कुण्डली मातृपक्षीय शुभाशुभ प्रभावको विश्लेषण गर्दछ।",
    },
    "D45": {
        "subject_ne": "चरित्र, नैतिकता, पितृपक्ष, आचरण",
        "key_houses": [1, 9],
        "key_planets": ["Sun", "Saturn"],
        "purpose_ne": "अक्षवेदांश कुण्डली चरित्र र पितृपक्षीय प्रभावको विश्लेषण गर्दछ।",
    },
    "D60": {
        "subject_ne": "पूर्वजन्म कर्म, संचित कर्म, आत्मशक्ति",
        "key_houses": [1, 5, 9],
        "key_planets": ["Saturn", "Jupiter", "Ketu"],
        "purpose_ne": "षष्ट्यंश कुण्डली पूर्वजन्मका कर्म र आत्माको यात्राको विश्लेषण गर्दछ।",
    },
}

# BPHS Timing: Dasha planets and approximate ages
DASHA_PERIODS = {
    "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16,
    "Saturn": 19, "Mercury": 17, "Ketu": 7, "Venus": 20
}
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────
def _pname(name: str) -> str:
    return PLANET_NAMES_NE.get(name, name)

def _sname(sign: int) -> str:
    return SIGN_NAMES_NE.get(sign, str(sign))

def _lord(sign: int) -> str:
    return SIGN_LORDS.get(sign, "")

def _house_from_lagna(planet_sign: int, lagna_sign: int) -> int:
    return (planet_sign - lagna_sign) % 12 + 1

def _is_exalted(planet: str, sign: int) -> bool:
    return EXALTATION.get(planet) == sign

def _is_debilitated(planet: str, sign: int) -> bool:
    return DEBILITATION.get(planet) == sign

def _is_own_sign(planet: str, sign: int) -> bool:
    return SIGN_LORDS.get(sign) == planet

def _planet_strength(planet: str, sign: int) -> str:
    """Returns 'exalted', 'own', 'neutral', 'debilitated'"""
    if _is_exalted(planet, sign):    return "exalted"
    if _is_own_sign(planet, sign):   return "own"
    if _is_debilitated(planet, sign): return "debilitated"
    return "neutral"

def _get_planets_in_varga(chart_data: dict, varga_key: str) -> List[dict]:
    """Extract varga-specific planet positions from chart data.
    
    actual structure:
    chart_data["vargas"][key] = {"lagna": {...}, "planets": [{"sign_number": N, "name": ..., ...}]}
    Each planet already has: sign_number, house, sidereal_longitude, is_retrograde, etc.
    """
    if not chart_data:
        return []

    # 1. From precomputed vargas
    vargas = chart_data.get("vargas", {})
    if varga_key in vargas:
        ventry = vargas[varga_key]
        if isinstance(ventry, dict):
            raw_planets = ventry.get("planets", [])
            # Normalize: add "varga_sign" alias for sign_number
            result = []
            for p in raw_planets:
                if isinstance(p, dict):
                    pdata = dict(p)
                    # "sign_number" is the actual key; add "varga_sign" alias
                    pdata["varga_sign"] = int(pdata.get("sign_number", 1) or 1)
                    result.append(pdata)
            return result

    # 2. D1 — use main planets list
    planets = chart_data.get("planets", [])
    if varga_key == "D1":
        result = []
        for p in planets:
            if isinstance(p, dict):
                pdata = dict(p)
                pdata["varga_sign"] = int(pdata.get("sign_number", 1) or 1)
                result.append(pdata)
        return result

    # 3. Compute on-the-fly from sidereal_longitude
    try:
        from backend.calculator.vargas import get_varga_sign
    except ImportError:
        try:
            from calculator.vargas import get_varga_sign
        except ImportError:
            return planets
    result = []
    for p in planets:
        if not isinstance(p, dict):
            continue
        lon = float(p.get("sidereal_longitude", p.get("longitude", 0)) or 0)
        vsign = get_varga_sign(varga_key, lon)
        pdata = dict(p)
        pdata["varga_sign"] = vsign
        pdata["sign_number"] = vsign
        result.append(pdata)
    return result

def _get_lagna_sign(chart_data: dict, varga_key: str) -> int:
    """Get lagna sign for the varga.
    
    actual data structure:
    chart_data["vargas"][vkey] = {"lagna": {"sign_number": N, ...}, "planets": [...]}
    chart_data["lagna"] = {"sign_number": N, "sign_name": ..., "longitude_in_sign": ...}
    """
    if not chart_data:
        return 1

    # 1. Try from precomputed vargas sub-dict
    vargas = chart_data.get("vargas", {})
    if varga_key in vargas:
        varga_entry = vargas[varga_key]
        # Correct key path: vargas[key]["lagna"]["sign_number"]
        if isinstance(varga_entry, dict):
            lagna_sub = varga_entry.get("lagna", {})
            if isinstance(lagna_sub, dict) and lagna_sub.get("sign_number"):
                return int(lagna_sub["sign_number"])
            # Fallback: direct lagna_sign key (old format)
            if varga_entry.get("lagna_sign"):
                return int(varga_entry["lagna_sign"])

    # 2. For D1: use chart_data["lagna"]["sign_number"] directly
    lagna_data = chart_data.get("lagna", {})
    if isinstance(lagna_data, dict):
        if lagna_data.get("sign_number"):
            lagna_sign_num = int(lagna_data["sign_number"])
            if varga_key == "D1":
                return lagna_sign_num
            # For other vargas: compute from lagna sidereal longitude
            lagna_lon = float(lagna_data.get("longitude",
                             lagna_data.get("sidereal_longitude",
                             (lagna_sign_num - 1) * 30.0)) or (lagna_sign_num - 1) * 30.0)
            try:
                from backend.calculator.vargas import get_varga_sign
            except ImportError:
                try:
                    from calculator.vargas import get_varga_sign
                except ImportError:
                    return lagna_sign_num  # best guess
            return get_varga_sign(varga_key, lagna_lon)

    return 1  # ultimate fallback


# ─────────────────────────────────────────────────────────────────────────────
# Core Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────
def _count_strength(planets: List[dict], lagna_sign: int) -> Tuple[int, int, List[str], List[str]]:
    """
    Returns (shubha_score, ashubha_score, shubha_points, ashubha_points)
    Based on BPHS: exaltation/own = shubha, debilitation/dusthana = ashubha.
    """
    shubha = 0
    ashubha = 0
    shubha_pts: List[str] = []
    ashubha_pts: List[str] = []

    for p in planets:
        name = str(p.get("name", ""))
        sign = int(p.get("varga_sign", p.get("sign_number", 1)) or 1)
        house = _house_from_lagna(sign, lagna_sign)
        strength = _planet_strength(name, sign)
        is_nat_ben = name in NAT_BENEFICS
        in_kendra = house in KENDRA
        in_trikona = house in TRIKONA
        in_dusthana = house in DUSTHANA

        # Strength scoring
        if strength == "exalted":
            shubha += 3
            shubha_pts.append(f"{_pname(name)} ({_sname(sign)}) — उच्च राशि, अत्यन्त शुभ")
        elif strength == "own":
            shubha += 2
            shubha_pts.append(f"{_pname(name)} ({_sname(sign)}) — स्वराशि, शुभ")
        elif strength == "debilitated":
            ashubha += 3
            ashubha_pts.append(f"{_pname(name)} ({_sname(sign)}) — नीच राशि, अशुभ")

        # House placement
        if in_kendra and (is_nat_ben or strength in ("exalted", "own")):
            shubha += 1
            shubha_pts.append(f"{_pname(name)} — {HOUSE_NAMES_NE[house]} (केन्द्र) मा, शुभ")
        if in_trikona and is_nat_ben:
            shubha += 1
            shubha_pts.append(f"{_pname(name)} — {HOUSE_NAMES_NE[house]} (त्रिकोण) मा, शुभ")
        if in_dusthana and not is_nat_ben:
            ashubha += 2
            ashubha_pts.append(f"{_pname(name)} — {HOUSE_NAMES_NE[house]} (दुःस्थान) मा, अशुभ")
        if in_dusthana and strength == "debilitated":
            ashubha += 1
            ashubha_pts.append(f"{_pname(name)} — दुःस्थानमा नीचस्थ, दोहोरो अशुभ")

    return shubha, ashubha, shubha_pts, ashubha_pts


def _yoga_detection(planets: List[dict], lagna_sign: int, varga_key: str) -> List[str]:
    """
    Detect key BPHS Yogas relevant to the varga.
    """
    yogas: List[str] = []
    by_sign: Dict[int, List[str]] = {}
    for p in planets:
        name = str(p.get("name", ""))
        sign = int(p.get("varga_sign", p.get("sign_number", 1)) or 1)
        by_sign.setdefault(sign, []).append(name)

    by_house: Dict[int, List[str]] = {}
    for p in planets:
        name = str(p.get("name", ""))
        sign = int(p.get("varga_sign", p.get("sign_number", 1)) or 1)
        h = _house_from_lagna(sign, lagna_sign)
        by_house.setdefault(h, []).append(name)

    # Raja Yoga: Kendra lord + Trikona lord conjunction/exchange
    kendra_lords  = {_lord((lagna_sign - 1 + k - 1) % 12 + 1) for k in KENDRA}
    trikona_lords = {_lord((lagna_sign - 1 + t - 1) % 12 + 1) for t in TRIKONA}
    raja_planets  = kendra_lords & trikona_lords
    if raja_planets:
        yogas.append(f"राजयोग सम्भावना: {', '.join(_pname(p) for p in raja_planets)} केन्द्र र त्रिकोणको स्वामी (BPHS अ. ४१)")

    # Gajakesari Yoga: Jupiter + Moon in Kendra
    jup_signs  = [int(p.get("varga_sign", p.get("sign_number", 1)) or 1) for p in planets if p.get("name") == "Jupiter"]
    moon_signs = [int(p.get("varga_sign", p.get("sign_number", 1)) or 1) for p in planets if p.get("name") == "Moon"]
    for js in jup_signs:
        for ms in moon_signs:
            dist = (js - ms) % 12
            if dist in (0, 3, 6, 9):
                yogas.append("गजकेसरी योग: गुरु र चन्द्र परस्परमा केन्द्र — प्रतिष्ठा र सम्मान (BPHS अ. ३५)")

    # Kemadruma: Moon alone without any planet in adjacent signs
    if moon_signs:
        ms = moon_signs[0]
        adj_signs = {(ms - 2) % 12 + 1, ms, ms % 12 + 1}
        adjacent_planets = [p for p in planets if
                            int(p.get("varga_sign", p.get("sign_number", 1)) or 1) in adj_signs
                            and p.get("name") != "Moon"]
        if not adjacent_planets:
            yogas.append("केमद्रुम योग: चन्द्र एक्लो — मानसिक तनाव सम्भव (BPHS अ. ३५)")

    # Budhaditya Yoga: Sun + Mercury together
    sun_signs  = [int(p.get("varga_sign", p.get("sign_number", 1)) or 1) for p in planets if p.get("name") == "Sun"]
    mer_signs  = [int(p.get("varga_sign", p.get("sign_number", 1)) or 1) for p in planets if p.get("name") == "Mercury"]
    for ss in sun_signs:
        if ss in mer_signs:
            yogas.append("बुधादित्य योग: सूर्य+बुध एकत्र — बुद्धि र वाकशक्ति उत्तम (BPHS अ. ३५)")

    # Shasha Yoga: Saturn in own/exalted in Kendra
    sat_signs = [int(p.get("varga_sign", p.get("sign_number", 1)) or 1) for p in planets if p.get("name") == "Saturn"]
    for ss in sat_signs:
        h = _house_from_lagna(ss, lagna_sign)
        if h in KENDRA and _planet_strength("Saturn", ss) in ("exalted", "own"):
            yogas.append("शश योग (पञ्चमहापुरुष): शनि केन्द्रमा उच्च/स्व — अनुशासन र दीर्घायु (BPHS)")

    # Hamsa Yoga: Jupiter exalted/own in Kendra
    jup_signs2 = [int(p.get("varga_sign", p.get("sign_number", 1)) or 1) for p in planets if p.get("name") == "Jupiter"]
    for js in jup_signs2:
        h = _house_from_lagna(js, lagna_sign)
        if h in KENDRA and _planet_strength("Jupiter", js) in ("exalted", "own"):
            yogas.append("हंस योग (पञ्चमहापुरुष): गुरु केन्द्रमा उच्च/स्व — ज्ञान र समृद्धि (BPHS)")

    return yogas


def _extract_active_dasha(chart_data: dict) -> dict:
    """
    Extract active Mahadasha, Antardasha, and Pratyantardasha from chart_data.
    Checks chart_data['dasha'], chart_data['dasha_reports'], or computes from Moon longitude.
    """
    import datetime
    today = datetime.date.today()
    
    # 1. Direct dasha list from chart_data["dasha"]
    dasha_list = chart_data.get("dasha")
    if isinstance(dasha_list, list) and dasha_list:
        for md_node in dasha_list:
            if not isinstance(md_node, dict):
                continue
            s_str = str(md_node.get("start", ""))[:10]
            e_str = str(md_node.get("end", ""))[:10]
            is_active = md_node.get("is_active")
            if is_active is None:
                try:
                    s_date = datetime.date.fromisoformat(s_str)
                    e_date = datetime.date.fromisoformat(e_str)
                    is_active = s_date <= today < e_date
                except Exception:
                    is_active = False

            if is_active:
                md_lord = md_node.get("lord", "")
                md_lord_ne = md_node.get("lord_nepali", _pname(md_lord))
                md_end_bs = md_node.get("end_bs", "")
                md_end_ad = e_str
                
                # Check children for Antardasha
                ad_lord = ""
                ad_lord_ne = ""
                ad_end_bs = ""
                ad_end_ad = ""
                pd_lord = ""
                pd_lord_ne = ""
                
                children = md_node.get("children", [])
                if isinstance(children, list):
                    for ad_node in children:
                        if not isinstance(ad_node, dict):
                            continue
                        as_str = str(ad_node.get("start", ""))[:10]
                        ae_str = str(ad_node.get("end", ""))[:10]
                        ad_active = ad_node.get("is_active")
                        if ad_active is None:
                            try:
                                as_date = datetime.date.fromisoformat(as_str)
                                ae_date = datetime.date.fromisoformat(ae_str)
                                ad_active = as_date <= today < ae_date
                            except Exception:
                                ad_active = False
                        
                        if ad_active:
                            ad_lord = ad_node.get("lord", "")
                            ad_lord_ne = ad_node.get("lord_nepali", _pname(ad_lord))
                            ad_end_bs = ad_node.get("end_bs", "")
                            ad_end_ad = ae_str
                            
                            # Check pratyantar
                            p_children = ad_node.get("children", [])
                            if isinstance(p_children, list):
                                for pd_node in p_children:
                                    if not isinstance(pd_node, dict):
                                        continue
                                    ps_str = str(pd_node.get("start", ""))[:10]
                                    pe_str = str(pd_node.get("end", ""))[:10]
                                    pd_active = pd_node.get("is_active")
                                    if pd_active is None:
                                        try:
                                            ps_date = datetime.date.fromisoformat(ps_str)
                                            pe_date = datetime.date.fromisoformat(pe_str)
                                            pd_active = ps_date <= today < pe_date
                                        except Exception:
                                            pd_active = False
                                    if pd_active:
                                        pd_lord = pd_node.get("lord", "")
                                        pd_lord_ne = pd_node.get("lord_nepali", _pname(pd_lord))
                                        break
                            break
                            
                return {
                    "has_dasha": True,
                    "mahadasha": md_lord,
                    "mahadasha_ne": md_lord_ne,
                    "mahadasha_end": md_end_bs or md_end_ad,
                    "mahadasha_end_ad": md_end_ad,
                    "antardasha": ad_lord,
                    "antardasha_ne": ad_lord_ne,
                    "antardasha_end": ad_end_bs or ad_end_ad,
                    "antardasha_end_ad": ad_end_ad,
                    "pratyantardasha": pd_lord,
                    "pratyantardasha_ne": pd_lord_ne,
                }

    # 2. Check fallback dasha_info or current_dasha
    dasha_info = chart_data.get("dasha_info") or chart_data.get("current_dasha")
    if isinstance(dasha_info, dict) and dasha_info.get("mahadasha"):
        md = dasha_info.get("mahadasha", "")
        ad = dasha_info.get("antardasha", "")
        return {
            "has_dasha": True,
            "mahadasha": md,
            "mahadasha_ne": _pname(md),
            "mahadasha_end": dasha_info.get("mahadasha_end", ""),
            "antardasha": ad,
            "antardasha_ne": _pname(ad),
            "antardasha_end": dasha_info.get("antardasha_end", ""),
            "pratyantardasha": dasha_info.get("pratyantardasha", ""),
            "pratyantardasha_ne": _pname(dasha_info.get("pratyantardasha", "")),
        }

    # 3. Dynamic compute from Moon longitude if birth_date is available in chart_data
    try:
        moon_data = next((p for p in chart_data.get("planets", []) if p.get("name") == "Moon"), None)
        birth_date_str = chart_data.get("birth_date") or chart_data.get("date")
        birth_time_str = chart_data.get("birth_time") or chart_data.get("time", "12:00:00")
        if moon_data and birth_date_str:
            moon_lon = float(moon_data.get("sidereal_longitude", moon_data.get("longitude", 0)) or 0)
            from backend.calculator.dasha import calculate_vimshottari_dasha
            computed = calculate_vimshottari_dasha(moon_lon, str(birth_date_str), str(birth_time_str))
            if computed:
                return _extract_active_dasha({"dasha": computed})
    except Exception:
        pass

    return {"has_dasha": False}


def _timing_analysis(chart_data: dict, varga_key: str, key_planets: List[str]) -> List[str]:
    """
    Derive BPHS timing analysis based on active Vimshottari Dasha and planet placements in this Varga.
    """
    timings: List[str] = []
    dasha = _extract_active_dasha(chart_data)
    
    # Extract planet positions in this specific Varga for dasha interpretation
    v_planets = _get_planets_in_varga(chart_data, varga_key)
    lagna_sign = _get_lagna_sign(chart_data, varga_key)
    v_planet_map = {p.get("name"): p for p in v_planets if isinstance(p, dict)}
    
    meta = VARGA_META.get(varga_key, VARGA_META["D1"])
    subject = meta.get("subject_ne", "यस क्षेत्र")

    if dasha.get("has_dasha"):
        md_name = dasha["mahadasha"]
        md_ne = dasha["mahadasha_ne"]
        md_end = dasha["mahadasha_end"]
        ad_name = dasha["antardasha"]
        ad_ne = dasha["antardasha_ne"]
        ad_end = dasha["antardasha_end"]
        pd_ne = dasha.get("pratyantardasha_ne", "")

        # 1. Current Active Dasha Status
        dasha_line = f"वर्तमान दशा: {md_ne} महादशा"
        if md_end:
            dasha_line += f" ({md_end} सम्म)"
        if ad_ne:
            dasha_line += f" ➔ {ad_ne} अन्तर्दशा"
            if ad_end:
                dasha_line += f" ({ad_end} सम्म)"
        if pd_ne:
            dasha_line += f" ➔ {pd_ne} प्रत्यन्तर्दशा"
        timings.append(dasha_line)

        # 2. Mahadasha Lord's impact in this Varga (BPHS rule)
        md_planet = v_planet_map.get(md_name)
        if md_planet:
            md_sign = int(md_planet.get("varga_sign", md_planet.get("sign_number", 1)) or 1)
            md_house = _house_from_lagna(md_sign, lagna_sign)
            md_strength = _planet_strength(md_name, md_sign)
            h_name = HOUSE_NAMES_NE.get(md_house, f"{md_house}औं भाव")

            if md_house in TRIKONA or md_house in KENDRA:
                if md_strength in ("exalted", "own"):
                    timings.append(
                        f"{md_ne} महादशापति यस वर्गमा {h_name}मा बलिष्ठ (उच्च/स्व) — "
                        f"{subject}मा अत्यधिक सफलता, उन्नति र अनुकूल समय।"
                    )
                else:
                    timings.append(
                        f"{md_ne} महादशापति यस वर्गमा {h_name} (केन्द्र/त्रिकोण) मा — "
                        f"{subject} सम्बन्धी कार्यहरूमा सकारात्मक प्रगति रहनेछ।"
                    )
            elif md_house in DUSTHANA:
                timings.append(
                    f"{md_ne} महादशापति यस वर्गमा {h_name} (दुःस्थान) मा — "
                    f"{subject}मा उतारचढाव र सावधानी अपनाउनुपर्ने समय।"
                )
            else:
                timings.append(
                    f"{md_ne} महादशापति यस वर्गमा {h_name}मा स्थित भई सामान्य फलदायक रहनेछ।"
                )

        # 3. Antardasha Lord's impact in this Varga
        if ad_name and ad_name != md_name:
            ad_planet = v_planet_map.get(ad_name)
            if ad_planet:
                ad_sign = int(ad_planet.get("varga_sign", ad_planet.get("sign_number", 1)) or 1)
                ad_house = _house_from_lagna(ad_sign, lagna_sign)
                ad_strength = _planet_strength(ad_name, ad_sign)
                ad_h_name = HOUSE_NAMES_NE.get(ad_house, f"{ad_house}औं भाव")

                if ad_name in key_planets:
                    timings.append(
                        f"{ad_ne} अन्तर्दशा यस वर्गको मुख्य कारक ग्रह भएकाले — "
                        f"हालको समय {subject} सम्बन्धी महत्त्वपूर्ण निर्णय र घटनाहरूको मुख्य समय हो।"
                    )
                elif ad_house in (1, 5, 9, 10, 11) and ad_strength != "debilitated":
                    timings.append(
                        f"{ad_ne} अन्तर्दशा ({ad_h_name}) अनुकूल — शुभ परिणाम र सहयोग मिल्नेछ।"
                    )
                elif ad_house in DUSTHANA:
                    timings.append(
                        f"{ad_ne} अन्तर्दशा {ad_h_name}मा रहेकाले धैर्य र उपाय फलदायी हुनेछ।"
                    )

        # 4. Key Planets for this Varga activation timing
        for kp in key_planets:
            if kp not in (md_name, ad_name) and kp in v_planet_map:
                kp_p = v_planet_map[kp]
                kp_sign = int(kp_p.get("varga_sign", kp_p.get("sign_number", 1)) or 1)
                kp_str = _planet_strength(kp, kp_sign)
                if kp_str in ("exalted", "own"):
                    timings.append(
                        f"भविष्यमा {_pname(kp)}को दशा/अन्तर्दशा आउँदा {subject}मा ठूलो उपलब्धि हासिल हुनेछ।"
                    )
                    break

    else:
        # Fallback if dasha payload was not attached: provide key planetary periods for this varga
        timings.append(f"यस {varga_key} वर्गका मुख्य कारक ग्रहहरू: {', '.join(_pname(p) for p in key_planets)}।")
        for kp in key_planets:
            if kp in v_planet_map:
                kp_p = v_planet_map[kp]
                kp_sign = int(kp_p.get("varga_sign", kp_p.get("sign_number", 1)) or 1)
                kp_house = _house_from_lagna(kp_sign, lagna_sign)
                kp_str = _planet_strength(kp, kp_sign)
                kp_h_name = HOUSE_NAMES_NE.get(kp_house, f"{kp_house}औं भाव")
                timings.append(
                    f"{_pname(kp)} ({kp_h_name}) को दशा वा गोचर कालमा {subject} सम्बन्धी विशेष फल प्राप्त हुनेछ।"
                )
                break

    return timings


def _remedies(varga_key: str, weak_planets: List[str], strong_planets: List[str]) -> List[str]:
    """
    BPHS-based remedies for weak planets.
    """
    PLANET_REMEDIES = {
        "Sun":     ["रविवार उपवास", "आदित्य हृदय स्तोत्र पाठ", "तामा दान", "सूर्य नमस्कार"],
        "Moon":    ["सोमवार उपवास", "चन्द्र मन्त्र (ॐ सों सोमाय नमः)", "चाँदी धारण", "शिवजीको पूजा"],
        "Mars":    ["मंगलवार उपवास", "हनुमान चालीसा", "रातो मूंगा धारण", "लाल चन्दन टीका"],
        "Mercury": ["बुधवार उपवास", "विष्णु सहस्रनाम", "हरियो पन्ना/एमराल्ड", "हरियो वस्तु दान"],
        "Jupiter": ["बिहीवार उपवास", "गुरु मन्त्र (ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः)", "पहेंलो पुखराज", "ब्राह्मण भोजन"],
        "Venus":   ["शुक्रवार उपवास", "लक्ष्मी पूजा", "हीरा/ओपल", "सेतो वस्तु दान"],
        "Saturn":  ["शनिवार तेल चढाउने", "शनि मन्त्र (ॐ शं शनैश्चराय नमः)", "नीलम (विशेषज्ञसँग सल्लाह)", "गरिबलाई दान"],
        "Rahu":    ["राहु मन्त्र", "गोमेद धारण (विशेषज्ञसँग)", "गणेश पूजा", "शनिवार उपवास"],
        "Ketu":    ["केतु मन्त्र", "वैदूर्य धारण (विशेषज्ञसँग)", "गणेश पूजा", "भैरव पूजा"],
    }
    GENERAL_REMEDIES = {
        "D2":  ["नित्य लक्ष्मी पूजा", "गुरुवार उपवास", "गाईलाई हरियो घाँस खुवाउनु"],
        "D7":  ["सन्तान गोपाल मन्त्र", "गुरु आराधना", "संतान प्राप्तिका लागि गुरुवार व्रत"],
        "D9":  ["नित्य विष्णु पूजा", "बिवाहित जीवन सुधारका लागि शुक्रवार व्रत"],
        "D10": ["नित्य गायत्री मन्त्र (१०८ जाप)", "शनिवार तेल दीप", "कार्यस्थल पूर्वमुखी राख्नु"],
        "D12": ["पितृ तर्पण", "पितृ पक्षमा श्राद्ध", "माता-पितालाई सम्मान"],
        "D30": ["नित्य हनुमान चालीसा", "शनिवार उपवास", "रोग भएमा महामृत्युञ्जय मन्त्र"],
        "D60": ["नित्य सन्ध्यावन्दन", "गायत्री मन्त्र", "पूर्वज तर्पण"],
    }
    remedies: List[str] = []
    for planet in weak_planets:
        if planet in PLANET_REMEDIES:
            for r in PLANET_REMEDIES[planet][:3]:
                remedies.append(f"• {_pname(planet)} (कमजोर): {r}")
    general = GENERAL_REMEDIES.get(varga_key, ["नित्य गायत्री मन्त्र", "ग्रह शान्ति पूजा"])
    for g in general:
        remedies.append(f"• सामान्य: {g}")
    return remedies[:8]


# ─────────────────────────────────────────────────────────────────────────────
# Main Public API
# ─────────────────────────────────────────────────────────────────────────────
def analyze_varga(chart_data: dict, varga_key: str) -> dict:
    """
    Perform comprehensive BPHS-based analysis of a Varga chart.

    Returns:
        {
          "varga_key": str,
          "conclusion": str,           # एक वाक्यमा निष्कर्ष
          "subject": str,              # यस वर्गको विषय
          "purpose": str,              # उद्देश्य
          "shubha_percent": int,       # शुभता प्रतिशत
          "ashubha_percent": int,      # अशुभता प्रतिशत
          "shubha_points": List[str],  # शुभ बुँदाहरू
          "ashubha_points": List[str], # अशुभ बुँदाहरू
          "yogas": List[str],          # महत्त्वपूर्ण योगहरू
          "timing": List[str],         # समय-फल
          "remedies": List[str],       # उपायहरू
          "planet_analysis": List[dict],# प्रत्येक ग्रहको विश्लेषण
          "lagna_sign": int,
          "lagna_sign_name": str,
        }
    """
    meta = VARGA_META.get(varga_key, VARGA_META["D1"])
    planets = _get_planets_in_varga(chart_data, varga_key)
    lagna_sign = _get_lagna_sign(chart_data, varga_key)

    # Per-planet analysis
    planet_analysis = []
    weak_planets: List[str] = []
    strong_planets: List[str] = []
    for p in planets:
        name = str(p.get("name", ""))
        if not name or name in ("Ascendant",):
            continue
        sign = int(p.get("varga_sign", p.get("sign_number", 1)) or 1)
        house = _house_from_lagna(sign, lagna_sign)
        strength = _planet_strength(name, sign)
        if strength == "debilitated":
            weak_planets.append(name)
        elif strength in ("exalted", "own"):
            strong_planets.append(name)

        house_type = (
            "केन्द्र (शुभ)" if house in KENDRA else
            "त्रिकोण (अत्यन्त शुभ)" if house in TRIKONA else
            "दुःस्थान (अशुभ)" if house in DUSTHANA else
            "उपचय (वृद्धि)" if house in UPACHAYA else
            "सामान्य"
        )
        strength_ne = {
            "exalted":    "उच्च राशि (बलिष्ठ)",
            "own":        "स्वराशि (बलिष्ठ)",
            "neutral":    "सामान्य",
            "debilitated":"नीच राशि (कमजोर)",
        }.get(strength, "सामान्य")

        planet_analysis.append({
            "name": name,
            "name_ne": _pname(name),
            "sign": sign,
            "sign_name": _sname(sign),
            "house": house,
            "house_name": HOUSE_NAMES_NE.get(house, str(house)),
            "house_type": house_type,
            "strength": strength,
            "strength_ne": strength_ne,
            "lord": _lord(sign),
            "lord_ne": _pname(_lord(sign)),
        })

    # Scoring
    shubha, ashubha, shubha_pts, ashubha_pts = _count_strength(planets, lagna_sign)
    total = shubha + ashubha
    if total == 0:
        shubha_pct, ashubha_pct = 50, 50
    else:
        shubha_pct  = round(shubha  / total * 100)
        ashubha_pct = 100 - shubha_pct

    # Add lagna lord position
    lagna_lord = _lord(lagna_sign)
    ll_planet   = next((p for p in planets if p.get("name") == lagna_lord), None)
    if ll_planet:
        ll_sign = int(ll_planet.get("varga_sign", ll_planet.get("sign_number", 1)) or 1)
        ll_house = _house_from_lagna(ll_sign, lagna_sign)
        ll_strength = _planet_strength(lagna_lord, ll_sign)
        if ll_house in TRIKONA and ll_strength in ("exalted", "own"):
            shubha_pts.insert(0, f"लग्नेश {_pname(lagna_lord)} त्रिकोणमा बलिष्ठ — अत्यन्त शुभ लग्न (BPHS अ. ७)")
            shubha_pct = min(100, shubha_pct + 5)
            ashubha_pct = max(0, 100 - shubha_pct)
        elif ll_house in DUSTHANA:
            ashubha_pts.insert(0, f"लग्नेश {_pname(lagna_lord)} दुःस्थान ({ll_house}ठौं) मा — कष्ट सम्भव (BPHS)")
            ashubha_pct = min(100, ashubha_pct + 5)
            shubha_pct  = max(0, 100 - ashubha_pct)

    # Yogas
    yogas = _yoga_detection(planets, lagna_sign, varga_key)

    # Timing
    timing = _timing_analysis(chart_data, varga_key, meta.get("key_planets", []))

    # Remedies
    remedies = _remedies(varga_key, weak_planets, strong_planets)

    # Conclusion (one sentence)
    if shubha_pct >= 70:
        verdict = "अत्यन्त शुभ"
        life_effect = "यस क्षेत्रमा जातकलाई उल्लेखनीय सफलता र समृद्धि प्राप्त हुने"
    elif shubha_pct >= 55:
        verdict = "मध्यम शुभ"
        life_effect = "यस क्षेत्रमा सामान्यतः राम्रो परिणाम, केही बाधाहरूसहित"
    elif shubha_pct >= 40:
        verdict = "मिश्रित"
        life_effect = "यस क्षेत्रमा उतारचढाव, शुभ र अशुभ दुवै प्रभाव"
    else:
        verdict = "कठिन"
        life_effect = "यस क्षेत्रमा विशेष प्रयास र उपाय आवश्यक"

    lagna_sign_name = _sname(lagna_sign)
    conclusion = (
        f"{varga_key} वर्ग कुण्डलीमा {lagna_sign_name} लग्न, "
        f"शुभता {shubha_pct}% — {life_effect}।"
    )

    return {
        "varga_key":       varga_key,
        "conclusion":      conclusion,
        "verdict":         verdict,
        "subject":         meta.get("subject_ne", ""),
        "purpose":         meta.get("purpose_ne", ""),
        "shubha_percent":  shubha_pct,
        "ashubha_percent": ashubha_pct,
        "shubha_points":   shubha_pts,
        "ashubha_points":  ashubha_pts,
        "yogas":           yogas,
        "timing":          timing,
        "remedies":        remedies,
        "planet_analysis": planet_analysis,
        "lagna_sign":      lagna_sign,
        "lagna_sign_name": lagna_sign_name,
        "lagna_lord":      lagna_lord,
        "lagna_lord_ne":   _pname(lagna_lord),
        "weak_planets":    weak_planets,
        "strong_planets":  strong_planets,
    }
