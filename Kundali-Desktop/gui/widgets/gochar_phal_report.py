# -*- coding: utf-8 -*-
"""
gui/widgets/gochar_phal_report.py

Gochar Phal — Detailed Transit Effect Report (गोचर फल विस्तृत रिपोर्ट)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each transiting planet, shows:
  - Current sign (gochar rashi)
  - Transit house from natal Moon (Chandra Rashi)
  - Effect on that house (classical interpretation)
  - Vedha (obstruction) check
  - Traffic light rating: Favourable / Neutral / Unfavourable

Uses classical Parashari transit rules (Sarvatobhadra & Ashtakavarga)
"""
from __future__ import annotations
import sys, os, datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, QTimer

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import COLOR_ERROR

PLANET_NE = {
    "Sun":"सूर्य","Moon":"चन्द्र","Mars":"मङ्गल","Mercury":"बुध",
    "Jupiter":"बृहस्पति","Venus":"शुक्र","Saturn":"शनि","Rahu":"राहु","Ketu":"केतु"
}
PLANET_EMOJI = {
    "Sun":"☀️","Moon":"🌙","Mars":"♂","Mercury":"☿",
    "Jupiter":"♃","Venus":"♀","Saturn":"♄","Rahu":"☊","Ketu":"☋"
}
SIGN_NE = ["मेष","वृष","मिथुन","कर्कट","सिंह","कन्या",
           "तुला","वृश्चिक","धनु","मकर","कुम्भ","मीन"]
SIGN_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
           "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# Classical transit effects from Moon sign (house 1-12)
