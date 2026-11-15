"""
Marriage Matching Calculator — Ashtakoot Guna Milan (36 Guna)
पाराशर ज्योतिष अनुसार सम्पूर्ण अष्टकूट विवाह मिलान गणना
Primary input: चन्द्र राशि, चन्द्र नक्षत्र (Swiss Ephemeris द्वारा गणित)
"""

# ─────────────────────────────────────────────────────────────────────────────
# Static Configuration Tables
# ─────────────────────────────────────────────────────────────────────────────

# 1. राशि → वर्ण  (Rashi → Varna)
RASHI_VARNA = {
    1: "Kshatriya",   # मेष    (अग्नि)
    2: "Vaishya",     # वृष    (पृथ्वी)
    3: "Shudra",      # मिथुन  (वायु)
    4: "Brahmin",     # कर्कट  (जल)
    5: "Kshatriya",   # सिंह   (अग्नि)
    6: "Vaishya",     # कन्या  (पृथ्वी)
    7: "Shudra",      # तुला   (वायु)
    8: "Brahmin",     # वृश्चिक (जल)
    9: "Kshatriya",   # धनु    (अग्नि)
    10: "Vaishya",    # मकर    (पृथ्वी)
    11: "Shudra",     # कुम्भ  (वायु)
    12: "Brahmin",    # मीन    (जल)
}
VARNA_RANK = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1}
VARNA_NEPALI = {"Brahmin": "ब्राह्मण", "Kshatriya": "क्षत्रिय",
                "Vaishya": "वैश्य", "Shudra": "शूद्र"}

# 2. राशि → वश्य वर्ग  (Rashi → Vashya class)
# धनु: 1–15° = मानव, 16–30° = चतुष्पद; मकर: 1–15° = चतुष्पद, 16–30° = जलचर
# सरलीकृत whole-sign mapping (पूर्ण राशि आधारित)
RASHI_VASHYA = {
    1: "Chatushpad",   # मेष
    2: "Chatushpad",   # वृष
    3: "Manava",       # मिथुन
    4: "Jalchar",      # कर्कट
    5: "Vanchar",      # सिंह (= Vanchar/Chatushpad)
    6: "Manava",       # कन्या
    7: "Manava",       # तुला
    8: "Keeta",        # वृश्चिक
    9: "Manava",       # धनु (पूर्वार्ध मानव, whole = मानव)
    10: "Chatushpad",  # मकर (पूर्वार्ध चतुष्पद, whole = चतुष्पद)
    11: "Manava",      # कुम्भ
    12: "Jalchar",     # मीन
}
VASHYA_NEPALI = {
    "Chatushpad": "चतुष्पद", "Manava": "मानव", "Jalchar": "जलचर",
    "Vanchar": "वनचर", "Keeta": "कीट"
}

# Vashya compatibility score matrix [groom_vashya][bride_vashya]
VASHYA_SCORE = {
    "Chatushpad": {"Chatushpad": 2, "Manava": 1, "Jalchar": 0, "Vanchar": 0, "Keeta": 0},
    "Manava":     {"Chatushpad": 1, "Manava": 2, "Jalchar": 1, "Vanchar": 0, "Keeta": 0},
    "Jalchar":    {"Chatushpad": 0, "Manava": 1, "Jalchar": 2, "Vanchar": 0, "Keeta": 0},
    "Vanchar":    {"Chatushpad": 0, "Manava": 0, "Jalchar": 0, "Vanchar": 2, "Keeta": 0},
    "Keeta":      {"Chatushpad": 0, "Manava": 0, "Jalchar": 0, "Vanchar": 0, "Keeta": 2},
}

# 3. नक्षत्र → तारा (Nakshatra → Tara group, 1–9)
# तारा ९ प्रकार: जन्म(1), सम्पत्(2), विपत्(3), क्षेम(4), प्रत्यारी(5), साधक(6), नैधन(7), मित्र(8), परममित्र(9)
# Standard shubha taras (excluding janma which is neutral):
SHUBHA_TARAS = {2, 4, 6, 8, 9}   # सम्पत्, क्षेम, साधक, मित्र, परममित्र
ASHUBHA_TARAS = {3, 5, 7}         # विपत्, प्रत्यारी, नैधन
TARA_NAMES = {
    1: "जन्म", 2: "सम्पत्", 3: "विपत्", 4: "क्षेम",
    5: "प्रत्यारी", 6: "साधक", 7: "नैधन", 8: "मित्र", 9: "परममित्र"
}

