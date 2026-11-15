"""
Complete BPHS (Brihat Parashara Hora Shastra) Yoga Detection Engine
Covers: Pancha Mahapurusha, Raja, Dhana, Chandra, Surya, Arishta,
        Spiritual, Dosha, and Miscellaneous Yogas
"""
from typing import List, Dict, Any, Optional
from .planet_names import get_planet_label
from .drishti import does_planet_aspect_planet
from .constants import (
    SIGN_LORDS, OWN_SIGNS, EXALTATION_SIGNS, DEBILITATION_SIGNS,
    KENDRA_HOUSES, TRIKONA_HOUSES, DUSTHANA_HOUSES, UPACHAYA_HOUSES,
    NATURAL_BENEFICS, NATURAL_MALEFICS,
)


# ─────────────────────────────────────────────
# Constants & Lookup Tables
# ─────────────────────────────────────────────
#  सबै स्थिरांक constants.py बाट import गरिएको छ — माथि हेर्नुहोस् ।

# Yoga categories
CAT_MAHAPURUSHA = "mahapurusha"
CAT_RAJA        = "raja"
CAT_DHANA       = "dhana"
CAT_CHANDRA     = "chandra"
CAT_SURYA       = "surya"
CAT_ARISHTA     = "arishta"
CAT_DOSHA       = "dosha"
CAT_SPIRITUAL   = "spiritual"
CAT_MISC        = "misc"
CAT_VIPARITA    = "viparita"
CAT_PARIVARTANA = "parivartana"
CAT_NABHAS      = "nabhas"
CAT_CONJUNCTION = "conjunction"
CAT_VIDYA       = "vidya"
CAT_VIVAHA      = "vivaha"
CAT_AYUR        = "ayur"
CAT_SANYASA     = "sanyasa"

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────

def _p(planets: List[Dict], name: str) -> Optional[Dict]:
    return next((p for p in planets if p.get("name") == name), None)

def _house(planet: Optional[Dict]) -> Optional[int]:
    return planet.get("house") if planet else None

def _sign(planet: Optional[Dict]) -> Optional[int]:
    return planet.get("sign_number") if planet else None

def _same_house(a: Optional[Dict], b: Optional[Dict]) -> bool:
    return bool(a and b and a.get("house") == b.get("house"))

def _house_dist(from_h: int, to_h: int) -> int:
    return ((to_h - from_h) % 12) + 1

def _kendra_from(ref: int, target: int) -> bool:
    return _house_dist(ref, target) in [1, 4, 7, 10]

def _trikona_from(ref: int, target: int) -> bool:
    return _house_dist(ref, target) in [1, 5, 9]

def _sign_of_house(house: int, lagna_sign: int) -> int:
    return ((lagna_sign - 1 + house - 1) % 12) + 1

def _lord_of(house: int, lagna_sign: int) -> str:
    return SIGN_LORDS[_sign_of_house(house, lagna_sign)]

def _is_lord_of(planet_name: str, house: int, lagna_sign: int) -> bool:
    return _lord_of(house, lagna_sign) == planet_name

def _mutual_exchange(a: Optional[Dict], b: Optional[Dict], lagna_sign: int) -> bool:
    if not a or not b:
        return False
    ha, hb = a.get("house"), b.get("house")
    if ha is None or hb is None:
        return False
    return _is_lord_of(a["name"], hb, lagna_sign) and _is_lord_of(b["name"], ha, lagna_sign)


def _planets_related(a: Optional[Dict], b: Optional[Dict], lagna_sign: int) -> bool:
    """True if planets share sambandha: conjunction, parivartana, OR mutual Parashari drishti.

    BPHS defines yoga-forming relationship (sambandha) as any of:
    1. युति (conjunction) — same house
    2. परिवर्तन (mutual exchange) — each in the other's sign
    3. दृष्टि (aspect) — a aspects b OR b aspects a
    """
    if not a or not b:
        return False
    # 1. Conjunction
    if _same_house(a, b):
        return True
    # 2. Mutual exchange
    if _mutual_exchange(a, b, lagna_sign):
        return True
    # 3. Drishti (Parashari aspect — either direction)
    if does_planet_aspect_planet(a, b) or does_planet_aspect_planet(b, a):
        return True
    return False

def _is_exalted(planet: Optional[Dict]) -> bool:
    if not planet:
        return False
    return planet.get("exaltation_state") == "exalted"

def _is_own_sign(planet: Optional[Dict]) -> bool:
    if not planet:
        return False
    name = planet.get("name", "")
    sign = planet.get("sign_number")
    return sign in OWN_SIGNS.get(name, [])

def _is_strong_in_kendra(planet: Optional[Dict]) -> bool:
    if not planet:
        return False
    return (_is_exalted(planet) or _is_own_sign(planet)) and planet.get("house") in KENDRA_HOUSES

def _pn(name: str, lang: str = "ne") -> str:
    return get_planet_label(name, lang)

def _yoga(id_, name, nepali, category, severity, cause_en, cause_ne, result_en, result_ne,
          remedy_en, remedy_ne, references=None, strength_pct=None, planets_involved=None) -> Dict:
    return {
        "id": id_, "name": name, "nepali": nepali,
        "category": category, "severity": severity,
        "cause_en": cause_en, "cause_ne": cause_ne,
        "result_en": result_en, "result_ne": result_ne,
        "remedy_en": remedy_en, "remedy_ne": remedy_ne,
        "references": references or [],
        "strength_pct": strength_pct,
        "planets_involved": planets_involved or [],
    }

# ─────────────────────────────────────────────
# PANCHA MAHAPURUSHA YOGAS (5 महापुरुष योग)
# ─────────────────────────────────────────────

def detect_ruchaka(planets, lagna_sign):
    mars = _p(planets, "Mars")
    if mars and (_is_exalted(mars) or _is_own_sign(mars)) and mars.get("house") in KENDRA_HOUSES:
        return _yoga("ruchaka", "Ruchaka Yoga", "रुचक योग", CAT_MAHAPURUSHA, "auspicious",
            "Mars occupies its own sign (Aries/Scorpio) or exaltation (Capricorn) in a Kendra house.",
            "मङ्गल आफ्नो राशि (मेष/वृश्चिक) वा उच्चको राशि (मकर) मा केन्द्रभावमा छ।",
            "Strong physique, military or athletic success, courageous leadership, and wealth through land or property.",
            "बलियो शरीर, सैन्य वा खेलकुदमा सफलता, साहसी नेतृत्व, र भूमि-सम्पत्तिद्वारा धन लाभ।",
            "Chant 'Om Angarakaya Namah' on Tuesdays; donate red lentils and copper items.",
            "मङ्गलवार 'ॐ अङ्गारकाय नमः' जप गर्नुहोस्; रातो दाल र तामाका वस्तु दान गर्नुहोस्।")
    return None

def detect_bhadra(planets, lagna_sign):
    mercury = _p(planets, "Mercury")
    if mercury and (_is_exalted(mercury) or _is_own_sign(mercury)) and mercury.get("house") in KENDRA_HOUSES:
        return _yoga("bhadra", "Bhadra Yoga", "भद्र योग", CAT_MAHAPURUSHA, "auspicious",
            "Mercury is in its own sign (Gemini/Virgo) or exaltation (Virgo) in a Kendra house.",
            "बुध आफ्नो राशि (मिथुन/कन्या) वा उच्चको राशि (कन्या) मा केन्द्रभावमा छ।",
            "Exceptional intellect, communication skills, business acumen, writing talent, and a long prosperous life.",
            "असाधारण बुद्धि, सञ्चार कौशल, व्यापारिक दक्षता, लेखन प्रतिभा, र दीर्घ सुखी जीवन।",
            "Recite 'Om Budhaya Namah' on Wednesdays; donate green items and books.",
            "बुधबार 'ॐ बुधाय नमः' जप गर्नुहोस्; हरियो वस्तु र पुस्तक दान गर्नुहोस्।")
    return None

def detect_hamsa(planets, lagna_sign):
    jupiter = _p(planets, "Jupiter")
    if jupiter and (_is_exalted(jupiter) or _is_own_sign(jupiter)) and jupiter.get("house") in KENDRA_HOUSES:
        return _yoga("hamsa", "Hamsa Yoga", "हंस योग", CAT_MAHAPURUSHA, "auspicious",
            "Jupiter is in its own sign (Sagittarius/Pisces) or exaltation (Cancer) in a Kendra house.",
            "गुरु आफ्नो राशि (धनु/मीन) वा उच्चको राशि (कर्कट) मा केन्द्रभावमा छ।",
            "Wisdom, spiritual devotion, fame, prosperity, and a noble respected character in society.",
            "ज्ञान, आध्यात्मिक भक्ति, यश, समृद्धि, र समाजमा आदरणीय चरित्र।",
            "Chant 'Om Guruve Namah' on Thursdays; offer yellow flowers and turmeric.",
            "गुरुवार 'ॐ गुरवे नमः' जप गर्नुहोस्; पहेँलो फूल र बेसार अर्पण गर्नुहोस्।")
    return None

def detect_malavya(planets, lagna_sign):
    venus = _p(planets, "Venus")
    if venus and (_is_exalted(venus) or _is_own_sign(venus)) and venus.get("house") in KENDRA_HOUSES:
        return _yoga("malavya", "Malavya Yoga", "मालव्य योग", CAT_MAHAPURUSHA, "auspicious",
            "Venus is in its own sign (Taurus/Libra) or exaltation (Pisces) in a Kendra house.",
            "शुक्र आफ्नो राशि (वृष/तुला) वा उच्चको राशि (मीन) मा केन्द्रभावमा छ।",
            "Beauty, artistic gifts, luxury, romantic success, wealth, and a charming influential personality.",
            "सौन्दर्य, कलात्मक प्रतिभा, विलासिता, प्रेम-सम्बन्धमा सफलता, धन, र आकर्षक प्रभावशाली व्यक्तित्व।",
            "Recite 'Om Shukraya Namah' on Fridays; donate white sweets or perfume.",
            "शुक्रवार 'ॐ शुक्राय नमः' जप गर्नुहोस्; सेतो मिठाइ वा इत्र दान गर्नुहोस्।")
    return None

def detect_sasa(planets, lagna_sign):
    saturn = _p(planets, "Saturn")
    if saturn and (_is_exalted(saturn) or _is_own_sign(saturn)) and saturn.get("house") in KENDRA_HOUSES:
        return _yoga("sasa", "Sasa Yoga", "शश योग", CAT_MAHAPURUSHA, "auspicious",
            "Saturn is in its own sign (Capricorn/Aquarius) or exaltation (Libra) in a Kendra house.",
            "शनि आफ्नो राशि (मकर/कुम्भ) वा उच्चको राशि (तुला) मा केन्द्रभावमा छ।",
            "Discipline, endurance, administrative authority, success through sustained effort, and long life.",
            "अनुशासन, सहनशीलता, प्रशासनिक अधिकार, निरन्तर प्रयासबाट सफलता, र दीर्घायु।",
            "Chant 'Om Shanaischaraya Namah' on Saturdays; donate sesame seeds and iron.",
            "शनिवार 'ॐ शनैश्चराय नमः' जप गर्नुहोस्; तिल र फलाम दान गर्नुहोस्।")
    return None

# ─────────────────────────────────────────────
# RAJA YOGAS (राज योग)
# ─────────────────────────────────────────────

def detect_raja_yoga(planets, lagna_sign):
    kendra_lords  = [_lord_of(h, lagna_sign) for h in KENDRA_HOUSES]
    trikona_lords = [_lord_of(h, lagna_sign) for h in TRIKONA_HOUSES]
    found = []
    for planet in planets:
        if planet["name"] in kendra_lords:
            for partner in planets:
                if partner["name"] in trikona_lords and partner["name"] != planet["name"]:
                    # BPHS sambandha: conjunction, parivartana, OR mutual drishti
                    if _planets_related(planet, partner, lagna_sign):
                        found.append((planet, partner))
    if found:
        # Use one canonical order for both languages. Set iteration made otherwise
        # identical Raja Yoga reports vary between Python processes.
        unique_pairs = sorted(
            {(a["name"], b["name"]) for a, b in found},
            reverse=True,
        )
        pairs_en = ", ".join(f"{a} & {b}" for a, b in unique_pairs)
        pairs_ne = ", ".join(
            f"{_pn(a, 'ne')} & {_pn(b, 'ne')}" for a, b in unique_pairs
        )
        return _yoga("raja_yoga", "Raja Yoga", "राज योग", CAT_RAJA, "highly_auspicious",
            f"Kendra lord and Trikona lord are in conjunction, exchange, or mutual aspect ({pairs_en}), forming a powerful royal yoga.",
            f"केन्द्र र त्रिकोण भावका अधिपति ({pairs_ne}) युति, आदानप्रदान, वा परस्पर दृष्टिद्वारा राजयोग बनाउँछन्।",
            "Status, authority, leadership opportunities, and great success in public life.",
            "प्रतिष्ठा, अधिकार, नेतृत्वको अवसर, र सार्वजनिक जीवनमा ठूलो सफलता।",
            "Respect elders and authority figures; wear the gem of the stronger planet.",
            "बुझापाकालाई सम्मान गर्नुहोस्; बलियो ग्रहको रत्न लगाउनुहोस्।")
    return None

def detect_viparita_raja_yoga(planets, lagna_sign):
    found = []
    for house in DUSTHANA_HOUSES:
        ruler = _lord_of(house, lagna_sign)
        planet = _p(planets, ruler)
        if planet and planet.get("house") in DUSTHANA_HOUSES:
            found.append((ruler, planet.get("house")))
    if found:
        det_en = ", ".join([f"{n} in H{h}" for n, h in found])
        det_ne = ", ".join([f"{_pn(n,'ne')} {h} भावमा" for n, h in found])
        return _yoga("viparita_raja_yoga", "Viparita Raja Yoga", "विपरित राज योग", CAT_RAJA, "auspicious",
            f"Dusthana lords in dusthana positions ({det_en}): unexpected rise through adversity.",
            f"दुष्टान भावका अधिपति दुष्टानमा ({det_ne}): विपरीत परिस्थितिमा अप्रत्याशित उन्नति।",
            "Success arising from struggle, resilience in difficult situations, gains through hidden means.",
            "संघर्षबाट सफलता, कठिन अवस्थामा लचकता, लुकेका माध्यमबाट लाभ।",
            "Practice service and discipline through challenges; focus on transforming obstacles into strength.",
            "चुनौतिमा सेवा र अनुशासन अभ्यास गर्नुहोस्; बाधालाई शक्तिमा बदल्नुहोस्।")
    return None