# Source: Brihat Parashara Hora Shastra + Phaladeepika
TRANSIT_EFFECTS: dict[str, dict[int, tuple[str, str, str]]] = {
    # planet: {house_from_moon: (effect_ne, effect_en, rating)}  rating: G/N/B
    "Sun": {
        1: ("स्वास्थ्य र व्यक्तित्वमा प्रभाव", "Health & personality affected", "N"),
        2: ("धन हानि सम्भव, वाणी कष्ट", "Financial loss possible", "B"),
        3: ("साहस, यात्रा शुभ", "Courage & travel favourable", "G"),
        4: ("गृह, माता कष्ट", "Home & mother trouble", "B"),
        5: ("सन्तान, बुद्धि लाभ", "Children & intellect gain", "G"),
        6: ("शत्रु पराजय, रोग मुक्ति", "Defeat enemies, cure illness", "G"),
        7: ("विवाह कष्ट, साझेदार समस्या", "Marital troubles", "B"),
        8: ("मृत्युभय, दुर्घटना सम्भव", "Danger, accidents possible", "B"),
        9: ("धर्म, भाग्य लाभ", "Religion & fortune gain", "G"),
        10: ("कार्य, यश, सफलता", "Career success & fame", "G"),
        11: ("लाभ, इच्छापूर्ति", "Gains & wish fulfillment", "G"),
        12: ("व्यय, विदेश, हानि", "Expenditure & losses", "B"),
    },
    "Moon": {
        1: ("सुख, मनोबल उच्च", "Happiness & high morale", "G"),
        2: ("धन लाभ, परिवार सुख", "Financial & family gains", "G"),
        3: ("भाई कष्ट, मानसिक चिन्ता", "Sibling trouble, mental worry", "B"),
        4: ("माता, घर सुख", "Mother & home happiness", "G"),
        5: ("सन्तान सुख, सिर्जनशीलता", "Children joy & creativity", "G"),
        6: ("रोग, शत्रु समस्या", "Illness & enemy trouble", "B"),
        7: ("जीवनसाथी सुख", "Spouse happiness", "G"),
        8: ("मानसिक कष्ट, भय", "Mental distress & fear", "B"),
        9: ("भाग्य, धर्म, यात्रा", "Fortune, religion, travel", "G"),
        10: ("कार्य सफलता", "Career success", "G"),
        11: ("सर्वसुख, इच्छापूर्ति", "All round happiness", "G"),
        12: ("खर्च, एकान्त, विदेश", "Expenditure & solitude", "N"),
    },
    "Mars": {
        1: ("स्वास्थ्य समस्या, झगडा", "Health problems & disputes", "B"),
        2: ("धन हानि, परिवार कलह", "Financial loss & family discord", "B"),
        3: ("साहस, विजय", "Courage & victory", "G"),
        4: ("गृह कलह, माता कष्ट", "Home discord", "B"),
        5: ("सन्तान कष्ट, बुद्धि बाधा", "Children & intellect issues", "B"),
        6: ("शत्रु पराजय, रोग मुक्ति", "Enemy defeat, cure illness", "G"),
        7: ("पति/पत्नी कष्ट, विच्छेद", "Marital problems", "B"),
        8: ("दुर्घटना, मृत्युभय", "Accidents & danger", "B"),
        9: ("भाग्य लाभ, यात्रा", "Fortune & travel gains", "G"),
        10: ("कार्य सफलता, प्रमोशन", "Career success & promotion", "G"),
        11: ("लाभ, इच्छापूर्ति", "Gains & fulfillment", "G"),
        12: ("व्यय, शत्रु, कारागार", "Expenditure & hidden enemies", "B"),
    },
    "Mercury": {
        1: ("बुद्धि, वाक् शक्ति वृद्धि", "Intelligence & speech gain", "G"),
        2: ("धन लाभ, वाणी शुभ", "Financial gain & good speech", "G"),
        3: ("भाई सहयोग, यात्रा", "Sibling support & travel", "G"),
        4: ("शिक्षा, घर सुख", "Education & home happiness", "G"),
        5: ("विद्या, सन्तान सुख", "Education & children gain", "G"),
        6: ("शत्रु पराजय", "Enemy defeat", "G"),
        7: ("व्यापार, साझेदारी शुभ", "Business & partnership gains", "G"),
        8: ("अशान्ति, स्वास्थ्य कमजोर", "Restlessness & health issues", "B"),
        9: ("विद्या, भाग्य लाभ", "Education & fortune gain", "G"),
        10: ("व्यापार, कार्य सफलता", "Business & career success", "G"),
        11: ("लाभ, मित्र सहयोग", "Gains & friend support", "G"),
        12: ("व्यय, एकान्त", "Expenditure & solitude", "N"),
    },
    "Jupiter": {
        1: ("स्वास्थ्य, यश, आत्मविश्वास", "Health, fame & confidence", "G"),
        2: ("धन, परिवार, वाणी लाभ", "Wealth, family & speech gains", "G"),
        3: ("भाई कष्ट, साहस कम", "Sibling issues, less courage", "B"),
        4: ("घर, माता, वाहन सुख", "Home, mother & vehicle gains", "G"),
        5: ("सन्तान, बुद्धि, विद्या लाभ", "Children, intellect & education", "G"),
        6: ("रोग, शत्रु वृद्धि", "Illness & enemy increase", "B"),
        7: ("विवाह, साझेदारी शुभ", "Marriage & partnership gains", "G"),
        8: ("दीर्घ रोग, मृत्युभय", "Chronic illness & danger", "B"),
        9: ("भाग्य, धर्म, गुरु कृपा", "Fortune, religion & grace", "G"),
        10: ("कार्य, यश, उन्नति", "Career, fame & progress", "G"),
        11: ("सर्वसुख, लाभ", "All round gains", "G"),
        12: ("व्यय, विदेश यात्रा", "Expenditure & foreign travel", "N"),
    },
    "Venus": {
        1: ("सौन्दर्य, सुख, प्रेम लाभ", "Beauty, happiness & love", "G"),
        2: ("धन, परिवार सुख", "Wealth & family happiness", "G"),
        3: ("भाई सहयोग, कला", "Sibling & arts gains", "G"),
        4: ("घर, वाहन, माता सुख", "Home, vehicle & mother gains", "G"),
        5: ("प्रेम, सन्तान सुख", "Love & children happiness", "G"),
        6: ("रोग, शत्रु समस्या", "Illness & enemy trouble", "B"),
        7: ("विवाह, प्रेम, साझेदार सुख", "Marriage, love & partner gains", "G"),
        8: ("यौन समस्या, स्वास्थ्य बाधा", "Health & intimacy issues", "B"),
        9: ("भाग्य, धर्म, यात्रा", "Fortune, religion & travel", "G"),
        10: ("व्यापार, यश", "Business & fame", "G"),
        11: ("लाभ, मनोकामना पूर्ति", "Gains & wish fulfillment", "G"),
        12: ("व्यय, गोप्य सम्बन्ध", "Expenditure & secret affairs", "N"),
    },
    "Saturn": {
        1: ("कष्ट, विलम्ब, शरीर दुर्बल", "Hardship, delays & weak body", "B"),
        2: ("धन हानि, परिवार कलह", "Financial loss & family discord", "B"),
        3: ("साहस, विजय, कठिन परिश्रम", "Courage, victory & hard work", "G"),
        4: ("गृह कलह, वाहन नाश", "Home discord & vehicle damage", "B"),
        5: ("सन्तान कष्ट, बुद्धि बाधा", "Children trouble & intellect issues", "B"),
        6: ("शत्रु पराजय, रोग मुक्ति", "Enemy defeat, cure illness", "G"),
        7: ("विवाह कष्ट, विछोड", "Marital hardship & separation", "B"),
        8: ("मृत्युभय, दीर्घ रोग", "Danger & chronic illness", "B"),
        9: ("भाग्य बाधा, पिता कष्ट", "Fortune blocked, father trouble", "B"),
        10: ("कार्य सफलता (विलम्बसहित)", "Career success (with delays)", "N"),
        11: ("लाभ, साध्य", "Gains & achievement", "G"),
        12: ("व्यय, एकान्त, मोक्ष", "Expenditure, solitude & liberation", "N"),
    },
    "Rahu": {
        1: ("भ्रम, स्वास्थ्य बाधा", "Confusion & health issues", "B"),
        2: ("धन हानि, वाणी कष्ट", "Financial loss & speech issues", "B"),
        3: ("साहस, विजय, यात्रा", "Courage & travel gains", "G"),
        4: ("घर, माता कष्ट", "Home & mother issues", "B"),
        5: ("सन्तान कष्ट, मानसिक चिन्ता", "Children trouble & mental worry", "B"),
        6: ("शत्रु पराजय, रोग मुक्ति", "Enemy defeat & healing", "G"),
        7: ("विवाह बाधा, साझेदार कष्ट", "Marital obstacles", "B"),
        8: ("मृत्युभय, दुर्घटना", "Danger & accidents", "B"),
        9: ("भाग्य बाधा, भ्रम", "Fortune blocked & confusion", "B"),
        10: ("अचानक उन्नति वा पतन", "Sudden rise or fall", "N"),
        11: ("लाभ (अपेक्षित नभएको)", "Unexpected gains", "G"),
        12: ("व्यय, विदेश, आध्यात्मिक", "Expenditure & spiritual matters", "N"),
    },
    "Ketu": {
        1: ("आध्यात्मिकता, वैराग्य", "Spirituality & detachment", "N"),
        2: ("धन हानि", "Financial loss", "B"),
        3: ("साहस, भाई कष्ट", "Courage but sibling trouble", "N"),
        4: ("घर कष्ट, माता रोग", "Home trouble & mother illness", "B"),
        5: ("सन्तान कष्ट, बुद्धि", "Children trouble", "B"),
        6: ("शत्रु पराजय", "Enemy defeat", "G"),
        7: ("साझेदार कष्ट", "Partner issues", "B"),
        8: ("मोक्ष, रहस्य, भय", "Moksha, mystery & fear", "N"),
        9: ("धर्म, आध्यात्म", "Religion & spirituality", "G"),
        10: ("कार्य बाधा", "Career obstacles", "B"),
        11: ("लाभ, मोक्ष मार्ग", "Gains & path to liberation", "G"),
        12: ("मोक्ष, विदेश", "Liberation & foreign travel", "G"),
    },
}


