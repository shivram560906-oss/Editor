# -*- coding: utf-8 -*-
"""Native education analysis assembled from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.education_narrative_engine import generate_education_narrative
except ImportError:
    from calculator.education_narrative_engine import generate_education_narrative

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
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _planet(planets: list[dict], name: Optional[str]) -> Optional[dict]:
    return next((item for item in planets if item.get("name") == name), None) if name else None


def _placement(item: Optional[dict]) -> dict:
    if not item:
        return {"available": False}
    return {
        "available": True,
        "house": _number(item.get("house")),
        "sign": _number(item.get("sign_number")),
        "retrograde": bool(item.get("is_retrograde")),
        "combust": bool(item.get("is_combust")),
        "exaltation_state": item.get("exaltation_state"),
    }


def _occupants(planets: list[dict], house: int) -> list[str]:
    return [str(item["name"]) for item in planets if _number(item.get("house")) == house and item.get("name")]


def _dasha_summary(value: Any) -> dict:
    if not isinstance(value, list) or not value:
        return {"available": False, "mahadasha_count": 0, "antardasha_count": 0}
    periods = [period for period in value if isinstance(period, dict)]
    children = sum(len(period["children"]) for period in periods if isinstance(period.get("children"), list))
    return {"available": bool(periods), "mahadasha_count": len(periods), "antardasha_count": children}


def _vidya_yogas(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [
        yoga for yoga in value
        if isinstance(yoga, dict) and str(yoga.get("category", "")).lower() == "vidya"
    ]


def build_education_analysis_model(data: Optional[dict]) -> dict:
    """Extract education facts without reproducing browser-only aptitude rules."""
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

    houses = []
    for house in (4, 5, 9):
        sign = (lagna_sign + house - 2) % 12 + 1
        house_lord = SIGN_LORDS[sign]
        houses.append({
            "house": house,
            "sign": sign,
            "lord": house_lord,
            "lord_placement": _placement(_planet(planets, house_lord)),
            "occupants": _occupants(planets, house),
        })

    d24 = _mapping_value(data.get("vargas"), "D24")
    d24 = d24 if isinstance(d24, dict) else None
    d24_lagna = d24.get("lagna") if d24 and isinstance(d24.get("lagna"), dict) else None
    d24_lagna_sign = _number(d24_lagna.get("sign_number")) if d24_lagna else None
    d24_planets = _valid_planets(d24.get("planets")) if d24 else []
    d24_available = d24_lagna_sign is not None and bool(d24_planets)
    d24_lagna_lord = SIGN_LORDS[d24_lagna_sign] if d24_available else None

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "state": "ready",
        "metadata": {"name": metadata.get("name"), "birth_date": metadata.get("birth_date")},
        "lagna_sign": lagna_sign,
        "education_houses": houses,
        "mercury_placement": _placement(_planet(planets, "Mercury")),
        "jupiter_placement": _placement(_planet(planets, "Jupiter")),
        "moon_placement": _placement(_planet(planets, "Moon")),
        "d24_available": d24_available,
        "d24_lagna_sign": d24_lagna_sign,
        "d24_lagna_lord": d24_lagna_lord,
        "d24_lagna_lord_placement": _placement(_planet(d24_planets, d24_lagna_lord)),
        "d24_mercury_placement": _placement(_planet(d24_planets, "Mercury")),
        "d24_jupiter_placement": _placement(_planet(d24_planets, "Jupiter")),
        "d24_fourth_occupants": _occupants(d24_planets, 4),
        "d24_fifth_occupants": _occupants(d24_planets, 5),
        "vidya_yogas": _vidya_yogas(data.get("parashara_yogas")),
        "dasha": _dasha_summary(data.get("dasha")),
    }


class EducationAnalysisPage(QWidget):
    """Web-structured education report rendering paragraph-style narrative chapters."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model = build_education_analysis_model(data)
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "educationAnalysisHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "educationAnalysisState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_education_analysis_model(data)
        self._clear()
        state = self._model["state"]
        self._header.setText(self._text("शिक्षा विश्लेषण", "Education Analysis"))
        if state == "no_chart":
            self._state(self._text("शिक्षा विश्लेषणका लागि पहिले कुण्डली गणना गर्नुहोस्।", "Calculate a chart before opening education analysis."))
            return
        if state == "error":
            self._state(self._model.get("message", self._text("विश्लेषण तयार भएन।", "Analysis failed.")), True)
            return
        if state != "ready":
            self._state(self._text("आवश्यक कुण्डली तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        m = self._model
        self._header.setText(self._text(
            f"शिक्षा विश्लेषण - {self._sign(m['lagna_sign'])} लग्न\nचतुर्थ + पञ्चम + नवम भाव | बुध + गुरु + चन्द्र | D24 फलादेश",
            f"Education Analysis - {self._sign(m['lagna_sign'])} Ascendant\nFourth + Fifth + Ninth houses | Mercury + Jupiter + Moon | D24 Reading",
        ))

        chapters = generate_education_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "educationAnalysis")
        self._content_layout.addStretch(1)

