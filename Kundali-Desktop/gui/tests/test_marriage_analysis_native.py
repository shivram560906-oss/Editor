# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.marriage_analysis import MarriageAnalysisPage, build_marriage_analysis_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5},
        {"name": "Moon", "sign_number": 4, "house": 4},
        {"name": "Mars", "sign_number": 7, "house": 7},
        {"name": "Mercury", "sign_number": 6, "house": 6},
        {"name": "Jupiter", "sign_number": 9, "house": 9},
        {"name": "Venus", "sign_number": 2, "house": 2},
        {"name": "Saturn", "sign_number": 10, "house": 10},
        {"name": "Rahu", "sign_number": 11, "house": 11},
        {"name": "Ketu", "sign_number": 5, "house": 5},
    ]
    d9_planets = [
        {**planet, "house": 7 if planet["name"] in {"Venus", "Jupiter"} else planet["house"]}
        for planet in planets
    ]
    return {
        "metadata": {
            "name": "Parity Chart",
            "birth_date": "1990-01-02",
            "birth_time": "10:30",
            "calculation_version": "test-v1",
        },
        "lagna": {"sign_number": 1},
        "planets": planets,
        "vargas": {"D9": {"planets": d9_planets}},
        "jaimini": {
            "chara_karakas": {"Darakaraka": "Venus"},
            "arudhas": {"Upapada": 12, "A7": 7},
        },
        "kp_system": {
            "significators": {
                "houses": {
                    7: {
                        "house_lord": "Venus",
                        "occupants": ["Mars"],
                        "significators": ["Mars", "Venus"],
                        "cusp": {"star_lord": "Jupiter", "sub_lord": "Saturn"},
                    }
                }
            }
        },
        "parashara_yogas": [
            {
                "id": "mangala_dosha",
                "name": "Mangala Dosha",
                "cause_en": "Mars occupies the seventh house.",
                "cause_ne": "मङ्गल सप्तम भावमा छ।",
            }
        ],
        "dasha": [
            {"lord": "Venus", "children": [{"lord": "Mars"}, {"lord": "Jupiter"}]},
            {"lord": "Sun", "children": [{"lord": "Moon"}]},
        ],
    }


class MarriageAnalysisModelTests(unittest.TestCase):
    def test_authoritative_factors_are_mapped_without_prediction_fields(self):
        model = build_marriage_analysis_model(sample_payload())
        self.assertEqual(model["state"], "ready")
        self.assertEqual(model["seventh_sign"], 7)
        self.assertEqual(model["seventh_lord"], "Venus")
        self.assertEqual(model["seventh_lord_house"], 2)
        self.assertEqual(model["seventh_occupants"], ["Mars"])
        self.assertEqual(model["darakaraka"], "Venus")
        self.assertEqual(model["upapada_sign"], 12)
        self.assertEqual(model["upapada_house"], 12)
        self.assertEqual(model["a7_sign"], 7)
        self.assertTrue(model["kp"]["available"])
        self.assertEqual(model["kp"]["sub_lord"], "Saturn")
        self.assertEqual(model["d9_seventh_occupants"], ["Mars", "Jupiter", "Venus"])
        self.assertTrue(model["mangal_present"])
        self.assertEqual(model["mahadasha_count"], 2)
        self.assertEqual(model["antardasha_count"], 3)
        self.assertIn("timing_formulas", model)
        self.assertIn("formula_1", model["timing_formulas"])
        self.assertIn("formula_2", model["timing_formulas"])
        self.assertNotIn("predicted_age", model)
        self.assertNotIn("marriage_type", model)


    def test_absent_mangal_yoga_is_distinct_from_missing_yoga_source(self):
        payload = sample_payload()
        payload["parashara_yogas"] = []
        self.assertFalse(build_marriage_analysis_model(payload)["mangal_present"])
        payload.pop("parashara_yogas")
        self.assertIsNone(build_marriage_analysis_model(payload)["mangal_present"])

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_marriage_analysis_model(None)["state"], "no_chart")
        self.assertEqual(build_marriage_analysis_model({})["state"], "empty")
        self.assertEqual(build_marriage_analysis_model({"lagna": {"sign_number": 1}, "planets": "bad"})["state"], "empty")
        error = build_marriage_analysis_model({"error": "calculation failed"})
        self.assertEqual(error, {"state": "error", "message": "calculation failed"})


class MarriageAnalysisWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_domain_sections_and_explicit_prediction_state(self):
        page = MarriageAnalysisPage(sample_payload(), "en")
        self.assertEqual(page._model["state"], "ready")
        self.assertEqual(len(page.findChildren(QLabel, "marriageAnalysisHeader")), 1)
        self.assertEqual(len(page.findChildren(QFrame, "marriageAnalysisCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Marriage Analysis", labels)
        self.assertIn("1. Astrological Foundation of Marriage", labels)
        self.assertIn("3. Marriage Timing & Opportunities", labels)
        self.assertIn("4. Probable Marriage Direction", labels)
        self.assertIn("7. Remedies & Guidance", labels)
        page.deleteLater()

    def test_ready_page_ne_renders_unified_marriage_timing_and_dms(self):
        page = MarriageAnalysisPage(sample_payload(), "ne")
        self.assertEqual(page._model["state"], "ready")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("विवाह विश्लेषण", labels)
        self.assertIn("विवाह समय निर्धारण गर्ने संयुक्त सूत्र", labels)
        self.assertIn("सूत्र–१", labels)
        self.assertIn("सूत्र–२", labels)
        page.deleteLater()


    def test_no_chart_page_has_explicit_state(self):
        page = MarriageAnalysisPage(None, "en")
        state = page.findChild(QLabel, "marriageAnalysisState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a birth chart first", state.text())
        page.deleteLater()

    def test_existing_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_marriage_analysis")
        self.assertIsInstance(page, MarriageAnalysisPage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
