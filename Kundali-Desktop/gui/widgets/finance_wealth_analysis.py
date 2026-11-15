# -*- coding: utf-8 -*-
"""Native finance and wealth analysis from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.finance_narrative_engine import generate_finance_narrative
except ImportError:
    from calculator.finance_narrative_engine import generate_finance_narrative

SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}
WEALTH_HOUSES = (2, 5, 9, 11)


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


def _wealth_yogas(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [yoga for yoga in value if isinstance(yoga, dict) and str(yoga.get("category", "")).lower() in {"dhana", "wealth"}]


def build_finance_wealth_model(data: Optional[dict]) -> dict:
    """Extract wealth facts without reproducing browser-only scoring rules."""
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
    for house in WEALTH_HOUSES:
        sign = (lagna_sign + house - 2) % 12 + 1
        lord = SIGN_LORDS[sign]
        houses.append({
            "house": house,
            "sign": sign,
            "lord": lord,
            "lord_placement": _placement(_planet(planets, lord)),
            "occupants": _occupants(planets, house),
        })

    d2 = _mapping_value(data.get("vargas"), "D2")
    d2 = d2 if isinstance(d2, dict) else None
    d2_lagna = d2.get("lagna") if d2 and isinstance(d2.get("lagna"), dict) else None
    d2_lagna_sign = _number(d2_lagna.get("sign_number")) if d2_lagna else None
    d2_planets = _valid_planets(d2.get("planets")) if d2 else []
    d2_available = d2_lagna_sign is not None and bool(d2_planets)
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "state": "ready",
        "metadata": {"name": metadata.get("name"), "birth_date": metadata.get("birth_date")},
        "lagna_sign": lagna_sign,
        "wealth_houses": houses,
        "d2_available": d2_available,
        "d2_lagna_sign": d2_lagna_sign,
        "d2_planet_count": len(d2_planets),
        "dhan_yogas": _wealth_yogas(data.get("parashara_yogas")),
        "dasha": _dasha_summary(data.get("dasha")),
    }


class FinanceWealthAnalysisPage(QWidget):
    """Web-structured wealth report rendering paragraph-style narrative chapters."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "financeWealthAnalysisHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "financeWealthAnalysisState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        model = build_finance_wealth_model(data)
        self._clear()
        self._header.setText(self._text("आर्थिक तथा धन विश्लेषण", "Finance & Wealth Analysis"))
        if model["state"] == "no_chart":
            self._state(self._text("आर्थिक विश्लेषणका लागि पहिले कुण्डली गणना गर्नुहोस्।", "Calculate a chart before opening finance analysis."))
            return
        if model["state"] == "error":
            self._state(model.get("message", self._text("विश्लेषण तयार भएन।", "Analysis failed.")), True)
            return
        if model["state"] != "ready":
            self._state(self._text("आवश्यक कुण्डली तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        self._header.setText(self._text(
            f"आर्थिक तथा धन विश्लेषण - {self._sign(model['lagna_sign'])} लग्न\nद्वितीय + पञ्चम + नवम + एकादश भाव | D2 | धन योग फलादेश",
            f"Finance & Wealth Analysis - {self._sign(model['lagna_sign'])} Ascendant\nSecond + Fifth + Ninth + Eleventh houses | D2 | Dhana Yogas Reading",
        ))

        chapters = generate_finance_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "financeWealthAnalysis")
        self._content_layout.addStretch(1)

