# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.education_analysis import EducationAnalysisPage, build_education_analysis_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5},
        {"name": "Moon", "sign_number": 4, "house": 4},
        {"name": "Mars", "sign_number": 7, "house": 7},
        {"name": "Mercury", "sign_number": 6, "house": 6, "is_combust": True},
        {"name": "Jupiter", "sign_number": 9, "house": 9, "is_retrograde": True},
        {"name": "Venus", "sign_number": 2, "house": 2},
        {"name": "Saturn", "sign_number": 10, "house": 10},
        {"name": "Rahu", "sign_number": 11, "house": 11},
        {"name": "Ketu", "sign_number": 12, "house": 12},
    ]
    return {
        "metadata": {"name": "Education Chart", "birth_date": "1990-01-02"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D24": {
                "lagna": {"sign_number": 3},
                "planets": [
                    {"name": "Mercury", "sign_number": 3, "house": 1},
                    {"name": "Jupiter", "sign_number": 6, "house": 4},
                    {"name": "Venus", "sign_number": 7, "house": 5},
                    {"name": "Moon", "sign_number": 9, "house": 7},
                ],
            }
        },
        "parashara_yogas": [
            {
                "id": "saraswati_yoga",
                "name": "Saraswati Yoga",
                "nepali": "सरस्वती योग",
                "category": "vidya",
                "cause_en": "Mercury, Jupiter and Venus support learning.",
                "cause_ne": "बुध, गुरु र शुक्रले विद्यालाई समर्थन गर्छन्।",
                "result_en": "Supports learning and scholarship.",
                "result_ne": "अध्ययन र विद्वत्तालाई समर्थन गर्छ।",
            },
            {"id": "dhana_yoga", "name": "Dhana Yoga", "category": "wealth"},
        ],
        "dasha": [
            {"lord": "Jupiter", "children": [{"lord": "Mercury"}, {"lord": "Moon"}]},
            {"lord": "Saturn", "children": [{"lord": "Venus"}]},
        ],
    }


class EducationAnalysisModelTests(unittest.TestCase):
    def test_authoritative_d1_d24_yoga_and_dasha_factors_are_mapped(self):
        model = build_education_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")

        houses = {item["house"]: item for item in model["education_houses"]}
        self.assertEqual(houses[4]["sign"], 4)
        self.assertEqual(houses[4]["lord"], "Moon")
        self.assertEqual(houses[4]["occupants"], ["Moon"])
        self.assertEqual(houses[5]["sign"], 5)
        self.assertEqual(houses[5]["lord"], "Sun")
        self.assertEqual(houses[5]["lord_placement"]["house"], 5)
        self.assertEqual(houses[9]["sign"], 9)
        self.assertEqual(houses[9]["lord"], "Jupiter")
        self.assertEqual(houses[9]["occupants"], ["Jupiter"])
        self.assertEqual(model["mercury_placement"]["house"], 6)
        self.assertTrue(model["mercury_placement"]["combust"])
        self.assertEqual(model["jupiter_placement"]["house"], 9)
        self.assertTrue(model["jupiter_placement"]["retrograde"])
        self.assertEqual(model["moon_placement"]["house"], 4)

        self.assertTrue(model["d24_available"])
        self.assertEqual(model["d24_lagna_sign"], 3)
        self.assertEqual(model["d24_lagna_lord"], "Mercury")
        self.assertEqual(model["d24_lagna_lord_placement"]["house"], 1)
        self.assertEqual(model["d24_mercury_placement"]["sign"], 3)
        self.assertEqual(model["d24_jupiter_placement"]["house"], 4)
        self.assertEqual(model["d24_fourth_occupants"], ["Jupiter"])
        self.assertEqual(model["d24_fifth_occupants"], ["Venus"])

        self.assertEqual([item["id"] for item in model["vidya_yogas"]], ["saraswati_yoga"])
        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        self.assertNotIn("learning", model)
        self.assertNotIn("memory", model)
        self.assertNotIn("higher", model)
        self.assertNotIn("fields", model)
        self.assertNotIn("periods", model)

    def test_d24_absence_remains_explicit(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_education_analysis_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d24_available"])
        self.assertIsNone(model["d24_lagna_sign"])
        self.assertIsNone(model["d24_lagna_lord"])
        self.assertFalse(model["d24_lagna_lord_placement"]["available"])
        self.assertEqual(model["d24_fourth_occupants"], [])
        self.assertEqual(model["d24_fifth_occupants"], [])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_education_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_education_analysis_model({})["state"], "empty")
        malformed = {"lagna": {"sign_number": 1}, "planets": "bad"}
        self.assertEqual(build_education_analysis_model(malformed)["state"], "empty")
        self.assertEqual(
            build_education_analysis_model({"error": "failed"}),
            {"state": "error", "message": "failed"},
        )


class EducationAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections_and_explicit_prediction_states(self):
        page = EducationAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "educationAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Education Analysis", labels)
        self.assertIn("1. Astrological Foundation of Education", labels)
        self.assertIn("4. Education Timeline by Dasha", labels)
        self.assertIn("6. Remedies & Guidance", labels)
        page.deleteLater()

    def test_nepali_yoga_name_uses_backend_nepali_key(self):
        page = EducationAnalysisPage(sample_payload(), "ne")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("शिक्षा विश्लेषण", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = EducationAnalysisPage(None, "en")
        state = page.findChild(QLabel, "educationAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_existing_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_education_analysis")
        self.assertIsInstance(page, EducationAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