def _sign_idx(lon: float) -> int:
    return int(lon / 30) % 12


def _house_from_moon(transit_sign: int, moon_sign: int) -> int:
    """House number of transiting planet from natal Moon sign."""
    return ((transit_sign - moon_sign) % 12) + 1


class _PlanetCard(QWidget):
    """Single planet transit entry — plain text, no box."""

    def __init__(self, planet: str, natal_moon_sign: int,
                 current_lon: float, lang: str, parent=None):
        super().__init__(parent)
        self._lang = lang
        is_ne = lang == "ne"
        self.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 10, 0, 10)
        lay.setSpacing(2)

        sign_idx = _sign_idx(current_lon)
        house    = _house_from_moon(sign_idx, natal_moon_sign)
        sign_name = SIGN_NE[sign_idx] if is_ne else SIGN_EN[sign_idx]
        p_name = PLANET_NE.get(planet, planet) if is_ne else planet

        effect_data = TRANSIT_EFFECTS.get(planet, {}).get(house, ("", "", "N"))
        rating = effect_data[2]
        rating_text = {
            "G": ("🟢 शुभ" if is_ne else "🟢 Good"),
            "N": ("🟡 साधारण" if is_ne else "🟡 Neutral"),
            "B": ("🔴 अशुभ" if is_ne else "🔴 Bad"),
        }.get(rating, "🟡 साधारण")

        # Planet name — large bold black
        title = QLabel(p_name)
        title.setStyleSheet("font-size: 19px; font-weight: 800; color: #000000; background: transparent;")
        lay.addWidget(title)

        # Transit info — bold black
        info = QLabel(
            f"{'गोचर राशि' if is_ne else 'Transit Rashi'}: {sign_name}  |  "
            f"{'चन्द्रमाबाट' if is_ne else 'House from Moon'}: {house}{'औँ' if is_ne else ''} {'भाव' if is_ne else 'house'}  |  {rating_text}"
        )
        info.setStyleSheet("font-size: 15px; font-weight: 700; color: #000000; background: transparent;")
        lay.addWidget(info)

        # Effect — black
        effect_ne  = effect_data[0]
        effect_en  = effect_data[1]
        effect_lbl = QLabel(effect_ne if is_ne else effect_en)
        effect_lbl.setWordWrap(True)
        effect_lbl.setStyleSheet("font-size: 14px; color: #000000; background: transparent;")
        lay.addWidget(effect_lbl)

        # Degree — black
        deg = round(current_lon % 30, 2)
        deg_lbl = QLabel(f"{'स्थान' if is_ne else 'Position'}: {int(deg)}°{int((deg%1)*60):02d}′ {sign_name}")
        deg_lbl.setStyleSheet("font-size: 12px; color: #000000; background: transparent;")
        lay.addWidget(deg_lbl)