def detect_chamara_yoga(planets, lagna_sign):
    lagna_lord_name = _lord_of(1, lagna_sign)
    lagna_lord = _p(planets, lagna_lord_name)
    jupiter = _p(planets, "Jupiter")
    if (lagna_lord and _is_exalted(lagna_lord) and lagna_lord.get("house") in KENDRA_HOUSES
            and jupiter and _kendra_from(lagna_lord.get("house", 1), jupiter.get("house", 1))):
        return _yoga("chamara_yoga", "Chamara Yoga", "चामर योग", CAT_RAJA, "auspicious",
            "Exalted Lagna lord in Kendra aspected by or conjunct Jupiter creates this rare royal yoga.",
            "केन्द्रमा उच्चको लग्नेश र गुरुको युति वा दृष्टिले यो दुर्लभ राजयोग बनाउँछ।",
            "High intellect, royal honors, fame, eloquence, and a distinguished public career.",
            "उच्च बुद्धि, राजकीय सम्मान, यश, वाक्पटुता, र प्रतिष्ठित सार्वजनिक करियर।",
            "Worship Jupiter on Thursdays; serve scholars and spiritual teachers.",
            "गुरुवार गुरुको पूजा गर्नुहोस्; विद्वान र गुरुजनको सेवा गर्नुहोस्।")
    return None

def detect_mahabhagya_yoga(planets, lagna_sign, birth_time=None):
    sun = _p(planets, "Sun")
    moon = _p(planets, "Moon")
    if not sun or not moon:
        return None
    sun_sign  = sun.get("sign_number", 0)
    moon_sign = moon.get("sign_number", 0)
    ODD_SIGNS = [1, 3, 5, 7, 9, 11]
    EVEN_SIGNS = [2, 4, 6, 8, 10, 12]
    # Day birth: Sun, Moon, Lagna all in odd signs
    if sun_sign in ODD_SIGNS and moon_sign in ODD_SIGNS and lagna_sign in ODD_SIGNS:
        return _yoga("mahabhagya_yoga", "Mahabhagya Yoga (Day)", "महाभाग्य योग (दिन)", CAT_RAJA, "highly_auspicious",
            "Day birth with Sun, Moon, and Lagna all in odd signs — a supreme yoga of great fortune.",
            "दिनको जन्म; सूर्य, चन्द्र र लग्न सबै विषम राशिमा — महाभाग्यको सर्वोच्च योग।",
            "Exceptional fortune, long life, royal comforts, fame, and virtuous character.",
            "असाधारण सौभाग्य, दीर्घायु, राजकीय सुख, यश, र सद्गुणी चरित्र।",
            "Perform Sun and Moon worship; practice gratitude and charitable acts daily.",
            "सूर्य र चन्द्रको पूजा गर्नुहोस्; प्रतिदिन कृतज्ञता र दानको अभ्यास गर्नुहोस्।")
    if sun_sign in EVEN_SIGNS and moon_sign in EVEN_SIGNS and lagna_sign in EVEN_SIGNS:
        return _yoga("mahabhagya_yoga_night", "Mahabhagya Yoga (Night)", "महाभाग्य योग (रात)", CAT_RAJA, "highly_auspicious",
            "Night birth with Sun, Moon, and Lagna all in even signs — supreme fortune yoga.",
            "रातको जन्म; सूर्य, चन्द्र र लग्न सबै सम राशिमा — महाभाग्यको सर्वोच्च योग।",
            "Wealth, fame, long life, and great achievements in one's chosen field.",
            "धन, यश, दीर्घायु, र आफ्नो क्षेत्रमा महान् उपलब्धिहरू।",
            "Perform lunar worship; offer white flowers and rice to the Moon deity.",
            "चन्द्रको पूजा गर्नुहोस्; चन्द्रदेवलाई सेतो फूल र चामल अर्पण गर्नुहोस्।")
    return None

# ─────────────────────────────────────────────
# DHANA YOGAS (धन योग)
# ─────────────────────────────────────────────

def detect_dhana_yoga(planets, lagna_sign):
    lord2  = _lord_of(2, lagna_sign)
    lord11 = _lord_of(11, lagna_sign)
    p2  = _p(planets, lord2)
    p11 = _p(planets, lord11)
    if p2 and p11:
        # BPHS: 2nd and 11th lords in sambandha (conjunction, exchange, or drishti)
        # OR either lord in a trikona (5th/9th) strengthens wealth signification
        if (_planets_related(p2, p11, lagna_sign)
                or p2.get("house") in [5, 9] or p11.get("house") in [5, 9]):
            return _yoga("dhana_yoga", "Dhana Yoga", "धन योग", CAT_DHANA, "auspicious",
                f"Lords of 2nd ({lord2}) and 11th ({lord11}) are associated (conjunction, exchange or aspect), favoring wealth accumulation.",
                f"दोस्रो ({_pn(lord2,'ne')}) र एकादश ({_pn(lord11,'ne')}) भावका अधिपतिको सम्बन्ध (युति, आदानप्रदान वा दृष्टि) ले धनयोग जनाउँछ।",
                "Financial growth, income stability, and favourable accumulation of wealth over time.",
                "आर्थिक वृद्धि, आय स्थिरता, र समय साथ अनुकूल धन संचय।",
                "Offer food to the poor; keep finances organised and avoid impulsive spending.",
                "गरीबलाई भोजन दान गर्नुहोस्; वित्त व्यवस्थित राख्नुहोस् र आवेगमा खर्च नगर्नुहोस्।")
    return None

def detect_lakshmi_yoga(planets, lagna_sign):
    lord9 = _lord_of(9, lagna_sign)
    lagna_lord_name = _lord_of(1, lagna_sign)
    p9   = _p(planets, lord9)
    ll   = _p(planets, lagna_lord_name)
    venus = _p(planets, "Venus")
    if (p9 and ll and venus
            and (_is_exalted(p9) or _is_own_sign(p9)) and p9.get("house") in KENDRA_HOUSES + TRIKONA_HOUSES
            and (_is_exalted(venus) or _is_own_sign(venus))):
        return _yoga("lakshmi_yoga", "Lakshmi Yoga", "लक्ष्मी योग", CAT_DHANA, "highly_auspicious",
            "9th lord strong in Kendra/Trikona and Venus in own/exalted sign — the yoga of Goddess Lakshmi.",
            "नवम भावेश केन्द्र/त्रिकोणमा बलियो र शुक्र स्वगृह/उच्चमा — लक्ष्मी योग।",
            "Great wealth, divine grace, beauty, luxury, strong spiritual merit, and long-lasting prosperity.",
            "महान् धन, दैवी कृपा, सौन्दर्य, विलासिता, बलियो आध्यात्मिक पुण्य र दीर्घकालीन समृद्धि।",
            "Worship Goddess Lakshmi on Fridays; chant 'Om Shrim Mahalakshmiyei Namah'.",
            "शुक्रवार लक्ष्मी माताको पूजा गर्नुहोस्; 'ॐ श्रीं महालक्ष्म्यै नमः' जप गर्नुहोस्।")
    return None

def detect_kubera_yoga(planets, lagna_sign):
    lord2  = _lord_of(2, lagna_sign)
    lord11 = _lord_of(11, lagna_sign)
    p2  = _p(planets, lord2)
    p11 = _p(planets, lord11)
    if p2 and p11 and _planets_related(p2, p11, lagna_sign):
        house = p2.get("house", 0)
        if house in TRIKONA_HOUSES + KENDRA_HOUSES:
            return _yoga("kubera_yoga", "Kubera Yoga", "कुबेर योग", CAT_DHANA, "auspicious",
                f"Lords of 2nd and 11th in sambandha (conjunction, exchange or aspect) in a Kendra/Trikona — wealth like Kubera.",
                f"दोस्रो र एकादश भावका अधिपति केन्द्र/त्रिकोणमा सम्बन्धित — कुबेर जस्तो धन।",
                "Immense wealth, financial security, and ability to accumulate great resources throughout life.",
                "अतुल धन, आर्थिक सुरक्षा, र जीवनभर महान् स्रोत संचय गर्ने क्षमता।",
                "Donate to temples and needy; chant 'Om Yakshaya Kuberaya Namah' on Thursdays.",
                "मन्दिर र आवश्यकतामा दान गर्नुहोस्; गुरुवार 'ॐ यक्षाय कुबेराय नमः' जप गर्नुहोस्।")
    return None

def detect_vasumati_yoga(planets, lagna_sign):
    moon = _p(planets, "Moon")
    if not moon:
        return None
    moon_house = moon.get("house", 0)
    benefics_in_upachaya_from_moon = [
        p for p in planets
        if p["name"] in NATURAL_BENEFICS
        and _house_dist(moon_house, p.get("house", 0)) in [3, 6, 10, 11]
    ]
    if len(benefics_in_upachaya_from_moon) >= 2:
        names = ", ".join([_pn(p["name"], "en") for p in benefics_in_upachaya_from_moon])
        names_ne = ", ".join([_pn(p["name"], "ne") for p in benefics_in_upachaya_from_moon])
        return _yoga("vasumati_yoga", "Vasumati Yoga", "वसुमती योग", CAT_DHANA, "auspicious",
            f"Natural benefics ({names}) in Upachaya houses from Moon, generating wealth through effort.",
            f"प्राकृतिक शुभ ग्रहहरू ({names_ne}) चन्द्रबाट उपचय भावमा — प्रयासबाट धन उत्पन्न।",
            "Wealth through persistent effort, business success, and gradual financial improvement over time.",
            "निरन्तर प्रयासबाट धन, व्यापारमा सफलता, र समयसँगै आर्थिक सुधार।",
            "Work diligently without shortcuts; offer white flowers to the Moon on Mondays.",
            "सोमवार चन्द्रमालाई सेतो फूल अर्पण गर्नुहोस्; बिना शर्तको परिश्रम गर्नुहोस्।")
    return None

# ─────────────────────────────────────────────
# CHANDRA (MOON) YOGAS
# ─────────────────────────────────────────────

def detect_gaja_kesari(planets, lagna_sign):
    moon    = _p(planets, "Moon")
    jupiter = _p(planets, "Jupiter")
    if moon and jupiter and _kendra_from(moon.get("house", 1), jupiter.get("house", 1)):
        return _yoga("gaja_kesari", "Gaja Kesari Yoga", "गज केसरी योग", CAT_CHANDRA, "highly_auspicious",
            "Jupiter is in a Kendra house from the Moon, creating mental strength, fortune, and reputation.",
            "चन्द्रबाट केन्द्र भावमा गुरुको स्थितिले मानसिक बल, सफलता र सम्मानको योग बनाउँछ।",
            "Strong intellect, public respect, stable career growth, generous nature, and wise decision-making.",
            "बलियो बुद्धि, सार्वजनिक सम्मान, स्थिर करियर वृद्धि, उदार स्वभाव र बुद्धिमान निर्णय।",
            "Chant 'Om Brim Brihaspataye Namah' on Thursdays; serve elders and donate yellow items.",
            "गुरुवार 'ॐ ब्रीं बृहस्पतये नमः' जप; वयस्कको सेवा र पहेँलो वस्तु दान।")
    return None

def detect_sunapha(planets, lagna_sign):
    moon = _p(planets, "Moon")
    if not moon:
        return None
    moon_house = moon.get("house", 0)
    in_2nd_from_moon = [
        p for p in planets
        if p["name"] not in ["Sun", "Moon", "Rahu", "Ketu"]
        and _house_dist(moon_house, p.get("house", 0)) == 2
    ]
    if in_2nd_from_moon:
        names = ", ".join([_pn(p["name"], "en") for p in in_2nd_from_moon])
        names_ne = ", ".join([_pn(p["name"], "ne") for p in in_2nd_from_moon])
        return _yoga("sunapha", "Sunapha Yoga", "सुनफा योग", CAT_CHANDRA, "auspicious",
            f"Planet(s) in the 2nd house from Moon ({names}): self-earned wealth and strong willpower.",
            f"चन्द्रबाट दोस्रो भावमा ग्रह ({names_ne}): स्वअर्जित धन र बलियो इच्छाशक्ति।",
            "Self-made wealth, leadership ability, royal-like status, and strong personal identity.",
            "स्वउपार्जित धन, नेतृत्व क्षमता, राजकीय जस्तो मर्यादा, र बलियो व्यक्तिगत पहिचान।",
            "Strengthen the Moon with white flowers and milk offerings on Mondays.",
            "सोमवार सेतो फूल र दूध अर्पण गरेर चन्द्रलाई बलियो बनाउनुहोस्।")
    return None

def detect_anapha(planets, lagna_sign):
    moon = _p(planets, "Moon")
    if not moon:
        return None
    moon_house = moon.get("house", 0)
    in_12th_from_moon = [
        p for p in planets
        if p["name"] not in ["Sun", "Moon", "Rahu", "Ketu"]
        and _house_dist(moon_house, p.get("house", 0)) == 12
    ]
    if in_12th_from_moon:
        names = ", ".join([_pn(p["name"], "en") for p in in_12th_from_moon])
        names_ne = ", ".join([_pn(p["name"], "ne") for p in in_12th_from_moon])
        return _yoga("anapha", "Anapha Yoga", "अनफा योग", CAT_CHANDRA, "auspicious",
            f"Planet(s) in the 12th house from Moon ({names}): renown, good health, and generosity.",
            f"चन्द्रबाट बाह्रौं भावमा ग्रह ({names_ne}): प्रसिद्धि, राम्रो स्वास्थ्य र उदारता।",
            "Health, fame, spiritual inclinations, generosity, and freedom from debts.",
            "स्वास्थ्य, प्रसिद्धि, आध्यात्मिक झुकाव, उदारता, र ऋणमुक्ति।",
            "Practice meditation and charitable giving; avoid excessive attachment to material things.",
            "ध्यान र दानको अभ्यास गर्नुहोस्; भौतिक वस्तुमा अत्यधिक आसक्ति त्याग गर्नुहोस्।")
    return None

