"""
backend/calculator/nepalicalendar_api.py

Client for api-nepalicalendar.leapcell.app - Primary data source for
tithi, nakshatra, festivals, and public holidays.

Endpoint: /calendar?year={bs_year}&month={bs_month}
Returns full month data in one request.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import pathlib
import requests
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# API Configuration
_API_BASE = "https://api-nepalicalendar.leapcell.app"
_MONTH_ENDPOINT = "/calendar"

# Cache Database Path
_appdata = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home())) / "ShivramJyotish"
_appdata.mkdir(parents=True, exist_ok=True)
_CACHE_DB = str((_appdata / "nepalicalendar_cache.db").resolve())

# Request timeout
_TIMEOUT = 10.0


def _init_cache_db():
    """Initialize SQLite cache database."""
    try:
        import sqlite3
        with sqlite3.connect(_CACHE_DB) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS month_cache (
                    cache_key TEXT PRIMARY KEY,
                    bs_year INTEGER,
                    bs_month INTEGER,
                    raw_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
    except Exception:
        pass


_init_cache_db()


def _cache_key(bs_year: int, bs_month: int) -> str:
    return f"{bs_year}-{bs_month:02d}"


def get_cached_month(bs_year: int, bs_month: int) -> Optional[Dict[str, Any]]:
    """Retrieve cached month data from SQLite."""
    try:
        import sqlite3
        with sqlite3.connect(_CACHE_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT raw_json FROM month_cache WHERE cache_key = ?", (_cache_key(bs_year, bs_month),))
            row = cur.fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return None


def save_to_cache(bs_year: int, bs_month: int, data: Dict[str, Any]):
    """Persist month data to local SQLite cache."""
    try:
        import sqlite3
        with sqlite3.connect(_CACHE_DB) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO month_cache (cache_key, bs_year, bs_month, raw_json) VALUES (?, ?, ?, ?)",
                (_cache_key(bs_year, bs_month), bs_year, bs_month, json.dumps(data, ensure_ascii=False)),
            )
            conn.commit()
    except Exception:
        pass


def fetch_month_from_api(bs_year: int, bs_month: int) -> Optional[Dict[str, Any]]:
    """
    Fetch full month data from api-nepalicalendar.leapcell.app.
    
    Expected endpoint: GET /calendar?year={bs_year}&month={bs_month}
    
    Expected response format:
    {
        "year": 2083,
        "month": 6,
        "month_name": "आषाढ",
        "days": [
            {
                "bs_day": 1,
                "ad_date": "2026-06-15",
                "tithi": "प्रतिपदा",
                "tithi_en": "Pratipada",
                "nakshatra": "मृगशिरा",
                "nakshatra_en": "Mrigashira",
                "yoga": "शोभन",
                "yoga_en": "Shobhana",
                "karana": "बव",
                "karana_en": "Bava",
                "festivals": [
                    {"name_ne": "फुल्यारो", "name_en": "Phulyaro", "type": "festival"},
                    {"name_ne": "सार्वजनिक बिदा", "name_en": "Public Holiday", "type": "holiday"}
                ],
                "is_holiday": false,
                "sunrise": "05:38",
                "sunset": "18:45"
            },
            ...
        ]
    }
    """
    url = f"{_API_BASE}{_MONTH_ENDPOINT}"
    params = {"year": bs_year, "month": bs_month}
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShivramJyotish/1.0",
            "Accept": "application/json",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=_TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            # Validate response structure
            if isinstance(data, dict) and "days" in data:
                return data
            # Handle case where response is just an array
            elif isinstance(data, list):
                return {"year": bs_year, "month": bs_month, "days": data}
        elif resp.status_code == 404:
            # Month not available in API
            return None
        else:
            logger.warning("nepalicalendar API error %s: %s",
                           resp.status_code, resp.text[:200])
            return None

    except requests.exceptions.Timeout:
        logger.warning("nepalicalendar API timeout for %s-%s", bs_year, bs_month)
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("nepalicalendar API connection error for %s-%s",
                       bs_year, bs_month)
        return None
    except json.JSONDecodeError:
        logger.warning("nepalicalendar API returned invalid JSON for %s-%s",
                       bs_year, bs_month)
        return None
    except Exception as e:
        logger.warning("nepalicalendar API unexpected error for %s-%s: %s",
                       bs_year, bs_month, e)
        return None


def get_month_data(bs_year: int, bs_month: int, use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Get full month panchang data (tithi, nakshatra, festivals, holidays).
    
    Tries cache first, then API. Saves successful API response to cache.
    """
    # Try cache first
    if use_cache:
        cached = get_cached_month(bs_year, bs_month)
        if cached:
            return cached
    
    # Fetch from API
    data = fetch_month_from_api(bs_year, bs_month)
    
    if data:
        # Save to cache
        if use_cache:
            save_to_cache(bs_year, bs_month, data)
        return data
    
    return None


