# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.app import normalize_action_id, NAV_STRUCTURE
from gui.widgets.remedies_page import RemediesPage
from backend.calculator.remedies import calculate_remedies

_APP = None

def get_qapp():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5, "exaltation_state": "OWN_SIGN"},
        {"name": "Moon", "sign_number": 4, "house": 4, "exaltation_state": "OWN_SIGN"},
        {"name": "Mars", "sign_number": 7, "house": 7, "exaltation_state": "NEUTRAL"},
        {"name": "Mercury", "sign_number": 6, "house": 6, "exaltation_state": "EXALTED"},
        {"name": "Jupiter", "sign_number": 9, "house": 9, "exaltation_state": "OWN_SIGN"},
        {"name": "Venus", "sign_number": 2, "house": 2, "exaltation_state": "OWN_SIGN"},
        {"name": "Saturn", "sign_number": 8, "house": 8, "exaltation_state": "DEBILITATED"},
        {"name": "Rahu", "sign_number": 11, "house": 11, "exaltation_state": "NEUTRAL"},
        {"name": "Ketu", "sign_number": 5, "house": 5, "exaltation_state": "NEUTRAL"},
    ]
    return {
        "metadata": {"name": "Remedies Chart", "birth_date": "1995-05-15"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "dasha": [
            {"lord": "Sun", "is_active": True, "children": []}
        ]
    }


class RemediesNativeWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = get_qapp()

    def test_navigation_action_id_resolution(self):
        self.assertEqual(normalize_action_id("report_remedies"), "report_remedies")
        self.assertEqual(normalize_action_id("remedies"), "report_remedies")
        self.assertEqual(normalize_action_id("gemstones"), "report_remedies")
        self.assertEqual(normalize_action_id("rudraksha"), "report_remedies")

        # Verify it is in NAV_STRUCTURE
        found = False
        for cat in NAV_STRUCTURE:
            for item in cat.get("items", []):
                if item["id"] == "report_remedies":
                    found = True
                    break
        self.assertTrue(found, "report_remedies must be present in NAV_STRUCTURE")

    def test_remedies_page_instantiation_and_tabs(self):
        payload = sample_payload()
        page = RemediesPage(payload, language="ne")

        self.assertIsNotNone(page)
        self.assertEqual(page._stack.count(), 4)

        # Tab 0: Gemstones
        page._switch_tab(0)
        self.assertEqual(page._stack.currentIndex(), 0)

        # Tab 1: Rudraksha
        page._switch_tab(1)
        self.assertEqual(page._stack.currentIndex(), 1)

        # Tab 2: Mantras
        page._switch_tab(2)
        self.assertEqual(page._stack.currentIndex(), 2)

        # Tab 3: Charity & Fasting
        page._switch_tab(3)
        self.assertEqual(page._stack.currentIndex(), 3)

    def test_remedies_page_refresh_and_language(self):
        payload = sample_payload()
        page_en = RemediesPage(payload, language="en")
        self.assertEqual(page_en._lang, "en")

        page_en.refresh(payload)
        self.assertEqual(page_en._stack.count(), 4)


if __name__ == "__main__":
    unittest.main()
