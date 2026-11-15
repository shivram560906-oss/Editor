import math
from datetime import datetime, timedelta
from typing import Dict, Any, List

from . import panchang

CHOGHADIYA_NAMES = {
    "udveg": {"en": "Udveg", "ne": "उद्वेग", "type": "bad", "color": "#f87171", "quality": "अशुभ"},
    "amrit": {"en": "Amrit", "ne": "अमृत", "type": "good", "color": "#4ade80", "quality": "सर्वोत्तम"},
    "rog":   {"en": "Rog",   "ne": "रोग",   "type": "bad", "color": "#f87171", "quality": "अशुभ"},
    "labh":  {"en": "Labh",  "ne": "लाभ",  "type": "good", "color": "#4ade80", "quality": "उत्तम"},
    "shubh": {"en": "Shubh", "ne": "शुभ",  "type": "good", "color": "#4ade80", "quality": "शुभ"},
    "char":  {"en": "Char",  "ne": "चर",   "type": "neutral", "color": "#facc15", "quality": "मध्यम/चल कार्य"},
    "kaal":  {"en": "Kaal",  "ne": "काल",  "type": "bad", "color": "#f87171", "quality": "हानिकारक"}
}

# Day starting choghadiya sequences (0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat)
CHOGHADIYA_DAY_START = [
    ["udveg", "char", "labh", "amrit", "kaal", "shubh", "rog", "udveg"], # Sunday
    ["amrit", "kaal", "shubh", "rog", "udveg", "char", "labh", "amrit"], # Monday
    ["rog", "udveg", "char", "labh", "amrit", "kaal", "shubh", "rog"],   # Tuesday
    ["labh", "amrit", "kaal", "shubh", "rog", "udveg", "char", "labh"],  # Wednesday
    ["shubh", "rog", "udveg", "char", "labh", "amrit", "kaal", "shubh"], # Thursday
    ["char", "labh", "amrit", "kaal", "shubh", "rog", "udveg", "char"],  # Friday
    ["kaal", "shubh", "rog", "udveg", "char", "labh", "amrit", "kaal"]   # Saturday
]

CHOGHADIYA_NIGHT_START = [
    ["shubh", "amrit", "char", "rog", "kaal", "labh", "udveg", "shubh"], # Sunday
    ["char", "rog", "kaal", "labh", "udveg", "shubh", "amrit", "char"],  # Monday
    ["rog", "kaal", "labh", "udveg", "shubh", "amrit", "char", "rog"],   # Tuesday
    ["kaal", "labh", "udveg", "shubh", "amrit", "char", "rog", "kaal"],  # Wednesday
    ["amrit", "char", "rog", "kaal", "labh", "udveg", "shubh", "amrit"], # Thursday
    ["rog", "kaal", "labh", "udveg", "shubh", "amrit", "char", "rog"],   # Friday
    ["labh", "udveg", "shubh", "amrit", "char", "rog", "kaal", "labh"]   # Saturday
]

PLANETS = [
    {"en": "Sun", "ne": "सूर्य", "nature": "क्रूर / ऊर्जा"},
    {"en": "Moon", "ne": "चन्द्र", "nature": "शुभ / सौम्य"},
    {"en": "Mars", "ne": "मंगल", "nature": "क्रूर / पराक्रम"},
    {"en": "Mercury", "ne": "बुध", "nature": "शुभ / बुद्धि"},
    {"en": "Jupiter", "ne": "गुरु", "nature": "परम शुभ / ज्ञान"},
    {"en": "Venus", "ne": "शुक्र", "nature": "शुभ / भोग"},
    {"en": "Saturn", "ne": "शनि", "nature": "क्रूर / कर्म"}
]

# Hora lord order (decreasing planetary speed): Saturn(6), Jupiter(4), Mars(2), Sun(0), Venus(5), Mercury(3), Moon(1)
HORA_LORDS = [6, 4, 2, 0, 5, 3, 1] 

# Rahu Kaal 8th parts to pick based on weekday (0=Sun to 6=Sat)
RAHU_KAAL_PARTS = [8, 2, 7, 5, 6, 4, 3]
GULIKA_PARTS = [7, 6, 5, 4, 3, 2, 1]
YAMAGANDA_PARTS = [5, 4, 3, 2, 1, 7, 6]

# Durmuhurta parts (15 daytime parts, 1-indexed) based on weekday (0=Sun to 6=Sat)
DURMUHURTA_PARTS = [
    [14],       # Sunday: 14th
    [8, 12],    # Monday: 8th and 12th
    [4, 11],    # Tuesday: 4th and 11th
    [8],        # Wednesday: 8th (Abhijit is prohibited on Wednesday)
    [12, 13],   # Thursday: 12th and 13th
    [4, 9],     # Friday: 4th and 9th
    [2, 3],     # Saturday: 2nd and 3rd
]


