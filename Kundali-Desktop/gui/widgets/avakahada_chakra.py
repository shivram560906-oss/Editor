# -*- coding: utf-8 -*-
"""Native Avakahada Chakra report backed by the calculated chart payload."""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.theme import (
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER_COLOR,
    COLOR_ACCENT,
    COLOR_ERROR,
    COLOR_GOLD,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)

UNAVAILABLE = "—"

_FIELD_GROUPS = (
    (
        ("nakshatra", "Nakshatra", "नक्षत्र"),
        ("pada", "Pada", "पाद"),
        ("rashi", "Rashi", "राशि"),
        ("rashi_lord", "Rashi Lord", "राशि स्वामी"),
        ("name_akshara", "Name Akshara", "नाम अक्षर"),
    ),
    (
        ("yoni", "Yoni", "योनि"),
        ("viryoni", "Vair Yoni", "वैर योनि"),
        ("gana", "Gana", "गण"),
        ("nadi", "Nadi", "नाडी"),
    ),
    (
        ("varna", "Varna", "वर्ण"),
        ("vashya", "Vashya", "वश्य"),
        ("varga", "Varga", "वर्ग"),
        ("shatru_varga", "Shatru Varga", "शत्रु वर्ग"),
    ),
    (
        ("asana", "Asana", "आसन"),
    ),
)

_METADATA_FIELDS = (
    ("birth_date", "Birth Date", "जन्म मिति"),
    ("birth_time", "Birth Time", "जन्म समय"),
    ("birth_place", "Birth Place", "जन्म स्थान"),
)


def _display(value: Any) -> str:
    if value is None or value == "":
        return UNAVAILABLE
    if isinstance(value, (dict, list, tuple, set)):
        return UNAVAILABLE
    return str(value)


def _nakshatra_name(data: dict, chakra: dict, language: str) -> str:
    panchang = data.get("panchang")
    if isinstance(panchang, dict):
        nakshatra = panchang.get("nakshatra")
        if isinstance(nakshatra, dict):
            preferred = "nepali" if language == "ne" else "name"
            value = nakshatra.get(preferred) or nakshatra.get("name") or nakshatra.get("nepali")
            if value not in (None, ""):
                return _display(value)
    return _display(chakra.get("nakshatra"))


def build_avakahada_model(data: Optional[dict], language: str = "ne") -> dict:
    """Normalize the existing backend payload for deterministic native rendering."""
    is_ne = language == "ne"
    if data is None or data == {}:
        return {
            "state": "no_chart",
            "message": "कृपया पहिले कुण्डली गणना गर्नुहोस्।" if is_ne else "Please calculate a chart first.",
            "rows": [],
            "groups": [],
        }
    if not isinstance(data, dict):
        return {
            "state": "error",
            "message": "अवकहडा विवरण पढ्न सकिएन।" if is_ne else "The Avakahada payload could not be read.",
            "rows": [],
            "groups": [],
        }
    if data.get("error"):
        return {
            "state": "error",
            "message": _display(data.get("error")),
            "rows": [],
            "groups": [],
        }

    chakra = data.get("avakahada_chakra")
    if chakra is None or chakra == {}:
        return {
            "state": "empty",
            "message": "यस कुण्डलीमा अवकहडा विवरण उपलब्ध छैन।" if is_ne else "Avakahada data is not available for this chart.",
            "rows": [],
            "groups": [],
        }
    if not isinstance(chakra, dict):
        return {
            "state": "error",
            "message": "अवकहडा विवरणको ढाँचा अमान्य छ।" if is_ne else "The Avakahada payload has an invalid format.",
            "rows": [],
            "groups": [],
        }

    panchang = data.get("panchang")
    if isinstance(panchang, dict) and (chakra.get("rashi") in (None, "", UNAVAILABLE) or chakra.get("name_akshara") in (None, "", UNAVAILABLE)):
        nak = panchang.get("nakshatra")
        if isinstance(nak, dict):
            nak_idx = nak.get("index")
            pada_val = nak.get("pada") or 1
            nak_name = nak.get("nepali") or nak.get("name")
            if nak_idx is not None:
                try:
                    from backend.calculator.avakahada_chakra import calculate_avakahada_chakra
                    computed = calculate_avakahada_chakra(nak_idx, pada_val, nakshatra_name=nak_name)
                    chakra = {**computed, **chakra}
                except Exception:
                    pass


    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    birth_place = metadata.get("city") or metadata.get("birth_place")
    metadata_values = {
        "birth_date": metadata.get("birth_date"),
        "birth_time": metadata.get("birth_time"),
        "birth_place": birth_place,
    }
    field_values = {key: chakra.get(key) for group in _FIELD_GROUPS for key, _, _ in group}
    field_values["nakshatra"] = _nakshatra_name(data, chakra, language)

    rows = []
    for key, en, ne in _METADATA_FIELDS:
        rows.append({"key": key, "label": ne if is_ne else en, "value": _display(metadata_values[key])})
    for group in _FIELD_GROUPS:
        for key, en, ne in group:
            rows.append({"key": key, "label": ne if is_ne else en, "value": _display(field_values[key])})

    groups = []
    for group in _FIELD_GROUPS:
        groups.append([
            {"key": key, "label": ne if is_ne else en, "value": _display(field_values[key])}
            for key, en, ne in group
        ])

    missing = [row["key"] for row in rows[3:] if row["value"] == UNAVAILABLE]
    return {
        "state": "incomplete" if missing else "ready",
        "message": (
            "केही अवकहडा मानहरू उपलब्ध छैनन्।" if is_ne else "Some Avakahada values are unavailable."
        ) if missing else "",
        "rows": rows,
        "groups": groups,
        "missing": missing,
    }


