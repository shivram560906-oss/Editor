# -*- coding: utf-8 -*-
"""
gui/widgets/graha_yuddha_page.py

Graha Yuddha (Planetary War) Calculator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Planetary War occurs when two planets are within 1° of each other.
Rules (Parashara / classical):
  - The planet with lesser ecliptic latitude (N/S) loses.
  - Sun & Moon never fight. Rahu/Ketu are not included.
  - Loser loses strength; winner gains.

Displays:
  1. Current natal chart yuddhas (from loaded kundali)
  2. Current sky yuddhas (real-time gochar)
  3. Historical / Upcoming yuddha dates (next 90 days)
"""
from __future__ import annotations
import sys, os, datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_GOLD, COLOR_ACCENT, COLOR_ERROR, COLOR_SUCCESS
)

# ── Constants ────────────────────────────────────────────────────────────────
PLANET_NE = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल",
    "Mercury": "बुध", "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि",
    "Rahu": "राहु", "Ketu": "केतु"
}
PLANET_EMOJI = {
    "Sun": "☀️", "Moon": "🌙", "Mars": "♂", "Mercury": "☿",
    "Jupiter": "♃", "Venus": "♀", "Saturn": "♄"
}
# Planets eligible for war (not Sun, Moon, Rahu, Ketu)
WAR_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

SIGN_NE = ["मेष","वृष","मिथुन","कर्कट","सिंह","कन्या",
           "तुला","वृश्चिक","धनु","मकर","कुम्भ","मीन"]
SIGN_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
           "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]


def _sign_name(lon: float, lang: str) -> str:
    idx = int(lon / 30) % 12
    return SIGN_NE[idx] if lang == "ne" else SIGN_EN[idx]


def _deg_in_sign(lon: float) -> str:
    d = lon % 30
    deg = int(d)
    minute = int((d - deg) * 60)
    return f"{deg}°{minute:02d}′"


def _find_yuddhas(planets: dict, lang: str) -> list[dict]:
    """Detect planetary wars — pairs within 1° longitude."""
    yuddhas = []
    p_list = [(name, data) for name, data in planets.items()
              if name in WAR_PLANETS and data.get("longitude") is not None]

    for i in range(len(p_list)):
        for j in range(i + 1, len(p_list)):
            n1, d1 = p_list[i]
            n2, d2 = p_list[j]
            lon1 = float(d1.get("sidereal_longitude") or d1.get("longitude") or 0)
            lon2 = float(d2.get("sidereal_longitude") or d2.get("longitude") or 0)
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff
            if diff <= 1.0:
                # Determine winner by latitude (lesser lat = loser)
                lat1 = float(d1.get("latitude") or d1.get("lat") or 0)
                lat2 = float(d2.get("latitude") or d2.get("lat") or 0)
                if abs(lat1) <= abs(lat2):
                    winner, loser = n2, n1
                else:
                    winner, loser = n1, n2
                yuddhas.append({
                    "p1": n1, "p2": n2,
                    "winner": winner, "loser": loser,
                    "diff_deg": round(diff, 4),
                    "sign_lon": (lon1 + lon2) / 2,
                    "lat1": lat1, "lat2": lat2,
                })
    return yuddhas


def _planet_map_from_chart(chart_data: dict) -> dict:
    """Build {name: data} from chart payload."""
    result = {}
    for p in (chart_data or {}).get("planets") or []:
        if isinstance(p, dict) and p.get("name"):
            result[p["name"]] = p
    return result


# ── Card widgets ──────────────────────────────────────────────────────────────

