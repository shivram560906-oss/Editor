# -*- coding: utf-8 -*-
"""
gui/widgets/transit_analysis_page.py

Enhanced Gochar (Transit) Analysis Widget.

Surfaces the native `calculator.transit_analysis` engine:
- Tarabala for every transit planet from the natal Moon nakshatra
- Chandrabala (Moon strength) for the selected date
- Transit dignity (exaltation / debilitation / own sign)
- Double Transit triggers (Jupiter + Saturn) for key life events
- Parashari transit aspects to natal planets

All calculations run synchronously and defensively: an un-joined QThread is
never created, matching the native crash-avoidance contract used by the other
report pages.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QPushButton,
    QGridLayout,
)

from gui.theme import (
    COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_SUCCESS,
    COLOR_ERROR, COLOR_WARNING, BG_PRIMARY,
)
from gui.utils.planet_colors import planet_color

_DIGNITY_LABELS = {
    "exalted": ("उच्च", "Exalted", COLOR_SUCCESS),
    "debilitated": ("नीच", "Debilitated", COLOR_ERROR),
    "own_sign": ("स्वगृह", "Own Sign", COLOR_ACCENT),
    "neutral": ("सम", "Neutral", COLOR_TEXT_SECONDARY),
}

_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_NAMES_NE = [
    "मेष", "वृष", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन",
]


def _clear_layout(layout) -> None:
    """Delete every child widget/item from a layout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        child = item.layout()
        if child is not None:
            _clear_layout(child)


def _section_card(title: str, icon: str = "✦") -> "tuple[QFrame, QVBoxLayout]":
    """Return a styled card frame and its inner vertical layout."""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{ background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; "
        f"border-radius: 10px; }}"
    )
    inner = QVBoxLayout(frame)
    inner.setContentsMargins(14, 12, 14, 12)
    inner.setSpacing(8)
    heading = QLabel(f"{icon} {title}")
    heading.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 14px; font-weight: 800; border: none;")
    inner.addWidget(heading)
    return frame, inner


