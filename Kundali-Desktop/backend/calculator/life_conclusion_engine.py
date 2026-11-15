# -*- coding: utf-8 -*-
"""
backend/calculator/life_conclusion_engine.py

सम्पूर्ण जीवन निष्कर्ष (Life Conclusion / Phalita) — evidence-only engine.

════════════════════════════════════════════════════════════════════════════
मूल सिद्धान्त (Core principle)
════════════════════════════════════════════════════════════════════════════
यो इन्जिनले एक काम मात्र गर्छ — परियोजनामा **पहिले नै गणना भइसकेका** डाटाबाट
शास्त्रीय सारांश लेख्ने। यसले कुनै नयाँ ग्रह-गणना, कुनै नयाँ दशा-सूत्र र कुनै
अनुमानित मिति उत्पादन गर्दैन।

स्रोत (Evidence sources — सबै पहिले नै विद्यमान इन्जिन)
──────────────────────────────────────────────────────
  • metadata, lagna, planets, vargas, dasha, dasha_reports,
    parashara_yogas, remedies          → perform_calculations() payload
  • marriage_timing_engine              → find_marriage_windows_age_15_to_50
  • career_analysis_engine              → calculate_comprehensive_career_analysis
  • ayurdaya                            → calculate_comprehensive_ayurdaya
  • gandanta_shanti_engine              → calculate_gandanta_shanti_analysis

कठोर नियम (Hard rules)
──────────────────────
  ✗ कुनै पनि `जन्मवर्ष + स्थिर अन्तर` (जस्तै birth_year + 60) प्रयोग गरिँदैन।
  ✗ कुनै पनि "यो मिति हुन्छ" भन्ने दावा गणना नभए गर्दैन।
  ✗ डाटा नभए → अध्यायमा स्पष्ट "unavailable" अवस्था।
  ✓ हरेक अध्यायसँग `sources` र `reference` जान्छ — पाठकले आफै जाँच गर्न सक्छ।

भाषा (Language)
───────────────
सबै उत्पादन `language="ne"` / `language="en"` अनुसार हुन्छ, जुन GUI ले
सिस्टमको छानिएको भाषाबाट पठाउँछ।
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .constants import (
    PLANET_NAMES_EN,
    PLANET_NAMES_NE,
    SIGN_LORDS,
    SIGN_NAMES_EN,
    SIGN_NAMES_NE,
)

# Explicit "unavailable" marker. Never a fabricated value.
_NA = "—"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION A — Localised reference tables
# ═══════════════════════════════════════════════════════════════════════════

_HOUSE_MEANING_NE = {
    1: "शारीरिक गठन, आत्मबल, जीवनको सामान्य प्रवृत्ति",
    2: "सञ्चित धन, वाणी, कुटुम्ब",
    3: "साहस, भाइ–बहिनी, यात्रा, प्रयास",
    4: "माता, घर, भूमि, शान्ति, शिक्षाको आधार",
    5: "सन्तान, बुद्धि, पूर्वपुण्य, मन्त्र–तपस्या",
    6: "रोग, शत्रु, ऋण, सेवा र प्रतिस्पर्धा",
    7: "विवाह, जीवनसाथी, साझेदारी, मार्ग",
    8: "आयु, संकट, गूढ विद्या, पैतृक धन",
    9: "भाग्य, धर्म, पिता, उच्च शिक्षा, यात्रा",
    10: "कर्म, पेशा, मान–सम्मान, सरकारी प्रतिष्ठा",
    11: "आय, लाभ, इच्छापूर्ति, मित्र मण्डली",
    12: "व्यय, मोक्ष, विदेश, शय्या–सुख, मुक्ति",
}
_HOUSE_MEANING_EN = {
    1: "Physique, vitality, general life tendency",
    2: "Accumulated wealth, speech, family",
    3: "Courage, siblings, travel, effort",
    4: "Mother, home, land, peace, educational foundation",
    5: "Children, intellect, past merit, mantra and tapasya",
    6: "Disease, enemies, debt, service and competition",
    7: "Marriage, spouse, partnership, journey",
    8: "Longevity, crisis, occult, ancestral wealth",
    9: "Fortune, dharma, father, higher education, travel",
    10: "Career, profession, status, government authority",
    11: "Gains, wish fulfilment, friend circle",
    12: "Expenditure, moksha, foreign lands, rest, release",
}

_BODY_NE = {
    "Sun": "हृदय, आँखा, हाड, रक्तचाप",
    "Moon": "मन, पाचन, तरल, मानसिक सन्तुलन",
    "Mars": "रक्त, मांसपेशी, शल्यक्रिया, ज्वर",
    "Mercury": "नसा, छाला, श्वसन, वाणी",
    "Jupiter": "कलेजो, बोसो, मधुमेह, वृद्धि",
    "Venus": "मिर्गौला, मूत्र, प्रजनन, हार्मोन",
    "Saturn": "जोर्नी, हाड, दाँत, दीर्घकालीन रोग",
    "Rahu": "अज्ञात रोग, विषाक्तता, मानसिक भ्रम",
    "Ketu": "संक्रमण, घाउ, शल्यक्रिया, एलर्जी",
}
_BODY_EN = {
    "Sun": "heart, eyes, bones, blood pressure",
    "Moon": "mind, digestion, fluids, mental balance",
    "Mars": "blood, muscles, surgery, fever",
    "Mercury": "nerves, skin, respiration, speech",
    "Jupiter": "liver, fat, diabetes, growth",
    "Venus": "kidneys, urinary, reproductive, hormones",
    "Saturn": "joints, bones, teeth, chronic illness",
    "Rahu": "undiagnosed illness, toxicity, mental confusion",
    "Ketu": "infection, wounds, surgery, allergy",
}

_HOUSE_WORDS_NE = ["", "पहिलो", "दोस्रो", "तेस्रो", "चौथो", "पाँचौँ", "छैटौँ",
                   "सातौँ", "आठौँ", "नवौँ", "दशौँ", "एघारौँ", "बाह्रौँ"]
_HOUSE_WORDS_EN = ["", "1st", "2nd", "3rd", "4th", "5th", "6th",
                  "7th", "8th", "9th", "10th", "11th", "12th"]


# ═══════════════════════════════════════════════════════════════════════════
# SECTION B — Safe formatting helpers (never invent a value)
# ═══════════════════════════════════════════════════════════════════════════

def _ne(value: Any) -> str:
    """ASCII digits → Devanagari digits. Non-numeric text passes through."""
    return str(value).translate(str.maketrans("0123456789", "०१२३४५६७८९"))


def _num(value: Any, lang: str) -> str:
    """Render a number in the selected language; the marker when unusable."""
    if value is None or value == "":
        return _NA
    return _ne(value) if lang == "ne" else str(value)


def _n(value: Any) -> Optional[int]:
    """Return a validated 1..12 sign/house number, or None."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 12 else None


