import datetime
import math
import re
from copy import deepcopy

import nepali_datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator

from config import settings
from database.connection import get_db
from database import models
from calculator import julian, planetary_positions, ayanamsha, houses, panchang, dasha, yogini, yogas, vargas, marriage_matching, special_points, varshaphala, jaimini, kp_system, surya_siddhanta
from calculator import planetary_ingress, timezone_resolver
from calculator.dasha_contract import report_from_tree, unavailable_report
from calculator.avakahada_chakra import calculate_avakahada_chakra
from calculator import ashtakavarga as ashtakavarga_calc
from calculator import shadbala as shadbala_calc
from calculator import vimshopaka as vimshopaka_calc
from calculator import avasthas as avasthas_calc
from calculator import kaal_sarp_dosha as kaal_sarp_dosha_calc
from calculator import lal_kitab as lal_kitab_calc
from calculator import remedies as remedies_calc
from calculator.comprehensive_book_engine import build_comprehensive_kundali_book
from cities_data import CITIES
from location_hierarchy import build_location_hierarchy
from rate_limit import limiter

router = APIRouter()

# --- Constants used for input validation ---

SUPPORTED_AYANAMSHA_TYPES = set(ayanamsha.SWISS_AYANAMSHA_MODES) | {"CUSTOM"}
SUPPORTED_NODE_TYPES = {"MEAN", "TRUE"}
SUPPORTED_HOUSE_SYSTEMS = {"WHOLE_SIGN", "SHRIPATI", "PLACIDUS"}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def _validate_birth_date(value: str) -> str:
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError("birth_date must be in YYYY-MM-DD format")
    try:
        datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"birth_date is not a valid calendar date: {exc}")
    return value


def _validate_birth_time(value: str) -> str:
    if not isinstance(value, str) or not _TIME_RE.match(value):
        raise ValueError("birth_time must be in HH:MM or HH:MM:SS format")
    parts = value.split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    if not (0 <= h <= 23):
        raise ValueError("birth_time hour must be between 0 and 23")
    if not (0 <= m <= 59):
        raise ValueError("birth_time minute must be between 0 and 59")
    if not (0 <= s <= 59):
        raise ValueError("birth_time second must be between 0 and 59")
    # Always normalise to HH:MM:SS so downstream parsers are deterministic.
    return f"{h:02d}:{m:02d}:{s:02d}"


def _validate_ayanamsha(value: str) -> str:
    value = str(value).upper()
    if value.startswith("CUSTOM:"):
        try:
            offset = float(value.split(":", 1)[1])
        except ValueError as exc:
            raise ValueError("CUSTOM ayanamsha must be CUSTOM:<degrees>") from exc
        if not -360.0 <= offset <= 360.0:
            raise ValueError("custom ayanamsha offset must be between -360 and 360")
        return value
    if value not in SUPPORTED_AYANAMSHA_TYPES:
        raise ValueError(
            f"ayanamsha_type must be one of {sorted(SUPPORTED_AYANAMSHA_TYPES)}"
        )
    return value


# --- Pydantic Schemas for Request/Response Validation ---

JANMAPATRIKA_TEXT_LIMITS = {
    "full_name": 200, "father_name": 200, "mother_name": 200,
    "gotra": 100, "surname": 100, "kula": 100, "kuladevata": 200,
    "spouse_name": 200, "marital_status": 50, "caste": 100,
    "religion": 100, "family_details": 2000, "country": 100,
    "birth_place": 200, "timezone_id": 100,
}


class JanmapatrikaDetails(BaseModel):
    """Additive identity metadata; never participates in chart calculations."""

    timezone_id: Optional[str] = None
    country: Optional[str] = None
    birth_place: Optional[str] = None
    full_name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    gotra: Optional[str] = None
    surname: Optional[str] = None
    kula: Optional[str] = None
    kuladevata: Optional[str] = None
    spouse_name: Optional[str] = None
    marital_status: Optional[str] = None
    caste: Optional[str] = None
    religion: Optional[str] = None
    family_details: Optional[str] = None

    @field_validator(*JANMAPATRIKA_TEXT_LIMITS.keys())
    @classmethod
    def _validate_janmapatrika_text(cls, value, info):
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        limit = JANMAPATRIKA_TEXT_LIMITS[info.field_name]
        if len(cleaned) > limit:
            raise ValueError(f"{info.field_name} must not exceed {limit} characters")
        return cleaned


