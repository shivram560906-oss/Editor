# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.planet_strength_profile import PlanetStrengthProfilePage, build_planet_strength_model


def sample_payload() -> dict:
    planets = [
        {"name": "Sun", "sign_number": 5, "house": 5, "is_combust": True, "nakshatra_name": "Magha"},
        {"name": "Moon", "sign_number": 4, "house": 4, "nakshatra_name": "Pushya"},
        {"name": "Mars", "sign_number": 7, "house": 7, "is_retrograde": True, "nakshatra_name": "Chitra"},
        {"name": "Mercury", "sign_number": 6, "house": 6, "nakshatra_name": "Hasta"},
        {"name": "Jupiter", "sign_number": 9, "house": 9, "exaltation_state": "exalted", "nakshatra_name": "Mula"},
        {"name": "Venus", "sign_number": 2, "house": 2, "nakshatra_name": "Rohini"},
        {"name": "Saturn", "sign_number": 10, "house": 10, "nakshatra_name": "Uttara Ashadha"},
        {"name": "Rahu", "sign_number": 11, "house": 11, "nakshatra_name": "Purva Bhadrapada"},
        {"name": "Ketu", "sign_number": 12, "house": 12, "nakshatra_name": "Uttara Bhadrapada"},
    ]
    return {
        "metadata": {"name": "Strength Chart", "birth_date": "1990-01-02"},
        "lagna": {"sign_number": 1},
        "planets": planets,
        "shadbala": {
            "ranking": ["Jupiter", "Sun", "Venus", "Mercury", "Moon", "Mars", "Saturn"],
            "planets": {
                "Sun": {
                    "components": {
                        "sthana": {"shashtiamsa": 90.0, "rupa": 1.5},
                        "dig": {"shashtiamsa": 60.0, "rupa": 1.0},
                        "kala": {"shashtiamsa": 120.0, "rupa": 2.0},
                        "cheshta": {"shashtiamsa": 30.0, "rupa": 0.5},
                        "naisargika": {"shashtiamsa": 60.0, "rupa": 1.0},
                        "drik": {"shashtiamsa": 30.0, "rupa": 0.5},
                    },
                    "total_shashtiamsa": 390.0,
                    "total_rupas": 6.5,
                    "required_rupas": 6.0,
                    "is_strong": True,
                },
                "Moon": {
                    "components": {
                        "sthana": {"shashtiamsa": 30.0, "rupa": 0.5},
                        "dig": {"shashtiamsa": 60.0, "rupa": 1.0},
                        "kala": {"shashtiamsa": 60.0, "rupa": 1.0},
                    },
                    "total_shashtiamsa": 150.0,
                    "total_rupas": 2.5,
                    "required_rupas": 3.0,
                    "is_strong": False,
                },
                "Mars": {
                    "components": {
                        "sthana": {"shashtiamsa": 45.0, "rupa": 0.75},
                        "dig": {"shashtiamsa": 30.0, "rupa": 0.5},
                        "kala": {"shashtiamsa": 60.0, "rupa": 1.0},
                    },
                    "total_shashtiamsa": 135.0,
                    "total_rupas": 2.25,
                    "required_rupas": 5.0,
                    "is_strong": False,
                },
                "Mercury": {
                    "components": {
                        "sthana": {"shashtiamsa": 60.0, "rupa": 1.0},
                        "dig": {"shashtiamsa": 30.0, "rupa": 0.5},
                        "kala": {"shashtiamsa": 90.0, "rupa": 1.5},
                    },
                    "total_shashtiamsa": 180.0,
                    "total_rupas": 3.0,
                    "required_rupas": 7.0,
                    "is_strong": False,
                },
                "Jupiter": {
                    "components": {
                        "sthana": {"shashtiamsa": 120.0, "rupa": 2.0},
                        "dig": {"shashtiamsa": 120.0, "rupa": 2.0},
                        "kala": {"shashtiamsa": 120.0, "rupa": 2.0},
                        "cheshta": {"shashtiamsa": 120.0, "rupa": 2.0},
                        "naisargika": {"shashtiamsa": 120.0, "rupa": 2.0},
                        "drik": {"shashtiamsa": 120.0, "rupa": 2.0},
                    },
                    "total_shashtiamsa": 720.0,
                    "total_rupas": 12.0,
                    "required_rupas": 6.5,
                    "is_strong": True,
                },
                "Venus": {
                    "components": {
                        "sthana": {"shashtiamsa": 90.0, "rupa": 1.5},
                        "dig": {"shashtiamsa": 60.0, "rupa": 1.0},
                        "kala": {"shashtiamsa": 60.0, "rupa": 1.0},
                    },
                    "total_shashtiamsa": 210.0,
                    "total_rupas": 3.5,
                    "required_rupas": 5.5,
                    "is_strong": False,
                },
                "Saturn": {
                    "components": {
                        "sthana": {"shashtiamsa": 90.0, "rupa": 1.5},
                        "dig": {"shashtiamsa": 90.0, "rupa": 1.5},
                        "kala": {"shashtiamsa": 90.0, "rupa": 1.5},
                    },
                    "total_shashtiamsa": 270.0,
                    "total_rupas": 4.5,
                    "required_rupas": 3.0,
                    "is_strong": True,
                },
            },
        },
        "avasthas": {
            "planets": {
                "Sun": {
                    "sign_number": 5,
                    "longitude_in_sign": 30.0,
                    "bala_avastha": {"state": "shishira", "nepali": "शिशिर"},
                    "deeptadi_avastha": {"state": "deepta", "nepali": "दीप्त"},
                },
                "Jupiter": {
                    "sign_number": 9,
                    "longitude_in_sign": 120.0,
                    "bala_avastha": {"state": "kishora", "nepali": "किशोर"},
                    "deeptadi_avastha": {"state": "deepta", "nepali": "दीप्त"},
                },
                "Moon": {
                    "sign_number": 4,
                    "longitude_in_sign": 80.0,
                    "bala_avastha": {"state": "yuva", "nepali": "युवा"},
                    "deeptadi_avastha": {"state": "swastha", "nepali": "स्वस्थ"},
                },
                "Mars": {
                    "sign_number": 7,
                    "longitude_in_sign": 150.0,
                    "bala_avastha": {"state": "vriddha", "nepali": "वृद्ध"},
                    "deeptadi_avastha": {"state": "kula", "nepali": "कुल"},
                },
                "Mercury": {
                    "sign_number": 6,
                    "longitude_in_sign": 100.0,
                    "bala_avastha": {"state": "mrita", "nepali": "मृत"},
                    "deeptadi_avastha": {"state": "nisha", "nepali": "निशा"},
                },
                "Venus": {
                    "sign_number": 2,
                    "longitude_in_sign": 40.0,
                    "bala_avastha": {"state": "kishora", "nepali": "किशोर"},
                    "deeptadi_avastha": {"state": "swastha", "nepali": "स्वस्थ"},
                },
                "Saturn": {
                    "sign_number": 10,
                    "longitude_in_sign": 200.0,
                    "bala_avastha": {"state": "vriddha", "nepali": "वृद्ध"},
                    "deeptadi_avastha": {"state": "sakta", "nepali": "सक्त"},
                },
            }
        },
    }


