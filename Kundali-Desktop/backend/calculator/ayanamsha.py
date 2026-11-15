import importlib
from typing import Optional

try:
    swe = importlib.import_module("swisseph")
except ImportError:  # pragma: no cover
    swe = None

# Swiss Ephemeris sidereal modes. Names are kept stable for API clients.
SWISS_AYANAMSHA_MODES = {
    "FAGAN_BRADLEY": "FAGAN_BRADLEY", "DELUCE": "DELUCE", "RAMAN": "RAMAN",
    "USHASHASHI": "USHASHASHI", "KRISHNAMURTI": "KRISHNAMURTI", "DJWHAL_KHUL": "DJWHAL_KHUL",
    "YUKTESHWAR": "YUKTESHWAR", "JN_BHASIN": "JN_BHASIN", "LAHIRI": "LAHIRI",
    "DELUCE_IAU": "DELUCE_IAU", "BABYL_KUGLER1": "BABYL_KUGLER1", "BABYL_KUGLER2": "BABYL_KUGLER2",
    "BABYL_KUGLER3": "BABYL_KUGLER3", "BABYL_HUBER": "BABYL_HUBER", "ARYABHATA": "ARYABHATA",
    "SURYASIDDHANTA": "SURYASIDDHANTA", "SURYASIDDHANTA_MSUN": "SURYASIDDHANTA_MSUN",
    "ARYABHATA_522": "ARYABHATA_522", "KP": "KRISHNAMURTI", "TROPICAL": "TROPICAL",
}


def get_ayanamsha(ayanamsha_type: str, T: float, custom_offset: Optional[float] = None) -> float:
    """Return Swiss ayanamsha when available, otherwise preserve calibrated legacy values."""
    key = str(ayanamsha_type or "LAHIRI").upper()
    if key.startswith("CUSTOM:"):
        try:
            custom_offset = float(key.split(":", 1)[1])
        except ValueError as exc:
            raise ValueError("CUSTOM ayanamsha must contain a numeric offset") from exc
        key = "CUSTOM"
    if key == "CUSTOM":
        if custom_offset is None or not -360.0 <= float(custom_offset) <= 360.0:
            raise ValueError("custom_offset must be between -360 and 360 degrees")
        return float(custom_offset)
    if key == "TROPICAL":
        return 0.0
    if swe is not None:
        mode_name = SWISS_AYANAMSHA_MODES.get(key)
        mode = getattr(swe, f"SIDM_{mode_name}", None) if mode_name else None
        if mode is not None:
            try:
                swe.set_sid_mode(mode)
                return float(swe.get_ayanamsa_ut(2451545.0 + T * 36525.0))
            except Exception:
                pass
    legacy = {
        "RAMAN": 22.460148 + 1.396042 * T + 0.000308 * T * T,
        "KP": 23.84361111 + 1.39736111 * T + 0.000308 * T * T,
    }
    return legacy.get(key, 23.85305556 + 1.396971278 * T + 0.0003086 * T * T)

def convert_tropical_to_sidereal(tropical_long: float, ayanamsha: float) -> float:
    """Converts tropical longitude to sidereal longitude by subtracting the ayanamsha."""
    return (tropical_long - ayanamsha) % 360.0
