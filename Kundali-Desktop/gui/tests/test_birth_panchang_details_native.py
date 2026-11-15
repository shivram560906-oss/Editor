# -*- coding: utf-8 -*-
"""Headless parity checks for the native combined Birth Panchang report."""
import os
import re
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from gui.app import NAV_STRUCTURE, JyotishMainWindow, normalize_action_id
from gui.widgets.avakahada_chakra import AvakahadaChakraPage
from gui.widgets.birth_panchang_details import (
    BirthPanchangDetailsPage,
    build_birth_panchang_model,
    compose_birth_panchang_text,
)


def sample_payload():
    return {
        "metadata": {
            "name": "Sita Sharma", "gender": 1, "birth_date": "2000-04-15",
            "birth_time": "10:30:00", "city": "Kathmandu", "country": "Nepal",
            "latitude": 27.7172, "longitude": 85.3240, "timezone": 5.75,
            "ayanamsha_value": 23.85, "ayanamsha_type": "LAHIRI",
        },
        "panchang": {
            "samvatsara": "Pramadi", "month_type": "normal",
            "month_type_nepali": "सामान्य",
            "tithi": {"name": "Panchami", "nepali": "पञ्चमी", "birth_name": "Panchami", "birth_nepali": "पञ्चमी", "paksha": "Shukla", "paksha_nepali": "शुक्ल", "end_time": "15:20"},
            "nakshatra": {"name": "Rohini", "nepali": "रोहिणी", "pada": 2, "end_time": "12:30"},
            "yoga": {"name": "Siddhi", "nepali": "सिद्धि", "end_time": "16:10"},
            "karana": {"name": "Bava", "nepali": "बव", "end_time": "14:00"},
            "sunrise": {"time": "05:55"}, "sunset": {"time": "18:20"}, "day_duration": "12:25",
        },
        "panchang_requested_day": {"panchang": {
            "tithi": {"name": "Panchami", "nepali": "पञ्चमी"},
            "nakshatra": {"name": "Rohini", "nepali": "रोहिणी"},
            "yoga": {"name": "Siddhi", "nepali": "सिद्धि"},
            "karana": {"name": "Bava", "nepali": "बव"},
            "sunrise": {"time": "05:55"}, "sunset": {"time": "18:20"},
        }},
        "lagna": {"sign_number": 1, "longitude_in_sign": 12.5},
        "planets": [
            {"name": "Moon", "sign_number": 2, "sidereal_longitude": 42.0},
            {"name": "Sun", "sign_number": 1, "longitude_in_sign": 1.5},
        ],
        "avakahada_chakra": {
            "nakshatra": "Rohini", "pada": 2, "name_akshara": "वि", "rashi": "वृष", "rashi_lord": "शुक्र",
            "varna": "वैश्य", "vashya": "चतुष्पद", "yoni": "सर्प", "viryoni": "नकुल", "varga": "क", "shatru_varga": "च", "gana": "मनुष्य", "nadi": "अन्त्य", "asana": 0,
        },
        "dasha": [{"is_active": True, "lord_nepali": "शुक्र", "lord": "Venus", "start_bs": "२०७५-०६-१८", "end_bs": "२०९५-०६-१८", "children": [{"is_active": True, "lord_nepali": "सूर्य", "lord": "Sun", "start_bs": "२०८२-०८-१६", "end_bs": "२०८५-०८-१६"}]}],
    }