def _jd_to_hhmm(jd: float, timezone: float) -> str:
    utc_frac = (jd + 0.5) % 1.0
    utc_hours = utc_frac * 24.0
    local_hours = (utc_hours + timezone) % 24.0
    h = int(local_hours)
    m = int((local_hours - h) * 60.0 + 0.5)
    if m >= 60:
        h = (h + 1) % 24
        m = 0
    return f"{h:02d}:{m:02d}"


def calculate_muhurta(jd_noon: float, latitude: float, longitude: float, timezone: float) -> Dict[str, Any]:
    """Calculate comprehensive classical Muhurta data: Choghadiya, Hora, Kaals, Brahma, Godhuli, Pradosha, Nishita, Durmuhurta, and Auspicious Windows."""
    # 1. Calculate sunrise, sunset for today
    sun_data = panchang.calculate_sunrise_sunset(jd_noon, latitude, longitude, timezone)
    if not sun_data:
        return {}
        
    sunrise_jd = panchang.calculate_sunrise_jd(jd_noon, latitude, longitude, timezone)
    day_dur_min = sun_data["day_duration_min"]
    sunset_jd = sunrise_jd + (day_dur_min / 1440.0)
    
    # Next day sunrise
    jd_noon_next = jd_noon + 1.0
    sunrise_next_jd = panchang.calculate_sunrise_jd(jd_noon_next, latitude, longitude, timezone)
    
    # Weekday (0 = Sunday)
    weekday = int(sunrise_jd + timezone / 24.0 + 1.5) % 7
    
    # Durations
    day_duration = sunset_jd - sunrise_jd
    night_duration = sunrise_next_jd - sunset_jd
    day_part = day_duration / 8.0
    night_part = night_duration / 8.0
    day_hora_part = day_duration / 12.0
    night_hora_part = night_duration / 12.0
    day_muhurta_part = day_duration / 15.0  # 15 divisions of the day
    
    # --- Choghadiya ---
    choghadiya_day = []
    for i in range(8):
        name_key = CHOGHADIYA_DAY_START[weekday][i]
        choghadiya_day.append({
            "start": _jd_to_hhmm(sunrise_jd + i * day_part, timezone),
            "end": _jd_to_hhmm(sunrise_jd + (i+1) * day_part, timezone),
            "name": CHOGHADIYA_NAMES[name_key]
        })
        
    choghadiya_night = []
    for i in range(8):
        name_key = CHOGHADIYA_NIGHT_START[weekday][i]
        choghadiya_night.append({
            "start": _jd_to_hhmm(sunset_jd + i * night_part, timezone),
            "end": _jd_to_hhmm(sunset_jd + (i+1) * night_part, timezone),
            "name": CHOGHADIYA_NAMES[name_key]
        })
        
    # --- Hora ---
    start_lord_idx = HORA_LORDS.index(weekday) if weekday in HORA_LORDS else 0 
    
    hora_day = []
    for i in range(12):
        lord_idx = HORA_LORDS[(start_lord_idx + i) % 7]
        hora_day.append({
            "start": _jd_to_hhmm(sunrise_jd + i * day_hora_part, timezone),
            "end": _jd_to_hhmm(sunrise_jd + (i+1) * day_hora_part, timezone),
            "lord": PLANETS[lord_idx]
        })
        
    hora_night = []
    start_night_idx = (start_lord_idx + 12) % 7
    for i in range(12):
        lord_idx = HORA_LORDS[(start_night_idx + i) % 7]
        hora_night.append({
            "start": _jd_to_hhmm(sunset_jd + i * night_hora_part, timezone),
            "end": _jd_to_hhmm(sunset_jd + (i+1) * night_hora_part, timezone),
            "lord": PLANETS[lord_idx]
        })

    # --- Inauspicious Kaals ---
    rahu_idx = RAHU_KAAL_PARTS[weekday] - 1
    rahu_start = sunrise_jd + rahu_idx * day_part
    rahu_end = rahu_start + day_part
    
    gulika_idx = GULIKA_PARTS[weekday] - 1
    gulika_start = sunrise_jd + gulika_idx * day_part
    gulika_end = gulika_start + day_part
    
    yamaganda_idx = YAMAGANDA_PARTS[weekday] - 1
    yamaganda_start = sunrise_jd + yamaganda_idx * day_part
    yamaganda_end = yamaganda_start + day_part
    
    # Abhijit Muhurta — Classical: Solar Noon ± 24 min
    solar_noon_jd = (sunrise_jd + sunset_jd) / 2.0
    abhijit_start = solar_noon_jd - (24.0 / 1440.0)
    abhijit_end   = solar_noon_jd + (24.0 / 1440.0)
    # Wednesday Abhijit is considered prohibited / Durmuhurta
    abhijit_is_good = (weekday != 3)

    # --- Special Classical Auspicious Muhurtas ---
    # Brahma Muhurta: 96 to 48 minutes before sunrise
    brahma_start = sunrise_jd - (96.0 / 1440.0)
    brahma_end   = sunrise_jd - (48.0 / 1440.0)

    # Godhuli Muhurta: 12 minutes before to 12 minutes after sunset
    godhuli_start = sunset_jd - (12.0 / 1440.0)
    godhuli_end   = sunset_jd + (12.0 / 1440.0)

    # Pradosha Kaal: Sunset to 72 minutes after sunset
    pradosha_start = sunset_jd
    pradosha_end   = sunset_jd + (72.0 / 1440.0)

    # Nishita Muhurta (Midnight power window): Solar midnight ± 24 minutes
    solar_midnight_jd = (sunset_jd + sunrise_next_jd) / 2.0
    nishita_start = solar_midnight_jd - (24.0 / 1440.0)
    nishita_end   = solar_midnight_jd + (24.0 / 1440.0)

    # Durmuhurta intervals
    durmuhurta_list = []
    for part_idx in DURMUHURTA_PARTS[weekday]:
        dm_start = sunrise_jd + (part_idx - 1) * day_muhurta_part
        dm_end = dm_start + day_muhurta_part
        durmuhurta_list.append({
            "part": part_idx,
            "start": _jd_to_hhmm(dm_start, timezone),
            "end": _jd_to_hhmm(dm_end, timezone),
            "description": f"दुर्मुहूर्त भाग {part_idx} (अशुभ समय)"
        })

    # Recommended Auspicious Windows
    auspicious_windows = []
    # 1. Brahma Muhurta
    auspicious_windows.append({
        "name": "Brahma Muhurta",
        "nepali": "ब्रह्म मुहूर्त",
        "start": _jd_to_hhmm(brahma_start, timezone),
        "end": _jd_to_hhmm(brahma_end, timezone),
        "quality": "सर्वोत्तम (ध्यान, साधना, अध्ययन)",
        "type": "spiritual"
    })
    # 2. Abhijit Muhurta (if not Wednesday)
    if abhijit_is_good:
        auspicious_windows.append({
            "name": "Abhijit Muhurta",
            "nepali": "अभिजित मुहूर्त",
            "start": _jd_to_hhmm(abhijit_start, timezone),
            "end": _jd_to_hhmm(abhijit_end, timezone),
            "quality": "विजयदायी / सर्वकार्य सिद्धि",
            "type": "general"
        })
    # 3. Godhuli Muhurta
    auspicious_windows.append({
        "name": "Godhuli Muhurta",
        "nepali": "गोधूलि मुहूर्त",
        "start": _jd_to_hhmm(godhuli_start, timezone),
        "end": _jd_to_hhmm(godhuli_end, timezone),
        "quality": "शुभ / शान्ति कर्म, यात्रा",
        "type": "ceremonial"
    })
    # 4. Amrit Choghadiya (day)
    for ch in choghadiya_day:
        if ch["name"]["en"] in ("Amrit", "Shubh", "Labh"):
            auspicious_windows.append({
                "name": f"{ch['name']['en']} Choghadiya",
                "nepali": f"{ch['name']['ne']} चौघडिया",
                "start": ch["start"],
                "end": ch["end"],
                "quality": f"{ch['name']['quality']} ({ch['name']['ne']})",
                "type": "daily"
            })
    
    return {
        "choghadiya_day": choghadiya_day,
        "choghadiya_night": choghadiya_night,
        "hora_day": hora_day,
        "hora_night": hora_night,
        "kaals": {
            "rahu": {"start": _jd_to_hhmm(rahu_start, timezone), "end": _jd_to_hhmm(rahu_end, timezone)},
            "gulika": {"start": _jd_to_hhmm(gulika_start, timezone), "end": _jd_to_hhmm(gulika_end, timezone)},
            "yamaganda": {"start": _jd_to_hhmm(yamaganda_start, timezone), "end": _jd_to_hhmm(yamaganda_end, timezone)},
            "abhijit": {"start": _jd_to_hhmm(abhijit_start, timezone), "end": _jd_to_hhmm(abhijit_end, timezone), "is_good": abhijit_is_good}
        },
        "special_muhurtas": {
            "brahma": {"start": _jd_to_hhmm(brahma_start, timezone), "end": _jd_to_hhmm(brahma_end, timezone)},
            "godhuli": {"start": _jd_to_hhmm(godhuli_start, timezone), "end": _jd_to_hhmm(godhuli_end, timezone)},
            "pradosha": {"start": _jd_to_hhmm(pradosha_start, timezone), "end": _jd_to_hhmm(pradosha_end, timezone)},
            "nishita": {"start": _jd_to_hhmm(nishita_start, timezone), "end": _jd_to_hhmm(nishita_end, timezone)},
            "durmuhurta": durmuhurta_list
        },
        "auspicious_windows": auspicious_windows
    }
