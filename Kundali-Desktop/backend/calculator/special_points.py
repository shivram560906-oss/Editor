"""Vedic special-lagna and upagraha calculations.

All public longitudes are tropical. The caller applies its selected ayanamsha once,
which keeps these points consistent with planets, houses, and custom offsets.
"""
from __future__ import annotations

from typing import Dict

from . import houses, panchang

_PLANETARY_SEQUENCE = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_UPAGRAHA_RULERS = {"Kala": "Sun", "Yamaghantaka": "Jupiter", "Gulika": "Saturn"}


def _forward_arc(start: float, end: float) -> float:
    return (end - start) % 360.0


def calculate_special_lagnas(
    jd: float,
    latitude: float,
    longitude: float,
    timezone: float,
    sun_tropical: float,
) -> Dict[str, float]:
    """Calculate Bhava, Hora, Ghati and Pranapada lagnas from local sunrise."""
    sunrise_jd = panchang.calculate_sunrise_jd(jd, latitude, longitude, timezone)
    elapsed_hours = ((jd - sunrise_jd) % 1.0) * 24.0
    # Classical rates: one sign per 2h, 1h and 24m respectively.
    bhava = (sun_tropical + elapsed_hours * 15.0) % 360.0
    hora = (sun_tropical + elapsed_hours * 30.0) % 360.0
    ghati = (sun_tropical + elapsed_hours * 75.0) % 360.0

    # Pranapada uses elapsed vighatis from sunrise. The movable/fixed/dual
    # correction is based on the Sun's sign as prescribed by Parashara.
    vighatis = elapsed_hours * 150.0
    base = (vighatis * 0.1) % 360.0
    sun_sign = int(sun_tropical // 30.0) % 12
    correction = 0.0 if sun_sign in {0, 3, 6, 9} else (240.0 if sun_sign in {1, 4, 7, 10} else 120.0)
    pranapada = (base + sun_tropical + correction) % 360.0
    return {"Bhava": bhava, "Hora": hora, "Ghati": ghati, "Pranapada": pranapada}


def calculate_upagrahas(
    jd: float,
    latitude: float,
    longitude: float,
    timezone: float,
) -> Dict[str, float]:
    """Calculate Kala, Yamaghantaka, Gulika and Mandi using eight day/night parts."""
    sunrise = panchang.calculate_sunrise_jd(jd, latitude, longitude, timezone)
    next_sunrise = panchang.calculate_sunrise_jd(jd + 1.0, latitude, longitude, timezone)
    # The sunset midpoint is sufficiently stable here and remains polar-safe when
    # the sunrise helper uses its documented fallback.
    sunset = (sunrise + next_sunrise) / 2.0
    is_day = sunrise <= jd < sunset
    start, end = (sunrise, sunset) if is_day else ((sunset, next_sunrise) if jd >= sunset else (sunrise - 0.5, sunrise))

    # JD 0 is Monday; convert to Sunday=0. The nocturnal sequence starts from
    # the fifth lord counted from the weekday lord.
    local_weekday = int(jd + timezone / 24.0 + 1.5) % 7
    first_lord = local_weekday if is_day else (local_weekday + 4) % 7
    duration = (end - start) / 8.0
    result: Dict[str, float] = {}
    for point, ruler in _UPAGRAHA_RULERS.items():
        segment = next(i for i in range(7) if _PLANETARY_SEQUENCE[(first_lord + i) % 7] == ruler)
        point_jd = start + segment * duration
        result[point] = houses.calculate_lagna(point_jd, latitude, longitude)
        if point == "Gulika":
            result["Mandi"] = houses.calculate_lagna(point_jd + duration / 2.0, latitude, longitude)
    return result