# 4. नक्षत्र → योनि  (Nakshatra → Yoni animal)
# BPHS standard
NAKSHATRA_YONI = {
    1:  ("Ashwa", "M"),    # अश्विनी — अश्व (नर)
    2:  ("Gaja", "F"),     # भरणी — गज (मादा)
    3:  ("Mesha", "F"),    # कृत्तिका — मेष (मादा)
    4:  ("Sarpa", "M"),    # रोहिणी — सर्प (नर)
    5:  ("Sarpa", "F"),    # मृगशिरा — सर्प (मादा)
    6:  ("Shwana", "F"),   # आर्द्रा — श्वान (मादा)
    7:  ("Marjara", "M"),  # पुनर्वसु — मार्जार (नर)
    8:  ("Mesha", "M"),    # पुष्य — मेष (नर)
    9:  ("Marjara", "F"),  # आश्लेषा — मार्जार (मादा)
    10: ("Mushaka", "M"),  # मघा — मूषक (नर)
    11: ("Mushaka", "F"),  # पूर्वाफाल्गुनी — मूषक (मादा)
    12: ("Gau", "M"),      # उत्तराफाल्गुनी — गो (नर)
    13: ("Mahisha", "F"),  # हस्त — महिष (मादा)
    14: ("Vyaghra", "F"),  # चित्रा — व्याघ्र (मादा)
    15: ("Ashwa", "F"),    # स्वाती — अश्व (मादा)
    16: ("Vyaghra", "M"),  # विशाखा — व्याघ्र (नर)
    17: ("Mriga", "M"),    # अनुराधा — मृग (नर)
    18: ("Mriga", "F"),    # ज्येष्ठा — मृग (मादा)
    19: ("Shwana", "M"),   # मूल — श्वान (नर)
    20: ("Vanara", "M"),   # पूर्वाषाढा — वानर (नर)
    21: ("Vanara", "F"),   # उत्तराषाढा — वानर (मादा)
    22: ("Nakula", "M"),   # श्रवण — नकुल (नर)   # Note: some texts: Ashwa
    23: ("Simha", "F"),    # धनिष्ठा — सिंह (मादा)
    24: ("Ashwa", "F"),    # शतभिषा — अश्व (मादा)   # some texts: Nakula
    25: ("Simha", "M"),    # पूर्वाभाद्रपद — सिंह (नर)
    26: ("Gau", "F"),      # उत्तराभाद्रपद — गो (मादा)
    27: ("Gaja", "M"),     # रेवती — गज (नर)
}
YONI_NEPALI = {
    "Ashwa": "अश्व", "Gaja": "गज", "Mesha": "मेष", "Sarpa": "सर्प",
    "Shwana": "श्वान", "Marjara": "मार्जार", "Mushaka": "मूषक",
    "Gau": "गो", "Mahisha": "महिष", "Vyaghra": "व्याघ्र",
    "Mriga": "मृग", "Vanara": "वानर", "Nakula": "नकुल", "Simha": "सिंह",
}

# Yoni compatibility score table [groom_yoni][bride_yoni]
# Same = 4, Friendly = 3, Neutral = 2, Enemy = 0
_YONI_ENEMY_PAIRS = {
    frozenset(["Ashwa", "Mahisha"]),
    frozenset(["Ashwa", "Mushaka"]),
    frozenset(["Mesha", "Sarpa"]),
    frozenset(["Mesha", "Mushaka"]),
    frozenset(["Sarpa", "Marjara"]),
    frozenset(["Sarpa", "Mriga"]),
    frozenset(["Shwana", "Vanara"]),
    frozenset(["Shwana", "Mriga"]),
    frozenset(["Marjara", "Mushaka"]),
    frozenset(["Mushaka", "Mahisha"]),
    frozenset(["Gau", "Vyaghra"]),
    frozenset(["Gau", "Simha"]),
    frozenset(["Mahisha", "Simha"]),
    frozenset(["Vanara", "Gaja"]),
    frozenset(["Mriga", "Simha"]),
    frozenset(["Nakula", "Mriga"]),   # नकुल-मृग शत्रु
}

def _yoni_score(groom_yoni: str, bride_yoni: str) -> float:
    if groom_yoni == bride_yoni:
        return 4
    if frozenset([groom_yoni, bride_yoni]) in _YONI_ENEMY_PAIRS:
        return 0
    return 2   # neutral

# 5. ग्रह प्राकृतिक सम्बन्ध (Natural Planet Relationships)
# F = Friend, N = Neutral, E = Enemy
# BPHS standard natural friendships
PLANET_NATURAL_RELATION = {
    # planet: {planet: relation}
    "Sun":     {"Sun": "F", "Moon": "F", "Mars": "F", "Mercury": "N",
                "Jupiter": "F", "Venus": "E", "Saturn": "E", "Rahu": "E", "Ketu": "E"},
    "Moon":    {"Sun": "F", "Moon": "F", "Mars": "N", "Mercury": "F",
                "Jupiter": "F", "Venus": "N", "Saturn": "N", "Rahu": "E", "Ketu": "E"},
    "Mars":    {"Sun": "F", "Moon": "F", "Mars": "F", "Mercury": "E",
                "Jupiter": "F", "Venus": "N", "Saturn": "N", "Rahu": "N", "Ketu": "N"},
    "Mercury": {"Sun": "F", "Moon": "N", "Mars": "N", "Mercury": "F",
                "Jupiter": "N", "Venus": "F", "Saturn": "F", "Rahu": "N", "Ketu": "N"},
    "Jupiter": {"Sun": "F", "Moon": "F", "Mars": "F", "Mercury": "E",
                "Jupiter": "F", "Venus": "E", "Saturn": "N", "Rahu": "E", "Ketu": "E"},
    "Venus":   {"Sun": "E", "Moon": "N", "Mars": "N", "Mercury": "F",
                "Jupiter": "N", "Venus": "F", "Saturn": "F", "Rahu": "N", "Ketu": "N"},
    "Saturn":  {"Sun": "E", "Moon": "E", "Mars": "E", "Mercury": "F",
                "Jupiter": "N", "Venus": "F", "Saturn": "F", "Rahu": "F", "Ketu": "N"},
    "Rahu":    {"Sun": "E", "Moon": "E", "Mars": "N", "Mercury": "F",
                "Jupiter": "E", "Venus": "F", "Saturn": "F", "Rahu": "F", "Ketu": "N"},
    "Ketu":    {"Sun": "N", "Moon": "N", "Mars": "F", "Mercury": "N",
                "Jupiter": "F", "Venus": "N", "Saturn": "N", "Rahu": "N", "Ketu": "F"},
}

