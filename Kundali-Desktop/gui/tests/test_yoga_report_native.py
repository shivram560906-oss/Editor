# -*- coding: utf-8 -*-
"""Desktop native tests for the plain white Parashara Yoga report page.

The payloads below replicate the EXACT schema produced by
backend/calculator/yogas.py calculate_parashara_yogas_with_diagnostics():
the backend returns only ACTIVE yogas — there is no ``is_present`` flag and
no ``name_ne``/``description_ne``/``effect`` keys. The old widget filtered on
``is_present`` and therefore always rendered "कुनै योग भेटिएन". These tests
lock in the correct contract.
"""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel


def _app():
    return QApplication.instance() or QApplication([])


def _backend_yoga(**over) -> dict:
    """A yoga dict shaped exactly like the backend engine output."""
    yoga = {
        "id": "ruchaka",
        "name": "Ruchaka Yoga",
        "nepali": "रुचक योग",
        "category": "mahapurusha",
        "severity": "auspicious",
        "cause_en": "Mars occupies its own sign or exaltation in a Kendra.",
        "cause_ne": "मङ्गल आफ्नो राशि वा उच्चको राशिमा केन्द्रभावमा छ।",
        "result_en": "Strong physique, courageous leadership, wealth.",
        "result_ne": "बलियो शरीर, साहसी नेतृत्व, धन।",
        "remedy_en": "Chant 'Om Angarakaya Namah'.",
        "remedy_ne": "'ॐ अङ्गारकाय नमः' जप गर्नुहोस्।",
        "references": ["BPHS Ch.36"],
        "strength_pct": 82,
        "planets_involved": ["Mars"],
        "formation_en": "**Ruchaka Yoga** forms in this chart because Mars is in Aries sign "
                        "in the 1st House (Exalted).",
        "formation_ne": "यो कुण्डलीमा **रुचक योग** मङ्गल मेष राशिमा प्रथम भावमा उच्च भएर अवस्थित "
                        "भएको कारणले बनेको छ।",
        "chart_position_en": "Mars: House 1 (Aries, 15.0°)",
        "chart_position_ne": "मङ्गल: प्रथम भाव (मेष, १५.०°)",
        "planet_rows": [
            {
                "name_en": "Mars", "name_ne": "मङ्गल",
                "sign_en": "Aries", "sign_ne": "मेष", "sign_num": 1,
                "house": 1, "house_name_en": "1st House", "house_name_ne": "प्रथम भाव",
                "degree": 15.0, "state": "exalted", "is_own": False,
                "is_retro": False, "is_combust": False,
            },
        ],
    }
    yoga.update(over)
    return yoga


def _payload(*yogas) -> dict:
    return {"parashara_yogas": list(yogas), "yoga_diagnostics": []}


def _label_texts(widget) -> str:
    return "\n".join(l.text() for l in widget.findChildren(QLabel))


class YogaReportPageTests(unittest.TestCase):
    def test_renders_backend_yogas_without_is_present_flag(self):
        """Regression: backend yogas carry no is_present — all must render."""
        app = _app()
        from gui.widgets.yoga_report import YogaReportPage

        page = YogaReportPage(_payload(_backend_yoga()), language="ne")
        text = _label_texts(page)
        self.assertIn("रुचक योग", text)
        self.assertIn("फल:", text)
        self.assertIn("बलियो शरीर", text)
        self.assertIn("मङ्गल", text)          # planet position line
        self.assertIn("बल ८२%", text)         # strength
        # formation string had ** markers stripped
        self.assertNotIn("**", text)

    def test_renders_english(self):
        app = _app()
        from gui.widgets.yoga_report import YogaReportPage

        page = YogaReportPage(_payload(_backend_yoga()), language="en")
        text = _label_texts(page)
        self.assertIn("Ruchaka Yoga", text)
        self.assertIn("Phala:", text)
        self.assertIn("Strong physique", text)
        self.assertIn("Strength 82%", text)

    def test_multiple_and_all_types_rendered(self):
        app = _app()
        from gui.widgets.yoga_report import YogaReportPage

        yoga2 = _backend_yoga(
            id="hamsa", name="Hamsa Yoga", nepali="हंस योग",
            category="mahapurusha", planets_involved=["Jupiter"],
            strength_pct=None,
            planet_rows=[],
            formation_en="**Hamsa Yoga** forms from the overall chart.",
            formation_ne="यो कुण्डलीमा **हंस योग** कुण्डलीको समग्र स्थितिको आधारमा बनेको छ।",
        )
        yoga3 = _backend_yoga(
            id="gaja_kesari", name="Gaja Kesari Yoga", nepali="गज केसरी योग",
            category="chandra", severity="highly_auspicious",
            planets_involved=["Moon", "Jupiter"], strength_pct=None,
            planet_rows=[],
        )
        page = YogaReportPage(_payload(_backend_yoga(), yoga2, yoga3), language="ne")
        text = _label_texts(page)
        self.assertIn("रुचक योग", text)
        self.assertIn("हंस योग", text)
        self.assertIn("गज केसरी योग", text)
        self.assertIn("अत्यन्त शुभ", text)   # severity label
        self.assertIn("यस कुण्डलीमा जम्मा ३ वटा योगहरू", text)

    def test_empty_state(self):
        app = _app()
        from gui.widgets.yoga_report import YogaReportPage

        page = YogaReportPage(_payload(), language="ne")
        text = _label_texts(page)
        self.assertIn("कुनै पाराशरीय योग", text)

    def test_plain_page_has_no_card_boxes(self):
        """No rounded/colored card QFrames — plain white page only."""
        app = _app()
        from PySide6.QtWidgets import QFrame

        from gui.widgets.yoga_report import YogaReportPage

        page = YogaReportPage(_payload(_backend_yoga()), language="ne")
        for f in page.findChildren(QFrame):
            low = f.styleSheet().lower()
            self.assertNotIn("border-radius", low)
            self.assertNotIn("background: rgba", low)
    def test_nepali_language_purity(self):
        """Verify that Nepali view has no stray English UI labels."""
        app = _app()
        from gui.widgets.yoga_report import YogaReportPage

        page = YogaReportPage(_payload(_backend_yoga()), language="ne")
        text = _label_texts(page)

        # Must have Nepali titles and headers
        self.assertIn("पाराशरी योग प्रतिवेदन", text)
        self.assertIn("निर्माण विधि:", text)
        self.assertIn("फल:", text)
        self.assertIn("उपाय:", text)
        self.assertIn("यस कुण्डलीमा ग्रहहरूको स्थिति:", text)
        self.assertIn("पञ्च महापुरुष योग", text)
        self.assertIn("शुभ", text)
        self.assertIn("[स्थिति]", text)
        self.assertIn("उच्च", text)

        # Must NOT have English UI strings in Nepali mode
        self.assertNotIn("How it forms:", text)
        self.assertNotIn("Phala (Result):", text)
        self.assertNotIn("Planet positions in this chart:", text)
        self.assertNotIn("[Placement]", text)
        self.assertNotIn("Exalted", text)
        self.assertNotIn("Strength 82%", text)


if __name__ == "__main__":
    unittest.main()

