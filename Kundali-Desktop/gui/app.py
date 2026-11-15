# -*- coding: utf-8 -*-

"""

gui/app.py

Main QMainWindow — Shivram Jyotish Desktop Application

Mirrors the InstitutionalUI.jsx layout:

  - Left sidebar with collapsible category menus

  - Top birth ribbon (after calculation)

  - Right content stacked widget

  - Bottom status bar

"""

from __future__ import annotations

import sys, os
from datetime import date

from typing import Optional, Any, Dict

from PySide6.QtWidgets import (

    QMainWindow, QWidget, QDialog, QHBoxLayout, QVBoxLayout, QSplitter,

    QLabel, QPushButton, QStackedWidget, QScrollArea, QFrame,

    QSizePolicy, QStatusBar, QApplication, QMessageBox,

    QProgressBar, QInputDialog, QMenuBar, QMenu, QGraphicsOpacityEffect

)

from PySide6.QtCore import (
    Qt, Signal, QThread, QObject, QSize, QTimer,
    QPropertyAnimation, QEasingCurve, Property, QParallelAnimationGroup
)

from PySide6.QtGui import QFont, QIcon, QColor, QPalette, QKeySequence, QShortcut, QAction

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if _ROOT not in sys.path:

    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_PRIMARY, BG_SECONDARY, BG_TERTIARY,

                        BORDER_COLOR, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,

                        COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ERROR, SIDEBAR_BG,

                        SIDEBAR_BORDER, SIDEBAR_ITEM_HOVER, SIDEBAR_ITEM_ACTIVE)

from gui.widgets.chart_input import ChartInputWidget
from gui.widgets.solar_system import SolarSystemWidget
from gui.utils.bs_calendar import BS_MONTHS_EN, BS_MONTHS_NE, gregorian_to_bs, to_nepali_digits


RIBBON_UNAVAILABLE = "—"
RIBBON_FIELD_KEYS = (
    "name", "birth_date_bs", "birth_time", "birth_place",
    "full_age", "gender", "mahadasha", "antardasha",
)


def _ribbon_text(value: Any) -> str:
    """Return a display-safe ribbon value without retaining stale data."""
    if value is None or value == "" or isinstance(value, (dict, list, tuple, set)):
        return RIBBON_UNAVAILABLE
    return str(value)


def _ribbon_birth_date(value: Any, language: str) -> str:
    """Match BirthRibbon.jsx: day Month year BS (English), year Month day (Nepali)."""
    text = _ribbon_text(value)
    if text == RIBBON_UNAVAILABLE:
        return text
    try:
        birth_date = date.fromisoformat(text[:10])
        bs = gregorian_to_bs(birth_date.year, birth_date.month, birth_date.day)
    except (TypeError, ValueError):
        bs = None
    if not bs:
        return RIBBON_UNAVAILABLE
    month = bs.get("month")
    if not isinstance(month, int) or not 1 <= month <= 12:
        return RIBBON_UNAVAILABLE
    if language == "ne":
        return f"{to_nepali_digits(bs['year'])} {BS_MONTHS_NE[month - 1]} {to_nepali_digits(bs['day'])}"
    return f"{bs['day']} {BS_MONTHS_EN[month - 1]} {bs['year']} BS"


def _ribbon_full_age(value: Any, language: str, today: Optional[date] = None) -> str:
    """Match the Web ribbon's compact age formatting and calendar arithmetic."""
    text = _ribbon_text(value)
    if text == RIBBON_UNAVAILABLE:
        return text
    try:
        born = date.fromisoformat(text[:10])
    except (TypeError, ValueError):
        return RIBBON_UNAVAILABLE
    today = today or date.today()
    years, months, days = today.year - born.year, today.month - born.month, today.day - born.day
    if days < 0:
        previous_month = today.replace(day=1).fromordinal(today.replace(day=1).toordinal() - 1)
        days += previous_month.day
        months -= 1
    if months < 0:
        months += 12
        years -= 1
    if language == "ne":
        return f"{to_nepali_digits(years)} वर्ष {to_nepali_digits(months)} महिना {to_nepali_digits(days)} दिन"
    return f"{years}y {months}m {days}d"


def _ribbon_dasha_value(period: Any, language: str) -> str:
    """Format an active Vimshottari period as the Web ribbon does."""
    if not isinstance(period, dict):
        return RIBBON_UNAVAILABLE
    lord = period.get("lord_nepali" if language == "ne" else "lord")
    start = period.get("start_bs")
    end = period.get("end_bs")
    if not lord or not start or not end:
        return RIBBON_UNAVAILABLE
    value = f"{lord} ({start} - {end})"
    return to_nepali_digits(value) if language == "ne" else value


def build_birth_ribbon_model(data: Optional[dict], language: str = "en", gender: int = 0,
                             today: Optional[date] = None) -> list[dict]:
    """Normalize a calculation payload into the Web BirthRibbon field contract."""
    is_ne = language == "ne"
    metadata = data.get("metadata") if isinstance(data, dict) and isinstance(data.get("metadata"), dict) else {}
    dasha = data.get("dasha") if isinstance(data, dict) and isinstance(data.get("dasha"), list) else []
    active_md = next((item for item in dasha if isinstance(item, dict) and item.get("is_active")), None)
    children = active_md.get("children") if isinstance(active_md, dict) and isinstance(active_md.get("children"), list) else []
    active_ad = next((item for item in children if isinstance(item, dict) and item.get("is_active")), None)
    gender_value = metadata["gender"] if "gender" in metadata else gender
    female = gender_value == 1
    labels = (
        ("Name", "नाम"),
        ("Birth Date (BS)", "जन्म मिति (वि.सं.)"),
        ("Birth Time", "जन्म समय"),
        ("Birth Place", "जन्म स्थान"),
        ("Full Age", "पूर्ण उमेर"),
        ("Gender", "लिङ्ग"),
        ("Active Mahadasha", "सक्रिय महादशा"),
        ("Active Antardasha", "सक्रिय अन्तर्दशा"),
    )
    values = (
        _ribbon_text(metadata.get("name")),
        _ribbon_birth_date(metadata.get("birth_date"), language),
        _ribbon_text(metadata.get("birth_time")),
        _ribbon_text(metadata.get("city")),
        _ribbon_full_age(metadata.get("birth_date"), language, today),
        "स्त्री" if is_ne and female else "पुरुष" if is_ne else "Female" if female else "Male",
        _ribbon_dasha_value(active_md, language),
        _ribbon_dasha_value(active_ad, language),
    )
    return [
        {"key": key, "label": label[1] if is_ne else label[0], "value": value,
         "badge": key in ("mahadasha", "antardasha")}
        for key, label, value in zip(RIBBON_FIELD_KEYS, labels, values)
    ]

# ── Lazy widget imports (loaded only when that view is opened) ──────────────

def _lazy_import(module_path: str, class_name: str):

    """Import a widget class lazily to avoid slow startup."""

    import importlib

    try:

        mod = importlib.import_module(module_path)

        return getattr(mod, class_name)

    except Exception as e:

        return None

# ——— Sidebar menu structure (mirrors InstitutionalUI.jsx NAV_ITEMS) ———————————

NAV_STRUCTURE = [

    {

        "id": "home",

        "icon": "🏠",

        "ne": "मुख्य ड्यासबोर्ड",

        "en": "Dashboard & Home",

        "items": [

            {"id": "home",              "ne": "गृह पृष्ठ (Overview)",   "en": "Home Overview"},

            {"id": "custom_dashboard",  "ne": "कस्टमाइज ड्यासबोर्ड",    "en": "Custom Dashboard"},

        ],

    },

    {

        "id": "charts",

        "icon": "🪐",

        "ne": "कुण्डली दृश्य",

        "en": "Kundali Charts",

        "items": [

            {"id": "kundali_nirman",     "ne": "कुण्डली निर्माण",        "en": "Traditional Janmapatrika"},
            {"id": "traditional_cheena_a4", "ne": "नेपाली चिना (A4 PDF)", "en": "Nepali Cheena (A4 PDF)"},

            {"id": "chart_rashi",        "ne": "राशि कुण्डली (D1)",      "en": "Rashi Chart (D1)"},

            {"id": "chart_navamsha",     "ne": "नवांश कुण्डली (D9)",     "en": "Navamsha (D9)"},

            {"id": "chart_dashamsha",    "ne": "दशमांश कुण्डली (D10)",   "en": "Dashamsha (D10)"},

            {"id": "chart_vargas",       "ne": "सबै वर्ग कुण्डलीहरू",    "en": "All Divisional Charts"},

            {"id": "chart_sudarshan",    "ne": "सुदर्शन चक्र",           "en": "Sudarshan Chakra"},

            {"id": "chart_bhava_chalit", "ne": "भाव चलित",               "en": "Bhava Chalit"},
            {"id": "chart_comparison",   "ne": "कुण्डली तुलना",            "en": "Chart Comparison"},

        ],

    },

    {

        "id": "dasha",

        "icon": "⏳",

        "ne": "दशा तथा फलादेश",

        "en": "Dasha & Predictions",

        "items": [

            {"id": "report_life_conclusion",       "ne": "निष्कर्ष (पूर्ण फलित)",      "en": "Life Conclusion (Phalita)"},
            {"id": "report_dasha_gochar_timeline", "ne": "दशा-गोचर मासिक चार्ट",       "en": "Dasha-Gochar Chart"},
            {"id": "report_dasha_transit_timeline","ne": "दशा तथा गोचर समयरेखा",     "en": "Dasha & Transit Timeline"},
            {"id": "report_complete_dasha",        "ne": "सम्पूर्ण दशा र रिपोर्ट",     "en": "Complete Dasha & Report"},
            {"id": "report_sadesati_adhaiya",      "ne": "साढेसाती / अढैया",          "en": "Sade Sati & Adhaiya"},
            {"id": "report_daily_horoscope",       "ne": "दैनिक राशिफल",             "en": "Daily Horoscope"},
            {"id": "dasha_visual_calendar",        "ne": "दशा भिजुअल क्यालेन्डर",     "en": "Dasha Visual Calendar"},
            {"id": "gochar_phal_report",           "ne": "गोचर फल विवरण",            "en": "Gochar Phala Report"},
            {"id": "report_yearly_forecast",       "ne": "वार्षिक वर्षफल",           "en": "Yearly Forecast"},
            {"id": "report_planetary_ingress",     "ne": "ग्रह गोचर क्यालेन्डर",      "en": "Planetary Transit Calendar"},

        ],

    },

    {

        "id": "calendars",

        "icon": "📅",

        "ne": "क्यालेन्डर तथा पर्वहरू",

        "en": "Calendars & Festivals",

        "items": [

            {"id": "nepali_festival_calendar", "ne": "नेपाली पर्व क्यालेन्डर", "en": "Nepali Festival Calendar"},
            {"id": "nakshatra_calendar",      "ne": "नक्षत्र पञ्चाङ्ग क्यालेन्डर", "en": "Nakshatra Panchang Calendar"},
            {"id": "muhurta_certificate",     "ne": "मुहूर्त प्रमाणपत्र",        "en": "Muhurta Certificate"},

        ],

    },

    {

        "id": "reports",

        "icon": "📊",

        "ne": "विवरण तथा विश्लेषण",

        "en": "Reports & Analysis",

        "items": [

            {"id": "report_panchang",        "ne": "विस्तृत पञ्चाङ्ग",              "en": "Detailed Panchang"},
            {"id": "report_birth_panchang",  "ne": "जन्म पञ्चाङ्ग तथा अवकहडा चक्र","en": "Birth Panchang & Avakahada"},
            {"id": "report_planets",         "ne": "ग्रह स्थिति विवरण",             "en": "Planetary Positions"},
            {"id": "report_avasthas",        "ne": "ग्रह अवस्था विश्लेषण",          "en": "Planetary Avasthas"},
            {"id": "report_yogas",           "ne": "योग फल",                       "en": "Yoga Report"},
            {"id": "report_kaal_sarp_dosha", "ne": "कालसर्प दोष",                  "en": "Kaal Sarp Dosha"},
            {"id": "report_shadbala",        "ne": "षड्बल",                        "en": "Shadbala"},
            {"id": "report_planet_strength", "ne": "ग्रह शक्ति प्रोफाइल",           "en": "Planet Strength Profile"},
            {"id": "report_ashtakavarga",    "ne": "अष्टकवर्ग",                    "en": "Ashtakavarga"},
            {"id": "report_visual_graphs",   "ne": "भिजुअल ग्राफहरू",              "en": "Visual Graphs"},
            {"id": "vimshopaka_bala",       "ne": "विंशोपक बल (षोडशवर्ग)",        "en": "Vimshopaka Bala"},
            {"id": "ayurdaya",              "ne": "आयुर्दाय (जीवनकाल)",           "en": "Ayurdaya (Longevity)"},
            {"id": "report_remedies",        "ne": "💎 रत्न तथा वैदिक उपचार",       "en": "Gemstones & Remedies"},
            {"id": "report_comprehensive_book", "ne": "📜 बृहत् जीवन कुण्डली (५०+ पृष्ठ)", "en": "Comprehensive Kundali Book (50+ Pages)"},
        ],
    },

    {

        "id": "analysis",

        "icon": "🔬",

        "ne": "विश्लेषण",

        "en": "Life Analysis",

        "items": [

            {"id": "report_marriage_analysis",  "ne": "विवाह/कलत्र विचार", "en": "Marriage Analysis"},

            {"id": "report_career_analysis",    "ne": "व्यवसाय/जीविका निर्णय", "en": "Career Analysis"},

            {"id": "report_health_analysis",    "ne": "स्वास्थ्य विश्लेषण","en": "Health Analysis"},

            {"id": "report_child_analysis",     "ne": "सन्तान विश्लेषण",   "en": "Child Analysis"},

            {"id": "report_gandanta_shanti",    "ne": "गण्डान्त तथा अनिष्ट शान्ति", "en": "Gandanta & Shanti"},

            {"id": "report_education_analysis", "ne": "शिक्षा विश्लेषण",   "en": "Education Analysis"},

            {"id": "report_finance_wealth_analysis","ne":"आर्थिक विश्लेषण","en": "Finance & Wealth"},

            {"id": "report_foreign_travel_analysis","ne": "विदेश यात्रा विश्लेषण","en": "Foreign Travel Analysis"},

            {"id": "report_business_analysis","ne": "व्यापार/व्यवसाय विश्लेषण","en": "Business Analysis"},

            {"id": "report_property_vehicle_analysis","ne": "सम्पत्ति तथा वाहन विश्लेषण","en": "Property & Vehicle Analysis"},

            {"id": "report_personality_analysis","ne": "व्यक्तित्व विश्लेषण","en": "Personality Analysis"},

        ],

    },

    {

        "id": "advanced",

        "icon": "🌟",

        "ne": "उन्नत सुविधाहरू",

        "en": "Advanced Features",

        "items": [

            {"id": "marriage_matching",        "ne": "विवाह मिलान",           "en": "Marriage Matching"},
            {"id": "prashna_chart",            "ne": "प्रश्न कुण्डली",         "en": "Prashna Chart"},
            {"id": "muhurta_finder",           "ne": "मुहूर्त अन्वेषण",       "en": "Muhurta Finder"},
            {"id": "report_lal_kitab",         "ne": "लाल किताब विश्लेषण",   "en": "Lal Kitab Analysis"},
            {"id": "report_jaimini_analysis",  "ne": "जैमिनी विश्लेषण",      "en": "Jaimini Analysis"},
            {"id": "report_kp_system",         "ne": "के.पी. पद्धति",         "en": "KP System"},
            {"id": "report_transit_analysis",  "ne": "गोचर विश्लेषण",         "en": "Transit Analysis"},
            {"id": "report_sarvatobhadra",     "ne": "सर्वतोभद्र चक्र",       "en": "Sarvatobhadra Chakra"},

            {"id": "report_ayanamsha_comparator", "ne": "अयनांश तुलना", "en": "Ayanamsha Comparator"},
            {"id": "graha_yuddha",          "ne": "ग्रह युद्ध",                    "en": "Graha Yuddha (Planetary War)"},
            {"id": "planetary_hora",        "ne": "ग्रह होरा",                     "en": "Planetary Hora"},

        ],

    },

]

