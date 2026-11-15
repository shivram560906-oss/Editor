"""Headless checks for the restored native Janmapatrika document."""

import itertools
import math
import os
import re
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend")
))

from calculator.dasha import calculate_vimshottari_dasha
from calculator.yogini import calculate_yogini_dasha
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from gui.widgets.janmapatrika_widget import (
    UNAVAILABLE,
    JanmapatrikaPage,
    JustifiedDocumentWidget,
    build_janmapatrika_model,
    compose_janmapatrika_prose,
)
from gui.widgets.north_indian_chart import NorthIndianChartWidget


def sample_payload(gender: int = 1) -> dict:
    return {
        "metadata": {
            "name": "Fallback Name",
            "full_name": "सीता शर्मा",
            "father_name": "राम शर्मा",
            "mother_name": "गीता शर्मा",
            "gotra": "कश्यप",
            "birth_place": "Kathmandu (काठमाडौं), Nepal",
            "country": "नेपाल",
            "gender": gender,
            "birth_date": "2000-04-15",
            "birth_time": "10:30:00",
            "latitude": 27.7,
            "longitude": 85.3,
            "timezone": 5.75,
            "family_details": "संयुक्त परिवार",
            "spouse_name": "हरि शर्मा",
        },
        "panchang": {
            "samvatsara": {"nepali": "विक्रम"},
            "tithi": {"nepali": "एकादशी", "birth_nepali": "द्वादशी", "paksha_nepali": "शुक्ल पक्ष"},
            "nakshatra": {"nepali": "रोहिणी", "pada": 2},
            "yoga": {"nepali": "शुभ", "birth_nepali": "शुक्ल"},
            "karana": {"nepali": "बव", "birth_nepali": "बालव"},
            "vara": {"nepali": "शनिवार"},
            "sunrise": {"time": "06:00"},
            "sunset": {"time": "18:30"},
        },
        "panchang_requested_day": {
            "panchang": {
                "sunrise": {"time": "05:55"},
                "tithi": {"nepali": "एकादशी", "end_time": "11:55"},
                "nakshatra": {"nepali": "कृत्तिका", "end_time": "13:55"},
                "yoga": {"nepali": "सिद्ध", "end_time": "14:55"},
                "karana": {"nepali": "तैतिल", "end_time": "09:55"},
            }
        },
        "avakahada_chakra": {"name_akshara": "वि", "gana": "मनुष्य", "yoni": "सर्प"},
        "lagna": {"sign_number": 1, "longitude_in_sign": 12.5},
        "planets": [
            {"name": "Sun", "sign_number": 1, "longitude_in_sign": 2.0, "house": 1},
            {"name": "Moon", "sign_number": 2, "longitude_in_sign": 15.0, "sidereal_longitude": 45.0, "house": 2},
        ],
        "vargas": {"D9": {"lagna": {"sign_number": 3}, "planets": []}},
        "dasha": [
            {
                "lord": "Venus", "lord_nepali": "शुक्र", "start": "2000-04-15", "end": "2010-04-15",
                "is_partial": True,
                "children": [{"lord": "Venus", "lord_nepali": "शुक्र", "start": "2000-04-15", "end": "2001-01-01"}],
            }
        ],
        "yogini_dasha": [
            {
                "name": "Mangala", "nepali": "मङ्गला", "start": "2000-04-15", "end": "2001-04-15",
                "is_partial": True,
                "antardashas": [{"name": "Mangala", "nepali": "मङ्गला", "start": "2000-04-15", "end": "2000-06-01"}],
            }
        ],
    }


class JanmapatrikaModelTests(unittest.TestCase):
    def test_dynamic_metadata_corrected_phrases_and_gender(self):
        model = build_janmapatrika_model(sample_payload())
        prose = compose_janmapatrika_prose(model)

        self.assertTrue(prose.startswith("अस्य श्रीमन्नृपतिवीरविक्रमादित्यराज्यतः"))
        self.assertTrue(prose.endswith("इति प्रतिष्ठितम्।"))
        self.assertNotIn("सदैव द्विजाशीर्वादैर्दीर्घमायुर्भूयात् ॥", prose)
        self.assertEqual(model["full_name"], "सीता शर्मा")
        self.assertEqual(model["place"], "काठमाडौं")
        self.assertEqual(model["calendar"]["month"], "अप्रिल")
        self.assertEqual(model["gender_label"], "पुत्री")
        for phrase in (
            "सूर्योदयकालीन", "जन्म तिथौ", "नक्षत्रस्य समाप्तिघट्यादिः",
            "जन्मयोगः", "जन्मकरणं", "पुत्री", "सीता शर्मा",
        ):
            self.assertIn(phrase, prose)

    def test_missing_values_and_default_gender_are_explicit(self):
        model = build_janmapatrika_model({"metadata": {}})
        self.assertEqual(model["father"], UNAVAILABLE)
        self.assertEqual(model["mother"], UNAVAILABLE)
        self.assertEqual(model["gender_label"], "पुत्र")
        self.assertIn(UNAVAILABLE, compose_janmapatrika_prose(model))


