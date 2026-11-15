# -*- coding: utf-8 -*-
"""Panchang calculation engine with high-precision astronomical ephemeris and
mathematical root-solving for transitions.

Calibrated against authoritative reference observations and standard Nepali
Patro / Drik Ganita conventions.
"""
import math
import os
from functools import lru_cache
from typing import Dict, Any, Tuple, Optional

try:
    import swisseph as swe
    _HAS_SWISSEPH = True
except ImportError:
    swe = None
    _HAS_SWISSEPH = False

from . import ayanamsha, planetary_positions, julian, surya_siddhanta

CALCULATION_MODES = ("DRIK", "SURYA_SIDDHANTA")
DEFAULT_CALCULATION_MODE = "DRIK"

# Standard Kathmandu geographic defaults
DEFAULT_KATHMANDU_LAT = 27.7172
DEFAULT_KATHMANDU_LON = 85.3240
DEFAULT_KATHMANDU_ALT = 1400.0  # meters above sea level


def normalize_calculation_mode(value: str | None) -> str:
    mode = str(value or DEFAULT_CALCULATION_MODE).strip().upper()
    if mode not in CALCULATION_MODES:
        raise ValueError(
            f"calculation_mode must be one of {', '.join(CALCULATION_MODES)}"
        )
    return mode


# Nakshatra Names (English & Nepali)
NAKSHATRAS = [
    {"name": "Ashwini",          "nepali": "अश्विनी"},
    {"name": "Bharani",          "nepali": "भरणी"},
    {"name": "Krittika",         "nepali": "कृत्तिका"},
    {"name": "Rohini",           "nepali": "रोहिणी"},
    {"name": "Mrigashira",       "nepali": "मृगशिरा"},
    {"name": "Ardra",            "nepali": "आर्द्रा"},
    {"name": "Punarvasu",        "nepali": "पुनर्वशु"},
    {"name": "Pushya",           "nepali": "पुष्य"},
    {"name": "Ashlesha",         "nepali": "अश्लेषा"},
    {"name": "Magha",            "nepali": "मघा"},
    {"name": "Purva Phalguni",   "nepali": "पूर्वफाल्गुनी"},
    {"name": "Uttara Phalguni",  "nepali": "उत्तरफाल्गुनी"},
    {"name": "Hasta",            "nepali": "हस्त"},
    {"name": "Chitra",           "nepali": "चित्रा"},
    {"name": "Svati",            "nepali": "स्वाती"},
    {"name": "Visakha",          "nepali": "विशाखा"},
    {"name": "Anuradha",         "nepali": "अनुराधा"},
    {"name": "Jyeshtha",         "nepali": "ज्येष्ठा"},
    {"name": "Mula",             "nepali": "मूल"},
    {"name": "Purva Ashadha",    "nepali": "पूर्वाषाढा"},
    {"name": "Uttara Ashadha",   "nepali": "उत्तराषाढा"},
    {"name": "Shravana",         "nepali": "श्रवण"},
    {"name": "Dhanishta",        "nepali": "धनिष्ठा"},
    {"name": "Shatabhisha",      "nepali": "शतभिषा"},
    {"name": "Purva Bhadrapada", "nepali": "पूर्वभाद्रपदा"},
    {"name": "Uttara Bhadrapada","nepali": "उत्तरभाद्रपदा"},
    {"name": "Revati",           "nepali": "रेवती"}
]

# Tithi Names
TITHIS = [
    {"name": "Prathama (Pratipada)", "nepali": "प्रतिपदा"},
    {"name": "Dwitiya",              "nepali": "द्वितिय"},
    {"name": "Tritiya",              "nepali": "तृतीया"},
    {"name": "Chaturthi",            "nepali": "चतुर्थी"},
    {"name": "Panchami",             "nepali": "पञ्चमी"},
    {"name": "Shashti",              "nepali": "षष्ठी"},
    {"name": "Saptami",              "nepali": "सप्तमी"},
    {"name": "Ashtami",              "nepali": "अष्टमी"},
    {"name": "Navami",               "nepali": "नवमी"},
    {"name": "Dashami",              "nepali": "दशमी"},
    {"name": "Ekadashi",             "nepali": "एकादशी"},
    {"name": "Dwadashi",             "nepali": "द्वादशी"},
    {"name": "Trayodashi",           "nepali": "त्रयोदशी"},
    {"name": "Chaturdashi",          "nepali": "चतुर्दशी"},
    {"name": "Purnima (Full Moon)",  "nepali": "पूर्णिमा"},
    {"name": "Prathama (Pratipada)", "nepali": "प्रतिपदा"},
    {"name": "Dwitiya",              "nepali": "द्वितिय"},
    {"name": "Tritiya",              "nepali": "तृतीया"},
    {"name": "Chaturthi",            "nepali": "चतुर्थी"},
    {"name": "Panchami",             "nepali": "पञ्चमी"},
    {"name": "Shashti",              "nepali": "षष्ठी"},
    {"name": "Saptami",              "nepali": "सप्तमी"},
    {"name": "Ashtami",              "nepali": "अष्टमी"},
    {"name": "Navami",               "nepali": "नवमी"},
    {"name": "Dashami",              "nepali": "दशमी"},
    {"name": "Ekadashi",             "nepali": "एकादशी"},
    {"name": "Dwadashi",             "nepali": "द्वादशी"},
    {"name": "Trayodashi",           "nepali": "त्रयोदशी"},
    {"name": "Chaturdashi",          "nepali": "चतुर्दशी"},
    {"name": "Amavasya (New Moon)",  "nepali": "औंसी"}
]

# Yoga Names
YOGAS = [
    {"name": "Vishkumbha",  "nepali": "विष्कम्भ"},
    {"name": "Priti",       "nepali": "प्रीति"},
    {"name": "Ayushman",    "nepali": "आयुष्मान्"},
    {"name": "Saubhagya",   "nepali": "सौभाग्य"},
    {"name": "Shobhana",    "nepali": "शोभन"},
    {"name": "Atiganda",    "nepali": "अतिगण्ड"},
    {"name": "Sukarma",     "nepali": "सुकर्मा"},
    {"name": "Dhriti",      "nepali": "धृति"},
    {"name": "Shula",       "nepali": "शूल"},
    {"name": "Ganda",       "nepali": "गण्ड"},
    {"name": "Vriddhi",     "nepali": "वृद्धि"},
    {"name": "Dhruva",      "nepali": "ध्रुव"},
    {"name": "Vyaghata",    "nepali": "व्याघात"},
    {"name": "Harshana",    "nepali": "हर्षण"},
    {"name": "Vajra",       "nepali": "वज्र"},
    {"name": "Siddhi",      "nepali": "सिद्धि"},
    {"name": "Vyatipata",   "nepali": "व्यतीपात"},
    {"name": "Variyan",     "nepali": "वरियान्"},
    {"name": "Parigha",     "nepali": "परिघ"},
    {"name": "Shiva",       "nepali": "शिव"},
    {"name": "Siddha",      "nepali": "सिद्ध"},
    {"name": "Sadhya",      "nepali": "साध्य"},
    {"name": "Shubha",      "nepali": "शुभ"},
    {"name": "Shukla",      "nepali": "शुक्ल"},
    {"name": "Brahma",      "nepali": "ब्रह्म"},
    {"name": "Indra",       "nepali": "ऐन्द्र"},
    {"name": "Vaidhriti",   "nepali": "वैधृति"}
]

# 12 Zodiac Rashis (Signs)
RASHIS = [
    {"name": "Aries",       "nepali": "मेष"},
    {"name": "Taurus",      "nepali": "वृष"},
    {"name": "Gemini",      "nepali": "मिथुन"},
    {"name": "Cancer",      "nepali": "कर्कट"},
    {"name": "Leo",         "nepali": "सिंह"},
    {"name": "Virgo",       "nepali": "कन्या"},
    {"name": "Libra",       "nepali": "तुला"},
    {"name": "Scorpio",     "nepali": "वृश्चिक"},
    {"name": "Sagittarius", "nepali": "धनु"},
    {"name": "Capricorn",   "nepali": "मकर"},
    {"name": "Aquarius",    "nepali": "कुम्भ"},
    {"name": "Pisces",      "nepali": "मीन"},
]

# Anandadi Yoga Names (28 yogas based on weekday + nakshatra)
ANANDADI_YOGAS = [
    "आनन्द", "कालदण्ड", "धूम्र", "धाता", "सौम्य", "ध्वांक्ष", "ध्वज",
    "श्रीवत्स", "वज्र", "मुद्गर", "छत्र", "मित्र", "मानस", "पद्म",
    "लुम्ब", "उत्पात", "मृत्यु", "काण", "सिद्धि", "शुभ", "अमृत",
    "मुसल", "गद", "मातङ्ग", "राक्षस", "चर", "सुस्थिर", "प्रवर्द्ध"
]

# Karana Names
KARANAS = [
    {"name": "Bava",         "nepali": "बव"},
    {"name": "Balava",       "nepali": "बालव"},
    {"name": "Kaulava",      "nepali": "कौलव"},
    {"name": "Taitila",      "nepali": "तैतिल"},
    {"name": "Gara",         "nepali": "गर"},
    {"name": "Vanija",       "nepali": "वणिज"},
    {"name": "Vishti (Bhadra)", "nepali": "भद्रा"},
    {"name": "Shakuni",      "nepali": "शकुनि"},
    {"name": "Chatushpada",  "nepali": "चतुष्पाद"},
    {"name": "Naga",         "nepali": "नाग"},
    {"name": "Kintughna",    "nepali": "किन्तुघ्न"}
]

# Amanta lunar months, keyed by the sidereal Sun sign at the ending new moon.
LUNAR_MONTHS = [
    {"name": "Vaishakha", "nepali": "वैशाख"},
    {"name": "Jyeshtha", "nepali": "ज्येष्ठ"},
    {"name": "Ashadha", "nepali": "आषाढ"},
    {"name": "Shravana", "nepali": "श्रावण"},
    {"name": "Bhadrapada", "nepali": "भाद्रपद"},
    {"name": "Ashwin", "nepali": "आश्विन"},
    {"name": "Kartika", "nepali": "कार्तिक"},
    {"name": "Margashirsha", "nepali": "मार्गशीर्ष"},
    {"name": "Pausha", "nepali": "पौष"},
    {"name": "Magha", "nepali": "माघ"},
    {"name": "Phalguna", "nepali": "फाल्गुन"},
    {"name": "Chaitra", "nepali": "चैत्र"},
]

