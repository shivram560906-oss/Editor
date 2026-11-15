"""
backend/calculator/sudarshan_analysis.py

बृहत् पाराशर होरा शास्त्र (BPHS) अध्याय ७४ अनुसार सुदर्शन चक्र विश्लेषण।
सुदर्शन चक्रले तीन प्रमुख विन्दुहरू:
  १. लग्न कुण्डली (शरीर, बाह्य व्यक्तित्व, भौतिक स्वास्थ्य)
  २. चन्द्र कुण्डली (मन, भावना, आन्तरिक सुख, मानसिक स्थिति)
  ३. सूर्य कुण्डली (आत्मा, इच्छाशक्ति, पिता, प्रतिष्ठा, सामाजिक प्रभाव)
बाट एकसाथ कुण्डलीको १२ भाव र ९ ग्रहहरूको संयुक्त फलको विश्लेषण गर्दछ।
"""
from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Tuple

SIGN_NAMES_NE = [
    "मेष", "वृष", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
]
SIGN_NAMES_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल",
    "Mercury": "बुध", "Jupiter": "गुरु", "Venus": "शुक्र",
    "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
}
HOUSE_NAMES_NE = {
    1: "प्रथम भाव (तन/शरीर)", 2: "द्वितीय भाव (धन/वाणी)", 3: "तृतीय भाव (पराक्रम/भ्राता)",
    4: "चतुर्थ भाव (सुख/माता/गृह)", 5: "पञ्चम भाव (विद्या/सन्तान/बुद्धि)", 6: "षष्ठ भाव (रोग/ऋण/शत्रु)",
    7: "सप्तम भाव (दाम्पत्य/साझेदारी)", 8: "अष्टम भाव (आयु/संकट)", 9: "नवम भाव (भाग्य/धर्म)",
    10: "दशम भाव (कर्म/करियर/पद)", 11: "एकादश भाव (लाभ/आय)", 12: "द्वादश भाव (व्यय/मोक्ष)"
}

NAT_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NAT_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def _get_sign_num(planet_or_lagna: Any) -> int:
    """Helper to extract 1-indexed sign number from planet dict or int."""
    if isinstance(planet_or_lagna, dict):
        if "sign_number" in planet_or_lagna and planet_or_lagna["sign_number"]:
            return int(planet_or_lagna["sign_number"])
        lon = float(planet_or_lagna.get("sidereal_longitude", planet_or_lagna.get("longitude", 0)) or 0)
        return (int(lon / 30.0) % 12) + 1
    elif isinstance(planet_or_lagna, (int, float)):
        return int(planet_or_lagna)
    return 1


