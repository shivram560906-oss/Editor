# -*- coding: utf-8 -*-
"""
gui/widgets/ashtakavarga_house_dialog.py

सामुदायिक अष्टकवर्ग भाव एवं बिन्दु विस्तृत प्रतिवेदन (Samudaya Ashtakavarga House & Bindu Detail Dialog)
- लग्नादि नम्बरमा क्लिक गर्दा: यो घरबाट के के हेरिन्छ र कुण्डली अनुसार कुन कुन फल पाएको छ सबै विवरण।
- समुदायिक अष्टकवर्ग नम्बरमा क्लिक गर्दा: उक्त बिन्दुले दिएको फल, लाभ कुन कुन कुरामा कति प्रतिशत पायो,
  हानि वा अशुभ के छ, शास्त्रीय फलादेश, गोचर फल र उपाय।
"""

import math
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTabWidget, QGridLayout,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette

from backend.calculator.constants import (
    SIGN_NAMES_NE, SIGN_NAMES_EN, SIGN_LORDS,
    EXALTATION_SIGNS, DEBILITATION_SIGNS, OWN_SIGNS,
    PLANET_NAMES_NE, NATURAL_BENEFICS, NATURAL_MALEFICS
)
from gui.utils.planet_analysis_engine import to_nepali_digits


# ── House Classical Names & Astrological Themes ───────────────────────────────

BHAVA_NAMES_NE = {
    1: "प्रथम भाव (तनु भाव / लग्न)",
    2: "द्वितीय भाव (धन एवं कुटुम्ब भाव)",
    3: "तृतीय भाव (सहज एवं पराक्रम भाव)",
    4: "चतुर्थ भाव (सुख एवं मातृ भाव)",
    5: "पञ्चम भाव (पुत्र, बुद्धि एवं विद्या भाव)",
    6: "षष्ठ भाव (रिपु, रोग एवं ऋण भाव)",
    7: "सप्तम भाव (जाया, कलत्र एवं साझेदारी भाव)",
    8: "अष्टम भाव (आयु, मृत्यु एवं रन्ध्र भाव)",
    9: "नवम भाव (भाग्य एवं धर्म भाव)",
    10: "दशम भाव (कर्म, राज्य एवं पद-प्रतिष्ठा भाव)",
    11: "एकादश भाव (लाभ एवं आय भाव)",
    12: "द्वादश भाव (व्यय, विदेश एवं मोक्ष भाव)",
}

BHAVA_CLASSIFICATION = {
    1: "केन्द्र एवं त्रिकोण (परम शुभ)",
    2: "पणफर एवं मारक भाव",
    3: "आपोक्लिम एवं उपचय भाव",
    4: "केन्द्र भाव (सुख स्थान)",
    5: "त्रिकोण भाव (लक्ष्मी स्थान)",
    6: "त्रिक / दुःस्थान एवं उपचय भाव",
    7: "केन्द्र एवं मारक भाव",
    8: "त्रिक / दुःस्थान (आयु स्थान)",
    9: "त्रिकोण भाव (परम भाग्य स्थान)",
    10: "केन्द्र एवं परम उपचय भाव",
    11: "आपोक्लिम एवं श्रेष्ठ उपचय भाव",
    12: "त्रिक / दुःस्थान (मोक्ष स्थान)",
}

BHAVA_KARAKAS = {
    1: ["सूर्य"],
    2: ["बृहस्पति", "बुध"],
    3: ["मङ्गल"],
    4: ["चन्द्र", "बुध"],
    5: ["बृहस्पति"],
    6: ["मङ्गल", "शनि"],
    7: ["शुक्र"],
    8: ["शनि"],
    9: ["बृहस्पति", "सूर्य"],
    10: ["सूर्य", "बुध", "बृहस्पति", "शनि"],
    11: ["बृहस्पति"],
    12: ["शनि"],
}

BHAVA_BODY_PARTS = {
    1: "शिर, मस्तिष्क, अनुहार, कपाल, समग्र शारीरिक बनोट",
    2: "दाहिने आँखा, मुख, दाँत, जिब्रो, घाँटीको माथिल्लो भाग, स्वर",
    3: "घाँटी, काँध, पाखुरा, हात, श्वासनली, कान (दाहिने)",
    4: "छाती, मुटु (हृदय), फोक्सो, स्तन, करङ",
    5: "पेट, कलेजो, पित्ताशय, गर्भाशय, स्मरण केन्द्र",
    6: "तल्लो पेट, आन्द्रा, मिर्गौला, पाचन प्रणाली",
    7: "तल्लो कम्मर, मूत्राशय, प्रजनन अङ्ग, पाठेघर",
    8: "गुदा, गुप्त अङ्ग, दीर्घकालीन व्याधि केन्द्र",
    9: "तिघ्रा, हिप्स, धमनी, कलेजोको तल्लो भाग",
    10: "घुँडा, जोर्नी, हड्डी, ढाडको तल्लो भाग",
    11: "पिँडुला, खुट्टाको नली, देब्रे कान",
    12: "खुट्टाका पैताला, देब्रे आँखा, निद्रा केन्द्र",
}

