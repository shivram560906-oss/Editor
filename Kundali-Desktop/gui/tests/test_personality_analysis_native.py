# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.personality_analysis import PersonalityAnalysisPage, build_personality_analysis_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5},
        {"name": "Moon", "sign_number": 4, "house": 4},
        {"name": "Mars", "sign_number": 7, "house": 7},
        {"name": "Mercury", "sign_number": 6, "house": 6},
        {"name": "Jupiter", "sign_number": 9, "house": 9, "is_retrograde": True},
        {"name": "Venus", "sign_number": 2, "house": 2},
        {"name": "Saturn", "sign_number": 10, "house": 10},
        {"name": "Rahu", "sign_number": 11, "house": 11},
        {"name": "Ketu", "sign_number": 12, "house": 12},
    ]
    return {
        "metadata": {"name": "Personality Chart", "birth_date": "1990-01-02"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D9": {
                "lagna": {"sign_number": 3},
                "planets": [
                    {"name": "Mercury", "sign_number": 3, "house": 1},
                    {"name": "Jupiter", "sign_number": 6, "house": 4},
                    {"name": "Moon", "sign_number": 9, "house": 7},
                    {"name": "Venus", "sign_number": 7, "house": 5},
                ],
            },
            "D45": {
                "lagna": {"sign_number": 5},
                "planets": [
                    {"name": "Sun", "sign_number": 5, "house": 1},
                    {"name": "Mercury", "sign_number": 7, "house": 3},
                    {"name": "Moon", "sign_number": 9, "house": 5},
                    {"name": "Saturn", "sign_number": 10, "house": 6},
                ],
            },
        },
        "dasha": [
            {"lord": "Jupiter", "children": [{"lord": "Mercury"}, {"lord": "Moon"}]},
            {"lord": "Saturn", "children": [{"lord": "Venus"}]},
        ],
    }


class PersonalityAnalysisModelTests(unittest.TestCase):
    def test_authoritative_lagna_lord_moon_sun_d9_d45_and_dasha_factors_are_mapped(self):
        model = build_personality_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")

        self.assertEqual(model["lagna_sign"], 1)
        self.assertEqual(model["lagna_lord"], "Mars")
        self.assertEqual(model["lagna_lord_placement"]["house"], 7)
        self.assertEqual(model["moon_placement"]["house"], 4)
        self.assertEqual(model["sun_placement"]["house"], 5)
        self.assertEqual(model["lagna_occupants"], [])

        self.assertTrue(model["d9_available"])
        self.assertEqual(model["d9_lagna_sign"], 3)
        self.assertEqual(model["d9_lagna_lord"], "Mercury")
        self.assertEqual(model["d9_lagna_lord_placement"]["house"], 1)
        self.assertEqual(model["d9_moon_sign"], 9)

        self.assertTrue(model["d45_available"])
        self.assertEqual(model["d45_lagna_sign"], 5)
        self.assertEqual(model["d45_lagna_lord"], "Sun")
        self.assertEqual(model["d45_lagna_lord_placement"]["house"], 1)

        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        self.assertNotIn("traits", model)
        self.assertNotIn("score", model)
        self.assertNotIn("swayambhu", model)

    def test_d9_and_d45_absence_remains_explicit(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_personality_analysis_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d9_available"])
        self.assertIsNone(model["d9_lagna_sign"])
        self.assertIsNone(model["d9_lagna_lord"])
        self.assertFalse(model["d9_lagna_lord_placement"]["available"])
        self.assertIsNone(model["d9_moon_sign"])
        self.assertFalse(model["d45_available"])
        self.assertIsNone(model["d45_lagna_sign"])
        self.assertIsNone(model["d45_lagna_lord"])
        self.assertFalse(model["d45_lagna_lord_placement"]["available"])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_personality_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_personality_analysis_model({})["state"], "empty")
        malformed = {"lagna": {"sign_number": 1}, "planets": "bad"}
        self.assertEqual(build_personality_analysis_model(malformed)["state"], "empty")
        self.assertEqual(
            build_personality_analysis_model({"error": "failed"}),
            {"state": "error", "message": "failed"},
        )


class PersonalityAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections(self):
        page = PersonalityAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "personalityAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Personality Analysis", labels)
        self.assertIn("1. Personality of the Ascendant Sign", labels)
        self.assertIn("6. Personality Timeline by Dasha", labels)
        self.assertIn("8. Suggestions for Personality Development", labels)
        page.deleteLater()

    def test_nepali_page_uses_backend_nepali_header(self):
        page = PersonalityAnalysisPage(sample_payload(), "ne")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("व्यक्तित्व विश्लेषण", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = PersonalityAnalysisPage(None, "en")
        state = page.findChild(QLabel, "personalityAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_personality_analysis")
        self.assertIsInstance(page, PersonalityAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
