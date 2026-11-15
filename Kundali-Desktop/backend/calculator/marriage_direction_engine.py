# -*- coding: utf-8 -*-
"""Marriage Direction Engine — Classical & Mathematical Direction Determination.

Evaluates:
- D1: Planets occupying the 7th house (Weight 3)
- D2: 7th lord planetary natural direction (Weight 3)
- D3: 7th lord sign direction (Weight 2)
- D4: Mathematical formula (7th Lord Spashta + Venus Spashta) sign direction (Weight 3)
- D5: 7th sign from Moon (Chandra Lagna 7th) sign direction (Weight 1)
- D6: Venus sign direction (Weight 1)
- D7: D9 Navamsha 7th house planets (Weight 2)
- D8: D9 Navamsha 7th lord planetary direction (Weight 2)
- D9: D9 Navamsha 7th lord sign direction (Weight 1)

Follows 0-based rashi indexing: 0=Aries (0-29.999), 1=Taurus, ..., 11=Pisces.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    from .marriage_timing_engine import (
        SIGN_LORDS,
        SIGN_NAMES_EN,
        SIGN_NAMES_NE,
        add_longitudes_dms,
        format_dms_string,
    )
except ImportError:
    from marriage_timing_engine import (
        SIGN_LORDS,
        SIGN_NAMES_EN,
        SIGN_NAMES_NE,
        add_longitudes_dms,
        format_dms_string,
    )

# ── 8 Cardinal and Intercardinal Directions ──────────────────────────────────
DIRECTIONS = {
    "EAST": {"ne": "पूर्व", "en": "East", "order": 0},
    "SOUTHEAST": {"ne": "आग्नेय", "en": "Southeast", "order": 1},
    "SOUTH": {"ne": "दक्षिण", "en": "South", "order": 2},
    "SOUTHWEST": {"ne": "नैऋत्य", "en": "Southwest", "order": 3},
    "WEST": {"ne": "पश्चिम", "en": "West", "order": 4},
    "NORTHWEST": {"ne": "वायव्य", "en": "Northwest", "order": 5},
    "NORTH": {"ne": "उत्तर", "en": "North", "order": 6},
    "NORTHEAST": {"ne": "ईशान", "en": "Northeast", "order": 7},
}

# ── Planetary Direction Mapping ──────────────────────────────────────────────
# Configurable Ketu direction (default SOUTHWEST per standard Jyotish, configurable)
KETU_DIRECTION = "SOUTHWEST"

PLANET_DIRECTIONS: Dict[str, str] = {
    "Sun": "EAST",
    "Moon": "NORTHWEST",
    "Mars": "SOUTH",
    "Mercury": "NORTH",
    "Jupiter": "NORTHEAST",
    "Venus": "SOUTHEAST",
    "Saturn": "WEST",
    "Rahu": "SOUTHWEST",
    "Ketu": KETU_DIRECTION,
}

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु",
}

# ── Sign Direction Mapping (0-based rashi index: 0=Aries, 1=Taurus, ...) ─────
# 0 (Aries), 4 (Leo), 8 (Sagittarius) -> EAST
# 1 (Taurus), 5 (Virgo), 9 (Capricorn) -> SOUTH
# 2 (Gemini), 6 (Libra), 10 (Aquarius) -> WEST
# 3 (Cancer), 7 (Scorpio), 11 (Pisces) -> NORTH
SIGN_DIRECTION_MAP = {
    0: "EAST", 4: "EAST", 8: "EAST",
    1: "SOUTH", 5: "SOUTH", 9: "SOUTH",
    2: "WEST", 6: "WEST", 10: "WEST",
    3: "NORTH", 7: "NORTH", 11: "NORTH",
}

DEFAULT_RULE_WEIGHTS = {
    "D1_seventh_occupants": 3,
    "D2_seventh_lord_planet": 3,
    "D3_seventh_lord_sign": 2,
    "D4_seventh_lord_plus_venus_math": 3,
    "D5_moon_seventh_sign": 1,
    "D6_venus_sign": 1,
    "D7_d9_seventh_occupants": 2,
    "D8_d9_seventh_lord_planet": 2,
    "D9_d9_seventh_lord_sign": 1,
}


def get_sign_direction(sign_0_indexed: int) -> str:
    """Return direction key ('EAST', 'SOUTH', 'WEST', 'NORTH') for a 0-indexed sign."""
    return SIGN_DIRECTION_MAP.get(sign_0_indexed % 12, "EAST")


def get_planet_direction(planet_name: str, ketu_dir: str = KETU_DIRECTION) -> str:
    """Return direction key for a given planet."""
    if planet_name == "Ketu":
        return ketu_dir
    return PLANET_DIRECTIONS.get(planet_name, "EAST")


def calculate_marriage_direction(
    chart_data: Dict[str, Any],
    rule_weights: Optional[Dict[str, int]] = None,
    ketu_dir: str = KETU_DIRECTION
) -> Dict[str, Any]:
    """Calculate marriage direction based on the multi-rule scoring system."""
    weights = {**DEFAULT_RULE_WEIGHTS, **(rule_weights or {})}

    lagna_info = chart_data.get("lagna", {})
    lagna_sign_1 = int(lagna_info.get("sign_number", 1)) if isinstance(lagna_info, dict) else 1
    lagna_sign_0 = (lagna_sign_1 - 1) % 12
    seventh_sign_0 = (lagna_sign_0 + 6) % 12
    seventh_sign_1 = seventh_sign_0 + 1

    seventh_lord = SIGN_LORDS[seventh_sign_1]
    seventh_lord_ne = PLANET_NAMES_NE.get(seventh_lord, seventh_lord)

    planets = chart_data.get("planets", [])
    if not isinstance(planets, list):
        planets = []

    # Planet maps
    by_name: Dict[str, Dict[str, Any]] = {
        str(p.get("name")): p for p in planets if isinstance(p, dict) and p.get("name")
    }

    scores: Dict[str, int] = {d: 0 for d in DIRECTIONS}
    evidence: List[Dict[str, Any]] = []

    # ── Rule D1: 7th House Occupants (Weight: 3) ──────────────────────────────
    seventh_occupants = [
        str(p.get("name")) for p in planets
        if isinstance(p, dict) and int(p.get("house", 0) or 0) == 7 and p.get("name")
    ]
    w_d1 = weights.get("D1_seventh_occupants", 3)
    for occ in seventh_occupants:
        d = get_planet_direction(occ, ketu_dir)
        scores[d] += w_d1
        evidence.append({
            "rule_id": "D1",
            "rule_name_ne": "सप्तम भावको ग्रह",
            "rule_name_en": "7th House Occupant",
            "source": f"{PLANET_NAMES_NE.get(occ, occ)} ({occ})",
            "direction": d,
            "direction_ne": DIRECTIONS[d]["ne"],
            "direction_en": DIRECTIONS[d]["en"],
            "weight": w_d1,
        })

    # ── Rule D2: 7th Lord Planetary Direction (Weight: 3) ─────────────────────
    w_d2 = weights.get("D2_seventh_lord_planet", 3)
    d_l7_planet = get_planet_direction(seventh_lord, ketu_dir)
    scores[d_l7_planet] += w_d2
    evidence.append({
        "rule_id": "D2",
        "rule_name_ne": "सप्तमेश ग्रह-दिशा",
        "rule_name_en": "7th Lord Natural Direction",
        "source": f"{seventh_lord_ne} ({seventh_lord})",
        "direction": d_l7_planet,
        "direction_ne": DIRECTIONS[d_l7_planet]["ne"],
        "direction_en": DIRECTIONS[d_l7_planet]["en"],
        "weight": w_d2,
    })

    # ── Rule D3: 7th Lord Sign Direction (Weight: 2) ──────────────────────────
    w_d3 = weights.get("D3_seventh_lord_sign", 2)
    l7_planet_info = by_name.get(seventh_lord, {})
    l7_sign_1 = int(l7_planet_info.get("sign_number", 1)) if l7_planet_info else 1
    l7_sign_0 = (l7_sign_1 - 1) % 12
    d_l7_sign = get_sign_direction(l7_sign_0)
    scores[d_l7_sign] += w_d3
    evidence.append({
        "rule_id": "D3",
        "rule_name_ne": "सप्तमेश बसेको राशि",
        "rule_name_en": "7th Lord Sign Direction",
        "source": f"{seventh_lord_ne} in {SIGN_NAMES_NE[l7_sign_0]} ({SIGN_NAMES_EN[l7_sign_0]})",
        "direction": d_l7_sign,
        "direction_ne": DIRECTIONS[d_l7_sign]["ne"],
        "direction_en": DIRECTIONS[d_l7_sign]["en"],
        "weight": w_d3,
    })

    # ── Rule D4: 7th Lord + Venus Mathematical Spashta (Weight: 3) ────────────
    w_d4 = weights.get("D4_seventh_lord_plus_venus_math", 3)
    l7_lon = float(l7_planet_info.get("longitude", (l7_sign_0 * 30.0) + float(l7_planet_info.get("degree", 0.0))))
    venus_info = by_name.get("Venus", {})
    venus_sign_1 = int(venus_info.get("sign_number", 1)) if venus_info else 1
    venus_sign_0 = (venus_sign_1 - 1) % 12
    venus_lon = float(venus_info.get("longitude", (venus_sign_0 * 30.0) + float(venus_info.get("degree", 0.0))))

    math_deg, math_dms = add_longitudes_dms(l7_lon, venus_lon)
    math_sign_0 = math_dms[0]
    d_math = get_sign_direction(math_sign_0)
    scores[d_math] += w_d4
    math_formatted_ne = format_dms_string(math_deg, "ne")
    math_formatted_en = format_dms_string(math_deg, "en")
    evidence.append({
        "rule_id": "D4",
        "rule_name_ne": "सप्तमेश + शुक्र स्पष्ट गणित",
        "rule_name_en": "7th Lord + Venus Math Point",
        "source": f"{math_formatted_ne}",
        "direction": d_math,
        "direction_ne": DIRECTIONS[d_math]["ne"],
        "direction_en": DIRECTIONS[d_math]["en"],
        "weight": w_d4,
    })

    # ── Rule D5: Moon 7th Sign (Chandra Lagna 7th) (Weight: 1) ────────────────
    w_d5 = weights.get("D5_moon_seventh_sign", 1)
    moon_info = by_name.get("Moon", {})
    moon_sign_1 = int(moon_info.get("sign_number", 1)) if moon_info else 1
    moon_sign_0 = (moon_sign_1 - 1) % 12
    moon_7th_sign_0 = (moon_sign_0 + 6) % 12
    d_moon_7th = get_sign_direction(moon_7th_sign_0)
    scores[d_moon_7th] += w_d5
    evidence.append({
        "rule_id": "D5",
        "rule_name_ne": "चन्द्रबाट सप्तम राशि",
        "rule_name_en": "7th Sign from Moon",
        "source": f"{SIGN_NAMES_NE[moon_7th_sign_0]} ({SIGN_NAMES_EN[moon_7th_sign_0]})",
        "direction": d_moon_7th,
        "direction_ne": DIRECTIONS[d_moon_7th]["ne"],
        "direction_en": DIRECTIONS[d_moon_7th]["en"],
        "weight": w_d5,
    })

    # ── Rule D6: Venus Sign (Weight: 1) ───────────────────────────────────────
    w_d6 = weights.get("D6_venus_sign", 1)
    d_venus_sign = get_sign_direction(venus_sign_0)
    scores[d_venus_sign] += w_d6
    evidence.append({
        "rule_id": "D6",
        "rule_name_ne": "शुक्र बसेको राशि",
        "rule_name_en": "Venus Sign Direction",
        "source": f"Venus in {SIGN_NAMES_NE[venus_sign_0]} ({SIGN_NAMES_EN[venus_sign_0]})",
        "direction": d_venus_sign,
        "direction_ne": DIRECTIONS[d_venus_sign]["ne"],
        "direction_en": DIRECTIONS[d_venus_sign]["en"],
        "weight": w_d6,
    })

    # ── Rules D7, D8, D9: D9 Navamsha (Weights: 2, 2, 1) ──────────────────────
    vargas = chart_data.get("vargas", {})
    d9_data = vargas.get("D9") if isinstance(vargas, dict) else None
    if isinstance(d9_data, dict):
        d9_planets = d9_data.get("planets", [])
        if isinstance(d9_planets, list):
            d9_by_name = {
                str(p.get("name")): p for p in d9_planets if isinstance(p, dict) and p.get("name")
            }
            d9_lagna_1 = int(d9_data.get("lagna", {}).get("sign_number", 1)) if isinstance(d9_data.get("lagna"), dict) else 1
            d9_lagna_0 = (d9_lagna_1 - 1) % 12
            d9_7th_sign_0 = (d9_lagna_0 + 6) % 12
            d9_7th_sign_1 = d9_7th_sign_0 + 1
            d9_7th_lord = SIGN_LORDS[d9_7th_sign_1]
            d9_7th_lord_ne = PLANET_NAMES_NE.get(d9_7th_lord, d9_7th_lord)

            # D7: D9 7th occupants
            w_d7 = weights.get("D7_d9_seventh_occupants", 2)
            d9_7th_occupants = [
                str(p.get("name")) for p in d9_planets
                if isinstance(p, dict) and int(p.get("house", 0) or 0) == 7 and p.get("name")
            ]
            for occ in d9_7th_occupants:
                d = get_planet_direction(occ, ketu_dir)
                scores[d] += w_d7
                evidence.append({
                    "rule_id": "D7",
                    "rule_name_ne": "नवांश (D9) सप्तम भावको ग्रह",
                    "rule_name_en": "D9 7th House Occupant",
                    "source": f"{PLANET_NAMES_NE.get(occ, occ)} in D9 7th",
                    "direction": d,
                    "direction_ne": DIRECTIONS[d]["ne"],
                    "direction_en": DIRECTIONS[d]["en"],
                    "weight": w_d7,
                })

            # D8: D9 7th lord planet direction
            w_d8 = weights.get("D8_d9_seventh_lord_planet", 2)
            d_d9_l7_planet = get_planet_direction(d9_7th_lord, ketu_dir)
            scores[d_d9_l7_planet] += w_d8
            evidence.append({
                "rule_id": "D8",
                "rule_name_ne": "नवांश (D9) सप्तमेश ग्रह",
                "rule_name_en": "D9 7th Lord Natural Direction",
                "source": f"D9 7th Lord {d9_7th_lord_ne} ({d9_7th_lord})",
                "direction": d_d9_l7_planet,
                "direction_ne": DIRECTIONS[d_d9_l7_planet]["ne"],
                "direction_en": DIRECTIONS[d_d9_l7_planet]["en"],
                "weight": w_d8,
            })

            # D9: D9 7th lord sign direction
            w_d9 = weights.get("D9_d9_seventh_lord_sign", 1)
            d9_l7_planet_info = d9_by_name.get(d9_7th_lord, {})
            d9_l7_sign_1 = int(d9_l7_planet_info.get("sign_number", 1)) if d9_l7_planet_info else 1
            d9_l7_sign_0 = (d9_l7_sign_1 - 1) % 12
            d_d9_l7_sign = get_sign_direction(d9_l7_sign_0)
            scores[d_d9_l7_sign] += w_d9
            evidence.append({
                "rule_id": "D9",
                "rule_name_ne": "नवांश (D9) सप्तमेशको राशि",
                "rule_name_en": "D9 7th Lord Sign Direction",
                "source": f"D9 {d9_7th_lord_ne} in {SIGN_NAMES_NE[d9_l7_sign_0]}",
                "direction": d_d9_l7_sign,
                "direction_ne": DIRECTIONS[d_d9_l7_sign]["ne"],
                "direction_en": DIRECTIONS[d_d9_l7_sign]["en"],
                "weight": w_d9,
            })

    # ── Score Compilation & Percentage Calculation ───────────────────────────
    total_score = sum(scores.values())
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    direction_scores: Dict[str, Dict[str, Any]] = {}
    for d_key, s_val in sorted_scores:
        pct = round((s_val / total_score * 100.0), 2) if total_score > 0 else 0.0
        direction_scores[d_key] = {
            "score": s_val,
            "percentage": pct,
            "name_ne": DIRECTIONS[d_key]["ne"],
            "name_en": DIRECTIONS[d_key]["en"],
        }

    top_1_key, top_1_score = sorted_scores[0]
    top_2_key, top_2_score = sorted_scores[1]

    top_1_pct = direction_scores[top_1_key]["percentage"]
    top_2_pct = direction_scores[top_2_key]["percentage"]

    # Confidence Classification
    if top_1_pct >= 50.0:
        confidence = "Strong"
        conf_label_ne = "स्पष्ट / उच्च अनुकूल"
        conf_label_en = "Strong / Clear Indication"
    elif top_1_pct >= 35.0:
        confidence = "Moderate"
        conf_label_ne = "मध्यम / अनुकूल"
        conf_label_en = "Moderate Indication"
    else:
        confidence = "Weak"
        conf_label_ne = "मिश्रित / बहु-दिशात्मक"
        conf_label_en = "Mixed / Multi-Directional"

    # Check if primary and secondary are adjacent / diagonal
    dir_order = {
        "EAST": 0, "SOUTHEAST": 1, "SOUTH": 2, "SOUTHWEST": 3,
        "WEST": 4, "NORTHWEST": 5, "NORTH": 6, "NORTHEAST": 7
    }
    ord1 = dir_order[top_1_key]
    ord2 = dir_order[top_2_key]
    is_adjacent = abs(ord1 - ord2) in (1, 7)

    combined_zone_ne = None
    combined_zone_en = None
    if is_adjacent and top_2_pct >= 25.0:
        combined_zone_ne = f"{DIRECTIONS[top_1_key]['ne']}–{DIRECTIONS[top_2_key]['ne']} क्षेत्र"
        combined_zone_en = f"{DIRECTIONS[top_1_key]['en']}–{DIRECTIONS[top_2_key]['en']} Sector"

    # Supporting rules for primary and secondary
    supporting_primary = [e for e in evidence if e["direction"] == top_1_key]
    supporting_secondary = [e for e in evidence if e["direction"] == top_2_key]

    # Narrative generation
    p_ne = DIRECTIONS[top_1_key]["ne"]
    p_en = DIRECTIONS[top_1_key]["en"]
    s_ne = DIRECTIONS[top_2_key]["ne"]
    s_en = DIRECTIONS[top_2_key]["en"]

    zone_text_ne = f" ({combined_zone_ne})" if combined_zone_ne else ""
    zone_text_en = f" ({combined_zone_en})" if combined_zone_en else ""

    narrative_ne = (
        f"<b>विवाह हुने सम्भावित मुख्य दिशा: {p_ne}{zone_text_ne}</b><br/>"
        f"जन्मकुण्डलीको सप्तमेश, सप्तम भाव तथा नवांशका संकेतहरूमा <b>{p_ne}</b> दिशाको प्रभाव सर्वाधिक ({top_1_pct}%) देखिन्छ। "
        + (f"सहायक संकेतका रूपमा <b>{s_ne}</b> दिशा ({top_2_pct}%) समेत सक्रिय रहेको छ।" if top_2_pct > 0 else "")
    )
    narrative_en = (
        f"<b>Probable Marriage Direction: {p_en}{zone_text_en}</b><br/>"
        f"Primary astrological indicators (7th house, 7th lord, D9, and mathematical point) strongly point towards the <b>{p_en}</b> direction ({top_1_pct}%). "
        + (f"Secondary support is observed towards the <b>{s_en}</b> direction ({top_2_pct}%)." if top_2_pct > 0 else "")
    )

    return {
        "primary_direction": {
            "key": top_1_key,
            "name_ne": p_ne,
            "name_en": p_en,
            "score": top_1_score,
            "percentage": top_1_pct,
        },
        "secondary_direction": {
            "key": top_2_key,
            "name_ne": s_ne,
            "name_en": s_en,
            "score": top_2_score,
            "percentage": top_2_pct,
        },
        "combined_zone_ne": combined_zone_ne,
        "combined_zone_en": combined_zone_en,
        "confidence": confidence,
        "confidence_label_ne": conf_label_ne,
        "confidence_label_en": conf_label_en,
        "direction_scores": direction_scores,
        "total_score": total_score,
        "evidence": evidence,
        "supporting_primary": supporting_primary,
        "supporting_secondary": supporting_secondary,
        "math_formula_point": {
            "longitude": math_deg,
            "dms": math_dms,
            "sign_0": math_sign_0,
            "sign_name_ne": SIGN_NAMES_NE[math_sign_0],
            "sign_name_en": SIGN_NAMES_EN[math_sign_0],
            "direction": d_math,
            "formatted_ne": math_formatted_ne,
            "formatted_en": math_formatted_en,
        },
        "narrative_ne": narrative_ne,
        "narrative_en": narrative_en,
    }