BHAVA_SIGNIFICATIONS_NE = {
    1: [
        "शारीरिक स्वास्थ्य, कद-काठी, रूप-रंग र आकर्षण",
        "आत्मबल, आत्मविश्वास, स्वभाव र चारित्रिक गुण",
        "जीवनशक्ति (Vitality), दीर्घायु र रोग-प्रतिरोधी क्षमता",
        "समाजमा मान-सम्मान, प्रतिष्ठा, प्रसिद्धि र प्रारम्भिक जीवन",
        "सोच्ने शैली, निर्णय क्षमता र नयाँ काम सुरु गर्ने ऊर्जा",
    ],
    2: [
        "सञ्चित धन, बैङ्क ब्यालेन्स, सुन-चाँदी र नगद सम्पत्ति",
        "पारिवारिक सुख, कुटुम्बसँगको सम्बन्ध र कुल परम्परा",
        "वाणी, बोलीको प्रभाव, गायन, मिठास र सत्यवादिता",
        "खानपानको बानी, भोजनको गुणस्तर र दाहिने आँखाको ज्योति",
        "प्रारम्भिक शिक्षा र पैतृक सम्पत्तिबाट प्राप्त लाभ",
    ],
    3: [
        "पराक्रम, साहस, पुरुषार्थ, धैर्य र मानसिक दृढता",
        "साना दाजुभाइ तथा दिदीबहिनीसँगको सम्बन्ध र सहयोग",
        "छोटो दुरीको यात्रा, सञ्चार, लेखन, सम्पादन र पत्रकारिता",
        "हातको सीप, कला, अभिनय, खेलकुद र प्राविधिक दक्षता",
        "छिमेकी र सहकर्मीसँगको सम्बन्ध तथा सामाजिक पहुँच",
    ],
    4: [
        "माताको सुख, स्वास्थ्य, सम्बन्ध र मातृवात्सल्य",
        "अचल सम्पत्ति, घर-जग्गा, घडेरी, भवन र निर्माण कार्य",
        "सवारी साधन (गाडी, मोटरसाइकल आदि) को सुख-सुविधा",
        "मानसिक शान्ति, सन्तोष, पारिवारिक सौहार्द र गृह सुख",
        "उच्च प्राथमिक शिक्षा, औपचारिक डिग्री र जनसमर्थन",
    ],
    5: [
        "तीव्र बौद्धिक क्षमता, विवेक, स्मरणशक्ति र रचनात्मकता",
        "सन्तान सुख, सन्तानको प्रगति, संस्कार र सन्तानबाट सन्तुष्टि",
        "उच्च विद्या, ज्ञान, मन्त्र दीक्षा, अनुसन्धान र प्रतिभा",
        "प्रेम सम्बन्ध, भावनात्मक लगाव, मनोरञ्जन र रोमान्स",
        "पूर्वजन्मको पुण्य फल (पूर्वपुण्य), आकस्मिक लाभ र शेयर बजार",
    ],
    6: [
        "शत्रुमाथि विजय, प्रतिस्पर्धा, परीक्षा र प्रतिस्पर्धी क्षमता",
        "रोग, बिरामी, स्वास्थ्य सङ्कट र रोग निवारण सामर्थ्य",
        "ऋण (कर्जा), ऋण तिर्ने क्षमता वा ऋणबाट मुक्ति",
        "मावली पक्ष (मामा-माइजू) सँगको सम्बन्ध र सहयोग",
        "दैनिक जागिर, श्रम, सेवाभाव, कानुनी विवाद र मुद्दा-मामिला",
    ],
    7: [
        "जीवनसाथी (पति/पत्नी), वैवाहिक सुख र दाम्पत्य सम्बन्ध",
        "व्यापारिक साझेदारी (Partnership) र व्यापारिक समझदारी",
        "दैनिक जनसम्पर्क, ग्राहक व्यवहार, समाजमा सार्वजनिक छवि",
        "काम-वासना, आकर्षण र विपरित लिङ्गीसँगको सम्बन्ध",
        "विदेश गमन, व्यापारिक सम्झौता र दैनिक आयआर्जन",
    ],
    8: [
        "आयु (Longevity), जीवनको लम्बाई र प्राकृतिक जीवनरेखा",
        "गूढ विद्या (ज्योतिष, तन्त्र, आध्यात्मिक साधना र अनुसन्धान)",
        "आकस्मिक धनलाभ, बीमा, चिट्ठा, पैतृक अंश र वसीयत",
        "दुर्घटना, संकट, अचानक आउने अवरोध र मानसिक तनाव",
        "गोप्य कुरा, रहस्यमय घटना र जीवनको अप्रत्याशित मोड",
    ],
    9: [
        "भाग्य (Fortune/Luck), ईश्वर कृपा र सौभाग्यको साथ",
        "धर्म-कर्म, नैतिकता, धार्मिक अनुष्ठान, दान र परोपकार",
        "पिताको सुख, पिताको स्वास्थ्य र पिताबाट प्राप्त मार्गदर्शन",
        "गुरु, आध्यात्मिक मार्गदर्शक र विद्वानहरूसँगको सम्पर्क",
        "तीर्थयात्रा, लामो विदेश यात्रा र उच्च दार्शनिक ज्ञान",
    ],
    10: [
        "कर्म, पेशा, व्यवसाय, नोकरी वा करियरको दिशा र सफलता",
        "सामाजिक मान-प्रतिष्ठा, ख्याति, पुरस्कार र यश",
        "सरकारी क्षेत्र, प्रशासन, राजनीति र नेतृत्व गर्ने अवसर",
        "पिताको सामाजिक स्थिति र पितासँगको कार्यगत सम्बन्ध",
        "अधिकार, शक्ति, पदोन्नति र सार्वजनिक दायित्व",
    ],
    11: [
        "समग्र आर्थिक लाभ (Gains), आम्दानीका बहुआयामिक स्रोत",
        "मनोकामना तथा अभिलाषा पूर्ति, जीवनका लक्ष्यहरूको प्राप्ति",
        "ठूला दाजुभाइ, दिदीहरू र प्रभावशाली मित्रहरूको सहयोग",
        "सामाजिक सञ्जाल, संस्थागत सम्बन्ध र समाजमा पहुँच",
        "लगानीबाट हुने उच्च प्रतिफल र व्यापारिक मुनाफा",
    ],
    12: [
        "खर्च (Expenditure), धनको लगानी र आर्थिक व्यय",
        "विदेश यात्रा, विदेश बसाइ (PR), आयात-निर्यात र विदेशी सम्पर्क",
        "मोक्ष, अध्यात्म, एकान्तवास, ध्यान र समाधि",
        "शयन सुख, निद्रा, शय्या सुख र विलासिता",
        "अस्पताल, कारागार वा अनावश्यक विवादबाट जोगिने क्षमता",
    ],
}

RASHI_LORDS_NE = {
    1: ("मङ्गल", "अग्नि", "चर"),
    2: ("शुक्र", "पृथ्वी", "स्थिर"),
    3: ("बुध", "वायु", "द्विस्वभाव"),
    4: ("चन्द्र", "जल", "चर"),
    5: ("सूर्य", "अग्नि", "स्थिर"),
    6: ("बुध", "पृथ्वी", "द्विस्वभाव"),
    7: ("शुक्र", "वायु", "चर"),
    8: ("मङ्गल", "जल", "स्थिर"),
    9: ("बृहस्पति", "अग्नि", "द्विस्वभाव"),
    10: ("शनि", "पृथ्वी", "चर"),
    11: ("शनि", "वायु", "स्थिर"),
    12: ("बृहस्पति", "जल", "द्विस्वभाव"),
}


def _calc_house_sign(lagna_sign: int, house: int) -> int:
    return ((lagna_sign - 1 + house - 1) % 12) + 1


def _calc_sign_house(lagna_sign: int, sign: int) -> int:
    return ((sign - lagna_sign) % 12) + 1


# ── Chart Analysis Engine for a House ────────────────────────────────────────

