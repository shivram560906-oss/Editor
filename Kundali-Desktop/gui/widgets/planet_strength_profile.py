# -*- coding: utf-8 -*-
"""Native planet strength profile assembled from authoritative chart payload fields."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui.utils.planet_colors import planet_full_name, rashi_name
from gui.widgets.analysis_document import add_state, build_plain_document, clear_document, render_narrative
try:
    from backend.calculator.planet_strength_narrative_engine import generate_planet_strength_narrative
except ImportError:
    from calculator.planet_strength_narrative_engine import generate_planet_strength_narrative

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _int(value: Any) -> Optional[int]:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 12 else None


def _mapping_value(mapping: Any, key: Any) -> Any:
    if not isinstance(mapping, dict):
        return None
    return mapping.get(key, mapping.get(str(key)))


def _shadbala_map(data: dict) -> dict:
    root = data.get("shadbala")
    planets = root.get("planets") if isinstance(root, dict) else None
    return planets if isinstance(planets, dict) else {}


def _avastha_map(data: dict) -> dict:
    root = data.get("avasthas")
    planets = root.get("planets") if isinstance(root, dict) else None
    return planets if isinstance(planets, dict) else {}


def build_planet_strength_model(data: Optional[dict]) -> dict:
    """Extract per-graha strength facts from the calculation payload only."""
    if data is None:
        return {"state": "no_chart"}
    if not isinstance(data, dict):
        return {"state": "empty"}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"])}

    shadbala_map = _shadbala_map(data)
    avastha_map = _avastha_map(data)
    if not shadbala_map:
        return {"state": "empty"}

    root = data.get("shadbala")
    ranking = root.get("ranking") if isinstance(root, dict) else None
    ranking = [str(item) for item in ranking] if isinstance(ranking, list) else None
    order = ranking if ranking else PLANETS

    by_name = {}
    planets = data.get("planets")
    if isinstance(planets, list):
        for planet in planets:
            if isinstance(planet, dict) and planet.get("name"):
                by_name[str(planet["name"])] = planet

    lagna = data.get("lagna") if isinstance(data.get("lagna"), dict) else {}
    lagna_sign = _int(lagna.get("sign_number"))

    rows = []
    for name in order:
        item = shadbala_map.get(name)
        if not isinstance(item, dict):
            continue
        planet = by_name.get(name, {})
        avastha = avastha_map.get(name) if isinstance(avastha_map.get(name), dict) else {}

        total_shashtiamsa = _number(item.get("total_shashtiamsa"))
        if total_shashtiamsa is None:
            total_rupas = _number(item.get("total_rupas"))
            total_shashtiamsa = total_rupas * 60.0 if total_rupas is not None else None
        required_rupas = _number(item.get("required_rupas"))
        total_rupas = _number(item.get("total_rupas"))
        if total_rupas is None and total_shashtiamsa is not None:
            total_rupas = total_shashtiamsa / 60.0
        is_strong = bool(item.get("is_strong"))
        if total_rupas is not None and required_rupas is not None:
            is_strong = total_rupas >= required_rupas

        components = {}
        raw_components = item.get("components")
        if isinstance(raw_components, dict):
            for key in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik"):
                comp = raw_components.get(key)
                value = _number(comp.get("rupa")) if isinstance(comp, dict) else None
                if value is not None:
                    components[key] = value

        rows.append({
            "name": name,
            "sign": _int(planet.get("sign_number")),
            "house": _int(planet.get("house")),
            "retrograde": bool(planet.get("is_retrograde")),
            "combust": bool(planet.get("is_combust")),
            "exaltation_state": planet.get("exaltation_state"),
            "nakshatra": planet.get("nakshatra_name") or planet.get("nakshatra"),
            "total_shashtiamsa": total_shashtiamsa,
            "total_rupas": total_rupas,
            "required_rupas": required_rupas,
            "is_strong": is_strong,
            "components": components,
            "bala_avastha": avastha.get("bala_avastha") if isinstance(avastha.get("bala_avastha"), dict) else None,
            "deeptadi_avastha": avastha.get("deeptadi_avastha") if isinstance(avastha.get("deeptadi_avastha"), dict) else None,
        })

    if not rows:
        return {"state": "empty"}

    return {
        "state": "ready",
        "lagna_sign": lagna_sign,
        "rows": rows,
        "strong_count": sum(1 for row in rows if row["is_strong"]),
        "weak_count": sum(1 for row in rows if not row["is_strong"]),
    }


class PlanetStrengthProfilePage(QWidget):
    """Single-page graha strength digest (Shadbala + Avastha + placement)."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model = build_planet_strength_model(data)
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        self.refresh(data)

    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "planetStrengthHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "planetStrengthState", message, error)

    def _planet(self, name: Optional[str]) -> str:
        return planet_full_name(name, self._language) if name else self._text("उपलब्ध छैन", "Unavailable")

    def _sign(self, number: Optional[int]) -> str:
        return rashi_name(number, self._language) if number else self._text("उपलब्ध छैन", "Unavailable")

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_planet_strength_model(data)
        self._clear()
        state = self._model["state"]
        self._header.setText(self._text("ग्रह शक्ति प्रोफाइल", "Planet Strength Profile"))
        if state == "no_chart":
            self._state(self._text("ग्रह शक्ति प्रोफाइलका लागि पहिले कुण्डली गणना गर्नुहोस्।", "Calculate a chart before opening the planet strength profile."))
            return
        if state == "error":
            self._state(self._model.get("message", self._text("प्रोफाइल तयार भएन।", "Profile failed.")), True)
            return
        if state != "ready":
            self._state(self._text("आवश्यक ग्रह बल तथ्याङ्क उपलब्ध छैन।", "Required graha strength data is unavailable."))
            return

        m = self._model
        title = self._text("ग्रह शक्ति प्रोफाइल", "Planet Strength Profile")
        if m["lagna_sign"]:
            suffix = " लग्न" if self._is_ne else " Lagna"
            header = f"{title} - {self._sign(m['lagna_sign'])}{suffix}"
        else:
            header = title
        self._header.setText(header)

        chapters = generate_planet_strength_narrative(data, self._language)
        render_narrative(self._content_layout, chapters, "planetStrength")
        self._content_layout.addStretch(1)
