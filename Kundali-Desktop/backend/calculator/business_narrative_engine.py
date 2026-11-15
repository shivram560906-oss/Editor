# -*- coding: utf-8 -*-
"""Business Narrative Engine — paragraph-based business analysis."""
from __future__ import annotations

from typing import Optional

try:
    from backend.calculator.narrative_shared import (
        _n, _ne, _sign, _planet, _ord, _bs_span, _occ,
        _house_lord_str, _base, _dasha_chapters_html, SIGN_LORDS,
    )
except ImportError:
    from calculator.narrative_shared import (
        _n, _ne, _sign, _planet, _ord, _bs_span, _occ,
        _house_lord_str, _base, _dasha_chapters_html, SIGN_LORDS,
    )


def generate_business_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
    if not chart_data or not isinstance(chart_data, dict):
        return []
    is_ne = language == "ne"
    lang = "ne" if is_ne else "en"
    b = _base(chart_data)
    ls = b["lagna_sign"]
    by = b["by_name"]
    pl = b["planets"]
    vargas = b["vargas"]
    dashas = b["dashas"]

    # 7th house (partnership/trade) and 10th house (career/business)
    business_houses = []
    for house in (7, 10):
        lord_en, lord_str, lord_house, lord_sign, lord_retro, _ = _house_lord_str(ls, house, by, lang)
        sign = (ls + house - 2) % 12 + 1
        occupants = _occ(pl, house, lang)
        business_houses.append({
            "house": house,
            "sign": sign,
            "lord_en": lord_en,
            "lord": lord_str,
            "lord_house": lord_house,
            "lord_sign": lord_sign,
            "lord_retro": lord_retro,
            "occupants": occupants,
        })

    h7, h10 = business_houses

    # Business significators
    mercury = by.get("Mercury", {})
    mars = by.get("Mars", {})
    venus = by.get("Venus", {})
    saturn = by.get("Saturn", {})
    rahu = by.get("Rahu", {})
    mercury_h = _n(mercury.get("house"))
    mars_h = _n(mars.get("house"))
    venus_h = _n(venus.get("house"))
    saturn_h = _n(saturn.get("house"))
    rahu_h = _n(rahu.get("house"))
    mercury_str = _planet("Mercury", lang)
    mars_str = _planet("Mars", lang)
    venus_str = _planet("Venus", lang)
    saturn_str = _planet("Saturn", lang)
    rahu_str = _planet("Rahu", lang)

    # D10 Dashamsha confirmation
    d10 = vargas.get("D10") if isinstance(vargas.get("D10"), dict) else None
    d10_lg = _n(d10.get("lagna", {}).get("sign_number")) if d10 else None
    d10_pl = [p for p in (d10.get("planets") or []) if isinstance(p, dict)] if d10 else []
    d10_tenth_sign = (d10_lg + 8) % 12 + 1 if d10_lg else None
    d10_tenth_lord_en = SIGN_LORDS[d10_tenth_sign] if d10_tenth_sign else None
    d10_tenth_lord = _planet(d10_tenth_lord_en, lang) if d10_tenth_lord_en else "—"
    d10_tenth_occ = _occ(d10_pl, 10, lang)
    d10_seventh_occ = _occ(d10_pl, 7, lang)

    retro_note = ""
    if h10["lord_retro"]:
        retro_note = (
            f" दशमेश <b>{h10['lord']}</b> वक्री हुँदा व्यवसायमा ढिलाइ, पुनर्संरचना वा "
            f"बीचमा दिशा परिवर्तनको संकेत गर्दछ।"
            if is_ne else
            f" Retrograde tenth lord suggests delays, restructuring or mid-course change of direction in business."
        )

    business_periods = []
    for candidate in (h7["lord_en"], h10["lord_en"], "Mercury", "Venus", "Jupiter", "Saturn"):
        period = next((d for d in dashas if d.get("lord") == candidate), None)
        if period:
            bs = _bs_span(period.get("start", ""), period.get("end", ""))
            if bs:
                business_periods.append(f"{_planet(candidate, lang)} ({bs})")
    business_window_txt = ", ".join(business_periods) if business_periods else "—"

    ch1 = (
        f"व्यवसाय विश्लेषणमा <b>सप्तम भाव</b> (साझेदारी/व्यापार) र <b>दशम भाव</b> (कर्म/व्यवसाय) "
        f"मुख्य आधार हुन्। व्यवसायका प्रमुख कारकहरू <b>{mercury_str} (व्यापार), {mars_str} (उद्यम), "
        f"{venus_str} (वाणिज्य), {saturn_str} (कर्मकारक) र {rahu_str} (नयाँ प्रवृत्ति)</b> हुन्।\n\n"
        f"सप्तम भाव <b>{_sign(h7['sign'], lang)}</b> राशिमा छ, यसका स्वामी <b>{h7['lord']}</b> "
        f"<b>{_ord(h7['lord_house'], lang)} भाव</b>मा रहेका छन्। सप्तम भावमा: <b>{h7['occupants']}</b>।\n\n"
        f"दशम भाव <b>{_sign(h10['sign'], lang)}</b> राशिमा छ, यसका स्वामी <b>{h10['lord']}</b> "
        f"<b>{_ord(h10['lord_house'], lang)} भाव</b>मा रहेका छन्। दशम भावमा: <b>{h10['occupants']}</b>।{retro_note}"
        if is_ne else
        f"Business analysis focuses on the <b>seventh house</b> (partnership/trade) and <b>tenth house</b> "
        f"(career/business). Key business significators are <b>{mercury_str} (trade), {mars_str} (enterprise), "
        f"{venus_str} (commerce), {saturn_str} (karmakaraka) and {rahu_str} (new trends)</b>.\n\n"
        f"The seventh house falls in <b>{_sign(h7['sign'], lang)}</b>; its lord <b>{h7['lord']}</b> is in the "
        f"<b>{_ord(h7['lord_house'], lang)} house</b>. Seventh-house occupants: <b>{h7['occupants']}</b>.\n\n"
        f"The tenth house falls in <b>{_sign(h10['sign'], lang)}</b>; its lord <b>{h10['lord']}</b> is in the "
        f"<b>{_ord(h10['lord_house'], lang)} house</b>. Tenth-house occupants: <b>{h10['occupants']}</b>.{retro_note}"
    )

    ch2 = (
        f"<b>व्यवसाय विस्तारको प्रमुख सम्भावित अवधि:</b> {business_window_txt}\n\n"
        f"बुध <b>{_ord(mercury_h, lang)} भाव</b>मा, मङ्गल <b>{_ord(mars_h, lang)} भाव</b>मा, "
        f"शुक्र <b>{_ord(venus_h, lang)} भाव</b>मा, शनि <b>{_ord(saturn_h, lang)} भाव</b>मा र "
        f"राहु <b>{_ord(rahu_h, lang)} भाव</b>मा रहेका छन्।\n\n"
        f"सप्तमेश बलियो भए साझेदारी/व्यापार सफल हुन्छ; दशमेश र कर्मकारक शनि बलियो भए "
        f"स्वतन्त्र व्यवसाय वा उद्योगमा सफलता मिल्छ।"
        if is_ne else
        f"<b>Primary probable business expansion window:</b> {business_window_txt}\n\n"
        f"Mercury is in the <b>{_ord(mercury_h, lang)} house</b>, Mars in the <b>{_ord(mars_h, lang)} house</b>, "
        f"Venus in the <b>{_ord(venus_h, lang)} house</b>, Saturn in the <b>{_ord(saturn_h, lang)} house</b> and "
        f"Rahu in the <b>{_ord(rahu_h, lang)} house</b>.\n\n"
        f"A strong seventh lord favors partnership/trade; a strong tenth lord and karmakaraka Saturn favor "
        f"success in independent business or industry."
    )

    ch3 = (
        f"सप्तम भावको स्वामी <b>{h7['lord']}</b> र त्यहाँका ग्रहहरू (<b>{h7['occupants']}</b>) ले "
        f"व्यवसायको प्रकृति र साझेदारको स्थिति देखाउँछ।\n\n"
        f"बुध बलियो भए व्यापार, ब्रोकरेज, सञ्चार वा परामर्श क्षेत्र; मङ्गल बलियो भए उद्योग, "
        f"निर्माण वा प्राविधिक क्षेत्र; शुक्र बलियो भए वाणिज्य, कला, सौन्दर्य वा वित्तीय क्षेत्र; "
        f"राहु बलियो भए नवीन/प्रविधि आधारित व्यवसाय उपयुक्त हुन्छ।"
        if is_ne else
        f"The seventh lord <b>{h7['lord']}</b> and its occupants (<b>{h7['occupants']}</b>) indicate the "
        f"nature of the business and the partner's position.\n\n"
        f"A strong Mercury suits trade, brokerage, communication or consultancy; strong Mars suits industry, "
        f"construction or technical fields; strong Venus suits commerce, arts, aesthetics or finance; "
        f"strong Rahu suits innovative/technology-driven business."
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा सप्तम/दशम भाव र तिनका स्वामीको स्थितिले "
        f"व्यवसाय तथा साझेदारीको सम्भावना देखाउँछ। "
        + (f"D10 दशमांशको दशम भाव <b>{_sign(d10_tenth_sign, lang)}</b> राशिमा छ, यसका स्वामी "
           f"<b>{d10_tenth_lord}</b> छन्; दशम भावमा: <b>{d10_tenth_occ}</b>, सप्तम भावमा: "
           f"<b>{d10_seventh_occ}</b> — यसले व्यवसाय योगको D10 पुष्टि गर्दछ।" if d10 else "")
        + f"\n\nव्यवसायमा सफलताको सर्वोत्तम समय सप्तमेश, दशमेश र कर्मकारकको अनुकूल दशा-अन्तर्दशामा हुन्छ।\n\n"
        + f"<i>यो विश्लेषण D1, D10 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"In this <b>{_sign(ls, lang)} ascendant</b> chart, the placement of the seventh/tenth houses and their "
        f"lords indicates business and partnership potential. "
        + (f"The D10 Dashamsha tenth house is in <b>{_sign(d10_tenth_sign, lang)}</b> with lord "
           f"<b>{d10_tenth_lord}</b>; tenth-house occupants: <b>{d10_tenth_occ}</b>, seventh-house occupants: "
           f"<b>{d10_seventh_occ}</b> — D10 confirmation of the business yoga." if d10 else "")
        + f"\n\nThe best time for business success occurs during favorable dasha periods of the seventh lord, "
        f"tenth lord and karmakaraka.\n\n"
        + f"<i>This analysis is based on D1, D10 and Vimshottari Dasha data.</i>"
    )

    ch6 = (
        f"व्यवसाय सफल बनाउन:\n\n"
        f"<b>१. दशमेश शान्ति:</b> शनि वा सम्बन्धित ग्रहको मन्त्र जप र दानले कर्मबल बढाउँछ।\n"
        f"<b>२. बुध-शुक्र बल:</b> बुधबार/शुक्रबार बुध र शुक्रको पूजा — व्यापारिक वृद्धि।\n"
        f"<b>३. लक्ष्मी पूजा:</b> धन र समृद्धिका लागि शुक्र/लक्ष्मी पूजा नियमित गर्नु।\n"
        f"<b>४. व्यावहारिक सुझाव:</b> लेखाजोखा, कानुनी दर्ता र बजार अनुसन्धानमा ध्यान दिनु।"
        if is_ne else
        f"To make business successful:\n\n"
        f"<b>1. Tenth-lord pacification:</b> Chant the mantra of Saturn or the relevant planet and donate — "
        f"increases karmic strength.\n"
        f"<b>2. Mercury-Venus strength:</b> Worship Mercury and Venus on Wednesday/Friday — trade growth.\n"
        f"<b>3. Lakshmi Puja:</b> Regularly worship Venus/Lakshmi for wealth and prosperity.\n"
        f"<b>4. Practical advice:</b> Pay attention to accounts, legal registration and market research."
    )

    return [
        {"title": "१. व्यवसाय योगको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Business Yoga", "content": ch1},
        {"title": "२. व्यवसाय विस्तारको सम्भावना र समय" if is_ne else "2. Business Growth Potential & Timing", "content": ch2},
        {"title": "३. व्यवसायको प्रकृति र साझेदारी" if is_ne else "3. Nature of Business & Partnership", "content": ch3},
        {"title": "४. दशाअनुसार व्यवसाय समयक्रम" if is_ne else "4. Business Timeline by Dasha", "content": ch4},
        {"title": "५. समग्र निष्कर्ष" if is_ne else "5. Overall Conclusion", "content": ch5},
        {"title": "६. उपाय तथा मार्गदर्शन" if is_ne else "6. Remedies & Guidance", "content": ch6},
    ]
