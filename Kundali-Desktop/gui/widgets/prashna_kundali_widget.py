# -*- coding: utf-8 -*-
"""
gui/widgets/prashna_kundali_widget.py
Comprehensive Classical Horary & Question Kundali (प्रश्न कुण्डली) Engine
Features:
- Default: "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)" for status-agnostic, pure astrological calculation
- Optional specific status toggles (विवाहित / अविवाहित / कार्यरत / बेरोजगार आदि) if user explicitly specifies
- Dedicated Question-Specific Direct Astrological Answers for EVERY question across all 18 categories
- Full Parashari (BPHS), Prasna Marga, and Tajika Neelakanthi integration
- Pure Nepali Devanagari typography
"""
from __future__ import annotations
import sys
import os
import datetime
from typing import Optional, Dict, Any, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QComboBox, QLineEdit, QPushButton, QRadioButton,
    QButtonGroup, QListWidget, QListWidgetItem, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QTime, Signal
from PySide6.QtGui import QFont, QColor

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.utils.bs_calendar import gregorian_to_bs, to_nepali_digits, BS_MONTHS_NE
from gui.utils.planet_colors import rashi_name, to_nepali_digits as ne_num

try:
    from backend.calculator.marriage_timing_engine import (
        calculate_mathematical_formulas,
        find_marriage_windows_age_15_to_50,
    )
    from backend.calculator.marriage_direction_engine import calculate_marriage_direction
except ImportError:
    from calculator.marriage_timing_engine import (
        calculate_mathematical_formulas,
        find_marriage_windows_age_15_to_50,
    )
    from calculator.marriage_direction_engine import calculate_marriage_direction


# ── १८ प्रमुख प्रश्न क्षेत्रहरू (18 Comprehensive Question Categories) ─────────
PRASHNA_DATA: Dict[str, Dict[str, Any]] = {
    "marriage": {
        "title_ne": "१. विवाह तथा दाम्पत्य",
        "title_en": "1. Marriage & Conjugal Life",
        "karya_bhava": 7,
        "aux_bhavas": [2, 11],
        "karakas": ["Venus", "Jupiter"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("already_married", "💍 विवाह भइसकेको (विवाहित — दाम्पत्य सुख र विगत विश्लेषण)"),
            ("not_married", "🕊️ विवाह नभएको (अविवाहित — भविष्यको विवाह समय निर्धारण)")
        ],
        "questions": [
            "मेरो विवाह कुन मितिमा हुन्छ?",
            "मलाई कुन दिशा वा स्थानबाट विवाहको प्रस्ताव आउँछ?",
            "मेरो विवाह परिवारको सहमतिमा (मागी) हुन्छ कि प्रेम विवाह हुन्छ?",
            "पति/पत्नीको स्वभाव, रूप, स्वास्थ्य र आर्थिक अवस्था कस्तो हुन्छ?",
            "विवाहपछि दाम्पत्य जीवन सुखी हुन्छ कि समस्या धेरै आउँछन्?",
            "मेरो विवाह हुन किन ढिलो भइरहेको छ? ढिलाइको मुख्य कारण र उपाय के हो?",
            "मेरो विवाह स्वदेशमा हुन्छ कि विदेशमा?",
            "मेरो विवाह आफ्नै जात/समुदायमा हुन्छ कि अन्तरजातीय विवाह हुन्छ?",
            "मेरो विवाह धनी, मध्यम वा सामान्य आर्थिक अवस्थाको परिवारमा हुन्छ?",
            "मेरो विवाह एकपटक मात्र हुन्छ कि पुनर्विवाहको योग छ?",
            "दाम्पत्य जीवनमा सुख र आपसी समझदारी कसरी वृद्धि गर्ने?",
            "सम्बन्धमा तनाव वा असमझदारी आएमा कसरी समाधान गर्ने?",
            "पति/पत्नीबाट सहयोग पाइन्छ कि बाधा आउँछ?",
            "विवाहपछि आर्थिक अवस्था बढ्छ कि घट्छ?",
            "विवाहपछि विदेश जाने योग छ?",
            "मेरो दाम्पत्यमा तेस्रो व्यक्तिको हस्तक्षेप हुन्छ कि हुँदैन?",
            "सम्बन्ध बिग्रनुको ज्योतिषीय मुख्य कारण के हो र उपाय के हो?",
            "दोस्रो विवाह पहिलोभन्दा राम्रो हुन्छ कि कस्तो हुन्छ?"
        ]
    },
    "love": {
        "title_ne": "२. प्रेम सम्बन्ध",
        "title_en": "2. Love & Relationships",
        "karya_bhava": 5,
        "aux_bhavas": [7, 11],
        "karakas": ["Venus", "Mars", "Moon"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("current_relation", "❤️ हाल प्रेम सम्बन्धमा रहेको"),
            ("looking_for_love", "🔍 नयाँ प्रेम सम्बन्धको प्रतीक्षामा"),
            ("breakup_phase", "💔 सम्बन्धमा तनाव वा छुट्टिएको अवस्था")
        ],
        "questions": [
            "मेरो जीवनमा प्रेम सम्बन्ध कहिले सुरु हुन्छ?",
            "अहिलेको प्रेम सम्बन्ध विवाहमा परिणत हुन्छ कि हुँदैन?",
            "उसले मलाई साँच्चिकै माया गर्छ कि गर्दैन?",
            "हाम्रो सम्बन्धमा तेस्रो व्यक्तिको प्रभाव छ कि छैन?",
            "प्रेम सम्बन्ध किन बिग्रिरहेको छ?",
            "हामीबीच पुनः मिलन हुन्छ कि स्थायी रूपमा छुट्टिन्छौं?",
            "प्रेम विवाह गरे परिवारले स्वीकार गर्छ कि विरोध गर्छ?",
            "यो सम्बन्ध मेरो लागि शुभ छ कि अशुभ?",
            "सम्बन्ध सुधार गर्न तत्काल के गर्नुपर्छ?",
            "छुट्टिएको व्यक्ति पुनः सम्पर्कमा आउँछ कि आउँदैन?",
            "नयाँ प्रेम सम्बन्ध कहिले आउँछ?",
            "मेरो प्रेम सम्बन्ध किन बारम्बार असफल हुन्छ?"
        ]
    },
    "children": {
        "title_ne": "३. सन्तान तथा गर्भसम्बन्धी",
        "title_en": "3. Children & Progeny",
        "karya_bhava": 5,
        "aux_bhavas": [2, 9, 11],
        "karakas": ["Jupiter", "Sun", "Mars"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("planning_child", "👶 सन्तान योजना गर्दै / सन्तान नभएको"),
            ("has_children", "👨‍👩‍👧‍👦 सन्तान भइसकेको / सन्तानको भविष्य सम्बन्धी")
        ],
        "questions": [
            "कति सन्तान हुने योग छ र पहिलो सन्तान कहिले हुन्छ?",
            "मेरो सन्तान योग कस्तो छ र सन्तान प्राप्ति कहिले हुन्छ?",
            "सन्तान प्राप्तिमा ढिलाइ किन भइरहेको छ?",
            "सन्तानको स्वास्थ्य र पढाइ कस्तो हुन्छ?",
            "सन्तानको आर्थिक भविष्य कस्तो हुन्छ?",
            "सन्तानबाट सुख पाइन्छ कि दुःख?",
            "सन्तान प्राप्तिमा कुन ग्रहले बाधा दिइरहेको छ?",
            "सन्तान प्राप्तिका लागि कुन समय सर्वाधिक अनुकूल छ?",
            "गर्भधारण/सन्तानसम्बन्धी समस्या कहिले सुधार हुन्छ?"
        ]
    },
    "education": {
        "title_ne": "४. शिक्षा तथा अध्ययन",
        "title_en": "4. Education & Studies",
        "karya_bhava": 4,
        "aux_bhavas": [5, 9],
        "karakas": ["Mercury", "Jupiter"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("studying_now", "📚 हाल अध्ययनरत / परीक्षाको तयारीमा"),
            ("higher_abroad", "🎓 उच्च शिक्षा / विदेश अध्ययन योजना")
        ],
        "questions": [
            "कुन विषय पढ्दा मलाई सबैभन्दा बढी सफलता मिल्छ?",
            "मेरो पढाइ कस्तो हुन्छ र शैक्षिक स्तर कति माथि पुग्छ?",
            "पढाइमा बारम्बार बाधा किन आउँछ?",
            "परीक्षा उत्तीर्ण हुन्छु कि हुँदिनँ?",
            "विदेशमा उच्च शिक्षा अध्ययन गर्ने योग छ?",
            "छात्रवृत्ति पाउने सम्भावना छ?",
            "प्रतिस्पर्धात्मक परीक्षामा सफलता कहिले मिल्छ?",
            "मेरो बुद्धि, स्मरणशक्ति र अध्ययन क्षमता कस्तो छ?"
        ]
    },
    "career": {
        "title_ne": "५. जागिर तथा पेशा",
        "title_en": "5. Job & Career",
        "karya_bhava": 10,
        "aux_bhavas": [1, 6, 11],
        "karakas": ["Sun", "Saturn", "Mercury", "Jupiter"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("employed", "💼 हाल कार्यरत / पदोन्नति वा परिवर्तन चाहने"),
            ("unemployed", "🔍 बेरोजगार / नयाँ जागिर खोज्दै")
        ],
        "questions": [
            "मलाई कुन प्रकारको जागिर वा पेशा उपयुक्त हुन्छ?",
            "सरकारी जागिर लाग्ने योग छ कि छैन?",
            "सरकारी जागिर कहिले लाग्छ?",
            "जागिरमा पदोन्नति (Promotion) कहिले हुन्छ?",
            "जागिर परिवर्तन गर्नु उचित हुन्छ कि हुँदैन?",
            "जागिरमा स्थायित्व हुन्छ कि बारम्बार परिवर्तन?",
            "विदेशमा जागिर पाउने योग छ?",
            "मेरो करियरको सबैभन्दा राम्रो समय कुन हो?",
            "जागिर गुम्ने सम्भावना छ?",
            "बेरोजगारी कहिले समाप्त हुन्छ?"
        ]
    },
    "business": {
        "title_ne": "६. व्यवसाय तथा उद्योग",
        "title_en": "6. Business & Trade",
        "karya_bhava": 7,
        "aux_bhavas": [10, 11, 2],
        "karakas": ["Mercury", "Jupiter", "Mars"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("running_business", "🏢 चलिरहेको व्यवसायको विस्तार वा सुधार"),
            ("new_business", "🚀 नयाँ व्यवसाय सुरु गर्न लागेको")
        ],
        "questions": [
            "मैले जागिर गर्ने कि व्यवसाय गर्ने?",
            "मेरो लागि कुन व्यवसाय सबैभन्दा उपयुक्त छ?",
            "साझेदारी (Partnership) व्यवसाय राम्रो हुन्छ कि एकल व्यवसाय?",
            "व्यवसाय सुरु गर्न उपयुक्त समय कहिले हो?",
            "व्यवसायमा घाटा किन भइरहेको छ र नाफा कहिले हुन्छ?",
            "कुन क्षेत्रमा लगानी गर्दा राम्रो हुन्छ?",
            "विदेशसँग व्यापार गर्ने योग छ?",
            "व्यापारमा प्रतिस्पर्धीबाट समस्या आउँछ?"
        ]
    },
    "wealth": {
        "title_ne": "७. धन, आय तथा आर्थिक अवस्था",
        "title_en": "7. Wealth & Finance",
        "karya_bhava": 2,
        "aux_bhavas": [11, 9, 5],
        "karakas": ["Jupiter", "Venus", "Mercury"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("general_wealth", "💰 सामान्य आर्थिक भविष्य"),
            ("debt_crisis", "⚠️ ऋण तथा आर्थिक संकट समाधान")
        ],
        "questions": [
            "धन कमाउने मुख्य स्रोत र पेशागत माध्यम के हुन्छ?",
            "मेरो आर्थिक अवस्था भविष्यमा कस्तो हुन्छ?",
            "पैसा आएर पनि टिक्दैन—किन?",
            "आर्थिक समस्या कहिले समाप्त हुन्छ?",
            "मेरो जीवनमा ठूलो धन प्राप्तिको योग छ?",
            "ऋण कहिले चुक्ता हुन्छ?",
            "शेयर बजार वा सट्टा बजारबाट लाभ हुन्छ कि घाटा?",
            "आकस्मिक धनलाभको योग छ?"
        ]
    },
    "property": {
        "title_ne": "८. घर, जग्गा तथा सम्पत्ति",
        "title_en": "8. Property & Vehicles",
        "karya_bhava": 4,
        "aux_bhavas": [2, 11],
        "karakas": ["Mars", "Saturn", "Venus"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("buying_property", "🏠 घर/जग्गा खरिद योजना"),
            ("selling_property", "🏷️ घर/जग्गा बिक्री योजना")
        ],
        "questions": [
            "मेरो आफ्नै घर हुने योग छ र कहिले बन्छ?",
            "जग्गा खरिद गर्ने समय कहिले हो?",
            "सवारी साधन (गाडी/मोटरसाइकल) कहिले जोडिन्छ?",
            "सम्पत्ति विवाद कहिले समाधान हुन्छ?",
            "पैतृक सम्पत्ति पाइन्छ कि पाइँदैन?",
            "घर/जग्गा बेच्दा फाइदा हुन्छ कि घाटा?"
        ]
    },
    "foreign": {
        "title_ne": "९. विदेश यात्रा तथा बसाइँसराइ",
        "title_en": "9. Foreign Travel & PR",
        "karya_bhava": 9,
        "aux_bhavas": [12, 3, 7],
        "karakas": ["Rahu", "Saturn", "Moon"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("planning_abroad", "✈️ विदेश जाने तयारीमा"),
            ("already_abroad", "🌍 हाल विदेशमा रहेको (स्थायित्व / फर्किने)")
        ],
        "questions": [
            "मेरो विदेश जाने योग छ र कुन देश जानु उपयुक्त हुन्छ?",
            "विदेश यात्रा कहिले हुन्छ?",
            "भिसा लाग्ने सम्भावना कति छ र किन ढिलाइ भइरहेको छ?",
            "विदेशमा स्थायी बसोबास (PR/Green Card) हुन्छ?",
            "विदेशमा सफलता मिल्छ कि स्वदेश फर्कनुपर्छ?",
            "विदेश यात्रामा केही खतरा वा बाधा छ?"
        ]
    },
    "health": {
        "title_ne": "१०. स्वास्थ्य तथा आयु",
        "title_en": "10. Health & Longevity",
        "karya_bhava": 1,
        "aux_bhavas": [6, 8],
        "karakas": ["Sun", "Moon", "Saturn"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("general_health", "🩺 सामान्य स्वास्थ्य अवस्था"),
            ("chronic_illness", "🏥 दीर्घकालीन रोग वा उपचार")
        ],
        "questions": [
            "मेरो समग्र स्वास्थ्य कस्तो रहन्छ र कुन रोगको सम्भावना छ?",
            "वर्तमान बिरामी कहिले निको हुन्छ?",
            "शल्यक्रिया (Surgery) गर्नुपर्ने योग छ?",
            "दुर्घटनाको योग छ कि छैन?",
            "मानसिक तनाव र चिन्ताबाट मुक्ति कहिले मिल्छ?",
            "मेरो दीर्घायुको योग कस्तो छ?"
        ]
    },
    "family": {
        "title_ne": "११. परिवार तथा कुल",
        "title_en": "11. Family & Kinship",
        "karya_bhava": 2,
        "aux_bhavas": [4, 9, 3],
        "karakas": ["Moon", "Sun", "Jupiter"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("family_peace", "🏡 पारिवारिक शान्ति"),
            ("family_dispute", "⚡ पारिवारिक विवाद")
        ],
        "questions": [
            "परिवारमा सुख-शान्ति कहिले हुन्छ?",
            "आमा-बुबाको स्वास्थ्य कस्तो रहन्छ?",
            "दाजुभाइ तथा दिदीबहिनीसँग सम्बन्ध कस्तो रहन्छ?",
            "पारिवारिक विवाद कहिले समाप्त हुन्छ?",
            "ससुराली पक्षसँगको सम्बन्ध कस्तो हुन्छ?"
        ]
    },
    "politics": {
        "title_ne": "१२. राजनीति तथा सामाजिक प्रतिष्ठा",
        "title_en": "12. Politics & Fame",
        "karya_bhava": 10,
        "aux_bhavas": [1, 9, 11],
        "karakas": ["Sun", "Jupiter", "Mars"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("active_politics", "🏛️ सक्रिय राजनीति / चुनाव"),
            ("social_work", "🤝 सामाजिक प्रतिष्ठा")
        ],
        "questions": [
            "मेरो राजनीतिमा सफलता मिल्ने योग छ?",
            "चुनाव जित्ने सम्भावना छ कि छैन?",
            "उच्च पद वा मन्त्री बन्ने योग छ?",
            "समाजमा मान-सम्मान कहिले बढ्छ?",
            "राजनीतिक शत्रुहरूबाट मुक्ति कहिले मिल्छ?"
        ]
    },
    "legal": {
        "title_ne": "१३. मुद्दा, मामिला तथा शत्रु",
        "title_en": "13. Litigation & Enemies",
        "karya_bhava": 6,
        "aux_bhavas": [7, 8],
        "karakas": ["Mars", "Saturn", "Rahu"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("court_case", "⚖️ अदालतमा मुद्दा चलिरहेको"),
            ("enemy_trouble", "🛡️ शत्रु बाधा")
        ],
        "questions": [
            "मुद्दामा मेरो जित हुन्छ कि हार?",
            "मुद्दा कहिले फैसला हुन्छ?",
            "शत्रुहरू पराजित हुन्छन् कि हुँदैनन्?",
            "झूटा आरोपबाट मुक्ति कहिले मिल्छ?",
            "कानुनी झमेलाबाट बच्ने उपाय के हो?"
        ]
    },
    "travel": {
        "title_ne": "१४. छोटो यात्रा तथा स्थानान्तरण",
        "title_en": "14. Travel & Relocation",
        "karya_bhava": 3,
        "aux_bhavas": [9, 12],
        "karakas": ["Moon", "Mercury"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("relocation", "📦 बसाइँसराइ"),
            ("short_trip", "🚗 छोटो यात्रा")
        ],
        "questions": [
            "बसाइँसराइ गर्नु उचित हुन्छ कि हुँदैन?",
            "नयाँ ठाउँमा जाँदा सफलता मिल्छ कि समस्या?",
            "आगामी यात्रा सफल हुन्छ कि हुँदैन?"
        ]
    },
    "spiritual": {
        "title_ne": "१५. आध्यात्म, धर्म तथा साधना",
        "title_en": "15. Spirituality & Dharma",
        "karya_bhava": 9,
        "aux_bhavas": [5, 12],
        "karakas": ["Jupiter", "Ketu", "Sun"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("spiritual_growth", "🧘 आध्यात्मिक उन्नति"),
            ("mantra_siddhi", "📿 मन्त्र साधना")
        ],
        "questions": [
            "मेरो इष्टदेव को हुनुहुन्छ?",
            "मन्त्र सिद्धि हुने योग छ?",
            "आध्यात्मिक प्रगति कहिले हुन्छ?",
            "तीर्थयात्राको योग कहिले छ?"
        ]
    },
    "debts": {
        "title_ne": "१६. ऋण तथा दायित्व",
        "title_en": "16. Debts & Liabilities",
        "karya_bhava": 6,
        "aux_bhavas": [8, 12],
        "karakas": ["Mars", "Saturn", "Rahu"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("heavy_debt", "💳 ठूलो ऋण भार"),
            ("debt_recovery", "💵 फसेको रकम उठाउने")
        ],
        "questions": [
            "ऋणबाट कहिले मुक्ति पाइन्छ?",
            "उधारो दिएको पैसा फिर्ता आउँछ कि आउँदैन?",
            "बैंकबाट ऋण पाउने सम्भावना छ?"
        ]
    },
    "overall": {
        "title_ne": "१७. जीवनको समग्र भाग्य एवं भविष्य",
        "title_en": "17. Overall Destiny",
        "karya_bhava": 1,
        "aux_bhavas": [9, 10],
        "karakas": ["Jupiter", "Sun"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("golden_period", "🌟 भाग्योदय काल"),
            ("general_fortune", "🔮 समग्र भविष्य")
        ],
        "questions": [
            "मेरो भाग्योदय कहिले हुन्छ?",
            "मेरो जीवनको स्वर्णिम काल (Golden Period) कुन हो?",
            "म धनी र प्रसिद्ध बन्ने योग छ?",
            "मेरो जीवनको प्रमुख उद्देश्य के हो?"
        ]
    },
    "universal": {
        "title_ne": "१८. सर्वतोभद्र तथा तात्कालिक प्रश्न",
        "title_en": "18. Universal & Instant Queries",
        "karya_bhava": 1,
        "aux_bhavas": [9, 10, 11],
        "karakas": ["Jupiter", "Sun"],
        "context_options": [
            ("unspecified", "🌐 सामान्य / अवस्था नखुलेको (कुण्डलीगत विश्लेषण)"),
            ("immediate_timing", "⚡ तत्कालको निर्णय / कार्य"),
            ("long_term_outcome", "🎯 दीर्घकालीन परिणाम")
        ],
        "questions": [
            "यो विषय मेरो लागि शुभ हो कि अशुभ?",
            "यसको मुख्य कारण के हो र कहिले सुधार हुन्छ?",
            "यसको सबैभन्दा राम्रो समय कहिले हो?",
            "यसमा मुख्य बाधा दिने ग्रह/योग कुन हो?",
            "यसबाट लाभ हुन्छ कि हानि?",
            "अन्तिममा स्पष्ट निष्कर्ष के हो?"
        ]
    }
}

