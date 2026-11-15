"""
gui/utils/bs_calendar.py
Bikram Sambat ↔ AD conversion utilities — ported from frontend/src/utils/julianDay.js
and backend's nepali_datetime library.

Uses nepali_datetime (already in backend requirements) for accuracy.
"""
from __future__ import annotations
import sys
import os

# Ensure backend is importable
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BACKEND = os.path.join(_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

try:
    import nepali_datetime
    _HAS_NEPALI_DT = True
except ImportError:
    _HAS_NEPALI_DT = False

import datetime

# Nepali digit map
_NE_DIGITS = ["०","१","२","३","४","५","६","७","८","९"]

# BS month names (matching frontend BS_MONTHS_NE / BS_MONTHS_EN)
BS_MONTHS_NE = ["बैशाख","जेठ","अषाढ","श्रावण","भाद्र","आश्विन",
                 "कार्तिक","मंसिर","पौष","माघ","फाल्गुन","चैत"]
BS_MONTHS_EN = ["Baisakh","Jestha","Ashadh","Shrawan","Bhadra","Ashwin",
                 "Kartik","Mangsir","Poush","Magh","Falgun","Chaitra"]


def to_nepali_digits(num) -> str:
    """Convert Arabic digits to Nepali digits."""
    return "".join(_NE_DIGITS[int(d)] if d.isdigit() else d for d in str(num))


def gregorian_to_bs(ad_year: int, ad_month: int, ad_day: int) -> dict | None:
    """
    Convert a Gregorian (AD) date to Bikram Sambat (BS).
    Returns dict with keys: year, month, day  OR  None on failure.
    """
    if _HAS_NEPALI_DT:
        try:
            ad_date = datetime.date(ad_year, ad_month, ad_day)
            bs = nepali_datetime.date.from_datetime_date(ad_date)
            return {"year": bs.year, "month": bs.month, "day": bs.day}
        except Exception:
            pass
    return None


def bs_to_gregorian(bs_year: int, bs_month: int, bs_day: int) -> datetime.date | None:
    """Convert a BS date to Gregorian date. Returns datetime.date or None."""
    if _HAS_NEPALI_DT:
        try:
            bs_date = nepali_datetime.date(bs_year, bs_month, bs_day)
            return bs_date.to_datetime_date()
        except Exception:
            pass
    return None


def format_bs_date(bs: dict, language: str = "ne") -> str:
    """Format a BS date dict as a readable string."""
    if not bs:
        return "—"
    y = bs.get("year", 0)
    m = bs.get("month", 1)
    d = bs.get("day", 1)
    if language == "ne":
        month_name = BS_MONTHS_NE[m - 1] if 1 <= m <= 12 else str(m)
        return f"{month_name} {to_nepali_digits(d)}, {to_nepali_digits(y)}"
    else:
        month_name = BS_MONTHS_EN[m - 1] if 1 <= m <= 12 else str(m)
        return f"{month_name} {d}, {y}"


def get_today_bs() -> dict | None:
    """Return today's BS date as dict {year, month, day}."""
    today = datetime.date.today()
    return gregorian_to_bs(today.year, today.month, today.day)


def bs_month_length(bs_year: int, bs_month: int) -> int | None:
    """Return the number of days in a given BS month, or None when unknown.

    Bikram Sambat months are 29, 30 or 32 days long and the lengths change
    year to year, so a fixed fallback of 30 silently shifted every date by a
    day or two.  Callers already treat ``None`` as "unavailable".
    """
    if _HAS_NEPALI_DT:
        try:
            if bs_month == 12:
                next_y, next_m = bs_year + 1, 1
            else:
                next_y, next_m = bs_year, bs_month + 1
            start = nepali_datetime.date(bs_year, bs_month, 1).to_datetime_date()
            end = nepali_datetime.date(next_y, next_m, 1).to_datetime_date()
            length = (end - start).days
            if length > 0:
                return length
        except Exception:
            pass
    return None


def format_ad_date(ad_date: datetime.date | str, language: str = "ne") -> str:
    """Format an AD date, converting to BS if language is 'ne'."""
    if isinstance(ad_date, str):
        try:
            ad_date = datetime.date.fromisoformat(ad_date)
        except Exception:
            return str(ad_date)
    if language == "ne":
        bs = gregorian_to_bs(ad_date.year, ad_date.month, ad_date.day)
        if bs:
            return format_bs_date(bs, "ne")
    return ad_date.strftime("%d %b %Y")
