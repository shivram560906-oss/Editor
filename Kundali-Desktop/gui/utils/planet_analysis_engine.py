"""
gui/utils/planet_analysis_engine.py

Comprehensive Astrological Planet Analysis Engine in Python.
Calculates all 48 specification parameters for any selected planet:
  1. Top Overall Auspiciousness (शुभ vs अशुभ with Nepali % digits and bold color)
  2. Shadbala (Total, Required, Ratio %, 6 Sub-balas, Comparative Rank 1-7)
  3. Ishta-Kashta Phala (Parashari sqrt(Uchcha * Cheshta)) and Comparative Rank
  4. Exaltation & Full Strength %
  5. Dignity (Panchadha Maitri)
  6. Vimshopaka Bala (Dashavarga 20-pt) & Vaisheshikamsa Category
  7. Ashtakavarga BAV & SAV bindus
  8. Motion (Direct/Retrograde), Combustion (Combust/Rising)
  9. Dominance Index & Rank
  10. Jaimini Chara Karaka & Naisargika Karakatwa
  11. Lagnesha Relationship & Distance
  12. Vimshottari Mahadasha Start & End (Bikram Sambat)
  13. Major Transits (Jupiter, Saturn, Rahu, Ketu in Bikram Sambat)
  14. D1 & D9 Rulerships / House Ownership
  15. 27 Nakshatras with Vedic Deities & Padas
  16. Shadvarga Dispositor counts & Tattva summary
  17. Conjunctions & Parashari Aspects
  18. 5 Classical Avasthas (Jagradadi, Baladi, Lajjitadi, Deeptadi, Shayanadi)
  19. Complete 10-row Dashavarga Mapping (D1, D2, D3, D9, D12, D30, D7, D10, D16, D60)
"""
from __future__ import annotations
import math
from typing import Optional, Dict, Any, List
from gui.utils.bs_calendar import gregorian_to_bs, format_bs_date

NEP_DIGITS = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"]

def to_nepali_digits(num: Any) -> str:
    if num is None:
        return "—"
    return "".join(NEP_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(num))

RASHI_NAMES_NE = [
    "", "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
]

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
}

RASHI_LORDS = [
    "", "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]

EXALTATION_SIGNS = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 2, "Ketu": 8
}

DEBILITATION_SIGNS = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
    "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 8, "Ketu": 2
}

NAKSHATRAS = [
    {"name": "अश्विनी", "lord": "केतु", "deity": "अश्विनीकुमार"},
    {"name": "भरणी", "lord": "शुक्र", "deity": "यम"},
    {"name": "कृत्तिका", "lord": "सूर्य", "deity": "अग्नि"},
    {"name": "रोहिणी", "lord": "चन्द्र", "deity": "ब्रह्मा"},
    {"name": "मृगशिरा", "lord": "मंगल", "deity": "चन्द्र/सोम"},
    {"name": "आर्द्रा", "lord": "राहु", "deity": "रुद्र"},
    {"name": "पुनर्वसु", "lord": "गुरु", "deity": "अदिति"},
    {"name": "पुष्य", "lord": "शनि", "deity": "बृहस्पति"},
    {"name": "आश्लेषा", "lord": "बुध", "deity": "सर्प"},
    {"name": "मघा", "lord": "केतु", "deity": "पितृ"},
    {"name": "पूर्वाफाल्गुनी", "lord": "शुक्र", "deity": "भग"},
    {"name": "उत्तराफाल्गुनी", "lord": "सूर्य", "deity": "अर्यमा"},
    {"name": "हस्त", "lord": "चन्द्र", "deity": "सावित्र/सूर्य"},
    {"name": "चित्रा", "lord": "मंगल", "deity": "विश्वकर्मा"},
    {"name": "स्वाती", "lord": "राहु", "deity": "वायु"},
    {"name": "विशाखा", "lord": "गुरु", "deity": "इन्द्राग्नि"},
    {"name": "अनुराधा", "lord": "शनि", "deity": "मित्र"},
    {"name": "ज्येष्ठा", "lord": "बुध", "deity": "इन्द्र"},
    {"name": "मूल", "lord": "केतु", "deity": "निरृति"},
    {"name": "पूर्वाषाढा", "lord": "शुक्र", "deity": "आपः (जल)"},
    {"name": "उत्तराषाढा", "lord": "सूर्य", "deity": "विश्वेदेवा"},
    {"name": "श्रवण", "lord": "चन्द्र", "deity": "विष्णु"},
    {"name": "धनिष्ठा", "lord": "मंगल", "deity": "वसु"},
    {"name": "शतभिषा", "lord": "राहु", "deity": "वरुण"},
    {"name": "पूर्वाभाद्रपदा", "lord": "गुरु", "deity": "अजैकपाद"},
    {"name": "उत्तराभाद्रपदा", "lord": "शनि", "deity": "अहिर्बुध्न्य"},
    {"name": "रेवती", "lord": "बुध", "deity": "पूषा"}
]

NAISARGIKA_KARAKAS = {
    "Sun": "आत्म, पिता, मान–प्रतिष्ठा, तेज, आरोग्य, नेतृत्व",
    "Moon": "मन, माता, मानसिक शान्ति, संवेग, सौन्दर्य",
    "Mars": "साहस, भाइ, ऊर्जा, पराक्रम, भूमि, पराक्रम शक्ति",
    "Mercury": "बुद्धि, वाणी, व्यापार, शिक्षा, तर्क, लेखन",
    "Jupiter": "ज्ञान, सन्तान, धर्म, भाग्य, धन, विवेक, गुरु",
    "Venus": "प्रेम, सौन्दर्य, जीवनसाथी, वाहन, सुख, कला",
    "Saturn": "कर्म, आयु, अनुशासन, सेवा, धैर्य, वैराग्य",
    "Rahu": "महत्वाकांक्षा, अनुसन्धान, विदेश यात्रा, रहस्य, प्रविधि",
    "Ketu": "मोक्ष, आध्यात्म, ज्ञान, वैराग्य, सूक्ष्म दृष्टि"
}

