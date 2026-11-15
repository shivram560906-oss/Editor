# -*- coding: utf-8 -*-
"""Native health analysis assembled from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.health_narrative_engine import generate_health_narrative
except ImportError:
    from calculator.health_narrative_engine import generate_health_narrative


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


def build_health_analysis_model(data: Optional[dict]) -> dict:
    """Extract health-related chart facts without deriving medical predictions."""
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

    lagna_lord = SIGN_LORDS[lagna_sign]
    health_houses = []
    for house in (6, 8, 12):
        sign = (lagna_sign + house - 2) % 12 + 1
        house_lord = SIGN_LORDS[sign]
        health_houses.append({
            "house": house,
            "sign": sign,
            "lord": house_lord,
            "lord_placement": _placement(_planet(planets, house_lord)),
            "occupants": _occupants(planets, house),
        })

    d6 = _mapping_value(data.get("vargas"), "D6")
    d6 = d6 if isinstance(d6, dict) else None
    d6_lagna = d6.get("lagna") if d6 and isinstance(d6.get("lagna"), dict) else None
    d6_lagna_sign = _number(d6_lagna.get("sign_number")) if d6_lagna else None
    d6_planets = _valid_planets(d6.get("planets")) if d6 else []
    d6_available = d6_lagna_sign is not None and bool(d6_planets)
    d6_lagna_lord = SIGN_LORDS[d6_lagna_sign] if d6_available else None

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "state": "ready",
        "metadata": {
            "name": metadata.get("name"),
            "birth_date": metadata.get("birth_date"),
            "calculation_version": metadata.get("calculation_version"),
        },
        "lagna_sign": lagna_sign,
        "lagna_lord": lagna_lord,
        "lagna_lord_placement": _placement(_planet(planets, lagna_lord)),
        "sun_placement": _placement(_planet(planets, "Sun")),
        "moon_placement": _placement(_planet(planets, "Moon")),
        "health_houses": health_houses,
        "d6_available": d6_available,
        "d6_lagna_sign": d6_lagna_sign,
        "d6_lagna_lord": d6_lagna_lord,
        "d6_lagna_lord_placement": _placement(_planet(d6_planets, d6_lagna_lord)),
        "d6_sixth_occupants": _occupants(d6_planets, 6),
        "dasha": _dasha_summary(data.get("dasha")),
    }


class HealthAnalysisPage(QWidget):
    """Web-structured health report rendering paragraph-style narrative chapters."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model = build_health_analysis_model(data)
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "healthAnalysisHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "healthAnalysisState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_health_analysis_model(data)
        self._clear()
        state = self._model["state"]
        self._header.setText(self._text("स्वास्थ्य विश्लेषण", "Health Analysis"))
        if state == "no_chart":
            self._state(self._text("स्वास्थ्य विश्लेषणका लागि पहिले कुण्डली गणना गर्नुहोस्।", "Calculate a chart before opening health analysis."))
            return
        if state == "error":
            self._state(self._model.get("message", self._text("विश्लेषण तयार भएन।", "Analysis failed.")), True)
            return
        if state != "ready":
            self._state(self._text("आवश्यक कुण्डली तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        m = self._model
        self._header.setText(self._text(
            f"स्वास्थ्य विश्लेषण - {self._sign(m['lagna_sign'])} लग्न | लग्नेश: {self._planet(m['lagna_lord'])}\nD1 + D6 + विंशोत्तरी फलादेश",
            f"Health Analysis - {self._sign(m['lagna_sign'])} Ascendant | Ascendant lord: {self._planet(m['lagna_lord'])}\nD1 + D6 + Vimshottari Reading",
        ))

        chapters = generate_health_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "healthAnalysis")
        self._content_layout.addStretch(1)
