# -*- coding: utf-8 -*-
"""Planet Strength Profile Narrative Engine.

Builds paragraph-style chapters that explain the relative strength of the
seven main grahas using only the authoritative backend payload: Shadbala,
Avasthas and the D1 placement facts.  No new astrology formulas are invented.
"""
from __future__ import annotations
from typing import Any, Optional

try:
    from backend.calculator.narrative_shared import _ne, _planet, _sign, _ord
except ImportError:
    from calculator.narrative_shared import _ne, _planet, _sign, _ord

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

COMPONENT_NE = {
    "sthana": "स्थान बल",
    "dig": "दिग् बल",
    "kala": "काल बल",
    "cheshta": "चेष्टा बल",
    "naisargika": "नैसर्गिक बल",
    "drik": "दृक् बल",
}
COMPONENT_EN = {
    "sthana": "Sthana Bala",
    "dig": "Dig Bala",
    "kala": "Kala Bala",
    "cheshta": "Cheshta Bala",
    "naisargika": "Naisargika Bala",
    "drik": "Drik Bala",
}

EXALTATION_NE = {
    "exalted": "उच्च",
    "debilitated": "नीच",
    "own": "स्वग्रही",
    "friend": "मित्र राशि",
    "neutral": "सम राशि",
    "enemy": "शत्रु राशि",
}
EXALTATION_EN = {
    "exalted": "exalted",
    "debilitated": "debilitated",
    "own": "own sign",
    "friend": "friendly sign",
    "neutral": "neutral sign",
    "enemy": "enemy sign",
}


def _n(value: Any) -> Optional[int]:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 12 else None


def _float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _shadbala_root(data: dict) -> dict:
    root = data.get("shadbala")
    planets = root.get("planets") if isinstance(root, dict) else None
    return planets if isinstance(planets, dict) else {}


def _avastha_root(data: dict) -> dict:
    root = data.get("avasthas")
    planets = root.get("planets") if isinstance(root, dict) else None
    return planets if isinstance(planets, dict) else {}


def _name(value: Any, lang: str = "ne") -> str:
    if isinstance(value, dict):
        if lang == "ne":
            return str(value.get("nepali") or value.get("state") or value.get("name") or "")
        return str(value.get("state") or value.get("name") or value.get("nepali") or "")
    return str(value or "")


def _status_text(item: dict, lang: str) -> str:
    """Build a compact dignity / avastha summary line for one graha."""
    parts = []
    exalt = str(item.get("exaltation_state") or "").lower()
    if exalt:
        table = EXALTATION_NE if lang == "ne" else EXALTATION_EN
        parts.append(table.get(exalt, exalt))
    if item.get("is_retrograde"):
        parts.append("वक्री" if lang == "ne" else "retrograde")
    if item.get("is_combust"):
        parts.append("अस्त" if lang == "ne" else "combust")
    if item.get("vargottama"):
        parts.append("वर्गोत्तम" if lang == "ne" else "vargottama")
    return ", ".join(parts) if parts else ("सामान्य" if lang == "ne" else "neutral")


def _strength_verdict(item: dict, lang: str) -> str:
    rupas = _float(item.get("total_rupas"))
    required = _float(item.get("required_rupas"))
    if rupas is None or required is None:
        return ""
    diff = rupas - required
    if diff >= 0:
        return (
            f"({_ne(round(rupas, 2))} रूपा — आवश्यक {_ne(round(required, 2))} रूपाभन्दा बलियो)"
            if lang == "ne"
            else f"({round(rupas, 2)} rupas — above the required {round(required, 2)} rupas)"
        )
    return (
        f"({_ne(round(rupas, 2))} रूपा — आवश्यक {_ne(round(required, 2))} रूपाभन्दा कमजोर)"
        if lang == "ne"
        else f"({round(rupas, 2)} rupas — below the required {round(required, 2)} rupas)"
    )


