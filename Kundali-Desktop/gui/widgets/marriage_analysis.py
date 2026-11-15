# -*- coding: utf-8 -*-
"""Native marriage analysis assembled from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.marriage_narrative_engine import generate_marriage_narrative
    from backend.calculator.marriage_timing_engine import calculate_mathematical_formulas
    from backend.calculator.marriage_direction_engine import calculate_marriage_direction
except ImportError:
    from calculator.marriage_narrative_engine import generate_marriage_narrative
    from calculator.marriage_timing_engine import calculate_mathematical_formulas
    from calculator.marriage_direction_engine import calculate_marriage_direction




SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


def _sign_number(value: Any) -> Optional[int]:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 12 else None


def _house_number(value: Any) -> Optional[int]:
    return _sign_number(value)


def _planet_map(planets: list[dict]) -> dict[str, dict]:
    return {
        str(planet.get("name")): planet
        for planet in planets
        if isinstance(planet, dict) and planet.get("name")
    }


def _house_from_sign(sign: Optional[int], lagna_sign: int) -> Optional[int]:
    if sign is None:
        return None
    return (sign - lagna_sign) % 12 + 1


def _mapping_value(mapping: Any, key: Any) -> Any:
    if not isinstance(mapping, dict):
        return None
    return mapping.get(key, mapping.get(str(key)))


def _active_mangal_yoga(yogas: Any) -> tuple[Optional[bool], Optional[dict]]:
    if not isinstance(yogas, list):
        return None, None
    match = next(
        (
            yoga for yoga in yogas
            if isinstance(yoga, dict)
            and str(yoga.get("id", "")).lower() in {"mangala_dosha", "mangal_dosha"}
        ),
        None,
    )
    return match is not None, match


def build_marriage_analysis_model(data: Optional[dict]) -> dict:
    """Map the shared calculation payload to display data without new predictions."""
    if data is None:
        return {"state": "no_chart"}
    if not isinstance(data, dict):
        return {"state": "empty"}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"])}

    lagna = data.get("lagna")
    planets = data.get("planets")
    lagna_sign = _sign_number(lagna.get("sign_number")) if isinstance(lagna, dict) else None
    valid_planets = [planet for planet in planets if isinstance(planet, dict)] if isinstance(planets, list) else []
    if lagna_sign is None or not valid_planets:
        return {"state": "empty"}

    by_name = _planet_map(valid_planets)
    seventh_sign = (lagna_sign + 5) % 12 + 1
    seventh_lord = SIGN_LORDS[seventh_sign]
    seventh_lord_planet = by_name.get(seventh_lord)
    seventh_lord_house = _house_number(seventh_lord_planet.get("house")) if seventh_lord_planet else None
    seventh_occupants = [
        str(planet.get("name"))
        for planet in valid_planets
        if _house_number(planet.get("house")) == 7 and planet.get("name")
    ]

    jaimini = data.get("jaimini") if isinstance(data.get("jaimini"), dict) else {}
    chara_karakas = jaimini.get("chara_karakas")
    darakaraka = _mapping_value(chara_karakas, "Darakaraka")
    if isinstance(darakaraka, dict):
        darakaraka = darakaraka.get("planet") or darakaraka.get("name")
    darakaraka = str(darakaraka) if darakaraka else None

    arudhas = jaimini.get("arudhas")
    upapada_sign = _sign_number(_mapping_value(arudhas, "Upapada"))
    a7_sign = _sign_number(_mapping_value(arudhas, "A7"))

    kp_system = data.get("kp_system") if isinstance(data.get("kp_system"), dict) else {}
    significators = kp_system.get("significators")
    kp_houses = significators.get("houses") if isinstance(significators, dict) else None
    kp_seventh = _mapping_value(kp_houses, 7)
    kp_seventh = kp_seventh if isinstance(kp_seventh, dict) else None
    kp_cusp = kp_seventh.get("cusp") if kp_seventh else None
    kp_cusp = kp_cusp if isinstance(kp_cusp, dict) else {}

    vargas = data.get("vargas") if isinstance(data.get("vargas"), dict) else {}
    d9 = _mapping_value(vargas, "D9")
    d9_planets = d9.get("planets") if isinstance(d9, dict) else None
    d9_available = isinstance(d9_planets, list) and bool(d9_planets)
    d9_seventh = []
    if d9_available:
        d9_seventh = [
            str(planet.get("name"))
            for planet in d9_planets
            if isinstance(planet, dict)
            and _house_number(planet.get("house")) == 7
            and planet.get("name")
        ]

    mangal_present, mangal_yoga = _active_mangal_yoga(data.get("parashara_yogas"))

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    dasha_list = data.get("dasha") if isinstance(data.get("dasha"), list) else []
    antardasha_count = sum(
        len(period["children"])
        for period in dasha_list
        if isinstance(period, dict) and isinstance(period.get("children"), list)
    )
    return {
        "state": "ready",
        "metadata": {
            "name": metadata.get("name"),
            "birth_date": metadata.get("birth_date"),
            "birth_time": metadata.get("birth_time"),
            "calculation_version": metadata.get("calculation_version"),
        },
        "lagna_sign": lagna_sign,
        "seventh_sign": seventh_sign,
        "seventh_lord": seventh_lord,
        "seventh_lord_house": seventh_lord_house,
        "seventh_occupants": seventh_occupants,
        "darakaraka": darakaraka,
        "upapada_sign": upapada_sign,
        "upapada_house": _house_from_sign(upapada_sign, lagna_sign),
        "a7_sign": a7_sign,
        "a7_house": _house_from_sign(a7_sign, lagna_sign),
        "kp": {
            "available": kp_seventh is not None,
            "house_lord": kp_seventh.get("house_lord") if kp_seventh else None,
            "occupants": kp_seventh.get("occupants", []) if kp_seventh else [],
            "significators": kp_seventh.get("significators", []) if kp_seventh else [],
            "star_lord": kp_cusp.get("star_lord"),
            "sub_lord": kp_cusp.get("sub_lord"),
        },
        "d9_available": d9_available,
        "d9_seventh_occupants": d9_seventh,
        "mangal_present": mangal_present,
        "mangal_yoga": mangal_yoga,
        "mahadasha_count": len(dasha_list),
        "antardasha_count": antardasha_count,
        "timing_formulas": calculate_mathematical_formulas(data),
        "direction_result": calculate_marriage_direction(data),
    }


class MarriageAnalysisPage(QWidget):
    """Web-aligned marriage report rendering paragraph-style narrative chapters."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model = build_marriage_analysis_model(data)
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "marriageAnalysisHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "marriageAnalysisState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_marriage_analysis_model(data)
        self._clear()
        state = self._model["state"]
        if state == "no_chart":
            self._header.setText(self._text("विवाह विश्लेषण", "Marriage Analysis"))
            self._state(self._text("कृपया पहिले जन्म कुण्डली गणना गर्नुहोस्।", "Calculate a birth chart first."))
            return
        if state == "error":
            self._header.setText(self._text("विवाह विश्लेषण", "Marriage Analysis"))
            self._state(self._model.get("message", self._text("विश्लेषण गर्न सकिएन।", "Analysis failed.")), True)
            return
        if state != "ready":
            self._header.setText(self._text("विवाह विश्लेषण", "Marriage Analysis"))
            self._state(self._text("विवाह विश्लेषणका लागि आवश्यक कुण्डली तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        m = self._model
        self._header.setText(
            self._text(
                f"विवाह/कलत्र विचार (विवाह विश्लेषण) - {self._sign(m['lagna_sign'])} लग्न | सप्तमेश: {self._planet(m['seventh_lord'])}\nबृहत्पाराशर ९-चरणे कलत्र विचार + D9 + Jaimini + विंशोत्तरी फलादेश",
                f"Marriage Analysis (Kalatra Vichara) - {self._sign(m['lagna_sign'])} Ascendant | Seventh lord: {self._planet(m['seventh_lord'])}\nBPHS 9-Step Kalatra Rules + D9 + Jaimini + Vimshottari Reading",
            )
        )

        chapters = generate_marriage_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "marriageAnalysis")
        self._content_layout.addStretch(1)
