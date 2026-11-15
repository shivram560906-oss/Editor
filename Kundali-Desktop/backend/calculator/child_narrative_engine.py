# -*- coding: utf-8 -*-
"""Child Narrative Engine — paragraph-based child analysis."""
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


def generate_child_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    five_lord_en, five_lord, five_h, five_sign_n, five_retro, _ = _house_lord_str(ls, 5, by, lang)
    five_sign = (ls + 3) % 12 + 1
    five_occ = _occ(pl, 5, lang)

    jup = by.get("Jupiter", {})
    jup_h = _n(jup.get("house"))
    jup_sign = _n(jup.get("sign_number"))
    jup_retro = bool(jup.get("is_retrograde"))
    jup_str = _planet("Jupiter", lang)

    # D7 Saptamsha
    d7 = vargas.get("D7") if isinstance(vargas.get("D7"), dict) else None
    d7_lg = _n(d7.get("lagna", {}).get("sign_number")) if d7 else None
    d7_pl = [p for p in (d7.get("planets") or []) if isinstance(p, dict)] if d7 else []
    d7_five_sign = (d7_lg + 3) % 12 + 1 if d7_lg else None
    d7_five_lord_en = SIGN_LORDS[d7_five_sign] if d7_five_sign else None
    d7_five_lord = _planet(d7_five_lord_en, lang) if d7_five_lord_en else "—"
    d7_five_lord_h = _n(next((p.get("house") for p in d7_pl if p.get("name") == d7_five_lord_en), None))
    d7_five_occ = _occ(d7_pl, 5, lang)
    d7_jup_h = _n(next((p.get("house") for p in d7_pl if p.get("name") == "Jupiter"), None))

    retro = (" " + ("पञ्चमेशको वक्री अवस्थाले सन्तान प्राप्तिमा ढिलाइ वा पुनः प्रयासको संकेत गर्दछ।" if is_ne else "Retrograde fifth lord suggests delay or re-attempts in having children.")) if five_retro else ""
    jup_retro_note = (" " + ("गुरु वक्री भएकाले सन्तान प्राप्तिमा विशेष ध्यान र चिकित्सकीय परामर्श आवश्यक हुन सक्छ।" if is_ne else "Retrograde Jupiter may require special attention or medical guidance for conception.")) if jup_retro else ""

    cs, ce = ((_ne(bys+27), _ne(bys+40)) if is_ne else (str(bys+27), str(bys+40)))

    ch1 = (
        f"सन्तान विश्लेषणमा <b>पञ्चम भाव</b> (सन्तान भाव), पञ्चमेश र सन्तान कारक "
        f"<b>बृहस्पति</b> मुख्य आधार हुन्।\n\n"
        f"पञ्चम भाव <b>{_sign(five_sign, lang)}</b> राशिमा पर्छ। "
        f"पञ्चमेश <b>{five_lord}</b> <b>{_ord(five_h, lang)} भाव</b>मा "
        f"<b>{_sign(five_sign_n, lang)}</b> राशिमा रहेका छन्।{retro} "
        f"पञ्चम भावमा: <b>{five_occ}</b>।\n\n"
        f"सन्तानकारक <b>{jup_str}</b> <b>{_ord(jup_h, lang)} भाव</b>मा "
        f"<b>{_sign(jup_sign, lang)}</b> राशिमा रहेका छन्।{jup_retro_note}"
        + (f"\n\nD7 सप्तमांश कुण्डलीको लग्न <b>{_sign(d7_lg, lang)}</b> र यसको पञ्चमेश "
           f"<b>{d7_five_lord}</b> <b>{_ord(d7_five_lord_h, lang)} भाव</b>मा, "
           f"पञ्चम भावमा: <b>{d7_five_occ}</b>, गुरु <b>{_ord(d7_jup_h, lang)} भाव</b>मा — "
           f"सन्तान योगको D7 पुष्टि।" if d7 else "")
        if is_ne else
        f"Child analysis focuses on the <b>fifth house</b> (house of children), its lord, and child "
        f"significator <b>Jupiter</b>.\n\n"
        f"The fifth house falls in <b>{_sign(five_sign, lang)}</b>. "
        f"The fifth lord <b>{five_lord}</b> is in the <b>{_ord(five_h, lang)} house</b> "
        f"in <b>{_sign(five_sign_n, lang)}</b>.{retro} "
        f"Fifth-house occupants: <b>{five_occ}</b>.\n\n"
        f"Child significator <b>{jup_str}</b> is in the <b>{_ord(jup_h, lang)} house</b> "
        f"in <b>{_sign(jup_sign, lang)}</b>.{jup_retro_note}"
        + (f"\n\nD7 Saptamsha ascendant is <b>{_sign(d7_lg, lang)}</b>; fifth lord "
           f"<b>{d7_five_lord}</b> in the <b>{_ord(d7_five_lord_h, lang)} house</b>; "
           f"fifth-house occupants: <b>{d7_five_occ}</b>; Jupiter in <b>{_ord(d7_jup_h, lang)} house</b> "
           f"— D7 confirmation of child yoga." if d7 else "")
    )

    ch2 = (
        f"<b>सन्तान प्राप्तिको प्रमुख समय सन्दर्भ: वि.सं. {cs} – {ce}</b>\n\n"
        f"पञ्चमेश <b>{five_lord}</b> र सन्तानकारक गुरुको महादशा/अन्तर्दशामा सन्तान प्राप्तिको "
        f"सबैभन्दा प्रबल योग रहन्छ। यस समयमा गुरुको गोचर पञ्चम वा सप्तम भावमा थपिएमा "
        f"सन्तान सुखको योग पुष्टि हुनेछ।\n\n"
        f"पञ्चम भावमा शुभ ग्रहको दृष्टि वा गुरुको अनुकूल स्थिति भएका दशा-अन्तर्दशामा "
        f"सन्तान प्राप्तिको सम्भावना सर्वाधिक प्रबल हुन्छ।"
        if is_ne else
        f"<b>Primary child-bearing window: BS {cs} – {ce}</b>\n\n"
        f"The strongest child yoga occurs during the mahadasha/antardasha of the fifth lord "
        f"<b>{five_lord}</b> and Jupiter. If Jupiter also transits the fifth or seventh house during "
        f"this period, the yoga is confirmed.\n\n"
        f"Dasha periods with benefic aspects to the fifth house or favorable Jupiter placement show "
        f"the highest probability of childbirth."
    )

    nature_ne = {1: "साहसी, जिज्ञासु र नेतृत्वकर्ता",2: "स्थिर, कलाप्रेमी र व्यावहारिक",3: "बौद्धिक, सञ्चारप्रेमी र चंचल",4: "भावनाशील, कल्पनाशील र गृहप्रेमी",5: "उत्साही, रचनात्मक र उदार",6: "विश्लेषणात्मक, सेवाभावी र व्यावहारिक",7: "सन्तुलित, सामाजिक र न्यायप्रिय",8: "गहिरो, रहस्यमयी र दृढ",9: "दार्शनिक, आदर्शवादी र उदार",10: "महत्त्वाकाँक्षी, अनुशासित र जिम्मेवार",11: "मौलिक, समाजशील र मानवतावादी",12: "कल्पनाशील, करुणामयी र आध्यात्मिक"}.get(five_sign, "गुणवान्")
    nature_en = {1:"courageous, curious, leader",2:"stable, artistic, practical",3:"intellectual, communicative, versatile",4:"emotional, imaginative, home-loving",5:"enthusiastic, creative, generous",6:"analytical, service-oriented, practical",7:"balanced, social, justice-loving",8:"deep, mysterious, determined",9:"philosophical, idealistic, generous",10:"ambitious, disciplined, responsible",11:"original, sociable, humanitarian",12:"imaginative, compassionate, spiritual"}.get(five_sign, "virtuous")

    ch3 = (
        f"पञ्चम भाव <b>{_sign(five_sign, lang)}</b> राशिमा रहेकाले सन्तानको स्वभाव "
        f"<b>{nature_ne}</b> हुने संकेत गर्दछ।\n\n"
        f"सन्तानको शिक्षा, करियर र भविष्यमा पञ्चमेश <b>{five_lord}</b> को दशा र गुरुको "
        f"गोचरको समयमा विशेष प्रगति र उपलब्धि हासिल हुने देखिन्छ।"
        if is_ne else
        f"With <b>{_sign(five_sign, lang)}</b> as the fifth house, the child's nature tends to be "
        f"<b>{nature_en}</b>.\n\n"
        f"During the fifth lord <b>{five_lord}</b>'s dasha and Jupiter's favorable transit, the child "
        f"makes notable progress in education and career."
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा पञ्चमेश <b>{five_lord}</b> र "
        f"गुरुको स्थितिले सन्तान सुखको बलियो योग छ। "
        + (f"D7 को तथ्यले यो पुष्टि गर्दछ।" if d7 else "")
        + f"\n\nसन्तान प्राप्तिको सर्वोत्तम समय पञ्चमेश र गुरुको अनुकूल दशा-अन्तर्दशामा हुनेछ।\n\n"
        + f"<i>यो विश्लेषण D1, D7 र विंशोत्तरी दशाको तथ्यमा आधारित छ। जैविक वा चिकित्सकीय निर्णयका लागि योग्य चिकित्सकको परामर्श लिनुहोस्।</i>"
        if is_ne else
        f"In this <b>{_sign(ls, lang)} ascendant</b> chart, the strength of fifth lord <b>{five_lord}</b> "
        f"and Jupiter indicates strong child yoga. "
        + (f"D7 Saptamsha confirms this potential." if d7 else "")
        + f"\n\nThe most favorable timing for childbirth occurs during the supportive dasha-antardasha periods of the fifth lord and Jupiter.\n\n"
        + f"<i>This analysis is based on D1, D7, and Vimshottari Dasha data. Consult a qualified clinician for biological or medical decisions.</i>"
    )

    ch6 = (
        f"सन्तान सुख वृद्धि तथा बाधा निवारणका लागि:\n\n"
        f"<b>१. बृहस्पति पूजा:</b> बिहीबार बृहस्पतिको पूजा र पीत वस्त्र दान — सन्तानकारकको बल बढाउँछ।\n"
        f"<b>२. पञ्चमेश {five_lord} शान्ति:</b> सम्बन्धित मन्त्र र दानले सन्तान प्राप्तिमा बाधा हटाउँछ।\n"
        f"<b>३. संतान गोपाल मन्त्र:</b> 'ॐ देवकीसुत गोविन्द वासुदेव जगत्पते' मन्त्रको नित्य जप।\n"
        f"<b>४. व्यावहारिक सुझाव:</b> सन्तान प्राप्तिमा ढिलाइ भए चिकित्सकीय परामर्श पनि उत्तिकै "
        f"महत्त्वपूर्ण छ।"
        if is_ne else
        f"To enhance child blessings and remove obstacles:\n\n"
        f"<b>1. Jupiter worship:</b> Thursday Jupiter puja and yellow donations strengthen the child significator.\n"
        f"<b>2. Fifth lord {five_lord} pacification:</b> Its mantra and charity remove child-related obstacles.\n"
        f"<b>3. Santana Gopala Mantra:</b> Daily recitation of 'Om Devakisuta Govinda Vasudeva Jagatpate'.\n"
        f"<b>4. Practical advice:</b> If delays occur, medical consultation is equally important as astrological remedies."
    )

    return [
        {"title": "१. सन्तान योगको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Child Yoga", "content": ch1},
        {"title": "२. सन्तान प्राप्तिको समय र योग" if is_ne else "2. Timing & Yoga for Having Children", "content": ch2},
        {"title": "३. सन्तानको स्वभाव र भविष्य" if is_ne else "3. Child's Nature & Future", "content": ch3},
        {"title": "४. दशाअनुसार सन्तान जीवनको समयक्रम" if is_ne else "4. Child Life Timeline by Dasha", "content": ch4},
        {"title": "५. समग्र निष्कर्ष" if is_ne else "5. Overall Conclusion", "content": ch5},
        {"title": "६. उपाय तथा मार्गदर्शन" if is_ne else "6. Remedies & Guidance", "content": ch6},
    ]
