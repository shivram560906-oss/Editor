from typing import Dict

PLANET_NAMES = {
    "Sun": {"en": "Sun", "ne": "सूर्य"},
    "Moon": {"en": "Moon", "ne": "चन्द्र"},
    "Mars": {"en": "Mars", "ne": "मङ्गल"},
    "Mercury": {"en": "Mercury", "ne": "बुध"},
    "Jupiter": {"en": "Jupiter", "ne": "गुरु"},
    "Venus": {"en": "Venus", "ne": "शुक्र"},
    "Saturn": {"en": "Saturn", "ne": "शनि"},
    "Rahu": {"en": "Rahu", "ne": "राहु"},
    "Ketu": {"en": "Ketu", "ne": "केतु"}
}


def get_planet_label(name: str, language: str = "en") -> str:
    return PLANET_NAMES.get(name, {"en": name, "ne": name}).get(language, name)