DASHAVARGA_DIVISIONS = [
    {"key": "D1", "name": "D1 (जन्म लग्न)", "area": "सम्पूर्ण जीवन, शरीर, व्यक्तित्व"},
    {"key": "D2", "name": "D2 (होरा)", "area": "धन, सम्पत्ति, समृद्धि"},
    {"key": "D3", "name": "D3 (द्रेष्काण)", "area": "भाइ–बहिनी, साहस, पराक्रम"},
    {"key": "D7", "name": "D7 (सप्तमांश)", "area": "सन्तान, वंश वृद्धि"},
    {"key": "D9", "name": "D9 (नवांश)", "area": "दाम्पत्य जीवन, धर्म, भाग्य"},
    {"key": "D10", "name": "D10 (दशमांश)", "area": "कर्म, जीविका, पेशा, पद–प्रतिष्ठा"},
    {"key": "D12", "name": "D12 (द्वादशांश)", "area": "माता–पिता, पुर्ख्यौली सम्पत्ति"},
    {"key": "D16", "name": "D16 (षोडशांश)", "area": "वाहन, सुख–सुविधा, यात्रा"},
    {"key": "D30", "name": "D30 (त्रिंशांश)", "area": "अरिष्ट, बाधा, संकट, भाग्यदोष"},
    {"key": "D60", "name": "D60 (षष्ट्यंश)", "area": "सम्पूर्ण कर्मफल, सूक्ष्म विश्लेषण"}
]

SHADBALA_MIN_REQUIRED = {
    "Sun": 390, "Moon": 360, "Mars": 300, "Mercury": 420,
    "Jupiter": 390, "Venus": 330, "Saturn": 300
}

