import unicodedata
from pathlib import Path
from typing import Dict, Any


# Animal-based varga grouping by first letter of name akshara
# (base consonant/vowel group → varga, shatru_varga)
AKSHARA_VARGA_MAP = [
    # Vowels: अ आ इ ई उ ऊ ऋ ऌ ए ऐ ओ औ
    ({"अ","आ","इ","ई","उ","ऊ","ऋ","ऌ","ए","ऐ","ओ","औ","ऑ","ऒ","ऍ","ऎ"}, "गरुण", "सर्प"),
    # क ख ग घ ङ (and क्ष)
    ({"क","ख","ग","घ","ङ","क्ष"}, "मार्जार", "मुषक"),
    # च छ ज झ ञ (and ज्ञ)
    ({"च","छ","ज","झ","ञ","ज्ञ"}, "सिंह", "मृग"),
    # ट ठ ड ढ ण
    ({"ट","ठ","ड","ढ","ण"}, "श्वान", "मेष"),
    # त थ द ध न (and त्र)
    ({"त","थ","द","ध","न","त्र"}, "सर्प", "गरुण"),
    # प फ ब भ म
    ({"प","फ","ब","भ","म"}, "मूषक", "मार्जार"),
    # य र ल व
    ({"य","र","ल","व"}, "मृग", "सिंह"),
    # श ष स ह (and श्र श्री ॉं)
    ({"श","ष","स","ह","श्र","श्री","ॉं"}, "मेष", "श्वान"),
]

# Devanagari dependent vowel marks to strip when finding base letter
_DEVA_MATRAS = frozenset(
    "ािीुूृॄॅॆेैॉॊोौ्ंःँऀ॒॓॔"
)


# Normalize rashi names from table spellings to standard Nepali
RASHI_NORMALIZE = {
    "मेष": "मेष", "बृष": "बृष", "बृश": "बृष", "मिथुन": "मिथुन",
    "कर्क": "कर्कट", "कर्कट": "कर्कट", "सिंह": "सिंह",
    "कन्या": "कन्या", "तुला": "तुला",
    "वृश्चिक": "वृश्चिक", "वृशचिक": "वृश्चिक",
    "बृष्चिक": "वृश्चिक", "धनु": "धनु", "मकर": "मकर",
    "कुम्भ": "कुम्भ", "मीन": "मीन",
}

RASHI_LORD_NORMALIZE = {
    "सूर्य": "सूर्य", "सूर्ये": "सूर्य", "चन्द्र": "चन्द्र", "चन्द्रमा": "चन्द्र",
    "मंगल": "मंगल", "मङ्गल": "मंगल", "बुध": "बुध",
    "गुरु": "गुरु", "बृहस्पति": "गुरु", "शुक्र": "शुक्र",
    "शनि": "शनि", "शनिश्चर": "शनि",
}

NADI_NORMALIZE = {
    "आदि": "आदि", "आध्य": "आदि", "आद्य": "आदि",
    "मध्य": "मध्य",
    "अन्त्य": "अन्त्य",
}

