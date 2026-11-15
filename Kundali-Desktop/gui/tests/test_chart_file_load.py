# -*- coding: utf-8 -*-
"""Test loading various chart formats (.json, .xml, .jhd) into PersonChartInputPanel."""
import unittest
import os
import tempfile
import json
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from gui.widgets.marriage_matching_widget import MarriageMatchingWidget, _load_chart_file


class ChartFileLoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_load_nested_json_chart_file(self):
        sample = {
            "metadata": {
                "name": "सरस्वती पाण्डे",
                "gender": 1,
                "birth_date": "2002/07/14",
                "birth_time": "09:40 AM",
                "country": "Nepal",
                "district": "Chitwan",
                "city": "Bharatpur",
                "latitude": 27.6833,
                "longitude": 84.4333,
                "timezone": 5.75
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample, f)
            tpath = f.name

        try:
            parsed = _load_chart_file(tpath)
            self.assertEqual(parsed["name"], "सरस्वती पाण्डे")
            self.assertEqual(parsed["city"], "Bharatpur")

            page = MarriageMatchingWidget("ne")
            page._girl_panel.load_from_dict(parsed)

            self.assertEqual(page._girl_panel._name_edit.text(), "सरस्वती पाण्डे")
            self.assertEqual(page._girl_panel._ad_edit.text(), "2002-07-14")
            self.assertEqual(page._girl_panel._time_edit.text(), "09:40:00")
            self.assertEqual(page._girl_panel._dist_cb.currentData(), "Chitwan")
            self.assertEqual(page._girl_panel._city_cb.currentText(), "Bharatpur")
            self.assertAlmostEqual(float(page._girl_panel._lat_edit.text()), 27.6833, places=3)
        finally:
            if os.path.exists(tpath):
                os.unlink(tpath)


class JhdImportSignTests(unittest.TestCase):
    """A .jhd import must keep western longitudes and negative UTC offsets.

    ``_load_chart_from_file`` used ``abs()`` on the timezone and longitude, which
    turned a New York birth (longitude -74.006, offset -5.0) into +74.006/+5.0
    and moved the ascendant and every house.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _write_jhd(self, lines):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jhd", delete=False, encoding="utf-8"
        )
        handle.write("\n".join(lines))
        handle.close()
        self.addCleanup(lambda: os.path.exists(handle.name) and os.unlink(handle.name))
        return handle.name

    def test_western_birth_keeps_negative_longitude_and_offset(self):
        from gui.app import _load_chart_from_file

        # month, day, year, decimal time, tz, longitude, latitude, place
        path = self._write_jhd([
            "7", "4", "1985", "14.5", "-5.0", "-74.0060", "40.7128", "New York",
        ])
        parsed = _load_chart_from_file(path)
        self.assertAlmostEqual(parsed["longitude"], -74.0060, places=4)
        self.assertAlmostEqual(parsed["timezone"], -5.0, places=4)
        self.assertAlmostEqual(parsed["latitude"], 40.7128, places=4)
        self.assertEqual(parsed["birth_time"], "14:30:00")

    def test_nepalese_birth_is_unchanged(self):
        from gui.app import _load_chart_from_file

        path = self._write_jhd([
            "1", "15", "1990", "10.5", "5.75", "85.3240", "27.7172", "Kathmandu",
        ])
        parsed = _load_chart_from_file(path)
        self.assertAlmostEqual(parsed["longitude"], 85.3240, places=4)
        self.assertAlmostEqual(parsed["timezone"], 5.75, places=4)


if __name__ == "__main__":
    unittest.main()
