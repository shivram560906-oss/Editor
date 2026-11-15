"""Normalization helpers for bilingual Bikram Sambat date input."""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

NEPALI_DIGITS = "०१२३४५६७८९"
ENGLISH_DIGITS = "0123456789"
_TO_ENGLISH = str.maketrans(NEPALI_DIGITS, ENGLISH_DIGITS)
_TO_NEPALI = str.maketrans(ENGLISH_DIGITS, NEPALI_DIGITS)


def to_english_digits(value: object) -> str:
    """Normalize Nepali and mixed-script numerals to ASCII digits."""
    return str(value).translate(_TO_ENGLISH)


def to_nepali_digits(value: object) -> str:
    """Convert ASCII or mixed-script numerals to canonical Nepali digits."""
    return to_english_digits(value).translate(_TO_NEPALI)


def normalize_date_query(value: object) -> str:
    """Normalize Unicode, numeral script, case, and whitespace for matching."""
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = to_english_digits(text).casefold().strip()
    return re.sub(r"\s+", " ", text)


def normalize_birth_time(value: object) -> str | None:
    """Return canonical HH:MM:SS for bilingual, flexibly separated time input (including AM/PM)."""
    text = unicodedata.normalize("NFKC", to_english_digits(value)).strip()
    if not text:
        return None
    is_pm = False
    is_am = False
    upper = text.upper()
    if "PM" in upper or "P.M." in upper:
        is_pm = True
        upper = upper.replace("PM", "").replace("P.M.", "").strip()
    elif "AM" in upper or "A.M." in upper:
        is_am = True
        upper = upper.replace("AM", "").replace("A.M.", "").strip()
    
    parts = re.split(r"[\s:;]+", upper)
    if len(parts) not in (2, 3) or any(not part.isdigit() for part in parts):
        return None
    hour, minute = int(parts[0]), int(parts[1])
    second = int(parts[2]) if len(parts) == 3 else 0
    if is_pm and hour < 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return None
    return f"{hour:02d}:{minute:02d}:{second:02d}"


BS_MONTHS = (
    {"value": 1, "display": "बैशाख", "aliases": ("बैशाष", "बैशाक", "वैशाख", "baishakh", "baisakh", "baisak", "bais", "bai")},
    {"value": 2, "display": "जेठ", "aliases": ("जेष्ठ", "jestha", "jetha", "jeth", "jeshtha")},
    {"value": 3, "display": "असार", "aliases": ("अषाढ", "आषाढ", "asar", "ashadh", "ashad", "asad")},
    {"value": 4, "display": "श्रावण", "aliases": ("साउन", "श्रावन", "shrawan", "shravan", "sawan", "saun")},
    {"value": 5, "display": "भाद्र", "aliases": ("भदौ", "भादौ", "bhadra", "bhadau", "bhado")},
    {"value": 6, "display": "आश्विन", "aliases": ("असोज", "आश्वीन", "ashwin", "aswin", "asoj")},
    {"value": 7, "display": "कार्तिक", "aliases": ("कात्तिक", "कार्तीक", "kartik", "kartika", "kattik")},
    {"value": 8, "display": "मंसिर", "aliases": ("मङ्सिर", "मार्गशीर्ष", "mangsir", "mangshir", "margashir")},
    {"value": 9, "display": "पौष", "aliases": ("पुस", "पौस", "poush", "paush", "push", "pus")},
    {"value": 10, "display": "माघ", "aliases": ("magh", "magha")},
    {"value": 11, "display": "फाल्गुण", "aliases": ("फाल्गुन", "फागुन", "falgun", "phalgun", "fagun")},
    {"value": 12, "display": "चैत्र", "aliases": ("चैत", "चैतर", "chaitra", "chait", "chaitr")},
)


def month_search_terms(month: dict) -> tuple[str, ...]:
    """Return normalized numeric, canonical, and common alias terms."""
    raw_terms: Iterable[object] = (
        month["value"],
        to_nepali_digits(month["value"]),
        month["display"],
        *month.get("aliases", ()),
    )
    return tuple(dict.fromkeys(normalize_date_query(term) for term in raw_terms))


def resolve_month(value: object, allow_partial: bool = False) -> int | None:
    """Resolve a month query to 1..12, preferring exact over partial matches."""
    query = normalize_date_query(value)
    if not query:
        return None
    exact = [month["value"] for month in BS_MONTHS if query in month_search_terms(month)]
    if len(exact) == 1:
        return exact[0]
    if not allow_partial:
        return None
    partial = [
        month["value"]
        for month in BS_MONTHS
        if any(term.startswith(query) or query in term for term in month_search_terms(month))
    ]
    return partial[0] if len(partial) == 1 else None
