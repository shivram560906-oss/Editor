# -*- coding: utf-8 -*-
"""Personality Narrative Engine — paragraph-based personality analysis."""
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


def generate_personality_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    # Lagna lord
    lagna_lord_en = SIGN_LORDS[ls]
    lagna_lord_str = _planet(lagna_lord_en, lang)
    lagna_lord_info = by.get(lagna_lord_en, {})
    lagna_lord_h = _n(lagna_lord_info.get("house"))
    lagna_lord_sign = _n(lagna_lord_info.get("sign_number"))
    lagna_lord_retro = bool(lagna_lord_info.get("is_retrograde"))

    # Moon (mind/emotion) and Sun (self/ego)
    moon = by.get("Moon", {})
    sun = by.get("Sun", {})
    moon_h = _n(moon.get("house"))
    moon_sign = _n(moon.get("sign_number"))
    sun_h = _n(sun.get("house"))
    sun_sign = _n(sun.get("sign_number"))
    moon_str = _planet("Moon", lang)
    sun_str = _planet("Sun", lang)

    # Lagna house occupants
    lagna_occ = _occ(pl, 1, lang)

    # D9 Navamsha (reflection of personality in life/partnership)
    d9 = vargas.get("D9") if isinstance(vargas.get("D9"), dict) else None
    d9_lg = _n(d9.get("lagna", {}).get("sign_number")) if d9 else None
    d9_pl = [p for p in (d9.get("planets") or []) if isinstance(p, dict)] if d9 else []
    d9_lagna_lord_en = SIGN_LORDS[d9_lg] if d9_lg else None
    d9_lagna_lord = _planet(d9_lagna_lord_en, lang) if d9_lagna_lord_en else "—"
    d9_lagna_lord_h = _n(next((p.get("house") for p in d9_pl if p.get("name") == d9_lagna_lord_en), None))
    d9_moon_sign = _n(next((p.get("sign_number") for p in d9_pl if p.get("name") == "Moon"), None))

    # D45 (character/ethics)
    d45 = vargas.get("D45") if isinstance(vargas.get("D45"), dict) else None
    d45_lg = _n(d45.get("lagna", {}).get("sign_number")) if d45 else None
    d45_pl = [p for p in (d45.get("planets") or []) if isinstance(p, dict)] if d45 else []
    d45_lagna_lord_en = SIGN_LORDS[d45_lg] if d45_lg else None
    d45_lagna_lord = _planet(d45_lagna_lord_en, lang) if d45_lagna_lord_en else "—"
    d45_lagna_lord_h = _n(next((p.get("house") for p in d45_pl if p.get("name") == d45_lagna_lord_en), None))

    lagna_nature_ne = {
        1: "साहसी, उत्साही र नेतृत्वकर्ता",
        2: "स्थिर, धैर्यवान् र व्यावहारिक",
        3: "बुद्धिमान्, सञ्चारप्रेमी र अनुकूलनशील",
        4: "भावनाशील, गृहप्रेमी र सुरक्षाप्रिय",
        5: "उज्ज्वल, रचनात्मक र आत्मविश्वासी",
        6: "विश्लेषणात्मक, सेवाभावी र विस्तारप्रिय",
        7: "मिलनसार, सन्तुलित र कूटनीतिज्ञ",
        8: "गहिरो, रहस्यमयी र दृढ इच्छाशक्ति",
        9: "दार्शनिक, आदर्शवादी र स्वतन्त्र",
        10: "महत्त्वाकाँक्षी, अनुशासित र जिम्मेवार",
        11: "मौलिक, समाजशील र दूरदर्शी",
        12: "कल्पनाशील, सहानुभूतिशील र आध्यात्मिक",
    }.get(ls, "गुणवान्")
    lagna_nature_en = {
        1: "courageous, enthusiastic and a natural leader",
        2: "steady, patient and practical",
        3: "intelligent, communicative and adaptable",
        4: "emotional, home-loving and security-oriented",
        5: "bright, creative and self-confident",
        6: "analytical, service-oriented and detail-loving",
        7: "sociable, balanced and diplomatic",
        8: "deep, mysterious and strong-willed",
        9: "philosophical, idealistic and independent",
        10: "ambitious, disciplined and responsible",
        11: "original, sociable and visionary",
        12: "imaginative, compassionate and spiritual",
    }.get(ls, "virtuous")

    retro_note = (
        " लग्नेश वक्री हुँदा व्यक्तित्वमा आत्म-पुनर्मूल्याङ्कन, ढिलाइ वा आन्तरिक सोचाइको गहिराइ रहन्छ।"
        if is_ne else
        " A retrograde lagna lord brings self-re-evaluation, delay or deeper introspection to the personality."
    ) if lagna_lord_retro else ""

    ch1 = (
        f"व्यक्तित्व विश्लेषणको मुख्य आधार <b>लग्न राशि</b> र <b>लग्नेश</b> हुन्। "
        f"<b>{_sign(ls, lang)} लग्न</b> राशिमा जन्मेकाले स्वभाव <b>{lagna_nature_ne}</b> हुन्छ।\n\n"
        f"लग्नेश <b>{lagna_lord_str}</b> <b>{_ord(lagna_lord_h, lang)} भाव</b>मा "
        f"<b>{_sign(lagna_lord_sign, lang)}</b> राशिमा रहेका छन्।{retro_note} "
        f"लग्न भावमा: <b>{lagna_occ}</b>।"
        if is_ne else
        f"The main basis of personality analysis is the <b>lagna (ascendant)</b> and its <b>lagna lord</b>. "
        f"A native born in <b>{_sign(ls, lang)}</b> ascendant tends to be <b>{lagna_nature_en}</b>.\n\n"
        f"The lagna lord <b>{lagna_lord_str}</b> is in the <b>{_ord(lagna_lord_h, lang)} house</b> in "
        f"<b>{_sign(lagna_lord_sign, lang)}</b>.{retro_note} "
        f"First-house occupants: <b>{lagna_occ}</b>."
    )

    ch2 = (
        f"मन र भावनाको स्वामी <b>{moon_str}</b> <b>{_ord(moon_h, lang)} भाव</b>मा "
        f"<b>{_sign(moon_sign, lang)}</b> राशिमा रहेका छन्। चन्द्रको स्थितिले मानसिक स्वभाव, "
        f"स्मरणशक्ति र भावनात्मक प्रतिक्रिया देखाउँछ।\n\n"
        f"चन्द्र बलियो भए सहज, सहानुभूतिशील र सन्तुलित स्वभाव; कमजोर भए चंचल वा भावनात्मक "
        f"उतार-चढाव बढी हुन्छ। चन्द्र जुन राशि/भावमा छ, त्यसले मनको प्रकृति थप स्पष्ट बनाउँछ।"
        if is_ne else
        f"The lord of mind and emotions, <b>{moon_str}</b>, is in the <b>{_ord(moon_h, lang)} house</b> in "
        f"<b>{_sign(moon_sign, lang)}</b>. The Moon's placement shows mental temperament, memory and emotional "
        f"responses.\n\n"
        f"A strong Moon gives an easy, empathetic and balanced nature; a weak Moon brings restlessness or "
        f"greater emotional swings. The sign/house of the Moon further clarifies the nature of the mind."
    )

    ch3 = (
        f"आत्मबल र व्यक्तित्वको केन्द्र <b>{sun_str}</b> <b>{_ord(sun_h, lang)} भाव</b>मा "
        f"<b>{_sign(sun_sign, lang)}</b> राशिमा रहेका छन्। सूर्यको स्थितिले आत्मविश्वास, "
        f"इच्छाशक्ति र अधिकार-भाव देखाउँछ।\n\n"
        f"सूर्य बलियो भए नेतृत्व, आत्मनिर्भरता र प्रतिष्ठाको भाव बलियो हुन्छ; कमजोर भए "
        f"आत्मविश्वासमा कमी वा आश्रित स्वभाव देखिन सक्छ।"
        if is_ne else
        f"The centre of self-strength and personality, <b>{sun_str}</b>, is in the <b>{_ord(sun_h, lang)} house</b> "
        f"in <b>{_sign(sun_sign, lang)}</b>. The Sun's placement shows confidence, willpower and a sense of authority.\n\n"
        f"A strong Sun brings leadership, self-reliance and prestige; a weak Sun may show low confidence or a "
        f"dependent nature."
    )

    ch4 = (
        f"<b>D9 नवांश प्रतिबिम्ब:</b>"
        + (f"\nD9 नवांशको लग्न <b>{_sign(d9_lg, lang)}</b> छ र यसको लग्नेश <b>{d9_lagna_lord}</b> "
           f"<b>{_ord(d9_lagna_lord_h, lang)} भाव</b>मा छन्। D9 मा चन्द्र <b>{_sign(d9_moon_sign, lang)}</b> "
           f"राशिमा छ — यसले जीवनसाथी र साथीसँगको व्यवहारमा देखिने स्वभावलाई प्रतिबिम्बित गर्दछ।"
           if d9 else "\nD9 नवांश तथ्याङ्क उपलब्ध छैन।")
        if is_ne else
        f"<b>D9 Navamsha reflection:</b>"
        + (f"\nThe D9 Navamsha lagna is <b>{_sign(d9_lg, lang)}</b> and its lord <b>{d9_lagna_lord}</b> is in the "
           f"<b>{_ord(d9_lagna_lord_h, lang)} house</b>. The Moon in D9 is in <b>{_sign(d9_moon_sign, lang)}</b> — "
           f"reflecting the nature shown toward partner and companions."
           if d9 else "\nD9 Navamsha data is unavailable.")
    )

    ch5 = (
        f"<b>D45 चरित्र तथा नैतिकताको गहिराइ:</b>"
        + (f"\nD45 कुण्डलीको लग्न <b>{_sign(d45_lg, lang)}</b> छ र यसको लग्नेश <b>{d45_lagna_lord}</b> "
           f"<b>{_ord(d45_lagna_lord_h, lang)} भाव</b>मा छन् — यसले गहिरो चरित्र, नैतिकता र "
           f"दीर्घकालीन स्वभावको संकेत गर्दछ।"
           if d45 else "\nD45 तथ्याङ्क उपलब्ध छैन।")
        if is_ne else
        f"<b>D45 character and ethical depth:</b>"
        + (f"\nThe D45 lagna is <b>{_sign(d45_lg, lang)}</b> and its lord <b>{d45_lagna_lord}</b> is in the "
           f"<b>{_ord(d45_lagna_lord_h, lang)} house</b> — indicating deep character, ethics and long-term nature."
           if d45 else "\nD45 data is unavailable.")
    )

    ch6 = _dasha_chapters_html(dashas, lang, is_ne)

    ch7 = (
        f"<b>{_sign(ls, lang)} लग्न</b>, लग्नेश <b>{lagna_lord_str}</b>, चन्द्र र सूर्यको स्थितिले "
        f"यस व्यक्तिको समग्र व्यक्तित्वको झलक दिन्छ। "
        + (f"D9 र D45 को तथ्यले स्वभाव र चरित्रको गहिराइ थप पुष्टि गर्दछ।" if d9 or d45 else "")
        + f"\n\nव्यक्तित्व विकासका लागि लग्नेश, चन्द्र र सूर्यको अनुकूल दशा-अन्तर्दशामा "
        f"आत्मविश्वास र उपलब्धि बढ्ने देखिन्छ।\n\n"
        + f"<i>यो विश्लेषण D1, D9, D45 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"The <b>{_sign(ls, lang)} ascendant</b>, lagna lord <b>{lagna_lord_str}</b>, Moon and Sun together give "
        f"an overview of this person's overall personality. "
        + (f"D9 and D45 data further confirm the depth of nature and character." if d9 or d45 else "")
        + f"\n\nConfidence and achievement tend to grow during favorable dasha periods of the lagna lord, Moon and Sun.\n\n"
        + f"<i>This analysis is based on D1, D9, D45 and Vimshottari Dasha data.</i>"
    )

    ch8 = (
        f"व्यक्तित्व विकासका लागि:\n\n"
        f"<b>१. लग्नेश सुदृढीकरण:</b> लग्नेशको मन्त्र जप र सम्बन्धित ग्रहको पूजा — आत्मबल वृद्धि।\n"
        f"<b>२. सूर्य नमस्कार:</b> दैनिक सूर्य नमस्कार र घिउको दीप — आत्मविश्वास र प्रतिष्ठा।\n"
        f"<b>३. चन्द्र शान्ति:</b> सोमवार शिव/चन्द्र पूजा — मानसिक स्थिरता।\n"
        f"<b>४. व्यावहारिक सुझाव:</b> नियमित ध्यान, स्वाध्याय र सकारात्मक सङ्गतले व्यक्तित्व निखारिन्छ।"
        if is_ne else
        f"For personality development:\n\n"
        f"<b>1. Strengthen the lagna lord:</b> Chant the lagna lord's mantra and worship the related planet — "
        f"increases inner strength.\n"
        f"<b>2. Surya Namaskar:</b> Daily Surya Namaskar and ghee lamp — confidence and prestige.\n"
        f"<b>3. Moon pacification:</b> Shiva/Moon worship on Monday — mental stability.\n"
        f"<b>4. Practical advice:</b> Regular meditation, self-study and positive company refine the personality."
    )

    return [
        {"title": "१. लग्न राशिको व्यक्तित्व" if is_ne else "1. Personality of the Ascendant Sign", "content": ch1},
        {"title": "२. चन्द्रको प्रभाव — मन र भावना" if is_ne else "2. Influence of the Moon — Mind & Emotion", "content": ch2},
        {"title": "३. सूर्यको प्रभाव — आत्मबल" if is_ne else "3. Influence of the Sun — Self-Strength", "content": ch3},
        {"title": "४. D9 नवांशबाट स्वभावको प्रतिबिम्ब" if is_ne else "4. D9 Navamsha Reflection of Nature", "content": ch4},
        {"title": "५. D45 बाट चरित्रको गहिराइ" if is_ne else "5. D45 Depth of Character", "content": ch5},
        {"title": "६. दशाअनुसार व्यक्तित्व समयक्रम" if is_ne else "6. Personality Timeline by Dasha", "content": ch6},
        {"title": "७. समग्र निष्कर्ष" if is_ne else "7. Overall Conclusion", "content": ch7},
        {"title": "८. व्यक्तित्व विकासका लागि सुझाव" if is_ne else "8. Suggestions for Personality Development", "content": ch8},
    ]
