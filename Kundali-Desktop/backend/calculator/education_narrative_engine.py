# -*- coding: utf-8 -*-
"""Education Narrative Engine — paragraph-based education analysis."""
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

_EDU_FIELD_NE = {
    1: "इञ्जिनियरिङ, प्रशासन, नेतृत्व",
    2: "वाणिज्य, अर्थशास्त्र, कला",
    3: "साहित्य, पत्रकारिता, भाषा",
    4: "कृषि विज्ञान, मनोविज्ञान, शिक्षण",
    5: "राजनीति, शिक्षा, गणित",
    6: "चिकित्सा, कानुन, जनस्वास्थ्य",
    7: "व्यापार, कूटनीति, कानुन",
    8: "अनुसन्धान, ज्योतिष, रसायन",
    9: "दर्शन, धर्मशास्त्र, विदेश भाषा",
    10: "इञ्जिनियरिङ, व्यवस्थापन, वास्तु",
    11: "प्रविधि, विज्ञान, अर्थशास्त्र",
    12: "मनोविज्ञान, अध्यात्म, विदेश अध्ययन",
}
_EDU_FIELD_EN = {
    1: "engineering, administration, leadership",
    2: "commerce, economics, arts",
    3: "literature, journalism, languages",
    4: "agricultural science, psychology, education",
    5: "politics, education, mathematics",
    6: "medicine, law, public health",
    7: "business, diplomacy, law",
    8: "research, astrology, chemistry",
    9: "philosophy, theology, foreign languages",
    10: "engineering, management, architecture",
    11: "technology, science, economics",
    12: "psychology, spirituality, foreign study",
}


