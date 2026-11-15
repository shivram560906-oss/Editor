# -*- coding: utf-8 -*-
"""Unit tests to verify district coordinates fallback when city is empty."""
import unittest
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from gui.widgets.chart_input import ChartInputWidget
from gui.widgets.marriage_matching_widget import PersonChartInputPanel, MarriageMatchingWidget
from gui.utils.location_data import district_metadata


class DistrictCoordinateFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_chart_input_district_fallback_when_city_empty(self):
        widget = ChartInputWidget("ne")
        widget._name_edit.setText("परीक्षण जातक")
        widget._btn_male.setChecked(True)
        widget._ad_date_edit.setText("2001-01-01")
        widget._time_edit.setText("10:30:00")

        # Select Gandaki province
        gandaki_idx = widget._region_combo.findData("Gandaki")
        self.assertGreaterEqual(gandaki_idx, 0)
        widget._region_combo.setCurrentIndex(gandaki_idx)
        widget._on_region_changed()

        # Select Kaski district
        kaski_idx = widget._district_combo.findData("Kaski")
        self.assertGreaterEqual(kaski_idx, 0)
        widget._district_combo.setCurrentIndex(kaski_idx)
        widget._on_district_changed()

        # Clear city combo / leave it empty
        widget._city_combo.setCurrentIndex(0)
        if widget._city_combo.lineEdit():
            widget._city_combo.lineEdit().clear()

        params = widget._collect_params()
        self.assertIsNotNone(params)
        kaski_meta = district_metadata("Nepal", "Kaski")
        self.assertAlmostEqual(params["latitude"], kaski_meta["lat"], places=3)
        self.assertAlmostEqual(params["longitude"], kaski_meta["lon"], places=3)
        self.assertEqual(params["district"], "Kaski")
        self.assertIn(params["city"], ("कास्की", "Kaski"))

    def test_marriage_matching_panel_district_fallback_when_city_empty(self):
        panel = PersonChartInputPanel("boy", "वर (केटा)", "👦")
        panel._name_edit.setText("वर शर्मा")
        panel._ad_edit.setText("1998-05-20")
        panel._time_edit.setText("08:15:00")

        # Select Bagmati province
        bagmati_idx = panel._region_cb.findData("Bagmati")
        self.assertGreaterEqual(bagmati_idx, 0)
        panel._region_cb.setCurrentIndex(bagmati_idx)
        panel._on_region_changed()

        # Select Chitwan district
        chitwan_idx = panel._dist_cb.findData("Chitwan")
        self.assertGreaterEqual(chitwan_idx, 0)
        panel._dist_cb.setCurrentIndex(chitwan_idx)
        panel._on_district_changed()

        # City is on default/empty
        panel._city_cb.setCurrentIndex(0)
        if panel._city_cb.lineEdit():
            panel._city_cb.lineEdit().clear()

        params = panel.collect_params()
        self.assertIsNotNone(params)
        chitwan_meta = district_metadata("Nepal", "Chitwan")
        self.assertAlmostEqual(params["latitude"], chitwan_meta["lat"], places=3)
        self.assertAlmostEqual(params["longitude"], chitwan_meta["lon"], places=3)
        self.assertEqual(params["district"], "Chitwan")
        self.assertIn(params["city"], ("चितवन", "Chitwan"))


if __name__ == "__main__":
    unittest.main()
