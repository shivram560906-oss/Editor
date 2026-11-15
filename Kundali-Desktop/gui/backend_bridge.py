"""
gui/backend_bridge.py

Direct Python bridge to the backend calculation engine.
Bypasses HTTP/FastAPI entirely — calls perform_calculations() directly.
Maintains identical inputs/outputs to the API.
"""
from __future__ import annotations
import datetime
import sys
import os
from typing import Any, Dict, Optional

# ── Backend path setup ─────────────────────────────────────────────────────
_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ── Canonical database URL + per-installation signing key ───────────────────
# Resolved by gui.paths (single source of truth) *before* backend.config is
# imported, because backend/config.py freezes its settings at import time.
# Three modules used to set DATABASE_URL themselves with three different paths,
# so the effective database depended on which module was imported first.
from gui.paths import configure as _configure_desktop_environment

_DESKTOP_ENV = _configure_desktop_environment()

# ── Lazy-import backend modules ────────────────────────────────────────────
_perform_calculations = None
_CITIES = None
_search_cities_fn = None


def _load_calculator():
    """Load the expensive calculation graph only when a chart is requested."""
    global _perform_calculations
    if _perform_calculations is None:
        # Make the Swiss Ephemeris data path deterministic before any
        # calculation runs. Defensive no-op when swisseph is unavailable.
        try:
            from calculator.ephemeris_path import configure_ephemeris_path
            configure_ephemeris_path()
        except Exception:
            pass
        from api.endpoints import perform_calculations as _pc
        _perform_calculations = _pc


def _load_cities():
    """Load lightweight location data without importing the calculation graph."""
    global _CITIES, _search_cities_fn
    if _CITIES is not None:
        return
    from cities_data import CITIES as _C
    _CITIES = _C

    def _search(query: str, limit: int = 12):
        q = query.strip().lower()
        results = [c for c in _CITIES if q in c["name"].lower() or q in c.get("country", "").lower()]
        return results[:limit]
    _search_cities_fn = _search


# ── Public API ─────────────────────────────────────────────────────────────

def calculate_chart(
    *args,
    name: str = "",
    birth_date: str = "",          # YYYY-MM-DD
    birth_time: str = "",          # HH:MM or HH:MM:SS
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone: float = 5.75,
    ayanamsha_type: str = "LAHIRI",
    node_type: str = "MEAN",
    house_system: str = "WHOLE_SIGN",
    city: Optional[str] = None,
    timezone_id: Optional[str] = None,
    calculation_siddhanta: str = "DRIK",
    **extra_meta                        # janmapatrika fields, ignored by engine
) -> Dict[str, Any]:
    """
    Calculate a full Vedic astrology chart.
    Supports either dictionary as first positional arg calculate_chart(dict) or keyword args calculate_chart(**dict).
    calculation_siddhanta: one of 'DRIK' (default) or 'SURYA_SIDDHANTA'
    """
    _load_calculator()

    if args and isinstance(args[0], dict):
        p = dict(args[0])
        name = str(p.get("name") or name or "")
        birth_date = str(p.get("birth_date") or birth_date or "")
        birth_time = str(p.get("birth_time") or birth_time or "12:00:00")
        latitude = float(p.get("latitude") if p.get("latitude") is not None else latitude)
        longitude = float(p.get("longitude") if p.get("longitude") is not None else longitude)
        timezone = float(p.get("timezone") if p.get("timezone") is not None else timezone)
        ayanamsha_type = str(p.get("ayanamsha_type") or ayanamsha_type or "LAHIRI")
        node_type = str(p.get("node_type") or node_type or "MEAN")
        house_system = str(p.get("house_system") or house_system or "WHOLE_SIGN")
        city = p.get("city", city)
        timezone_id = p.get("timezone_id", timezone_id)
        calculation_siddhanta = str(p.get("calculation_siddhanta") or calculation_siddhanta or "DRIK")
        for k, v in p.items():
            if k not in ("name", "birth_date", "birth_time", "latitude", "longitude", "timezone",
                         "ayanamsha_type", "node_type", "house_system", "city", "timezone_id",
                         "calculation_siddhanta"):
                extra_meta[k] = v

    # Normalise time
    time_str = str(birth_time).strip()
    parts = time_str.split(":")
    if len(parts) == 2:
        birth_time = f"{parts[0]}:{parts[1]}:00"
    elif len(parts) == 1 and parts[0]:
        birth_time = f"{parts[0]}:00:00"

    try:
        result = _perform_calculations(
            name=name,
            birth_date=str(birth_date),
            birth_time=str(birth_time),
            latitude=float(latitude),
            longitude=float(longitude),
            timezone=float(timezone),
            ayanamsha_type=ayanamsha_type,
            city=city,
            timezone_id=timezone_id,
            node_type=node_type,
            house_system=house_system,
            calculation_siddhanta=calculation_siddhanta,
            # The five-level Yogini tree is several MB; the Dasha page asks for
            # it lazily through calculate_yogini_report() below.
            include_yogini_tree=False,
        )
        # Merge any extra janmapatrika metadata so widgets can display it
        if extra_meta:
            result.setdefault("metadata", {}).update(
                {k: v for k, v in extra_meta.items() if v is not None}
            )
        return result
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Calculation failed: {exc}") from exc


