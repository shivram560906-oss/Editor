import importlib
import math
from typing import Any, Dict, Tuple, Optional

try:  # Dynamic import keeps analytical fallback usable before dependencies install.
    swe: Any = importlib.import_module("swisseph")
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    swe = None


def get_ephemeris_version() -> str:
    """Return a provenance string for the active planetary-position backend.

    Used by the calculation payload so every saved report records which
    ephemeris produced its positions. Examples:
    ``"swisseph 2.10.3"`` or ``"analytical-fallback"``.
    """
    if swe is None:
        return "analytical-fallback"
    try:
        version = getattr(swe, "version", None)
        if not version:
            version = swe.version()  # older bindings expose a callable
        return f"swisseph {version}"
    except Exception:
        return "swisseph (version unavailable)"

# Helper mathematical constants and functions
PI_2 = 2.0 * math.pi

def dtor(d: float) -> float:
    return d * math.pi / 180.0

def rtod(r: float) -> float:
    return r * 180.0 / math.pi

def rev(angle: float) -> float:
    """Normalize angle to 0..360 degrees."""
    return angle % 360.0

def solve_kepler(M_rad: float, e: float) -> float:
    """Solves Kepler's Equation E - e*sin(E) = M using iteration."""
    E = M_rad
    for _ in range(15):
        delta = E - e * math.sin(E) - M_rad
        if abs(delta) < 1e-7:
            break
        E = E - delta / (1.0 - e * math.cos(E))
    return E

# Keplerian Orbital Elements at J2000.0
# Elements: (a_0, a_dot, e_0, e_dot, I_0, I_dot, L_0, L_dot, w_0, w_dot, node_0, node_dot)
# Time T is in Julian Centuries from J2000.0
PLANET_ELEMENTS = {
    # Earth (used to get heliocentric Earth vector, equivalent to Sun geocentric)
    "Earth": {
        "a": (1.00000261, -0.00000003),
        "e": (0.01671123, -0.00003842),
        "i": (-0.00001531, -0.01294668),
        "L": (100.46457166, 35999.37244981),
        "w": (102.93768193, 0.32327364),
        "node": (0.0, 0.0)
    },
    "Mercury": {
        "a": (0.38709893, 0.0),
        "e": (0.20563069, 0.00002040),
        "i": (7.00497902, -0.00594749),
        "L": (252.25032350, 149472.67411175),
        "w": (77.45645, 0.15901),
        "node": (48.33076, -0.12534)
    },
    "Venus": {
        "a": (0.72333199, 0.0),
        "e": (0.00677323, -0.00004776),
        "i": (3.39467605, -0.00078890),
        "L": (181.97909950, 58517.81538729),
        "w": (131.53298, 0.00213),
        "node": (76.68069, -0.27769)
    },
    "Mars": {
        "a": (1.52371034, 0.00000184),
        "e": (0.09340510, 0.00009132),
        "i": (1.84969142, -0.00072447),
        "L": (355.44656795, 19140.30268499),
        "w": (336.04084, 0.44388),
        "node": (49.55953, -0.29252)
    },
    "Jupiter": {
        "a": (5.20288700, -0.00011607),
        "e": (0.04838624, -0.00013253),
        "i": (1.30439695, -0.00172324),
        "L": (34.39644051, 3034.74612775),
        "w": (14.72847, 0.19112),
        "node": (100.47392, 0.20469)
    },
    "Saturn": {
        "a": (9.53667594, -0.00125060),
        "e": (0.05415060, -0.00036762),
        "i": (2.48599187, 0.00193609),
        "L": (50.07747140, 1222.11379404),
        "w": (92.43194, -0.41897),
        "node": (113.66242, -0.28867)
    }
}

