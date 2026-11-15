# -*- coding: utf-8 -*-
"""Native career analysis assembled from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.career_narrative_engine import generate_career_narrative
except ImportError:
    from calculator.career_narrative_engine import generate_career_narrative


SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


def _number(value: Any) -> Optional[int]:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 12 else None


def _mapping_value(mapping: Any, key: Any) -> Any:
    if not isinstance(mapping, dict):
        return None
    return mapping.get(key, mapping.get(str(key)))


def _valid_planets(value: Any) -> list[dict]:
    return [planet for planet in value if isinstance(planet, dict)] if isinstance(value, list) else []


def _occupants(planets: list[dict], house: int) -> list[str]:
    return [str(planet["name"]) for planet in planets if _number(planet.get("house")) == house and planet.get("name")]


def _active_dasha(dasha_periods: Any) -> dict:
    if not isinstance(dasha_periods, list):
        return {}
    for period in dasha_periods:
        if not isinstance(period, dict) or not period.get("is_active"):
            continue
        antardasha = next((c for c in period.get("children", []) if isinstance(c, dict) and c.get("is_active")), None)
        return {
            "lord": period.get("lord"),
            "antardasha_lord": antardasha.get("lord") if antardasha else None,
            "start": period.get("start"),
            "end": period.get("end"),
        }
    return {}


def build_career_analysis_model(data: Optional[dict]) -> dict:
    """Extract career-report facts from the shared calculation response."""
    if data is None:
        return {"state": "no_chart"}
    if not isinstance(data, dict):
        return {"state": "empty"}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"])}

    d1 = _mapping_value(data.get("vargas"), "D1")
    d1 = d1 if isinstance(d1, dict) else data
    lagna = d1.get("lagna") if isinstance(d1.get("lagna"), dict) else data.get("lagna")
    lagna_sign = _number(lagna.get("sign_number")) if isinstance(lagna, dict) else None
    planets = _valid_planets(d1.get("planets")) or _valid_planets(data.get("planets"))
    if lagna_sign is None or not planets:
        return {"state": "empty"}

    tenth_sign = (lagna_sign + 8) % 12 + 1
    tenth_lord = SIGN_LORDS[tenth_sign]
    tenth_lord_planet = next((planet for planet in planets if planet.get("name") == tenth_lord), None)

    d10 = _mapping_value(data.get("vargas"), "D10")
    d10 = d10 if isinstance(d10, dict) else None
    d10_lagna = d10.get("lagna") if d10 and isinstance(d10.get("lagna"), dict) else None
    d10_planets = _valid_planets(d10.get("planets")) if d10 else []

    jaimini = data.get("jaimini") if isinstance(data.get("jaimini"), dict) else {}
    karakas = jaimini.get("chara_karakas")
    amatyakaraka = _mapping_value(karakas, "Amatyakaraka")
    if isinstance(amatyakaraka, dict):
        amatyakaraka = amatyakaraka.get("planet") or amatyakaraka.get("name")

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "state": "ready",
        "metadata": {
            "name": metadata.get("name"),
            "birth_date": metadata.get("birth_date"),
            "calculation_version": metadata.get("calculation_version"),
        },
        "lagna_sign": lagna_sign,
        "tenth_sign": tenth_sign,
        "tenth_lord": tenth_lord,
        "tenth_lord_house": _number(tenth_lord_planet.get("house")) if tenth_lord_planet else None,
        "tenth_lord_sign": _number(tenth_lord_planet.get("sign_number")) if tenth_lord_planet else None,
        "tenth_lord_retrograde": bool(tenth_lord_planet.get("is_retrograde")) if tenth_lord_planet else None,
        "tenth_lord_combust": bool(tenth_lord_planet.get("is_combust")) if tenth_lord_planet else None,
        "tenth_occupants": _occupants(planets, 10),
        "second_occupants": _occupants(planets, 2),
        "eleventh_occupants": _occupants(planets, 11),
        "ninth_occupants": _occupants(planets, 9),
        "twelfth_occupants": _occupants(planets, 12),
        "amatyakaraka": str(amatyakaraka) if amatyakaraka else None,
        "d10_available": bool(d10 and d10_planets),
        "d10_lagna_sign": _number(d10_lagna.get("sign_number")) if d10_lagna else None,
        "d10_tenth_occupants": _occupants(d10_planets, 10),
        "active_dasha": _active_dasha(data.get("dasha")),
    }


class CareerAnalysisPage(QWidget):
    """Web-structured career report rendering paragraph-style narrative chapters."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model = build_career_analysis_model(data)
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "careerAnalysisHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "careerAnalysisState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_career_analysis_model(data)
        self._clear()
        state = self._model["state"]
        self._header.setText(self._text("बृहत्पाराशर व्यवसाय/जीविका निर्णय (करियर विश्लेषण)", "Career Analysis (Profession & Livelihood)"))
        if state == "no_chart":
            self._state(self._text("व्यवसाय/जीविका निर्णय विश्लेषणका लागि पहिले कुण्डली गणना गर्नुहोस्।", "Calculate a chart before opening career analysis."))
            return
        if state == "error":
            self._state(self._model.get("message", self._text("विश्लेषण तयार भएन।", "Analysis failed.")), True)
            return
        if state != "ready":
            self._state(self._text("आवश्यक कुण्डली तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        m = self._model
        self._header.setText(self._text(
            f"व्यवसाय/जीविका निर्णय (करियर विश्लेषण) - {self._sign(m['lagna_sign'])} लग्न | दशमेश: {self._planet(m['tenth_lord'])}\nबृहत्पाराशर ८-चरणे कर्माधिपति + D10 + जैमिनि + विंशोत्तरी फलादेश",
            f"Career Analysis (Profession & Livelihood) - {self._sign(m['lagna_sign'])} Ascendant | Tenth lord: {self._planet(m['tenth_lord'])}\nBPHS 8-Step Karma Rules + D10 + Jaimini + Vimshottari Reading",
        ))

        chapters = generate_career_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "careerAnalysis")
        self._content_layout.addStretch(1)
