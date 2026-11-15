# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.foreign_travel_analysis import ForeignTravelAnalysisPage, build_foreign_travel_analysis_model


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
        "metadata": {"name": "Foreign Travel Chart", "birth_date": "1990-01-02"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D9": {
                "lagna": {"sign_number": 3},
                "planets": [
                    {"name": "Mercury", "sign_number": 3, "house": 1},
                    {"name": "Jupiter", "sign_number": 6, "house": 4},
                    {"name": "Moon", "sign_number": 9, "house": 9},
                    {"name": "Venus", "sign_number": 12, "house": 12},
                ],
            }
        },
        "parashara_yogas": [
            {
                "id": "yatra_yoga",
                "name": "Yatra Yoga",
                "category": "travel",
                "cause_en": "Rahu and ninth house support travel.",
                "cause_ne": "राहु र नवौँ भावले यात्रालाई समर्थन गर्छन्।",
                "result_en": "Supports foreign travel.",
                "result_ne": "विदेश यात्रालाई समर्थन गर्छ।",
            },
            {"id": "dhana_yoga", "name": "Dhana Yoga", "category": "wealth"},
        ],
        "dasha": [
            {"lord": "Jupiter", "children": [{"lord": "Mercury"}, {"lord": "Moon"}]},
            {"lord": "Saturn", "children": [{"lord": "Venus"}]},
        ],
    }


class ForeignTravelAnalysisModelTests(unittest.TestCase):
    def test_authoritative_houses_significators_d9_and_dasha_factors_are_mapped(self):
        model = build_foreign_travel_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")

        houses = {item["house"]: item for item in model["travel_houses"]}
        self.assertEqual(houses[3]["sign"], 3)
        self.assertEqual(houses[3]["lord"], "Mercury")
        self.assertEqual(houses[3]["lord_placement"]["house"], 6)
        self.assertEqual(houses[3]["occupants"], [])
        self.assertEqual(houses[9]["sign"], 9)
        self.assertEqual(houses[9]["lord"], "Jupiter")
        self.assertEqual(houses[9]["lord_placement"]["house"], 9)
        self.assertEqual(houses[9]["occupants"], ["Jupiter"])
        self.assertEqual(houses[12]["sign"], 12)
        self.assertEqual(houses[12]["lord"], "Jupiter")
        self.assertEqual(houses[12]["occupants"], ["Ketu"])

        self.assertEqual(model["rahu_placement"]["house"], 11)
        self.assertEqual(model["moon_placement"]["house"], 4)
        self.assertEqual(model["saturn_placement"]["house"], 10)
        self.assertEqual(model["jupiter_placement"]["house"], 9)
        self.assertTrue(model["jupiter_placement"]["retrograde"])

        self.assertTrue(model["d9_available"])
        self.assertEqual(model["d9_lagna_sign"], 3)
        self.assertEqual(model["d9_ninth_sign"], 11)
        self.assertEqual(model["d9_ninth_occupants"], ["Moon"])
        self.assertEqual(model["d9_twelfth_occupants"], ["Venus"])

        self.assertEqual([item["id"] for item in model["travel_yogas"]], ["yatra_yoga"])
        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        self.assertNotIn("likelihood", model)
        self.assertNotIn("score", model)
        self.assertNotIn("window", model)

    def test_d9_absence_remains_explicit(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_foreign_travel_analysis_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d9_available"])
        self.assertIsNone(model["d9_lagna_sign"])
        self.assertIsNone(model["d9_ninth_sign"])
        self.assertEqual(model["d9_ninth_occupants"], [])
        self.assertEqual(model["d9_twelfth_occupants"], [])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_foreign_travel_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_foreign_travel_analysis_model({})["state"], "empty")
        malformed = {"lagna": {"sign_number": 1}, "planets": "bad"}
        self.assertEqual(build_foreign_travel_analysis_model(malformed)["state"], "empty")
        self.assertEqual(
            build_foreign_travel_analysis_model({"error": "failed"}),
            {"state": "error", "message": "failed"},
        )


class ForeignTravelAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections(self):
        page = ForeignTravelAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "foreignTravelAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Foreign Travel Analysis", labels)
        self.assertIn("1. Astrological Foundation of Travel Yoga", labels)
        self.assertIn("4. Travel Timeline by Dasha", labels)
        self.assertIn("6. Remedies & Guidance", labels)
        page.deleteLater()

    def test_nepali_page_uses_backend_nepali_header(self):
        page = ForeignTravelAnalysisPage(sample_payload(), "ne")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("विदेश यात्रा विश्लेषण", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = ForeignTravelAnalysisPage(None, "en")
        state = page.findChild(QLabel, "foreignTravelAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_foreign_travel_analysis")
        self.assertIsInstance(page, ForeignTravelAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
