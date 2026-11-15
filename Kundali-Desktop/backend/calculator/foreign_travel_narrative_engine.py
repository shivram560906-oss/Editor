# -*- coding: utf-8 -*-
"""Foreign Travel Narrative Engine — paragraph-based travel analysis."""
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


def generate_foreign_travel_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    # Houses: 3rd (short travel), 9th (long/foreign travel), 12th (foreign residence/expenses)
    travel_houses = []
    for house in (3, 9, 12):
        lord_en, lord_str, lord_house, lord_sign, lord_retro, _ = _house_lord_str(ls, house, by, lang)
        sign = (ls + house - 2) % 12 + 1
        occupants = _occ(pl, house, lang)
        travel_houses.append({
            "house": house,
            "sign": sign,
            "lord_en": lord_en,
            "lord": lord_str,
            "lord_house": lord_house,
            "lord_sign": lord_sign,
            "lord_retro": lord_retro,
            "occupants": occupants,
        })

    h3, h9, h12 = travel_houses

    # Travel significators
    rahu = by.get("Rahu", {})
    moon = by.get("Moon", {})
    saturn = by.get("Saturn", {})
    jupiter = by.get("Jupiter", {})
    rahu_h = _n(rahu.get("house"))
    moon_h = _n(moon.get("house"))
    saturn_h = _n(saturn.get("house"))
    jupiter_h = _n(jupiter.get("house"))
    rahu_str = _planet("Rahu", lang)
    moon_str = _planet("Moon", lang)
    saturn_str = _planet("Saturn", lang)
    jupiter_str = _planet("Jupiter", lang)

    # D9 Navamsha confirmation
    d9 = vargas.get("D9") if isinstance(vargas.get("D9"), dict) else None
    d9_lg = _n(d9.get("lagna", {}).get("sign_number")) if d9 else None
    d9_pl = [p for p in (d9.get("planets") or []) if isinstance(p, dict)] if d9 else []
    d9_ninth_sign = (d9_lg + 7) % 12 + 1 if d9_lg else None
    d9_ninth_lord_en = SIGN_LORDS[d9_ninth_sign] if d9_ninth_sign else None
    d9_ninth_lord = _planet(d9_ninth_lord_en, lang) if d9_ninth_lord_en else "—"
    d9_ninth_occ = _occ(d9_pl, 9, lang)
    d9_twelfth_occ = _occ(d9_pl, 12, lang)

    # Retrograde notes
    retros = []
    if h3["lord_retro"]:
        retros.append(_planet(h3["lord_en"], lang))
    if h9["lord_retro"]:
        retros.append(_planet(h9["lord_en"], lang))
    if h12["lord_retro"]:
        retros.append(_planet(h12["lord_en"], lang))
    retro_note = (
        (" वक्री " + " र ".join(retros) + " ले यात्रामा ढिलाइ, पुनः योजना वा बीचमै रोकिने संकेत गर्दछ।")
        if retros and is_ne else
        (" Retrograde " + " and ".join(retros) + " suggests delays, re-planning, or interrupted travel.")
        if retros else ""
    )

    # Build the travel windows note
    travel_periods = []
    for candidate in (h3["lord_en"], h9["lord_en"], h12["lord_en"], "Rahu", "Jupiter", "Moon"):
        period = next((d for d in dashas if d.get("lord") == candidate), None)
        if period:
            bs = _bs_span(period.get("start", ""), period.get("end", ""))
            if bs:
                travel_periods.append(f"{_planet(candidate, lang)} ({bs})")
    travel_window_txt = ", ".join(travel_periods) if travel_periods else "—"

    ch1 = (
        f"विदेश यात्रा विश्लेषणमा <b>तेस्रो भाव</b> (छोटो यात्रा), <b>नवौँ भाव</b> (लामो/विदेश यात्रा) र "
        f"<b>बाह्रौँ भाव</b> (परदेश बसोबास) मुख्य आधार हुन्। यात्राका प्रमुख कारकहरू "
        f"<b>{rahu_str}, {moon_str}, {saturn_str} र {jupiter_str}</b> हुन्।\n\n"
        f"तेस्रो भाव <b>{_sign(h3['sign'], lang)}</b> राशिमा छ, यसका स्वामी <b>{h3['lord']}</b> "
        f"<b>{_ord(h3['lord_house'], lang)} भाव</b>मा रहेका छन्। तेस्रो भावमा: <b>{h3['occupants']}</b>।\n\n"
        f"नवौँ भाव <b>{_sign(h9['sign'], lang)}</b> राशिमा छ, यसका स्वामी <b>{h9['lord']}</b> "
        f"<b>{_ord(h9['lord_house'], lang)} भाव</b>मा रहेका छन्। नवौँ भावमा: <b>{h9['occupants']}</b>।\n\n"
        f"बाह्रौँ भाव <b>{_sign(h12['sign'], lang)}</b> राशिमा छ, यसका स्वामी <b>{h12['lord']}</b> "
        f"<b>{_ord(h12['lord_house'], lang)} भाव</b>मा रहेका छन्। बाह्रौँ भावमा: <b>{h12['occupants']}</b>।{retro_note}"
        if is_ne else
        f"Foreign travel analysis focuses on the <b>third house</b> (short trips), <b>ninth house</b> "
        f"(long/foreign travel) and <b>twelfth house</b> (residence abroad). Key travel significators are "
        f"<b>{rahu_str}, {moon_str}, {saturn_str} and {jupiter_str}</b>.\n\n"
        f"The third house falls in <b>{_sign(h3['sign'], lang)}</b>; its lord <b>{h3['lord']}</b> is in the "
        f"<b>{_ord(h3['lord_house'], lang)} house</b>. Third-house occupants: <b>{h3['occupants']}</b>.\n\n"
        f"The ninth house falls in <b>{_sign(h9['sign'], lang)}</b>; its lord <b>{h9['lord']}</b> is in the "
        f"<b>{_ord(h9['lord_house'], lang)} house</b>. Ninth-house occupants: <b>{h9['occupants']}</b>.\n\n"
        f"The twelfth house falls in <b>{_sign(h12['sign'], lang)}</b>; its lord <b>{h12['lord']}</b> is in the "
        f"<b>{_ord(h12['lord_house'], lang)} house</b>. Twelfth-house occupants: <b>{h12['occupants']}</b>.{retro_note}"
    )

    ch2 = (
        f"<b>विदेश यात्राको प्रमुख सम्भावित अवधि:</b> {travel_window_txt}\n\n"
        f"राहु <b>{_ord(rahu_h, lang)} भाव</b>मा, चन्द्र <b>{_ord(moon_h, lang)} भाव</b>मा, "
        f"शनि <b>{_ord(saturn_h, lang)} भाव</b>मा र गुरु <b>{_ord(jupiter_h, lang)} भाव</b>मा रहेका छन्।\n\n"
        f"नवौँ वा बाह्रौँ भावमा बलियो स्थान/दृष्टि र नवौँ/बाह्रौँ भावका स्वामीको अनुकूल दशा-अन्तर्दशा "
        f"चल्दा विदेश यात्रा तथा बसोबासको योग पुष्टि हुन्छ।"
        if is_ne else
        f"<b>Primary probable travel window:</b> {travel_window_txt}\n\n"
        f"Rahu is in the <b>{_ord(rahu_h, lang)} house</b>, Moon in the <b>{_ord(moon_h, lang)} house</b>, "
        f"Saturn in the <b>{_ord(saturn_h, lang)} house</b> and Jupiter in the <b>{_ord(jupiter_h, lang)} house</b>.\n\n"
        f"Strong placement/aspects on the ninth or twelfth house combined with favorable dasha of their lords "
        f"confirm the foreign travel or residence yoga."
    )

    ch3 = (
        f"बाह्रौँ भावको बल र <b>{h12['lord']}</b> को स्थितिले परदेशमा बसोबास, "
        f"आय-व्यय र मानसिक स्थितिको संकेत गर्दछ।\n\n"
        f"गुरु नवौँ भावमा बलियो भए विदेशमा ज्ञान, अध्ययन वा धार्मिक/शैक्षिक कार्य सफल हुन्छ। "
        f"शनि बलियो भए लामो समयसम्मको दिगो बसोबास र श्रमसाध्य तर टिकाउ यात्रा योग देखिन्छ।\n\n"
        f"राहु बाह्रौँ वा नवौँ भावसँग सम्बन्धित भए नयाँ देश, प्रविधि वा गैर-परम्परागत क्षेत्रमा "
        f"सफलताको सम्भावना बढ्छ।"
        if is_ne else
        f"The strength of the twelfth house and placement of <b>{h12['lord']}</b> indicate residence abroad, "
        f"income-expenses and mental state.\n\n"
        f"A strong Jupiter in the ninth house makes study, learning or religious/educational work abroad successful. "
        f"A strong Saturn indicates long-term, sustainable settlement and laborious but durable travel.\n\n"
        f"Rahu connected to the twelfth or ninth house increases the chance of success in new countries, "
        f"technology or unconventional fields."
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा नवौँ/बाह्रौँ भाव र तिनका स्वामीको स्थितिले "
        f"विदेश यात्रा तथा बसोबासको सम्भावना देखाउँछ। "
        + (f"D9 नवांशको नवौँ भाव <b>{_sign(d9_ninth_sign, lang)}</b> राशिमा छ, यसका स्वामी "
           f"<b>{d9_ninth_lord}</b> छन्; नवौँ भावमा: <b>{d9_ninth_occ}</b>, बाह्रौँ भावमा: "
           f"<b>{d9_twelfth_occ}</b> — यसले यात्रा योगको D9 पुष्टि गर्दछ।" if d9 else "")
        + f"\n\nसबैभन्दा प्रबल यात्रा सम्भावना तेस्रो, नवौँ, बाह्रौँ भावका स्वामी र यात्रा कारकहरूको "
        f"अनुकूल दशा-अन्तर्दशामा हुन्छ।\n\n"
        + f"<i>यो विश्लेषण D1, D9 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"In this <b>{_sign(ls, lang)} ascendant</b> chart, the placement of the ninth/twelfth houses and their "
        f"lords indicates potential for foreign travel and settlement. "
        + (f"The D9 Navamsha ninth house is in <b>{_sign(d9_ninth_sign, lang)}</b> with lord <b>{d9_ninth_lord}</b>; "
           f"ninth-house occupants: <b>{d9_ninth_occ}</b>, twelfth-house occupants: <b>{d9_twelfth_occ}</b> "
           f"— D9 confirmation of the travel yoga." if d9 else "")
        + f"\n\nThe strongest travel potential occurs during favorable dasha periods of the third, ninth, "
        f"twelfth lords and travel significators.\n\n"
        + f"<i>This analysis is based on D1, D9 and Vimshottari Dasha data.</i>"
    )

    ch6 = (
        f"विदेश यात्रा सफल तथा सुरक्षित बनाउन:\n\n"
        f"<b>१. गुरु-राहु शान्ति:</b> यात्रा अघि बृहस्पति र राहुको पूजा तथा हनुमान चालीसा पाठ — "
        f"बाधा हटाउँछ।\n"
        f"<b>२. नवौँ भाव बल:</b> नवग्रह शान्ति वा गुरु मन्त्रको जपले यात्रा सफल बनाउँछ।\n"
        f"<b>३. शुभ दिन छान्ने:</b> महूरत अनुसार शुभ समयमा यात्रा थालनी गर्नु।\n"
        f"<b>४. व्यावहारिक सुझाव:</b> कागजात, स्वास्थ्य बीमा र आर्थिक योजना पूर्ण तयारीसाथ गर्नु।"
        if is_ne else
        f"To make foreign travel successful and safe:\n\n"
        f"<b>1. Jupiter-Rahu pacification:</b> Worship Jupiter and Rahu and recite Hanuman Chalisa before travel — "
        f"removes obstacles.\n"
        f"<b>2. Ninth-house strength:</b> Navagraha shanti or Jupiter mantra japa makes travel successful.\n"
        f"<b>3. Choose an auspicious day:</b> Start travel at a favorable muhurta.\n"
        f"<b>4. Practical advice:</b> Complete documents, health insurance and financial planning beforehand."
    )

    return [
        {"title": "१. यात्रा योगको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Travel Yoga", "content": ch1},
        {"title": "२. विदेश यात्राको सम्भावना र समय" if is_ne else "2. Foreign Travel Potential & Timing", "content": ch2},
        {"title": "३. यात्राको परिणाम र बसोबास" if is_ne else "3. Travel Outcome & Settlement", "content": ch3},
        {"title": "४. दशाअनुसार यात्रा समयक्रम" if is_ne else "4. Travel Timeline by Dasha", "content": ch4},
        {"title": "५. समग्र निष्कर्ष" if is_ne else "5. Overall Conclusion", "content": ch5},
        {"title": "६. उपाय तथा मार्गदर्शन" if is_ne else "6. Remedies & Guidance", "content": ch6},
    ]
