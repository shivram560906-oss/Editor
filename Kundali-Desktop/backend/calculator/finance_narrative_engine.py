# -*- coding: utf-8 -*-
"""Finance & Wealth Narrative Engine — paragraph-based wealth analysis."""
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


def generate_finance_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    two_lord_en, two_lord, two_h, two_sign_n, _, _ = _house_lord_str(ls, 2, by, lang)
    five_lord_en, five_lord, five_h, five_sign_n, _, _ = _house_lord_str(ls, 5, by, lang)
    nine_lord_en, nine_lord, nine_h, nine_sign_n, _, _ = _house_lord_str(ls, 9, by, lang)
    eleven_lord_en, eleven_lord, eleven_h, eleven_sign_n, _, _ = _house_lord_str(ls, 11, by, lang)
    la_lord_en, la_lord, la_h, _, _, _ = _house_lord_str(ls, 1, by, lang)

    two_occ   = _occ(pl, 2, lang)
    five_occ  = _occ(pl, 5, lang)
    nine_occ  = _occ(pl, 9, lang)
    eleven_occ = _occ(pl, 11, lang)

    # D2 Hora
    d2 = vargas.get("D2") if isinstance(vargas.get("D2"), dict) else None
    d2_lg = _n(d2.get("lagna", {}).get("sign_number")) if d2 else None
    d2_pl = [p for p in (d2.get("planets") or []) if isinstance(p, dict)] if d2 else []
    d2_count = len(d2_pl)

    # Dhana yogas
    yogas = [y for y in (chart_data.get("parashara_yogas") or [])
             if isinstance(y, dict) and str(y.get("category", "")).lower() in ("dhana", "wealth")]
    yoga_names = [(y.get("nepali") if is_ne else y.get("name") or y.get("id", "")) for y in yogas]

    yoga_txt = (
        (f"\n\n<b>धन योग:</b> यस कुण्डलीमा {', '.join([str(n) for n in yoga_names if n])} सक्रिय छन्। यी योगहरूले दीर्घकालीन आर्थिक समृद्धिको संकेत गर्दछन्।"
         if is_ne else
         f"\n\n<b>Dhana Yoga:</b> Active wealth yogas in this chart: {', '.join([str(n) for n in yoga_names if n])} — indicating long-term financial prosperity.")
        if yoga_names else ""
    )
    d2_txt = (f"\n\nD2 होरा लग्न <b>{_sign(d2_lg, lang)}</b> र {d2_count} ग्रह सक्रिय — आर्थिक क्षमताको पुष्टि।" if d2 else "") if is_ne else (f"\n\nD2 Hora ascendant <b>{_sign(d2_lg, lang)}</b> with {d2_count} active planets — wealth capacity confirmed." if d2 else "")

    ms, me = ((_ne(bys+25), _ne(bys+45)) if is_ne else (str(bys+25), str(bys+45)))
    ls_s = _ne(bys+45) if is_ne else str(bys+45)

    ch1 = (
        f"आर्थिक विश्लेषणमा मुख्यतः <b>द्वितीय भाव</b> (सञ्चित धन), <b>पञ्चम भाव</b> (लगानी, भाग्य), "
        f"<b>नवम भाव</b> (भाग्य लक्ष्मी) र <b>एकादश भाव</b> (लाभ, आय) विचार गरिन्छ।\n\n"
        f"द्वितीयेश <b>{two_lord}</b> <b>{_ord(two_h, lang)} भाव</b>मा रहेका छन्, "
        f"द्वितीय भावमा: <b>{two_occ}</b>।\n"
        f"एकादशेश <b>{eleven_lord}</b> <b>{_ord(eleven_h, lang)} भाव</b>मा रहेका छन्, "
        f"एकादश भावमा: <b>{eleven_occ}</b>।\n"
        f"नवमेश <b>{nine_lord}</b> <b>{_ord(nine_h, lang)} भाव</b>मा रहेका छन्, "
        f"नवम भावमा: <b>{nine_occ}</b>।\n"
        f"पञ्चमेश <b>{five_lord}</b> <b>{_ord(five_h, lang)} भाव</b>मा, पञ्चम भावमा: <b>{five_occ}</b>।"
        + d2_txt + yoga_txt
        if is_ne else
        f"Wealth analysis focuses on: <b>second house</b> (accumulated wealth), <b>fifth house</b> (investment/fortune), "
        f"<b>ninth house</b> (Lakshmi/luck), and <b>eleventh house</b> (income/gains).\n\n"
        f"Second lord <b>{two_lord}</b> is in the <b>{_ord(two_h, lang)} house</b>; "
        f"second-house occupants: <b>{two_occ}</b>.\n"
        f"Eleventh lord <b>{eleven_lord}</b> is in the <b>{_ord(eleven_h, lang)} house</b>; "
        f"eleventh-house occupants: <b>{eleven_occ}</b>.\n"
        f"Ninth lord <b>{nine_lord}</b> is in the <b>{_ord(nine_h, lang)} house</b>; "
        f"ninth-house occupants: <b>{nine_occ}</b>.\n"
        f"Fifth lord <b>{five_lord}</b> is in the <b>{_ord(five_h, lang)} house</b>; "
        f"fifth-house occupants: <b>{five_occ}</b>."
        + d2_txt + yoga_txt
    )

    ch2 = (
        f"<b>समय सन्दर्भ: वि.सं. {ms} – {me}</b>\n\n"
        f"यस अवधिमा करियर स्थापित भएपछि एकाधिक आयस्रोत निर्माण हुने योग बलियो छ। "
        f"द्वितीयेश <b>{two_lord}</b> र एकादशेश <b>{eleven_lord}</b> को दशाकालमा "
        f"तलब, व्यापार वा लगानीबाट आम्दानी बृद्धि हुनेछ।\n\n"
        f"चतुर्थेश बलवान् भए यस अवधिमा घर, जग्गा वा वाहन प्राप्त गर्ने योग रहन्छ। "
        f"नवमेश <b>{nine_lord}</b> को दशामा भाग्यले सहयोग गर्दछ — लगानीमा राम्रो प्रतिफल आउन सक्छ।"
        if is_ne else
        f"<b>Time reference: BS {ms} – {me}</b>\n\n"
        f"After career establishment, multiple income sources develop. During the dasha of second lord "
        f"<b>{two_lord}</b> and eleventh lord <b>{eleven_lord}</b>, income from salary, business, or "
        f"investments increases.\n\n"
        f"If the fourth lord is strong, acquiring property, land, or vehicles is indicated. During the "
        f"ninth lord <b>{nine_lord}</b>'s dasha, fortune assists — investment returns are promising."
    )

    ch3 = (
        f"<b>समय सन्दर्भ: वि.सं. {ls_s} पछि</b>\n\n"
        f"जीवनको उत्तरार्धमा सञ्चित सम्पत्ति, निवृत्तिभरण वा परिवारबाट आम्दानीको स्रोत सक्रिय रहनेछ। "
        f"षष्ठेश वा व्ययेशको दशामा अनावश्यक खर्च वा ऋणको जोखिम रहनेछ — यस समयमा विशेष "
        f"आर्थिक अनुशासन आवश्यक छ।\n\n"
        f"एकादश भाव बलवान् भए जीवनभर आयस्रोत सक्रिय रहन्छ। "
        f"धन संग्रह र लगानीमा दीर्घकालीन दृष्टिकोण राख्नु सर्वाधिक लाभदायक हुनेछ।"
        if is_ne else
        f"<b>Time reference: After BS {ls_s}</b>\n\n"
        f"In later life, accumulated assets, pension, or family income remain active. During the dasha of "
        f"the sixth or twelfth lord, unnecessary expenses or debt risks arise — financial discipline is essential.\n\n"
        f"If the eleventh house is strong, income sources remain active throughout life. A long-term approach "
        f"to savings and investment yields the highest returns."
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा द्वितीयेश <b>{two_lord}</b> र "
        f"एकादशेश <b>{eleven_lord}</b> को संयुक्त बलले आर्थिक उन्नतिको बलियो आधार रहेको छ। "
        + (f"कुण्डलीमा {', '.join([str(n) for n in yoga_names if n])} जस्ता धन योगहरूले दीर्घकालीन सम्पत्ति निर्माणको संकेत गर्दछन्।" if yoga_names else "")
        + f"\n\n<i>यो विश्लेषण D1, D2 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"For this <b>{_sign(ls, lang)} ascendant</b> chart, the combined strength of the second lord <b>{two_lord}</b> "
        f"and eleventh lord <b>{eleven_lord}</b> forms a solid foundation for financial growth. "
        + (f"Wealth yogas such as {', '.join([str(n) for n in yoga_names if n])} indicate long-term wealth accumulation." if yoga_names else "")
        + f"\n\n<i>This analysis is based on D1, D2, and Vimshottari Dasha data.</i>"
    )

    ch6 = (
        f"आर्थिक समृद्धि वृद्धि तथा दोष निवारणका लागि:\n\n"
        f"<b>१. लक्ष्मी पूजा:</b> शुक्रबार लक्ष्मी पूजा र श्रीसूक्त पाठले धन वृद्धि गराउँछ।\n"
        f"<b>२. द्वितीयेश {two_lord} शान्ति:</b> संचित धनको रक्षाका लागि द्वितीयेशको मन्त्र जप।\n"
        f"<b>३. दान:</b> अन्न, वस्त्र र धनको दानले षष्ठेश र व्ययेशको अशुभ प्रभाव कम गर्दछ।\n"
        f"<b>४. आर्थिक अनुशासन:</b> बजेट, बचत र दीर्घकालीन लगानी — ग्रहीय उपायभन्दा बढी "
        f"प्रभावकारी व्यावहारिक समाधान।"
        if is_ne else
        f"To enhance wealth and neutralize financial obstacles:\n\n"
        f"<b>1. Lakshmi puja:</b> Friday Lakshmi worship and Sri Sukta recitation bring wealth growth.\n"
        f"<b>2. Second lord {two_lord} pacification:</b> Its mantra protects accumulated wealth.\n"
        f"<b>3. Charity:</b> Donating food, clothes, and money reduces sixth/twelfth lord afflictions.\n"
        f"<b>4. Financial discipline:</b> Budgeting, saving, and long-term investment are the most effective practical solutions."
    )

    return [
        {"title": "१. आर्थिक अवस्थाको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Finance", "content": ch1},
        {"title": "२. मध्यम जीवनको आर्थिक उन्नति" if is_ne else "2. Financial Growth in Mid-Life", "content": ch2},
        {"title": "३. उत्तरार्धको आर्थिक स्थिति" if is_ne else "3. Financial Situation in Later Life", "content": ch3},
        {"title": "४. दशाअनुसार आर्थिक समयक्रम" if is_ne else "4. Financial Timeline by Dasha", "content": ch4},
        {"title": "५. समग्र आर्थिक निष्कर्ष" if is_ne else "5. Overall Financial Conclusion", "content": ch5},
        {"title": "६. उपाय तथा मार्गदर्शन" if is_ne else "6. Remedies & Guidance", "content": ch6},
    ]