def generate_education_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    four_lord_en, four_lord, four_h, four_sign_n, _, _ = _house_lord_str(ls, 4, by, lang)
    five_lord_en, five_lord, five_h, five_sign_n, _, _ = _house_lord_str(ls, 5, by, lang)
    nine_lord_en, nine_lord, nine_h, nine_sign_n, _, _ = _house_lord_str(ls, 9, by, lang)
    five_sign = (ls + 3) % 12 + 1

    merc = by.get("Mercury", {})
    merc_h = _n(merc.get("house"))
    merc_sign = _n(merc.get("sign_number"))
    merc_retro = bool(merc.get("is_retrograde"))
    merc_comb = bool(merc.get("is_combust"))
    merc_str = _planet("Mercury", lang)

    jup = by.get("Jupiter", {})
    jup_h = _n(jup.get("house"))
    jup_retro = bool(jup.get("is_retrograde"))
    jup_str = _planet("Jupiter", lang)

    # D24
    d24 = vargas.get("D24") if isinstance(vargas.get("D24"), dict) else None
    d24_lg = _n(d24.get("lagna", {}).get("sign_number")) if d24 else None
    d24_pl = [p for p in (d24.get("planets") or []) if isinstance(p, dict)] if d24 else []
    d24_merc_h = _n(next((p.get("house") for p in d24_pl if p.get("name") == "Mercury"), None))
    d24_jup_h = _n(next((p.get("house") for p in d24_pl if p.get("name") == "Jupiter"), None))

    # Vidya yogas
    yogas = [y for y in (chart_data.get("parashara_yogas") or [])
             if isinstance(y, dict) and str(y.get("category", "")).lower() == "vidya"]
    yoga_names = [(y.get("nepali") or y.get("name") or y.get("id", "")) for y in yogas]

    field = _EDU_FIELD_NE.get(five_sign, "") if is_ne else _EDU_FIELD_EN.get(five_sign, "")

    merc_note = ""
    if merc_retro:
        merc_note += (" बुध वक्री भएकाले शिक्षामा पुनः प्रयास वा गैर-परम्परागत विधिबाट सफलताको संकेत छ।" if is_ne else " Retrograde Mercury suggests re-attempts or unconventional learning methods.")
    if merc_comb:
        merc_note += (" बुध अस्त भएकाले आत्म-अभिव्यक्ति र परीक्षामा अतिरिक्त प्रयास आवश्यक हुन्छ।" if is_ne else " Combust Mercury requires extra effort in self-expression and exams.")

    es, ee = ((_ne(bys+8), _ne(bys+22)) if is_ne else (str(bys+8), str(bys+22)))
    hs, he = ((_ne(bys+18), _ne(bys+28)) if is_ne else (str(bys+18), str(bys+28)))

    yoga_txt = (
        f"\n\nयस कुण्डलीमा {', '.join(yoga_names)} विद्या योग सक्रिय रहेका छन् — यसले शैक्षिक उत्कृष्टता र विद्वत्तामा विशेष वरदान दिन्छ।"
        if is_ne else
        f"\n\nActive Vidya yogas in this chart: {', '.join(yoga_names)} — granting academic excellence and scholarly distinction."
    ) if yoga_names else ""

    ch1 = (
        f"यस कुण्डलीमा <b>चतुर्थ भाव</b> (प्राथमिक शिक्षा, मन) को भावेश <b>{four_lord}</b> "
        f"<b>{_ord(four_h, lang)} भाव</b>मा, "
        f"<b>पञ्चम भाव</b> (बुद्धि, विद्या) को भावेश <b>{five_lord}</b> "
        f"<b>{_ord(five_h, lang)} भाव</b>मा र "
        f"<b>नवम भाव</b> (उच्च शिक्षा, भाग्य) को भावेश <b>{nine_lord}</b> "
        f"<b>{_ord(nine_h, lang)} भाव</b>मा रहेका छन्।\n\n"
        f"बुद्धिकारक <b>{merc_str}</b> <b>{_ord(merc_h, lang)} भाव</b>मा "
        f"<b>{_sign(merc_sign, lang)}</b> राशिमा"
        + (" (वक्री)" if merc_retro else "") + " र "
        + f"ज्ञानकारक <b>{jup_str}</b> <b>{_ord(jup_h, lang)} भाव</b>मा"
        + (" (वक्री)" if jup_retro else "") + f" रहेका छन्।{merc_note}\n\n"
        + (f"D24 चतुर्विंशांश कुण्डलीको लग्न <b>{_sign(d24_lg, lang)}</b> र यसमा बुध "
           f"<b>{_ord(d24_merc_h, lang)} भाव</b>मा र गुरु <b>{_ord(d24_jup_h, lang)} भाव</b>मा "
           f"रहेकाले शैक्षिक क्षमताको पुष्टि हुन्छ।" if d24 else "")
        + yoga_txt
        if is_ne else
        f"In this chart, the lord of the <b>fourth house</b> (primary education) <b>{four_lord}</b> is in the "
        f"<b>{_ord(four_h, lang)} house</b>; the fifth lord (intellect/vidya) <b>{five_lord}</b> is in the "
        f"<b>{_ord(five_h, lang)} house</b>; and the ninth lord (higher education) <b>{nine_lord}</b> is in the "
        f"<b>{_ord(nine_h, lang)} house</b>.\n\n"
        f"Intelligence significator <b>{merc_str}</b> is in the <b>{_ord(merc_h, lang)} house</b> in "
        f"<b>{_sign(merc_sign, lang)}</b>"
        + (" (retrograde)" if merc_retro else "") + f"; knowledge significator <b>{jup_str}</b> is in the "
        + f"<b>{_ord(jup_h, lang)} house</b>"
        + (" (retrograde)" if jup_retro else "") + f".{merc_note}\n\n"
        + (f"D24 Chaturvimshamsha ascendant is <b>{_sign(d24_lg, lang)}</b>, with Mercury in the "
           f"<b>{_ord(d24_merc_h, lang)} house</b> and Jupiter in the <b>{_ord(d24_jup_h, lang)} house</b> "
           f"— confirming educational capacity." if d24 else "")
        + yoga_txt
    )

    ch2 = (
        f"<b>समय सन्दर्भ: वि.सं. {es} – {ee}</b>\n\n"
        f"यस अवधिमा चतुर्थेश <b>{four_lord}</b> र पञ्चमेश <b>{five_lord}</b> को दशाले "
        f"प्रारम्भिक शिक्षामा रुचि र सफलताको जग बनाउँछ। "
        f"<b>{_sign(five_sign, lang)}</b> राशिको पञ्चम भाव भएकाले "
        f"<b>{field}</b> क्षेत्रतर्फ स्वाभाविक रुचि विकास हुनेछ।\n\n"
        f"यस उमेरमा बुध र चन्द्रको दशाले स्मरण शक्ति, भाषा दक्षता र गणितीय बुद्धिको विकास गर्दछ।"
        if is_ne else
        f"<b>Time reference: BS {es} – {ee}</b>\n\n"
        f"During this period, the dasha of the fourth lord <b>{four_lord}</b> and fifth lord <b>{five_lord}</b> "
        f"builds foundation in early education. With <b>{_sign(five_sign, lang)}</b> as the fifth house, natural "
        f"aptitude develops toward <b>{field}</b>.\n\n"
        f"Mercury and Moon dashas during this age develop memory, language skills, and mathematical ability."
    )

    ch3 = (
        f"<b>समय सन्दर्भ: वि.सं. {hs} – {he}</b>\n\n"
        f"नवमेश <b>{nine_lord}</b> को <b>{_ord(nine_h, lang)} भाव</b>मा रहेकाले उच्च शिक्षाको "
        f"योग बलियो छ। यस अवधिमा <b>{field}</b> क्षेत्रमा उच्च डिग्री, विशिष्ट तालिम वा विदेश "
        f"अध्ययनको अवसर आउन सक्छ।\n\n"
        f"गुरु (<b>{jup_str}</b>) को दशा वा गोचरमा गुरुको नवम वा पञ्चममा दृष्टि भएको समयमा "
        f"उच्च शिक्षाका लागि अनुकूल अवसरहरू सर्वाधिक प्राप्त हुनेछन्।"
        if is_ne else
        f"<b>Time reference: BS {hs} – {he}</b>\n\n"
        f"The ninth lord <b>{nine_lord}</b> in the <b>{_ord(nine_h, lang)} house</b> strongly supports "
        f"higher education. Opportunities for advanced degrees, specialized training, or foreign study in "
        f"<b>{field}</b> are possible.\n\n"
        f"The most favorable times for higher education are during Jupiter's dasha or when Jupiter transits "
        f"the ninth or fifth house."
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा शैक्षिक संरचना बलियो छ। "
        f"पञ्चमेश <b>{five_lord}</b>, बुध र गुरुको संयुक्त बल र D24 को स्थितिले "
        f"<b>{field}</b> क्षेत्रमा उत्कृष्ट शैक्षिक उपलब्धिको संकेत गर्दछ।\n\n"
        f"सबैभन्दा अनुकूल शिक्षा काल: पञ्चमेश <b>{five_lord}</b>, नवमेश <b>{nine_lord}</b> र "
        f"गुरुको महादशा/अन्तर्दशाको समयमा।\n\n"
        f"<i>यो विश्लेषण D1, D24 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"For this <b>{_sign(ls, lang)} ascendant</b>, the educational structure is strong. The combined "
        f"strength of the fifth lord <b>{five_lord}</b>, Mercury, Jupiter, and D24 placement indicates "
        f"excellent academic achievement in <b>{field}</b>.\n\n"
        f"Most favorable study periods: mahadasha/antardasha of <b>{five_lord}</b>, <b>{nine_lord}</b>, and Jupiter.\n\n"
        f"<i>This analysis is based on D1, D24, and Vimshottari Dasha data.</i>"
    )

    ch6 = (
        f"शैक्षिक उन्नतिका लागि:\n\n"
        f"<b>१. सरस्वती पूजा:</b> बुधबार बुधको आराधना र सरस्वती मन्त्र जपले बुद्धि र स्मरण शक्ति बढाउँछ।\n"
        f"<b>२. पञ्चमेश {five_lord} शान्ति:</b> सम्बन्धित मन्त्र र दानले परीक्षामा सफलता दिलाउँछ।\n"
        f"<b>३. गुरु उपासना:</b> बिहीबार बृहस्पतिको पूजाले उच्च शिक्षाको द्वार खोल्दछ।\n"
        f"<b>४. अध्ययन शैली:</b> नियमित अभ्यास, प्रश्न लेखन र समूह अध्ययनले मन्त्रको जत्तिकै "
        f"शैक्षिक उपलब्धि दिन्छ।"
        if is_ne else
        f"For educational advancement:\n\n"
        f"<b>1. Saraswati worship:</b> Wednesday worship of Mercury and Saraswati mantra boosts intellect and memory.\n"
        f"<b>2. Fifth lord {five_lord} pacification:</b> Related mantra and charity bring exam success.\n"
        f"<b>3. Jupiter worship:</b> Thursday Jupiter puja opens doors to higher education.\n"
        f"<b>4. Study habits:</b> Regular practice, question writing, and group study achieve as much as mantras."
    )

    return [
        {"title": "१. शिक्षाको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Education", "content": ch1},
        {"title": "२. प्रारम्भिक शिक्षा र बौद्धिक विकास" if is_ne else "2. Early Education & Intellectual Growth", "content": ch2},
        {"title": "३. उच्च शिक्षा र विशेषज्ञता" if is_ne else "3. Higher Education & Specialization", "content": ch3},
        {"title": "४. दशाअनुसार शिक्षाको समयक्रम" if is_ne else "4. Education Timeline by Dasha", "content": ch4},
        {"title": "५. समग्र शैक्षिक निष्कर्ष" if is_ne else "5. Overall Education Conclusion", "content": ch5},
        {"title": "६. उपाय तथा मार्गदर्शन" if is_ne else "6. Remedies & Guidance", "content": ch6},
    ]