def detect_durudhura(planets, lagna_sign):
    moon = _p(planets, "Moon")
    if not moon:
        return None
    moon_house = moon.get("house", 0)
    in_2nd  = [p for p in planets if p["name"] not in ["Sun","Moon","Rahu","Ketu"] and _house_dist(moon_house, p.get("house",0))==2]
    in_12th = [p for p in planets if p["name"] not in ["Sun","Moon","Rahu","Ketu"] and _house_dist(moon_house, p.get("house",0))==12]
    if in_2nd and in_12th:
        return _yoga("durudhura", "Durudhura Yoga", "दुरुधुर योग", CAT_CHANDRA, "auspicious",
            "Planets on both sides of the Moon (2nd and 12th from Moon) create this rare yoga of abundance.",
            "चन्द्रको दुवै पट्टि (दोस्रो र बाह्रौं भावमा) ग्रहहरू — प्रचुरताको दुर्लभ योग।",
            "Wealth, reputation, charitable nature, popularity, and enjoyment of many life pleasures.",
            "धन, मर्यादा, दयालु स्वभाव, लोकप्रियता, र जीवनका धेरै सुखको उपभोग।",
            "Balance material and spiritual pursuits; make regular charitable donations.",
            "भौतिक र आध्यात्मिक लक्ष्यमा सन्तुलन राख्नुहोस्; नियमित दान गर्नुहोस्।")
    return None

def detect_kemadruma(planets, lagna_sign):
    moon = _p(planets, "Moon")
    if not moon:
        return None
    moon_house = moon.get("house", 0)
    has_neighbor = any(
        p["name"] not in ["Sun","Rahu","Ketu"] and p["name"] != "Moon"
        and _house_dist(moon_house, p.get("house",0)) in [2, 12]
        for p in planets
    )
    if not has_neighbor:
        return _yoga("kemadruma", "Kemadruma Yoga", "केमद्रुम योग", CAT_CHANDRA, "challenging",
            "Moon is isolated — no planets in its 2nd or 12th house. Mental struggles may arise.",
            "चन्द्र एकाकी छ — दोस्रो र बाह्रौं भावमा कोही ग्रह छैन। मानसिक संघर्ष आउन सक्छ।",
            "Mental instability, loneliness, financial difficulties, and lack of support at critical times.",
            "मानसिक अस्थिरता, एकाकीपन, आर्थिक कठिनाइ, र महत्वपूर्ण समयमा समर्थनको कमी।",
            "Strengthen the Moon through Monday fasting, white pearl gem, and regular meditation.",
            "सोमवारको व्रत, सेतो मोती रत्न, र नियमित ध्यानले चन्द्रलाई बलियो बनाउनुहोस्।")
    return None

def detect_adhi_yoga(planets, lagna_sign):
    moon = _p(planets, "Moon")
    if not moon:
        return None
    moon_house = moon.get("house", 0)
    benefics_6_7_8 = [
        p for p in planets
        if p["name"] in NATURAL_BENEFICS and p["name"] != "Moon"
        and _house_dist(moon_house, p.get("house",0)) in [6, 7, 8]
    ]
    if len(benefics_6_7_8) >= 2:
        names = ", ".join([_pn(p["name"],"en") for p in benefics_6_7_8])
        names_ne = ", ".join([_pn(p["name"],"ne") for p in benefics_6_7_8])
        return _yoga("adhi_yoga", "Adhi Yoga", "अधि योग", CAT_CHANDRA, "highly_auspicious",
            f"Natural benefics ({names}) in 6th, 7th, or 8th from Moon — leadership and prosperity.",
            f"प्राकृतिक शुभ ग्रह ({names_ne}) चन्द्रबाट षष्ठ, सप्तम, वा अष्टम भावमा — नेतृत्व र समृद्धि।",
            "Political power, high status, wealth, enemies defeated, and long healthy life.",
            "राजनीतिक शक्ति, उच्च पद, धन, शत्रु परास्त, र दीर्घ स्वस्थ जीवन।",
            "Serve community leaders; chant 'Om Chandraya Namah' on Mondays.",
            "समुदायका नेताको सेवा गर्नुहोस्; सोमवार 'ॐ चन्द्राय नमः' जप गर्नुहोस्।")
    return None

def detect_shakata_yoga(planets, lagna_sign):
    moon    = _p(planets, "Moon")
    jupiter = _p(planets, "Jupiter")
    if moon and jupiter:
        dist = _house_dist(jupiter.get("house",1), moon.get("house",1))
        if dist in [6, 8, 12]:
            return _yoga("shakata_yoga", "Shakata Yoga", "शकट योग", CAT_CHANDRA, "challenging",
                "Moon is in 6th, 8th, or 12th from Jupiter — fluctuating fortunes and obstacles.",
                "चन्द्र गुरुबाट षष्ठ, अष्टम, वा द्वादश भावमा — भाग्यमा उतारचढाव र बाधाहरू।",
                "Ups and downs in fortune, obstacles in career, and periods of hardship followed by recovery.",
                "भाग्यमा उतारचढाव, करियरमा बाधा, र कठिनाइपछि सुधारका अवधिहरू।",
                "Strengthen Jupiter through Thursday worship; stay disciplined during low periods.",
                "गुरुवार गुरुको पूजा गरेर बलियो बनाउनुहोस्; कठिन समयमा अनुशासित रहनुहोस्।")
    return None

# ─────────────────────────────────────────────
# SURYA (SUN) YOGAS
# ─────────────────────────────────────────────

def detect_budhaditya(planets, lagna_sign):
    sun     = _p(planets, "Sun")
    mercury = _p(planets, "Mercury")
    if sun and mercury and _same_house(sun, mercury):
        return _yoga("budhaditya", "Budhaditya Yoga", "बुधादित्य योग", CAT_SURYA, "auspicious",
            "Sun and Mercury share the same house, blending intellect with solar authority.",
            "सूर्य र बुध एउटै भावमा — बौद्धिकता र अधिकारको संयोजन।",
            "Strong communication, analytical skill, educational success, and intelligence in public life.",
            "प्रभावकारी सञ्चार, विश्लेषणात्मक क्षमता, शैक्षिक सफलता, र सार्वजनिक जीवनमा बुद्धिमत्ता।",
            "Recite Mercury mantras; keep the mind calm before important decisions.",
            "बुधका मन्त्र जप गर्नुहोस्; महत्त्वपूर्ण निर्णयअघि मन शान्त राख्नुहोस्।")
    return None

def detect_vesi_yoga(planets, lagna_sign):
    sun = _p(planets, "Sun")
    if not sun:
        return None
    sun_house = sun.get("house", 0)
    in_2nd_from_sun = [
        p for p in planets
        if p["name"] not in ["Sun","Moon","Rahu","Ketu"]
        and _house_dist(sun_house, p.get("house",0)) == 2
    ]
    if in_2nd_from_sun:
        names = ", ".join([_pn(p["name"],"en") for p in in_2nd_from_sun])
        names_ne = ", ".join([_pn(p["name"],"ne") for p in in_2nd_from_sun])
        return _yoga("vesi_yoga", "Vesi Yoga", "वेसि योग", CAT_SURYA, "auspicious",
            f"Planet(s) in the 2nd house from Sun ({names}) — virtuous and prosperous.",
            f"सूर्यबाट दोस्रो भावमा ग्रह ({names_ne}) — सद्गुणी र समृद्ध।",
            "Virtuous character, good speech, happiness, and prosperity through honest means.",
            "सद्गुणी चरित्र, राम्रो वाणी, खुशी, र इमानदार माध्यमबाट समृद्धि।",
            "Offer water (Arghya) to the Sun daily at sunrise; practice truthful speech.",
            "प्रतिदिन सूर्योदयमा सूर्यलाई अर्घ्य दिनुहोस्; सत्यवादिताको अभ्यास गर्नुहोस्।")
    return None

def detect_vasi_yoga(planets, lagna_sign):
    sun = _p(planets, "Sun")
    if not sun:
        return None
    sun_house = sun.get("house", 0)
    in_12th_from_sun = [
        p for p in planets
        if p["name"] not in ["Sun","Moon","Rahu","Ketu"]
        and _house_dist(sun_house, p.get("house",0)) == 12
    ]
    if in_12th_from_sun:
        names = ", ".join([_pn(p["name"],"en") for p in in_12th_from_sun])
        names_ne = ", ".join([_pn(p["name"],"ne") for p in in_12th_from_sun])
        return _yoga("vasi_yoga", "Vasi Yoga", "वासि योग", CAT_SURYA, "auspicious",
            f"Planet(s) in the 12th house from Sun ({names}) — happiness and generosity.",
            f"सूर्यबाट बाह्रौं भावमा ग्रह ({names_ne}) — खुशी र उदारता।",
            "Happiness, generosity, liberalism, and freedom from enemies.",
            "खुशी, उदारता, उदार सोच, र शत्रुमुक्ति।",
            "Practice daily Sun salutation (Surya Namaskar); donate to the elderly.",
            "प्रतिदिन सूर्य नमस्कार गर्नुहोस्; वृद्धजनलाई दान गर्नुहोस्।")
    return None

def detect_ubhayachari(planets, lagna_sign):
    sun = _p(planets, "Sun")
    if not sun:
        return None
    sun_house = sun.get("house", 0)
    in_2nd  = [p for p in planets if p["name"] not in ["Sun","Moon","Rahu","Ketu"] and _house_dist(sun_house, p.get("house",0))==2]
    in_12th = [p for p in planets if p["name"] not in ["Sun","Moon","Rahu","Ketu"] and _house_dist(sun_house, p.get("house",0))==12]
    if in_2nd and in_12th:
        return _yoga("ubhayachari", "Ubhayachari Yoga", "उभयचारी योग", CAT_SURYA, "highly_auspicious",
            "Planets on both sides of the Sun (2nd and 12th) — rare solar yoga of great power.",
            "सूर्यको दुवै पट्टि ग्रहहरू (दोस्रो र बाह्रौं) — महान् शक्तिको दुर्लभ सौर योग।",
            "Fame, eloquence, affluence, happiness, and all qualities of royal status.",
            "यश, वाक्पटुता, समृद्धि, खुशी, र राजकीय मर्यादाका सबै गुण।",
            "Worship the Sun and perform Aditya Hridayam recitation daily.",
            "प्रतिदिन सूर्यको पूजा र आदित्य हृदयम् पाठ गर्नुहोस्।")
    return None

# ─────────────────────────────────────────────
# MISCELLANEOUS SHUBHA YOGAS
# ─────────────────────────────────────────────

def detect_chandra_mangal(planets, lagna_sign):
    moon = _p(planets, "Moon")
    mars = _p(planets, "Mars")
    if moon and mars and (_same_house(moon, mars) or _house_dist(moon.get("house",1), mars.get("house",1)) == 7):
        return _yoga("chandra_mangal", "Chandra-Mangal Yoga", "चन्द्र-मङ्गल योग", CAT_MISC, "auspicious",
            "Moon and Mars conjunct or in opposition — emotional drive with strong ambition.",
            "चन्द्र र मङ्गल युति वा विपक्षमा — भावनात्मक उर्जा र बलियो महत्त्वाकांक्षा।",
            "Financial ambition, courage, bold action, and strong determination in achieving goals.",
            "आर्थिक महत्त्वाकांक्षा, साहस, निर्धक्क कार्य, र लक्ष्य प्राप्तिमा बलियो दृढता।",
            "Practice calming breathwork; channel energy into productive physical activity.",
            "शान्त श्वास अभ्यास गर्नुहोस्; उर्जालाई उत्पादक शारीरिक गतिविधिमा लगाउनुहोस्।")
    return None

def detect_neechabhanga(planets, lagna_sign):
    for planet in planets:
        if planet.get("exaltation_state") == "debilitated":
            planet_sign = planet.get("sign_number", 0)
            debi_lord = _p(planets, SIGN_LORDS.get(planet_sign, ""))
            exalt_sign = EXALTATION_SIGNS.get(planet.get("name",""), 0)
            exalt_sign_lord = _p(planets, SIGN_LORDS.get(exalt_sign, ""))
            cancellation = (
                planet.get("house") in KENDRA_HOUSES
                or (debi_lord and debi_lord.get("house") in KENDRA_HOUSES)
                or (exalt_sign_lord and exalt_sign_lord.get("house") in KENDRA_HOUSES)
                or any(_same_house(planet, _p(planets, b)) for b in NATURAL_BENEFICS)
            )
            if cancellation:
                return _yoga("neechabhanga", "Neecha Bhanga Yoga", "नीचभंग योग", CAT_MISC, "auspicious",
                    f"Debilitation of {planet.get('name')} is cancelled by supportive placement — weakness becomes strength.",
                    f"{_pn(planet.get('name',''),'ne')} को नीच दोष सहयोगी स्थितिले खण्डित — कमजोरी शक्तिमा बदलिन्छ।",
                    "Weakness converts into resilience; delays give way to recovery and regained strength.",
                    "कमजोरी लचकतामा परिणत; ढिलाइपछि सुधार र शक्ति फिर्ता।",
                    "Strengthen the debilitated planet with its mantra; avoid forcing decisions when feeling weak.",
                    "नीच ग्रहको मन्त्र जप; कमजोरी महसुस हुँदा निर्णय थाम्नुहोस्।")
    return None

def detect_parivartana(planets, lagna_sign):
    for a in planets:
        for b in planets:
            if a["name"] != b["name"] and _mutual_exchange(a, b, lagna_sign):
                return _yoga("parivartana", "Parivartana Yoga", "परिवर्तन योग", CAT_MISC, "auspicious",
                    f"{a['name']} and {b['name']} exchange houses — locked energies and shared destiny.",
                    f"{_pn(a['name'],'ne')} र {_pn(b['name'],'ne')} ले भाव आदानप्रदान — साझा भाग्यको योग।",
                    "Strong outcomes tied to partnership, contracts, or shared destiny.",
                    "साझेदारी, सम्झौता, वा साझा भाग्यसँग सम्बन्धित बलियो परिणाम।",
                    "Build trust carefully; align decisions with the long-term needs of both planets' houses.",
                    "आत्मविश्वासपूर्वक विश्वास निर्माण; दुवै भावको दीर्घकालीन आवश्यकतासँग निर्णय मेलाउनुहोस्।")
    return None

def detect_shubha_trikona(planets, lagna_sign):
    for planet in planets:
        if planet["name"] in NATURAL_BENEFICS and planet.get("house") in TRIKONA_HOUSES:
            return _yoga("shubha_trikona", "Shubha Trikona Yoga", "शुभ त्रिकोण योग", CAT_MISC, "auspicious",
                f"{planet['name']} in a Trikona house — grace, happiness, and blessings.",
                f"{_pn(planet['name'],'ne')} त्रिकोण भावमा — अनुग्रह, खुशी र आशीर्वाद।",
                "Good fortune, spiritual ease, and opportunities for natural growth and happiness.",
                "सौभाग्य, आध्यात्मिक सहजता, र स्वाभाविक वृद्धि तथा खुशीका अवसर।",
                "Honor the planet's qualities through prayer and good habits aligned with its nature.",
                "ग्रहको गुणलाई सम्मान गर्दै प्रार्थना र राम्रो बानी अपनाउनुहोस्।")
    return None