class VimshottariAntardashaTests(unittest.TestCase):
    """Regression checks for the complete antardasha payload used by Janmapatrika."""

    @staticmethod
    def timeline():
        # Moon at 7.7895/27 of the zodiac puts birth near the end of Pushya,
        # so the first Saturn mahadasha is partial with only its last two
        # antardashas (Rahu and Jupiter) still running after birth.
        longitude = 7.7895 * (360.0 / 27.0)
        return calculate_vimshottari_dasha(longitude, "2023-01-01", "10:30:00")

    def test_every_mahadasha_has_complete_nine_lord_antardasha_cycle(self):
        timeline = self.timeline()
        self.assertEqual(len(timeline), 9)
        for mahadasha in timeline:
            antardashas = mahadasha.get("antardashas") or []
            self.assertEqual(len(antardashas), 9, mahadasha["lord"])
            self.assertEqual(antardashas[0]["lord"], mahadasha["lord"])
            self.assertEqual(len({item["lord"] for item in antardashas}), 9)
            for previous, current in itertools.pairwise(antardashas):
                self.assertEqual(previous["end"], current["start"])
            self.assertEqual(antardashas[-1]["end"], mahadasha["end"])
            self.assertEqual(antardashas[-1]["end_bs"], mahadasha["end_bs"])

    def test_partial_birth_mahadasha_keeps_pre_birth_antardashas(self):
        first = self.timeline()[0]
        self.assertTrue(first["is_partial"])
        self.assertEqual(first["start"], "2023-01-01")
        # The legacy visible chain drops everything completed before birth.
        self.assertLess(len(first["children"]), 9)
        antardashas = first["antardashas"]
        self.assertEqual(len(antardashas), 9)
        self.assertLess(antardashas[0]["start"], first["start"])
        # The last two antardashas (Rahu and Jupiter) are still running at birth.
        self.assertTrue(all(item["is_before_birth"] for item in antardashas[:7]))
        self.assertFalse(antardashas[7]["is_before_birth"])
        self.assertFalse(antardashas[8]["is_before_birth"])
        self.assertEqual(antardashas[-1]["end"], first["end"])


class JanmapatrikaPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _dasha_rows(html: str) -> list[str]:
        """Return the rows of the single antardasha table."""
        match = re.search(r"<table.*?</table>", html, re.DOTALL)
        if not match:
            return []
        return re.findall(r"<tr[^>]*>(.*?)</tr>", match.group(0), re.DOTALL)

    @classmethod
    def _dasha_cells(cls, html: str) -> list[list[str]]:
        """Return every row of the single antardasha table as cells."""
        return [
            re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            for row in cls._dasha_rows(html)
        ]

    def _assert_grid(self, html: str, columns: int) -> list[list[str]]:
        """Assert one independent-cell grid with a fixed column count."""
        self.assertEqual(html.count("<table"), 1)
        self.assertNotIn("colspan", html)
        self.assertNotIn("rowspan", html)
        rows = self._dasha_cells(html)
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(len(row), columns)
        self.assertEqual(rows[0][0], "दशा")
        for row in rows[1:]:
            self.assertEqual(row[0], "बाँकी उमेर")
        return rows

    def test_page_uses_website_visual_proportions_and_theme(self):
        page = JanmapatrikaPage(sample_payload())
        self.assertEqual(page._paper.width(), round(148 * 96 / 25.4))
        prose = page._paper.findChildren(JustifiedDocumentWidget)[0]
        self.assertEqual(prose.width(), round(112 * 96 / 25.4))
        self.assertGreater(prose.height(), 100)
        self.assertGreaterEqual(prose.height(), int(prose._document.documentLayout().documentSize().height()))
        self.assertEqual(prose.maximumHeight(), 16777215)

        page.show()
        self.app.processEvents()
        charts = page._paper.findChildren(NorthIndianChartWidget)
        self.assertEqual(len(charts), 2)
        for chart in charts:
            parent_rect = chart.parentWidget().contentsRect()
            self.assertLessEqual(chart.geometry().right(), parent_rect.right())
            self.assertLessEqual(chart.geometry().bottom(), parent_rect.bottom())

        blessing_text = "सदैव द्विजाशीर्वादैर्दीर्घमायुर्भूयात् ॥"
        prose_index = next(
            index for index in range(page._paper_layout.count())
            if page._paper_layout.itemAt(index).widget() is prose
        )
        prose_item = page._paper_layout.itemAt(prose_index)
        blessing_item = page._paper_layout.itemAt(prose_index + 1)
        self.assertGreaterEqual(prose_item.geometry().height(), prose.height())
        blessing = blessing_item.widget()
        self.assertIsInstance(blessing, QLabel)
        self.assertIn(blessing_text, blessing.text())
        self.assertTrue(blessing.alignment() & Qt.AlignHCenter)

        paper_style = page._paper.styleSheet()
        self.assertIn("#f1f8eb", paper_style)
        self.assertIn("#087329", paper_style)
        self.assertIn("#9b183c", page.sw_top.styleSheet())

    def test_document_zoom_controls_scale_the_complete_paper(self):
        page = JanmapatrikaPage(sample_payload())
        page.show()
        self.app.processEvents()
        self.assertEqual(page._zoom, 1.0)
        self.assertEqual(page._zoom_reset_btn.text(), "100%")
        original_scale = page._paper_proxy.scale()
        page._set_zoom(1.5)
        self.assertEqual(page._paper_proxy.scale(), 1.5)
        self.assertEqual(page._zoom_reset_btn.text(), "150%")
        self.assertGreater(page._scene.sceneRect().width(), page._paper.width())
        page._set_zoom(0.2)
        self.assertEqual(page._zoom, 0.6)
        page._set_zoom(3.0)
        self.assertEqual(page._zoom, 2.0)
        page._set_zoom(1.0)
        self.assertEqual(page._paper_proxy.scale(), original_scale)

    def test_classical_mahadasha_cycles_durations_and_remaining_age_fit(self):
        payload = sample_payload()
        vimshottari = [
            ("Sun", "सूर्य", 6), ("Moon", "चन्द्र", 10), ("Mars", "मङ्गल", 7),
            ("Rahu", "राहु", 18), ("Jupiter", "गुरु", 16), ("Saturn", "शनि", 19),
            ("Mercury", "बुध", 17), ("Ketu", "केतु", 7), ("Venus", "शुक्र", 20),
        ]
        yoginis = [
            ("Mangala", "मङ्गला", 1), ("Pingala", "पिङ्गला", 2),
            ("Dhanya", "धान्या", 3), ("Bhramari", "भ्रामरी", 4),
            ("Bhadrika", "भद्रिका", 5), ("Ulka", "उल्का", 6),
            ("Siddha", "सिद्धा", 7), ("Sankata", "संकटा", 8),
        ]

        def periods(spec, *, yogini=False):
            result = []
            cursor = 2000
            for name, nepali, years in spec:
                node = {
                    "start": f"{cursor}-01-01", "end": f"{cursor + years}-01-01",
                    "total_years": years,
                }
                node.update({"name": name, "nepali": nepali} if yogini else {"lord": name, "lord_nepali": nepali})
                cursor += years
                result.append(node)
            child_key = "antardashas" if yogini else "children"
            for node in result:
                node[child_key] = [dict(item) for item in result]
            return result

        payload["dasha"] = periods(vimshottari)
        payload["yogini_dasha"] = periods(yoginis, yogini=True)
        page = JanmapatrikaPage(payload)
        maha_html = page._dasha_table_html(payload["dasha"])
        yogini_html = page._dasha_table_html(payload["yogini_dasha"])

        expected_planets = [item[1] for item in vimshottari]
        positions = [maha_html.index(f">{name}</td>") for name in expected_planets]
        self.assertEqual(positions, sorted(positions))
        for years in (6, 10, 7, 18, 16, 19, 17, 20):
            self.assertIn(f">{str(years).translate(str.maketrans('0123456789', '०१२३४५६७८९'))} वर्ष</td>", maha_html)
        self.assertEqual(maha_html.count("width='10%'"), 30)
        self.assertIn(">६ वर्ष</td>", maha_html)
        self.assertIn(">१२० वर्ष</td>", maha_html)

        expected_yoginis = [item[1] for item in yoginis]
        positions = [yogini_html.index(f">{name}</td>") for name in expected_yoginis]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(yogini_html.count("width='11%'"), 27)
        self.assertNotIn("केतु", yogini_html)
        self.assertIn(">३६ वर्ष</td>", yogini_html)

        page.show()
        self.app.processEvents()
        dasha_tables = [
            label for label in page._paper.findChildren(QLabel)
            if "font-size:9px" in label.text() and ("दशा</td>" in label.text() or "ग्रह</td>" in label.text() or "योगिनी</td>" in label.text())
        ]
        self.assertEqual(len(dasha_tables), 4)
        for table in dasha_tables:
            self.assertLessEqual(table.width(), table.parentWidget().contentsRect().width())

    def test_antardasha_grid_starts_at_birth_and_runs_positionally(self):
        timeline = VimshottariAntardashaTests.timeline()
        html = JanmapatrikaPage._dasha_table_html(
            timeline, children_key="antardashas", visible_rows=3
        )
        rows = self._assert_grid(html, 10)
        self.assertEqual(len(rows), 4)
        self.assertNotIn("जन्म अघि", html)

        self.assertEqual(
            rows[0],
            ["दशा", "सूर्य", "चन्द्र", "मङ्गल", "राहु",
             "गुरु", "शनि", "बुध", "केतु", "शुक्र"],
        )
        # The first column is a label only; the birth antardasha's value
        # sits in its own column, not in the label column.
        self.assertEqual(rows[1][0], "बाँकी उमेर")
        self.assertEqual(
            rows[1][1:],
            ["—", "—", "—", "१ वर्ष<br>५ महिना", "३ वर्ष<br>११ महिना",
             "—", "—", "—", "—"],
        )

        self.assertEqual(rows[2][0], "बाँकी उमेर")
        self.assertEqual(
            rows[2][1:],
            ["११ वर्ष", "१२ वर्ष<br>५ महिना", "१३ वर्ष<br>५ महिना",
             "१६ वर्ष", "१८ वर्ष<br>३ महिना", "२० वर्ष<br>११ महिना",
             "६ वर्ष<br>४ महिना", "७ वर्ष<br>४ महिना",
             "१० वर्ष<br>२ महिना"],
        )

        self.assertEqual(rows[3][0], "बाँकी उमेर")
        self.assertEqual(
            rows[3][1:],
            ["२२ वर्ष<br>११ महिना", "२३ वर्ष<br>६ महिना",
             "२३ वर्ष<br>१० महिना", "२४ वर्ष<br>११ महिना",
             "२५ वर्ष<br>१० महिना", "२६ वर्ष<br>११ महिना",
             "२७ वर्ष<br>११ महिना", "२१ वर्ष<br>४ महिना",
             "२२ वर्ष<br>६ महिना"],
        )
        for row in rows:
            self.assertIn(row[0], {"दशा", "बाँकी उमेर"})

    def test_expand_link_reveals_three_more_rows(self):
        timeline = VimshottariAntardashaTests.timeline()
        html = JanmapatrikaPage._dasha_table_html(
            timeline, children_key="antardashas", visible_rows=3, show_more=True
        )
        rows = self._assert_grid(html, 10)
        self.assertEqual(len(rows), 4)
        self.assertEqual(html.count("href='expand'"), 1)
        self.assertIn("href='expand'", rows[-1][-1])

        expanded = JanmapatrikaPage._dasha_table_html(
            timeline, children_key="antardashas", visible_rows=6, show_more=True
        )
        expanded_rows = self._assert_grid(expanded, 10)
        self.assertEqual(len(expanded_rows), 7)
        self.assertEqual(expanded.count("href='expand'"), 1)
        self.assertIn("href='expand'", expanded_rows[-1][-1])

        complete = JanmapatrikaPage._dasha_table_html(
            timeline, children_key="antardashas", visible_rows=None, show_more=True
        )
        complete_rows = self._assert_grid(complete, 10)
        self.assertEqual(len(complete_rows), 10)
        self.assertNotIn("href='expand'", complete)

    def test_antardasha_labels_reserve_the_full_table_height(self):
        page = JanmapatrikaPage(sample_payload())
        page.show()
        self.app.processEvents()
        labels = [
            label for label in page._paper.findChildren(QLabel)
            if "font-size:9px" in label.text()
            and "cellpadding='2'" in label.text()
        ]
        self.assertEqual(len(labels), 2)
        for label in labels:
            document = QTextDocument()
            document.setDefaultFont(label.font())
            document.setHtml(label.text())
            document.setTextWidth(max(1, label.width()))
            self.assertGreaterEqual(
                label.minimumHeight(),
                math.ceil(document.size().height()),
            )

    def test_short_antardasha_keeps_days(self):
        self.assertEqual(
            JanmapatrikaPage._dasha_cell_value("2000-01-01", "2000-01-13"),
            "१२ दिन",
        )
        self.assertEqual(
            JanmapatrikaPage._dasha_cell_value("2000-01-01", "2001-04-13"),
            "१ वर्ष<br>३ महिना",
        )
        self.assertEqual(
            JanmapatrikaPage._dasha_cell_value("2000-01-01", "2000-03-01"),
            "० वर्ष<br>२ महिना",
        )

    def test_legacy_antardasha_payload_renders_only_post_birth_cells(self):
        periods = [
            {
                "lord": "Saturn", "lord_nepali": "शनि",
                "start": "2000-04-15", "end": "2000-08-01",
                "total_years": 19, "is_partial": True,
                "children": [
                    {
                        "lord": "Jupiter", "lord_nepali": "गुरु",
                        "start": "2000-04-15", "end": "2000-08-01",
                    }
                ],
            }
        ]
        html = JanmapatrikaPage._dasha_table_html(
            periods, children_key="antardashas"
        )
        self.assertNotIn("जन्म अघि", html)
        rows = self._assert_grid(html, 10)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            rows[0],
            ["दशा", "सूर्य", "चन्द्र", "मङ्गल", "राहु",
             "गुरु", "शनि", "बुध", "केतु", "शुक्र"],
        )
        self.assertEqual(rows[1][0], "बाँकी उमेर")
        self.assertEqual(rows[1][5], "० वर्ष<br>३ महिना")
        self.assertEqual(
            [rows[1][index] for index in (1, 2, 3, 4, 6, 7, 8, 9)],
            ["—"] * 8,
        )

    def test_reference_chart_grid_starts_at_birth_and_accumulates_balance(self):
        timeline = calculate_vimshottari_dasha(
            344.7034913728455, "1986-06-29", "09:15:00"
        )
        maha_html = JanmapatrikaPage._dasha_table_html(timeline)
        maha_rows = re.findall(r"<tr>(.*?)</tr>", maha_html)
        maha_cells = [
            re.findall(r"<td width='10%'>(.*?)</td>", row) for row in maha_rows
        ]
        self.assertEqual(
            maha_cells[0][1:],
            ["शनि", "बुध", "केतु", "शुक्र", "सूर्य",
             "चन्द्र", "मङ्गल", "राहु", "गुरु"],
        )
        self.assertEqual(
            maha_cells[2][1:],
            ["२ वर्ष<br>९ महिना", "१९ वर्ष<br>९ महिना",
             "२६ वर्ष<br>९ महिना", "४६ वर्ष<br>९ महिना",
             "५२ वर्ष<br>९ महिना", "६२ वर्ष<br>९ महिना",
             "६९ वर्ष<br>९ महिना", "८७ वर्ष<br>९ महिना",
             "१०३ वर्ष<br>९ महिना"],
        )

        ad_html = JanmapatrikaPage._dasha_table_html(
            timeline, children_key="antardashas", visible_rows=3
        )
        rows = self._assert_grid(ad_html, 10)
        self.assertEqual(len(rows), 4)
        self.assertNotIn("जन्म अघि", ad_html)
        self.assertEqual(
            rows[0],
            ["दशा", "सूर्य", "चन्द्र", "मङ्गल", "राहु",
             "गुरु", "शनि", "बुध", "केतु", "शुक्र"],
        )
        self.assertEqual(
            rows[1][1:],
            ["—", "—", "—", "० वर्ष<br>२ महिना",
             "२ वर्ष<br>९ महिना", "—", "—", "—", "—"],
        )
        # Values remain cumulative from birth, and every value stays under
        # its own lord's fixed header column.
        self.assertEqual(
            rows[2][1:],
            ["९ वर्ष<br>१० महिना", "११ वर्ष<br>३ महिना",
             "१२ वर्ष<br>३ महिना", "१४ वर्ष<br>९ महिना",
             "१७ वर्ष<br>१ महिना", "१९ वर्ष<br>९ महिना",
             "५ वर्ष<br>२ महिना", "६ वर्ष<br>२ महिना", "९ वर्ष"],
        )
        self.assertEqual(
            rows[3][1:],
            ["२१ वर्ष<br>८ महिना", "२२ वर्ष<br>३ महिना",
             "२२ वर्ष<br>८ महिना", "२३ वर्ष<br>९ महिना",
             "२४ वर्ष<br>८ महिना", "२५ वर्ष<br>९ महिना",
             "२६ वर्ष<br>९ महिना", "२० वर्ष<br>२ महिना",
             "२१ वर्ष<br>४ महिना"],
        )
        for row in rows:
            self.assertIn(row[0], {"दशा", "बाँकी उमेर"})

    def test_yogini_antardasha_starts_with_birth_yogini_and_has_no_gaps(self):
        timeline = calculate_yogini_dasha(
            344.7034913728455, "1986-06-29", "09:15:00"
        )
        html = JanmapatrikaPage._dasha_table_html(
            timeline, children_key="antardashas", visible_rows=3
        )
        rows = self._assert_grid(html, 9)
        self.assertEqual(len(rows), 4)
        self.assertNotIn("जन्म अघि", html)
        self.assertEqual(
            rows[0],
            ["दशा", "मङ्गला", "पिङ्गला", "धान्या", "भ्रामरी",
             "भद्रिका", "उल्का", "सिद्धा", "संकटा"],
        )
        self.assertEqual(
            rows[1][1:],
            ["—", "—", "० वर्ष<br>२ महिना", "० वर्ष<br>८ महिना",
             "—", "—", "—", "—"],
        )
        # Cumulative from birth, aligned under each Yogini's own column.
        self.assertEqual(
            rows[2][1:],
            ["४ वर्ष<br>४ महिना", "४ वर्ष<br>८ महिना",
             "५ वर्ष<br>२ महिना", "५ वर्ष<br>१० महिना",
             "६ वर्ष<br>८ महिना", "१ वर्ष<br>८ महिना",
             "२ वर्ष<br>१० महिना", "४ वर्ष<br>२ महिना"],
        )
        self.assertEqual(
            rows[3][1:],
            ["९ वर्ष<br>१० महिना", "१० वर्ष<br>२ महिना",
             "१० वर्ष<br>९ महिना", "११ वर्ष<br>७ महिना",
             "१२ वर्ष<br>६ महिना", "१३ वर्ष<br>८ महिना",
             "८ वर्ष<br>१ महिना", "९ वर्ष<br>७ महिना"],
        )
        for row in rows:
            self.assertIn(row[0], {"दशा", "बाँकी उमेर"})

    def test_yogini_antardasha_keeps_all_three_thirty_six_year_cycles(self):
        timeline = calculate_yogini_dasha(
            344.7034913728455, "1986-06-29", "09:15:00"
        )
        html = JanmapatrikaPage._dasha_table_html(
            timeline, children_key="antardashas", visible_rows=None
        )
        rows = self._assert_grid(html, 9)
        self.assertEqual(len(rows), 25)
        self.assertEqual(rows[0][0], "दशा")
        self.assertEqual(rows[-1][0], "बाँकी उमेर")
        self.assertEqual(rows[-1][3], "१०३ वर्ष<br>८ महिना")
        self.assertEqual(rows[-1][8], "१०३ वर्ष")
        self.assertNotIn("जन्म अघि", html)

    def test_page_builds_all_supported_sections_and_pdf(self):
        page = JanmapatrikaPage(sample_payload())
        labels = "\n".join(label.text() for label in page._paper.findChildren(QLabel))
        for text in (
            "श्रीमङ्गलमूर्तये नमः", "जन्म कुण्डली (D1)", "चन्द्र कुण्डली",
            "ग्रह स्थिति तालिका", "विंशोत्तरी महादशा चक्रम्",
            "विंशोत्तरी अन्तरदशा चक्रम्", "योगिनी महादशा चक्रम्",
            "योगिनी अन्तरदशा चक्रम्", "परिवारको विवरण", "॥ इति जन्मपत्रिका ॥",
        ):
            self.assertIn(text, labels)
        self.assertNotIn("नवमांश कुण्डली (D9)", labels)
        controls = [button.text() for button in page.findChildren(QPushButton)]
        controls += [button.text() for button in page._paper.findChildren(QPushButton)]
        self.assertIn("+", controls)
        self.assertIn("-", controls)

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "janmapatrika.pdf")
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            page._configure_printer(printer)
            pages = page._render_to_printer(printer)
            self.assertGreaterEqual(pages, 1)
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 1000)


if __name__ == "__main__":
    unittest.main()
