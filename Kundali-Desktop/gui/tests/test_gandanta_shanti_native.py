# -*- coding: utf-8 -*-
"""
gui/tests/test_gandanta_shanti_native.py

UI tests for the Gandanta & Arishta Janma Shanti page and model builder.
"""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.gandanta_shanti import GandantaShantiPage, build_gandanta_shanti_model


def sample_chart_payload() -> dict:
    return {
        "metadata": {
            "name": "Gandanta Test Chart",
            "birth_date": "2024-05-15",
            "birth_time": "12:30",
        },
        "lagna": {"sign_number": 1, "longitude": 15.0},
        "planets": {
            "Sun": {"sign_number": 2, "longitude": 35.0},
            "Moon": {"sign_number": 9, "longitude": 240.2}, # Moola Pada 1 (Abhukta Moola)
            "Mars": {"sign_number": 12, "longitude": 345.0},
            "Mercury": {"sign_number": 1, "longitude": 22.0},
            "Jupiter": {"sign_number": 1, "longitude": 25.0}, # Kendra (Arishta Bhanga)
            "Venus": {"sign_number": 2, "longitude": 40.0},
            "Saturn": {"sign_number": 11, "longitude": 320.0},
            "Rahu": {"sign_number": 12, "longitude": 350.0},
            "Ketu": {"sign_number": 6, "longitude": 170.0},
        }
    }


class TestGandantaShantiNative(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_model_states(self):
        # None -> no_chart
        self.assertEqual(build_gandanta_shanti_model(None)["state"], "no_chart")

        # Empty dict -> empty
        self.assertEqual(build_gandanta_shanti_model({})["state"], "empty")

        # Incomplete dict -> empty
        self.assertEqual(build_gandanta_shanti_model({"lagna": {"sign_number": 1}})["state"], "empty")

        # Valid payload -> success
        m = build_gandanta_shanti_model(sample_chart_payload())
        self.assertEqual(m["state"], "success")
        self.assertTrue(m["nakshatra_gandanta"]["is_abhukta_moola"])
        self.assertTrue(m["is_arishta_bhanga"])
        self.assertIsNotNone(m["remedies"])

    def test_widget_rendering_empty(self):
        page = GandantaShantiPage(None, language="ne")
        header = page.findChild(QLabel, "gandantaShantiHeader")
        self.assertIsNotNone(header)
        state_label = page.findChild(QLabel, "gandantaShantiState")
        self.assertIsNotNone(state_label)
        self.assertIn("कुण्डली गणना", state_label.text())

    def test_widget_rendering_populated(self):
        payload = sample_chart_payload()
        page = GandantaShantiPage(payload, language="ne")
        header = page.findChild(QLabel, "gandantaShantiHeader")
        self.assertIsNotNone(header)
        self.assertIn("गण्डान्त", header.text())

        banner = page.findChild(QLabel, "gandantaStatusBanner")
        self.assertIsNotNone(banner)
        self.assertIn("गण्डान्त", banner.text())

    def test_app_page_factory(self):
        owner = JyotishMainWindow.__new__(JyotishMainWindow)
        owner._chart_data = sample_chart_payload()
        owner._language = "ne"
        owner._is_ne = True

        page1 = JyotishMainWindow._build_page(owner, "gandanta_shanti")
        self.assertIsInstance(page1, GandantaShantiPage)

        page2 = JyotishMainWindow._build_page(owner, "report_gandanta_shanti")
        self.assertIsInstance(page2, GandantaShantiPage)

    def test_list_format_planets_real_app(self):
        # In real desktop calculation, chart_data["planets"] is a list of dicts
        list_payload = {
            "metadata": {"name": "List Payload", "birth_time": "14:00"},
            "lagna": {"sign_number": 1, "longitude": 10.0},
            "planets": [
                {"name": "Sun", "sign_number": 1, "longitude": 12.0},
                {"name": "Moon", "sign_number": 9, "longitude": 240.2},
                {"name": "Jupiter", "sign_number": 4, "longitude": 100.0},
            ]
        }
        m = build_gandanta_shanti_model(list_payload)
        self.assertEqual(m["state"], "success")
        self.assertTrue(m["nakshatra_gandanta"]["is_sandhi_gandanta"])

    def test_action_normalization(self):
        from gui.app import normalize_action_id
        self.assertEqual(normalize_action_id("report_gandanta_shanti"), "report_gandanta_shanti")
        self.assertEqual(normalize_action_id("gandanta_shanti"), "report_gandanta_shanti")
        self.assertEqual(normalize_action_id("gandanta"), "report_gandanta_shanti")
        self.assertEqual(normalize_action_id("shanti"), "report_gandanta_shanti")


if __name__ == "__main__":
    unittest.main()
