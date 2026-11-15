# -*- coding: utf-8 -*-
"""Native foreign travel analysis assembled from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.foreign_travel_narrative_engine import generate_foreign_travel_narrative
except ImportError:
    from calculator.foreign_travel_narrative_engine import generate_foreign_travel_narrative

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


def _travel_yogas(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [
        yoga for yoga in value
        if isinstance(yoga, dict) and str(yoga.get("category", "")).lower() in ("travel", "disha", "yatra")
    ]


def build_foreign_travel_analysis_model(data: Optional[dict]) -> dict:
    """Extract foreign-travel facts without reproducing browser-only scoring rules."""
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
    for house in (3, 9, 12):
        sign = (lagna_sign + house - 2) % 12 + 1
        house_lord = SIGN_LORDS[sign]
        houses.append({
            "house": house,
            "sign": sign,
            "lord": house_lord,
            "lord_placement": _placement(_planet(planets, house_lord)),
            "occupants": _occupants(planets, house),
        })

    d9 = _mapping_value(data.get("vargas"), "D9")
    d9 = d9 if isinstance(d9, dict) else None
    d9_lagna = d9.get("lagna") if d9 and isinstance(d9.get("lagna"), dict) else None
    d9_lagna_sign = _number(d9_lagna.get("sign_number")) if d9_lagna else None
    d9_planets = _valid_planets(d9.get("planets")) if d9 else []
    d9_available = d9_lagna_sign is not None and bool(d9_planets)
    d9_ninth_sign = (d9_lagna_sign + 7) % 12 + 1 if d9_available else None

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "state": "ready",
        "metadata": {"name": metadata.get("name"), "birth_date": metadata.get("birth_date")},
        "lagna_sign": lagna_sign,
        "travel_houses": houses,
        "rahu_placement": _placement(_planet(planets, "Rahu")),
        "moon_placement": _placement(_planet(planets, "Moon")),
        "saturn_placement": _placement(_planet(planets, "Saturn")),
        "jupiter_placement": _placement(_planet(planets, "Jupiter")),
        "d9_available": d9_available,
        "d9_lagna_sign": d9_lagna_sign,
        "d9_ninth_sign": d9_ninth_sign,
        "d9_ninth_occupants": _occupants(d9_planets, 9) if d9_available else [],
        "d9_twelfth_occupants": _occupants(d9_planets, 12) if d9_available else [],
        "travel_yogas": _travel_yogas(data.get("parashara_yogas")),
        "dasha": _dasha_summary(data.get("dasha")),
    }


class ForeignTravelAnalysisPage(QWidget):
    """Web-structured foreign-travel report rendering paragraph-style narrative chapters."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model = build_foreign_travel_analysis_model(data)
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "foreignTravelAnalysisHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "foreignTravelAnalysisState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_foreign_travel_analysis_model(data)
        self._clear()
        state = self._model["state"]
        self._header.setText(self._text("विदेश यात्रा विश्लेषण", "Foreign Travel Analysis"))
        if state == "no_chart":
            self._state(self._text("विदेश यात्रा विश्लेषणका लागि पहिले कुण्डली गणना गर्नुहोस्।", "Calculate a chart before opening foreign travel analysis."))
            return
        if state == "error":
            self._state(self._model.get("message", self._text("विश्लेषण तयार भएन।", "Analysis failed.")), True)
            return
        if state != "ready":
            self._state(self._text("आवश्यक कुण्डली तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        m = self._model
        self._header.setText(self._text(
            f"विदेश यात्रा विश्लेषण - {self._sign(m['lagna_sign'])} लग्न\nतेस्रो + नवौँ + बाह्रौँ भाव | राहु + चन्द्र + शनि + गुरु | D9 फलादेश",
            f"Foreign Travel Analysis - {self._sign(m['lagna_sign'])} Ascendant\nThird + Ninth + Twelfth houses | Rahu + Moon + Saturn + Jupiter | D9 Reading",
        ))

        chapters = generate_foreign_travel_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "foreignTravelAnalysis")
        self._content_layout.addStretch(1)