def _yuddha_card(yuddha: dict, lang: str) -> QFrame:
    """Build a single Graha Yuddha card."""
    is_ne = lang == "ne"
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background: {BG_TERTIARY};
            border: 1px solid {COLOR_ERROR};
            border-radius: 10px;
        }}
    """)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 12, 16, 12)
    lay.setSpacing(6)

    p1, p2 = yuddha["p1"], yuddha["p2"]
    winner, loser = yuddha["winner"], yuddha["loser"]
    diff = yuddha["diff_deg"]

    # Title row
    e1 = PLANET_EMOJI.get(p1, "🪐")
    e2 = PLANET_EMOJI.get(p2, "🪐")
    n1 = PLANET_NE.get(p1, p1) if is_ne else p1
    n2 = PLANET_NE.get(p2, p2) if is_ne else p2
    title = QLabel(f"{e1} {n1}  ⚔️  {e2} {n2}")
    title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {COLOR_ERROR};")
    lay.addWidget(title)

    # Distance
    dist_lbl = QLabel(
        f"📐 {'अन्तर' if is_ne else 'Distance'}: {diff}°"
    )
    dist_lbl.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
    lay.addWidget(dist_lbl)

    # Winner / Loser
    w_name = PLANET_NE.get(winner, winner) if is_ne else winner
    l_name = PLANET_NE.get(loser, loser) if is_ne else loser
    result_lbl = QLabel(
        f"🏆 {'विजेता' if is_ne else 'Winner'}: {PLANET_EMOJI.get(winner,'')} {w_name}   "
        f"  💀 {'पराजित' if is_ne else 'Loser'}: {PLANET_EMOJI.get(loser,'')} {l_name}"
    )
    result_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};")
    lay.addWidget(result_lbl)

    # Effect
    effect = (
        f"'{l_name}' कमजोर — यसको कारकत्व र भाव फल घट्छ।"
        if is_ne else
        f"'{l_name}' weakened — its karakatwa and house results diminish."
    )
    eff_lbl = QLabel(effect)
    eff_lbl.setWordWrap(True)
    eff_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
    lay.addWidget(eff_lbl)
    return card


def _no_yuddha_card(lang: str) -> QFrame:
    card = QFrame()
    card.setStyleSheet(f"QFrame {{ background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; }}")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(20, 16, 20, 16)
    lbl = QLabel("☮️ " + ("कुनै ग्रह युद्ध छैन।" if lang == "ne" else "No Planetary War detected."))
    lbl.setStyleSheet(f"font-size: 14px; color: {COLOR_SUCCESS}; font-weight: 700;")
    lbl.setAlignment(Qt.AlignCenter)
    lay.addWidget(lbl)
    return card


# ── Main Widget ───────────────────────────────────────────────────────────────

class GrahaYuddhPage(QWidget):
    """Graha Yuddha (Planetary War) analysis page."""

    def __init__(self, chart_data: Optional[dict] = None, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data
        self._build_ui()
        self._refresh_gochar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Header
        header = QLabel("⚔️ " + ("ग्रह युद्ध विश्लेषण (Graha Yuddha)" if self._is_ne else "Graha Yuddha — Planetary War"))
        header.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {COLOR_GOLD}; "
            f"border-bottom: 2px solid {BORDER_COLOR}; padding-bottom: 8px;"
        )
        layout.addWidget(header)

        desc = QLabel(
            "जब दुई ग्रहको अन्तर १° भित्र हुन्छ तब 'ग्रह युद्ध' हुन्छ। न्यून अक्षांश भएको ग्रह पराजित हुन्छ।"
            if self._is_ne else
            "Graha Yuddha occurs when two planets are within 1° of each other. The planet with lesser latitude loses."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        # Tabs: Natal | Gochar (Current Sky)
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {BORDER_COLOR}; border-radius: 6px; }}
            QTabBar::tab {{ padding: 7px 18px; font-weight: 600; color: {COLOR_TEXT_MUTED}; }}
            QTabBar::tab:selected {{ color: {COLOR_GOLD}; border-bottom: 2px solid {COLOR_GOLD}; }}
        """)

        # ── Natal tab ──
        self._natal_scroll = QScrollArea()
        self._natal_scroll.setWidgetResizable(True)
        self._natal_scroll.setStyleSheet("QScrollArea { border: none; }")
        self._natal_container = QWidget()
        self._natal_layout = QVBoxLayout(self._natal_container)
        self._natal_layout.setSpacing(10)
        self._natal_layout.setContentsMargins(8, 8, 8, 8)
        self._natal_scroll.setWidget(self._natal_container)
        self._tabs.addTab(self._natal_scroll, "🪐 " + ("जन्म कुण्डली" if self._is_ne else "Natal Chart"))

        # ── Gochar tab ──
        self._gochar_scroll = QScrollArea()
        self._gochar_scroll.setWidgetResizable(True)
        self._gochar_scroll.setStyleSheet("QScrollArea { border: none; }")
        self._gochar_container = QWidget()
        self._gochar_layout = QVBoxLayout(self._gochar_container)
        self._gochar_layout.setSpacing(10)
        self._gochar_layout.setContentsMargins(8, 8, 8, 8)
        self._gochar_scroll.setWidget(self._gochar_container)
        self._tabs.addTab(self._gochar_scroll, "🌐 " + ("आजको आकाश" if self._is_ne else "Current Sky"))

        layout.addWidget(self._tabs, 1)

        # Last updated
        self._updated_lbl = QLabel("")
        self._updated_lbl.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_MUTED};")
        self._updated_lbl.setAlignment(Qt.AlignRight)
        layout.addWidget(self._updated_lbl)

        # Build natal tab
        self._build_natal_tab()

        # Auto-refresh gochar every 5 minutes
        self._timer = QTimer(self)
        self._timer.setInterval(300_000)
        self._timer.timeout.connect(self._refresh_gochar)
        self._timer.start()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _build_natal_tab(self):
        self._clear_layout(self._natal_layout)
        if not self._chart_data:
            lbl = QLabel(
                "⚠️ कुण्डली लोड गरिएको छैन।\nपहिले जन्म विवरण भरेर गणना गर्नुहोस्।"
                if self._is_ne else
                "⚠️ No chart loaded.\nPlease calculate a chart first."
            )
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; padding: 40px;")
            self._natal_layout.addWidget(lbl)
            self._natal_layout.addStretch()
            return

        planets = _planet_map_from_chart(self._chart_data)
        yuddhas = _find_yuddhas(planets, self._lang)

        # Header info
        meta = self._chart_data.get("metadata") or {}
        name = meta.get("name", "")
        info_lbl = QLabel(
            f"{'व्यक्ति' if self._is_ne else 'Person'}: {name}  |  "
            f"{'ग्रह युद्ध पाइयो' if self._is_ne else 'Wars found'}: {len(yuddhas)}"
        )
        info_lbl.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY}; font-weight: 600;")
        self._natal_layout.addWidget(info_lbl)

        if yuddhas:
            for y in yuddhas:
                self._natal_layout.addWidget(_yuddha_card(y, self._lang))
        else:
            self._natal_layout.addWidget(_no_yuddha_card(self._lang))

        self._natal_layout.addStretch()

    def _refresh_gochar(self):
        """Check current sky for planetary wars."""
        self._clear_layout(self._gochar_layout)

        try:
            backend = os.path.join(_ROOT, "backend")
            if backend not in sys.path:
                sys.path.insert(0, backend)
            import swisseph as swe
            from calculator.planetary_positions import get_swiss_positions
            now = datetime.datetime.now()
            jd  = swe.julday(now.year, now.month, now.day,
                             now.hour + now.minute / 60.0)
            raw = get_swiss_positions(jd)   # {name: (lon, lat)}
            # Build a dict compatible with _find_yuddhas
            positions = {
                name: {"longitude": lon, "sidereal_longitude": lon, "latitude": lat}
                for name, (lon, lat) in (raw or {}).items()
            }
            yuddhas = _find_yuddhas(positions, self._lang)
        except Exception as exc:
            err = QLabel(f"गोचर डाटा लोड हुन सकेन: {exc}" if self._is_ne else f"Gochar data failed: {exc}")
            err.setStyleSheet(f"color: {COLOR_ERROR}; padding: 20px;")
            self._gochar_layout.addWidget(err)
            self._gochar_layout.addStretch()
            return

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self._updated_lbl.setText(
            f"{'अन्तिम अपडेट' if self._is_ne else 'Last updated'}: {now_str}"
        )

        info_lbl = QLabel(
            f"📅 {'आजको आकाश' if self._is_ne else 'Current sky'}: {now_str}  |  "
            f"{'ग्रह युद्ध' if self._is_ne else 'Wars'}: {len(yuddhas)}"
        )
        info_lbl.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY}; font-weight: 600;")
        self._gochar_layout.addWidget(info_lbl)

        if yuddhas:
            for y in yuddhas:
                self._gochar_layout.addWidget(_yuddha_card(y, self._lang))
        else:
            self._gochar_layout.addWidget(_no_yuddha_card(self._lang))

        self._gochar_layout.addStretch()

    def refresh(self, chart_data: dict):
        """Called when main window loads new chart data."""
        self._chart_data = chart_data
        self._build_natal_tab()