def detect_amala_yoga(planets, lagna_sign):
    moon = _p(planets, "Moon")
    for planet in planets:
        if planet["name"] in NATURAL_BENEFICS:
            if planet.get("house") == 10:
                return _yoga("amala_yoga", "Amala Yoga", "अमल योग", CAT_MISC, "auspicious",
                    f"{planet['name']} in the 10th house from Lagna — spotless reputation.",
                    f"{_pn(planet['name'],'ne')} लग्नबाट दशम भावमा — निष्कलंक मर्यादा।",
                    "Spotless reputation, charitable nature, fame, and success in career lasting throughout life.",
                    "निष्कलंक मर्यादा, दयालु स्वभाव, यश, र जीवनभर करियरमा सफलता।",
                    "Maintain high ethical standards in all dealings; serve those in need regularly.",
                    "सबै व्यवहारमा उच्च नैतिक मापदण्ड कायम राख्नुहोस्; नियमित रूपमा जरुरतमन्दको सेवा गर्नुहोस्।")
            if moon and planet.get("house") == ((moon.get("house", 0) + 9) % 12) + 1:
                return _yoga("amala_yoga_moon", "Amala Yoga (from Moon)", "अमल योग (चन्द्रबाट)", CAT_MISC, "auspicious",
                    f"{planet['name']} in the 10th house from Moon — lasting fame and goodwill.",
                    f"{_pn(planet['name'],'ne')} चन्द्रबाट दशम भावमा — स्थायी यश र सद्भावना।",
                    "Lasting fame, goodwill from the public, and career success through honest means.",
                    "स्थायी यश, जनताको सद्भावना, र इमानदार माध्यमबाट करियर सफलता।",
                    "Practice honesty and transparency; engage in public service activities.",
                    "इमानदारी र पारदर्शिता अभ्यास गर्नुहोस्; सार्वजनिक सेवामा संलग्न होनुहोस्।")
    return None

def detect_parvata_yoga(planets, lagna_sign):
    kendra_planets = [p for p in planets if p.get("house") in KENDRA_HOUSES]
    benefics_in_kendra = [p for p in kendra_planets if p["name"] in NATURAL_BENEFICS]
    dusthana_planets = [p for p in planets if p.get("house") in DUSTHANA_HOUSES]
    malefics_in_dusthana = [p for p in dusthana_planets if p["name"] in NATURAL_MALEFICS]
    if len(benefics_in_kendra) >= 2 and len(malefics_in_dusthana) == 0:
        return _yoga("parvata_yoga", "Parvata Yoga", "पर्वत योग", CAT_MISC, "auspicious",
            "Natural benefics in Kendra houses and dusthana houses free of malefics — mountain of prosperity.",
            "प्राकृतिक शुभ ग्रह केन्द्रमा र दुष्टान भाव पापग्रहमुक्त — समृद्धिको पर्वत।",
            "Wealth, generosity, political success, fame, and freedom from enemies and obstacles.",
            "धन, उदारता, राजनीतिक सफलता, यश, र शत्रु तथा बाधामुक्ति।",
            "Cultivate generosity; make regular charitable donations to maintain this yoga's blessings.",
            "उदारता विकास गर्नुहोस्; यस योगको आशीर्वाद कायम राख्न नियमित दान गर्नुहोस्।")
    return None

def detect_kaahala_yoga(planets, lagna_sign):
    lord4 = _lord_of(4, lagna_sign)
    lord9 = _lord_of(9, lagna_sign)
    lagna_lord_name = _lord_of(1, lagna_sign)
    p4 = _p(planets, lord4)
    p9 = _p(planets, lord9)
    ll = _p(planets, lagna_lord_name)
    if (p4 and p9 and ll
            and (_same_house(p4, p9) or _mutual_exchange(p4, p9, lagna_sign))
            and (_is_exalted(ll) or _is_own_sign(ll))):
        return _yoga("kaahala_yoga", "Kaahala Yoga", "काहल योग", CAT_MISC, "auspicious",
            "4th and 9th lords in mutual relationship with a strong Lagna lord — boldness and authority.",
            "चतुर्थ र नवम भावेशको परस्पर सम्बन्ध र बलियो लग्नेश — साहस र अधिकार।",
            "Boldness, authority, strong will, command over armies or large organizations.",
            "साहस, अधिकार, बलियो इच्छाशक्ति, सेना वा ठूला संस्थाहरूमा नेतृत्व।",
            "Lead with integrity; practice discipline and physical fitness regularly.",
            "इमानदारीसाथ नेतृत्व गर्नुहोस्; नियमित अनुशासन र शारीरिक स्वास्थ्यको अभ्यास।")
    return None

def detect_sankha_yoga(planets, lagna_sign):
    lord5 = _lord_of(5, lagna_sign)
    lord6 = _lord_of(6, lagna_sign)
    p5 = _p(planets, lord5)
    p6 = _p(planets, lord6)
    if p5 and p6 and _kendra_from(p5.get("house",1), p6.get("house",1)):
        return _yoga("sankha_yoga", "Sankha Yoga", "शंख योग", CAT_MISC, "auspicious",
            "5th and 6th lords in mutual Kendra — long life, righteousness, and leadership.",
            "पञ्चम र षष्ठ भावेश परस्पर केन्द्रमा — दीर्घायु, धर्मपरायणता र नेतृत्व।",
            "Long life, justice, righteousness, compassion, and success in competitive situations.",
            "दीर्घायु, न्याय, धर्मपरायणता, दया, र प्रतिस्पर्धात्मक परिस्थितिमा सफलता।",
            "Practice righteousness (Dharma) in daily life; help others overcome their difficulties.",
            "दैनिक जीवनमा धर्मको अभ्यास गर्नुहोस्; अरूलाई कठिनाइ पार गर्न सहयोग गर्नुहोस्।")
    return None

# ─────────────────────────────────────────────
# ARISHTA & DOSHA YOGAS (अरिष्ट / दोष)
# ─────────────────────────────────────────────

def detect_kala_sarpa_yoga(planets, lagna_sign):
    rahu = _p(planets, "Rahu")
    ketu = _p(planets, "Ketu")
    if not rahu or not ketu:
        return None
    rahu_h = rahu.get("house", 0)
    ketu_h = ketu.get("house", 0)
    all_planet_names = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
    non_rahu_ketu = [p for p in planets if p["name"] in all_planet_names]
    # Check if all planets lie between Rahu and Ketu in one half
    hemis = set()
    for p in non_rahu_ketu:
        dist = _house_dist(rahu_h, p.get("house",0))
        if 1 < dist < 7:
            hemis.add("rahu_side")
        elif dist > 7 or dist == 7:
            hemis.add("ketu_side")
    if len(hemis) == 1:
        return _yoga("kala_sarpa_yoga", "Kala Sarpa Yoga", "काल सर्प योग", CAT_DOSHA, "challenging",
            "All planets are hemmed between Rahu and Ketu, forming the feared Kala Sarpa Yoga.",
            "सबै ग्रह राहु र केतुको बीचमा आबद्ध छन् — भयंकर काल सर्प योग।",
            "Obstacles, delays, struggles with fate, karmic challenges, and periods of unexpected reversals.",
            "बाधा, ढिलाइ, भाग्यसँग संघर्ष, कार्मिक चुनौतीहरू, र अप्रत्याशित उलटफेरका अवधि।",
            "Perform Naga Panchami puja; chant 'Om Namo Bhagavate Vasudevaya'; visit Trimbakeshwar Jyotirlinga.",
            "नाग पञ्चमी पूजा गर्नुहोस्; 'ॐ नमो भगवते वासुदेवाय' जप; त्र्यम्बकेश्वर ज्योतिर्लिंग दर्शन गर्नुहोस्।")
    return None

def detect_mangala_dosha(planets, lagna_sign):
    mars = _p(planets, "Mars")
    if mars and mars.get("house") in [1, 2, 4, 7, 8, 12]:
        house = mars.get("house")
        return _yoga("mangala_dosha", "Mangala Dosha (Manglik)", "मंगल दोष (मांगलिक)", CAT_DOSHA, "challenging",
            f"Mars in the {house}th house creates Mangala Dosha — caution required in marriage matters.",
            f"मंगल {house}औं भावमा — मंगल दोष; विवाह विषयमा सावधानी आवश्यक।",
            "Marital disharmony, aggressive temperament, delay in marriage, and possible partner health issues.",
            "वैवाहिक असामंजस्य, आक्रामक स्वभाव, विवाहमा ढिलाइ, र साथीको स्वास्थ्य समस्या।",
            "Perform Mangal Puja and Kumbh Vivah (symbolic marriage ritual) before actual marriage; chant 'Om Angarakaya Namah'.",
            "विवाहअघि मंगल पूजा र कुम्भ विवाह गर्नुहोस्; 'ॐ अङ्गारकाय नमः' जप गर्नुहोस्।")
    return None

def detect_grahan_yoga(planets, lagna_sign):
    sun  = _p(planets, "Sun")
    moon = _p(planets, "Moon")
    rahu = _p(planets, "Rahu")
    ketu = _p(planets, "Ketu")
    results = []
    if sun and rahu and _same_house(sun, rahu):
        results.append(("Sun-Rahu", "सूर्य-राहु", "solar eclipse"))
    if sun and ketu and _same_house(sun, ketu):
        results.append(("Sun-Ketu", "सूर्य-केतु", "solar Ketu"))
    if moon and rahu and _same_house(moon, rahu):
        results.append(("Moon-Rahu", "चन्द्र-राहु", "lunar eclipse"))
    if moon and ketu and _same_house(moon, ketu):
        results.append(("Moon-Ketu", "चन्द्र-केतु", "lunar Ketu"))
    if results:
        comb_en = "; ".join([r[0] for r in results])
        comb_ne = "; ".join([r[1] for r in results])
        return _yoga("grahan_yoga", "Grahan Yoga", "ग्रहण योग", CAT_DOSHA, "challenging",
            f"Eclipse combination(s) present: {comb_en} — shadow planets afflict luminaries.",
            f"ग्रहण संयोजन: {comb_ne} — छाया ग्रहले ज्योतिर्मय ग्रहलाई पीडित गरेको छ।",
            "Mental anxieties, health concerns, sudden reversals, and challenges with authority figures.",
            "मानसिक चिन्ता, स्वास्थ्य सरोकार, अचानक उलटफेर, र प्राधिकरण व्यक्तिसँग चुनौती।",
            "Perform Navagraha Puja; chant Mahamrityunjaya Mantra; donate black sesame on Saturdays.",
            "नवग्रह पूजा गर्नुहोस्; महामृत्युञ्जय मन्त्र जप; शनिवार कालो तिल दान गर्नुहोस्।")
    return None

def detect_shrapit_yoga(planets, lagna_sign):
    saturn = _p(planets, "Saturn")
    rahu   = _p(planets, "Rahu")
    if saturn and rahu and _same_house(saturn, rahu):
        return _yoga("shrapit_yoga", "Shrapit Yoga", "श्रापित योग", CAT_DOSHA, "challenging",
            "Saturn and Rahu conjunct — indicating past-life karmic debts and obstacles in this life.",
            "शनि र राहुको युति — पूर्वजन्मको कार्मिक ऋण र यस जन्ममा बाधाको संकेत।",
            "Persistent obstacles, feeling cursed, delayed success, and karmic lessons around discipline.",
            "निरन्तर बाधाहरू, श्रापित महसुस, ढिलो सफलता, र अनुशासनसम्बन्धी कार्मिक पाठहरू।",
            "Perform Shrapit Dosha Nivaran Puja; worship Lord Shiva; donate to the poor on Saturdays.",
            "श्रापित दोष निवारण पूजा गर्नुहोस्; शिवजीको पूजा; शनिवार गरीबलाई दान।")
    return None

def detect_pitra_dosha(planets, lagna_sign):
    sun  = _p(planets, "Sun")
    rahu = _p(planets, "Rahu")
    saturn = _p(planets, "Saturn")
    if sun and rahu and _same_house(sun, rahu):
        return _yoga("pitra_dosha", "Pitra Dosha", "पितृ दोष", CAT_DOSHA, "challenging",
            "Sun conjunct Rahu — Pitra Dosha indicating ancestral karmic imbalances affecting the native.",
            "सूर्य र राहुको युति — पितृ दोष; पूर्वजको कार्मिक असन्तुलनले प्रभाव पार्छ।",
            "Family obstacles, father-related difficulties, unexpected setbacks, and ancestral karmic debts.",
            "पारिवारिक बाधाहरू, पिता सम्बन्धी कठिनाइ, अप्रत्याशित असफलता, र पूर्वजको कार्मिक ऋण।",
            "Perform Pitra Tarpan on Amavasya; donate food to Brahmins; recite Pitru Sukta.",
            "अमावास्यामा पितृ तर्पण गर्नुहोस्; ब्राह्मणलाई भोजन दान; पितृ सूक्त पाठ गर्नुहोस्।")
    return None

# ─────────────────────────────────────────────
# SPIRITUAL YOGAS
# ─────────────────────────────────────────────

def detect_pravrajya_yoga(planets, lagna_sign):
    # 4+ planets in one sign, especially with a strong Sun
    from collections import Counter
    sign_counts = Counter(p.get("sign_number") for p in planets if p["name"] not in ["Rahu","Ketu"])
    max_sign, max_count = sign_counts.most_common(1)[0] if sign_counts else (0, 0)
    sun = _p(planets, "Sun")
    if max_count >= 4 and sun and (_is_exalted(sun) or _is_own_sign(sun)):
        return _yoga("pravrajya_yoga", "Pravrajya Yoga", "प्रव्रज्या योग", CAT_SPIRITUAL, "auspicious",
            f"Four or more planets congregate in one sign with a strong Sun — renunciation and spiritual life.",
            "चारवा बढी ग्रह एउटै राशिमा र बलियो सूर्य — संन्यास र आध्यात्मिक जीवनको योग।",
            "Strong spiritual inclination, possible renunciation of worldly life, and wisdom beyond one's years.",
            "बलियो आध्यात्मिक झुकाव, सांसारिक जीवन त्याग्ने सम्भावना, र उमेरभन्दा बढी ज्ञान।",
            "Embrace spiritual practice; meditation, service, and study of sacred texts are beneficial.",
            "आध्यात्मिक अभ्यास अँगाल्नुहोस्; ध्यान, सेवा, र धर्मग्रन्थ अध्ययन लाभदायक छ।")
    return None

