# -*- coding: utf-8 -*-
"""Marriage Narrative Engine — paragraph-based marriage analysis."""
from __future__ import annotations
from typing import Optional
try:
    from backend.calculator.narrative_shared import (
        _n, _ne, _sign, _planet, _ord, _bs_span, _occ,
        _house_lord_str, _base, _dasha_chapters_html, SIGN_LORDS,
    )
    from backend.calculator.marriage_timing_engine import (
        calculate_mathematical_formulas,
        find_marriage_windows_age_15_to_50,
        SIGN_NAMES_NE,
        SIGN_NAMES_EN,
    )
    from backend.calculator.marriage_direction_engine import calculate_marriage_direction
except ImportError:
    from calculator.narrative_shared import (
        _n, _ne, _sign, _planet, _ord, _bs_span, _occ,
        _house_lord_str, _base, _dasha_chapters_html, SIGN_LORDS,
    )
    from calculator.marriage_timing_engine import (
        calculate_mathematical_formulas,
        find_marriage_windows_age_15_to_50,
        SIGN_NAMES_NE,
        SIGN_NAMES_EN,
    )
    from calculator.marriage_direction_engine import calculate_marriage_direction



_SIGN_PARTNER_NE = {
    1: "साहसी, नेतृत्वकर्ता, स्वतन्त्र",
    2: "व्यावहारिक, कलात्मक, स्थिर",
    3: "बौद्धिक, सञ्चारप्रेमी, चंचल",
    4: "भावनाशील, गृहप्रेमी, संवेदनशील",
    5: "उत्साही, रचनात्मक, उदार",
    6: "विश्लेषणात्मक, सेवाभावी, व्यावहारिक",
    7: "सामाजिक, सन्तुलित, सहकारी",
    8: "गहिरो, रहस्यमयी, दृढ",
    9: "दार्शनिक, आदर्शवादी, उदार",
    10: "महत्त्वाकाँक्षी, अनुशासित, जिम्मेवार",
    11: "मौलिक, समाजशील, मानवतावादी",
    12: "कल्पनाशील, करुणामयी, आध्यात्मिक",
}
_SIGN_PARTNER_EN = {
    1: "courageous, independent, leader",
    2: "practical, artistic, stable",
    3: "intellectual, communicative, versatile",
    4: "emotional, home-loving, sensitive",
    5: "enthusiastic, creative, generous",
    6: "analytical, service-oriented, practical",
    7: "social, balanced, cooperative",
    8: "deep, mysterious, determined",
    9: "philosophical, idealistic, generous",
    10: "ambitious, disciplined, responsible",
    11: "original, sociable, humanitarian",
    12: "imaginative, compassionate, spiritual",
}


try:
    from backend.calculator.marriage_analysis_engine import calculate_comprehensive_marriage_analysis
except ImportError:
    from calculator.marriage_analysis_engine import calculate_comprehensive_marriage_analysis


