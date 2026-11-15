# -*- coding: utf-8 -*-
"""Regression tests for the calculation thread lifecycle.

Two defects are guarded here:

1. ``_clear_calc_worker`` used to delete whatever ``self._calc_thread`` pointed
   at, so a calculation started while the previous thread's ``finished`` event
   was still queued had its worker deleted mid-run (lost result, and Qt's
   "QThread: Destroyed while thread is still running").
2. The main window had no ``closeEvent``, so closing the app during a
   calculation destroyed a running QThread and aborted the process (0xC0000409).
"""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication

from gui.app import JyotishMainWindow


PARAMS = {
    "name": "Thread Lifecycle Test",
    "birth_date": "1990-01-15",
    "birth_time": "10:30:00",
    "latitude": 27.7172,
    "longitude": 85.3240,
    "timezone": 5.75,
    "city": "Kathmandu",
    "gender": 0,
    "ayanamsha_type": "LAHIRI",
    "node_type": "MEAN",
    "house_system": "WHOLE_SIGN",
}


class _ImmediateWorker(QObject):
    """Stand-in for CalcWorker that finishes as soon as the thread starts."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, params=None):
        super().__init__()
        self._params = params

    def run(self):
        self.finished.emit({"metadata": {"name": "Thread Lifecycle Test"}})


class CalcThreadLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _pump(self, window, rounds=200):
        for _ in range(rounds):
            self.app.processEvents()

    def test_finished_thread_is_cleared_after_a_successful_run(self):
        import gui.app as app_module

        original = app_module.CalcWorker
        app_module.CalcWorker = _ImmediateWorker
        window = JyotishMainWindow(language="en")
        try:
            window.show()
            window._start_calculation(dict(PARAMS))
            self._pump(window)
            self.assertIsNone(
                window._calc_thread,
                "a finished calculation thread must be released",
            )
            self.assertIsNone(window._worker)
        finally:
            app_module.CalcWorker = original
            window._stop_background_work()
            window.close()

    def test_stale_thread_cannot_clear_a_live_one(self):
        window = JyotishMainWindow(language="en")
        try:
            live = QThread(window)
            window._calc_thread = live
            stale = QThread(window)
            # The queued cleanup of a *previous* thread must not delete the
            # worker of the calculation that is running now.
            window._clear_calc_worker(stale)
            self.assertIs(window._calc_thread, live)
            live.deleteLater()
            stale.deleteLater()
        finally:
            window._stop_background_work()
            window.close()

    def test_closing_the_window_joins_a_running_calculation(self):
        import gui.app as app_module

        class _BlockingWorker(QObject):
            finished = Signal(dict)
            error = Signal(str)

            def __init__(self, params=None):
                super().__init__()
                self._params = params

            def run(self):
                # Simulate a long ephemeris run that outlives the close request.
                import time
                time.sleep(1.5)

        original = app_module.CalcWorker
        app_module.CalcWorker = _BlockingWorker
        window = JyotishMainWindow(language="en")
        try:
            window.show()
            self.app.processEvents()
            window._start_calculation(dict(PARAMS))
            self.app.processEvents()  # let the thread start
            thread = window._calc_thread
            self.assertIsNotNone(thread)
            window.close()
            self.assertIsNone(
                window._calc_thread,
                "closeEvent must release the calculation thread",
            )
            self.assertFalse(
                thread.isRunning(),
                "the worker thread must be stopped before the window is destroyed",
            )
        finally:
            app_module.CalcWorker = original
            window._stop_background_work()
            window.close()


if __name__ == "__main__":
    unittest.main()
