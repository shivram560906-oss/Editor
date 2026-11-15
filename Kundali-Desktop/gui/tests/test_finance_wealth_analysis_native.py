# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.finance_wealth_analysis import FinanceWealthAnalysisPage, build_finance_wealth_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5},
        {"name": "Moon", "sign_number": 4, "house": 4},
        {"name": "Mars", "sign_number": 1, "house": 1},
        {"name": "Mercury", "sign_number": 6, "house": 6, "is_combust": True},
        {"name": "Jupiter", "sign_number": 9, "house": 9, "is_retrograde": True},
        {"name": "Venus", "sign_number": 2, "house": 2, "exaltation_state": "own_sign"},
        {"name": "Saturn", "sign_number": 11, "house": 11},
        {"name": "Rahu", "sign_number": 8, "house": 8},
        {"name": "Ketu", "sign_number": 2, "house": 2},
    ]
    return {
        "metadata": {"name": "Finance Chart", "birth_date": "1990-01-02"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {
            "D2": {
                "lagna": {"sign_number": 5},
                "planets": [
                    {"name": "Sun", "sign_number": 5, "house": 1},
                    {"name": "Moon", "sign_number": 4, "house": 12},
                    {"name": "Venus", "sign_number": 5, "house": 1},
                ],
            }
        },
        "parashara_yogas": [
            {
                "id": "dhana_yoga",
                "name": "Dhana Yoga",
                "nepali": "धन योग",
                "category": "dhana",
                "cause_en": "The wealth lords are associated.",
                "cause_ne": "धन भावका स्वामी सम्बन्धित छन्।",
                "result_en": "Supports financial growth.",
                "result_ne": "आर्थिक वृद्धिलाई समर्थन गर्छ।",
            },
            {"id": "saraswati_yoga", "name": "Saraswati Yoga", "category": "vidya"},
        ],
        "dasha": [
            {"lord": "Jupiter", "children": [{"lord": "Mercury"}, {"lord": "Venus"}]},
            {"lord": "Saturn", "children": [{"lord": "Moon"}]},
        ],
    }


class FinanceWealthModelTests(unittest.TestCase):
    def test_authoritative_d1_d2_yoga_and_dasha_factors_are_mapped(self):
        model = build_finance_wealth_model(sample_payload())
        self.assertEqual(model["state"], "ready")
        houses = {item["house"]: item for item in model["wealth_houses"]}
        self.assertEqual(houses[2]["sign"], 2)
        self.assertEqual(houses[2]["lord"], "Venus")
        self.assertEqual(houses[2]["occupants"], ["Venus", "Ketu"])
        self.assertEqual(houses[2]["lord_placement"]["house"], 2)
        self.assertEqual(houses[5]["lord"], "Sun")
        self.assertEqual(houses[5]["occupants"], ["Sun"])
        self.assertEqual(houses[9]["lord"], "Jupiter")
        self.assertTrue(houses[9]["lord_placement"]["retrograde"])
        self.assertEqual(houses[11]["lord"], "Saturn")
        self.assertEqual(houses[11]["occupants"], ["Saturn"])

        self.assertTrue(model["d2_available"])
        self.assertEqual(model["d2_lagna_sign"], 5)
        self.assertEqual(model["d2_planet_count"], 3)
        self.assertEqual([item["id"] for item in model["dhan_yogas"]], ["dhana_yoga"])
        self.assertEqual(model["dasha"]["mahadasha_count"], 2)
        self.assertEqual(model["dasha"]["antardasha_count"], 3)
        for browser_only_key in ("income", "savings", "gains", "dhanYoga", "riskPlanets", "periods"):
            self.assertNotIn(browser_only_key, model)

    def test_d2_absence_remains_explicit(self):
        payload = sample_payload()
        payload["vargas"] = {}
        model = build_finance_wealth_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertFalse(model["d2_available"])
        self.assertIsNone(model["d2_lagna_sign"])
        self.assertEqual(model["d2_planet_count"], 0)

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_finance_wealth_model(None)["state"], "no_chart")
        self.assertEqual(build_finance_wealth_model({})["state"], "empty")
        malformed = {"lagna": {"sign_number": 1}, "planets": "bad"}
        self.assertEqual(build_finance_wealth_model(malformed)["state"], "empty")
        self.assertEqual(build_finance_wealth_model({"error": "failed"}), {"state": "error", "message": "failed"})


class FinanceWealthWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections_and_explicit_prediction_states(self):
        page = FinanceWealthAnalysisPage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "financeWealthAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Finance & Wealth Analysis", labels)
        self.assertIn("1. Astrological Foundation of Finance", labels)
        self.assertIn("4. Financial Timeline by Dasha", labels)
        self.assertIn("6. Remedies & Guidance", labels)
        page.deleteLater()

    def test_nepali_yoga_name_uses_backend_nepali_key(self):
        page = FinanceWealthAnalysisPage(sample_payload(), "ne")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("आर्थिक तथा धन विश्लेषण", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = FinanceWealthAnalysisPage(None, "en")
        state = page.findChild(QLabel, "financeWealthAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_existing_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_finance_wealth_analysis")
        self.assertIsInstance(page, FinanceWealthAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