# Graha Maitri score matrix based on combined relationship of both lords
# key: (groom_lord_relation_to_bride, bride_lord_relation_to_groom) → score
GRAH_MAITRI_SCORE = {
    ("F", "F"): 5,    # उभय मित्र
    ("F", "N"): 4,    # एक मित्र, एक सम
    ("N", "F"): 4,
    ("N", "N"): 3,    # उभय सम
    ("F", "E"): 2,    # एक मित्र, एक शत्रु
    ("E", "F"): 2,
    ("N", "E"): 1,    # एक सम, एक शत्रु
    ("E", "N"): 1,
    ("E", "E"): 0,    # उभय शत्रु
}
PLANET_NEPALI = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु"
}

# 6. राशि स्वामी  (Sign Lords)
RASHI_LORD = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}

# 7. नक्षत्र → गण  (Nakshatra → Gana)
NAKSHATRA_GANA = {
    1: "Deva",     # अश्विनी
    2: "Manava",   # भरणी
    3: "Rakshasa", # कृत्तिका
    4: "Manava",   # रोहिणी
    5: "Deva",     # मृगशिरा
    6: "Manava",   # आर्द्रा   (some: Rakshasa — here BPHS)
    7: "Deva",     # पुनर्वसु
    8: "Deva",     # पुष्य
    9: "Rakshasa", # आश्लेषा
    10: "Rakshasa", # मघा  (BPHS = Rakshasa; avakahada_chakra table सँग मेल)
    11: "Manava",  # पूर्वाफाल्गुनी
    12: "Manava",  # उत्तराफाल्गुनी
    13: "Deva",    # हस्त
    14: "Rakshasa",# चित्रा
    15: "Deva",    # स्वाती
    16: "Rakshasa",# विशाखा
    17: "Deva",    # अनुराधा
    18: "Rakshasa",# ज्येष्ठा
    19: "Rakshasa",# मूल
    20: "Manava",  # पूर्वाषाढा
    21: "Manava",  # उत्तराषाढा
    22: "Deva",    # श्रवण
    23: "Rakshasa",# धनिष्ठा
    24: "Rakshasa",# शतभिषा
    25: "Manava",  # पूर्वाभाद्रपद
    26: "Manava",  # उत्तराभाद्रपद
    27: "Deva",    # रेवती
}
GANA_NEPALI = {"Deva": "देव", "Manava": "मानव", "Rakshasa": "राक्षस"}

# Gana score matrix [groom_gana][bride_gana]
GANA_SCORE_MATRIX = {
    "Deva":     {"Deva": 6, "Manava": 6, "Rakshasa": 1},
    "Manava":   {"Deva": 5, "Manava": 6, "Rakshasa": 0},
    "Rakshasa": {"Deva": 0, "Manava": 0, "Rakshasa": 6},
}

# 8. नक्षत्र → नाडी  (Nakshatra → Nadi)
NAKSHATRA_NADI = {}
_NADI_CYCLE = ["Adi", "Madhya", "Antya"]
for _i in range(1, 28):
    NAKSHATRA_NADI[_i] = _NADI_CYCLE[(_i - 1) % 3]
NADI_NEPALI = {"Adi": "आदि", "Madhya": "मध्य", "Antya": "अन्त्य"}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: extract Moon data from chart dict
# ─────────────────────────────────────────────────────────────────────────────

def _get_moon_data(chart: dict) -> tuple:
    """Returns (moon_sign_number 1-12, nakshatra_number 1-27, pada 1-4)"""
    for planet in chart.get("planets", []):
        name = planet.get("name", "")
        if name in ("Moon", "Chandra", "चन्द्र"):
            sign = int(planet.get("sign_number", 0) or 0)
            lon = float(planet.get("sidereal_longitude", 0.0) or 0.0)
            nak_idx = int(lon / (360.0 / 27.0)) % 27 + 1
            pada = int((lon % (360.0 / 27.0)) / (360.0 / 27.0 / 4)) + 1
            pada = max(1, min(4, pada))
            if not sign:
                sign = int((lon / 30.0) % 12) + 1
            return sign, nak_idx, pada
    return 0, 0, 0


