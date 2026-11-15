# -*- coding: utf-8 -*-
"""Headless regression tests for the Nepali festival calendar page layout.

The bottom action bar (मुहूर्त / मिति परिवर्तन / बिदा / प्रतिक्रिया pills) used to
be clipped on 1366x768 laptops: the main window opened at 1400x900, so its
native frame hung below the taskbar (the work area is only 1366x720) and the
last ~40px of every page — including the whole action-bar row — sat off-screen.

These tests pin both halves of the fix:

  * the main window frame is clamped into the screen work area on first show;
  * the action bar keeps its own height and stays inside the page no matter how
    little vertical space the page is given.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from gui.app import JyotishMainWindow
from gui.widgets.nepali_festival_calendar import NepaliFestivalCalendarPage


def build_page() -> NepaliFestivalCalendarPage:
    """Create the page without its network-backed month load."""
    with patch.object(NepaliFestivalCalendarPage, "_load_month_data", lambda self: None):
        page = NepaliFestivalCalendarPage(language="ne")
    page._render_grid()
    page.show()
    return page


class FestivalCalendarActionBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_data_source_is_reported_instead_of_being_silent(self):
        """A fallback month must not be presented as if it came from the API."""
        page = build_page()
        page.show()
        self.app.processEvents()
        self.assertFalse(page._source_lbl.isVisibleTo(page))

        page._on_data_loaded(page._request_id, {
            1: {"_source": "स्थानीय इन्जिन (local engine)"},
            2: {"_source": "स्थानीय इन्जिन (local engine)"},
        })
        self.app.processEvents()
        self.assertTrue(page._source_lbl.isVisibleTo(page))
        self.assertIn("local engine", page._source_lbl.text())

    def test_action_bar_holds_all_four_pills_at_full_height(self):
        page = build_page()
        self.app.processEvents()

        pills = page._action_bar.findChildren(QPushButton)
        self.assertEqual(len(pills), 4)
        self.assertGreaterEqual(page._action_bar.height(), page._ACTION_BAR_MIN_H)
        for pill in pills:
            with self.subTest(pill=pill.toolTip()):
                self.assertGreaterEqual(pill.height(), page._PILL_H)
                self.assertTrue(page.rect().contains(pill.mapTo(page, pill.rect().topLeft())))
                self.assertTrue(page.rect().contains(pill.mapTo(page, pill.rect().bottomRight())))

    def test_action_bar_stays_visible_when_vertical_space_is_short(self):
        page = build_page()
        # The bar is the last row; the scrollable grid must shrink instead.
        for height in (700, 560, 480, 380, 300, 240):
            page.resize(1100, height)
            self.app.processEvents()
            with self.subTest(page_height=height):
                bar = page._action_bar
                self.assertLessEqual(bar.y() + bar.height(), page.height())
                self.assertGreaterEqual(bar.height(), page._ACTION_BAR_MIN_H)
                for pill in bar.findChildren(QPushButton):
                    self.assertGreaterEqual(pill.height(), page._PILL_H)


class MainWindowWorkAreaFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_oversized_window_is_clamped_into_the_work_area_on_show(self):
        window = JyotishMainWindow(language="en")
        try:
            # Emulate the old 1400x900 default on a smaller laptop panel.
            window.resize(4000, 9000)
            window.show()
            self.app.processEvents()

            self.assertTrue(window._work_area_fitted)
            avail = window.screen().availableGeometry()
            frame = window.frameGeometry()
            self.assertLessEqual(frame.width(), avail.width())
            self.assertLessEqual(frame.height(), avail.height())
            self.assertLessEqual(window.minimumWidth(), avail.width())
            self.assertLessEqual(window.minimumHeight(), avail.height())
        finally:
            window.close()

    def test_calendar_action_bar_is_inside_the_work_area(self):
        window = JyotishMainWindow(language="en")
        try:
            with patch.object(
                NepaliFestivalCalendarPage, "_load_month_data", lambda self: None
            ):
                window.show()
                self.app.processEvents()
                window._navigate("nepali_festival_calendar")
                self.app.processEvents()

            page = window._page_cache["nepali_festival_calendar"]
            bar = page._action_bar
            work = window.screen().availableGeometry()
            self.assertLessEqual(bar.y() + bar.height(), page.height())
            for pill in bar.findChildren(QPushButton):
                with self.subTest(pill=pill.toolTip()):
                    top_left = pill.mapToGlobal(pill.rect().topLeft())
                    bottom_right = pill.mapToGlobal(pill.rect().bottomRight())
                    self.assertTrue(work.contains(top_left))
                    self.assertTrue(work.contains(bottom_right))
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
