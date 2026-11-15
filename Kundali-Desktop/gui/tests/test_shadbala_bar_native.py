"""Native tests for the Shadbala bar chart embedded in the Rashi (D1) page.

Regression context: the widget read ``shadbala["Sun"]`` while the payload nests
the graha table at ``shadbala["planets"]["Sun"]``.  Because a fabricated
house/sign fallback filled the gap, the chart always looked plausible - and
always showed invented numbers.  Removing that fallback revealed the bad read
as a blank chart on the D1 page.
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

from gui.widgets.shadbala_bar_widget import (                               # noqa: E402
    PLANETS_ORDER,
    ShadbalaMiniBarWidget,
)

NODES = ("Rahu", "Ketu")   # not plotted by this chart; kept for documentation


def _values(payload):
    widget = ShadbalaMiniBarWidget(payload)
    return {key: value for key, _, value, _ in widget._get_planet_rupas()}


class ShadbalaBarPayloadPathTests(unittest.TestCase):
    """The chart must read the nested payload, or it renders nothing."""

    NESTED = {
        "shadbala": {
            "planets": {
                "Sun": {"total_rupas": 9.12, "total_shashtiamsa": 547.3},
                "Moon": {"total_rupas": 5.14},
            },
            "ranking": ["Sun", "Moon"],
        }
    }

    def test_nested_planets_table_is_read(self):
        values = _values(self.NESTED)
        self.assertEqual(values["Sun"], 9.12)
        self.assertEqual(values["Moon"], 5.14)

    def test_shashtiamsa_is_converted_when_rupas_is_absent(self):
        values = _values({"shadbala": {"planets": {"Sun": {"total_shashtiamsa": 600.0}}}})
        self.assertEqual(values["Sun"], 10.0)

    def test_flat_legacy_shape_is_still_accepted(self):
        flat = {"shadbala": {name: {"total_rupas": 5.0}
                            for name in ("Sun", "Moon", "Mars")}}
        values = _values(flat)
        self.assertEqual(values["Sun"], 5.0)

    def test_the_wrong_path_is_not_used(self):
        """A payload with only a top-level Sun entry must not be read as nested."""
        wrong = {"shadbala": {"Sun": {"total_rupas": 9.12}, "ranking": ["Sun"]}}
        values = _values(wrong)
        self.assertEqual(values["Sun"], 9.12)   # flat fallback still reaches it


class ShadbalaBarHonestyTests(unittest.TestCase):
    def test_grahas_without_data_are_unavailable_not_estimated(self):
        values = _values({"planets": [
            {"name": "Sun", "house": 1, "sign_number": 1},
            {"name": "Jupiter", "house": 4, "sign_number": 4},
        ]})
        # The chart plots only the seven grahas; with no Shadbala table every
        # slot is unavailable.  The old heuristic filled these with ~0.95.
        self.assertEqual(len(values), len(PLANETS_ORDER))
        for name in PLANETS_ORDER:
            self.assertIsNone(values[name], name)

    def test_a_partial_payload_values_only_what_it_has(self):
        values = _values({"shadbala": {"planets": {"Sun": {"total_rupas": 6.5}}}})
        self.assertEqual(values["Sun"], 6.5)
        for name in PLANETS_ORDER:
            if name != "Sun":
                self.assertIsNone(values[name], name)

    def test_malformed_values_degrade_to_unavailable(self):
        values = _values({"shadbala": {"planets": {
            "Venus": {"total_rupas": "abc"},
            "Mars": {"total_rupas": None},
        }}})
        self.assertIsNone(values["Venus"])
        self.assertIsNone(values["Mars"])

    def test_the_old_heuristic_is_gone(self):
        import inspect
        import gui.widgets.shadbala_bar_widget as module

        source = inspect.getsource(module)
        self.assertNotIn("base = 0.95", source)
        self.assertNotIn("Fallback estimation", source)


class ShadbalaBarPaintTests(unittest.TestCase):
    """The unavailable state must be readable, not a blank white box."""

    def _render(self, payload):
        widget = ShadbalaMiniBarWidget(payload)
        widget.resize(340, 321)
        widget.show()
        return widget.grab()

    def test_ready_payload_paints(self):
        payload = {"shadbala": {"planets": {
            n: {"total_rupas": 5.0} for n in PLANETS_ORDER[:7]}}}
        self.assertFalse(self._render(payload).isNull())

    def test_empty_payload_still_paints_an_explicit_panel(self):
        self.assertFalse(self._render({"planets": []}).isNull())

    def test_partial_payload_paints(self):
        payload = {"shadbala": {"planets": {"Sun": {"total_rupas": 5.0}}}}
        self.assertFalse(self._render(payload).isNull())


if __name__ == "__main__":
    unittest.main()