_EMBEDDED_TABLE_TEXT = """चरण | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4 | 1 | 2 | 3 | 4
नामाक्षर | चु | चे | चो | ला | ली | लु | ले  | लो | अ | इ | उ | ए | ओ | वा | वी | वु | वे | वो | का | की | कु | घ | ङ | छ | के | को | हा | ही | हु | हे | हो | डा | डी | डु | डे | डो | मा | मी | मू | मे | मो | टा | टि | टु | टे | टो | पा | पी | पू | ष | ण | ठ | पे | पो | रा | री | रु | रे | रो | ता | ती | तु | ते | तो | ना | नी | नू | ने | नो | या | यी | यू | ये | यो | भा | भी | भू | धा | फा | ढा | भे | भो | जा | जी | जु | जे | जो | ख | खी | खु | खे | खो | गा | गी | गु | गे | गो | सा | सी | सू | से | सो | दा | दी | दू | थ | झ | ञ | दे | दो | चा | ची
नक्षत्र | अश्विनी |  |  |  | भरणी |  |  |  | कृतिका |  |  |  | रोहिणी |  |  |  | मृगशिरा |  |  |  | आर्दा |  |  |  | पुनर्वशु |  |  |  | तिष्य |  |  |  | अश्लेषा |  |  |  | मघा |  |  |  | पूर्व फाल्गुनी |  |  |  | उत्तर फाल्गुनी |  |  |  | हस्ता |  |  |  | चित्रा |  |  |  | स्वाती |  |  |  | विशाषा |  |  |  | अनुराधा |  |  |  | ज्येष्ठा |  |  |  | मूल |  |  |  | पूर्वाषाढा |  |  |  | उत्तरषाढा |  |  |  | अभिजित |  |  |  | श्रवण |  |  |  | धनिष्ठा |  |  |  | शतभिषा |  |  |  | पूर्व भाद्रपद |  |  |  | उत्तर भाद्रपद |  |  |  | रेवती |  |  | 
राशी | मेष |  |  |  |  |  |  |  |  | बृष |  |  |  |  |  |  |  |  | मिथुन |  |  |  |  |  |  |  |  | कर्कट |  |  |  |  |  |  |  |  | सिंह |  |  |  |  |  |  |  |  | कन्या |  |  |  |  |  |  |  |  | तुला |  |  |  |  |  |  |  |  | बृष्चिक |  |  |  |  |  |  |  |  | धनु |  |  |  |  |  |  |  |  | मकर |  |  |  |  |  |  |  |  |  |  |  |  | कुम्भ |  |  |  |  |  |  |  |  | मीन |  |  |  |  |  |  |  | 
राश स्वामी | मंगल |  |  |  |  |  |  |  |  | शुक्र |  |  |  |  |  |  |  |  | बुध |  |  |  |  |  |  |  |  | चन्द्र |  |  |  |  |  |  |  |  | सूर्य |  |  |  |  |  |  |  |  | बुध |  |  |  |  |  |  |  |  | शुक्र |  |  |  |  |  |  |  |  | मंगल |  |  |  |  |  |  |  |  | गुरु |  |  |  |  |  |  |  |  | शनि |  |  |  |  |  |  |  |  |  |  |  |  | शनि |  |  |  |  |  |  |  |  | गुरु |  |  |  |  |  |  |  | 
वर्ण | क्षत्री |  |  |  |  |  |  |  |  | वैश्य |  |  |  |  |  |  |  |  | शूद्र |  |  |  |  |  |  |  |  | विप्र |  |  |  |  |  |  |  |  | क्षत्री |  |  |  |  |  |  |  |  | वैश्य |  |  |  |  |  |  |  |  | शूद्र |  |  |  |  |  |  |  |  | विप्र |  |  |  |  |  |  |  |  | क्षत्री |  |  |  |  |  |  |  |  | वैश्य |  |  |  |  |  |  |  |  |  |  |  |  | शूद्र |  |  |  |  |  |  |  |  | विप्र |  |  |  |  |  |  |  | 
वश्य | चतुष्पद |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | द्विपद |  |  |  |  |  |  |  |  | जलचर |  |  |  |  |  |  |  |  | चतुष्पद |  |  |  |  |  |  |  |  | द्विपद |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | किट |  |  |  |  |  |  |  |  | मनुष्य |  |  |  |  |  |  |  |  | चतुष्पद |  |  |  |  |  |  |  |  |  |  |  |  | द्विपद |  |  |  |  |  |  |  |  | जलचर |  |  |  |  |  |  |  | 
योनि | अश्व |  |  |  | गज |  |  |  | अज |  |  |  | सर्प |  |  |  | सर्प |  |  |  | श्वान |  |  |  | मार्जर |  |  |  | अज |  |  |  | मार्जर |  |  |  | मुषक |  |  |  | मुषक |  |  |  | गौ |  |  |  | महिष |  |  |  | ब्याघ्र |  |  |  | महिष |  |  |  | ब्याघ्र |  |  |  | मृग |  |  |  | मृग |  |  |  | श्वान |  |  |  | वानर |  |  |  | नकुल |  |  |  | नकुल |  | अज |  | वानर |  |  |  | सिंह |  |  |  | अश्व |  |  |  | सिंह |  |  |  | गौ |  |  |  | गज |  |  | 
वैरयोनि | महिष |  |  |  | सिंह |  |  |  | वानर |  |  |  | नकुल |  |  |  | नकुल |  |  |  | मृग |  |  |  | मुषक |  |  |  | वानर |  |  |  | मुषक |  |  |  | मार्जर |  |  |  | मार्जर |  |  |  | ब्याघ्र |  |  |  | अश्व |  |  |  | गौ |  |  |  | अश्व |  |  |  | गौ |  |  |  | श्वान |  |  |  | श्वान |  |  |  | मृग |  |  |  | अज |  |  |  | सर्प |  |  |  | अज |  | गज |  | अज |  |  |  | गज |  |  |  | महिष |  |  |  | गज |  |  |  | ब्याघ्र |  |  |  | सिंह |  |  | 
गण | देव |  |  |  | नर |  |  |  | राक्षस |  |  |  | नर |  |  |  | देव |  |  |  | नर |  |  |  | देव |  |  |  | देव |  |  |  | राक्षस |  |  |  | राक्षस |  |  |  | नर |  |  |  | नर |  |  |  | देव |  |  |  | राक्षस |  |  |  | देव |  |  |  | राक्षस |  |  |  | देव |  |  |  | राक्षस |  |  |  | राक्षस |  |  |  | नर |  |  |  | नर |  |  |  | नर |  | देव |  | देव |  |  |  | राक्षस |  |  |  | राक्षस |  |  |  | नर |  |  |  | नर |  |  |  | देव |  |  | 
नाडी | आद्य |  |  |  | मध्य |  |  |  | अन्त्य |  |  |  | अन्त्य |  |  |  | मध्य |  |  |  | आद्य |  |  |  | आद्य |  |  |  | मध्य |  |  |  | अन्त्य |  |  |  | अन्त्य |  |  |  | मध्य |  |  |  | आध्य |  |  |  | आध्य |  |  |  | मध्य |  |  |  | अन्त्य |  |  |  | अन्त्य |  |  |  | मध्य |  |  |  | आध्य |  |  |  | आध्य |  |  |  | मध्य |  |  |  | अन्त्य |  |  |  | अन्त्य |  | अन्त्य |  | अन्त्य |  |  |  | मध्य |  |  |  | आध्य |  |  |  | आध्य |  |  |  | मध्य |  |  |  | अन्त्य |  |  | 
आसन | अश्व |  |  |  | प्रेत |  |  |  | अग्नी कुण्ड |  |  |  | गौ |  |  |  | मृग |  |  |  | भुजंग |  |  |  | कमल |  |  |  | कलश |  |  |  | काक |  |  |  | महिष |  |  |  | शिला |  |  |  | शिला |  |  |  | गज |  |  |  | मयूर |  |  |  | दोल |  |  |  | अज |  |  |  | हंश |  |  |  | कच्छप |  |  |  | मुल |  |  |  | शयन |  |  |  | शयन |  |  |  | शयन |  | नर |  | नर |  |  |  | आढक |  |  |  | बृष |  |  |  | भद्रपीठ |  |  |  | भद्रपीठ |  |  |  | चक्र |  |  | 
"""

