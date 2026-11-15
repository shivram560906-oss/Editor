# -*- coding: utf-8 -*-
"""Headless regression tests for the Research & Tools pages."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.widgets.tools_widget import MarriageMatchingPage, MuhurtaPage, PrashnaChartPage
from gui.widgets.marriage_matching_widget import MarriageMatchingWidget


class ToolsWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_marriage_matching_renders_calculated_score(self):
        """New widget: status shows success message after mocked calculate."""
        page = MarriageMatchingWidget("ne")
        page._boy_panel._name_edit.setText("राम शर्मा")
        page._boy_panel._ad_edit.setText("2000-01-01")
        page._girl_panel._name_edit.setText("सीता श्रेष्ठ")
        page._girl_panel._ad_edit.setText("2002-05-15")
        # Mock calculate_marriage_match and calculate_chart
        compat = {
            "ashtakoot": {
                "total_score": 28, "max_score": 36, "compatibility": "उत्तम (Excellent)",
                "varna": 1, "vasya": 2, "tara": 3, "yoni": 4, "grah_maitri": 5,
                "gana": 6, "bhakut": 0, "nadi": 7,
                "boy_moon_sign": 4, "girl_moon_sign": 7,
                "bhakut_mahadosh": False, "bhakut_mahadosh_note": "",
                "details": {"varna_detail": {"boy": "ब्राह्मण", "girl": "क्षत्रिय"}},
            },
            "recommendation": "विवाह गर्न योग्य छ",
            "mangal_dosh_note": "",
            "boy_mangal_dosh":  {"has_mangal_dosh": False, "mars_house": 5, "cancellation_possible": False},
            "girl_mangal_dosh": {"has_mangal_dosh": False, "mars_house": 3, "cancellation_possible": False},
        }
        empty_chart = {"planets": [], "lagna": {"sign_number": 1}}
        with patch("gui.backend_bridge.calculate_marriage_match", return_value={"compatibility": compat}), \
             patch("gui.backend_bridge.calculate_chart", return_value=empty_chart):
            page._calculate()
        self.assertIn("सम्पन्न", page._status.text())

    def test_marriage_matching_reports_backend_errors(self):
        """New widget: status shows error message on exception."""
        page = MarriageMatchingWidget("ne")
        page._boy_panel._name_edit.setText("राम शर्मा")
        page._boy_panel._ad_edit.setText("2000-01-01")
        page._girl_panel._name_edit.setText("सीता श्रेष्ठ")
        page._girl_panel._ad_edit.setText("2002-05-15")
        with patch("gui.backend_bridge.calculate_marriage_match", side_effect=ValueError("invalid birth date")):
            page._calculate()
        self.assertIn("invalid birth date", page._status.text())


    def test_prashna_chart_page_initialization_and_category_selection(self):
        sample_chart = {
            "lagna": {"sign_number": 4},
            "planets": [{"name": "Moon", "sign_number": 4, "longitude": 100.0, "house": 1}],
        }
        page = PrashnaChartPage("ne", data=sample_chart)
        self.assertIsNotNone(page._cat_combo)
        self.assertGreater(page._cat_combo.count(), 0)
        self.assertIsNotNone(page._question_combo)
        self.assertGreater(page._question_combo.count(), 0)
        page._on_category_changed(0)
        page._on_question_changed(0)
        self.assertIsNotNone(page._report_layout)

    def test_prashna_search_filters_questions(self):
        page = PrashnaChartPage("ne", data={})
        page._search_input.setText("विवाह")
        page._on_search_text_changed("विवाह")
        self.assertFalse(page._suggest_list.isHidden())
        self.assertGreater(page._suggest_list.count(), 0)

    def test_muhurta_populates_day_and_night_rows(self):
        page = MuhurtaPage("en")
        result = {
            "choghadiya_day": [{"name": {"en": "Amrit"}, "start": "06:00", "end": "07:30"}],
            "choghadiya_night": [{"name": {"en": "Shubh"}, "start": "18:00", "end": "19:30"}],
            "hora_day": [{"lord": {"en": "Sun"}, "start": "06:00", "end": "07:00"}],
            "hora_night": [{"lord": {"en": "Moon"}, "start": "18:00", "end": "19:00"}],
            "kaals": {"rahu": {"start": "10:30", "end": "12:00"}},
        }
        with patch("gui.backend_bridge.calculate_muhurta", return_value=result):
            page.calculate()
        self.assertEqual(page._result.rowCount(), 5)
        self.assertEqual(page._result.item(0, 0).text(), "Amrit")
        self.assertEqual(page._result.item(1, 2).text(), "19:30")
        self.assertEqual(page._result.item(2, 0).text(), "Sun")
        self.assertEqual(page._result.item(4, 0).text(), "Rahu")
        self.assertEqual(page._state.text(), "Result ready.")

    def test_muhurta_clears_stale_rows_on_error(self):
        page = MuhurtaPage("en")
        page._result.setRowCount(1)
        with patch("gui.backend_bridge.calculate_muhurta", side_effect=RuntimeError("No sunrise data")):
            page.calculate()
        self.assertEqual(page._result.rowCount(), 0)
        self.assertIn("No sunrise data", page._state.text())


if __name__ == "__main__":
    unittest.main()