def compose_avakahada_text(model: dict) -> str:
    """Return the Web-compatible Label: Value clipboard representation."""
    return "\n".join(f"{row['label']}: {row['value']}" for row in model.get("rows", []))


class AvakahadaChakraPage(QWidget):
    """Scrollable native report for the backend-produced Avakahada Chakra."""

    def __init__(self, data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._language = language
        self._model: dict = {}
        self._build_ui()
        self.refresh(data)

    @property
    def report_text(self) -> str:
        return compose_avakahada_text(self._model)

    @property
    def state(self) -> str:
        return self._model.get("state", "error")

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("अवकहडा चक्र" if self._language == "ne" else "Avakahada Chakra")
        title.setObjectName("avakahadaTitle")
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch(1)
        self._copy_button = QPushButton("प्रतिलिपि" if self._language == "ne" else "Copy")
        self._copy_button.setToolTip("विवरण प्रतिलिपि गर्नुहोस्" if self._language == "ne" else "Copy report")
        self._copy_button.clicked.connect(self.copy_report)
        header.addWidget(self._copy_button)
        root.addLayout(header)

        meaning = QLabel(
            "हाल खोलिएको जन्म कुण्डलीको जन्मकालीन नक्षत्र र पादमा आधारित विवरण।"
            if self._language == "ne"
            else "Based on the birth nakshatra and pada of the currently opened chart."
        )
        meaning.setWordWrap(True)
        meaning.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        root.addWidget(meaning)

        self._state_label = QLabel()
        self._state_label.setObjectName("avakahadaState")
        self._state_label.setWordWrap(True)
        self._state_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self._state_label)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._content = QVBoxLayout(self._container)
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(10)
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll, 1)

    def _clear_content(self) -> None:
        while self._content.count():
            item = self._content.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _field_card(self, row: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("avakahadaField")
        card.setStyleSheet(
            f"QFrame#avakahadaField {{ background: {BG_TERTIARY}; border: 1px solid {BORDER_COLOR}; "
            "border-radius: 6px; }}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        label = QLabel(row["label"])
        label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        value = QLabel(row["value"])
        value.setObjectName(f"avakahadaValue_{row['key']}")
        value.setWordWrap(True)
        value.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: 700;")
        layout.addWidget(label)
        layout.addWidget(value)
        return card

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_avakahada_model(data, self._language)
        self._clear_content()
        state = self._model["state"]
        message = self._model.get("message", "")
        self._copy_button.setEnabled(bool(self._model.get("rows")))
        self._scroll.setVisible(bool(self._model.get("groups")))
        self._state_label.setVisible(bool(message))
        self._state_label.setText(message)
        self._state_label.setStyleSheet(
            f"background: {BG_SECONDARY}; border: 1px solid {COLOR_ERROR if state == 'error' else BORDER_COLOR}; "
            f"border-radius: 6px; color: {COLOR_ERROR if state == 'error' else COLOR_TEXT_SECONDARY}; padding: 10px;"
        )

        for group_index, group in enumerate(self._model.get("groups", [])):
            section = QFrame()
            section.setObjectName("avakahadaGroup")
            section.setStyleSheet(
                f"QFrame#avakahadaGroup {{ background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; "
                "border-radius: 6px; }}"
            )
            grid = QGridLayout(section)
            grid.setContentsMargins(10, 10, 10, 10)
            grid.setSpacing(8)
            for index, row in enumerate(group):
                grid.addWidget(self._field_card(row), index // 2, index % 2)
            self._content.addWidget(section)
        self._content.addStretch(1)

    def copy_report(self) -> None:
        if self.report_text:
            QApplication.clipboard().setText(self.report_text)