def detect_moksha_yoga(planets, lagna_sign):
    lord12 = _lord_of(12, lagna_sign)
    p12    = _p(planets, lord12)
    ketu   = _p(planets, "Ketu")
    jupiter = _p(planets, "Jupiter")
    if (p12 and (_is_exalted(p12) or _is_own_sign(p12))
            and ketu and ketu.get("house") in TRIKONA_HOUSES
            and jupiter and jupiter.get("house") in TRIKONA_HOUSES + KENDRA_HOUSES):
        return _yoga("moksha_yoga", "Moksha Yoga", "मोक्ष योग", CAT_SPIRITUAL, "auspicious",
            "Strong 12th lord, Ketu in Trikona, and Jupiter in Kendra/Trikona — liberation yoga.",
            "बलियो द्वादशेश, त्रिकोणमा केतु, र केन्द्र/त्रिकोणमा गुरु — मोक्ष योग।",
            "Deep spiritual evolution, liberation from the cycle of rebirth, and divine grace in later life.",
            "गहिरो आध्यात्मिक विकास, पुनर्जन्मको चक्रबाट मुक्ति, र उत्तरार्द्ध जीवनमा दैवी कृपा।",
            "Practice Japa, meditation, and selfless service (Seva); study Vedanta and spiritual scriptures.",
            "जप, ध्यान, र निःस्वार्थ सेवा अभ्यास गर्नुहोस्; वेदान्त र आध्यात्मिक शास्त्र अध्ययन।")
    return None

# ─────────────────────────────────────────────
# VIPARITA RAJA YOGAS — Harsha, Sarala, Vimala
# (फलदीपिका, BPHS Ch.36, Jataka Parijata)
# ─────────────────────────────────────────────

def detect_harsha_yoga(planets, lagna_sign):
    """6th lord in 6th, 8th, or 12th house"""
    lord6 = _lord_of(6, lagna_sign)
    p6 = _p(planets, lord6)
    if p6 and p6.get("house") in DUSTHANA_HOUSES:
        strength = 80 if p6.get("house") == 6 else 65
        return _yoga("harsha_yoga", "Harsha Yoga", "हर्ष योग",
            CAT_VIPARITA, "auspicious",
            f"6th lord ({lord6}) placed in a Dusthana (6/8/12) house — Harsha Yoga of Viparita Raja.",
            f"षष्ठेश ({_pn(lord6,'ne')}) दुष्टान भावमा (६/८/१२) — विपरीत राजयोगको हर्ष योग।",
            "Victory over enemies, good health, happiness, freedom from disease and litigation. Success through apparent difficulties.",
            "शत्रुमाथि विजय, उत्तम स्वास्थ्य, आनन्द, रोग र विवादमुक्ति। कठिनाइबाट सफलता।",
            "Worship Lord Vishnu; perform charity for the sick; recite Aditya Hridayam.",
            "विष्णुको आराधना; बिरामीलाई दान; आदित्य हृदयम् पाठ गर्नुहोस्।",
            references=["BPHS Ch.36", "Phaladeepika Ch.6", "Jataka Parijata 3.17"],
            strength_pct=strength, planets_involved=[lord6])

def detect_sarala_yoga(planets, lagna_sign):
    """8th lord in 6th, 8th, or 12th house"""
    lord8 = _lord_of(8, lagna_sign)
    p8 = _p(planets, lord8)
    if p8 and p8.get("house") in DUSTHANA_HOUSES:
        strength = 80 if p8.get("house") == 8 else 65
        return _yoga("sarala_yoga", "Sarala Yoga", "सरल योग",
            CAT_VIPARITA, "auspicious",
            f"8th lord ({lord8}) in Dusthana (6/8/12) — Sarala Yoga, protection from death and enemies.",
            f"अष्टमेश ({_pn(lord8,'ne')}) दुष्टानमा — सरल योग, मृत्यु र शत्रुबाट सुरक्षा।",
            "Long life, courage, protection from enemies, fearlessness, and unexpected windfalls.",
            "दीर्घायु, साहस, शत्रुबाट सुरक्षा, निडरता, र अप्रत्याशित लाभ।",
            "Worship Lord Shiva (Mahamrityunjaya); perform Mrityunjaya homa.",
            "महामृत्युञ्जय पूजा र होम गर्नुहोस्।",
            references=["BPHS Ch.36", "Phaladeepika Ch.6", "Saravali 36.1"],
            strength_pct=strength, planets_involved=[lord8])

def detect_vimala_yoga(planets, lagna_sign):
    """12th lord in 6th, 8th, or 12th house"""
    lord12 = _lord_of(12, lagna_sign)
    p12 = _p(planets, lord12)
    if p12 and p12.get("house") in DUSTHANA_HOUSES:
        strength = 80 if p12.get("house") == 12 else 65
        return _yoga("vimala_yoga", "Vimala Yoga", "विमल योग",
            CAT_VIPARITA, "auspicious",
            f"12th lord ({lord12}) in Dusthana (6/8/12) — Vimala Yoga, purity of character and savings.",
            f"द्वादशेश ({_pn(lord12,'ne')}) दुष्टानमा — विमल योग, चारित्रिक शुद्धता र बचत।",
            "Virtuous character, frugality, happiness in later life, minimal expenses, and spiritual elevation.",
            "सद्गुणी चरित्र, मितव्ययिता, उत्तरार्द्ध जीवनमा सुख, न्यून खर्च, र आध्यात्मिक उन्नति।",
            "Practice daily Vishnu Sahasranama; live a disciplined, simple life.",
            "दैनिक विष्णु सहस्रनाम पाठ; अनुशासित, सरल जीवन।",
            references=["BPHS Ch.36", "Phaladeepika Ch.6", "Jataka Parijata 3.19"],
            strength_pct=strength, planets_involved=[lord12])

# ─────────────────────────────────────────────
# RAJA YOGA — Specific lord combinations
# (BPHS Ch.34, Phaladeepika, Sarvartha Chintamani)
# ─────────────────────────────────────────────

def detect_dharmakarmadhipati(planets, lagna_sign):
    """9th (dharma) + 10th (karma) lords connected"""
    lord9  = _lord_of(9, lagna_sign)
    lord10 = _lord_of(10, lagna_sign)
    p9  = _p(planets, lord9)
    p10 = _p(planets, lord10)
    if lord9 == lord10:
        return None  # same planet, different yoga
    if p9 and p10 and (_same_house(p9, p10) or _mutual_exchange(p9, p10, lagna_sign)):
        strength = 90 if (_is_exalted(p9) or _is_own_sign(p9)) else 70
        return _yoga("dharmakarmadhipati", "Dharma-Karma-Adhipati Yoga", "धर्म-कर्माधिपति योग",
            CAT_RAJA, "highly_auspicious",
            f"9th lord ({lord9}) and 10th lord ({lord10}) conjunct or exchange — the supreme Raja Yoga.",
            f"नवमेश ({_pn(lord9,'ne')}) र दशमेश ({_pn(lord10,'ne')}) युति वा आदानप्रदान — सर्वोच्च राजयोग।",
            "Royal power, fame, career excellence, authority, professional peak, and lasting recognition.",
            "राजकीय शक्ति, यश, उत्कृष्ट करियर, अधिकार, व्यावसायिक शिखर, र दीर्घकालीन मान्यता।",
            "Worship Surya and Brihaspati; perform charitable acts on Sundays and Thursdays.",
            "सूर्य र बृहस्पतिको पूजा; आइतवार र गुरुवार दान।",
            references=["BPHS Ch.34 v.1-10", "Phaladeepika Ch.6 v.1", "Saravali 36.1", "Jataka Parijata 3.1"],
            strength_pct=strength, planets_involved=[lord9, lord10])

def detect_lagnesh_navamesh(planets, lagna_sign):
    lord1 = _lord_of(1, lagna_sign)
    lord9 = _lord_of(9, lagna_sign)
    p1 = _p(planets, lord1)
    p9 = _p(planets, lord9)
    if lord1 == lord9: return None
    if p1 and p9 and (_same_house(p1, p9) or _mutual_exchange(p1, p9, lagna_sign)):
        strength = 85 if (_is_exalted(p1) or _is_own_sign(p1)) else 70
        return _yoga("lagnesh_navamesh", "Lagnesh-Navamesh Raja Yoga", "लग्नेश-नवमेश राजयोग",
            CAT_RAJA, "highly_auspicious",
            f"Lagna lord ({lord1}) and 9th lord ({lord9}) associated — fate and self combine for great fortune.",
            f"लग्नेश ({_pn(lord1,'ne')}) र नवमेश ({_pn(lord9,'ne')}) को सम्बन्ध — भाग्य र स्वयंको मेल।",
            "Great fortune, dharmic life, father's blessings, spiritual merit, and protection by destiny.",
            "महाभाग्य, धर्मपरायण जीवन, पिताको आशीर्वाद, आध्यात्मिक पुण्य, र भाग्यको सुरक्षा।",
            "Perform Guru-puja; visit pilgrimage sites; study scriptures.",
            "गुरुपूजा; तीर्थयात्रा; शास्त्र अध्ययन।",
            references=["BPHS Ch.34", "Phaladeepika Ch.6", "Uttara Kalamrita"],
            strength_pct=strength, planets_involved=[lord1, lord9])

def detect_lagnesh_panchamesh(planets, lagna_sign):
    lord1 = _lord_of(1, lagna_sign)
    lord5 = _lord_of(5, lagna_sign)
    p1 = _p(planets, lord1)
    p5 = _p(planets, lord5)
    if lord1 == lord5: return None
    if p1 and p5 and (_same_house(p1, p5) or _mutual_exchange(p1, p5, lagna_sign)):
        return _yoga("lagnesh_panchamesh", "Lagnesh-Panchamesh Yoga", "लग्नेश-पञ्चमेश योग",
            CAT_RAJA, "auspicious",
            f"Lagna lord ({lord1}) and 5th lord ({lord5}) conjunct/exchange — intelligence meets self.",
            f"लग्नेश ({_pn(lord1,'ne')}) र पञ्चमेश ({_pn(lord5,'ne')}) युति/आदानप्रदान — बुद्धि र स्वयंको मेल।",
            "Intellect, children's welfare, creativity, political success, and good judgment.",
            "बुद्धि, सन्तानको कल्याण, सृजनशीलता, राजनीतिक सफलता, र उत्तम निर्णय।",
            "Worship Saraswati; donate to students and children.",
            "सरस्वतीको पूजा; विद्यार्थी र बालबालिकाको सहायता।",
            references=["BPHS Ch.34", "Phaladeepika Ch.6"],
            strength_pct=72, planets_involved=[lord1, lord5])

def detect_panchamesh_dashamesh(planets, lagna_sign):
    lord5  = _lord_of(5, lagna_sign)
    lord10 = _lord_of(10, lagna_sign)
    p5  = _p(planets, lord5)
    p10 = _p(planets, lord10)
    if lord5 == lord10: return None
    if p5 and p10 and (_same_house(p5, p10) or _mutual_exchange(p5, p10, lagna_sign)):
        return _yoga("panchamesh_dashamesh", "Panchamesh-Dashamesh Yoga", "पञ्चमेश-दशमेश योग",
            CAT_RAJA, "auspicious",
            f"5th lord ({lord5}) and 10th lord ({lord10}) associated — intellect fuels career success.",
            f"पञ्चमेश ({_pn(lord5,'ne')}) र दशमेश ({_pn(lord10,'ne')}) को सम्बन्ध।",
            "Career through intellect or creativity, government honors, and recognition for talent.",
            "बुद्धि वा सृजनशीलताबाट करियर, सरकारी सम्मान, र प्रतिभाको पहिचान।",
            "Worship Sun on Sundays; develop expertise in your field.",
            "आइतवार सूर्य पूजा; आफ्नो क्षेत्रमा विशेषज्ञता विकास।",
            references=["BPHS Ch.34", "Sarvartha Chintamani"],
            strength_pct=70, planets_involved=[lord5, lord10])

# ─────────────────────────────────────────────
# CONJUNCTION (GRAHA YUTI) YOGAS
# ─────────────────────────────────────────────

def detect_guru_chandal(planets, lagna_sign):
    jupiter = _p(planets, "Jupiter")
    rahu    = _p(planets, "Rahu")
    if jupiter and rahu and _same_house(jupiter, rahu):
        h = jupiter.get("house", 0)
        severity = "challenging" if h not in TRIKONA_HOUSES else "neutral"
        return _yoga("guru_chandal", "Guru Chandal Yoga", "गुरु चाण्डाल योग",
            CAT_CONJUNCTION, severity,
            "Jupiter conjunct Rahu — wisdom tainted by materialism and unconventional thinking.",
            "गुरु र राहुको युति — ज्ञान भौतिकवाद र अपरम्परागत विचारबाट दूषित।",
            "Unconventional wisdom, possible deception, ethical dilemmas, gain through foreign connections. Can grant unique genius if well-placed.",
            "अपरम्परागत ज्ञान, सम्भावित छल, नैतिक दुविधा, विदेश सम्बन्धबाट लाभ। राम्रो स्थानमा अद्वितीय प्रतिभा।",
            "Worship Brihaspati and Rahu on Thursdays; chant Vishnu Sahasranama; avoid unethical shortcuts.",
            "गुरुवार बृहस्पति र राहुको पूजा; विष्णु सहस्रनाम; अनैतिक शर्टकटबाट बच्नुहोस्।",
            references=["Phaladeepika Ch.7", "BPHS Ch.38", "Chamatkar Chintamani"],
            strength_pct=60, planets_involved=["Jupiter", "Rahu"])

