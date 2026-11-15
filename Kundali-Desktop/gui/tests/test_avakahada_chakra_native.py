# -*- coding: utf-8 -*-
"""Headless checks for the native Avakahada Chakra restoration."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from gui.app import NAV_STRUCTURE, JyotishMainWindow, normalize_action_id
from gui.widgets.avakahada_chakra import (
    UNAVAILABLE,
    AvakahadaChakraPage,
    build_avakahada_model,
    compose_avakahada_text,
)


def sample_payload() -> dict:
    return {
        "metadata": {
            "birth_date": "2000-04-15",
            "birth_time": "10:30:00",
            "city": "Kathmandu",
        },
        "panchang": {"nakshatra": {"name": "Rohini", "nepali": "रोहिणी"}},
        "avakahada_chakra": {
            "nakshatra": "Rohini",
            "pada": 2,
            "name_akshara": "वि",
            "rashi": "Vrishabha",
            "rashi_lord": "Venus",
            "varna": "Vaishya",
            "vashya": "Chatushpada",
            "yoni": "Serpent",
            "viryoni": "Mongoose",
            "varga": "Ka",
            "shatru_varga": "Cha",
            "gana": "Manushya",
            "nadi": "Antya",
            "asana": 0,
        },
    }


class AvakahadaActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_legacy_and_current_actions_resolve_to_distinct_native_reports(self):
        for action_id in ("birth_panchang", "report_birth_panchang"):
            self.assertEqual(normalize_action_id(action_id), "report_birth_panchang")
        for action_id in ("avakahada_chakra", "report_avakahada_chakra"):
            self.assertEqual(normalize_action_id(action_id), "report_avakahada_chakra")

    def test_page_dispatch_constructs_native_widget(self):
        owner = type("PageOwner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        page = JyotishMainWindow._build_page(owner, "report_avakahada_chakra")
        self.assertIsInstance(page, AvakahadaChakraPage)
        self.assertEqual(page.state, "ready")


class AvakahadaModelTests(unittest.TestCase):
    def test_representative_payload_preserves_all_web_report_rows(self):
        model = build_avakahada_model(sample_payload(), "en")
        self.assertEqual(model["state"], "ready")
        self.assertEqual(len(model["rows"]), 17)
        values = {row["key"]: row["value"] for row in model["rows"]}
        self.assertEqual(values["nakshatra"], "Rohini")
        self.assertEqual(values["name_akshara"], "वि")
        self.assertEqual(values["shatru_varga"], "Cha")
        self.assertEqual(values["asana"], "0")
        report = compose_avakahada_text(model)
        self.assertIn("Birth Place: Kathmandu", report)
        self.assertIn("Vair Yoni: Mongoose", report)

    def test_empty_incomplete_and_error_states_are_explicit(self):
        self.assertEqual(build_avakahada_model(None, "en")["state"], "no_chart")
        self.assertEqual(build_avakahada_model({"metadata": {}}, "en")["state"], "empty")
        self.assertEqual(build_avakahada_model({"avakahada_chakra": "bad"}, "en")["state"], "error")
        self.assertEqual(build_avakahada_model({"error": "Calculation failed"}, "en")["message"], "Calculation failed")

        incomplete = build_avakahada_model({"avakahada_chakra": {"pada": 1}}, "en")
        self.assertEqual(incomplete["state"], "incomplete")
        values = {row["key"]: row["value"] for row in incomplete["rows"]}
        self.assertEqual(values["pada"], "1")
        self.assertEqual(values["gana"], UNAVAILABLE)


class AvakahadaPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_page_renders_payload_and_copies_report(self):
        page = AvakahadaChakraPage(sample_payload(), "en")
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        for text in ("Avakahada Chakra", "Name Akshara", "वि", "Shatru Varga", "Cha", "Asana", "0"):
            self.assertIn(text, labels)

        page.copy_report()
        self.assertEqual(QApplication.clipboard().text(), page.report_text)
        self.assertEqual(len(page.report_text.splitlines()), 17)

    def test_page_refreshes_through_all_state_views(self):
        page = AvakahadaChakraPage(None, "en")
        self.assertEqual(page.state, "no_chart")
        self.assertIn("calculate a chart", page.findChild(QLabel, "avakahadaState").text())

        page.refresh({"metadata": {}})
        self.assertEqual(page.state, "empty")
        self.assertIn("not available", page.findChild(QLabel, "avakahadaState").text())

        page.refresh({"avakahada_chakra": []})
        self.assertEqual(page.state, "error")
        self.assertIn("invalid format", page.findChild(QLabel, "avakahadaState").text())

        page.refresh({"avakahada_chakra": {"pada": 4}})
        self.assertEqual(page.state, "incomplete")
        self.assertIn("unavailable", page.findChild(QLabel, "avakahadaState").text())


class NativeRouteCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.owner = type(
            "PageOwner",
            (),
            {"_chart_data": {
                "metadata": {"birth_date": "2000-04-15", "birth_time": "10:30:00"},
                "lagna": {"sign_number": 1, "longitude_in_sign": 12.5},
                "planets": [],
                "vargas": {},
                "dasha": [],
                "yogini_dasha": [],
            }, "_language": "en"},
        )()

    def test_foundational_aliases_normalize_to_native_routes(self):
        expected = {
            "hora_lagna": "chart_hora_lagna",
            "kundali_hora": "chart_hora_lagna",
            "special_chakras": "chart_special_chakras",
            "calc_detailed_shad_bala": "report_shadbala",
            "calc_ashtakavarga_summary": "report_ashtakavarga",
            "calc_krishnamurti_chart": "report_kp_system",
            "jaimini": "report_jaimini_analysis",
            "vimshottari_dasha": "report_complete_dasha",
            "dasha_vimshottari": "report_complete_dasha",
            "report_vimshottari": "report_complete_dasha",
        }
        for action_id, canonical_id in expected.items():
            with self.subTest(action_id=action_id):
                self.assertEqual(normalize_action_id(action_id), canonical_id)

        dasha_items = next(category for category in NAV_STRUCTURE if category["id"] == "dasha")["items"]
        visible_ids = [item["id"] for item in dasha_items]
        self.assertIn("report_complete_dasha", visible_ids)
        self.assertNotIn("report_vimshottari", visible_ids)
        self.assertNotIn("report_yogini_dasha", visible_ids)

        owner = type("PageOwner", (), {"_chart_data": {}, "_language": "en"})()
        self.assertIsNone(JyotishMainWindow._build_page(owner, "report_vimshottari"))

    def test_foundational_actions_build_real_native_pages(self):
        from gui.widgets.ashtakavarga import AshtakavargaPage
        from gui.widgets.complete_dasha import CompleteDashaPage
        from gui.widgets.dasha_gochar_widget import DashaGocharPage
        from gui.widgets.jaimini_kp import JaiminiPage, KPSystemPage
        from gui.widgets.janmapatrika_widget import JanmapatrikaPage
        from gui.widgets.life_analysis import DashaPhalPage
        from gui.widgets.north_indian_chart import NorthIndianChartPage
        from gui.widgets.panchang_info import PanchangInfoPage
        from gui.widgets.sadesati import SadeSatiPage
        from gui.widgets.shadbala_widget import ShadbalaPage
        from gui.widgets.vargas_grid import VargasGridPage
        from gui.widgets.yoga_report import YogaReportPage

        expected_pages = {
            "chart_rashi": NorthIndianChartPage,
            "chart_navamsha": NorthIndianChartPage,
            "chart_vargas": VargasGridPage,
            "report_dasha_gochar_timeline": DashaGocharPage,
            "report_dasha_transit_timeline": DashaGocharPage,
            "report_dasha_phal": CompleteDashaPage,
            "report_yogini": CompleteDashaPage,
            "report_complete_dasha": CompleteDashaPage,
            "report_sadesati_adhaiya": SadeSatiPage,
            "report_panchang": PanchangInfoPage,
            "report_ashtakavarga": AshtakavargaPage,
            "report_shadbala": ShadbalaPage,
            "report_yogas": YogaReportPage,
            "kundali_nirman": JanmapatrikaPage,
            "report_jaimini_analysis": JaiminiPage,
            "report_kp_system": KPSystemPage,
        }
        for action_id, page_type in expected_pages.items():
            with self.subTest(action_id=action_id):
                page = JyotishMainWindow._build_page(self.owner, action_id)
                self.assertIsInstance(page, page_type)

        for action_id in ("chart_hora_lagna", "chart_special_chakras"):
            with self.subTest(action_id=action_id):
                self.assertIsNone(JyotishMainWindow._build_page(self.owner, action_id))


if __name__ == "__main__":
    unittest.main()