class ChartRequest(JanmapatrikaDetails):
    name: str
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM:SS
    latitude: float
    longitude: float
    timezone: float  # legacy numeric fallback; effective offset may include DST
    ayanamsha_type: str = "LAHIRI"
    node_type: str = "MEAN"
    house_system: str = "WHOLE_SIGN"
    city: Optional[str] = None
    # The web editor does not render these heavyweight sections; it asks the
    # engine to skip them so free-tier CPUs and response sizes stay small.
    include_yogini_tree: bool = True
    include_comprehensive_book: bool = True

    @field_validator("birth_date")
    @classmethod
    def _check_birth_date(cls, v):
        return _validate_birth_date(v)

    @field_validator("birth_time")
    @classmethod
    def _check_birth_time(cls, v):
        return _validate_birth_time(v)

    @field_validator("ayanamsha_type")
    @classmethod
    def _check_ayanamsha(cls, v):
        return _validate_ayanamsha(v)

    @field_validator("node_type")
    @classmethod
    def _check_node_type(cls, v):
        value = str(v).upper()
        if value not in SUPPORTED_NODE_TYPES:
            raise ValueError("node_type must be MEAN or TRUE")
        return value

    @field_validator("house_system")
    @classmethod
    def _check_house_system(cls, v):
        value = str(v).upper()
        if value not in SUPPORTED_HOUSE_SYSTEMS:
            raise ValueError("house_system must be WHOLE_SIGN, SHRIPATI, or PLACIDUS")
        return value

    @field_validator("latitude")
    @classmethod
    def _check_latitude(cls, v):
        if not -90.0 <= v <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def _check_longitude(cls, v):
        if not -180.0 <= v <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return v

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, v):
        if not -12.0 <= v <= 14.0:
            raise ValueError("timezone must be between -12 and +14 hours")
        return v

    @field_validator("name")
    @classmethod
    def _check_name(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

class RecordCreate(JanmapatrikaDetails):
    name: str
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone: float
    gender: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("birth_date")
    @classmethod
    def _check_birth_date(cls, v):
        return _validate_birth_date(v)

    @field_validator("birth_time")
    @classmethod
    def _check_birth_time(cls, v):
        return _validate_birth_time(v)

    @field_validator("latitude")
    @classmethod
    def _check_latitude(cls, v):
        if not -90.0 <= v <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def _check_longitude(cls, v):
        if not -180.0 <= v <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return v

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, v):
        if not -12.0 <= v <= 14.0:
            raise ValueError("timezone must be between -12 and +14 hours")
        return v

    @field_validator("name")
    @classmethod
    def _check_name(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("name must not be empty")
        return v


class RecordResponse(JanmapatrikaDetails):
    id: int
    name: str
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone: float
    gender: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


RECORD_EDITABLE_FIELDS = (
    "name",
    "birth_date",
    "birth_time",
    "latitude",
    "longitude",
    "timezone",
    "gender",
    "notes",
    *JANMAPATRIKA_TEXT_LIMITS.keys(),
)


def _replace_record_fields(db_record: models.KundaliRecord, record: RecordCreate) -> None:
    """Replace persisted input fields without involving calculation output."""
    for field_name in RECORD_EDITABLE_FIELDS:
        setattr(db_record, field_name, getattr(record, field_name, None))


class SettingsUpdate(BaseModel):
    ayanamsha_type: str
    chart_style: str
    language: str

    @field_validator("ayanamsha_type")
    @classmethod
    def _check_ayanamsha(cls, v):
        return _validate_ayanamsha(v)

    @field_validator("language")
    @classmethod
    def _check_language(cls, v):
        if v not in {"en", "ne"}:
            raise ValueError("language must be 'en' or 'ne'")
        return v

    @field_validator("chart_style")
    @classmethod
    def _check_chart_style(cls, v):
        if v not in {"NORTH_INDIAN", "SOUTH_INDIAN", "EAST_INDIAN"}:
            raise ValueError("chart_style must be NORTH_INDIAN, SOUTH_INDIAN, or EAST_INDIAN")
        return v


class MarriageMatchRequest(BaseModel):
    boy_name: str
    boy_birth_date: str
    boy_birth_time: str
    boy_latitude: float
    boy_longitude: float
    boy_timezone: float
    boy_city: Optional[str] = None
    boy_timezone_id: Optional[str] = None
    boy_ayanamsha_type: str = "LAHIRI"
    girl_name: str
    girl_birth_date: str
    girl_birth_time: str
    girl_latitude: float
    girl_longitude: float
    girl_timezone: float
    girl_city: Optional[str] = None
    girl_timezone_id: Optional[str] = None
    girl_ayanamsha_type: str = "LAHIRI"

    @field_validator("boy_birth_date", "girl_birth_date")
    @classmethod
    def _check_birth_date(cls, v):
        return _validate_birth_date(v)

    @field_validator("boy_birth_time", "girl_birth_time")
    @classmethod
    def _check_birth_time(cls, v):
        return _validate_birth_time(v)

    @field_validator("boy_ayanamsha_type", "girl_ayanamsha_type")
    @classmethod
    def _check_ayanamsha(cls, v):
        return _validate_ayanamsha(v)

    @field_validator("boy_latitude", "girl_latitude")
    @classmethod
    def _check_latitude(cls, v):
        if not -90.0 <= v <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("boy_longitude", "girl_longitude")
    @classmethod
    def _check_longitude(cls, v):
        if not -180.0 <= v <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return v

    @field_validator("boy_timezone", "girl_timezone")
    @classmethod
    def _check_timezone(cls, v):
        if not -12.0 <= v <= 14.0:
            raise ValueError("timezone must be between -12 and +14 hours")
        return v

    @field_validator("boy_name", "girl_name")
    @classmethod
    def _check_name(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("name must not be empty")
        return v


class PrashnaRequest(BaseModel):
    question_text: str
    question_category: str  # marriage, education, career, health, wealth, travel, legal, children, business, love
    question_date: str  # YYYY-MM-DD
    question_time: str  # HH:MM:SS
    latitude: float
    longitude: float
    timezone: float
    ayanamsha_type: str = "LAHIRI"

    @field_validator("question_date")
    @classmethod
    def _check_date(cls, v):
        return _validate_birth_date(v)

    @field_validator("question_time")
    @classmethod
    def _check_time(cls, v):
        return _validate_birth_time(v)

    @field_validator("ayanamsha_type")
    @classmethod
    def _check_ayanamsha(cls, v):
        return _validate_ayanamsha(v)

    @field_validator("latitude")
    @classmethod
    def _check_latitude(cls, v):
        if not -90.0 <= v <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def _check_longitude(cls, v):
        if not -180.0 <= v <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return v

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, v):
        if not -12.0 <= v <= 14.0:
            raise ValueError("timezone must be between -12 and +14 hours")
        return v

class MuhurtaRequest(BaseModel):
    date: str  # YYYY-MM-DD
    latitude: float
    longitude: float
    timezone: float
    city: Optional[str] = None
    timezone_id: Optional[str] = None

    @field_validator("date")
    @classmethod
    def _check_date(cls, v):
        return _validate_birth_date(v)

    @field_validator("latitude")
    @classmethod
    def _check_latitude(cls, v):
        if not -90.0 <= v <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def _check_longitude(cls, v):
        if not -180.0 <= v <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return v

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, v):
        if not -12.0 <= v <= 14.0:
            raise ValueError("timezone must be between -12 and +14 hours")
        return v

# --- Astrological Calculations & Helpers ---