def detect_saraswati_yoga(planets, lagna_sign):
    mercury = _p(planets, "Mercury")
    venus   = _p(planets, "Venus")
    jupiter = _p(planets, "Jupiter")
    if not (mercury and venus and jupiter): return None
    # All three in Kendra/Trikona or conjunct
    good_positions = KENDRA_HOUSES + TRIKONA_HOUSES
    if (mercury.get("house") in good_positions and
        venus.get("house") in good_positions and
        jupiter.get("house") in good_positions):
        strength = 90
        return _yoga("saraswati_yoga", "Saraswati Yoga", "सरस्वती योग",
            CAT_VIDYA, "highly_auspicious",
            "Mercury, Venus, and Jupiter all in Kendra/Trikona — the great yoga of learning and arts.",
            "बुध, शुक्र र गुरु तीनैजना केन्द्र/त्रिकोणमा — विद्या र कलाको महायोग।",
            "Exceptional intelligence, mastery of arts/music/poetry, eloquence, respect in academia, and creative genius.",
            "असाधारण बुद्धि, कला/संगीत/काव्यमा दक्षता, वाक्पटुता, शैक्षिक क्षेत्रमा सम्मान, र सृजनात्मक प्रतिभा।",
            "Worship Goddess Saraswati on Panchami; study diligently; donate books and pens.",
            "पञ्चमीमा सरस्वती पूजा; लगनशील अध्ययन; पुस्तक र कलम दान।",
            references=["Phaladeepika Ch.6 v.3", "BPHS Ch.36", "Jataka Parijata 3.22"],
            strength_pct=strength, planets_involved=["Mercury", "Venus", "Jupiter"])
    return None

def detect_budha_mangal_yoga(planets, lagna_sign):
    mercury = _p(planets, "Mercury")
    mars    = _p(planets, "Mars")
    if mercury and mars and _same_house(mercury, mars):
        h = mercury.get("house", 0)
        strength = 75 if h in KENDRA_HOUSES else 60
        return _yoga("budha_mangal", "Budha-Mangal Yoga", "बुध-मङ्गल योग",
            CAT_CONJUNCTION, "auspicious",
            "Mercury and Mars conjunct — sharp technical mind, engineering or trade skill.",
            "बुध र मङ्गलको युति — तीव्र प्राविधिक मस्तिष्क, इन्जिनियरिङ वा व्यापार कौशल।",
            "Success in engineering, mathematics, surgery, business, and martial arts. Quick analytical mind.",
            "इन्जिनियरिङ, गणित, शल्यचिकित्सा, व्यापार, र मार्शल आर्टमा सफलता।",
            "Recite Budha and Mangal mantras; practice precision in work.",
            "बुध र मङ्गलका मन्त्र जप; कार्यमा सटीकता।",
            references=["Phaladeepika Ch.7", "Chamatkar Chintamani", "Saravali"],
            strength_pct=strength, planets_involved=["Mercury", "Mars"])

def detect_budha_shukra_yoga(planets, lagna_sign):
    mercury = _p(planets, "Mercury")
    venus   = _p(planets, "Venus")
    if mercury and venus and _same_house(mercury, venus):
        h = mercury.get("house", 0)
        strength = 78 if h in KENDRA_HOUSES + TRIKONA_HOUSES else 62
        return _yoga("budha_shukra", "Budha-Shukra Yoga", "बुध-शुक्र योग",
            CAT_CONJUNCTION, "auspicious",
            "Mercury and Venus conjunct — artistic communication, trade in luxury goods, business acumen.",
            "बुध र शुक्रको युति — कलात्मक सञ्चार, विलासिता व्यापार, व्यापारिक चातुर्य।",
            "Success in arts, music, poetry, trade, diplomacy, and media. Charming personality.",
            "कला, संगीत, काव्य, व्यापार, कूटनीति र सञ्चार माध्यममा सफलता।",
            "Worship on Wednesdays and Fridays; develop artistic skills.",
            "बुधबार र शुक्रवार पूजा; कलात्मक कौशल विकास।",
            references=["Phaladeepika Ch.7", "Jataka Parijata"],
            strength_pct=strength, planets_involved=["Mercury", "Venus"])

def detect_guru_mangal_yoga(planets, lagna_sign):
    jupiter = _p(planets, "Jupiter")
    mars    = _p(planets, "Mars")
    if jupiter and mars and _same_house(jupiter, mars):
        h = jupiter.get("house", 0)
        strength = 80 if h in KENDRA_HOUSES + TRIKONA_HOUSES else 65
        return _yoga("guru_mangal", "Guru-Mangal Yoga", "गुरु-मङ्गल योग",
            CAT_CONJUNCTION, "auspicious",
            "Jupiter and Mars conjunct — wisdom combined with courage, military/spiritual leadership.",
            "गुरु र मङ्गलको युति — ज्ञान र साहसको संयोग, सैनिक/आध्यात्मिक नेतृत्व।",
            "Leadership, courage with wisdom, success in military or spiritual fields, administrative excellence.",
            "नेतृत्व, ज्ञानसहित साहस, सैनिक वा आध्यात्मिक क्षेत्रमा सफलता।",
            "Worship Mars on Tuesdays and Jupiter on Thursdays; practice righteous courage.",
            "मङ्गलवार र गुरुवार पूजा; धर्मपूर्ण साहसको अभ्यास।",
            references=["Chamatkar Chintamani", "Phaladeepika Ch.7"],
            strength_pct=strength, planets_involved=["Jupiter", "Mars"])

def detect_surya_guru_yoga(planets, lagna_sign):
    sun     = _p(planets, "Sun")
    jupiter = _p(planets, "Jupiter")
    if sun and jupiter and _same_house(sun, jupiter):
        h = sun.get("house", 0)
        strength = 78 if h in KENDRA_HOUSES + TRIKONA_HOUSES else 63
        return _yoga("surya_guru", "Surya-Guru Yoga", "सूर्य-गुरु योग",
            CAT_CONJUNCTION, "auspicious",
            "Sun and Jupiter conjunct — royal wisdom, governmental authority, and spiritual leadership.",
            "सूर्य र गुरुको युति — राजकीय बुद्धि, सरकारी अधिकार, र आध्यात्मिक नेतृत्व।",
            "Government positions, judicial roles, teaching, wisdom, and respected social status.",
            "सरकारी पद, न्यायिक भूमिका, शिक्षण, ज्ञान, र सम्मानित सामाजिक स्थिति।",
            "Worship the Sun and Guru on Sundays and Thursdays.",
            "आइतवार र गुरुवार सूर्य र गुरुको पूजा।",
            references=["Phaladeepika Ch.7", "Saravali", "Chamatkar Chintamani"],
            strength_pct=strength, planets_involved=["Sun", "Jupiter"])

def detect_chandra_mangal_yoga(planets, lagna_sign):
    moon = _p(planets, "Moon")
    mars = _p(planets, "Mars")
    if moon and mars and _same_house(moon, mars):
        h = moon.get("house", 0)
        return _yoga("chandra_mangal_y", "Chandra-Mangal Yoga", "चन्द्र-मङ्गल योग",
            CAT_CONJUNCTION, "auspicious",
            "Moon and Mars conjunct — passion, wealth through real estate, and strong emotional drive.",
            "चन्द्र र मङ्गलको युति — जोश, भूमि सम्पत्तिबाट धन, र बलियो भावनात्मक उत्साह।",
            "Wealth through land/property, passion, boldness, success in business, and athletic ability.",
            "भूमि/सम्पत्तिबाट धन, जोश, साहस, व्यापारमा सफलता, र खेलकुद क्षमता।",
            "Chant both Moon and Mars mantras; donate red items on Tuesdays.",
            "चन्द्र र मङ्गल दुवैका मन्त्र जप; मङ्गलवार रातो वस्तु दान।",
            references=["Phaladeepika Ch.7", "Saravali Ch.36", "Chamatkar Chintamani"],
            strength_pct=72, planets_involved=["Moon", "Mars"])

# ─────────────────────────────────────────────
# PARIVARTANA (EXCHANGE) YOGAS
# (BPHS Ch.35, Phaladeepika)
# ─────────────────────────────────────────────

def detect_maha_parivartana(planets, lagna_sign):
    """Exchange between Kendra/Trikona lords = Maha Parivartana"""
    results = []
    good_houses = KENDRA_HOUSES + TRIKONA_HOUSES
    for i, p in enumerate(planets):
        for q in planets[i+1:]:
            if p["name"] in ["Rahu", "Ketu"] or q["name"] in ["Rahu", "Ketu"]:
                continue
            if _mutual_exchange(p, q, lagna_sign):
                ph, qh = p.get("house",0), q.get("house",0)
                if ph in good_houses and qh in good_houses:
                    results.append((p["name"], q["name"], ph, qh))
    if results:
        desc = "; ".join([f"{a}(H{ph})↔{b}(H{qh})" for a,b,ph,qh in results])
        desc_ne = "; ".join([f"{_pn(a,'ne')}({ph}भाव)↔{_pn(b,'ne')}({qh}भाव)" for a,b,ph,qh in results])
        # Preserve deterministic planet order. Set iteration order varies between
        # Python processes and made otherwise identical reports compare unequal.
        involved = list(dict.fromkeys(p for t in results for p in [t[0], t[1]]))
        return _yoga("maha_parivartana", "Maha Parivartana Yoga", "महा परिवर्तन योग",
            CAT_PARIVARTANA, "highly_auspicious",
            f"Exchange between Kendra/Trikona lords ({desc}) — supreme Raja Yoga through exchange.",
            f"केन्द्र/त्रिकोण भावेशहरूको आदानप्रदान ({desc_ne}) — आदानप्रदानबाट सर्वोच्च राजयोग।",
            "Exceptional fortune, powerful career, royal status, and life-changing positive events.",
            "असाधारण सौभाग्य, शक्तिशाली करियर, राजकीय दर्जा, र जीवन परिवर्तन गर्ने शुभ घटनाहरू।",
            "Honor and serve the planets involved; wear appropriate gemstones.",
            "सम्बन्धित ग्रहको सम्मान र सेवा; उचित रत्न लगाउनुहोस्।",
            references=["BPHS Ch.35", "Phaladeepika Ch.7 v.8", "Sarvartha Chintamani"],
            strength_pct=90, planets_involved=involved)
    return None

def detect_khala_parivartana(planets, lagna_sign):
    """Exchange where one planet is in Dusthana"""
    results = []
    for i, p in enumerate(planets):
        for q in planets[i+1:]:
            if p["name"] in ["Rahu","Ketu"] or q["name"] in ["Rahu","Ketu"]: continue
            if _mutual_exchange(p, q, lagna_sign):
                ph, qh = p.get("house",0), q.get("house",0)
                if (ph in DUSTHANA_HOUSES) != (qh in DUSTHANA_HOUSES):  # exactly one in dusthana
                    results.append((p["name"], q["name"], ph, qh))
    if results:
        a,b,ph,qh = results[0]
        return _yoga("khala_parivartana", "Khala Parivartana Yoga", "खल परिवर्तन योग",
            CAT_PARIVARTANA, "neutral",
            f"Exchange between {a}(H{ph}) and {b}(H{qh}) — mixed results, one dusthana lord involved.",
            f"{_pn(a,'ne')}({ph}भाव) र {_pn(b,'ne')}({qh}भाव) को आदानप्रदान — मिश्रित फल।",
            "Mixed results — some areas thrive while others face obstacles; overall moderate outcome.",
            "मिश्रित फल — केही क्षेत्र फस्टाउँछ भने अन्यमा बाधा; समग्र मध्यम परिणाम।",
            "Balance efforts across life areas; don't neglect troubled houses.",
            "जीवनका क्षेत्रहरूमा प्रयास सन्तुलित गर्नुहोस्।",
            references=["BPHS Ch.35", "Phaladeepika Ch.7"],
            strength_pct=55, planets_involved=[a, b])
    return None

def detect_dainya_parivartana(planets, lagna_sign):
    """Exchange where both planets are in Dusthana"""
    results = []
    for i, p in enumerate(planets):
        for q in planets[i+1:]:
            if p["name"] in ["Rahu","Ketu"] or q["name"] in ["Rahu","Ketu"]: continue
            if _mutual_exchange(p, q, lagna_sign):
                ph, qh = p.get("house",0), q.get("house",0)
                if ph in DUSTHANA_HOUSES and qh in DUSTHANA_HOUSES:
                    results.append((p["name"], q["name"], ph, qh))
    if results:
        a,b,ph,qh = results[0]
        return _yoga("dainya_parivartana", "Dainya Parivartana Yoga", "दैन्य परिवर्तन योग",
            CAT_PARIVARTANA, "challenging",
            f"Exchange between dusthana lords {a}(H{ph}) and {b}(H{qh}) — adversity and hardship.",
            f"दुष्टान भावेश {_pn(a,'ne')}({ph}भाव) र {_pn(b,'ne')}({qh}भाव) को आदानप्रदान — दुःख र कठिनाइ।",
            "Poverty, disease, enmity, losses, and persistent life challenges in affected areas.",
            "गरिबी, रोग, शत्रुता, हानि, र प्रभावित क्षेत्रमा निरन्तर जीवन चुनौतीहरू।",
            "Perform remedies for both planets; recite Vishnu Sahasranama and Hanuman Chalisa daily.",
            "दुवै ग्रहको उपाय; दैनिक विष्णु सहस्रनाम र हनुमान चालीसा।",
            references=["BPHS Ch.35", "Phaladeepika Ch.7"],
            strength_pct=40, planets_involved=[a, b])
    return None

# ─────────────────────────────────────────────
# NABHAS YOGAS (BPHS Ch.29, Brihat Jataka)
# ─────────────────────────────────────────────

def detect_rajju_yoga(planets, lagna_sign):
    """All planets in movable (chara) signs: 1,4,7,10"""
    MOVABLE = [1, 4, 7, 10]
    non_rk = [p for p in planets if p["name"] not in ["Rahu","Ketu"]]
    if all(p.get("sign_number") in MOVABLE for p in non_rk) and non_rk:
        return _yoga("rajju_yoga", "Rajju Yoga (Nabhas)", "रज्जु योग (नाभस)",
            CAT_NABHAS, "auspicious",
            "All planets in movable (Chara) signs — Rajju Nabhas Yoga, signifying constant movement.",
            "सबै ग्रह चर राशिमा — रज्जु नाभस योग, निरन्तर गतिशीलताको संकेत।",
            "Frequent travel, dynamic life, restlessness, adventure, and success through change and movement.",
            "बारम्बार यात्रा, गतिशील जीवन, बेचैनी, साहसिक कार्य, र परिवर्तन र गतिबाट सफलता।",
            "Embrace mobility; work in travel, diplomacy, or import-export fields.",
            "गतिशीलता अँगाल्नुहोस्; यात्रा, कूटनीति वा आयात-निर्यात क्षेत्रमा काम।",
            references=["BPHS Ch.29", "Brihat Jataka Ch.19", "Saravali Ch.11"],
            strength_pct=68, planets_involved=[])
    return None

