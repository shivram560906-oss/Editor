# -*- coding: utf-8 -*-
"""
gui/tests/test_traditional_cheena_a4.py

Tests for the Traditional Nepali Janmapatrika (चिना) A4 PDF Document and Print Engine.
Validates:
  1. HTML generation containing sacred verses, Panchang, D1/D9 charts, Avakahada, longitudes, Dashas, and remedies.
  2. High-resolution base64 chart rendering.
  3. Interactive widget instantiation, zoom controls, and refresh.
  4. PDF document generation via QPrinter producing a valid A4 PDF.
  5. Menu and NAV_STRUCTURE integration.
"""
import os
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout
from PySide6.QtCore import QMarginsF

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.widgets.traditional_cheena_a4 import (
    TraditionalCheenaA4Page,
    generate_traditional_cheena_html,
    render_traditional_chart_base64,
    to_ne_digits,
    dms_format_ne,
)
from gui.app import NAV_STRUCTURE, normalize_action_id, JyotishMainWindow


def sample_cheena_payload() -> dict:
    return {
        "metadata": {
            "name": "शिवराम पराजुली",
            "full_name": "शिवराम पराजुली",
            "father_name": "रामकृष्ण पराजुली",
            "mother_name": "सीता पराजुली",
            "gotra": "भारद्वाज",
            "gender": 0,
            "birth_date": "1990-01-15",
            "birth_time": "10:30:00",
            "birth_place": "काठमाडौं, नेपाल",
            "city": "काठमाडौं",
            "latitude": 27.7172,
            "longitude": 85.3240,
            "timezone": 5.75,
        },
        "panchang": {
            "samvatsara": {"nepali": "कालयुक्त"},
            "tithi": {"nepali": "तृतीया", "birth_nepali": "तृतीया", "paksha_nepali": "कृष्ण पक्ष"},
            "nakshatra": {"nepali": "मघा", "pada": 2},
            "yoga": {"nepali": "आयुष्मान", "birth_nepali": "आयुष्मान"},
            "karana": {"nepali": "विष्टि", "birth_nepali": "विष्टि"},
            "vara": {"nepali": "सोमवार"},
            "sunrise": {"time": "०६:५२"},
            "sunset": {"time": "१७:३१"},
        },
        "avakahada_chakra": {
            "name_akshara": "मी",
            "paya": "स्वर्ण",
            "varna": "ब्राह्मण",
            "vashya": "चतुष्पद",
            "tara": "जन्म",
            "yoni": "मूषक",
            "gana": "राक्षस",
            "nadi": "अन्त्य",
            "tatva": "अग्नि",
            "chandra_rashi": "सिंह",
            "rashi_lord": "सूर्य",
        },
        "lagna": {
            "sign_number": 12,
            "sign_name": "Pisces",
            "longitude_in_sign": 15.42,
        },
        "planets": [
            {"name": "Sun", "sign_number": 9, "longitude_in_sign": 1.25, "house": 10, "is_retrograde": False, "nakshatra": "मूला", "nakshatra_pada": 1},
            {"name": "Moon", "sign_number": 5, "longitude_in_sign": 4.50, "house": 6, "is_retrograde": False, "nakshatra": "मघा", "nakshatra_pada": 2},
            {"name": "Mars", "sign_number": 8, "longitude_in_sign": 22.10, "house": 9, "is_retrograde": False, "exaltation_state": "own", "nakshatra": "ज्येष्ठा", "nakshatra_pada": 2},
            {"name": "Mercury", "sign_number": 9, "longitude_in_sign": 18.00, "house": 10, "is_retrograde": False, "nakshatra": "पूर्वाषाढा", "nakshatra_pada": 2},
            {"name": "Jupiter", "sign_number": 3, "longitude_in_sign": 8.35, "house": 4, "is_retrograde": True, "exaltation_state": "exalted", "nakshatra": "पुनर्वसु", "nakshatra_pada": 1},
            {"name": "Venus", "sign_number": 10, "longitude_in_sign": 12.00, "house": 11, "is_retrograde": False, "nakshatra": "श्रवण", "nakshatra_pada": 1},
            {"name": "Saturn", "sign_number": 9, "longitude_in_sign": 24.15, "house": 10, "is_retrograde": False, "nakshatra": "उत्तराषाढा", "nakshatra_pada": 1},
            {"name": "Rahu", "sign_number": 11, "longitude_in_sign": 23.30, "house": 12, "is_retrograde": True, "nakshatra": "पूर्वाभाद्रपदा", "nakshatra_pada": 2},
            {"name": "Ketu", "sign_number": 5, "longitude_in_sign": 23.30, "house": 6, "is_retrograde": True, "nakshatra": "पूर्वाफाल्गुनी", "nakshatra_pada": 4},
        ],
        "vargas": {
            "D9": {
                "lagna": {"sign_number": 8},
                "planets": [
                    {"name": "Sun", "sign_number": 1},
                    {"name": "Moon", "sign_number": 6},
                    {"name": "Mars", "sign_number": 2},
                    {"name": "Mercury", "sign_number": 7},
                    {"name": "Jupiter", "sign_number": 4},
                    {"name": "Venus", "sign_number": 4},
                    {"name": "Saturn", "sign_number": 10},
                    {"name": "Rahu", "sign_number": 11},
                    {"name": "Ketu", "sign_number": 5},
                ],
            }
        },
        "dasha": [
            {"lord": "Ketu", "lord_nepali": "केतु", "total_years": 7, "start_bs": "२०४६-१०-०१", "end_bs": "२०५३-१०-०१"},
            {"lord": "Venus", "lord_nepali": "शुक्र", "total_years": 20, "start_bs": "२०५३-१०-०१", "end_bs": "२०७३-१०-०१"},
            {"lord": "Sun", "lord_nepali": "सूर्य", "total_years": 6, "start_bs": "२०७३-१०-०१", "end_bs": "२०७९-१०-०१"},
            {"lord": "Moon", "lord_nepali": "चन्द्र", "total_years": 10, "start_bs": "२०७९-१०-०१", "end_bs": "२०८९-१०-०१"},
        ],
        "ashtottari_dasha": [
            {"lord": "Sun", "lord_nepali": "सूर्य", "total_years": 6, "start_bs": "२०४६-१०-०१", "end_bs": "२०५२-१०-०१"},
            {"lord": "Moon", "lord_nepali": "चन्द्र", "total_years": 15, "start_bs": "२०५२-१०-०१", "end_bs": "२०६७-१०-०१"},
        ],
        "yogini_dasha": [
            {"name": "Dhanya", "nepali": "धान्या", "total_years": 3, "start_bs": "२०४६-१०-०१", "end_bs": "२०४९-१०-०१"},
            {"name": "Bhramari", "nepali": "भ्रामरी", "total_years": 4, "start_bs": "२०४९-१०-०१", "end_bs": "२०५३-१०-०१"},
        ],
        "ashtakavarga": {
            "samudaya": {
                "scores": [28, 30, 26, 32, 29, 31, 25, 27, 33, 24, 28, 24]
            }
        },
        "remedies": {
            "gemstones": {
                "life_stone": {"gemstone_ne": "पुखराज (Yellow Sapphire)"},
                "lucky_stone": {"gemstone_ne": "मूङ्गा (Red Coral)"},
                "punya_stone": {"gemstone_ne": "माणिक्य (Ruby)"},
            },
            "rudraksha": {
                "primary": {"name_ne": "पञ्चमुखी रुद्राक्ष (5 Mukhi Rudraksha)"}
            }
        }
    }


class TraditionalCheenaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv if hasattr(sys, 'argv') and sys.argv else ["test"])

    def test_helpers(self):
        self.assertEqual(to_ne_digits(12345), "१२३४५")
        self.assertEqual(to_ne_digits("2083-05-15"), "२०८३-०५-१५")
        self.assertIn("°", dms_format_ne(15.5))

    def test_chart_rendering_produces_base64_image(self):
        b64 = render_traditional_chart_base64(1, {1: ["सू", "चं"], 4: ["गु"]}, "Test Chart")
        self.assertTrue(b64.startswith("data:image/png;base64,"))
        self.assertGreater(len(b64), 500)

    def test_generate_cheena_html_contains_all_pages_and_sections(self):
        payload = sample_cheena_payload()
        html_out = generate_traditional_cheena_html(payload, "ne")

        # Page 1 checks
        self.assertIn("॥ श्री गणेशाय नमः ॥ श्रीमङ्गलमूर्तये नमः ॥", html_out)
        self.assertIn("आदित्याद्या ग्रहासर्वे सनक्षत्राः सराशयः", html_out)
        self.assertIn("शिवराम पराजुली", html_out)
        self.assertIn("अवकहडा चक्र", html_out)
        self.assertIn("जन्म लग्न कुण्डली (D1)", html_out)
        self.assertIn("नवमांश कुण्डली (D9)", html_out)

        # Page 2 checks
        self.assertIn("स्पष्ट ग्रह स्थिति तालिका", html_out)
        self.assertIn("चन्द्र कुण्डली", html_out)
        self.assertIn("समुदाय अष्टकवर्ग", html_out)

        # Page 3 checks
        self.assertIn("विंशोत्तरी महादशा तालिका", html_out)
        self.assertIn("अष्टोत्तरी महादशा तालिका", html_out)
        self.assertIn("योगिनी महादशा तालिका", html_out)

        # Page 4 checks
        self.assertIn("जीवनोपयोगी शुभ तत्त्वहरू", html_out)
        self.assertIn("पुखराज", html_out)
        self.assertIn("शास्त्रीय आशीर्वचन श्लोक", html_out)
        self.assertIn("॥ इति श्री परम्परागत नेपाली जन्मपत्रिका शुभा सम्पूर्णा ॥", html_out)

    def test_cheena_birth_date_bs_accuracy(self):
        # 1982-06-24 AD is 2039 Ashadh 10 BS
        p = sample_cheena_payload()
        p["metadata"]["birth_date"] = "1982-06-24"
        html_out = generate_traditional_cheena_html(p, "ne")
        self.assertIn("वि.सं. २०३९ अषाढ १० गते", html_out)
        self.assertNotIn("२०३९ जेठ १०", html_out)
        self.assertIn("<b>वि.सं. २०३९ अषाढ १० गते</b>", html_out)

    def test_cheena_office_location_kapilvastu(self):
        p = sample_cheena_payload()
        p["metadata"]["city"] = "Kapilvastu"
        html_out = generate_traditional_cheena_html(p, "ne")
        self.assertIn("कपिलवस्तु, नेपाल", html_out)
        self.assertIn("शिवराम ज्योतिष अनुसन्धान केन्द्र", html_out)

    def test_cheena_gender_label_accuracy(self):
        # Male chart (e.g. डोल प्रसाद पराजुली)
        p_male = sample_cheena_payload()
        p_male["metadata"]["name"] = "डोल प्रसाद पराजुली"
        p_male["metadata"]["gender"] = 0
        h_male = generate_traditional_cheena_html(p_male, "ne")
        self.assertIn("डोल प्रसाद पराजुली</b> (पुत्र)", h_male)
        self.assertNotIn("पुत्री", h_male)

        # Female chart
        p_fem = sample_cheena_payload()
        p_fem["metadata"]["name"] = "सीता पराजुली"
        p_fem["metadata"]["gender"] = 1
        h_fem = generate_traditional_cheena_html(p_fem, "ne")
        self.assertIn("सीता पराजुली</b> (पुत्री)", h_fem)


    def test_page_widget_instantiation_and_zoom(self):
        payload = sample_cheena_payload()
        page = TraditionalCheenaA4Page(payload, "ne")
        self.assertIsNotNone(page._viewer)
        self.assertIn("शिवराम पराजुली", page._current_html)

        # Test zoom
        page._zoom_in()
        self.assertGreater(page._zoom, 100)
        page._zoom_out()
        self.assertEqual(page._zoom, 100)

    def test_pdf_export_produces_real_valid_file(self):
        payload = sample_cheena_payload()
        html_out = generate_traditional_cheena_html(payload, "ne")

        with tempfile.TemporaryDirectory() as td:
            pdf_path = os.path.join(td, "traditional_cheena_test.pdf")
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(pdf_path)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Millimeter)

            doc = QTextDocument()
            doc.setHtml(html_out)
            doc.print_(printer)

            self.assertTrue(os.path.isfile(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 5000)

    def test_cheena_birth_date_bs_direct_metadata(self):
        p = sample_cheena_payload()
        p["metadata"]["birth_date_bs"] = "२०३९ अषाढ १०"
        html_out = generate_traditional_cheena_html(p, "ne")
        self.assertIn("वि.सं. २०३९ अषाढ १० गते", html_out)
        self.assertIn("कपिलवस्तु, नेपाल", html_out)

    def test_cheena_webengine_4page_pdf_export(self):
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtCore import QEventLoop, QMarginsF
        from PySide6.QtGui import QPageSize, QPageLayout
        import fitz

        payload = sample_cheena_payload()
        html_out = generate_traditional_cheena_html(payload, "ne")

        view = QWebEngineView()
        loop = QEventLoop()
        view.loadFinished.connect(lambda ok: loop.quit())
        view.setHtml(html_out)
        loop.exec()

        with tempfile.TemporaryDirectory() as td:
            pdf_file = os.path.join(td, "webengine_test.pdf")
            layout = QPageLayout(
                QPageSize(QPageSize.A4),
                QPageLayout.Portrait,
                QMarginsF(0, 0, 0, 0)
            )
            loop2 = QEventLoop()
            view.page().pdfPrintingFinished.connect(lambda p, ok: loop2.quit())
            view.page().printToPdf(pdf_file, layout)
            loop2.exec()

            self.assertTrue(os.path.isfile(pdf_file))
            doc = fitz.open(pdf_file)
            try:
                self.assertEqual(len(doc), 4)
                # Check charts present on page 1 and page 2
                self.assertGreaterEqual(len(doc[0].get_images()), 2)
                self.assertGreaterEqual(len(doc[1].get_images()), 2)
                # Check text on pages
                p0_text = doc[0].get_text()
                self.assertTrue("गणेशाय नमः" in p0_text or "जन्मपत्रिका" in p0_text)
                self.assertTrue("स्पष्ट ग्रह स्थिति" in doc[1].get_text() or "तालिका" in doc[1].get_text())
                self.assertTrue("महादशा" in doc[2].get_text() or "दशा" in doc[2].get_text())
                self.assertTrue("शिवराम ज्योतिष अनुसन्धान केन्द्र" in doc[3].get_text())
            finally:
                doc.close()


    def test_navigation_and_menu_wiring(self):
        self.assertEqual(normalize_action_id("traditional_cheena"), "traditional_cheena_a4")
        self.assertEqual(normalize_action_id("cheena"), "traditional_cheena_a4")
        self.assertEqual(normalize_action_id("cheena_a4"), "traditional_cheena_a4")

        charts_category = next(c for c in NAV_STRUCTURE if c["id"] == "charts")
        chart_ids = [item["id"] for item in charts_category["items"]]
        self.assertIn("traditional_cheena_a4", chart_ids)

        owner = type("PageOwner", (), {"_chart_data": sample_cheena_payload(), "_language": "ne"})()
        page = JyotishMainWindow._build_page(owner, "traditional_cheena_a4")
        self.assertIsInstance(page, TraditionalCheenaA4Page)


if __name__ == "__main__":
    unittest.main()