# ─────────────────────────────────────────────────────────────────────────────
# 8 Kuta Calculators
# ─────────────────────────────────────────────────────────────────────────────

def calculate_varna(groom_sign: int, bride_sign: int) -> float:
    """
    वर्ण कूट — अधिकतम १ गुण
    वरको वर्ण वधूको वर्ण बराबर वा उच्च भए १ गुण, अन्यथा ०
    """
    g_varna = RASHI_VARNA.get(groom_sign, "Shudra")
    b_varna = RASHI_VARNA.get(bride_sign, "Shudra")
    return 1.0 if VARNA_RANK.get(g_varna, 1) >= VARNA_RANK.get(b_varna, 1) else 0.0


def get_varna_detail(groom_sign: int, bride_sign: int) -> dict:
    return {
        "boy": VARNA_NEPALI.get(RASHI_VARNA.get(groom_sign, "Shudra"), "शूद्र"),
        "girl": VARNA_NEPALI.get(RASHI_VARNA.get(bride_sign, "Shudra"), "शूद्र"),
    }


def calculate_vasya(groom_sign: int, bride_sign: int) -> float:
    """
    वश्य कूट — अधिकतम २ गुण
    वश्य वर्गीकरण तालिकाबाट compatibility matrix प्रयोग
    """
    gv = RASHI_VASHYA.get(groom_sign, "Manava")
    bv = RASHI_VASHYA.get(bride_sign, "Manava")
    return float(VASHYA_SCORE.get(gv, {}).get(bv, 0))


def get_vasya_detail(groom_sign: int, bride_sign: int) -> dict:
    gv = RASHI_VASHYA.get(groom_sign, "Manava")
    bv = RASHI_VASHYA.get(bride_sign, "Manava")
    score = VASHYA_SCORE.get(gv, {}).get(bv, 0)
    combined = "उत्तम" if score == 2 else ("साधारण" if score == 1 else "अनुपयुक्त")
    return {
        "boy": VASHYA_NEPALI.get(gv, gv),
        "girl": VASHYA_NEPALI.get(bv, bv),
        "combined": combined,
    }


def calculate_tara(groom_nakshatra: int, bride_nakshatra: int) -> float:
    """
    तारा कूट — अधिकतम ३ गुण
    27-नक्षत्र दूरी निकाल्ने, त्यसपछि ९ले भाग गर्ने
    दुवै दिशा शुभ = ३, एक शुभ = १.५, दुवै अशुभ = ०
    """
    # distance: 27-nakshatra inclusive count
    dist_gb = ((bride_nakshatra - groom_nakshatra) % 27) + 1   # groom → bride
    dist_bg = ((groom_nakshatra - bride_nakshatra) % 27) + 1   # bride → groom

    t_gb = dist_gb % 9
    t_bg = dist_bg % 9
    if t_gb == 0:
        t_gb = 9
    if t_bg == 0:
        t_bg = 9

    gb_good = t_gb in SHUBHA_TARAS
    bg_good = t_bg in SHUBHA_TARAS

    if gb_good and bg_good:
        return 3.0
    elif gb_good or bg_good:
        return 1.5
    return 0.0


def get_tara_detail(groom_nakshatra: int, bride_nakshatra: int) -> dict:
    dist_gb = ((bride_nakshatra - groom_nakshatra) % 27) + 1
    dist_bg = ((groom_nakshatra - bride_nakshatra) % 27) + 1
    t_gb = (dist_gb % 9) or 9
    t_bg = (dist_bg % 9) or 9

    gb_good = t_gb in SHUBHA_TARAS
    bg_good = t_bg in SHUBHA_TARAS

    if gb_good and bg_good:
        status = "अनुकूल"
    elif gb_good or bg_good:
        status = "मिश्रित"
    else:
        status = "अनुपयुक्त"

    return {
        "boy": f"{TARA_NAMES.get(t_gb, '-')} ({t_gb})",
        "girl": f"{TARA_NAMES.get(t_bg, '-')} ({t_bg})",
        "combined": status,
    }


def calculate_yoni(groom_nakshatra: int, bride_nakshatra: int) -> float:
    """
    योनि कूट — अधिकतम ४ गुण
    नक्षत्र → योनि → YONI_SCORE matrix
    """
    gy = NAKSHATRA_YONI.get(groom_nakshatra, ("Ashwa", "M"))[0]
    by = NAKSHATRA_YONI.get(bride_nakshatra, ("Ashwa", "F"))[0]
    return float(_yoni_score(gy, by))


def get_yoni_detail(groom_nakshatra: int, bride_nakshatra: int) -> dict:
    gy, _gs = NAKSHATRA_YONI.get(groom_nakshatra, ("Ashwa", "M"))
    by, _bs = NAKSHATRA_YONI.get(bride_nakshatra, ("Ashwa", "F"))
    score = _yoni_score(gy, by)
    status = "समान" if gy == by else ("सामान्य" if score == 2 else "शत्रु")
    return {
        "boy": YONI_NEPALI.get(gy, gy),
        "girl": YONI_NEPALI.get(by, by),
        "combined": status,
    }


