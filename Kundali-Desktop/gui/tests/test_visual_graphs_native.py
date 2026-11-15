# -*- coding: utf-8 -*-
"""Headless parity checks for authoritative native visual graph data."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from gui.widgets.visual_graphs import AstroVisualGraphsPage, build_visual_graphs_model


def sample_payload() -> dict:
    component_values = {
        "sthana": 120.0,
        "dig": 40.0,
        "kala": 100.0,
        "cheshta": 30.0,
        "naisargika": 60.0,
        "drik": 20.0,
    }
    planets = {}
    for index, name in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")):
        offset = float(index)
        components = {
            key: {"shashtiamsa": value + offset}
            for key, value in component_values.items()
        }
        planets[name] = {
            "total_shashtiamsa": sum(value["shashtiamsa"] for value in components.values()),
            "total_rupas": sum(value["shashtiamsa"] for value in components.values()) / 60.0,
            "components": components,
        }
    return {
        "shadbala": {"planets": planets, "ranking": list(planets)},
        "ashtakavarga": {"sav": [24, 28, 32, 29, 25, 33, 27, 28, 30, 26, 31, 24]},
    }


class VisualGraphModelTests(unittest.TestCase):
    def test_authoritative_backend_shape_populates_all_graph_series(self):
        model = build_visual_graphs_model(sample_payload())
        self.assertEqual(model["state"], "ready")
        self.assertEqual(len(model["shadbala"]), 7)
        self.assertEqual(len(model["breakdown"]), 7)
        self.assertEqual(len(model["sav"]), 12)
        self.assertEqual(model["shadbala"][0]["actual"], 370.0)
        self.assertAlmostEqual(model["shadbala"][0]["ratio"], 370.0 / 390.0)
        self.assertEqual(model["breakdown"][0]["sthana"], 120.0)
        self.assertEqual(model["breakdown"][0]["total"], 370.0)
        self.assertEqual(model["sav"][2], 32.0)

    def test_total_rupas_is_converted_when_shashtiamsa_is_absent(self):
        payload = {"shadbala": {"planets": {"Sun": {"total_rupas": 6.5}}}}
        model = build_visual_graphs_model(payload)
        self.assertEqual(model["state"], "ready")
        self.assertEqual(model["shadbala"][0]["actual"], 390.0)
        self.assertEqual(model["shadbala"][0]["ratio"], 1.0)

    def test_missing_or_malformed_values_never_generate_synthetic_points(self):
        self.assertEqual(build_visual_graphs_model(None)["state"], "no_chart")
        empty = build_visual_graphs_model({})
        self.assertEqual(empty["state"], "empty")
        self.assertEqual(empty["shadbala"], [])
        self.assertEqual(empty["sav"], [])
        malformed = build_visual_graphs_model({
            "shadbala": {"planets": {"Sun": {"total_shashtiamsa": "bad"}}},
            "ashtakavarga": {"sav": [28] * 11},
        })
        self.assertEqual(malformed["state"], "empty")
        self.assertEqual(malformed["shadbala"], [])
        self.assertEqual(malformed["sav"], [])

    def test_error_state_preserves_backend_message(self):
        model = build_visual_graphs_model({"error": "Calculation failed"})
        self.assertEqual(model["state"], "error")
        self.assertEqual(model["message"], "Calculation failed")


class VisualGraphWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_empty_payload_shows_explicit_state(self):
        page = AstroVisualGraphsPage({}, "en")
        page.refresh({})
        state = page.findChild(QLabel, "visualGraphsState")
        self.assertIsNotNone(state)
        self.assertEqual(state.text(), "No calculated graph data is available.")

    def test_ready_widget_retains_authoritative_model(self):
        page = AstroVisualGraphsPage(sample_payload(), "en")
        self.assertEqual(page._model["state"], "ready")
        self.assertEqual(page._model["shadbala"][0]["actual"], 370.0)


if __name__ == "__main__":
    unittest.main()