def generate_marriage_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
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

    # Compute comprehensive 9-step Parashari marriage analysis
    try:
        p_res = calculate_comprehensive_marriage_analysis(chart_data, language=lang)
    except Exception:
        p_res = {}

    s1 = p_res.get("step1_core_factors", {})
    s2 = p_res.get("step2_seventh_house_and_aspects", {})
    s3 = p_res.get("step3_mangal_dosha", {})
    s4 = p_res.get("step4_karakas", {})
    s5 = p_res.get("step5_obstacles_and_yogas", {})
    s6 = p_res.get("step6_d9_navamsha", {})
    s7 = p_res.get("step7_spouse_characteristics", {})
    s8 = p_res.get("step8_timing_and_remedies", {})
    s9 = p_res.get("step9_ashtakoot_guidelines", {})

    seven_lord_en, seven_lord, seven_h, seven_sign_n, seven_retro, seven_comb = _house_lord_str(ls, 7, by, lang)
    seven_sign = (ls + 5) % 12 + 1
    seven_occ = _occ(pl, 7, lang)

    # Venus
    venus = by.get("Venus", {})
    venus_h = _n(venus.get("house"))
    venus_sign = _n(venus.get("sign_number"))
    venus_str = _planet("Venus", lang)

    # D9 navamsha
    d9 = vargas.get("D9") if isinstance(vargas.get("D9"), dict) else None
    d9_lg = _n(d9.get("lagna", {}).get("sign_number")) if d9 else None

    # Check Mangal Dosha
    mangal_dosha = s3.get("has_dosha", False)
    mars = by.get("Mars", {})
    mars_h = _n(mars.get("house"))

    partner_nature = s7.get("traits_ne", "") if is_ne else s7.get("traits_en", "")
    if not partner_nature:
        partner_nature = _SIGN_PARTNER_NE.get(seven_sign, "") if is_ne else _SIGN_PARTNER_EN.get(seven_sign, "")

    retro = (" " + ("सप्तमेशको वक्री अवस्थाले विवाहमा ढिलाइ वा पुनः विचार गर्नुपर्ने संकेत गर्दछ।" if is_ne else "Retrograde seventh lord suggests marriage delay or reconsideration.")) if seven_retro else ""
    comb = (" " + ("सप्तमेश अस्त भएकाले जीवनसाथीसँग सुरुमा मतभेद हुन सक्छ।" if is_ne else "Combust seventh lord may bring initial disagreements with partner.")) if seven_comb else ""

    mangal_status = s3.get("status_ne", "")
    bhangas_text = (" (भंग योग: " + " ".join(s3.get("bhangas", [])) + ")" if s3.get("bhangas") else "") if is_ne else ""
    mangal_note = (
        f"\n\n<b>मङ्गल दोष विश्लेषण:</b> {mangal_status}{bhangas_text}"
        if is_ne else
        (f"\n\n<b>Mangal Dosha:</b> Mars in house {mars_h} evaluated. " + ("Dosha cancelled by classical rules." if s3.get("is_cancelled") else "Active Mangal Dosha."))
    ) if mangal_dosha else "\n\n<b>मङ्गल दोष:</b> कुण्डलीमा कुनै मङ्गल दोष छैन।" if is_ne else "\n\n<b>Mangal Dosha:</b> No Mangal Dosha in this chart."

    ch1 = (
        f"यस कुण्डलीको <b>सप्तम भाव (दाम्पत्य भाव)</b> <b>{_sign(seven_sign, lang)}</b> राशिमा पर्दछ। "
        f"सप्तमेश <b>{seven_lord}</b> <b>{_ord(seven_h, lang)} भाव</b>मा "
        f"<b>{_sign(seven_sign_n, lang)}</b> राशिमा अवस्थित छ।{retro}{comb} "
        f"सप्तम भावमा: <b>{seven_occ}</b>।\n\n"
        f"विवाहकारक ग्रह <b>{venus_str}</b> <b>{_ord(venus_h, lang)} भाव</b>मा "
        f"<b>{_sign(venus_sign, lang)}</b> राशिमा रहेकाले दाम्पत्य जीवनमा {venus_str} को "
        f"कारकत्व प्रत्यक्ष सक्रिय रहनेछ। "
        f"कुटुम्ब (२ भाव) र माङ्गल्य (८ भाव) को स्थितिले पारिवारिक स्थायित्वलाई टेवा दिन्छ।"
        + (f" नवमांश कुण्डली (D-9) को लग्न <b>{_sign(d9_lg, lang)}</b> रहेकाले जीवनसाथीसँगको "
           f"मनोवैज्ञानिक सम्बन्ध र गहिरो बन्धनको पुष्टि हुन्छ।" if d9 else "")
        + mangal_note
        if is_ne else
        f"The <b>seventh house (marriage)</b> falls in <b>{_sign(seven_sign, lang)}</b>. "
        f"The seventh lord <b>{seven_lord}</b> is in the <b>{_ord(seven_h, lang)} house</b> "
        f"in <b>{_sign(seven_sign_n, lang)}</b>.{retro}{comb} "
        f"Seventh-house occupants: <b>{seven_occ}</b>.\n\n"
        f"Marriage significator <b>{venus_str}</b> is in the <b>{_ord(venus_h, lang)} house</b> "
        f"in <b>{_sign(venus_sign, lang)}</b>, making its significations directly active in marital life."
        + (f" The D9 Navamsha ascendant is <b>{_sign(d9_lg, lang)}</b>, confirming depth of partnership." if d9 else "")
        + mangal_note
    )


    ch2 = (
        f"सप्तम भाव <b>{_sign(seven_sign, lang)}</b> राशिमा रहेकाले जीवनसाथी स्वभावतः "
        f"<b>{partner_nature}</b> हुनेछ। "
        f"सप्तमेश <b>{seven_lord}</b> को <b>{_ord(seven_h, lang)} भाव</b>मा रहेकाले "
        f"जीवनसाथी {seven_lord} ग्रहका गुणहरू — जस्तै बुद्धिमत्ता, जिम्मेवारी र व्यावहारिकता — "
        f"प्रदर्शन गर्नेछ।\n\n"
        f"{venus_str} <b>{_ord(venus_h, lang)} भाव</b>मा रहेकाले जीवनसाथीको "
        f"सौन्दर्यबोध, कलात्मक रुचि वा व्यावहारिक क्षमता उल्लेखनीय हुनेछ। "
        f"सम्बन्धमा आपसी सम्मान, खुला संवाद र परिवारप्रति समर्पणले दाम्पत्य जीवन सुखमय बन्नेछ।"
        if is_ne else
        f"Because the seventh house is in <b>{_sign(seven_sign, lang)}</b>, the life partner will be "
        f"<b>{partner_nature}</b> by disposition. "
        f"With the seventh lord <b>{seven_lord}</b> placed in the <b>{_ord(seven_h, lang)} house</b>, "
        f"the partner will exhibit qualities associated with {seven_lord} — such as "
        f"intelligence, responsibility, and practical capability.\n\n"
        f"{venus_str} in the <b>{_ord(venus_h, lang)} house</b> indicates the partner will have "
        f"notable aesthetic sense, artistic flair, or capability. "
        f"Mutual respect, open communication, and family dedication make married life harmonious."
    )

    math_res = calculate_mathematical_formulas(chart_data)
    f1_str = math_res["formula_1"]["formatted_ne"] if is_ne else math_res["formula_1"]["formatted_en"]
    f2_str = math_res["formula_2"]["formatted_ne"] if is_ne else math_res["formula_2"]["formatted_en"]
    f1_sign_name = SIGN_NAMES_NE[math_res["formula_1"]["sign_0"]] if is_ne else SIGN_NAMES_EN[math_res["formula_1"]["sign_0"]]
    f2_sign_name = SIGN_NAMES_NE[math_res["formula_2"]["sign_0"]] if is_ne else SIGN_NAMES_EN[math_res["formula_2"]["sign_0"]]

    windows = find_marriage_windows_age_15_to_50(chart_data, min_score=40)

    # Build windows formatted list
    windows_html_ne = ""
    windows_html_en = ""
    if windows:
        for idx, w in enumerate(windows, 1):
            bs_str = f" (वि.सं. {w['bs_start']} देखि {w['bs_end']})" if w.get("bs_start") and w.get("bs_end") else ""
            indicators_list_ne = "".join([f"<li>✓ {ind}</li>" for ind in w["indicators_ne"]])
            windows_html_ne += (
                f"\n\n<b>{_ne(idx)}. सम्भावित अवधि: {w['start_date']} देखि {w['end_date']}{bs_str}</b><br/>"
                f"• उमेर: <b>{_ne(w['age_start'])} – {_ne(w['age_end'])} वर्ष</b> | सम्भाव्यता / बल: <b>{_ne(w['score'])}% ({w['strength_ne']})</b><br/>"
                f"• सक्रिय सूचकहरू:<br/><ul>{indicators_list_ne}</ul>"
            )
            indicators_list_en = "".join([f"<li>✓ {ind}</li>" for ind in w["indicators_en"]])
            windows_html_en += (
                f"\n\n<b>{idx}. Probable Period: {w['start_date']} to {w['end_date']}</b><br/>"
                f"• Age: <b>{w['age_start']} – {w['age_end']} yrs</b> | Probability / Strength: <b>{w['score']}% ({w['strength_en']})</b><br/>"
                f"• Active Indicators:<br/><ul>{indicators_list_en}</ul>"
            )
    else:
        # No window passed the classical score threshold.  Keep the narrative
        # useful by naming the age-15-to-50 search span instead of referring to
        # undefined variables (the previous ``ms``/``me`` names crashed here).
        start_bs = bys + 15
        end_bs = bys + 50
        windows_html_ne = (
            f"\n\n<i>वि.सं. {_ne(start_bs)} – {_ne(end_bs)} को सामान्य दशा अवधिमा "
            "अनुकूल गोचर सक्रिय रहँदा विवाहको अवसर बन्नेछ।</i>"
        )
        windows_html_en = (
            f"\n\n<i>Favorable opportunities arise between BS {start_bs} and "
            f"BS {end_bs} when supportive transits are active.</i>"
        )

    ch3 = (
        f"<b>विवाह समय निर्धारण गर्ने संयुक्त सूत्र (गोचर पद्धति + गणितीय विधि):</b>\n\n"
        f"<b>१. गोचर पद्धति (Primary Transits):</b>\n"
        f"• लग्नेश, सप्तमेश (<b>{seven_lord}</b>) वा <b>{venus_str}</b> ले सप्तम भाव (<b>{_sign(seven_sign, lang)}</b>) वा लग्न (<b>{_sign(ls, lang)}</b>) मा गोचर गर्दा विवाह योग सक्रिय हुन्छ।\n"
        f"• <b>बृहस्पति तथा शनि</b> ले सप्तम भाव, सप्तमबाट ५/९ भाव, जन्म शुक्रको राशि (<b>{_sign(venus_sign, lang)}</b>), वा लग्न/सप्तममा गोचर गर्दा विवाहको प्रमुख अवसर खुल्दछ।\n\n"
        f"<b>२. गणितीय स्पष्ट योग तथा पुष्टि (DMS Verification):</b>\n"
        f"• <b>सूत्र–१ (लग्नेश + सप्तमेश स्पष्ट):</b> <code>{f1_str}</code><br/>"
        f"  $\rightarrow$ उक्त प्राप्त <b>{f1_sign_name}</b> राशि वा त्यसबाट ५औँ/९औँ राशिमा बृहस्पतिको गोचर विवाहका लागि अत्यन्त शुभ मानिन्छ।\n"
        f"• <b>सूत्र–२ (लग्नेश + सप्तमेश + शुक्र स्पष्ट):</b> <code>{f2_str}</code><br/>"
        f"  $\rightarrow$ उक्त प्राप्त <b>{f2_sign_name}</b> राशि वा ५औँ/९औँ राशिमा बृहस्पतिको गोचरले विवाह समयको थप बलियो पुष्टि गर्दछ।\n\n"
        f"<b>३. १५ देखि ५० वर्ष उमेर भित्रका सम्भावित विवाह अवधिहरू (Chronological Order):</b>"
        f"{windows_html_ne}"
        if is_ne else
        f"<b>Unified Marriage Timing System (Transit + Mathematical Verification):</b>\n\n"
        f"<b>1. Primary Transit Rules:</b>\n"
        f"• Lagna lord, 7th lord (<b>{seven_lord}</b>), or <b>{venus_str}</b> transiting the 7th house (<b>{_sign(seven_sign, lang)}</b>) or 1st house (<b>{_sign(ls, lang)}</b>) activates marriage timing.\n"
        f"• <b>Jupiter and Saturn</b> transiting the 7th house, 5th/9th from 7th, natal Venus sign (<b>{_sign(venus_sign, lang)}</b>), or Lagna/7th house.\n\n"
        f"<b>2. Mathematical Longitude Verification (DMS Formulations):</b>\n"
        f"• <b>Formula 1 (Lagna Lord + 7th Lord):</b> <code>{f1_str}</code><br/>"
        f"  $\rightarrow$ Jupiter transiting <b>{f1_sign_name}</b> or 5th/9th from it indicates prime marriage opportunities.\n"
        f"• <b>Formula 2 (Lagna Lord + 7th Lord + Venus):</b> <code>{f2_str}</code><br/>"
        f"  $\rightarrow$ Jupiter transiting <b>{f2_sign_name}</b> or 5th/9th from it provides cross-verified confirmation.\n\n"
        f"<b>3. Probable Marriage Windows (Age 15 to 50, Chronological Order):</b>"
        f"{windows_html_en}"
    )

    # ── विवाह हुने दिशा निर्धारण (Marriage Direction Determination) ──────────
    dir_res = calculate_marriage_direction(chart_data)
    p_dir = dir_res["primary_direction"]
    s_dir = dir_res["secondary_direction"]
    confidence_label = dir_res["confidence_label_ne"] if is_ne else dir_res["confidence_label_en"]
    p_name = p_dir["name_ne"] if is_ne else p_dir["name_en"]
    s_name = s_dir["name_ne"] if is_ne else s_dir["name_en"]
    zone_str = f" ({dir_res['combined_zone_ne']})" if is_ne and dir_res.get('combined_zone_ne') else (f" ({dir_res['combined_zone_en']})" if dir_res.get('combined_zone_en') else "")

    evidence_ne = "".join([
        f"<li><b>{e['rule_name_ne']}:</b> {e['source']} $\\rightarrow$ <b>{e['direction_ne']}</b> (भार: {_ne(e['weight'])})</li>"
        for e in dir_res["evidence"]
    ])
    evidence_en = "".join([
        f"<li><b>{e['rule_name_en']}:</b> {e['source']} $\\rightarrow$ <b>{e['direction_en']}</b> (Weight: {e['weight']})</li>"
        for e in dir_res["evidence"]
    ])

    ch_dir = (
        f"<b>विवाह हुने सम्भावित मुख्य दिशा: {p_name}{zone_str}</b><br/>"
        f"• <b>मुख्य दिशा संकेत बल:</b> {_ne(p_dir['percentage'])}% (<b>{p_name}</b>)<br/>"
        f"• <b>सहायक दिशा संकेत:</b> {_ne(s_dir['percentage'])}% (<b>{s_name}</b>)<br/>"
        f"• <b>दिशा विश्वसनीयता / स्थिति:</b> {confidence_label}<br/><br/>"
        f"<b>शास्त्रीय तथा गणितीय नियमहरूबाट प्राप्त प्रमाण (Rule Evidence):</b><br/>"
        f"<ul>{evidence_ne}</ul><br/>"
        f"<i>(नोट: सप्तमेश, सप्तम भाव, चन्द्रबाट सप्तम, D9 नवांश तथा 'सप्तमेश+शुक्र' स्पष्ट गणितीय बिन्दुको बहु-सूचक स्कोरबाट यो दिशा निर्धारण गरिएको हो।)</i>"
        if is_ne else
        f"<b>Probable Marriage Direction: {p_name}{zone_str}</b><br/>"
        f"• <b>Primary Direction Score:</b> {p_dir['percentage']}% (<b>{p_name}</b>)<br/>"
        f"• <b>Secondary Direction Score:</b> {s_dir['percentage']}% (<b>{s_name}</b>)<br/>"
        f"• <b>Confidence Level:</b> {confidence_label}<br/><br/>"
        f"<b>Astrological & Mathematical Evidence (D1–D9 Rules):</b><br/>"
        f"<ul>{evidence_en}</ul><br/>"
        f"<i>(Note: Evaluated using 7th house occupants, 7th lord planet/sign, Moon 7th, D9 Navamsha, and 7th Lord + Venus exact DMS longitude arithmetic.)</i>"
    )

    ch4 = _dasha_chapters_html(dashas, lang, is_ne)

    d9_note_ch5 = f"\n\n• <b>D-9 नवमांश पुष्टि:</b> {s6.get('confirmation_ne','')}" if s6.get("available") and is_ne else ""
    obstacles_note = f"\n• <b>बाधा तथा भंग स्थिति:</b> {s5.get('overall_status_ne','')}" if s5.get("overall_status_ne") and is_ne else ""

    ch5 = (
        f"<b>{_sign(ls, lang)} लग्न</b>को यस कुण्डलीमा सप्तमेश <b>{seven_lord}</b> को "
        f"<b>{_ord(seven_h, lang)} भाव</b>मा रहेकाले दाम्पत्य जीवन समग्रमा सुखमय र टिकाउ हुनेछ। "
        f"सम्बन्धमा सुरुवाती वर्षहरूमा अनुकूलनको समय आए तापनि दीर्घकालमा बुझाइ र आपसी सहयोगले सम्बन्ध सुदृढ बन्नेछ।{d9_note_ch5}{obstacles_note}\n\n"
        f"<i>यो विश्लेषण बृहत्पाराशर होराशास्त्रको ९-चरणे कलत्र विचार, D1, D9 र विंशोत्तरी दशाको तथ्यमा आधारित छ।</i>"
        if is_ne else
        f"For this <b>{_sign(ls, lang)} ascendant</b> chart, the seventh lord <b>{seven_lord}</b> "
        f"in the <b>{_ord(seven_h, lang)} house</b> indicates a marital life that is generally harmonious and lasting. "
        f"Even if initial years require adaptation, mutual understanding and support strengthen the bond over time.\n\n"
        f"<i>This analysis is based on BPHS 9-step Kalatra rules, D1, D9, and Vimshottari Dasha data.</i>"
    )

    remedies_list = s8.get("remedies", [])
    remedy_text_ne = "<br/>".join([f"• {r}" for r in remedies_list]) if remedies_list else ""

    ashtakoot_guidance = (
        f"<br/><br/><b>कुण्डली मेलापक (अष्टकूट गुण मिलान) शास्त्रीय मार्गदर्शन:</b><br/>"
        f"बृहत्पाराशर होराशास्त्र अनुसार विवाह पूर्व वर-वधु दुवैको कुण्डलीमा ३६ गुणमध्ये कम्तीमा १८ गुण मिलेको हुनुपर्दछ। "
        f"विशेषतः नाडी दोष र मङ्गल दोषको समुचित साम्य वा परिहार गरी विवाह गर्दा दाम्पत्य जीवन दीर्घायु र सुखमय रहन्छ।"
        if is_ne else
        "<br/><br/><b>Kundali Matching (Ashtakoot Guna Milan) Classical Guidance:</b><br/>"
        "According to BPHS, at least 18 out of 36 Gunas must match between prospective partners, with careful cancellation of Nadi and Mangal Dosha."
    )

    ch6 = (
        f"दाम्पत्य जीवन सुखमय बनाउन तथा विवाह-सम्बन्धी बाधा हटाउन शास्त्रीय उपायहरू:<br/><br/>"
        f"{remedy_text_ne}{ashtakoot_guidance}"
        if is_ne else
        f"To enhance marital happiness and remove obstacles:\n\n"
        f"<b>1. Venus worship:</b> Chanting Venus mantra on Fridays and donating white items.\n"
        f"<b>2. Seventh lord {seven_lord} pacification:</b> Its mantra and related charity remove marriage obstacles.\n"
        f"<b>3. Jupiter's blessings:</b> Thursday Jupiter worship strengthens marriage yoga.\n"
        f"<b>4. Marital mantra:</b> Daily recitation of 'Om Uma Maheshvara' or Gayatri Mantra enhances marital joy.{ashtakoot_guidance}"
    )

    return [
        {"title": "१. विवाह योगको ज्योतिषीय आधार" if is_ne else "1. Astrological Foundation of Marriage", "content": ch1},
        {"title": "२. जीवनसाथीको स्वभाव तथा गुण" if is_ne else "2. Nature & Qualities of Life Partner", "content": ch2},
        {"title": "३. विवाहको समय र अवसर" if is_ne else "3. Marriage Timing & Opportunities", "content": ch3},
        {"title": "४. विवाह हुने सम्भावित दिशा" if is_ne else "4. Probable Marriage Direction", "content": ch_dir},
        {"title": "५. दशाअनुसार दाम्पत्य जीवनको समयक्रम" if is_ne else "5. Marital Life Timeline by Dasha", "content": ch4},
        {"title": "६. समग्र निष्कर्ष" if is_ne else "6. Overall Conclusion", "content": ch5},
        {"title": "७. उपाय तथा मार्गदर्शन" if is_ne else "7. Remedies & Guidance", "content": ch6},
    ]

