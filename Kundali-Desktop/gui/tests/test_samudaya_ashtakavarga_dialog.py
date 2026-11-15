# -*- coding: utf-8 -*-
"""
gui/tests/test_samudaya_ashtakavarga_dialog.py
Unit tests for Samudaya Ashtakavarga house click, target detection, analysis engine,
and SamudayaHouseDetailDialog modal reporting.
"""

import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QRectF

from gui.widgets.ashtakavarga_house_dialog import (
    SamudayaHouseDetailDialog,
    analyze_house_in_chart,
    analyze_sav_bindus_for_house,
    BHAVA_NAMES_NE,
    BHAVA_SIGNIFICATIONS_NE
)
from gui.widgets.ashtakavarga import SamudayaAshtakavargaChartWidget

# Ensure single QApplication instance
app = QApplication.instance() or QApplication([])


class TestSamudayaAshtakavargaDialog(unittest.TestCase):

    def setUp(self):
        self.mock_chart_data = {
            "lagna": {"sign_number": 1, "degree": 14.5},
            "planets": [
                {"name": "Sun", "sign_number": 5, "house": 5, "degree": 12.3, "is_retrograde": False},
                {"name": "Moon", "sign_number": 4, "house": 4, "degree": 8.1, "is_retrograde": False},
                {"name": "Mars", "sign_number": 10, "house": 10, "degree": 28.0, "is_retrograde": False},
                {"name": "Mercury", "sign_number": 6, "house": 6, "degree": 15.0, "is_retrograde": False},
                {"name": "Jupiter", "sign_number": 9, "house": 9, "degree": 21.4, "is_retrograde": False},
                {"name": "Venus", "sign_number": 12, "house": 12, "degree": 27.2, "is_retrograde": False},
                {"name": "Saturn", "sign_number": 11, "house": 11, "degree": 4.5, "is_retrograde": False},
            ],
            "ashtakavarga": {
                "sav": [32, 28, 26, 30, 34, 24, 29, 23, 31, 35, 33, 22],
                "bhinnashtakavarga": {
                    "Sun": [4] * 12, "Moon": [4] * 12, "Mars": [4] * 12,
                    "Mercury": [4] * 12, "Jupiter": [5] * 12, "Venus": [5] * 12, "Saturn": [4] * 12
                }
            }
        }

    def test_analyze_house_in_chart(self):
        # House 1 in Aries Ascendant
        res1 = analyze_house_in_chart(1, 1, self.mock_chart_data)
        self.assertEqual(res1["house_num"], 1)
        self.assertEqual(res1["sign_num"], 1)
        self.assertEqual(res1["lord_name_ne"], "मङ्गल")
        self.assertEqual(res1["lord_house"], 10)  # Mars in 10th house
        self.assertIn("उच्च", res1["lord_dignity"])
        self.assertTrue(len(res1["fruits_received"]) > 0)

        # House 10 in Aries Ascendant (contains exalted Mars)
        res10 = analyze_house_in_chart(10, 1, self.mock_chart_data)
        self.assertEqual(res10["house_num"], 10)
        self.assertEqual(res10["sign_num"], 10)
        self.assertTrue(any(p["name_en"] == "Mars" for p in res10["placed_planets"]))

    def test_analyze_sav_bindus_for_house(self):
        # High score: 32
        high = analyze_sav_bindus_for_house(1, 32, "मेष")
        self.assertEqual(high["bindus"], 32)
        self.assertGreater(high["gain_pct"], 100.0)
        self.assertIn("अत्यन्त बलियो", high["strength_badge"])
        self.assertTrue(len(high["benefits"]) > 0)
        self.assertIn("finance", high["domain_gains"])
        self.assertIn("career", high["domain_gains"])
        self.assertIn("health", high["domain_gains"])
        self.assertIn("relations", high["domain_gains"])

        # Low score: 22
        low = analyze_sav_bindus_for_house(12, 22, "मीन")
        self.assertEqual(low["bindus"], 22)
        self.assertLess(low["gain_pct"], 100.0)
        self.assertIn("कमजोर", low["strength_badge"])
        self.assertTrue(len(low["risks"]) > 0)

    def test_dialog_creation_and_switching(self):
        dlg = SamudayaHouseDetailDialog(
            house_num=1,
            lagna_sign=1,
            sav_scores=[32, 28, 26, 30, 34, 24, 29, 23, 31, 35, 33, 22],
            chart_data=self.mock_chart_data,
            initial_tab="house"
        )
        self.assertEqual(dlg._house_num, 1)
        self.assertEqual(dlg._tabs.currentIndex(), 0)

        # Switch to score tab
        dlg._tabs.setCurrentIndex(1)
        self.assertEqual(dlg._tabs.currentIndex(), 1)

        # Switch house to 5
        dlg._load_house(5)
        self.assertEqual(dlg._house_num, 5)

        # Next house to 6
        dlg._next_house()
        self.assertEqual(dlg._house_num, 6)

        # Prev house to 5
        dlg._prev_house()
        self.assertEqual(dlg._house_num, 5)

    def test_chart_widget_hit_testing_and_signals(self):
        widget = SamudayaAshtakavargaChartWidget(
            lagna_sign=1,
            sav_scores=[32, 28, 26, 30, 34, 24, 29, 23, 31, 35, 33, 22],
            chart_data=self.mock_chart_data
        )
        widget.resize(400, 300)
        widget._play_animation()

        # Simulate rect population
        widget._sav_rects[1] = QRectF(150, 100, 40, 30)
        widget._rashi_rects[1] = QRectF(150, 60, 40, 20)
        widget._house_rects[1] = QRectF(140, 50, 60, 90)

        # Target at rashi rect
        h, t = widget._target_at(QPointF(160, 70))
        self.assertEqual(h, 1)
        self.assertEqual(t, "rashi")

        # Target at sav score rect
        h, t = widget._target_at(QPointF(160, 110))
        self.assertEqual(h, 1)
        self.assertEqual(t, "score")

        # Test signals
        clicked_events = []
        element_events = []
        widget.house_clicked.connect(lambda h, s: clicked_events.append((h, s)))
        widget.element_clicked.connect(lambda h, sn, s, t: element_events.append((h, sn, s, t)))

        widget.house_clicked.emit(1, 32)
        widget.element_clicked.emit(1, 1, 32, "rashi")

        self.assertEqual(len(clicked_events), 1)
        self.assertEqual(clicked_events[0], (1, 32))
        self.assertEqual(len(element_events), 1)
        self.assertEqual(element_events[0], (1, 1, 32, "rashi"))


if __name__ == "__main__":
    unittest.main()