class PlanetStrengthProfileModelTests(unittest.TestCase):
    def test_authoritative_shadbala_and_avastha_facts_are_mapped(self):
        model = build_planet_strength_model(sample_payload())
        self.assertEqual(model["state"], "ready")
        self.assertEqual(model["lagna_sign"], 1)

        rows = {row["name"]: row for row in model["rows"]}
        self.assertEqual(len(rows), 7)

        jupiter = rows["Jupiter"]
        self.assertEqual(jupiter["sign"], 9)
        self.assertEqual(jupiter["house"], 9)
        self.assertEqual(jupiter["exaltation_state"], "exalted")
        self.assertAlmostEqual(jupiter["total_shashtiamsa"], 720.0)
        self.assertAlmostEqual(jupiter["total_rupas"], 12.0)
        self.assertAlmostEqual(jupiter["required_rupas"], 6.5)
        self.assertTrue(jupiter["is_strong"])
        self.assertAlmostEqual(jupiter["components"]["sthana"], 2.0)
        self.assertAlmostEqual(jupiter["components"]["cheshta"], 2.0)
        self.assertAlmostEqual(jupiter["components"]["drik"], 2.0)
        self.assertEqual(jupiter["bala_avastha"]["nepali"], "किशोर")
        self.assertEqual(jupiter["deeptadi_avastha"]["nepali"], "दीप्त")

        saturn = rows["Saturn"]
        self.assertTrue(saturn["is_strong"])
        self.assertAlmostEqual(saturn["total_rupas"], 4.5)

        mars = rows["Mars"]
        self.assertTrue(mars["retrograde"])
        self.assertFalse(mars["is_strong"])

        sun = rows["Sun"]
        self.assertTrue(sun["combust"])
        self.assertTrue(sun["is_strong"])

        self.assertEqual(model["strong_count"], 3)
        self.assertEqual(model["weak_count"], 4)

    def test_ranking_drives_row_order_and_fallback_to_rupas(self):
        payload = sample_payload()
        model = build_planet_strength_model(payload)
        self.assertEqual([row["name"] for row in model["rows"]], [
            "Jupiter", "Sun", "Venus", "Mercury", "Moon", "Mars", "Saturn",
        ])

        # total_rupas removed → converted from total_shashtiamsa / 60
        for name in ("Sun", "Mars"):
            del payload["shadbala"]["planets"][name]["total_rupas"]
        model = build_planet_strength_model(payload)
        sun = next(row for row in model["rows"] if row["name"] == "Sun")
        self.assertAlmostEqual(sun["total_rupas"], 6.5)
        mars = next(row for row in model["rows"] if row["name"] == "Mars")
        self.assertAlmostEqual(mars["total_rupas"], 2.25)

    def test_no_chart_empty_malformed_and_error_states(self):
        self.assertEqual(build_planet_strength_model(None)["state"], "no_chart")
        self.assertEqual(build_planet_strength_model({})["state"], "empty")
        self.assertEqual(build_planet_strength_model({"lagna": {"sign_number": 1}})["state"], "empty")
        self.assertEqual(
            build_planet_strength_model({"error": "failed"}),
            {"state": "error", "message": "failed"},
        )


class PlanetStrengthProfileWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ready_page_is_plain_document_with_strength_chapters(self):
        page = PlanetStrengthProfilePage(sample_payload(), "en")
        self.assertEqual(len(page.findChildren(QFrame, "planetStrengthCard")), 0)
        self.assertEqual(page.objectName(), "lifeAnalysisDocumentPage")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Planet Strength Profile", labels)
        self.assertIn("Shadbala Overview", labels)
        self.assertIn("Strong Grahas", labels)
        self.assertIn("Weak Grahas", labels)
        self.assertIn("Sub-strength Breakdown", labels)
        self.assertIn("Conclusion", labels)
        self.assertIn("Jupiter", labels)
        page.deleteLater()

    def test_nepali_page_renders_nepali_chapters_and_facts(self):
        page = PlanetStrengthProfilePage(sample_payload(), "ne")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("ग्रह शक्ति प्रोफाइल", labels)
        self.assertIn("षड्बल सिंहावलोकन", labels)
        self.assertIn("बलवान् ग्रहहरू", labels)
        self.assertIn("निर्बल ग्रहहरू", labels)
        self.assertIn("बृहस्पति", labels)
        page.deleteLater()

    def test_no_chart_page_has_explicit_state(self):
        page = PlanetStrengthProfilePage(None, "en")
        state = page.findChild(QLabel, "planetStrengthState")
        self.assertIsNotNone(state)
        self.assertIn("Calculate a chart", state.text())
        page.deleteLater()

    def test_existing_action_routes_to_dedicated_page(self):
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_planet_strength")
        self.assertIsInstance(page, PlanetStrengthProfilePage)
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
