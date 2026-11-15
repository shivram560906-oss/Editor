"""Offline country/region/district/city hierarchy for birth-place pickers.

The curated city dataset only stores a flat city list.  The GUI already owns
the Nepal administrative metadata, so this module reuses those helpers and
returns one compact payload that the web form can cascade through without any
network lookup or free-text coordinate entry.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

# GUI helpers live next to the backend package; make them importable when the
# backend is started directly from Kundali-Desktop/backend.
_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from cities_data import CITIES
from calculator import timezone_resolver
from gui.utils.location_data import (
    NEPAL_DISTRICT_META,
    NEPAL_PROVINCE_NE,
    countries as _countries,
    districts_for_region,
    enrich_cities,
    regions_for_country,
)

_CACHE: Optional[dict[str, Any]] = None


def _city_record(city: dict[str, Any]) -> dict[str, Any]:
    """Return one API-safe city with its IANA timezone provenance."""
    enriched = timezone_resolver.enrich_city(city)
    return {
        "name": city.get("name"),
        "country": city.get("country"),
        "region": city.get("region"),
        "district": city.get("district"),
        "latitude": enriched["latitude"],
        "longitude": enriched["longitude"],
        "timezone": enriched["timezone"],
        "timezone_id": enriched["timezone_id"],
    }


def _district_center(meta: dict[str, Any]) -> dict[str, Any]:
    name_ne = meta.get("name_ne")
    return {
        "name": meta["name"],
        "name_ne": name_ne,
        "label": f'{meta["name"]} / {name_ne}' if name_ne else meta["name"],
        "country": meta["country"],
        "region": meta["region"],
        "district": meta["district"],
        "latitude": meta["lat"],
        "longitude": meta["lon"],
        "timezone": meta["tz"],
        "timezone_id": meta["timezone_id"],
    }


def _region_label(country: str, region: str) -> str:
    translated = NEPAL_PROVINCE_NE.get(region) if country == "Nepal" else None
    return f"{region} / {translated}" if translated else region


def _district_label(district: str) -> str:
    meta = NEPAL_DISTRICT_META.get(district) or {}
    translated = meta.get("name_ne")
    return f"{district} / {translated}" if translated else district


def build_location_hierarchy() -> dict[str, Any]:
    """Build (once) the complete cascading birth-place payload."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    cities = enrich_cities(CITIES)
    country_names = _countries(cities)

    regions: dict[str, list[dict[str, str]]] = {}
    districts: dict[str, dict[str, list[dict[str, str]]]] = {}
    for country in country_names:
        country_regions = regions_for_country(country, cities)
        regions[country] = [
            {"name": region, "label": _region_label(country, region)}
            for region in country_regions
        ]
        districts[country] = {
            region: [
                {"name": district, "label": _district_label(district)}
                for district in districts_for_region(country, region, cities)
            ]
            for region in country_regions
        }

    _CACHE = {
        "countries": [
            {
                "name": country,
                "label": "Nepal / नेपाल" if country == "Nepal" else country,
            }
            for country in country_names
        ],
        "regions": regions,
        "districts": districts,
        "cities": [_city_record(city) for city in cities],
        "district_centers": {
            name: _district_center(meta)
            for name, meta in NEPAL_DISTRICT_META.items()
        },
    }
    return _CACHE