# Vara Names
VARAS = [
    {"name": "Sunday (Adityavara)",   "nepali": "आइतवार"},
    {"name": "Monday (Somavara)",     "nepali": "सोमवार"},
    {"name": "Tuesday (Mangalavara)", "nepali": "मङ्गलवार"},
    {"name": "Wednesday (Budhavara)", "nepali": "बुधवार"},
    {"name": "Thursday (Guruvara)",   "nepali": "बिहिवार"},
    {"name": "Friday (Shukravara)",   "nepali": "शुक्रवार"},
    {"name": "Saturday (Shanivara)", "nepali": "शनिवार"}
]

# 60 Samvatsara names (Prabhava=0 ... Kshaya=59)
SAMVATSARA = [
    "प्रभव",   "विभव",     "शुक्ल",     "प्रमोद",   "प्रजापति",
    "अंगिरस",  "श्रीमुख",  "भाव",       "युव",       "धातृ",
    "ईश्वर",   "बहुधान्य", "प्रमाथि",   "विक्रम",   "वृष",
    "चित्रभानु","सुभानु",   "तारण",      "पार्थिव",  "व्यय",
    "सर्वजित्","सर्वधारी", "विरोधी",    "विकृति",   "खर",
    "नन्दन",   "विजय",     "जय",        "मन्मथ",    "दुर्मुख",
    "हेमलम्बी","विलम्बी",  "विकारी",    "शार्वरी",  "प्लव",
    "शुभकृत्", "शोभकृत्",  "क्रोधी",    "विश्वावसु","पराभव",
    "प्लवंग",  "कीलक",     "सौम्य",     "साधारण",   "विरोधकृत्",
    "परिधावी", "प्रमादीच", "आनन्द",     "राक्षस",   "नल",
    "पिंगल",   "काल",      "सिद्धार्थ", "रौद्र",    "दुर्मति",
    "दुन्दुभि","रुधिरोद्गारी","रक्ताक्षी","क्रोधन",  "क्षय"
]

# Nepal Samvat 12-year era names
NS_ERA_NAMES_12 = [
    "ताहा", "धान्यक", "तुगु", "नागा", "शिखर", "कुयलु",
    "गुथि", "बख्खु", "छिल्लागु", "तछलागा", "थु", "छेयलागा"
]
NS_ERA_OFFSET = 3


def get_ns_era(ns_year: int) -> str:
    idx = (ns_year + NS_ERA_OFFSET) % 12
    return NS_ERA_NAMES_12[idx]


def get_samvatsara(bs_year: int) -> str:
    idx = (bs_year + 10) % 60
    return SAMVATSARA[idx]


def _ad_to_bs_year(ad_year: int, month: int, day: int) -> int:
    """
    Convert AD date to Bikram Sambat year.
    BS year starts around April 13-14 (Mesha Sankranti).
    Approximation: Before mid-April use AD + 56, after use AD + 57.
    """
    if month < 4 or (month == 4 and day < 14):
        return ad_year + 56
    else:
        return ad_year + 57


def _jd_to_ad_date(jd: float, timezone: float = 5.75) -> Tuple[int, int, int]:
    """Convert JD to AD date (year, month, day) in local timezone."""
    local_jd = jd + timezone / 24.0
    jd_int = int(local_jd + 0.5)
    f = local_jd + 0.5 - jd_int
    if f < 0:
        f += 1
        jd_int -= 1
    if jd_int > 2299160:
        a = jd_int + 32044
        b = (4 * a + 3) // 146097
        c = a - (146097 * b) // 4
    else:
        b = 0
        c = jd_int + 32082
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + (m // 10)
    return year, month, day


def _normalize_angle(angle: float) -> float:
    return angle % 360.0


# ── Swiss Ephemeris & Fallback Longitudes ─────────────────────────────────────

def _get_swisseph_sidereal_mode(ayanamsha_type: str) -> Optional[int]:
    if not _HAS_SWISSEPH:
        return None
    mode_str = str(ayanamsha_type or "LAHIRI").strip().upper()
    mapping = {
        "LAHIRI": swe.SIDM_LAHIRI,
        "CHITRAPAKSHA": swe.SIDM_LAHIRI,
        "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,
        "KP": swe.SIDM_KRISHNAMURTI,
        "RAMAN": swe.SIDM_RAMAN,
        "TRUE_CITRA": swe.SIDM_TRUE_CITRA,
        "FAGAN_BRADLEY": swe.SIDM_FAGAN_BRADLEY,
        "YUKTESHWAR": swe.SIDM_YUKTESHWAR,
        "JN_BHASIN": swe.SIDM_JN_BHASIN,
        "SURYA_SIDDHANTA": swe.SIDM_SURYASIDDHANTA,
        "GRAHALAGHAVA": swe.SIDM_ARYABHATA,
        "ARYABHATA": swe.SIDM_ARYABHATA,
    }
    return mapping.get(mode_str, swe.SIDM_LAHIRI)


def _swe_sidereal_longitudes(
    jd: float, ayanamsha_type: str = "LAHIRI"
) -> Optional[Tuple[float, float]]:
    """Return high-precision apparent sidereal longitudes (Sun, Moon) via Swiss Ephemeris."""
    if not _HAS_SWISSEPH:
        return None
    try:
        mode_str = str(ayanamsha_type or "LAHIRI").strip().upper()
        if mode_str == "TROPICAL":
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            sun_res = swe.calc_ut(jd, swe.SUN, flags)
            moon_res = swe.calc_ut(jd, swe.MOON, flags)
            return (_normalize_angle(sun_res[0][0]), _normalize_angle(moon_res[0][0]))
        
        sid_mode = _get_swisseph_sidereal_mode(mode_str)
        swe.set_sid_mode(sid_mode)
        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
        sun_res = swe.calc_ut(jd, swe.SUN, flags)
        moon_res = swe.calc_ut(jd, swe.MOON, flags)
        return (_normalize_angle(sun_res[0][0]), _normalize_angle(moon_res[0][0]))
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_panchang_ephemeris():
    """Load the bundled Skyfield JPL ephemeris once; return None when unavailable."""
    try:
        from skyfield.api import load

        bsp_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "de421.bsp")
        )
        if not os.path.exists(bsp_path):
            return None
        return load.timescale(), load(bsp_path)
    except Exception:
        return None


def _jpl_sidereal_longitudes(
    jd: float, ayanamsha_type: str = "LAHIRI"
) -> Optional[Tuple[float, float]]:
    """Return JPL apparent ecliptic longitudes via Skyfield."""
    loaded = _load_panchang_ephemeris()
    if loaded is None:
        return None
    try:
        timescale, ephemeris = loaded
        time = timescale.ut1_jd(jd)
        earth = ephemeris["earth"]
        sun_tropical = float(
            earth.at(time).observe(ephemeris["sun"]).apparent()
            .ecliptic_latlon(epoch="date")[1].degrees
        )
        moon_tropical = float(
            earth.at(time).observe(ephemeris["moon"]).apparent()
            .ecliptic_latlon(epoch="date")[1].degrees
        )
        aya_val = ayanamsha.get_ayanamsha(
            ayanamsha_type, julian.jd_to_julian_centuries(jd)
        )
        return (
            _normalize_angle(sun_tropical - aya_val),
            _normalize_angle(moon_tropical - aya_val),
        )
    except Exception:
        return None


def _uncalibrated_sidereal_longitudes(
    jd: float, ayanamsha_type: str = "LAHIRI"
) -> Tuple[float, float]:
    """Analytical fallback sidereal longitudes."""
    T = julian.jd_to_julian_centuries(jd)
    aya_val = ayanamsha.get_ayanamsha(ayanamsha_type, T)
    sun_long_tropical, _ = planetary_positions.get_sun_position(T)
    moon_long_tropical, _ = planetary_positions.get_moon_position(T)
    return (
        _normalize_angle(sun_long_tropical - aya_val),
        _normalize_angle(moon_long_tropical - aya_val),
    )


def _sidereal_longitudes(
    jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    longitude: float = DEFAULT_KATHMANDU_LON,
) -> Tuple[float, float]:
    """Return sidereal longitudes (Sun, Moon) from the selected engine."""
    mode = normalize_calculation_mode(calculation_mode)
    if mode == "SURYA_SIDDHANTA":
        return surya_siddhanta.sidereal_longitudes(jd, longitude=longitude)
    
    swe_result = _swe_sidereal_longitudes(jd, ayanamsha_type)
    if swe_result is not None:
        return swe_result
    
    jpl_result = _jpl_sidereal_longitudes(jd, ayanamsha_type)
    if jpl_result is not None:
        return jpl_result
        
    return _uncalibrated_sidereal_longitudes(jd, ayanamsha_type)


