# -*- coding: utf-8 -*-
"""Unit tests to verify file loading and form reset on Boy and Girl panels."""
import unittest
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from gui.widgets.marriage_matching_widget import MarriageMatchingWidget, PersonChartInputPanel


class MarriageMatchingLoadResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_girl_panel_load_from_dict_populates_all_fields(self):
        page = MarriageMatchingWidget("ne")
        girl_panel = page._girl_panel

        girl_data = {
            "name": "अनिता अधिकारी",
            "gender": 1,
            "birth_date": "2003-08-25",
            "birth_time": "14:45:30",
            "country": "Nepal",
            "region": "Gandaki",
            "district": "Kaski",
            "city": "Pokhara",
            "latitude": 28.2096,
            "longitude": 83.9856,
            "timezone": 5.75,
        }
        girl_panel.load_from_dict(girl_data)

        self.assertEqual(girl_panel._name_edit.text(), "अनिता अधिकारी")
        self.assertTrue(girl_panel._rb_female.isChecked())
        self.assertEqual(girl_panel._ad_edit.text(), "2003-08-25")
        self.assertEqual(girl_panel._time_edit.text(), "14:45:30")
        self.assertEqual(girl_panel._dist_cb.currentData(), "Kaski")
        self.assertEqual(girl_panel._city_cb.currentText(), "Pokhara")
        self.assertAlmostEqual(float(girl_panel._lat_edit.text()), 28.2096, places=3)
        self.assertAlmostEqual(float(girl_panel._lon_edit.text()), 83.9856, places=3)
        # Verify BS dropdowns also got synced
        self.assertGreater(girl_panel._bs_year_cb.value(), 2050)

    def test_reset_form_clears_fields_separately(self):
        page = MarriageMatchingWidget("ne")
        boy_panel = page._boy_panel
        girl_panel = page._girl_panel

        boy_panel._name_edit.setText("राम")
        girl_panel._name_edit.setText("सीता")

        # Reset boy panel only
        boy_panel.reset_form()
        self.assertEqual(boy_panel._name_edit.text(), "")
        # Girl panel remains intact
        self.assertEqual(girl_panel._name_edit.text(), "सीता")

        # Reset girl panel
        girl_panel.reset_form()
        self.assertEqual(girl_panel._name_edit.text(), "")


if __name__ == "__main__":
    unittest.main()