def analyze_house_in_chart(house_num: int, lagna_sign: int, chart_data: dict) -> dict:
    """
    Extracts deep house analysis based on native's chart:
    - Sign in this house, Element, Quality, Lord
    - Where the house lord is situated, dignity (exalted/debilitated/own/friendly)
    - Planets placed in this house
    - Planets casting aspect on this house
    - Comprehensive synthesis of fruits received
    """
    sign_num = _calc_house_sign(lagna_sign, house_num)
    sign_name_ne = SIGN_NAMES_NE.get(sign_num, "मेष")
    sign_name_en = SIGN_NAMES_EN.get(sign_num, "Aries")
    lord_name_ne, tatva, swabhav = RASHI_LORDS_NE.get(sign_num, ("मङ्गल", "अग्नि", "चर"))
    lord_en = SIGN_LORDS.get(sign_num, "Mars")

    planets = chart_data.get("planets", []) if isinstance(chart_data, dict) else []

    # 1. House Lord Placement
    lord_planet = next((p for p in planets if p.get("name") == lord_en), None)
    lord_placement_text = ""
    lord_house = None
    lord_sign = None
    lord_dignity = "सामान्य"

    if lord_planet:
        lord_sign = int(lord_planet.get("sign_number", 1) or 1)
        lord_house = _calc_sign_house(lagna_sign, lord_sign)
        lord_sign_name = SIGN_NAMES_NE.get(lord_sign, "")
        lord_deg = lord_planet.get("norm_degree", lord_planet.get("degree", 0.0))
        is_retro = bool(lord_planet.get("is_retrograde", lord_planet.get("retrograde", False)))

        # Dignity check
        if lord_sign == EXALTATION_SIGNS.get(lord_en):
            lord_dignity = "उच्च (Exalted) — परम शक्तिशाली"
        elif lord_sign == DEBILITATION_SIGNS.get(lord_en):
            lord_dignity = "नीच (Debilitated) — कमजोर"
        elif lord_sign in OWN_SIGNS.get(lord_en, []):
            lord_dignity = "स्वगृही (Own Sign) — सुदृढ"
        else:
            lord_dignity = "शुभ/सम राशिगत"

        retro_str = " (वक्री)" if is_retro else ""
        lord_placement_text = (
            f"यस भावका स्वामी <b>{lord_name_ne}</b> कुण्डलीको <b>{to_nepali_digits(lord_house)} औं भाव</b> "
            f"({lord_sign_name} राशि, {to_nepali_digits(f'{lord_deg:.1f}')}°){retro_str} मा बसेका छन्। "
            f"अवस्था: <b>{lord_dignity}</b>।"
        )
    else:
        lord_placement_text = f"यस भावका स्वामी <b>{lord_name_ne}</b> हुन्।"

    # 2. Planets present in this house
    placed_planets = []
    for p in planets:
        p_name = p.get("name", "")
        p_house = p.get("house")
        p_sign = p.get("sign_number")
        if p_house == house_num or p_sign == sign_num:
            ne_name = PLANET_NAMES_NE.get(p_name, p_name)
            deg = p.get("norm_degree", p.get("degree", 0.0))
            is_retro = bool(p.get("is_retrograde", p.get("retrograde", False)))
            placed_planets.append({
                "name_ne": ne_name,
                "name_en": p_name,
                "degree": deg,
                "is_retro": is_retro,
                "is_benefic": p_name in NATURAL_BENEFICS
            })

    # 3. Aspects casting on this house
    aspecting_planets = []
    for p in planets:
        p_name = p.get("name", "")
        p_sign = int(p.get("sign_number", 1) or 1)
        p_h = _calc_sign_house(lagna_sign, p_sign)
        if p_h == house_num:
            continue

        aspect_offsets = [7]  # Universal 7th aspect
        if p_name == "Mars":
            aspect_offsets = [4, 7, 8]
        elif p_name == "Jupiter":
            aspect_offsets = [5, 7, 9]
        elif p_name == "Saturn":
            aspect_offsets = [3, 7, 10]
        elif p_name in ("Rahu", "Ketu"):
            aspect_offsets = [5, 7, 9]

        for offset in aspect_offsets:
            target_h = ((p_h - 1 + offset - 1) % 12) + 1
            if target_h == house_num:
                ne_name = PLANET_NAMES_NE.get(p_name, p_name)
                aspecting_planets.append({
                    "name_ne": ne_name,
                    "offset": offset,
                    "is_benefic": p_name in NATURAL_BENEFICS
                })

    # 4. Synthesize direct fruits received
    fruits_received = []
    cautions_received = []

    # Based on Lord Placement
    if lord_house in (1, 4, 7, 10):
        fruits_received.append(f"भावेश {lord_name_ne} केन्द्र भावमा बस्नुले यो घरका फलहरू जीवनमा सहजै र दृढ रूपमा प्राप्त हुनेछन्।")
    elif lord_house in (5, 9):
        fruits_received.append(f"भावेश {lord_name_ne} त्रिकोण भावमा बस्नुले पूर्वपुण्य र भाग्यको विशेष सहयोग प्राप्त भई शुभ फल मिल्नेछ।")
    elif lord_house in (6, 8, 12):
        cautions_received.append(f"भावेश {lord_name_ne} त्रिक भाव ({to_nepali_digits(lord_house)} औं) मा बस्नुले यस भावका फल प्राप्त गर्न बढी संघर्ष र धैर्य आवश्यक छ।")

    # Based on Placed Planets
    if placed_planets:
        p_names = ", ".join(f"{p['name_ne']}{' (वक्री)' if p['is_retro'] else ''}" for p in placed_planets)
        benefics = [p for p in placed_planets if p["is_benefic"]]
        malefics = [p for p in placed_planets if not p["is_benefic"]]
        if benefics:
            b_names = ", ".join(p["name_ne"] for p in benefics)
            fruits_received.append(f"यस भावमा शुभ ग्रह <b>{b_names}</b> को उपस्थिति हुनाले यस घरका कारक विषयहरूमा सौम्यता, वृद्धि र सुखद परिणाम मिल्नेछ।")
        if malefics:
            m_names = ", ".join(p["name_ne"] for p in malefics)
            if house_num in (3, 6, 10, 11):
                fruits_received.append(f"उपचय भावमा क्रूर ग्रह <b>{m_names}</b> बस्नु शास्त्रीय रूपमा शत्रु विजय र दृढ पुरुषार्थ दिने योग मानिन्छ।")
            else:
                cautions_received.append(f"यस भावमा <b>{m_names}</b> को प्रभावले केही उतार-चढाव वा प्रारम्भिक अवरोधको सामना गर्नुपर्ने हुन सक्छ।")
    else:
        fruits_received.append("यस भावमा कुनै पनि प्रत्यक्ष पाप वा क्रूर ग्रह बसेका छैनन्, जसले भावलाई बाधा-रहित राख्न मद्दत गर्दछ।")

    # Based on Aspects
    if aspecting_planets:
        b_asp = [a["name_ne"] for a in aspecting_planets if a["is_benefic"]]
        m_asp = [a["name_ne"] for a in aspecting_planets if not a["is_benefic"]]
        if b_asp:
            fruits_received.append(f"शुभ ग्रह <b>{', '.join(b_asp)}</b> को पूर्ण दृष्टिले यस भावलाई रक्षा तथा पोषण प्रदान गरेको छ।")
        if m_asp:
            cautions_received.append(f"ग्रह <b>{', '.join(m_asp)}</b> को दृष्टि प्रभावले केही चुनौती तथा संघर्षको वातावरण बनाउन सक्छ।")

    return {
        "house_num": house_num,
        "sign_num": sign_num,
        "sign_name_ne": sign_name_ne,
        "sign_name_en": sign_name_en,
        "lord_name_ne": lord_name_ne,
        "lord_en": lord_en,
        "tatva": tatva,
        "swabhav": swabhav,
        "lord_house": lord_house,
        "lord_dignity": lord_dignity,
        "lord_placement_text": lord_placement_text,
        "placed_planets": placed_planets,
        "aspecting_planets": aspecting_planets,
        "fruits_received": fruits_received,
        "cautions_received": cautions_received,
    }


# ── Ashtakavarga Bindu & Percentage Gain Engine ───────────────────────────────