def _date(value: Any) -> str:
    """Return an ISO date string as-is, or '' when the payload has none."""
    raw = str(value or "").strip()
    return raw[:10] if len(raw) >= 10 else ""


def _planet(name: Any, lang: str) -> str:
    key = str(name) if name else ""
    if not key:
        return _NA
    if lang == "ne":
        return PLANET_NAMES_NE.get(key, key)
    return PLANET_NAMES_EN.get(key, key)


def _sign(number: Any, lang: str) -> str:
    value = _n(number)
    if value is None:
        return _NA
    return SIGN_NAMES_NE[value] if lang == "ne" else SIGN_NAMES_EN[value]


def _ord(house: Any, lang: str) -> str:
    value = _n(house)
    if value is None:
        return _NA
    return _ne(value) if lang == "ne" else str(value)


def _lord_of(lagna_sign: int, house: int) -> str:
    """Lord of a bhava, derived arithmetically from the ascendant sign."""
    return SIGN_LORDS[((lagna_sign - 1 + house - 1) % 12) + 1]


def _span(node: Any, lang: str) -> str:
    """Render a period's date span, preferring exact BS when the payload has it.

    Accepts both dasha key spellings (``start_bs``/``bs_start``) because the
    marriage timing engine emits the latter. Never invents a year: when only AD
    dates exist it shows AD only, and when neither exists it shows the marker.
    """
    if not isinstance(node, dict):
        return _NA
    bs_s = str(node.get("start_bs") or node.get("bs_start") or "")
    bs_e = str(node.get("end_bs") or node.get("bs_end") or "")
    ad_s, ad_e = _date(node.get("start") or node.get("start_date")), \
        _date(node.get("end") or node.get("end_date"))
    if bs_s or bs_e:
        bs = f"{_ne(bs_s)} – {_ne(bs_e)}" if lang == "ne" else f"{bs_s} – {bs_e}"
        if ad_s and ad_e:
            if lang == "ne":
                return f"वि.सं. {bs} (AD {ad_s} → {ad_e})"
            return f"B.S. {bs} (AD {ad_s} → {ad_e})"
        return f"वि.सं. {bs}" if lang == "ne" else f"B.S. {bs}"
    if ad_s and ad_e:
        return f"{ad_s} → {ad_e}"
    return _NA


def _clock(value: Any) -> str:
    """Panchang sunrise/sunset are dicts such as {'time': '06:56'}."""
    if isinstance(value, dict):
        value = value.get("time") or value.get("sunrise") or value.get("sunset")
    text = str(value or "").strip()
    return text or _NA


def _lines(items: Any, lang: str) -> List[str]:
    """Flatten the remedies payload's nested dicts into readable one-liners.

    The remedies engine returns dicts for mantras; printing them raw would leak
    Python repr into the document, so the known keys are rendered as text.
    """
    labels = (
        (("planet", "ग्रह"), ("beej_mantra", "बीज मन्त्र"),
         ("jap_count", "जप"), ("charity_items", "दान"))
        if lang == "ne" else
        (("planet", "Planet"), ("beej_mantra", "Beej mantra"),
         ("jap_count", "Japa"), ("charity_items", "Charity"))
    )
    lines: List[str] = []
    for item in items or []:
        if isinstance(item, str):
            lines.append(item)
        elif isinstance(item, dict):
            parts = [
                f"{label}: {item[key]}"
                for key, label in labels
                if item.get(key)
            ]
            if parts:
                lines.append(" | ".join(parts))
    return lines



def _bullets(items: List[str], lang: str) -> str:
    if not items:
        return _NA
    return "<br>• ".join(items)


def _unavailable(lang: str, topic: str) -> str:
    """Explicit unavailable sentence naming exactly which data is missing."""
    if lang == "ne":
        return f"‘{topic}’ को गणनाबाट यो विषय उपलब्ध छैन।"
    return f"This topic is unavailable: {topic} was not calculated."


def _chapter(
    chapter_id: str, title: str, body: str,
    sources: List[str], reference: str, unavailable: bool = False,
) -> dict:
    return {
        "id": chapter_id,
        "title": title,
        "body": body,
        "sources": sources,
        "reference": reference,
        "unavailable": unavailable,
    }


# ═══════════════════════════════════════════════════════════════════════════
# SECTION C — Main entry point
# ═══════════════════════════════════════════════════════════════════════════