def analyze_sudarshan_chakra(chart_data: dict, language: str = "ne") -> dict:
    """
    Perform deep BPHS-compliant Sudarshan Chakra analysis.
    Returns:
      - references: {lagna_sign, moon_sign, sun_sign}
      - houses_analysis: list of 12 house analysis items
      - planets_analysis: list of 9 planets placement from 3 angles
      - sudarshan_dasha: active sudarshan year/dasha predictions
      - harmony_score: percentage
      - conclusion: one-sentence executive summary
      - remedies: list of remedies
    """
    if not isinstance(chart_data, dict):
        chart_data = {}

    planets_raw = chart_data.get("planets", [])
    planets = []
    for p in planets_raw:
        if isinstance(p, dict) and p.get("name"):
            s_num = _get_sign_num(p)
            planets.append({
                "name": p["name"],
                "name_ne": PLANET_NAMES_NE.get(p["name"], p["name"]),
                "sign_number": s_num,
                "is_retrograde": bool(p.get("is_retrograde", False)),
                "is_combust": bool(p.get("is_combust", False)),
            })

    by_name = {p["name"]: p for p in planets}

    # Reference signs
    lagna_sign = _get_sign_num(chart_data.get("lagna", {}))
    moon_sign = _get_sign_num(by_name.get("Moon", {"sign_number": 1}))
    sun_sign = _get_sign_num(by_name.get("Sun", {"sign_number": 1}))

    # 1. House-by-House Analysis from all 3 Reference Points
    houses_analysis = []
    total_shubha_points = 0
    total_possible_points = 12 * 3  # 36

    for h in range(1, 13):
        # Sign for house h from Lagna, Moon, and Sun
        l_sign = ((lagna_sign - 1 + h - 1) % 12) + 1
        m_sign = ((moon_sign - 1 + h - 1) % 12) + 1
        s_sign = ((sun_sign - 1 + h - 1) % 12) + 1

        l_planets = [p["name_ne"] for p in planets if p["sign_number"] == l_sign]
        m_planets = [p["name_ne"] for p in planets if p["sign_number"] == m_sign]
        s_planets = [p["name_ne"] for p in planets if p["sign_number"] == s_sign]

        l_p_raw = [p["name"] for p in planets if p["sign_number"] == l_sign]
        m_p_raw = [p["name"] for p in planets if p["sign_number"] == m_sign]
        s_p_raw = [p["name"] for p in planets if p["sign_number"] == s_sign]

        # Scoring strength from 3 reference points
        l_ben = any(p in NAT_BENEFICS for p in l_p_raw)
        m_ben = any(p in NAT_BENEFICS for p in m_p_raw)
        s_ben = any(p in NAT_BENEFICS for p in s_p_raw)

        score = 0
        if l_ben or (not any(p in NAT_MALEFICS for p in l_p_raw) and l_planets):
            score += 1
        elif not l_planets and h in (1, 4, 5, 9, 10, 11):
            score += 0.5

        if m_ben or (not any(p in NAT_MALEFICS for p in m_p_raw) and m_planets):
            score += 1
        elif not m_planets and h in (1, 4, 5, 9, 10, 11):
            score += 0.5

        if s_ben or (not any(p in NAT_MALEFICS for p in s_p_raw) and s_planets):
            score += 1
        elif not s_planets and h in (1, 4, 5, 9, 10, 11):
            score += 0.5

        total_shubha_points += score

        # Verdict for house
        if score >= 2.5:
            h_verdict = "अत्यन्त बलवान् (पूर्ण शुभ)"
            h_color = "#15803d"
        elif score >= 1.5:
            h_verdict = "मध्यम शुभ (अनुकूल)"
            h_color = "#2563eb"
        elif score >= 0.5:
            h_verdict = "मिश्रित फलदायक"
            h_color = "#d97706"
        else:
            h_verdict = "कमजोर/सावधानी आवश्यक"
            h_color = "#b91c1c"

        houses_analysis.append({
            "house": h,
            "house_name": HOUSE_NAMES_NE.get(h, f"{h}औं भाव"),
            "lagna_sign_num": l_sign,
            "lagna_sign_name": SIGN_NAMES_NE[l_sign - 1],
            "lagna_planets": l_planets,
            "moon_sign_num": m_sign,
            "moon_sign_name": SIGN_NAMES_NE[m_sign - 1],
            "moon_planets": m_planets,
            "sun_sign_num": s_sign,
            "sun_sign_name": SIGN_NAMES_NE[s_sign - 1],
            "sun_planets": s_planets,
            "score": round(score, 1),
            "verdict": h_verdict,
            "verdict_color": h_color,
        })

    # 2. Planetary Strength across 3 Reference Points
    planets_analysis = []
    for p in planets:
        p_name = p["name"]
        p_sign = p["sign_number"]
        h_from_l = ((p_sign - lagna_sign) % 12) + 1
        h_from_m = ((p_sign - moon_sign) % 12) + 1
        h_from_s = ((p_sign - sun_sign) % 12) + 1

        kendra_count = sum(1 for h in (h_from_l, h_from_m, h_from_s) if h in (1, 4, 7, 10))
        trikona_count = sum(1 for h in (h_from_l, h_from_m, h_from_s) if h in (1, 5, 9))

        planets_analysis.append({
            "name": p_name,
            "name_ne": p["name_ne"],
            "sign_name": SIGN_NAMES_NE[p_sign - 1],
            "house_from_lagna": h_from_l,
            "house_from_moon": h_from_m,
            "house_from_sun": h_from_s,
            "kendra_count": kendra_count,
            "trikona_count": trikona_count,
            "is_retrograde": p["is_retrograde"],
            "is_combust": p["is_combust"],
        })

    # 3. Sudarshan Dasha (BPHS Chapter 74 - 1 Year per House Sequential Progression)
    birth_date_str = (
        chart_data.get("metadata", {}).get("birth_date")
        or chart_data.get("birth_date")
        or chart_data.get("date")
        or chart_data.get("input", {}).get("birth_date")
    )
    # If not found directly, extract from dasha start or panchang
    if not birth_date_str and isinstance(chart_data.get("dasha"), list) and chart_data["dasha"]:
        birth_date_str = str(chart_data["dasha"][0].get("start", ""))[:10]

    current_year_age = 1
    bs_date_display = ""
    if birth_date_str:
        try:
            b_date = datetime.date.fromisoformat(str(birth_date_str)[:10])
            today = datetime.date.today()
            age_years = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
            current_year_age = max(1, age_years + 1)
            
            # Convert to Bikram Sambat (BS)
            try:
                import nepali_datetime
                bs = nepali_datetime.date.from_datetime_date(b_date)
                nep_digits = str.maketrans("0123456789", "०१२३४५६७८९")
                bs_raw = f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d}"
                bs_date_display = f"वि.सं. {bs_raw.translate(nep_digits)}"
            except Exception:
                nep_digits = str.maketrans("0123456789", "०१२३४५६७८९")
                bs_date_display = str(birth_date_str).translate(nep_digits)
        except Exception:
            current_year_age = 1

    nep_digits = str.maketrans("0123456789", "०१२३४५६७८९")
    age_str_ne = f"{str(current_year_age).translate(nep_digits)}औँ वर्ष"

    # Active house in Sudarshan Chakra Dasha: (age - 1) % 12 + 1
    active_dasha_house = ((current_year_age - 1) % 12) + 1
    active_l_sign = ((lagna_sign - 1 + active_dasha_house - 1) % 12) + 1
    active_m_sign = ((moon_sign - 1 + active_dasha_house - 1) % 12) + 1
    active_s_sign = ((sun_sign - 1 + active_dasha_house - 1) % 12) + 1

    active_h_info = HOUSE_NAMES_NE.get(active_dasha_house, f"{active_dasha_house}औँ भाव")

    date_label = bs_date_display or str(birth_date_str).translate(nep_digits)

    sudarshan_dasha = {
        "birth_date": birth_date_str,
        "birth_date_bs": bs_date_display,
        "current_age_year": current_year_age,
        "current_age_year_ne": age_str_ne,
        "active_house": active_dasha_house,
        "active_house_name": active_h_info,
        "lagna_active_sign": SIGN_NAMES_NE[active_l_sign - 1],
        "moon_active_sign": SIGN_NAMES_NE[active_m_sign - 1],
        "sun_active_sign": SIGN_NAMES_NE[active_s_sign - 1],
        "summary": (
            f"सुदर्शन चक्र दशा (BPHS अ. ७४) अनुसार जातकको जन्म मिति ({date_label}) को आधारमा "
            f"हाल {age_str_ne} चलिरहेको छ। "
            f"यस वर्ष सुदर्शन चक्रको {active_h_info} सक्रिय छ।\n"
            f"• भौतिक/स्वास्थ्य फल: {SIGN_NAMES_NE[active_l_sign - 1]} राशि (लग्नबाट)\n"
            f"• मानसिक/पारिवारिक फल: {SIGN_NAMES_NE[active_m_sign - 1]} राशि (चन्द्रबाट)\n"
            f"• आत्मिक/सामाजिक प्रतिष्ठा फल: {SIGN_NAMES_NE[active_s_sign - 1]} राशि (सूर्यबाट)"
        )
    }

    # 4. Overall Harmony Percentage & Conclusion
    harmony_pct = round((total_shubha_points / total_possible_points) * 100)
    harmony_pct = max(35, min(95, harmony_pct))

    l_name = SIGN_NAMES_NE[lagna_sign - 1]
    m_name = SIGN_NAMES_NE[moon_sign - 1]
    s_name = SIGN_NAMES_NE[sun_sign - 1]

    if harmony_pct >= 70:
        verdict = "उत्कृष्ट समन्वय (अत्यन्त शुभ)"
        effect = "लग्न, चन्द्र र सूर्य तीनै विन्दुहरू परस्पर अनुकूल भई जातकको जीवनमा चौतर्फी उन्नति र सन्तुलन रहनेछ।"
    elif harmony_pct >= 55:
        verdict = "मध्यम शुभ समन्वय"
        effect = "भौतिक र मानसिक पक्षमा राम्रो सन्तुलन, केही क्षेत्रहरूमा प्रयास अनुसार सफलता प्राप्त हुनेछ।"
    else:
        verdict = "मिश्रित समन्वय"
        effect = "मानसिक र भौतिक क्षेत्रमा उतारचढाव रहने हुँदा सन्तुलित निर्णय र उपाय फलदायी रहनेछ।"

    conclusion = f"सुदर्शन चक्रमा {l_name} लग्न, {m_name} चन्द्र र {s_name} सूर्य — समग्र त्रि-विन्दु समन्वयता {harmony_pct}% ({verdict})। {effect}"

    # 5. BPHS Remedies
    remedies = [
        "नित्य सूर्य नमस्कार तथा प्रातःकालमा तामाको पात्रबाट सूर्यलाई जल अर्पण गर्नु (सूर्य बलका लागि)।",
        "पूर्णिमा वा सोमबार शिवजीको जल/दूध अभिषेक तथा ॐ नमः शिवाय जप (चन्द्र/मनोबलका लागि)।",
        "लग्न बल वृद्धि गर्न आफ्नो इष्टदेव वा कुलदेवताको नित्य ध्यान तथा गायत्री मन्त्रको जप (१०८ पटक)।",
        f"चालु सुदर्शन दशा वर्ष ({current_year_age}औं वर्ष) मा {active_h_info}को शुभता बढाउन बिहीबार गुरु र गरिबलाई अन्नदान गर्नु।"
    ]

    return {
        "lagna_sign": lagna_sign,
        "lagna_sign_name": l_name,
        "moon_sign": moon_sign,
        "moon_sign_name": m_name,
        "sun_sign": sun_sign,
        "sun_sign_name": s_name,
        "harmony_percent": harmony_pct,
        "verdict": verdict,
        "conclusion": conclusion,
        "houses_analysis": houses_analysis,
        "planets_analysis": planets_analysis,
        "sudarshan_dasha": sudarshan_dasha,
        "remedies": remedies,
    }