def detect_musala_yoga(planets, lagna_sign):
    """All planets in fixed (sthira) signs: 2,5,8,11"""
    FIXED = [2, 5, 8, 11]
    non_rk = [p for p in planets if p["name"] not in ["Rahu","Ketu"]]
    if all(p.get("sign_number") in FIXED for p in non_rk) and non_rk:
        return _yoga("musala_yoga", "Musala Yoga (Nabhas)", "मूसल योग (नाभस)",
            CAT_NABHAS, "auspicious",
            "All planets in fixed (Sthira) signs — Musala Yoga of steadiness and determination.",
            "सबै ग्रह स्थिर राशिमा — स्थिरता र दृढताको मूसल योग।",
            "Stability, determination, wealth accumulation, respect, and leadership qualities.",
            "स्थिरता, दृढता, धन संचय, सम्मान, र नेतृत्व गुण।",
            "Build long-term foundations; invest in fixed assets and consistent practices.",
            "दीर्घकालीन आधार बनाउनुहोस्; स्थिर सम्पत्तिमा लगानी।",
            references=["BPHS Ch.29", "Brihat Jataka Ch.19", "Saravali Ch.11"],
            strength_pct=70, planets_involved=[])
    return None

def detect_nala_yoga(planets, lagna_sign):
    """All planets in dual (dwiswabhava) signs: 3,6,9,12"""
    DUAL = [3, 6, 9, 12]
    non_rk = [p for p in planets if p["name"] not in ["Rahu","Ketu"]]
    if all(p.get("sign_number") in DUAL for p in non_rk) and non_rk:
        return _yoga("nala_yoga", "Nala Yoga (Nabhas)", "नल योग (नाभस)",
            CAT_NABHAS, "auspicious",
            "All planets in dual (Dwiswabhava) signs — versatile, adaptable, and multitalented.",
            "सबै ग्रह द्विस्वभाव राशिमा — बहुमुखी, अनुकूलनशील र बहुप्रतिभाशाली।",
            "Versatility, adaptability, success in multiple fields, but potential lack of focus.",
            "बहुमुखी प्रतिभा, अनुकूलनशीलता, बहु क्षेत्रमा सफलता, तर ध्यान केन्द्रीकरणमा कमी।",
            "Focus on one primary skill; balance versatility with depth.",
            "एउटा प्रमुख सीपमा ध्यान दिनुहोस्; बहुमुखिता र गहराइको सन्तुलन।",
            references=["BPHS Ch.29", "Brihat Jataka Ch.19"],
            strength_pct=65, planets_involved=[])
    return None

# ─────────────────────────────────────────────
# VIDYA YOGAS (विद्या योग)
# ─────────────────────────────────────────────

def detect_budha_guru_yoga(planets, lagna_sign):
    mercury = _p(planets, "Mercury")
    jupiter = _p(planets, "Jupiter")
    if mercury and jupiter and _same_house(mercury, jupiter):
        h = mercury.get("house", 0)
        strength = 82 if h in KENDRA_HOUSES + TRIKONA_HOUSES else 65
        return _yoga("budha_guru_yoga", "Budha-Guru Vidya Yoga", "बुध-गुरु विद्या योग",
            CAT_VIDYA, "auspicious",
            "Mercury and Jupiter conjunct — supreme learning, teaching ability, and philosophical mind.",
            "बुध र गुरुको युति — उत्कृष्ट विद्या, शिक्षण क्षमता, र दार्शनिक मस्तिष्क।",
            "Excellence in education, philosophy, law, astrology, and teaching. Respected scholar.",
            "शिक्षा, दर्शन, कानून, ज्योतिष र शिक्षणमा उत्कृष्टता। सम्मानित विद्वान।",
            "Study sacred texts; worship Saraswati and Brihaspati; donate books.",
            "धर्मग्रन्थ अध्ययन; सरस्वती र बृहस्पति पूजा; पुस्तक दान।",
            references=["Phaladeepika Ch.7", "Chamatkar Chintamani", "BPHS"],
            strength_pct=strength, planets_involved=["Mercury", "Jupiter"])
    return None

# ─────────────────────────────────────────────
# DARIDRA (POVERTY) & DUR YOGAS
# (BPHS Ch.37, Phaladeepika Ch.9)
# ─────────────────────────────────────────────

def detect_daridra_yoga(planets, lagna_sign):
    """Lagna lord or 2nd lord in Dusthana, or 11th lord debilitated"""
    ll_name = _lord_of(1, lagna_sign)
    lord2   = _lord_of(2, lagna_sign)
    lord11  = _lord_of(11, lagna_sign)
    ll  = _p(planets, ll_name)
    p2  = _p(planets, lord2)
    p11 = _p(planets, lord11)
    conditions = []
    if ll and ll.get("house") in DUSTHANA_HOUSES and not (_is_exalted(ll) or _is_own_sign(ll)):
        conditions.append(f"Lagna lord {ll_name} in dusthana H{ll.get('house')}")
    if p2 and p2.get("house") in DUSTHANA_HOUSES and not (_is_exalted(p2) or _is_own_sign(p2)):
        conditions.append(f"2nd lord {lord2} in dusthana H{p2.get('house')}")
    if p11 and p11.get("exaltation_state") == "debilitated":
        conditions.append(f"11th lord {lord11} debilitated")
    if conditions:
        return _yoga("daridra_yoga", "Daridra Yoga", "दारिद्र योग",
            CAT_DOSHA, "challenging",
            "Financial weakness: " + "; ".join(conditions),
            "आर्थिक कमजोरी: " + "; ".join([c.replace("Lagna lord","लग्नेश").replace("2nd lord","द्वितीयेश").replace("11th lord","एकादशेश").replace("in dusthana","दुष्टानमा").replace("debilitated","नीचमा") for c in conditions]),
            "Financial hardships, debt, poverty, or instability in wealth. Requires sustained effort to overcome.",
            "आर्थिक कठिनाइ, ऋण, गरिबी, वा धनमा अस्थिरता। पार गर्न निरन्तर प्रयास आवश्यक।",
            "Worship Goddess Lakshmi on Fridays; perform Kuber puja; donate to the poor consistently.",
            "शुक्रवार लक्ष्मी पूजा; कुबेर पूजा; नियमित रूपमा गरिबलाई दान।",
            references=["BPHS Ch.37", "Phaladeepika Ch.9", "Saravali Ch.37"],
            strength_pct=45, planets_involved=[ll_name, lord2])
    return None

def detect_papakartari(planets, lagna_sign):
    """Malefics on both sides of Lagna or Moon"""
    MALEFICS = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]
    lagna_h = 1
    moon = _p(planets, "Moon")
    moon_h = moon.get("house", 0) if moon else 0
    results = []
    for ref_h, label, label_ne in [(lagna_h, "Lagna", "लग्न"), (moon_h, "Moon", "चन्द्र")]:
        if ref_h == 0: continue
        h2  = ((ref_h) % 12) + 1
        h12 = ((ref_h - 2) % 12) + 1
        mal_2nd  = [p["name"] for p in planets if p["name"] in MALEFICS and p.get("house") == h2]
        mal_12th = [p["name"] for p in planets if p["name"] in MALEFICS and p.get("house") == h12]
        if mal_2nd and mal_12th:
            results.append((label, label_ne, mal_2nd, mal_12th))
    if results:
        label, label_ne, m2, m12 = results[0]
        return _yoga("papakartari", "Papa-Kartari Yoga", "पापकर्तरी योग",
            CAT_DOSHA, "challenging",
            f"Malefics ({', '.join(m2)}) and ({', '.join(m12)}) hem the {label} — scissors of malefics.",
            f"पाप ग्रह ({', '.join([_pn(x,'ne') for x in m2])}) र ({', '.join([_pn(x,'ne') for x in m12])}) ले {label_ne} लाई घेरेका छन्।",
            "Obstacles, pressure, restrictions, stress, and suppression of natural abilities.",
            "बाधाहरू, दबाब, प्रतिबन्धहरू, तनाव, र प्राकृतिक क्षमताको दमन।",
            "Perform Navagraha puja; recite Mahamrityunjaya mantra; strengthen the hemmed planet.",
            "नवग्रह पूजा; महामृत्युञ्जय मन्त्र; घेरिएको ग्रहलाई बलियो बनाउनुहोस्।",
            references=["BPHS Ch.38", "Phaladeepika Ch.9", "Saravali"],
            strength_pct=40, planets_involved=m2 + m12)
    return None

def detect_neecha_yoga(planets, lagna_sign):
    """Debilitated planets not cancelled"""
    debilitated = [p for p in planets if p.get("exaltation_state") == "debilitated"
                   and not p.get("neecha_bhanga")]
    if debilitated:
        names = [p["name"] for p in debilitated]
        names_ne = [_pn(n,"ne") for n in names]
        return _yoga("neecha_yoga", "Neecha Yoga", "नीच योग",
            CAT_DOSHA, "challenging",
            f"Debilitated planets without cancellation: {', '.join(names)}.",
            f"नीचभंग नभएका नीच ग्रह: {', '.join(names_ne)}।",
            "Weakness in the significations of the debilitated planet — delays, humiliation, and reduced results.",
            "नीच ग्रहको कारकत्वमा कमजोरी — ढिलाइ, अपमान, र कम परिणाम।",
            "Worship the debilitated planet; wear its gemstone; perform its specific remedies.",
            "नीच ग्रहको पूजा; यसको रत्न लगाउनुहोस्; यसका उपाय गर्नुहोस्।",
            references=["BPHS Ch.27", "Phaladeepika Ch.5", "Saravali Ch.22"],
            strength_pct=35, planets_involved=names)
    return None

def detect_vish_yoga(planets, lagna_sign):
    """Saturn and Moon conjunct (Vish = poison)"""
    saturn = _p(planets, "Saturn")
    moon   = _p(planets, "Moon")
    if saturn and moon and _same_house(saturn, moon):
        return _yoga("vish_yoga", "Vish Yoga", "विष योग",
            CAT_DOSHA, "challenging",
            "Saturn and Moon conjunct — Vish (Poison) Yoga causing mental distress and pessimism.",
            "शनि र चन्द्रको युति — विष योग, मानसिक पीडा र निराशावाद।",
            "Depression, pessimism, mental health challenges, difficulties with mother, and emotional instability.",
            "अवसाद, निराशावाद, मानसिक स्वास्थ्य चुनौती, माताको कठिनाइ, र भावनात्मक अस्थिरता।",
            "Worship Shiva and Chandra; practice meditation and mindfulness daily; avoid isolation.",
            "शिव र चन्द्रको पूजा; ध्यान र माइन्डफुलनेसको दैनिक अभ्यास; एकान्तबाट बच्नुहोस्।",
            references=["BPHS Ch.38", "Phaladeepika Ch.9", "Brihat Jataka"],
            strength_pct=38, planets_involved=["Saturn", "Moon"])
    return None

# ─────────────────────────────────────────────
# AYUR YOGAS (आयु योग)
# (BPHS Ch.44, Saravali, Jataka Parijata)
# ─────────────────────────────────────────────

def detect_ayur_yoga(planets, lagna_sign):
    """Estimate life span category based on Lagna/8th lord strength"""
    ll_name = _lord_of(1, lagna_sign)
    lord8   = _lord_of(8, lagna_sign)
    ll  = _p(planets, ll_name)
    p8  = _p(planets, lord8)
    jupiter = _p(planets, "Jupiter")
    saturn  = _p(planets, "Saturn")
    # Purna Ayur: Both Lagna lord and 8th lord strong
    if (ll and (_is_exalted(ll) or _is_own_sign(ll)) and ll.get("house") in KENDRA_HOUSES + TRIKONA_HOUSES and
        p8 and (_is_exalted(p8) or _is_own_sign(p8))):
        return _yoga("purna_ayur", "Purna Ayur Yoga", "पूर्णायु योग",
            CAT_AYUR, "auspicious",
            f"Strong Lagna lord ({ll_name}) and 8th lord ({lord8}) — indicator of long, full life span.",
            f"बलियो लग्नेश ({_pn(ll_name,'ne')}) र अष्टमेश ({_pn(lord8,'ne')}) — दीर्घ, पूर्ण आयुको संकेत।",
            "Long life, robust health throughout life, and natural death at an old age.",
            "दीर्घायु, जीवनभर सबल स्वास्थ्य, र वृद्धावस्थामा स्वाभाविक मृत्यु।",
            "Maintain healthy routines; worship longevity deities (Mahamrityunjaya).",
            "स्वस्थ दैनिकी पालना; महामृत्युञ्जयको पूजा।",
            references=["BPHS Ch.44", "Saravali Ch.41", "Jataka Parijata"],
            strength_pct=82, planets_involved=[ll_name, lord8])
    return None

# ─────────────────────────────────────────────
# SANYASA YOGA (संन्यास योग)
# (BPHS Ch.38, Narada Samhita)
# ─────────────────────────────────────────────

def detect_sanyasa_yoga(planets, lagna_sign):
    """4+ planets in one sign, or Saturn strong in 9th/12th with Jupiter"""
    from collections import Counter
    sign_counts = Counter(p.get("sign_number") for p in planets if p["name"] not in ["Rahu","Ketu"])
    if sign_counts:
        max_sign, max_count = sign_counts.most_common(1)[0]
        if max_count >= 4:
            involved = [p["name"] for p in planets if p.get("sign_number") == max_sign]
            return _yoga("sanyasa_yoga", "Sanyasa Yoga", "सन्यास योग",
                CAT_SANYASA, "spiritual",
                f"Four or more planets ({', '.join(involved)}) in one sign — powerful renunciation yoga.",
                f"चार वा बढी ग्रह ({', '.join([_pn(n,'ne') for n in involved])}) एउटै राशिमा — संन्यास योग।",
                "Strong renunciation tendency, spiritual path, service to humanity, or life as an ascetic.",
                "बलियो त्याग प्रवृत्ति, आध्यात्मिक पथ, मानवसेवा, वा तपस्वी जीवन।",
                "Embrace spiritual practice; serve others without expectation; study sacred texts.",
                "आध्यात्मिक अभ्यास अँगाल्नुहोस्; निःस्वार्थ सेवा; धर्मग्रन्थ अध्ययन।",
                references=["BPHS Ch.38 v.14-17", "Narada Samhita", "Jataka Parijata 3.28"],
                strength_pct=75, planets_involved=involved)
    return None

# ─────────────────────────────────────────────
# STRENGTH PERCENTAGE CALCULATOR
# ─────────────────────────────────────────────