def analyze_sav_bindus_for_house(house_num: int, bindus: int, sign_name_ne: str, bav_dict: Optional[dict] = None) -> dict:
    """
    Computes exact Bindu Fruit, Percentage Gain/Loss by domains,
    vulnerabilities, classical Parashari results, remedies, and BAV distribution.
    """
    BENCHMARK = 28.0
    gain_pct = round((bindus / BENCHMARK) * 100.0, 1)
    diff_pct = round(((bindus - BENCHMARK) / BENCHMARK) * 100.0, 1)

    if bindus >= 32:
        strength_badge = "अत्यन्त बलियो (उत्कृष्ट)"
        strength_color = "#15803d"  # green
        strength_summary = "यस भावमा प्राप्त बिन्दु अत्यन्त उच्च छ। यस भावका फलहरू जीवनमा अत्यधिक अनुकूल, समृद्ध र फलदायी रहनेछन्।"
    elif bindus >= 28:
        strength_badge = "बलियो (शुभ एवं सबल)"
        strength_color = "#16a34a"  # green
        strength_summary = "यस भावमा मानक २८ वा सोभन्दा माथि बिन्दु प्राप्त भएकोले यो भाव पूर्ण रूपमा सुरक्षित र शुभ फलदायी छ।"
    elif bindus >= 25:
        strength_badge = "मध्यम (सामान्य / सम)"
        strength_color = "#d97706"  # amber
        strength_summary = "यस भावमा मध्यम बिन्दु छन्। प्रयास अनुसारको सामान्य फल मिल्नेछ, विशेष शुभ वा अशुभ दुवै मध्यम रहनेछन्।"
    else:
        strength_badge = "कमजोर (चुनौतीपूर्ण / न्यून)"
        strength_color = "#dc2626"  # red
        strength_summary = "यस भावमा बिन्दु न्यून छन्। यो भाव कमजोर मानिन्छ र सम्बन्धित विषयहरूमा सतर्कता, धैर्य र उपायको खाँचो पर्दछ।"

    factors = {
        1:  {"finance": 1.00, "career": 1.08, "health": 1.15, "relations": 1.05},
        2:  {"finance": 1.25, "career": 1.05, "health": 1.00, "relations": 1.10},
        3:  {"finance": 1.05, "career": 1.15, "health": 1.10, "relations": 1.05},
        4:  {"finance": 1.15, "career": 1.05, "health": 1.10, "relations": 1.20},
        5:  {"finance": 1.15, "career": 1.10, "health": 1.05, "relations": 1.15},
        6:  {"finance": 1.00, "career": 1.20, "health": 1.10, "relations": 0.95},
        7:  {"finance": 1.10, "career": 1.15, "health": 1.00, "relations": 1.25},
        8:  {"finance": 1.10, "career": 0.95, "health": 1.20, "relations": 0.95},
        9:  {"finance": 1.20, "career": 1.20, "health": 1.10, "relations": 1.15},
        10: {"finance": 1.15, "career": 1.30, "health": 1.05, "relations": 1.00},
        11: {"finance": 1.35, "career": 1.20, "health": 1.05, "relations": 1.15},
        12: {"finance": 0.90, "career": 1.05, "health": 1.00, "relations": 1.05},
    }
    f = factors.get(house_num, {"finance": 1.0, "career": 1.0, "health": 1.0, "relations": 1.0})

    def _calc_pct(mult):
        val = round(gain_pct * mult, 1)
        return min(160.0, max(25.0, val))

    domain_gains = {
        "finance": {
            "name": "आर्थिक लाभ एवं सम्पत्ति सामर्थ्य",
            "pct": _calc_pct(f["finance"]),
            "desc": "धन आर्जन, बचत, पैतृक लाभ र आर्थिक स्थिरतामा प्राप्त हुने सकारात्मक सामर्थ्य।"
        },
        "career": {
            "name": "करियर, प्रतिष्ठा एवं कार्यसिद्धि",
            "pct": _calc_pct(f["career"]),
            "desc": "पेशा, जागिर वा व्यवसायमा सफलता, मान-सम्मान र नेतृत्व क्षमतामा लाभ।"
        },
        "health": {
            "name": "स्वास्थ्य, आयु एवं आत्मिक स्फूर्ति",
            "pct": _calc_pct(f["health"]),
            "desc": "रोग-प्रतिरोधी क्षमता, शारीरिक ऊर्जा, दीर्घायु र मानसिक दृढता।"
        },
        "relations": {
            "name": "पारिवारिक, सामाजिक एवं सम्बन्ध सुख",
            "pct": _calc_pct(f["relations"]),
            "desc": "परिवार, बन्धुबान्धव, जीवनसाथी र साथीभाइबाट प्राप्त हुने सहयोग र प्रेम।"
        }
    }

    benefits = []
    if bindus >= 28:
        benefits.append(f"शास्त्रीय मानक २८ भन्दा बढी ({to_nepali_digits(bindus)}) बिन्दु हुनाले {to_nepali_digits(diff_pct)}% अतिरिक्त शुभ ऊर्जा प्राप्त भएको छ।")
        if house_num in (1, 5, 9):
            benefits.append("त्रिकोण/लग्न बलियो हुनाले व्यक्तित्व, भाग्य, ज्ञान र आत्मविश्वासमा निरन्तर अभिवृद्धि हुनेछ।")
        elif house_num in (2, 11):
            benefits.append("धन तथा लाभ स्थानमा उच्च बिन्दु हुनाले आर्थिक अभाव कहिल्यै हुँदैन र आम्दानीका निरन्तर नयाँ बाटाहरू खुल्नेछन्।")
        elif house_num in (4, 10):
            benefits.append("गृहसुख, वाहन लाभ र कार्यक्षेत्रमा उच्च पद-प्रतिष्ठा तथा स्थायित्व प्राप्त हुनेछ।")
        elif house_num in (3, 6):
            benefits.append("साहस, पुरुषार्थ र प्रतिस्पर्धात्मक परीक्षा वा शत्रुहरूमाथि सहज विजय प्राप्त हुनेछ।")
        elif house_num == 7:
            benefits.append("जीवनसाथीको सहयोग र व्यावसायिक साझेदारीमा दिगो लाभ मिल्नेछ।")
        elif house_num in (8, 12):
            benefits.append("दीर्घायु, संकटबाट स्वतः मुक्ति, आध्यात्मिक उन्नति वा विदेश यात्राबाट लाभ मिल्नेछ।")
        benefits.append("गोचरमा कुनै पनि ग्रह यस भावमा प्रवेश गर्दा अधिकतम शुभ फल दिन सक्षम रहनेछन्।")
    else:
        benefits.append(f"यस भावमा {to_nepali_digits(bindus)} बिन्दु भए पनि नियमित प्रयास र धैर्यले मध्यम फल प्राप्त गर्न सकिनेछ।")
        if house_num == 12:
            benefits.append("द्वादश भावमा कम बिन्दु हुनुले फजुल खर्च नियन्त्रणमा रहन सक्ने सकारात्मक पक्ष पनि रहन्छ।")
        if house_num == 6:
            benefits.append("शत्रु र रोगसँग लड्ने सतर्कता विकास हुन्छ।")

    risks = []
    if bindus < 25:
        deficit = round(abs(diff_pct), 1)
        risks.append(f"मानक २८ बिन्दुको तुलनामा {to_nepali_digits(deficit)}% सामर्थ्य कम रहेकोले यस भाव सम्बन्धी काममा ढिलाइ र चुनौती आउन सक्छ।")
        if house_num == 1:
            risks.append("शारीरिक थकान, आत्मबलमा कमी वा मौसम परिवर्तन हुँदा स्वास्थ्यमा शीघ्र असर पर्न सक्छ।")
        elif house_num == 2:
            risks.append("बचतमा अवरोध, अनपेक्षित खर्च वा कुटुम्बभित्र स-साना कुरामा मतभेद हुन सक्छ।")
        elif house_num == 3:
            risks.append("मेहनत अनुसार श्रेय कम मिल्ने वा दाजुभाइसँग वैचारिक दूरी हुन सक्छ।")
        elif house_num == 4:
            risks.append("मानसिक अशान्ति, घर-जग्गा सम्बन्धी झमेला वा आमाको स्वास्थ्यमा चिन्ता रहन सक्छ।")
        elif house_num == 5:
            risks.append("पढाइमा एकाग्रता भंग हुने वा निर्णयमा अन्योल उत्पन्न हुन सक्छ।")
        elif house_num == 6:
            risks.append("ऋणको भार बढ्न सक्ने वा पुराना रोग बल्झिन सक्ने जोखिम रहन्छ।")
        elif house_num == 7:
            risks.append("दाम्पत्य जीवनमा समझदारीको कमी वा व्यापारिक साझेदारीमा पारदर्शिता आवश्यक छ।")
        elif house_num == 8:
            risks.append("आकस्मिक चोटपटक वा स्वास्थ्यमा अचानक बाधा आउन सक्छ, सतर्क रहनुपर्छ।")
        elif house_num == 9:
            risks.append("भाग्यले ढिलो साथ दिने वा धर्म र गुरुको मार्गदर्शनमा अविश्वास उत्पन्न हुन सक्छ।")
        elif house_num == 10:
            risks.append("कार्यक्षेत्रमा उच्च अधिकारीसँग विवाद वा कामको उचित मूल्याङ्कन नहुन सक्छ।")
        elif house_num == 11:
            risks.append("आम्दानीमा अवरोध वा साथीभाइबाट धोका हुने जोखिम रहन्छ।")
        elif house_num == 12:
            risks.append("अनिद्रा, मानसिक तनाव वा अस्पताल सम्बन्धी खर्च हुन सक्छ।")
    elif bindus < 28:
        risks.append("सामर्थ्य सामान्य रहेकोले कुनै पनि ठूलो जोखिम लिनुअघि सोचविचार र योजना आवश्यक छ।")
        risks.append("अति-उत्साह वा हतारमा गरिएको निर्णयले सामान्य नोक्सानी पुर्याउन सक्छ।")
    else:
        risks.append("बिन्दु उच्च भए पनि अति-आत्मविश्वास वा घमण्डबाट बच्नुपर्छ।")
        risks.append("पाप ग्रहको गोचर चल्दा उच्च बिन्दु भए तापनि सन्तुलित व्यवहार कायम राख्नुपर्छ।")

    parashari_texts = {
        1: (
            "लग्न भावमा २८ वा सोभन्दा बढी बिन्दु हुँदा जातक सर्वगुण सम्पन्न, कान्तिवान, दीर्घायु र समाजमा आदरणीय हुन्छ। "
            "यदि बिन्दु ३० भन्दा माथि भएमा जीवनभर निरोगी र विजयी रहने पराशर वचन छ।"
        ),
        2: (
            "द्वितीय भावमा अधिक बिन्दु भएमा जातक धनधान्यले भरिपूर्ण, मीठो बोल्ने र कुटुम्बप्रिय हुन्छ। "
            "२८ भन्दा कम भएमा धन सञ्चयमा अवरोध र अनावश्यक खर्च हुने महर्षि पराशरको सिद्धान्त छ।"
        ),
        3: (
            "तृतीय भावमा अधिक बिन्दु हुनुले जातक अत्यन्त पराक्रमी, भ्रातृस्नेही र साहसिक कार्यमा दक्ष हुने जनाउँछ। "
            "कम बिन्दु भएमा साहसको कमी र भाइबहिनीसँग असमझदारी रहन सक्छ।"
        ),
        4: (
            "चतुर्थ भावमा उच्च बिन्दु हुनुले माता, गृह, भूमि, वाहन र विद्याको पूर्ण सुख दिलाउँछ। "
            "जातकको मन सधैं प्रसन्न र सन्तुष्ट रहन्छ।"
        ),
        5: (
            "पञ्चम भावमा अधिक बिन्दु भएमा जातक प्रखर बुद्धिमान, सन्तान सुखले युक्त, नीतिज्ञ र शास्त्रज्ञ हुन्छ। "
            "बिन्दु न्यून भएमा बुद्धिमा भ्रम र सन्तान सम्बन्धी चिन्ता रहन्छ।"
        ),
        6: (
            "षष्ठ भावमा अधिक बिन्दु हुनुले जातक शत्रुहन्ता, रोगमुक्त र प्रतिस्पर्धीहरूलाई परास्त गर्न सक्षम हुन्छ। "
            "तर अत्यधिक बिन्दु भएमा अनावश्यक शत्रुता र झन्झट पनि निम्तिन सक्छ।"
        ),
        7: (
            "सप्तम भावमा अधिक बिन्दु भएमा सुन्दर, गुणवती एवं सहयोगी जीवनसाथी प्राप्त हुन्छ र व्यापारमा प्रचुर लाभ हुन्छ। "
            "न्यून बिन्दु भएमा दाम्पत्यमा तालमेल मिलाउनुपर्ने हुन्छ।"
        ),
        8: (
            "अष्टम भावमा मध्यम वा न्यून बिन्दु रहनु सामान्यतया कष्ट निवारणका दृष्टिले अनुकूल मानिन्छ। "
            "तर २८ भन्दा बढी बिन्दु भएमा गूढ विद्या, अनुसन्धान र दीर्घायुको लाभ मिल्छ।"
        ),
        9: (
            "नवम भाव (भाग्य स्थान) मा अधिक बिन्दु हुनु पूर्वजन्मको महान् पुण्यको द्योतक हो। "
            "जातक भाग्यवान, धर्मनिष्ठ, तीर्थसेवी र पिताको कृपापात्र हुन्छ।"
        ),
        10: (
            "दशम भावमा अधिक बिन्दु भएमा जातक आफ्नो कर्मक्षेत्रमा उच्च पद, सरकारी सम्मान, मान-प्रतिष्ठा र स्थायित्व प्राप्त गर्दछ। "
            "कम बिन्दु हुँदा जागिरमा अस्थिरता आउन सक्छ।"
        ),
        11: (
            "एकादश भावमा सर्वथा अधिक बिन्दु हुनुपर्छ। १० औं र १२ औं भावभन्दा ११ औं भावमा बढी बिन्दु हुनु महालक्ष्मी योग समान मानिन्छ। "
            "यसले जातकलाई अपार धनलाभ र मनोकामना सिद्धि गराउँछ।"
        ),
        12: (
            "द्वादश भावमा ११ औं भन्दा कम बिन्दु हुनु शुभ मानिन्छ, जसले आम्दानीभन्दा खर्च कम रहने जनाउँछ। "
            "तर अधिक बिन्दु भएमा परोपकार, दान र विदेश यात्रामा धन खर्च हुन्छ।"
        ),
    }

    remedies = {
        1: "प्रातः सूर्यलाई तामाको लोटाबाट जल अर्पण गर्ने, गायत्री मन्त्र जप गर्ने र रातो चन्दनको टीका लगाउने।",
        2: "गायत्री मन्त्र वा महालक्ष्मी मन्त्रको नित्य जप गर्ने, वाणीमा मधुरता राख्ने र कुलदेवताको पूजा गर्ने।",
        3: "हनुमान चालिसा पाठ गर्ने, साना भाइबहिनीलाई स्नेह र सहयोग गर्ने र मङ्गलवार रातो फल दान गर्ने।",
        4: "आमाको चरण स्पर्श गरी आशीर्वाद लिने, शिवजीलाई दूध र जल चढाउने र घरको सरसफाइमा ध्यान दिने।",
        5: "सरस्वती स्तोत्र वा गणेश अथर्वशीर्ष पाठ गर्ने, बिहान विद्यार्थी वा साना बालबालिकालाई पठन सामग्री सहयोग गर्ने।",
        6: "शनिवार र मङ्गलवार हनुमान अष्टक पाठ गर्ने, गरिब वा बिरामीलाई औषधि सहयोग गर्ने र ऋण नबढाउने।",
        7: "शुक्रवार दुर्गा सप्तशती वा शुक्र मन्त्र जप गर्ने, जीवनसाथीलाई सम्मान गर्ने र सुगन्धित वस्तुको प्रयोग गर्ने।",
        8: "महामृत्युञ्जय मन्त्रको नित्य ११ पटक जप गर्ने, शनिवार कालो तिल र तेल दान गर्ने र नियमित ध्यान गर्ने।",
        9: "गुरु, पिता र वृद्धजनको आदर गर्ने, बृहस्पतिवार विष्णु सहस्रनाम पाठ गर्ने र केशरको तिलक लगाउने।",
        10: "सूर्य नमस्कार गर्ने, आफ्नो काममा निष्ठावान् रहने, दशमेश ग्रहको मन्त्र जप गर्ने र पीपलको रुखमा जल चढाउने।",
        11: "श्री सूक्त पाठ गर्ने, बिहान नियमित रूपमा इष्टदेवको आराधना गर्ने र समाज सेवामा अग्रसर रहने।",
        12: "सुत्नुअघि ध्यान गर्ने, कम्तीमा महिनामा एकपटक असहाय व्यक्तिलाई अन्न वा वस्त्र दान गर्ने र फजुल खर्चबाट जोगिने।",
    }

    return {
        "house_num": house_num,
        "bindus": bindus,
        "gain_pct": gain_pct,
        "diff_pct": diff_pct,
        "strength_badge": strength_badge,
        "strength_color": strength_color,
        "strength_summary": strength_summary,
        "domain_gains": domain_gains,
        "benefits": benefits,
        "risks": risks,
        "parashari_dictum": parashari_texts.get(house_num, "महर्षि पराशर वचन अनुसार बिन्दुको प्रभाव विशिष्ट हुन्छ।"),
        "remedies": remedies.get(house_num, "इष्टदेवको आराधना र नियमित दान-धर्म गर्नुहोस्।"),
    }


