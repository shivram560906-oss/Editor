# -*- coding: utf-8 -*-
"""Health Narrative Engine — paragraph-based health analysis."""
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

_BODY_NE = {
    "Sun": "हृदय, आँखा, हड्डी, रक्तचाप",
    "Moon": "मन, पाचन, तरल, मानसिक स्वास्थ्य",
    "Mars": "रक्त, मांसपेशी, शल्यक्रिया, ज्वरो",
    "Mercury": "नसा तन्त्र, छाला, श्वसन, वाणी",
    "Jupiter": "कलेजो, बोसो, मधुमेह, वृद्धि",
    "Venus": "मिर्गौला, मूत्र, प्रजनन, हर्मोन",
    "Saturn": "जोर्नी, हड्डी, दाँत, दीर्घ रोग",
    "Rahu": "अज्ञात रोग, विषाक्तता, मानसिक भ्रम",
    "Ketu": "संक्रमण, घाउ, शल्यक्रिया, एलर्जी",
}
_BODY_EN = {
    "Sun": "heart, eyes, bones, blood pressure",
    "Moon": "mind, digestion, fluids, mental health",
    "Mars": "blood, muscles, surgery, fever",
    "Mercury": "nervous system, skin, respiratory, speech",
    "Jupiter": "liver, fat, diabetes, growth",
    "Venus": "kidneys, urinary, reproductive, hormones",
    "Saturn": "joints, bones, teeth, chronic disease",
    "Rahu": "unknown illness, toxicity, mental confusion",
    "Ketu": "infections, wounds, surgery, allergies",
}


