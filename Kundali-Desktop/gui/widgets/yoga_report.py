# -*- coding: utf-8 -*-
"""
gui/widgets/yoga_report.py
Parashara Yoga Report — plain-page desktop view (v2).

Backend (calculator/yogas.py) computes every yoga live.
Yogas can now be formed via:
  1. Yuti (Conjunction)       - same house
  2. Parivartana (Exchange)   - mutual sign exchange
  3. Drishti (Aspect)         - Parashari aspects Mars(4/8), Jupiter(5/9), Saturn(3/10)

This widget detects and badges each sambandha type.
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)
from PySide6.QtCore import Qt

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
                        COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_ERROR)

# ------------------------------------------------------------------
# Category / Severity / Sambandha lookups
# ------------------------------------------------------------------
CATEGORY_LABELS = {
    "mahapurusha": ("पञ्च महापुरुष योग",       "Pancha Mahapurusha Yoga", "#f59e0b"),
    "raja":        ("राज योग",               "Raja Yoga",               "#a855f7"),
    "viparita":    ("विपरीत राज योग",        "Viparita Raja Yoga",      "#8b5cf6"),
    "dhana":       ("धन योग",                "Dhana Yoga",              "#22c55e"),
    "chandra":     ("चन्द्र योग",             "Chandra Yoga",            "#2563eb"),
    "surya":       ("सूर्य योग",              "Surya Yoga",              "#d97706"),
    "conjunction": ("ग्रह युति योग",          "Conjunction Yoga",        "#06b6d4"),
    "parivartana": ("परिवर्तन योग",          "Parivartana Yoga",        "#10b981"),
    "nabhas":      ("नाभस योग",              "Nabhas Yoga",             "#6366f1"),
    "vidya":       ("विद्या योग",             "Vidya Yoga",              "#0ea5e9"),
    "ayur":        ("आयु योग",               "Ayur Yoga",               "#84cc16"),
    "sanyasa":     ("सन्यास योग",            "Sanyasa Yoga",            "#a78bfa"),
    "misc":        ("शुभ योग",               "Misc. Auspicious Yoga",   "#34d399"),
    "arishta":     ("अरिष्ट योग",             "Arishta Yoga",            "#f97316"),
    "dosha":       ("दोष / दुर्योग",          "Dosha / Dur-Yoga",        "#ef4444"),
    "spiritual":   ("आध्यात्मिक योग",        "Spiritual Yoga",          "#818cf8"),
    "kubera":      ("कुबेर योग",             "Kubera Yoga",             "#fbbf24"),
}

CATEGORY_LABELS_NE = {
    "mahapurusha": "पञ्च महापुरुष योग",
    "raja":        "राज योग",
    "viparita":    "विपरीत राज योग",
    "dhana":       "धन योग",
    "chandra":     "चन्द्र योग",
    "surya":       "सूर्य योग",
    "conjunction": "ग्रह युति योग",
    "parivartana": "परिवर्तन योग",
    "nabhas":      "नाभस योग",
    "vidya":       "विद्या योग",
    "ayur":        "आयु योग",
    "sanyasa":     "सन्यास योग",
    "misc":        "शुभ योग",
    "arishta":     "अरिष्ट योग",
    "dosha":       "दोष / दुर्योग",
    "spiritual":   "आध्यात्मिक योग",
    "kubera":      "कुबेर योग",
}

SEVERITY_LABELS = {
    "highly_auspicious": ("अत्यन्त शुभ",   "Highly Auspicious", "#16a34a"),
    "auspicious":        ("शुभ",           "Auspicious",        "#16a34a"),
    "neutral":           ("तटस्थ",         "Neutral",           "#64748b"),
    "spiritual":         ("आध्यात्मिक",     "Spiritual",         "#6366f1"),
    "challenging":       ("चुनौतीपूर्ण",     "Challenging",       "#dc2626"),
}

SAMBANDHA_BADGES = {
    "drishti":     (("दृष्टि", "Drishti (Aspect)"), "#a855f7"),
    "exchange":    (("परिवर्तन", "Exchange"),       "#10b981"),
    "conjunction": (("युति", "Conjunction"),         "#06b6d4"),
    "placement":   (("स्थिति", "Placement"),         "#f59e0b"),
}

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु", "Ascendant": "लग्न"
}

NEPALI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")


def _to_nepali_num(value) -> str:
    if value is None:
        return "—"
    return str(value).translate(NEPALI_DIGITS)


def _clean_markup(text: str) -> str:
    return (text or "").replace("**", "").strip()


def _detect_sambandha_type(formation_text: str) -> str:
    t = (formation_text or "").lower()
    if any(w in t for w in ["drishti", "aspect", "aspects", "mutual aspect"]):
        return "drishti"
    if any(w in t for w in ["exchange", "parivartana", "mutual exchange"]):
        return "exchange"
    if any(w in t for w in ["conjunct", "conjunction", "same house", "same sign"]):
        return "conjunction"
    return "placement"


class YogaReportPage(QWidget):
    """Plain white report page listing every yoga active in this kundali."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._all_yogas: list = []
        self._build_ui()
        if data:
            self.refresh(data)

    def _t(self, en: str, ne: str) -> str:
        return ne if self._is_ne else en

    def set_language(self, language: str) -> None:
        self._lang = language
        self._is_ne = language == "ne"
        if self._data:
            self.refresh(self._data)

    def _category_label(self, category: str):
        key = (category or "").lower()
        info = CATEGORY_LABELS.get(key, ("", "", "#a1a1aa"))
        ne_name = CATEGORY_LABELS_NE.get(key, info[0])
        return (ne_name if self._is_ne else info[1], info[2])

    def _severity_label(self, severity: str):
        info = SEVERITY_LABELS.get((severity or "").lower(), ("", "", "#64748b"))
        return (info[0] if self._is_ne else info[1], info[2])

    @staticmethod
    def _make_label(text: str, color: str = COLOR_TEXT_PRIMARY, size: int = 16,
                    bold: bool = False, wrap: bool = True) -> QLabel:
        lbl = QLabel(text)
        weight = "700" if bold else "400"
        lbl.setStyleSheet(
            f"color: {color}; font-size: {size}px; font-weight: {weight}; "
            "line-height: 1.5; background: transparent;")
        if wrap:
            lbl.setWordWrap(True)
        return lbl

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")

        self._container = QWidget()
        self._container.setObjectName("PlainPage")
        self._container.setStyleSheet("QWidget#PlainPage { background: #ffffff; }")
        self._content = QVBoxLayout(self._container)
        self._content.setContentsMargins(28, 20, 28, 20)
        self._content.setSpacing(8)
        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll, 1)

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #dbe5f6; background: #dbe5f6; max-height: 1px;"
                           " border: none; margin: 6px 0;")
        return line

    # -- Public API ---------------------------------------------------
    def refresh(self, data: dict) -> None:
        self._data = data
        self._clear_content()

        raw = data.get("parashara_yogas")
        if raw is None:
            raw = data.get("yoga_report") or data.get("yogas") or []
        self._all_yogas = [
            y for y in raw
            if y and y.get("is_present", True) is not False
        ]

        count = len(self._all_yogas)
        auspicious_count = sum(
            1 for y in self._all_yogas
            if y.get("severity", "") in ("highly_auspicious", "auspicious", "spiritual"))
        dosha_count = sum(
            1 for y in self._all_yogas
            if y.get("category", "") in ("arishta", "dosha"))
        drishti_count = sum(
            1 for y in self._all_yogas
            if _detect_sambandha_type(
                (y.get("formation_ne") or "") + (y.get("formation_en") or "")
            ) == "drishti"
        )

        # Header
        title = QLabel(self._t("Parashara Yoga Report", "पाराशरी योग प्रतिवेदन"))
        title.setStyleSheet(
            f"color: {COLOR_GOLD}; font-size: 24px; font-weight: 700;"
            " background: transparent;")
        self._content.addWidget(title)

        if count:
            if self._is_ne:
                summary_text = (
                    f"यस कुण्डलीमा जम्मा {_to_nepali_num(count)} वटा योगहरू प्रमाणित भएका छन् — "
                    f"{_to_nepali_num(auspicious_count)} शुभ, "
                    f"{_to_nepali_num(dosha_count)} दोष/अरिष्ट, "
                    f"{_to_nepali_num(drishti_count)} पाराशरी दृष्टिबाट निर्मित। "
                    "प्रत्येक योग वास्तविक ग्रह स्थिति, डिग्री तथा दृष्टि अनुसार प्रत्यक्ष रूपमा गणना गरिएको हो।"
                )
            else:
                summary_text = (
                    f"{count} yogas confirmed -- "
                    f"{auspicious_count} auspicious, "
                    f"{dosha_count} dosha/arishta, "
                    f"{drishti_count} via Parashari Drishti (aspect). "
                    "Each yoga is derived live from actual planetary positions, degrees and aspects."
                )
            summary = self._make_label(summary_text, COLOR_TEXT_SECONDARY, 16)
        else:
            summary = self._make_label(
                self._t(
                    "No Parashara yoga is currently formed in this chart.",
                    "यस कुण्डलीमा कुनै पाराशरीय योग फेला परेन।"
                ),
                COLOR_TEXT_MUTED, 17)
        self._content.addWidget(summary)
        self._content.addWidget(self._separator())

        for idx, yoga in enumerate(self._all_yogas, 1):
            self._add_yoga_block(yoga, idx)

        diag = data.get("yoga_diagnostics") or []
        if diag:
            note_lbl = self._make_label(
                self._t(
                    f"Warning: {len(diag)} detector(s) reported an issue.",
                    f"चेतावनी: {_to_nepali_num(len(diag))} वटा सूचकमा समस्या भेटियो।"
                ),
                COLOR_ERROR, 13)
            note_lbl.setToolTip("\n".join(
                f"{d.get('detector', '?')}: {d.get('error', '')}" for d in diag))
            self._content.addWidget(note_lbl)

        self._content.addWidget(self._separator())
        self._content.addWidget(self._make_label(
            self._t(
                "BPHS Parashari Drishti included: Mars (4th/8th), Jupiter (5th/9th), "
                "Saturn (3rd/10th). Yogas formed via aspect are marked [Drishti].",
                "बृहत् पाराशर होरा शास्त्र अनुसारको विशेष दृष्टि समावेश: मङ्गल (४/८), गुरु (५/९), "
                "शनि (३/१०)। दृष्टिद्वारा निर्मित योगहरूलाई [दृष्टि] चिन्ह लगाइएको छ।"
            ),
            COLOR_TEXT_MUTED, 13))
        self._content.addStretch()

    # -- Yoga block renderer ------------------------------------------
    def _add_yoga_block(self, yoga: dict, index: int) -> None:
        name_ne = yoga.get("nepali") or yoga.get("name_ne") or yoga.get("name", "-")
        name_en = yoga.get("name") or name_ne
        name = name_ne if self._is_ne else name_en

        category = yoga.get("category", "")
        severity = yoga.get("severity", "")
        _, cat_color = self._category_label(category)
        sev_text, _  = self._severity_label(severity)

        idx_str = f"{_to_nepali_num(index)}." if self._is_ne else f"{index}."
        name_lbl = self._make_label(
            f"{idx_str} {name}", cat_color, 19, bold=True)
        self._content.addWidget(name_lbl)

        # Sambandha type detection
        formation_raw = (yoga.get("formation_ne") or "") + (yoga.get("formation_en") or "")
        sb_type = _detect_sambandha_type(formation_raw)
        sb_info = SAMBANDHA_BADGES.get(sb_type, (("युति", "Conjunction"), "#06b6d4"))
        sb_label = sb_info[0][0] if self._is_ne else sb_info[0][1]
        sb_icon = {
            "drishti": "[दृष्टि]" if self._is_ne else "[Drishti]",
            "exchange": "[परिवर्तन]" if self._is_ne else "[Exchange]",
            "conjunction": "[युति]" if self._is_ne else "[Conjunction]",
            "placement": "[स्थिति]" if self._is_ne else "[Placement]",
        }.get(sb_type, "")

        meta_parts = []
        cat_text, _ = self._category_label(category)
        if cat_text:
            meta_parts.append(cat_text)
        if sev_text:
            meta_parts.append(sev_text)
        strength = yoga.get("strength_pct")
        if strength is not None:
            if self._is_ne:
                meta_parts.append(f"बल {_to_nepali_num(strength)}%")
            else:
                meta_parts.append(f"Strength {strength}%")
        if sb_icon:
            meta_parts.append(sb_icon)

        meta_lbl = self._make_label(
            "  |  ".join(p for p in meta_parts if p),
            COLOR_TEXT_MUTED, 13, bold=True)
        self._content.addWidget(meta_lbl)

        formation = _clean_markup(
            yoga.get("formation_ne" if self._is_ne else "formation_en", ""))
        if not formation:
            formation = _clean_markup(
                yoga.get("cause_ne" if self._is_ne else "cause_en", ""))
        if formation:
            self._content.addWidget(self._make_label(
                self._t("How it forms:", "निर्माण विधि:"), COLOR_TEXT_PRIMARY, 15, bold=True))
            self._content.addWidget(self._make_label(
                formation, COLOR_TEXT_PRIMARY, 16))

        result = yoga.get("result_ne" if self._is_ne else "result_en", "")
        if result:
            self._content.addWidget(self._make_label(
                self._t("Phala:", "फल:"), COLOR_GOLD, 15, bold=True))
            self._content.addWidget(self._make_label(
                result, COLOR_TEXT_PRIMARY, 17, bold=True))

        self._add_planet_position_lines(yoga)

        remedy = yoga.get("remedy_ne" if self._is_ne else "remedy_en", "")
        if remedy:
            self._content.addWidget(self._make_label(
                self._t("Remedy:", "उपाय:"), COLOR_SUCCESS, 15, bold=True))
            self._content.addWidget(self._make_label(
                remedy, COLOR_TEXT_SECONDARY, 16))

        refs = yoga.get("references") or []
        if refs:
            ref_prefix = self._t("References: ", "शास्त्रीय सन्दर्भ: ")
            self._content.addWidget(self._make_label(
                ref_prefix + ", ".join(str(r) for r in refs),
                COLOR_TEXT_MUTED, 13))

        self._content.addWidget(self._separator())

    def _add_planet_position_lines(self, yoga: dict) -> None:
        rows = yoga.get("planet_rows") or []
        if not rows:
            involved = yoga.get("planets_involved") or []
            if involved:
                inv_names = [PLANET_NAMES_NE.get(str(p), str(p)) if self._is_ne else str(p) for p in involved]
                p_title = self._t("Planets: ", "सम्बन्धित ग्रहहरू: ")
                self._content.addWidget(self._make_label(
                    p_title + ", ".join(inv_names),
                    COLOR_TEXT_SECONDARY, 15))
            return

        self._content.addWidget(self._make_label(
            self._t("Planet positions in this chart:", "यस कुण्डलीमा ग्रहहरूको स्थिति:"),
            COLOR_TEXT_PRIMARY, 15, bold=True))

        for r in rows:
            name_key = "name_ne" if self._is_ne else "name_en"
            house_key = "house_name_ne" if self._is_ne else "house_name_en"
            sign_key  = "sign_ne" if self._is_ne else "sign_en"
            pname = r.get(name_key) or r.get("name_en", "")
            if self._is_ne:
                pname = PLANET_NAMES_NE.get(pname, pname)
            house = r.get(house_key, "")
            sign  = r.get(sign_key, "")
            deg_val = r.get("degree", "")
            deg_str = f"{_to_nepali_num(deg_val)}°" if self._is_ne else f"{deg_val}°"
            line  = f"{pname}: {house} ({sign}, {deg_str})"
            extras = []
            state = r.get("state", "")
            if state == "exalted":       extras.append("उच्च" if self._is_ne else "Exalted")
            elif state == "debilitated": extras.append("नीच" if self._is_ne else "Debilitated")
            elif r.get("is_own"):        extras.append("स्वगृही" if self._is_ne else "Own sign")
            if r.get("is_retro"):        extras.append("वक्री (R)" if self._is_ne else "Retrograde R")
            if r.get("is_combust"):      extras.append("अस्त" if self._is_ne else "Combust")
            if r.get("is_vargottama"):   extras.append("वर्गोत्तम ✨" if self._is_ne else "Vargottama ✨")
            if extras:
                line += " (" + ", ".join(extras) + ")"
            self._content.addWidget(
                self._make_label("• " + line, COLOR_TEXT_SECONDARY, 15))

    def _clear_content(self) -> None:
        while self._content.count():
            item = self._content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
