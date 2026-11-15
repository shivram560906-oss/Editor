# -*- coding: utf-8 -*-
"""Headless tests for reusable intelligent Bikram Sambat date entry."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from gui.utils.nepali_date_input import (
    BS_MONTHS,
    normalize_birth_time,
    normalize_date_query,
    resolve_month,
    to_english_digits,
    to_nepali_digits,
)
from gui.widgets.chart_input import ChartInputWidget
from gui.widgets.smart_nepali_date_dropdown import SmartNepaliDateDropdown


class NepaliDateNormalizationTests(unittest.TestCase):
    def test_english_nepali_and_mixed_numeral_conversion(self):
        cases = (
            ("2081", "2081", "२०८१"),
            ("२०८१", "2081", "२०८१"),
            ("20८१", "2081", "२०८१"),
            ("२०81", "2081", "२०८१"),
        )
        for source, english, nepali in cases:
            with self.subTest(source=source):
                self.assertEqual(to_english_digits(source), english)
                self.assertEqual(to_nepali_digits(source), nepali)

    def test_query_normalization_handles_unicode_case_digits_and_spaces(self):
        self.assertEqual(normalize_date_query("  BAISAKH\t२०81  "), "baisakh 2081")
        self.assertEqual(normalize_date_query("ＭＡＧＨ"), "magh")

    def test_birth_time_normalization_accepts_requested_flexible_formats(self):
        cases = (
            ("11 45", "11:45:00"),
            ("11;45", "11:45:00"),
            ("11:45", "11:45:00"),
            ("११ ४५", "11:45:00"),
            ("११ ४५ ००", "11:45:00"),
            ("१1;४५;३०", "11:45:30"),
            ("  7   5  ", "07:05:00"),
        )
        for typed, expected in cases:
            with self.subTest(typed=typed):
                self.assertEqual(normalize_birth_time(typed), expected)

    def test_birth_time_normalization_rejects_invalid_values(self):
        for typed in ("", "11", "24 00", "11 60", "11 45 60", "11-45", "a b"):
            with self.subTest(typed=typed):
                self.assertIsNone(normalize_birth_time(typed))

    def test_every_month_numeric_name_and_alias_resolves_exactly(self):
        self.assertEqual(len(BS_MONTHS), 12)
        for month in BS_MONTHS:
            value = month["value"]
            inputs = (
                str(value),
                to_nepali_digits(value),
                month["display"],
                *month["aliases"],
            )
            for query in inputs:
                with self.subTest(month=value, query=query):
                    self.assertEqual(resolve_month(query), value)

    def test_month_partial_resolution_requires_one_unique_month(self):
        self.assertEqual(resolve_month("baisha", allow_partial=True), 1)
        self.assertEqual(resolve_month("marg", allow_partial=True), 8)
        self.assertIsNone(resolve_month("a", allow_partial=True))
        self.assertIsNone(resolve_month("15", allow_partial=True))


class SmartNepaliDateDropdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def assert_commits(self, combo, typed, expected_value, expected_text):
        combo.lineEdit().setText(typed)
        self.assertTrue(combo.commit_text())
        self.assertTrue(combo.isValid())
        self.assertEqual(combo.value(), expected_value)
        self.assertEqual(combo.currentData(), expected_value)
        self.assertEqual(combo.currentText(), expected_text)
        self.assertNotIn("#dc2626", combo.styleSheet())

    def test_year_accepts_english_nepali_and_mixed_digits(self):
        combo = SmartNepaliDateDropdown("year", 1970, 2099)
        for typed in ("2081", "२०८१", "20८१", "२०81"):
            with self.subTest(typed=typed):
                self.assert_commits(combo, typed, 2081, "२०८१")

    def test_day_accepts_both_scripts_and_preserves_valid_bs_day_32(self):
        combo = SmartNepaliDateDropdown("day", 1, 32)
        cases = (
            ("1", 1, "१"),
            ("१", 1, "१"),
            ("25", 25, "२५"),
            ("२५", 25, "२५"),
            ("31", 31, "३१"),
            ("३१", 31, "३१"),
            ("3२", 32, "३२"),
        )
        for typed, value, display in cases:
            with self.subTest(typed=typed):
                self.assert_commits(combo, typed, value, display)

    def test_all_month_inputs_commit_to_canonical_nepali_and_integer_data(self):
        combo = SmartNepaliDateDropdown("month")
        for month in BS_MONTHS:
            value = month["value"]
            inputs = (
                str(value),
                to_nepali_digits(value),
                month["display"],
                *month["aliases"],
            )
            for typed in inputs:
                with self.subTest(month=value, typed=typed):
                    self.assert_commits(
                        combo, typed, value, month["display"]
                    )

    def test_exact_match_wins_and_partial_filter_shows_canonical_items(self):
        combo = SmartNepaliDateDropdown("month")
        combo._filter_from_text("1")
        self.assertEqual(combo.count(), 1)
        self.assertEqual(combo.itemData(0), 1)
        self.assertEqual(combo.itemText(0), BS_MONTHS[0]["display"])

        combo._filter_from_text("a")
        values = [combo.itemData(index) for index in range(combo.count())]
        labels = [combo.itemText(index) for index in range(combo.count())]
        self.assertGreater(len(values), 1)
        self.assertEqual(labels, [BS_MONTHS[value - 1]["display"] for value in values])
        self.assertFalse(combo.commit_text())

        self.assert_commits(combo, "baisha", 1, "बैशाख")

    def test_year_partial_filter_does_not_auto_commit_ambiguous_input(self):
        combo = SmartNepaliDateDropdown("year", 1970, 2099)
        combo._filter_from_text("208")
        self.assertEqual(combo.count(), 10)
        self.assertEqual(combo.itemText(0), "२०८०")
        self.assertEqual(combo.itemText(9), "२०८९")
        self.assertFalse(combo.commit_text())
        self.assertEqual(combo.value(), 0)

    def test_year_keystrokes_preserve_the_query_and_filter_until_four_digits(self):
        combo = SmartNepaliDateDropdown("year", 1970, 2099)
        combo.show()
        combo.lineEdit().setFocus()
        combo.lineEdit().selectAll()

        expected = (
            ("2", 100),
            ("20", 100),
            ("208", 10),
            ("2081", 1),
        )
        for digit, (text, count) in zip("2081", expected):
            QTest.keyClicks(combo.lineEdit(), digit)
            self.app.processEvents()
            self.assertEqual(combo.currentText(), text)
            self.assertEqual(combo.lineEdit().cursorPosition(), len(text))
            self.assertEqual(combo.count(), count)

        self.assertEqual(combo.itemData(0), 2081)
        self.assertTrue(combo.commit_text())
        self.assertEqual(combo.currentText(), "२०८१")
        combo.close()

    def test_day_keystrokes_preserve_the_query_and_filter_until_two_digits(self):
        combo = SmartNepaliDateDropdown("day", 1, 32)
        combo.show()
        combo.lineEdit().setFocus()
        combo.lineEdit().selectAll()

        QTest.keyClicks(combo.lineEdit(), "2")
        self.app.processEvents()
        self.assertEqual(combo.currentText(), "2")
        self.assertEqual(
            [combo.itemData(index) for index in range(combo.count())],
            [2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
        )

        QTest.keyClicks(combo.lineEdit(), "5")
        self.app.processEvents()
        self.assertEqual(combo.currentText(), "25")
        self.assertEqual(combo.lineEdit().cursorPosition(), 2)
        self.assertEqual(combo.count(), 1)
        self.assertEqual(combo.itemData(0), 25)
        self.assertTrue(combo.commit_text())
        self.assertEqual(combo.currentText(), "२५")
        combo.close()

    def test_first_digit_replaces_initialized_value_after_focus(self):
        combo = SmartNepaliDateDropdown("year", 1970, 2099)
        combo.show()
        self.app.processEvents()
        QTest.mouseClick(combo.lineEdit(), Qt.LeftButton)
        self.app.processEvents()

        QTest.keyClicks(combo.lineEdit(), "2")
        self.app.processEvents()
        self.assertEqual(combo.currentText(), "2")
        self.assertEqual(combo.lineEdit().cursorPosition(), 1)
        self.assertEqual(combo.count(), 100)
        combo.close()

    def test_invalid_values_are_rejected_and_highlighted(self):
        cases = (
            ("year", 1970, 2099, "99999"),
            ("month", 1, 12, "15"),
            ("day", 1, 32, "45"),
        )
        for part, minimum, maximum, typed in cases:
            with self.subTest(part=part, typed=typed):
                combo = SmartNepaliDateDropdown(part, minimum, maximum)
                combo.lineEdit().setText(typed)
                self.assertFalse(combo.commit_text())
                self.assertFalse(combo.isValid())
                self.assertEqual(combo.value(), 0)
                self.assertIn("#dc2626", combo.styleSheet())


class SmartNepaliDateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_invalid_bs_control_prevents_backend_date_conversion(self):
        widget = ChartInputWidget(language="en")
        widget._calendar_mode = "BS"
        widget._ad_verification_label.setText("AD Date: stale")
        widget._bs_year.lineEdit().setText("99999")
        widget._bs_month.setValue(1)
        widget._bs_day.setValue(1)

        with patch("gui.widgets.chart_input.convert_bs_to_ad") as converter:
            widget._sync_bs_to_ad()

        converter.assert_not_called()
        self.assertEqual(widget._ad_verification_label.text(), "")

    def test_valid_bs_controls_pass_standardized_integers_to_backend(self):
        widget = ChartInputWidget(language="en")
        widget._calendar_mode = "AD"
        widget._bs_year.lineEdit().setText("२०81")
        self.assertTrue(widget._bs_year.commit_text())
        widget._bs_month.lineEdit().setText("Baishakh")
        self.assertTrue(widget._bs_month.commit_text())
        widget._bs_day.lineEdit().setText("2५")
        self.assertTrue(widget._bs_day.commit_text())
        widget._calendar_mode = "BS"

        with patch(
            "gui.widgets.chart_input.convert_bs_to_ad",
            return_value={"year": 2024, "month": 5, "day": 7},
        ) as converter:
            widget._sync_bs_to_ad()

        converter.assert_called_once_with(2081, 1, 25)
        self.assertEqual(widget._ad_date_edit.text(), "2024-05-07")
        self.assertEqual(
            widget._ad_verification_label.text(),
            "AD Date: 2024-05-07",
        )

    def test_ad_verification_label_is_black_and_beside_birth_time(self):
        widget = ChartInputWidget(language="en")
        widget.show()
        self.app.processEvents()

        self.assertIn("color: #111111", widget._ad_verification_label.styleSheet())
        self.assertEqual(widget._time_edit.y(), widget._ad_verification_label.y())
        self.assertGreater(widget._ad_verification_label.x(), widget._time_edit.x())

        widget._btn_ad.setChecked(True)
        widget._on_calendar_mode_changed(widget._btn_ad)
        self.assertEqual(widget._ad_verification_label.text(), "")
        widget.close()

    def test_time_field_normalizes_display_on_commit(self):
        widget = ChartInputWidget(language="en")
        cases = (
            ("11 45", "11:45"),
            ("11;45", "11:45"),
            ("११ ४५", "11:45"),
            ("११ ४५ ००", "11:45"),
            ("११ ४५ ३०", "11:45:30"),
        )
        for typed, display in cases:
            with self.subTest(typed=typed):
                widget._time_edit.setText(typed)
                self.assertTrue(widget._normalize_time_field())
                self.assertEqual(widget._time_edit.text(), display)

        widget._time_edit.setText("25 45")
        self.assertFalse(widget._normalize_time_field())
        self.assertEqual(widget._time_edit.text(), "25 45")


if __name__ == "__main__":
    unittest.main()