def parse_month_data(raw_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Parse API response into day-by-day dict for calendar grid.
    
    Returns:
        Dict[bs_day, {
            "ad": datetime.date,
            "tithi_name": str,
            "nakshatra_name": str,
            "yoga_name": str,
            "karana_name": str,
            "festivals": List[Dict],
            "is_holiday": bool,
            "sunrise": str,
            "sunset": str,
        }]
    """
    result: Dict[int, Dict[str, Any]] = {}
    
    days = raw_data.get("days", [])
    for day_data in days:
        try:
            bs_day = int(day_data.get("bs_day", 0))
            if bs_day <= 0:
                continue
                
            ad_str = day_data.get("ad_date", "")
            if ad_str:
                ad_date = datetime.date.fromisoformat(ad_str)
            else:
                continue
            
            festivals = day_data.get("festivals", [])
            if not isinstance(festivals, list):
                festivals = []
            
            is_holiday = day_data.get("is_holiday", False)
            # Also check if any festival is a holiday type
            if not is_holiday:
                is_holiday = any(f.get("type") == "holiday" for f in festivals)
            
            result[bs_day] = {
                "ad": ad_date,
                "tithi_name": day_data.get("tithi", ""),
                "nakshatra_name": day_data.get("nakshatra", ""),
                "yoga_name": day_data.get("yoga", ""),
                "karana_name": day_data.get("karana", ""),
                "festivals": festivals,
                "is_holiday": is_holiday,
                "sunrise": day_data.get("sunrise", ""),
                "sunset": day_data.get("sunset", ""),
                "rahu_kaal": day_data.get("rahu_kaal", day_data.get("rahu_kala", "")),
                "choghadiya": day_data.get("choghadiya", ""),
            }
        except Exception as e:
            logger.warning("nepalicalendar parse error for a day entry: %s", e)
            continue
    
    return result


# Fallback: generate minimal data if API completely unavailable
def generate_fallback_month(bs_year: int, bs_month: int) -> Dict[int, Dict[str, Any]]:
    """
    Generate minimal fallback data when API is unavailable.
    Uses nepali_datetime for BS<->AD conversion and basic tithi calculation.
    """
    try:
        import nepali_datetime
    except ImportError:
        return {}
    
    result: Dict[int, Dict[str, Any]] = {}
    total_days = 30
    
    # Try to get actual month length
    try:
        if bs_month == 12:
            next_y, next_m = bs_year + 1, 1
        else:
            next_y, next_m = bs_year, bs_month + 1
        start = nepali_datetime.date(bs_year, bs_month, 1).to_datetime_date()
        end = nepali_datetime.date(next_y, next_m, 1).to_datetime_date()
        total_days = (end - start).days
    except Exception:
        pass
    
    for day in range(1, total_days + 1):
        try:
            ad = nepali_datetime.date(bs_year, bs_month, day).to_datetime_date()
            result[day] = {
                "ad": ad,
                "tithi_name": "",  # Would need calculation
                "nakshatra_name": "",
                "yoga_name": "",
                "karana_name": "",
                "festivals": [],
                "is_holiday": ad.weekday() == 5,  # Saturday
                "sunrise": "",
                "sunset": "",
            }
        except Exception:
            continue
    
    return result


if __name__ == "__main__":
    # Test the API
    import sys
    if len(sys.argv) >= 3:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        # Default to current BS month
        try:
            import nepali_datetime
            today = datetime.date.today()
            bs = nepali_datetime.date.from_datetime_date(today)
            year, month = bs.year, bs.month
        except Exception:
            year, month = 2083, 6
    
    print(f"Fetching data for BS {year}-{month}...")
    data = get_month_data(year, month, use_cache=False)
    
    if data:
        print("Success! Raw response keys:", data.keys())
        print(f"Days count: {len(data.get('days', []))}")
        if data.get("days"):
            print("Sample day:", json.dumps(data["days"][0], ensure_ascii=False, indent=2))
        
        parsed = parse_month_data(data)
        print(f"\nParsed {len(parsed)} days")
        for d in sorted(parsed.keys())[:3]:
            print(f"  Day {d}: {parsed[d]}")
    else:
        print("API failed, trying fallback...")
        fallback = generate_fallback_month(year, month)
        print(f"Fallback generated {len(fallback)} days")