# Current native menu IDs are canonical. These aliases retain compatibility with
# action names used by the previous web shell and saved/custom workflows.
_CANONICAL_ACTION_IDS = frozenset(
    item["id"]
    for category in NAV_STRUCTURE
    for item in category["items"]
) | frozenset({
    "home",
    "saved_charts",
    "settings",
    "classical_bphs",
    "classical_saravali",
    "classical_phaladeepika",
    "classical_jataka",
    "chart_special_chakras",
    "chart_hora_lagna",
    "report_birth_panchang",
    "report_avakahada_chakra",
    # ── New tool pages ──
    "planetary_hora",
    "chart_comparison",
    "graha_yuddha",
    "dasha_visual_calendar",
    "nakshatra_calendar",
    "muhurta_certificate",
    "vimshopaka_bala",
    "ayurdaya",
    "gochar_phal_report",
})

_ACTION_ALIASES = {
    "dashboard": "home",
    "home_overview": "home",
    "home_welcome": "home",
    "home_dashboard": "custom_dashboard",
    "rashi": "chart_rashi",
    "rashi_chart": "chart_rashi",
    "kundali_rashi": "chart_rashi",
    "navamsha": "chart_navamsha",
    "navamsha_chart": "chart_navamsha",
    "kundali_navamsha": "chart_navamsha",
    "dashamsha": "chart_dashamsha",
    "dashamsha_chart": "chart_dashamsha",
    "kundali_dashamsha": "chart_dashamsha",
    "divisional_charts": "chart_vargas",
    "kundali_varga": "chart_vargas",
    "all_vargas": "chart_vargas",
    "sudarshan": "chart_sudarshan",
    "special_chakras": "chart_special_chakras",
    "kundali_special": "chart_special_chakras",
    "bhava_chalit": "chart_bhava_chalit",
    "kundali_bhava": "chart_bhava_chalit",
    "hora_lagna": "chart_hora_lagna",
    "kundali_hora": "chart_hora_lagna",
    "planetary_positions": "report_planets",
    "reports_planets": "report_planets",
    "panchang": "report_panchang",
    "reports_panchang": "report_panchang",
    "birth_panchang": "report_birth_panchang",
    "avakahada_chakra": "report_avakahada_chakra",
    "yoga_report": "report_yogas",
    "reports_yogas": "report_yogas",
    "kaal_sarp_dosha": "report_kaal_sarp_dosha",
    "reports_kaal_sarp_dosha": "report_kaal_sarp_dosha",
    "ksd": "report_kaal_sarp_dosha",
    "shadbala": "report_shadbala",
    "reports_shadbala": "report_shadbala",
    "calc_detailed_shad_bala": "report_shadbala",
    "calc_graha_bhava_bala": "report_shadbala",
    "comprehensive_book": "report_comprehensive_book",
    "brihat_kundali": "report_comprehensive_book",
    "kundali_book": "report_comprehensive_book",
    "mega_report": "report_comprehensive_book",
    "report_kundali_book": "report_comprehensive_book",
    "planet_strength": "report_planet_strength",
    "planet_strength_profile": "report_planet_strength",
    "graha_bala": "report_planet_strength",
    "graha_strength": "report_planet_strength",
    "ashtakavarga": "report_ashtakavarga",
    "reports_ashtakavarga": "report_ashtakavarga",
    "calc_ashtakavarga_bhinnashtaka_1": "report_ashtakavarga",
    "calc_ashtakavarga_bhinnashtaka_2": "report_ashtakavarga",
    "calc_ashtakavarga_reductions": "report_ashtakavarga",
    "calc_ashtakavarga_summary": "report_ashtakavarga",
    "calc_ashtakavarga_sarvashtaka_chancha": "report_ashtakavarga",
    "calc_divisional_charts_ashtakavarga": "report_ashtakavarga",
    "vimshottari_dasha": "report_complete_dasha",
    "dasha_vimshottari": "report_complete_dasha",
    "report_vimshottari": "report_complete_dasha",
    "dasha_gochar": "report_dasha_gochar_timeline",
    "dasha_gochar_timeline": "report_dasha_gochar_timeline",
    "dasha_transit": "report_dasha_transit_timeline",
    "dasha_transit_timeline": "report_dasha_transit_timeline",
    "dasha_results": "report_dasha_phal",
    "dasha_complete": "report_complete_dasha",
    "dasha_yogini": "report_yogini_dasha",
    "yogini": "report_yogini_dasha",
    "yogini_dasha": "report_yogini_dasha",
    "dasha_conclusion": "report_life_conclusion",
    "conclusion": "report_life_conclusion",
    "phalita": "report_life_conclusion",
    "life_conclusion": "report_life_conclusion",
    "report_phalita": "report_life_conclusion",
    "dasha_sadesati": "report_sadesati_adhaiya",
    "dasha_daily": "report_daily_horoscope",
    "dasha_yearly": "report_yearly_forecast",
    "reports_all": "report_all_in_one",
    "jaimini": "report_jaimini_analysis",
    "jaimini_analysis": "report_jaimini_analysis",
    "kp": "report_kp_system",
    "kp_system": "report_kp_system",
    "calc_krishnamurti_chart": "report_kp_system",
    "calc_krishnamurti_significators": "report_kp_system",
    "lal_kitab": "report_lal_kitab",
    "lalkitab": "report_lal_kitab",
    "ingress": "report_planetary_ingress",
    "transit_calendar": "report_planetary_ingress",
    "planetary_ingress": "report_planetary_ingress",
    "avasthas": "report_avasthas",
    "graha_avasthas": "report_avasthas",
    "analysis_marriage": "report_marriage_analysis",
    "analysis_children": "report_child_analysis",
    "analysis_health": "report_health_analysis",
    "analysis_education": "report_education_analysis",
    "analysis_career": "report_career_analysis",
    "analysis_wealth": "report_finance_wealth_analysis",
    "analysis_gandanta": "report_gandanta_shanti",
    "gandanta_shanti": "report_gandanta_shanti",
    "gandanta": "report_gandanta_shanti",
    "arishta_shanti": "report_gandanta_shanti",
    "shanti": "report_gandanta_shanti",
    "remedies": "report_remedies",
    "report_remedy": "report_remedies",
    "gemstones": "report_remedies",
    "rudraksha": "report_remedies",
    "upaya": "report_remedies",
    "traditional_cheena": "traditional_cheena_a4",
    "cheena": "traditional_cheena_a4",
    "cheena_a4": "traditional_cheena_a4",
    "nepali_cheena": "traditional_cheena_a4",
    "saved": "saved_charts",
    "saved_charts_manager": "saved_charts",
    "preferences": "settings",
    "settings_preferences": "settings",
}


def normalize_action_id(action_id: Any) -> Optional[str]:
    """Return a canonical native action ID, or None for unsupported input."""
    if not isinstance(action_id, str):
        return None
    candidate = action_id.strip().lower()
    if not candidate:
        return None
    if candidate in _CANONICAL_ACTION_IDS:
        return candidate
    return _ACTION_ALIASES.get(candidate)


# ── Background calculation thread ────────────────────────────────────────────

class CalcWorker(QObject):

    finished = Signal(dict)

    error    = Signal(str)

    def __init__(self, params: dict):

        super().__init__()

        self._params = params

    def run(self):

        try:

            from gui.backend_bridge import calculate_chart

            result = calculate_chart(**{k: v for k, v in self._params.items() if k != "gender"})

            result.setdefault("metadata", {})["gender"] = self._params.get("gender", 0)

            self.finished.emit(result)

        except ValueError as e:

            self.error.emit(f"Validation: {e}")

        except RuntimeError as e:

            self.error.emit(str(e))

        except Exception as e:

            self.error.emit(f"Unexpected error: {e}")

# ── Animated Stacked Widget for silky-smooth page transitions ─────────────────