LAGNA_PLANET_RELATIONS = {
    1: { # Aries / Mesha
        "karaka": ["Sun", "Jupiter", "Mars"],
        "maraka": ["Mercury", "Venus", "Saturn", "Rahu", "Ketu"],
        "sama": ["Moon"]
    },
    2: { # Taurus / Vrisha
        "karaka": ["Sun", "Mercury", "Saturn", "Venus"],
        "maraka": ["Moon", "Mars", "Jupiter", "Rahu", "Ketu"],
        "sama": []
    },
    3: { # Gemini / Mithuna
        "karaka": ["Mercury", "Venus"],
        "maraka": ["Sun", "Mars", "Jupiter", "Rahu", "Ketu"],
        "sama": ["Moon", "Saturn"]
    },
    4: { # Cancer / Karka
        "karaka": ["Moon", "Mars", "Jupiter"],
        "maraka": ["Mercury", "Venus", "Saturn", "Rahu", "Ketu"],
        "sama": ["Sun"]
    },
    5: { # Leo / Simha
        "karaka": ["Sun", "Mars", "Jupiter"],
        "maraka": ["Mercury", "Venus", "Saturn", "Rahu", "Ketu"],
        "sama": ["Moon"]
    },
    6: { # Virgo / Kanya
        "karaka": ["Mercury", "Venus"],
        "maraka": ["Moon", "Mars", "Jupiter", "Rahu", "Ketu"],
        "sama": ["Sun", "Saturn"]
    },
    7: { # Libra / Tula
        "karaka": ["Venus", "Mercury", "Saturn"],
        "maraka": ["Sun", "Mars", "Jupiter", "Rahu", "Ketu"],
        "sama": ["Moon"]
    },
    8: { # Scorpio / Vrishchika
        "karaka": ["Mars", "Moon", "Sun", "Jupiter"],
        "maraka": ["Mercury", "Venus", "Rahu", "Ketu"],
        "sama": ["Saturn"]
    },
    9: { # Sagittarius / Dhanu
        "karaka": ["Jupiter", "Sun", "Mars"],
        "maraka": ["Mercury", "Venus", "Rahu", "Ketu"],
        "sama": ["Moon", "Saturn"]
    },
    10: { # Capricorn / Makara
        "karaka": ["Saturn", "Mercury", "Venus"],
        "maraka": ["Sun", "Mars", "Jupiter", "Rahu", "Ketu"],
        "sama": ["Moon"]
    },
    11: { # Aquarius / Kumbha
        "karaka": ["Saturn", "Venus", "Mercury"],
        "maraka": ["Sun", "Mars", "Jupiter", "Rahu", "Ketu"],
        "sama": ["Moon"]
    },
    12: { # Pisces / Mina
        "karaka": ["Jupiter", "Moon", "Mars"],
        "maraka": ["Sun", "Mercury", "Venus", "Saturn", "Rahu", "Ketu"],
        "sama": []
    }
}

def is_planet_retrograde(planet_name: str, T: float) -> bool:
    if planet_name in ["Sun", "Moon"]:
        return False
    if planet_name in ["Rahu", "Ketu"]:
        return True
    lon1, _ = planetary_positions.get_geocentric_coordinates(planet_name, T)
    dT = 1e-6
    lon2, _ = planetary_positions.get_geocentric_coordinates(planet_name, T + dT)
    diff = (lon2 - lon1 + 180) % 360 - 180
    return diff < 0

def is_planet_combust(planet_name: str, T: float, is_retrograde: bool) -> bool:
    if planet_name in ["Sun", "Rahu", "Ketu"]:
        return False
    sun_lon = planetary_positions.get_sun_position(T)[0]
    if planet_name == "Moon":
        lon = planetary_positions.get_moon_position(T)[0]
    else:
        lon = planetary_positions.get_geocentric_coordinates(planet_name, T)[0]
    diff = abs((lon - sun_lon + 180) % 360 - 180)
    limits = {
        "Moon": 12.0,
        "Mars": 17.0,
        "Mercury": 12.0 if is_retrograde else 14.0,
        "Jupiter": 11.0,
        "Venus": 8.0 if is_retrograde else 10.0,
        "Saturn": 15.0
    }
    return diff <= limits.get(planet_name, 0.0)

def get_planet_relationship(planet_name: str, lagna_sign: int) -> str:
    relations = LAGNA_PLANET_RELATIONS.get(lagna_sign, {})
    if planet_name in relations.get("karaka", []):
        return "karaka"
    elif planet_name in relations.get("maraka", []):
        return "maraka"
    else:
        return "sama"

def get_planet_exaltation_debilitation(planet_name: str, sign_number: int) -> str:
    exaltation_signs = {
        "Sun": 1,      # Aries
        "Moon": 2,     # Taurus
        "Mars": 10,    # Capricorn
        "Mercury": 6,  # Virgo
        "Jupiter": 4,  # Cancer
        "Venus": 12,   # Pisces
        "Saturn": 7,   # Libra
        "Rahu": 2,     # Taurus
        "Ketu": 8      # Scorpio
    }
    debilitation_signs = {
        "Sun": 7,      # Libra
        "Moon": 8,     # Scorpio
        "Mars": 4,     # Cancer
        "Mercury": 12, # Pisces
        "Jupiter": 10, # Capricorn
        "Venus": 6,    # Virgo
        "Saturn": 1,   # Aries
        "Rahu": 8,     # Scorpio
        "Ketu": 2      # Taurus
    }
    if exaltation_signs.get(planet_name) == sign_number:
        return "exalted"
    elif debilitation_signs.get(planet_name) == sign_number:
        return "debilitated"
    return ""

# --- Calculation Logic Wrapper ---