def calculate_grah_maitri(groom_sign: int, bride_sign: int) -> float:
    """
    ग्रह मैत्री कूट — अधिकतम ५ गुण
    चन्द्र राशि स्वामी ग्रहको प्राकृतिक मित्रता सम्बन्धबाट score
    """
    g_lord = RASHI_LORD.get(groom_sign, "Jupiter")
    b_lord = RASHI_LORD.get(bride_sign, "Jupiter")

    # groom lord's relation to bride lord
    rel_gb = PLANET_NATURAL_RELATION.get(g_lord, {}).get(b_lord, "N")
    # bride lord's relation to groom lord
    rel_bg = PLANET_NATURAL_RELATION.get(b_lord, {}).get(g_lord, "N")

    return float(GRAH_MAITRI_SCORE.get((rel_gb, rel_bg), 3))


def get_grah_maitri_detail(groom_sign: int, bride_sign: int) -> dict:
    g_lord = RASHI_LORD.get(groom_sign, "Jupiter")
    b_lord = RASHI_LORD.get(bride_sign, "Jupiter")
    rel_gb = PLANET_NATURAL_RELATION.get(g_lord, {}).get(b_lord, "N")
    rel_bg = PLANET_NATURAL_RELATION.get(b_lord, {}).get(g_lord, "N")
    _rel_ne = {"F": "मित्र", "N": "सम", "E": "शत्रु"}
    return {
        "boy": f"{PLANET_NEPALI.get(g_lord, g_lord)} ({_rel_ne.get(rel_gb, '-')})",
        "girl": f"{PLANET_NEPALI.get(b_lord, b_lord)} ({_rel_ne.get(rel_bg, '-')})",
    }


def calculate_gana(groom_nakshatra: int, bride_nakshatra: int) -> float:
    """
    गण कूट — अधिकतम ६ गुण
    GANA_SCORE_MATRIX प्रयोग
    """
    gg = NAKSHATRA_GANA.get(groom_nakshatra, "Manava")
    bg = NAKSHATRA_GANA.get(bride_nakshatra, "Manava")
    return float(GANA_SCORE_MATRIX.get(gg, {}).get(bg, 0))


def get_gana_detail(groom_nakshatra: int, bride_nakshatra: int) -> dict:
    gg = NAKSHATRA_GANA.get(groom_nakshatra, "Manava")
    bg = NAKSHATRA_GANA.get(bride_nakshatra, "Manava")
    return {
        "boy": GANA_NEPALI.get(gg, gg),
        "girl": GANA_NEPALI.get(bg, bg),
    }


def calculate_bhakut(groom_sign: int, bride_sign: int) -> float:
    """
    भकूट कूट — अधिकतम ७ गुण
    चन्द्र राशिहरूको सम्बन्ध pair: शुभ सम्बन्धमा ७ गुण
    महादोष (२/१२, ६/८) = ० गुण
    """
    count_bg = (bride_sign - groom_sign) % 12 + 1    # groom → bride
    count_gb = (groom_sign - bride_sign) % 12 + 1    # bride → groom
    pair = tuple(sorted([count_bg, count_gb]))

    # महादोष
    if pair in {(2, 12), (6, 8)}:
        return 0.0
    # उत्तम सम्बन्ध
    if pair in {(1, 1), (7, 7), (1, 7)}:
        return 7.0
    # ३/११ — लाभ
    if pair == (3, 11):
        return 7.0
    # ५/९ — त्रिकोण
    if pair == (5, 9):
        return 7.0
    # ४/१० — केन्द्र (शुभ केन्द्र सम्बन्ध — BPHS traditional texts)
    if pair == (4, 10):
        return 7.0
    return 0.0


def get_bhakut_detail(groom_sign: int, bride_sign: int) -> dict:
    count_bg = (bride_sign - groom_sign) % 12 + 1
    count_gb = (groom_sign - bride_sign) % 12 + 1
    pair = tuple(sorted([count_bg, count_gb]))

    pair_labels = {
        (1, 1): "१/१ — समान राशि — उत्तम",
        (1, 7): "१/७ — सप्तम सम्बन्ध — उत्तम",
        (7, 7): "७/७ — परस्पर सप्तम — उत्तम",
        (3, 11): "३/११ — लाभ सम्बन्ध — शुभ",
        (5, 9): "५/९ — त्रिकोण सम्बन्ध — शुभ",
        (4, 10): "४/१० — केन्द्र सम्बन्ध — मध्यम",
        (6, 8): "६/८ — षडाष्टक — भकूट दोष",
        (2, 12): "२/१२ — द्वादश — भकूट दोष",
    }
    return {
        "boy": f"राशि {groom_sign}",
        "girl": f"राशि {bride_sign}",
        "combined": pair_labels.get(pair, f"{count_bg}/{count_gb} — अन्य"),
    }