def get_heliocentric_vector(planet_name: str, T: float) -> Tuple[float, float, float]:
    """Calculates heliocentric rectangular coordinates (x, y, z) for a planet at time T."""
    elems = PLANET_ELEMENTS[planet_name]
    
    # Calculate orbital elements at Julian century T
    a = elems["a"][0] + elems["a"][1] * T
    e = elems["e"][0] + elems["e"][1] * T
    i = dtor(elems["i"][0] + elems["i"][1] * T)
    L = dtor(rev(elems["L"][0] + elems["L"][1] * T))
    w = dtor(rev(elems["w"][0] + elems["w"][1] * T))
    node = dtor(rev(elems["node"][0] + elems["node"][1] * T))
    
    # Mean anomaly M
    M = L - w
    E = solve_kepler(M, e)
    
    # Coordinates in orbital plane
    x_rect = a * (math.cos(E) - e)
    y_rect = a * math.sqrt(1.0 - e * e) * math.sin(E)
    
    # Argument of perihelion w_orb
    w_orb = w - node
    
    # Transform to ecliptic 3D coordinates
    cos_w = math.cos(w_orb)
    sin_w = math.sin(w_orb)
    cos_node = math.cos(node)
    sin_node = math.sin(node)
    cos_i = math.cos(i)
    sin_i = math.sin(i)
    
    x = x_rect * (cos_w * cos_node - sin_w * sin_node * cos_i) - y_rect * (sin_w * cos_node + cos_w * sin_node * cos_i)
    y = x_rect * (cos_w * sin_node + sin_w * cos_node * cos_i) - y_rect * (sin_w * sin_node - cos_w * cos_node * cos_i)
    z = x_rect * (sin_w * sin_i) + y_rect * (cos_w * sin_i)
    
    return x, y, z

def get_geocentric_coordinates(planet_name: str, T: float) -> Tuple[float, float]:
    """
    Returns geocentric Ecliptic Longitude and Latitude (Sayana/Tropical) 
    in degrees for a major planet.
    """
    px, py, pz = get_heliocentric_vector(planet_name, T)
    ex, ey, ez = get_heliocentric_vector("Earth", T)
    
    # Geocentric vector = Planet vector - Earth vector
    gx = px - ex
    gy = py - ey
    gz = pz - ez
    
    # Convert to spherical coordinates
    long_rad = math.atan2(gy, gx)
    lat_rad = math.atan2(gz, math.sqrt(gx*gx + gy*gy))
    
    longitude = rev(rtod(long_rad))
    latitude = rtod(lat_rad)
    
    return longitude, latitude

def get_sun_position(T: float) -> Tuple[float, float]:
    """
    Returns the Sun's geocentric longitude and latitude (tropical).
    Uses an analytical solar longitude formula rather than low-precision Earth orbital vectors.
    """
    # Mean longitude of the Sun
    L0 = rev(280.46646 + 36000.76983 * T + 0.0003032 * T * T)
    # Mean anomaly of the Sun
    M = rev(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    M_r = dtor(M)

    # Equation of center
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_r)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M_r)
         + 0.000289 * math.sin(3 * M_r))

    # True longitude
    sun_true_lon = L0 + C

    # Apparent longitude corrected for nutation and aberration
    omega = 125.04 - 1934.136 * T
    sun_app_lon = sun_true_lon - 0.00569 - 0.00478 * math.sin(dtor(omega))

    return rev(sun_app_lon), 0.0


