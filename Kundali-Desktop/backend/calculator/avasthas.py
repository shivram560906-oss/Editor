"""Planetary Avasthas (states).

Implements the two classical avastha schemes:
1. **Bala Avastha** (age/state by longitude in sign): Bala, Kumara, Yuva,
   Vriddha, Mrita — based on which third of the sign the planet occupies.
2. **Deeptadi Avastha** (dignity-based): Deepta, Swastha, Pramudita, etc.,
   derived from the planet's relationship to its current sign (exaltation,
   own sign, friendly, etc.).
"""
from typing import Dict, List, Any
from .constants import SIGN_LORDS




EXALTATION_LORD = {  # sign → planet exalted there
    1: "Sun", 2: "Moon", 3: None, 4: "Jupiter", 5: None, 6: "Mercury",
    7: "Saturn", 8: None, 9: None, 10: "Mars", 11: None, 12: "Venus",
}

# Natural friendships (simplified Naisargika Maitri): friend / neutral / enemy.
FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury", "Saturn"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}


def _long_in_sign(p: Dict[str, Any]) -> float:
    return float(p.get("longitude_in_sign", p.get("longitude", 0.0) % 30.0) or 0.0)


def _sign_number(p: Dict[str, Any]) -> int:
    return int(p.get("sign_number", 1))


def bala_avastha(longitude_in_sign: float) -> Dict[str, str]:
    """Age-based avastha from the planet's position within its sign (0–30°)."""
    if longitude_in_sign < 6:
        state, ne = "Bala (Infant)", "बाल"
    elif longitude_in_sign < 12:
        state, ne = "Kumara (Youth)", "कुमार"
    elif longitude_in_sign < 18:
        state, ne = "Yuva (Adult)", "युवा"
    elif longitude_in_sign < 24:
        state, ne = "Vriddha (Old)", "वृद्ध"
    else:
        state, ne = "Mrita (Dead)", "मृत"
    return {"state": state, "nepali": ne}


def deeptadi_avastha(name: str, sign: int) -> Dict[str, str]:
    """Dignity-based avastha (Deeptadi)."""
    lord = SIGN_LORDS.get(sign)
    exalt = EXALTATION_LORD.get(sign)
    if exalt == name:
        return {"state": "Deepta (Exalted)", "nepali": "दीप्त (उच्च)"}
    if lord == name:
        return {"state": "Swastha (Own sign)", "nepali": "स्वस्थ (स्वराशि)"}
    if name in FRIENDS.get(lord, set()):
        return {"state": "Pramudita (Friendly)", "nepali": "प्रमुदित (मित्र)"}
    if name in ENEMIES.get(lord, set()):
        return {"state": "Deena (Inimical)", "nepali": "दीन (शत्रु)"}
    return {"state": "Shanta (Neutral)", "nepali": "शान्त (सम)"}


def calculate_avasthas(planets: List[Dict[str, Any]], lagna_sign: int) -> Dict[str, Any]:
    """Compute Bala + Deeptadi avasthas for the 7 main grahas."""
    results = {}
    for p in planets:
        name = p.get("name")
        if name not in SIGN_LORDS.values() and name not in FRIENDS:
            continue
        sign = _sign_number(p)
        long_in = _long_in_sign(p)
        bala = bala_avastha(long_in)
        deepta = deeptadi_avastha(name, sign)
        results[name] = {
            "sign_number": sign,
            "longitude_in_sign": round(long_in, 3),
            "bala_avastha": bala,
            "deeptadi_avastha": deepta,
        }
    return {"planets": results}
