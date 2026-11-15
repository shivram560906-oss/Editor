import math
from typing import Dict, Any, List

SIGNS = [
    "Aries (मेष)", "Taurus (वृष)", "Gemini (मिथुन)", "Cancer (कर्क)",
    "Leo (सिंह)", "Virgo (कन्या)", "Libra (तुला)", "Scorpio (वृश्चिक)",
    "Sagittarius (धनु)", "Capricorn (मकर)", "Aquarius (कुम्भ)", "Pisces (मीन)"
]

def get_varga_sign(varga: str, longitude: float) -> int:
    longitude = longitude % 360.0
    sign_number = int(longitude / 30.0) % 12 + 1
    deg = longitude % 30.0

    if varga == "D1":
        return sign_number

    elif varga == "D2":
        # Hora (wealth) — पाराशर BPHS अनुसार:
        # विषम राशि (Odd signs): पहिलो १५° → सिंह (5, Sun's Hora), दोस्रो १५° → कर्क (4, Moon's Hora)
        # सम राशि (Even signs): पहिलो १५° → कर्क (4), दोस्रो १५° → सिंह (5)
        half = int(deg / 15.0)  # 0 = first 15°, 1 = second 15°
        if sign_number % 2 != 0:   # Odd sign (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius)
            return 5 if half == 0 else 4   # Leo → Cancer
        else:                               # Even sign (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces)
            return 4 if half == 0 else 5   # Cancer → Leo

    elif varga == "D3":
        # Drekkana (siblings/courage): three 10° parts.
        # 1st drekkana = same sign, 2nd = 5th from it, 3rd = 9th from it.
        part = int(deg / 10.0)
        return (sign_number - 1 + part * 4) % 12 + 1

    elif varga == "D4":
        # Chaturthamsha (property/fortune): four 7.5° parts, start from same sign.
        part = int(deg / 7.5)
        return (sign_number - 1 + part * 3) % 12 + 1

    elif varga == "D9":
        part = int(deg / (30.0 / 9.0))
        if sign_number in [1, 5, 9]:    # Fire
            return (0 + part) % 12 + 1
        elif sign_number in [2, 6, 10]: # Earth
            return (9 + part) % 12 + 1
        elif sign_number in [3, 7, 11]: # Air
            return (6 + part) % 12 + 1
        else:                           # Water
            return (3 + part) % 12 + 1

    elif varga == "D7":
        # Saptamsha (children/progeny): odd signs start from the same sign,
        # even signs start from the seventh sign from the natal sign.
        part = min(6, int(deg / (30.0 / 7.0)))
        start_offset = 0 if sign_number % 2 != 0 else 6
        return (sign_number - 1 + start_offset + part) % 12 + 1

    elif varga == "D10":
        # Dashamsha (karma/profession) — पाराशर BPHS:
        # विषम राशि: आफ्नै राशिबाट सुरु
        # सम राशि: ९औं राशिबाट सुरु (sign_number - 1 + 9 - 1 = sign_number + 7)
        part = int(deg / 3.0)
        if sign_number % 2 != 0:   # Odd signs: start from same sign
            return (sign_number - 1 + part) % 12 + 1
        else:                       # Even signs: start from 9th sign
            return (sign_number - 1 + 9 + part) % 12 + 1

    elif varga == "D12":
        part = int(deg / 2.5)
        return (sign_number - 1 + part) % 12 + 1

    elif varga == "D16":
        part = int(deg / 1.875)
        if sign_number in [1, 4, 7, 10]:
            return (0 + part) % 12 + 1
        elif sign_number in [2, 5, 8, 11]:
            return (4 + part) % 12 + 1
        else:
            return (8 + part) % 12 + 1

    elif varga == "D20":
        part = int(deg / 1.5)
        if sign_number in [1, 4, 7, 10]:
            return (0 + part) % 12 + 1
        elif sign_number in [2, 5, 8, 11]:
            return (8 + part) % 12 + 1
        else:
            return (4 + part) % 12 + 1

    elif varga == "D24":
        part = int(deg / 1.25)
        if sign_number % 2 != 0:
            return (4 + part) % 12 + 1
        else:
            return (3 + part) % 12 + 1

    elif varga == "D27":
        part = int(deg / (30.0 / 27.0))
        if sign_number in [1, 5, 9]:
            return (0 + part) % 12 + 1
        elif sign_number in [2, 6, 10]:
            return (3 + part) % 12 + 1
        elif sign_number in [3, 7, 11]:
            return (6 + part) % 12 + 1
        else:
            return (9 + part) % 12 + 1

    elif varga == "D30":
        # Trimshamsha (misfortune/evil) — पाराशर BPHS:
        # विषम राशि (Odd signs):
        #   0°–5°   → Mars  (Aries = 1)
        #   5°–10°  → Saturn (Aquarius = 11)
        #   10°–18° → Jupiter (Sagittarius = 9)
        #   18°–25° → Mercury (Gemini = 3)
        #   25°–30° → Venus (Libra = 7)  ← NOTE: Libra, NOT Taurus
        # सम राशि (Even signs):
        #   0°–5°   → Venus  (Taurus = 2)
        #   5°–12°  → Mercury (Virgo = 6)  ← NOTE: Virgo, NOT Gemini
        #   12°–20° → Jupiter (Pisces = 12) ← NOTE: Pisces, NOT Sagittarius
        #   20°–25° → Saturn (Capricorn = 10) ← NOTE: Capricorn, NOT Aquarius
        #   25°–30° → Mars (Scorpio = 8)   ← NOTE: Scorpio, NOT Aries
        if sign_number % 2 != 0:   # Odd signs
            if deg < 5.0:   return 1    # Aries (Mars)
            elif deg < 10.0: return 11  # Aquarius (Saturn)
            elif deg < 18.0: return 9   # Sagittarius (Jupiter)
            elif deg < 25.0: return 3   # Gemini (Mercury)
            else:            return 7   # Libra (Venus) — सही
        else:                           # Even signs
            if deg < 5.0:   return 2    # Taurus (Venus)
            elif deg < 12.0: return 6   # Virgo (Mercury) — सही
            elif deg < 20.0: return 12  # Pisces (Jupiter) — सही
            elif deg < 25.0: return 10  # Capricorn (Saturn) — सही
            else:            return 8   # Scorpio (Mars) — सही

    elif varga == "D40":
        part = int(deg / 0.75)
        if sign_number % 2 != 0:
            return (0 + part) % 12 + 1
        else:
            return (6 + part) % 12 + 1

    elif varga == "D45":
        part = int(deg / (30.0 / 45.0))
        if sign_number in [1, 4, 7, 10]:
            return (0 + part) % 12 + 1
        elif sign_number in [2, 5, 8, 11]:
            return (4 + part) % 12 + 1
        else:
            return (8 + part) % 12 + 1

    elif varga == "D60":
        part = int(deg / 0.5)
        if sign_number % 2 != 0:
            return (0 + part) % 12 + 1
        else:
            return (6 + part) % 12 + 1

    return sign_number


