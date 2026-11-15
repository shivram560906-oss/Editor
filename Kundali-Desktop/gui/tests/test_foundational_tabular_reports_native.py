# -*- coding: utf-8 -*-
"""Headless contract checks for native foundational tabular reports."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from gui.widgets.complete_dasha import CompleteDashaPage, build_dasha_model
from gui.widgets.life_analysis import DashaPhalPage
from gui.widgets.panchang_info import (
    DAILY_PANCHANG_LOCATION,
    PanchangInfoPage,
    build_panchang_model,
    calculate_daily_panchang,
    daily_panchang_params,
)
from gui.widgets.planetary_info import (
    COLUMN_KEYS,
    STATUS_COLORS,
    PlanetaryInfoPage,
    build_planetary_model,
)


def sample_payload() -> dict:
    return {
        "metadata": {
            "birth_date": "2000-04-15",
            "ayanamsha_type": "LAHIRI",
            "ayanamsha_value": 23.8531,
        },
        "lagna": {"sign_number": 1, "sign_name": "Aries", "longitude_in_sign": 12.5},
        "planets": [
            {
                "name": "Sun", "sign_number": 1, "sign_name": "Aries",
                "longitude_in_sign": 10.5, "sidereal_longitude": 10.5,
                "house": 1, "nakshatra_name": "Ashwini", "is_retrograde": False,
                "is_combust": False, "relationship": "friend",
                "exaltation_state": "exalted", "is_vargottama": True,
            },
            {
                "name": "Saturn", "sign_number": 1, "sign_name": "Aries",
                "longitude_in_sign": 22.25, "sidereal_longitude": 22.25,
                "house": 7, "nakshatra_name": "Bharani", "is_retrograde": True,
                "is_combust": True, "relationship": "enemy",
                "exaltation_state": "debilitated",
            },
            {"name": "Moon", "sign_number": 2, "longitude_in_sign": 3.25},
            {"name": "Mars", "sign_number": 3, "longitude_in_sign": 4.5},
            {"name": "Mercury", "sign_number": 4, "longitude_in_sign": 5.75},
            {"name": "Jupiter", "sign_number": 5, "longitude_in_sign": 6.0},
            {"name": "Venus", "sign_number": 6, "longitude_in_sign": 7.0},
            {"name": "Rahu", "sign_number": 7, "longitude_in_sign": 8.0},
        ],
        "panchang_requested_day": {"panchang": {
            "shaka_samvat": "1922", "nepal_samvat": "1120", "samvatsara": "Pramadi",
            "ayana": "Uttarayana", "season": "Vasanta",
            "vara": {"name": "Saturday", "nepali": "शनिवार"},
            "tithi": {"name": "Panchami", "nepali": "पञ्चमी", "paksha": "Shukla", "paksha_nepali": "शुक्ल", "end_time": "15:20", "next_name": "Shashthi", "next_nepali": "षष्ठी"},
            "nakshatra": {"name": "Rohini", "nepali": "रोहिणी", "end_time": "12:30", "next_name": "Mrigashira"},
            "yoga": {"name": "Siddhi", "nepali": "सिद्धि"},
            "karana": {"name": "Bava", "nepali": "बव"},
            "moon_sign": {"name": "Taurus", "nepali": "वृष"},
            "anandadi_yoga": {"name": "Ananda", "nepali": "आनन्द"},
            "day_duration": "12:25", "sunrise": "05:55", "sunset": "18:20",
            "special_day": "Festival",
        }},
        "dasha": [{
            "lord": "Venus", "lord_nepali": "शुक्र", "level": 1,
            "start": "2018-10-04", "end": "2038-10-04",
            "start_bs": "२०७५-०६-१८", "end_bs": "२०९५-०६-१८",
            "is_active": True, "is_partial": True,
            "children": [{
                "lord": "Sun", "lord_nepali": "सूर्य", "level": 2,
                "start": "2025-12-02", "end": "2028-12-02",
                "start_bs": "२०८२-०८-१६", "end_bs": "२०८५-०८-१६",
                "is_active": True,
                "children": [{
                    "lord": "Moon", "lord_nepali": "चन्द्र", "level": 3,
                    "start": "2026-07-01", "end": "2026-10-01",
                    "start_bs": "२०८३-०३-१७", "end_bs": "२०८३-०६-१५",
                    "is_active": True,
                }],
            }],
        }],
    }


class FoundationalModelTests(unittest.TestCase):
    def test_planetary_nine_field_order_values_and_status_colors(self):
        model = build_planetary_model(sample_payload(), "en")
        self.assertEqual(model["state"], "ready")
        self.assertEqual(model["columns"], COLUMN_KEYS)
        self.assertEqual(COLUMN_KEYS, ["planet", "sign", "degree", "house", "nakshatra", "retrograde", "combust", "relation", "status", "vargottama"])
        sun, saturn = model["rows"][:2]
        self.assertEqual(sun["values"], ["Su", "Aries", "10°30′", "1", "Ashwini", "—", "—", "Friend", "Exalted ✓", "✨ Yes"])
        self.assertEqual(sun["status_color"], STATUS_COLORS["exalted"])
        self.assertTrue(sun["is_vargottama"])
        self.assertEqual(saturn["values"][5:10], ["Yes", "Yes", "Enemy", "Debilitated ✗", "—"])
        self.assertEqual(saturn["status_color"], STATUS_COLORS["debilitated"])

    def test_panchang_section_and_field_order_with_payload_values(self):
        model = build_panchang_model(sample_payload(), "en")
        self.assertEqual(model["state"], "ready")
        self.assertEqual([section["key"] for section in model["sections"]], ["samvat", "panchang", "sun_day", "special_day", "sunrise_planets"])
        sections = {section["key"]: section for section in model["sections"]}
        self.assertEqual([row["key"] for row in sections["samvat"]["rows"]], ["bs_date", "ad_date", "shaka", "nepal_samvat", "samvatsara", "ayana", "season", "weekday", "paksha"])
        self.assertEqual([row["key"] for row in sections["panchang"]["rows"]], ["tithi", "nakshatra", "yoga", "karana", "moon_sign", "anandadi_yoga"])
        values = {row["key"]: row["value"] for section in model["sections"] for row in section["rows"]}
        self.assertEqual(values["tithi"], "Panchami, 15:20 after Shashthi")
        self.assertEqual(values["moon_sign"], "Taurus")
        self.assertEqual(values["nepal_samvat"], "1120")
        self.assertEqual([row["key"] for row in sections["sunrise_planets"]["rows"]], ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu"])

    def test_daily_model_derives_missing_calendar_and_moon_fields_from_authoritative_inputs(self):
        payload = sample_payload()
        payload["daily_panchang_context"] = {"selected_date": "2026-08-16"}
        payload["planets"][0]["sign_number"] = 5
        payload["planets"][2]["sign_number"] = 6
        panchang = payload["panchang_requested_day"]["panchang"]
        panchang.pop("shaka_samvat")
        panchang.pop("ayana")
        panchang.pop("season")
        panchang.pop("moon_sign")
        panchang["nepal_samvat"] = {"year": 1146, "era": "Tachhalaga"}
        panchang["samvatsara"] = {"name": "Parabhava", "nepali": "पराभव"}
        panchang["sunrise"] = {"time": "05:42"}
        panchang["sunset"] = {"time": "18:42"}

        model = build_panchang_model(payload, "en")
        values = {row["key"]: row["value"] for section in model["sections"] for row in section["rows"]}

        self.assertEqual(values["shaka"], "1948")
        self.assertEqual(values["nepal_samvat"], "1146 (Tachhalaga)")
        self.assertEqual(values["samvatsara"], "Parabhava")
        self.assertEqual(values["ayana"], "Dakshinayan")
        self.assertEqual(values["season"], "Monsoon")
        self.assertEqual(values["moon_sign"], "Virgo")
        self.assertEqual(values["sunrise"], "05:42")
        self.assertEqual(values["sunset"], "18:42")
        for key in ("shaka", "nepal_samvat", "samvatsara", "ayana", "season", "moon_sign", "sunrise", "sunset"):
            self.assertNotEqual(values[key], "—")

    def test_dasha_hierarchy_active_chain_and_payload_dates(self):
        model = build_dasha_model(sample_payload(), "ne")
        self.assertEqual(model["state"], "ready")
        maha = model["nodes"][0]
        antar = maha["children"][0]
        pratyantar = antar["children"][0]
        self.assertEqual([maha["level_key"], antar["level_key"], pratyantar["level_key"]], ["maha", "antar", "pratyantar"])
        self.assertEqual(pratyantar["path_text"], "शुक्र / सूर्य / चन्द्र")
        self.assertEqual([node["display_lord"] for node in model["active_chain"]], ["शुक्र", "सूर्य", "चन्द्र"])
        self.assertEqual(maha["start_display"], "२०७५-०६-१८")
        self.assertTrue(maha["partial"])

    def test_dasha_phal_levels_flattening_and_active_antardasha_default(self):
        payload = sample_payload()
        levels = [DashaPhalPage.LEVELS[level][0] for level in range(1, 6)]
        self.assertEqual(
            levels,
            ["महादशा", "अन्तर्दशा", "प्रत्यन्तरदशा", "सूक्ष्मदशा", "प्राणदशा"],
        )

        maha = DashaPhalPage.flatten_periods(payload["dasha"], 1)
        antar = DashaPhalPage.flatten_periods(payload["dasha"], 2)
        pratyantar = DashaPhalPage.flatten_periods(payload["dasha"], 3)
        self.assertEqual([item[0]["lord"] for item in maha], ["Venus"])
        self.assertEqual([item[0]["lord"] for item in antar], ["Sun"])
        self.assertEqual([item[0]["lord"] for item in pratyantar], ["Moon"])

        active = DashaPhalPage.active_path(payload["dasha"])
        self.assertEqual([node["lord"] for node in active], ["Venus", "Sun", "Moon"])
        default = next(
            item for item in antar
            if item[0].get("is_active") or item[0] in active
        )
        self.assertEqual(default[0]["lord"], "Sun")
        self.assertEqual([node["lord"] for node in default[1]], ["Venus", "Sun"])

    def test_missing_empty_malformed_and_error_states_are_explicit(self):
        for builder in (build_planetary_model, build_panchang_model, build_dasha_model):
            self.assertEqual(builder(None, "en")["state"], "no_chart")
            self.assertEqual(builder({"error": "Calculation failed"}, "en")["state"], "error")
        self.assertEqual(build_planetary_model({}, "en")["state"], "empty")
        self.assertEqual(build_dasha_model({}, "en")["state"], "empty")
        self.assertEqual(build_panchang_model({}, "en")["state"], "empty")
        self.assertEqual(build_panchang_model({"panchang_requested_day": "bad"}, "en")["state"], "error")

    def test_daily_request_uses_kathmandu_noon_then_calculated_sunrise(self):
        params = daily_panchang_params(__import__("datetime").date(2026, 8, 16), "RAMAN")
        self.assertEqual(params["birth_time"], "12:00:00")
        self.assertEqual(params["city"], "Kathmandu")
        self.assertEqual(params["latitude"], 27.7172)
        self.assertEqual(params["longitude"], 85.3240)
        self.assertEqual(params["timezone"], 5.75)
        calls = []

        def fake_calculator(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                return {"panchang_requested_day": {"panchang": {"sunrise": {"time": "05:42"}}}, "planets": [{"name": "Moon", "longitude_in_sign": 2}]}
            return {"planets": [{"name": "Sun", "longitude_in_sign": 10}]}

        result = calculate_daily_panchang(__import__("datetime").date(2026, 8, 16), "RAMAN", calculator=fake_calculator)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["birth_time"], "12:00:00")
        self.assertEqual(calls[1]["birth_time"], "05:42:00")
        self.assertEqual(calls[1]["name"], "Daily Panchang Sunrise Positions")
        self.assertEqual(result["planets"][0]["name"], "Sun")
        self.assertEqual(result["daily_panchang_context"]["selected_date"], "2026-08-16")

    def test_daily_display_matches_web_minute_precision_for_backend_times(self):
        payload = sample_payload()
        payload["daily_panchang_context"] = {"selected_date": "2026-08-16"}
        panchang = payload["panchang_requested_day"]["panchang"]
        panchang["sunrise"] = {"time": "05:42"}
        panchang["sunset"] = {"time": "18:37"}
        panchang["tithi"]["end_time"] = "15:20:59"
        panchang["nakshatra"]["end_time"] = "12:30:41"
        panchang["yoga"]["end_time"] = "24:07:33"
        panchang["yoga"]["next_name"] = "Vyatipata"
        panchang["karana"]["end_time"] = "08:11:27"
        panchang["karana"]["next_name"] = "Balava"

        model = build_panchang_model(payload, "en")
        values = {row["key"]: row["value"] for section in model["sections"] for row in section["rows"]}

        self.assertEqual(values["sunrise"], "05:42")
        self.assertEqual(values["sunset"], "18:37")
        self.assertEqual(values["tithi"], "Panchami, 15:20 after Shashthi")
        self.assertEqual(values["nakshatra"], "Rohini, 12:30 after Mrigashira")
        self.assertEqual(values["yoga"], "Siddhi, 24:07 after Vyatipata")
        self.assertEqual(values["karana"], "Bava, 08:11 after Balava")

    def test_real_backend_daily_model_has_exact_web_minute_parity(self):
        payload = calculate_daily_panchang(__import__("datetime").date(2026, 8, 16))
        panchang = payload["panchang_requested_day"]["panchang"]
        model = build_panchang_model(payload, "en")
        values = {
            row["key"]: row["value"]
            for section in model["sections"]
            for row in section["rows"]
        }

        self.assertEqual(
            payload["daily_panchang_context"]["location"],
            DAILY_PANCHANG_LOCATION,
        )
        self.assertEqual(values["sunrise"], panchang["sunrise"]["time"][:5])
        self.assertEqual(values["sunset"], panchang["sunset"]["time"][:5])
        for key in ("tithi", "nakshatra", "yoga", "karana"):
            expected_minute = panchang[key]["end_time"][:5]
            self.assertIn(f", {expected_minute} ", values[key])

    def test_daily_model_labels_selected_date_instead_of_birth_date(self):
        payload = sample_payload()
        payload["daily_panchang_context"] = {"selected_date": "2026-08-16"}
        model = build_panchang_model(payload, "en")
        values = {row["key"]: row["value"] for section in model["sections"] for row in section["rows"]}
        self.assertEqual(values["ad_date"], "16 Aug 2026")


class FoundationalWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_planetary_table_headers_colors_dimensions_and_state(self):
        page = PlanetaryInfoPage(sample_payload(), "en")
        self.assertEqual(page._table.columnCount(), 10)
        self.assertEqual([page._table.horizontalHeaderItem(i).text() for i in range(10)], ["Planet", "Sign", "Degree", "House", "Nakshatra", "Retrograde", "Combust", "Relation", "Status", "Vargottama"])
        self.assertGreaterEqual(page._table.minimumWidth(), 860)
        self.assertGreaterEqual(page._table.minimumHeight(), 380)
        self.assertEqual(page._table.verticalHeader().defaultSectionSize(), 34)
        self.assertEqual(page._table.item(0, 8).foreground().color().name(), STATUS_COLORS["exalted"])
        self.assertEqual(page._table.item(1, 8).foreground().color().name(), STATUS_COLORS["debilitated"])
        page.refresh({"error": "Calculation failed"})
        self.assertEqual(page.state, "error")
        self.assertEqual(page._state_label.text(), "Calculation failed")

    def test_panchang_sections_layout_dimensions_and_selectable_output(self):
        page = PanchangInfoPage(sample_payload(), "en")
        self.assertEqual(page.state, "ready")
        # The report grid is a 2x3 layout. Row 0 holds the date/sun banner,
        # the sankalpa card and the samvat section; row 1 holds the panchang,
        # sun/day and sunrise-planets sections. Assert by grid cell so the
        # deterministic positions are verified rather than layout insertion order.
        frame_at = {
            (page._grid.getItemPosition(i)[0], page._grid.getItemPosition(i)[1]):
            page._grid.itemAt(i).widget().objectName()
            for i in range(page._grid.count())
            if page._grid.itemAt(i).widget() is not None
        }
        self.assertEqual(
            frame_at,
            {
                (0, 0): "panchangSection_date_sun",
                (0, 1): "panchangSection_sankalpa",
                (0, 2): "panchangSection_samvat",
                (1, 0): "panchangSection_panchang",
                (1, 1): "panchangSection_sun_day",
                (1, 2): "panchangSection_sunrise_planets",
            },
        )
        self.assertEqual(page._grid.getItemPosition(0), (0, 0, 1, 1))
        self.assertEqual(page._grid.getItemPosition(1), (0, 1, 1, 1))
        labels = page.findChildren(QLabel)
        row_labels = [label for label in labels if label.text() == "Bikram Sambat"]
        self.assertEqual(len(row_labels), 1)
        self.assertGreaterEqual(row_labels[0].minimumWidth(), 100)
        value_labels = [label for label in labels if label.text() == "Taurus"]
        self.assertTrue(value_labels[0].textInteractionFlags() & Qt.TextSelectableByMouse)
        page.refresh(None)
        self.assertEqual(page.state, "no_chart")

    def test_daily_controls_and_navigation_activation_are_independent_of_birth_report(self):
        page = PanchangInfoPage(
            None,
            "en",
            auto_calculate=True,
            show_initial_data=False,
        )
        # auto_calculate renders *today's* panchang inline during __init__: the
        # daily worker QThread was removed because its queued quit() leaked the
        # thread and aborted the process with 0xC0000409.  So the page is
        # already "ready" with the daily report and without any birth chart -
        # which is exactly the independence this test guards.
        self.assertEqual(page.state, "ready")
        self.assertEqual(
            page._data["daily_panchang_context"]["selected_date"],
            QDate.currentDate().toString("yyyy-MM-dd"),
        )
        # The ephemeris computation is synchronous, so no worker thread may be
        # left behind for the page or the process to clean up.
        self.assertIsNone(page._daily_thread)
        self.assertEqual(page._date_edit.date(), QDate.currentDate())
        self.assertEqual(
            (page._ayanamsha, page._node_type, page._house_system),
            ("LAHIRI", "MEAN", "WHOLE_SIGN"),
        )
        page._date_edit.setDate(QDate(2026, 8, 16))
        self.assertTrue(page._bs_date_label.text().startswith("BS "))
        page._today_button.click()
        self.assertEqual(page._date_edit.date(), QDate.currentDate())

        calls = []
        page.calculate_selected_date = lambda: calls.append(page._date_edit.date())
        page.activate()
        page.activate()
        self.assertEqual(calls, [QDate.currentDate()])

        personal_payload = sample_payload()
        personal_payload["metadata"].update({
            "ayanamsha_type": "RAMAN",
            "node_type": "TRUE",
            "house_system": "PLACIDUS",
        })
        independent_page = PanchangInfoPage(personal_payload, "en", show_initial_data=False)
        self.assertEqual(
            (independent_page._ayanamsha, independent_page._node_type, independent_page._house_system),
            ("LAHIRI", "MEAN", "WHOLE_SIGN"),
        )

    def test_unified_dasha_page_defaults_to_vimshottari_and_exposes_status_tabs(self):
        payload = sample_payload()
        payload["dasha_reports"] = {
            "vimshottari": {"status": "ready"},
            "tribhagi": {"status": "unavailable", "message": "pending"},
            "yogini": {"status": "unavailable", "message": "pending"},
        }
        page = CompleteDashaPage(payload, "en")
        self.assertEqual(page._stack.currentWidget(), page._pages["vimshottari"])
        self.assertEqual(set(page._pages), {"vimshottari", "tribhagi", "ashtottari", "yogini"})
        self.assertEqual(
            [page._buttons[key].text() for key, _, _ in page.SYSTEMS],
            ["Vimshottari", "Tribhagi", "Ashtottari", "Yogini"],
        )
        level_labels = {
            "Mahadasha", "Antardasha", "Pratyantardasha", "Sookshmadasha", "Pranadasha",
        }
        level_buttons = {
            button.text() for button in page._pages["vimshottari"].findChildren(QPushButton)
        }
        self.assertTrue(level_labels.issubset(level_buttons))
        page._select_system("tribhagi")
        self.assertEqual(page._stack.currentWidget(), page._pages["tribhagi"])
        self.assertIn("unavailable", page._pages["tribhagi"].findChildren(QLabel)[0].text())

    def test_unified_dasha_page_supports_legacy_payload_without_normalized_reports(self):
        page = CompleteDashaPage(sample_payload(), "en")
        self.assertIsInstance(page._pages["vimshottari"], DashaPhalPage)
        self.assertEqual(page._stack.currentWidget(), page._pages["vimshottari"])

    def test_unified_dasha_page_initializes_no_chart_and_refreshes_explicit_states(self):
        page = CompleteDashaPage(None, "en")
        self.assertEqual(set(page._pages), {"vimshottari", "tribhagi", "ashtottari", "yogini"})
        # The level renderer is debounced (50 ms single-shot timer) so the first
        # rebuild never runs in a headless test without an event loop. Force it
        # deterministically before asserting the empty-state result panel.
        vimshottari_page = page._pages["vimshottari"]
        vimshottari_page._level_render_timer.stop()
        vimshottari_page._apply_pending_level()
        self.assertTrue(
            any(
                "Select a dasha period" in label.text()
                for label in vimshottari_page.findChildren(QLabel)
            )
        )
        page.refresh({
            "dasha_reports": {
                "vimshottari": {"status": "error", "message": "Calculation failed"},
                "tribhagi": {"status": "empty", "message": "No periods"},
                "yogini": {"status": "no_chart", "message": "No chart"},
            }
        })
        self.assertIn("Calculation failed", page._pages["vimshottari"].findChildren(QLabel)[0].text())

    def test_unified_dasha_page_uses_nepali_system_and_level_labels(self):
        page = CompleteDashaPage(sample_payload(), "ne")
        self.assertEqual(
            [page._buttons[key].text() for key, _, _ in page.SYSTEMS],
            ["विंशोत्तरी", "त्रिभागी", "अष्टोत्तरी", "योगिनी"],
        )
        level_buttons = page._pages["vimshottari"].findChildren(QPushButton)
        self.assertTrue(
            all(label in {button.text() for button in level_buttons} for label in (
                "महादशा", "अन्तर्दशा", "प्रत्यन्तरदशा", "सूक्ष्मदशा", "प्राणदशा",
            ))
        )

    def test_tribhagi_ready_report_uses_shared_five_level_dasha_phal_page(self):
        payload = sample_payload()
        node = {
            "lord": "Sun",
            "lord_nepali": "सूर्य",
            "level": 1,
            "start": "2020-01-01",
            "end": "2030-01-01",
            "start_bs": "२०७६-०९-१७",
            "end_bs": "२०८६-०९-१७",
            "is_active": True,
        }
        current = node
        for level, lord in ((2, "Moon"), (3, "Mars"), (4, "Mercury"), (5, "Jupiter")):
            child = {
                "lord": lord,
                "level": level,
                "start": "2026-01-01",
                "end": "2027-01-01",
                "is_active": level == 5,
                "children": [],
            }
            current["children"] = [child]
            current = child
        payload["dasha_reports"] = {
            "tribhagi": {"status": "ready", "periods": [node]},
        }
        page = CompleteDashaPage(payload, "en")
        page._select_system("tribhagi")
        tribhagi_page = page._pages["tribhagi"]
        # The level renderer is debounced (50 ms single-shot timer) so the first
        # rebuild never runs in a headless test without an event loop. Force it
        # deterministically before counting the rendered period buttons.
        tribhagi_page._level_render_timer.stop()
        tribhagi_page._apply_pending_level()
        self.assertIsInstance(tribhagi_page, DashaPhalPage)
        self.assertEqual(tribhagi_page._system, "tribhagi")
        self.assertEqual(tribhagi_page._level, 2)
        level_labels = {
            "Mahadasha", "Antardasha", "Pratyantardasha", "Sookshmadasha", "Pranadasha",
        }
        self.assertTrue(
            level_labels.issubset({
                button.text() for button in tribhagi_page.findChildren(QPushButton)
            })
        )
        self.assertEqual(len(tribhagi_page._period_buttons), 1)
        self.assertIn("Tribhagi Dasha Phal", tribhagi_page._title.text())

    def test_dasha_timeline_groups_subperiods_under_mahadasha_headers(self):
        """Sub-periods must stay grouped under their Mahadasha header.

        Regression: flattening all Antardashas into one undifferentiated list
        made each Mahadasha boundary look like a missing planet/yogini (e.g. a
        Bhadrika Mahadasha ending with भ्रामरी followed by an Ulka Mahadasha
        starting with उल्का read as "भ्रामरी → उल्का, भद्रिका छैन"). The web
        timeline solves this with Mahadasha group headers; the native timeline
        must render one header per Mahadasha before its sub-periods."""
        def md(lord, lord_ne, start, end, ad_lords):
            children = [
                {
                    "lord": child_lord,
                    "lord_nepali": child_ne,
                    "level": 2,
                    "start": start,
                    "end": end,
                    "children": [],
                }
                for child_lord, child_ne in ad_lords
            ]
            return {
                "lord": lord,
                "lord_nepali": lord_ne,
                "level": 1,
                "start": start,
                "end": end,
                "is_active": False,
                "children": children,
            }

        payload = sample_payload()
        payload["dasha_reports"] = {
            "yogini": {
                "status": "ready",
                "periods": [
                    md("Bhadrika", "भद्रिका", "2022-08-16", "2027-08-16", [
                        ("Bhadrika", "भद्रिका"), ("Ulka", "उल्का"),
                        ("Siddha", "सिद्धा"), ("Sankata", "संकटा"),
                        ("Mangala", "मङ्गला"), ("Pingala", "पिङ्गला"),
                        ("Dhanya", "धान्या"), ("Bhramari", "भ्रामरी"),
                    ]),
                    md("Ulka", "उल्का", "2027-08-16", "2033-08-15", [
                        ("Ulka", "उल्का"), ("Siddha", "सिद्धा"),
                        ("Sankata", "संकटा"), ("Mangala", "मङ्गला"),
                        ("Pingala", "पिङ्गला"), ("Dhanya", "धान्या"),
                        ("Bhramari", "भ्रामरी"), ("Bhadrika", "भद्रिका"),
                    ]),
                ],
            },
        }
        page = DashaPhalPage(payload, "ne", system="yogini")
        page._set_level(2)

        # The level-change timer is single-shot (50 ms); force the rebuild so
        # the assertions below are deterministic.
        page._level_render_timer.stop()
        page._apply_pending_level()

        headers = [
            item.widget().text()
            for i in range(page._timeline_layout.count())
            if (item := page._timeline_layout.itemAt(i)) and isinstance(item.widget(), QLabel)
            and "महादशा" in item.widget().text()
        ]
        self.assertEqual(len(headers), 2)
        self.assertIn("भद्रिका", headers[0])
        self.assertIn("उल्का", headers[1])
        # The active Antardasha still lands in the Bhadrika group and each group
        # keeps all eight Antardashas in canonical order.
        bhadrika_block = [
            item.widget().text().splitlines()[0] for i in range(page._timeline_layout.count())
            if (item := page._timeline_layout.itemAt(i)) and isinstance(item.widget(), QPushButton)
            and item.widget().text().splitlines()[0].startswith("भद्रिका")
        ]
        self.assertEqual(bhadrika_block, [
            "भद्रिका → भद्रिका", "भद्रिका → उल्का", "भद्रिका → सिद्धा",
            "भद्रिका → संकटा", "भद्रिका → मङ्गला", "भद्रिका → पिङ्गला",
            "भद्रिका → धान्या", "भद्रिका → भ्रामरी",
        ])


if __name__ == "__main__":
    unittest.main()