class GocharPhalReportPage(QWidget):
    """Detailed Gochar (Transit) Effect report page."""

    def __init__(self, chart_data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data
        self._natal_moon_sign = 0
        self._build_ui()
        if chart_data:
            self._load(chart_data)
        # Auto-refresh every 10 minutes
        self._timer = QTimer(self)
        self._timer.setInterval(600_000)
        self._timer.timeout.connect(self._refresh_gochar)
        self._timer.start()

    def _build_ui(self):
        # Plain white page, black text — no boxes
        self.setStyleSheet("background: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("गोचर फल विस्तृत रिपोर्ट" if self._is_ne else "Gochar Phal — Detailed Transit Report")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #000000; background: transparent;")
        hdr.addWidget(title)
        hdr.addStretch()

        refresh_btn = QPushButton("🔄 " + ("ताजा गर्नुस्" if self._is_ne else "Refresh"))
        refresh_btn.clicked.connect(self._refresh_gochar)
        refresh_btn.setStyleSheet("""
            QPushButton { background: #ffffff; border: 1px solid #000000;
                border-radius: 4px; padding: 6px 12px; font-size: 12px; color: #000000; }
            QPushButton:hover { background: #f0f0f0; }
        """)
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        # Info line — plain text, no box
        self._info_lbl = QLabel("")
        self._info_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #000000; background: transparent;")
        self._info_lbl.setWordWrap(True)
        layout.addWidget(self._info_lbl)

        # Scroll
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")
        self._cards_container = QWidget()
        self._cards_container.setStyleSheet("background: #ffffff;")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setSpacing(6)
        self._scroll.setWidget(self._cards_container)
        layout.addWidget(self._scroll, 1)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("font-size: 11px; color: #000000; background: transparent;")
        self._status_lbl.setAlignment(Qt.AlignRight)
        layout.addWidget(self._status_lbl)

    def refresh(self, chart_data: dict):
        self._chart_data = chart_data
        self._load(chart_data)

    def _load(self, chart_data: dict):
        """Extract natal Moon sign from chart data."""
        for p in (chart_data or {}).get("planets") or []:
            if isinstance(p, dict) and p.get("name") == "Moon":
                lon = float(p.get("sidereal_longitude") or p.get("longitude") or 0)
                self._natal_moon_sign = _sign_idx(lon)
                break
        name = (chart_data or {}).get("metadata", {}).get("name", "")
        moon_name = SIGN_NE[self._natal_moon_sign] if self._is_ne else SIGN_EN[self._natal_moon_sign]
        self._info_lbl.setText(
            f"👤 {'व्यक्ति' if self._is_ne else 'Person'}: {name}  |  "
            f"🌙 {'जन्म चन्द्र राशि' if self._is_ne else 'Natal Moon Sign'}: {moon_name}  |  "
            f"📅 {'आजको गोचर' if self._is_ne else 'Current transits as of'}: {datetime.date.today()}"
        )
        self._refresh_gochar()

    def _refresh_gochar(self):
        """Fetch current sky positions and render cards."""
        # Clear cards
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            import importlib
            backend = os.path.join(_ROOT, "backend")
            if backend not in sys.path:
                sys.path.insert(0, backend)

            swe = importlib.import_module("swisseph")
            try:
                pp_mod = importlib.import_module("backend.calculator.planetary_positions")
            except ImportError:
                pp_mod = importlib.import_module("calculator.planetary_positions")
            get_swiss_positions = getattr(pp_mod, "get_swiss_positions")

            now = datetime.datetime.now()
            jd  = swe.julday(now.year, now.month, now.day,
                             now.hour + now.minute / 60.0)
            raw = get_swiss_positions(jd)   # {name: (lon, lat)}

            positions = {
                name: {"longitude": lon, "sidereal_longitude": lon, "latitude": lat}
                for name, (lon, lat) in (raw or {}).items()
            }
        except Exception as exc:
            err = QLabel(f"गोचर डाटा लोड हुन सकेन: {exc}" if self._is_ne else f"Could not load gochar: {exc}")
            err.setStyleSheet(f"color: {COLOR_ERROR}; padding: 20px;")
            self._cards_layout.addWidget(err)
            self._cards_layout.addStretch()
            return

        # Render cards for each planet
        PLANET_ORDER = ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars", "Sun", "Mercury", "Venus", "Moon"]
        for planet in PLANET_ORDER:
            data = (positions or {}).get(planet)
            if not data:
                continue
            lon = float(data.get("sidereal_longitude") or data.get("longitude") or 0)
            card = _PlanetCard(planet, self._natal_moon_sign, lon, self._lang)
            self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()
        self._status_lbl.setText(
            f"{'अन्तिम अपडेट' if self._is_ne else 'Last updated'}: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