def calculate_nadi(groom_nakshatra: int, bride_nakshatra: int) -> float:
    """
    नाडी कूट — अधिकतम ८ गुण
    फरक नाडी = ८ गुण; समान नाडी = ० (नाडी दोष)
    """
    gn = NAKSHATRA_NADI.get(groom_nakshatra, "Adi")
    bn = NAKSHATRA_NADI.get(bride_nakshatra, "Adi")
    return 0.0 if gn == bn else 8.0


def get_nadi_detail(groom_nakshatra: int, bride_nakshatra: int) -> dict:
    gn = NAKSHATRA_NADI.get(groom_nakshatra, "Adi")
    bn = NAKSHATRA_NADI.get(bride_nakshatra, "Adi")
    return {
        "boy": NADI_NEPALI.get(gn, gn),
        "girl": NADI_NEPALI.get(bn, bn),
        "combined": "नाडी दोष — समान नाडी" if gn == bn else "अनुकूल",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main Ashtakoota Engine
# ─────────────────────────────────────────────────────────────────────────────

def calculate_ashtakoot(boy_chart: dict, girl_chart: dict) -> dict:
    """
    अष्टकूट गुण मिलान — सम्पूर्ण 36 गुण गणना
    Input: Swiss Ephemeris द्वारा गणित boy_chart र girl_chart dict
    Output: structured result dict
    """
    # Extract Moon data
    boy_moon_sign, boy_nakshatra, boy_pada = _get_moon_data(boy_chart)
    girl_moon_sign, girl_nakshatra, girl_pada = _get_moon_data(girl_chart)

    # Fallback to lagna if Moon not found
    if not boy_moon_sign:
        boy_moon_sign = boy_chart.get("lagna", {}).get("sign_number", 1)
        boy_nakshatra = 1
        boy_pada = 1
    if not girl_moon_sign:
        girl_moon_sign = girl_chart.get("lagna", {}).get("sign_number", 1)
        girl_nakshatra = 1
        girl_pada = 1

    # Calculate all 8 kootas
    varna      = calculate_varna(boy_moon_sign, girl_moon_sign)
    vasya      = calculate_vasya(boy_moon_sign, girl_moon_sign)
    tara       = calculate_tara(boy_nakshatra, girl_nakshatra)
    yoni       = calculate_yoni(boy_nakshatra, girl_nakshatra)
    grah_maitri = calculate_grah_maitri(boy_moon_sign, girl_moon_sign)
    gana       = calculate_gana(boy_nakshatra, girl_nakshatra)
    bhakut     = calculate_bhakut(boy_moon_sign, girl_moon_sign)
    nadi       = calculate_nadi(boy_nakshatra, girl_nakshatra)

    total_score = varna + vasya + tara + yoni + grah_maitri + gana + bhakut + nadi
    max_score = 36.0

    # Compatibility label
    if total_score >= 32:
        compatibility = "अत्यन्त उत्तम (Excellent)"
        compat_en = "Excellent"
    elif total_score >= 26:
        compatibility = "धेरै राम्रो (Very Good)"
        compat_en = "Very Good"
    elif total_score >= 22:
        compatibility = "राम्रो (Good)"
        compat_en = "Good"
    elif total_score >= 18:
        compatibility = "स्वीकार्य (Average)"
        compat_en = "Average"
    else:
        compatibility = "कमजोर (Weak)"
        compat_en = "Weak"

    # Dosha flags
    nadi_dosha = (nadi == 0.0)
    bhakut_dosha = (bhakut == 0.0) and (
        tuple(sorted([(girl_moon_sign - boy_moon_sign) % 12 + 1,
                      (boy_moon_sign - girl_moon_sign) % 12 + 1])) in {(2, 12), (6, 8)}
    )
    gana_conflict = (gana == 0.0)
    yoni_conflict_level = (
        "शत्रु" if yoni == 0.0 else
        ("सामान्य" if yoni == 2.0 else "अनुकूल")
    )
    tara_conflict = (tara == 0.0)
    varna_conflict = (varna == 0.0)

    # Bhakut mahadosha note
    bhakut_mahadosh_note = ""
    if bhakut_dosha:
        bhakut_mahadosh_note = (
            f"वरको चन्द्र राशि {boy_moon_sign} र वधूको चन्द्र राशि {girl_moon_sign} — "
            f"{get_bhakut_detail(boy_moon_sign, girl_moon_sign).get('combined', '')}"
        )

    return {
        # Individual scores
        "varna":        varna,
        "vasya":        vasya,
        "tara":         tara,
        "yoni":         yoni,
        "grah_maitri":  grah_maitri,
        "gana":         gana,
        "bhakut":       bhakut,
        "nadi":         nadi,

        # Totals
        "total_score":  total_score,
        "max_score":    max_score,

        # Labels
        "compatibility":    compatibility,
        "compatibility_en": compat_en,

        # Moon positions
        "boy_moon_sign":     boy_moon_sign,
        "girl_moon_sign":    girl_moon_sign,
        "boy_nakshatra":     boy_nakshatra,
        "girl_nakshatra":    girl_nakshatra,
        "boy_pada":          boy_pada,
        "girl_pada":         girl_pada,

        # Dosha flags
        "nadi_dosha":        nadi_dosha,
        "bhakut_dosha":      bhakut_dosha,
        "bhakut_mahadosh":   bhakut_dosha,
        "bhakut_mahadosh_note": bhakut_mahadosh_note,
        "gana_conflict":     gana_conflict,
        "yoni_conflict":     yoni_conflict_level,
        "tara_conflict":     tara_conflict,
        "varna_conflict":    varna_conflict,

        # Detail dicts for UI table
        "details": {
            "varna_detail":      get_varna_detail(boy_moon_sign, girl_moon_sign),
            "vasya_detail":      get_vasya_detail(boy_moon_sign, girl_moon_sign),
            "tara_detail":       get_tara_detail(boy_nakshatra, girl_nakshatra),
            "yoni_detail":       get_yoni_detail(boy_nakshatra, girl_nakshatra),
            "grah_maitri_detail": get_grah_maitri_detail(boy_moon_sign, girl_moon_sign),
            "gana_detail":       get_gana_detail(boy_nakshatra, girl_nakshatra),
            "bhakut_detail":     get_bhakut_detail(boy_moon_sign, girl_moon_sign),
            "nadi_detail":       get_nadi_detail(boy_nakshatra, girl_nakshatra),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Mangal Dosha (D1 Lagna basis)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_mangal_dosh(chart: dict, gender: str = "male") -> dict:
    """
    मंगल दोष — D1 लग्न कुण्डलीबाट
    मंगल १, ४, ७, ८, १२ भावमा भएमा मंगल दोष
    """
    mars_house = None
    mars_sign = None

    for planet in chart.get("planets", []):
        name = planet.get("name", "")
        if name in ("Mars", "Mangal", "मंगल"):
            mars_house = planet.get("house")
            mars_sign = planet.get("sign_number")
            break

    if not mars_house:
        return {
            "has_mangal_dosh": False,
            "dosh_houses": [],
            "mars_house": None,
            "cancellation_possible": False,
            "severity": "none",
        }

    dosh_houses_check = {1, 4, 7, 8, 12}
    has_dosh = mars_house in dosh_houses_check

    # Cancellation rules (primary)
    mars_own_signs = {1, 8}      # मेष, वृश्चिक
    mars_exalted = 10             # मकर
    cancellation = bool(mars_sign and (mars_sign in mars_own_signs or mars_sign == mars_exalted))

    return {
        "has_mangal_dosh": has_dosh and not cancellation,
        "dosh_houses": [mars_house] if has_dosh else [],
        "mars_house": mars_house,
        "cancellation_possible": cancellation,
        "severity": ("high" if (has_dosh and not cancellation) else
                     "cancelled" if (has_dosh and cancellation) else "none"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main Compatibility Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def _extract_planets_map(chart: dict) -> dict:
    result = {}
    for p in chart.get("planets", []):
        name = p.get("name")
        long_val = p.get("sidereal_longitude")
        if long_val is None:
            long_val = p.get("longitude")
        if name and long_val is not None:
            try:
                result[name] = float(long_val)
            except (ValueError, TypeError):
                pass
    return result


def _calculate_synastry(boy_chart: dict, girl_chart: dict) -> list:
    boy_planets = _extract_planets_map(boy_chart)
    girl_planets = _extract_planets_map(girl_chart)
    aspects = []

    # 1. Sun - Moon (Soul & Emotional connection)
    b_sun, g_moon = boy_planets.get("Sun"), girl_planets.get("Moon")
    if b_sun is not None and g_moon is not None:
        diff = abs(b_sun - g_moon) % 360
        shortest = min(diff, 360 - diff)
        if shortest <= 10:
            aspects.append({"type": "conjunction", "pair": "वर सूर्य - वधू चन्द्र", "nepali": "आत्मिक र भावनात्मक गहिरो सम्बन्ध", "nature": "excellent"})
        elif 110 <= shortest <= 130:
            aspects.append({"type": "trine", "pair": "वर सूर्य - वधू चन्द्र (त्रिकोण)", "nepali": "उत्तम तालमेल र परस्पर सम्मान", "nature": "good"})

    # 2. Venus - Mars (Attraction & Romance)
    b_mars, g_venus = boy_planets.get("Mars"), girl_planets.get("Venus")
    if b_mars is not None and g_venus is not None:
        diff = abs(b_mars - g_venus) % 360
        shortest = min(diff, 360 - diff)
        if shortest <= 10 or (50 <= shortest <= 70) or (110 <= shortest <= 130):
            aspects.append({"type": "harmonious", "pair": "वर मंगल - वधू शुक्र", "nepali": "आकर्षण र दाम्पत्य सौहार्दता", "nature": "good"})

    # 3. Jupiter - Moon (Blessings & Prosperity)
    b_jup, g_moon = boy_planets.get("Jupiter"), girl_planets.get("Moon")
    if b_jup is not None and g_moon is not None:
        diff = abs(b_jup - g_moon) % 360
        shortest = min(diff, 360 - diff)
        if shortest <= 10 or (110 <= shortest <= 130):
            aspects.append({"type": "gajakesari_harmony", "pair": "वर गुरु - वधू चन्द्र", "nepali": "शुभता, सुरक्षा र वंशवृद्धि कारक", "nature": "excellent"})

    return aspects


def calculate_compatibility(boy_chart: dict, girl_chart: dict) -> dict:
    """
    सम्पूर्ण विवाह मिलान: अष्टकूट + मंगल दोष + Radar Chart + Synastry
    """
    ashtakoot = calculate_ashtakoot(boy_chart, girl_chart)
    boy_mangal = calculate_mangal_dosh(boy_chart, "male")
    girl_mangal = calculate_mangal_dosh(girl_chart, "female")

    mangal_dosh_note = ""
    if boy_mangal["has_mangal_dosh"] and girl_mangal["has_mangal_dosh"]:
        mangal_dosh_note = "दुवैमा मंगल दोष — परस्पर निरसन हुन्छ।"
    elif boy_mangal["has_mangal_dosh"] or girl_mangal["has_mangal_dosh"]:
        mangal_dosh_note = "एक पक्षमा मंगल दोष — मंगल शान्ति विचार गर्नुहोस्।"

    # ध्यान: अष्टकूट score मात्रले final decision होइन
    # आर्किटेक्चर अनुसार अन्य विश्लेषण (सप्तमेश, नवांश, दशा) पनि आवश्यक
    overall_compatible = True
    if ashtakoot["total_score"] < 18:
        overall_compatible = False

    if ashtakoot["total_score"] >= 26:
        recommendation = "✅ विवाहका लागि अनुकूल — गुण मिलान राम्रो छ।"
    elif ashtakoot["total_score"] >= 18:
        recommendation = "⚠️ स्वीकार्य मिलान — अन्य ज्योतिषीय विचार आवश्यक।"
    else:
        recommendation = "❌ गुण मिलान कमजोर — विशेष ज्योतिषीय परामर्श लिनुहोस्।"

    # 8-Koota Radar Chart data
    radar_chart = [
        {"koota": "Varna", "nepali": "वर्ण", "score": ashtakoot["varna"], "max": 1, "pct": round(ashtakoot["varna"] / 1.0 * 100, 1)},
        {"koota": "Vashya", "nepali": "वश्य", "score": ashtakoot["vasya"], "max": 2, "pct": round(ashtakoot["vasya"] / 2.0 * 100, 1)},
        {"koota": "Tara", "nepali": "तारा", "score": ashtakoot["tara"], "max": 3, "pct": round(ashtakoot["tara"] / 3.0 * 100, 1)},
        {"koota": "Yoni", "nepali": "योनि", "score": ashtakoot["yoni"], "max": 4, "pct": round(ashtakoot["yoni"] / 4.0 * 100, 1)},
        {"koota": "Graha Maitri", "nepali": "ग्रह मैत्री", "score": ashtakoot["grah_maitri"], "max": 5, "pct": round(ashtakoot["grah_maitri"] / 5.0 * 100, 1)},
        {"koota": "Gana", "nepali": "गण", "score": ashtakoot["gana"], "max": 6, "pct": round(ashtakoot["gana"] / 6.0 * 100, 1)},
        {"koota": "Bhakoot", "nepali": "भकूट", "score": ashtakoot["bhakut"], "max": 7, "pct": round(ashtakoot["bhakut"] / 7.0 * 100, 1)},
        {"koota": "Nadi", "nepali": "नाडी", "score": ashtakoot["nadi"], "max": 8, "pct": round(ashtakoot["nadi"] / 8.0 * 100, 1)},
    ]

    synastry = _calculate_synastry(boy_chart, girl_chart)

    # Key doshas and remedies
    dosha_alerts = []
    if ashtakoot.get("nadi_dosha"):
        dosha_alerts.append({
            "dosha": "नाडी दोष",
            "severity": "उच्च",
            "remedy": "महामृत्युञ्जय जप, स्वर्ण दान, वा रुद्राभिषेक पूजा उत्तम मानिन्छ।"
        })
    if ashtakoot.get("bhakut_dosha"):
        dosha_alerts.append({
            "dosha": "भकूट दोष (षडाष्टक/द्विर्द्वादश/नवपञ्चम)",
            "severity": "मध्यम",
            "remedy": "राशी स्वामीको मैत्री भएमा वा पूजा अनुष्ठानले दोष शान्ति हुन्छ।"
        })
    if boy_mangal["has_mangal_dosh"] != girl_mangal["has_mangal_dosh"]:
        dosha_alerts.append({
            "dosha": "एकपक्षीय मंगल दोष",
            "severity": "मध्यम",
            "remedy": "कुम्भ विवाह, मंगल चण्डिका स्तोत्र पाठ वा मंगल शान्ति गर्न सकिन्छ।"
        })

    return {
        "ashtakoot": ashtakoot,
        "boy_mangal_dosh": boy_mangal,
        "girl_mangal_dosh": girl_mangal,
        "mangal_dosh_note": mangal_dosh_note,
        "overall_compatible": overall_compatible,
        "recommendation": recommendation,
        "radar_chart": radar_chart,
        "synastry": synastry,
        "dosha_alerts": dosha_alerts,
    }
