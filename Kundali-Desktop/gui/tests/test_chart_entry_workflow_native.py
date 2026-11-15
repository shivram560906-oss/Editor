# -*- coding: utf-8 -*-
"""Focused headless tests for the native chart-entry approval workflow."""
import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QTableWidgetItem

from gui.app import JyotishMainWindow
from gui.widgets.chart_input import ChartInputWidget


def valid_params(name="Sita Sharma"):
    return {
        "name": name,
        "birth_date": "2000-04-15",
        "birth_time": "10:30:00",
        "latitude": 27.7172,
        "longitude": 85.3240,
        "timezone": 5.75,
        "timezone_id": "Asia/Kathmandu",
        "country": "Nepal",
        "region": "Bagmati",
        "province": "Bagmati",
        "district": "Kathmandu",
        "city": "Kathmandu",
        "birth_place": "Kathmandu",
        "gender": 1,
        "ayanamsha_type": "LAHIRI",
        "node_type": "MEAN",
        "house_system": "WHOLE_SIGN",
    }


def preview_data(name="Sita Sharma"):
    planets = [
        {
            "name": planet,
            "house": index + 1,
            "sign_number": index + 1,
            "longitude_in_sign": 10.0 + index,
        }
        for index, planet in enumerate(
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        )
    ]
    return {
        "metadata": {"name": name},
        "lagna": {"sign_number": 1, "longitude_in_sign": 12.5},
        "planets": planets,
        "vargas": {
            "D1": {
                "lagna": {"sign_number": 1, "longitude_in_sign": 12.5},
                "planets": planets,
            }
        },
    }


class ChartInputWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_widget(self, params=None):
        widget = ChartInputWidget(language="en")
        if params is not None:
            widget.load_params(params)
        return widget

    def test_four_tabs_and_required_fields(self):
        widget = self.make_widget(valid_params())
        self.assertEqual(
            [widget._tabs.tabText(index) for index in range(widget._tabs.count())],
            ["Birth Details", "Events", "Family", "Comments"],
        )
        self.assertEqual(
            widget._gender_group.buttons(),
            [widget._btn_male, widget._btn_female],
        )
        self.assertFalse(hasattr(widget, "_btn_other"))
        self.assertEqual(widget._name_edit.minimumWidth(), 220)
        self.assertEqual(widget._name_edit.maximumWidth(), 220)
        # Jyotish settings were moved to the Settings dialog; the birth form
        # must not expose Ayanamsha/Node/House selectors anymore.
        self.assertFalse(hasattr(widget, "_ayanamsha_combo"))
        self.assertFalse(hasattr(widget, "_node_combo"))
        self.assertFalse(hasattr(widget, "_house_combo"))
        self.assertFalse(hasattr(widget, "_siddhanta_combo"))
        for button in widget._gender_group.buttons():
            self.assertEqual(button.size().width(), 68)
            self.assertEqual(button.size().height(), 26)
        widget.show()
        self.app.processEvents()
        self.assertEqual(widget._name_edit.y(), widget._btn_male.y())
        self.assertEqual(widget._name_edit.y(), widget._btn_female.y())
        self.assertIsNotNone(widget.collect_params())

        required_controls = (
            (widget._name_edit, ""),
            (widget._ad_date_edit, ""),
            (widget._time_edit, ""),
        )
        for control, missing_value in required_controls:
            with self.subTest(control=control):
                original = control.text()
                control.setText(missing_value)
                self.assertIsNone(widget.collect_params())
                control.setText(original)

        # When city is empty, it falls back to district; when country is unselected, it returns None
        orig_country_idx = widget._country_combo.currentIndex()
        widget._country_combo.setCurrentIndex(0)  # prompt / None
        self.assertIsNone(widget.collect_params())
        widget._country_combo.setCurrentIndex(orig_country_idx)

        widget._gender_group.setExclusive(False)
        for button in (widget._btn_male, widget._btn_female):
            button.setChecked(False)
        widget._gender_group.setExclusive(True)
        self.assertIsNone(widget.collect_params())

    def test_nepal_location_cascade_and_coordinates(self):
        widget = self.make_widget()
        self.assertEqual(widget._country_combo.currentData(), "Nepal")
        self.assertEqual(widget._region_combo.currentData(), "Lumbini")
        self.assertEqual(widget._district_combo.currentData(), "Kapilvastu")
        self.assertEqual(widget._city_combo.currentText(), "Kapilvastu")
        self.assertEqual(widget._lat_edit.text(), "27.5833")
        self.assertEqual(widget._lon_edit.text(), "83.05")
        self.assertEqual(widget._tz_edit.text(), "5.75")
        self.assertTrue(widget._lat_edit.isReadOnly())
        self.assertTrue(widget._lon_edit.isReadOnly())
        self.assertTrue(widget._tz_edit.isReadOnly())
        self.assertFalse(widget._custom_location.isChecked())
        self.assertEqual(widget._region_combo.count() - 1, 7)

        widget._region_combo.setCurrentIndex(
            widget._region_combo.findData("Bagmati")
        )
        self.assertIn("Kathmandu", [
            widget._district_combo.itemData(index)
            for index in range(widget._district_combo.count())
        ])
        widget._district_combo.setCurrentIndex(
            widget._district_combo.findData("Kathmandu")
        )
        kathmandu_index = widget._city_combo.findText("Kathmandu")
        self.assertGreaterEqual(kathmandu_index, 0)
        widget._city_combo.setCurrentIndex(kathmandu_index)
        self.assertEqual(widget._lat_edit.text(), "27.7172")
        self.assertEqual(widget._lon_edit.text(), "85.324")
        self.assertEqual(widget._tz_edit.text(), "5.75")

        india_index = widget._country_combo.findData("India")
        self.assertGreaterEqual(india_index, 0)
        widget._country_combo.setCurrentIndex(india_index)
        self.assertEqual(widget._lat_edit.text(), "")
        self.assertEqual(widget._lon_edit.text(), "")
        self.assertIsNone(widget._district_combo.currentData())
        self.assertFalse(widget._district_combo.isEnabled())

    def test_location_restore_and_custom_place(self):
        widget = self.make_widget(valid_params())
        self.assertEqual(widget._country_combo.currentData(), "Nepal")
        self.assertEqual(widget._region_combo.currentData(), "Bagmati")
        self.assertEqual(widget._district_combo.currentData(), "Kathmandu")
        self.assertEqual(widget._city_combo.currentText(), "Kathmandu")
        self.assertEqual(widget._lat_edit.text(), "27.7172")

        widget._custom_location.setChecked(True)
        self.assertFalse(widget._lat_edit.isReadOnly())
        self.assertFalse(widget._lon_edit.isReadOnly())
        self.assertFalse(widget._tz_edit.isReadOnly())
        widget._city_combo.lineEdit().setText("Kirtipur")
        widget._lat_edit.setText("27.6766")
        widget._lon_edit.setText("85.2775")
        widget._tz_edit.setText("5.75")
        params = widget.collect_params()
        self.assertEqual(params["city"], "Kirtipur")
        self.assertEqual(params["province"], "Bagmati")
        self.assertEqual(params["district"], "Kathmandu")
        self.assertIsNone(params["timezone_id"])

    def test_bilingual_search_and_high_contrast_location_popups(self):
        widget = self.make_widget()
        self.assertIn("Nepal", widget._country_combo.itemText(
            widget._country_combo.findData("Nepal")
        ))
        self.assertIn("नेपाल", widget._country_combo.itemText(
            widget._country_combo.findData("Nepal")
        ))
        self.assertIn("Lumbini", widget._region_combo.itemText(
            widget._region_combo.findData("Lumbini")
        ))
        self.assertIn("लुम्बिनी", widget._region_combo.itemText(
            widget._region_combo.findData("Lumbini")
        ))
        self.assertIn("कपिलवस्तु", widget._district_combo.itemText(
            widget._district_combo.findData("Kapilvastu")
        ))
        for combo in (
            widget._country_combo, widget._region_combo,
            widget._district_combo, widget._city_combo,
        ):
            self.assertTrue(combo.isEditable())
            self.assertEqual(combo.completer().filterMode(), Qt.MatchContains)
            self.assertLessEqual(combo.maximumWidth(), 300)
            self.assertIn("background: #ffffff", combo.styleSheet())
            self.assertIn("color: #111111", combo.styleSheet())

        self.assertLessEqual(widget._name_edit.maximumWidth(), 300)
        self.assertLessEqual(widget._time_edit.maximumWidth(), 120)
        self.assertIn("background: #ffffff", widget.styleSheet())
        self.assertIn("color: #111111", widget.styleSheet())
        self.assertIn("background: #ffffff", widget._lat_edit.styleSheet())
        self.assertIn("color: #111111", widget._lat_edit.styleSheet())
        for field in (
            widget._name_edit,
            widget._bs_year,
            widget._bs_month,
            widget._bs_day,
            widget._time_edit,
        ):
            with self.subTest(field=field):
                self.assertIn("background-color: #ffffff", field.styleSheet())
                self.assertIn("color: #111111", field.styleSheet())
        self.assertIn("QTabWidget::pane { border: none", widget._tabs.styleSheet())

    def test_chart_entry_uses_separate_reusable_window(self):
        window = JyotishMainWindow(language="en")
        try:
            self.assertIsInstance(window._input_panel, QDialog)
            self.assertIs(window._input_panel.parent(), window)
            self.assertIs(window._chart_input.parent(), window._input_panel)
            self.assertEqual(window._main_splitter.indexOf(window._input_panel), -1)
            self.assertEqual(window._input_panel.minimumSize().width(), 720)
            self.assertEqual(window._input_panel.minimumSize().height(), 540)
            self.assertLessEqual(window._input_panel.width(), 780)
            self.assertLessEqual(window._input_panel.height(), 600)

            window._show_input_panel()
            self.app.processEvents()
            self.assertTrue(window._input_panel.isVisible())
            dialog_rect = window._input_panel.rect()
            for button in (
                window._chart_input._calc_btn,
                window._chart_input._approve_btn,
                window._chart_input._reject_btn,
            ):
                with self.subTest(button=button.text()):
                    self.assertTrue(button.isVisible())
                    top_left = button.mapTo(window._input_panel, button.rect().topLeft())
                    bottom_right = button.mapTo(
                        window._input_panel, button.rect().bottomRight()
                    )
                    self.assertTrue(dialog_rect.contains(top_left))
                    self.assertTrue(dialog_rect.contains(bottom_right))

            window._hide_input_panel()
            self.assertFalse(window._input_panel.isVisible())
            self.assertIsNotNone(window._chart_input)
        finally:
            window._input_panel.hide()
            window.close()

    def test_optional_metadata_events_and_comments_are_collected(self):
        widget = self.make_widget(valid_params())
        params = widget.collect_params()
        self.assertIsNotNone(params)
        self.assertIsNone(params["full_name"])
        self.assertIsNone(params["marital_status"])
        self.assertEqual(params["life_events"], [])
        self.assertIsNone(params["comments"])

        widget._janmapatrika_edits["full_name"].setText("Sita Kumari Sharma")
        widget._janmapatrika_edits["father_name"].setText("Hari Sharma")
        widget._janmapatrika_edits["gotra"].setText("Bharadwaj")
        widget._marital_status.setCurrentIndex(2)
        widget._family_details.setText("One elder brother")
        widget._events_table.setItem(0, 0, QTableWidgetItem("2020-01-01"))
        widget._events_table.setItem(0, 1, QTableWidgetItem("Graduation"))
        widget._comments_edit.setPlainText("Verified birth time")

        params = widget.collect_params()
        self.assertEqual(params["full_name"], "Sita Kumari Sharma")
        self.assertEqual(params["father_name"], "Hari Sharma")
        self.assertEqual(params["gotra"], "Bharadwaj")
        self.assertEqual(params["marital_status"], "विवाहित")
        self.assertEqual(params["family_details"], "One elder brother")
        self.assertEqual(
            params["life_events"],
            [{"date": "2020-01-01", "event": "Graduation"}],
        )
        self.assertEqual(params["comments"], "Verified birth time")

    def test_flexible_birth_time_inputs_submit_canonical_backend_value(self):
        widget = self.make_widget(valid_params())
        cases = (
            ("11 45", "11:45:00", "11:45"),
            ("11;45", "11:45:00", "11:45"),
            ("११ ४५", "11:45:00", "11:45"),
            ("११ ४५ ००", "11:45:00", "11:45"),
            ("११ ४५ ३०", "11:45:30", "11:45:30"),
        )
        for typed, backend_value, display in cases:
            with self.subTest(typed=typed):
                widget._time_edit.setText(typed)
                params = widget.collect_params()
                self.assertIsNotNone(params)
                self.assertEqual(params["birth_time"], backend_value)
                self.assertEqual(widget._time_edit.text(), display)

        for invalid in ("24 00", "11 60", "11 45 60", "11-45"):
            with self.subTest(invalid=invalid):
                widget._time_edit.setText(invalid)
                self.assertIsNone(widget.collect_params())

    def test_preview_is_optional_and_approval_is_immediate(self):
        widget = self.make_widget(valid_params())
        calculations = []
        approvals = []
        widget.calculate_requested.connect(calculations.append)
        widget.approve_requested.connect(approvals.append)

        self.assertTrue(widget._approve_btn.isEnabled())
        widget._on_calculate()
        self.assertEqual(len(calculations), 1)

        widget._on_approve()
        self.assertEqual(len(approvals), 1)