class BirthPanchangModelTests(unittest.TestCase):
    def test_sections_rows_and_payload_values_match_web_major_sections(self):
        model = build_birth_panchang_model(sample_payload(), "ne", 1)
        self.assertEqual(model["state"], "ready")
        self.assertEqual(
            [section["key"] for section in model["sections"]],
            ["birth_details", "geographic", "samvat", "avakahada", "panchanga", "sun_moon", "dasha"],
        )
        sections = {section["key"]: section for section in model["sections"]}
        self.assertEqual(set(sections), {"birth_details", "geographic", "samvat", "avakahada", "panchanga", "sun_moon", "dasha"})
        values = {row["key"]: row["value"] for section in model["sections"] for row in section["rows"]}
        for key, value in {"name": "Sita Sharma", "place": "Kathmandu", "nakshatra": "रोहिणी", "yoni": "सर्प", "gana": "मनुष्य", "day_duration": "१२:२५", "moon_sign": "वृष", "birth_mahadasha": "शुक्र", "birth_antardasha": "सूर्य"}.items():
            self.assertEqual(values[key], value)
        for key in ("birth_date_bs", "birth_date_ad", "weekday", "birth_time", "latitude", "longitude", "timezone", "gmt", "lagna", "tithi_sunrise", "tithi_end", "tithi_birth", "nakshatra_sunrise", "nakshatra_end", "nakshatra_birth", "yoga_sunrise", "karana_birth", "sunrise", "sunset", "moon_pada", "ayanamsha"):
            self.assertIn(key, values)
        self.assertEqual(model["ribbon"]["mahadasha"], "शुक्र (२०७५-०६-१८ - २०९५-०६-१८)")
        self.assertEqual(model["ribbon"]["antardasha"], "सूर्य (२०८२-०८-१६ - २०८५-०८-१६)")
        self.assertIn("वर्ष", model["metadata"]["full_age"])
        panchanga_keys = [row["key"] for row in sections["panchanga"]["rows"]]
        self.assertEqual(panchanga_keys[:3], ["tithi_birth", "tithi_sunrise", "tithi_end"])

    def test_nepali_mode_converts_every_visible_number_to_nepali_digits(self):
        model = build_birth_panchang_model(sample_payload(), "ne", 1)
        visible_values = [
            row["value"]
            for section in model["sections"]
            for row in section["rows"]
        ]
        visible_values.extend(model["ribbon"].values())
        visible_values.append(model["metadata"]["full_age"])

        self.assertFalse(re.search(r"[0-9]", "\n".join(visible_values)))
        values = {
            row["key"]: row["value"]
            for section in model["sections"]
            for row in section["rows"]
        }
        self.assertEqual(values["birth_date_bs"], "२०५७ बैशाख ३")
        self.assertEqual(values["birth_date_ad"], "२०००-०४-१५")
        self.assertEqual(values["birth_time"], "१०:३०:००")
        self.assertEqual(values["latitude"], "२७°४३′०२″ N")
        self.assertEqual(values["timezone"], "+०५:४५ घण्टा")
        self.assertEqual(values["moon_pada"], "२")

    def test_english_labels_and_copy_text(self):
        model = build_birth_panchang_model(sample_payload(), "en", 1)
        text = compose_birth_panchang_text(model)
        for label in ("Birth Details", "Geographic Details", "Avakahada Chakra", "Panchanga - Five Limbs", "Sun and Moon Details", "Dasha Details", "Birth Place", "Nakshatra", "Shatru Varga"):
            self.assertIn(label, text)
        self.assertIn("Sita Sharma", text)
        self.assertIn("2000-04-15", text)
        self.assertIn("10:30:00", text)

    def test_missing_and_error_states_are_explicit(self):
        self.assertEqual(build_birth_panchang_model(None, "en")["state"], "no_chart")
        self.assertEqual(build_birth_panchang_model({"error": "Calculation failed"}, "en")["state"], "error")
        incomplete = build_birth_panchang_model({"metadata": {"birth_date": "2000-04-15"}, "avakahada_chakra": {}}, "en")
        self.assertEqual(incomplete["state"], "incomplete")
        self.assertIn("—", compose_birth_panchang_text(incomplete))


class BirthPanchangRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_daily_and_birth_reports_are_separate_visible_actions(self):
        reports = next(category for category in NAV_STRUCTURE if category["id"] == "reports")
        visible_ids = [item["id"] for item in reports["items"]]
        self.assertEqual(visible_ids[:2], ["report_panchang", "report_birth_panchang"])
        self.assertNotIn("report_avakahada_chakra", visible_ids)

    def test_combined_and_standalone_routes_are_distinct(self):
        self.assertEqual(normalize_action_id("birth_panchang"), "report_birth_panchang")
        self.assertEqual(normalize_action_id("report_birth_panchang"), "report_birth_panchang")
        self.assertEqual(normalize_action_id("avakahada_chakra"), "report_avakahada_chakra")
        owner = type("Owner", (), {"_chart_data": sample_payload(), "_language": "en"})()
        combined = JyotishMainWindow._build_page(owner, "report_birth_panchang")
        avakahada = JyotishMainWindow._build_page(owner, "report_avakahada_chakra")
        self.assertIsInstance(combined, BirthPanchangDetailsPage)
        self.assertIsInstance(avakahada, AvakahadaChakraPage)
        self.assertNotIsInstance(combined, AvakahadaChakraPage)

    def test_widget_renders_reference_structure_values_and_actions(self):
        page = BirthPanchangDetailsPage(sample_payload(), "ne", 1)
        page.resize(1200, 800)
        QApplication.processEvents()
        labels = "\n".join(label.text() for label in page.findChildren(QLabel))
        self.assertIsNone(re.search(r"[0-9]", labels))
        for text in ("जन्म पञ्चाङ्ग", "ज्योतिषीय विवरण र विश्लेषण", "जन्म पञ्चाङ्ग तथा अवकहडा चक्र", "जन्म विवरण", "भौगोलिक विवरण", "अवकहडा चक्र", "पञ्चाङ्ग - पञ्च अङ्ग", "रोहिणी", "सर्प", "सूर्योदय", "महादशा"):
            self.assertIn(text, labels)
        self.assertGreaterEqual(labels.count("२०५७ बैशाख ३"), 2)
        self.assertNotIn("बैशाख ३, २०५७", labels)
        ribbon_labels = [label.text() for label in page._ribbon.findChildren(QLabel)][::2]
        self.assertEqual(ribbon_labels, ["नाम", "जन्म मिति (वि.सं.)", "जन्म समय", "जन्म स्थान", "पूर्ण उमेर", "लिङ्ग", "सक्रिय महादशा", "सक्रिय अन्तर्दशा"])
        expected_positions = {
            "birth_details": (0, 0, 1, 1),
            "geographic": (0, 1, 1, 1),
            "samvat": (0, 2, 1, 1),
            "avakahada": (0, 3, 1, 1),
            "panchanga": (1, 0, 1, 1),
            "sun_moon": (1, 1, 1, 1),
            "dasha": (1, 2, 1, 1),
        }
        for key, position in expected_positions.items():
            self.assertEqual(
                page._grid.getItemPosition(page._grid.indexOf(page._frames[key])),
                position,
            )
        first_row_frames = [page._frames[key] for key in ("birth_details", "geographic", "samvat", "avakahada")]
        first_row_heights = [frame.height() for frame in first_row_frames]
        self.assertTrue(all(height == first_row_heights[0] for height in first_row_heights))
        for frame in first_row_frames:
            heading = frame.findChild(QLabel, "birthPanchangBoxTitle")
            self.assertIsNotNone(heading)
            field_labels = [
                label for label in frame.findChildren(QLabel)
                if label.objectName() == "birthPanchangFieldLabel"
            ]
            self.assertTrue(field_labels)
            self.assertTrue(all(label.minimumWidth() >= page._TOP_ROW_LABEL_WIDTH for label in field_labels))
        actions = {button.text() for button in page.findChildren(QPushButton)}
        self.assertEqual(actions, {"प्रतिलिपि", "PDF सुरक्षित गर्नुहोस्", "प्रिन्ट"})
        page.copy_report()
        self.assertIn("रोहिणी", QApplication.clipboard().text())

    @unittest.skipIf(
        sys.platform == "win32" and os.environ.get("QT_QPA_PLATFORM") == "offscreen",
        "QPrinter triggers a native exception in the Windows offscreen platform",
    )
    def test_report_content_renders_to_pdf_without_dialog(self):
        from PySide6.QtPrintSupport import QPrinter
        page = BirthPanchangDetailsPage(sample_payload(), "en", 1)
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "birth-panchang.pdf")
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            page._configure_printer(printer)
            self.assertGreaterEqual(page._render_to_printer(printer), 1)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main()