def get_moon_position(T: float) -> Tuple[float, float]:
    """Return the Moon's geocentric tropical longitude and latitude.

    Longitude uses the complete Meeus table 47.A periodic series.  The former
    abbreviated series contained several wrong arguments and omitted the
    eccentricity factors, causing its angular error (and therefore Panchang
    transition-time error) to grow noticeably from one day to the next.
    """
    L0 = rev(218.3164477 + 481267.88123421 * T - 0.0015786 * T*T
             + T*T*T / 538841.0 - T*T*T*T / 65194000.0)
    D = rev(297.8501921 + 445267.1114034 * T - 0.0018819 * T*T
            + T*T*T / 545868.0 - T*T*T*T / 113065000.0)
    M = rev(357.5291092 + 35999.0502909 * T - 0.0001536 * T*T
            + T*T*T / 24490000.0)
    M_prime = rev(134.9633964 + 477198.8675055 * T + 0.0087414 * T*T
                  + T*T*T / 69699.0 - T*T*T*T / 14712000.0)
    F = rev(93.2720950 + 483202.0175233 * T - 0.0036539 * T*T
            - T*T*T / 3526000.0 + T*T*T*T / 863310000.0)

    D_r, M_r, Mp_r, F_r = map(dtor, (D, M, M_prime, F))
    eccentricity = 1.0 - 0.002516 * T - 0.0000074 * T * T
    longitude_terms = (
        (0,0,1,0,6288774),(2,0,-1,0,1274027),(2,0,0,0,658314),
        (0,0,2,0,213618),(0,1,0,0,-185116),(0,0,0,2,-114332),
        (2,0,-2,0,58793),(2,-1,-1,0,57066),(2,0,1,0,53322),
        (2,-1,0,0,45758),(0,1,-1,0,-40923),(1,0,0,0,-34720),
        (0,1,1,0,-30383),(2,0,0,-2,15327),(0,0,1,2,-12528),
        (0,0,1,-2,10980),(4,0,-1,0,10675),(0,0,3,0,10034),
        (4,0,-2,0,8548),(2,1,-1,0,-7888),(2,1,0,0,-6766),
        (1,0,-1,0,-5163),(1,1,0,0,4987),(2,-1,1,0,4036),
        (2,0,2,0,3994),(4,0,0,0,3861),(2,0,-3,0,3665),
        (0,1,-2,0,-2689),(2,0,-1,2,-2602),(2,-1,-2,0,2390),
        (1,0,1,0,-2348),(2,-2,0,0,2236),(0,1,2,0,-2120),
        (0,2,0,0,-2069),(2,-2,-1,0,2048),(2,0,1,-2,-1773),
        (2,0,0,2,-1595),(4,-1,-1,0,1215),(0,0,2,2,-1110),
        (3,0,-1,0,-892),(2,1,1,0,-810),(4,-1,-2,0,759),
        (0,2,-1,0,-713),(2,2,-1,0,-700),(2,1,-2,0,691),
        (2,-1,0,-2,596),(4,0,1,0,549),(0,0,4,0,537),
        (4,-1,0,0,520),(1,0,-2,0,-487),(2,1,0,-2,-399),
        (0,0,2,-2,-381),(1,1,1,0,351),(3,0,-2,0,-340),
        (4,0,-3,0,330),(2,-1,2,0,327),(0,2,1,0,-323),
        (1,1,-1,0,299),(2,0,3,0,294),
    )
    sigma_l = 0.0
    for d_mult, m_mult, mp_mult, f_mult, coefficient in longitude_terms:
        sigma_l += (coefficient * eccentricity ** abs(m_mult)
                    * math.sin(d_mult*D_r + m_mult*M_r + mp_mult*Mp_r + f_mult*F_r))

    a1 = dtor(rev(119.75 + 131.849 * T))
    a2 = dtor(rev(53.09 + 479264.290 * T))
    sigma_l += 3958 * math.sin(a1) + 1962 * math.sin(dtor(L0) - F_r) + 318 * math.sin(a2)
    moon_long = rev(L0 + sigma_l / 1_000_000.0)

    # Latitude perturbations
    lat_corr = 0.0
    lat_corr += 5.128122 * math.sin(F_r)
    lat_corr += 0.280602 * math.sin(Mp_r + F_r)
    lat_corr += 0.277693 * math.sin(Mp_r - F_r)
    lat_corr += 0.173237 * math.sin(2.0 * D_r - F_r)
    lat_corr += 0.055413 * math.sin(2.0 * D_r + F_r - Mp_r)
    lat_corr += 0.046272 * math.sin(2.0 * D_r - F_r - Mp_r)
    lat_corr += 0.032573 * math.sin(2.0 * D_r + F_r)
    lat_corr += 0.017198 * math.sin(2.0 * Mp_r + F_r)
    lat_corr += 0.009267 * math.sin(2.0 * D_r + F_r + Mp_r)
    lat_corr += 0.008823 * math.sin(2.0 * Mp_r - F_r)
    lat_corr += 0.008247 * math.sin(2.0 * D_r - F_r - M_r - Mp_r)
    lat_corr += 0.004323 * math.sin(2.0 * D_r - F_r + Mp_r)
    lat_corr += 0.004200 * math.sin(2.0 * D_r - F_r - Mp_r)
    lat_corr += 0.003372 * math.sin(2.0 * Mp_r - F_r - 2.0 * D_r)
    lat_corr += 0.002472 * math.sin(2.0 * D_r + F_r - M_r - Mp_r)

    moon_lat = lat_corr

    return moon_long, moon_lat

