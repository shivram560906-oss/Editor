# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.health_analysis import HealthAnalysisPage, build_health_analysis_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5, "exaltation_state": "neutral"},
        {"name": "Moon", "sign_number": 4, "house": 4},
        {"name": "Mars", "sign_number": 6, "house": 6},
        {"name": "Mercury", "sign_number": 6, "house": 6, "is_combust": True},
        {"name": "Jupiter", "sign_number": 9, "house": 9},
        {"name": "Venus", "sign_number": 8, "house": 8},
        {"name": "Saturn", "sign_number": 10, "house": 10, "is_retrograde": True},
        {"name": "Rahu", "sign_number": 12, "house": 12},
        {"name": "Ketu", "sign_number": 6, "house": 6},
    ]
    return {
        "metadata": {"name": "Health Chart", "birth_date": "1990-01-02", "calculation_version": "test-v1"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D6": {
                "lagna": {"sign_number": 4},
                "planets": [
                    {"name": "Moon", "sign_number": 4, "house": 1},
                    {"name": "Saturn", "sign_number": 9, "house": 6},
                    {"name": "Jupiter", "sign_number": 10, "house": 7},
                ],
            }
        },
        "dasha": [
            {"lord": "Sun", "children": [{"lord": "Moon"}, {"lord": "Mars"}]},
            {"lord": "Moon", "children": [{"lord": "Jupiter"}]},
        ],
    }


class HealthAnalysisModelTests(unittest.TestCase):
    def test_authoritative_health_chart_factors_are_mapped(self):
        model = build_health_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")
        self.assertEqual(model["lagna_lord"], "Mars")
        self.assertEqual(model["lagna_lord_placement"]["house"], 6)
        self.assertEqual(model["sun_placement"]["house"], 5)
        self.assertEqual(model["moon_placement"]["sign"], 4)

        houses = {item["house"]: item for item in model["health_houses"]}
        self.assertEqual(houses[6]["sign"], 6)
        self.assertEqual(houses[6]["lord"], "Mercury")
        self.assertEqual(houses[6]["occupants"], ["Mars", "Mercury", "Ketu"])
        self.assertEqual(houses[8]["sign"], 8)
        self.assertEqual(houses[8]["lord"], "Mars")
        self.assertEqual(houses[12]["sign"], 12)
        self.assertEqual(houses[12]["lord"], "Jupiter")
        self.assertEqual(houses[12]["occupants"], ["Rahu"])

        self.assertTrue(model["d6_available"])
        self.assertEqual(model["d6_lagna_sign"], 4)
        self.assertEqual(model["d6_lagna_lord"], "Moon")
        self.assertEqual(model["d6_lagna_lord_placement"]["house"], 1)
        self.assertEqual(model["d6_sixth_occupants"], ["Saturn"])
        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        self.assertNotIn("vitality", model)
        self.assertNotIn("sensitive_areas", model)
        self.assertNotIn("health_periods", model)
        self.assertNotIn("recommendations", model)

    def test_d6_absence_remains_explicit(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_health_analysis_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d6_available"])
        self.assertIsNone(model["d6_lagna_sign"])
        self.assertIsNone(model["d6_lagna_lord"])
        self.assertFalse(model["d6_lagna_lord_placement"]["available"])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_health_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_health_analysis_model({})["state"], "empty")
        self.assertEqual(build_health_analysis_model({"lagna": {"sign_number": 1}, "planets": "bad"})["state"], "empty")
        self.assertEqual(build_health_analysis_model({"error": "failed"}), {"state": "error", "message": "failed"})


class HealthAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections_and_explicit_health_limits(self):
        page = HealthAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "healthAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Health Analysis", labels)
        self.assertIn("1. Astrological Foundation of Health", labels)
        self.assertIn("4. Health Timeline by Dasha", labels)
        self.assertIn("6. Health Remedies & Guidance", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = HealthAnalysisPage(None, "en")
        state = page.findChild(QLabel, "healthAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_existing_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_health_analysis")
        self.assertIsInstance(page, HealthAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