class TransitAnalysisPage(QWidget):
    """Enhanced transit / Gochar analysis for the active natal chart."""

    def __init__(self, data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._result: Optional[Dict[str, Any]] = None
        self._build_ui()
        if isinstance(data, dict) and data:
            self.refresh(data)
        else:
            self._render_message(
                "कृपया पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne
                else "Please calculate a chart first.",
                COLOR_TEXT_MUTED,
            )

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(
            "🛰️ " + ("गोचर तथा ट्रान्जिट विश्लेषण (Transit Analysis)" if self._is_ne
                     else "Enhanced Transit (Gochar) Analysis")
        )
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 800;")
        header.addWidget(title)
        header.addStretch()

        header.addWidget(QLabel("मिति (Date):" if self._is_ne else "Date:"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setStyleSheet(
            f"background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; "
            f"padding: 4px 8px; border: 1px solid {BORDER_COLOR}; border-radius: 4px;"
        )
        header.addWidget(self._date_edit)

        btn = QPushButton("🔄 " + ("विश्लेषण गर्नुहोस्" if self._is_ne else "Analyze"))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: {COLOR_GOLD}; color: #ffffff; font-weight: 700; "
            f"padding: 6px 16px; border-radius: 6px; }} "
            f"QPushButton:hover {{ background: {COLOR_ACCENT}; }}"
        )
        btn.clicked.connect(self._compute)
        header.addWidget(btn)
        root.addLayout(header)

        info = QLabel(
            "स्वीस इफेमेरिसद्वारा छनोट मितिको ग्रहस्थिति निकाली जन्मकुण्डलीसँग तुलना गरी ताराबल, "
            "चन्द्रबल, ग्रह बल, युगपत् गोचर (Double Transit) र गोचर दृष्टि देखाइन्छ।"
            if self._is_ne else
            "Swiss Ephemeris transit positions compared against the natal chart "
            "(Tarabala, Chandrabala, dignity, Double Transit and transit aspects)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; padding: 2px 0;")
        root.addWidget(info)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(f"QScrollArea {{ background: {BG_PRIMARY}; border: none; }}")
        self._content = QWidget()
        self._content.setStyleSheet(f"background: {BG_PRIMARY};")
        self._body = QVBoxLayout(self._content)
        self._body.setContentsMargins(2, 2, 2, 2)
        self._body.setSpacing(12)
        self._body.addStretch()
        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, 1)

    # ── Public API ─────────────────────────────────────────────────────────
    def refresh(self, data: dict) -> None:
        self._data = data
        self._compute()

    # ── Computation & rendering ────────────────────────────────────────────
    def _selected_jd(self) -> float:
        qdate = self._date_edit.date()
        timezone = 5.75
        metadata = (self._data or {}).get("metadata") or {}
        try:
            timezone = float(metadata.get("timezone", 5.75) or 5.75)
        except (TypeError, ValueError):
            timezone = 5.75
        from calculator.julian import datetime_to_jd
        return datetime_to_jd(qdate.year(), qdate.month(), qdate.day(), 12, 0, 0, timezone)

    def _compute(self) -> None:
        if not isinstance(self._data, dict) or not self._data:
            self._render_message(
                "कृपया पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne
                else "Please calculate a chart first.",
                COLOR_TEXT_MUTED,
            )
            return
        try:
            from gui.backend_bridge import calculate_transit_analysis
            self._result = calculate_transit_analysis(
                self._data, transit_jd=self._selected_jd(), language=self._lang
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._render_message(
                f"गणना त्रुटि: {exc}" if self._is_ne else f"Calculation error: {exc}",
                COLOR_ERROR,
            )
            return
        self._render()

    def _render_message(self, text: str, color: str) -> None:
        _clear_layout(self._body)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {color}; font-size: 14px; padding: 40px 20px;")
        self._body.addWidget(label)
        self._body.addStretch()

    def _render(self) -> None:
        _clear_layout(self._body)
        result = self._result or {}
        summary = result.get("summary") or {}

        self._body.addWidget(self._summary_card(result, summary))
        self._body.addWidget(self._chandrabala_card(result.get("chandrabala") or {}))
        self._body.addWidget(self._planet_table(result.get("planet_transits") or {}))
        self._body.addWidget(self._double_transit_card(result.get("double_transit_triggers") or []))
        self._body.addWidget(self._aspects_card(result.get("transit_aspects") or []))
        self._body.addStretch()

    def _summary_card(self, result: dict, summary: dict) -> QFrame:
        frame, inner = _section_card("सारांश (Summary)" if self._is_ne else "Summary", "📊")
        score = summary.get("overall_score", 0)
        quality = summary.get("overall_quality_ne" if self._is_ne else "overall_quality_en", "-")
        score_color = COLOR_SUCCESS if score >= 6 else (COLOR_WARNING if score >= 4 else COLOR_ERROR)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(6)

        def _cell(row: int, col: int, label: str, value: str, value_color: str = COLOR_TEXT_PRIMARY):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; border: none;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {value_color}; font-size: 14px; font-weight: 700; border: none;")
            grid.addWidget(lbl, row, col * 2)
            grid.addWidget(val, row, col * 2 + 1)

        janma = result.get("janma_nakshatra") or {}
        _cell(0, 0, "जन्म नक्षत्र (Natal Nak.):",
              janma.get("ne" if self._is_ne else "en", "-"))
        _cell(0, 1, "लग्न राशि (Lagna Sign):",
              self._sign_name(result.get("lagna_sign", 0)))
        _cell(1, 0, "जन्म चन्द्र राशि (Natal Moon):",
              self._sign_name(result.get("natal_moon_sign", 0)))
        _cell(1, 1, "शुभ ग्रह (Auspicious):",
              f"{summary.get('auspicious_planets_count', 0)} / {summary.get('total_planets_analyzed', 0)}")
        _cell(2, 0, "चन्द्रबल (Chandrabala):",
              "शुभ" if summary.get("chandrabala_ok") else "अशुभ" if self._is_ne
              else ("Auspicious" if summary.get("chandrabala_ok") else "Inauspicious"),
              COLOR_SUCCESS if summary.get("chandrabala_ok") else COLOR_ERROR)
        _cell(2, 1, "युगपत् गोचर (Double Transit):",
              str(summary.get("double_transit_events", 0)))
        _cell(3, 0, "चन्द्र तारा चेतावनी (Moon Tara Warning):",
              ("छ" if summary.get("moon_tara_warning") else "छैन") if self._is_ne
              else ("Yes" if summary.get("moon_tara_warning") else "No"),
              COLOR_WARNING if summary.get("moon_tara_warning") else COLOR_SUCCESS)
        _cell(3, 1, "कुल स्कोर (Overall Score):", f"{score} — {quality}", score_color)

        inner.addLayout(grid)
        return frame

    def _chandrabala_card(self, chandrabala: dict) -> QFrame:
        frame, inner = _section_card("चन्द्रबल (Chandrabala)" if self._is_ne else "Chandrabala", "🌙")
        if not chandrabala:
            inner.addWidget(self._muted_label("—"))
            return frame
        text = (
            f"जन्म चन्द्र राशि: {self._sign_name(chandrabala.get('natal_moon_sign', 0))} | "
            f"गोचर चन्द्र राशि: {self._sign_name(chandrabala.get('current_moon_sign', 0))} | "
            f"दूरी: {chandrabala.get('distance_from_natal', '-')} | "
            f"स्कोर: {chandrabala.get('chandrabala_score', '-')}"
        ) if self._is_ne else (
            f"Natal Moon: {self._sign_name(chandrabala.get('natal_moon_sign', 0))} | "
            f"Transit Moon: {self._sign_name(chandrabala.get('current_moon_sign', 0))} | "
            f"Distance: {chandrabala.get('distance_from_natal', '-')} | "
            f"Score: {chandrabala.get('chandrabala_score', '-')}"
        )
        label = QLabel(text)
        label.setWordWrap(True)
        color = COLOR_SUCCESS if chandrabala.get("is_auspicious") else COLOR_ERROR
        label.setStyleSheet(f"color: {color}; font-size: 13px; border: none;")
        inner.addWidget(label)
        return frame

    def _planet_table(self, transits: dict) -> QFrame:
        frame, inner = _section_card(
            "ग्रह गोचर विवरण (Planet Transits)" if self._is_ne else "Planet Transits", "🪐"
        )
        if not transits:
            inner.addWidget(self._muted_label("—"))
            return frame

        headers = [
            ("ग्रह (Planet)", "Planet"),
            ("राशि (Sign)", "Sign"),
            ("भाव (House)", "House"),
            ("नक्षत्र (Nakshatra)", "Nakshatra"),
            ("तारा (Tara)", "Tara"),
            ("बल (Dignity)", "Dignity"),
            ("वेध (Vedha)", "Vedha"),
            ("शुभ? (Auspicious)", "Auspicious"),
        ]
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels([h[0] if self._is_ne else h[1] for h in headers])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet(
            f"QTableWidget {{ background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; "
            f"gridline-color: {BORDER_COLOR}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; }} "
            f"QHeaderView::section {{ background: {BG_PRIMARY}; color: {COLOR_GOLD}; "
            f"font-weight: 700; padding: 6px; border: 1px solid {BORDER_COLOR}; }}"
        )

        items = list(transits.items())
        table.setRowCount(len(items))
        for row, (pname, data) in enumerate(items):
            tara = data.get("tarabala") or {}
            vedha = data.get("vedha") or {}
            dignity_key = data.get("dignity", "neutral")
            d_ne, d_en, d_color = _DIGNITY_LABELS.get(dignity_key, _DIGNITY_LABELS["neutral"])
            if self._is_ne:
                tara_label = tara.get("tara_ne", "-")
                nak_label = data.get("transit_nakshatra_ne", "-")
            else:
                tara_label = tara.get("tara_en", "-")
                nak_label = data.get("transit_nakshatra_en", "-")
            tara_color = {
                "good": COLOR_SUCCESS, "bad": COLOR_ERROR, "neutral": COLOR_TEXT_SECONDARY,
            }.get(tara.get("type", "neutral"), COLOR_TEXT_SECONDARY)

            cells = [
                (data.get("planet_ne", pname) if self._is_ne else pname, planet_color(pname)),
                (self._sign_name(data.get("transit_sign", 0)), COLOR_TEXT_PRIMARY),
                (str(data.get("transit_house", "-")), COLOR_TEXT_PRIMARY),
                (nak_label, COLOR_TEXT_SECONDARY),
                (tara_label, tara_color),
                (d_ne if self._is_ne else d_en, d_color),
                (("छ" if self._is_ne else "Yes") if vedha.get("is_vedha") else ("छैन" if self._is_ne else "No"),
                 COLOR_ERROR if vedha.get("is_vedha") else COLOR_SUCCESS),
                (("शुभ" if self._is_ne else "Yes") if data.get("overall_auspicious")
                 else ("अशुभ" if self._is_ne else "No"),
                 COLOR_SUCCESS if data.get("overall_auspicious") else COLOR_TEXT_MUTED),
            ]
            for col, (text, color) in enumerate(cells):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                table.setItem(row, col, item)

        table.setMinimumHeight(min(360, 34 * (len(items) + 1) + 8))
        inner.addWidget(table)
        return frame

    def _double_transit_card(self, triggers: list) -> QFrame:
        frame, inner = _section_card(
            "युगपत् गोचर संकेत (Double Transit Triggers)" if self._is_ne
            else "Double Transit Triggers", "🔔"
        )
        if not triggers:
            inner.addWidget(self._muted_label(
                "यस मितिमा कुनै युगपत् संकेत सक्रिय छैन।" if self._is_ne
                else "No double-transit trigger is active on this date."
            ))
            return frame
        for trig in triggers:
            strength = trig.get("strength", "")
            badge = ("बलियो" if strength == "strong" else "मध्यम") if self._is_ne \
                else ("Strong" if strength == "strong" else "Moderate")
            text = (
                f"• {trig.get('event_ne', '')} — {trig.get('description_ne', '')} "
                f"[गुरु भाव {trig.get('jupiter_house')}, शनि भाव {trig.get('saturn_house')}] ({badge})"
                if self._is_ne else
                f"• {trig.get('event_en', '')} — {trig.get('description_en', '')} "
                f"[Jupiter H{trig.get('jupiter_house')}, Saturn H{trig.get('saturn_house')}] ({badge})"
            )
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 13px; border: none;")
            inner.addWidget(label)
        return frame

    def _aspects_card(self, aspects: list) -> QFrame:
        frame, inner = _section_card(
            "गोचर दृष्टि (Transit Aspects)" if self._is_ne else "Transit Aspects", "🔭"
        )
        if not aspects:
            inner.addWidget(self._muted_label(
                "कुनै प्रमुख गोचर दृष्टि फेला परेन।" if self._is_ne
                else "No notable transit aspect was found."
            ))
            return frame
        for asp in aspects[:40]:
            if self._is_ne:
                text = (f"• {asp.get('transit_planet_ne', '')} (भाव {asp.get('transit_house')}) → "
                        f"{asp.get('natal_planet_ne', '')} (भाव {asp.get('natal_house')})")
            else:
                text = (f"• {asp.get('transit_planet', '')} (H{asp.get('transit_house')}) → "
                        f"{asp.get('natal_planet', '')} (H{asp.get('natal_house')})")
            label = QLabel(text)
            label.setWordWrap(True)
            color = COLOR_SUCCESS if asp.get("is_auspicious") else COLOR_TEXT_SECONDARY
            label.setStyleSheet(f"color: {color}; font-size: 13px; border: none;")
            inner.addWidget(label)
        return frame

    # ── Helpers ────────────────────────────────────────────────────────────
    def _sign_name(self, sign_number: Any) -> str:
        try:
            idx = int(sign_number) - 1
        except (TypeError, ValueError):
            return "-"
        if not 0 <= idx < 12:
            return "-"
        return _SIGN_NAMES_NE[idx] if self._is_ne else _SIGN_NAMES[idx]

    def _muted_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; border: none;")
        return label