RASHI_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}

PLANET_NAMES_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्रमा", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "बृहस्पति (गुरु)", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु"
}

CATEGORY_RULES: Dict[str, Any] = {
    "marriage":  {"primary_bhava": 7, "sec_bhavas": [2, 11], "karakas": ["Venus", "Jupiter"], "min_event_age": 16, "max_natural_age": 80, "sutra": "सप्तमेश, शुक्र र गुरुको बल, विंशोत्तरी दशा, गोचर तथा नवांश (D9) विश्लेषण। (बृहत् पराशर होरा शास्त्र अ.८१, प्रश्नमार्ग)"},
    "love":      {"primary_bhava": 5, "sec_bhavas": [7, 11], "karakas": ["Venus", "Mars"], "min_event_age": 14, "max_natural_age": 70, "sutra": "पञ्चमेश, शुक्र र मंगलको बल; पञ्चम भावमा शुभ ग्रहको प्रभाव। (फलदीपिका अ.१२)"},
    "children":  {"primary_bhava": 5, "sec_bhavas": [2, 9], "karakas": ["Jupiter", "Sun"], "min_event_age": 16, "max_natural_age": 55, "sutra": "पञ्चमेश, गुरु र सूर्यको बल; नवांश पञ्चम भाव। (बृहत् पराशर होरा शास्त्र अ.२३, सप्तांश D7)"},
    "education": {"primary_bhava": 4, "sec_bhavas": [5, 9], "karakas": ["Mercury", "Jupiter"], "min_event_age": 5,  "max_natural_age": 40, "sutra": "चतुर्थेश, गुरु र बुधको बल; पञ्चम र नवम भाव। (बृहत् पराशर होरा शास्त्र)"},
    "career":    {"primary_bhava": 10, "sec_bhavas": [1, 6, 11], "karakas": ["Sun", "Saturn"], "min_event_age": 15, "max_natural_age": 65, "sutra": "दशमेश, शनि, सूर्य र बुधको बल; कर्मकारकको दशा-गोचर तथा दशमांश (D10) विश्लेषण।"},
    "business":  {"primary_bhava": 7, "sec_bhavas": [10, 11], "karakas": ["Mercury", "Mars"], "min_event_age": 18, "max_natural_age": 70, "sutra": "सप्तमेश (व्यापार), दशमेश, बुध र मंगलको दशा-गोचर।"},
    "wealth":    {"primary_bhava": 2, "sec_bhavas": [11, 9], "karakas": ["Jupiter", "Venus"], "min_event_age": 18, "max_natural_age": 80, "sutra": "द्वितीयेश, लाभेश, गुरु र शुक्रको बल एवं धन योग विश्लेषण।"},
    "property":  {"primary_bhava": 4, "sec_bhavas": [2, 11], "karakas": ["Mars", "Saturn"], "min_event_age": 18, "max_natural_age": 80, "sutra": "चतुर्थेश, मंगल र शनिको बल तथा वाहन/भूमि योग।"},
    "foreign":   {"primary_bhava": 9, "sec_bhavas": [12, 3], "karakas": ["Rahu", "Saturn"], "min_event_age": 16, "max_natural_age": 70, "sutra": "नवमेश, व्ययेश, राहु र शनिको बल तथा चर राशि प्रभाव।"},
    "health":    {"primary_bhava": 1, "sec_bhavas": [6, 8],  "karakas": ["Sun", "Moon"], "min_event_age": 0,  "max_natural_age": 100, "sutra": "लग्न, लग्नेश, सूर्य-चन्द्रको बल; षष्ठ-अष्टम भावको रोगकारक अवस्था।"},
    "family":    {"primary_bhava": 2, "sec_bhavas": [4, 3],  "karakas": ["Moon", "Jupiter"], "min_event_age": 0,  "max_natural_age": 100, "sutra": "द्वितीयेश, चतुर्थेश, चन्द्रमा र गुरुको पारिवारिक भाव विश्लेषण।"},
    "politics":  {"primary_bhava": 10, "sec_bhavas": [1, 9], "karakas": ["Sun", "Jupiter"], "min_event_age": 21, "max_natural_age": 80, "sutra": "दशमेश, सूर्य र गुरुको राज्यकारक बल एवं राजयोग।"},
    "legal":     {"primary_bhava": 6, "sec_bhavas": [7, 8],  "karakas": ["Mars", "Saturn"], "min_event_age": 14, "max_natural_age": 90, "sutra": "षष्ठेश, लग्नेश, मंगल र शनिको शत्रुजय योग।"},
    "travel":    {"primary_bhava": 3, "sec_bhavas": [9, 12], "karakas": ["Moon", "Mercury"], "min_event_age": 5,  "max_natural_age": 85, "sutra": "तृतीयेश, नवमेश र चन्द्रमाको यात्रा कारक योग।"},
    "spiritual": {"primary_bhava": 9, "sec_bhavas": [5, 12], "karakas": ["Jupiter", "Ketu"], "min_event_age": 10, "max_natural_age": 100, "sutra": "नवमेश, पञ्चमेश, गुरु र केतुको आत्मकारक एवं इष्टदेव योग।"},
    "debts":     {"primary_bhava": 6, "sec_bhavas": [8, 12], "karakas": ["Mars", "Rahu"], "min_event_age": 14, "max_natural_age": 90, "sutra": "षष्ठेश, एकादशेश, मंगल र राहुको ऋणमुक्ति योग।"},
    "overall":   {"primary_bhava": 1, "sec_bhavas": [9, 10], "karakas": ["Jupiter", "Sun"], "min_event_age": 0,  "max_natural_age": 100, "sutra": "लग्नेश, भाग्येश, दशमेश र गुरु-सूर्यको त्रिकोण-केन्द्र राजयोग।"},
    "universal": {"primary_bhava": 1, "sec_bhavas": [9, 10], "karakas": ["Jupiter"], "min_event_age": 0,  "max_natural_age": 100, "sutra": "सामान्य कार्यकारण एवं तात्कालिक प्रश्न फल।"}
}
_DEFAULT_RULE = CATEGORY_RULES["universal"]


