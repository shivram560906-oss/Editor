# -*- coding: utf-8 -*-
"""Focused headless parity tests for the main native birth-data ribbon."""
import os
import unittest
from datetime import date
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QWidget

from gui.app import (
    RIBBON_FIELD_KEYS,
    RIBBON_UNAVAILABLE,
    JyotishMainWindow,
    build_birth_ribbon_model,
)


def payload(name="Sita Sharma", city="Kathmandu", gender=1):
    return {
        "metadata": {
            "name": name,
            "birth_date": "2000-04-15",
            "birth_time": "10:30:00",
            "city": city,
            "gender": gender,
        },
        "dasha": [
            {
                "is_active": True,
                "lord": "Venus",
                "lord_nepali": "शुक्र",
                "start_bs": "2075-06-18",
                "end_bs": "2095-06-18",
                "children": [
                    {
                        "is_active": True,
                        "lord": "Sun",
                        "lord_nepali": "सूर्य",
                        "start_bs": "2082-08-16",
                        "end_bs": "2085-08-16",
                    }
                ],
            }
        ],
    }


class RibbonHarness(QWidget):
    _build_ribbon = JyotishMainWindow._build_ribbon
    _update_ribbon = JyotishMainWindow._update_ribbon

    def __init__(self, language="en"):
        super().__init__()
        self._language = language
        self._is_ne = language == "ne"
        self.saved = False

    def build_ribbon(self):
        self._ribbon = self._build_ribbon()
        return self._ribbon

    def _save_current_chart(self):
        self.saved = True

    def _edit_current_chart(self):
        self.edited = True

    def _close_chart(self):
        self.closed = True


class BirthRibbonModelTests(unittest.TestCase):
    def test_exact_english_field_order_labels_and_values(self):
        with patch("gui.app.gregorian_to_bs", return_value={"year": 2057, "month": 1, "day": 3}):
            model = build_birth_ribbon_model(payload(), "en", today=date(2026, 8, 16))
        self.assertEqual([field["key"] for field in model], list(RIBBON_FIELD_KEYS))
        self.assertEqual(
            [field["label"] for field in model],
            ["Name", "Birth Date (BS)", "Birth Time", "Birth Place", "Full Age", "Gender", "Active Mahadasha", "Active Antardasha"],
        )
        self.assertEqual(
            [field["value"] for field in model],
            [
                "Sita Sharma",
                "3 Baisakh 2057 BS",
                "10:30:00",
                "Kathmandu",
                "26y 4m 1d",
                "Female",
                "Venus (2075-06-18 - 2095-06-18)",
                "Sun (2082-08-16 - 2085-08-16)",
            ],
        )
        self.assertEqual([field["badge"] for field in model], [False] * 6 + [True, True])

    def test_nepali_formatting_metadata_gender_precedence_and_unavailable_states(self):
        with patch("gui.app.gregorian_to_bs", return_value={"year": 2057, "month": 1, "day": 3}):
            model = build_birth_ribbon_model(payload(gender=0), "ne", gender=1, today=date(2026, 8, 16))
        values = {field["key"]: field["value"] for field in model}
        self.assertEqual(values["birth_date_bs"], "२०५७ बैशाख ३")
        self.assertEqual(values["full_age"], "२६ वर्ष ४ महिना १ दिन")
        self.assertEqual(values["gender"], "पुरुष")
        self.assertEqual(values["mahadasha"], "शुक्र (२०७५-०६-१८ - २०९५-०६-१८)")

        missing = build_birth_ribbon_model({"metadata": {"gender": 1}}, "en")
        missing_values = {field["key"]: field["value"] for field in missing}
        for key in ("name", "birth_date_bs", "birth_time", "birth_place", "full_age", "mahadasha", "antardasha"):
            self.assertEqual(missing_values[key], RIBBON_UNAVAILABLE)
        self.assertEqual(missing_values["gender"], "Female")


class BirthRibbonWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_widget_structure_style_visibility_and_horizontal_overflow(self):
        owner = RibbonHarness("en")
        ribbon = owner.build_ribbon()
        ribbon.hide()
        owner._update_ribbon(payload())
        QApplication.processEvents()

        self.assertTrue(ribbon.isVisibleTo(owner))
        self.assertEqual(ribbon.height(), 48)
        self.assertEqual(list(owner._ribbon_fields), list(RIBBON_FIELD_KEYS))
        self.assertEqual(owner._ribbon_scroll.verticalScrollBarPolicy(), Qt.ScrollBarAlwaysOff)
        self.assertEqual(owner._ribbon_scroll.horizontalScrollBarPolicy(), Qt.ScrollBarAsNeeded)
        self.assertIn("height: 0px", owner._ribbon_scroll.styleSheet())
        self.assertEqual(owner._ribbon_fields_layout.contentsMargins().left(), 16)
        self.assertEqual(owner._ribbon_fields_layout.contentsMargins().top(), 8)
        self.assertEqual(owner._ribbon_fields_layout.spacing(), 16)

        labels = [pair[0] for pair in owner._ribbon_fields.values()]
        values = [pair[1] for pair in owner._ribbon_fields.values()]
        self.assertEqual([label.text() for label in labels], [
            "Name", "Birth Date (BS)", "Birth Time", "Birth Place", "Full Age", "Gender", "Active Mahadasha", "Active Antardasha"
        ])
        self.assertTrue(all(label.objectName() == "BirthRibbonLabel" for label in labels))
        self.assertTrue(all("font-size: 10px" in label.styleSheet() and "font-weight: 700" in label.styleSheet() for label in labels))
        self.assertTrue(all(value.objectName() == "BirthRibbonValue" for value in values))
        self.assertTrue(all("font-size: 13px" in value.styleSheet() for value in values[:6]))
        self.assertTrue(all("font-size: 11px" in value.styleSheet() and "border-radius: 999px" in value.styleSheet() for value in values[6:]))
        frames = owner._ribbon_content.findChildren(QFrame, "BirthRibbonField")
        self.assertEqual(len(frames), 8)
        self.assertTrue(all("border-right: 1px" in frame.styleSheet() for frame in frames[:-1]))
        self.assertEqual(frames[-1].styleSheet(), "")

    def test_every_update_replaces_old_values_and_clears_missing_fields(self):
        owner = RibbonHarness("en")
        ribbon = owner.build_ribbon()
        owner._update_ribbon(payload(name="First Person", city="Old City", gender=1))
        first = {key: value.text() for key, (_, value) in owner._ribbon_fields.items()}
        self.assertEqual(first["name"], "First Person")
        self.assertEqual(first["birth_place"], "Old City")
        self.assertIn("Venus", first["mahadasha"])

        owner._update_ribbon({"metadata": {"name": "Second Person", "gender": 0}})
        second = {key: value.text() for key, (_, value) in owner._ribbon_fields.items()}
        self.assertEqual(second["name"], "Second Person")
        self.assertEqual(second["gender"], "Male")
        for key in ("birth_date_bs", "birth_time", "birth_place", "full_age", "mahadasha", "antardasha"):
            self.assertEqual(second[key], RIBBON_UNAVAILABLE)
        self.assertNotIn("First Person", "\n".join(second.values()))
        self.assertNotIn("Old City", "\n".join(second.values()))
        self.assertNotIn("Venus", "\n".join(second.values()))
        self.assertFalse(ribbon.isHidden())


if __name__ == "__main__":
    unittest.main()
