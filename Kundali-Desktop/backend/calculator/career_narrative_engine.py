# -*- coding: utf-8 -*-
"""Career Narrative Engine — paragraph-based career analysis."""
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

_CAREER_NE = {
    1: "साहसिक, सैनिक, इञ्जिनियरिङ, नेतृत्व, प्रहरी",
    2: "बैङ्किङ, कला, सौन्दर्य, कृषि, खाद्य उद्योग",
    3: "लेखन, सञ्चार, पत्रकारिता, यातायात, बिक्री",
    4: "अचल सम्पत्ति, शिक्षण, कृषि, गृह व्यवस्थापन",
    5: "सरकारी सेवा, राजनीति, शिक्षा, मनोरञ्जन",
    6: "स्वास्थ्य, चिकित्सा, कानुन, लेखा, सेवा",
    7: "व्यापार, कूटनीति, साझेदारी, न्याय, सम्पर्क",
    8: "अनुसन्धान, बीमा, गोप्य कार्य, उत्खनन, ज्योतिष",
    9: "शिक्षा, दर्शन, धर्म, विदेश सम्बन्ध, प्रकाशन",
    10: "राजनीति, प्रशासन, इञ्जिनियरिङ, औद्योगिक",
    11: "प्रविधि, नेटवर्किङ, सामाजिक संस्था, व्यापार",
    12: "अध्यात्म, विदेश सेवा, अनुसन्धान, अस्पताल, एनजीओ",
}
_CAREER_EN = {
    1: "military, engineering, leadership, sports, adventure",
    2: "banking, arts, beauty, agriculture, food industry",
    3: "writing, media, journalism, transport, sales",
    4: "real estate, teaching, agriculture, home management",
    5: "government service, politics, education, entertainment",
    6: "healthcare, medicine, law, accounting, service",
    7: "business, diplomacy, partnerships, trade, justice",
    8: "research, insurance, investigation, occult, mining",
    9: "academia, philosophy, religion, foreign relations, publishing",
    10: "politics, administration, engineering, industry",
    11: "technology, networking, social work, import-export",
    12: "spirituality, foreign service, research, hospital, NGO",
}


try:
    from backend.calculator.career_analysis_engine import calculate_comprehensive_career_analysis
except ImportError:
    from calculator.career_analysis_engine import calculate_comprehensive_career_analysis