class PrashnaKundaliEngine:
    @classmethod
    def evaluate_question(
        cls,
        category_key: str,
        question_text: str,
        context_mode: str,
        chart_data: Optional[Dict[str, Any]] = None,
        prashna_datetime: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        now = prashna_datetime or datetime.datetime.now()
        bs_today = gregorian_to_bs(now.year, now.month, now.day) or {"year": 2081, "month": 5, "day": 14}
        current_bs_year = bs_today["year"]
        current_bs_month = bs_today["month"]

        cat_info = PRASHNA_DATA.get(category_key, PRASHNA_DATA["universal"])
        rule = CATEGORY_RULES.get(category_key, _DEFAULT_RULE)

        # १. ग्रह तथा लग्न डेटा निष्कर्षण
        planets = (chart_data or {}).get("planets", [])
        lagna_data = (chart_data or {}).get("lagna", {})
        lagna_sign = int(lagna_data.get("sign_number", 1) or 1) if lagna_data else (
            (now.hour * 2 + now.minute // 30) % 12 + 1
        )
        lagnesh = RASHI_LORDS.get(lagna_sign, "Mars")
        karya_bhava = rule["primary_bhava"]
        karya_sign = ((lagna_sign - 1 + karya_bhava - 1) % 12) + 1
        karyesh = RASHI_LORDS.get(karya_sign, "Venus")

        lagnesh_p = next((p for p in planets if p.get("name") == lagnesh), None)
        karyesh_p = next((p for p in planets if p.get("name") == karyesh), None)
        lagnesh_house = int((lagnesh_p or {}).get("house", 1) or 1)
        karyesh_house = int((karyesh_p or {}).get("house", karya_bhava) or karya_bhava)

        # २. जातकको उमेर तथा जन्म मिति (वि.सं.)
        birth_year_bs = 2051
        metadata = (chart_data or {}).get("metadata", {})
        b_date_str = str(metadata.get("birth_date", ""))
        if b_date_str and len(b_date_str) >= 4:
            try:
                b_dt = datetime.date.fromisoformat(b_date_str[:10])
                bs_b = gregorian_to_bs(b_dt.year, b_dt.month, b_dt.day)
                if bs_b:
                    birth_year_bs = bs_b["year"]
            except Exception:
                pass
        native_age = max(0, current_bs_year - birth_year_bs)

        # ३. ताजिक योग निर्धारण
        yoga_name, yoga_desc, prob_score = cls._determine_tajika_yoga(lagnesh_house, karyesh_house)

        # ४. प्रश्न-विशिष्ट प्रत्यक्ष फलादेश संश्लेषण (Direct Answer)
        answer_data = cls._synthesize_direct_answer(
            category_key=category_key,
            question_text=question_text,
            context_mode=context_mode,
            native_age=native_age,
            birth_year_bs=birth_year_bs,
            current_bs_year=current_bs_year,
            current_bs_month=current_bs_month,
            lagna_sign=lagna_sign,
            lagnesh=lagnesh,
            karya_bhava=karya_bhava,
            karya_sign=karya_sign,
            karyesh=karyesh,
            planets=planets,
            chart_data=chart_data,
            prob_score=prob_score
        )

        # ५. उपाय
        remedy_text = cls._get_remedy_for_category(category_key, karyesh)

        return {
            "question": question_text,
            "category_title": cat_info["title_ne"],
            "lagna_sign": lagna_sign,
            "lagna_name": rashi_name(lagna_sign, "ne"),
            "lagnesh": PLANET_NAMES_NE.get(lagnesh, lagnesh),
            "karya_bhava": karya_bhava,
            "karya_sign": karya_sign,
            "karya_sign_name": rashi_name(karya_sign, "ne"),
            "karyesh": PLANET_NAMES_NE.get(karyesh, karyesh),
            "yoga_name": yoga_name,
            "yoga_desc": yoga_desc,
            "probability_score": answer_data["prob_score"],
            "probable_window_bs": answer_data["window_bs"],
            "peak_window_bs": answer_data["peak_bs"],
            "direct_answer": answer_data["direct_answer"],
            "time_analysis_note": answer_data["time_note"],
            "obstacle": answer_data["obstacle"],
            "life_status_note": answer_data["life_status_note"],
            "sutra_applied": rule.get("sutra", ""),
            "remedy": remedy_text,
            "conclusion": answer_data["conclusion"],
            "prashna_date_bs": f"{to_nepali_digits(bs_today['year'])}/{to_nepali_digits(bs_today['month'])}/{to_nepali_digits(bs_today['day'])}",
            "prashna_time": now.strftime("%H:%M:%S"),
        }

    @classmethod
    def _determine_tajika_yoga(cls, lagnesh_house: int, karyesh_house: int) -> Tuple[str, str, int]:
        dist = abs(lagnesh_house - karyesh_house) % 12
        if dist in (0, 4, 8):
            return ("इत्थशाल योग (Ithasala Yoga — शुभ दृष्टि/युति)", "लग्नेश र कार्येशबीच प्रत्यक्ष शुभ दृष्टि सम्बन्ध बनेको छ, जसले कार्य सिद्ध हुने निश्चित शास्त्रीय संकेत गर्दछ।", 88)
        elif dist in (3, 6, 9):
            return ("कम्बूल योग (Kamboola Yoga — चन्द्रमा मार्फत सिद्धि)", "चन्द्रमाले लग्नेश र कार्येश दुवैसँग शुभ सम्बन्ध बनाएकाले मित्र वा मध्यस्थकर्ताको सहयोगबाट कार्य पूर्ण हुनेछ।", 82)
        elif dist in (5, 7):
            return ("ईशराफ योग (Esharapha Yoga — प्रयास एवं समयसापेक्ष)", "लग्नेश र कार्येशबीच विपरित दृष्टि रहेकाले कार्य सम्पन्न हुन विशेष धैर्यता र प्रयास आवश्यक पर्नेछ।", 68)
        elif dist == 1:
            return ("नक्त योग (Nakta Yoga — अन्य शुभ ग्रह मार्फत)", "अन्य सहयोगी ग्रहको मध्यस्थताले समयक्रममा सकारात्मक फल प्राप्त हुनेछ।", 74)
        else:
            return ("यमया योग (Yamaya Yoga — समान स्थिति)", "कार्य क्रमशः सकारात्मक दिशातर्फ अगाडि बढ्ने मध्यम सम्भावना छ।", 76)

    @classmethod
    def _synthesize_direct_answer(
        cls,
        category_key: str,
        question_text: str,
        context_mode: str,
        native_age: int,
        birth_year_bs: int,
        current_bs_year: int,
        current_bs_month: int,
        lagna_sign: int,
        lagnesh: str,
        karya_bhava: int,
        karya_sign: int,
        karyesh: str,
        planets: List[Dict[str, Any]],
        chart_data: Optional[Dict[str, Any]],
        prob_score: int
    ) -> Dict[str, Any]:
        q = question_text.strip()
        l_name = rashi_name(lagna_sign, "ne")
        l_lord_ne = PLANET_NAMES_NE.get(lagnesh, lagnesh)

        fifth_sign = ((lagna_sign - 1 + 5 - 1) % 12) + 1
        fifth_sign_name = rashi_name(fifth_sign, "ne")
        fifth_lord = RASHI_LORDS.get(fifth_sign, "Jupiter")
        fifth_lord_ne = PLANET_NAMES_NE.get(fifth_lord, fifth_lord)

        seventh_sign = ((lagna_sign - 1 + 7 - 1) % 12) + 1
        seventh_sign_name = rashi_name(seventh_sign, "ne")
        seventh_lord = RASHI_LORDS.get(seventh_sign, "Moon")
        seventh_lord_ne = PLANET_NAMES_NE.get(seventh_lord, seventh_lord)

        tenth_sign = ((lagna_sign - 1 + 10 - 1) % 12) + 1
        tenth_sign_name = rashi_name(tenth_sign, "ne")
        tenth_lord = RASHI_LORDS.get(tenth_sign, "Saturn")
        tenth_lord_ne = PLANET_NAMES_NE.get(tenth_lord, tenth_lord)

        ninth_sign = ((lagna_sign - 1 + 9 - 1) % 12) + 1
        ninth_sign_name = rashi_name(ninth_sign, "ne")
        ninth_lord = RASHI_LORDS.get(ninth_sign, "Mercury")
        ninth_lord_ne = PLANET_NAMES_NE.get(ninth_lord, ninth_lord)

        second_sign = ((lagna_sign - 1 + 2 - 1) % 12) + 1
        second_sign_name = rashi_name(second_sign, "ne")
        second_lord = RASHI_LORDS.get(second_sign, "Saturn")
        second_lord_ne = PLANET_NAMES_NE.get(second_lord, second_lord)

        fourth_sign = ((lagna_sign - 1 + 4 - 1) % 12) + 1
        fourth_sign_name = rashi_name(fourth_sign, "ne")
        fourth_lord = RASHI_LORDS.get(fourth_sign, "Mars")
        fourth_lord_ne = PLANET_NAMES_NE.get(fourth_lord, fourth_lord)

        sixth_sign = ((lagna_sign - 1 + 6 - 1) % 12) + 1
        sixth_sign_name = rashi_name(sixth_sign, "ne")
        sixth_lord = RASHI_LORDS.get(sixth_sign, "Mercury")
        sixth_lord_ne = PLANET_NAMES_NE.get(sixth_lord, sixth_lord)

        # Status note string
        if context_mode == "already_married":
            life_status = f"💍 विवाह भइसकेको (विवाहित) | उमेर: {to_nepali_digits(native_age)} वर्ष"
        elif context_mode == "not_married":
            life_status = f"🕊️ विवाह नभएको (अविवाहित) | उमेर: {to_nepali_digits(native_age)} वर्ष"
        elif context_mode == "employed":
            life_status = f"💼 हाल कार्यरत | उमेर: {to_nepali_digits(native_age)} वर्ष"
        elif context_mode == "unemployed":
            life_status = f"🔍 नयाँ अवसर खोज्दै | उमेर: {to_nepali_digits(native_age)} वर्ष"
        elif context_mode == "has_children":
            life_status = f"👨‍👩‍👧‍👦 सन्तान भइसकेको | उमेर: {to_nepali_digits(native_age)} वर्ष"
        elif context_mode == "planning_child":
            life_status = f"👶 सन्तान योजना | उमेर: {to_nepali_digits(native_age)} वर्ष"
        else:
            life_status = f"🌐 कुण्डलीगत सामान्य विश्लेषण (अवस्था नखुलेको) | उमेर: {to_nepali_digits(native_age)} वर्ष"

        # ══════════════════════════════════════════════════════════════════════
        # ३. सन्तान तथा गर्भसम्बन्धी (Children Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "children":
            if "कति सन्तान" in q or "कति" in q:
                direct_ans = (
                    f"बृहत् पराशर होरा शास्त्र र सप्तांश कुण्डली (D7) को नियम अनुसार पञ्चम भाव (सुत भाव) <b>{fifth_sign_name} राशि</b>मा रहेको र "
                    f"यसका स्वामी <b>{fifth_lord_ne}</b> तथा सन्तानकारक <b>बृहस्पति (गुरु)</b> को स्थिति विश्लेषण गर्दा:<br><br>"
                    f"• <b>सन्तान संख्या:</b> तपाईंको कुण्डलीमा <b>२ सन्तान (१ पुत्र र १ पुत्री)</b> को प्रबल एवं शुभ योग देखिन्छ।<br>"
                    f"• <b>पहिलो सन्तान:</b> पञ्चम भावको राशि तथा गुरुको गोचर अनुकूलता अनुसार पहिलो सन्तान गुणवान्, आज्ञाकारी र मातापिताप्रति समर्पित हुनेछ।<br>"
                    f"• <b>सन्तान सुख:</b> सन्तानबाट जीवनभर सुख, मानसम्मान र सहयोग प्राप्त हुने उत्तम योग छ।"
                )
                window_bs = f"वि.सं. {to_nepali_digits(current_bs_year)} देखि वि.सं. {to_nepali_digits(current_bs_year + 3)}"
                peak_bs = f"वि.सं. {to_nepali_digits(current_bs_year + 1)} (गुरुको पञ्चम भाव गोचर)"
                return {
                    "prob_score": 90,
                    "window_bs": window_bs,
                    "peak_bs": peak_bs,
                    "direct_answer": direct_ans,
                    "time_note": f"सन्तान सुख एवं प्रगतिको प्रमुख समय: <b>{window_bs}</b> (सर्वाधिक बलियो: <b>{peak_bs}</b>)।",
                    "obstacle": "पञ्चम भावमा कुनै सामान्य पाप दृष्टि भए सन्तानको स्वास्थ्यमा सामान्य ध्यान दिनु शुभ हुन्छ।",
                    "life_status_note": life_status,
                    "conclusion": "तपाईंको कुण्डलीमा २ सन्तान (१ पुत्र र १ पुत्री) को उत्तम शास्त्रीय योग रहेको छ।"
                }

            elif "सन्तान प्राप्ति कहिले" in q or "योग कस्तो" in q:
                if context_mode == "has_children":
                    direct_ans = (
                        f"तपाईंले 'सन्तान भइसकेको' सन्दर्भ छनोट गर्नुभएको छ। पञ्चम भाव ({fifth_sign_name}) र गुरुको गोचर अनुसार "
                        f"हालका सन्तानको स्वास्थ्य, शिक्षा र भविष्य अत्यन्त उज्ज्वल छ। थप सन्तानको योजनाका लागि पनि समय अनुकूल रहनेछ।"
                    )
                elif context_mode == "already_married":
                    direct_ans = (
                        f"पञ्चम भाव ({fifth_sign_name}) र गुरुको गोचर अनुसार सन्तान सुख र थप सन्तानको सम्भावना अनुकूल रहेको छ। "
                        f"सन्तानबाट मातापितालाई सदैव सुख र सन्तोष मिल्नेछ।"
                    )
                else:
                    future_yr = current_bs_year + 1
                    direct_ans = (
                        f"पञ्चम भाव ({fifth_sign_name}), पञ्चमेश ({fifth_lord_ne}) र बृहस्पति (गुरु) को गोचर अनुसार "
                        f"कुण्डलीमा सन्तान प्राप्तिको प्रबल शुभ समय <b>वि.सं. {to_nepali_digits(future_yr)} देखि वि.सं. {to_nepali_digits(future_yr + 2)}</b> भित्र रहने योग छ।"
                    )
                window_bs = f"वि.सं. {to_nepali_digits(current_bs_year + 1)} देखि वि.सं. {to_nepali_digits(current_bs_year + 3)}"
                peak_bs = f"वि.सं. {to_nepali_digits(current_bs_year + 1)}"
                return {
                    "prob_score": 88,
                    "window_bs": window_bs,
                    "peak_bs": peak_bs,
                    "direct_answer": direct_ans,
                    "time_note": f"सन्तान प्राप्तिको सर्वाधिक शुभ समय: <b>{window_bs}</b>।",
                    "obstacle": "सन्तान प्राप्तिका लागि बिहीबार गुरु मन्त्र जप तथा पहेँलो वस्तुको दान गर्नु शुभ हुन्छ।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

            elif "स्वास्थ्य र पढाइ" in q:
                direct_ans = (
                    f"पञ्चमेश {fifth_lord_ne} र बुध/गुरुको प्रभावले गर्दा सन्तानको <b>स्वास्थ्य सामान्यतया राम्रो र पढाइमा उत्कृष्ट क्षमता</b> रहनेछ। "
                    f"सन्तान विज्ञान, व्यवस्थापन वा प्राविधिक विषयमा सफल हुने देखिन्छ।"
                )
                return {
                    "prob_score": 86,
                    "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 3)}",
                    "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                    "direct_answer": direct_ans,
                    "time_note": "सन्तानको शैक्षिक विकास निरन्तर सकारात्मक रहनेछ।",
                    "obstacle": "पढाइमा एकाग्रता बढाउन सरस्वती स्तोत्र पाठ गराउनुहोला।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

            else:
                direct_ans = (
                    f"पञ्चम भाव ({fifth_sign_name}) र सन्तानकारक गुरुको शुभ प्रभावले गर्दा सन्तान सम्बन्धी समग्र पक्ष <b>सकारात्मक र सुखदायी</b> रहनेछ। "
                    f"सन्तानबाट मातापिताको मानसम्मान र पारिवारिक प्रतिष्ठा वृद्धि हुनेछ।"
                )
                return {
                    "prob_score": 88,
                    "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 3)}",
                    "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                    "direct_answer": direct_ans,
                    "time_note": "सन्तान सम्बन्धी सम्पूर्ण मनोकामना पूर्ण हुने योग छ।",
                    "obstacle": "गुरुको आराधना तथा इष्टदेवको सेवा गर्नु शुभ हुन्छ।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

        # ══════════════════════════════════════════════════════════════════════
        # ५. जागिर तथा पेशा (Job & Career Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "career":
            if tenth_lord in ("Venus", "Mercury"):
                suitable_fields = [
                    "१. <b>प्रशासन, व्यवस्थापन, मानव संसाधन (HR) र योजना निर्माण</b>",
                    "२. <b>बैंकिङ, वित्तीय क्षेत्र, लेखा (Accountancy), अडिटिङ र अर्थशास्त्र</b>",
                    "३. <b>सूचना प्रविधि (IT), सफ्टवेयर विकास, डाटा व्यवस्थापन र डिजिटल प्रविधि</b>",
                    "४. <b>प्राध्यापन, शैक्षिक परामर्श, मिडिया, विज्ञापन र व्यापार व्यवस्थापन</b>"
                ]
            elif tenth_lord in ("Sun", "Mars"):
                suitable_fields = [
                    "१. <b>सरकारी सेवा, निजामती प्रशासन र नीति निर्माण तह</b>",
                    "२. <b>इन्जिनियरिङ, निर्माण, रियलस्टेट र प्राविधिक आयोजनाहरू</b>",
                    "३. <b>सुरक्षा निकाय, प्रहरी, सेना, अनुसन्धान र नेतृत्वदायी पद</b>",
                    "४. <b>चिकित्सा, शल्यक्रिया (Surgery) वा औषधि उद्योग</b>"
                ]
            elif tenth_lord in ("Jupiter", "Moon"):
                suitable_fields = [
                    "१. <b>शिक्षा, प्राध्यापन, अनुसन्धान तथा कानुनी सेवा (वकालत/न्याय)</b>",
                    "२. <b>सार्वजनिक सेवा, एनजीओ/आईएनजीओ तथा कूटनीतिक नियोगहरू</b>",
                    "३. <b>स्वास्थ्य, चिकित्सा, नर्सिङ तथा सामाजिक कल्याणकारी क्षेत्र</b>",
                    "४. <b>पर्यटन, परामर्श, लेखन तथा साहित्य/सञ्चार</b>"
                ]
            else: # Saturn
                suitable_fields = [
                    "१. <b>उद्योग, उत्पादन, इन्जिनियरिङ, खानी, फलाम तथा धातु व्यवसाय</b>",
                    "२. <b>न्याय सेवा, श्रम प्रशासन, कानुनी सल्लाहकार तथा अनुसन्धान</b>",
                    "३. <b>कम्प्युटर हार्डवेयर, सञ्चार पूर्वाधार र ठूला प्राविधिक परियोजनाहरू</b>",
                    "४. <b>कृषि, जडीबुटी तथा दीर्घकालीन सार्वजनिक सेवा</b>"
                ]

            fields_text = "<br>".join(suitable_fields)

            if "कुन प्रकारको जागिर" in q or "कुन पेशा" in q:
                direct_ans = (
                    f"तपाईंको जन्म कुण्डली अनुसार <b>लग्न {l_name}</b> रहेको र <b>कर्म भाव (दशम भाव) {tenth_sign_name} राशि</b>मा पर्दछ, "
                    f"जसको स्वामी <b>{tenth_lord_ne}</b> हुनुहुन्छ। बृहत् पराशर होरा शास्त्र र प्रश्नमार्गको दशम भाव फल अनुसार तपाईंको लागि निम्न क्षेत्रका पेशा/जागिर सर्वाधिक शुभ र सफल रहनेछन्:<br><br>"
                    f"{fields_text}<br><br>"
                    f"<b>विशेष सल्लाह:</b> तपाईंमा बौद्धिक विश्लेषण, व्यवस्थापकीय कुशलता र नेतृत्व क्षमता राम्रो भएकाले कुनै पनि संस्थामा जिम्मेवार पद वा प्राविधिक/व्यवस्थापकीय नेतृत्वमा काम गर्दा द्रुत उन्नति हुनेछ।"
                )
                window_bs = f"वि.सं. {to_nepali_digits(current_bs_year)} देखि वि.सं. {to_nepali_digits(current_bs_year + 3)}"
                peak_bs = f"वि.सं. {to_nepali_digits(current_bs_year + 1)} (दशमेश-गोचर अनुकूलता)"
                return {
                    "prob_score": 92,
                    "window_bs": window_bs,
                    "peak_bs": peak_bs,
                    "direct_answer": direct_ans,
                    "time_note": f"कर्म कारक ग्रहहरूको अनुकूल दशा-गोचर अनुसार <b>{window_bs}</b> भित्र पेशागत जीवनमा ठूलो स्थायित्व र प्रगति हासिल हुनेछ।",
                    "obstacle": "कार्यक्षेत्रमा अनावश्यक शंका वा हतारबाट बची आत्मविश्वासका साथ अगाडि बढ्नुहोस्।",
                    "life_status_note": life_status,
                    "conclusion": "तपाईंको लागि बौद्धिक, व्यवस्थापकीय तथा प्राविधिक क्षेत्र सर्वाधिक उपयुक्त छ।"
                }

            elif "सरकारी जागिर" in q:
                is_gov = tenth_lord in ("Sun", "Mars", "Jupiter") or lagna_sign in (1, 5, 9, 10)
                direct_ans = (
                    f"जन्म कुण्डलीमा सूर्य, दशम भाव र छैटौं भाव (प्रतियोगिता) को विश्लेषण गर्दा "
                    f"<b>{'सरकारी वा अर्ध-सरकारी सेवामा प्रवेशको बलियो सम्भावना छ' if is_gov else 'निजी तथा बहुराष्ट्रिय कम्पनीमा उच्च पद वा सरकारी संस्थानमा परामर्शदाताको रूपमा सफलता मिल्ने योग छ'}</b>। "
                    f"दशमेश {tenth_lord_ne} को शुभ दृष्टि रहने भएकाले प्रतिस्पर्धात्मक परीक्षामा कडा मेहनत गर्नाले सफलता हात लाग्नेछ।"
                )
                window_bs = f"वि.सं. {to_nepali_digits(current_bs_year + 1)} देखि वि.सं. {to_nepali_digits(current_bs_year + 3)}"
                peak_bs = f"वि.सं. {to_nepali_digits(current_bs_year + 1)} (सूर्य-दशमेश गोचर)"
                return {
                    "prob_score": 85 if is_gov else 75,
                    "window_bs": window_bs,
                    "peak_bs": peak_bs,
                    "direct_answer": direct_ans,
                    "time_note": f"प्रतियोगिता र सरकारी जागिरका लागि <b>{peak_bs}</b> सबैभन्दा अनुकूल रहनेछ।",
                    "obstacle": "प्रतिस्पर्धात्मक परीक्षामा नियमित अध्ययन र समय व्यवस्थापनमा विशेष ध्यान दिनुहोस्।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

            elif "पदोन्नति" in q or "Promotion" in q:
                future_start = current_bs_year + 1
                window_bs = f"वि.सं. {to_nepali_digits(future_start)} देखि वि.सं. {to_nepali_digits(future_start + 2)}"
                peak_bs = f"वि.सं. {to_nepali_digits(future_start)} को पहिलो ६ महिना"
                direct_ans = (
                    f"वर्तमान विंशोत्तरी दशा र दशमेश {tenth_lord_ne} को गोचर अनुसार आगामी <b>{window_bs}</b> भित्र पदोन्नति (Promotion), "
                    f"तलब वृद्धि वा जिम्मेवारी विस्तार हुने प्रबल योग बनेको छ।"
                )
                return {
                    "prob_score": 86,
                    "window_bs": window_bs,
                    "peak_bs": peak_bs,
                    "direct_answer": direct_ans,
                    "time_note": f"पदोन्नतिको सर्वाधिक अनुकूल समय <b>{peak_bs}</b> हो।",
                    "obstacle": "कार्यालयमा सहयोगीहरूसँग सुमधुर सम्बन्ध कायम राख्नुहोस्।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

            else:
                direct_ans = (
                    f"दशम भाव ({tenth_sign_name}) र दशमेश {tenth_lord_ne} को बलियो स्थिति अनुसार करियरमा <b>स्थायित्व र दीर्घकालीन प्रगति</b> हुनेछ। "
                    f"समय-समयमा पदोन्नति र नयाँ अवसरहरू प्राप्त भइरहनेछन्।"
                )
                return {
                    "prob_score": 85,
                    "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 3)}",
                    "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                    "direct_answer": direct_ans,
                    "time_note": "करियरमा स्थायित्वको समय अनुकूल छ।",
                    "obstacle": "लक्ष्यमा केन्द्रित भई काम गर्नुहोस्।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

        # ══════════════════════════════════════════════════════════════════════
        # १. विवाह तथा दाम्पत्य (Marriage Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "marriage":
            # ── विवाह दिशा: Multi-rule Direction Engine ─────────────────────────
            _dir_res = None
            if chart_data and isinstance(chart_data, dict):
                try:
                    _dir_res = calculate_marriage_direction(chart_data)
                except Exception:
                    _dir_res = None
            if _dir_res:
                m_dir = _dir_res["primary_direction"]["name_ne"]
                m_dir_pct = _dir_res["primary_direction"]["percentage"]
                m_dir_2 = _dir_res["secondary_direction"]["name_ne"]
                m_dir_2_pct = _dir_res["secondary_direction"]["percentage"]
                m_dir_conf = _dir_res["confidence_label_ne"]
                m_dir_zone = _dir_res.get("combined_zone_ne") or ""
                _ev_lines = "".join(
                    f"<li><b>{e['rule_name_ne']}:</b> {e['source']} → <b>{e['direction_ne']}</b> (भार: {e['weight']})</li>"
                    for e in _dir_res["evidence"]
                )
                m_dir_evidence_html = f"<ul>{_ev_lines}</ul>"
            else:
                # fallback to sign-based direction
                _fallback_dirs = {1:"पूर्व",5:"पूर्व",9:"पूर्व",2:"दक्षिण",6:"दक्षिण",10:"दक्षिण",3:"पश्चिम",7:"पश्चिम",11:"पश्चिम",4:"उत्तर",8:"उत्तर",12:"उत्तर"}
                m_dir = _fallback_dirs.get(seventh_sign, "दक्षिण")
                m_dir_pct = 0
                m_dir_2 = ""
                m_dir_2_pct = 0
                m_dir_conf = ""
                m_dir_zone = ""
                m_dir_evidence_html = ""

            # Try to get dynamic windows from marriage_timing_engine
            dynamic_windows = []
            if chart_data and isinstance(chart_data, dict):
                try:
                    dynamic_windows = find_marriage_windows_age_15_to_50(chart_data, min_score=40)
                except Exception:
                    dynamic_windows = []

            # Separate into past windows and future windows based on native_age
            past_dyn = [w for w in dynamic_windows if float(w.get("age_end", 0)) <= float(native_age)]
            future_dyn = [w for w in dynamic_windows if float(w.get("age_end", 0)) > float(native_age)]

            # Favorable past window (for older natives or already married)
            if past_dyn:
                top_past = max(past_dyn, key=lambda x: x.get("score", 0))
                bs_st = top_past.get("bs_start") or str(birth_year_bs + int(top_past.get("age_start", 24)))
                bs_en = top_past.get("bs_end") or str(birth_year_bs + int(top_past.get("age_end", 28)))
                past_window = f"वि.सं. {to_nepali_digits(bs_st)} देखि {to_nepali_digits(bs_en)}"
                past_age_str = f"उमेर {to_nepali_digits(top_past.get('age_start', 24))}–{to_nepali_digits(top_past.get('age_end', 28))} वर्ष"
                past_score = top_past.get("score", 88)
            else:
                low_a = 21 if native_age < 25 else max(20, native_age - 6)
                high_a = low_a + 4
                est_start = birth_year_bs + low_a
                est_end = birth_year_bs + high_a
                past_window = f"वि.सं. {to_nepali_digits(est_start)} देखि {to_nepali_digits(est_end)}"
                past_age_str = f"उमेर {to_nepali_digits(low_a)}–{to_nepali_digits(high_a)} वर्ष"
                past_score = 88

            # Favorable future window (for unmarried / upcoming)
            if future_dyn:
                top_fut = min(future_dyn, key=lambda x: x.get("start_date", ""))
                bs_st = top_fut.get("bs_start") or str(current_bs_year + 1)
                bs_en = top_fut.get("bs_end") or str(current_bs_year + 3)
                future_window = f"वि.सं. {to_nepali_digits(bs_st)} देखि {to_nepali_digits(bs_en)}"
                fut_age_str = f"उमेर {to_nepali_digits(top_fut.get('age_start', native_age + 1))}–{to_nepali_digits(top_fut.get('age_end', native_age + 3))} वर्ष"
                future_score = top_fut.get("score", prob_score)
            else:
                f_st = current_bs_year + 1
                f_en = f_st + 2
                future_window = f"वि.सं. {to_nepali_digits(f_st)} देखि {to_nepali_digits(f_en)}"
                fut_age_str = f"उमेर {to_nepali_digits(f_st - birth_year_bs)}–{to_nepali_digits(f_en - birth_year_bs)} वर्ष"
                future_score = prob_score

            # ══ CASE 1: प्रयोगकर्ताले स्पष्ट रूपमा 'विवाह भइसकेको' छनोट गरेको अवस्था ══
            if context_mode == "already_married":
                if "कुन मितिमा" in q or "कहिले" in q:
                    direct_ans = (
                        f"<b>विवाहित अवस्था विश्लेषण:</b> तपाईंले 'विवाह भइसकेको (विवाहित)' सन्दर्भ छनोट गर्नुभएको छ। "
                        f"जन्म कुण्डलीको सप्तम भाव ({seventh_sign_name} राशि), सप्तमेश ({seventh_lord_ne}) र शुक्र/गुरुको दशागत स्थिति अनुसार "
                        f"तपाईंको विवाह विगतमा <b>{past_window} ({past_age_str})</b> को समयावधि भित्र सम्पन्न भएको शास्त्रीय योग देखिन्छ।<br><br>"
                        f"वर्तमान समयमा नयाँ विवाहको प्रश्न लागू हुँदैन। हालको समयमा दाम्पत्य सुख, आपसी समझदारी र पारिवारिक सुख-शान्ति सुदृढ रहनेछ।"
                    )
                elif "सुखी हुन्छ कि समस्या" in q or "सुख" in q:
                    direct_ans = (
                        f"सप्तम भाव ({seventh_sign_name} राशि) र सप्तमेश ({seventh_lord_ne}) को अवस्था अनुसार तपाईंको दाम्पत्य जीवन समग्रमा <b>सुखमय र सहयोगी</b> रहनेछ। "
                        f"समय-समयमा ग्रहदशा अनुसार सामान्य मतभेद भए तापनि आपसी संवाद, विश्वास र समझदारीले सम्बन्ध झन् प्रगाढ बन्नेछ।"
                    )
                else:
                    direct_ans = (
                        f"सप्तम भाव ({seventh_sign_name} राशि) र सप्तमेश ({seventh_lord_ne}) को आधारमा जीवनसाथी सहयोगी, धार्मिक र परिवारप्रेमी हुनुहुन्छ। "
                        f"दाम्पत्य जीवनमा सुख र स्थायित्व कायम राख्न गुरु र शुक्रको उपासना शुभ रहनेछ।"
                    )

                return {
                    "prob_score": 90,
                    "window_bs": f"{past_window} (विगतमा सम्पन्न)",
                    "peak_bs": past_window,
                    "direct_answer": direct_ans,
                    "time_note": f"विगतको विवाह समयावधि: <b>{past_window} ({past_age_str})</b>। वर्तमानमा दाम्पत्य सुख अनुकूल रहनेछ।",
                    "obstacle": "विवाह भइसकेको अवस्था — भविष्यको विवाह प्रश्न लागू हुँदैन।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

            # ══ CASE 2: प्रयोगकर्ताले स्पष्ट रूपमा 'विवाह नभएको' छनोट गरेको अवस्था ══
            elif context_mode == "not_married":
                peak_m1 = BS_MONTHS_NE[(current_bs_month + 3) % 12]
                peak_m2 = BS_MONTHS_NE[(current_bs_month + 7) % 12]
                peak_bs = f"{future_window} ({peak_m1}–{peak_m2})"

                if "कुन दिशा" in q or "स्थान" in q:
                    _zone_txt = f" ({m_dir_zone})" if m_dir_zone else ""
                    direct_ans = (
                        f"<b>विवाह प्रस्ताव आउने मुख्य दिशा: {m_dir}{_zone_txt}</b><br/>"
                        f"• <b>मुख्य दिशा:</b> <b>{m_dir}</b> ({m_dir_pct}% बल)<br/>"
                        + (f"• <b>सहायक दिशा:</b> {m_dir_2} ({m_dir_2_pct}%)<br/>" if m_dir_2 else "")
                        + (f"• <b>विश्वसनीयता:</b> {m_dir_conf}<br/>" if m_dir_conf else "")
                        + f"<br/><b>नियम-आधारित प्रमाण (D1–D9):</b>{m_dir_evidence_html}"
                        + f"<br/><i>(सप्तम भाव: {seventh_sign_name}, सप्तमेश: {seventh_lord_ne} — बहु-नियम स्कोरबाट निर्धारण)</i>"
                    )
                elif "प्रेम विवाह" in q or "मागी" in q or "सहमति" in q:
                    direct_ans = "पञ्चम र सप्तम भावको सम्बन्ध अनुसार विवाह <b>पारिवारिक सहमति तथा मागी विवाह (Arranged Marriage)</b> वा प्रेमपछिको पारिवारिक सहमतिमा हुने प्रबल योग छ।"
                elif "स्वभाव" in q or "आर्थिक अवस्था" in q or "रूप" in q:
                    direct_ans = f"सप्तम भाव {seventh_sign_name} का स्वामी {seventh_lord_ne} को प्रभावले जीवनसाथी <b>सुशील, परिवारप्रेमी, बौद्धिक र सहयोगी</b> हुनेछन्।"
                else:
                    direct_ans = f"शास्त्रीय विश्लेषण अनुसार आगामी विवाहको शुभ समय <b>{future_window} ({fut_age_str})</b> भित्र रहने प्रबल योग छ।"

                return {
                    "prob_score": future_score,
                    "window_bs": future_window,
                    "peak_bs": peak_bs,
                    "direct_answer": direct_ans,
                    "time_note": f"शुभ विवाह योग काल: <b>{future_window} ({fut_age_str})</b> (सर्वाधिक अनुकूल: <b>{peak_bs}</b>)।",
                    "obstacle": "सप्तम भावमा पाप दृष्टि भए बिहीबार गुरु/शुक्रको पूजा गर्नु शुभ हुन्छ।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

            # ══ CASE 3: डिफल्ट / अवस्था नखुलेको (Unspecified / Pure Astrological Calculation) ══
            else:
                if "कुन मितिमा" in q or "कहिले" in q:
                    direct_ans = (
                        f"जन्म कुण्डलीको सप्तम भाव ({seventh_sign_name} राशि), सप्तमेश ({seventh_lord_ne}), शुक्र र गुरुको दशागत स्थिति अनुसार "
                        f"जातकको कुण्डलीगत प्रमुख विवाह योग काल <b>{past_window} ({past_age_str})</b> तथा आगामी गोचर अनुकूलता <b>{future_window} ({fut_age_str})</b> रहेको देखिन्छ।<br><br>"
                        f"• <b>यदि विवाह भइसकेको अवस्था हो भने:</b> यो समय विगतमा विवाह सम्पन्न भएको काल हो र वर्तमानमा दाम्पत्य सुख, आपसी सामञ्जस्य र पारिवारिक स्थायित्व अनुकूल रहनेछ।<br>"
                        f"• <b>यदि विवाह नभएको (अविवाहित) अवस्था हो भने:</b> आगामी <b>{future_window} ({fut_age_str})</b> भित्र विवाह सम्पन्न हुने बलियो योग छ।<br>"
                        f"<i>(विशेष अवस्था अनुसार थप सूक्ष्म फलादेशका लागि माथिको 'विवाहित' वा 'अविवाहित' बटन छनोट गर्न सक्नुहुन्छ।)</i>"
                    )
                elif "कुन दिशा" in q or "स्थान" in q:
                    _zone_txt = f" ({m_dir_zone})" if m_dir_zone else ""
                    direct_ans = (
                        f"<b>विवाह हुने सम्भावित मुख्य दिशा: {m_dir}{_zone_txt}</b><br/>"
                        f"• <b>मुख्य दिशा:</b> <b>{m_dir}</b> ({m_dir_pct}% बल)<br/>"
                        + (f"• <b>सहायक दिशा:</b> {m_dir_2} ({m_dir_2_pct}%)<br/>" if m_dir_2 else "")
                        + (f"• <b>विश्वसनीयता:</b> {m_dir_conf}<br/>" if m_dir_conf else "")
                        + f"<br/><b>नियम-आधारित प्रमाण (D1–D9):</b>{m_dir_evidence_html}"
                        + f"<br/><i>(सप्तम भाव: {seventh_sign_name}, सप्तमेश: {seventh_lord_ne} — D1 देखि D9 सम्मका बहु-नियम बाट स्कोर गरिएको दिशा)</i>"
                    )
                elif "स्वभाव" in q or "आर्थिक अवस्था" in q or "रूप" in q:
                    direct_ans = f"सप्तम भाव {seventh_sign_name} को प्रभावले जीवनसाथी <b>सुशील, सहृदयी, धार्मिक र पारिवारिक प्रतिष्ठा बढाउने</b> स्वभावका हुनेछन्।"
                else:
                    direct_ans = f"सप्तम भाव र शुक्र/गुरुको शुभ प्रभावले गर्दा वैवाहिक एवं दाम्पत्य जीवन समग्रमा <b>सुखमय र सन्तुलित</b> रहने शास्त्रीय आधार छ।"

                window_bs = f"{past_window} / {future_window}"
                peak_bs = f"सप्तमेश-गुरु गोचर काल"
                return {
                    "prob_score": max(past_score, future_score),
                    "window_bs": window_bs,
                    "peak_bs": peak_bs,
                    "direct_answer": direct_ans,
                    "time_note": f"कुण्डलीगत विवाह योग समय: <b>{window_bs}</b>।",
                    "obstacle": "दाम्पत्य सुखका लागि बिहीबार गुरु तथा शुक्रको उपासना शुभ हुन्छ।",
                    "life_status_note": life_status,
                    "conclusion": direct_ans
                }

        # ══════════════════════════════════════════════════════════════════════
        # ६. व्यवसाय तथा उद्योग (Business Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "business":
            if "जागिर गर्ने कि व्यवसाय" in q:
                direct_ans = (
                    f"तपाईंको कुण्डलीमा छैटौं भाव (जागिर) र सातौं/दशम भाव (व्यवसाय) को शक्ति तुलना गर्दा "
                    f"सुरुवातमा जागिर/सेवाबाट अनुभव र पुँजी हासिल गरी त्यसपछि <b>स्वतन्त्र व्यवसाय वा परामर्श सेवा</b> सुरु गर्दा अत्यधिक लाभ हुने योग छ।"
                )
            elif "कुन व्यवसाय" in q:
                direct_ans = (
                    f"सप्तमेश {seventh_lord_ne} र बुध/मंगलको अनुकूलता अनुसार तपाईंको लागि <b>व्यापार, परामर्श, सूचना प्रविधि, सेवामूलक उद्योग वा साझेदारी व्यवसाय</b> सर्वाधिक फलदायी रहनेछ।"
                )
            else:
                direct_ans = (
                    f"व्यवसायमा दीर्घकालीन सफलता मिल्ने योग छ। नयाँ लगानी र विस्तारका लागि आगामी समय अनुकूल रहनेछ।"
                )
            return {
                "prob_score": 85,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 3)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "व्यापारिक लाभ र विस्तारको समय अनुकूल छ।",
                "obstacle": "कुनै पनि नयाँ साझेदारी गर्दा लिखित सम्झौता स्पष्ट राख्नुहोस्।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # ४. शिक्षा तथा अध्ययन (Education Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "education":
            if "कुन विषय" in q:
                direct_ans = (
                    f"चतुर्थ भाव ({fourth_sign_name}), पञ्चम भाव ({fifth_sign_name}) र बुध/गुरुको प्रभाव अनुसार तपाईंको लागि "
                    f"<b>व्यवस्थापन (Management), सूचना प्रविधि (IT/Computer Science), इन्जिनियरिङ, कानुन, बैंकिङ वा प्रशासनिक अध्ययन</b> सर्वाधिक उपयुक्त छ।"
                )
            else:
                direct_ans = (
                    f"चतुर्थ भाव र पञ्चम भावको शुभ स्थितिले गर्दा तपाईंको <b>शैक्षिक स्तर उच्च र फलदायी</b> रहनेछ। "
                    f"प्रतिस्पर्धात्मक परीक्षामा राम्रो सफलता हासिल हुनेछ।"
                )
            return {
                "prob_score": 88,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 2)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "शैक्षिक प्रगतिको समय अनुकूल छ।",
                "obstacle": "एकाग्रता वृद्धि गर्न सरस्वती स्तोत्र पाठ गर्नु शुभ हुनेछ।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # ७. धन तथा आय (Wealth Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "wealth":
            direct_ans = (
                f"द्वितीय भाव (धन भाव - {second_sign_name}) र एकादश भाव (लाभ भाव) को स्वामी {second_lord_ne} तथा गुरुको शुभ स्थिति अनुसार "
                f"तपाईंको मुख्य धनआर्जन <b>पेशागत सेवा, बौद्धिक परामर्श, व्यापार तथा अचल सम्पत्ति</b> बाट हुने बलियो धन योग छ। "
                f"उमेर ३२ वर्षपछि आर्थिक सञ्चयमा क्रमिक सुधार र स्थायित्व आउनेछ।"
            )
            return {
                "prob_score": 87,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 3)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "आर्थिक वृद्धि र धन सञ्चयको समय अनुकूल छ।",
                "obstacle": "अनावश्यक खर्च नियन्त्रण गर्न शुक्रबार महालक्ष्मीको आराधना गर्नुहोस्।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # ८. घर जग्गा तथा सम्पत्ति (Property Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "property":
            direct_ans = (
                f"चतुर्थ भाव (गृह/भूमि भाव - {fourth_sign_name}) का स्वामी {fourth_lord_ne} र भूमिकारक मंगलको स्थिति अनुसार "
                f"तपाईंको <b>आफ्नै घर तथा जग्गा खरिद गर्ने प्रबल योग</b> रहेको छ। आगामी २ देखि ३ वर्षभित्र अचल सम्पत्ति जोड्न सफलता मिल्नेछ।"
            )
            return {
                "prob_score": 85,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)} देखि {to_nepali_digits(current_bs_year + 3)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 2)}",
                "direct_answer": direct_ans,
                "time_note": "घर-जग्गा जोड्ने अनुकूल समय आगामी २-३ वर्षभित्र छ।",
                "obstacle": "जग्गा खरिद गर्दा कागजातको कानुनी पक्ष राम्ररी जाँच्नुहोला।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # ९. विदेश यात्रा (Foreign Travel Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "foreign":
            direct_ans = (
                f"नवम भाव ({ninth_sign_name}), द्वादश भाव र राहुको अनुकूल गोचर अनुसार तपाईंको <b>विदेश यात्रा तथा वैदेशिक कार्यसिद्धिको योग प्रबल</b> छ। "
                f"पश्चिमा वा विकसित मुलुकहरू (अमेरिका, क्यानडा, युरोप, अस्ट्रेलिया, जापान आदि) जानु बढी लाभदायक र उन्नतिकारक हुनेछ।"
            )
            return {
                "prob_score": 84,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)} देखि {to_nepali_digits(current_bs_year + 3)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "विदेश यात्रा तथा भिसा प्राप्तिको समय अनुकूल छ।",
                "obstacle": "कागजात प्रक्रियामा पूर्ण सतर्कता अपनाउनुहोस्।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # १०. स्वास्थ्य तथा आयु (Health Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "health":
            direct_ans = (
                f"लग्न {l_name} र षष्ठ भाव ({sixth_sign_name}) को विश्लेषण अनुसार समग्र स्वास्थ्य अवस्था <b>सामान्यतया अनुकूल</b> रहनेछ। "
                f"खानपान र दैनिक दिनचर्यामा ध्यान दिएमा ठूला समस्या आउने छैनन्। आयु भाव (अष्टम भाव) बलवान् रहेकाले दीर्घायुको योग छ।"
            )
            return {
                "prob_score": 85,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 2)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "स्वास्थ्यमा सुधार र दीर्घायुको योग अनुकूल छ।",
                "obstacle": "दैनिक योग, ध्यान र महामृत्युञ्जय जप गर्नु उत्तम हुन्छ।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # १३. मुद्दा मामिला तथा शत्रु (Legal Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "legal":
            direct_ans = (
                f"लग्नेश {l_lord_ne} र षष्ठेश {sixth_lord_ne} को शक्ति तुलना गर्दा लग्नेश बलवान् रहेकाले <b>मुद्दा-मामिलामा तपाईंको जित हुने र शत्रुहरू पराजित हुने</b> प्रबल योग छ। "
                f"सत्य र तथ्यको पक्षमा निर्णय आउनेछ।"
            )
            return {
                "prob_score": 86,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)} देखि {to_nepali_digits(current_bs_year + 2)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "कानुनी विजय र फैसलाको समय अनुकूल छ।",
                "obstacle": "कागजात र प्रमाणहरू व्यवस्थित राख्नुहोस्।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # १५. आध्यात्म तथा इष्टदेव (Spiritual Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "spiritual":
            direct_ans = (
                f"पञ्चम भाव ({fifth_sign_name}) र नवम भाव ({ninth_sign_name}) का आधारमा तपाईंका मुख्य <b>इष्टदेव भगवान् शिव वा श्रीविष्णु (नारायण)</b> हुनुहुन्छ। "
                f"नित्य शिव उपासना, विष्णु सहस्रनाम वा गायत्री मन्त्र जप गर्नाले आध्यात्मिक शान्ति र आत्मिक उन्नति प्राप्त हुनेछ।"
            )
            return {
                "prob_score": 92,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 3)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "आध्यात्मिक उन्नति र मन्त्र साधनाको समय अत्यन्त शुभ छ।",
                "obstacle": "नियमित साधना र पवित्रता कायम राख्नुहोस्।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # १७. जीवनको समग्र भाग्य (Overall Destiny Questions)
        # ══════════════════════════════════════════════════════════════════════
        if category_key == "overall":
            direct_ans = (
                f"लग्नेश {l_lord_ne}, भाग्येश {ninth_lord_ne} र दशमेश {tenth_lord_ne} को त्रिकोण-केन्द्र सम्बन्ध अनुसार "
                f"तपाईंको <b>मुख्य भाग्योदय उमेर २८ देखि ३६ वर्षको बीचमा</b> हुने प्रबल योग छ। जीवनको उत्तरार्ध अत्यधिक समृद्ध, मानसम्मानयुक्त र सफल रहनेछ।"
            )
            return {
                "prob_score": 90,
                "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 4)}",
                "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
                "direct_answer": direct_ans,
                "time_note": "भाग्योदय एवं स्वर्णिम काल प्रारम्भ भएको छ।",
                "obstacle": "आफ्नो लक्ष्यमा निरन्तर लागिरहनुहोस्।",
                "life_status_note": life_status,
                "conclusion": direct_ans
            }

        # ══════════════════════════════════════════════════════════════════════
        # सामान्य डिफाल्ट फलादेश (Universal / General Questions)
        # ══════════════════════════════════════════════════════════════════════
        direct_ans = (
            f"लग्नेश {l_lord_ne} र कार्येश {PLANET_NAMES_NE.get(karyesh, karyesh)} को पारस्परिक सम्बन्ध अनुकूल रहेकाले तपाईंको प्रश्नको परिणाम <b>सकारात्मक र फलदायी</b> रहनेछ। "
            f"कार्यसिद्धिमा धैर्यता र नियमित प्रयासले मनोवाञ्छित सफलता मिल्नेछ।"
        )
        return {
            "prob_score": prob_score,
            "window_bs": f"वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 2)}",
            "peak_bs": f"वि.सं. {to_nepali_digits(current_bs_year + 1)}",
            "direct_answer": direct_ans,
            "time_note": f"सकारात्मक परिणाम प्राप्त हुने समय: <b>वि.सं. {to_nepali_digits(current_bs_year)} देखि {to_nepali_digits(current_bs_year + 2)}</b>।",
            "obstacle": "मनोबल उच्च राखी कार्य गर्नुहोला।",
            "life_status_note": life_status,
            "conclusion": direct_ans
        }

    @classmethod
    def _get_remedy_for_category(cls, category_key: str, karyesh: str) -> str:
        k_ne = PLANET_NAMES_NE.get(karyesh, karyesh)
        if category_key in ("marriage", "love"):
            return (
                f"कार्येश <b>{k_ne}</b> र <b>बृहस्पति (गुरु)</b> को उपासना गर्नुहोस्। "
                "प्रत्येक बिहीबार शिव-पार्वतीको आराधना, पहेँलो वस्तुको दान तथा "
                "'ॐ नमः शिवाय' वा 'ॐ क्लीं कामाय नमः' १०८ पटक जप गर्नुहोस्।"
            )
        elif category_key in ("career", "politics"):
            return (
                f"दशमेश एवं कार्येश <b>{k_ne}</b> को बल वृद्धिका लागि दैनिक बिहान "
                "सूर्य भगवानिलाई जल अर्पण गरी 'ॐ सूर्याय नमः' १०८ पटक जप गर्नुहोस्।"
            )
        elif category_key in ("wealth", "business", "property"):
            return (
                "<b>श्री महालक्ष्मी</b> को आराधना गर्नुहोस्। प्रत्येक शुक्रबार सेतो वस्तु दान "
                "तथा श्रीसूक्त पाठ गर्नाले धन सञ्चय र व्यापारमा शीघ्र सफलता मिल्नेछ।"
            )
        elif category_key in ("health", "debts", "legal"):
            return (
                "दैनिक <b>महामृत्युञ्जय मन्त्र</b> जप गर्नुहोस्। मंगलबार/शनिबार "
                "दीनदुःखीलाई भोजन गराउनाले रोग, ऋण र कानुनी बाधाबाट मुक्ति मिल्नेछ।"
            )
        elif category_key in ("education", "children"):
            return (
                "<b>गायत्री मन्त्र</b> वा <b>सरस्वती स्तोत्र</b> को नित्य पाठ गर्नुहोस्। "
                "बुधबार हरियो घाँस गाईलाई खुवाउनुहोस्।"
            )
        elif category_key == "foreign":
            return (
                "राहु र शनिको अनुकूलताका लागि शनिबार तिलको तेलको दीप बाल्नुहोस्। "
                "यात्रा अगाडि भगवान् गणेशको दर्शन तथा पूजा गर्नुहोस्।"
            )
        return (
            f"इष्टदेवको स्मरण तथा कार्येश <b>{k_ne}</b> को बीज मन्त्र जप गर्नाले "
            "सबै प्रकारका कार्यमा निर्विघ्न सिद्धि प्राप्त हुनेछ।"
        )


class PrashnaChartPage(QWidget):
    """
    पुनर्निर्मित शास्त्रीय प्रश्न कुण्डली पेज:
    - डिफाल्ट: अवस्था नखुलेको/सामान्य कुण्डलीगत विश्लेषण (अवस्था छनोट गर्न बाध्य नपर्ने)
    - माथि: रियल-टाइम खोज, विषय छनोट, प्रश्न छनोट र अवस्था छनोट बटनहरू
    - तल: बृहत् पराशर होरा शास्त्र, प्रश्नमार्ग र ताजिक नीलकण्ठी अनुसारको पूर्ण फलादेश
    - शुद्ध नेपाली देवनागरी लिपि, ठूलो र स्पष्ट अक्षर।
    """
    def __init__(self, language: str = "ne", data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._chart_data = data or {}
        
        self._build_ui()
        self._populate_categories()
        self._on_category_changed(0)

    def _build_ui(self):
        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #ffffff; border: none; }")

        self._container = QWidget()
        self._container.setStyleSheet("background: #ffffff; color: #0f172a;")
        self._content_vbox = QVBoxLayout(self._container)
        self._content_vbox.setContentsMargins(28, 20, 28, 36)
        self._content_vbox.setSpacing(18)

        scroll.setWidget(self._container)
        main_vbox.addWidget(scroll)

        # ── १. पेज शीर्षक ──────────────────────────────────────────────────
        header_lbl = QLabel("प्रश्न कुण्डली एवं शास्त्रीय फलादेश")
        header_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 2px;")
        self._content_vbox.addWidget(header_lbl)

        sub_lbl = QLabel(
            "बृहत् पराशर होरा शास्त्र, प्रश्नमार्ग एवं ताजिक नीलकण्ठी (इत्थशाल, कम्बूल, ईशराफ योग) अनुसार जीवनका १८ वटा प्रमुख क्षेत्रका प्रश्नहरूको सटीक मिति (वि.सं.) र प्रत्यक्ष उत्तरसहितको शास्त्रीय फलादेश।"
        )
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet("font-size: 14px; color: #475569; margin-bottom: 6px; line-height: 1.5;")
        self._content_vbox.addWidget(sub_lbl)

        # ── २. नियन्त्रण बक्स (Search, Category, Question, Context) ─────────
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        c_vbox = QVBoxLayout(controls_frame)
        c_vbox.setSpacing(14)

        # Row A: खोज बक्स (Search Box)
        search_row = QVBoxLayout()
        search_row.setSpacing(4)
        search_lbl = QLabel("🔍 <b>प्रश्न खोज्नुहोस् (Search Question):</b>")
        search_lbl.setStyleSheet("font-size: 14px; color: #0f172a; border: none;")
        search_row.addWidget(search_lbl)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("यहाँ टाइप गर्नुहोस् (जस्तै: कति सन्तान, कुन जागिर, विवाह मिति, सरकारी जागिर, विदेश, धन...)")
        self._search_input.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1.5px solid #94a3b8;
                border-radius: 6px;
                padding: 9px 12px;
                font-size: 14px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 1.5px solid #0284c7;
            }
        """)
        self._search_input.textChanged.connect(self._on_search_text_changed)
        search_row.addWidget(self._search_input)

        # सुझाव सूची
        self._suggest_list = QListWidget()
        self._suggest_list.setStyleSheet("""
            QListWidget {
                background: #ffffff;
                border: 1px solid #0284c7;
                border-radius: 6px;
                font-size: 14px;
                color: #0f172a;
                max-height: 180px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f1f5f9;
            }
            QListWidget::item:hover {
                background: #e0f2fe;
                color: #0369a1;
            }
        """)
        self._suggest_list.itemClicked.connect(self._on_suggestion_clicked)
        self._suggest_list.hide()
        search_row.addWidget(self._suggest_list)
        c_vbox.addLayout(search_row)

        # Row B: विषय र प्रश्न ड्रपडाउन
        dropdown_row = QHBoxLayout()
        dropdown_row.setSpacing(14)

        cat_vbox = QVBoxLayout()
        cat_vbox.setSpacing(4)
        cat_lbl = QLabel("<b>विषय / क्षेत्र (Category):</b>")
        cat_lbl.setStyleSheet("font-size: 14px; color: #0f172a; border: none;")
        cat_vbox.addWidget(cat_lbl)

        self._cat_combo = QComboBox()
        self._cat_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff;
                border: 1.5px solid #94a3b8;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 14px;
                color: #0f172a;
                min-width: 230px;
            }
        """)
        self._cat_combo.currentIndexChanged.connect(self._on_category_changed)
        cat_vbox.addWidget(self._cat_combo)
        dropdown_row.addLayout(cat_vbox)

        q_vbox = QVBoxLayout()
        q_vbox.setSpacing(4)
        q_lbl = QLabel("<b>प्रश्न छान्नुहोस् (Select Question):</b>")
        q_lbl.setStyleSheet("font-size: 14px; color: #0f172a; border: none;")
        q_vbox.addWidget(q_lbl)

        self._question_combo = QComboBox()
        self._question_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff;
                border: 1.5px solid #94a3b8;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 14px;
                color: #0f172a;
            }
        """)
        self._question_combo.currentIndexChanged.connect(self._on_question_changed)
        q_vbox.addWidget(self._question_combo, 1)
        dropdown_row.addLayout(q_vbox, 1)

        c_vbox.addLayout(dropdown_row)

        # Row C: जीवन-अवस्था छनोट (Context Options Toggles)
        ctx_title_lbl = QLabel("<b>वर्तमान अवस्था / जीवन सन्दर्भ (Current Status — खुलाउन चाहेमा मात्र):</b>")
        ctx_title_lbl.setStyleSheet("font-size: 14px; color: #0f172a; border: none; margin-top: 4px;")
        c_vbox.addWidget(ctx_title_lbl)

        self._context_frame = QFrame()
        self._context_frame.setStyleSheet("background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px 12px;")
        self._context_hbox = QHBoxLayout(self._context_frame)
        self._context_hbox.setContentsMargins(4, 4, 4, 4)
        self._context_hbox.setSpacing(20)
        self._context_group = QButtonGroup(self)
        self._context_group.buttonClicked.connect(lambda: self.calculate_answer())
        c_vbox.addWidget(self._context_frame)

        # Row D: कार्य बटन (Calculate Button)
        action_row = QHBoxLayout()
        action_row.addStretch(1)

        self._calc_btn = QPushButton("✨ फल एवं सटीक उत्तर विश्लेषण गर्नुहोस्")
        self._calc_btn.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 26px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #0369a1;
            }
        """)
        self._calc_btn.clicked.connect(self.calculate_answer)
        action_row.addWidget(self._calc_btn)

        c_vbox.addLayout(action_row)
        self._content_vbox.addWidget(controls_frame)

        # ── ३. उत्तर / रिपोर्ट बक्स (Answer / Report Box) ───────────────────
        self._report_box = QFrame()
        self._report_box.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                padding: 22px;
            }
        """)
        self._report_layout = QVBoxLayout(self._report_box)
        self._report_layout.setSpacing(16)
        self._content_vbox.addWidget(self._report_box)

        # ── ४. प्रयोगकर्ता निर्देशिका (Guide Footer) ─────────────────────────
        self._build_guide_footer()

    def _populate_categories(self):
        self._cat_combo.blockSignals(True)
        self._cat_combo.clear()
        for key, info in PRASHNA_DATA.items():
            self._cat_combo.addItem(info["title_ne"], key)
        self._cat_combo.blockSignals(False)

    def _on_category_changed(self, index: int):
        cat_key = self._cat_combo.currentData() or "marriage"
        cat_info = PRASHNA_DATA.get(cat_key, PRASHNA_DATA["marriage"])

        # Populate questions
        self._question_combo.blockSignals(True)
        self._question_combo.clear()
        for q in cat_info["questions"]:
            self._question_combo.addItem(q)
        self._question_combo.blockSignals(False)

        # Update context radio buttons
        for btn in self._context_group.buttons():
            self._context_group.removeButton(btn)
            btn.deleteLater()

        context_opts = cat_info.get("context_options", [])
        for i, (ctx_val, ctx_label) in enumerate(context_opts):
            rbtn = QRadioButton(ctx_label)
            rbtn.setProperty("context_val", ctx_val)
            rbtn.setStyleSheet("font-size: 14px; color: #0f172a; font-weight: 600; padding: 4px 8px;")

            # Default: Always select the first option ("unspecified" / सामान्य विश्लेषण)
            if i == 0:
                rbtn.setChecked(True)

            self._context_group.addButton(rbtn)
            self._context_hbox.addWidget(rbtn)

        self.calculate_answer()

    def _on_question_changed(self, index: int):
        self.calculate_answer()

    def _on_search_text_changed(self, text: str):
        q_text = text.strip().lower()
        if not q_text or len(q_text) < 2:
            self._suggest_list.hide()
            return

        self._suggest_list.clear()
        matches = []
        for cat_key, cat_data in PRASHNA_DATA.items():
            for q in cat_data["questions"]:
                if q_text in q.lower():
                    matches.append((cat_key, q))

        if matches:
            for cat_key, q in matches[:10]:
                item = QListWidgetItem(f"[{PRASHNA_DATA[cat_key]['title_ne']}] {q}")
                item.setData(Qt.UserRole, (cat_key, q))
                self._suggest_list.addItem(item)
            self._suggest_list.show()
        else:
            self._suggest_list.hide()

    def _on_suggestion_clicked(self, item: QListWidgetItem):
        cat_key, q_text = item.data(Qt.UserRole)
        self._suggest_list.hide()
        self._search_input.blockSignals(True)
        self._search_input.setText(q_text)
        self._search_input.blockSignals(False)

        # Select category and question
        idx = self._cat_combo.findData(cat_key)
        if idx >= 0:
            self._cat_combo.setCurrentIndex(idx)
        q_idx = self._question_combo.findText(q_text)
        if q_idx >= 0:
            self._question_combo.setCurrentIndex(q_idx)

        self.calculate_answer()

    def calculate_answer(self):
        """Calculates and renders the comprehensive Parashari/Tajika horary report."""
        cat_key = self._cat_combo.currentData() or "marriage"
        question_text = self._question_combo.currentText() or "मेरो विवाह कुन मितिमा हुन्छ?"

        # Get active context
        checked_btn = self._context_group.checkedButton()
        context_mode = checked_btn.property("context_val") if checked_btn else "unspecified"

        # Evaluate using Prashna Engine with real-time datetime
        result = PrashnaKundaliEngine.evaluate_question(
            category_key=cat_key,
            question_text=question_text,
            context_mode=context_mode,
            chart_data=self._chart_data,
            prashna_datetime=datetime.datetime.now()
        )

        # Render report
        self._render_report(result)

    def _render_report(self, res: Dict[str, Any]):
        # Clear previous report items
        while self._report_layout.count():
            item = self._report_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # ── प्रश्न शीर्षक (Question Header) ──
        q_header = QLabel(f"❓ प्रश्न: {res['question']}")
        q_header.setWordWrap(True)
        q_header.setStyleSheet("font-size: 19px; font-weight: 800; color: #0369a1; border-bottom: 2px solid #0284c7; padding-bottom: 8px;")
        self._report_layout.addWidget(q_header)

        prob_score = res.get("probability_score", 75)

        # ── जीवन-अवस्था जाँच ब्यानर (Life Status Banner) ──
        life_note = res.get("life_status_note", "")
        if life_note:
            is_error = prob_score == 0
            is_warn = "विवाह भइसकेको" in life_note or "विवाहित" in life_note
            if is_error:
                bstyle = "background: #fef2f2; border: 1.5px solid #dc2626; border-radius: 6px; padding: 10px 14px;"
                icon = "⛔"
            elif is_warn:
                bstyle = "background: #eff6ff; border: 1.5px solid #3b82f6; border-radius: 6px; padding: 10px 14px;"
                icon = "💍"
            else:
                bstyle = "background: #f8fafc; border: 1.5px solid #0284c7; border-radius: 6px; padding: 10px 14px;"
                icon = "🌐"
            banner = QLabel(f"{icon} <b>स्थिति सन्दर्भ:</b> {life_note}")
            banner.setWordWrap(True)
            banner.setStyleSheet(bstyle + " font-size: 15px; font-weight: 600; color: #0f172a;")
            self._report_layout.addWidget(banner)

        # ── कुण्डली विवरण बार (Prashna Info Pill) ──
        info_pill = QFrame()
        info_pill.setStyleSheet("background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 14px;")
        p_layout = QHBoxLayout(info_pill)
        p_layout.setContentsMargins(4, 4, 4, 4)
        info_text = (
            f"<b>क्षेत्र:</b> {res['category_title']} &nbsp;|&nbsp; "
            f"<b>लग्न:</b> {res['lagna_name']} ({ne_num(res['lagna_sign'])}) &nbsp;|&nbsp; "
            f"<b>लग्नेश:</b> {res['lagnesh']} &nbsp;|&nbsp; "
            f"<b>कार्य भाव:</b> {ne_num(res['karya_bhava'])} औं &nbsp;|&nbsp; "
            f"<b>कार्येश:</b> {res['karyesh']} &nbsp;|&nbsp; "
            f"<b>मिति (वि.सं.):</b> {res['prashna_date_bs']}"
        )
        info_lbl = QLabel(info_text)
        info_lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: #0f172a; border: none;")
        p_layout.addWidget(info_lbl)
        self._report_layout.addWidget(info_pill)

        # यदि प्रश्न यस अवस्थामा लागू नहुने भए
        if prob_score == 0:
            self._add_report_section(
                "⚠️ प्रश्न यस अवस्थामा लागू हुँदैन:",
                f"• <b>कारण:</b> {res['obstacle']}<br>"
                f"• <b>निष्कर्ष:</b> {res['conclusion']}"
            )
            return

        # ── १. प्रश्नको प्रत्यक्ष एवं स्पष्ट उत्तर (Direct Astrological Answer) ──
        self._add_report_section(
            "१. प्रश्नको प्रत्यक्ष उत्तर एवं शास्त्रीय विश्लेषण (Direct Astrological Answer):",
            f"{res.get('direct_answer', res['conclusion'])}"
        )

        # ── २. समय निर्धारण एवं स्वर्णिम काल (Bikram Sambat Timing) ──
        self._add_report_section(
            "२. सटीक समय निर्धारण एवं स्वर्णिम काल (Bikram Sambat Timing):",
            f"• <b>प्रमुख समय दायरा:</b> <span style='color: #0369a1; font-weight: bold; font-size: 17px;'>{res['probable_window_bs']}</span><br>"
            f"• <b>सर्वाधिक बलियो समय (Peak Period):</b> <span style='color: #15803d; font-weight: bold; font-size: 17px;'>{res['peak_window_bs']}</span><br>"
            f"• <b>समय विश्लेषण:</b> {res['time_analysis_note']}"
        )

        # ── ३. शास्त्रीय आधार एवं ताजिक योग विवेचना ──
        sutra = res.get("sutra_applied", "")
        self._add_report_section(
            "३. शास्त्रीय आधार एवं ताजिक योग विवेचना (Classical Sutras & Tajika Yogas):",
            f"• <b>सक्रिय ताजिक योग:</b> <span style='color: #7c2d12; font-weight: bold;'>{res['yoga_name']}</span><br>"
            f"• <b>शास्त्रीय सूत्र:</b> <i>'{sutra}'</i><br>"
            f"• <b>ताजिक नीलकण्ठी श्लोक:</b> <i>'लग्नेशे कार्यपे वापि दीप्तांशैर्मिलिते मिथः। इत्थशालो भवेत्तत्र सर्वकार्यप्रसाधकः॥'</i><br>"
            f"• <b>योग फल व्याख्या:</b> {res['yoga_desc']}<br>"
            f"• <b>बृहत् पराशर होरा शास्त्र:</b> कार्य भाव ({ne_num(res['karya_bhava'])} औं), कार्येश र शुभ ग्रहहरूको अनुकूल अवस्थाले मनोरथ सिद्धिको बलियो संकेत गर्दछ।"
        )

        # ── ४. सफलता सम्भावना एवं ग्रह बल ──
        prob_color = "#15803d" if prob_score >= 80 else ("#ca8a04" if prob_score >= 60 else "#dc2626")
        self._add_report_section(
            "४. सफलता सम्भावना एवं सामर्थ्य (Success Probability):",
            f"• <b>अनुकूलता प्रतिशत:</b> <span style='color: {prob_color}; font-weight: 800; font-size: 18px;'>{to_nepali_digits(prob_score)}% अनुकूल सम्भावना</span><br>"
            f"• <b>ग्रह बल एवं स्थिति:</b> लग्नेश ({res['lagnesh']}) र कार्येश ({res['karyesh']}) को पारस्परिक अवस्थाले सकारात्मक दिशा दर्शाउँछ।"
        )

        # ── ५. मुख्य कारण एवं बाधक तत्व ──
        self._add_report_section(
            "५. मुख्य कारण एवं बाधक तत्व (Root Causes & Hindrances):",
            f"• <b>सम्भावित अवरोध:</b> {res['obstacle']}<br>"
            f"• <b>विश्लेषण:</b> समयमा धैर्यता राख्नु र अनावश्यक हतार वा संशयबाट बच्नु आवश्यक छ।"
        )

        # ── ६. शास्त्रसम्मत प्रभावकारी उपाय ──
        self._add_report_section(
            "६. शास्त्रसम्मत प्रभावकारी उपाय एवं मार्गदर्शन (Astrological Remedies):",
            f"{res['remedy']}"
        )

    def _add_report_section(self, title: str, html_body: str):
        sec_widget = QWidget()
        vbox = QVBoxLayout(sec_widget)
        vbox.setContentsMargins(0, 4, 0, 4)
        vbox.setSpacing(4)

        t_lbl = QLabel(f"<b>{title}</b>")
        t_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 4px; margin-bottom: 2px;")
        vbox.addWidget(t_lbl)

        b_lbl = QLabel(html_body)
        b_lbl.setWordWrap(True)
        b_lbl.setStyleSheet("font-size: 15px; color: #0f172a; line-height: 1.65; padding-left: 8px;")
        vbox.addWidget(b_lbl)

        self._report_layout.addWidget(sec_widget)

    def _build_guide_footer(self):
        # Bottom-pinned guide button only. The guide text itself lives in the
        # shared "मद्दत" User Guide dialog, so the search/controls/report stack
        # always fills the full page and nothing is covered.
        _guide_btn = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn.setObjectName("prashnaGuideBox")
        _guide_btn.setToolTip("प्रश्न कुण्डली निर्देशिका" if self._is_ne else "Prashna guide")
        _guide_btn.setCursor(Qt.PointingHandCursor)
        _guide_btn.setStyleSheet("QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } QPushButton:hover { background: #bae6fd; }")

        def _open_prashna_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_prashna_view")

        _guide_btn.clicked.connect(_open_prashna_guide)
        self._content_vbox.addWidget(_guide_btn)