def generate_health_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
    if not chart_data or not isinstance(chart_data, dict):
        return []
    is_ne = language == "ne"
    lang = "ne" if is_ne else "en"
    b = _base(chart_data)
    ls = b["lagna_sign"]
    by = b["by_name"]
    pl = b["planets"]
    vargas = b["vargas"]
    bys = b["birth_year_bs"]
    dashas = b["dashas"]

    la_lord_en, la_lord, la_h, la_sign_n, la_retro, la_comb = _house_lord_str(ls, 1, by, lang)
    six_lord_en, six_lord, six_h, six_sign_n, _, _ = _house_lord_str(ls, 6, by, lang)
    eight_lord_en, eight_lord, eight_h, eight_sign_n, _, _ = _house_lord_str(ls, 8, by, lang)

    # Moon info
    moon = by.get("Moon", {})
    moon_h = _n(moon.get("house"))
    moon_sign = _n(moon.get("sign_number"))
    moon_str = _planet("Moon", lang)

    # Planets in 6th and 8th
    six_occ = _occ(pl, 6, lang)
    eight_occ = _occ(pl, 8, lang)
    lagna_occ = _occ(pl, 1, lang)

    # D6 shashtyamsha
    d6 = vargas.get("D6") if isinstance(vargas.get("D6"), dict) else None
    d6_note = ""
    if d6:
        d6_lg = _n(d6.get("lagna", {}).get("sign_number"))
        d6_note = (f" D6 षष्टयांश लग्न <b>{_sign(d6_lg, lang)}</b> रहेकाले रोग प्रतिरोधक क्षमताको पुष्टि हुन्छ।" if is_ne else f" D6 Shashtyamsha ascendant is <b>{_sign(d6_lg, lang)}</b>, corroborating disease resistance.")

    risk_planets = []
    for p in pl:
        pname = p.get("name", "")
        if pname in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            ph = _n(p.get("house"))
            if ph in (6, 8, 12):
                risk_planets.append(pname)

    risk_str = ""
    if risk_planets:
        parts = []
        for pn in risk_planets:
            body = _BODY_NE.get(pn, "") if is_ne else _BODY_EN.get(pn, "")
            pstr = _planet(pn, lang)
            parts.append(f"<b>{pstr}</b> ({body})")
        risk_str = (f"षष्ठ/अष्टम/द्वादश भावमा {', '.join(parts)} रहेकाले यी ग्रहहरूसँग सम्बन्धित अङ्ग तथा रोगतर्फ विशेष सावधानी आवश्यक छ।" if is_ne else f"{', '.join(parts)} are in the sixth/eighth/twelfth houses — caution is needed for the related body systems.")

    ch1 = (
        f"यस कुण्डलीको लग्न <b>{_sign(ls, lang)}</b> र लग्नेश <b>{la_lord}</b> "
        f"<b>{_ord(la_h, lang)} भाव</b>मा <b>{_sign(la_sign_n, lang)}</b> राशिमा अवस्थित छ। "
        f"लग्नले शरीरको समग्र स्वास्थ्य र जीवनशक्ति दर्शाउँछ।"
        + (" लग्नेश वक्री भएकाले स्वास्थ्यमा उतारचढावको सम्भावना बढी हुन्छ।" if la_retro else "")
        + (f" लग्न भावमा: <b>{lagna_occ}</b>।" if lagna_occ != ("कोही छैन" if is_ne else "none") else "")
        + f"\n\nषष्ठ भाव (रोग तथा शत्रु) को भावेश <b>{six_lord}</b> <b>{_ord(six_h, lang)} भाव</b>मा र "
        f"अष्टम भाव (आयु तथा संकट) को भावेश <b>{eight_lord}</b> <b>{_ord(eight_h, lang)} भाव</b>मा "
        f"अवस्थित छ। षष्ठ भावमा: <b>{six_occ}</b>; अष्टम भावमा: <b>{eight_occ}</b>।\n\n"
        + (risk_str + "\n\n" if risk_str else "")
        + f"चन्द्रमा <b>{_ord(moon_h, lang)} भाव</b>मा <b>{_sign(moon_sign, lang)}</b> राशिमा "
        f"रहेकाले मानसिक स्वास्थ्य र भावनात्मक सन्तुलनमा {moon_str} को प्रत्यक्ष प्रभाव छ।{d6_note}"
        if is_ne else
        f"The ascendant is <b>{_sign(ls, lang)}</b> and the ascendant lord <b>{la_lord}</b> is in the "
        f"<b>{_ord(la_h, lang)} house</b> in <b>{_sign(la_sign_n, lang)}</b>, representing overall "
        f"health and vitality."
        + (" A retrograde ascendant lord increases health fluctuations." if la_retro else "")
        + (f" Lagna house occupants: <b>{lagna_occ}</b>." if lagna_occ != "none" else "")
        + f"\n\nSixth house lord (disease) <b>{six_lord}</b> is in the <b>{_ord(six_h, lang)} house</b>; "
        f"eighth house lord (longevity) <b>{eight_lord}</b> is in the <b>{_ord(eight_h, lang)} house</b>. "
        f"Sixth-house occupants: <b>{six_occ}</b>; Eighth-house: <b>{eight_occ}</b>.\n\n"
        + (risk_str + "\n\n" if risk_str else "")
        + f"Moon in the <b>{_ord(moon_h, lang)} house</b> in <b>{_sign(moon_sign, lang)}</b> directly "
        f"influences mental health and emotional balance.{d6_note}"
    )

    ys, ye = ((_ne(bys+10), _ne(bys+30)) if is_ne else (str(bys+10), str(bys+30)))
    ms, me = ((_ne(bys+30), _ne(bys+55)) if is_ne else (str(bys+30), str(bys+55)))

    ch2 = (
        f"<b>समय सन्दर्भ: वि.सं. {ys} – {ye}</b>\n\n"
        f"यस अवधिमा लग्न र लग्नेश <b>{la_lord}</b> को स्थितिले समग्र रोग प्रतिरोधक क्षमता "
        f"राम्रो रहने संकेत गर्दछ। सामान्यतया बाल्यकाल र किशोरावस्थामा लग्नेशको दशा र अन्तर्दशाले "
        f"शारीरिक विकास र रोग प्रतिरोधमा महत्त्वपूर्ण भूमिका खेल्दछ।\n\n"
        f"षष्ठेश <b>{six_lord}</b> को दशाकालमा सावधानी राख्नु उचित हुन्छ। "
        f"खानपान, नियमित व्यायाम र नींद व्यवस्थापनले यस उमेरको स्वास्थ्य सुनिश्चित गर्दछ।"
        if is_ne else
        f"<b>Time reference: BS {ys} – {ye}</b>\n\n"
        f"During this period, the ascendant and lord <b>{la_lord}</b> indicate generally good immunity. "
        f"Childhood and adolescence health is primarily shaped by the ascendant lord's dasha.\n\n"
        f"Caution is advised during the dasha of the sixth lord <b>{six_lord}</b>. "
        f"Balanced diet, regular exercise, and sleep hygiene ensure health during this age."
    )

    ch3 = (
        f"<b>समय सन्दर्भ: वि.सं. {ms} – {me}</b>\n\n"
        f"यस अवधिमा कार्यव्यस्तता, मानसिक तनाव र जीवनशैलीका कारण {', '.join([_planet(p, lang) for p in risk_planets[:3]]) if risk_planets else 'ग्रहीय'} "
        f"प्रभावसँग सम्बन्धित स्वास्थ्य समस्याहरूतर्फ सचेत रहनुपर्छ।\n\n"
        f"षष्ठेश <b>{six_lord}</b> र अष्टमेश <b>{eight_lord}</b> को दशा-अन्तर्दशाको समयमा "
        f"स्वास्थ्य जाँच, सावधान यातायात र मानसिक स्वास्थ्यमा विशेष ध्यान दिनु उचित हुन्छ।"
        if is_ne else
        f"<b>Time reference: BS {ms} – {me}</b>\n\n"
        f"During this phase, work pressure, stress, and lifestyle may aggravate issues related to "
        f"{'the planets ' + ', '.join([_planet(p, lang) for p in risk_planets[:3]]) if risk_planets else 'planetary'} influences.\n\n"
        f"During the dasha of sixth lord <b>{six_lord}</b> and eighth lord <b>{eight_lord}</b>, "
        f"regular health check-ups and mental wellness attention are strongly advised."
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा लग्नेश <b>{la_lord}</b> को स्थितिले "
        f"समग्रमा दीर्घायु र स्वस्थ जीवनको योग बलियो छ। "
        f"षष्ठेश <b>{six_lord}</b> र अष्टमेश <b>{eight_lord}</b> को दशामा सावधानी राख्दा "
        f"र नियमित स्वास्थ्य जाँच गर्दा दीर्घकालीन स्वास्थ्य सुनिश्चित हुनेछ।\n\n"
        f"<i>यो विश्लेषण D1 राशि कुण्डली र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"For this <b>{_sign(ls, lang)} ascendant</b>, the placement of <b>{la_lord}</b> generally "
        f"supports longevity and a healthy life. Caution during the dasha of sixth lord <b>{six_lord}</b> "
        f"and eighth lord <b>{eight_lord}</b>, combined with regular check-ups, ensures long-term health.\n\n"
        f"<i>This analysis is based on D1 Rashi chart and Vimshottari Dasha data.</i>"
    )

    ch6 = (
        f"स्वास्थ्य सुदृढ राख्न तथा रोग प्रतिरोधक क्षमता बढाउन:\n\n"
        f"<b>१. लग्नेश {la_lord} को उपासना:</b> सम्बन्धित मन्त्र र उपासनाले लग्नको बल बढाउँछ।\n"
        f"<b>२. षष्ठेश {six_lord} शान्ति:</b> षष्ठेशको दशामा दान, व्रत वा मन्त्र जपले रोगबाट रक्षा गर्दछ।\n"
        f"<b>३. चन्द्र शान्ति:</b> सोमबार उपवास, सेतो रंगको दान र चन्द्र मन्त्रले मानसिक स्वास्थ्य "
        f"सुधार्दछ।\n"
        f"<b>४. दैनिक दिनचर्या:</b> नियमित व्यायाम, ध्यान र सात्विक आहारले ग्रहीय दोषको प्रभाव "
        f"कम गर्दछ।"
        if is_ne else
        f"To strengthen health and immunity:\n\n"
        f"<b>1. Worship ascendant lord {la_lord}:</b> Related mantras and worship strengthens the lagna.\n"
        f"<b>2. Sixth lord {six_lord} pacification:</b> Charity, fasting, or mantra during sixth lord dasha "
        f"protects against disease.\n"
        f"<b>3. Moon pacification:</b> Monday fasting, white donations, and Moon mantra improve mental health.\n"
        f"<b>4. Daily routine:</b> Regular exercise, meditation, and sattvic diet reduce planetary afflictions."
    )

    return [
        {"title": "१. स्वास्थ्यको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Health", "content": ch1},
        {"title": "२. बाल्यकाल तथा युवा स्वास्थ्य" if is_ne else "2. Health in Childhood & Youth", "content": ch2},
        {"title": "३. मध्यम तथा उत्तरार्ध स्वास्थ्य" if is_ne else "3. Health in Mid & Later Life", "content": ch3},
        {"title": "४. दशाअनुसार स्वास्थ्यको समयक्रम" if is_ne else "4. Health Timeline by Dasha", "content": ch4},
        {"title": "५. समग्र स्वास्थ्य निष्कर्ष" if is_ne else "5. Overall Health Conclusion", "content": ch5},
        {"title": "६. स्वास्थ्य उपाय तथा मार्गदर्शन" if is_ne else "6. Health Remedies & Guidance", "content": ch6},
    ]
