"""
gui/utils/planet_colors.py
Planet color constants — exactly matching the React frontend's PLANET_COLORS and ASPECT_COLORS.
"""

# Primary display colors per planet (used in chart labels, tables, badges)
PLANET_COLORS = {
    "Sun":     "#f97316",   # orange-500
    "Moon":    "#94a3b8",   # slate-400
    "Mars":    "#ef4444",   # red-500
    "Mercury": "#22c55e",   # green-500
    "Jupiter": "#eab308",   # yellow-500
    "Venus":   "#ec4899",   # pink-500
    "Saturn":  "#6366f1",   # indigo-500
    "Rahu":    "#78716c",   # stone-500
    "Ketu":    "#a78bfa",   # violet-400
}

# Special aspect colors (Mars, Jupiter, Saturn have unique aspects in Parashara)
ASPECT_COLORS = {
    "Mars":    "#ff5555",
    "Saturn":  "#88aaff",
    "Jupiter": "#ffcc44",
}

# "Good" / "Bad" / "Neutral" planet classification colors (same as CSS vars)
PLANET_GOOD_COLOR    = "#22c55e"
PLANET_BAD_COLOR     = "#ef4444"
PLANET_NEUTRAL_COLOR = "#f8fafc"

# Nepali & English abbreviations — matches PLANET_ABBR in NorthIndianChart.jsx
PLANET_ABBR = {
    "ne": {
        "Sun": "सू", "Moon": "च", "Mars": "मं", "Mercury": "बु",
        "Jupiter": "गु", "Venus": "शु", "Saturn": "श", "Rahu": "रा", "Ketu": "के"
    },
    "en": {
        "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"
    },
}

# Full planet names in Nepali and English
PLANET_NAMES = {
    "ne": {
        "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल", "Mercury": "बुध",
        "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
    },
    "en": {
        "Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
        "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn", "Rahu": "Rahu", "Ketu": "Ketu"
    },
}

# Rashi (zodiac sign) names
RASHI_NAMES = {
    "ne": ["मेष","वृष","मिथुन","कर्क","सिंह","कन्या","तुला","वृश्चिक","धनु","मकर","कुम्भ","मीन"],
    "en": ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
           "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"],
}

# Nepali digit conversion
_NE_DIGITS = ["०","१","२","३","४","५","६","७","८","९"]

def to_nepali_digits(num) -> str:
    return "".join(_NE_DIGITS[int(d)] if d.isdigit() else d for d in str(num))


def planet_color(name: str) -> str:
    """Return the display hex color for a planet name."""
    return PLANET_COLORS.get(name, "#f8fafc")


def planet_abbr(name: str, language: str = "ne") -> str:
    """Return abbreviated planet name in the given language."""
    return PLANET_ABBR.get(language, PLANET_ABBR["ne"]).get(name, name[:2])


def planet_full_name(name: str, language: str = "ne") -> str:
    """Return full planet name in the given language."""
    return PLANET_NAMES.get(language, PLANET_NAMES["ne"]).get(name, name)


def rashi_name(sign_num: int, language: str = "ne") -> str:
    """Return rashi name for sign number 1..12."""
    idx = max(0, min(11, sign_num - 1))
    return RASHI_NAMES.get(language, RASHI_NAMES["ne"])[idx]