def generate_career_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    # Compute comprehensive 8-step Parashari career analysis
    try:
        p_res = calculate_comprehensive_career_analysis(chart_data, language=lang)
    except Exception:
        p_res = {}

    s1 = p_res.get("step1_core_factors", {})
    s2 = p_res.get("step2_tenth_house_and_aspects", {})
    s3 = p_res.get("step3_karmadhipati_sign", {})
    s4 = p_res.get("step4_sun_karmakaraka", {})
    s5 = p_res.get("step5_planetary_influences", {})
    s6 = p_res.get("step6_business_vs_service", {})
    s7 = p_res.get("step7_d10_dasamsa", {})
    s8 = p_res.get("step8_timing_and_remedies", {})

    # Tenth house
    ten_sign = (ls + 8) % 12 + 1
    ten_lord_en, ten_lord, ten_h, ten_sign_n, ten_retro, ten_comb = _house_lord_str(ls, 10, by, lang)
    ten_occ = _occ(pl, 10, lang)
    la_lord_en, la_lord, la_h, _, _, _ = _house_lord_str(ls, 1, by, lang)

    # D10
    d10 = vargas.get("D10") if isinstance(vargas.get("D10"), dict) else None
    d10_lg = _n(d10.get("lagna", {}).get("sign_number")) if d10 else None
    d10_pl = [p for p in (d10.get("planets") or []) if isinstance(p, dict)] if d10 else []
    d10_occ = _occ(d10_pl, 10, lang)

    # Jaimini Amatyakaraka
    jaimini = chart_data.get("jaimini") or {}
    jaimini = jaimini if isinstance(jaimini, dict) else {}
    kk = jaimini.get("chara_karakas") or {}
    kk = kk if isinstance(kk, dict) else {}
    amk_r = kk.get("Amatyakaraka")
    amk_en = (amk_r.get("planet") or amk_r.get("name")) if isinstance(amk_r, dict) else amk_r
    amk = _planet(str(amk_en), lang) if amk_en else None

    ct = s3.get("professions_ne", "") if is_ne else s3.get("professions_en", "")
    if not ct:
        ct = _CAREER_NE.get(ten_sign, "") if is_ne else _CAREER_EN.get(ten_sign, "")

    retro = (" " + ("दशमेशको वक्री अवस्थाले सुरुमा करियरमा केही उतारचढाव वा पुनः प्रयासको संकेत गर्दछ।" if is_ne else "The retrograde tenth lord suggests instability or re-attempts early in career.")) if ten_retro else ""
    comb = (" " + ("दशमेश अस्त भएकाले वरिष्ठसँग तालमेल मिलाउन अतिरिक्त ध्यान दिनुपर्ने हुन्छ।" if is_ne else "Combust tenth lord may bring conflict with superiors, offset by merit.")) if ten_comb else ""

    d10_note = ""
    if d10:
        d10_note = (f" D10 दशमांश लग्न <b>{_sign(d10_lg, lang)}</b> र दशम भावमा <b>{d10_occ}</b> — यो संकेत D-10 वर्ग कुण्डलीले समेत पुष्टि गर्दछ।" if is_ne else f" D10 ascendant <b>{_sign(d10_lg, lang)}</b> with <b>{d10_occ}</b> in tenth — corroborated by D-10.")
    amk_note = (f" जैमिनि अनुसार <b>{amk}</b> अमात्यकारक — पेशागत उन्नतिमा {amk} ग्रहको भूमिका निर्णायक रहनेछ।" if is_ne else f" Jaimini Amatyakaraka is <b>{amk}</b> — decisive for career growth.") if amk else ""

    sun_note = ""
    if s4:
        sun_note = (
            f"\n\n<b>कर्मकारक सूर्य विश्लेषण:</b> सूर्य {s4.get('house','')} भावमा ({s4.get('dignity_ne','')}) "
            f"रहेकाले प्रशासनिक क्षमता र नेतृत्व स्तर: <b>{s4.get('leadership_status_ne','')}</b>। "
            f"{s4.get('digbala_note_ne','')}"
            if is_ne else
            f"\n\n<b>Karmakaraka Sun Analysis:</b> Sun in house {s4.get('house','')} indicates leadership capacity: <b>{s4.get('leadership_status_ne','')}</b>."
        )

    b_v_s_note = ""
    if s6:
        b_v_s_note = (
            f"\n\n<b>स्वतन्त्र व्यवसाय वा नोकरी निर्णय:</b> {s6.get('category_ne','')}<br>"
            f"• <i>{s6.get('verdict_ne','')}</i>"
            if is_ne else
            f"\n\n<b>Business vs Service Determination:</b> {s6.get('category_ne','')}<br>"
            f"• <i>{s6.get('verdict_ne','')}</i>"
        )

    ch1 = (
        f"यस कुण्डलीको <b>दशम भाव (कर्म भाव)</b> <b>{_sign(ten_sign, lang)}</b> राशिमा पर्दछ। "
        f"दशमेश <b>{ten_lord}</b> <b>{_ord(ten_h, lang)} भाव</b>मा "
        f"<b>{_sign(ten_sign_n, lang)}</b> राशिमा अवस्थित छ।{retro}{comb} "
        f"दशम भावमा: <b>{ten_occ}</b>। "
        f"लग्न <b>{_sign(ls, lang)}</b> र लग्नेश <b>{la_lord}</b> <b>{_ord(la_h, lang)} भाव</b>मा "
        f"रहेकाले व्यक्तिगत पहल र आत्मविश्वासले पेशागत उन्नतिमा महत्त्वपूर्ण भूमिका खेल्दछ।{d10_note}{amk_note}\n\n"
        f"<b>{_sign(ten_sign, lang)}</b> राशिको दशम भाव भएकाले बृहत्पाराशर होराशास्त्र अनुसार यस जातकको स्वाभाविक पेशागत झुकाव मुख्यतः "
        f"<b>{ct}</b> क्षेत्रतर्फ हुनेछ।{sun_note}{b_v_s_note}"
        if is_ne else
        f"The <b>tenth house (career)</b> falls in <b>{_sign(ten_sign, lang)}</b>. "
        f"The tenth lord <b>{ten_lord}</b> is in the <b>{_ord(ten_h, lang)} house</b> "
        f"in <b>{_sign(ten_sign_n, lang)}</b>.{retro}{comb} "
        f"Planets in tenth: <b>{ten_occ}</b>. "
        f"Ascendant <b>{_sign(ls, lang)}</b> with ascendant lord <b>{la_lord}</b> in the "
        f"<b>{_ord(la_h, lang)} house</b> — personal initiative is key.{d10_note}{amk_note}\n\n"
        f"With <b>{_sign(ten_sign, lang)}</b> as the tenth house, classical Parashari aptitude points to <b>{ct}</b>.{sun_note}{b_v_s_note}"
    )

    ys, ye = ((_ne(bys+20), _ne(bys+32)) if is_ne else (str(bys+20), str(bys+32)))
    ms, me = ((_ne(bys+32), _ne(bys+50)) if is_ne else (str(bys+32), str(bys+50)))

    ch2 = (
        f"<b>समय सन्दर्भ: वि.सं. {ys} – {ye}</b>\n\n"
        f"यस अवधिमा जातकको करियरको पहिलो अध्याय सुरु हुन्छ। "
        f"दशमेश <b>{ten_lord}</b> को <b>{_ord(ten_h, lang)} भाव</b>मा अवस्थिति र "
        f"लग्नेश <b>{la_lord}</b> को प्रभावले पहिलो रोजगारी, सेवा प्रवेश वा व्यावसायिक तालिमको योग बलियो छ। "
        f"प्रारम्भमा नयाँ वातावरणसँग अनुकूलन र अनुभव संकलनको समय हुनेछ।\n\n"
        f"<b>{_sign(ls, lang)}</b> लग्नका जातक परिश्रमी र जिम्मेवार भएकाले यस चरणका संघर्षहरू "
        f"भविष्यको सफलताको जग बन्नेछन्।"
        if is_ne else
        f"<b>Time reference: BS {ys} – {ye}</b>\n\n"
        f"This marks the start of the career journey. The tenth lord <b>{ten_lord}</b> in the "
        f"<b>{_ord(ten_h, lang)} house</b>, with <b>{la_lord}</b>'s influence, supports entry into "
        f"employment or vocational training. Early years bring adjustment and experience-gathering.\n\n"
        f"Natives of <b>{_sign(ls, lang)}</b> ascendant are naturally diligent; early struggles lay the "
        f"foundation for future success."
    )

    ch3 = (
        f"<b>समय सन्दर्भ: वि.सं. {ms} – {me}</b>\n\n"
        f"यस चरण जातकको जीवनको सबैभन्दा सक्रिय करियर काल हो। "
        f"दशमेश <b>{ten_lord}</b> को <b>{_ord(ten_h, lang)} भाव</b>मा रहेकाले "
        f"पदोन्नति, नेतृत्व भूमिका वा ठूलो जिम्मेवारी लिने अवसर आउँछ।\n\n"
        f"<b>{_sign(ten_sign, lang)}</b> राशिको प्रकृति अनुसार <b>{ct}</b> "
        f"क्षेत्रमा विशेष मान्यता र उपलब्धि हासिल हुनेछ। "
        f"यस अवधिमा आर्थिक स्थायित्व, सामाजिक प्रतिष्ठा र व्यावसायिक पहिचानमा उल्लेखनीय वृद्धि हुनेछ।"
        if is_ne else
        f"<b>Time reference: BS {ms} – {me}</b>\n\n"
        f"This is the most active and productive career phase. The tenth lord <b>{ten_lord}</b> in the "
        f"<b>{_ord(ten_h, lang)} house</b> brings promotions, leadership roles, and greater responsibilities.\n\n"
        f"Consistent with <b>{_sign(ten_sign, lang)}</b> as the tenth house, notable achievement in "
        f"<b>{ct}</b> is indicated, along with financial stability and growing social standing."
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)
    if s8 and s8.get("transit_trigger_ne"):
        ch4 += (
            f"\n\n<b>गोचर सक्रियता:</b> {s8.get('transit_trigger_ne')}"
            if is_ne else
            f"\n\n<b>Transit Trigger:</b> Jupiter/Saturn transits over the 10th house or 10th lord initiate major career growth and structural evolution."
        )

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा दशमेश <b>{ten_lord}</b> को "
        f"<b>{_ord(ten_h, lang)} भाव</b>मा उपस्थितिले करियरमा क्रमिक र दिगो उन्नतिको संकेत गर्दछ। "
        f"<b>{ct}</b> क्षेत्रमा जातकको स्वाभाविक दक्षता भएकाले यही क्षेत्रमा दीर्घकालीन सफलता सम्भव छ।\n\n"
        f"• <b>पेशागत स्वरूप:</b> {s6.get('verdict_ne', '')}\n\n"
        f"सबैभन्दा अनुकूल करियर काल: दशमेश <b>{ten_lord}</b> र लग्नेश <b>{la_lord}</b> को "
        f"महादशा/अन्तर्दशाको समयमा उच्च पदमा पुग्ने, सम्मान पाउने र आर्थिक स्थायित्व हासिल गर्ने "
        f"सबैभन्दा प्रबल योग हुनेछ।\n\n"
        f"<i>यो विश्लेषण बृहत्पाराशर होराशास्त्रको ८-चरणे कर्माधिपति सिद्धान्त, D1, D10 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"For this <b>{_sign(ls, lang)} ascendant</b> chart, the tenth lord <b>{ten_lord}</b> in the "
        f"<b>{_ord(ten_h, lang)} house</b> signals steady, sustained career growth. Long-term success "
        f"is most probable in <b>{ct}</b>.\n\n"
        f"Most favorable periods: mahadasha/antardasha of <b>{ten_lord}</b> and <b>{la_lord}</b>, "
        f"bringing recognition, promotion, and financial stability.\n\n"
        f"<i>This analysis is based on BPHS 8-step Karma rules, D1, D10, and Vimshottari Dasha data.</i>"
    )

    remedy_items = s8.get("remedies", [])
    if remedy_items and is_ne:
        ch6 = (
            "करियर सम्बन्धी अनुकूलता वृद्धिका लागि बृहत्पाराशर होराशास्त्र अनुसार शास्त्रीय उपायहरू:\n\n"
            + "\n".join([f"• {r}" for r in remedy_items])
        )
    else:
        ch6 = (
            f"करियर सम्बन्धी अनुकूलता वृद्धिका लागि:\n\n"
            f"<b>१. दशमेश {ten_lord} को उपासना:</b> सम्बन्धित वारमा मन्त्र जप लाभदायक।\n"
            f"<b>२. कर्म अनुशासन:</b> इमानदारी, समयपालन, व्यावसायिकता — ग्रहीय प्रतिकूलता कम गर्ने सर्वोत्तम उपाय।\n"
            f"<b>३. सूर्य अर्घ्य र उपासना:</b> नित्य बिहान सूर्यलाई जल अर्पण र आदित्य हृदय स्तोत्र पाठ।\n"
            f"<b>४. शनि दोष निवारण:</b> शनिको प्रतिकूल प्रभाव भए शनिबार तेल दान र हनुमान आराधना हितकर।"
            if is_ne else
            f"To strengthen career-related planetary influences:\n\n"
            f"<b>1. Worship tenth lord {ten_lord}:</b> Chanting its mantra on its weekday is beneficial.\n"
            f"<b>2. Professional discipline:</b> Honesty, punctuality, and professionalism are the strongest remedies.\n"
            f"<b>3. Solar propitiation:</b> Morning water offering (Arghya) to the Sun with Aditya Hridaya Stotra.\n"
            f"<b>4. Saturn remediation:</b> Oil donation on Saturdays and Hanuman Chalisa if Saturn is adverse."
        )

    return [
        {"title": "१. करियर तथा पेशाको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Career", "content": ch1},
        {"title": "२. युवा अवस्थाको करियर यात्रा" if is_ne else "2. Career in Early Adulthood", "content": ch2},
        {"title": "३. मध्यम जीवनको पेशागत उचाइ" if is_ne else "3. Professional Peak in Mid-Life", "content": ch3},
        {"title": "४. दशाअनुसार करियरको समयक्रम" if is_ne else "4. Career Timeline by Dasha", "content": ch4},
        {"title": "५. समग्र निष्कर्ष" if is_ne else "5. Overall Conclusion", "content": ch5},
        {"title": "६. उपाय तथा मार्गदर्शन" if is_ne else "6. Remedies & Guidance", "content": ch6},
    ]

