# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.business_analysis import BusinessAnalysisPage, build_business_analysis_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5},
        {"name": "Moon", "sign_number": 4, "house": 4},
        {"name": "Mars", "sign_number": 7, "house": 7},
        {"name": "Mercury", "sign_number": 6, "house": 6, "is_combust": True},
        {"name": "Jupiter", "sign_number": 9, "house": 9},
        {"name": "Venus", "sign_number": 2, "house": 2},
        {"name": "Saturn", "sign_number": 10, "house": 10},
        {"name": "Rahu", "sign_number": 11, "house": 11},
        {"name": "Ketu", "sign_number": 12, "house": 12},
    ]
    return {
        "metadata": {"name": "Business Chart", "birth_date": "1990-01-02"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D10": {
                "lagna": {"sign_number": 5},
                "planets": [
                    {"name": "Sun", "sign_number": 5, "house": 1},
                    {"name": "Mercury", "sign_number": 7, "house": 3},
                    {"name": "Mars", "sign_number": 10, "house": 6},
                    {"name": "Saturn", "sign_number": 2, "house": 10},
                    {"name": "Moon", "sign_number": 11, "house": 7},
                ],
            }
        },
        "parashara_yogas": [
            {
                "id": "vyapar_yoga",
                "name": "Vyapar Yoga",
                "category": "business",
                "cause_en": "Tenth house and Mercury support business.",
                "cause_ne": "दशम भाव र बुधले व्यवसायलाई समर्थन गर्छन्।",
                "result_en": "Supports entrepreneurship.",
                "result_ne": "उद्यमशीलतालाई समर्थन गर्छ।",
            },
            {"id": "vidya_yoga", "name": "Saraswati Yoga", "category": "vidya"},
        ],
        "dasha": [
            {"lord": "Saturn", "children": [{"lord": "Mercury"}, {"lord": "Venus"}]},
            {"lord": "Jupiter", "children": [{"lord": "Moon"}]},
        ],
    }


class BusinessAnalysisModelTests(unittest.TestCase):
    def test_authoritative_houses_significators_d10_and_dasha_factors_are_mapped(self):
        model = build_business_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")

        houses = {item["house"]: item for item in model["business_houses"]}
        self.assertEqual(houses[7]["sign"], 7)
        self.assertEqual(houses[7]["lord"], "Venus")
        self.assertEqual(houses[7]["lord_placement"]["house"], 2)
        self.assertEqual(houses[7]["occupants"], ["Mars"])
        self.assertEqual(houses[10]["sign"], 10)
        self.assertEqual(houses[10]["lord"], "Saturn")
        self.assertEqual(houses[10]["lord_placement"]["house"], 10)
        self.assertEqual(houses[10]["occupants"], ["Saturn"])

        self.assertEqual(model["mercury_placement"]["house"], 6)
        self.assertTrue(model["mercury_placement"]["combust"])
        self.assertEqual(model["mars_placement"]["house"], 7)
        self.assertEqual(model["venus_placement"]["house"], 2)
        self.assertEqual(model["saturn_placement"]["house"], 10)
        self.assertEqual(model["rahu_placement"]["house"], 11)

        self.assertTrue(model["d10_available"])
        self.assertEqual(model["d10_lagna_sign"], 5)
        self.assertEqual(model["d10_tenth_sign"], 2)
        self.assertEqual(model["d10_tenth_occupants"], ["Saturn"])
        self.assertEqual(model["d10_seventh_occupants"], ["Moon"])

        self.assertEqual([item["id"] for item in model["business_yogas"]], ["vyapar_yoga"])
        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        self.assertNotIn("types", model)
        self.assertNotIn("success", model)
        self.assertNotIn("sector", model)

    def test_d10_absence_remains_explicit(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_business_analysis_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d10_available"])
        self.assertIsNone(model["d10_lagna_sign"])
        self.assertIsNone(model["d10_tenth_sign"])
        self.assertEqual(model["d10_tenth_occupants"], [])
        self.assertEqual(model["d10_seventh_occupants"], [])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_business_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_business_analysis_model({})["state"], "empty")
        malformed = {"lagna": {"sign_number": 1}, "planets": "bad"}
        self.assertEqual(build_business_analysis_model(malformed)["state"], "empty")
        self.assertEqual(
            build_business_analysis_model({"error": "failed"}),
            {"state": "error", "message": "failed"},
        )


class BusinessAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections(self):
        page = BusinessAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "businessAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Business Analysis", labels)
        self.assertIn("1. Astrological Foundation of Business Yoga", labels)
        self.assertIn("4. Business Timeline by Dasha", labels)
        self.assertIn("6. Remedies & Guidance", labels)
        page.deleteLater()

    def test_nepali_page_uses_backend_nepali_header(self):
        page = BusinessAnalysisPage(sample_payload(), "ne")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("व्यापार/व्यवसाय विश्लेषण", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = BusinessAnalysisPage(None, "en")
        state = page.findChild(QLabel, "businessAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_business_analysis")
        self.assertIsInstance(page, BusinessAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
