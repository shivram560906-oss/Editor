# -*- coding: utf-8 -*-
"""Shared helpers for narrative analysis engines."""
from __future__ import annotations
from typing import Any, Optional

SIGN_NAMES = {
    "ne": ["", "मेष", "वृष", "मिथुन", "कर्क", "सिंह", "कन्या",
           "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"],
    "en": ["", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
           "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
}
PLANET_NAMES = {
    "ne": {"Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
           "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि",
           "Rahu": "राहु", "Ketu": "केतु"},
    "en": {"Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
           "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn",
           "Rahu": "Rahu", "Ketu": "Ketu"},
}
from .constants import SIGN_LORDS

HOUSE_ORDINALS = {
    "ne": {1:"पहिलो",2:"दोस्रो",3:"तेस्रो",4:"चौथो",5:"पाँचौँ",
           6:"छैटौँ",7:"सातौँ",8:"आठौँ",9:"नवौँ",10:"दशौँ",
           11:"एघारौँ",12:"बाह्रौँ"},
    "en": {1:"first",2:"second",3:"third",4:"fourth",5:"fifth",
           6:"sixth",7:"seventh",8:"eighth",9:"ninth",10:"tenth",
           11:"eleventh",12:"twelfth"},
}
ND = str.maketrans("0123456789", "०१२३४५६७८९")

def _n(v: Any) -> Optional[int]:
    try:
        x = int(v)
        return x if 1 <= x <= 12 else None
    except (TypeError, ValueError):
        return None

def _ne(n) -> str:
    return str(n).translate(ND)

def _sign(num: Optional[int], lang: str) -> str:
    if num and 1 <= num <= 12:
        return SIGN_NAMES[lang][num]
    return "—"

def _planet(name: Optional[str], lang: str) -> str:
    if name and name in PLANET_NAMES[lang]:
        return PLANET_NAMES[lang][name]
    return str(name) if name else "—"

def _ord(house: Optional[int], lang: str) -> str:
    if house and 1 <= house <= 12:
        return HOUSE_ORDINALS[lang][house]
    return "—"

def _bs_span(start: str, end: str) -> str:
    try:
        y1, y2 = int(str(start)[:4]) + 57, int(str(end)[:4]) + 57
        return f"वि.सं. {_ne(y1)} – {_ne(y2)}"
    except Exception:
        if start and end:
            return f"{start} – {end}"
        return ""

def _occ(planets_list: list, house: int, lang: str) -> str:
    names = [_planet(p["name"], lang) for p in planets_list
             if _n(p.get("house")) == house and p.get("name")]
    return ", ".join(names) if names else ("कोही छैन" if lang == "ne" else "none")

def _house_lord_str(lagna_sign: int, house_num: int, by_name: dict, lang: str):
    sign = (lagna_sign + house_num - 2) % 12 + 1
    lord_en = SIGN_LORDS[sign]
    lord_str = _planet(lord_en, lang)
    info = by_name.get(lord_en, {})
    lord_house = _n(info.get("house"))
    lord_sign = _n(info.get("sign_number"))
    retro = bool(info.get("is_retrograde"))
    comb = bool(info.get("is_combust"))
    return lord_en, lord_str, lord_house, lord_sign, retro, comb

def _base(chart_data: dict):
    """Extract common chart fields. Returns dict."""
    vargas = chart_data.get("vargas") or {}
    vargas = vargas if isinstance(vargas, dict) else {}
    d1 = vargas.get("D1") if isinstance(vargas.get("D1"), dict) else chart_data
    lagna = d1.get("lagna") if isinstance(d1.get("lagna"), dict) else chart_data.get("lagna") or {}
    lagna_sign = _n(lagna.get("sign_number")) or 1
    planets = [p for p in (d1.get("planets") or chart_data.get("planets") or []) if isinstance(p, dict)]
    by_name = {p["name"]: p for p in planets if p.get("name")}
    dashas = [d for d in (chart_data.get("dasha") or []) if isinstance(d, dict)]
    meta = chart_data.get("metadata") or {}
    meta = meta if isinstance(meta, dict) else {}
    try:
        birth_year_bs = int(str(meta.get("birth_date", "1990"))[:4]) + 57
    except Exception:
        birth_year_bs = 2047
    return {
        "vargas": vargas, "d1": d1, "lagna_sign": lagna_sign,
        "planets": planets, "by_name": by_name, "dashas": dashas,
        "meta": meta, "birth_year_bs": birth_year_bs,
    }

def _dasha_chapters_html(dashas: list, lang: str, is_ne: bool) -> str:
    paras = []
    for d in dashas[:9]:
        lord_str = _planet(d.get("lord", ""), lang)
        bs = _bs_span(d.get("start", ""), d.get("end", ""))
        if not bs:
            continue
        active = (" <b>(हाल सक्रिय)</b>" if is_ne else " <b>(Currently Active)</b>") if d.get("is_active") else ""
        ads = [c for c in (d.get("children") or []) if isinstance(c, dict)]
        ad_notes = []
        for ad in ads[:4]:
            ad_s = _bs_span(ad.get("start", ""), ad.get("end", ""))
            al = _planet(ad.get("lord", ""), lang)
            act = (" ✓" if ad.get("is_active") else "")
            if ad_s:
                ad_notes.append(f"{al}{act} ({ad_s})")
        ad_txt = ("; ".join(ad_notes) + "।") if ad_notes else ""
        if is_ne:
            para = (f"<b>{bs} — {lord_str} महादशा{active}</b><br>"
                    f"यस अवधिमा <b>{lord_str}</b> ग्रहको कारकत्व, भाव र दृष्टि सक्रिय रहनेछ। "
                    f"जीवनको सम्बन्धित क्षेत्रमा यसको सीधा प्रभाव पर्नेछ।")
        else:
            para = (f"<b>{bs} — {lord_str} Mahadasha{active}</b><br>"
                    f"The significations, house lordship, and aspects of <b>{lord_str}</b> become active. "
                    f"Direct influence on the relevant life area is expected.")
        if ad_txt:
            para += (" अन्तर्दशाहरू: " if is_ne else " Antardashas: ") + ad_txt
        paras.append(para)
    return "<br><br>".join(paras) if paras else ("दशा तथ्याङ्क उपलब्ध छैन।" if is_ne else "Dasha data unavailable.")
