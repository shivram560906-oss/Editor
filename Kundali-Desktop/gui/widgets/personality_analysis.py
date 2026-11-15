# -*- coding: utf-8 -*-
"""Native personality analysis assembled from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.personality_narrative_engine import generate_personality_narrative
except ImportError:
    from calculator.personality_narrative_engine import generate_personality_narrative

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


def _varga_lagna_lord_placement(varga: Optional[dict], lagna_sign: Optional[int]) -> dict:
    """Locate the varga lagna lord inside that varga's planet list."""
    if not varga or lagna_sign is None:
        return {"available": False}
    lord_name = SIGN_LORDS[lagna_sign]
    planets = _valid_planets(varga.get("planets"))
    return _placement(_planet(planets, lord_name))


def build_personality_analysis_model(data: Optional[dict]) -> dict:
    """Extract personality facts without reproducing browser-only scoring rules."""
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

    d9 = _mapping_value(data.get("vargas"), "D9")
    d9 = d9 if isinstance(d9, dict) else None
    d9_lagna = d9.get("lagna") if d9 and isinstance(d9.get("lagna"), dict) else None
    d9_lagna_sign = _number(d9_lagna.get("sign_number")) if d9_lagna else None
    d9_planets = _valid_planets(d9.get("planets")) if d9 else []
    d9_available = d9_lagna_sign is not None and bool(d9_planets)
    d9_lagna_lord = SIGN_LORDS[d9_lagna_sign] if d9_available else None
    d9_moon_sign = _number(_planet(d9_planets, "Moon").get("sign_number")) if d9_available else None

    d45 = _mapping_value(data.get("vargas"), "D45")
    d45 = d45 if isinstance(d45, dict) else None
    d45_lagna = d45.get("lagna") if d45 and isinstance(d45.get("lagna"), dict) else None
    d45_lagna_sign = _number(d45_lagna.get("sign_number")) if d45_lagna else None
    d45_planets = _valid_planets(d45.get("planets")) if d45 else []
    d45_available = d45_lagna_sign is not None and bool(d45_planets)
    d45_lagna_lord = SIGN_LORDS[d45_lagna_sign] if d45_available else None

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "state": "ready",
        "metadata": {"name": metadata.get("name"), "birth_date": metadata.get("birth_date")},
        "lagna_sign": lagna_sign,
        "lagna_lord": lagna_lord,
        "lagna_lord_placement": _placement(_planet(planets, lagna_lord)),
        "moon_placement": _placement(_planet(planets, "Moon")),
        "sun_placement": _placement(_planet(planets, "Sun")),
        "lagna_occupants": _occupants(planets, 1),
        "d9_available": d9_available,
        "d9_lagna_sign": d9_lagna_sign,
        "d9_lagna_lord": d9_lagna_lord,
        "d9_lagna_lord_placement": _varga_lagna_lord_placement(d9, d9_lagna_sign),
        "d9_moon_sign": d9_moon_sign,
        "d45_available": d45_available,
        "d45_lagna_sign": d45_lagna_sign,
        "d45_lagna_lord": d45_lagna_lord,
        "d45_lagna_lord_placement": _varga_lagna_lord_placement(d45, d45_lagna_sign),
        "dasha": _dasha_summary(data.get("dasha")),
    }


class PersonalityAnalysisPage(QWidget):
    """Web-structured personality report rendering paragraph-style narrative chapters."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model = build_personality_analysis_model(data)
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "personalityAnalysisHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "personalityAnalysisState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_personality_analysis_model(data)
        self._clear()
        state = self._model["state"]
        self._header.setText(self._text("व्यक्तित्व विश्लेषण", "Personality Analysis"))
        if state == "no_chart":
            self._state(self._text("व्यक्तित्व विश्लेषणका लागि पहिले कुण्डली गणना गर्नुहोस्।", "Calculate a chart before opening personality analysis."))
            return
        if state == "error":
            self._state(self._model.get("message", self._text("विश्लेषण तयार भएन।", "Analysis failed.")), True)
            return
        if state != "ready":
            self._state(self._text("आवश्यक कुण्डली तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        m = self._model
        self._header.setText(self._text(
            f"व्यक्तित्व विश्लेषण - {self._sign(m['lagna_sign'])} लग्न\nलग्नेश {self._planet(m['lagna_lord'])} | चन्द्र (मन) + सूर्य (आत्मबल) | D9 + D45 गहिराइ",
            f"Personality Analysis - {self._sign(m['lagna_sign'])} Ascendant\nLagna lord {self._planet(m['lagna_lord'])} | Moon (mind) + Sun (self-strength) | D9 + D45 Depth",
        ))

        chapters = generate_personality_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "personalityAnalysis")
        self._content_layout.addStretch(1)
