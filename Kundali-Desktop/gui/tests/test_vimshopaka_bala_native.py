"""Native PySide6 tests for the Vimshopaka Bala page.

The page must render the engine's payload and nothing else.  It previously
computed its own scores in the GUI and fell back to a fabricated neutral 0.5,
so these tests assert that no number appears that the engine did not publish.
"""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "backend"))

from PySide6.QtWidgets import QApplication                                  # noqa: E402

_app = QApplication.instance() or QApplication([])

from backend.calculator.vimshopaka import (                                # noqa: E402
    VIMSHOPAKA_GRAHAS,
    calculate_vimshopaka_bala,
)
from gui.widgets.vimshopaka_bala_page import (                             # noqa: E402
    VARGAS,
    VimshopakaBalaPage,
)

VARGAS_IDS = [v[0] for v in VARGAS]
TOTAL_COL = len(VARGAS_IDS) + 1


def _payload(planets):
    payload = calculate_vimshopaka_bala(planets)
    return {"vimshopaka_bala": payload}


def _full_chart():
    return [
        {"name": name, "sidereal_longitude": float((index * 47) % 360)}
        for index, name in enumerate(VIMSHOPAKA_GRAHAS)
    ]


def _page(payload, language="en"):
    page = VimshopakaBalaPage(payload, language)
    return page


class VimshopakaPageModelTests(unittest.TestCase):
    def test_table_has_a_row_per_graha_and_a_column_per_varga(self):
        page = _page(_payload(_full_chart()))
        self.assertEqual(page._table.rowCount(), len(VIMSHOPAKA_GRAHAS))
        # graha + 16 vargas + total + rating
        self.assertEqual(page._table.columnCount(), TOTAL_COL + 2)

    def test_totals_render_the_engine_values(self):
        payload = _payload(_full_chart())
        page = _page(payload)
        for row, name in enumerate(VIMSHOPAKA_GRAHAS):
            expected = payload["vimshopaka_bala"]["planets"][name]["total"]
            shown = page._table.item(row, TOTAL_COL).text()
            self.assertNotEqual(shown, "—", name)
            self.assertAlmostEqual(float(shown), expected, delta=0.11, msg=name)

    def test_rating_column_is_populated(self):
        page = _page(_payload(_full_chart()))
        for row in range(page._table.rowCount()):
            self.assertNotEqual(page._table.item(row, TOTAL_COL + 1).text(), "—")

    def test_nepali_and_english_both_render(self):
        payload = _payload(_full_chart())
        for language in ("ne", "en"):
            page = _page(payload, language)
            self.assertEqual(page._table.rowCount(), len(VIMSHOPAKA_GRAHAS))


class VimshopakaUnavailableStateTests(unittest.TestCase):
    """A missing varga must render an em-dash, never an invented score."""

    def test_missing_payload_shows_only_em_dashes(self):
        page = _page({"planets": []})
        for row in range(page._table.rowCount()):
            for col in range(1, TOTAL_COL + 2):
                self.assertEqual(page._table.item(row, col).text(), "—")

    def test_partial_payload_only_shows_its_available_rows(self):
        # Only the Sun has a longitude; every other graha is unavailable.
        payload = _payload([{"name": "Sun", "sidereal_longitude": 12.0}])
        page = _page(payload)
        planets = payload["vimshopaka_bala"]["planets"]
        for row, name in enumerate(VIMSHOPAKA_GRAHAS):
            shown = page._table.item(row, TOTAL_COL).text()
            if planets[name]["available"]:
                self.assertNotEqual(shown, "—", name)
            else:
                self.assertEqual(shown, "—", name)

    def test_page_never_shows_the_old_neutral_fallback(self):
        # A chart payload with planets but no vimshopaka_bala key: every cell
        # must be an em-dash.  The old code painted 0.5 * weight here.
        page = _page({"planets": [{"name": "Sun", "sidereal_longitude": 5.0}]})
        for row in range(page._table.rowCount()):
            for col in range(1, TOTAL_COL):
                self.assertEqual(page._table.item(row, col).text(), "—")

    def test_no_chart_leaves_the_placeholder_instead_of_a_table(self):
        page = _page({})
        self.assertFalse(page._placeholder.isHidden())
        self.assertIsNone(page._table.item(0, TOTAL_COL))


class VimshopakaNoGuiCalculationTests(unittest.TestCase):
    def test_page_module_contains_no_astrology_score_table(self):
        import inspect
        import gui.widgets.vimshopaka_bala_page as module

        source = inspect.getsource(module)
        self.assertNotIn("SCORE_MAP", source)
        self.assertNotIn("_compute_varga_score", source)
        self.assertNotIn("neutral fallback", source)


if __name__ == "__main__":
    unittest.main()
