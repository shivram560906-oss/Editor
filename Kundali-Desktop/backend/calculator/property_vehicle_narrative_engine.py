# -*- coding: utf-8 -*-
"""Property & Vehicle Narrative Engine — paragraph-based property and vehicle analysis."""
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


def generate_property_vehicle_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    # 4th house (home/property/comfort)
    fourth_lord_en, fourth_lord, fourth_h, fourth_sign_n, fourth_retro, _ = _house_lord_str(ls, 4, by, lang)
    fourth_sign = (ls + 2) % 12 + 1
    fourth_occ = _occ(pl, 4, lang)

    # Property/vehicle significators
    mars = by.get("Mars", {})
    venus = by.get("Venus", {})
    moon = by.get("Moon", {})
    saturn = by.get("Saturn", {})
    mars_h = _n(mars.get("house"))
    venus_h = _n(venus.get("house"))
    moon_h = _n(moon.get("house"))
    saturn_h = _n(saturn.get("house"))
    mars_str = _planet("Mars", lang)
    venus_str = _planet("Venus", lang)
    moon_str = _planet("Moon", lang)
    saturn_str = _planet("Saturn", lang)

    # D4 Chaturthamsha (immovable property/vehicles)
    d4 = vargas.get("D4") if isinstance(vargas.get("D4"), dict) else None
    d4_lg = _n(d4.get("lagna", {}).get("sign_number")) if d4 else None
    d4_pl = [p for p in (d4.get("planets") or []) if isinstance(p, dict)] if d4 else []
    d4_fourth_sign = (d4_lg + 2) % 12 + 1 if d4_lg else None
    d4_fourth_occ = _occ(d4_pl, 4, lang)
    d4_mars_h = _n(next((p.get("house") for p in d4_pl if p.get("name") == "Mars"), None))
    d4_venus_h = _n(next((p.get("house") for p in d4_pl if p.get("name") == "Venus"), None))

    # D16 Shodashamsha (vehicles/comforts)
    d16 = vargas.get("D16") if isinstance(vargas.get("D16"), dict) else None
    d16_lg = _n(d16.get("lagna", {}).get("sign_number")) if d16 else None
    d16_pl = [p for p in (d16.get("planets") or []) if isinstance(p, dict)] if d16 else []
    d16_fourth_sign = (d16_lg + 2) % 12 + 1 if d16_lg else None
    d16_fourth_occ = _occ(d16_pl, 4, lang)
    d16_fourth_lord_en = SIGN_LORDS[d16_fourth_sign] if d16_fourth_sign else None
    d16_fourth_lord = _planet(d16_fourth_lord_en, lang) if d16_fourth_lord_en else "—"
    d16_fourth_lord_h = _n(next((p.get("house") for p in d16_pl if p.get("name") == d16_fourth_lord_en), None))
    d16_venus_h = _n(next((p.get("house") for p in d16_pl if p.get("name") == "Venus"), None))

    retro_note = (
        " चतुर्थेश वक्री हुँदा सम्पत्ति प्राप्तिमा ढिलाइ, विवाद वा पुनः प्रयासको संकेत गर्दछ।"
        if is_ne else
        " Retrograde fourth lord suggests delay, dispute or re-attempts in acquiring property."
    ) if fourth_retro else ""

    property_periods = []
    for candidate in (fourth_lord_en, "Mars", "Venus", "Jupiter", "Saturn"):
        period = next((d for d in dashas if d.get("lord") == candidate), None)
        if period:
            bs = _bs_span(period.get("start", ""), period.get("end", ""))
            if bs:
                property_periods.append(f"{_planet(candidate, lang)} ({bs})")
    property_window_txt = ", ".join(property_periods) if property_periods else "—"

    ch1 = (
        f"सम्पत्ति तथा वाहन विश्लेषणमा <b>चतुर्थ भाव</b> (घर/सम्पत्ति/सुख) र चतुर्थेश मुख्य आधार हुन्। "
        f"प्रमुख कारकहरू <b>{mars_str} (भूमि/सम्पत्ति), {venus_str} (सुख/वाहन), "
        f"{moon_str} (मन/गाडी) र {saturn_str} (ढिलो तर दिगो)</b> हुन्।\n\n"
        f"चतुर्थ भाव <b>{_sign(fourth_sign, lang)}</b> राशिमा छ, चतुर्थेश <b>{fourth_lord}</b> "
        f"<b>{_ord(fourth_h, lang)} भाव</b>मा <b>{_sign(fourth_sign_n, lang)}</b> राशिमा रहेका छन्।{retro_note} "
        f"चतुर्थ भावमा: <b>{fourth_occ}</b>।\n\n"
        f"मङ्गल <b>{_ord(mars_h, lang)} भाव</b>मा, शुक्र <b>{_ord(venus_h, lang)} भाव</b>मा, "
        f"चन्द्र <b>{_ord(moon_h, lang)} भाव</b>मा र शनि <b>{_ord(saturn_h, lang)} भाव</b>मा रहेका छन्।"
        if is_ne else
        f"Property and vehicle analysis focuses on the <b>fourth house</b> (home/property/comfort) and its lord. "
        f"Key significators are <b>{mars_str} (land/property), {venus_str} (comfort/vehicle), "
        f"{moon_str} (mind/vehicle) and {saturn_str} (slow but durable)</b>.\n\n"
        f"The fourth house falls in <b>{_sign(fourth_sign, lang)}</b>; the fourth lord <b>{fourth_lord}</b> is "
        f"in the <b>{_ord(fourth_h, lang)} house</b> in <b>{_sign(fourth_sign_n, lang)}</b>.{retro_note} "
        f"Fourth-house occupants: <b>{fourth_occ}</b>.\n\n"
        f"Mars is in the <b>{_ord(mars_h, lang)} house</b>, Venus in the <b>{_ord(venus_h, lang)} house</b>, "
        f"Moon in the <b>{_ord(moon_h, lang)} house</b> and Saturn in the <b>{_ord(saturn_h, lang)} house</b>."
    )

    ch2 = (
        f"<b>सम्पत्ति प्राप्तिको प्रमुख सम्भावित अवधि:</b> {property_window_txt}\n\n"
        f"चतुर्थ भाव र चतुर्थेश बलियो भए घर, जग्गा र अचल सम्पत्ति प्राप्ति हुन्छ। "
        f"मङ्गल र शुक्रको अनुकूल स्थिति तथा चतुर्थेशको बलले जग्गा-जमिन र वाहनको योग बलियो बनाउँछ।\n\n"
        f"शनि चतुर्थ भाव वा चतुर्थेशसँग सम्बन्धित भए ढिलो तर दिगो र टिकाउ सम्पत्ति प्राप्तिको योग देखिन्छ।"
        if is_ne else
        f"<b>Primary probable property-acquisition window:</b> {property_window_txt}\n\n"
        f"A strong fourth house and fourth lord bring home, land and immovable property. "
        f"Favorable Mars and Venus placement combined with a strong fourth lord strengthen the "
        f"land-vehicle yoga.\n\n"
        f"Saturn connected to the fourth house or fourth lord indicates slow but durable and lasting property."
    )

    ch3 = (
        f"<b>घर-जग्गा तथा अचल सम्पत्ति:</b>"
        + (f"\nD4 चतुर्‌थांश कुण्डलीको लग्न <b>{_sign(d4_lg, lang)}</b> छ; यसको चतुर्थ भाव "
           f"<b>{_sign(d4_fourth_sign, lang)}</b> राशिमा पर्छ, त्यहाँ: <b>{d4_fourth_occ}</b>। "
           f"मङ्गल D4 मा <b>{_ord(d4_mars_h, lang)} भाव</b>मा र शुक्र <b>{_ord(d4_venus_h, lang)} भाव</b>मा "
           f"छन् — यसले अचल सम्पत्ति योगको D4 पुष्टि गर्दछ।"
           if d4 else "\nD4 चतुर्‌थांश तथ्याङ्क उपलब्ध छैन, अचल सम्पत्तिको विस्तृत विश्लेषण सीमित छ।")
        if is_ne else
        f"<b>Home, land and immovable property:</b>"
        + (f"\nThe D4 Chaturthamsha ascendant is <b>{_sign(d4_lg, lang)}</b>; its fourth house falls in "
           f"<b>{_sign(d4_fourth_sign, lang)}</b> with occupants: <b>{d4_fourth_occ}</b>. "
           f"Mars is in the <b>{_ord(d4_mars_h, lang)} house</b> and Venus in the <b>{_ord(d4_venus_h, lang)} house</b> "
           f"of D4 — D4 confirmation of the immovable-property yoga."
           if d4 else "\nD4 Chaturthamsha data is unavailable; detailed immovable-property analysis is limited.")
    )

    ch4 = (
        f"<b>वाहन तथा सुख-सुविधा:</b>"
        + (f"\nD16 षोडशांश कुण्डलीको लग्न <b>{_sign(d16_lg, lang)}</b> छ; यसको चतुर्थ भाव "
           f"<b>{_sign(d16_fourth_sign, lang)}</b> राशिमा पर्छ र चतुर्थेश <b>{d16_fourth_lord}</b> "
           f"<b>{_ord(d16_fourth_lord_h, lang)} भाव</b>मा छन्। त्यहाँ: <b>{d16_fourth_occ}</b>। "
           f"शुक्र D16 मा <b>{_ord(d16_venus_h, lang)} भाव</b>मा छन् — यसले वाहन तथा सुख-सुविधाको D16 पुष्टि गर्दछ।"
           if d16 else "\nD16 षोडशांश तथ्याङ्क उपलब्ध छैन, वाहन तथा सुख-सुविधाको विस्तृत विश्लेषण सीमित छ।")
        if is_ne else
        f"<b>Vehicles and comforts:</b>"
        + (f"\nThe D16 Shodashamsha ascendant is <b>{_sign(d16_lg, lang)}</b>; its fourth house falls in "
           f"<b>{_sign(d16_fourth_sign, lang)}</b> and the fourth lord <b>{d16_fourth_lord}</b> is in the "
           f"<b>{_ord(d16_fourth_lord_h, lang)} house</b>. Occupants: <b>{d16_fourth_occ}</b>. "
           f"Venus is in the <b>{_ord(d16_venus_h, lang)} house</b> of D16 — D16 confirmation of the "
           f"vehicle-comfort yoga."
           if d16 else "\nD16 Shodashamsha data is unavailable; detailed vehicle-comfort analysis is limited.")
    )

    ch5 = _dasha_chapters_html(dashas, lang, is_ne)

    ch6 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा चतुर्थ भाव, चतुर्थेश र कारक ग्रहहरूको "
        f"स्थितिले सम्पत्ति तथा वाहनको सम्भावना देखाउँछ। "
        + (f"D4/D16 को तथ्यले यसलाई थप पुष्टि गर्दछ।" if d4 or d16 else "")
        + f"\n\nसम्पत्ति र वाहन प्राप्तिको सर्वोत्तम समय चतुर्थेश, मङ्गल, शुक्र र शनिको अनुकूल "
        f"दशा-अन्तर्दशामा हुन्छ।\n\n"
        + f"<i>यो विश्लेषण D1, D4, D16 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"In this <b>{_sign(ls, lang)} ascendant</b> chart, the placement of the fourth house, its lord and "
        f"significators indicates property and vehicle potential. "
        + (f"D4/D16 data further confirms this." if d4 or d16 else "")
        + f"\n\nThe best time for property and vehicle acquisition occurs during favorable dasha periods of "
        f"the fourth lord, Mars, Venus and Saturn.\n\n"
        + f"<i>This analysis is based on D1, D4, D16 and Vimshottari Dasha data.</i>"
    )

    ch7 = (
        f"सम्पत्ति तथा वाहनको सुख बढाउन:\n\n"
        f"<b>१. मङ्गल-शुक्र शान्ति:</b> मङ्गलबार हनुमान पूजा र शुक्रबार लक्ष्मी पूजा — सम्पत्ति र "
        f"सुखको बल।\n"
        f"<b>२. चतुर्थेश पूजा:</b> चतुर्थ भावको स्वामीको मन्त्र जप र दान।\n"
        f"<b>३. गृह शान्ति:</b> घरमा नियमित गृह शान्ति तथा वास्तु सचेतना।\n"
        f"<b>४. व्यावहारिक सुझाव:</b> कागजात कानुनी रूपमा सुरक्षित राख्नु र नियमित मर्मत गर्नु।"
        if is_ne else
        f"To enhance the comfort of property and vehicles:\n\n"
        f"<b>1. Mars-Venus pacification:</b> Hanuman puja on Tuesday and Lakshmi puja on Friday — "
        f"strengthens property and comfort.\n"
        f"<b>2. Fourth-lord worship:</b> Chant the fourth lord's mantra and donate.\n"
        f"<b>3. Home peace:</b> Regular griha shanti and Vastu awareness at home.\n"
        f"<b>4. Practical advice:</b> Keep documents legally safe and maintain assets regularly."
    )

    return [
        {"title": "१. सम्पत्ति तथा वाहन योगको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Property & Vehicle Yoga", "content": ch1},
        {"title": "२. सम्पत्ति प्राप्तिको सम्भावना र समय" if is_ne else "2. Property Acquisition Potential & Timing", "content": ch2},
        {"title": "३. घर-जग्गा तथा अचल सम्पत्ति" if is_ne else "3. Land & Immovable Property", "content": ch3},
        {"title": "४. वाहन तथा सुख-सुविधा" if is_ne else "4. Vehicles & Comforts", "content": ch4},
        {"title": "५. दशाअनुसार सम्पत्ति समयक्रम" if is_ne else "5. Property Timeline by Dasha", "content": ch5},
        {"title": "६. समग्र निष्कर्ष" if is_ne else "6. Overall Conclusion", "content": ch6},
        {"title": "७. उपाय तथा मार्गदर्शन" if is_ne else "7. Remedies & Guidance", "content": ch7},
    ]
