# -*- coding: utf-8 -*-
"""
gui/widgets/ayanamsha_comparator_page.py

Ayanamsha Comparator Widget (Phase 1 accuracy tool).

Compares every supported Swiss-Ephemeris ayanamsha system at a chosen
reference date and shows how each system shifts the sidereal ascendant
(lagna) degree and sign. This makes the accuracy of the active ayanamsha
visibly verifiable against the alternatives.

All calculations run synchronously and defensively: an un-joined QThread is
never created, matching the native crash-avoidance contract used by the other
report pages.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QPushButton,
)

from gui.theme import (
    COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_SUCCESS,
)

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


class AyanamshaComparatorPage(QWidget):
    """Side-by-side ayanamsha comparison for a chosen reference date."""

    def __init__(self, data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._result: Optional[Dict[str, Any]] = None
        self._build_ui()
        self._compute()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QLabel(
            "🕉️ अयनांश तुलना (Ayanamsha Comparator)" if self._is_ne
            else "🕉️ Ayanamsha Comparator"
        )
        header.setStyleSheet(
            f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 900; "
            f"padding: 12px 16px; background: {BG_TERTIARY};"
        )
        root.addWidget(header)

        controls = QHBoxLayout()
        controls.setContentsMargins(16, 10, 16, 6)
        controls.setSpacing(10)

        date_label = QLabel("सन्दर्भ मिति:" if self._is_ne else "Reference date:")
        date_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        controls.addWidget(date_label)

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.dateChanged.connect(lambda _d: self._compute())
        controls.addWidget(self._date_edit)

        self._compute_btn = QPushButton("गणना गर्नुहोस्" if self._is_ne else "Compute")
        self._compute_btn.clicked.connect(self._compute)
        controls.addWidget(self._compute_btn)

        controls.addStretch(1)
        root.addLayout(controls)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(16, 8, 16, 16)
        self._body_layout.setSpacing(12)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

    # ── Computation ────────────────────────────────────────────────────────
    def _selected_date(self) -> str:
        qdate = self._date_edit.date()
        return f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"

    def _compute(self) -> None:
        try:
            from gui.backend_bridge import calculate_ayanamsha_comparison
            self._result = calculate_ayanamsha_comparison(reference_date=self._selected_date())
        except Exception as exc:  # pragma: no cover - defensive
            self._result = None
            self._render_message(
                f"गणना असफल भयो: {exc}" if self._is_ne else f"Comparison failed: {exc}",
                COLOR_TEXT_MUTED,
            )
            return
        self._render()

    # ── Rendering ──────────────────────────────────────────────────────────
    def _render_message(self, text: str, color: str) -> None:
        _clear_layout(self._body_layout)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {color}; font-size: 13px;")
        self._body_layout.addWidget(label)
        self._body_layout.addStretch(1)

    def _render(self) -> None:
        _clear_layout(self._body_layout)
        result = self._result or {}
        systems = result.get("systems") or []
        if not systems:
            self._render_message(
                "अयनांश डेटा उपलब्ध छैन।" if self._is_ne
                else "No ayanamsha data available.",
                COLOR_TEXT_MUTED,
            )
            return

        self._body_layout.addWidget(self._summary_card(result))
        self._body_layout.addWidget(self._table_card(systems))
        self._body_layout.addStretch(1)

    def _summary_card(self, result: dict) -> QFrame:
        frame, inner = _section_card(
            "सन्दर्भ जानकारी (Reference)" if self._is_ne else "Reference", "📅"
        )
        lagna_tropical = float(result.get("lagna_tropical", 0) or 0)
        sign_idx = int(lagna_tropical / 30.0) % 12
        sign_name = (_SIGN_NAMES_NE if self._is_ne else _SIGN_NAMES)[sign_idx]

        rows = [
            ("सन्दर्भ मिति (Date)", result.get("reference_date", "—")),
            ("स्थान (Location)", f"{result.get('latitude')}°, {result.get('longitude')}°"),
            ("समय क्षेत्र (Timezone)", f"UTC{float(result.get('timezone', 0) or 0):+.2f}"),
            ("Julian Day", f"{float(result.get('julian_day', 0) or 0):.5f}"),
            ("सायन लग्न (Tropical Lagna)", f"{lagna_tropical:.4f}°  ({sign_name})"),
        ]
        for label, value in rows:
            row = QHBoxLayout()
            name = QLabel(f"{label}:")
            name.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; border: none;")
            name.setFixedWidth(220)
            val = QLabel(str(value))
            val.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; border: none;")
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row.addWidget(name)
            row.addWidget(val, 1)
            inner.addLayout(row)
        return frame

    def _table_card(self, systems: list) -> QFrame:
        frame, inner = _section_card(
            "प्रणाली अनुसार अयनांश (Per-System Values)" if self._is_ne
            else "Per-System Values",
            "📊",
        )
        headers = [
            "प्रणाली (System)" if self._is_ne else "System",
            "अयनांश (°)" if self._is_ne else "Ayanamsha (°)",
            "निरयन लग्न (°)" if self._is_ne else "Sidereal Lagna (°)",
            "लग्न राशि (Lagna Sign)" if self._is_ne else "Lagna Sign",
        ]
        table = QTableWidget(len(systems), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setStyleSheet(
            f"QTableWidget {{ background: {BG_TERTIARY}; color: {COLOR_TEXT_PRIMARY}; "
            f"gridline-color: {BORDER_COLOR}; border: none; }}"
            f"QHeaderView::section {{ background: {BG_SECONDARY}; color: {COLOR_GOLD}; "
            f"padding: 6px; border: none; font-weight: 700; }}"
        )
        default_system = str(self._result.get("default_system", "LAHIRI")) if self._result else "LAHIRI"

        for row_idx, entry in enumerate(systems):
            sign_idx = int(entry.get("lagna_sign", 1)) - 1
            sign_name = (_SIGN_NAMES_NE if self._is_ne else _SIGN_NAMES)[sign_idx % 12]
            cells = [
                str(entry.get("code", "")),
                f"{float(entry.get('ayanamsha', 0) or 0):.4f}",
                f"{float(entry.get('lagna_sidereal', 0) or 0):.4f}",
                f"{sign_name} ({entry.get('lagna_sign')})",
            ]
            is_default = str(entry.get("code")) == default_system
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemIsEnabled)
                if is_default:
                    item.setForeground(QBrush(QColor(COLOR_SUCCESS)))
                elif col == 0:
                    item.setForeground(QBrush(QColor(COLOR_ACCENT)))
                table.setItem(row_idx, col, item)

        table.resizeColumnsToContents()
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        inner.addWidget(table)

        note = QLabel(
            "हरियो पङ्क्ति = सक्रिय मानक अयनांश।" if self._is_ne
            else "Green row = active standard ayanamsha."
        )
        note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; border: none;")
        inner.addWidget(note)
        return frame
