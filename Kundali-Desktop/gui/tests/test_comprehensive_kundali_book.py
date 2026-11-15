# -*- coding: utf-8 -*-
"""
gui/tests/test_comprehensive_kundali_book.py

Unit test for Comprehensive 50+ Page Kundali Book engine and desktop widget.
"""
import os, sys, unittest
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from api.endpoints import perform_calculations
from calculator.comprehensive_book_engine import build_comprehensive_kundali_book
from gui.widgets.comprehensive_kundali_book import ComprehensiveKundaliBookPage


class ComprehensiveKundaliBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_comprehensive_book_builds_all_chapters_in_nepali(self):
        result = perform_calculations(
            name="Shivram Parajuli",
            birth_date="1982-06-24",
            birth_time="11:45:00",
            latitude=27.5333,
            longitude=83.05,
            timezone=5.5,
            ayanamsha_type="lahiri",
            node_type="mean"
        )
        self.assertIn("comprehensive_book", result)
        book = result["comprehensive_book"]
        html = book["html"]
        
        # Verify key headings & chapters
        self.assertIn("बृहत् जीवन कुण्डली", html)
        self.assertIn("अध्याय १: पञ्चाङ्ग, अवकहडा चक्र तथा अनुकूल/घातक बिन्दु", html)
        self.assertIn("अध्याय २: जन्म लग्न कुण्डली, नवमांश, चन्द्र कुण्डली तथा ग्रह स्थिति", html)
        self.assertIn("अध्याय ३: जन्म लग्न फल, चन्द्र राशि फल तथा नक्षत्र फल", html)
        self.assertIn("अध्याय ४: सम्पूर्ण १२ भाव फल विस्तृत शास्त्रीय विवेचन", html)
        self.assertIn("अध्याय ५: नवग्रह विस्तृत शास्त्रीय फल विवेचन", html)
        self.assertIn("अध्याय ६: बृहत् शास्त्रीय योग विश्लेषण", html)
        self.assertIn("अध्याय ७: शिक्षा, विद्या तथा बौद्धिक क्षमता विवेचन", html)
        self.assertIn("अध्याय ८: युवावस्था, पेशा, करियर तथा व्यवसाय विवेचन", html)
        self.assertIn("अध्याय ९: धन, वैभव, सम्पत्ति, घर-जग्गा तथा सवारी सुख", html)
        self.assertIn("अध्याय १०: प्रेम, विवाह, जीवनसाथी, दिशा तथा दाम्पत्य सुख", html)
        self.assertIn("अध्याय ११: सन्तान, सन्तति सुख तथा वंशवृद्धि", html)
        self.assertIn("अध्याय १२: स्वास्थ्य, रोग, आयु तथा आरोग्य विवेचन", html)
        self.assertIn("अध्याय १३: विदेश यात्रा, स्थान परिवर्तन तथा भाग्योदय", html)
        self.assertIn("अध्याय १४: मङ्गल दोष, कालसर्प दोष तथा पितृ दोष विवेचन", html)
        self.assertIn("अध्याय १५: शनि साढेसाती तथा अढैया आजीवन समय तालिका", html)
        self.assertIn("अध्याय १६: सम्पूर्ण विंशोत्तरी महादशा तथा अन्तर्दशा कालक्रम", html)
        self.assertIn("अध्याय १७: योगिनी दशा आजीवन चक्र तथा फल", html)
        self.assertIn("अध्याय १८: ताजिक वार्षिक वर्षफल", html)
        self.assertIn("अध्याय १९: जैमिनी ज्योतिष पद्धति", html)
        self.assertIn("अध्याय २०: लालकिताब कुण्डली, ग्रह स्थिति तथा अचूक टोटका/उपाय", html)
        self.assertIn("अध्याय २१: षोडशवर्ग कुण्डली चक्रहरू", html)
        self.assertIn("अध्याय २२: के.पी. (KP) पद्धति, भाव कस्प तथा सब-लर्ड", html)
        self.assertIn("अध्याय २३: षड्बल, भावबल तथा समुदाय अष्टकवर्ग (SAV)", html)
        self.assertIn("अध्याय २४: सम्पूर्ण शास्त्रीय शान्ति उपाय, रत्न, रुद्राक्ष, मन्त्र तथा दान", html)

        # Verify charts are embedded as base64 images
        self.assertIn("data:image/png;base64,", html)

        # Verify Bikram Sambat date
        self.assertIn("वि.सं. २०३९", html)

    def test_gui_widget_renders_and_exports(self):
        result = perform_calculations(
            name="Shivram Parajuli",
            birth_date="1982-06-24",
            birth_time="11:45:00",
            latitude=27.5333,
            longitude=83.05,
            timezone=5.5,
            ayanamsha_type="lahiri",
            node_type="mean"
        )
        page = ComprehensiveKundaliBookPage(result, language="ne")
        self.assertIsNotNone(page._viewer.toHtml())
        self.assertIn("बृहत् जीवन कुण्डली", page._viewer.toPlainText())
        page.deleteLater()


if __name__ == "__main__":
    unittest.main()
