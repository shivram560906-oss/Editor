"""Reusable searchable dropdowns for canonical Nepali BS date entry."""
from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QComboBox

from gui.utils.nepali_date_input import (
    BS_MONTHS,
    month_search_terms,
    normalize_date_query,
    resolve_month,
    to_english_digits,
    to_nepali_digits,
)

DatePart = Literal["year", "month", "day"]


class SmartNepaliDateDropdown(QComboBox):
    """Editable BS date selector with canonical Nepali display and numeric data."""

    valueChanged = Signal(int)

    def __init__(
        self,
        part: DatePart,
        minimum: int | None = None,
        maximum: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._part = part
        self._minimum = minimum if minimum is not None else (1970 if part == "year" else 1)
        self._maximum = maximum if maximum is not None else (
            2099 if part == "year" else 32 if part == "day" else 12
        )
        self._options = self._build_options()
        self._committed_value: int | None = None
        self._filtering = False
        self._replace_on_next_input = False

        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(14)
        # Qt's default completer can replace the in-progress numeric query
        # while the filtered item model is being rebuilt.
        self.lineEdit().setCompleter(None)
        self.lineEdit().installEventFilter(self)
        self.lineEdit().textEdited.connect(self._filter_from_text)
        self.lineEdit().returnPressed.connect(self.commit_text)
        self.activated.connect(self._commit_selected_index)
        self._show_options(self._options)
        if self._options:
            self.setValue(self._options[0][0])

    def _build_options(self) -> list[tuple[int, str, tuple[str, ...]]]:
        if self._part == "month":
            return [
                (month["value"], month["display"], month_search_terms(month))
                for month in BS_MONTHS
            ]
        return [
            (value, to_nepali_digits(value), (str(value),))
            for value in range(self._minimum, self._maximum + 1)
        ]

    def _matches(self, query: str) -> list[tuple[int, str, tuple[str, ...]]]:
        if not query:
            return self._options
        if self._part != "month":
            return [
                option
                for option in self._options
                if any(term.startswith(query) for term in option[2])
            ]
        exact = [option for option in self._options if query in option[2]]
        if exact:
            return exact
        return [
            option
            for option in self._options
            if any(term.startswith(query) or query in term for term in option[2])
        ]

    def _show_options(
        self,
        options: list[tuple[int, str, tuple[str, ...]]],
        typed_text: str | None = None,
    ) -> None:
        self._filtering = True
        self.blockSignals(True)
        self.clear()
        for value, display, _terms in options:
            self.addItem(display, value)
        self.setCurrentIndex(-1)
        if typed_text is not None:
            self.lineEdit().setText(typed_text)
            # Rebuilding a QComboBox model resets the edit cursor. Keep it at
            # the end so the next digit continues the same query.
            self.lineEdit().setCursorPosition(len(typed_text))
        self.blockSignals(False)
        self._filtering = False

    def _filter_from_text(self, text: str) -> None:
        query = normalize_date_query(text)
        matches = self._matches(query)
        self._show_options(matches, text)
        self._set_invalid(False)
        if len(matches) > 1 and self.lineEdit().hasFocus():
            self.showPopup()
        else:
            self.hidePopup()

    def _resolve(self, text: str, allow_partial: bool = True) -> int | None:
        query = normalize_date_query(text)
        if not query:
            return None
        if self._part == "month":
            return resolve_month(query, allow_partial=allow_partial)
        numeric = to_english_digits(query)
        if not numeric.isdigit():
            return None
        value = int(numeric)
        return value if self._minimum <= value <= self._maximum else None

    def commit_text(self) -> bool:
        """Resolve typed text and replace it with canonical Nepali display."""
        value = self._resolve(self.currentText(), allow_partial=True)
        if value is None:
            self._set_invalid(True)
            return False
        self.setValue(value)
        return True

    def _commit_selected_index(self, index: int) -> None:
        value = self.itemData(index)
        if isinstance(value, int):
            self.setValue(value)

    def setValue(self, value: int) -> None:
        """Select a standardized numeric value and display canonical Nepali text."""
        option = next((item for item in self._options if item[0] == int(value)), None)
        if option is None:
            self._set_invalid(True)
            return
        changed = self._committed_value != option[0]
        self._show_options(self._options)
        index = self.findData(option[0])
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.lineEdit().setText(option[1])
        self.blockSignals(False)
        self._committed_value = option[0]
        self._replace_on_next_input = False
        self._set_invalid(False)
        if changed:
            self.valueChanged.emit(option[0])

    def value(self) -> int:
        """Return the standardized numeric value, or zero for invalid text."""
        resolved = self._resolve(self.currentText(), allow_partial=False)
        return resolved if resolved is not None else 0

    def isValid(self) -> bool:
        return self._resolve(self.currentText(), allow_partial=False) is not None

    def eventFilter(self, watched, event) -> bool:
        if watched is self.lineEdit():
            if event.type() in (QEvent.FocusIn, QEvent.MouseButtonPress):
                self._replace_on_next_input = True
            elif event.type() == QEvent.KeyPress and self._replace_on_next_input:
                modifiers = event.modifiers()
                has_text = bool(event.text())
                uses_shortcut_modifier = bool(
                    modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)
                )
                if has_text and not uses_shortcut_modifier:
                    # The initial value is a committed display value. Clear it
                    # before Qt inserts the first character, regardless of the
                    # cursor position produced by the preceding mouse click.
                    self.lineEdit().clear()
                    self._replace_on_next_input = False
        return super().eventFilter(watched, event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.commit_text()
        super().focusOutEvent(event)

    def _set_invalid(self, invalid: bool) -> None:
        border = "#dc2626" if invalid else "#9ca3af"
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: #111111;
                border: 1px solid {border};
                padding: 2px 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                color: #111111;
                selection-background-color: #1d4ed8;
                selection-color: #ffffff;
                border: 1px solid #4b5563;
            }}
        """)