def _swiss_longitude(jd: float, body: int) -> Optional[Tuple[float, float]]:
    """Return Swiss apparent geocentric tropical longitude/latitude when available."""
    if swe is None:
        return None
    try:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        raw = swe.calc_ut(jd, body, flags)
        # New swisseph (>= 2.10) returns 3-tuple: (values, retflag, errmsg)
        # Old swisseph returns 2-tuple: (values, retflag)
        values = raw[0] if isinstance(raw[0], (tuple, list)) else raw
        return rev(float(values[0])), float(values[1])
    except Exception:
        return None


def get_swiss_positions(jd: float, node_type: str = "MEAN") -> Optional[Dict[str, Tuple[float, float]]]:
    """Calculate chart bodies through Swiss Ephemeris, returning None on unavailable data.
    Returns only the 7 classical Jyotish planets + Rahu + Ketu to avoid breaking
    downstream calculators that don't handle outer planets (Uranus/Neptune/Pluto).
    """
    if swe is None:
        return None
    bodies = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
    }
    result: Dict[str, Tuple[float, float]] = {}
    for name, body in bodies.items():
        position = _swiss_longitude(jd, body)
        if position is None:
            return None
        result[name] = position
    node_body = swe.TRUE_NODE if str(node_type).upper() == "TRUE" else swe.MEAN_NODE
    node = _swiss_longitude(jd, node_body)
    if node is None:
        return None
    result["Rahu"] = node
    result["Ketu"] = (rev(node[0] + 180.0), -node[1])
    return result


def get_swiss_declination(jd: float, body_name: str) -> Optional[float]:
    """Apparent equatorial declination in degrees, or None when unavailable.

    All Swiss access in this module goes through the module-level ``swe``
    handle so callers (notably the calculation regression guard) can switch the
    engine to the analytical fallback by setting ``swe = None``.  Callers must
    not import ``swisseph`` directly, otherwise results would depend on whether
    the optional dependency happens to be installed.
    """
    if swe is None:
        return None
    body = getattr(swe, str(body_name).upper(), None)
    if body is None:
        return None
    try:
        raw = swe.calc_ut(jd, body, swe.FLG_EQUATORIAL | swe.FLG_SWIEPH)
        values = raw[0] if isinstance(raw[0], (tuple, list)) else raw
        return float(values[1])
    except Exception:
        return None


def get_rahu_position(T: float) -> float:
    """
    Returns the Mean Node (Rahu) tropical longitude.
    Rahu is the Ascending Node.
    """
    # Rahu mean longitude = 125.0445550 - 1934.1361849 * T
    return rev(125.0445550 - 1934.1361849 * T + 0.0020762 * T*T)

def get_ketu_position(rahu_long: float) -> float:
    """Ketu is always 180 degrees opposite of Rahu."""
    return rev(rahu_long + 180.0)

def get_all_tropical_positions(T: float, jd: Optional[float] = None, node_type: str = "MEAN") -> Dict[str, Tuple[float, float]]:
    """Calculate tropical positions, preferring Swiss Ephemeris without breaking the fallback."""
    if jd is not None:
        swiss_positions = get_swiss_positions(jd, node_type)
        if swiss_positions is not None:
            return swiss_positions
    positions = {}
    positions["Sun"] = get_sun_position(T)
    positions["Moon"] = get_moon_position(T)
    
    for planet in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
        positions[planet] = get_geocentric_coordinates(planet, T)
        
    rahu = get_rahu_position(T)
    positions["Rahu"] = (rahu, 0.0)
    positions["Ketu"] = (get_ketu_position(rahu), 0.0)
    
    return positions