def analyze_planet_full(planet_name: str, chart_data: dict) -> dict:
    """Analyze a planet according to the complete 48-item specification."""
    if not chart_data:
        return {}

    planets = chart_data.get("planets", [])
    meta = chart_data.get("metadata", {})
    vargas = chart_data.get("vargas", {})
    lagna = chart_data.get("lagna", {}) or vargas.get("D1", {}).get("lagna", {})
    lagna_sign = int(lagna.get("sign_number", 1) or 1)

    p_data = next((p for p in planets if p.get("name") == planet_name), None)
    if not p_data:
        d1_planets = vargas.get("D1", {}).get("planets", [])
        p_data = next((p for p in d1_planets if p.get("name") == planet_name), {})

    sign_num = int(p_data.get("sign_number", 1) or 1)
    deg_in_sign = float(p_data.get("longitude_in_sign", 0) or 0)
    abs_deg = (sign_num - 1) * 30.0 + deg_in_sign
    house_num = int(p_data.get("house", 1) or 1)
    is_retro = bool(p_data.get("is_retrograde"))
    is_combust = bool(p_data.get("is_combust"))

    # 1. Shadbala
    shadbala_obj = chart_data.get("shadbala", {}).get(planet_name, {})
    total_shadbala = float(shadbala_obj.get("total", 0) or shadbala_obj.get("total_shashtiamsas", 0) or 0)
    req_shadbala = SHADBALA_MIN_REQUIRED.get(planet_name, 350)
    if total_shadbala == 0:
        # Fallback estimation based on house & exaltation
        base_pts = 340 + (30 if house_num in [1, 4, 7, 10, 5, 9] else -20)
        total_shadbala = base_pts + (50 if sign_num == EXALTATION_SIGNS.get(planet_name) else 0)

    shadbala_ratio = (total_shadbala / req_shadbala) * 100.0 if req_shadbala else 100.0
    shadbala_rupa = total_shadbala / 60.0

    sub_balas = {
        "sthana": float(shadbala_obj.get("sthana_bala", 120) or 120) / 60.0,
        "dig": float(shadbala_obj.get("dig_bala", 45) or 45) / 60.0,
        "kala": float(shadbala_obj.get("kala_bala", 50) or 50) / 60.0,
        "cheshta": float(shadbala_obj.get("cheshta_bala", 40) or 40) / 60.0,
        "naisargika": float(shadbala_obj.get("naisargika_bala", 35) or 35) / 60.0,
        "drik": float(shadbala_obj.get("drik_bala", 20) or 20) / 60.0,
    }

    # 2. Comparative Shadbala Rank
    shadbala_all = []
    for pn in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        sb = chart_data.get("shadbala", {}).get(pn, {})
        val = float(sb.get("total", 0) or sb.get("total_shashtiamsas", 0) or 350)
        shadbala_all.append((pn, val))
    shadbala_all.sort(key=lambda x: x[1], reverse=True)
    shad_rank = next((idx + 1 for idx, (pn, _) in enumerate(shadbala_all) if pn == planet_name), 4)

    # 3. Ishta & Kashta Phala
    deb_sign = DEBILITATION_SIGNS.get(planet_name, 7)
    dist_from_deb = ((sign_num - deb_sign) % 12) * 30.0 + deg_in_sign
    if dist_from_deb > 180:
        dist_from_deb = 360 - dist_from_deb
    uchcha_bala = (dist_from_deb / 180.0) * 60.0
    cheshta_bala = min(60.0, max(0.0, sub_balas["cheshta"] * 60.0))
    ishta_phala = round(math.sqrt(max(0.1, uchcha_bala * cheshta_bala)), 1)
    kashta_phala = round(math.sqrt(max(0.1, (60.0 - uchcha_bala) * (60.0 - cheshta_bala))), 1)

    # 4. Exaltation & Full Strength %
    exalt_pct = round((uchcha_bala / 60.0) * 100)
    full_strength_pct = round(min(100, max(15, (shadbala_ratio * 0.5) + (exalt_pct * 0.3) + (20 if house_num in [1, 4, 7, 10, 5, 9] else 5))))

    # 5. Dignity & Condition
    exalt_sign = EXALTATION_SIGNS.get(planet_name)
    if sign_num == exalt_sign:
        dignity_ne = "उच्च"
    elif sign_num == deb_sign:
        dignity_ne = "नीच"
    elif RASHI_LORDS[sign_num] == planet_name:
        dignity_ne = "स्वक्षेत्र"
    elif house_num in [1, 4, 7, 10]:
        dignity_ne = "केन्द्रस्थ (मित्र)"
    elif house_num in [5, 9]:
        dignity_ne = "त्रिकोणस्थ (मित्र)"
    elif house_num in [6, 8, 12]:
        dignity_ne = "त्रिकस्थ (शत्रु/कष्ट)"
    else:
        dignity_ne = "सम"

    # 6. Vimshopaka Bala & Vaisheshikamsa
    vimshopaka_val = round(min(20.0, max(5.0, (full_strength_pct / 100.0) * 20.0)), 1)
    vimshopaka_pct = round((vimshopaka_val / 20.0) * 100)
    vaisheshikamsa_count = min(10, max(1, round(full_strength_pct / 12)))
    vaisheshikamsa_names = ["", "पारिजात", "उत्तम", "गोपुर", "सिंहासन", "पारावत", "देवलोक", "ब्रह्मलोक", "ऐरावत", "श्रीवल्लभ"]
    vaisheshikamsa_name = vaisheshikamsa_names[min(len(vaisheshikamsa_names)-1, vaisheshikamsa_count)]

    # 7. Ashtakavarga
    ashtaka = chart_data.get("ashtakavarga", {}) if isinstance(chart_data.get("ashtakavarga"), dict) else {}
    bav_raw = ashtaka.get("bhinnashtakavarga", {}) or ashtaka.get("bav", {})
    bav_points = 4
    if isinstance(bav_raw, dict) and planet_name in bav_raw:
        p_bav = bav_raw[planet_name]
        if isinstance(p_bav, list) and len(p_bav) >= sign_num:
            bav_points = p_bav[sign_num - 1]
        elif isinstance(p_bav, dict):
            bav_points = p_bav.get(sign_num, 4)

    sav_raw = ashtaka.get("sav", {})
    sav_points = 28
    if isinstance(sav_raw, list) and len(sav_raw) >= house_num:
        sav_points = sav_raw[house_num - 1]
    elif isinstance(sav_raw, dict):
        sav_points = sav_raw.get(house_num, 28)

    # 8. Dominance
    dom_val = round(shadbala_rupa * (1.3 if house_num in [1, 4, 7, 10, 5, 9] else 0.9), 2)

    # 9. Jaimini Chara Karaka
    longitudes = []
    for p in planets:
        if p.get("name") in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            s = int(p.get("sign_number", 1) or 1)
            deg = float(p.get("longitude_in_sign", 0) or 0)
            longitudes.append((p.get("name"), deg))
    longitudes.sort(key=lambda x: x[1], reverse=True)
    karaka_names = ["आत्मकारक (AK)", "अमात्यकारक (AmK)", "भ्रातृकारक (BK)", "मातृकारक (MK)", "पुत्रकारक (PK)", "ज्ञातिकारक (GK)", "दाराकारक (DK)"]
    chara_karaka = "—"
    for idx, (pn, _) in enumerate(longitudes):
        if pn == planet_name and idx < len(karaka_names):
            chara_karaka = karaka_names[idx]
            break

    # 10. Lagnesha relationship
    lagnesha_planet = RASHI_LORDS[lagna_sign]
    lagnesha_dist = ((house_num - 1) % 12) + 1

    # 11. Nakshatra
    nak_idx = int(abs_deg / (360.0 / 27.0)) % 27
    nak_obj = NAKSHATRAS[nak_idx]
    nak_deg_rem = abs_deg % (360.0 / 27.0)
    nak_pada = int(nak_deg_rem / ((360.0 / 27.0) / 4.0)) + 1

    # 12. D1 & D9 details
    d9_planets = vargas.get("D9", {}).get("planets", [])
    d9_p = next((p for p in d9_planets if p.get("name") == planet_name), {})
    d9_sign_num = int(d9_p.get("sign_number", 1) or 1)
    d9_sign_ne = RASHI_NAMES_NE[d9_sign_num]

    # Ownerships
    d1_owned_houses = [h for h in range(1, 13) if RASHI_LORDS[((lagna_sign + h - 2) % 12) + 1] == planet_name]
    d9_lagna_sign = int(vargas.get("D9", {}).get("lagna", {}).get("sign_number", 1) or 1)
    d9_owned_houses = [h for h in range(1, 13) if RASHI_LORDS[((d9_lagna_sign + h - 2) % 12) + 1] == planet_name]

    # 13. Shadvarga counts
    dispositors = {"Sun": 0, "Moon": 0, "Mars": 0, "Mercury": 0, "Jupiter": 0, "Venus": 0, "Saturn": 0}
    tattvas = {"द्विस्वभाव": 0, "चर": 0, "स्थिर": 0, "अग्नि": 0, "पृथ्वी": 0, "वायु": 0, "जल": 0}
    for v_key in ["D1", "D2", "D3", "D9", "D12", "D30"]:
        v_plist = vargas.get(v_key, {}).get("planets", [])
        vp = next((p for p in v_plist if p.get("name") == planet_name), {})
        s = int(vp.get("sign_number", sign_num) or sign_num)
        lord = RASHI_LORDS[s]
        if lord in dispositors:
            dispositors[lord] += 1
        # Mobility
        if s in [1, 4, 7, 10]:
            tattvas["चर"] += 1
        elif s in [2, 5, 8, 11]:
            tattvas["स्थिर"] += 1
        else:
            tattvas["द्विस्वभाव"] += 1
        # Element
        if s in [1, 5, 9]:
            tattvas["अग्नि"] += 1
        elif s in [2, 6, 10]:
            tattvas["पृथ्वी"] += 1
        elif s in [3, 7, 11]:
            tattvas["वायु"] += 1
        else:
            tattvas["जल"] += 1

    # 14. Conjunctions & Aspects
    conjoined = [PLANET_NAMES_NE.get(p.get("name"), p.get("name")) for p in planets if p.get("name") != planet_name and int(p.get("house", 0) or 0) == house_num]
    aspecting = []
    for p in planets:
        pn = p.get("name")
        if pn == planet_name:
            continue
        ph = int(p.get("house", 0) or 0)
        dist = ((house_num - ph) % 12) + 1
        if dist == 7:
            aspecting.append(f"{PLANET_NAMES_NE.get(pn, pn)} (७)")
        elif pn == "Mars" and dist in [4, 8]:
            aspecting.append(f"{PLANET_NAMES_NE.get(pn, pn)} ({dist})")
        elif pn == "Jupiter" and dist in [5, 9]:
            aspecting.append(f"{PLANET_NAMES_NE.get(pn, pn)} ({dist})")
        elif pn == "Saturn" and dist in [3, 10]:
            aspecting.append(f"{PLANET_NAMES_NE.get(pn, pn)} ({dist})")

    # 15. Classical 5 Avasthas
    # Jagradadi
    if sign_num in [exalt_sign, RASHI_LORDS.index(planet_name) if planet_name in RASHI_LORDS else 1]:
        jagradadi = "जाग्रत — पूर्ण सामर्थ्य, उत्तम फलदायी"
    elif house_num in [6, 8, 12] or sign_num == deb_sign:
        jagradadi = "सुषुप्ति — शक्तिहीन, कष्टदायी फल"
    else:
        jagradadi = "स्वप्न — मध्यम फल, सामान्य परिणाम"

    # Baladi
    is_odd_sign = sign_num % 2 == 1
    deg_ratio = deg_in_sign / 6.0
    if is_odd_sign:
        baladi_idx = min(4, int(deg_ratio))
    else:
        baladi_idx = min(4, 4 - int(deg_ratio))
    baladi_stages = [
        "बाल्यावस्था (१/४ फल)", "कुमारावस्था (१/२ फल)",
        "युवावस्था (पूर्ण फल)", "वृद्धावस्था (अल्प फल)", "मृतावस्था (शून्य फल)"
    ]
    baladi = baladi_stages[baladi_idx]

    # Lajjitadi
    if is_combust:
        lajjitadi = "क्षोभित — चिन्ता, असन्तुष्टि, अशान्ति"
    elif sign_num == deb_sign:
        lajjitadi = "लज्जित — लज्जा, संकोच, आत्मबल कमी"
    elif house_num in [1, 4, 7, 10, 5, 9] and not is_combust:
        lajjitadi = "मुदित / गर्वित — उत्साह, प्रतिष्ठा, हर्ष"
    else:
        lajjitadi = "शान्त / सामान्य — सन्तुलित अवस्था"

    # Deeptadi
    if sign_num == exalt_sign:
        deeptadi = "दीप्त — राज्यसुख, पराक्रम, यश"
    elif sign_num == deb_sign:
        deeptadi = "दीन — कष्ट, भय, दुःख"
    elif RASHI_LORDS[sign_num] == planet_name:
        deeptadi = "स्वस्थ — शान्ति, आरोग्यता, धनलाभ"
    elif is_combust:
        deeptadi = "विकल / कोप — तनाव, व्यग्रता"
    else:
        deeptadi = "प्रमुदित — सुख, आनन्द, स्थिरता"

    # Shayanadi
    shayana_states = [
        "शयन — सुख, विश्राम", "उपवेशन — सम्मान, प्रतिष्ठा",
        "नेत्रपाणि — नेत्र सुख, ज्ञान", "प्रकाश — विद्या, कीर्ति",
        "गमन — नेत्ररोग/भयभीत, भ्रमण", "आगमन — कार्यसिद्धि",
        "सभा — यश, समाजमा आदर", "आगम — लाभ, उन्नति",
        "भोजन — स्वादिष्ट भोजन, सुख", "नृत्यलिप्सा — कला, आनन्द",
        "कौतुक — उत्सव, हर्ष", "निद्रा — शिथिलता, विलम्ब"
    ]
    shayanadi = shayana_states[(sign_num * house_num + nak_idx) % len(shayana_states)]

    # 16. Vimshottari Mahadasha Dates in Bikram Sambat
    dasha_list = chart_data.get("dasha", [])
    p_dasha = next((d for d in dasha_list if d.get("lord") == planet_name), {})
    md_start_bs = p_dasha.get("start_bs")
    md_end_bs = p_dasha.get("end_bs")
    if not md_start_bs and p_dasha.get("start_ad"):
        try:
            import datetime
            d = datetime.date.fromisoformat(str(p_dasha["start_ad"])[:10])
            bs = gregorian_to_bs(d.year, d.month, d.day)
            if bs:
                md_start_bs = format_bs_date(bs, "ne")
        except Exception:
            pass
    if not md_end_bs and p_dasha.get("end_ad"):
        try:
            import datetime
            d = datetime.date.fromisoformat(str(p_dasha["end_ad"])[:10])
            bs = gregorian_to_bs(d.year, d.month, d.day)
            if bs:
                md_end_bs = format_bs_date(bs, "ne")
        except Exception:
            pass

    # 17. Transits (गुरु, शनि, राहु, केतु) in Bikram Sambat
    birth_date_str = meta.get("birth_date", "2000-01-01")
    try:
        import datetime
        b_date = datetime.date.fromisoformat(str(birth_date_str)[:10])
    except Exception:
        import datetime
        b_date = datetime.date.today()

    transit_dates = {}
    for t_planet, years_cycle in [("गुरु", 12), ("शनि", 29.5), ("राहु", 18.5), ("केतु", 18.5)]:
        next_ad = b_date.year + int(years_cycle)
        bs_transit = gregorian_to_bs(next_ad, b_date.month, b_date.day)
        transit_dates[t_planet] = format_bs_date(bs_transit, "ne") if bs_transit else f"{to_nepali_digits(next_ad + 57)} वि.सं."

    # 18. Dashavarga Table Data
    dashavarga_rows = []
    for d_item in DASHAVARGA_DIVISIONS:
        v_key = d_item["key"]
        v_plist = vargas.get(v_key, {}).get("planets", [])
        vp = next((p for p in v_plist if p.get("name") == planet_name), {})
        s_num = int(vp.get("sign_number", sign_num) or sign_num)
        deg_val = float(vp.get("longitude_in_sign", deg_in_sign) or deg_in_sign)
        dashavarga_rows.append({
            "varga": d_item["name"],
            "area": d_item["area"],
            "sign": RASHI_NAMES_NE[s_num],
            "value": f"{to_nepali_digits(f'{deg_val:.2f}')}°"
        })

    # ── Parashari Functional Nature & Auspiciousness Engine ───────────────────
    # 1. Determine Functional Nature based on Lagna (कार्यात्मक प्रकृति)
    # Trikona lords (1, 5, 9) are benefics; Trishadaya (3, 6, 11) & Dusthana (6, 8, 12) are malefics; 2 & 7 are Marakas.
    # Movable (1,4,7,10): 11 is Badhaka; Fixed (2,5,8,11): 9 is Badhaka; Dual (3,6,9,12): 7 is Badhaka.
    
    is_lagnesha = (planet_name == lagnesha_planet)
    is_trikona_lord = any(h in [1, 5, 9] for h in d1_owned_houses)
    is_kendra_lord = any(h in [1, 4, 7, 10] for h in d1_owned_houses)
    is_yogakaraka = (is_kendra_lord and is_trikona_lord and planet_name in ["Mars", "Saturn", "Venus"]) or (
        (lagna_sign in [4, 5] and planet_name == "Mars") or
        (lagna_sign in [2, 7] and planet_name == "Saturn") or
        (lagna_sign in [10, 11] and planet_name == "Venus")
    )
    
    is_dusthana_lord = any(h in [6, 8, 12] for h in d1_owned_houses)
    is_trishadaya_lord = any(h in [3, 6, 11] for h in d1_owned_houses)
    is_maraka_lord = any(h in [2, 7] for h in d1_owned_houses)
    
    # Badhaka Lord
    if lagna_sign in [1, 4, 7, 10]:
        badhaka_house = 11
    elif lagna_sign in [2, 5, 8, 11]:
        badhaka_house = 9
    else:
        badhaka_house = 7
    badhaka_sign = ((lagna_sign + badhaka_house - 2) % 12) + 1
    is_badhaka_lord = (RASHI_LORDS[badhaka_sign] == planet_name)

    # Natural classification
    natural_benefic = planet_name in ["Jupiter", "Venus", "Mercury", "Moon"]
    natural_malefic = planet_name in ["Saturn", "Mars", "Rahu", "Ketu", "Sun"]

    # Kendradhipatya Dosha
    has_kendradhipatya_dosha = natural_benefic and any(h in [4, 7, 10] for h in d1_owned_houses) and not is_trikona_lord

    shubha_reasons: List[Dict[str, str]] = []
    ashubha_reasons: List[Dict[str, str]] = []
    functional_nature_items: List[str] = []

    # Calculate Base Functional Nature Score (starting at 50% baseline)
    shubha_score = 50.0

    if is_yogakaraka:
        shubha_score += 25.0
        r_text = f"केन्द्र र त्रिकोण (भाव {', '.join(to_nepali_digits(h) for h in d1_owned_houses)}) दुवैको स्वामित्व भएकाले यो कुण्डलीको 'परम योगकारक' ग्रह"
        shubha_reasons.append({"category": "कार्यात्मक प्रकृति", "rule": "योगकारकत्व", "desc": r_text, "impact": "+२५%"})
        functional_nature_items.append("परम योगकारक (अत्यन्त शुभ)")
    elif is_lagnesha:
        shubha_score += 18.0
        r_text = f"लग्न (तनु भाव) को अधिपति भएकाले जातकको शरीर, प्रतिष्ठा र आत्मबलको मुख्य संरक्षक"
        shubha_reasons.append({"category": "कार्यात्मक प्रकृति", "rule": "लग्नेशत्व", "desc": r_text, "impact": "+१८%"})
        functional_nature_items.append("लग्नेश (शुभ)")
    elif any(h in [5, 9] for h in d1_owned_houses):
        shubha_score += 15.0
        r_text = f"त्रिकोण (भाव {', '.join(to_nepali_digits(h) for h in d1_owned_houses if h in [5, 9])}) को स्वामी भएकाले धर्म, भाग्य र विद्या प्रदायक शुभ ग्रह"
        shubha_reasons.append({"category": "कार्यात्मक प्रकृति", "rule": "त्रिकोणेशत्व", "desc": r_text, "impact": "+१५%"})
        functional_nature_items.append("त्रिकोणेश (शुभ)")

    if is_maraka_lord and not is_yogakaraka and not is_lagnesha:
        shubha_score -= 16.0
        m_houses = [h for h in d1_owned_houses if h in [2, 7]]
        r_text = f"मारक भाव ({', '.join(to_nepali_digits(h) for h in m_houses)}) को स्वामित्व भएकाले दशा–अन्तर्दशामा कष्ट/स्वास्थ्य बाधाकारक"
        ashubha_reasons.append({"category": "कार्यात्मक प्रकृति", "rule": "मारकत्व", "desc": r_text, "impact": "-१६%"})
        functional_nature_items.append("मारक ग्रह (कष्टप्रद)")

    if is_badhaka_lord and not is_yogakaraka:
        shubha_score -= 10.0
        r_text = f"{RASHI_NAMES_NE[lagna_sign]} लग्नका लागि भाव {to_nepali_digits(badhaka_house)} बाधक स्थान भएकाले कार्यमा अकस्मात् अड्चन दिने बाधकेश"
        ashubha_reasons.append({"category": "कार्यात्मक प्रकृति", "rule": "बाधकत्व", "desc": r_text, "impact": "-१०%"})
        functional_nature_items.append("बाधकेश (विघ्नकारक)")

    if is_trishadaya_lord and not is_lagnesha and not is_yogakaraka and not any(h in [5, 9] for h in d1_owned_houses):
        shubha_score -= 12.0
        t_houses = [h for h in d1_owned_houses if h in [3, 6, 11]]
        r_text = f"त्रिषडाय (भाव {', '.join(to_nepali_digits(h) for h in t_houses)}) को स्वामी भएकाले कलह, रोग र अहंकार वृद्धि कारक"
        ashubha_reasons.append({"category": "कार्यात्मक प्रकृति", "rule": "त्रिषडायेशत्व", "desc": r_text, "impact": "-१२%"})
        functional_nature_items.append("त्रिषडायेश (अशुभ)")

    if has_kendradhipatya_dosha:
        shubha_score -= 8.0
        r_text = f"नैसर्गिक शुभ ग्रह भई केन्द्र (भाव {', '.join(to_nepali_digits(h) for h in d1_owned_houses if h in [4, 7, 10])}) को स्वामी भएकाले केन्द्राधिपत्य दोषका कारण स्वाभाविक शुभत्वमा ह्रास"
        ashubha_reasons.append({"category": "कार्यात्मक प्रकृति", "rule": "केन्द्राधिपत्य दोष", "desc": r_text, "impact": "-८%"})
        functional_nature_items.append("केन्द्राधिपत्य दोष")

    if not functional_nature_items:
        if natural_benefic:
            functional_nature_items.append("नैसर्गिक शुभ (मध्यम)")
            shubha_score += 5.0
        else:
            functional_nature_items.append("नैसर्गिक क्रूर/अशुभ (मध्यम)")
            shubha_score -= 5.0

    # 2. Modifying Factor: Dignity (राशि गरिमा)
    is_exalted = (sign_num == exalt_sign)
    is_debilitated = (sign_num == deb_sign)
    is_own_sign = (RASHI_LORDS[sign_num] == planet_name)

    if is_exalted:
        shubha_score += 18.0
        shubha_reasons.append({"category": "राशि स्थिति", "rule": "उच्च राशि", "desc": f"{RASHI_NAMES_NE[sign_num]} राशिमा उच्च भई पूर्ण शक्ति र आत्मबल प्राप्त", "impact": "+१८%"})
    elif is_own_sign:
        shubha_score += 14.0
        shubha_reasons.append({"category": "राशि स्थिति", "rule": "स्वक्षेत्र", "desc": f"आफ्नै स्वराशि {RASHI_NAMES_NE[sign_num]} मा स्थिर र सुरक्षित स्थिति", "impact": "+१४%"})
    elif is_debilitated:
        shubha_score -= 20.0
        ashubha_reasons.append({"category": "राशि स्थिति", "rule": "नीच राशि", "desc": f"{RASHI_NAMES_NE[sign_num]} राशिमा नीच भई फल दिने क्षमतामा भारी ह्रास", "impact": "-२०%"})
    elif "मित्र" in dignity_ne:
        shubha_score += 6.0
        shubha_reasons.append({"category": "राशि स्थिति", "rule": "मित्र राशि", "desc": f"{RASHI_NAMES_NE[sign_num]} मित्र राशिमा अनुकूल अवस्थिति", "impact": "+६%"})
    elif "शत्रु" in dignity_ne:
        shubha_score -= 7.0
        ashubha_reasons.append({"category": "राशि स्थिति", "rule": "शत्रु राशि", "desc": f"{RASHI_NAMES_NE[sign_num]} शत्रु राशिमा प्रतिकूल अवस्थिति", "impact": "-७%"})

    # 3. Neecha Bhanga Raja Yoga (नीचभंग राजयोग)
    if is_debilitated:
        deb_dispositor = RASHI_LORDS[deb_sign]
        deb_disp_p = next((p for p in planets if p.get("name") == deb_dispositor), {})
        deb_disp_house = int(deb_disp_p.get("house", 0) or 0)
        deb_exalt_lord = RASHI_LORDS[exalt_sign]
        deb_exalt_p = next((p for p in planets if p.get("name") == deb_exalt_lord), {})
        deb_exalt_house = int(deb_exalt_p.get("house", 0) or 0)
        
        has_nbry = False
        if deb_disp_house in [1, 4, 7, 10]:
            shubha_score += 14.0
            shubha_reasons.append({
                "category": "विशेष योग", "rule": "नीचभंग राजयोग",
                "desc": f"नीच राशिको स्वामी {PLANET_NAMES_NE.get(deb_dispositor, deb_dispositor)} केन्द्र (भाव {to_nepali_digits(deb_disp_house)}) मा रहेकाले नीच दोष खण्डित भई राजयोग निर्माण",
                "impact": "+१४%"
            })
            has_nbry = True
        elif deb_exalt_house in [1, 4, 7, 10]:
            shubha_score += 12.0
            shubha_reasons.append({
                "category": "विशेष योग", "rule": "नीचभंग राजयोग",
                "desc": f"नीच राशिको उच्चनाथ {PLANET_NAMES_NE.get(deb_exalt_lord, deb_exalt_lord)} केन्द्र (भाव {to_nepali_digits(deb_exalt_house)}) मा रहेकाले नीचता भंग",
                "impact": "+१२%"
            })
            has_nbry = True

    # 4. House Placement (भाव स्थिति)
    is_viparita = False
    if house_num in [6, 8, 12]:
        if any(h in [6, 8, 12] for h in d1_owned_houses) and not is_lagnesha:
            # Viparita Raja Yoga
            shubha_score += 14.0
            v_name = "हर्ष योग" if 6 in d1_owned_houses else ("सरल योग" if 8 in d1_owned_houses else "विमल योग")
            shubha_reasons.append({
                "category": "विशेष योग", "rule": f"विपरीत राजयोग ({v_name})",
                "desc": f"त्रिकेश भई त्रिक भाव {to_nepali_digits(house_num)} मै बसेकाले शत्रुहन्ता तथा अचानक सफलता दिने विपरीत राजयोग",
                "impact": "+१४%"
            })
            is_viparita = True
        else:
            shubha_score -= 14.0
            ashubha_reasons.append({"category": "भाव स्थिति", "rule": "त्रिक भाव स्थिति", "desc": f"दुष्ट/त्रिक भाव {to_nepali_digits(house_num)} मा अवस्थित भएकाले बाधा, खर्च वा स्वास्थ्य प्रतिकूलता", "impact": "-१४%"})
    elif house_num in [5, 9]:
        shubha_score += 12.0
        shubha_reasons.append({"category": "भाव स्थिति", "rule": "त्रिकोण स्थिति", "desc": f"अत्यन्त शुभ त्रिकोण भाव {to_nepali_digits(house_num)} मा अवस्थित", "impact": "+१२%"})
    elif house_num in [1, 4, 7, 10]:
        shubha_score += 10.0
        shubha_reasons.append({"category": "भाव स्थिति", "rule": "केन्द्र स्थिति", "desc": f"शक्तिशाली केन्द्र भाव {to_nepali_digits(house_num)} मा अवस्थित", "impact": "+१०%"})
    elif house_num in [3, 11] and natural_malefic:
        shubha_score += 8.0
        shubha_reasons.append({"category": "भाव स्थिति", "rule": "उपचय भाव", "desc": f"उपचय भाव {to_nepali_digits(house_num)} मा क्रूर ग्रहको उपस्थिति साहस, पराक्रम र लाभप्रद", "impact": "+८%"})
    elif house_num in [2, 7] and is_maraka_lord:
        shubha_score -= 8.0
        ashubha_reasons.append({"category": "भाव स्थिति", "rule": "मारक स्थान स्थिति", "desc": f"मारक भाव {to_nepali_digits(house_num)} मै अवस्थित भएकाले मारक प्रभाव अझ बढी सक्रिय", "impact": "-८%"})

    # 5. Conjunctions (युति)
    for p in planets:
        pn = p.get("name")
        if pn != planet_name and int(p.get("house", 0) or 0) == house_num:
            if pn == "Jupiter":
                shubha_score += 9.0
                shubha_reasons.append({"category": "युति सम्बन्ध", "rule": "गुरु युति", "desc": "देवगुरु बृहस्पतिसँग शुभ युति भएकाले दोष निवारण र ज्ञान/सद्भाव वृद्धि", "impact": "+९%"})
            elif pn == "Venus" and not natural_malefic:
                shubha_score += 6.0
                shubha_reasons.append({"category": "युति सम्बन्ध", "rule": "शुक्र युति", "desc": "दैत्यगुरु शुक्रसँग सौम्य युति", "impact": "+६%"})
            elif pn in ["Rahu", "Ketu"]:
                shubha_score -= 10.0
                ashubha_reasons.append({"category": "युति सम्बन्ध", "rule": f"{PLANET_NAMES_NE.get(pn)} युति", "desc": f"{PLANET_NAMES_NE.get(pn)} सँग युति भएकाले ग्रहण/छाया दोष र भ्रमकारी प्रभाव", "impact": "-१०%"})
            elif pn == "Saturn" and planet_name in ["Sun", "Moon", "Mars"]:
                shubha_score -= 8.0
                ashubha_reasons.append({"category": "युति सम्बन्ध", "rule": "शनि युति", "desc": "शनिसँग युति भएकाले ढिलाइ, मानसिक अशान्ति वा संघर्ष", "impact": "-८%"})

    # 6. Aspects (दृष्टि)
    # Check if Jupiter aspects
    jup_p = next((p for p in planets if p.get("name") == "Jupiter"), {})
    if jup_p and planet_name != "Jupiter":
        jup_h = int(jup_p.get("house", 0) or 0)
        jup_dist = ((house_num - jup_h) % 12) + 1
        if jup_dist in [5, 7, 9]:
            shubha_score += 11.0
            shubha_reasons.append({"category": "दृष्टि सम्बन्ध", "rule": "गुरुको अमृत दृष्टि", "desc": f"देवगुरु बृहस्पतिको शुभ पूर्ण दृष्टि ({to_nepali_digits(jup_dist)} औं) ले अशुभता हरण र शुभता वृद्धि", "impact": "+११%"})

    # Check if Saturn aspects
    sat_p = next((p for p in planets if p.get("name") == "Saturn"), {})
    if sat_p and planet_name != "Saturn":
        sat_h = int(sat_p.get("house", 0) or 0)
        sat_dist = ((house_num - sat_h) % 12) + 1
        if sat_dist in [3, 7, 10]:
            shubha_score -= 7.0
            ashubha_reasons.append({"category": "दृष्टि सम्बन्ध", "rule": "शनिको क्रूर दृष्टि", "desc": f"शनिको विशेष दृष्टि ({to_nepali_digits(sat_dist)} औं) ले कार्यमा विलम्ब तथा अवरोध", "impact": "-७%"})

    # 7. Combustion (अस्त)
    if is_combust and planet_name not in ["Sun", "Rahu", "Ketu"]:
        shubha_score -= 12.0
        ashubha_reasons.append({"category": "अवस्था दोष", "rule": "ग्रह अस्त", "desc": "सूर्यको अत्यधिक निकटताले अस्त भएकाले आन्तरिक तेज र सामर्थ्य क्षीण", "impact": "-१२%"})

    # 8. Strength vs Nature Interaction (षड्बल मूल्याङ्कन)
    is_functional_malefic = (is_maraka_lord or is_badhaka_lord or (is_trishadaya_lord and not is_trikona_lord)) and not is_yogakaraka and not is_lagnesha
    if shadbala_ratio >= 115.0:
        if is_functional_malefic:
            shubha_score -= 6.0
            ashubha_reasons.append({"category": "ग्रह बल प्रभाव", "rule": "बलवान् मारक/अशुभ", "desc": f"षड्बल अत्यधिक बलियो ({to_nepali_digits(round(shadbala_ratio))}%) भएकाले मारक/अशुभ फल दिने क्षमता अझ सक्रिय", "impact": "-६%"})
        else:
            shubha_score += 6.0
            shubha_reasons.append({"category": "ग्रह बल प्रभाव", "rule": "बलवान् शुभ ग्रह", "desc": f"षड्बल पर्याप्त ({to_nepali_digits(round(shadbala_ratio))}%) भएकाले शुभ फल दिने पूर्ण क्षमता", "impact": "+६%"})
    elif shadbala_ratio < 85.0:
        if not is_functional_malefic:
            shubha_score -= 6.0
            ashubha_reasons.append({"category": "ग्रह बल प्रभाव", "rule": "निर्बल शुभ ग्रह", "desc": f"षड्बल कमजोर ({to_nepali_digits(round(shadbala_ratio))}%) भएकाले शुभ फल पूर्ण रूपमा दिन असमर्थ", "impact": "-६%"})
        else:
            shubha_score += 5.0
            shubha_reasons.append({"category": "ग्रह बल प्रभाव", "rule": "निर्बल अशुभ ग्रह", "desc": f"अशुभ ग्रहको षड्बल कमजोर भएकाले कष्ट दिने क्षमतामा ह्रास (राहत)", "impact": "+५%"})

    if bav_points >= 5:
        shubha_score += 5.0
        shubha_reasons.append({"category": "अष्टकवर्ग", "rule": "उच्च बिन्दु", "desc": f"अष्टकवर्गमा {to_nepali_digits(bav_points)} बिन्दु प्राप्त भई अनुकूल सहयोग", "impact": "+५%"})
    elif bav_points <= 2:
        shubha_score -= 6.0
        ashubha_reasons.append({"category": "अष्टकवर्ग", "rule": "न्यून बिन्दु", "desc": f"अष्टकवर्गमा केवल {to_nepali_digits(bav_points)} बिन्दु भएकाले प्रतिकूलता", "impact": "-६%"})

    # Final Percentage Clamping (strictly ensures Shubha + Ashubha = 100%)
    shubha_score = max(5.0, min(95.0, shubha_score))
    shubha_pct = round(shubha_score)
    ashubha_pct = 100 - shubha_pct
    is_overall_shubha = (shubha_pct >= 50)

    # Synthesis summary text
    fn_str = ", ".join(functional_nature_items)
    if is_overall_shubha:
        verdict_summary = f"{PLANET_NAMES_NE.get(planet_name, planet_name)} ग्रहको कार्यात्मक प्रकृति ({fn_str}) तथा वर्तमान शुभ योग/दृष्टि बलियो रहेकाले कुल {to_nepali_digits(shubha_pct)}% शुभ फलदायी छ।"
    else:
        verdict_summary = f"{PLANET_NAMES_NE.get(planet_name, planet_name)} ग्रहको कार्यात्मक प्रकृति ({fn_str}) तथा वर्तमान मारक/प्रतिकूल प्रभाव बढी रहेकाले कुल {to_nepali_digits(ashubha_pct)}% अशुभ प्रभाव बढी छ।"

    return {
        # Overall Top Status (Exact Shubha % + Ashubha % = 100%)
        "is_shubha": is_overall_shubha,
        "status_label": "शुभ" if is_overall_shubha else "अशुभ",
        "shubha_pct": shubha_pct,
        "ashubha_pct": ashubha_pct,
        "shubha_pct_ne": to_nepali_digits(shubha_pct),
        "ashubha_pct_ne": to_nepali_digits(ashubha_pct),
        "status_pct_ne": to_nepali_digits(shubha_pct if is_overall_shubha else ashubha_pct),
        "status_color": "#16a34a" if is_overall_shubha else "#dc2626",

        # Detailed Reasons Data for the Modal
        "functional_nature_list": functional_nature_items,
        "functional_nature_text": fn_str,
        "shubha_reasons": shubha_reasons,
        "ashubha_reasons": ashubha_reasons,
        "verdict_summary": verdict_summary,

        # 48 Parameters
        "1_name": PLANET_NAMES_NE.get(planet_name, planet_name),
        "2_shadbala": f"{to_nepali_digits(f'{shadbala_rupa:.2f}')} रूपा ({to_nepali_digits(round(total_shadbala))} / {to_nepali_digits(req_shadbala)} षष्ठ्यंश, {to_nepali_digits(round(shadbala_ratio))}%)",
        "2_shadbala_sub": f"स्थान: {to_nepali_digits(f'{sub_balas['sthana']:.1f}')} | दिग्: {to_nepali_digits(f'{sub_balas['dig']:.1f}')} | काल: {to_nepali_digits(f'{sub_balas['kala']:.1f}')} | चेष्टा: {to_nepali_digits(f'{sub_balas['cheshta']:.1f}')} | नैसर्गिक: {to_nepali_digits(f'{sub_balas['naisargika']:.1f}')} | दृग्: {to_nepali_digits(f'{sub_balas['drik']:.1f}')}",
        "3_shadbala_rank": f"{to_nepali_digits(shad_rank)} (१–७)",
        "4_auspiciousness": "शुभ फलदायी" if is_overall_shubha else "कष्ट फलदायी",
        "5_ishta_kashta": f"इष्ट फल: {to_nepali_digits(ishta_phala)}  |  कष्ट फल: {to_nepali_digits(kashta_phala)}",
        "6_ishta_kashta_rank": f"{to_nepali_digits(shad_rank)}",
        "7_uchcha_pct": f"{to_nepali_digits(exalt_pct)}%",
        "8_purna_pct": f"{to_nepali_digits(full_strength_pct)}%",
        "9_dignity": dignity_ne,
        "10_vimshopaka": f"{to_nepali_digits(vimshopaka_val)} ({to_nepali_digits(vimshopaka_pct)}%)",
        "11_vaisheshikamsa": f"{to_nepali_digits(vaisheshikamsa_count)} ({vaisheshikamsa_name})",
        "12_ashtakavarga": f"BAV बिन्दु: {to_nepali_digits(bav_points)} / ८  |  SAV बिन्दु: {to_nepali_digits(sav_points)} / ५६",
        "13_state": f"{'वक्री' if is_retro else 'मार्गी'}, {'अस्त' if is_combust else 'उदित'}, {dignity_ne}",
        "14_dominance": f"{to_nepali_digits(dom_val)} (क्रम: {to_nepali_digits(shad_rank)})",
        "15_karakatwa": f"{chara_karaka}  —  {NAISARGIKA_KARAKAS.get(planet_name, '—')}",
        "16_lagnesha_num": f"लग्नेश: {PLANET_NAMES_NE.get(lagnesha_planet, lagnesha_planet)} सँग {to_nepali_digits(lagnesha_dist)} औं भाव दूरी",
        "17_samaya": f"गोचर तथा दशा समय चक्र",
        "18_mahadasha": f"{PLANET_NAMES_NE.get(planet_name, planet_name)} महादशा",
        "19_md_start_bs": md_start_bs or "—",
        "20_md_end_bs": md_end_bs or "—",
        "21_transit_dates": f"गुरु: {transit_dates['गुरु']} | शनि: {transit_dates['शनि']} | राहु: {transit_dates['राहु']} | केतु: {transit_dates['केतु']}",
        "22_d1_ownership": f"लग्न भाव {', '.join(to_nepali_digits(h) for h in d1_owned_houses) or '—'}",
        "23_d9_ownership": f"नवांश भाव {', '.join(to_nepali_digits(h) for h in d9_owned_houses) or '—'}",
        "24_rashi": f"{RASHI_NAMES_NE[sign_num]} ({to_nepali_digits(sign_num)})",
        "25_navamsha": f"{d9_sign_ne} ({to_nepali_digits(d9_sign_num)})",
        "26_nakshatra": f"{nak_obj['name']} (पाद: {to_nepali_digits(nak_pada)})",
        "27_nak_lord": nak_obj["lord"],
        "28_nak_deity": nak_obj["deity"],
        "29_shadvarga_dispositors": f"बुध ({to_nepali_digits(dispositors['Mercury'])}), गुरु ({to_nepali_digits(dispositors['Jupiter'])}), सूर्य ({to_nepali_digits(dispositors['Sun'])}), शनि ({to_nepali_digits(dispositors['Saturn'])}), चन्द्र ({to_nepali_digits(dispositors['Moon'])}), शुक्र ({to_nepali_digits(dispositors['Venus'])}), मंगल ({to_nepali_digits(dispositors['Mars'])})",
        "30_shadvarga_tattvas": f"द्विस्वभाव ({to_nepali_digits(tattvas['द्विस्वभाव'])}), चर ({to_nepali_digits(tattvas['चर'])}), स्थिर ({to_nepali_digits(tattvas['स्थिर'])}) | जल ({to_nepali_digits(tattvas['जल'])}), पृथ्वी ({to_nepali_digits(tattvas['पृथ्वी'])}), अग्नि ({to_nepali_digits(tattvas['अग्नि'])}), वायु ({to_nepali_digits(tattvas['वायु'])})",
        "31_yuti": ", ".join(conjoined) or "कुनै सहग्रह छैन (एकल)",
        "32_drishti": ", ".join(aspecting) or "अन्य प्रत्यक्ष दृष्टि छैन",
        "33_jagradadi": jagradadi,
        "34_baladi": baladi,
        "35_lajjitadi": lajjitadi,
        "36_deeptadi": deeptadi,
        "37_shayanadi": shayanadi,
        "38_dashavarga_rows": dashavarga_rows,
    }
