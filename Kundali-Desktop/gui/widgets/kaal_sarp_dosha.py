"""
gui/widgets/kaal_sarp_dosha.py
Kaal Sarp Dosha report — plain-page desktop view.
Displays Kaal Sarp Dosha analysis produced by
backend/calculator/kaal_sarp_dosha.py (data["kaal_sarp_dosha"]).
No card boxes — only clean, larger text on an open page.
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea
)
from PySide6.QtCore import Qt

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
                        COLOR_TEXT_MUTED, COLOR_ERROR, COLOR_SUCCESS)

# ─────────────────────────────────────────────
# Labels
# ─────────────────────────────────────────────
PLANET_LABELS = {
    "en": {"Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
           "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn",
           "Rahu": "Rahu", "Ketu": "Ketu"},
    "ne": {"Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
           "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि",
           "Rahu": "राहु", "Ketu": "केतु"},
}

SIGN_LABELS = {
    "en": ["", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
           "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
    "ne": ["", "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या", "तुला",
           "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"],
}

NAKSHATRA_NAMES = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
    "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी",
    "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा",
    "मूल", "पूर्वाषाढा", "उत्तराषाढा", "श्रवण", "धनिष्ठा", "शतभिषा",
    "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती",
]

SEVERITY_COLORS = {
    1: "#16a34a",
    2: "#d97706",
    3: "#ea580c",
    4: "#dc2626",
}


def _to_nepali_num(value) -> str:
    """Convert digits in a string to Nepali numerals."""
    if value is None:
        return "—"
    d = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"]
    return "".join(d[int(ch)] if ch.isdigit() else ch for ch in str(value))


def _planet_label(name: str, lang: str) -> str:
    return PLANET_LABELS.get(lang, PLANET_LABELS["en"]).get(name, name)


def _sign_label(num, lang: str) -> str:
    labels = SIGN_LABELS.get(lang, SIGN_LABELS["en"])
    try:
        return labels[int(num)]
    except (TypeError, ValueError, IndexError):
        return ""


def _nakshatra_label(index) -> str:
    try:
        return NAKSHATRA_NAMES[int(index) % 27]
    except (TypeError, ValueError):
        return ""


def _house_ordinal(h, lang: str) -> str:
    if lang == "ne":
        return f"{_to_nepali_num(h)}औं"
    return f"House {h}"


class KaalSarpDoshaPage(QWidget):
    """Plain-text Kaal Sarp Dosha page (no boxes, larger letters)."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        if data:
            self.refresh(data)

    # ── UI helpers ──────────────────────────────────────────────
    @staticmethod
    def _styled(text: str, color: str = COLOR_TEXT_PRIMARY, size: int = 15,
                bold: bool = False, wrap: bool = True) -> QLabel:
        lbl = QLabel(text)
        weight = "700" if bold else "400"
        lbl.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: {weight};")
        if wrap:
            lbl.setWordWrap(True)
        return lbl

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 16, 24, 16)
        outer.setSpacing(6)

        # Scrollable plain page
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._content = QVBoxLayout(self._container)
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(10)
        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll, 1)

    # ── Public API ──────────────────────────────────────────────
    def refresh(self, data: dict) -> None:
        self._data = data
        self._clear_content()
        ksd = data.get("kaal_sarp_dosha") or {}
        if not ksd:
            empty = QLabel(
                "कालसर्प दोष डाटा उपलब्ध छैन।" if self._is_ne
                else "Kaal Sarp Dosha data is not available."
            )
            empty.setStyleSheet(
                f"color: {COLOR_TEXT_MUTED}; font-size: 17px; padding: 24px;")
            empty.setAlignment(Qt.AlignCenter)
            self._content.addWidget(empty)
            return

        present = bool(ksd.get("present"))

        # Big title
        title = QLabel("🐍 " + ("कालसर्प दोष विश्लेषण" if self._is_ne
                                else "Kaal Sarp Dosha Analysis"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 24px; font-weight: 700;")
        self._content.addWidget(title)

        # Partial KSD detection — BPHS rule
        in_planets  = ksd.get("grahas_in_ksd", [])
        out_planets = ksd.get("grahas_outside", [])
        is_partial  = present and bool(out_planets)
        if is_partial:
            out_names = ", ".join(
                _planet_label(g.get("name"), self._lang) for g in out_planets
            )
            partial_note = self._styled(
                "⚠ " + ("आंशिक कालसर्प दोष (Partial KSD):\n"
                         f"राहु-केतु अक्ष बाहिर: {out_names}\n"
                         "पूर्ण कालसर्प दोष: सबै ७ ग्रह Rahu-Ketu बीच हुनु पर्छ।\n"
                         "यहाँ केही ग्रह बाहिर छन् — फल तुलनात्मक रूपमा कम प्रभावकारी।"
                         if self._is_ne else
                         "Partial Kaal Sarp Dosha:\n"
                         f"Planets outside axis: {out_names}\n"
                         "Full KSD requires ALL 7 planets within the Rahu-Ketu arc.\n"
                         "Since some are outside, the effects are proportionally reduced."),
                "#f97316", 15)
            self._content.addWidget(partial_note)

        # Severity stars (rank 1-4)
        severity = ksd.get("severity") or {}
        sev_rank = severity.get("rank", 0)
        if present and sev_rank:
            stars    = "★" * sev_rank + "☆" * (4 - sev_rank)
            sev_color = SEVERITY_COLORS.get(sev_rank, "#64748b")
            sev_label_text = severity.get("label_ne" if self._is_ne else "label_en", "")
            stars_lbl = self._styled(
                f"गम्भीरता: {stars}  {sev_label_text}" if self._is_ne
                else f"Severity: {stars}  {sev_label_text}",
                sev_color, 17, bold=True)
            self._content.addWidget(stars_lbl)

        # Status line
        if present:
            status = self._styled("✓ " + ("दोष उपस्थित" if self._is_ne
                                          else "Dosha Present"),
                                  COLOR_ERROR, 18, bold=True)
        else:
            status = self._styled("✓ " + ("यो कुण्डलीमा कालसर्प दोष छैन।" if self._is_ne
                                          else "Kaal Sarp Dosha is not present."),
                                  COLOR_SUCCESS, 18, bold=True)
        self._content.addWidget(status)

        # Narrative
        narrative = ksd.get("narrative_ne" if self._is_ne else "narrative_en", "")
        if narrative:
            self._content.addWidget(self._styled(narrative, COLOR_TEXT_PRIMARY, 16))

        if present:
            self._build_present_sections(ksd)
        else:
            self._build_not_present_sections(ksd)

        self._build_remedies_section(ksd)
        self._build_disclaimer_section(ksd)
        self._content.addStretch()

    # ── Section builders ─────────────────────────────────────────
    def _add_heading(self, text: str) -> None:
        self._content.addWidget(
            self._styled(text, COLOR_GOLD, 19, bold=True))

    def _node_position_text(self, node_name: str, node: dict) -> str:
        sign_no = node.get("sign_number")
        naks = node.get("nakshatra") or {}
        nidx = naks.get("index")
        pada = naks.get("pada")
        naks_name = _nakshatra_label(nidx) if nidx is not None else ""
        if self._is_ne:
            parts = [f"{_planet_label(node_name, 'ne')}: {_sign_label(sign_no, 'ne')} राशि",
                     f"{naks_name} नक्षत्र"]
            if pada is not None:
                parts.append(f"{_to_nepali_num(pada)} चरण")
            return ", ".join(parts)
        text = f"{node_name}: {_sign_label(sign_no, 'en')} sign, {naks.get('name', naks_name)} nakshatra"
        if pada is not None:
            text += f", pada {pada}"
        return text

    def _build_present_sections(self, ksd: dict) -> None:
        type_info = ksd.get("type") or {}
        severity = ksd.get("severity") or {}

        # Type + meaning
        type_name = type_info.get("name_ne" if self._is_ne else "name_en", "—")
        sev_color = SEVERITY_COLORS.get(severity.get("rank", 1), SEVERITY_COLORS[1])
        self._content.addWidget(self._styled("कालसर्पको प्रकार: " if self._is_ne
                                             else "Kaal Sarp Type: ",
                                             COLOR_TEXT_MUTED, 16))
        self._content.addWidget(self._styled(type_name, sev_color, 18, bold=True))
        meaning = type_info.get("meaning_ne" if self._is_ne else "meaning_en", "")
        if meaning:
            self._content.addWidget(self._styled(meaning, COLOR_TEXT_SECONDARY, 16))
        if severity:
            sev_label = severity.get("label_ne" if self._is_ne else "label_en", "")
            self._content.addWidget(self._styled(
                ("गम्भीरता: " if self._is_ne else "Severity: ") + str(sev_label),
                sev_color, 17, bold=True))

        # Node positions (Rahu / Ketu)
        self._add_heading("राहु र केतु स्थिति" if self._is_ne
                          else "Rahu & Ketu Positions")
        rahu = ksd.get("rahu") or {}
        ketu = ksd.get("ketu") or {}
        for node_name, node in (("Rahu", rahu), ("Ketu", ketu)):
            if node:
                self._content.addWidget(
                    self._styled(self._node_position_text(node_name, node),
                                 COLOR_TEXT_PRIMARY, 16, bold=True))

        # Affected houses
        house_details = ksd.get("house_details", [])
        if house_details:
            self._add_heading("प्रभावित भावहरू" if self._is_ne else "Affected Houses")
            for item in house_details:
                h = item.get("house")
                sig = item.get("signification_ne" if self._is_ne
                               else "signification_en", "")
                planets = item.get("planets", [])
                planets_text = ", ".join(
                    _planet_label(p, self._lang) for p in planets) if planets else "—"
                if self._is_ne:
                    line = (f"{_house_ordinal(h, self._lang)} "
                            f"({_sign_label(item.get('sign_number'), 'ne')} राशि): {sig}"
                            f"\nग्रहहरू: {planets_text}")
                else:
                    line = (f"{_house_ordinal(h, self._lang)} "
                            f"({_sign_label(item.get('sign_number'), 'en')} sign): {sig}"
                            f"\nPlanets: {planets_text}")
                self._content.addWidget(self._styled(line, COLOR_TEXT_SECONDARY, 16))

        # Grahas in/out summary
        in_planets = ksd.get("grahas_in_ksd", [])
        out_planets = ksd.get("grahas_outside", [])
        in_names = ", ".join(_planet_label(g.get("name"), self._lang) for g in in_planets)
        out_names = ", ".join(_planet_label(g.get("name"), self._lang) for g in out_planets)
        if in_names:
            self._add_heading("ग्रह स्थिति सारांश" if self._is_ne
                              else "Planet Position Summary")
            if self._is_ne:
                self._content.addWidget(self._styled(
                    f"राहु-केतु बीचमा ({len(in_planets)} ग्रह): {in_names}",
                    COLOR_TEXT_PRIMARY, 16))
                if out_names:
                    self._content.addWidget(self._styled(
                        f"अक्ष बाहिर ({len(out_planets)} ग्रह): {out_names}",
                        COLOR_TEXT_MUTED, 15))
            else:
                self._content.addWidget(self._styled(
                    f"Between Rahu–Ketu ({len(in_planets)} planets): {in_names}",
                    COLOR_TEXT_PRIMARY, 16))
                if out_names:
                    self._content.addWidget(self._styled(
                        f"Outside axis ({len(out_planets)} planets): {out_names}",
                        COLOR_TEXT_MUTED, 15))

    def _build_not_present_sections(self, ksd: dict) -> None:
        rahu = ksd.get("rahu") or {}
        ketu = ksd.get("ketu") or {}
        if rahu or ketu:
            self._add_heading("राहु र केतु स्थिति" if self._is_ne
                              else "Rahu & Ketu Positions")
            for node_name, node in (("Rahu", rahu), ("Ketu", ketu)):
                if node:
                    self._content.addWidget(
                        self._styled(self._node_position_text(node_name, node),
                                     COLOR_TEXT_PRIMARY, 16, bold=True))

    def _build_remedies_section(self, ksd: dict) -> None:
        remedies = ksd.get("remedies", [])
        if not remedies:
            return
        self._add_heading("उपायहरू" if self._is_ne else "Remedies")
        for i, r in enumerate(remedies, 1):
            text = r.get("ne" if self._is_ne else "en", "")
            if not text:
                continue
            self._content.addWidget(self._styled(
                f"{_to_nepali_num(i)}. {text}", COLOR_TEXT_SECONDARY, 16))

    def _build_disclaimer_section(self, ksd: dict) -> None:
        disclaimer = ksd.get("disclaimer") or {}
        text = disclaimer.get("ne" if self._is_ne else "en", "")
        if not text:
            return
        self._content.addWidget(self._styled(
            "⚠ " + text, COLOR_TEXT_MUTED, 14))

    # ── Helpers ──────────────────────────────────────────────────
    def _clear_content(self) -> None:
        while self._content.count():
            item = self._content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