def is_vargottama(longitude: float) -> bool:
    """Return True if the planet is Vargottama (same sign in D1 and D9).

    BPHS (Brihat Parashar Hora Shastra) considers a planet Vargottama when
    its D1 (Rashi) sign and D9 (Navamsa) sign are identical. Such a planet
    is considered extremely strong — equivalent to being in its own sign.

    Args:
        longitude: Sidereal longitude in degrees (0–360).

    Returns:
        True if D1 sign == D9 sign (Vargottama condition).
    """
    d1_sign = get_varga_sign("D1", longitude)
    d9_sign = get_varga_sign("D9", longitude)
    return d1_sign == d9_sign


def get_planet_exaltation_debilitation(planet_name: str, sign_number: int) -> str:
    exaltation_signs = {
        "Sun": 1,
        "Moon": 2,
        "Mars": 10,
        "Mercury": 6,
        "Jupiter": 4,
        "Venus": 12,
        "Saturn": 7,
        "Rahu": 2,
        "Ketu": 8
    }
    debilitation_signs = {
        "Sun": 7,
        "Moon": 8,
        "Mars": 4,
        "Mercury": 12,
        "Jupiter": 10,
        "Venus": 6,
        "Saturn": 1,
        "Rahu": 8,
        "Ketu": 2
    }
    if exaltation_signs.get(planet_name) == sign_number:
        return "exalted"
    elif debilitation_signs.get(planet_name) == sign_number:
        return "debilitated"
    return ""

def calculate_varga_positions(lagna_sidereal: float, planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    vargas = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]
    result = {}

    # Pre-compute Vargottama for each planet (D1==D9 sign check) — BPHS rule.
    # This is a natal-chart property so we compute it once outside the varga loop.
    vargottama_map = {
        p["name"]: is_vargottama(p["sidereal_longitude"])
        for p in planets
        if "sidereal_longitude" in p
    }

    for v in vargas:
        lagna_v_sign = get_varga_sign(v, lagna_sidereal)

        varga_planets = []
        for p in planets:
            p_v_sign = get_varga_sign(v, p["sidereal_longitude"])
            v_house = (p_v_sign - lagna_v_sign) % 12 + 1
            exalt = get_planet_exaltation_debilitation(p["name"], p_v_sign)

            varga_planets.append({
                "name": p["name"],
                "sidereal_longitude": p["sidereal_longitude"],
                "sign_number": p_v_sign,
                "sign_name": SIGNS[p_v_sign - 1],
                "longitude_in_sign": p["sidereal_longitude"] % 30.0,
                "house": v_house,
                "is_retrograde": p["is_retrograde"],
                "is_combust": p["is_combust"],
                "relationship": p["relationship"],
                "exaltation_state": exalt,
                # Vargottama — D1==D9, BPHS strength indicator. Included on every varga
                # chart so the frontend can highlight Vargottama planets everywhere.
                "is_vargottama": vargottama_map.get(p["name"], False),
            })

        result[v] = {
            "lagna": {
                "longitude": lagna_sidereal,
                "sign_number": lagna_v_sign,
                "sign_name": SIGNS[lagna_v_sign - 1],
                "longitude_in_sign": lagna_sidereal % 30.0
            },
            "planets": varga_planets
        }

    return result

