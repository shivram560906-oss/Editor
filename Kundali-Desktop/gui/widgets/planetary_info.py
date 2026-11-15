"""
gui/widgets/planetary_info.py
Port of PlanetaryInfo.jsx — shows planet positions in a rich table.
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QBrush

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY, PLANET_COLORS)
from gui.utils.planet_colors import (planet_abbr, rashi_name, to_nepali_digits,
                                       PLANET_ABBR, RASHI_NAMES, planet_color)

# Legacy Web report contract: these nine fields and their order are stable.
COLS_NE = ["ग्रह", "राशि", "अंश", "भाव", "नक्षत्र", "वक्री", "अस्त", "सम्बन्ध", "स्थिति", "वर्गोत्तम"]
COLS_EN = ["Planet", "Sign", "Degree", "House", "Nakshatra", "Retrograde", "Combust", "Relation", "Status", "Vargottama"]
COLUMN_KEYS = ["planet", "sign", "degree", "house", "nakshatra", "retrograde", "combust", "relation", "status", "vargottama"]
UNAVAILABLE = "—"
STATUS_COLORS = {
    "exalted": "#16a34a",
    "debilitated": "#dc2626",
    "retrograde": "#ea580c",
    "combust": "#dc2626",
    "neutral": COLOR_TEXT_PRIMARY,
}

NAKSHATRAS_NE = [
    "अश्विनी","भरणी","कृत्तिका","रोहिणी","मृगशिरा","आर्द्रा","पुनर्वसु","पुष्य","आश्लेषा",
    "मघा","पूर्वाफाल्गुनी","उत्तराफाल्गुनी","हस्त","चित्रा","स्वाती","विशाखा","अनुराधा","ज्येष्ठा",
    "मूल","पूर्वाषाढा","उत्तराषाढा","श्रवण","धनिष्ठा","शतभिषा","पूर्वाभाद्रपद","उत्तराभाद्रपद","रेवती"
]
NAKSHATRAS_EN = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha",
    "Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Moola","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

RELATION_MAP = {
    "ne": {"own": "स्वग्रही", "friend": "मित्र", "enemy": "शत्रु",
           "neutral": "सम", "maraka": "मारक", "sama": "सम", "": "—"},
    "en": {"own": "Own", "friend": "Friend", "enemy": "Enemy",
           "neutral": "Neutral", "maraka": "Maraka", "sama": "Neutral", "": "—"},
}
EXALT_MAP = {
    "ne": {"exalted": "उच्च ✓", "debilitated": "नीच ✗", "": "—"},
    "en": {"exalted": "Exalted ✓", "debilitated": "Debilitated ✗", "": "—"},
}


def _nakshatra_name(lon: float, language: str) -> str:
    idx = int(lon / (360.0 / 27)) % 27
    return (NAKSHATRAS_NE if language == "ne" else NAKSHATRAS_EN)[idx]


def _ne_digits(n) -> str:
    return to_nepali_digits(n)


def _fmt_deg(deg: float, lang: str) -> str:
    try:
        value = float(deg)
    except (TypeError, ValueError):
        return UNAVAILABLE
    d = int(value)
    m = int((value - d) * 60)
    if lang == "ne":
        return f"{_ne_digits(d)}°{_ne_digits(f'{m:02d}')}′"
    return f"{d}°{m:02d}′"


def build_planetary_model(data: Optional[dict], language: str = "ne") -> dict:
    """Build the stable nine-column report model from payload values only."""
    is_ne = language == "ne"
    if data is None:
        return {"state": "no_chart", "message": "कुण्डली गणना गर्नुहोस्।" if is_ne else "Calculate a chart to view planetary positions.", "columns": COLUMN_KEYS, "rows": []}
    if not isinstance(data, dict):
        return {"state": "error", "message": "अमान्य ग्रह विवरण।" if is_ne else "Invalid planetary data.", "columns": COLUMN_KEYS, "rows": []}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"]), "columns": COLUMN_KEYS, "rows": []}
    planets = data.get("planets")
    if planets is None:
        return {"state": "empty", "message": "ग्रह विवरण उपलब्ध छैन।" if is_ne else "Planetary positions are not available.", "columns": COLUMN_KEYS, "rows": []}
    if not isinstance(planets, list):
        return {"state": "error", "message": "अमान्य ग्रह विवरण।" if is_ne else "Invalid planetary data.", "columns": COLUMN_KEYS, "rows": []}

    rows = []
    for planet in planets:
        if not isinstance(planet, dict):
            continue
        name = str(planet.get("name") or UNAVAILABLE)
        sign_number = planet.get("sign_number")
        sign = planet.get("sign_name") or (rashi_name(sign_number, language) if sign_number else UNAVAILABLE)
        sidereal = planet.get("sidereal_longitude")
        nakshatra = planet.get("nakshatra_name") or planet.get("nakshatra")
        if isinstance(nakshatra, dict):
            nakshatra = nakshatra.get("nepali" if is_ne else "name") or nakshatra.get("name")
        if not nakshatra and sidereal is not None:
            nakshatra = _nakshatra_name(float(sidereal), language)
        retrograde = bool(planet.get("is_retrograde"))
        combust = bool(planet.get("is_combust"))
        relation_key = str(planet.get("relationship") or "").lower()
        status_key = str(planet.get("exaltation_state") or "").lower()
        relation = RELATION_MAP.get(language, RELATION_MAP["en"]).get(relation_key, relation_key or UNAVAILABLE)
        status = EXALT_MAP.get(language, EXALT_MAP["en"]).get(status_key, UNAVAILABLE)
        is_vargottama = bool(planet.get("is_vargottama"))
        values = [
            PLANET_ABBR.get(language, PLANET_ABBR["en"]).get(name, name),
            str(sign),
            _fmt_deg(planet.get("longitude_in_sign"), language),
            _ne_digits(planet.get("house")) if is_ne and planet.get("house") is not None else str(planet.get("house", UNAVAILABLE)),
            str(nakshatra or UNAVAILABLE),
            ("हो" if is_ne else "Yes") if retrograde else UNAVAILABLE,
            ("हो" if is_ne else "Yes") if combust else UNAVAILABLE,
            relation,
            status,
            ("✨ हो" if is_ne else "✨ Yes") if is_vargottama else UNAVAILABLE,
        ]
        rows.append({
            "name": name, "values": values, "retrograde": retrograde, "combust": combust,
            "status": status_key, "planet_color": planet_color(name),
            "status_color": STATUS_COLORS.get(status_key, STATUS_COLORS["neutral"]),
            "is_vargottama": is_vargottama,
        })
    state = "ready" if rows else "empty"
    message = "" if rows else ("ग्रह विवरण उपलब्ध छैन।" if is_ne else "Planetary positions are not available.")
    return {"state": state, "message": message, "columns": COLUMN_KEYS, "rows": rows, "lagna": data.get("lagna") or {}, "metadata": data.get("metadata") or {}}


class PlanetaryInfoPage(QWidget):
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        self.refresh(data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Title
        title = QLabel("🪐 " + ("ग्रह स्थिति विवरण" if self._is_ne else "Planetary Positions"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 17px; font-weight: 700;")
        layout.addWidget(title)

        # Ayanamsha / calc info row
        self._meta_label = QLabel("")
        self._meta_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._meta_label)

        # Main table
        self._state_label = QLabel("")
        self._state_label.setObjectName("planetaryState")
        self._state_label.setAlignment(Qt.AlignCenter)
        self._state_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; padding: 28px;")
        layout.addWidget(self._state_label)

        cols = COLS_NE if self._is_ne else COLS_EN
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setMinimumSectionSize(72)
        self._table.verticalHeader().setDefaultSectionSize(34)
        self._table.setMinimumSize(860, 380)
        layout.addWidget(self._table, 1)

        # Lagna row below
        self._lagna_frame = QFrame()
        self._lagna_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(212,175,55,0.08);
                border: 1px solid rgba(212,175,55,0.25);
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        lagna_layout = QHBoxLayout(self._lagna_frame)
        lagna_layout.setContentsMargins(12, 8, 12, 8)
        self._lagna_details = QLabel("")
        self._lagna_details.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 13px;")
        lagna_layout.addWidget(self._lagna_details)
        layout.addWidget(self._lagna_frame)

    def refresh(self, data: Optional[dict]) -> None:
        self._data = data
        self.model = build_planetary_model(data, self._lang)
        self.state = self.model["state"]
        ready = self.state == "ready"
        self._state_label.setText(self.model["message"])
        self._state_label.setVisible(not ready)
        self._table.setVisible(ready)
        self._lagna_frame.setVisible(ready and bool(self.model.get("lagna")))

        meta = self.model.get("metadata", {})
        ayan = meta.get("ayanamsha_type", "LAHIRI")
        try:
            ayan_value = f"{float(meta.get('ayanamsha_value')):.4f}°"
        except (TypeError, ValueError):
            ayan_value = UNAVAILABLE
        self._meta_label.setText((f"अयनांश: {ayan} = {ayan_value}" if self._is_ne else f"Ayanamsha: {ayan} = {ayan_value}"))
        self._meta_label.setVisible(ready)
        self._table.setRowCount(len(self.model["rows"]))

        for row, row_model in enumerate(self.model["rows"]):
            is_vargo = row_model.get("is_vargottama", False)
            for col, value in enumerate(row_model["values"]):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                # Vargottama rows get a subtle golden background
                if is_vargo:
                    item.setBackground(QBrush(QColor(120, 90, 0, 55)))
                if col == 0:
                    item.setForeground(QBrush(QColor(row_model["planet_color"])))
                    item.setFont(QFont("Noto Sans Devanagari", 11, QFont.Bold))
                elif col == 5 and row_model["retrograde"]:
                    item.setForeground(QBrush(QColor(STATUS_COLORS["retrograde"])))
                    item.setFont(QFont("", 11, QFont.Bold))
                elif col == 6 and row_model["combust"]:
                    item.setForeground(QBrush(QColor(STATUS_COLORS["combust"])))
                elif col == 8:
                    item.setForeground(QBrush(QColor(row_model["status_color"])))
                    if row_model["status"] in ("exalted", "debilitated"):
                        item.setFont(QFont("", 11, QFont.Bold))
                elif col == 9 and is_vargo:
                    item.setForeground(QBrush(QColor("#f59e0b")))
                    item.setFont(QFont("", 11, QFont.Bold))
                self._table.setItem(row, col, item)

        lagna = self.model.get("lagna", {})
        if lagna:
            sign_number = lagna.get("sign_number")
            lag_sign = lagna.get("sign_name") or (rashi_name(sign_number, self._lang) if sign_number else UNAVAILABLE)
            self._lagna_details.setText(
                f"{'लग्न' if self._is_ne else 'Lagna'}: {lag_sign}  {_fmt_deg(lagna.get('longitude_in_sign'), self._lang)}"
            )