def _new_moon_phase_angle(
    jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> float:
    """Return smooth phase angle for lunation/month classification."""
    sun_sid, moon_sid = _sidereal_longitudes(jd, ayanamsha_type, calculation_mode)
    diff = _normalize_angle(moon_sid - sun_sid)
    return math.atan2(math.sin(math.radians(diff)), math.cos(math.radians(diff)))


def _find_root(f, start_jd: float, end_jd: float, max_iter: int = 45, tol_days: float = 0.05 / 86400.0) -> float:
    """Refine a root for a continuous function using bisection."""
    f0 = f(start_jd)
    f1 = f(end_jd)
    if abs(f0) < 1e-9:
        return start_jd
    if abs(f1) < 1e-9:
        return end_jd

    lo, hi = start_jd, end_jd
    flo, fhi = f0, f1
    if flo * fhi > 0:
        return (start_jd + end_jd) / 2.0

    for _ in range(max_iter):
        if (hi - lo) <= tol_days:
            break
        mid = (lo + hi) / 2.0
        fmid = f(mid)
        if abs(fmid) < 1e-9:
            return mid
        if flo * fmid <= 0:
            hi, fhi = mid, fmid
        else:
            lo, flo = mid, fmid
    return (lo + hi) / 2.0


def _new_moon_diff(jd: float, ayanamsha_type: str, calculation_mode: str) -> float:
    s, m = _sidereal_longitudes(jd, ayanamsha_type, calculation_mode)
    diff = _normalize_angle(m - s)
    return ((diff + 180.0) % 360.0) - 180.0


def find_previous_new_moon(
    jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> float | None:
    """Return the JD of the previous new moon before or at jd."""
    # Approximate lunar month is 29.53 days
    # Fast bracket
    def f(t):
        return _new_moon_diff(t, ayanamsha_type, calculation_mode)
    
    # Step backwards in 3-day increments
    curr = jd - 0.05
    f_curr = f(curr)
    for _ in range(15):
        prev = curr - 2.5
        f_prev = f(prev)
        if f_prev * f_curr <= 0 and f_prev <= 0 and f_curr >= 0:
            return _find_root(f, prev, curr, max_iter=30)
        curr, f_curr = prev, f_prev
    return None


def find_next_new_moon(
    jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> float | None:
    """Return the JD of the next new moon at or after jd."""
    def f(t):
        return _new_moon_diff(t, ayanamsha_type, calculation_mode)
    
    curr = jd + 0.05
    f_curr = f(curr)
    for _ in range(15):
        nxt = curr + 2.5
        f_nxt = f(nxt)
        if f_curr * f_nxt <= 0 and f_curr <= 0 and f_nxt >= 0:
            return _find_root(f, curr, nxt, max_iter=30)
        curr, f_curr = nxt, f_nxt
    return None


def _solar_sign_index(
    jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> int:
    sun_sid, _ = _sidereal_longitudes(jd, ayanamsha_type, calculation_mode)
    return int(sun_sid // 30.0) % 12


def _tithi_idx_at(
    t: float, ayanamsha_type: str = "LAHIRI", calculation_mode: str = DEFAULT_CALCULATION_MODE
) -> int:
    sun_sid, moon_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode)
    return int(((moon_sid - sun_sid) % 360.0) / 12.0) % 30


def _nakshatra_idx_at(
    t: float, ayanamsha_type: str = "LAHIRI", calculation_mode: str = DEFAULT_CALCULATION_MODE
) -> int:
    _, moon_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode)
    return int(moon_sid / (360.0 / 27.0)) % 27


def _yoga_idx_at(
    t: float, ayanamsha_type: str = "LAHIRI", calculation_mode: str = DEFAULT_CALCULATION_MODE
) -> int:
    sun_sid, moon_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode)
    return int(((sun_sid + moon_sid) % 360.0) / (360.0 / 27.0)) % 27


def _karana_idx_at(
    t: float, ayanamsha_type: str = "LAHIRI", calculation_mode: str = DEFAULT_CALCULATION_MODE
) -> int:
    sun_sid, moon_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode)
    return int(((moon_sid - sun_sid) % 360.0) / 6.0) % 60


def _find_next_index_change(
    start_jd: float,
    current_idx: int,
    get_idx_fn,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    max_hours: float = 36.0,
    step_hours: float = 0.5
) -> Optional[float]:
    """Compatibility bridge to precise mathematical transition functions."""
    if get_idx_fn == _nakshatra_idx_at:
        return calculate_nakshatra_transition(start_jd, current_idx, ayanamsha_type, calculation_mode, max_hours)
    elif get_idx_fn == _tithi_idx_at:
        return calculate_tithi_transition(start_jd, current_idx, ayanamsha_type, calculation_mode, max_hours)
    elif get_idx_fn == _yoga_idx_at:
        return calculate_yoga_transition(start_jd, current_idx, ayanamsha_type, calculation_mode, max_hours)
    elif get_idx_fn == _karana_idx_at:
        return calculate_karana_transition(start_jd, current_idx, ayanamsha_type, calculation_mode, max_hours)

    actual_current = get_idx_fn(start_jd, ayanamsha_type, calculation_mode)
    t_max = start_jd + max_hours / 24.0
    step = 0.5 / 24.0
    t = start_jd
    lo, hi = start_jd, t_max
    found = False
    while t < t_max:
        t_next = min(t_max, t + step)
        if get_idx_fn(t_next, ayanamsha_type, calculation_mode) != actual_current:
            lo, hi = t, t_next
            found = True
            break
        t = t_next
    if not found:
        return None
    for _ in range(30):
        mid = (lo + hi) / 2.0
        if get_idx_fn(mid, ayanamsha_type, calculation_mode) == actual_current:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def count_solar_ingresses(
    start_jd: float,
    end_jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> int:
    if start_jd >= end_jd:
        return 0
    step = 1.0
    count = 0
    previous_sign = _solar_sign_index(start_jd, ayanamsha_type, calculation_mode)
    jd = start_jd + step
    while jd < end_jd + 1e-9:
        current_sign = _solar_sign_index(jd, ayanamsha_type, calculation_mode)
        if current_sign != previous_sign:
            count += 1
            previous_sign = current_sign
        jd += step
    return count


def get_lunar_month(
    jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    _cached_adhika_status: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    status = _cached_adhika_status if _cached_adhika_status is not None else get_adhika_month_status(jd, ayanamsha_type, calculation_mode)
    next_new_moon_jd = status.get("next_new_moon_jd")
    if next_new_moon_jd is None:
        return {
            "name": "",
            "nepali": "",
            "base_name": "",
            "base_nepali": "",
            "index": None,
            "type": status["month_type"],
            "type_nepali": status["month_type_nepali"],
        }

    sun_longitude, _ = _sidereal_longitudes(
        next_new_moon_jd, ayanamsha_type, calculation_mode
    )
    month_index = int(sun_longitude / 30.0) % 12
    base = LUNAR_MONTHS[month_index]
    is_adhika = status["month_type"] == "adhika"
    return {
        "name": f"Adhika {base['name']}" if is_adhika else base["name"],
        "nepali": f"अधिक {base['nepali']}" if is_adhika else base["nepali"],
        "base_name": base["name"],
        "base_nepali": base["nepali"],
        "index": month_index + 1,
        "type": status["month_type"],
        "type_nepali": status["month_type_nepali"],
    }


def get_adhika_month_status(
    jd: float,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> Dict[str, Any]:
    prev_nm = find_previous_new_moon(jd, ayanamsha_type, calculation_mode)
    next_nm = find_next_new_moon(jd, ayanamsha_type, calculation_mode)
    if prev_nm is None or next_nm is None:
        return {
            "month_type": "normal",
            "month_type_nepali": "सामान्य",
            "solar_ingress_count": 1
        }

    ingress_count = count_solar_ingresses(
        prev_nm + 0.05, next_nm - 0.05, ayanamsha_type, calculation_mode
    )
    if ingress_count == 0:
        month_type = "adhika"
        month_type_nepali = "अधिक मास"
    elif ingress_count >= 2:
        month_type = "kshaya"
        month_type_nepali = "क्षय मास"
    else:
        month_type = "normal"
        month_type_nepali = "सामान्य"

    return {
        "month_type": month_type,
        "month_type_nepali": month_type_nepali,
        "solar_ingress_count": ingress_count,
        "previous_new_moon_jd": prev_nm,
        "next_new_moon_jd": next_nm
    }


# ── Sunrise & Sunset Calculations ─────────────────────────────────────────────

def _minutes_to_hhmm(total_minutes: float) -> str:
    total_minutes = total_minutes % (24 * 60)
    total_minutes_rounded = round(total_minutes)
    total_minutes_rounded = total_minutes_rounded % (24 * 60)
    h = total_minutes_rounded // 60
    m = total_minutes_rounded % 60
    return f"{h:02d}:{m:02d}"


def calculate_sunrise(
    jd: float,
    latitude: float = DEFAULT_KATHMANDU_LAT,
    longitude: float = DEFAULT_KATHMANDU_LON,
    timezone: float = 5.75,
    altitude: float = DEFAULT_KATHMANDU_ALT,
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> Dict[str, Any]:
    """Calculate precise sunrise for the given civil date."""
    sun_data = calculate_sunrise_sunset(jd, latitude, longitude, timezone, altitude, calculation_mode=calculation_mode)
    return {"time": sun_data["sunrise"], "jd": calculate_sunrise_jd(jd, latitude, longitude, timezone, altitude, calculation_mode=calculation_mode)}


def calculate_sunset(
    jd: float,
    latitude: float = DEFAULT_KATHMANDU_LAT,
    longitude: float = DEFAULT_KATHMANDU_LON,
    timezone: float = 5.75,
    altitude: float = DEFAULT_KATHMANDU_ALT,
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> Dict[str, Any]:
    """Calculate precise sunset for the given civil date."""
    sun_data = calculate_sunrise_sunset(jd, latitude, longitude, timezone, altitude, calculation_mode=calculation_mode)
    return {"time": sun_data["sunset"]}


def _swe_sunrise_sunset(
    jd_noon: float,
    latitude: float,
    longitude: float,
    timezone: float,
    altitude: float = DEFAULT_KATHMANDU_ALT,
) -> Optional[Dict[str, Any]]:
    """Compute sunrise/sunset using Swiss Ephemeris with atmospheric refraction and altitude."""
    if not _HAS_SWISSEPH:
        return None
    try:
        import datetime as _dt
        j2000 = _dt.datetime(2000, 1, 1, 12, 0, 0)
        local_noon_utc = j2000 + _dt.timedelta(days=jd_noon - 2451545.0)
        local_dt = local_noon_utc + _dt.timedelta(hours=timezone)
        local_date = local_dt.date()
        
        # Local midnight in UT
        jd_mid_ut = swe.julday(local_date.year, local_date.month, local_date.day, 0.0 - timezone)
        
        geopos = (longitude, latitude, altitude)
        ret_sr, tret_sr = swe.rise_trans(jd_mid_ut, swe.SUN, swe.CALC_RISE, geopos, 1013.25, 15.0)
        ret_ss, tret_ss = swe.rise_trans(jd_mid_ut, swe.SUN, swe.CALC_SET, geopos, 1013.25, 15.0)
        
        if ret_sr != 0 or ret_ss != 0:
            return None
            
        sr_sec = (tret_sr[0] - jd_mid_ut) * 86400.0
        ss_sec = (tret_ss[0] - jd_mid_ut) * 86400.0
        
        sr_min = round(sr_sec / 60.0) % 1440
        ss_min = round(ss_sec / 60.0) % 1440
        
        sunrise_str = f"{sr_min // 60:02d}:{sr_min % 60:02d}"
        sunset_str = f"{ss_min // 60:02d}:{ss_min % 60:02d}"
        
        # Calculate Sun declination and EoT
        t_sr_jd = tret_sr[0]
        sun_res = swe.calc_ut(t_sr_jd, swe.SUN, swe.FLG_EQUATORIAL | swe.FLG_SWIEPH)
        decl = sun_res[0][1]
        
        # Equation of time
        # EoT = Apparent Solar Time - Mean Solar Time
        T = (jd_noon - 2451545.0) / 36525.0
        L0 = (280.46646 + 36000.76983 * T) % 360.0
        eot = (L0 - sun_res[0][0]) * 4.0
        if eot > 720: eot -= 1440
        if eot < -720: eot += 1440
        
        return {
            "sunrise": sunrise_str,
            "sunset": sunset_str,
            "day_duration_min": max(0, ss_min - sr_min),
            "sun_declination": decl,
            "equation_of_time_min": eot,
            "sunrise_jd": tret_sr[0],
            "sunset_jd": tret_ss[0]
        }
    except Exception:
        return None


def _skyfield_sunrise_sunset(jd_noon: float, latitude: float, longitude: float, timezone: float) -> Optional[Dict[str, str]]:
    try:
        from skyfield.api import wgs84
        from skyfield import almanac

        loaded = _load_panchang_ephemeris()
        if loaded is None:
            return None

        ts, eph = loaded
        observer = wgs84.latlon(latitude, longitude)

        import datetime as _dt
        j2000 = _dt.datetime(2000, 1, 1, 12, 0, 0)
        local_noon_utc = j2000 + _dt.timedelta(days=jd_noon - 2451545.0)
        local_dt = local_noon_utc + _dt.timedelta(hours=timezone)
        local_date = local_dt.date()
        start_utc = _dt.datetime(local_date.year, local_date.month, local_date.day,
                                  0, 0, 0) - _dt.timedelta(hours=timezone)
        end_utc   = start_utc + _dt.timedelta(hours=24)
        t0 = ts.utc(start_utc.year, start_utc.month, start_utc.day,
                    start_utc.hour, start_utc.minute, start_utc.second)
        t1 = ts.utc(end_utc.year,   end_utc.month,   end_utc.day,
                    end_utc.hour,   end_utc.minute,   end_utc.second)

        f = almanac.sunrise_sunset(eph, observer)
        times, events = almanac.find_discrete(t0, t1, f)

        result = {"sunrise": None, "sunset": None}
        for t, e in zip(times, events):
            utc_dt = t.utc_datetime()
            total_local_seconds = (
                utc_dt.hour * 3600 + utc_dt.minute * 60 + utc_dt.second
                + int(timezone * 3600)
            ) % 86400
            total_min = round(total_local_seconds / 60.0) % 1440
            h = total_min // 60
            mn = total_min % 60
            hhmm = f"{h:02d}:{mn:02d}"
            if e == 1:
                result["sunrise"] = hhmm
            else:
                result["sunset"] = hhmm

        if result["sunrise"] and result["sunset"]:
            return result
        return None
    except Exception:
        return None


def calculate_sunrise_jd(
    jd_for_date: float,
    latitude: float = DEFAULT_KATHMANDU_LAT,
    longitude: float = DEFAULT_KATHMANDU_LON,
    timezone: float = 5.75,
    altitude: float = DEFAULT_KATHMANDU_ALT,
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> float:
    """Return the Julian Date of local sunrise for the civil date of ``jd_for_date``."""
    sun_data = calculate_sunrise_sunset(jd_for_date, latitude, longitude, timezone, altitude, calculation_mode=calculation_mode)
    if "sunrise_jd" in sun_data and sun_data["sunrise_jd"] is not None:
        return sun_data["sunrise_jd"]
    sunrise_h, sunrise_m = (int(part) for part in sun_data["sunrise"].split(":"))
    local_jd = jd_for_date + timezone / 24.0
    local_midnight_jd = math.floor(local_jd - 0.5) + 0.5
    return local_midnight_jd + (sunrise_h + sunrise_m / 60.0 - timezone) / 24.0


def calculate_sunrise_sunset(
    jd_noon: float,
    latitude: float = DEFAULT_KATHMANDU_LAT,
    longitude: float = DEFAULT_KATHMANDU_LON,
    timezone: float = 5.75,
    altitude: float = DEFAULT_KATHMANDU_ALT,
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
) -> Dict[str, Any]:
    """High-accuracy sunrise/sunset calculation matching Nepali Patro / Ephemeris standard.
    
    Primary: Swiss Ephemeris with atmospheric refraction and elevation.
    Secondary: Skyfield + DE421 ephemeris.
    Fallback: NOAA solar calculation.
    Surya Siddhanta: Pure classical Surya Siddhanta Triprasnadhikara method.
    """
    if not latitude and not longitude:
        latitude = DEFAULT_KATHMANDU_LAT
        longitude = DEFAULT_KATHMANDU_LON
    if not timezone:
        timezone = 5.75

    mode = normalize_calculation_mode(calculation_mode)
    if mode == "SURYA_SIDDHANTA":
        return surya_siddhanta.calculate_sunrise_sunset(
            jd_noon=jd_noon,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            altitude=altitude,
        )

    # 1. Try Swiss Ephemeris
    swe_result = _swe_sunrise_sunset(jd_noon, latitude, longitude, timezone, altitude)
    if swe_result is not None:
        return swe_result

    # 2. Try Skyfield
    sky_result = _skyfield_sunrise_sunset(jd_noon, latitude, longitude, timezone)
    if sky_result:
        T = (jd_noon - 2451545.0) / 36525.0
        L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360.0
        M = (357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360.0
        M_r = math.radians(M)
        C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_r)
             + (0.019993 - 0.000101 * T) * math.sin(2 * M_r)
             + 0.000289 * math.sin(3 * M_r))
        sun_lon = L0 + C
        omega = 125.04 - 1934.136 * T
        lambda_sun = sun_lon - 0.00569 - 0.00478 * math.sin(math.radians(omega))
        epsilon0 = (23 + 26 / 60.0 + 21.448 / 3600.0
                    - (46.8150 / 3600.0) * T
                    - (0.00059 / 3600.0) * T * T
                    + (0.001813 / 3600.0) * T * T * T)
        epsilon = epsilon0 + 0.00256 * math.cos(math.radians(omega))
        decl = math.degrees(math.asin(math.sin(math.radians(epsilon)) * math.sin(math.radians(lambda_sun))))
        y = math.tan(math.radians(epsilon / 2)) ** 2
        L0_r = math.radians(L0)
        eot = (4 * math.degrees(
            y * math.sin(2 * L0_r)
            - 2 * 0.016708634 * math.sin(M_r)
            + 4 * 0.016708634 * y * math.sin(M_r) * math.cos(2 * L0_r)
            - 0.5 * y * y * math.sin(4 * L0_r)
            - 1.25 * 0.016708634 * 0.016708634 * math.sin(2 * M_r)
        ))
        def hhmm_to_min(t):
            h, m = map(int, t.split(':'))
            return h * 60 + m
        sr_min = hhmm_to_min(sky_result["sunrise"])
        ss_min = hhmm_to_min(sky_result["sunset"])
        return {
            "sunrise": sky_result["sunrise"],
            "sunset": sky_result["sunset"],
            "day_duration_min": ss_min - sr_min,
            "sun_declination": decl,
            "equation_of_time_min": eot
        }

    # 3. Fallback: NOAA algorithm
    T = (jd_noon - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360.0
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360.0
    M_r = math.radians(M)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_r)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M_r)
         + 0.000289 * math.sin(3 * M_r))
    sun_lon = L0 + C
    omega = 125.04 - 1934.136 * T
    lambda_sun = sun_lon - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    epsilon0 = (23 + 26 / 60.0 + 21.448 / 3600.0
                - (46.8150 / 3600.0) * T
                - (0.00059 / 3600.0) * T * T
                + (0.001813 / 3600.0) * T * T * T)
    epsilon = epsilon0 + 0.00256 * math.cos(math.radians(omega))
    decl = math.degrees(math.asin(math.sin(math.radians(epsilon)) * math.sin(math.radians(lambda_sun))))
    y = math.tan(math.radians(epsilon / 2)) ** 2
    L0_r = math.radians(L0)
    eot = (4 * math.degrees(
        y * math.sin(2 * L0_r)
        - 2 * 0.016708634 * math.sin(M_r)
        + 4 * 0.016708634 * y * math.sin(M_r) * math.cos(2 * L0_r)
        - 0.5 * y * y * math.sin(4 * L0_r)
        - 1.25 * 0.016708634 * 0.016708634 * math.sin(2 * M_r)
    ))
    lat_r = math.radians(latitude)
    decl_r = math.radians(decl)
    cos_ha = (math.cos(math.radians(90.833)) / (math.cos(lat_r) * math.cos(decl_r))
              - math.tan(lat_r) * math.tan(decl_r))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    ha_deg = math.degrees(math.acos(cos_ha))
    solar_noon_min = 720 - 4 * longitude - eot + timezone * 60
    sunrise_min = solar_noon_min - 4 * ha_deg
    sunset_min  = solar_noon_min + 4 * ha_deg
    return {
        "sunrise": _minutes_to_hhmm(sunrise_min),
        "sunset":  _minutes_to_hhmm(sunset_min),
        "day_duration_min": sunset_min - sunrise_min,
        "sun_declination": decl,
        "equation_of_time_min": eot
    }


def _jd_to_local_hhmmss_panchang(jd: float, midnight_local_jd: float, round_to_minute: bool = False) -> str:
    """Convert a transition JD to local Panchang ``HH:MM:SS``."""
    if jd is None:
        return ""
    if round_to_minute:
        total_minutes = int(round((jd - midnight_local_jd) * 1440.0))
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{h:02d}:{m:02d}:00"
    total_seconds = int(round((jd - midnight_local_jd) * 86400.0))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _jd_to_local_hhmm_panchang(jd: float, midnight_local_jd: float, timezone: float = 5.75) -> str:
    """Convert a transition JD to local Panchang ``HH:MM``."""
    if jd is None:
        return ""
    total_minutes = int(round((jd - midnight_local_jd) * 1440.0))
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


# ── High-Precision Transition Functions ───────────────────────────────────────

def _angular_root_search(
    phase_func,
    target_boundary: float,
    start_jd: float,
    max_hours: float = 36.0,
    rate_deg_per_day: float = 12.0,
) -> Optional[float]:
    """Find the exact instant when ``phase_func(jd)`` crosses ``target_boundary`` (rising)."""
    def dist_func(t):
        val = phase_func(t)
        return ((val - target_boundary + 180.0) % 360.0) - 180.0

    d0 = dist_func(start_jd)
    if abs(d0) < 1e-7:
        # If already on boundary at start_jd, find next occurrence
        start_jd += 0.01
        d0 = dist_func(start_jd)

    # Estimate expected time to reach boundary
    if d0 > 0:
        # Boundary is ahead in cycle
        est_days = (360.0 - d0) / max(0.1, rate_deg_per_day)
    else:
        est_days = (-d0) / max(0.1, rate_deg_per_day)

    # Search window
    t_min = start_jd
    t_max = start_jd + max_hours / 24.0

    # Step through window with coarse step to find bracket
    step_days = 0.05  # ~1.2 hours
    lo = t_min
    flo = dist_func(lo)
    found_bracket = False
    hi = lo

    while lo < t_max:
        hi = min(t_max, lo + step_days)
        fhi = dist_func(hi)
        if flo * fhi <= 0 and flo <= 0 and fhi >= 0:
            found_bracket = True
            break
        lo = hi
        flo = fhi

    if not found_bracket:
        return None

    # High precision bisection (< 0.1 second accuracy)
    return _find_root(dist_func, lo, hi, max_iter=45, tol_days=0.05 / 86400.0)


def calculate_tithi_transition(
    jd_start: float,
    current_idx: int,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    max_hours: float = 36.0,
    longitude: float = DEFAULT_KATHMANDU_LON,
) -> Optional[float]:
    """Calculate the exact Julian Date when the current Tithi ends (12° boundary)."""
    boundary = ((current_idx + 1) * 12.0) % 360.0
    if normalize_calculation_mode(calculation_mode) == "SURYA_SIDDHANTA":
        s0, m0 = surya_siddhanta.sidereal_longitudes(jd_start, longitude=longitude)
        vs, vm = surya_siddhanta.get_daily_motions(jd_start, longitude=longitude)
        rel_motion = (vm - vs) % 360.0
        if rel_motion < 0.1:
            rel_motion = 12.0
        diff0 = (m0 - s0) % 360.0
        rem = (boundary - diff0) % 360.0
        return jd_start + (rem / rel_motion)
    
    def tithi_phase(t):
        s_sid, m_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode, longitude=longitude)
        return _normalize_angle(m_sid - s_sid)
        
    return _angular_root_search(
        tithi_phase, boundary, jd_start, max_hours=max_hours, rate_deg_per_day=12.2
    )


def calculate_nakshatra_transition(
    jd_start: float,
    current_idx: int,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    max_hours: float = 36.0,
    longitude: float = DEFAULT_KATHMANDU_LON,
) -> Optional[float]:
    """Calculate the exact Julian Date when the current Nakshatra ends (13°20' boundary)."""
    span = 360.0 / 27.0
    boundary = ((current_idx + 1) * span) % 360.0
    if normalize_calculation_mode(calculation_mode) == "SURYA_SIDDHANTA":
        _, m0 = surya_siddhanta.sidereal_longitudes(jd_start, longitude=longitude)
        _, vm = surya_siddhanta.get_daily_motions(jd_start, longitude=longitude)
        if vm < 0.1:
            vm = 13.0
        rem = (boundary - (m0 % 360.0)) % 360.0
        return jd_start + (rem / vm)
    
    def nak_phase(t):
        _, m_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode, longitude=longitude)
        return _normalize_angle(m_sid)
        
    return _angular_root_search(
        nak_phase, boundary, jd_start, max_hours=max_hours, rate_deg_per_day=13.2
    )


def calculate_yoga_transition(
    jd_start: float,
    current_idx: int,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    max_hours: float = 36.0,
    longitude: float = DEFAULT_KATHMANDU_LON,
) -> Optional[float]:
    """Calculate the exact Julian Date when the current Yoga ends (13°20' boundary)."""
    span = 360.0 / 27.0
    boundary = ((current_idx + 1) * span) % 360.0
    if normalize_calculation_mode(calculation_mode) == "SURYA_SIDDHANTA":
        s0, m0 = surya_siddhanta.sidereal_longitudes(jd_start, longitude=longitude)
        vs, vm = surya_siddhanta.get_daily_motions(jd_start, longitude=longitude)
        comb_motion = (vs + vm) % 360.0
        if comb_motion < 0.1:
            comb_motion = 13.5
        sum0 = (s0 + m0) % 360.0
        rem = (boundary - sum0) % 360.0
        return jd_start + (rem / comb_motion)
    
    def yoga_phase(t):
        s_sid, m_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode, longitude=longitude)
        return _normalize_angle(s_sid + m_sid)
        
    return _angular_root_search(
        yoga_phase, boundary, jd_start, max_hours=max_hours, rate_deg_per_day=14.2
    )


def calculate_karana_transition(
    jd_start: float,
    current_idx: int,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    max_hours: float = 36.0,
    longitude: float = DEFAULT_KATHMANDU_LON,
) -> Optional[float]:
    """Calculate the exact Julian Date when the current Karana ends (6° boundary)."""
    boundary = ((current_idx + 1) * 6.0) % 360.0
    if normalize_calculation_mode(calculation_mode) == "SURYA_SIDDHANTA":
        s0, m0 = surya_siddhanta.sidereal_longitudes(jd_start, longitude=longitude)
        vs, vm = surya_siddhanta.get_daily_motions(jd_start, longitude=longitude)
        rel_motion = (vm - vs) % 360.0
        if rel_motion < 0.1:
            rel_motion = 12.0
        diff0 = (m0 - s0) % 360.0
        rem = (boundary - diff0) % 360.0
        return jd_start + (rem / rel_motion)
    
    def karana_phase(t):
        s_sid, m_sid = _sidereal_longitudes(t, ayanamsha_type, calculation_mode, longitude=longitude)
        return _normalize_angle(m_sid - s_sid)
        
    return _angular_root_search(
        karana_phase, boundary, jd_start, max_hours=max_hours, rate_deg_per_day=12.2
    )


# ── Bhadra (Vishti Karana) Calculation ───────────────────────────────────────

def _compute_bhadra(
    karana_idx_all: int,
    karana_start_jd: float | None,
    karana_end_jd: float | None,
    karana_end_jd2: float | None,
    chandra_rashi_idx: int,
    midnight_local_jd: float,
    round_to_minute: bool = False
) -> Dict[str, Any]:
    """Calculate Classical Bhadra (Vishti Karana) status, timing, residence, Mukha, and Puchha."""
    vishti_map = {
        7: ("Shukla Chaturthi (2nd half)", "शुक्ल चतुर्थी (उत्तरार्ध)"),
        14: ("Shukla Ashtami (1st half)", "शुक्ल अष्टमी (पूर्वार्ध)"),
        21: ("Shukla Ekadashi (2nd half)", "शुक्ल एकादशी (उत्तरार्ध)"),
        28: ("Purnima (1st half)", "पूर्णिमा (पूर्वार्ध)"),
        35: ("Krishna Tritiya (2nd half)", "कृष्ण तृतीया (उत्तरार्ध)"),
        42: ("Krishna Saptami (1st half)", "कृष्ण सप्तमी (पूर्वार्ध)"),
        49: ("Krishna Dashami (2nd half)", "कृष्ण दशमी (उत्तरार्ध)"),
        56: ("Krishna Chaturdashi (1st half)", "कृष्ण चतुर्दशी (पूर्वार्ध)"),
    }

    is_active_sr = karana_idx_all in vishti_map
    starts_today = ((karana_idx_all + 1) % 60) in vishti_map

    target_vishti_idx = None
    b_start_jd = None
    b_end_jd = None

    if is_active_sr:
        target_vishti_idx = karana_idx_all
        b_start_jd = karana_start_jd
        b_end_jd = karana_end_jd
    elif starts_today:
        target_vishti_idx = (karana_idx_all + 1) % 60
        b_start_jd = karana_end_jd
        b_end_jd = karana_end_jd2

    if target_vishti_idx is None:
        return {
            "has_bhadra": False,
            "is_active_today": False,
            "is_active_at_sunrise": False,
            "name": "",
            "nepali": "भद्रा छैन",
            "start_time": "",
            "end_time": "",
            "vas": "",
            "vas_en": "",
            "is_evil_on_earth": False,
            "phala": "आज भद्राको कुनै प्रभाव छैन (शुभ कार्य गर्न सकिने)",
            "phala_en": "No Bhadra active today",
            "mukha": None,
            "puchha": None,
        }

    name_en, name_ne = vishti_map[target_vishti_idx]

    # Residence (Bhadra Vas) based on Moon sign
    # Mesha (0), Vrishabha (1), Mithuna (2), Vrischika (7) -> Swarga
    # Kanya (5), Tula (6), Dhanu (8), Makara (9) -> Patala
    # Karka (3), Simha (4), Kumbha (10), Meena (11) -> Martya (Earth)
    if chandra_rashi_idx in (0, 1, 2, 7):
        vas = "स्वर्ग लोक"
        vas_en = "Swarga (Heaven)"
        phala = "शुभ फलदायी (पृथ्वीमा दोषरहित)"
        phala_en = "Auspicious on Earth (Resides in Heaven)"
        is_evil = False
    elif chandra_rashi_idx in (5, 6, 8, 9):
        vas = "पाताल लोक"
        vas_en = "Patala (Netherworld)"
        phala = "धनधान्य लाभ (पृथ्वीमा दोषरहित)"
        phala_en = "Prosperity and Gain (Resides in Netherworld)"
        is_evil = False
    else:
        vas = "मृत्युलोक (पृथ्वी)"
        vas_en = "Martya (Earth)"
        phala = "सर्वकार्य विनाशिनी / अनिष्ट (शुभ कार्य सर्वथा निषेध)"
        phala_en = "Harmful / Inauspicious on Earth (Avoid all auspicious works)"
        is_evil = True

    start_str = _jd_to_local_hhmmss_panchang(b_start_jd, midnight_local_jd, round_to_minute=round_to_minute) if b_start_jd else ""
    end_str = _jd_to_local_hhmmss_panchang(b_end_jd, midnight_local_jd, round_to_minute=round_to_minute) if b_end_jd else ""

    mukha = None
    puchha = None
    if b_start_jd and b_end_jd and b_end_jd > b_start_jd:
        dur = b_end_jd - b_start_jd
        m_start = b_start_jd
        m_end = b_start_jd + (5.0 / 30.0) * dur
        p_start = b_end_jd - (3.0 / 30.0) * dur
        p_end = b_end_jd

        mukha = {
            "start": _jd_to_local_hhmmss_panchang(m_start, midnight_local_jd, round_to_minute=round_to_minute),
            "end": _jd_to_local_hhmmss_panchang(m_end, midnight_local_jd, round_to_minute=round_to_minute),
            "description": "मुख काल: सर्वथा त्याज्य (बहिष्कार्य)",
            "description_en": "Mouth of Bhadra: Strictly forbidden for all auspicious works"
        }
        puchha = {
            "start": _jd_to_local_hhmmss_panchang(p_start, midnight_local_jd, round_to_minute=round_to_minute),
            "end": _jd_to_local_hhmmss_panchang(p_end, midnight_local_jd, round_to_minute=round_to_minute),
            "description": "पुच्छ काल: अत्यावश्यक शुभ कार्यको लागि ग्राह्य",
            "description_en": "Tail of Bhadra: Permissible for unavoidable auspicious works"
        }

    return {
        "has_bhadra": True,
        "is_active_today": True,
        "is_active_at_sunrise": is_active_sr,
        "name": name_en,
        "nepali": name_ne,
        "start_time": start_str,
        "end_time": end_str,
        "vas": vas,
        "vas_en": vas_en,
        "is_evil_on_earth": is_evil,
        "phala": phala,
        "phala_en": phala_en,
        "mukha": mukha,
        "puchha": puchha,
    }


# ── Full Panchang Calculation ─────────────────────────────────────────────────

def calculate_panchang(
    jd: float,
    sun_long: float,
    moon_long: float,
    latitude: float = DEFAULT_KATHMANDU_LAT,
    longitude: float = DEFAULT_KATHMANDU_LON,
    timezone: float = 5.75,
    bs_year: int | None = None,
    bs_month: int = 3,
    sunrise_jd: float | None = None,
    ayanamsha_type: str = "LAHIRI",
    calculation_mode: str = DEFAULT_CALCULATION_MODE,
    altitude: float = DEFAULT_KATHMANDU_ALT,
) -> Dict[str, Any]:
    """Calculate full Panchang with exact transition times, sunrise/sunset, samvatsara, etc."""
    calculation_mode = normalize_calculation_mode(calculation_mode)
    
    if not latitude and not longitude:
        latitude = DEFAULT_KATHMANDU_LAT
        longitude = DEFAULT_KATHMANDU_LON

    # ── 1. Vara ──────────────────────────────────────────────────────────────
    vara_idx = int(jd + timezone / 24.0 + 1.5) % 7
    vara = VARAS[vara_idx]

    # Karana name helper
    def _get_karana(idx60: int) -> Dict:
        idx = int(idx60) % 60
        if idx == 0:
            return KARANAS[10]  # Kintughna
        elif 1 <= idx <= 56:
            return KARANAS[(idx - 1) % 7]
        elif idx == 57:
            return KARANAS[7]   # Shakuni
        elif idx == 58:
            return KARANAS[8]   # Chatushpada
        else:
            return KARANAS[9]   # Naga

    # ── 2. Sunrise / Sunset ───────────────────────────────────────────────────
    # calculate_sunrise_sunset expects jd_noon (local noon JD).
    # If sunrise_jd is provided, compute noon JD from it (sunrise ~6 AM local, noon ~6 hours later).
    # Otherwise assume jd is already noon JD.
    if sunrise_jd is not None:
        # Approximate 6-hour offset from sunrise to noon
        jd_noon_for_sun = sunrise_jd + 0.25
    else:
        jd_noon_for_sun = jd
    
    sun_data = calculate_sunrise_sunset(jd_noon_for_sun, latitude, longitude, timezone, altitude, calculation_mode=calculation_mode)
    sunrise_str = sun_data["sunrise"]
    sunset_str  = sun_data["sunset"]

    sr_parts = sunrise_str.split(":")
    sunrise_local_min = int(sr_parts[0]) * 60 + int(sr_parts[1])

    ss_parts = sunset_str.split(":")
    sunset_local_min  = int(ss_parts[0]) * 60 + int(ss_parts[1])
    day_dur_min = max(0, sunset_local_min - sunrise_local_min)
    day_dur_hh = int(day_dur_min // 60)
    day_dur_mm = int(day_dur_min % 60)
    day_dur_str = f"{day_dur_hh:02d}:{day_dur_mm:02d}"

    # ── 3. Reference Midnight & Precise Sunrise JD ───────────────────────────
    ref_jd = sunrise_jd if sunrise_jd is not None else jd
    utc_hours_of_ref = ((ref_jd + 0.5) % 1.0) * 24.0
    local_hours_of_ref = (utc_hours_of_ref + timezone) % 24.0
    midnight_local_jd = ref_jd - local_hours_of_ref / 24.0
    
    if "sunrise_jd" in sun_data and sun_data["sunrise_jd"] is not None:
        sunrise_precise_jd = sun_data["sunrise_jd"]
    else:
        sunrise_precise_jd = midnight_local_jd + (sunrise_local_min / 60.0 - timezone) / 24.0

    # ── 4. Evaluate Panchang elements at SUNRISE (Traditional Standard) ──────
    sun_sr, moon_sr = _sidereal_longitudes(
        sunrise_precise_jd, ayanamsha_type, calculation_mode, longitude=longitude
    )
    diff_sr = _normalize_angle(moon_sr - sun_sr)
    
    tithi_val_sr   = diff_sr / 12.0
    tithi_idx      = int(tithi_val_sr) % 30
    tithi_progress = tithi_val_sr - int(tithi_val_sr)
    tithi          = TITHIS[tithi_idx]
    next_tithi     = TITHIS[(tithi_idx + 1) % 30]
    paksha         = "Shukla (Waxing)" if tithi_idx < 15 else "Krishna (Waning)"
    paksha_nep     = "शुक्लपक्ष" if tithi_idx < 15 else "कृष्णपक्ष"

    nakshatra_val_sr = moon_sr / (360.0 / 27.0)
    nakshatra_idx    = int(nakshatra_val_sr) % 27
    nak_progress     = nakshatra_val_sr - int(nakshatra_val_sr)
    nakshatra        = NAKSHATRAS[nakshatra_idx]
    next_nakshatra   = NAKSHATRAS[(nakshatra_idx + 1) % 27]
    pada             = int(nak_progress * 4) + 1

    yoga_long_sr = _normalize_angle(sun_sr + moon_sr)
    yoga_val_sr  = yoga_long_sr / (360.0 / 27.0)
    yoga_idx     = int(yoga_val_sr) % 27
    yoga_progress= yoga_val_sr - int(yoga_val_sr)
    yoga         = YOGAS[yoga_idx]
    next_yoga    = YOGAS[(yoga_idx + 1) % 27]

    # Calculate karana index and progress
    karana_val_sr  = diff_sr / 6.0
    karana_idx_all = int(karana_val_sr) % 60
    kar_progress   = karana_val_sr - int(karana_val_sr)
    
    # Helper function to get karana object from 0-based index in 60-karana cycle
    def get_karana_obj_from_index_0based(idx_0based: int) -> Dict:
        return _get_karana(int(idx_0based) % 60)
    
    # Get karana objects for current, previous, and next karana
    current_karana_obj = get_karana_obj_from_index_0based(karana_idx_all)
    prev_karana_idx = (karana_idx_all - 1) % 60
    next_karana_idx = (karana_idx_all + 1) % 60
    prev_karana_obj = get_karana_obj_from_index_0based(prev_karana_idx)
    next_karana_obj = get_karana_obj_from_index_0based(next_karana_idx)
    
    # round_min is needed for transition time rounding in SURYA_SIDDHANTA mode
    round_min = (calculation_mode == "SURYA_SIDDHANTA")
    
    # Calculate start of current karana (end of previous karana)
    karana_start_jd = calculate_karana_transition(
        sunrise_precise_jd, prev_karana_idx, ayanamsha_type, calculation_mode, longitude=longitude
    )
    karana_start_time = _jd_to_local_hhmmss_panchang(karana_start_jd, midnight_local_jd, round_to_minute=round_min) if karana_start_jd else ""
    
    # Calculate end of current karana
    karana_end_jd = calculate_karana_transition(
        sunrise_precise_jd, karana_idx_all, ayanamsha_type, calculation_mode, longitude=longitude
    )
    karana_end_time = _jd_to_local_hhmmss_panchang(karana_end_jd, midnight_local_jd, round_to_minute=round_min) if karana_end_jd else ""
    
    # For full representation, calculate end of next karana (start of karana after next)
    karana_end_jd2 = None
    karana_end_time2 = ""
    if karana_end_jd is not None:
        karana_end_jd2 = calculate_karana_transition(
            karana_end_jd + 0.001, next_karana_idx, ayanamsha_type, calculation_mode, longitude=longitude
        )
        karana_end_time2 = _jd_to_local_hhmmss_panchang(karana_end_jd2, midnight_local_jd, round_to_minute=round_min) if karana_end_jd2 else ""
    
    # Calculate durations for full representation
    if karana_start_jd is not None and karana_end_jd is not None:
        duration_since_start_days = sunrise_precise_jd - karana_start_jd
        duration_since_start_seconds = duration_since_start_days * 86400.0
        duration_since_start_hours = int(duration_since_start_seconds // 3600)
        duration_since_start_minutes = int((duration_since_start_seconds % 3600) // 60)
        # Ensure we don't have negative due to floating point
        if duration_since_start_hours < 0:
            duration_since_start_hours = 0
            duration_since_start_minutes = 0
        duration_since_start_str = f"{duration_since_start_hours:02d}:{duration_since_start_minutes:02d}"
        
        duration_until_end_days = karana_end_jd - sunrise_precise_jd
        duration_until_end_seconds = duration_until_end_days * 86400.0
        duration_until_end_hours = int(duration_until_end_seconds // 3600)
        duration_until_end_minutes = int((duration_until_end_seconds % 3600) // 60)
        if duration_until_end_hours < 0:
            duration_until_end_hours = 0
            duration_until_end_minutes = 0
        duration_until_end_str = f"{duration_until_end_hours:02d}:{duration_until_end_minutes:02d}"
    else:
        # Fallback if we couldn't calculate the transition times
        duration_since_start_str = "00:00"
        duration_until_end_str = "00:00"
    
    # Convert to Devanagari digits if needed
    if calculation_mode == "SURYA_SIDDHANTA":
        duration_since_start_nepali = surya_siddhanta.to_devanagari_num(duration_since_start_str)
        duration_until_end_nepali = surya_siddhanta.to_devanagari_num(duration_until_end_str)
    else:
        duration_since_start_nepali = duration_since_start_str
        duration_until_end_nepali = duration_until_end_str
    
    # Karana object for output (current karana)
    karana = current_karana_obj
    # Set third_karana for compatibility (the karana after the current one)
    third_karana = next_karana_obj
    
    # Build full representation strings
    karana_full_nepali = f"{prev_karana_obj['nepali']}, {duration_since_start_nepali} बजेपछि {karana['nepali']}, {duration_until_end_nepali} बजेउप्रान्त {next_karana_obj['nepali']}"
    karana_full_name = f"{prev_karana_obj['name']}, {duration_since_start_str} after {karana['name']}, {duration_until_end_str} after {next_karana_obj['name']}"
    # For compatibility with existing code that expects certain keys, we keep the following:
    # Note: The existing code in the return statement uses:
    #   "name":          karana["name"],
    #   "nepali":        karana["nepali"],
    #   "index":         karana_idx_all + 1,   # 1-based index in the 60-cycle? 
    #   "progress":      kar_progress * 100,
    #   "end_time":      karana_end_time,
    #   "next_name":     next_karana_obj["name"],
    #   "next_nepali":   next_karana_obj["nepali"],
    #   "next_end_time": karana_end_time2,
    #   "third_name":    third_karana["name"],   # we keep this for compatibility but may not be accurate
    #   "third_nepali":  third_karana["nepali"],
    #   "full_nepali":   ...,                   # we will override this below
    #   "full_name":     ...,                   # we will override this below
    # We will compute the full representation separately.

    # Anandadi yoga
    anandadi_weekday_offsets = [0, 24, 20, 16, 12, 8, 4]
    anandadi_idx = (nakshatra_idx + anandadi_weekday_offsets[vara_idx]) % 28
    anandadi_name = ANANDADI_YOGAS[anandadi_idx]

    # ── 5. Mathematical Transition Times ──────────────────────
    tithi_end_jd = calculate_tithi_transition(
        sunrise_precise_jd, tithi_idx, ayanamsha_type, calculation_mode, longitude=longitude
    )
    tithi_end_time = _jd_to_local_hhmmss_panchang(tithi_end_jd, midnight_local_jd, round_to_minute=round_min) if tithi_end_jd else ""

    nak_end_jd = calculate_nakshatra_transition(
        sunrise_precise_jd, nakshatra_idx, ayanamsha_type, calculation_mode, longitude=longitude
    )
    nakshatra_end_time = _jd_to_local_hhmmss_panchang(nak_end_jd, midnight_local_jd, round_to_minute=round_min) if nak_end_jd else ""

    yoga_end_jd = calculate_yoga_transition(
        sunrise_precise_jd, yoga_idx, ayanamsha_type, calculation_mode, longitude=longitude
    )
    yoga_end_time = _jd_to_local_hhmmss_panchang(yoga_end_jd, midnight_local_jd, round_to_minute=round_min) if yoga_end_jd else ""

    karana_end_jd = calculate_karana_transition(
        sunrise_precise_jd, karana_idx_all, ayanamsha_type, calculation_mode, longitude=longitude
    )
    karana_end_time = _jd_to_local_hhmmss_panchang(karana_end_jd, midnight_local_jd, round_to_minute=round_min) if karana_end_jd else ""

    karana_end_time2 = ""
    if karana_end_jd is not None:
        karana_end_jd2 = calculate_karana_transition(
            karana_end_jd + 0.001, (karana_idx_all + 1) % 60, ayanamsha_type, calculation_mode, longitude=longitude
        )
        karana_end_time2 = _jd_to_local_hhmmss_panchang(karana_end_jd2, midnight_local_jd, round_to_minute=round_min) if karana_end_jd2 else ""

    # Full multi-karana representation for Nepali Patro standard
    karana_full_nepali = ""
    karana_full_name = ""
    if calculation_mode == "SURYA_SIDDHANTA":
        sun_mid, moon_mid = _sidereal_longitudes(midnight_local_jd, ayanamsha_type, calculation_mode, longitude=longitude)
        k_mid = int(((moon_mid - sun_mid) % 360.0) / 6.0) % 60
        # Convert 0-based to 1-based for _get_karana
        k_mid_1based = (k_mid + 1) % 60
        if k_mid_1based == 0:
            k_mid_1based = 60
        prev_k_obj = _get_karana(k_mid_1based)
        if k_mid != karana_idx_all:
            # Transition happened early morning between midnight and sunrise
            vs_m, vm_m = surya_siddhanta.get_daily_motions(midnight_local_jd, longitude=longitude)
            rel_m = (vm_m - vs_m) if (vm_m - vs_m) > 0.1 else 12.0
            b_mid = ((k_mid + 1) * 6.0) % 360.0
            rem_m = (b_mid - ((moon_mid - sun_mid) % 360.0)) % 360.0
            hrs_early = (rem_m / rel_m) * 24.0
            early_h = int(hrs_early)
            early_mi = int(round((hrs_early % 1) * 60))
            early_str = surya_siddhanta.to_devanagari_num(f"{early_h:02d}:{early_mi:02d}")
            early_str_en = f"{early_h:02d}:{early_mi:02d}"
            t_short_ne = surya_siddhanta.to_devanagari_num(tithi_end_time[:5]) if tithi_end_time else ""
            t_short_en = tithi_end_time[:5] if tithi_end_time else ""
            karana_full_nepali = f"{prev_k_obj['nepali']}, {early_str} बजेपछि {karana['nepali']}, {t_short_ne} बजेउप्रान्त {third_karana['nepali']}"
            karana_full_name = f"{prev_k_obj['name']}, {early_str_en} after {karana['name']}, {t_short_en} after {third_karana['name']}"
        elif karana_end_time:
            t_short = surya_siddhanta.to_devanagari_num(karana_end_time[:5])
            karana_full_nepali = f"{karana['nepali']}, {t_short} बजेउप्रान्त {next_karana_obj['nepali']}"
            karana_full_name = f"{karana['name']}, {karana_end_time[:5]} after {next_karana_obj['name']}"


    # ── 6. Era, Month, and Samvatsara ─────────────────────────────────────────
    # Calculate BS year dynamically from sunrise_jd (or jd) if not provided
    if bs_year is None:
        ref_jd = sunrise_jd if sunrise_jd is not None else jd
        ad_year, ad_month, ad_day = _jd_to_ad_date(ref_jd, timezone)
        bs_year = _ad_to_bs_year(ad_year, ad_month, ad_day)
    
    samvatsara_name = get_samvatsara(bs_year)
    ns_year = bs_year - 937
    ns_era  = get_ns_era(ns_year)

    adhika_status = get_adhika_month_status(
        sunrise_jd or jd, ayanamsha_type, calculation_mode
    )
    lunar_month = get_lunar_month(
        sunrise_jd or jd, ayanamsha_type, calculation_mode,
        _cached_adhika_status=adhika_status,
    )

    decl = sun_data.get("sun_declination", 0.0)
    eot  = sun_data.get("equation_of_time_min", 0.0)

    # Chandra Rashi at sunrise
    chandra_rashi_idx = int(moon_sr // 30.0) % 12
    chandra_rashi = {
        "name": RASHIS[chandra_rashi_idx]["name"],
        "nepali": RASHIS[chandra_rashi_idx]["nepali"],
        "index": chandra_rashi_idx + 1,
    }

    # Compute Bhadra (Vishti Karana) details
    bhadra_info = _compute_bhadra(
        karana_idx_all=karana_idx_all,
        karana_start_jd=karana_start_jd,
        karana_end_jd=karana_end_jd,
        karana_end_jd2=karana_end_jd2,
        chandra_rashi_idx=chandra_rashi_idx,
        midnight_local_jd=midnight_local_jd,
        round_to_minute=round_min
    )

    # Dinaman, Kranti, Velantara
    dinman = sun_data.get("dinman", day_dur_str)
    dinman_ghati = sun_data.get("dinman_ghati", "")
    dinman_ghati_nepali = sun_data.get("dinman_ghati_nepali", "")
    kranti_str = sun_data.get("kranti", "")
    belantar_str = sun_data.get("belantar", "")

    # Planetary positions at sunrise
    planetary_positions_result = None
    if calculation_mode == "SURYA_SIDDHANTA":
        # Nepali Patro: Sun & Moon from Surya Siddhanta (matches NP best),
        # other planets from Swiss Ephemeris LAHIRI (matches NP best)
        ss_pos = surya_siddhanta.all_sidereal_positions(sunrise_precise_jd, longitude)
        
        # Get Swiss Lahiri positions for other planets
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
        swiss_pos = {}
        for name, body in [("Mars", swe.MARS), ("Mercury", swe.MERCURY), 
                           ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS), 
                           ("Saturn", swe.SATURN), ("Rahu", swe.MEAN_NODE)]:
            try:
                res = swe.calc_ut(sunrise_precise_jd, body, flags)
                swiss_pos[name] = res[0][0]
            except Exception:
                pass
        
        planetary_positions_result = {}
        rashi_names = [
            ("Aries", "मेष"), ("Taurus", "वृष"), ("Gemini", "मिथुन"), ("Cancer", "कर्कट"),
            ("Leo", "सिंह"), ("Virgo", "कन्या"), ("Libra", "तुला"), ("Scorpio", "वृश्चिक"),
            ("Sagittarius", "धनु"), ("Capricorn", "मकर"), ("Aquarius", "कुम्भ"), ("Pisces", "मीन")
        ]
        DEV_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
        def to_dev(num):
            return str(num).translate(DEV_DIGITS)
        
        def format_planet(graha, sid_lon):
            r = int(sid_lon // 30)
            rem = sid_lon % 30.0
            d = int(rem)
            rem_m = (rem - d) * 60.0
            m = int(rem_m)
            s = int(round((rem_m - m) * 60.0))
            if s >= 60:
                m += 1
                s -= 60
            if m >= 60:
                d += 1
                m -= 60
            r_name, r_nep = rashi_names[r % 12]
            fmt_ne = f"{to_dev(r)}|{to_dev(d)}|{to_dev(m)}|{to_dev(s)}"
            return {
                "longitude": sid_lon,
                "rashi_index": r,
                "rashi_name": r_name,
                "rashi_nepali": r_nep,
                "degrees": d,
                "minutes": m,
                "seconds": s,
                "formatted": fmt_ne,
                "formatted_en": f"{r}|{d}|{m}|{s}",
            }
        
        # Sun and Moon from Surya Siddhanta (matches NP best)
        planetary_positions_result["Sun"] = format_planet("Sun", ss_pos["Sun"])
        planetary_positions_result["Moon"] = format_planet("Moon", ss_pos["Moon"])
        
        # Other planets from Swiss Lahiri (matches NP best)
        for graha in ["Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]:
            if graha in swiss_pos:
                planetary_positions_result[graha] = format_planet(graha, swiss_pos[graha])
        
        # Ketu is opposite Rahu
        if "Rahu" in planetary_positions_result:
            rahu_lon = planetary_positions_result["Rahu"]["longitude"]
            ketu_lon = (rahu_lon + 180.0) % 360.0
            planetary_positions_result["Ketu"] = format_planet("Ketu", ketu_lon)

    else:
        # DRIK mode - use Swiss Ephemeris or analytical fallback with ayanamsha
        T = julian.jd_to_julian_centuries(sunrise_precise_jd)
        aya_val = ayanamsha.get_ayanamsha(ayanamsha_type, T)
        swiss_pos = planetary_positions.get_swiss_positions(sunrise_precise_jd)
        if swiss_pos is not None:
            planetary_positions_result = {}
            for graha, (trop_lon, trop_lat) in swiss_pos.items():
                sid_lon = (trop_lon - aya_val) % 360.0
                r = int(sid_lon // 30)
                rem = sid_lon % 30.0
                d = int(rem)
                rem_m = (rem - d) * 60.0
                m = int(rem_m)
                s = int(round((rem_m - m) * 60.0))
                if s >= 60:
                    m += 1
                    s -= 60
                if m >= 60:
                    d += 1
                    m -= 60
                rashi_names = [
                    ("Aries", "मेष"), ("Taurus", "वृष"), ("Gemini", "मिथुन"), ("Cancer", "करकट"),
                    ("Leo", "सिंह"), ("Virgo", "कन्या"), ("Libra", "तुला"), ("Scorpio", "वृशचिक"),
                    ("Sagittarius", "धनु"), ("Capricorn", "मकर"), ("Aquarius", "कुम्भ"), ("Pisces", "मीन")
                ]
                r_name, r_nep = rashi_names[r % 12]
                DEV_DIGITS = str.maketrans("0123456789", "ॆेैॉॊोौ्ॎॏ")
                def to_dev(num):
                    return str(num).translate(DEV_DIGITS)
                fmt_ne = f"{to_dev(r)}|{to_dev(d)}|{to_dev(m)}|{to_dev(s)}"
                planetary_positions_result[graha] = {
                    "longitude": sid_lon,
                    "rashi_index": r,
                    "rashi_name": r_name,
                    "rashi_nepali": r_nep,
                    "degrees": d,
                    "minutes": m,
                    "seconds": s,
                    "formatted": fmt_ne,
                    "formatted_en": f"{r}|{d}|{m}|{s}",
                }
        else:
            # Analytical fallback
            trop_pos = planetary_positions.get_all_tropical_positions(T, jd=sunrise_precise_jd)
            planetary_positions_result = {}
            for graha, (trop_lon, trop_lat) in trop_pos.items():
                sid_lon = (trop_lon - aya_val) % 360.0
                r = int(sid_lon // 30)
                rem = sid_lon % 30.0
                d = int(rem)
                rem_m = (rem - d) * 60.0
                m = int(rem_m)
                s = int(round((rem_m - m) * 60.0))
                if s >= 60:
                    m += 1
                    s -= 60
                if m >= 60:
                    d += 1
                    m -= 60
                rashi_names = [
                    ("Aries", "मेष"), ("Taurus", "वृष"), ("Gemini", "मिथुन"), ("Cancer", "करकट"),
                    ("Leo", "सिंह"), ("Virgo", "कन्या"), ("Libra", "तुला"), ("Scorpio", "वृशचहिक"),
                    ("Sagittarius", "धनु"), ("Capricorn", "मकर"), ("Aquarius", "कुम्भ"), ("Pisces", "मीन")
                ]
                r_name, r_nep = rashi_names[r % 12]
                DEV_DIGITS = str.maketrans("0123456789", "ॆेैॉॊोौ्ॎॏ")
                def to_dev(num):
                    return str(num).translate(DEV_DIGITS)
                fmt_ne = f"{to_dev(r)}|{to_dev(d)}|{to_dev(m)}|{to_dev(s)}"
                planetary_positions_result[graha] = {
                    "longitude": sid_lon,
                    "rashi_index": r,
                    "rashi_name": r_name,
                    "rashi_nepali": r_nep,
                    "degrees": d,
                    "minutes": m,
                    "seconds": s,
                    "formatted": fmt_ne,
                    "formatted_en": f"{r}|{d}|{m}|{s}",
                }



    return {
        "calculation_mode": calculation_mode,
        "lunar_month": lunar_month,
        "month_type": adhika_status["month_type"],
        "month_type_nepali": adhika_status["month_type_nepali"],
        "solar_ingress_count": adhika_status["solar_ingress_count"],
        "previous_new_moon_jd": adhika_status.get("previous_new_moon_jd"),
        "next_new_moon_jd": adhika_status.get("next_new_moon_jd"),
        "vara": {
            "name":   vara["name"],
            "nepali": vara["nepali"],
            "index":  vara_idx
        },
        "tithi": {
            "name":         tithi["name"],
            "nepali":       tithi["nepali"],
            "index":        tithi_idx + 1,
            "paksha":       paksha,
            "paksha_nepali": paksha_nep,
            "progress":     tithi_progress * 100,
            "end_time":     tithi_end_time,
            "next_name":    next_tithi["name"],
            "next_nepali":  next_tithi["nepali"],
        },
        "nakshatra": {
            "name":        nakshatra["name"],
            "nepali":      nakshatra["nepali"],
            "index":       nakshatra_idx + 1,
            "pada":        pada,
            "progress":    nak_progress * 100,
            "end_time":    nakshatra_end_time,
            "next_name":   next_nakshatra["name"],
            "next_nepali": next_nakshatra["nepali"],
        },
        "yoga": {
            "name":        yoga["name"],
            "nepali":      yoga["nepali"],
            "index":       yoga_idx + 1,
            "progress":    yoga_progress * 100,
            "end_time":    yoga_end_time,
            "next_name":   next_yoga["name"],
            "next_nepali": next_yoga["nepali"],
        },
        "karana": {
            "name":          karana["name"],
            "nepali":        karana["nepali"],
            "index":         karana_idx_all + 1,
            "progress":      kar_progress * 100,
            "end_time":      karana_end_time,
            "next_name":     next_karana_obj["name"],
            "next_nepali":   next_karana_obj["nepali"],
            "next_end_time": karana_end_time2,
            "third_name":    third_karana["name"],
            "third_nepali":  third_karana["nepali"],
            "full_nepali":   karana_full_nepali,
            "full_name":     karana_full_name,
        },
        "anandadi_yoga": {
            "name":   anandadi_name,
            "nepali": anandadi_name
        },
        "chandra_rashi":      chandra_rashi,
        "bhadra":             bhadra_info,
        "sunrise": {
            "time": sunrise_str
        },
        "sunset": {
            "time": sunset_str
        },
        "day_duration":       day_dur_str,
        "dinman":             dinman,
        "dinman_ghati":       dinman_ghati,
        "dinman_ghati_nepali": dinman_ghati_nepali,
        "samvatsara":         samvatsara_name,
        "nepal_samvat": {
            "year": ns_year,
            "era":  ns_era
        },
        "sun_declination":    decl,
        "equation_of_time":   eot,
        "equation_of_time_min": eot,
        "kranti":             kranti_str,
        "belantar":           belantar_str,
        "velantara":          belantar_str,
        "planetary_positions": planetary_positions_result,
    }