def perform_calculations(
    name: str,
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: float,
    ayanamsha_type: str,
    city: Optional[str] = None,
    timezone_id: Optional[str] = None,
    node_type: str = "MEAN",
    house_system: str = "WHOLE_SIGN",
    calculation_siddhanta: str = "DRIK",
    include_yogini_tree: bool = True,
    include_comprehensive_book: bool = True,
) -> Dict[str, Any]:
    
    # 1. Parse hour, minute, second from time string.
    # Validation is enforced at the schema layer; here we fail loudly rather
    # than silently substituting noon, which would produce a wrong chart.
    try:
        h, m, s = map(float, birth_time.split(":"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            f"birth_time must be HH:MM or HH:MM:SS (got {birth_time!r})"
        ) from exc

    try:
        y, month, d = map(int, birth_date.split("-"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            f"birth_date must be YYYY-MM-DD (got {birth_date!r})"
        ) from exc
    
    # 2. Resolve historical civil offset when an IANA zone is available.
    # Keep the supplied numeric offset as the compatibility fallback.
    timezone_info = timezone_resolver.resolve_timezone(
        birth_date, birth_time, timezone, timezone_id=timezone_id, city=city
    )
    timezone = timezone_info["timezone"]

    # 3. Get Julian Date and Julian Centuries
    jd = julian.datetime_to_jd(y, month, d, int(h), int(m), s, timezone)
    panchang_jd = julian.datetime_to_jd(y, month, d, 12, 0, 0, timezone)
    T = julian.jd_to_julian_centuries(jd)
    
    # 4. Calculate Ayanamsha value
    aya_val = ayanamsha.get_ayanamsha(ayanamsha_type, T)
    
    # 4. Calculate Lagna (Ascendant)
    lagna_tropical = houses.calculate_lagna(jd, latitude, longitude)
    lagna_sidereal = ayanamsha.convert_tropical_to_sidereal(lagna_tropical, aya_val)
    lagna_sign_num, lagna_sign_name = houses.get_zodiac_sign(lagna_sidereal)
    lagna_deg = lagna_sidereal % 30.0
    
    # 5. Calculate Planetary positions
    tropical_positions = planetary_positions.get_all_tropical_positions(T, jd=jd, node_type=node_type)
    sidereal_positions = {}
    planets_data = []
    
    # Standard list of planets for sorting
    planet_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron", "Rahu", "Ketu"]
    
    ss_positions = (
        surya_siddhanta.all_sidereal_positions(jd, longitude)
        if calculation_siddhanta == "SURYA_SIDDHANTA"
        else {}
    )

    for name_key in planet_order:
        if name_key not in tropical_positions:
            continue
        trop_long, trop_lat = tropical_positions[name_key]
        if calculation_siddhanta == "SURYA_SIDDHANTA" and name_key in ss_positions:
            sid_long = ss_positions[name_key]
        else:
            sid_long = ayanamsha.convert_tropical_to_sidereal(trop_long, aya_val)
        sidereal_positions[name_key] = sid_long
        
        sign_num, sign_name = houses.get_zodiac_sign(sid_long)
        long_in_sign = sid_long % 30.0
        
        if name_key in {"Uranus", "Neptune", "Pluto", "Chiron"}:
            probe = planetary_positions.get_swiss_positions(jd + 1.0 / 24.0, node_type)
            next_long = probe.get(name_key, (trop_long, 0.0))[0] if probe else trop_long
            is_retro = (next_long - trop_long + 180.0) % 360.0 - 180.0 < 0.0
        else:
            is_retro = is_planet_retrograde(name_key, T)
        is_comb = is_planet_combust(name_key, T, is_retro)
        rel = get_planet_relationship(name_key, lagna_sign_num)
        exalt = get_planet_exaltation_debilitation(name_key, sign_num)
        
        # Nakshatra (sidereal position divided into 27 segments of 13°20')
        _nak_idx = int(sid_long / (360.0 / 27.0)) % 27
        _nak_pada = int((sid_long % (360.0 / 27.0)) / (360.0 / 27.0 / 4.0)) + 1
        _nak_obj = panchang.NAKSHATRAS[_nak_idx]
        # Nakshatra lords follow Vimshottari sequence (same as dasha lords)
        _NAK_LORDS = [
            "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
            "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
            "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
        ]
        planets_data.append({
            "name": name_key,
            "tropical_longitude": trop_long,
            "sidereal_longitude": sid_long,
            "sign_number": sign_num,
            "sign_name": sign_name,
            "longitude_in_sign": long_in_sign,
            "latitude": trop_lat,
            "is_retrograde": is_retro,
            "is_combust": is_comb,
            "relationship": rel,
            "exaltation_state": exalt,
            "nakshatra_index": _nak_idx,
            "nakshatra_name": _nak_obj["name"],
            "nakshatra_nepali": _nak_obj["nepali"],
            "nakshatra_pada": _nak_pada,
            "nakshatra_lord": _NAK_LORDS[_nak_idx],
            # Vargottama: D1 == D9 sign (BPHS Brihat Parashar Hora Shastra, Ch.27).
            # A Vargottama planet has maximum natural strength — equivalent to own sign.
            # Computed once here and injected into every planet dict for all GUI widgets.
            "is_vargottama": vargas.is_vargottama(sid_long),
        })
        
    # 6. House placements. Keep legacy rashi-house in `house`; expose Chalit separately.
    house_placements = houses.get_house_placements(sidereal_positions, lagna_sidereal)
    tropical_cusps = houses.calculate_house_cusps(jd, latitude, longitude, house_system)
    sidereal_cusps = [ayanamsha.convert_tropical_to_sidereal(value, aya_val) for value in tropical_cusps]
    bhava_placements = houses.get_bhava_chalit_placements(sidereal_positions, sidereal_cusps)
    for p in planets_data:
        p["house"] = house_placements[p["name"]]
        p["bhava_house"] = bhava_placements[p["name"]]
        
    # 7. Panchang Calculations
    # The birth chart report should be clearly tied to the birth-time reference,
    # while the requested-day context can be computed separately for comparison.
    sun_sid = sidereal_positions["Sun"]
    moon_sid = sidereal_positions["Moon"]
    birth_sun_sid, birth_moon_sid = panchang._sidereal_longitudes(
        jd, ayanamsha_type, calculation_mode=calculation_siddhanta
    )
    ad_date = datetime.date(y, month, d)
    bs_date = nepali_datetime.date.from_datetime_date(ad_date)

    birth_sunrise_jd = panchang.calculate_sunrise_jd(
        jd, latitude, longitude, timezone, calculation_mode=calculation_siddhanta
    )
    sunrise_sun_sid, sunrise_moon_sid = panchang._sidereal_longitudes(
        birth_sunrise_jd, ayanamsha_type, calculation_mode=calculation_siddhanta
    )
    panchang_birth_time = panchang.calculate_panchang(
        birth_sunrise_jd,
        sunrise_sun_sid,
        sunrise_moon_sid,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        bs_year=bs_date.year,
        bs_month=bs_date.month,
        sunrise_jd=birth_sunrise_jd,
        ayanamsha_type=ayanamsha_type,
        calculation_mode=calculation_siddhanta,
    )

    # ── Standard NST Daily Panchang (Kathmandu meridian, independent of birth city) ──
    # Nepali Patro always publishes transitions referenced to the Kathmandu standard
    # meridian (85.3240° E, NST +5:45), regardless of the person's birth location.
    # Compute the requested-day panchang at Kathmandu so it exactly matches Patro.
    _KTM_LAT, _KTM_LON, _KTM_TZ = 27.7172, 85.3240, 5.75
    if abs(latitude - _KTM_LAT) < 0.02 and abs(longitude - _KTM_LON) < 0.02:
        # Birth is already Kathmandu; reuse the computation above (0 extra cost).
        panchang_requested_day = deepcopy(panchang_birth_time)
    else:
        ktm_sunrise_jd = panchang.calculate_sunrise_jd(
            jd, _KTM_LAT, _KTM_LON, _KTM_TZ, calculation_mode=calculation_siddhanta
        )
        ktm_sun_sid, ktm_moon_sid = panchang._sidereal_longitudes(
            ktm_sunrise_jd, ayanamsha_type, calculation_mode=calculation_siddhanta
        )
        panchang_requested_day = panchang.calculate_panchang(
            ktm_sunrise_jd,
            ktm_sun_sid,
            ktm_moon_sid,
            latitude=_KTM_LAT,
            longitude=_KTM_LON,
            timezone=_KTM_TZ,
            bs_year=bs_date.year,
            bs_month=bs_date.month,
            sunrise_jd=ktm_sunrise_jd,
            ayanamsha_type=ayanamsha_type,
            calculation_mode=calculation_siddhanta,
        )

    # A birth report needs both references: the limb at local sunrise and the
    # limb at the exact birth instant.  calculate_panchang() intentionally
    # returns the sunrise values used by a daily Panchang; derive all four
    # birth-time limbs from the same continuous longitude model here.
    birth_phase = (birth_moon_sid - birth_sun_sid) % 360.0
    birth_tithi_idx = int(birth_phase / 12.0) % 30
    birth_nakshatra_idx = int(birth_moon_sid / (360.0 / 27.0)) % 27
    birth_yoga_idx = int(((birth_sun_sid + birth_moon_sid) % 360.0) / (360.0 / 27.0)) % 27
    birth_karana_idx = int(birth_phase / 6.0) % 60

    panchang_context = {
        "report_type": "birth_time",
        "reference_date": birth_date,
        "reference_time": birth_time,
        "label_ne": "जन्म समय",
        "label_en": "Birth time",
        "description_ne": "यो पञ्चाङ्ग जन्म समयको आधारमा गणना गरिएको छ।",
        "description_en": "This Panchang is calculated from the birth time."
    }

    # Birth-chart nakshatra MUST be derived from the Moon's position at the
    # exact birth moment — NOT from the sunrise-based panchang nakshatra.
    # The panchang nakshatra is the one present at sunrise (the "nakshatra of
    # the day"), which is correct for a daily panchang but WRONG for a birth
    # chart: the Moon moves ~13°/day, so a night birth can be 1–2 padas (or
    # even a whole nakshatra) away from the sunrise value. PL7 and all
    # standard software use the birth-time Moon for the avakahada chakra.
    nak_val = birth_moon_sid / 13.3333333
    nakshatra_index = int(nak_val) % 27
    nak_progress = nak_val - int(nak_val)
    pada = int(nak_progress * 4) + 1
    birth_nakshatra = panchang.NAKSHATRAS[nakshatra_index]
    nakshatra_name = birth_nakshatra.get("nepali") or birth_nakshatra.get("name")

    # Nakshatra end-time measured from the BIRTH moment (when the Moon next
    # crosses a 13°20' boundary). This is what a birth-chart report shows.
    birth_nak_end_jd = panchang._find_next_index_change(
        jd, nakshatra_index, panchang._nakshatra_idx_at, ayanamsha_type,
        calculation_mode=calculation_siddhanta
    )
    birth_nak_end_time = ""
    if birth_nak_end_jd:
        # Local HH:MM relative to the birth-date midnight.
        utc_hours_of_birth = ((jd + 0.5) % 1.0) * 24.0
        local_hours_of_birth = (utc_hours_of_birth + timezone) % 24.0
        midnight_local_jd = jd - local_hours_of_birth / 24.0
        birth_nak_end_time = panchang._jd_to_local_hhmm_panchang(
            birth_nak_end_jd, midnight_local_jd, timezone
        )

    avakahada_chakra = calculate_avakahada_chakra(nakshatra_index, pada, nakshatra_name=nakshatra_name)
    avakahada_chakra["nakshatra_end_time"] = birth_nak_end_time
    avakahada_chakra["nakshatra_reference"] = "birth_time"

    # Keep the birth-time panchang's nakshatra consistent with the birth-time
    # Moon (the sunrise-based value is the "nakshatra of the day" and is left
    # available on the requested-day panchang). The birth chart must show the
    # nakshatra actually occupied by the Moon at the moment of birth.
    next_nak_obj = panchang.NAKSHATRAS[(nakshatra_index + 1) % 27]
    panchang_birth_time["nakshatra"] = {
        **panchang_birth_time.get("nakshatra", {}),
        "index": nakshatra_index,
        "pada": pada,
        "name": birth_nakshatra.get("name"),
        "nepali": birth_nakshatra.get("nepali"),
        "next_name": next_nak_obj.get("name"),
        "next_nepali": next_nak_obj.get("nepali"),
        "end_time": birth_nak_end_time,
        "reference": "birth_time",
    }

    def _karana_for_index(idx60: int) -> Dict[str, Any]:
        if idx60 == 0:
            return panchang.KARANAS[10]
        if 1 <= idx60 <= 57:
            return panchang.KARANAS[(idx60 - 1) % 7]
        if idx60 == 58:
            return panchang.KARANAS[7]
        if idx60 == 59:
            return panchang.KARANAS[8]
        return panchang.KARANAS[9]

    birth_tithi = panchang.TITHIS[birth_tithi_idx]
    birth_yoga = panchang.YOGAS[birth_yoga_idx]
    birth_karana = _karana_for_index(birth_karana_idx)
    panchang_birth_time["tithi"]["birth_name"] = birth_tithi["name"]
    panchang_birth_time["tithi"]["birth_nepali"] = birth_tithi["nepali"]
    panchang_birth_time["tithi"]["birth_index"] = birth_tithi_idx + 1
    panchang_birth_time["yoga"]["birth_name"] = birth_yoga["name"]
    panchang_birth_time["yoga"]["birth_nepali"] = birth_yoga["nepali"]
    panchang_birth_time["yoga"]["birth_index"] = birth_yoga_idx + 1
    panchang_birth_time["karana"]["birth_name"] = birth_karana["name"]
    panchang_birth_time["karana"]["birth_nepali"] = birth_karana["nepali"]
    panchang_birth_time["karana"]["birth_index"] = birth_karana_idx + 1

    panchang_requested_day_context = {
        "report_type": "requested_day",
        "reference_date": birth_date,
        "reference_time": "12:00:00",
        "label_ne": "माग गरिएको दिन/समय",
        "label_en": "Requested day/time",
        "description_ne": "यो पञ्चाङ्ग माग गरिएको दिनको आधारमा (स्थानीय मध्यान्ह) गणना गरिएको छ।",
        "description_en": "This Panchang is calculated for the requested day at local noon."
    }
    
    # 8. Dasha Calculations
    dasha_data = dasha.calculate_vimshottari_dasha(moon_sid, birth_date, birth_time)
    tribhagi_dasha_data = dasha.calculate_tribhagi_dasha(moon_sid, birth_date, birth_time)
    # BPHS 32.27: Ashtottari starts from Ardra when a graha occupies the Lagna,
    # otherwise from Krittika.  Only the nine traditional grahas are counted.
    traditional_names = {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
    }
    lagna_occupied = any(
        planet.get("name") in traditional_names
        and planet.get("sign_number") == lagna_sign_num
        for planet in planets_data
    )
    ashtottari_dasha_data = dasha.calculate_ashtottari_dasha(
        moon_sid, birth_date, birth_time, lagna_occupied=lagna_occupied
    )

    # 9. Yogini Dasha Calculations
    yogini_dasha_data = yogini.calculate_yogini_dasha(moon_sid, birth_date, birth_time)
    if include_yogini_tree:
        yogini_five_level_data = yogini.calculate_yogini_dasha_five_level(
            moon_sid, birth_date, birth_time
        )
        yogini_report = report_from_tree("yogini", yogini_five_level_data)
    else:
        # The five-level Yogini tree is ~20k nodes / several MB of JSON.  The
        # native desktop shell asks for it only when the Dasha page is opened.
        yogini_five_level_data = None
        yogini_report = unavailable_report(
            "yogini",
            "The five-level Yogini tree is calculated on demand by the desktop app.",
        )
        yogini_report["deferred"] = True

    # Additive normalized reports for the unified desktop/web presentation. The
    # legacy fields above intentionally remain untouched for compatibility.
    dasha_reports = {
        "vimshottari": report_from_tree("vimshottari", dasha_data),
        "tribhagi": report_from_tree("tribhagi", tribhagi_dasha_data),
        "ashtottari": report_from_tree("ashtottari", ashtottari_dasha_data),
        "yogini": yogini_report,
    }

    # 10. Parashara Yoga Detection (with structured detector diagnostics)
    parashara_yogas, yoga_diagnostics = yogas.calculate_parashara_yogas_with_diagnostics(
        planets_data, lagna_sign_num
    )
    
    vargas_data = vargas.calculate_varga_positions(lagna_sidereal, planets_data)

    special_tropical = special_points.calculate_special_lagnas(jd, latitude, longitude, timezone, tropical_positions["Sun"][0])
    upagraha_tropical = special_points.calculate_upagrahas(jd, latitude, longitude, timezone)
    special_lagnas = {key: ayanamsha.convert_tropical_to_sidereal(value, aya_val) for key, value in special_tropical.items()}
    upagrahas = {key: ayanamsha.convert_tropical_to_sidereal(value, aya_val) for key, value in upagraha_tropical.items()}

    # Ashtakavarga (Parashari) — relative-distance BAV/SAV with 337 invariant.
    ashtakavarga_data = ashtakavarga_calc.compute_samudaya_ashtakavarga(planets_data, lagna_sign_num)

    # Vimshopaka Bala — Shodashavarga weighted strength, out of 20.
    # Calculated in the engine so the desktop page never invents a score.
    vimshopaka_data = vimshopaka_calc.calculate_vimshopaka_bala(planets_data)

    # Shadbala — classical six-fold strength in Shashtiamsa/Rupa units.
    local_weekday = int(jd + timezone / 24.0 + 1.5) % 7
    sun_times = panchang.calculate_sunrise_sunset(jd, latitude, longitude, timezone)
    sunset_h, sunset_m = (int(part) for part in sun_times["sunset"].split(":"))
    local_midnight_jd = math.floor(jd + timezone / 24.0 - 0.5) + 0.5 - timezone / 24.0
    sunset_jd = local_midnight_jd + (sunset_h + sunset_m / 60.0) / 24.0
    shadbala_data = shadbala_calc.calculate_shadbala(
        planets_data,
        lagna_sign_num,
        jd=jd,
        sunrise_jd=birth_sunrise_jd,
        sunset_jd=sunset_jd,
        weekday=local_weekday,
    )

    # Planetary Avasthas (age + dignity/deeptadi states).
    avasthas_data = avasthas_calc.calculate_avasthas(planets_data, lagna_sign_num)

    # Phase 3 engines are additive and do not alter any legacy chart result.
    current_year = datetime.date.today().year
    varshaphala_data = varshaphala.calculate_varshaphala(
        tropical_positions["Sun"][0], planets_data, lagna_sidereal, current_year,
        return_jd=jd + (current_year - y) * varshaphala.SOLAR_YEAR,
    )
    jaimini_data = jaimini.calculate_jaimini(planets_data, lagna_sign_num, y)
    kp_data = kp_system.calculate_kp_system(jd, latitude, longitude, aya_val, planets_data)

    # Kaal Sarp Dosha — all seven grahas hemmed between Rahu and Ketu.
    kaal_sarp_data = kaal_sarp_dosha_calc.calculate_kaal_sarp_dosha(
        planets_data, lagna_sign_num, language="ne"
    )

    # Lal Kitab — 35-year cycle, planet status and traditional remedies.
    lal_kitab_data = lal_kitab_calc.calculate_lal_kitab_data(
        planets_data, lagna_sign_num, birth_date
    )

    # Vedic Gemstones, Rudraksha and Remedies
    remedies_data = remedies_calc.calculate_remedies(
        planets_data, lagna_sign_num, dasha_data=dasha_data, language="ne"
    )

    metadata = {
            "name": name,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "timezone_id": timezone_info["timezone_id"],
            "standard_timezone": timezone_info["standard_timezone"],
            "dst_offset": timezone_info["dst_offset"],
            "is_dst": timezone_info["is_dst"],
            "timezone_source": timezone_info["timezone_source"],
            "timezone_resolution": timezone_info["timezone_resolution"],
            "ayanamsha_type": ayanamsha_type,
            "ayanamsha_value": aya_val,
            "node_type": node_type,
            "house_system": house_system,
            "ephemeris": "SWISS" if planetary_positions.swe is not None else "ANALYTICAL_FALLBACK",
            # Additive provenance detail: exact ephemeris build behind the positions.
            "ephemeris_version": planetary_positions.get_ephemeris_version(),
            "julian_date": jd,
            # Version calculation output so saved reports remain auditable when
            # formulas evolve in future releases.
            "calculation_version": settings.CALCULATION_VERSION,
        }
    if city:
        metadata["city"] = city

    result_payload = {
        "metadata": metadata,
        "lagna": {
            "longitude": lagna_sidereal,
            "sign_number": lagna_sign_num,
            "sign_name": lagna_sign_name,
            "longitude_in_sign": lagna_deg
        },
        "planets": planets_data,
        "houses": {
            "system": house_system,
            "cusps": sidereal_cusps,
            "boundaries": houses.calculate_bhava_boundaries(sidereal_cusps),
            "placements": bhava_placements,
        },
        "special_lagnas": special_lagnas,
        "upagrahas": upagrahas,
        "panchang": panchang_birth_time,
        "panchang_context": panchang_context,
        "panchang_requested_day": {
            **panchang_requested_day_context,
            "panchang": panchang_requested_day,
        },
        "avakahada_chakra": avakahada_chakra,
        "dasha": dasha_data,
        "tribhagi_dasha": tribhagi_dasha_data,
        "yogini_dasha": yogini_dasha_data,
        "yogini_dasha_five_level": yogini_five_level_data,
        "ashtottari_dasha": ashtottari_dasha_data,
        "dasha_reports": dasha_reports,
        "parashara_yogas": parashara_yogas,
        # Additive detector audit trail: empty list means every yoga detector
        # ran cleanly. Non-empty entries identify which detector failed and
        # why, so a missing yoga is never silently hidden from the user.
        "yoga_diagnostics": yoga_diagnostics,
        "vargas": vargas_data,
        "ashtakavarga": ashtakavarga_data,
        "shadbala": shadbala_data,
        "vimshopaka_bala": vimshopaka_data,
        "avasthas": avasthas_data,
        "varshaphala": varshaphala_data,
        "jaimini": jaimini_data,
        "kp_system": kp_data,
        "kaal_sarp_dosha": kaal_sarp_data,
        "lal_kitab": lal_kitab_data,
        "remedies": remedies_data
    }

    # Add comprehensive 50+ page book generator model. The web proxy strips it
    # from responses, so it can be skipped entirely for browser requests.
    if include_comprehensive_book:
        result_payload["comprehensive_book"] = build_comprehensive_kundali_book(
            result_payload, language="ne"
        )

    return result_payload

# --- Route Handlers ---

@router.post("/calculate")
@limiter.limit(settings.CALCULATE_RATE_LIMIT)
def calculate_chart(request: Request, req: ChartRequest):
    try:
        results = perform_calculations(
            name=req.name,
            birth_date=req.birth_date,
            birth_time=req.birth_time,
            latitude=req.latitude,
            longitude=req.longitude,
            timezone=req.timezone,
            ayanamsha_type=req.ayanamsha_type,
            city=req.city,
            timezone_id=req.timezone_id,
            node_type=req.node_type,
            house_system=req.house_system,
            include_yogini_tree=req.include_yogini_tree,
            include_comprehensive_book=req.include_comprehensive_book,
        )
        return results
    except ValueError as e:
        # Input-level problems surfaced from perform_calculations.
        raise HTTPException(status_code=422, detail=f"Validation Error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation Error: {str(e)}")

@router.get("/transits/planetary-transition-window")
def get_planetary_transition_window(
    planet: str,
    reference_date: Optional[str] = None,
    before: int = 3,
    after: int = 3,
    ayanamsha_type: str = "LAHIRI",
    node_type: str = "MEAN",
):
    """Return a lazy, per-planet transition window around a dynamic reference date."""
    try:
        reference = datetime.date.fromisoformat(reference_date) if reference_date else datetime.date.today()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="reference_date must be a valid YYYY-MM-DD date") from exc
    try:
        validated_ayanamsha = _validate_ayanamsha(ayanamsha_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    validated_node = str(node_type).upper()
    if validated_node not in SUPPORTED_NODE_TYPES:
        raise HTTPException(status_code=422, detail="node_type must be MEAN or TRUE")
    try:
        return planetary_ingress.calculate_planetary_transition_window(
            reference_date=reference,
            planet=planet,
            before=before,
            after=after,
            ayanamsha_type=validated_ayanamsha,
            node_type=validated_node,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Transit Calculation Error: {str(exc)}") from exc


@router.get("/transits/planetary-ingresses")
def get_planetary_ingresses(
    start_date: Optional[str] = None,
    years: int = 5,
    ayanamsha_type: str = "LAHIRI",
    node_type: str = "MEAN",
):
    """Return chart-independent sidereal sign ingresses in Nepal time."""
    try:
        start = datetime.date.fromisoformat(start_date) if start_date else datetime.date.today()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="start_date must be a valid YYYY-MM-DD date") from exc
    if not 1 <= years <= 5:
        raise HTTPException(status_code=422, detail="years must be between 1 and 5")
    try:
        validated_ayanamsha = _validate_ayanamsha(ayanamsha_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    validated_node = str(node_type).upper()
    if validated_node not in SUPPORTED_NODE_TYPES:
        raise HTTPException(status_code=422, detail="node_type must be MEAN or TRUE")
    try:
        end = start.replace(year=start.year + years)
    except ValueError:
        end = start.replace(year=start.year + years, day=28)
    try:
        return planetary_ingress.calculate_planetary_ingresses(
            start_date=start,
            end_date=end,
            ayanamsha_type=validated_ayanamsha,
            node_type=validated_node,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Transit Calculation Error: {str(exc)}") from exc


@router.get("/records", response_model=List[RecordResponse])
def get_records(db: Session = Depends(get_db)):
    """Return every saved record stored on this machine (newest first)."""
    return (
        db.query(models.KundaliRecord)
        .order_by(models.KundaliRecord.created_at.desc())
        .all()
    )

@router.post("/records", response_model=RecordResponse)
def save_record(
    record: RecordCreate,
    db: Session = Depends(get_db),
):
    existing_record = db.query(models.KundaliRecord).filter(
        models.KundaliRecord.name == record.name,
        models.KundaliRecord.birth_date == record.birth_date,
        models.KundaliRecord.birth_time == record.birth_time,
        models.KundaliRecord.latitude == record.latitude,
        models.KundaliRecord.longitude == record.longitude,
        models.KundaliRecord.timezone == record.timezone,
        models.KundaliRecord.gender == record.gender,
    ).first()

    detail_fields = tuple(JANMAPATRIKA_TEXT_LIMITS.keys())
    if existing_record:
        changed = False
        for field_name in (*detail_fields, "notes"):
            value = getattr(record, field_name, None)
            if value is not None and getattr(existing_record, field_name, None) != value:
                setattr(existing_record, field_name, value)
                changed = True
        if changed:
            db.commit()
            db.refresh(existing_record)
        return existing_record

    detail_values = {field_name: getattr(record, field_name, None) for field_name in detail_fields}
    db_record = models.KundaliRecord(
        name=record.name,
        birth_date=record.birth_date,
        birth_time=record.birth_time,
        latitude=record.latitude,
        longitude=record.longitude,
        timezone=record.timezone,
        gender=record.gender,
        notes=record.notes,
        user_id=None,
        **detail_values,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.put("/records/{record_id}", response_model=RecordResponse)
def update_record(
    record_id: int,
    record: RecordCreate,
    db: Session = Depends(get_db),
):
    db_record = (
        db.query(models.KundaliRecord)
        .filter(models.KundaliRecord.id == record_id)
        .first()
    )
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")

    _replace_record_fields(db_record, record)

    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/local-records", response_model=List[RecordResponse])
def get_local_records(db: Session = Depends(get_db)):
    """Return records owned by this local installation."""
    return (
        db.query(models.KundaliRecord)
        .filter(models.KundaliRecord.user_id.is_(None))
        .order_by(models.KundaliRecord.created_at.desc(), models.KundaliRecord.id.desc())
        .all()
    )


@router.post("/local-records", response_model=RecordResponse, status_code=201)
def create_local_record(record: RecordCreate, db: Session = Depends(get_db)):
    """Persist birth input in the installation's private SQLite database."""
    db_record = models.KundaliRecord(user_id=None)
    _replace_record_fields(db_record, record)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.put("/local-records/{record_id}", response_model=RecordResponse)
def update_local_record(
    record_id: int,
    record: RecordCreate,
    db: Session = Depends(get_db),
):
    """Replace one local record in place, preserving its stable database ID."""
    db_record = (
        db.query(models.KundaliRecord)
        .filter(
            models.KundaliRecord.id == record_id,
            models.KundaliRecord.user_id.is_(None),
        )
        .first()
    )
    if not db_record:
        raise HTTPException(status_code=404, detail="Local record not found")
    _replace_record_fields(db_record, record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.delete("/local-records/{record_id}")
def delete_local_record(record_id: int, db: Session = Depends(get_db)):
    """Delete one record belonging to this local installation."""
    db_record = (
        db.query(models.KundaliRecord)
        .filter(
            models.KundaliRecord.id == record_id,
            models.KundaliRecord.user_id.is_(None),
        )
        .first()
    )
    if not db_record:
        raise HTTPException(status_code=404, detail="Local record not found")
    db.delete(db_record)
    db.commit()
    return {"message": "Local record deleted successfully"}


@router.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    db_record = (
        db.query(models.KundaliRecord)
        .filter(models.KundaliRecord.id == record_id)
        .first()
    )
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(db_record)
    db.commit()
    return {"message": "Record deleted successfully"}

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    db_settings = (
        db.query(models.Settings)
        .filter(models.Settings.user_id.is_(None))
        .first()
    )
    if not db_settings:
        db_settings = models.Settings(
            user_id=None,
            ayanamsha_type="LAHIRI",
            chart_style="NORTH_INDIAN",
            language="ne",
        )
        db.add(db_settings)
        db.commit()
        db.refresh(db_settings)
    return db_settings

@router.post("/settings")
def update_settings(
    settings: SettingsUpdate,
    db: Session = Depends(get_db),
):
    db_settings = (
        db.query(models.Settings)
        .filter(models.Settings.user_id.is_(None))
        .first()
    )
    if not db_settings:
        db_settings = models.Settings(user_id=None)
        db.add(db_settings)
    db_settings.ayanamsha_type = settings.ayanamsha_type
    db_settings.chart_style = settings.chart_style
    db_settings.language = settings.language
    db.commit()
    db.refresh(db_settings)
    return db_settings

@router.get("/cities/search")
def search_cities(q: str = "", limit: int = 20):
    """Search the curated offline city dataset with IANA timezone metadata."""
    return timezone_resolver.search_cities(q, limit)

@router.get("/cities/hierarchy")
def city_hierarchy():
    """Return the offline country → region → district → city hierarchy.

    The same district metadata powers both the desktop GUI and the web form,
    so a selected district always supplies its reference coordinates instead
    of trusting free-text latitude/longitude entry.
    """
    return build_location_hierarchy()

@router.get("/convert/bs-to-ad")
def convert_bs_to_ad(year: int, month: int, day: int):
    try:
        bs_date = nepali_datetime.date(year, month, day)
        ad_date = bs_date.to_datetime_date()
        return {"ad_date": ad_date.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"BS to AD conversion failed: {str(e)}")

@router.get("/convert/ad-to-bs")
def convert_ad_to_bs(date: str):
    try:
        # date format: YYYY-MM-DD
        ad_dt = datetime.date.fromisoformat(date)
        bs_date = nepali_datetime.date.from_datetime_date(ad_dt)
        return {
            "bs_date": f"{bs_date.year}-{bs_date.month:02d}-{bs_date.day:02d}",
            "year": bs_date.year,
            "month": bs_date.month,
            "day": bs_date.day
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AD to BS conversion failed: {str(e)}")

@router.post("/marriage-match")
@limiter.limit(settings.CALCULATE_RATE_LIMIT)
def calculate_marriage_match(request: Request, req: MarriageMatchRequest):
    try:
        # Calculate boy's chart
        boy_chart = perform_calculations(
            name=req.boy_name,
            birth_date=req.boy_birth_date,
            birth_time=req.boy_birth_time,
            latitude=req.boy_latitude,
            longitude=req.boy_longitude,
            timezone=req.boy_timezone,
            ayanamsha_type=req.boy_ayanamsha_type,
            city=req.boy_city,
            timezone_id=req.boy_timezone_id,
        )

        # Calculate girl's chart
        girl_chart = perform_calculations(
            name=req.girl_name,
            birth_date=req.girl_birth_date,
            birth_time=req.girl_birth_time,
            latitude=req.girl_latitude,
            longitude=req.girl_longitude,
            timezone=req.girl_timezone,
            ayanamsha_type=req.girl_ayanamsha_type,
            city=req.girl_city,
            timezone_id=req.girl_timezone_id,
        )

        # Calculate compatibility
        compatibility = marriage_matching.calculate_compatibility(boy_chart, girl_chart)

        return {
            "boy_chart": boy_chart,
            "girl_chart": girl_chart,
            "compatibility": compatibility
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation Error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Marriage matching calculation error: {str(e)}")


@router.post("/prashna")
@limiter.limit(settings.CALCULATE_RATE_LIMIT)
def calculate_prashna(request: Request, req: PrashnaRequest):
    """Cast a Prashna (horary) chart for the moment the question is asked.

    The chart is computed for the question's date/time and location using the
    same calculation engine as a natal chart, then annotated with the question
    metadata so the frontend can render a Prashna-specific report.
    """
    try:
        chart = perform_calculations(
            name=f"Prashna: {req.question_category}",
            birth_date=req.question_date,
            birth_time=req.question_time,
            latitude=req.latitude,
            longitude=req.longitude,
            timezone=req.timezone,
            ayanamsha_type=req.ayanamsha_type,
            city=None,
        )
        chart["prashna"] = {
            "question_text": req.question_text,
            "question_category": req.question_category,
            "question_date": req.question_date,
            "question_time": req.question_time,
        }
        return chart
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation Error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prashna calculation error: {str(e)}")

@router.post("/muhurta")
@limiter.limit(settings.CALCULATE_RATE_LIMIT)
def get_muhurta(request: Request, req: MuhurtaRequest):
    try:
        from calculator import muhurta
        y, month, d = map(int, req.date.split("-"))

        timezone_info = timezone_resolver.resolve_timezone(
            req.date, "12:00:00", req.timezone, timezone_id=req.timezone_id, city=req.city
        )
        tz = timezone_info["timezone"]

        jd_noon = julian.datetime_to_jd(y, month, d, 12, 0, 0, tz)
        result = muhurta.calculate_muhurta(jd_noon, req.latitude, req.longitude, tz)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Muhurta calculation error: {str(e)}")