class _FakeChartInput:
    def __init__(self):
        self.invalidated = False

    def invalidate_preview(self):
        self.invalidated = True


class WorkflowHarness:
    _approve_preview = JyotishMainWindow._approve_preview
    _reject_entry = JyotishMainWindow._reject_entry

    def __init__(self):
        self._editing_record_id = None
        self._active_record_id = None
        self._preview_chart_data = preview_data()
        self._chart_input = _FakeChartInput()
        self._is_ne = False
        self.promoted = None
        self.hidden = False
        self.navigation = None
        self.status = None

    def _promote_preview(self, params):
        if self._preview_chart_data is None:
            raise RuntimeError("No calculated preview is available")
        self.promoted = dict(params)
        self._preview_chart_data = None

    def _refresh_saved_chart_views(self):
        pass

    def _hide_input_panel(self):
        self.hidden = True

    def _navigate(self, view_id):
        self.navigation = view_id

    def _set_status(self, message, error=False):
        self.status = (message, error)


class ChartStorageWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.old_database_url = os.environ.get("DATABASE_URL")
        cls.database_path = os.path.join(cls.temp_dir.name, "chart-entry.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{cls.database_path.replace(os.sep, '/')}"

        from gui.utils import chart_storage

        cls.storage = chart_storage
        cls.storage._SessionMaker = None

    @classmethod
    def tearDownClass(cls):
        if cls.storage._SessionMaker is not None:
            bind = cls.storage._SessionMaker.kw.get("bind")
            if bind is not None:
                bind.dispose()
        cls.storage._SessionMaker = None
        if cls.old_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = cls.old_database_url
        cls.temp_dir.cleanup()

    def setUp(self):
        # Every test starts with an empty local chart collection.
        for record in self.storage.list_charts():
            self.storage.delete_chart(record["id"])

    def detailed_params(self, name="Sita Sharma"):
        params = valid_params(name)
        params.update({
            "full_name": "Sita Kumari Sharma",
            "father_name": "Hari Sharma",
            "mother_name": "Gita Sharma",
            "gotra": "Bharadwaj",
            "marital_status": "विवाहित",
            "family_details": "One elder brother",
            "life_events": [{"date": "2020-01-01", "event": "Graduation"}],
            "comments": "Verified birth time",
        })
        return params

    def test_new_approval_inserts_once_and_round_trips_metadata(self):
        harness = WorkflowHarness()
        params = self.detailed_params()
        harness._approve_preview(params)

        records = self.storage.list_charts()
        self.assertEqual(len(records), 1)
        self.assertEqual(harness._active_record_id, records[0]["id"])
        loaded = self.storage.get_chart_params(records[0]["id"])
        self.assertEqual(loaded["record_id"], records[0]["id"])
        self.assertEqual(loaded["region"], "Bagmati")
        self.assertEqual(loaded["province"], "Bagmati")
        self.assertEqual(loaded["district"], "Kathmandu")
        self.assertEqual(loaded["full_name"], "Sita Kumari Sharma")
        self.assertEqual(loaded["father_name"], "Hari Sharma")
        self.assertEqual(loaded["life_events"], params["life_events"])
        self.assertEqual(loaded["comments"], "Verified birth time")
        self.assertEqual(harness.navigation, "chart_rashi")

    def test_edit_approval_replaces_same_row_without_duplicate(self):
        original_id = self.storage.save_chart(self.detailed_params())
        harness = WorkflowHarness()
        harness._editing_record_id = original_id
        updated = self.detailed_params("Sita Sharma Updated")
        updated["comments"] = "Corrected record"

        harness._approve_preview(updated)

        records = self.storage.list_charts()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], original_id)
        self.assertEqual(harness._active_record_id, original_id)
        loaded = self.storage.get_chart_params(original_id)
        self.assertEqual(loaded["name"], "Sita Sharma Updated")
        self.assertEqual(loaded["comments"], "Corrected record")

    def test_edit_rejection_leaves_original_row_unchanged(self):
        original = self.detailed_params()
        original_id = self.storage.save_chart(original)
        harness = WorkflowHarness()
        harness._editing_record_id = original_id

        harness._reject_entry()

        records = self.storage.list_charts()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], original_id)
        loaded = self.storage.get_chart_params(original_id)
        self.assertEqual(loaded["name"], original["name"])
        self.assertEqual(loaded["comments"], original["comments"])
        self.assertTrue(harness._chart_input.invalidated)

    def test_every_saved_chart_is_visible_without_login(self):
        alice_id = self.storage.save_chart(self.detailed_params("Alice Chart"))
        bob_id = self.storage.save_chart(self.detailed_params("Bob Chart"))

        ids = {record["id"] for record in self.storage.list_charts()}
        self.assertEqual(ids, {alice_id, bob_id})
        self.assertIsNotNone(self.storage.get_chart_params(alice_id))
        self.assertIsNotNone(self.storage.get_chart_params(bob_id))

    def test_save_update_and_delete_need_no_account(self):
        record_id = self.storage.save_chart(self.detailed_params())
        self.storage.update_chart(record_id, self.detailed_params("Renamed"))
        self.assertEqual(
            self.storage.get_chart_params(record_id)["name"], "Renamed"
        )
        self.assertTrue(self.storage.delete_chart(record_id))
        self.assertEqual(self.storage.list_charts(), [])


if __name__ == "__main__":
    unittest.main()