def calculate_yogini_report(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate only the five-level Yogini tree for an already-built chart.

    The normal chart payload deliberately omits this tree because it contains
    ~20,000 nodes / several MB of JSON.  The Dasha page calls this function when
    the Yogini tab is first opened, avoiding that cost for every calculation.
    """
    if not isinstance(chart, dict) or not chart:
        raise ValueError("A calculated chart payload is required.")

    from calculator import yogini
    from calculator.dasha_contract import report_from_tree

    planets = {
        p.get("name"): p
        for p in (chart.get("planets") or [])
        if isinstance(p, dict)
    }
    moon = planets.get("Moon") or {}
    moon_longitude = moon.get("sidereal_longitude", moon.get("longitude"))
    if moon_longitude is None:
        raise ValueError("Chart payload has no Moon longitude.")

    metadata = chart.get("metadata") or {}
    birth_date = str(metadata.get("birth_date") or "")[:10]
    birth_time = str(metadata.get("birth_time") or "12:00:00").strip()
    if len(birth_time) == 5:                       # HH:MM -> HH:MM:SS
        birth_time += ":00"
    if not birth_date:
        raise ValueError("Chart payload has no birth date.")

    return report_from_tree(
        "yogini",
        yogini.calculate_yogini_dasha_five_level(
            float(moon_longitude), birth_date, birth_time
        ),
    )


def calculate_marriage_match(boy_params: dict, girl_params: dict) -> Dict[str, Any]:
    """Calculate both natal charts and return the complete compatibility report."""
    from calculator.marriage_matching import calculate_compatibility

    boy_chart = calculate_chart(dict(boy_params))
    girl_chart = calculate_chart(dict(girl_params))
    return {
        "boy_chart": boy_chart,
        "girl_chart": girl_chart,
        "compatibility": calculate_compatibility(boy_chart, girl_chart),
    }


def calculate_prashna(
    question_text: str,
    question_category: str,
    question_date: str,
    question_time: str,
    latitude: float,
    longitude: float,
    timezone: float,
    ayanamsha_type: str = "LAHIRI",
) -> Dict[str, Any]:
    """Cast a horary chart and retain the question metadata in the payload."""
    question = (question_text or "").strip()
    if not question:
        raise ValueError("Question must not be empty.")
    chart = calculate_chart(
        name=f"Prashna: {question_category}",
        birth_date=question_date,
        birth_time=question_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        ayanamsha_type=ayanamsha_type,
        city="Prashna location",
    )
    chart["prashna"] = {
        "question_text": question,
        "question_category": question_category,
        "question_date": question_date,
        "question_time": question_time,
    }
    return chart


def calculate_muhurta(
    selected_date: str,
    latitude: float,
    longitude: float,
    timezone: float,
) -> Dict[str, Any]:
    """Calculate Choghadiya, Hora and inauspicious periods for a local date."""
    from calculator import julian, muhurta

    try:
        year, month, day = map(int, selected_date.split("-"))
        datetime.date(year, month, day)
    except (TypeError, ValueError) as exc:
        raise ValueError("Date must use YYYY-MM-DD format.") from exc
    jd_noon = julian.datetime_to_jd(year, month, day, 12, 0, 0, float(timezone))
    result = muhurta.calculate_muhurta(jd_noon, float(latitude), float(longitude), float(timezone))
    if not result:
        raise RuntimeError("Muhurta calculation returned no result for this location and date.")
    return result


def calculate_transit_analysis(
    natal_chart: dict,
    transit_jd: Optional[float] = None,
    language: str = "ne",
) -> Dict[str, Any]:
    """Enhanced Gochar (transit) analysis for an already-calculated natal chart.

    The engine already tolerates both legacy (``lagna.sidereal_longitude``)
    and canonical (``lagna.longitude`` / ``metadata.ayanamsha_value``) payload
    shapes, so the calculated chart is forwarded unchanged.
    """
    from calculator.transit_analysis import calculate_transit_analysis as _cta

    if not isinstance(natal_chart, dict) or not natal_chart:
        raise ValueError("A calculated natal chart payload is required.")
    return _cta(natal_chart, transit_jd=transit_jd, language=language)


def calculate_sarvatobhadra(
    natal_chart: dict,
    on_date: "datetime.date | None" = None,
    timezone: float = 5.75,
    language: str = "ne",
) -> Dict[str, Any]:
    """Sarvatobhadra Chakra transit report for a chosen date (defaults to today)."""
    from calculator import julian, planetary_positions
    from calculator.sarvatobhadra import calculate_sarvatobhadra_for_date

    if not isinstance(natal_chart, dict) or not natal_chart:
        raise ValueError("A calculated natal chart payload is required.")
    if on_date is None:
        on_date = datetime.date.today()

    # Natal Moon longitude / sign (canonical payload exposes "longitude").
    natal_planets = {
        p.get("name"): p
        for p in (natal_chart.get("planets") or [])
        if isinstance(p, dict)
    }
    natal_moon = natal_planets.get("Moon", {}) or {}
    natal_moon_lon = float(
        natal_moon.get("sidereal_longitude", natal_moon.get("longitude", 0)) or 0
    )
    natal_moon_sign = int(natal_moon_lon / 30.0) % 12 + 1

    metadata = natal_chart.get("metadata") or {}
    ayanamsha = float(
        natal_chart.get("ayanamsha_value", metadata.get("ayanamsha_value", 23.85)) or 23.85
    )

    jd = julian.datetime_to_jd(
        on_date.year, on_date.month, on_date.day, 12, 0, 0, float(timezone)
    )
    tropical = planetary_positions.get_swiss_positions(jd, node_type="MEAN")
    if tropical is None:
        T = (jd - 2451545.0) / 36525.0
        tropical = planetary_positions.get_all_tropical_positions(T, jd)

    transit_sidereal: Dict[str, float] = {}
    for name, pos in tropical.items():
        raw = pos[0] if isinstance(pos, (tuple, list)) else float(pos)
        transit_sidereal[name] = (float(raw) - ayanamsha) % 360.0

    current_moon_sign = int(transit_sidereal.get("Moon", 0.0) / 30.0) % 12 + 1
    # Python weekday(): Monday=0..Sunday=6. The engine expects Sunday=0..Saturday=6.
    weekday = (on_date.weekday() + 1) % 7

    return calculate_sarvatobhadra_for_date(
        natal_moon_lon,
        natal_moon_sign,
        transit_sidereal,
        current_moon_sign,
        weekday,
    )


def calculate_ayanamsha_comparison(
    reference_date: Optional[str] = None,
    latitude: float = 27.7172,
    longitude: float = 85.3240,
    timezone: float = 5.75,
    hour: int = 12,
) -> Dict[str, Any]:
    """Compare every supported ayanamsha system at a reference date.

    Returns the Swiss-Ephemeris ayanamsha offset for each system together with
    the derived sidereal ascendant (lagna) degree and sign, so the accuracy of
    the active ayanamsha can be verified against the alternatives.
    """
    _load_calculator()
    import datetime as _dt
    from calculator import ayanamsha as _ayan
    from calculator.julian import datetime_to_jd
    from calculator import houses as _houses

    if reference_date:
        y, m, d = (int(part) for part in str(reference_date).split("-")[:3])
    else:
        today = _dt.date.today()
        y, m, d = today.year, today.month, today.day

    jd = datetime_to_jd(int(y), int(m), int(d), int(hour), 0, 0.0, float(timezone))
    t_centuries = (jd - 2451545.0) / 36525.0
    lagna_tropical = float(_houses.calculate_lagna(jd, float(latitude), float(longitude)))

    systems = []
    for code in sorted(_ayan.SWISS_AYANAMSHA_MODES):
        try:
            offset = float(_ayan.get_ayanamsha(code, t_centuries))
        except Exception:
            continue
        lagna_sidereal = (lagna_tropical - offset) % 360.0
        systems.append({
            "code": code,
            "ayanamsha": round(offset, 6),
            "lagna_sidereal": round(lagna_sidereal, 6),
            "lagna_sign": int(lagna_sidereal / 30.0) + 1,
        })

    return {
        "reference_date": f"{int(y):04d}-{int(m):02d}-{int(d):02d}",
        "hour": int(hour),
        "timezone": float(timezone),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "julian_day": jd,
        "lagna_tropical": lagna_tropical,
        "default_system": "LAHIRI",
        "systems": systems,
    }


def search_cities(query: str, limit: int = 12) -> list[dict]:
    """Search the city database. Returns list of dicts with name/country/lat/lon/tz."""
    _load_cities()
    return _search_cities_fn(query, limit)


def get_all_cities() -> list[dict]:
    """Return all cities (for dropdown/combo-box population)."""
    _load_cities()
    return list(_CITIES)


def convert_bs_to_ad(bs_year: int, bs_month: int, bs_day: int) -> dict | None:
    """
    Convert BS date to AD.  Returns dict {year,month,day} or None.
    Uses nepali_datetime (same library as backend).
    """
    try:
        import nepali_datetime
        import datetime
        bs = nepali_datetime.date(bs_year, bs_month, bs_day)
        ad = bs.to_datetime_date()
        return {"year": ad.year, "month": ad.month, "day": ad.day}
    except Exception:
        return None


def convert_ad_to_bs(ad_year: int, ad_month: int, ad_day: int) -> dict | None:
    """
    Convert AD date to BS.  Returns dict {year,month,day} or None.
    """
    try:
        import nepali_datetime
        ad = datetime.date(ad_year, ad_month, ad_day)
        bs = nepali_datetime.date.from_datetime_date(ad)
        return {"year": bs.year, "month": bs.month, "day": bs.day}
    except Exception:
        return None


def calculate_ayurdaya(chart_data: dict, language: str = "ne") -> dict:
    """
    Calculate comprehensive 7-step classical Parashari Ayurdaya reading.
    """
    from calculator.ayurdaya import calculate_comprehensive_ayurdaya
    return calculate_comprehensive_ayurdaya(chart_data, language=language)


def calculate_child_analysis(chart_data: dict, language: str = "ne") -> dict:
    """
    Calculate comprehensive 8-step classical Parashari Child Analysis (पुत्र अध्याय).
    """
    from calculator.child_analysis_engine import calculate_comprehensive_child_analysis
    return calculate_comprehensive_child_analysis(chart_data, language=language)


def calculate_career_analysis(chart_data: dict, language: str = "ne") -> dict:
    """
    Calculate comprehensive 8-step classical Parashari Career & Livelihood Analysis (व्यवसाय/जीविका निर्णय).
    """
    from calculator.career_analysis_engine import calculate_comprehensive_career_analysis
    return calculate_comprehensive_career_analysis(chart_data, language=language)


def calculate_marriage_analysis(chart_data: dict, language: str = "ne", gender: str = "male") -> dict:
    """
    Calculate comprehensive 9-step classical Parashari Marriage Analysis (विवाह/कलत्र विचार).
    """
    from calculator.marriage_analysis_engine import calculate_comprehensive_marriage_analysis
    return calculate_comprehensive_marriage_analysis(chart_data, language=language, gender=gender)


def calculate_gandanta_shanti(
    chart_data: dict,
    birth_time_str: str = None,
    order_of_child: str = None,
    language: str = "ne"
) -> dict:
    """
    Calculate comprehensive Classical BPHS Gandanta and Arishta Janma Shanti (गण्डान्त तथा अनिष्ट जन्म-शान्ति).
    """
    from calculator.gandanta_shanti_engine import calculate_gandanta_shanti_analysis
    return calculate_gandanta_shanti_analysis(
        chart_data,
        birth_time_str=birth_time_str,
        order_of_child=order_of_child,
        language=language
    )