def generate_planet_strength_narrative(chart_data: Optional[dict], language: str = "ne") -> list:
    """Return a list of {'title', 'content'} chapters explaining graha strength."""
    if not chart_data or not isinstance(chart_data, dict):
        return []
    is_ne = language == "ne"
    lang = "ne" if is_ne else "en"

    shadbala_planets = _shadbala_root(chart_data)
    avastha_planets = _avastha_root(chart_data)
    if not shadbala_planets:
        return []

    # Order the seven grahas by payload ranking when present, else fixed order.
    root = chart_data.get("shadbala")
    ranking = root.get("ranking") if isinstance(root, dict) else None
    ranking = [str(item) for item in ranking] if isinstance(ranking, list) else None
    order = ranking if ranking else PLANETS

    rows = []
    for name in order:
        if name not in shadbala_planets:
            continue
        item = shadbala_planets[name]
        planet_data = {}
        for p in (chart_data.get("planets") or []):
            if isinstance(p, dict) and p.get("name") == name:
                planet_data = p
                break
        av = avastha_planets.get(name, {})
        rows.append({
            "name": name,
            "planet": planet_data,
            "avastha": av if isinstance(av, dict) else {},
            "shadbala": item if isinstance(item, dict) else {},
        })

    if not rows:
        return []

    strong = [row for row in rows if row["shadbala"].get("is_strong")]
    weak = [row for row in rows if not row["shadbala"].get("is_strong")]
    total_rupas = {row["name"]: _float(row["shadbala"].get("total_rupas")) for row in rows}

    def _planet_line(row: dict) -> str:
        name = _planet(row["name"], lang)
        pl = row["planet"]
        sign = _sign(_n(pl.get("sign_number")), lang)
        house = _ord(_n(pl.get("house")), lang)
        text = f"<b>{name}</b>: {sign} राशि, {house} भाव" if is_ne else f"<b>{name}</b>: {sign} sign, {house} house"
        status = _status_text({**pl, "vargottama": row.get("vargottama")}, lang)
        if status:
            text += f" ({status})"
        bala = row["avastha"].get("bala_avastha")
        deeptadi = row["avastha"].get("deeptadi_avastha")
        if bala:
            text += f" — {_name(bala, lang)}"
        if deeptadi:
            text += f", {_name(deeptadi, lang)}"
        return text

    def _component_line(row: dict) -> str:
        comps = row["shadbala"].get("components") or {}
        parts = []
        for key in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik"):
            comp = comps.get(key)
            value = _float(comp.get("rupa")) if isinstance(comp, dict) else None
            if value is None:
                continue
            label = COMPONENT_NE[key] if is_ne else COMPONENT_EN[key]
            parts.append(f"{label}: {_ne(round(value, 2))}" if is_ne else f"{label}: {round(value, 2)}")
        return "; ".join(parts) if parts else ("उपलब्ध छैन" if is_ne else "unavailable")

    # ── Chapter 1: Overview ────────────────────────────────────────────────
    total_all = sum(v for v in total_rupas.values() if v is not None)
    count = len(rows)
    avg = total_all / count if count else 0.0
    strongest = rows[0]
    weakest = rows[-1] if len(rows) > 1 else rows[0]
    ch1 = (
        f"यस कुण्डलीमा {_ne(count)} ग्रहको षड्बल जाँच गर्दा कुल {_ne(round(total_all, 2))} रूपा र "
        f"औसत {_ne(round(avg, 2))} रूपा देखिन्छ। सबैभन्दा बलियो ग्रह "
        f"<b>{_planet(strongest['name'], lang)}</b> {_strength_verdict(strongest['shadbala'], lang)} हो।\n\n"
        f"सबैभन्दा कमजोर ग्रह <b>{_planet(weakest['name'], lang)}</b> "
        f"{_strength_verdict(weakest['shadbala'], lang)} छ।"
        if is_ne else
        f"This chart shows a combined Shadbala of {round(total_all, 2)} rupas across {count} grahas "
        f"(average {round(avg, 2)} rupas). The strongest graha is "
        f"<b>{_planet(strongest['name'], lang)}</b> {_strength_verdict(strongest['shadbala'], lang)}.\n\n"
        f"The weakest graha is <b>{_planet(weakest['name'], lang)}</b> "
        f"{_strength_verdict(weakest['shadbala'], lang)}."
    )

    # ── Chapter 2: Strong planets ──────────────────────────────────────────
    if strong:
        lines = [_planet_line(row) for row in strong]
        ch2 = (
            f"आवश्यक रूपाभन्दा बढी बल भएका {_ne(len(strong))} ग्रह निम्न छन्। यी ग्रहको दशा-गोचरमा "
            f"तिनका कारकत्व (भाव, राशि, दृष्टि) बलवान् भई शुभ फल दिन सक्छन्:\n\n"
            f"{'<br>'.join(lines)}"
            if is_ne else
            f"{len(strong)} grahas exceed their required rupas. Their dasha-antar and gochar periods "
            f"tend to deliver the significations of their houses and lordships effectively:\n\n"
            f"{'<br>'.join(lines)}"
        )
    else:
        ch2 = (
            "कुनै पनि ग्रह आवश्यक रूपाभन्दा बलियो देखिएन। जीवनका फलहरू बढी संयम र दशा-क्रमको "
            "अनुशासनमा प्राप्त हुने सम्भावना छ।"
            if is_ne else
            "No graha exceeds its required rupas. Results may come more gradually, governed by the "
            "discipline of the dasha sequence."
        )

    # ── Chapter 3: Weak planets ────────────────────────────────────────────
    if weak:
        lines = [_planet_line(row) for row in weak]
        ch3 = (
            f"आवश्यक रूपाभन्दा कम बल भएका {_ne(len(weak))} ग्रह निम्न छन्। यिनका अवस्था, दशा र गोचरमा "
            f"सतर्कता आवश्यक छ — उपाय, रत्न वा दानबाट बल बढाउन सकिन्छ:\n\n"
            f"{'<br>'.join(lines)}"
            if is_ne else
            f"{len(weak)} grahas fall below their required rupas. Their dasha and transit periods call for "
            f"care; remedies such as mantra, gemstone or charity may strengthen them:\n\n"
            f"{'<br>'.join(lines)}"
        )
    else:
        ch3 = (
            "सबै ग्रह आवश्यक रूपाभन्दा बलियो छन् — कुण्डलीमा ग्रह बलको राम्रो अवस्था देखिन्छ।"
            if is_ne else
            "All grahas exceed their required rupas — the chart shows a strong planetary balance."
        )

    # ── Chapter 4: Component breakdown ─────────────────────────────────────
    comp_lines = []
    for row in rows:
        name = _planet(row["name"], lang)
        comp_lines.append(f"<b>{name}</b> — {_component_line(row)}")
    ch4 = (
        f"षड्बलका छ उप-बल (स्थान, दिग्, काल, चेष्टा, नैसर्गिक, दृक्) को विवरण प्रत्येक ग्रहको लागि:\n\n"
        f"{'<br><br>'.join(comp_lines)}"
        if is_ne else
        f"The six sub-strengths (Sthana, Dig, Kala, Cheshta, Naisargika, Drik) per graha:\n\n"
        f"{'<br><br>'.join(comp_lines)}"
    )

    # ── Chapter 5: Conclusion ──────────────────────────────────────────────
    strongest_name = _planet(strongest["name"], lang)
    weakest_name = _planet(weakest["name"], lang)
    ch5 = (
        f"समग्रमा <b>{strongest_name}</b> सबैभन्दा बलवान् र <b>{weakest_name}</b> सबैभन्दा निर्बल छ। "
        f"बलवान् ग्रहका दशा-गोचर सुनिश्चित फल दिने र निर्बल ग्रहका समयमा विशेष उपाय गर्नुपर्ने निष्कर्ष निस्कन्छ।\n\n"
        f"<i>यो प्रोफाइल गणना-डेटामा आधारित तथ्य-विवरण हो; निर्णयका लागि अनुभवी ज्योतिषीको परामर्श लिनु उचित हुन्छ।</i>"
        if is_ne else
        f"In summary, <b>{strongest_name}</b> is the strongest and <b>{weakest_name}</b> the weakest graha. "
        f"Dashas and transits of the strong graha deliver dependable results, while the weak graha's periods "
        f"deserve specific remedial care.\n\n"
        f"<i>This profile is a factual digest of the calculation data; consult an experienced astrologer before decisions.</i>"
    )

    return [
        {"title": "षड्बल सिंहावलोकन" if is_ne else "Shadbala Overview", "content": ch1},
        {"title": "बलवान् ग्रहहरू" if is_ne else "Strong Grahas", "content": ch2},
        {"title": "निर्बल ग्रहहरू" if is_ne else "Weak Grahas", "content": ch3},
        {"title": "उप-बल विवरण" if is_ne else "Sub-strength Breakdown", "content": ch4},
        {"title": "निष्कर्ष" if is_ne else "Conclusion", "content": ch5},
    ]