# ── The Complete Samudaya Ashtakavarga House & Bindu Detail Dialog ────────────

class SamudayaHouseDetailDialog(QDialog):
    """
    Stunning, comprehensive modal report dialog for Samudaya Ashtakavarga:
    - House Significatons & Chart Placements (लग्नादि नम्बर विवरण)
    - Bindu Score, Domain Gain %, Losses & Parashari Dictum (अष्टकवर्ग नम्बर विवरण)
    - 7 Planet BAV Matrix Contribution
    - Easy house switcher (1-12) and Prev/Next buttons
    """
    def __init__(
        self,
        house_num: int = 1,
        lagna_sign: int = 1,
        sav_scores: Optional[List[int]] = None,
        chart_data: Optional[dict] = None,
        initial_tab: str = "house",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._house_num = max(1, min(12, int(house_num)))
        self._lagna_sign = max(1, min(12, int(lagna_sign)))
        self._sav_scores = sav_scores or [28] * 12
        self._chart_data = chart_data or {}
        self._initial_tab = initial_tab

        self.setWindowTitle(f"समुदाय अष्टकवर्ग भाव प्रतिवेदन — {BHAVA_NAMES_NE.get(self._house_num, '')}")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        # Dynamic screen-aware responsive sizing & centering
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        screen_w = avail.width() if avail else 1280
        screen_h = avail.height() if avail else 720

        dlg_w = min(1020, max(680, int(screen_w * 0.88)))
        dlg_h = min(630, max(440, int(screen_h * 0.82)))
        self.resize(dlg_w, dlg_h)
        self.setMinimumSize(min(620, int(screen_w * 0.65)), min(380, int(screen_h * 0.55)))

        if avail:
            x = avail.x() + (avail.width() - dlg_w) // 2
            y = avail.y() + (avail.height() - dlg_h) // 2
            self.move(x, y)

        self._house_buttons = []
        self._build_ui()
        self._load_house(self._house_num, switch_tab=True)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(6)

        # ── Top Bar: Title & Close Button ─────────────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(8)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        dlg_title = QLabel("समुदाय अष्टकवर्ग — भाव एवं बिन्दु बृहत् विश्लेषण")
        dlg_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a;")
        dlg_subtitle = QLabel("महर्षि पराशर प्रतिपादित अष्टकवर्ग बिन्दु सामर्थ्य, भाव-कारकत्व, कुण्डलीगत स्थिति तथा लाभ/हानि प्रतिशत")
        dlg_subtitle.setStyleSheet("font-size: 11px; color: #64748b;")
        title_box.addWidget(dlg_title)
        title_box.addWidget(dlg_subtitle)
        top_bar.addLayout(title_box, 1)

        close_btn = QPushButton("✕ बन्द गर्नुहोस्")
        close_btn.setFixedHeight(30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                color: #475569;
                font-weight: 700;
                font-size: 12px;
                padding: 3px 14px;
            }
            QPushButton:hover {
                background: #f1f5f9;
                color: #0f172a;
                border-color: #94a3b8;
            }
        """)
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        root.addLayout(top_bar)

        # ── House Selector Strip (१ देखि १२ औं भाव बटनहरू) ──────────────────────
        strip_frame = QFrame()
        strip_frame.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        strip_layout = QHBoxLayout(strip_frame)
        strip_layout.setContentsMargins(6, 2, 6, 2)
        strip_layout.setSpacing(4)

        prev_btn = QPushButton("‹ अघिल्लो भाव")
        prev_btn.setFixedHeight(26)
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px;
                padding: 2px 8px; font-size: 11.5px; font-weight: 600; color: #334155;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        prev_btn.clicked.connect(self._prev_house)
        strip_layout.addWidget(prev_btn)

        self._house_buttons = []
        for h in range(1, 13):
            btn = QPushButton(f"{to_nepali_digits(h)}")
            btn.setFixedSize(34, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("house_num", h)
            btn.clicked.connect(lambda checked=False, house=h: self._load_house(house))
            self._house_buttons.append(btn)
            strip_layout.addWidget(btn)

        next_btn = QPushButton("अर्को भाव ›")
        next_btn.setFixedHeight(26)
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px;
                padding: 2px 8px; font-size: 11.5px; font-weight: 600; color: #334155;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        next_btn.clicked.connect(self._next_house)
        strip_layout.addWidget(next_btn)

        root.addWidget(strip_frame)

        # ── Quick Overview Banner ─────────────────────────────────────────────
        self._banner_frame = QFrame()
        self._banner_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f172a, stop:0.5 #1e293b, stop:1 #0f172a);
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        banner_layout = QHBoxLayout(self._banner_frame)
        banner_layout.setContentsMargins(10, 4, 10, 4)
        banner_layout.setSpacing(10)

        self._banner_title = QLabel()
        self._banner_title.setStyleSheet("font-size: 14.5px; font-weight: 800; color: #fbbf24;")
        banner_layout.addWidget(self._banner_title, 1)

        self._banner_badge_score = QLabel()
        self._banner_badge_score.setStyleSheet("""
            background: #1e3a8a; color: #93c5fd; font-size: 12px; font-weight: 700;
            padding: 3px 10px; border-radius: 5px; border: 1px solid #3b82f6;
        """)
        banner_layout.addWidget(self._banner_badge_score)

        self._banner_badge_strength = QLabel()
        self._banner_badge_strength.setStyleSheet("""
            background: #14532d; color: #86efac; font-size: 12px; font-weight: 700;
            padding: 3px 10px; border-radius: 5px; border: 1px solid #22c55e;
        """)
        banner_layout.addWidget(self._banner_badge_strength)

        self._banner_badge_gain = QLabel()
        self._banner_badge_gain.setStyleSheet("""
            background: #4c1d95; color: #c4b5fd; font-size: 12px; font-weight: 700;
            padding: 3px 10px; border-radius: 5px; border: 1px solid #8b5cf6;
        """)
        banner_layout.addWidget(self._banner_badge_gain)

        root.addWidget(self._banner_frame)

        # ── Modern Tabs ───────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background: #f1f5f9;
                color: #475569;
                font-size: 12.5px;
                font-weight: 700;
                padding: 7px 18px;
                border: 1px solid #cbd5e1;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 3px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0369a1;
                border-bottom: 2px solid #0284c7;
            }
            QTabBar::tab:hover:!selected {
                background: #e2e8f0;
                color: #0f172a;
            }
        """)

        # Tab 1: House & Significations
        self._tab_house = self._create_scrollable_container()
        self._tabs.addTab(self._tab_house["scroll"], "🏛️ १. भाव विश्लेषण (के हेरिन्छ र के फल पाएको छ)")

        # Tab 2: Ashtakavarga Bindus & Gains
        self._tab_sav = self._create_scrollable_container()
        self._tabs.addTab(self._tab_sav["scroll"], "📊 २. अष्टकवर्ग बिन्दु & लाभ/हानि प्रतिशत")

        # Tab 3: BAV 7 Planets Breakdown
        self._tab_bav = self._create_scrollable_container()
        self._tabs.addTab(self._tab_bav["scroll"], "🪐 ३. भिन्न अष्टकवर्ग (७ ग्रहको बिन्दु योगदान)")

        root.addWidget(self._tabs, 1)

    def _create_scrollable_container(self) -> dict:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background: #ffffff;
                border: none;
            }
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 14px;
                border-radius: 7px;
                margin: 2px 2px 2px 2px;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                min-height: 36px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0284c7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        body = QWidget()
        body.setStyleSheet("background: #ffffff; color: #0f172a;")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 12, 16, 18)
        layout.setSpacing(12)
        scroll.setWidget(body)

        return {"scroll": scroll, "layout": layout, "body": body}

    def _prev_house(self):
        new_h = 12 if self._house_num <= 1 else self._house_num - 1
        self._load_house(new_h)

    def _next_house(self):
        new_h = 1 if self._house_num >= 12 else self._house_num + 1
        self._load_house(new_h)

    def _load_house(self, house_num: int, switch_tab: bool = False):
        self._house_num = house_num
        self.setWindowTitle(f"समुदाय अष्टकवर्ग भाव प्रतिवेदन — {BHAVA_NAMES_NE.get(self._house_num, '')}")

        # Update button styles
        for btn in self._house_buttons:
            h = btn.property("house_num")
            if h == house_num:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #0284c7; color: #ffffff; font-weight: 800; font-size: 13px;
                        border: 1px solid #0369a1; border-radius: 6px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #ffffff; color: #334155; font-weight: 600; font-size: 12px;
                        border: 1px solid #cbd5e1; border-radius: 6px;
                    }
                    QPushButton:hover { background: #f1f5f9; color: #0284c7; }
                """)

        # Data calculations
        sign_num = _calc_house_sign(self._lagna_sign, house_num)
        bindus = (self._sav_scores[sign_num - 1]
                  if 0 <= sign_num - 1 < len(self._sav_scores) else 28)

        house_info = analyze_house_in_chart(house_num, self._lagna_sign, self._chart_data)
        sav_info = analyze_sav_bindus_for_house(house_num, bindus, house_info["sign_name_ne"])

        # Update banner
        self._banner_title.setText(
            f"{BHAVA_NAMES_NE.get(house_num, '')} — "
            f"<span style='color:#e2e8f0;'>{house_info['sign_name_ne']} ({house_info['sign_name_en']}) "
            f"| स्वामी: {house_info['lord_name_ne']}</span>"
        )
        self._banner_badge_score.setText(f"SAV बिन्दु: {to_nepali_digits(bindus)}")
        self._banner_badge_strength.setText(f"{sav_info['strength_badge']}")
        self._banner_badge_strength.setStyleSheet(f"""
            background: #14532d; color: #86efac; font-size: 13px; font-weight: 700;
            padding: 4px 12px; border-radius: 6px; border: 1px solid {sav_info['strength_color']};
        """)

        diff_str = f"+{to_nepali_digits(sav_info['diff_pct'])}%" if sav_info['diff_pct'] >= 0 else f"{to_nepali_digits(sav_info['diff_pct'])}%"
        self._banner_badge_gain.setText(f"सामर्थ्य: {to_nepali_digits(sav_info['gain_pct'])}% ({diff_str})")

        # Populate Tabs
        self._render_tab_house(house_info, sav_info)
        self._render_tab_sav(house_info, sav_info)
        self._render_tab_bav(house_info)

        if switch_tab:
            if self._initial_tab in ("score", "sav", "bindu"):
                self._tabs.setCurrentIndex(1)
            elif self._initial_tab in ("bav", "planet"):
                self._tabs.setCurrentIndex(2)
            else:
                self._tabs.setCurrentIndex(0)

    # ── TAB 1: House & Significations Rendering ───────────────────────────────

    def _render_tab_house(self, house_info: dict, sav_info: dict):
        layout = self._tab_house["layout"]
        self._clear_layout(layout)

        h = house_info["house_num"]

        # Card 1: What is seen from this house (यो घरबाट के के हेरिन्छ)
        c1 = self._create_card("📌 यो घरबाट के के हेरिन्छ? (भाव कारकतत्त्वहरू)", "#0284c7")
        c1_layout = c1.layout()

        c1_sub = QLabel("<b>शास्त्रीय वर्गीकरण:</b> " + BHAVA_CLASSIFICATION.get(h, "सामान्य"))
        c1_sub.setStyleSheet("font-size: 13px; color: #0369a1; margin-bottom: 6px;")
        c1_layout.addWidget(c1_sub)

        # Bullets of significations
        for sig in BHAVA_SIGNIFICATIONS_NE.get(h, []):
            item_lbl = QLabel(f"• &nbsp;<b>{sig}</b>")
            item_lbl.setWordWrap(True)
            item_lbl.setStyleSheet("font-size: 13px; color: #1e293b; padding: 2px 0;")
            c1_layout.addWidget(item_lbl)

        # Details Grid: Body parts, Karaka, etc.
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 8, 0, 0)

        grid.addWidget(self._create_mini_meta("शरीरका अङ्गहरू", BHAVA_BODY_PARTS.get(h, "—")), 0, 0)
        grid.addWidget(self._create_mini_meta("स्थिर कारक ग्रह", ", ".join(BHAVA_KARAKAS.get(h, ["—"]))), 0, 1)
        grid.addWidget(self._create_mini_meta("राशि एवं तत्त्व", f"{house_info['sign_name_ne']} ({house_info['tatva']} तत्त्व, {house_info['swabhav']})"), 1, 0)
        grid.addWidget(self._create_mini_meta("भाव स्वामी (भावेश)", f"{house_info['lord_name_ne']} ({house_info['lord_en']})"), 1, 1)

        c1_layout.addLayout(grid)
        layout.addWidget(c1)

        # Card 2: Current Chart State for this House (कुण्डलीगत स्थिति)
        c2 = self._create_card("🪐 तपाईंको कुण्डली अनुसार यो घरको अवस्था र फल", "#7c3aed")
        c2_layout = c2.layout()

        # Lord Placement
        lord_box = QLabel(f"👑 <b>भावेश स्थिति:</b> {house_info['lord_placement_text']}")
        lord_box.setWordWrap(True)
        lord_box.setStyleSheet("background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 6px; padding: 8px 12px; font-size: 13px; color: #4c1d95;")
        c2_layout.addWidget(lord_box)

        # Present Planets
        placed_lbl = QLabel("<b>यस भावमा उपस्थित ग्रहहरू:</b>")
        placed_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #0f172a; margin-top: 4px;")
        c2_layout.addWidget(placed_lbl)

        if house_info["placed_planets"]:
            for p in house_info["placed_planets"]:
                p_tag = "शुभ ग्रह" if p["is_benefic"] else "पाप/क्रूर ग्रह"
                p_box = QLabel(
                    f"⭐ <b>{p['name_ne']} ({p['name_en']})</b> — {to_nepali_digits(f'{p['degree']:.2f}')}° "
                    f"{' [वक्री]' if p['is_retro'] else ''} &nbsp;|&nbsp; वर्ग: {p_tag}"
                )
                p_box.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px; font-size: 13px; color: #0f172a;")
                c2_layout.addWidget(p_box)
        else:
            no_p = QLabel("यस भावमा कुनै पनि प्रत्यक्ष ग्रह बसेका छैनन् (रिक्त भाव)। यस्तो अवस्थामा भाव स्वामी र अष्टकवर्ग बिन्दुको प्रभाव मुख्य रहन्छ।")
            no_p.setStyleSheet("font-size: 12.5px; color: #64748b; font-style: italic; padding: 4px 0;")
            c2_layout.addWidget(no_p)

        # Aspecting Planets
        if house_info["aspecting_planets"]:
            asp_names = ", ".join(f"<b>{a['name_ne']}</b> ({to_nepali_digits(a['offset'])} औं दृष्टि)" for a in house_info["aspecting_planets"])
            asp_lbl = QLabel(f"👁️ <b>यस भावमा दृष्टि दिने ग्रहहरू:</b> {asp_names}")
            asp_lbl.setWordWrap(True)
            asp_lbl.setStyleSheet("background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 8px 12px; font-size: 13px; color: #166534; margin-top: 4px;")
            c2_layout.addWidget(asp_lbl)

        layout.addWidget(c2)

        # Card 3: Direct Results Received (यो घरबाट पाएका फलहरू)
        c3 = self._create_card("🎯 कुण्डली अनुसार यो घरबाट प्राप्त फल निष्कर्ष", "#059669")
        c3_layout = c3.layout()

        fruits_lbl = QLabel("<b>सबल एवं शुभ पक्षहरू:</b>")
        fruits_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #15803d;")
        c3_layout.addWidget(fruits_lbl)

        for f in house_info["fruits_received"]:
            f_box = QLabel(f"✅ &nbsp;{f}")
            f_box.setWordWrap(True)
            f_box.setStyleSheet("font-size: 13px; color: #0f172a; line-height: 1.45; padding: 2px 0;")
            c3_layout.addWidget(f_box)

        if house_info["cautions_received"]:
            caut_lbl = QLabel("<b>सावधान रहनुपर्ने पक्षहरू:</b>")
            caut_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #b91c1c; margin-top: 8px;")
            c3_layout.addWidget(caut_lbl)

            for c in house_info["cautions_received"]:
                c_box = QLabel(f"⚠️ &nbsp;{c}")
                c_box.setWordWrap(True)
                c_box.setStyleSheet("font-size: 13px; color: #7f1d1d; line-height: 1.45; padding: 2px 0;")
                c3_layout.addWidget(c_box)

        layout.addWidget(c3)
        layout.addStretch(1)

    # ── TAB 2: Ashtakavarga Bindus & Gains Rendering ──────────────────────────

    def _render_tab_sav(self, house_info: dict, sav_info: dict):
        layout = self._tab_sav["layout"]
        self._clear_layout(layout)

        # Card 1: Score & Core Strength
        c1 = self._create_card("⭐ समुदाय अष्टकवर्ग बिन्दु सामर्थ्य", sav_info["strength_color"])
        c1_layout = c1.layout()

        score_row = QHBoxLayout()
        pts_lbl = QLabel(f"<span style='font-size:32px; font-weight:900; color:{sav_info['strength_color']};'>{to_nepali_digits(sav_info['bindus'])}</span> "
                         f"<span style='font-size:16px; font-weight:700; color:#475569;'>बिन्दु (SAV Points)</span>")
        score_row.addWidget(pts_lbl)
        score_row.addStretch(1)

        badge_box = QLabel(f"स्तर: <b>{sav_info['strength_badge']}</b> &nbsp;|&nbsp; शास्त्रीय मानक: <b>२८ बिन्दु</b>")
        badge_box.setStyleSheet(f"""
            background: #ffffff; border: 1.5px solid {sav_info['strength_color']};
            border-radius: 6px; padding: 6px 14px; font-size: 13px; color: #0f172a;
        """)
        score_row.addWidget(badge_box)
        c1_layout.addLayout(score_row)

        summary_p = QLabel(sav_info["strength_summary"])
        summary_p.setWordWrap(True)
        summary_p.setStyleSheet("font-size: 13.5px; color: #334155; line-height: 1.45; margin-top: 6px;")
        c1_layout.addWidget(summary_p)

        layout.addWidget(c1)

        # Card 2: Domain Gain Percentages (लाभ कुन कुन कुरामा कति प्रतिशत पायो)
        c2 = self._create_card("📈 लाभ कुन कुन कुरामा कति प्रतिशत पायो? (Domain Gain %)", "#0284c7")
        c2_layout = c2.layout()

        c2_intro = QLabel("शास्त्रीय मानक २८ बिन्दुलाई १००% आधार मान्दा यस भावमा प्राप्त बिन्दुले विभिन्न जीवन आयाममा दिएको प्रभाव प्रतिशत:")
        c2_intro.setWordWrap(True)
        c2_intro.setStyleSheet("font-size: 13px; color: #475569; margin-bottom: 8px;")
        c2_layout.addWidget(c2_intro)

        for key, d in sav_info["domain_gains"].items():
            pct = d["pct"]
            d_box = QFrame()
            d_box.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px;")
            d_layout = QVBoxLayout(d_box)
            d_layout.setContentsMargins(4, 4, 4, 4)
            d_layout.setSpacing(4)

            header_row = QHBoxLayout()
            h_lbl = QLabel(f"<b>{d['name']}</b>")
            h_lbl.setStyleSheet("font-size: 13px; color: #0f172a;")
            header_row.addWidget(h_lbl)
            header_row.addStretch(1)

            pct_color = "#15803d" if pct >= 105 else ("#ca8a04" if pct >= 95 else "#dc2626")
            pct_lbl = QLabel(f"<span style='font-size:15px; font-weight:800; color:{pct_color};'>{to_nepali_digits(pct)}%</span>")
            header_row.addWidget(pct_lbl)
            d_layout.addLayout(header_row)

            # Progress Bar
            pbar = QProgressBar()
            pbar.setFixedHeight(10)
            pbar.setTextVisible(False)
            pbar.setRange(0, 150)
            pbar.setValue(int(min(150, pct)))
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background: #e2e8f0; border-radius: 5px;
                }}
                QProgressBar::chunk {{
                    background: {pct_color}; border-radius: 5px;
                }}
            """)
            d_layout.addWidget(pbar)

            desc_lbl = QLabel(d["desc"])
            desc_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
            d_layout.addWidget(desc_lbl)

            c2_layout.addWidget(d_box)

        layout.addWidget(c2)

        # Card 3: Benefits & Gains (विस्तृत शुभ फलहरू)
        c3 = self._create_card("✨ यस बिन्दुबाट प्राप्त हुने विशेष लाभहरू", "#16a34a")
        c3_layout = c3.layout()
        for b in sav_info["benefits"]:
            b_lbl = QLabel(f"💎 &nbsp;<b>{b}</b>")
            b_lbl.setWordWrap(True)
            b_lbl.setStyleSheet("font-size: 13px; color: #064e3b; line-height: 1.45; padding: 2px 0;")
            c3_layout.addWidget(b_lbl)
        layout.addWidget(c3)

        # Card 4: Risks & Inauspicious Indications (हानि वा अशुभ के छ)
        c4 = self._create_card("⚠️ हानि वा अशुभ के छ? (चुनौती, जोखिम र सावधानी)", "#dc2626")
        c4_layout = c4.layout()
        for r in sav_info["risks"]:
            r_lbl = QLabel(f"• &nbsp;<b>{r}</b>")
            r_lbl.setWordWrap(True)
            r_lbl.setStyleSheet("font-size: 13px; color: #7f1d1d; line-height: 1.45; padding: 2px 0;")
            c4_layout.addWidget(r_lbl)
        layout.addWidget(c4)

        # Card 5: Classical Parashari Dictum & Remedies
        c5 = self._create_card("📜 महर्षि पराशर शास्त्रीय फलादेश एवं उपाय", "#854d0e")
        c5_layout = c5.layout()

        para_lbl = QLabel(f"<b>वृहत्पाराशर होराशास्त्र वचन:</b><br>{sav_info['parashari_dictum']}")
        para_lbl.setWordWrap(True)
        para_lbl.setStyleSheet("background: #fefce8; border: 1px solid #fef08a; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #713f12; line-height: 1.45;")
        c5_layout.addWidget(para_lbl)

        rem_lbl = QLabel(f"🪔 <b>सुझाव तथा उपाय:</b><br>{sav_info['remedies']}")
        rem_lbl.setWordWrap(True)
        rem_lbl.setStyleSheet("background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #166534; line-height: 1.45; margin-top: 6px;")
        c5_layout.addWidget(rem_lbl)

        layout.addWidget(c5)
        layout.addStretch(1)

    # ── TAB 3: BAV 7 Planets Breakdown Rendering ──────────────────────────────

    def _render_tab_bav(self, house_info: dict):
        layout = self._tab_bav["layout"]
        self._clear_layout(layout)

        c = self._create_card(f"🪐 {house_info['sign_name_ne']} राशिमा ७ ग्रहहरूको भिन्न अष्टकवर्ग (BAV) बिन्दु योगदान", "#0369a1")
        c_layout = c.layout()

        intro = QLabel("कुनै पनि राशिमा समुदाय अष्टकवर्ग बिन्दु (SAV) भनेको ७ ग्रहहरू (सूर्य, चन्द्र, मङ्गल, बुध, गुरु, शुक्र, शनि) ले दिएका बिन्दुहरूको कुल जोड हो।")
        intro.setWordWrap(True)
        intro.setStyleSheet("font-size: 13px; color: #475569; margin-bottom: 8px;")
        c_layout.addWidget(intro)

        # Extract BAV scores from chart_data
        av = self._chart_data.get("ashtakavarga", {}) if isinstance(self._chart_data, dict) else {}
        bav = av.get("bhinnashtakavarga", {}) if isinstance(av, dict) else {}

        sign_idx = house_info["sign_num"] - 1

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ग्रह (Planet)", "योगदान (Bindu)", "स्थिति", "गोचर प्रभाव"])
        table.setRowCount(7)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff; alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0; border: 1px solid #cbd5e1; font-size: 12.5px;
            }
            QHeaderView::section {
                background-color: #f1f5f9; color: #0f172a; font-weight: 700;
                padding: 6px; border: 1px solid #cbd5e1;
            }
        """)

        GRAHAS = [
            ("Sun", "सूर्य", "आत्मा, पिता र स्वास्थ्य"),
            ("Moon", "चन्द्र", "मन, माता र भावना"),
            ("Mars", "मङ्गल", "साहस, पुरुषार्थ र ऊर्जा"),
            ("Mercury", "बुध", "बुद्धि, व्यापार र वाणी"),
            ("Jupiter", "बृहस्पति", "ज्ञान, सन्तान र भाग्य"),
            ("Venus", "शुक्र", "सुख, वाहन र दाम्पत्य"),
            ("Saturn", "शनि", "कर्म, आयु र धैर्य"),
        ]

        total_bav = 0
        for row, (p_en, p_ne, karakatwa) in enumerate(GRAHAS):
            scores = bav.get(p_en, [4] * 12) if isinstance(bav, dict) else [4] * 12
            pt = scores[sign_idx] if 0 <= sign_idx < len(scores) else 4
            total_bav += pt

            if pt >= 5:
                status_str = "अत्यन्त शुभ"
                status_color = "#15803d"
                transit_str = f"{p_ne} यस राशिमा गोचर गर्दा प्रचुर लाभ र सफलता मिल्नेछ।"
            elif pt == 4:
                status_str = "मध्यम / सम"
                status_color = "#ca8a04"
                transit_str = f"{p_ne} यस राशिमा गोचर गर्दा सामान्य फलदायी रहनेछ।"
            else:
                status_str = "कमजोर"
                status_color = "#dc2626"
                transit_str = f"{p_ne} यस राशिमा गोचर गर्दा सतर्क रहनुपर्छ र कार्यमा ढिलाइ हुन सक्छ।"

            item_p = QTableWidgetItem(f"{p_ne} ({p_en})")
            item_p.setFont(QFont("Noto Sans Devanagari", 11, QFont.Bold))

            item_pt = QTableWidgetItem(to_nepali_digits(pt))
            item_pt.setTextAlignment(Qt.AlignCenter)
            item_pt.setFont(QFont("Noto Sans Devanagari", 13, QFont.Bold))

            item_st = QTableWidgetItem(status_str)
            item_st.setTextAlignment(Qt.AlignCenter)
            item_st.setForeground(QColor(status_color))
            item_st.setFont(QFont("Noto Sans Devanagari", 11, QFont.Bold))

            item_tr = QTableWidgetItem(transit_str)
            item_tr.setFont(QFont("Noto Sans Devanagari", 11))

            table.setItem(row, 0, item_p)
            table.setItem(row, 1, item_pt)
            table.setItem(row, 2, item_st)
            table.setItem(row, 3, item_tr)

        table.setFixedHeight(260)
        c_layout.addWidget(table)

        summary_box = QLabel(
            f"<b>कुल जोड:</b> {to_nepali_digits(total_bav)} बिन्दु (समुदाय अष्टकवर्गसँग दुरुस्त मेल खान्छ)। "
            f"जुन ग्रहको बिन्दु ४ भन्दा बढी छ, त्यो ग्रहको गोचर यस भावमा जातकका लागि अति उत्तम सावित हुन्छ।"
        )
        summary_box.setWordWrap(True)
        summary_box.setStyleSheet("background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #0f172a; margin-top: 8px;")
        c_layout.addWidget(summary_box)

        layout.addWidget(c)
        layout.addStretch(1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _create_card(self, title: str, border_accent: str = "#0284c7") -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-left: 4px solid {border_accent};
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {border_accent}; padding-bottom: 4px;")
        layout.addWidget(t_lbl)
        return card

    def _create_mini_meta(self, label: str, value: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(2, 2, 2, 2)
        l.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
        val = QLabel(value)
        val.setStyleSheet("font-size: 12.5px; color: #0f172a; font-weight: 700;")
        val.setWordWrap(True)
        l.addWidget(lbl)
        l.addWidget(val)
        return w

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