_CACHED_TABLE: Dict[str, list[str]] | None = None


def _parse_table_text(text: str) -> Dict[str, list[str]]:
    rows: Dict[str, list[str]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("===") or line.startswith("अवकहडा चक्र") or line.startswith("चरण"):
            continue

        parts = [part.strip() for part in line.split("|")]
        if not parts:
            continue

        key = parts[0]
        values = parts[1:]
        if not key:
            continue
        rows[key] = values
    return rows


def _load_table() -> Dict[str, list[str]]:
    global _CACHED_TABLE
    if _CACHED_TABLE:
        return _CACHED_TABLE

    import sys
    candidate_paths = [
        Path(__file__).resolve().parents[1] / "formatted_extracted.txt",
        Path(__file__).resolve().parents[2] / "formatted_extracted.txt",
        Path(__file__).resolve().parent / "formatted_extracted.txt",
        Path.cwd() / "backend" / "formatted_extracted.txt",
        Path.cwd() / "formatted_extracted.txt",
    ]
    if hasattr(sys, "_MEIPASS"):
        candidate_paths.insert(0, Path(sys._MEIPASS) / "formatted_extracted.txt")
        candidate_paths.insert(1, Path(sys._MEIPASS) / "backend" / "formatted_extracted.txt")

    for p in candidate_paths:
        if p.exists():
            try:
                parsed = _parse_table_text(p.read_text(encoding="utf-8"))
                if parsed and len(parsed.get("नक्षत्र", [])) >= 108:
                    _CACHED_TABLE = parsed
                    return _CACHED_TABLE
            except Exception:
                pass

    _CACHED_TABLE = _parse_table_text(_EMBEDDED_TABLE_TEXT)
    return _CACHED_TABLE


def _normalize_akshara_symbol(symbol: str) -> str:
    if not symbol:
        return ""

    normalized = str(symbol).strip()
    if not normalized:
        return ""

    replacements = {
        "क़": "क",
        "ख़": "ख",
        "ग़": "ग",
        "ज़": "ज",
        "ड़": "ड",
        "ढ़": "ढ",
        "फ़": "फ",
        "य़": "य",
        "ऩ": "न",
        "ऱ": "र",
        "ऴ": "ल",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized


NAKSHATRA_ALIASES = {
    "आश्लेषा": "अश्लेषा",
    "ashlesha": "अश्लेषा",
    "aslesha": "अश्लेषा",
    "कृत्तिका": "कृतिका",
    "krittika": "कृतिका",
    "आर्द्रा": "आर्दा",
    "ardra": "आर्दा",
    "पुनर्वसु": "पुनर्वशु",
    "punarvasu": "पुनर्वशु",
    "पुष्य": "तिष्य",
    "pushya": "तिष्य",
    "हस्त": "हस्ता",
    "hasta": "हस्ता",
    "विशाखा": "विशाषा",
    "vishakha": "विशाषा",
    "पूर्वाषाढ": "पूर्वाषाढा",
    "उत्तराषाढा": "उत्तरषाढा",
    "उत्तराषाढ": "उत्तरषाढा",
}



# Abhijit (नक्षत्र २२) को embedded table मा केवल 2 charan छ (partial)।
_ABHIJIT_COL_OFFSET = 84  # 0-indexed: 21 normal nakshatras * 4 charans = 84



def _find_group_index(table: Dict[str, list[str]], nakshatra_name: str | None, nakshatra_index: int) -> int:
    nakshatra_row = [str(value).strip() for value in table.get("नक्षत्र", [])]
    if nakshatra_name:
        name_str = str(nakshatra_name).strip()
        aliased = NAKSHATRA_ALIASES.get(name_str) or NAKSHATRA_ALIASES.get(name_str.lower()) or name_str
        for idx, value in enumerate(nakshatra_row):
            if value and (value == aliased or value == name_str):
                return idx

    normalized_index = max(1, int(nakshatra_index))

    # Abhijit (index 22) has only 2 charans in the traditional table.
    # Standard nakshatras 1-21: 4 charans each → columns 0-83
    # Abhijit (22): starts at column 84 (4*21), only 2 charans
    # Shravana onwards (23-27): back to 4 charans
    if normalized_index == 22:
        # Abhijit — return start of its 2-charan block
        col = 21 * 4  # = 84
        return max(0, min(len(nakshatra_row) - 1, col))
    elif normalized_index > 22:
        # Post-Abhijit nakshatras (Shravana=23 through Revati=27):
        # 21 normal * 4 + Abhijit * 2 + (n-23) * 4
        col = 21 * 4 + 2 + (normalized_index - 23) * 4
        return max(0, min(len(nakshatra_row) - 1, col))
    else:
        # Normal nakshatras 1-21: 4 charans each
        return max(0, min(len(nakshatra_row) - 1, (normalized_index - 1) * 4))



def _get_row_value(
    table: Dict[str, list[str]],
    row_key: str,
    nakshatra_name: str | None,
    nakshatra_index: int,
    pada: int,
    use_pada_index: bool = False,
    span_direction: str = "backward",
) -> str:
    """Look up a value from a table row for the given nakshatra/pada."""
    values = [str(value).strip() for value in table.get(row_key, ["—"])]
    if not values:
        return "—"

    group_index = _find_group_index(table, nakshatra_name, nakshatra_index)

    # Per-pada rows (e.g. नामाक्षर) have a distinct value for every pada.
    if use_pada_index:
        index = group_index + (max(1, min(4, int(pada))) - 1)
        val = values[index] if 0 <= index < len(values) else ""
        return val if val else "—"

    if span_direction == "forward":
        # Marker is at the start of the nakshatra group; scan forward.
        for idx in range(group_index, len(values)):
            if values[idx]:
                return values[idx]
        return "—"

    # span_direction == "backward": marker is at the start of its own span.
    # The value covering the target pada is the last non-empty value at or
    # before the target column (group_index + pada - 1).
    target_col = group_index + (max(1, min(4, int(pada))) - 1)
    target_col = min(len(values) - 1, max(0, target_col))
    for idx in range(target_col, -1, -1):
        if values[idx]:
            return values[idx]
    return "—"


def _get_akshara_base(akshara: str) -> str:
    """Return the root consonant or vowel from a Devanagari syllable."""
    s = str(akshara).strip()
    if not s:
        return ""
    # Check multi-char conjuncts first (longest match)
    for conjunct in ["श्री", "श्र", "क्ष", "त्र", "ज्ञ"]:
        if s.startswith(conjunct):
            return conjunct
    first_char = _normalize_akshara_symbol(s[0])
    return first_char[0] if first_char else s[0]


def _get_varga_from_akshara(name_akshara: str) -> tuple[str, str]:
    """Return (varga, shatru_varga) based on the first consonant/vowel of name_akshara."""
    if not name_akshara or name_akshara == "—":
        return ("—", "—")
    base = _get_akshara_base(name_akshara)
    for letters_set, varga, shatru_varga in AKSHARA_VARGA_MAP:
        if base in letters_set:
            return (varga, shatru_varga)
    return ("—", "—")


def calculate_avakahada_chakra(nakshatra_index: int, pada: int, nakshatra_name: str | None = None) -> Dict[str, Any]:
    """Return the Avakahada Chakra values for a given nakshatra and pada."""
    table = _load_table()
    pada_int = max(1, min(4, int(pada or 1)))

    name_akshara = _get_row_value(table, "नामाक्षर", nakshatra_name, nakshatra_index, pada_int, use_pada_index=True)
    rashi_raw = _get_row_value(table, "राशी", nakshatra_name, nakshatra_index, pada_int, span_direction="backward")
    rashi_lord_raw = _get_row_value(table, "राश स्वामी", nakshatra_name, nakshatra_index, pada_int, span_direction="backward")
    nadi_raw = _get_row_value(table, "नाडी", nakshatra_name, nakshatra_index, pada_int, span_direction="forward")
    varga, shatru_varga = _get_varga_from_akshara(name_akshara)

    nakshatra_val = _get_row_value(table, "नक्षत्र", nakshatra_name, nakshatra_index, pada_int, span_direction="forward")
    rashi_val = RASHI_NORMALIZE.get(rashi_raw, rashi_raw)
    rashi_lord_val = RASHI_LORD_NORMALIZE.get(rashi_lord_raw, rashi_lord_raw)
    nadi_val = NADI_NORMALIZE.get(nadi_raw, nadi_raw)

    return {
        "nakshatra_index": int(nakshatra_index),
        "pada": pada_int,
        "name_akshara": name_akshara,
        "nakshatra": nakshatra_val,
        "rashi": rashi_val,
        "rashi_lord": rashi_lord_val,
        "varna": _get_row_value(table, "वर्ण", nakshatra_name, nakshatra_index, pada_int, span_direction="backward"),
        "vashya": _get_row_value(table, "वश्य", nakshatra_name, nakshatra_index, pada_int, span_direction="backward"),
        "yoni": _get_row_value(table, "योनि", nakshatra_name, nakshatra_index, pada_int, span_direction="forward"),
        "viryoni": _get_row_value(table, "वैरयोनि", nakshatra_name, nakshatra_index, pada_int, span_direction="forward"),
        "gana": _get_row_value(table, "गण", nakshatra_name, nakshatra_index, pada_int, span_direction="forward"),
        "nadi": nadi_val,
        "asana": _get_row_value(table, "आसन", nakshatra_name, nakshatra_index, pada_int, span_direction="forward"),
        "varga": varga,
        "shatru_varga": shatru_varga,
    }

