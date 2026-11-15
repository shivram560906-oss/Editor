import importlib
import math
from typing import Dict, List, Tuple

try:
    swe = importlib.import_module("swisseph")
except ImportError:  # pragma: no cover
    swe = None
from .julian import jd_to_julian_centuries
from .planetary_positions import rev, dtor, rtod

def get_obliquity(T: float) -> float:
    """Calculates the obliquity of the ecliptic (in degrees) for Julian Century T."""
    # Obliquity formula (Laskar, 1986)
    return 23.43929111 - (46.8150 * T - 0.00059 * T*T + 0.001813 * T*T*T) / 3600.0

def get_sidereal_time(jd: float, longitude: float) -> float:
    """
    Calculates Local Sidereal Time (LST) in degrees.
    longitude is east positive, west negative.
    """
    T = jd_to_julian_centuries(jd)
    
    # Greenwich Mean Sidereal Time (GMST) in degrees
    # Formula from IAU 1982
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T*T - T*T*T / 38710000.0
    gmst = rev(gmst)
    
    # Local Sidereal Time (LST)
    lst = rev(gmst + longitude)
    return lst

def calculate_lagna(jd: float, latitude: float, longitude: float) -> float:
    """
    Calculates the geocentric Tropical Ascendant (Lagna) in degrees.
    latitude: North positive, South negative.
    longitude: East positive, West negative.
    """
    T = jd_to_julian_centuries(jd)
    lst = get_sidereal_time(jd, longitude)
    
    lst_rad = dtor(lst)
    eps_rad = dtor(get_obliquity(T))
    lat_rad = dtor(latitude)
    
    # Ascendant formula:
    # tan(Asc) = cos(LST) / (-sin(LST)*cos(eps) - tan(lat)*sin(eps))
    # Using atan2 to handle quadrants properly:
    # y = cos(LST)
    # x = -sin(LST)*cos(eps) - tan(lat)*sin(eps)
    y = math.cos(lst_rad)
    x = -math.sin(lst_rad) * math.cos(eps_rad) - math.tan(lat_rad) * math.sin(eps_rad)
    
    lagna_rad = math.atan2(y, x)
    lagna = rev(rtod(lagna_rad))
    
    return lagna

def get_zodiac_sign(longitude: float) -> Tuple[int, str]:
    """
    Returns the 1-indexed zodiac sign number (1 = Aries, 12 = Pisces)
    and the name of the sign for a given longitude.
    """
    signs = [
        "Aries (मेष)", "Taurus (वृष)", "Gemini (मिथुन)", "Cancer (कर्क)",
        "Leo (सिंह)", "Virgo (कन्या)", "Libra (तुला)", "Scorpio (वृश्चिक)",
        "Sagittarius (धनु)", "Capricorn (मकर)", "Aquarius (कुम्भ)", "Pisces (मीन)"
    ]
    sign_idx = int(longitude / 30.0) % 12
    return sign_idx + 1, signs[sign_idx]

def get_house_placements(planetary_sidereal_longs: Dict[str, float], lagna_sidereal_long: float) -> Dict[str, int]:
    """
    Determines which house each planet belongs to, using the standard Rashi-Bhava system.
    House 1 is the zodiac sign containing the Lagna.
    House 2 is the next sign, etc.
    """
    lagna_sign_idx = int(lagna_sidereal_long / 30.0) % 12
    placements = {}
    
    for planet, long in planetary_sidereal_longs.items():
        planet_sign_idx = int(long / 30.0) % 12
        # House calculation: (planet_sign - lagna_sign) % 12 + 1
        house = (planet_sign_idx - lagna_sign_idx) % 12 + 1
        placements[planet] = house
        
    return placements


def _midpoint(a: float, b: float) -> float:
    """Circular midpoint on the forward zodiac arc from a to b."""
    return rev(a + ((b - a) % 360.0) / 2.0)


def calculate_house_cusps(
    jd: float, latitude: float, longitude: float, system: str = "WHOLE_SIGN"
) -> List[float]:
    """Return twelve tropical house cusps for Whole Sign, Shripati, or Placidus."""
    key = str(system or "WHOLE_SIGN").upper()
    asc = calculate_lagna(jd, latitude, longitude)
    if key == "WHOLE_SIGN":
        start = math.floor(asc / 30.0) * 30.0
        return [rev(start + i * 30.0) for i in range(12)]
    if key == "PLACIDUS":
        if swe is None:
            raise ValueError("Placidus houses require pyswisseph")
        cusps, _ = swe.houses_ex(jd, latitude, longitude, b"P", 0)
        # pyswisseph releases expose either twelve values or a traditional
        # 1-indexed thirteen-value sequence with a dummy zero at index 0.
        values = cusps[1:13] if len(cusps) == 13 else cusps[:12]
        return [rev(float(value)) for value in values]
    if key != "SHRIPATI":
        raise ValueError("house_system must be WHOLE_SIGN, SHRIPATI, or PLACIDUS")

    # Sripati: trisect each quadrant between Ascendant, IC, Descendant and MC.
    if swe is not None:
        _, ascmc = swe.houses_ex(jd, latitude, longitude, b"P", 0)
        asc, mc = rev(float(ascmc[0])), rev(float(ascmc[1]))
    else:
        lst = get_sidereal_time(jd, longitude)
        mc = rev(rtod(math.atan2(math.sin(dtor(lst)), math.cos(dtor(lst)) * math.cos(dtor(get_obliquity(jd_to_julian_centuries(jd)))))))
    anchors = {0: asc, 3: rev(mc + 180.0), 6: rev(asc + 180.0), 9: mc, 12: asc}
    cusps = [0.0] * 12
    for start_index in (0, 3, 6, 9):
        start, end = anchors[start_index], anchors[start_index + 3]
        arc = (end - start) % 360.0
        for step in range(3):
            cusps[start_index + step] = rev(start + arc * step / 3.0)
    return cusps


def calculate_bhava_boundaries(cusps: List[float]) -> List[Tuple[float, float]]:
    """Return start/end sandhis around each cusp."""
    if len(cusps) != 12:
        raise ValueError("exactly 12 house cusps are required")
    return [(_midpoint(cusps[i - 1], cusps[i]), _midpoint(cusps[i], cusps[(i + 1) % 12])) for i in range(12)]


def get_bhava_chalit_placements(planetary_longs: Dict[str, float], cusps: List[float]) -> Dict[str, int]:
    """Place each longitude inside circular cusp-midpoint house boundaries."""
    boundaries = calculate_bhava_boundaries(cusps)
    result: Dict[str, int] = {}
    for name, longitude in planetary_longs.items():
        for index, (start, end) in enumerate(boundaries):
            arc = (end - start) % 360.0
            if (longitude - start) % 360.0 < arc:
                result[name] = index + 1
                break
    return result
