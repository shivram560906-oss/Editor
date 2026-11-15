# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.child_analysis import ChildAnalysisPage, build_child_analysis_model


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
        "metadata": {"name": "Child Chart", "birth_date": "1990-01-02", "calculation_version": "test-v1"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D7": {
                "lagna": {"sign_number": 3},
                "planets": [
                    {"name": "Venus", "sign_number": 7, "house": 5},
                    {"name": "Jupiter", "sign_number": 9, "house": 7},
                    {"name": "Mercury", "sign_number": 6, "house": 4},
                ],
            }
        },
        "dasha": [
            {
                "lord": "Jupiter",
                "children": [
                    {"lord": "Sun", "start": "2020-01-01", "end": "2021-01-01"},
                    {"lord": "Moon", "start": "2021-01-01", "end": "2022-01-01"},
                ],
            },
            {"lord": "Saturn", "children": [{"lord": "Mercury"}]},
        ],
    }


class ChildAnalysisModelTests(unittest.TestCase):
    def test_authoritative_d1_d7_and_dasha_factors_are_mapped(self):
        model = build_child_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")
        self.assertEqual(model["fifth_sign"], 5)
        self.assertEqual(model["fifth_lord"], "Sun")
        self.assertEqual(model["fifth_lord_placement"]["house"], 5)
        self.assertEqual(model["fifth_occupants"], ["Sun"])
        self.assertEqual(model["jupiter_placement"]["house"], 9)
        self.assertTrue(model["jupiter_placement"]["retrograde"])
        self.assertTrue(model["d7_available"])
        self.assertEqual(model["d7_lagna_sign"], 3)
        self.assertEqual(model["d7_fifth_sign"], 7)
        self.assertEqual(model["d7_fifth_lord"], "Venus")
        self.assertEqual(model["d7_fifth_lord_placement"]["house"], 5)
        self.assertEqual(model["d7_fifth_occupants"], ["Venus"])
        self.assertEqual(model["d7_jupiter_placement"]["house"], 7)
        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        self.assertNotIn("promise_score", model)
        self.assertNotIn("estimated_count", model)
        self.assertNotIn("children", model)

    def test_d7_absence_is_explicit_without_invalid_derived_values(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_child_analysis_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d7_available"])
        self.assertIsNone(model["d7_lagna_sign"])
        self.assertIsNone(model["d7_fifth_sign"])
        self.assertIsNone(model["d7_fifth_lord"])
        self.assertFalse(model["d7_fifth_lord_placement"]["available"])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_child_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_child_analysis_model({})["state"], "empty")
        self.assertEqual(build_child_analysis_model({"lagna": {"sign_number": 1}, "planets": "bad"})["state"], "empty")
        self.assertEqual(build_child_analysis_model({"error": "failed"}), {"state": "error", "message": "failed"})


class ChildAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections_and_explicit_prediction_states(self):
        page = ChildAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "childAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Child Potential and Reading", labels)
        self.assertIn("1. Astrological Foundation of Child Yoga", labels)
        self.assertIn("4. Child Life Timeline by Dasha", labels)
        self.assertIn("6. Remedies & Guidance", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = ChildAnalysisPage(None, "en")
        state = page.findChild(QLabel, "childAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_existing_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_child_analysis")
        self.assertIsInstance(page, ChildAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