def _compute_strength_pct(yoga: Dict, planets: List[Dict], lagna_sign: int) -> int:
    """If strength_pct not set, compute a rough estimate from planet strengths."""
    if yoga.get("strength_pct") is not None:
        return yoga["strength_pct"]
    involved = yoga.get("planets_involved", [])
    if not involved:
        return 60  # default
    scores = []
    for name in involved:
        p = _p(planets, name)
        if not p: continue
        score = 50
        if _is_exalted(p): score = 95
        elif _is_own_sign(p): score = 85
        elif p.get("exaltation_state") == "debilitated": score = 25
        if p.get("is_retrograde"): score += 5
        if p.get("is_combust"): score -= 15
        if p.get("house") in KENDRA_HOUSES: score += 8
        if p.get("house") in TRIKONA_HOUSES: score += 6
        if p.get("house") in DUSTHANA_HOUSES: score -= 10
        scores.append(max(10, min(99, score)))
    return int(sum(scores) / len(scores)) if scores else 60

# ─────────────────────────────────────────────
# CHART-SPECIFIC FORMATION DETAILS
# ─────────────────────────────────────────────

SIGN_NAMES_EN = {
    1:"Aries",2:"Taurus",3:"Gemini",4:"Cancer",5:"Leo",6:"Virgo",
    7:"Libra",8:"Scorpio",9:"Sagittarius",10:"Capricorn",11:"Aquarius",12:"Pisces"
}
SIGN_NAMES_NE = {
    1:"मेष",2:"वृष",3:"मिथुन",4:"कर्कट",5:"सिंह",6:"कन्या",
    7:"तुला",8:"वृश्चिक",9:"धनु",10:"मकर",11:"कुम्भ",12:"मीन"
}
HOUSE_NAMES_NE = {
    1:"प्रथम (लग्न)",2:"द्वितीय (धन)",3:"तृतीय (साहस)",4:"चतुर्थ (माता/गृह)",
    5:"पञ्चम (सन्तान/बुद्धि)",6:"षष्ठ (शत्रु/रोग)",7:"सप्तम (विवाह)",
    8:"अष्टम (आयु/रहस्य)",9:"नवम (भाग्य/धर्म)",10:"दशम (कर्म/यश)",
    11:"एकादश (लाभ)",12:"द्वादश (व्यय/मोक्ष)"
}
HOUSE_NAMES_EN = {
    1:"1st (Lagna)",2:"2nd (Wealth)",3:"3rd (Courage)",4:"4th (Home/Mother)",
    5:"5th (Children/Intellect)",6:"6th (Enemies/Health)",7:"7th (Marriage)",
    8:"8th (Longevity/Secrets)",9:"9th (Fortune/Dharma)",10:"10th (Career/Fame)",
    11:"11th (Gains)",12:"12th (Expenditure/Moksha)"
}

def _planet_detail_en(p: Dict) -> str:
    """One-line description of a planet's chart position."""
    if not p: return ""
    name  = p.get("name","")
    house = p.get("house", "?")
    sign  = SIGN_NAMES_EN.get(p.get("sign_number",0), "")
    deg   = round(p.get("longitude_in_sign", 0), 2)
    state = p.get("exaltation_state","")
    retro = " ℞" if p.get("is_retrograde") else ""
    combust = " (combust)" if p.get("is_combust") else ""
    state_str = f" [{state.upper()}]" if state in ["exalted","debilitated"] else ""
    own = " [OWN]" if _is_own_sign(p) and state != "exalted" else ""
    return f"{name}{retro}: {sign} {deg}° | House {house}{state_str}{own}{combust}"

def _planet_detail_ne(p: Dict) -> str:
    """One-line Nepali description of a planet's chart position."""
    if not p: return ""
    name  = _pn(p.get("name",""), "ne")
    house = p.get("house", "?")
    sign  = SIGN_NAMES_NE.get(p.get("sign_number",0), "")
    deg   = round(p.get("longitude_in_sign", 0), 2)
    state = p.get("exaltation_state","")
    retro = " (वक्री)" if p.get("is_retrograde") else ""
    combust = " (अस्त)" if p.get("is_combust") else ""
    state_map = {"exalted":"उच्च","debilitated":"नीच"}
    state_str = f" [{state_map.get(state,'')}]" if state in state_map else ""
    own = " [स्वगृह]" if _is_own_sign(p) and state != "exalted" else ""
    h_name = HOUSE_NAMES_NE.get(house, f"{house}औं भाव")
    return f"{name}{retro}: {sign} {deg}° | {h_name}{state_str}{own}{combust}"

def _add_formation_details(yoga: Dict, planets: List[Dict], lagna_sign: int) -> Dict:
    """
    Enrich a yoga dict with:
      - formation_en / formation_ne  : HOW this yoga forms in THIS chart
      - chart_position_en / _ne      : WHERE the yoga planets sit (house/sign/degree)
      - planet_rows                  : list of dicts for frontend table display
    """
    involved_names = yoga.get("planets_involved", [])
    involved_planets = [_p(planets, n) for n in involved_names if _p(planets, n)]

    # ── planet_rows for table ────────────────────────────────────
    planet_rows = []
    for p in involved_planets:
        if not p: continue
        sign_num = p.get("sign_number", 0)
        house    = p.get("house", 0)
        state    = p.get("exaltation_state", "normal")
        own      = _is_own_sign(p) and state != "exalted"
        planet_rows.append({
            "name_en":    p.get("name",""),
            "name_ne":    _pn(p.get("name",""), "ne"),
            "sign_en":    SIGN_NAMES_EN.get(sign_num,""),
            "sign_ne":    SIGN_NAMES_NE.get(sign_num,""),
            "sign_num":   sign_num,
            "house":      house,
            "house_name_en": HOUSE_NAMES_EN.get(house, f"H{house}"),
            "house_name_ne": HOUSE_NAMES_NE.get(house, f"{house}औं भाव"),
            "degree":     round(p.get("longitude_in_sign", 0), 2),
            "state":      state,
            "is_own":     own,
            "is_retro":   bool(p.get("is_retrograde")),
            "is_combust": bool(p.get("is_combust")),
        })

    # ── formation strings ───────────────────────────────────────
    y_name_en = yoga.get("name", "Yoga")
    y_name_ne = yoga.get("nepali", "योग")

    if planet_rows:
        parts_en = [f"{r['name_en']} is in {r['sign_en']} sign in the {r['house_name_en']}" +
                    (f" (Exalted)" if r['state'] == 'exalted' else "") +
                    (f" (Debilitated)" if r['state'] == 'debilitated' else "") +
                    (" (Own Sign)" if r['is_own'] else "") +
                    (" (Retrograde)" if r['is_retro'] else "") +
                    (" (Combust)" if r['is_combust'] else "")
                    for r in planet_rows]
        parts_ne = [f"{r['sign_ne']} राशिमा {r['house_name_ne']}मा {_pn(r['name_en'], 'ne')}" +
                    (f" उच्च भएर" if r['state'] == 'exalted' else "") +
                    (f" नीच भएर" if r['state'] == 'debilitated' else "") +
                    (" स्वगृह भएर" if r['is_own'] else "") +
                    (" (वक्री)" if r['is_retro'] else "") +
                    (" (अस्त)" if r['is_combust'] else "")
                    for r in planet_rows]

        formation_en = f"**{y_name_en}** forms in this chart because " + ", and ".join(parts_en) + "."
        formation_ne = f"यो कुण्डलीमा **{y_name_ne}** {', '.join(parts_ne)} अवस्थित भएको कारणले बनेको छ।"

        pos_en_parts = [f"{r['name_en']}: House {r['house']} ({r['sign_en']}, {r['degree']}°)" for r in planet_rows]
        pos_ne_parts = [f"{r['name_ne']}: {r['house_name_ne']} ({r['sign_ne']}, {r['degree']}°)" for r in planet_rows]
        chart_pos_en = " | ".join(pos_en_parts)
        chart_pos_ne = " | ".join(pos_ne_parts)
    else:
        formation_en = f"**{y_name_en}** forms based on the overall configuration of the chart (Lagna: {SIGN_NAMES_EN.get(lagna_sign,'')}). {yoga.get('cause_en','')}"
        formation_ne = f"यो कुण्डलीमा **{y_name_ne}** कुण्डलीको समग्र ग्रह स्थितिको आधारमा बनेको छ (लग्न राशि: {SIGN_NAMES_NE.get(lagna_sign,'')})। {yoga.get('cause_ne','')}"
        chart_pos_en = f"Lagna: {SIGN_NAMES_EN.get(lagna_sign,'')} | General chart layout"
        chart_pos_ne = f"लग्न: {SIGN_NAMES_NE.get(lagna_sign,'')} | समग्र ग्रह स्थिति"

    yoga["formation_en"]       = formation_en
    yoga["formation_ne"]       = formation_ne
    yoga["chart_position_en"]  = chart_pos_en
    yoga["chart_position_ne"]  = chart_pos_ne
    yoga["planet_rows"]        = planet_rows
    return yoga

# ─────────────────────────────────────────────
# MASTER FUNCTION
# ─────────────────────────────────────────────

def calculate_parashara_yogas_with_diagnostics(
    planets: List[Dict[str, Any]], lagna_sign: int
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Detect all yogas for the given chart, with structured detector diagnostics.

    Covers: BPHS, Phaladeepika, Saravali, Jataka Parijata, Brihat Jataka,
            Uttara Kalamrita, Sarvartha Chintamani, Chamatkar Chintamani.

    Returns a tuple ``(yogas, diagnostics)``:

    - ``yogas``: list of active yoga dicts with category, severity, bilingual
      descriptions, references, strength_pct, and planets_involved.
    - ``diagnostics``: one entry per detector that raised an exception, with
      ``detector``, ``error_type`` and ``error`` fields. A detector that
      returns ``None`` or a valid result produces no diagnostic entry, so an
      empty list means every detector ran cleanly.

    This function never raises: a single broken detector can no longer make a
    yoga silently disappear from the report without an audit trail.
    """
    detectors = [
        # ── Pancha Mahapurusha (5) ──────────────────
        detect_ruchaka,
        detect_bhadra,
        detect_hamsa,
        detect_malavya,
        detect_sasa,
        # ── Raja Yogas (6) ──────────────────────────
        detect_raja_yoga,
        detect_chamara_yoga,
        detect_mahabhagya_yoga,
        detect_dharmakarmadhipati,
        detect_lagnesh_navamesh,
        detect_lagnesh_panchamesh,
        detect_panchamesh_dashamesh,
        # ── Viparita Raja Yogas (3) ─────────────────
        detect_harsha_yoga,
        detect_sarala_yoga,
        detect_vimala_yoga,
        detect_viparita_raja_yoga,   # generic viparita
        # ── Dhana Yogas (4) ─────────────────────────
        detect_dhana_yoga,
        detect_lakshmi_yoga,
        detect_kubera_yoga,
        detect_vasumati_yoga,
        # ── Chandra Yogas (7) ───────────────────────
        detect_gaja_kesari,
        detect_sunapha,
        detect_anapha,
        detect_durudhura,
        detect_kemadruma,
        detect_adhi_yoga,
        detect_shakata_yoga,
        # ── Surya Yogas (4) ─────────────────────────
        detect_budhaditya,
        detect_vesi_yoga,
        detect_vasi_yoga,
        detect_ubhayachari,
        # ── Conjunction Yogas (7) ───────────────────
        detect_chandra_mangal,        # existing
        detect_chandra_mangal_yoga,   # new (duplicate check handled by different id)
        detect_guru_chandal,
        detect_saraswati_yoga,
        detect_budha_mangal_yoga,
        detect_budha_shukra_yoga,
        detect_guru_mangal_yoga,
        detect_surya_guru_yoga,
        detect_budha_guru_yoga,
        # ── Parivartana Yogas (3) ───────────────────
        detect_maha_parivartana,
        detect_khala_parivartana,
        detect_dainya_parivartana,
        detect_parivartana,           # existing generic
        # ── Nabhas Yogas (3) ────────────────────────
        detect_rajju_yoga,
        detect_musala_yoga,
        detect_nala_yoga,
        # ── Misc Shubha Yogas (7) ───────────────────
        detect_neechabhanga,
        detect_shubha_trikona,
        detect_amala_yoga,
        detect_parvata_yoga,
        detect_kaahala_yoga,
        detect_sankha_yoga,
        # ── Vidya Yogas (1) ─────────────────────────
        # saraswati_yoga already in conjunction above
        # ── Arishta / Dosha (9) ─────────────────────
        detect_kala_sarpa_yoga,
        detect_mangala_dosha,
        detect_grahan_yoga,
        detect_shrapit_yoga,
        detect_pitra_dosha,
        detect_daridra_yoga,
        detect_papakartari,
        detect_neecha_yoga,
        detect_vish_yoga,
        # ── Ayur Yogas (1) ──────────────────────────
        detect_ayur_yoga,
        # ── Sanyasa / Spiritual (3) ─────────────────
        detect_sanyasa_yoga,
        detect_pravrajya_yoga,
        detect_moksha_yoga,
    ]

    seen_ids = set()
    yogas = []
    diagnostics: List[Dict[str, Any]] = []
    for detector in detectors:
        try:
            result = detector(planets, lagna_sign)
            if result and result.get("id") not in seen_ids:
                # Compute strength_pct if not already set
                if result.get("strength_pct") is None:
                    result["strength_pct"] = _compute_strength_pct(result, planets, lagna_sign)
                # Add chart-specific formation details
                _add_formation_details(result, planets, lagna_sign)
                seen_ids.add(result["id"])
                yogas.append(result)
        except Exception as exc:
            # Never crash the entire chart over a single yoga detector, but
            # record the failure so the report can surface it instead of
            # silently dropping the yoga.
            diagnostics.append({
                "detector": getattr(detector, "__name__", repr(detector)),
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

    # Sort: highly_auspicious → auspicious → neutral → spiritual → challenging
    ORDER = {"highly_auspicious": 0, "auspicious": 1, "neutral": 2, "spiritual": 3, "challenging": 4}
    yogas.sort(key=lambda y: ORDER.get(y.get("severity", "neutral"), 2))
    return yogas, diagnostics


def calculate_parashara_yogas(planets: List[Dict[str, Any]], lagna_sign: int) -> List[Dict[str, Any]]:
    """
    Backward-compatible wrapper around
    :func:`calculate_parashara_yogas_with_diagnostics`.

    Returns only the detected yoga list, exactly as before. Callers that need
    the detector audit trail should call the diagnostics variant directly.
    """
    yogas, _diagnostics = calculate_parashara_yogas_with_diagnostics(planets, lagna_sign)
    return yogas
