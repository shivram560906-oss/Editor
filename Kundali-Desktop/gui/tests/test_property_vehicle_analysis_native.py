# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.property_vehicle_analysis import PropertyVehicleAnalysisPage, build_property_vehicle_analysis_model


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
        "metadata": {"name": "Property Chart", "birth_date": "1990-01-02"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D4": {
                "lagna": {"sign_number": 2},
                "planets": [
                    {"name": "Venus", "sign_number": 2, "house": 1},
                    {"name": "Moon", "sign_number": 5, "house": 4},
                    {"name": "Mars", "sign_number": 10, "house": 9},
                    {"name": "Jupiter", "sign_number": 3, "house": 2},
                ],
            },
            "D16": {
                "lagna": {"sign_number": 7},
                "planets": [
                    {"name": "Venus", "sign_number": 7, "house": 1},
                    {"name": "Moon", "sign_number": 10, "house": 4},
                    {"name": "Saturn", "sign_number": 9, "house": 3},
                    {"name": "Jupiter", "sign_number": 1, "house": 7},
                ],
            },
        },
        "dasha": [
            {"lord": "Moon", "children": [{"lord": "Mars"}, {"lord": "Venus"}]},
            {"lord": "Saturn", "children": [{"lord": "Mercury"}]},
        ],
    }


class PropertyVehicleAnalysisModelTests(unittest.TestCase):
    def test_authoritative_fourth_lord_significators_d4_d16_and_dasha_factors_are_mapped(self):
        model = build_property_vehicle_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")

        self.assertEqual(model["lagna_sign"], 1)
        self.assertEqual(model["fourth_sign"], 4)
        self.assertEqual(model["fourth_lord"], "Moon")
        self.assertEqual(model["fourth_lord_placement"]["house"], 4)
        self.assertEqual(model["fourth_occupants"], ["Moon"])

        self.assertEqual(model["mars_placement"]["house"], 7)
        self.assertEqual(model["venus_placement"]["house"], 2)
        self.assertEqual(model["moon_placement"]["house"], 4)
        self.assertEqual(model["saturn_placement"]["house"], 10)
        self.assertTrue(model["saturn_placement"]["retrograde"])

        self.assertTrue(model["d4_available"])
        self.assertEqual(model["d4_lagna_sign"], 2)
        self.assertEqual(model["d4_fourth_sign"], 5)
        self.assertEqual(model["d4_fourth_occupants"], ["Moon"])

        self.assertTrue(model["d16_available"])
        self.assertEqual(model["d16_lagna_sign"], 7)
        self.assertEqual(model["d16_fourth_sign"], 10)
        self.assertEqual(model["d16_fourth_occupants"], ["Moon"])

        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        self.assertNotIn("property_score", model)
        self.assertNotIn("vehicle_score", model)
        self.assertNotIn("rate", model)

    def test_d4_and_d16_absence_remains_explicit(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_property_vehicle_analysis_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d4_available"])
        self.assertIsNone(model["d4_lagna_sign"])
        self.assertIsNone(model["d4_fourth_sign"])
        self.assertEqual(model["d4_fourth_occupants"], [])
        self.assertFalse(model["d16_available"])
        self.assertIsNone(model["d16_lagna_sign"])
        self.assertIsNone(model["d16_fourth_sign"])
        self.assertEqual(model["d16_fourth_occupants"], [])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_property_vehicle_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_property_vehicle_analysis_model({})["state"], "empty")
        malformed = {"lagna": {"sign_number": 1}, "planets": "bad"}
        self.assertEqual(build_property_vehicle_analysis_model(malformed)["state"], "empty")
        self.assertEqual(
            build_property_vehicle_analysis_model({"error": "failed"}),
            {"state": "error", "message": "failed"},
        )


class PropertyVehicleAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections(self):
        page = PropertyVehicleAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "propertyVehicleAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Property & Vehicle Analysis", labels)
        self.assertIn("1. Astrological Foundation of Property & Vehicle Yoga", labels)
        self.assertIn("5. Property Timeline by Dasha", labels)
        self.assertIn("7. Remedies & Guidance", labels)
        page.deleteLater()

    def test_nepali_page_uses_backend_nepali_header(self):
        page = PropertyVehicleAnalysisPage(sample_payload(), "ne")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("सम्पत्ति तथा वाहन विश्लेषण", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = PropertyVehicleAnalysisPage(None, "en")
        state = page.findChild(QLabel, "propertyVehicleAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_property_vehicle_analysis")
        self.assertIsInstance(page, PropertyVehicleAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