def generate_comprehensive_life_phalita(chart_data: dict, language: str = "ne") -> dict:
    """Build the evidence-based multi-chapter life reading.

    Every chapter reads already-calculated payload fields or already-calculated
    engine output. No date, age or score is ever synthesised.
    """
    lang = language if language in ("ne", "en") else "ne"

    if not chart_data or not isinstance(chart_data, dict):
        return {
            "status": "no_chart", "state": "no_chart", "chapters": [], "metadata": {},
            "message": ("कुण्डली डाटा उपलब्ध छैन।" if lang == "ne"
                        else "Chart data is unavailable."),
            "footnote_ne": "", "footnote_en": "",
        }

    meta = chart_data.get("metadata") if isinstance(chart_data.get("metadata"), dict) else {}
    lagna = chart_data.get("lagna") if isinstance(chart_data.get("lagna"), dict) else {}
    planets = [p for p in (chart_data.get("planets") or []) if isinstance(p, dict)]
    vargas = chart_data.get("vargas") if isinstance(chart_data.get("vargas"), dict) else {}
    dashas = [d for d in (chart_data.get("dasha") or []) if isinstance(d, dict)]
    panchang = chart_data.get("panchang") if isinstance(chart_data.get("panchang"), dict) else {}

    lagna_sign = _n(lagna.get("sign_number"))
    if lagna_sign is None or not planets:
        return {
            "status": "empty", "state": "empty", "chapters": [], "metadata": {},
            "message": ("कुण्डलीको आधार तथ्य (लग्न/ग्रह) उपलब्ध छैन।" if lang == "ne"
                        else "Base chart facts (ascendant/planets) are unavailable."),
            "footnote_ne": "", "footnote_en": "",
        }

    by_name = {str(p.get("name")): p for p in planets if p.get("name")}
    lagna_lord = _lord_of(lagna_sign, 1)
    lagna_lord_house = _n(by_name.get(lagna_lord, {}).get("house"))
    chapters: List[dict] = []

    # ── Chapter 1: Calculation provenance (from metadata) ───────────────────
    def _prov(label: str, key: str) -> str:
        raw = meta.get(key)
        shown = _NA if raw in (None, "") else (_ne(raw) if lang == "ne" else str(raw))
        return f"<b>{label}:</b> {shown}"

    chapters.append(_chapter(
        "provenance",
        "१. गणना प्रमाणपत्र" if lang == "ne" else "1. Calculation Provenance",
        "<br>".join([
            _prov("अयनांश" if lang == "ne" else "Ayanamsha", "ayanamsha_type"),
            _prov("अयनांश मान" if lang == "ne" else "Ayanamsha value", "ayanamsha_value"),
            _prov("नोड प्रकार" if lang == "ne" else "Node type", "node_type"),
            _prov("भाव प्रणाली" if lang == "ne" else "House system", "house_system"),
            _prov("एफिमेरिस" if lang == "ne" else "Ephemeris", "ephemeris"),
            _prov("एफिमेरिस संस्करण" if lang == "ne" else "Ephemeris version",
                  "ephemeris_version"),
            _prov("गणना संस्करण" if lang == "ne" else "Calculation version",
                  "calculation_version"),
        ]) + (
            "<br><br>" + (
                "<i>यो पेजका सबै मिति र निष्कर्ष माथिकै सेटिङबाट गणना भएका हुन्। "
                "सेटिङ बदलिए पुनः गणना गर्नुपर्छ।</i>" if lang == "ne" else
                "<i>Every date and conclusion on this page is computed with exactly "
                "the settings above. Changing a setting requires recalculation.</i>"
            )
        ),
        ["metadata"], "Audit / provenance",
    ))

    # ── Chapter 2: Birth basis (real chart values only) ─────────────────────
    moon = by_name.get("Moon", {})
    moon_sign = _n(moon.get("sign_number"))
    nak = panchang.get("nakshatra") if isinstance(panchang.get("nakshatra"), dict) else {}
    tithi = panchang.get("tithi") if isinstance(panchang.get("tithi"), dict) else {}
    varada = panchang.get("vara") if isinstance(panchang.get("vara"), dict) else {}
    sunrise = str(panchang.get("sunrise") or "")
    sunset = str(panchang.get("sunset") or "")

    basis_bits = [
        (("<b>लग्न:</b> {0} ({1}°) | <b>लग्नेश:</b> {2}{3} | <b>चन्द्र राशि:</b> {4}")
         if lang == "ne" else
         ("<b>Ascendant:</b> {0} ({1}°) | <b>Lagna lord:</b> {2}{3} | "
          "<b>Moon sign:</b> {4}")
        ).format(
            _sign(lagna_sign, lang),
            _num(round(lagna.get("longitude_in_sign") or 0, 2), lang),
            _planet(lagna_lord, lang),
            (f" — {_ord(lagna_lord_house, lang)} भावमा" if lang == "ne"
             else f" — house {lagna_lord_house}") if lagna_lord_house else "",
            _sign(moon_sign, lang),
        ),
    ]
    basis_bits.append(
        (("<b>जन्म नक्षत्र:</b> {0} (पद {1}) | <b>नक्षत्रेश:</b> {2} | "
          "<b>तिथि:</b> {3} | <b>वार:</b> {4}") if lang == "ne" else
         ("<b>Birth nakshatra:</b> {0} (pada {1}) | <b>Nakshatra lord:</b> {2} | "
          "<b>Tithi:</b> {3} | <b>Vara:</b> {4}")
        ).format(
            (nak.get("nepali") if lang == "ne" else nak.get("name")) or _NA,
            _num(nak.get("pada"), lang),
            _planet(moon.get("nakshatra_lord"), lang),
            (tithi.get("nepali") if lang == "ne" else tithi.get("name")) or _NA,
            (varada.get("nepali") if lang == "ne" else varada.get("name")) or _NA,
        )
    )
    if sunrise or sunset:
        basis_bits.append(
            (f"<b>सूर्योदय:</b> {_clock(sunrise)} | <b>सूर्यास्त:</b> {_clock(sunset)}"
             if lang == "ne" else
             f"<b>Sunrise:</b> {_clock(sunrise)} | <b>Sunset:</b> {_clock(sunset)}")
        )
    basis_bits.append(_HOUSE_MEANING_NE[1] if lang == "ne" else _HOUSE_MEANING_EN[1])

    chapters.append(_chapter(
        "birth_basis",
        "२. जन्म आधार तथा पञ्चाङ्ग तथ्य" if lang == "ne"
        else "2. Birth Basis & Panchang Facts",
        "<br><br>".join(basis_bits),
        ["lagna", "planets", "panchang"], "D1 Rashi + Panchang",
    ))


    # ── Chapter 3: Vimshottari mahadasha timeline (real dates) ─────────────
    if dashas:
        rows: List[str] = []
        for md in dashas:
            lord = md.get("lord")
            if not lord:
                continue
            flag = (" <b>(हाल सक्रिय)</b>" if lang == "ne" else " <b>(active)</b>") \
                if md.get("is_active") else ""
            partial = (" <i>(आंशिक)</i>" if lang == "ne" else " <i>(partial)</i>") \
                if md.get("is_partial") else ""
            word = "महादशा" if lang == "ne" else "Mahadasha"
            rows.append(
                f"<b>{_planet(lord, lang)} {word}</b> — {_span(md, lang)}{flag}{partial}"
            )
        chapters.append(_chapter(
            "dasha_timeline",
            "३. विंशोत्तरी महादशा समयरेखा" if lang == "ne"
            else "3. Vimshottari Mahadasha Timeline",
            ("यी सबै मिति चन्द्रको जन्मकालिकी नक्षत्र-भेदबाट गणना भएका हुन्; "
             "कुनै अनुमानित मिति होइनन्।<br><br>" if lang == "ne" else
             "These dates are calculated from the Moon's birth-nakshatra balance; "
             "none of them is an estimate.<br><br>") + _bullets(rows, lang),
            ["dasha", "dasha_reports.vimshottari"], "BPHS Ch.46–47 (Dasha)",
        ))
    else:
        chapters.append(_chapter(
            "dasha_timeline",
            "३. विंशोत्तरी महादशा समयरेखा" if lang == "ne"
            else "3. Vimshottari Mahadasha Timeline",
            _unavailable(lang, "विंशोत्तरी दशा" if lang == "ne" else "Vimshottari dasha"),
            ["dasha"], "BPHS Ch.46–47 (Dasha)", unavailable=True,
        ))

    # ── Chapter 4: Pratyantardasha (finest calculated periods) ──────────────
    pd_rows: List[str] = []
    for md in dashas:
        for ad in (md.get("children") or []):
            if not isinstance(ad, dict):
                continue
            for pd in (ad.get("children") or []):
                if not isinstance(pd, dict):
                    continue
                flag = (" <b>✓ सक्रिय</b>" if lang == "ne" else " <b>✓ active</b>") \
                    if pd.get("is_active") else ""
                pd_rows.append(f"{_planet(pd.get('lord'), lang)} — {_span(pd, lang)}{flag}")
    if pd_rows:
        more = (f"<br><br>… (+{len(pd_rows) - 60})" if len(pd_rows) > 60 else "")
        chapters.append(_chapter(
            "pratyantardasha",
            "४. प्रत्यन्तर्दशा (सूक्ष्मतम कालखण्ड)" if lang == "ne"
            else "4. Pratyantardasha (Finest Calculated Periods)",
            ("कुनै एक घटना कहिले हुन्छ भन्ने प्रश्नको सबैभन्दा सानो गणित-आधारित "
             "कालखण्ड यही हो।<br><br>" if lang == "ne" else
             "These are the finest calculated periods for locating when a single "
             "event may occur.<br><br>") + _bullets(pd_rows[:60], lang) + more,
            ["dasha.children.children"], "BPHS Ch.61 (Pratyantar Dasha)",
        ))
    else:
        chapters.append(_chapter(
            "pratyantardasha",
            "४. प्रत्यन्तर्दशा (सूक्ष्मतम कालखण्ड)" if lang == "ne"
            else "4. Pratyantardasha (Finest Calculated Periods)",
            _unavailable(lang, "प्रत्यन्तर्दशा" if lang == "ne" else "Pratyantardasha"),
            ["dasha"], "BPHS Ch.61 (Pratyantar Dasha)", unavailable=True,
        ))


    # ── Chapter 5: Marriage windows (real transit scan, not invented) ───────
    try:
        from .marriage_timing_engine import find_marriage_windows_age_15_to_50
        windows = find_marriage_windows_age_15_to_50(chart_data, min_score=40) or []
    except Exception:
        windows = []

    if windows:
        wr: List[str] = []
        for index, win in enumerate(windows, 1):
            if lang == "ne":
                wr.append(
                    f"<b>{_ne(index)}. {_span(win, lang)}</b> — उमेर "
                    f"{_num(win.get('age_start'), lang)}–{_num(win.get('age_end'), lang)} "
                    f"वर्ष | बल {_num(win.get('score'), lang)}%"
                )
            else:
                wr.append(
                    f"<b>{index}. {_span(win, lang)}</b> — age "
                    f"{win.get('age_start', _NA)}–{win.get('age_end', _NA)} yrs | "
                    f"strength {win.get('score', _NA)}%"
                )
        chapters.append(_chapter(
            "marriage_windows",
            "५. विवाहका गणना-आधारित सम्भावित अवधि" if lang == "ne"
            else "5. Calculated Marriage Windows",
            ("तलका अवधिहरू १५–५० वर्षको उमेर सीमाभित्र प्रत्येक ४५ दिनमा "
             "सप्तमेश, गुरु र शनिको गोचर स्क्यान गरि निकालिएका हुन्। यी सम्भावित "
             "अवधि हुन्, विवाहको निश्चित मिति होइनन्।<br><br>" if lang == "ne" else
             "These windows come from a 45-day transit scan between ages 15 and 50 "
             "for the seventh lord, Jupiter and Saturn. They are probable windows, "
             "not a confirmed date.<br><br>") + _bullets(wr, lang),
            ["marriage_timing_engine.find_marriage_windows_age_15_to_50"],
            "BPHS Ch.18 (Yuvati Bhava) + Dasha–Gochar",
        ))
    else:
        chapters.append(_chapter(
            "marriage_windows",
            "५. विवाहका गणना-आधारित सम्भावित अवधि" if lang == "ne"
            else "5. Calculated Marriage Windows",
            _unavailable(lang, "विवाह समय स्क्यान" if lang == "ne"
                         else "marriage transit scan"),
            ["marriage_timing_engine"], "BPHS Ch.18", unavailable=True,
        ))

    # ── Chapter 6: Marriage conditions (chart-derived only) ────────────────
    seventh_lord = _lord_of(lagna_sign, 7)
    seventh_p = by_name.get(seventh_lord, {})
    seventh_house_no = _n(seventh_p.get("house"))
    seventh_occupants = [
        _planet(p.get("name"), lang) for p in planets if _n(p.get("house")) == 7
    ]
    mars_house = _n(by_name.get("Mars", {}).get("house"))
    d9 = vargas.get("D9") if isinstance(vargas.get("D9"), dict) else {}
    d9_lagna = _n((d9.get("lagna") or {}).get("sign_number")) if d9 else None

    if lang == "ne":
        seventh_lord_place = (f" — {_ord(seventh_house_no, lang)} भावमा"
                              if seventh_house_no else "")
        m_head = (
            f"<b>सप्तमेश:</b> {_planet(seventh_lord, lang)}{seventh_lord_place} | "
            f"<b>सप्तम भावका ग्रह:</b> {', '.join(seventh_occupants) or _NA} | "
            f"<b>नवमांश (D9) लग्न:</b> {_sign(d9_lagna, lang)}"
        )
    else:
        seventh_lord_place = (f" — house {seventh_house_no}"
                              if seventh_house_no else "")
        m_head = (
            f"<b>7th lord:</b> {_planet(seventh_lord, lang)}{seventh_lord_place} | "
            f"<b>7th-house occupants:</b> {', '.join(seventh_occupants) or _NA} | "
            f"<b>D9 Navamsha lagna:</b> {_sign(d9_lagna, lang)}"
        )

    m_bits = [m_head]
    if mars_house is not None:
        applies = mars_house in (1, 2, 4, 7, 8, 12)
        m_bits.append(
            (f"<b>मङ्गल दोष:</b> मङ्गल {_ord(mars_house, lang)} भावमा — "
             + ("शास्त्रीय दोष-स्थितिमा पर्दछ।" if applies
                else "शास्त्रीय दोष-भावहरूमा पर्दैन।")
             + " भङ्ग/शान्ति विवाह पृष्ठबाट हेर्नुहोस्।") if lang == "ne" else
            (f"<b>Mangal dosha:</b> Mars in house {mars_house} — "
             + ("classical condition applies." if applies
                else "outside the classical dosha houses.")
             + " See the marriage page for cancellation rules.")
        )
    if seventh_p.get("is_retrograde"):
        m_bits.append(
            ("<b>सप्तमेश वक्री:</b> शास्त्रीय रूपमा विवाहमा पुनर्विचारको संकेत।"
             if lang == "ne" else
             "<b>7th lord retrograde:</b> classically indicates reconsideration "
             "in marriage matters.")
        )
    seventh_spans = [_span(md, lang) for md in dashas if md.get("lord") == seventh_lord]
    seventh_spans = [s for s in seventh_spans if s != _NA]
    if seventh_spans:
        m_bits.append(
            (f"<b>सप्तमेश {_planet(seventh_lord, lang)} महादशा अवधि:</b>"
             if lang == "ne" else
             f"<b>7th lord {_planet(seventh_lord, lang)} mahadasha periods:</b>")
            + "<br>" + _bullets(seventh_spans, lang)
        )

    chapters.append(_chapter(
        "marriage_conditions",
        "६. विवाह अवस्था: सप्तम भाव र सम्बन्धित योग" if lang == "ne"
        else "6. Marriage Conditions: 7th House & Related Yogas",
        "<br><br>".join(m_bits),
        ["planets", "vargas.D9", "dasha"], "BPHS Ch.18 (Yuvati Bhava)",
    ))


    # ── Chapter 7: Career (10th house + career engine verdict) ─────────────
    ten_lord = _lord_of(lagna_sign, 10)
    ten_house_no = _n(by_name.get(ten_lord, {}).get("house"))
    ten_occupants = [_planet(p.get("name"), lang) for p in planets if _n(p.get("house")) == 10]
    d10 = vargas.get("D10") if isinstance(vargas.get("D10"), dict) else {}
    d10_lagna = _n((d10.get("lagna") or {}).get("sign_number")) if d10 else None
    sun_house = _n(by_name.get("Sun", {}).get("house"))

    if lang == "ne":
        tenth_lord_place = (f" — {_ord(ten_house_no, lang)} भावमा"
                            if ten_house_no else "")
        sun_part = ""
        if sun_house:
            digbala = " (दिग्बली)" if sun_house == 10 else ""
            sun_part = f" | <b>सूर्य:</b> {_ord(sun_house, lang)} भावमा{digbala}"
        head_line = (
            f"<b>दशम भावका ग्रह:</b> {', '.join(ten_occupants) or _NA} | "
            f"<b>दशमेश:</b> {_planet(ten_lord, lang)}{tenth_lord_place} | "
            f"<b>दशमांश (D10) लग्न:</b> {_sign(d10_lagna, lang)}{sun_part}"
        )
    else:
        tenth_lord_place = (f" — house {ten_house_no}" if ten_house_no else "")
        sun_part = ""
        if sun_house:
            digbala = " (digbala)" if sun_house == 10 else ""
            sun_part = f" | <b>Sun:</b> house {sun_house}{digbala}"
        head_line = (
            f"<b>10th-house occupants:</b> {', '.join(ten_occupants) or _NA} | "
            f"<b>10th lord:</b> {_planet(ten_lord, lang)}{tenth_lord_place} | "
            f"<b>D10 lagna:</b> {_sign(d10_lagna, lang)}{sun_part}"
        )

    c_bits = [
        head_line,
        _HOUSE_MEANING_NE[10] if lang == "ne" else _HOUSE_MEANING_EN[10],
    ]

    # Promotion windows: only the 10th lord's own mahadasha spans (real dates).
    ten_spans = [s for s in (_span(md, lang) for md in dashas
                             if md.get("lord") == ten_lord) if s != _NA]
    if ten_spans:
        promo_title = (
            f"<b>पदोन्नति/प्रतिष्ठाका प्रमुख कालखण्ड — {_planet(ten_lord, lang)} "
            "महादशा:</b><br>" if lang == "ne" else
            f"<b>Prime promotion periods — {_planet(ten_lord, lang)} mahadasha:</b><br>"
        )
        c_bits.append(promo_title + _bullets(ten_spans, lang))
    else:
        c_bits.append(_unavailable(lang, "दशमेशको दशा" if lang == "ne"
                                   else "10th lord dasha"))

    # Career engine verdict, if the engine could run.
    try:
        from .career_analysis_engine import calculate_comprehensive_career_analysis
        career = calculate_comprehensive_career_analysis(chart_data, language=lang)
    except Exception:
        career = {}
    step6 = career.get("step6_business_vs_service") if isinstance(career, dict) else None
    if isinstance(step6, dict) and step6:
        verdict_bits = [
            f"<b>{'निर्णय' if lang == 'ne' else 'Verdict'}:</b> {step6[key]}"
            for key in ("category_ne", "verdict_ne") if step6.get(key)
        ]
        if verdict_bits:
            verdict_title = (
                "<b>व्यवसाय प्रकार (गणना इन्जिनबाट):</b><br>" if lang == "ne" else
                "<b>Career type (from career engine):</b><br>"
            )
            c_bits.append(verdict_title + "<br>".join(verdict_bits))

    chapters.append(_chapter(
        "career",
        "७. व्यवसाय र पदोन्नति सम्भावना" if lang == "ne"
        else "7. Career & Promotion Windows",
        "<br><br>".join(c_bits),
        ["planets", "vargas.D10", "dasha", "career_analysis_engine"],
        "BPHS Ch.21 (Karma Bhava)",
    ))

    # ── Chapter 8: Children (5th house) ─────────────────────────────────────
    five_lord = _lord_of(lagna_sign, 5)
    five_house_no = _n(by_name.get(five_lord, {}).get("house"))
    five_occupants = [_planet(p.get("name"), lang) for p in planets if _n(p.get("house")) == 5]
    jupiter_house = _n(by_name.get("Jupiter", {}).get("house"))
    d7 = vargas.get("D7") if isinstance(vargas.get("D7"), dict) else {}
    d7_lagna = _n((d7.get("lagna") or {}).get("sign_number")) if d7 else None

    if lang == "ne":
        fifth_lord_place = (f" — {_ord(five_house_no, lang)} भावमा"
                            if five_house_no else "")
        jupiter_part = (f" | <b>गुरु:</b> {_ord(jupiter_house, lang)} भावमा"
                        if jupiter_house else "")
        k_head = (
            f"<b>पञ्चम भावका ग्रह:</b> {', '.join(five_occupants) or _NA} | "
            f"<b>पञ्चमेश:</b> {_planet(five_lord, lang)}{fifth_lord_place}"
            f"{jupiter_part} | <b>सप्तमांश (D7) लग्न:</b> {_sign(d7_lagna, lang)}"
        )
    else:
        fifth_lord_place = (f" — house {five_house_no}" if five_house_no else "")
        jupiter_part = (f" | <b>Jupiter:</b> house {jupiter_house}"
                        if jupiter_house else "")
        k_head = (
            f"<b>5th-house occupants:</b> {', '.join(five_occupants) or _NA} | "
            f"<b>5th lord:</b> {_planet(five_lord, lang)}{fifth_lord_place}"
            f"{jupiter_part} | <b>D7 lagna:</b> {_sign(d7_lagna, lang)}"
        )

    k_bits = [
        k_head,
        _HOUSE_MEANING_NE[5] if lang == "ne" else _HOUSE_MEANING_EN[5],
    ]
    five_spans = [s for s in (_span(md, lang) for md in dashas
                              if md.get("lord") == five_lord) if s != _NA]
    if five_spans:
        child_title = (
            f"<b>सन्तानसम्बन्धी कालखण्ड — {_planet(five_lord, lang)} महादशा:</b><br>"
            if lang == "ne" else
            f"<b>Child-related periods — {_planet(five_lord, lang)} mahadasha:</b><br>"
        )
        k_bits.append(child_title + _bullets(five_spans, lang))
    # Explicitly refuse to state a count — no deterministic rule supports one.
    k_bits.append(
        ("<i>सन्तान संख्याको ठ्याक्कै निर्धारण गर्ने शास्त्रीय सूत्र उपलब्ध इञ्जिनमा "
         "छैन; त्यसैले संख्या बताइएको छैन।</i>" if lang == "ne" else
         "<i>No deterministic classical rule for the exact number of children "
         "exists in the available engines, so no number is stated.</i>")
    )

    chapters.append(_chapter(
        "children",
        "८. सन्तान (पञ्चम भाव)" if lang == "ne" else "8. Children (5th House)",
        "<br><br>".join(k_bits),
        ["planets", "vargas.D7", "dasha", "child_analysis_engine"],
        "BPHS Ch.16 (Suta Bhava)",
    ))


    # ── Chapter 9: Health (6th/8th/12th) ────────────────────────────────────
    h_bits: List[str] = []
    listed = False
    for p in planets:
        if _n(p.get("house")) not in (6, 8, 12):
            continue
        name = str(p.get("name"))
        body = _BODY_NE.get(name) if lang == "ne" else _BODY_EN.get(name)
        if not body:
            continue
        listed = True
        h_bits.append(
            (f"<b>{_planet(name, lang)}</b> ({_ord(_n(p.get('house')), lang)} भाव — {body})"
             if lang == "ne" else
             f"<b>{_planet(name, lang)}</b> (house {_n(p.get('house'))} — {body})")
        )
    if listed:
        h_bits.append(
            ("<b>कारण:</b> षष्ठ, अष्टम र द्वादश भाव रोग-विकार, संकट तथा व्ययका "
             "कारक मानिन्छन्।" if lang == "ne" else
             "<b>Basis:</b> the 6th, 8th and 12th houses are the classical houses "
             "of illness, crisis and loss.")
        )
    else:
        h_bits.append(
            ("षष्ठ, अष्टम वा द्वादश भावमा कुनै ग्रह छैन।" if lang == "ne" else
             "No planet occupies the 6th, 8th or 12th house.")
        )

    six_lord = _lord_of(lagna_sign, 6)
    h_spans = [s for s in (_span(md, lang) for md in dashas
                           if md.get("lord") in (six_lord, "Saturn")) if s != _NA]
    if h_spans:
        h_bits.append(
            (f"<b>स्वास्थ्य-सावधानीका कालखण्ड (षष्ठेश {_planet(six_lord, lang)} र शनि "
             "दशा — गणित मिति):</b><br>" if lang == "ne" else
             f"<b>Health-caution periods (6th lord {_planet(six_lord, lang)} and "
             "Saturn dasha — calculated dates):</b><br>")
            + _bullets(h_spans, lang)
        )
    h_bits.append(
        ("<i>यो रोग-निदान होइन; स्वास्थ्य सम्बन्धी निर्णय चिकित्सकसँग गर्नुहोस्।</i>"
         if lang == "ne" else
         "<i>This is not a medical diagnosis; consult a physician.</i>")
    )

    chapters.append(_chapter(
        "health",
        "९. स्वास्थ्य: अङ्ग–ग्रह सम्बन्ध र सावधानी अवधि" if lang == "ne"
        else "9. Health: Body–Planet Map & Caution Periods",
        "<br><br>".join(h_bits),
        ["planets", "dasha"], "BPHS Ch.17–19 (Ari / Randhra Bhava)",
    ))


    # ── Chapter 10: Ayurdaya (longevity indication, never a death date) ─────
    try:
        from .ayurdaya import calculate_comprehensive_ayurdaya
        ayur = calculate_comprehensive_ayurdaya(chart_data, language=lang)
    except Exception:
        ayur = {}
    ay_summary = ayur.get("summary") if isinstance(ayur, dict) else None

    if isinstance(ay_summary, dict) and ay_summary.get("primary_years") is not None:
        chapters.append(_chapter(
            "longevity",
            "१०. आयुर्दाय (जीवनकाल सङ्केत)" if lang == "ne"
            else "10. Ayurdaya (Longevity Indication)",
            "<br><br>".join([
                (f"<b>प्राथमिक विधि:</b> {ay_summary.get('primary_method_ne') or _NA} | "
                 f"<b>आयु-अनुमान:</b> {_num(ay_summary.get('primary_years'), lang)} वर्ष"
                 if lang == "ne" else
                 f"<b>Primary method:</b> {ay_summary.get('primary_method_ne') or _NA} | "
                 f"<b>Estimate:</b> {ay_summary.get('primary_years')} yrs"),
                (f"<b>सन्दर्भ सीमा:</b> {_num(ay_summary.get('range_min'), lang)} – "
                 f"{_num(ay_summary.get('range_max'), lang)} वर्ष"
                 if lang == "ne" else
                 f"<b>Reference range:</b> {ay_summary.get('range_min')} – "
                 f"{ay_summary.get('range_max')} yrs"),
                ("<i>आयु-गणना शास्त्रीय उद्घोष हो। यसले मृत्युको ठ्याक्कै मिति "
                 "दिँदैन र दिँदैन।</i>" if lang == "ne" else
                 "<i>Longevity here is a classical indication. It does not and "
                 "cannot give an exact date of death.</i>"),
            ]),
            ["ayurdaya.calculate_comprehensive_ayurdaya"],
            "BPHS Ch.43–44 (Ayurdaya)",
        ))
    else:
        chapters.append(_chapter(
            "longevity",
            "१०. आयुर्दाय (जीवनकाल सङ्केत)" if lang == "ne"
            else "10. Ayurdaya (Longevity Indication)",
            _unavailable(lang, "आयुर्दाय" if lang == "ne" else "Ayurdaya"),
            ["ayurdaya"], "BPHS Ch.43–44", unavailable=True,
        ))

    # ── Chapter 11: Birth afflictions & pacification (engine) ───────────────
    try:
        from .gandanta_shanti_engine import calculate_gandanta_shanti_analysis
        gand = calculate_gandanta_shanti_analysis(chart_data, language=lang)
    except Exception:
        gand = {}

    if isinstance(gand, dict) and gand.get("state") == "success":
        g_bits: List[str] = []
        arishta = gand.get("arishta_yogas")
        if arishta:
            for item in arishta:
                if not isinstance(item, dict):
                    continue
                g_bits.append(
                    (f"<b>{item.get('name', '')}</b> — शास्त्रीय सन्दर्भ: "
                     f"{item.get('reference', _NA)}<br>• कारण: {item.get('condition', '')}")
                    if lang == "ne" else
                    (f"<b>{item.get('name', '')}</b> — reference: "
                     f"{item.get('reference', _NA)}<br>• condition: "
                     f"{item.get('condition', '')}")
                )
        else:
            g_bits.append(
                ("गणनामा कुनै गम्भीर अनिष्ट जन्मदोष फेला परेन।" if lang == "ne" else
                 "No serious birth affliction was detected by the engine.")
            )
        remedy = gand.get("remedies") if isinstance(gand.get("remedies"), dict) else {}
        if remedy.get("deity"):
            g_bits.append(
                (f"<b>शान्ति:</b> देवता {remedy.get('deity', _NA)}; "
                 f"मन्त्र {remedy.get('vedic_mantra', _NA)}; "
                 f"जप {_num(remedy.get('japa_count'), lang)}") if lang == "ne" else
                (f"<b>Pacification:</b> deity {remedy.get('deity', _NA)}; "
                 f"mantra {remedy.get('vedic_mantra', _NA)}; "
                 f"japa {remedy.get('japa_count', _NA)}")
            )
        chapters.append(_chapter(
            "birth_afflictions",
            "११. अनिष्ट जन्मदोष तथा शान्ति" if lang == "ne"
            else "11. Birth Afflictions & Pacification",
            "<br><br>".join(g_bits),
            ["gandanta_shanti_engine"], "BPHS Ch.86–97 (Shanti Adhyayas)",
        ))
    else:
        chapters.append(_chapter(
            "birth_afflictions",
            "११. अनिष्ट जन्मदोष तथा शान्ति" if lang == "ne"
            else "11. Birth Afflictions & Pacification",
            _unavailable(lang, "अनिष्ट जन्म विचार" if lang == "ne"
                         else "birth affliction check"),
            ["gandanta_shanti_engine"], "BPHS Ch.86–97", unavailable=True,
        ))


    # ── Chapter 12: Yogas (only detector output, with its own references) ───
    yogas = [y for y in (chart_data.get("parashara_yogas") or []) if isinstance(y, dict)]
    if yogas:
        y_lines: List[str] = []
        for yoga in yogas:
            name = yoga.get("nepali") if lang == "ne" else yoga.get("name")
            refs = yoga.get("references") or []
            ref_text = (" [" + ", ".join(str(r) for r in refs) + "]") if refs else ""
            severity = yoga.get("severity")
            sev_text = f" <i>({severity})</i>" if severity and lang == "en" else ""
            y_lines.append(f"<b>{name}</b>{sev_text}{ref_text}")
        chapters.append(_chapter(
            "yogas",
            "१२. योग (स्रोतसहित)" if lang == "ne" else "12. Yogas (with references)",
            ("तलका योग कुण्डलीबाट सिधै पहिचान गरिएका हुन्; ब्रह्मजिह्नुका अनुसार "
             "योगको फल निश्चित हुँदैन, सामान्य प्रवृत्ति मात्र हो।<br><br>"
             if lang == "ne" else
             "These yogas were detected directly from the chart. Per Brihat Jataka "
             "a yoga indicates a general tendency, never a certainty of outcome."
             "<br><br>") + _bullets(y_lines, lang),
            ["parashara_yogas", "yoga_diagnostics"],
            "Brihat Jataka / BPHS yoga detection",
        ))
    else:
        diagnostics = chart_data.get("yoga_diagnostics") or []
        note = (
            "<br><i>केही योग-पहिचानकर्ता त्रुटिले चलेका छन्।</i>"
            if lang == "ne" and diagnostics else
            ("<br><i>Some yoga detectors reported errors.</i>"
             if lang == "en" and diagnostics else "")
        )
        chapters.append(_chapter(
            "yogas",
            "१२. योग (स्रोतसहित)" if lang == "ne" else "12. Yogas (with references)",
            (("यस कुण्डलीमा कुनै योग पहिचान गरिएको छैन।" if lang == "ne"
              else "No yoga was detected in this chart.") + note),
            ["parashara_yogas"], "yoga detection", unavailable=True,
        ))

    # ── Chapter 13: Remedies (from the existing remedies payload) ──────────
    remedies = chart_data.get("remedies") if isinstance(chart_data.get("remedies"), dict) else {}
    r_bits: List[str] = []
    gems = remedies.get("recommended_gemstones") or []
    g_lines = []
    for gem in gems:
        if not isinstance(gem, dict):
            continue
        name = gem.get("gemstone_ne") if lang == "ne" else gem.get("gemstone_en")
        if not name:
            continue
        g_lines.append(
            f"<b>{name}</b> ({_planet(gem.get('planet'), lang)}) — {gem.get('purpose', _NA)}"
        )
    if g_lines:
        r_bits.append(
            ("<b>सुझाव गरिएका रत्न:</b><br>" if lang == "ne"
             else "<b>Recommended gemstones:</b><br>") + _bullets(g_lines, lang)
        )
    for key, label in (("mantras_and_charity", "मन्त्र र दान" if lang == "ne"
                        else "Mantras & charity"),
                       ("general_guidelines", "सामान्य मार्गदर्शन" if lang == "ne"
                        else "General guidance")):
        items = _lines(remedies.get(key), lang)
        if items:
            r_bits.append(
                f"<b>{label}:</b><br>" + _bullets(items, lang)
            )
    if r_bits:
        chapters.append(_chapter(
            "remedies",
            "१३. रत्न, मन्त्र तथा उपाय" if lang == "ne"
            else "13. Gemstones, Mantras & Remedies",
            "<br><br>".join(r_bits),
            ["remedies"], "BPHS Ch.84 (Graha Shanti)",
        ))
    else:
        chapters.append(_chapter(
            "remedies",
            "१३. रत्न, मन्त्र तथा उपाय" if lang == "ne"
            else "13. Gemstones, Mantras & Remedies",
            _unavailable(lang, "उपाय गणना" if lang == "ne" else "remedies"),
            ["remedies"], "BPHS Ch.84", unavailable=True,
        ))

    # ── Chapter 14: Coverage summary (what is and is not known) ─────────────
    ready = [c for c in chapters if not c["unavailable"]]
    missing = [c for c in chapters if c["unavailable"]]
    s_bits = [
        (f"<b>गणना भएका अध्याय:</b> {_ne(len(ready))} / {_ne(len(chapters))}"
         if lang == "ne" else
         f"<b>Chapters with calculated data:</b> {len(ready)} / {len(chapters)}")
    ]
    if missing:
        s_bits.append(
            ("<b>गणना नभएका अध्याय:</b> " if lang == "ne"
             else "<b>Chapters without data:</b> ")
            + ", ".join(c["id"] for c in missing)
        )
    s_bits.append(
        ("<i>यो पेजले कुनै अनुमानित मिति, काल्पनिक उमेर वा निश्चित भविष्यवाणी "
         "दिँदैन। जुन कुरा गणना गरिएको छैन, त्यसलाई स्पष्ट रूपमा उपलब्ध छैन "
         "भनी लेखिएको छ।</i>" if lang == "ne" else
         "<i>This page states no estimated date, invented age or certain "
         "prediction. Anything that could not be calculated is explicitly "
         "labelled unavailable.</i>")
    )
    chapters.append(_chapter(
        "coverage",
        "१४. निष्कर्ष: के गणना भयो, के भएन" if lang == "ne"
        else "14. Conclusion: What Was and Was Not Calculated",
        "<br><br>".join(s_bits),
        ["(internal coverage audit)"], "Audit",
    ))


    # ── Page header metadata (all real payload values) ─────────────────────
    active_md = next((d for d in dashas if d.get("is_active")), None)
    active_ad = None
    if active_md is not None:
        active_ad = next(
            (a for a in (active_md.get("children") or []) if a.get("is_active")), None
        )
    lat, lon = meta.get("latitude"), meta.get("longitude")

    header = {
        "name": meta.get("name") or _NA,
        "birth_date": meta.get("birth_date") or _NA,
        "birth_time": meta.get("birth_time") or _NA,
        "birth_place": (
            f"{meta.get('city', _NA)} ({_num(round(lat, 4), lang)}°, "
            f"{_num(round(lon, 4), lang)}°)"
            if meta.get("city") or lat else _NA
        ),
        "lagna": _sign(lagna_sign, lang),
        "moon_rashi": _sign(moon_sign, lang),
        "nakshatra": (nak.get("nepali") if lang == "ne" else nak.get("name")) or _NA,
        "tithi": (tithi.get("nepali") if lang == "ne" else tithi.get("name")) or _NA,
        "current_dasha": (
            f"{_planet(active_md.get('lord'), lang)} — {_span(active_md, lang)}"
            if active_md else _NA
        ),
        "current_antardasha": (
            f"{_planet(active_ad.get('lord'), lang)} — {_span(active_ad, lang)}"
            if active_ad else _NA
        ),
        "calculation_version": meta.get("calculation_version") or _NA,
        "ayanamsha": (
            f"{meta.get('ayanamsha_type', _NA)} "
            f"({_num(meta.get('ayanamsha_value'), lang)}°)"
            if meta.get("ayanamsha_type") else _NA
        ),
    }

    return {
        "status": "ready",
        "state": "ready",
        "language": lang,
        "metadata": header,
        "provenance": {
            "ayanamsha_type": meta.get("ayanamsha_type"),
            "ayanamsha_value": meta.get("ayanamsha_value"),
            "node_type": meta.get("node_type"),
            "house_system": meta.get("house_system"),
            "ephemeris": meta.get("ephemeris"),
            "ephemeris_version": meta.get("ephemeris_version"),
            "calculation_version": meta.get("calculation_version"),
            "timezone": meta.get("timezone"),
        },
        "chapters": chapters,
        "message": "",
        "footnote_ne": (
            "आधार: माथि उल्लिखित metadata अनुसार गणना भएको D1 कुण्डली, विंशोत्तरी "
            "दशा, वर्गकुण्डली तथा उपलब्ध शास्त्रीय इन्जिनका गणनाबाट। प्रत्येक "
            "अध्यायसँग स्रोत (sources) र शास्त्रीय सन्दर्भ (reference) छ।"
        ),
        "footnote_en": (
            "Basis: the D1 chart, Vimshottari dasha, divisional charts and the "
            "available classical engines, computed with the metadata above. Each "
            "chapter carries its source(s) and scripture reference."
        ),
    }


__all__ = ["generate_comprehensive_life_phalita"]