class AnimatedStackedWidget(QStackedWidget):
    """
    QStackedWidget with silky-smooth cross-fade transition between pages.
    Gives a cohesive, fluid animation experience across the entire desktop app.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._anim: Optional[QPropertyAnimation] = None
        self._effect: Optional[QGraphicsOpacityEffect] = None

    def setCurrentWidget(self, widget: QWidget, animate: bool = True) -> None:
        """Switch to target widget with smooth fade transition."""
        if widget is None or widget == self.currentWidget():
            return

        if self.indexOf(widget) == -1:
            self.addWidget(widget)

        if not animate:
            super().setCurrentWidget(widget)
            return

        # Cancel active animation safely
        if self._anim and self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()

        if self._effect:
            try:
                target = self._effect.parent()
                if target:
                    target.setGraphicsEffect(None)
            except Exception:
                pass
            self._effect = None

        # Switch page
        super().setCurrentWidget(widget)

        # Apply smooth opacity fade-in
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0.0)
        widget.setGraphicsEffect(effect)
        self._effect = effect

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():
            if widget.graphicsEffect() == effect:
                widget.setGraphicsEffect(None)
            self._effect = None
            self._anim = None

        anim.finished.connect(_cleanup)
        self._anim = anim
        anim.start()


# ── Sidebar category header with smooth accordion animation ──────────────────

class SidebarCategoryWidget(QWidget):

    toggled = Signal(str, bool)   # (category_id, expanded)

    def __init__(self, cat: dict, language: str = "ne", parent=None):

        super().__init__(parent)

        self._id = cat["id"]

        self._is_ne = language == "ne"

        self._expanded = True

        self._anim: Optional[QPropertyAnimation] = None

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        self._cat_name = cat["ne"] if self._is_ne else cat["en"]
        self._cat_icon = cat["icon"]

        # Header button with disclosure indicator
        self._header = QPushButton(
            f"  {self._cat_icon}  {self._cat_name}  ▾"
        )

        self._header.setStyleSheet(f"""

            QPushButton {{

                background: {BG_TERTIARY};

                border: none;

                border-bottom: 1px solid {SIDEBAR_BORDER};

                color: {COLOR_GOLD};

                text-align: left;

                font-size: 11px;

                font-weight: 700;

                letter-spacing: 0.5px;

                padding: 8px 12px;

            }}

            QPushButton:hover {{

                background: {SIDEBAR_ITEM_HOVER};

            }}

        """)

        self._header.setCursor(Qt.PointingHandCursor)

        self._header.clicked.connect(self._toggle)

        layout.addWidget(self._header)

        # Items container

        self._items_widget = QWidget()

        self._items_layout = QVBoxLayout(self._items_widget)

        self._items_layout.setContentsMargins(0, 2, 0, 2)

        self._items_layout.setSpacing(1)

        self._items_widget.setStyleSheet("background: transparent;")

        layout.addWidget(self._items_widget)

        self._item_buttons: list[QPushButton] = []

    def add_item(self, item: dict, callback) -> QPushButton:

        btn = QPushButton(item["ne"] if self._is_ne else item["en"])

        btn.setObjectName("SidebarItem")

        btn.setProperty("view_id", item["id"])

        btn.setCursor(Qt.PointingHandCursor)

        btn.setMinimumHeight(30)

        btn.clicked.connect(lambda: callback(item["id"]))

        self._items_layout.addWidget(btn)

        self._item_buttons.append(btn)

        return btn

    def _toggle(self):
        self._expanded = not self._expanded
        indicator = "▾" if self._expanded else "▸"
        self._header.setText(f"  {self._cat_icon}  {self._cat_name}  {indicator}")

        if self._anim and self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()

        target_h = max(32, len(self._item_buttons) * 32 + 8) if self._expanded else 0
        current_h = self._items_widget.height() if self._items_widget.isVisible() else 0

        self._items_widget.setVisible(True)

        anim = QPropertyAnimation(self._items_widget, b"maximumHeight", self)
        anim.setDuration(220)
        anim.setStartValue(current_h)
        anim.setEndValue(target_h)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _on_done():
            if not self._expanded:
                self._items_widget.setVisible(False)
            else:
                self._items_widget.setMaximumHeight(16777215)
            self._anim = None

        anim.finished.connect(_on_done)
        self._anim = anim
        anim.start()

        self.toggled.emit(self._id, self._expanded)

    def highlight_item(self, view_id: Optional[str]):

        for btn in self._item_buttons:

            active = btn.property("view_id") == view_id

            btn.setProperty("active", "true" if active else "false")

            btn.style().unpolish(btn)

            btn.style().polish(btn)

class JyotishMainWindow(QMainWindow):

    #: Cross-thread notification from UpdateChecker.  Emitting a Qt signal is
    #: thread-safe; the queued connection delivers the dialog on the GUI thread.
    _update_available = Signal(str, str)

    def __init__(self, language: str = "ne", ayanamsha: str = "LAHIRI"):

        super().__init__()

        self._update_available.connect(
            self._show_update_notification, Qt.QueuedConnection
        )

        self._language = language

        self._is_ne = language == "ne"

        self._ayanamsha = ayanamsha

        self._chart_data: Optional[dict] = None

        self._last_calc_params: Optional[dict] = None

        self._preview_chart_data: Optional[dict] = None

        self._editing_record_id: Optional[int] = None

        self._active_record_id: Optional[int] = None

        self._active_view: str = "home"

        self._sidebar_cats: list[SidebarCategoryWidget] = []

        self._sidebar_buttons: dict[str, QPushButton] = {}

        self._calc_thread: Optional[QThread] = None

        self._direct_calc_params: Optional[dict] = None

        self._page_cache: dict[str, QWidget] = {}

        self._unavailable_page: Optional[QWidget] = None

        # Ensure theme is applied (fallback in case desktop_main didn't apply it)
        try:
            from PySide6.QtCore import QSettings
            from gui.theme import apply_theme
            settings = QSettings("ShivramJyotish", "Desktop")
            theme_mode = settings.value("theme_mode", "classic")
            apply_theme(QApplication.instance(), theme_mode)
        except Exception:
            pass

        self._setup_window()

        self._setup_shortcuts()

        self._build_ui()

    def _setup_window(self):

        self.setWindowTitle("Shivram Jyotish Software")

        self.setMinimumSize(1024, 680)

        # The 1400x900 default is taller/wider than the work area of common
        # laptop panels (a 1366x768 screen only offers 1366x720 once the taskbar
        # is removed).  Qt honours the requested *client* size, so the native
        # frame then hangs below the work area and its bottom strip — the
        # Nepali festival calendar action bar, the status bar — becomes
        # unreachable behind the taskbar.  Start work-area aware and finish the
        # fit in showEvent(), where the real frame overhead is known.
        self._work_area_fitted = False

        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen is not None else None
        self.resize(
            min(1400, avail.width()) if avail is not None else 1400,
            min(900, avail.height()) if avail is not None else 900,
        )

        icon_dirs = [
            os.path.join(_ROOT, "public"),
            os.path.join(_ROOT, "frontend", "public"),
        ]

        icon_path = next(
            (
                os.path.join(d, name)
                for d in icon_dirs
                for name in ("favicon.ico", "favicon.svg")
                if os.path.exists(os.path.join(d, name))
            ),
            None,
        )

        if icon_path:

            self.setWindowIcon(QIcon(icon_path))

    def _fit_window_to_work_area(self) -> None:
        """Clamp the window so its complete frame fits the screen work area.

        Runs once, immediately after the first show, because the title-bar and
        border overhead is only known once the native frame exists.  Without
        this clamp the oversized default keeps the bottom of the window behind
        the taskbar, which hides the bottom button rows of pages such as the
        Nepali festival calendar.
        """
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return

        avail = screen.availableGeometry()
        chrome_w = max(0, self.frameGeometry().width() - self.width())
        chrome_h = max(0, self.frameGeometry().height() - self.height())
        max_w = max(320, avail.width() - chrome_w)
        max_h = max(240, avail.height() - chrome_h)

        # A minimum size larger than the display would keep the window
        # off-screen no matter how the user resizes it.
        self.setMinimumSize(min(1024, max_w), min(680, max_h))

        target_w = min(max(self.minimumWidth(), self.width()), max_w)
        target_h = min(max(self.minimumHeight(), self.height()), max_h)
        if (target_w, target_h) != (self.width(), self.height()):
            self.resize(target_w, target_h)

        frame = self.frameGeometry()
        self.move(
            avail.x() + max(0, (avail.width() - frame.width()) // 2),
            avail.y() + max(0, (avail.height() - frame.height()) // 2),
        )

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_work_area_fitted", False):
            self._work_area_fitted = True
            self._fit_window_to_work_area()

    def _setup_shortcuts(self):

        QShortcut(QKeySequence("Ctrl+K"), self).activated.connect(self._open_search)

        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._focus_input)

        # Ctrl+D always switches back to the main Rashi Kundali (D1) page.
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(
            lambda: self._navigate("chart_rashi")
        )

        # Ctrl+E — Export current page as PDF.
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._export_current_as_pdf)

    def _build_ui(self):

        # ── Menu Bar ──

        self._build_menubar()

        central = QWidget()

        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        root_layout.setContentsMargins(0, 0, 0, 0)

        root_layout.setSpacing(0)

        # ── Main area (splitter: input pane + content pane) ──

        self._main_splitter = QSplitter(Qt.Horizontal)

        self._main_splitter.setHandleWidth(2)

        self._main_splitter.setStyleSheet(f"QSplitter::handle {{ background: {BORDER_COLOR}; }}")

        # Chart entry is a reusable top-level window kept alive between sessions.

        self._input_panel = self._build_input_panel()

        self._input_panel.hide()

        # Content stack (right pane — 100% full width) with smooth animated page transitions

        self._content_stack = AnimatedStackedWidget()

        self._content_stack.setObjectName("ContentArea")

        self._main_splitter.addWidget(self._content_stack)

        self._main_splitter.setSizes([0, 1400])   # full width on startup

        self._main_splitter.setStretchFactor(1, 1)

        main_container = QWidget()

        main_layout = QVBoxLayout(main_container)

        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)

        # Birth ribbon (hidden until chart is calculated)

        self._ribbon = self._build_ribbon()

        self._ribbon.hide()

        main_layout.addWidget(self._ribbon)

        main_layout.addWidget(self._main_splitter, 1)

        root_layout.addWidget(main_container, 1)

        # ── Home page ──

        home_page = self._build_home_page()

        self._content_stack.addWidget(home_page)

        self._page_cache["home"] = home_page

        # ── Status bar ──

        self._status = QStatusBar()

        self._status.setSizeGripEnabled(True)

        self.setStatusBar(self._status)

        self._status_label = QLabel(

            "शिवराम जयोतिष सफटवेयर — तयार" if self._is_ne else "Shivram Jyotish — Ready"

        )

        self._status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        self._status.addWidget(self._status_label)

        self._progress = QProgressBar()

        self._progress.setMaximumWidth(180)

        self._progress.setMaximumHeight(14)

        self._progress.setRange(0, 0)  # indeterminate

        self._progress.hide()

        self._status.addPermanentWidget(self._progress)

        # Database-backed recent entries are non-critical startup work. Let the
        # window paint first so a slow/locked SQLite file cannot stall launch.
        QTimer.singleShot(0, self._refresh_recent_menu)

        lang_label = QLabel(f"🌐 {'नेपाली' if self._is_ne else 'English'}  |  {self._ayanamsha}")

        lang_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; padding-right: 8px;")

        self._status.addPermanentWidget(lang_label)

    # ── Menu Bar ──────────────────────────────────────────────────────────────

    def _build_menubar(self) -> None:
        """Build full top Menu Bar supporting dynamic Nepali / English switching."""
        mb = self.menuBar()
        mb.clear()
        mb.setNativeMenuBar(False)
        is_ne = self._is_ne

        # ── File menu ──
        self._file_menu = mb.addMenu("फाइल (&File)" if is_ne else "&File")

        act_new = QAction("📄  " + ("नयाँ कुण्डली (New Chart)\t\tCtrl+N" if is_ne else "New Chart\t\tCtrl+N"), self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._menu_new_chart)
        self._file_menu.addAction(act_new)

        act_open = QAction("📂  " + ("फाइल खोल्नुहोस् (Open File...)\t\tCtrl+O" if is_ne else "Open File...\t\tCtrl+O"), self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._open_chart_file)
        self._file_menu.addAction(act_open)

        act_fm = QAction("🗂  " + ("सेभ गरिएका कुण्डलीहरू (Saved Charts)\tCtrl+M" if is_ne else "File Manager / Saved Charts...\tCtrl+M"), self)
        act_fm.setShortcut(QKeySequence("Ctrl+M"))
        act_fm.triggered.connect(lambda: self._navigate("saved_charts"))
        self._file_menu.addAction(act_fm)

        act_save = QAction("💾  " + ("कुण्डली सेभ गर्नुहोस् (Save Chart)\t\tCtrl+S" if is_ne else "Save Chart\t\tCtrl+S"), self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._save_current_chart)
        self._file_menu.addAction(act_save)

        act_save_as = QAction("💾  " + ("सेभ एज (Save As...)" if is_ne else "Save As..."), self)
        act_save_as.triggered.connect(self._export_chart_file)
        self._file_menu.addAction(act_save_as)

        save_to_menu = QMenu("सेभ गर्ने ढाँचा (Save To)" if is_ne else "Save To", self)
        act_st_xml = QAction("XML File (.xml)...", self)
        act_st_xml.triggered.connect(lambda: self._export_chart_file("xml"))
        save_to_menu.addAction(act_st_xml)
        act_st_json = QAction("JSON File (.json)...", self)
        act_st_json.triggered.connect(lambda: self._export_chart_file("json"))
        save_to_menu.addAction(act_st_json)
        self._file_menu.addMenu(save_to_menu)

        act_close = QAction("❌  " + ("कुण्डली बन्द गर्नुहोस् (Close Chart)\tCtrl+W" if is_ne else "Close Chart\t\tCtrl+W"), self)
        act_close.setShortcut(QKeySequence("Ctrl+W"))
        act_close.triggered.connect(self._close_chart)
        self._file_menu.addAction(act_close)

        self._file_menu.addSeparator()

        act_model_print = QAction("📜  " + ("जन्मपत्रिका (कुण्डली निर्माण)" if is_ne else "Janmapatrika Print"), self)
        act_model_print.triggered.connect(lambda: self._navigate("kundali_nirman"))
        self._file_menu.addAction(act_model_print)

        act_print_screen = QAction("🖨  " + ("स्क्रिन प्रिन्ट (Print Screen)\tCtrl+P" if is_ne else "Print screen...\tCtrl+P"), self)
        act_print_screen.setShortcut(QKeySequence("Ctrl+P"))
        act_print_screen.triggered.connect(self._print_screen)
        self._file_menu.addAction(act_print_screen)

        act_print_setup = QAction("⚙  " + ("प्रिन्टर सेटिङ (Printer Setup)" if is_ne else "Printer Setup"), self)
        act_print_setup.triggered.connect(self._printer_setup)
        self._file_menu.addAction(act_print_setup)

        act_copy_screen = QAction("📋  " + ("स्क्रिन कपी (Copy Screen)\tCtrl+C" if is_ne else "Copy screen to Clipboard\tCtrl+C"), self)
        act_copy_screen.setShortcut(QKeySequence("Ctrl+C"))
        act_copy_screen.triggered.connect(self._copy_screen_to_clipboard)
        self._file_menu.addAction(act_copy_screen)

        self._file_menu.addSeparator()

        act_exit = QAction("🚪  " + ("बाहिरिनुहोस् (Exit)\tCtrl+Q" if is_ne else "Exit\t\tCtrl+Q"), self)
        act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        act_exit.triggered.connect(self.close)
        self._file_menu.addAction(act_exit)

        # _recent_actions list is maintained across menu rebuilds.
        # Only initialize it on first build (if not already set).
        if not hasattr(self, '_recent_actions'):
            self._recent_actions: list[QAction] = []
        else:
            # On rebuild, just clear existing recent actions (already removed by mb.clear())
            self._recent_actions.clear()

        # ── Charts menu (all kundali chart views) ──
        charts_menu = mb.addMenu("कुण्डली (&Charts)" if is_ne else "&Charts")
        for label_ne, label_en, view_id in [
            ("📜  कुण्डली निर्माण (जन्मपत्रिका)",  "📜  Traditional Janmapatrika",        "kundali_nirman"),
            ("📑  नेपाली चिना (A4 PDF)",           "📑  Nepali Cheena (A4 PDF)",         "traditional_cheena_a4"),
            ("🪐  राशि कुण्डली (D1)\t\tCtrl+D",     "🪐  Rashi Chart (D1)\t\tCtrl+D",     "chart_rashi"),
            ("🌌  नवांश कुण्डली (D9)",              "🌌  Navamsha Chart (D9)",            "chart_navamsha"),
            ("💼  दशमांश कुण्डली (D10)",            "💼  Dashamsha Chart (D10)",          "chart_dashamsha"),
            ("📊  सबै वर्ग कुण्डलीहरू (D1-D60)",     "📊  All Divisional Charts (D1-D60)", "chart_vargas"),
            ("☸  सुदर्शन चक्र",                    "☸  Sudarshan Chakra",                "chart_sudarshan"),
            ("☯  भाव चलित कुण्डली",                "☯  Bhava Chalit Chart",             "chart_bhava_chalit"),
        ]:
            a = QAction(label_ne if is_ne else label_en, self)
            a.triggered.connect(lambda checked=False, v=view_id: self._navigate(v))
            charts_menu.addAction(a)

        # Local helper so every report action is wired identically.
        def _add_report_items(parent_menu, items):
            for label_ne, label_en, view_id in items:
                a = QAction(label_ne if is_ne else label_en, self)
                a.triggered.connect(lambda checked=False, v=view_id: self._navigate(v))
                parent_menu.addAction(a)

        # ── Reports menu (all report options in one place, grouped) ──
        reports_menu = mb.addMenu("प्रतिवेदन (&Reports)" if is_ne else "&Reports")

        sub_comprehensive = reports_menu.addMenu(
            "📕  " + ("समग्र जीवन प्रतिवेदन" if is_ne else "Comprehensive Reports")
        )
        _add_report_items(sub_comprehensive, [
            ("📜  बृहत् जीवन कुण्डली (५०+ पृष्ठ)", "📜  Comprehensive Kundali Book (50+ Pg)", "report_comprehensive_book"),
            ("🧾  सबै-इन-वन प्रतिवेदन",           "🧾  All-in-One Report",                 "report_all_in_one"),
            ("📜  निष्कर्ष (पूर्ण फलित)",          "📜  Life Conclusion (Phalita)",         "report_life_conclusion"),
        ])

        sub_panchang = reports_menu.addMenu(
            "📅  " + ("पञ्चाङ्ग तथा ग्रह स्थिति" if is_ne else "Panchang & Planet Positions")
        )
        _add_report_items(sub_panchang, [
            ("📅  विस्तृत पञ्चाङ्ग",                "📅  Detailed Panchang",              "report_panchang"),
            ("📜  जन्म पञ्चाङ्ग तथा अवकहडा चक्र", "📜  Birth Panchang & Avakahada",    "report_birth_panchang"),
            ("🌀  अवकहडा चक्र (विस्तृत)",          "🌀  Avakahada Chakra (Detailed)",   "report_avakahada_chakra"),
            ("🌙  ग्रह स्थिति विवरण",               "🌙  Planetary Positions & Details", "report_planets"),
            ("📊  भिजुअल ग्राफहरू",                "📊  Astro Visual Graphs",           "report_visual_graphs"),
        ])

        sub_yoga = reports_menu.addMenu(
            "⭐  " + ("योग तथा दोष" if is_ne else "Yogas & Doshas")
        )
        _add_report_items(sub_yoga, [
            ("⭐  पराशरीय योग फल",                 "⭐  Parashara Yoga Report",         "report_yogas"),
            ("🐍  कालसर्प दोष",                    "🐍  Kaal Sarp Dosha",               "report_kaal_sarp_dosha"),
        ])

        sub_strength = reports_menu.addMenu(
            "⚡  " + ("ग्रह बल तथा अष्टकवर्ग" if is_ne else "Planet Strength & Ashtakavarga")
        )
        _add_report_items(sub_strength, [
            ("⚡  षड्बल तथा ग्रह बल",              "⚡  Shadbala Strength",              "report_shadbala"),
            ("💪  ग्रह शक्ति प्रोफाइल",            "💪  Planet Strength Profile",        "report_planet_strength"),
            ("📊  ग्रह अवस्था विश्लेषण",          "📊  Planetary Avasthas",             "report_avasthas"),
            ("⬡  अष्टकवर्ग तालिका",                "⬡  Ashtakavarga Grid",             "report_ashtakavarga"),
        ])

        reports_menu.addSeparator()

        sub_dasha = reports_menu.addMenu(
            "🪐  " + ("दशा तथा फलादेश" if is_ne else "Dasha & Predictions")
        )
        _add_report_items(sub_dasha, [
            ("📅  दशा-गोचर मासिक चार्ट",           "📅  Dasha-Gochar Monthly Chart",     "report_dasha_gochar_timeline"),
            ("📈  दशा तथा गोचर समयरेखा",          "📈  Dasha & Transit Timeline",      "report_dasha_transit_timeline"),
            ("📊  सम्पूर्ण दशा र रिपोर्ट",          "📊  Complete Dasha & Report",       "report_complete_dasha"),
            ("🪐  साढेसाती तथा अढैया",              "🪐  Sade Sati & Adhaiya",            "report_sadesati_adhaiya"),
            ("☀  दैनिक राशिफल",                    "☀  Daily Horoscope",                "report_daily_horoscope"),
            ("📅  वार्षिक वर्षफल (Varshaphala)",   "📅  Yearly Forecast (Varshaphala)", "report_yearly_forecast"),
            ("🪐  ग्रह गोचर क्यालेन्डर",            "🪐  Planetary Transit Calendar",     "report_planetary_ingress"),
        ])

        reports_menu.addSeparator()

        sub_life = reports_menu.addMenu(
            "💍  " + ("जीवन विश्लेषण" if is_ne else "Life Analysis")
        )
        _add_report_items(sub_life, [
            ("💍  विवाह/कलत्र विचार (दाम्पत्य विश्लेषण)", "💍  Marriage & Relationship (Kalatra) Analysis", "report_marriage_analysis"),
            ("💼  व्यवसाय/जीविका निर्णय (करियर विश्लेषण)", "💼  Career & Profession (Livelihood) Analysis",     "report_career_analysis"),
            ("🩺  स्वास्थ्य विश्लेषण",             "🩺  Health & Vitality Analysis",        "report_health_analysis"),
            ("👶  सन्तान तथा परिवार विश्लेषण",      "👶  Children & Family Analysis",       "report_child_analysis"),
            ("🪔  गण्डान्त तथा अनिष्ट शान्ति (BPHS)", "🪔  Gandanta & Arishta Shanti (BPHS)", "report_gandanta_shanti"),
            ("📚  शिक्षा तथा बुद्धि विश्लेषण",      "📚  Education & Intellect Analysis",   "report_education_analysis"),
            ("💰  आर्थिक तथा सम्पत्ति विश्लेषण",    "💰  Finance & Wealth Analysis",         "report_finance_wealth_analysis"),
            ("✈  विदेश यात्रा विश्लेषण",           "✈  Foreign Travel Analysis",           "report_foreign_travel_analysis"),
            ("🏪  व्यापार विश्लेषण",               "🏪  Business Analysis",                "report_business_analysis"),
            ("🏠  सम्पत्ति तथा सवारी विश्लेषण",     "🏠  Property & Vehicle Analysis",       "report_property_vehicle_analysis"),
            ("🧘  व्यक्तित्व विश्लेषण",             "🧘  Personality Analysis",              "report_personality_analysis"),
        ])

        reports_menu.addSeparator()

        sub_advanced = reports_menu.addMenu(
            "🔯  " + ("उन्नत ज्योतिष (जैमिनी, के.पी., लाल किताब)" if is_ne else "Advanced (Jaimini, KP, Lal Kitab)")
        )
        _add_report_items(sub_advanced, [
            ("📕  लाल किताब विश्लेषण तथा अचुक उपाय", "📕  Lal Kitab & Remedies",           "report_lal_kitab"),
            ("🔯  जैमिनी ज्योतिष विश्लेषण",        "🔯  Jaimini Astrology Analysis",       "report_jaimini_analysis"),
            ("🔮  के.पी. पद्धति विश्लेषण",          "🔮  KP System Analysis",               "report_kp_system"),
            ("💎  रत्न तथा वैदिक उपचार परामर्श",    "💎  Gemstones & Remedies",             "report_remedies"),
        ])

        reports_menu.addSeparator()

        sub_remedies = reports_menu.addMenu(
            "💎  " + ("रत्न तथा वैदिक उपचार" if is_ne else "Gemstones & Remedies")
        )
        _add_report_items(sub_remedies, [
            ("💎  रत्न, रुद्राक्ष तथा वैदिक उपचार (पूर्ण रिपोर्ट)", "💎  Gemstones, Rudraksha & Remedies", "report_remedies"),
        ])

        # ── Matching & Tools menu (interactive calculators) ──
        tools_menu = mb.addMenu("मिलान तथा औजार (&Tools)" if is_ne else "&Matching & Tools")
        for label_ne, label_en, view_id in [
            ("💎  रत्न तथा वैदिक उपचार",           "💎  Gemstones & Remedies",             "report_remedies"),
            ("💑  विवाह मिलान (३६ गुण)",           "💑  Marriage Matching (36 Gun Milan)", "marriage_matching"),
            ("❓  प्रश्न कुण्डली",                  "❓  Prashna Horary Chart",             "prashna_chart"),
            ("⏰  शुभ मुहूर्त अन्वेषण",             "⏰  Shubh Muhurta Finder",             "muhurta_finder"),
        ]:
            a = QAction(label_ne if is_ne else label_en, self)
            a.triggered.connect(lambda checked=False, v=view_id: self._navigate(v))
            tools_menu.addAction(a)

        tools_menu.addSeparator()

        act_hora = QAction("🕐  " + ("ग्रह होरा (वर्तमान होरा हेर्नुहोस्)" if is_ne else "Planetary Hora (Current Hour)"), self)
        act_hora.triggered.connect(lambda: self._navigate("planetary_hora"))
        tools_menu.addAction(act_hora)

        act_compare = QAction("⚖️  " + ("कुण्डली तुलना (Chart Comparison)" if is_ne else "Chart Comparison (Synastry)"), self)
        act_compare.triggered.connect(lambda: self._navigate("chart_comparison"))
        tools_menu.addAction(act_compare)

        act_yuddha = QAction("⚔️  " + ("ग्रह युद्ध (Graha Yuddha)" if is_ne else "Graha Yuddha — Planetary War"), self)
        act_yuddha.triggered.connect(lambda: self._navigate("graha_yuddha"))
        tools_menu.addAction(act_yuddha)

        act_dasha_cal = QAction("📅  " + ("दशा भिजुअल क्यालेन्डर" if is_ne else "Dasha Visual Calendar"), self)
        act_dasha_cal.triggered.connect(lambda: self._navigate("dasha_visual_calendar"))
        tools_menu.addAction(act_dasha_cal)

        act_nak_cal = QAction("🌙  " + ("नक्षत्र पञ्चाङ्ग क्यालेन्डर" if is_ne else "Nakshatra Panchang Calendar"), self)
        act_nak_cal.triggered.connect(lambda: self._navigate("nakshatra_calendar"))
        tools_menu.addAction(act_nak_cal)

        act_festival_cal = QAction("🪔  " + ("नेपाली पर्व क्यालेन्डर" if is_ne else "Nepali Festival Calendar"), self)
        act_festival_cal.triggered.connect(lambda: self._navigate("nepali_festival_calendar"))
        tools_menu.addAction(act_festival_cal)

        tools_menu.addSeparator()

        act_muhurta_cert = QAction("📜  " + ("मुहूर्त प्रमाणपत्र (Certificate)" if is_ne else "Muhurta Certificate Generator"), self)
        act_muhurta_cert.triggered.connect(lambda: self._navigate("muhurta_certificate"))
        tools_menu.addAction(act_muhurta_cert)

        act_vimsh = QAction("⚖️  " + ("षोडशवर्ग विंशोपक बल" if is_ne else "Shodashavarga Vimshopaka Bala"), self)
        act_vimsh.triggered.connect(lambda: self._navigate("vimshopaka_bala"))
        tools_menu.addAction(act_vimsh)

        act_ayur = QAction("⏳  " + ("पाराशर आयुर्दाय (आयु विश्लेषण)" if is_ne else "Parashari Ayurdaya — Longevity Analysis"), self)
        act_ayur.triggered.connect(lambda: self._navigate("ayurdaya"))
        tools_menu.addAction(act_ayur)

        act_gochar_rpt = QAction("🌐  " + ("गोचर फल विस्तृत रिपोर्ट" if is_ne else "Gochar Phal — Transit Report"), self)
        act_gochar_rpt.triggered.connect(lambda: self._navigate("gochar_phal_report"))
        tools_menu.addAction(act_gochar_rpt)

        act_gandanta = QAction("🪔  " + ("गण्डान्त तथा अनिष्ट शान्ति (BPHS)" if is_ne else "Gandanta & Arishta Shanti (BPHS)"), self)
        act_gandanta.triggered.connect(lambda: self._navigate("report_gandanta_shanti"))
        tools_menu.addAction(act_gandanta)


        # ── Classical References (प्राचीन ग्रन्थ) menu ──
        # Every entry opens a full-book reader showing the verbatim text that
        # was imported from authoritative Internet Archive scans (no fabricated
        # content). All texts are chart-independent full-book readers.
        classical_menu = mb.addMenu("प्राचीन ग्रन्थ (&References)" if is_ne else "&Classical References")
        for label_ne, label_en, view_id in [
            ("बृहत् पराशर होरा शास्त्र",  "Brihat Parashara Hora Shastra", "classical_bphs"),
            ("कल्याण वर्माको सारावली",   "Kalyan Verma's Saravali",        "classical_saravali"),
            ("मन्त्रेश्वरको फलदीपिका",   "Mantreswara's Phaladeepika",     "classical_phaladeepika"),
            ("जातक पारिजात",            "Jataka Parijata",                 "classical_jataka"),
        ]:
            a = QAction(label_ne if is_ne else label_en, self)
            a.triggered.connect(lambda checked=False, v=view_id: self._navigate(v))
            classical_menu.addAction(a)

        # ── View & Windows menu ──
        view_menu = mb.addMenu("दृश्य (&View)" if is_ne else "&View")
        act_cd = QAction("✨  " + ("कस्टमाइज ड्यासबोर्ड" if is_ne else "Customized Dashboard"), self)
        act_cd.triggered.connect(lambda: self._navigate("custom_dashboard"))
        view_menu.addAction(act_cd)

        act_home = QAction("🏠  " + ("गृह पृष्ठ (Home Overview)" if is_ne else "Home Overview"), self)
        act_home.triggered.connect(lambda: self._navigate("home"))
        view_menu.addAction(act_home)

        view_menu.addSeparator()
        act_input = QAction("📋  " + ("जन्म विवरण प्यानल (Input Panel)" if is_ne else "Show/Hide Input Panel"), self)
        act_input.triggered.connect(self._toggle_input_panel)
        view_menu.addAction(act_input)

        view_menu.addSeparator()

        act_export_pdf = QAction("📄  " + ("PDF एक्सपोर्ट (Export PDF)\tCtrl+E" if is_ne else "Export Current Page as PDF...\tCtrl+E"), self)
        act_export_pdf.setShortcut("Ctrl+E")
        act_export_pdf.triggered.connect(self._export_current_as_pdf)
        view_menu.addAction(act_export_pdf)

        act_export_png = QAction("🖼️  " + ("PNG एक्सपोर्ट (Export PNG)..." if is_ne else "Export Current Page as PNG..."), self)
        act_export_png.triggered.connect(self._export_current_as_png)
        view_menu.addAction(act_export_png)

        act_theme = QAction("🌙  " + ("डार्क/लाइट थिम बदल्नुहोस्" if is_ne else "Toggle Dark / Light Theme"), self)
        act_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(act_theme)

        # ── Settings menu (app, reminders & language) ──
        settings_menu = mb.addMenu("सेटिङ (&Settings)" if is_ne else "&Settings")

        act_settings = QAction("⚙  " + ("सेटिङ तथा प्राथमिकता..." if is_ne else "Settings & Preferences..."), self)
        act_settings.triggered.connect(self._show_settings_dialog)
        settings_menu.addAction(act_settings)

        act_reminders = QAction("⏰  " + ("रिमाइन्डर सेटिङ..." if is_ne else "Reminder Settings..."), self)
        act_reminders.triggered.connect(self._open_reminder_settings)
        settings_menu.addAction(act_reminders)

        settings_menu.addSeparator()

        lang_menu = QMenu("🌐  " + ("भाषा (Language)" if is_ne else "Language"), self)
        act_lang_ne = QAction("🇳🇵 नेपाली (Nepali)", self)
        act_lang_ne.setCheckable(True)
        act_lang_ne.setChecked(self._is_ne)
        act_lang_ne.triggered.connect(lambda: self._change_language("ne"))
        lang_menu.addAction(act_lang_ne)
        act_lang_en = QAction("🇬🇧 English", self)
        act_lang_en.setCheckable(True)
        act_lang_en.setChecked(not self._is_ne)
        act_lang_en.triggered.connect(lambda: self._change_language("en"))
        lang_menu.addAction(act_lang_en)
        settings_menu.addMenu(lang_menu)

        # ── Help menu ──
        help_menu = mb.addMenu("मद्दत (&Help)" if is_ne else "&Help")
        act_guide = QAction("📖  " + ("प्रयोगकर्ता निर्देशिका तथा कुण्डली इनपुट गाइड (User Guide)\tF1" if is_ne else "User Guide & Kundali Guidelines\tF1"), self)
        act_guide.setShortcut("F1")
        act_guide.triggered.connect(self._show_user_guide)
        help_menu.addAction(act_guide)

        act_shortcuts = QAction("⌨  " + ("किबोर्ड सर्टकट (Keyboard Shortcuts)\tCtrl+/" if is_ne else "Keyboard Shortcuts\tCtrl+/"), self)
        act_shortcuts.setShortcut("Ctrl+/")
        act_shortcuts.triggered.connect(self._show_shortcuts)
        help_menu.addAction(act_shortcuts)

        help_menu.addSeparator()
        act_about = QAction("ℹ  " + ("शिवराम ज्योतिषको बारेमा (About)..." if is_ne else "About Shivram Jyotish..."), self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

        act_update = QAction("🔄  " + ("अपडेट जाँच गर्नुहोस् (Check for Updates)" if is_ne else "Check for Updates..."), self)
        act_update.triggered.connect(self._start_update_checker)
        help_menu.addAction(act_update)

        # Always restore recent charts list after every menu rebuild
        self._refresh_recent_menu()

    RECENT_SETTINGS_KEY = "recent_kundali_list"

    def _get_recent_list(self) -> list[dict]:
        """Load the recent-chart list from persistent settings."""
        from PySide6.QtCore import QSettings
        import json

        settings = QSettings("ShivramJyotish", "Desktop")
        try:
            raw = settings.value(self.RECENT_SETTINGS_KEY, None)
            if raw is not None:
                items = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(items, list):
                    return [dict(item) for item in items if isinstance(item, dict)]
        except Exception:
            pass

        # First run (or a database added later): seed once from saved charts.
        try:
            from gui.utils.chart_storage import get_chart_params, list_charts

            seeded = []
            for chart in list_charts()[:6]:
                seeded.append({
                    "id": chart.get("id"),
                    "name": chart.get("name", ""),
                    "birth_date": chart.get("birth_date", ""),
                    "birth_time": chart.get("birth_time", ""),
                    "birth_place": chart.get("birth_place", ""),
                    "params": get_chart_params(chart["id"]) if chart.get("id") else chart,
                })
            if seeded:
                self._save_recent_list(seeded)
                return seeded
        except Exception:
            pass
        return []

    def _save_recent_list(self, recents: list[dict]) -> None:
        """Persist up to 6 recent charts in settings."""
        try:
            from PySide6.QtCore import QSettings
            import json

            settings = QSettings("ShivramJyotish", "Desktop")
            serializable = []
            for r in recents[:6]:
                serializable.append({
                    "id": r.get("id"),
                    "name": r.get("name", ""),
                    "birth_date": r.get("birth_date", ""),
                    "birth_time": r.get("birth_time", ""),
                    "birth_place": r.get("birth_place", ""),
                    "params": r.get("params", {}),
                })
            settings.setValue(
                self.RECENT_SETTINGS_KEY,
                json.dumps(serializable, ensure_ascii=False),
            )
        except Exception:
            pass

    def _add_to_recent(self, params: dict) -> None:
        """Move an opened chart to the top of the recent-chart list.

        Rules: at most 6 entries, newest first, no duplicates.
        """
        if not params:
            return

        name = str(params.get("name") or "अज्ञात").strip()
        birth_date = str(params.get("birth_date") or "").strip()
        birth_time = str(params.get("birth_time") or "").strip()
        birth_place = str(params.get("birth_place") or params.get("city") or "").strip()
        record_id = params.get("id") or params.get("record_id")

        recent = self._get_recent_list()

        def is_match(item: dict) -> bool:
            if record_id is not None and item.get("id") is not None:
                if str(item["id"]) == str(record_id):
                    return True
            item_name = str(item.get("name") or "").strip().lower()
            item_bd = str(item.get("birth_date") or "").strip()[:10]
            item_bt = str(item.get("birth_time") or "").strip()[:5]
            return (item_name == name.lower()
                    and item_bd == birth_date[:10]
                    and item_bt == birth_time[:5])

        recent = [r for r in recent if not is_match(r)]
        recent.insert(0, {
            "id": record_id,
            "name": name,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_place": birth_place,
            "params": dict(params),
        })
        self._save_recent_list(recent[:6])
        self._refresh_recent_menu()

    def _refresh_recent_menu(self) -> None:
        """Populate the Recent section below Exit in File menu (max 6 items)."""
        # Guard: _file_menu may not exist yet during very early startup
        if not hasattr(self, '_file_menu') or self._file_menu is None:
            return
        if not hasattr(self, '_recent_actions'):
            self._recent_actions = []

        # Remove old recent actions from current file menu (safe try/except)
        for a in self._recent_actions:
            try:
                self._file_menu.removeAction(a)
            except Exception:
                pass
        self._recent_actions.clear()

        recent = self._get_recent_list()[:6]
        if not recent:
            return

        sep = self._file_menu.addSeparator()
        self._recent_actions.append(sep)

        for idx, rec in enumerate(recent):
            chart_name = rec.get("name", "अज्ञात") or "अज्ञात"
            bd = str(rec.get("birth_date", ""))[:10]
            place = rec.get("birth_place") or ""

            label = (f"  {idx + 1}. {chart_name}"
                     + (f"  ({place})" if place else "")
                     + (f"  [{bd}]" if bd else ""))

            a = QAction(label, self)
            if idx == 0:
                a.setShortcut(QKeySequence("Ctrl+L"))

            rec_params = rec.get("params")
            rec_id = rec.get("id")

            def make_handler(params_dict, chart_id):
                def handler(checked=False):
                    if params_dict and (params_dict.get("latitude") is not None
                                        or params_dict.get("birth_date")):
                        self._open_saved_chart(params_dict)
                    elif chart_id:
                        self._open_chart_by_id(chart_id)
                return handler

            a.triggered.connect(make_handler(rec_params, rec_id))
            self._file_menu.addAction(a)
            self._recent_actions.append(a)

    def _open_chart_by_id(self, record_id: int) -> None:
        from gui.utils.chart_storage import get_chart_params
        params = get_chart_params(record_id)
        if params:
            params["id"] = record_id
            params["record_id"] = record_id
            self._open_saved_chart(params)

    def _menu_new_chart(self) -> None:
        """Open a clean, unpersisted chart-entry session without disrupting an open chart."""
        self._editing_record_id = None
        self._preview_chart_data = None
        self._show_input_panel()
        if self._chart_data is None:
            self._navigate("home")
        try:
            self._chart_input.load_params({
                "name": "", "birth_date": "", "birth_time": "",
                "latitude": 27.5833, "longitude": 83.05, "timezone": 5.75,
                "country": "Nepal", "region": "Lumbini", "province": "Lumbini",
                "district": "Kapilvastu", "city": "Kapilvastu",
                "gender": None, "ayanamsha_type": "LAHIRI",
            })
        except Exception:
            pass

    def _show_input_panel(self) -> None:
        """Show the reusable birth-data form in its own compact window."""
        self._input_panel.show()
        self._input_panel.raise_()
        self._input_panel.activateWindow()
        self._chart_input.setFocus()

    def _export_chart_file(self, fmt: str = "xml") -> None:

        """Export current chart params to an XML or JSON file.

        ``fmt`` is the file format (``'xml'`` or ``'json'``).  The File menu
        "Save To → XML / JSON" actions pass the format explicitly; the plain
        "Save As…" action uses the default ``'xml'``.
        """

        if not self._last_calc_params:

            self._set_status("No chart to export. Calculate a chart first.", error=True)

            return

        from PySide6.QtWidgets import QFileDialog

        name = self._last_calc_params.get("name", "chart").replace(" ", "_")
        default_name = f"{name}.{fmt}"

        path, _ = QFileDialog.getSaveFileName(

            self,

            "कुण्डली एक्सपोर्ट गर्नुहोस्" if self._is_ne else "Export Chart",

            default_name,

            "XML Files (*.xml);;JSON Files (*.json);;All Files (*)"

        )

        if not path:

            return

        try:

            _export_chart_to_file(self._last_calc_params, path)

            self._set_status(f"✓ Exported to: {path}")

        except Exception as e:

            QMessageBox.critical(self, "Export Error", f"Could not export:\n{e}")

    def _export_current_as_pdf(self) -> None:
        """Ctrl+E — Export the current visible page as PDF.

        If the active page is the Comprehensive Kundali Book it uses the
        book's own high-fidelity PDF engine; all other pages are captured
        as a pixmap and printed to PDF via QPrinter.
        """
        if self._chart_data is None:
            self._set_status(
                "पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne else "Calculate a chart first.",
                error=True,
            )
            return

        # If the current page is the comprehensive book, delegate to its handler.
        if self._active_view in ("report_comprehensive_book", "comprehensive_kundali_book"):
            page = self._page_cache.get(self._active_view)
            if page and hasattr(page, "_handle_export_pdf"):
                page._handle_export_pdf()
                return

        # General: grab current page and save as PDF via QPrinter.
        try:
            from PySide6.QtWidgets import QFileDialog
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QPainter, QPageSize, QPageLayout
            from PySide6.QtCore import QMarginsF, Qt

            meta = self._chart_data.get("metadata", {})
            name = (meta.get("name") or "chart").replace(" ", "_")
            default_name = f"{name}_{self._active_view}.pdf"

            path, _ = QFileDialog.getSaveFileName(
                self,
                "PDF सेभ गर्नुहोस्" if self._is_ne else "Save Page as PDF",
                default_name,
                "PDF Files (*.pdf)",
            )
            if not path:
                return

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Landscape)
            printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Millimeter)

            current_widget = self._content_stack.currentWidget()
            if current_widget is None:
                self._set_status("Export गर्नको लागि कुनै page खुलेको छैन।", error=True)
                return

            pix = current_widget.grab()
            painter = QPainter(printer)
            rect = painter.viewport()
            scaled = pix.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (rect.width() - scaled.width()) // 2
            painter.drawPixmap(x, 0, scaled)
            painter.end()

            self._set_status(f"✓ PDF सेभ गरियो: {path}")

        except Exception as e:
            QMessageBox.critical(self, "PDF Export Error", str(e))

    def _hide_input_panel(self) -> None:
        """Hide the reusable birth-data window without destroying its form."""
        self._input_panel.hide()

    def _toggle_input_panel(self) -> None:
        if self._input_panel.isVisible():
            self._hide_input_panel()
        else:
            self._show_input_panel()

    def _close_chart(self) -> None:
        """Close current chart and return cleanly to home screen without closing the application."""
        self._chart_data = None
        self._last_calc_params = None
        self._active_record_id = None
        self._editing_record_id = None
        self._preview_chart_data = None
        for vid in list(self._page_cache.keys()):
            if vid != "home":
                widget = self._page_cache.pop(vid)
                self._content_stack.removeWidget(widget)
                widget.deleteLater()
        self._ribbon.hide()
        self._edit_btn.hide()
        self._save_btn.hide()
        if hasattr(self, "_close_chart_btn"):
            self._close_chart_btn.hide()
        self._navigate("home")
        self._set_status("कुण्डली बन्द गरियो।" if self._is_ne else "Chart closed.")

    def _print_screen(self) -> None:

        """Print current screen or chart."""

        try:

            from PySide6.QtPrintSupport import QPrintDialog, QPrinter

            from PySide6.QtGui import QPainter

            printer = QPrinter()

            dlg = QPrintDialog(printer, self)

            if dlg.exec():

                painter = QPainter(printer)

                pix = self.grab()

                painter.drawPixmap(0, 0, pix)

                painter.end()

                self._set_status("✓ Print job sent to printer.")

        except Exception as e:

            QMessageBox.information(self, "Print", f"Print dialog: {e}")

    def _printer_setup(self) -> None:

        """Show printer setup dialog."""

        try:

            from PySide6.QtPrintSupport import QPageSetupDialog, QPrinter

            printer = QPrinter()

            dlg = QPageSetupDialog(printer, self)

            dlg.exec()

        except Exception as e:

            QMessageBox.information(self, "Printer Setup", f"Printer setup: {e}")

    def _copy_screen_to_clipboard(self) -> None:

        """Copy current window screenshot to system clipboard."""

        try:

            pixmap = self.grab()

            QApplication.clipboard().setPixmap(pixmap)

            self._set_status("✓ Screen copied to Clipboard!")

        except Exception as e:

            QMessageBox.warning(self, "Clipboard", f"Could not copy: {e}")

    def _change_language(self, lang: str) -> None:
        self._language = lang
        self._is_ne = lang == "ne"

        from PySide6.QtCore import QSettings
        settings = QSettings("ShivramJyotish", "Desktop")
        settings.setValue("language", lang)

        self._build_menubar()

        if hasattr(self, "_chart_input") and self._chart_input:
            self._chart_input.set_language(lang)

        self._page_cache.clear()

        if hasattr(self, "_active_view"):
            self._navigate(self._active_view)

        # Keep the system-tray reminder service in sync with the app language.
        service = getattr(self, "_reminder_service", None)
        if service is not None and hasattr(service, "set_language"):
            service.set_language(lang)

        msg = f"भाषा परिवर्तन गरियो: {'नेपाली' if self._is_ne else 'English'}" if self._is_ne else f"Language changed to {lang.upper()}"
        self._set_status(msg)

    # ── File open / export ───────────────────────────────────────────────────

    def _open_chart_file(self) -> None:

        """Open a chart from an XML or JSON file via file dialog."""

        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "कुण्डली फाइल खोल्नुहोस्" if self._is_ne else "Open Jyotish Chart File",
            "",
            "All Supported Chart Files (*.xml *.qck *.jhd *.json);;XML / QCK Files (*.xml *.qck);;Jagannatha Hora Files (*.jhd);;JSON Files (*.json);;All Files (*)"
        )

        if not path:

            return

        try:

            params = _load_chart_from_file(path)

            self._open_saved_chart(params)

            self._set_status(f"Opened: {path}")

        except Exception as e:

            QMessageBox.critical(self, "Open Error", f"Could not open file:\n{e}")


    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:

        sidebar = QWidget()

        sidebar.setObjectName("Sidebar")

        sidebar.setFixedWidth(248)

        sidebar_layout = QVBoxLayout(sidebar)

        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        sidebar_layout.setSpacing(0)

        # App header

        header = QWidget()

        header.setObjectName("SidebarHeader")

        header.setFixedHeight(72)

        header_layout = QVBoxLayout(header)

        header_layout.setContentsMargins(14, 10, 14, 10)

        header_layout.setSpacing(2)

        title = QLabel("☸ शिवराम जयोतिष")

        title.setObjectName("AppTitle")

        title.setStyleSheet(f"""

            font-family: "Cinzel", "Georgia", serif;

            font-size: 15px;

            font-weight: 700;

            color: {COLOR_GOLD};

        """)

        header_layout.addWidget(title)

        subtitle = QLabel("VEDIC ASTROLOGY SOFTWARE")

        subtitle.setStyleSheet(f"""

            font-size: 9px;

            font-weight: 700;

            color: {COLOR_TEXT_MUTED};

            letter-spacing: 1.5px;

        """)

        header_layout.addWidget(subtitle)

        sidebar_layout.addWidget(header)

        # Scrollable nav items

        nav_scroll = QScrollArea()

        nav_scroll.setWidgetResizable(True)

        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        nav_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        nav_container = QWidget()

        nav_container.setStyleSheet(f"background: {SIDEBAR_BG};")

        nav_layout = QVBoxLayout(nav_container)

        nav_layout.setContentsMargins(0, 4, 0, 4)

        nav_layout.setSpacing(0)

        for cat in NAV_STRUCTURE:

            cat_widget = SidebarCategoryWidget(cat, self._language)

            for item in cat["items"]:

                btn = cat_widget.add_item(item, self._navigate)

                self._sidebar_buttons[item["id"]] = btn

            nav_layout.addWidget(cat_widget)

            self._sidebar_cats.append(cat_widget)

        nav_layout.addStretch()

        nav_scroll.setWidget(nav_container)

        sidebar_layout.addWidget(nav_scroll, 1)

        # Bottom action buttons

        bottom = QWidget()

        bottom.setStyleSheet(f"background: {BG_SECONDARY}; border-top: 1px solid {SIDEBAR_BORDER};")

        bottom_layout = QVBoxLayout(bottom)

        bottom_layout.setContentsMargins(10, 8, 10, 8)

        bottom_layout.setSpacing(4)

        saved_btn = QPushButton("💾 " + ("सेव गरिका" if self._is_ne else "Saved Charts"))

        saved_btn.setObjectName("SidebarItem")

        saved_btn.setCursor(Qt.PointingHandCursor)

        saved_btn.clicked.connect(lambda: self._navigate("saved_charts"))

        bottom_layout.addWidget(saved_btn)

        settings_btn = QPushButton("⚙ " + ("सेटिङ" if self._is_ne else "Settings"))

        settings_btn.setObjectName("SidebarItem")

        settings_btn.setCursor(Qt.PointingHandCursor)

        settings_btn.clicked.connect(lambda: self._navigate("settings"))

        bottom_layout.addWidget(settings_btn)

        sidebar_layout.addWidget(bottom)

        return sidebar

    # ── Separate chart-entry window ───────────────────────────────────────────

    def _build_input_panel(self) -> QDialog:

        panel = QDialog(self)
        panel.setWindowTitle("📋 " + ("जन्म विवरण" if self._is_ne else "Birth Data"))
        panel.setWindowModality(Qt.NonModal)
        panel.setModal(False)
        panel.setMinimumSize(720, 540)
        panel.resize(780, 600)
        panel.setAttribute(Qt.WA_DeleteOnClose, False)
        panel.setStyleSheet(f"QDialog {{ background: {BG_SECONDARY}; }}")

        layout = QVBoxLayout(panel)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        # Header

        hdr = QLabel("  📋 " + ("जन्म विवरण" if self._is_ne else "Birth Data"))

        hdr.setStyleSheet(f"""
            background: {BG_TERTIARY}; color: {COLOR_GOLD};
            font-size: 13px; font-weight: 700;
            padding: 7px 10px;
            border-bottom: 1px solid {BORDER_COLOR};
        """)

        layout.addWidget(hdr)

        self._chart_input = ChartInputWidget(
            language=self._language,
            parent=panel,
        )

        self._chart_input.calculate_requested.connect(self._start_calculation)

        self._chart_input.approve_requested.connect(self._approve_preview)

        self._chart_input.reject_requested.connect(self._reject_entry)

        layout.addWidget(self._chart_input, 1)

        return panel

    # ── Birth ribbon ─────────────────────────────────────────────────────────

    def _build_ribbon(self) -> QWidget:
        """Build the centered, horizontally-scrollable birth ribbon bar."""
        ribbon = QFrame()
        ribbon.setObjectName("BirthRibbon")
        ribbon.setFixedHeight(48)
        outer = QVBoxLayout(ribbon)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Scroll host: keeps every field reachable on narrow windows ──
        self._ribbon_scroll = QScrollArea(ribbon)
        self._ribbon_scroll.setObjectName("BirthRibbonScroll")
        self._ribbon_scroll.setWidgetResizable(True)
        self._ribbon_scroll.setFrameShape(QFrame.NoFrame)
        self._ribbon_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._ribbon_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._ribbon_scroll.setFixedHeight(48)
        self._ribbon_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { height: 0px; width: 0px; }"
            "QScrollBar:horizontal { height: 0px; }"
        )
        outer.addWidget(self._ribbon_scroll)

        self._ribbon_content = QWidget()
        self._ribbon_content.setObjectName("BirthRibbonContent")
        content_layout = QHBoxLayout(self._ribbon_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ── Fields row — centered, with an inner spacer on either side ──
        self._ribbon_fields: dict[str, tuple[QLabel, QLabel]] = {}
        self._ribbon_fields_layout = QHBoxLayout()
        self._ribbon_fields_layout.setContentsMargins(16, 8, 16, 8)
        self._ribbon_fields_layout.setSpacing(16)
        self._ribbon_fields_layout.setAlignment(Qt.AlignVCenter)
        self._ribbon_fields_layout.addStretch(1)
        for index, key in enumerate(RIBBON_FIELD_KEYS):
            field = QFrame()
            field.setObjectName("BirthRibbonField")
            field_layout = QVBoxLayout(field)
            field_layout.setContentsMargins(10, 4, 10, 4)
            field_layout.setSpacing(1)
            field_layout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            if index < len(RIBBON_FIELD_KEYS) - 1:
                field.setStyleSheet(f"border-right: 1px solid {BORDER_COLOR};")
            label = QLabel("")
            label.setObjectName("BirthRibbonLabel")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; border: none;")
            value = QLabel("")
            value.setObjectName("BirthRibbonValue")
            value.setAlignment(Qt.AlignCenter)
            value.setStyleSheet("border: none;")
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            field_layout.addWidget(label)
            field_layout.addWidget(value)
            self._ribbon_fields_layout.addWidget(field)
            self._ribbon_fields[key] = (label, value)
        self._ribbon_fields_layout.addStretch(1)
        content_layout.addLayout(self._ribbon_fields_layout, 1)

        # ── Ribbon action buttons: [सम्पादन] [सेभ] [✕] ──
        self._edit_btn = QPushButton("✏️ " + ("सम्पादन" if self._is_ne else "Edit"))
        self._edit_btn.setFixedHeight(28)
        self._edit_btn.setCursor(Qt.PointingHandCursor)
        self._edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_TERTIARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                color: {COLOR_TEXT_PRIMARY};
                font-size: 11px;
                font-weight: 700;
                padding: 2px 10px;
            }}
            QPushButton:hover {{
                border-color: {COLOR_GOLD};
                color: {COLOR_GOLD};
                background: rgba(212,175,55,0.15);
            }}
        """)
        self._edit_btn.hide()
        self._edit_btn.clicked.connect(self._edit_current_chart)

        self._save_btn = QPushButton("💾 " + ("सेभ" if self._is_ne else "Save"))
        self._save_btn.setFixedHeight(28)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(212,175,55,0.15);
                border: 1px solid rgba(212,175,55,0.4);
                border-radius: 6px;
                color: {COLOR_GOLD};
                font-size: 11px;
                font-weight: 700;
                padding: 2px 12px;
            }}
            QPushButton:hover {{
                background: rgba(212,175,55,0.3);
            }}
        """)
        self._save_btn.hide()
        self._save_btn.clicked.connect(self._save_current_chart)

        self._close_chart_btn = QPushButton("✕")
        self._close_chart_btn.setToolTip("कुण्डली बन्द गर्नुहोस्" if self._is_ne else "Close Chart")
        self._close_chart_btn.setFixedSize(28, 28)
        self._close_chart_btn.setCursor(Qt.PointingHandCursor)
        self._close_chart_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.35);
                border-radius: 6px;
                color: #ef4444;
                font-size: 13px;
                font-weight: 800;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.3);
                border-color: #ef4444;
                color: #ffffff;
            }}
        """)
        self._close_chart_btn.hide()
        self._close_chart_btn.clicked.connect(getattr(self, "_close_chart", lambda: None))

        actions = QWidget()
        actions.setObjectName("BirthRibbonActions")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(4, 0, 10, 0)
        actions_layout.setSpacing(4)
        actions_layout.addWidget(self._edit_btn)
        actions_layout.addWidget(self._save_btn)
        actions_layout.addWidget(self._close_chart_btn)
        content_layout.addWidget(actions, 0, Qt.AlignVCenter)

        self._ribbon_scroll.setWidget(self._ribbon_content)

        return ribbon

    def _update_ribbon(self, data: dict) -> None:
        """Replace every displayed ribbon value after calculation or saved-chart load."""
        for field in build_birth_ribbon_model(data, self._language):
            label, value = self._ribbon_fields[field["key"]]
            label.setText(field["label"])
            value.setText(field["value"])
            if field["badge"]:
                if field["key"] == "mahadasha":
                    value.setStyleSheet(
                        f"color: {COLOR_GOLD}; background: rgba(29, 78, 216, 0.10); "
                        f"border: 1px solid {BORDER_COLOR}; border-radius: 999px; "
                        "font-size: 11px; font-weight: 700; padding: 0 6px;"
                    )
                else:
                    value.setStyleSheet(
                        f"color: {COLOR_TEXT_SECONDARY}; background: {BG_TERTIARY}; "
                        f"border: 1px solid {BORDER_COLOR}; border-radius: 999px; "
                        "font-size: 11px; font-weight: 700; padding: 0 6px;"
                    )
            else:
                value.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 700; border: none;")

        was_visible = self._ribbon.isVisible()
        self._ribbon.show()
        if not was_visible:
            self._ribbon.setMaximumHeight(0)
            anim = QPropertyAnimation(self._ribbon, b"maximumHeight", self)
            anim.setDuration(240)
            anim.setStartValue(0)
            anim.setEndValue(48)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._ribbon_anim = anim
        else:
            self._ribbon.setMaximumHeight(48)

        self._edit_btn.show()
        self._save_btn.show()
        self._close_chart_btn.show()

    # ── Home page ─────────────────────────────────────────────────────────────

    def _build_home_page(self) -> QWidget:
        return SolarSystemWidget(language=self._language)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, view_id: str) -> None:
        canonical_id = normalize_action_id(view_id)
        if canonical_id is None:
            self._active_view = view_id if isinstance(view_id, str) else ""
            for cat_w in self._sidebar_cats:
                cat_w.highlight_item(None)
            self._show_unavailable_page(view_id)
            return
        view_id = canonical_id

        if view_id != "home" and self._chart_data is None and view_id not in (

            "home", "custom_dashboard", "settings", "saved_charts", "classical_bphs",
            "classical_saravali", "classical_phaladeepika", "classical_jataka",
            "marriage_matching", "prashna_chart", "muhurta_finder", "report_panchang",
            "report_planetary_ingress", "traditional_cheena_a4", "kundali_nirman",
            # ── New tools (don't require a loaded chart) ──
            "planetary_hora", "chart_comparison", "graha_yuddha",
            "dasha_visual_calendar", "nakshatra_calendar", "nepali_festival_calendar",
            "muhurta_certificate", "vimshopaka_bala", "ayurdaya", "gochar_phal_report",
            "gandanta_shanti", "report_gandanta_shanti",
        ):

            self._set_status("कृपया पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne

                             else "Please calculate a chart first.", error=True)

            return

        self._active_view = view_id

        # The classical text pages are distraction-free book readers. Hide the
        # application chrome only for these views and restore it for every other
        # desktop page.
        book_only = view_id in ("classical_bphs", "classical_saravali", "classical_phaladeepika", "classical_jataka")
        self.menuBar().setVisible(not book_only)
        self.statusBar().setVisible(not book_only)
        self._ribbon.setVisible((bool(self._chart_data) or view_id == "marriage_matching") and not book_only)

        # Highlight sidebar

        for cat_w in self._sidebar_cats:

            cat_w.highlight_item(view_id)

        # Build or fetch page

        page = self._get_or_build_page(view_id)

        if page is None:
            self._show_unavailable_page(view_id)
            return

        if view_id == "report_panchang" and hasattr(page, "activate"):
            page.activate()

        # Show page

        if self._content_stack.indexOf(page) == -1:

            self._content_stack.addWidget(page)

        self._content_stack.setCurrentWidget(page)

    def _get_or_build_page(self, view_id: str) -> Optional[QWidget]:

        if view_id in self._page_cache:

            # Update existing page with fresh data if it has a refresh method

            page = self._page_cache[view_id]

            if hasattr(page, "refresh") and self._chart_data and view_id != "report_panchang":

                page.refresh(self._chart_data)

            return page

        page = self._build_page(view_id)

        if page:

            self._page_cache[view_id] = page

        return page

    def _build_page(self, view_id: str) -> Optional[QWidget]:

        """Build a content page widget for the given view_id."""

        data = self._chart_data

        # Saved Charts & Settings & Dashboard — no chart data strictly required

        if view_id == "saved_charts":

            return self._build_saved_charts_page()

        if view_id == "planetary_hora":

            from gui.widgets.planetary_hora_widget import PlanetaryHoraWidget
            # Use chart location if available, else default (Kathmandu)
            lat, lon, tz = 27.7172, 85.3240, 5.75
            if self._last_calc_params:
                lat = float(self._last_calc_params.get("latitude", lat))
                lon = float(self._last_calc_params.get("longitude", lon))
                tz  = float(self._last_calc_params.get("timezone",  tz))
            return PlanetaryHoraWidget(self._language, lat, lon, tz)

        if view_id == "chart_comparison":

            from gui.widgets.chart_comparison import ChartComparisonWidget
            return ChartComparisonWidget(self._language)

        if view_id == "graha_yuddha":

            from gui.widgets.graha_yuddha_page import GrahaYuddhPage
            return GrahaYuddhPage(
                chart_data=self._chart_data,
                language=self._language,
            )

        if view_id == "dasha_visual_calendar":

            from gui.widgets.dasha_visual_calendar import DashaVisualCalendarPage
            return DashaVisualCalendarPage(
                chart_data=self._chart_data,
                language=self._language,
            )

        if view_id == "nakshatra_calendar":

            from gui.widgets.nakshatra_calendar import NakshatraCalendarPage
            lat, lon, tz = 27.7172, 85.324, 5.75
            if self._last_calc_params:
                lat = float(self._last_calc_params.get("latitude", lat))
                lon = float(self._last_calc_params.get("longitude", lon))
                tz  = float(self._last_calc_params.get("timezone",  tz))
            return NakshatraCalendarPage(language=self._language, lat=lat, lon=lon, tz=tz)

        if view_id == "nepali_festival_calendar":

            from gui.widgets.nepali_festival_calendar import NepaliFestivalCalendarPage
            return NepaliFestivalCalendarPage(language=self._language)

        if view_id == "muhurta_certificate":

            from gui.widgets.muhurta_certificate import MuhurtaCertificatePage
            return MuhurtaCertificatePage(language=self._language)

        if view_id == "vimshopaka_bala":

            from gui.widgets.vimshopaka_bala_page import VimshopakaBalaPage
            return VimshopakaBalaPage(
                chart_data=self._chart_data,
                language=self._language,
            )

        if view_id == "ayurdaya":

            from gui.widgets.ayurdaya_page import AyurdayaPage
            return AyurdayaPage(
                chart_data=self._chart_data,
                language=self._language,
            )

        if view_id == "gochar_phal_report":

            from gui.widgets.gochar_phal_report import GocharPhalReportPage
            return GocharPhalReportPage(
                chart_data=self._chart_data,
                language=self._language,
            )

        if view_id in ("gandanta_shanti", "report_gandanta_shanti"):

            from gui.widgets.gandanta_shanti import GandantaShantiPage
            return GandantaShantiPage(
                chart_data=self._chart_data,
                language=self._language,
            )



        if view_id == "custom_dashboard":

            from gui.widgets.custom_dashboard import CustomDashboardPage

            return CustomDashboardPage(data, self._language)

        if view_id in ("classical_bphs", "classical_saravali", "classical_phaladeepika", "classical_jataka"):

            from gui.widgets.classical_references import ClassicalReferencePage

            page = ClassicalReferencePage(data, self._language, book_id=view_id)
            page.close_requested.connect(lambda: self._navigate("home"))
            return page

        if view_id == "settings":

            from gui.widgets.tools_widget import SettingsPage

            return SettingsPage(self._language)

        if view_id == "marriage_matching":

            from gui.widgets.tools_widget import MarriageMatchingPage

            return MarriageMatchingPage(self._language)

        if view_id == "prashna_chart":

            from gui.widgets.tools_widget import PrashnaChartPage

            return PrashnaChartPage(self._language, data=data)

        if view_id == "muhurta_finder":

            from gui.widgets.tools_widget import MuhurtaPage

            return MuhurtaPage(self._language)

        # Import widgets lazily

        if view_id == "home":

            return self._build_home_page()

        if view_id == "chart_rashi":

            from gui.widgets.north_indian_chart import NorthIndianChartPage

            return NorthIndianChartPage(data, "D1", self._language)

        if view_id == "chart_navamsha":

            from gui.widgets.north_indian_chart import NorthIndianChartPage

            return NorthIndianChartPage(data, "D9", self._language)

        if view_id == "chart_dashamsha":

            from gui.widgets.north_indian_chart import NorthIndianChartPage

            return NorthIndianChartPage(data, "D10", self._language)

        if view_id == "chart_vargas":

            from gui.widgets.vargas_grid import VargasGridPage

            return VargasGridPage(data, self._language)

        if view_id == "chart_sudarshan":

            from gui.widgets.vargas_grid import SudarshanChakraPage

            return SudarshanChakraPage(data, self._language)

        if view_id == "chart_bhava_chalit":

            from gui.widgets.bhava_chalit import BhavaChalitPage

            return BhavaChalitPage(data, self._language)

        if view_id == "report_planets":

            from gui.widgets.planetary_info import PlanetaryInfoPage

            return PlanetaryInfoPage(data, self._language)

        if view_id in ("report_life_conclusion", "report_phalita", "life_conclusion"):

            from gui.widgets.life_conclusion_page import LifeConclusionPage

            return LifeConclusionPage(data, self._language)

        if view_id in ("report_dasha_gochar_timeline", "report_dasha_transit_timeline", "report_dasha_gochar_monthly"):

            from gui.widgets.dasha_gochar_widget import DashaGocharPage

            default_m = "timeline" if view_id == "report_dasha_transit_timeline" else "grid"
            return DashaGocharPage(data, self._language, default_mode=default_m)

        if view_id in ("report_complete_dasha", "report_yogini", "report_yogini_dasha", "report_dasha_phal"):

            from gui.widgets.complete_dasha import CompleteDashaPage

            page = CompleteDashaPage(data, self._language)
            if view_id in ("report_yogini", "report_yogini_dasha"):
                page._select_system("yogini")
            return page

        if view_id in ("report_planetary_ingress", "ingress", "transit_calendar"):

            from gui.widgets.planetary_ingress_page import PlanetaryIngressPage

            return PlanetaryIngressPage(data, self._language)

        if view_id in ("report_avasthas", "graha_avasthas"):

            from gui.widgets.avasthas_page import PlanetaryAvasthasPage

            return PlanetaryAvasthasPage(data, self._language)

        if view_id in ("report_lal_kitab", "lal_kitab"):

            from gui.widgets.lal_kitab_page import LalKitabPage

            return LalKitabPage(data, self._language)

        if view_id == "report_sadesati_adhaiya":

            from gui.widgets.sadesati import SadeSatiPage

            return SadeSatiPage(data, self._language)

        if view_id == "report_daily_horoscope":

            from gui.widgets.life_analysis import HoroscopePage

            return HoroscopePage(data, "daily", self._language)

        if view_id == "report_yearly_forecast":

            from gui.widgets.life_analysis import VarshaphalaPage

            return VarshaphalaPage(data, self._language)

        if view_id == "report_panchang":

            from gui.widgets.panchang_info import PanchangInfoPage

            return PanchangInfoPage(
                None,
                self._language,
                auto_calculate=True,
                show_initial_data=False,
            )

        if view_id == "report_birth_panchang":

            from gui.widgets.birth_panchang_details import BirthPanchangDetailsPage

            metadata = data.get("metadata") if isinstance(data, dict) else {}
            try:
                gender = int((metadata or {}).get("gender", 0))
            except (TypeError, ValueError):
                gender = 0
            return BirthPanchangDetailsPage(data, self._language, gender)

        if view_id == "report_avakahada_chakra":

            from gui.widgets.avakahada_chakra import AvakahadaChakraPage

            return AvakahadaChakraPage(data, self._language)

        if view_id == "report_shadbala":

            from gui.widgets.shadbala_widget import ShadbalaPage

            return ShadbalaPage(data, self._language)

        if view_id == "report_planet_strength":

            from gui.widgets.planet_strength_profile import PlanetStrengthProfilePage

            return PlanetStrengthProfilePage(data, self._language)

        if view_id == "report_visual_graphs":

            from gui.widgets.visual_graphs import AstroVisualGraphsPage

            return AstroVisualGraphsPage(data, self._language)

        if view_id == "report_yogas":

            from gui.widgets.yoga_report import YogaReportPage

            return YogaReportPage(data, self._language)

        if view_id == "report_kaal_sarp_dosha":

            from gui.widgets.kaal_sarp_dosha import KaalSarpDoshaPage

            return KaalSarpDoshaPage(data, self._language)

        if view_id == "report_ashtakavarga":

            from gui.widgets.ashtakavarga import AshtakavargaPage

            return AshtakavargaPage(data, self._language)

        if view_id in ["report_comprehensive_book", "comprehensive_kundali_book"]:
            from gui.widgets.comprehensive_kundali_book import ComprehensiveKundaliBookPage
            return ComprehensiveKundaliBookPage(data, self._language)

        if view_id == "report_all_in_one":

            from gui.widgets.tools_widget import AllInOneReportPage

            return AllInOneReportPage(data, self._language)

        if view_id in ("report_remedies", "remedies", "gemstones", "rudraksha", "upaya"):

            from gui.widgets.remedies_page import RemediesPage

            return RemediesPage(data, self._language)

        if view_id == "report_marriage_analysis":

            from gui.widgets.marriage_analysis import MarriageAnalysisPage

            return MarriageAnalysisPage(data, self._language)

        if view_id == "report_career_analysis":

            from gui.widgets.career_analysis import CareerAnalysisPage

            return CareerAnalysisPage(data, self._language)

        if view_id == "report_health_analysis":

            from gui.widgets.health_analysis import HealthAnalysisPage

            return HealthAnalysisPage(data, self._language)

        if view_id == "report_child_analysis":

            from gui.widgets.child_analysis import ChildAnalysisPage

            return ChildAnalysisPage(data, self._language)

        if view_id in ("report_gandanta_shanti", "gandanta_shanti"):

            from gui.widgets.gandanta_shanti import GandantaShantiPage

            return GandantaShantiPage(data, self._language)

        if view_id == "report_education_analysis":

            from gui.widgets.education_analysis import EducationAnalysisPage

            return EducationAnalysisPage(data, self._language)

        if view_id == "report_finance_wealth_analysis":

            from gui.widgets.finance_wealth_analysis import FinanceWealthAnalysisPage

            return FinanceWealthAnalysisPage(data, self._language)

        if view_id == "report_foreign_travel_analysis":

            from gui.widgets.foreign_travel_analysis import ForeignTravelAnalysisPage

            return ForeignTravelAnalysisPage(data, self._language)

        if view_id == "report_business_analysis":

            from gui.widgets.business_analysis import BusinessAnalysisPage

            return BusinessAnalysisPage(data, self._language)

        if view_id == "report_property_vehicle_analysis":

            from gui.widgets.property_vehicle_analysis import PropertyVehicleAnalysisPage

            return PropertyVehicleAnalysisPage(data, self._language)

        if view_id == "report_personality_analysis":

            from gui.widgets.personality_analysis import PersonalityAnalysisPage

            return PersonalityAnalysisPage(data, self._language)

        if view_id == "kundali_nirman":

            from gui.widgets.janmapatrika_widget import JanmapatrikaPage

            return JanmapatrikaPage(data, self._language)

        if view_id in ("traditional_cheena_a4", "traditional_cheena", "cheena", "cheena_a4"):

            from gui.widgets.traditional_cheena_a4 import TraditionalCheenaA4Page

            return TraditionalCheenaA4Page(data, self._language)

        if view_id == "report_jaimini_analysis":

            from gui.widgets.jaimini_kp import JaiminiPage

            return JaiminiPage(data, self._language)

        if view_id == "report_kp_system":

            from gui.widgets.jaimini_kp import KPSystemPage

            return KPSystemPage(data, self._language)

        if view_id in ("report_transit_analysis", "transit_analysis", "gochar_analysis"):

            from gui.widgets.transit_analysis_page import TransitAnalysisPage

            return TransitAnalysisPage(data, self._language)

        if view_id in ("report_sarvatobhadra", "sarvatobhadra", "sarvatobhadra_chakra"):

            from gui.widgets.sarvatobhadra_page import SarvatobhadraPage

            return SarvatobhadraPage(data, self._language)

        if view_id in ("report_ayanamsha_comparator", "ayanamsha_comparator", "ayanamsha_tool"):

            from gui.widgets.ayanamsha_comparator_page import AyanamshaComparatorPage

            return AyanamshaComparatorPage(data, self._language)

        # Unimplemented actions are handled by _navigate without caching.
        return None

    def _show_unavailable_page(self, action_id: Any) -> None:
        """Show an explicit transient unavailable state; never cache it."""
        if self._unavailable_page is not None:
            old_page = self._unavailable_page
            self._content_stack.removeWidget(old_page)
            old_page.deleteLater()

        page = self._placeholder_page(str(action_id))
        self._unavailable_page = page
        self._content_stack.addWidget(page)
        self._content_stack.setCurrentWidget(page)
        self._set_status(
            "यो सुविधा हाल उपलब्ध छैन।" if self._is_ne
            else f"The selected action is unavailable: {action_id}",
            error=True,
        )

    def _placeholder_page(self, view_id: str) -> QWidget:

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("🚧")

        icon.setAlignment(Qt.AlignCenter)

        icon.setStyleSheet("font-size: 48px;")

        layout.addWidget(icon)

        lbl = QLabel(

            f"'{view_id}'\nयो सुविधा हाल उपलब्ध छैन।"

            if self._is_ne else

            f"'{view_id}'\nThis action is currently unavailable."

        )

        lbl.setAlignment(Qt.AlignCenter)

        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; line-height: 1.6;")

        layout.addWidget(lbl)

        return page

    def _build_saved_charts_page(self) -> QWidget:

        """Build saved charts page and wire open signal."""

        from gui.widgets.saved_charts import SavedChartsPage

        page = SavedChartsPage(self._language)

        page.chart_open_requested.connect(self._open_saved_chart)

        return page

    # ── Calculation ───────────────────────────────────────────────────────────

    def _stop_background_work(self) -> None:
        """Join worker threads before the window (and the process) goes away.

        A QThread that is still running when its owning QObject is destroyed
        aborts the process natively ("QThread: Destroyed while thread is still
        running", 0xC0000409), so closing the app during a calculation has to
        wait for it.
        """
        thread = self._calc_thread
        if thread is None:
            return
        try:
            if thread.isRunning():
                thread.quit()
                if not thread.wait(5000):
                    thread.terminate()
                    thread.wait(1000)
        except RuntimeError:
            pass  # already destroyed
        finally:
            self._calc_thread = None
            self._worker = None

    def closeEvent(self, event):
        self._stop_background_work()
        try:
            reminder = getattr(self, "_reminder_service", None)
            if reminder is not None and hasattr(reminder, "stop"):
                reminder.stop()
        except Exception:
            pass
        super().closeEvent(event)

    def _clear_calc_worker(self, thread=None) -> None:
        """Dispose of a finished calculation thread and its worker.

        ``thread`` is the QThread whose ``finished`` signal triggered this call.
        It matters: the attribute-based version deleted whatever
        ``self._calc_thread`` happened to point at, so a calculation started
        while the previous thread's ``finished`` event was still queued got its
        worker deleted mid-run ("QThread: Destroyed while thread is still
        running" and a lost result).
        """
        if thread is not None and thread is not self._calc_thread:
            return
        worker, calc_thread = self._worker, self._calc_thread
        self._worker = None
        self._calc_thread = None
        for obj in (worker, calc_thread):
            if obj is not None:
                try:
                    obj.deleteLater()
                except RuntimeError:
                    pass  # underlying C++ object already gone

    def _start_calculation(self, params: dict) -> None:
        """Calculate an entry preview without changing persisted or active chart state."""
        # Refuse to start a second run while one is in flight (the chart engine
        # is not re-entrant).  The second click is not silently lost: the user
        # can retry once the first run finishes.
        if self._calc_thread is not None:
            try:
                if self._calc_thread.isRunning():
                    return
            except RuntimeError:
                self._calc_thread = None
                self._worker = None

        self._preview_chart_data = None
        self._chart_input.set_loading(True)
        self._progress.show()
        self._set_status("गणना हुँदैछ..." if self._is_ne else "Calculating preview...")

        thread = QThread(self)
        worker = CalcWorker(params)
        worker.moveToThread(thread)
        self._calc_thread = thread
        self._worker = worker
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_calc_finished)
        worker.error.connect(self._on_calc_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(lambda t=thread: self._clear_calc_worker(t))
        thread.start()

    def _on_calc_finished(self, data: dict) -> None:
        self._preview_chart_data = data
        self._chart_input.set_loading(False)
        self._chart_input.set_preview_data(data)
        self._progress.hide()
        name = data.get("metadata", {}).get("name", "")
        self._set_status(
            f"{'पूर्वावलोकन तयार भयो' if self._is_ne else 'Preview ready'} — {name}"
        )

    def _on_calc_error(self, msg: str) -> None:
        self._preview_chart_data = None
        self._chart_input.set_loading(False)
        self._chart_input.invalidate_preview()
        self._progress.hide()
        self._set_status(f"त्रुटि: {msg}" if self._is_ne else f"Error: {msg}", error=True)
        QMessageBox.warning(
            self,
            "Calculation Error",
            msg,
            QMessageBox.Ok,
        )

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, error: bool = False) -> None:

        color = COLOR_ERROR if error else COLOR_TEXT_MUTED

        self._status_label.setStyleSheet(f"color: {color}; font-size: 11px;")

        self._status_label.setText(msg)

    def _open_search(self):

        self._set_status("Ctrl+K — Global search (coming soon)")

    def _focus_input(self):

        self._chart_input.setFocus()

    # ── Feature 1: Chart Export PNG/PDF ──────────────────────────────────────

    def _export_current_as_pdf(self) -> None:
        """Export current visible page as PDF (Ctrl+E)."""
        from PySide6.QtWidgets import QFileDialog
        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtGui import QPainter

        name = ""
        if self._chart_data:
            name = self._chart_data.get("metadata", {}).get("name", "kundali")
        name = name.replace(" ", "_") or "kundali"

        path, _ = QFileDialog.getSaveFileName(
            self, "PDF सुरक्षित गर्नुहोस्" if self._is_ne else "Export as PDF",
            f"{name}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageSize(printer.A4)
            widget = self._content_stack.currentWidget()
            if widget is None:
                return
            painter = QPainter(printer)
            widget.render(painter)
            painter.end()
            self._set_status(
                f"✓ PDF सुरक्षित: {path}" if self._is_ne else f"✓ PDF saved: {path}"
            )
            import subprocess
            subprocess.Popen(["explorer", "/select," + path.replace("/", "\\")])
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", str(exc))

    def _export_current_as_png(self) -> None:
        """Export current page as PNG image."""
        from PySide6.QtWidgets import QFileDialog

        name = ""
        if self._chart_data:
            name = self._chart_data.get("metadata", {}).get("name", "kundali")
        name = name.replace(" ", "_") or "kundali"

        path, _ = QFileDialog.getSaveFileName(
            self, "PNG सुरक्षित गर्नुहोस्" if self._is_ne else "Export as PNG",
            f"{name}.png", "PNG Images (*.png);;JPEG Images (*.jpg)"
        )
        if not path:
            return
        try:
            widget = self._content_stack.currentWidget()
            if widget is None:
                return
            pixmap = widget.grab()
            if pixmap.save(path):
                self._set_status(
                    f"✓ PNG सुरक्षित: {path}" if self._is_ne else f"✓ PNG saved: {path}"
                )
                import subprocess
                subprocess.Popen(["explorer", "/select," + path.replace("/", "\\")])
            else:
                QMessageBox.warning(self, "Export Error", "Image save failed.")
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", str(exc))

    # ── Feature 7: Clipboard Copy ─────────────────────────────────────────────

    def _copy_screen_to_clipboard(self) -> None:
        """Copy current page screenshot to clipboard."""
        from PySide6.QtWidgets import QApplication
        widget = self._content_stack.currentWidget()
        if widget is None:
            return
        pixmap = widget.grab()
        QApplication.clipboard().setPixmap(pixmap)
        self._set_status(
            "✓ स्क्रिन क्लिपबोर्डमा कपी भयो!" if self._is_ne
            else "✓ Screen copied to clipboard!"
        )

    # ── Print helpers ─────────────────────────────────────────────────────────

    def _print_screen(self) -> None:
        """Print current visible page."""
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        from PySide6.QtGui import QPainter
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.Accepted:
            return
        widget = self._content_stack.currentWidget()
        if widget is None:
            return
        painter = QPainter(printer)
        widget.render(painter)
        painter.end()
        self._set_status(
            "✓ प्रिन्ट पठाइयो।" if self._is_ne else "✓ Sent to printer."
        )

    def _printer_setup(self) -> None:
        """Open printer setup/properties dialog."""
        from PySide6.QtPrintSupport import QPrinter, QPageSetupDialog
        printer = QPrinter()
        dlg = QPageSetupDialog(printer, self)
        dlg.exec()

    # ── Feature 9: Theme Toggle ───────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        """Toggle between Classic (Light) and Dark theme."""
        from PySide6.QtCore import QSettings
        from gui.theme import apply_theme
        s = QSettings("ShivramJyotish", "Desktop")
        current = s.value("theme_mode", "classic")
        new_mode = "dark" if current == "classic" else "classic"
        s.setValue("theme_mode", new_mode)
        apply_theme(QApplication.instance(), new_mode)
        icon = "🌙" if new_mode == "dark" else "☀️"
        label = "डार्क थिम" if new_mode == "dark" else "लाइट थिम"
        self._set_status(f"{icon} {label} सक्रिय भयो।" if self._is_ne else f"{icon} {label} activated.")

    # ── Feature 13: Auto-Update Checker ──────────────────────────────────────

    def _start_update_checker(self) -> None:
        """Start background update check (called after window shows)."""
        try:
            from gui.utils.update_checker import UpdateChecker
            checker = UpdateChecker(
                current_version="2.0.0",
                on_update_available=self._on_update_available,
            )
            checker.start()
        except Exception:
            pass  # Update check failure must never block the app

    def _on_update_available(self, version: str, url: str) -> None:
        """Called from the background update-check thread."""
        self._update_available.emit(version, url)

    def _show_update_notification(self, version: str, url: str) -> None:
        """Show update notification dialog on main thread."""
        import webbrowser
        msg = QMessageBox(self)
        msg.setWindowTitle("नया संस्करण उपलब्ध!" if self._is_ne else "Update Available!")
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            f"शिवराम ज्योतिष संस्करण <b>{version}</b> उपलब्ध छ!<br>"
            f"<a href='{url}'>Download गर्न यहाँ क्लिक गर्नुहोस्</a>"
            if self._is_ne else
            f"Shivram Jyotish version <b>{version}</b> is available!<br>"
            f"<a href='{url}'>Click here to download</a>"
        )
        msg.setTextFormat(Qt.RichText)
        download_btn = msg.addButton(
            "Download" , QMessageBox.AcceptRole
        )
        msg.addButton(
            "पछि" if self._is_ne else "Later", QMessageBox.RejectRole
        )
        msg.exec()
        if msg.clickedButton() == download_btn and url:
            webbrowser.open(url)

    def _promote_preview(self, params: dict) -> None:
        if self._preview_chart_data is None:
            from gui.backend_bridge import calculate_chart
            self._preview_chart_data = calculate_chart(**params)

        self._chart_data = self._preview_chart_data
        self._last_calc_params = dict(params)
        self._preview_chart_data = None

        for vid in list(self._page_cache.keys()):
            if vid != "home":
                widget = self._page_cache.pop(vid)
                self._content_stack.removeWidget(widget)
                widget.deleteLater()

        self._update_ribbon(self._chart_data)
        self._add_to_recent(params)

    def _refresh_saved_chart_views(self) -> None:
        self._refresh_recent_menu()
        if "saved_charts" in self._page_cache:
            page = self._page_cache["saved_charts"]
            if hasattr(page, "_reload"):
                page._reload()

    def _approve_preview(self, params: dict) -> None:
        try:
            if self._preview_chart_data is None:
                from gui.backend_bridge import calculate_chart
                self._preview_chart_data = calculate_chart(**params)
            elif isinstance(self._preview_chart_data, dict):
                meta = self._preview_chart_data.setdefault("metadata", {})
                meta.update(params)

            from gui.utils.chart_storage import save_chart, update_chart

            if self._editing_record_id is None:
                record_id = save_chart(params)
            else:
                record_id = update_chart(self._editing_record_id, params)

            self._promote_preview(params)
            self._editing_record_id = None
            self._active_record_id = record_id
            self._refresh_saved_chart_views()
            self._hide_input_panel()
            self._navigate("chart_rashi")

            name = params.get("name", "")
            self._set_status(
                f"'{name}' स्वीकृत गरी सुरक्षित गरियो।" if self._is_ne
                else f"'{name}' approved and saved (ID {record_id})."
            )
        except Exception as exc:
            QMessageBox.warning(self, "Save Error", str(exc))

    def _reject_entry(self) -> None:
        self._editing_record_id = None
        self._preview_chart_data = None
        self._chart_input.invalidate_preview()
        self._hide_input_panel()
        self._set_status(
            "परिवर्तन अस्वीकृत गरियो; कुनै डेटा सुरक्षित भएन।" if self._is_ne
            else "Changes rejected; no data was saved."
        )

    def _edit_current_chart(self) -> None:
        """Open currently loaded chart in Edit Mode."""
        if not self._chart_data or not self._chart_data.get("metadata"):
            self._set_status("सम्पादनका लागि कुनै कुण्डली खुलेको छैन।" if self._is_ne else "No chart is currently open to edit.", error=True)
            return

        meta = self._chart_data.get("metadata", {})
        params = dict(self._last_calc_params) if self._last_calc_params else dict(meta)
        target_id = self._active_record_id or self._editing_record_id
        params["record_id"] = target_id
        self._editing_record_id = target_id
        self._preview_chart_data = dict(self._chart_data)
        self._chart_input.load_params(params)
        self._chart_input.set_preview_data(self._chart_data)
        self._show_input_panel()
        self._set_status(
            f"'{meta.get('name', '')}' को विवरण सम्पादन फारममा लोड गरियो।" if self._is_ne
            else f"Loaded '{meta.get('name', '')}' into edit form."
        )

    def _start_calculation_direct(self, params: dict) -> None:
        """Calculate a saved/imported chart without blocking the GUI thread."""
        if self._calc_thread is not None:
            try:
                if self._calc_thread.isRunning():
                    return
            except RuntimeError:
                self._calc_thread = None
                self._worker = None

        self._direct_calc_params = dict(params)
        self._progress.show()
        self._set_status("गणना हुँदैछ..." if self._is_ne else "Calculating...")

        thread = QThread(self)
        worker = CalcWorker(params)
        worker.moveToThread(thread)
        self._calc_thread = thread
        self._worker = worker
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_direct_calc_finished)
        worker.error.connect(self._on_direct_calc_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(lambda t=thread: self._clear_calc_worker(t))
        thread.start()

    def _on_direct_calc_finished(self, data: dict) -> None:
        params = self._direct_calc_params
        self._direct_calc_params = None
        if params is None:
            return
        try:
            self._preview_chart_data = data
            self._promote_preview(params)
            self._progress.hide()
            self._navigate("chart_rashi")
        except Exception as exc:
            self._on_direct_calc_error(str(exc))

    def _on_direct_calc_error(self, msg: str) -> None:
        self._direct_calc_params = None
        self._progress.hide()
        self._set_status(f"त्रुटि: {msg}" if self._is_ne else f"Error: {msg}", error=True)
        QMessageBox.warning(self, "Calculation Error", msg)

    def _save_current_chart(self) -> None:
        """Save or update the currently accepted chart in place."""
        if not self._last_calc_params:
            self._set_status("सेभ गर्नको लागि पहिले कुण्डली गणना गर्नुहोस्।"
                             if self._is_ne else "Calculate a chart first.", error=True)
            return

        try:
            from gui.utils.chart_storage import save_chart, update_chart
            target_id = self._active_record_id or self._editing_record_id
            name = self._last_calc_params.get("name", "")
            if target_id is None:
                record_id = save_chart(self._last_calc_params)
                self._active_record_id = record_id
                self._editing_record_id = record_id
                self._set_status(
                    f"✓ '{name}' नयाँ कुण्डली डाटाबेसमा सुरक्षित भयो (ID {record_id})।" if self._is_ne else f"✓ '{name}' saved to database (ID {record_id})."
                )
                QMessageBox.information(
                    self, "कुण्डली सेभ" if self._is_ne else "Save Chart",
                    f"नयाँ कुण्डली डाटाबेसमा सुरक्षित भयो (ID {record_id})।" if self._is_ne else f"New chart saved to database (ID {record_id})."
                )
            else:
                record_id = update_chart(target_id, self._last_calc_params)
                self._active_record_id = record_id
                self._editing_record_id = record_id
                self._set_status(
                    f"✓ '{name}' सोही स्थानमा सफलतापूर्वक अपडेट/रिप्लेस भयो (ID {record_id})।" if self._is_ne else f"✓ '{name}' updated in place (ID {record_id})."
                )
                QMessageBox.information(
                    self, "कुण्डली अपडेट" if self._is_ne else "Update Chart",
                    f"कुण्डली रेकर्ड सोही स्थानमा सफलतापूर्वक अपडेट/रिप्लेस भयो (ID {record_id})।" if self._is_ne else f"Chart record updated in place (ID {record_id})."
                )

            self._refresh_saved_chart_views()
        except Exception as e:
            QMessageBox.warning(self, "Save Error", str(e))

    def _open_saved_chart(self, params: dict) -> None:
        """Directly calculate and display a saved chart without showing the entry form."""
        record_id = params.get("id") or params.get("record_id")
        self._active_record_id = record_id
        self._editing_record_id = record_id
        self._last_calc_params = dict(params)
        try:
            self._hide_input_panel()
            self._start_calculation_direct(params)
            name = params.get("name", "")
            self._set_status(
                f"कुण्डली खोलियो: {name}" if self._is_ne
                else f"Chart loaded: {name}"
            )
        except Exception as exc:
            QMessageBox.warning(self, "Open Error", str(exc))

    def _show_settings_dialog(self) -> None:
        """Open settings dialog and reload preferences."""
        try:
            from gui.widgets.settings_dialog import show_settings_dialog
            from PySide6.QtCore import QSettings
            if show_settings_dialog(self):
                settings = QSettings("ShivramJyotish", "Desktop")
                self._ayanamsha = settings.value("ayanamsha", "LAHIRI")
                self._language = settings.value("language", "ne")
                if hasattr(self, "_chart_input") and self._chart_input:
                    self._chart_input.reload_settings()
                self._set_status(
                    "सेटिङ सफलतापूर्वक अपडेट भयो।" if self._is_ne else "Settings updated successfully."
                )
        except Exception as e:
            QMessageBox.warning(self, "Settings Error", str(e))

    def _open_reminder_settings(self) -> None:
        """Open the system-tray reminder configuration dialog from the Settings menu."""
        try:
            from gui.reminder_service import ReminderSettingsDialog
        except Exception as exc:  # defensive — Settings menu must never break
            QMessageBox.warning(self, "Reminders",
                                f"रिमाइन्डर सेटिङ लोड गर्न सकिएन।\n{exc}" if self._is_ne
                                else f"Could not load reminder settings.\n{exc}")
            return

        dialog = ReminderSettingsDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.values()

        # 1) Persist directly (works even if the live tray service is not attached yet).
        from PySide6.QtCore import QSettings
        s = QSettings("ShivramJyotish", "Desktop")
        s.setValue("reminders/enabled", bool(values["enabled"]))
        s.setValue("reminders/digest_time", str(values["digest_time"]))
        s.setValue("reminders/rahu_kaal", bool(values["rahu"]))
        s.setValue("reminders/choghadiya", bool(values["choghadiya"]))
        s.setValue("reminders/festivals", bool(values["festivals"]))
        s.setValue("reminders/upcoming_days", int(values["upcoming"]))
        s.setValue("reminders/latitude", float(values["latitude"]))
        s.setValue("reminders/longitude", float(values["longitude"]))
        s.setValue("reminders/timezone", float(values["timezone"]))

        # 2) Push into the live service so the tray / digest refresh immediately.
        service = getattr(self, "_reminder_service", None)
        if service is not None and hasattr(service, "update_settings"):
            service.update_settings(values)

        QMessageBox.information(
            self,
            "Reminders",
            ("रिमाइन्डर सेटिङ सुरक्षित भयो।" if self._is_ne
             else "Reminder settings saved."),
        )

    def _show_user_guide(self) -> None:
        """Open the interactive User Guide & Guidelines dialog."""
        try:
            from gui.widgets.user_guide import show_user_guide
            show_user_guide(self)
        except Exception as e:
            QMessageBox.warning(self, "Guide Error", str(e))

    def _show_shortcuts(self) -> None:
        """Display keyboard shortcuts dialog."""
        shortcuts_text = """
        <h3>⌨️ किबोर्ड सर्टकटहरू (Keyboard Shortcuts)</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #332820; color: #d4af37;"><th>सर्टकट</th><th>कार्य</th></tr>
            <tr><td><b>F1</b></td><td>प्रयोगकर्ता निर्देशिका (User Guide / Help)</td></tr>
            <tr><td><b>Ctrl + N</b></td><td>नयाँ कुण्डली इनपुट फारम (New Chart Form)</td></tr>
            <tr><td><b>Ctrl + O</b></td><td>कुण्डली फाइल खोल्नुहोस् (Open Saved Chart)</td></tr>
            <tr><td><b>Ctrl + S</b></td><td>कुण्डली सेभ गर्नुहोस् (Save to Database)</td></tr>
            <tr><td><b>Ctrl + P</b></td><td>कुण्डली प्रिन्ट गर्नुहोस् (Print Chart)</td></tr>
            <tr><td><b>Ctrl + E</b></td><td>PDF एक्सपोर्ट गर्नुहोस् (Export PDF)</td></tr>
            <tr><td><b>Ctrl + R</b></td><td>पूर्वावलोकन / पुनः गणना (Preview / Recalculate)</td></tr>
            <tr><td><b>Ctrl + D</b></td><td>राशि कुण्डली (D1) मा जानुहोस् (Go to Rashi Chart D1)</td></tr>
            <tr><td><b>Ctrl + /</b></td><td>किबोर्ड सर्टकट सूची हेर्नुहोस् (Shortcuts)</td></tr>
            <tr><td><b>Esc</b></td><td>इनपुट प्यानल वा डायलग बन्द गर्नुहोस् (Close)</td></tr>
        </table>
        """
        dlg = QMessageBox(self)
        dlg.setWindowTitle("किबोर्ड सर्टकटहरू (Keyboard Shortcuts)")
        dlg.setTextFormat(Qt.RichText)
        dlg.setText(shortcuts_text)
        dlg.setIcon(QMessageBox.Information)
        dlg.exec()

    def _show_about(self) -> None:
        """Display About Shivram Jyotish dialog."""
        about_text = """
        <div style="text-align: center;">
            <h2 style="color: #d4af37; margin-bottom: 4px;">शिवराम ज्योतिष (Shivram Jyotish)</h2>
            <p style="color: #a89f91; font-size: 13px;">व्यावसायिक वैदिक ज्योतिष तथा पञ्चाङ्ग गणना प्रणाली</p>
            <hr style="border: 0; border-top: 1px solid #44372c; margin: 12px 0;">
            <p style="text-align: left; line-height: 1.6; font-size: 13px;">
                <b>संस्करण:</b> 2.0 (High-Precision Swiss Ephemeris Calibrated)<br>
                <b>खगोलीय इन्जिन:</b> Swiss Ephemeris & JPL DE421 Drik Ganita<br>
                <b>अयनांश:</b> चित्रपक्षीय / लाहिरी (Chitrapaksha Lahiri standard)<br>
                <b>सुविधाहरू:</b> कुण्डली, वर्ग चक्रहरू (D1-D60), भाव चलित, अष्टकवर्ग, षड्बल, विंशोत्तरी/योगिनी/चर दशा, गोचर, पञ्चाङ्ग, मुहूर्त, विवाह मेलापक, ३ वर्षको क्यालिब्रेटेड नेपाली पात्रो, ६००+ विश्व सहरहरू र स्वचालित DST।
            </p>
        </div>
        """
        dlg = QMessageBox(self)
        dlg.setWindowTitle("शिवराम ज्योतिषको बारेमा (About Shivram Jyotish)")
        dlg.setTextFormat(Qt.RichText)
        dlg.setText(about_text)
        dlg.setIcon(QMessageBox.Information)
        dlg.exec()

# ── Module-level file import/export helpers ────────────────────────────────────

_CHART_FIELDS = [

    "name", "birth_date", "birth_time",

    "latitude", "longitude", "timezone", "timezone_id",

    "city", "gender", "ayanamsha_type", "node_type", "house_system",

]

def julian_day_to_gregorian(jd: float):

    import math

    jd_adj = jd + 0.5

    Z = math.floor(jd_adj)

    F = jd_adj - Z

    if Z < 2299161:

        A = Z

    else:

        alpha = math.floor((Z - 1867216.25) / 36524.25)

        A = Z + 1 + alpha - math.floor(alpha / 4)

    B = A + 1524

    C = math.floor((B - 122.1) / 365.25)

    D = math.floor(365.25 * C)

    E = math.floor((B - D) / 30.6001)

    day = int(B - D - math.floor(30.6001 * E))

    month = int(E - 1 if E < 14 else E - 13)

    year = int(C - 4716 if month > 2 else C - 4715)

    total_seconds = round(F * 86400)

    hour = int(total_seconds // 3600)

    minute = int((total_seconds % 3600) // 60)

    second = int(total_seconds % 60)

    return f"{year:04d}-{month:02d}-{day:02d}", f"{hour:02d}:{minute:02d}:{second:02d}"

def _export_chart_to_file(params: dict, path: str) -> None:

    """Export birth params to XML or JSON file."""

    if path.lower().endswith(".json"):

        import json

        with open(path, "w", encoding="utf-8") as f:

            json.dump({k: params.get(k) for k in _CHART_FIELDS}, f,

                      ensure_ascii=False, indent=2)

    else:

        # PL7 compatible XML format

        import xml.etree.ElementTree as ET

        root = ET.Element("BirthData")

        name_parts = (params.get("name") or "Unknown").split(" ", 1)

        fname = name_parts[0]

        lname = name_parts[1] if len(name_parts) > 1 else ""

        ET.SubElement(root, "FirstName").text = fname

        ET.SubElement(root, "LastName").text = lname

        ET.SubElement(root, "City").text = str(params.get("city") or "Kathmandu")

        ET.SubElement(root, "Gender").text = str(params.get("gender", 0))

        # Birth date/time

        bd = params.get("birth_date", "1990-01-15")

        bt = params.get("birth_time", "10:30:00")

        try:

            y, m, d = map(int, bd.split("-"))

            h, mi = map(int, bt.split(":")[:2])

            # Rough JD estimation for export

            from datetime import date

            jd_val = date(y, m, d).toordinal() + 1721424.5 + (h + mi / 60.0) / 24.0

            ET.SubElement(root, "BirthDate").text = f"{jd_val:.7f}"

        except Exception:

            ET.SubElement(root, "BirthDate").text = bd

        ET.SubElement(root, "TimeZone").text = f"-{abs(float(params.get('timezone', 5.75))):.7f}"

        ET.SubElement(root, "Latitude").text = f"{float(params.get('latitude', 27.7172)):.7f}"

        ET.SubElement(root, "Longitude").text = f"-{abs(float(params.get('longitude', 85.3240))):.7f}"

        ET.SubElement(root, "AyanamshaType").text = str(params.get("ayanamsha_type", "LAHIRI"))

        tree = ET.ElementTree(root)

        ET.indent(tree, space="  ")

        tree.write(path, encoding="utf-8", xml_declaration=True)

def _load_chart_from_file(path: str) -> dict:
    """Load birth params from XML (.xml, .qck), Jagannatha Hora (.jhd), or JSON file."""
    if path.lower().endswith(".json"):
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Flatten if metadata object exists
            if isinstance(data, dict) and "metadata" in data and isinstance(data["metadata"], dict):
                merged = dict(data["metadata"])
                merged.update({k: v for k, v in data.items() if k != "metadata"})
                return merged
            return data

    # Read binary raw bytes to prevent encoding mismatch errors
    with open(path, "rb") as f:
        raw_bytes = f.read()

    # Try common text encodings
    text = None
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin1"):
        try:
            t = raw_bytes.decode(enc)
            if t.strip():
                text = t
                break
        except Exception:
            pass

    if text is None:
        text = raw_bytes.decode("utf-8", errors="replace")

    text = text.strip()

    # Check for Jagannatha Hora (.jhd) format (plain text lines)
    if not text.startswith("<") and ("." in path.lower() and path.lower().endswith(".jhd")):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) >= 7:
            try:
                m = int(lines[0])
                d = int(lines[1])
                y = int(lines[2])
                t_dec = float(lines[3])
                thour = int(t_dec)
                tmin = int((t_dec - thour) * 60)
                tsec = int(round(((t_dec - thour) * 60 - tmin) * 60))
                btime = f"{thour:02d}:{tmin:02d}:{tsec:02d}"
                # Keep the signs as stored.  The previous abs() turned a western
                # birth (longitude -74.006, offset -5.0) into an eastern one
                # (+74.006, +5.0), which moved the ascendant and every house -
                # the imported chart was simply wrong.  If a file only stores
                # magnitudes the values are unchanged, so this is safe either way.
                tz = float(lines[4])
                lon = float(lines[5])
                lat = float(lines[6])
                name = lines[7] if len(lines) > 7 else "Jagannatha Hora Chart"
                return {
                    "name": name,
                    "birth_date": f"{y:04d}-{m:02d}-{d:02d}",
                    "birth_time": btime,
                    "latitude": lat,
                    "longitude": lon,
                    "timezone": tz,
                    "city": "",
                    "gender": 0,
                    "ayanamsha_type": "LAHIRI",
                }
            except Exception:
                pass

    # Strip XML header declaration (e.g. <?xml ...?>)
    if text.startswith("<?xml"):
        end_idx = text.find("?>")
        if end_idx != -1:
            text = text[end_idx + 2:].strip()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(text)

    # Prefer <BirthInfo> element if present, otherwise root
    birth_info_el = root.find("BirthInfo")
    if birth_info_el is None:
        birth_info_el = root.find("birthinfo")
    if birth_info_el is None:
        birth_info_el = root

    tag_map = {child.tag.lower(): (child.text or "").strip() for child in birth_info_el.iter() if child.tag}
    # Also capture root tags if not present in birth_info_el
    for child in root:
        if child.tag and child.tag.lower() not in tag_map:
            tag_map[child.tag.lower()] = (child.text or "").strip()

    # Check Parashara's Light / QuickChart / Julian day format
    if "birthdate" in tag_map and tag_map["birthdate"]:
        try:
            jd = float(tag_map["birthdate"])
            bdate, btime = julian_day_to_gregorian(jd)
        except Exception:
            # The Julian Day value was unusable.  Note that tag_map keys are
            # lower-cased, so the ISO date is stored under "birthdate" too.
            # Falling back to a fixed placeholder date would silently build a
            # chart for the wrong person, so use the real date when present and
            # refuse the file otherwise.
            bdate = (tag_map.get("birth_date") or tag_map.get("birthdate")
                     or tag_map.get("date"))
            btime = tag_map.get("birth_time") or tag_map.get("birthtime") or tag_map.get("time")
            if not bdate:
                raise ValueError(
                    "The file's birth date is neither a valid Julian Day nor a "
                    "recognised date, so the chart cannot be built."
                )

        fname = tag_map.get("firstname", "")
        lname = tag_map.get("lastname", "")
        name = f"{fname} {lname}".strip() or tag_map.get("name", "Unknown")
        tz = abs(float(tag_map.get("timezone") or tag_map.get("tz") or 5.75))
        lat = float(tag_map.get("latitude") or tag_map.get("lat") or 27.7172)
        lon = abs(float(tag_map.get("longitude") or tag_map.get("lon") or 85.3240))
        city = tag_map.get("city") or tag_map.get("birth_place") or "Kathmandu"
        gender = int(tag_map.get("gender") or 0)

        return {
            "name": name,
            "birth_date": bdate,
            "birth_time": btime,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "city": city,
            "gender": gender,
            "ayanamsha_type": tag_map.get("ayanamsha_type") or tag_map.get("ayanamsha") or "LAHIRI",
        }

    # Standard XML tag matching (case-insensitive)
    name = (tag_map.get("name") or tag_map.get("fullname") or
            f"{tag_map.get('firstname', '')} {tag_map.get('lastname', '')}".strip() or "Unknown")
    bdate = tag_map.get("birth_date") or tag_map.get("birthdate") or tag_map.get("date")
    if not bdate:
        # No birth date in the file: a chart cannot be computed, and inventing
        # one would present a real-looking horoscope for a person who does not
        # exist in the file.
        raise ValueError("The file contains no birth date, so no chart can be built.")
    btime = tag_map.get("birth_time") or tag_map.get("birthtime") or tag_map.get("time") or "12:00:00"
    lat = float(tag_map.get("latitude") or tag_map.get("lat") or 27.7172)
    lon = abs(float(tag_map.get("longitude") or tag_map.get("lon") or 85.3240))
    tz = abs(float(tag_map.get("timezone") or tag_map.get("tz") or 5.75))
    city = tag_map.get("city") or tag_map.get("birth_place") or tag_map.get("place") or ""
    gender = int(tag_map.get("gender") or 0)
    ayanamsha = tag_map.get("ayanamsha_type") or tag_map.get("ayanamsha") or "LAHIRI"

    return {
        "name": name,
        "birth_date": bdate,
        "birth_time": btime,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "city": city,
        "gender": gender,
        "ayanamsha_type": ayanamsha,
    }

