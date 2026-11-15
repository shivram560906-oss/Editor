import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QLabel

from gui.app import JyotishMainWindow
from gui.widgets.north_indian_chart import (
    CHART_BG,
    CHART_LINE,
    CHART_MAX_SIZE,
    CHART_MIN_SIZE,
    NorthIndianChartPage,
    NorthIndianChartWidget,
    chart_page_model,
    planet_label_positions,
)
from gui.widgets.bhava_chalit import BhavaChalitPage
from gui.widgets.vargas_grid import SudarshanChakraPage, sudarshan_model


def sample_data():
    names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    planets = [
        {
            "name": name,
            "house": index + 1,
            "sign_number": index + 1,
            "longitude_in_sign": 10.0 + index,
            "relationship": "friend" if index % 3 == 0 else "neutral",
            "exaltation_state": "exalted" if name == "Sun" else "",
            "is_retrograde": name in ("Saturn", "Rahu"),
            "is_combust": name == "Mercury",
        }
        for index, name in enumerate(names)
    ]
    d9 = [{**planet, "house": (index + 4) % 12 + 1, "sign_number": (index + 4) % 12 + 1} for index, planet in enumerate(planets)]
    d10 = [{**planet, "house": (index + 7) % 12 + 1, "sign_number": (index + 7) % 12 + 1} for index, planet in enumerate(planets)]
    return {
        "metadata": {"name": "Test Native", "birth_date": "2000-01-01", "birth_time": "10:30:00", "city": "Kathmandu", "ayanamsha_type": "LAHIRI"},
        "lagna": {"sign_number": 1, "longitude_in_sign": 12.5},
        "planets": planets,
        "vargas": {
            "D1": {"lagna": {"sign_number": 1, "longitude_in_sign": 12.5}, "planets": planets},
            "D9": {"lagna": {"sign_number": 5, "longitude_in_sign": 2.5}, "planets": d9},
            "D10": {"lagna": {"sign_number": 8, "longitude_in_sign": 5.5}, "planets": d10},
        },
        "parashara_yogas": [{"id": "sample", "name": "Sample Yoga"}],
        "jaimini": {"sign_aspects": {"by_planet": {"Sun": [4, 7, 10]}}},
    }


class NativeChartParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_dedicated_chart_identity_and_palette(self):
        data = sample_data()
        for code, expected_lagna in (("D1", 1), ("D9", 5), ("D10", 8)):
            model = chart_page_model(data, code, "en")
            self.assertEqual(model["identity"], code)
            self.assertEqual(model["lagna"]["sign_number"], expected_lagna)
            self.assertEqual(len(model["planets"]), 9)
            self.assertEqual(model["palette"]["background"], CHART_BG)
            self.assertEqual(model["palette"]["line"], CHART_LINE)
            self.assertEqual(model["dimensions"]["minimum"], CHART_MIN_SIZE)
            self.assertEqual(model["dimensions"]["maximum"], CHART_MAX_SIZE)

    def test_every_displayed_planet_is_hit_selectable(self):
        data = sample_data()
        widget = NorthIndianChartWidget(data, "D1", "en")
        widget.resize(500, 500)
        selected = []
        widget.planet_selected.connect(selected.append)
        positions = planet_label_positions(widget._get_varga_planets())
        self.assertEqual({item["name"] for item in positions}, {p["name"] for p in data["planets"]})
        for item in positions:
            hit = widget._planet_at(QPoint(round(item["x"]), round(item["y"])))
            self.assertEqual(hit, item["name"])
            widget._select = hit
        self.assertIn("Sun", {item["name"] for item in positions})
        self.assertIn("Moon", {item["name"] for item in positions})
        self.assertIn("Venus", {item["name"] for item in positions})

    def test_selection_keeps_chart_and_detail_dimensions_stable(self):
        page = NorthIndianChartPage(sample_data(), "D1", "en")
        chart = page._chart_widget
        detail = page.findChild(QLabel, "planetDetail")
        before = (chart.minimumSize(), chart.maximumSize(), detail.minimumHeight())
        for name in ("Sun", "Moon", "Venus", "Ketu"):
            page._select_planet(name)
            self.assertTrue(len(detail.text().strip()) > 10)
            self.assertEqual((chart.minimumSize(), chart.maximumSize(), detail.minimumHeight()), before)

    def test_sudarshan_has_three_actual_reference_rings(self):
        data = sample_data()
        model = sudarshan_model(data, "en")
        self.assertEqual(model["identity"], "sudarshan")
        self.assertEqual([ring["key"] for ring in model["rings"]], ["sun", "moon", "lagna"])
        self.assertEqual([ring["reference_sign"] for ring in model["rings"]], [1, 2, 1])
        self.assertTrue(all(len(ring["houses"]) == 12 for ring in model["rings"]))
        moon_ring = model["rings"][1]
        self.assertEqual(moon_ring["houses"][0]["sign"], 2)
        self.assertEqual(moon_ring["houses"][0]["planets"][0]["name"], "Moon")
        page = SudarshanChakraPage(data, "en")
        self.assertEqual(page._model["planet_count"], 9)
        self.assertIsNotNone(page.findChild(QLabel, "sudarshanLegend"))

    def test_false_alias_routes_are_explicitly_unavailable(self):
        source = Path("gui/app.py").read_text(encoding="utf-8")
        self.assertIn('if view_id == "chart_sudarshan":', source)
        self.assertNotIn('view_id == "chart_rashi" or view_id == "chart_bhava_chalit"', source)
        self.assertNotIn('if view_id == "chart_hora_lagna":', source)
        self.assertNotIn('if view_id in ("chart_sudarshan", "chart_special_chakras"):', source)
        owner = type("Owner", (), {"_chart_data": sample_data(), "_language": "en"})()
        # Only genuinely unsupported pseudo-routes must resolve to None.
        for action in ("chart_hora_lagna", "chart_special_chakras"):
            self.assertIsNone(JyotishMainWindow._build_page(owner, action))
        # chart_bhava_chalit and chart_sudarshan are real dedicated pages.
        self.assertIsInstance(JyotishMainWindow._build_page(owner, "chart_bhava_chalit"), BhavaChalitPage)
        self.assertIsInstance(JyotishMainWindow._build_page(owner, "chart_sudarshan"), SudarshanChakraPage)


    def test_planet_analysis_dialog_all_planets(self):
        from gui.widgets.planet_analysis_dialog import PlanetAnalysisDialog, PlanetReasonsDialog
        data = sample_data()
        page = NorthIndianChartPage(data, "D1", "ne")
        page.show()

        for planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            page._select_planet(planet_name)
            self.assertFalse(page._btn_full_report.isHidden())
            dlg = PlanetAnalysisDialog(planet_name, data, page)
            self.assertIsNotNone(dlg)
            self.assertIn("shubha_pct", dlg._report)
            self.assertIn("ashubha_pct", dlg._report)
            self.assertEqual(dlg._report["shubha_pct"] + dlg._report["ashubha_pct"], 100)
            reasons_dlg = PlanetReasonsDialog(planet_name, dlg._report, dlg)
            self.assertIsNotNone(reasons_dlg)

    def test_samudaya_ashtakavarga_on_d1_page(self):
        from gui.widgets.ashtakavarga import SamudayaAshtakavargaChartWidget, AshtakavargaPage
        data = sample_data()
        page = NorthIndianChartPage(data, "D1", "ne")
        self.assertTrue(hasattr(page, "_sav_chart_widget"))
        self.assertIsInstance(page._sav_chart_widget, SamudayaAshtakavargaChartWidget)
        self.assertEqual(len(page._sav_chart_widget._sav_scores), 12)

        # Ensure AshtakavargaPage also works as intended
        av_page = AshtakavargaPage(data, "ne")
        self.assertIsNotNone(av_page)
        self.assertIsInstance(av_page._chart_widget, SamudayaAshtakavargaChartWidget)


if __name__ == "__main__":
    unittest.main()
