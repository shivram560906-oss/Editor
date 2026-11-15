# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.career_analysis import CareerAnalysisPage, build_career_analysis_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5},
        {"name": "Moon", "sign_number": 4, "house": 4},
        {"name": "Mars", "sign_number": 7, "house": 7},
        {"name": "Mercury", "sign_number": 6, "house": 6},
        {"name": "Jupiter", "sign_number": 9, "house": 9},
        {"name": "Venus", "sign_number": 2, "house": 2},
        {"name": "Saturn", "sign_number": 10, "house": 10, "is_retrograde": True},
        {"name": "Rahu", "sign_number": 11, "house": 11},
        {"name": "Ketu", "sign_number": 12, "house": 12},
    ]
    return {
        "metadata": {"name": "Career Chart", "birth_date": "1990-01-02", "calculation_version": "test-v1"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D10": {
                "lagna": {"sign_number": 3},
                "planets": [
                    {"name": "Sun", "sign_number": 1, "house": 10},
                    {"name": "Saturn", "sign_number": 10, "house": 7},
                ],
            }
        },
        "jaimini": {"chara_karakas": {"Amatyakaraka": "Mercury"}},
        "dasha": [
            {
                "lord": "Saturn",
                "start": "2020-01-01",
                "end": "2039-01-01",
                "is_active": True,
                "children": [
                    {"lord": "Mercury", "start_bs": "2082-01-01", "end_bs": "2084-09-01", "is_active": True}
                ],
            },
            {"lord": "Mercury", "children": []},
        ],
    }


class CareerAnalysisModelTests(unittest.TestCase):
    def test_authoritative_career_factors_are_mapped(self):
        model = build_career_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")
        self.assertEqual(model["tenth_sign"], 10)
        self.assertEqual(model["tenth_lord"], "Saturn")
        self.assertEqual(model["tenth_lord_house"], 10)
        self.assertTrue(model["tenth_lord_retrograde"])
        self.assertEqual(model["tenth_occupants"], ["Saturn"])
        self.assertEqual(model["second_occupants"], ["Venus"])
        self.assertEqual(model["eleventh_occupants"], ["Rahu"])
        self.assertEqual(model["amatyakaraka"], "Mercury")
        self.assertTrue(model["d10_available"])
        self.assertEqual(model["d10_lagna_sign"], 3)
        self.assertEqual(model["d10_tenth_occupants"], ["Sun"])
        self.assertEqual(model["active_dasha"]["lord"], "Saturn")
        self.assertEqual(model["active_dasha"]["antardasha_lord"], "Mercury")
        self.assertNotIn("career_score", model)
        self.assertNotIn("profession_fields", model)

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_career_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_career_analysis_model({})["state"], "empty")
        self.assertEqual(build_career_analysis_model({"lagna": {"sign_number": 1}, "planets": "bad"})["state"], "empty")
        self.assertEqual(build_career_analysis_model({"error": "failed"}), {"state": "error", "message": "failed"})


class CareerAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections_and_explicit_score_state(self):
        page = CareerAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "careerAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Career Analysis", labels)
        self.assertIn("D10", labels)
        self.assertIn("1. Astrological Foundation of Career", labels)
        self.assertIn("6. Remedies & Guidance", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = CareerAnalysisPage(None, "en")
        state = page.findChild(QLabel, "careerAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_existing_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_career_analysis")
        self.assertIsInstance(page, CareerAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
