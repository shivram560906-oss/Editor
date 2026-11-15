"""
gui/widgets/north_indian_chart.py

Native Qt port of NorthIndianChart.jsx.
Draws the North Indian diamond-style Kundali chart using QPainter.
Exact same:
  - house centroid positions
  - diagonal line structure
  - planet labels with color, retrograde/combust suffixes
  - special aspect arrows on hover (Mars, Jupiter, Saturn)
  - Ashtakavarga score overlay mode
  - Lagna marker (▲ ल)
"""
from __future__ import annotations
import sys, os, math
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QFrame, QScrollArea, QPushButton, QButtonGroup, QGridLayout
)
from PySide6.QtCore import (
    Qt, QPoint, QPointF, QRectF, QSizeF, Signal, QTimer,
    QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup, Property
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QPolygonF, QFontMetrics, QPalette, QConicalGradient, QRadialGradient, QLinearGradient
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_PRIMARY, BG_SECONDARY, BG_TERTIARY,
                        BORDER_COLOR, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
                        COLOR_TEXT_MUTED, COLOR_ACCENT, PLANET_COLORS)
from gui.utils.planet_colors import (planet_color, planet_abbr, rashi_name,
                                       PLANET_ABBR, RASHI_NAMES)
from gui.widgets.shadbala_bar_widget import ShadbalaMiniBarWidget

# ── Constants matching NorthIndianChart.jsx exactly ─────────────────────────

SPECIAL_ASPECTS = {
    "Mars":    [4, 7, 8],
    "Saturn":  [3, 7, 10],
    "Jupiter": [5, 7, 9],
}

ASPECT_COLORS = {
    "Mars":    "#ff5555",
    "Saturn":  "#88aaff",
    "Jupiter": "#ffcc44",
}

# House centroids in 500×500 viewBox — EXACTLY from NorthIndianChart.jsx
HOUSE_CENTROIDS = {
    1:  (250, 90),
    2:  (130, 50),
    3:  (50,  130),
    4:  (90,  250),
    5:  (50,  370),
    6:  (130, 450),
    7:  (250, 410),
    8:  (370, 450),
    9:  (450, 370),
    10: (410, 250),
    11: (450, 130),
    12: (370, 50),
}

CHART_SIZE = 500   # logical units (viewBox)
CHART_MIN_SIZE = 360
CHART_MAX_SIZE = 560
CHART_BG = "#dce8ff"
CHART_LINE = "#002288"
CHART_SIGN = "#cc0000"
CHART_LAGNA = "#0000cc"
DIGNITY_COLORS = {"strong": "#16a34a", "weak": "#dc2626", "neutral": "#0f172a"}

VARGA_TITLES = {
    "D1": {"en": "Rashi Chart - D1 (Birth Lagna)", "ne": "राशि कुण्डली - D1 (जन्म लग्न)"},
    "D9": {"en": "Navamsha Chart - D9 (Spouse & Dharma)", "ne": "नवांश कुण्डली - D9 (दाम्पत्य र धर्म)"},
    "D10": {"en": "Dashamsha Chart - D10 (Profession & Career)", "ne": "दशमांश कुण्डली - D10 (कर्म र जीविका)"},
}


def chart_payload(data: Optional[dict], varga: str) -> dict:
    """Return one authoritative chart payload without substituting another identity."""
    if not isinstance(data, dict):
        return {}
    if varga == "D1":
        candidate = data.get("vargas", {}).get("D1")
        if isinstance(candidate, dict) and candidate.get("planets"):
            merged = dict(candidate)
            merged.setdefault("metadata", data.get("metadata", {}))
            return merged
        return data
    candidate = data.get("vargas", {}).get(varga)
    return candidate if isinstance(candidate, dict) else {}


def planet_label_positions(planets: list[dict]) -> list[dict]:
    """Stable logical label rectangles shared by paint and all-planet hit testing."""
    positions = []
    for house_num, (lx, ly) in HOUSE_CENTROIDS.items():
        occupants = [p for p in planets if int(p.get("house", 0) or 0) == house_num]
        count = len(occupants)
        logical_font = max(10, 18 - math.floor((count - 1) * 1.2))
        line_height = logical_font + 4
        start_y = ly + 28 - ((count - 1) * line_height) / 2
        for index, planet in enumerate(occupants):
            positions.append({
                "name": planet.get("name", ""), "house": house_num,
                "x": lx, "y": start_y + index * line_height,
                "width": 70, "height": max(20, line_height),
            })
    return positions


def chart_page_model(data: Optional[dict], varga: str, language: str = "ne") -> dict:
    payload = chart_payload(data, varga)
    planets = list(payload.get("planets", []))
    source = data if isinstance(data, dict) else {}
    lagna = payload.get("lagna", {})
    return {
        "identity": varga,
        "title": VARGA_TITLES.get(varga, {}).get(language, varga),
        "payload_available": bool(payload),
        "lagna": lagna,
        "planets": planets,
        "metadata": source.get("metadata", {}),
        "yogas": source.get("parashara_yogas", []) if varga == "D1" else [],
        "aspects": source.get("jaimini", {}).get("sign_aspects", {}) if varga == "D1" else {},
        "dimensions": {"logical": CHART_SIZE, "minimum": CHART_MIN_SIZE, "maximum": CHART_MAX_SIZE},
        "palette": {"background": CHART_BG, "line": CHART_LINE, "sign": CHART_SIGN,
                    "lagna": CHART_LAGNA, "dignity": dict(DIGNITY_COLORS)},
    }


def _aspect_house(from_house: int, offset: int) -> int:
    """Exact port of getAspectHouse() from NorthIndianChart.jsx"""
    return ((from_house - 1 + offset - 1) % 12) + 1


def _to_ne_num(num) -> str:
    NE = ["०","१","२","३","४","५","६","७","८","९"]
    return "".join(NE[int(d)] if d.isdigit() else d for d in str(num))


class NorthIndianChartWidget(QWidget):
    """
    Draws the North Indian diamond-style chart with Vedic cosmic animations.
    Equivalent to the <svg> element in NorthIndianChart.jsx.
    """
    planet_hovered   = Signal(str)   # planet name or ""
    planet_selected  = Signal(str)
    planet_double_clicked = Signal(str)

    # ── Qt Properties for QPropertyAnimation ───────────────────────────────
    def _get_line_progress(self) -> float: return self.__line_progress
    def _set_line_progress(self, v: float):
        self.__line_progress = max(0.0, min(1.0, float(v)))
        self.update()
    line_progress = Property(float, _get_line_progress, _set_line_progress)

    def _get_flash_intensity(self) -> float: return self.__flash_intensity
    def _set_flash_intensity(self, v: float):
        self.__flash_intensity = max(0.0, min(1.0, float(v)))
        self.update()
    flash_intensity = Property(float, _get_flash_intensity, _set_flash_intensity)

    def _get_planet_progress(self) -> float: return self.__planet_progress
    def _set_planet_progress(self, v: float):
        self.__planet_progress = max(0.0, min(1.0, float(v)))
        self.update()
    planet_progress = Property(float, _get_planet_progress, _set_planet_progress)

    # Backwards-compatibility alias for tests and external callers
    def _get_planet_opacity(self) -> float: return self.__planet_progress
    def _set_planet_opacity(self, v: float):
        self._set_planet_progress(v)
    planet_opacity = Property(float, _get_planet_opacity, _set_planet_opacity)

    def __init__(self, chart_data: Optional[dict] = None,
                 varga: str = "D1",
                 language: str = "ne",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._data     = chart_data
        self._varga    = varga
        self._lang     = language
        self._is_ne    = language == "ne"
        self._hovered_planet: Optional[str] = None
        self._selected_planet: Optional[str] = None
        self._sav_scores: Optional[dict] = None   # Ashtakavarga SAV overlay

        # ── Animation state ─────────────────────────────────────────────────
        self.__line_progress: float = 0.0 if chart_data else 1.0
        self.__flash_intensity: float = 0.0
        self.__planet_progress: float = 0.0 if chart_data else 1.0
        self._has_animated: bool = False

        self._lagna_glow: float = 0.0          # 0.0-1.0 sine pulse for House 1
        self._ambient_glow: float = 0.0        # 0.0-1.0 sine pulse for central Brahmasthan
        self._aspect_flow_offset: float = 0.0  # continuous dash offset for flowing drishti rays
        self._hover_ring_angle: float = 0.0    # 0-360 clockwise celestial halo
        self._hover_ring_angle2: float = 0.0   # 0-360 counter-clockwise celestial halo
        self._pulse_tick: int = 0
        self._anim_group: Optional[QSequentialAnimationGroup] = None
        self._pulse_timer: Optional[QTimer] = None

        # 16 drifting celestial stardust particles (pure mathematical elegance)
        self._stardust = [
            {
                "x": 35.0 + (i * 27.3) % 430.0,
                "y": 35.0 + ((i * 33.7) + 15.0) % 430.0,
                "vx": (0.18 + (i % 3) * 0.12) * (1 if i % 2 == 0 else -1),
                "vy": (0.14 + (i % 4) * 0.09) * (1 if (i // 2) % 2 == 0 else -1),
                "phase": i * 0.39,
                "size": 1.4 + (i % 3) * 0.7,
                "is_gold": (i % 2 == 0),
            }
            for i in range(16)
        ]

        self._replay_hovered: bool = False

        self.setMinimumSize(CHART_MIN_SIZE, CHART_MIN_SIZE)
        self.setMaximumSize(CHART_MAX_SIZE, CHART_MAX_SIZE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolTip("Select any planet for details" if not self._is_ne else "विवरणका लागि कुनै पनि ग्रह छान्नुहोस् (डबल क्लिक वा ↻ ले एनिमेसन पुनः देखाउँछ)")
        self.setMouseTracking(True)

        # Start continuous ambient pulse timer (25ms = 40fps)
        self._start_pulse_timer()

        # If chart data passed at construction, trigger animation on first show/load
        if self._data:
            QTimer.singleShot(60, self._play_entry_animation)

    # ── Lifecycle & Public API ────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if self._pulse_timer is not None and not self._pulse_timer.isActive():
            self._pulse_timer.start()
        elif self._pulse_timer is None:
            self._start_pulse_timer()

        if self._data and not self._has_animated:
            self._play_entry_animation()

    def hideEvent(self, event):
        super().hideEvent(event)
        # Power-saving / zero-lag: stop pulse timer immediately when widget is hidden
        if self._pulse_timer is not None and self._pulse_timer.isActive():
            self._pulse_timer.stop()

    def set_data(self, data: dict, varga: str = "D1") -> None:
        self._data = data
        self._varga = varga
        self._has_animated = False
        self._play_entry_animation()

    # ── Supreme Animation Engine ──────────────────────────────────────────────

    def _play_entry_animation(self) -> None:
        """
        Plays the crisp sacred Vedic Kundali manifestation:
        Phase 1: Sacred Geometry Tracing (260ms OutCubic)
        Phase 2: Golden Bloom Flash (180ms OutQuad)
        Phase 3: Celestial Planetary Manifestation (240ms OutBack)
        Fast, responsive, and 0-lag.
        """
        if self._anim_group and self._anim_group.state() != QPropertyAnimation.Stopped:
            self._anim_group.stop()

        self.__line_progress = 0.0
        self.__flash_intensity = 0.0
        self.__planet_progress = 0.0
        self._has_animated = True
        self.update()

        # Phase 1: Sacred line drawing (snappy 260ms)
        line_anim = QPropertyAnimation(self, b"line_progress", self)
        line_anim.setStartValue(0.0)
        line_anim.setEndValue(1.0)
        line_anim.setDuration(260)
        line_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Phase 2 & 3 in parallel: Golden completion flash + Planet manifestation
        par_group = QParallelAnimationGroup(self)

        flash_anim = QPropertyAnimation(self, b"flash_intensity", self)
        flash_anim.setStartValue(1.0)
        flash_anim.setEndValue(0.0)
        flash_anim.setDuration(180)
        flash_anim.setEasingCurve(QEasingCurve.OutQuad)

        planet_anim = QPropertyAnimation(self, b"planet_progress", self)
        planet_anim.setStartValue(0.0)
        planet_anim.setEndValue(1.0)
        planet_anim.setDuration(240)
        planet_anim.setEasingCurve(QEasingCurve.OutBack)

        par_group.addAnimation(flash_anim)
        par_group.addAnimation(planet_anim)

        self._anim_group = QSequentialAnimationGroup(self)
        self._anim_group.addAnimation(line_anim)
        self._anim_group.addPause(15)
        self._anim_group.addAnimation(par_group)
        self._anim_group.start()

    def _start_pulse_timer(self) -> None:
        """Energy-efficient 40ms timer (25 FPS) for ambient cosmic breath and lagna pulse."""
        if self._pulse_timer is not None:
            if not self._pulse_timer.isActive():
                self._pulse_timer.start()
            return
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(40)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start()

    def _tick_pulse(self) -> None:
        self._pulse_tick += 1
        # Lagna heartbeat: periodic sine wave (full cycle ≈ 2.2s)
        self._lagna_glow = (math.sin(self._pulse_tick * 0.08) + 1.0) / 2.0
        # Brahmasthan central sanctuary breath: slow serenity (full cycle ≈ 3.5s)
        self._ambient_glow = (math.sin(self._pulse_tick * 0.05) + 1.0) / 2.0
        # Dynamic flowing light rays for aspects
        self._aspect_flow_offset = (self._aspect_flow_offset + 1.2) % 32.0
        # Hover celestial halos
        if self._hovered_planet:
            self._hover_ring_angle = (self._hover_ring_angle + 6.0) % 360.0
            self._hover_ring_angle2 = (self._hover_ring_angle2 - 4.5) % 360.0

        # Drift celestial stardust
        for p in self._stardust:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < 25.0: p["x"] = 475.0
            elif p["x"] > 475.0: p["x"] = 25.0
            if p["y"] < 25.0: p["y"] = 475.0
            elif p["y"] > 475.0: p["y"] = 25.0

        self.update()

    def set_sav_scores(self, scores: Optional[dict]) -> None:
        self._sav_scores = scores
        self.update()

    def set_selected_planet(self, name: Optional[str]) -> None:
        self._selected_planet = name
        self.update()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _scale(self) -> float:
        """Scale factor from logical 500px to widget pixels."""
        side = min(self.width(), self.height())
        return side / CHART_SIZE

    def _pt(self, lx: float, ly: float) -> QPointF:
        """Convert logical coords to widget coords."""
        s = self._scale()
        ox = (self.width()  - CHART_SIZE * s) / 2
        oy = (self.height() - CHART_SIZE * s) / 2
        return QPointF(ox + lx * s, oy + ly * s)

    def _replay_btn_rect(self) -> QRectF:
        """Position of the sleek replay button in top-right corner."""
        s = self._scale()
        pt = self._pt(468, 24)
        r = max(11.0, 14.0 * s)
        return QRectF(pt.x() - r, pt.y() - r, r * 2, r * 2)

    def _is_replay_hit(self, pos: QPoint) -> bool:
        rect = self._replay_btn_rect()
        return rect.contains(QPointF(pos.x(), pos.y()))

    def _get_planets_in_house(self, house_num: int) -> list[dict]:
        if not self._data:
            return []
        planets = self._get_varga_planets()
        return [p for p in planets if p.get("house") == house_num]

    def _get_varga_planets(self) -> list:
        if not self._data:
            return []
        if self._varga == "D1":
            return chart_payload(self._data, "D1").get("planets", [])
        if self._varga == "Moon":
            planets = self._data.get("planets", [])
            moon_lagna = self._get_lagna_sign()
            moon_planets = []
            for p in planets:
                p_copy = p.copy()
                sign = p.get("sign_number", 1)
                p_copy["house"] = ((sign - moon_lagna) % 12) + 1
                moon_planets.append(p_copy)
            return moon_planets
        vargas = self._data.get("vargas", {})
        v_data = vargas.get(self._varga)
        if isinstance(v_data, dict) and "planets" in v_data:
            return v_data["planets"]
        elif isinstance(v_data, list):
            return v_data
        return self._data.get("planets", [])

    def _get_lagna_sign(self) -> int:
        if not self._data:
            return 1
        if self._varga == "D1":
            return chart_payload(self._data, "D1").get("lagna", {}).get("sign_number", 1)
        if self._varga == "Moon":
            for p in self._data.get("planets", []):
                if p.get("name") == "Moon":
                    return p.get("sign_number", 1)
            return 1
        vargas = self._data.get("vargas", {})
        v_data = vargas.get(self._varga)
        if isinstance(v_data, dict) and "lagna" in v_data:
            return v_data["lagna"].get("sign_number", 1)
        v = vargas.get(self._varga + "_lagna", {})
        if isinstance(v, dict):
            return v.get("sign_number", self._data.get("lagna", {}).get("sign_number", 1))
        return self._data.get("lagna", {}).get("sign_number", 1)

    def _get_sign_for_house(self, house_num: int) -> int:
        lagna = self._get_lagna_sign()
        return ((lagna - 1 + house_num - 1) % 12) + 1

    def _format_num(self, n) -> str:
        return _to_ne_num(n) if self._is_ne else str(n)

    # ── Mouse events ──────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        if not self._data:
            return
        # Check replay button hover
        is_rep = self._is_replay_hit(event.pos())
        if is_rep != self._replay_hovered:
            self._replay_hovered = is_rep
            self.setCursor(Qt.PointingHandCursor if is_rep else Qt.ArrowCursor)
            self.update()
            if is_rep:
                return

        hit = self._planet_at(event.pos())
        if hit != self._hovered_planet:
            self._hovered_planet = hit
            self.planet_hovered.emit(hit or "")
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._is_replay_hit(event.pos()):
                self._play_entry_animation()
                return
            hit = self._planet_at(event.pos())
            if hit:
                self._selected_planet = hit
                self.planet_selected.emit(hit)
                self.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            hit = self._planet_at(event.pos())
            if hit:
                self._selected_planet = hit
                self.planet_selected.emit(hit)
                self.planet_double_clicked.emit(hit)
            else:
                # Double-clicking on chart background replays the cosmic animation!
                self._play_entry_animation()
            self.update()

    def leaveEvent(self, event):
        self._hovered_planet = None
        self._replay_hovered = False
        self.setCursor(Qt.ArrowCursor)
        self.planet_hovered.emit("")
        self.update()

    def _planet_at(self, pos: QPoint) -> Optional[str]:
        """Return planet name at widget position, or None."""
        if not self._data:
            return None
        s = self._scale()
        planets = self._get_varga_planets()

        # 1. Check label rectangles with hit padding
        for hit in planet_label_positions(planets):
            pt = self._pt(hit["x"], hit["y"])
            half_w = max(50.0, (hit["width"] * s) / 2 + 15)
            half_h = max(20.0, (hit["height"] * s) / 2 + 10)
            if abs(pos.x() - pt.x()) <= half_w and abs(pos.y() - pt.y()) <= half_h:
                return hit["name"] or None

        # 2. Check distance to planet center positions
        best_p = None
        min_dist = max(35.0, 45.0 * s)
        for hit in planet_label_positions(planets):
            pt = self._pt(hit["x"], hit["y"])
            dist = math.hypot(pos.x() - pt.x(), pos.y() - pt.y())
            if dist < min_dist:
                min_dist = dist
                best_p = hit["name"]
        if best_p:
            return best_p

        # 3. Check house centroid proximity
        for house_num, (lx, ly) in HOUSE_CENTROIDS.items():
            pt = self._pt(lx, ly)
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) < max(40.0, 60.0 * s):
                house_planets = [p for p in planets if int(p.get("house", 0) or 0) == house_num]
                if house_planets:
                    return house_planets[0].get("name")

        return None

    # ── Paint Pipeline ────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        if not self._data:
            self._draw_empty(painter)
            painter.end()
            return

        self._draw_background(painter)
        self._draw_stardust(painter)
        self._draw_grid_lines(painter)
        self._draw_lagna_glow(painter)

        active_aspect_planet = (
            self._hovered_planet if (self._hovered_planet and self._hovered_planet in SPECIAL_ASPECTS)
            else (self._selected_planet if (self._selected_planet and self._selected_planet in SPECIAL_ASPECTS) else None)
        )
        if active_aspect_planet:
            self._draw_aspect_arrows(painter, active_aspect_planet)

        self._draw_house_labels(painter)
        self._draw_replay_button(painter)
        painter.end()

    def _draw_empty(self, painter: QPainter):
        painter.fillRect(self.rect(), QColor(CHART_BG))
        painter.setPen(QColor("#475569"))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(self.rect(), Qt.AlignCenter,
                         "कुण्डली गणना गर्नुहोस्" if self._is_ne else "Calculate chart first")

    def _draw_background(self, painter: QPainter):
        s = self._scale()
        painter.fillRect(self.rect(), QColor(CHART_BG))

        # Sacred Brahmasthan (Kendra / Vishnu-sthana) central breathing aura
        c_pt = self._pt(250, 250)
        grad_r = max(60, int(135 * s))
        grad = QRadialGradient(c_pt, grad_r)
        alpha = int(18 + self._ambient_glow * 32)
        grad.setColorAt(0.0, QColor(245, 158, 11, alpha))              # Golden sanctum
        grad.setColorAt(0.50, QColor(59, 130, 246, int(alpha * 0.45))) # Celestial azure
        grad.setColorAt(1.0, QColor(220, 232, 255, 0))                 # Outer edge
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(c_pt, grad_r, grad_r)

    def _draw_stardust(self, painter: QPainter):
        """Floating celestial stardust particles giving an alive Vedic cosmic aura."""
        s = self._scale()
        painter.setPen(Qt.NoPen)
        for p in self._stardust:
            pt = self._pt(p["x"], p["y"])
            twinkle = (math.sin(self._pulse_tick * 0.06 + p["phase"]) + 1.0) / 2.0
            alpha = int(25 + twinkle * 85)
            r = max(1.2, p["size"] * s)
            if p["is_gold"]:
                color = QColor(245, 158, 11, alpha)
            else:
                color = QColor(56, 189, 248, alpha)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pt, r, r)

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1: Sacred Line Tracing + Luminous Jyoti-Tip + Golden Flash
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_grid_lines(self, painter: QPainter):
        s = self._scale()
        p = self.__line_progress
        flash = self.__flash_intensity

        segments = [
            # Outer boundary square (progress 0–0.40)
            ((10, 10), (490, 10)),
            ((490, 10), (490, 490)),
            ((490, 490), (10, 490)),
            ((10, 490), (10, 10)),
            # Main diagonal axes (progress 0.40–0.65)
            ((10, 10), (490, 490)),
            ((10, 490), (490, 10)),
            # Inner diamond lines (progress 0.65–1.0)
            ((250, 10), (10, 250)),
            ((10, 250), (250, 490)),
            ((250, 490), (490, 250)),
            ((490, 250), (250, 10)),
        ]
        n = len(segments)
        seg_width = 1.0 / n

        base_line_color = QColor(CHART_LINE)
        core_pen_width = max(1, int(s * 1.5))
        active_tip: Optional[QPointF] = None

        for idx, (seg_s, seg_e) in enumerate(segments):
            seg_start = idx * seg_width
            seg_end = seg_start + seg_width
            if p <= seg_start:
                break

            local = min(1.0, (p - seg_start) / seg_width)
            s_pt = self._pt(seg_s[0], seg_s[1])
            e0_pt = self._pt(seg_e[0], seg_e[1])
            cur_ex = s_pt.x() + (e0_pt.x() - s_pt.x()) * local
            cur_ey = s_pt.y() + (e0_pt.y() - s_pt.y()) * local
            cur_end = QPointF(cur_ex, cur_ey)

            if local < 1.0 and p < 1.0:
                active_tip = cur_end

            # Pass 1: Luminous Golden / Celestial Glow trail
            glow_alpha = 0
            if local < 1.0 and p < 1.0:
                glow_alpha = 150
            elif flash > 0.0:
                glow_alpha = int(flash * 190)

            if glow_alpha > 0:
                glow_pen = QPen(QColor(245, 158, 11, glow_alpha))
                glow_pen.setWidth(max(3, int(s * 4.5)))
                glow_pen.setCapStyle(Qt.RoundCap)
                painter.setPen(glow_pen)
                painter.drawLine(s_pt, cur_end)

            # Pass 2: Sharp Core Stroke
            if flash > 0.0:
                core_color = QColor(
                    int(base_line_color.red() * (1.0 - flash) + 251 * flash),
                    int(base_line_color.green() * (1.0 - flash) + 191 * flash),
                    int(base_line_color.blue() * (1.0 - flash) + 36 * flash),
                )
            else:
                core_color = base_line_color

            core_pen = QPen(core_color, core_pen_width)
            core_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(core_pen)
            painter.drawLine(s_pt, cur_end)

        # Draw radiant Jyoti-Bindu (comet head) at drawing tip
        if active_tip is not None:
            tip_r = max(8, int(13 * s))
            flare = QRadialGradient(active_tip, tip_r)
            flare.setColorAt(0.0, QColor(255, 255, 255, 255))
            flare.setColorAt(0.35, QColor(254, 240, 138, 220))
            flare.setColorAt(0.70, QColor(245, 158, 11, 150))
            flare.setColorAt(1.0, QColor(245, 158, 11, 0))
            painter.setBrush(QBrush(flare))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(active_tip, tip_r, tip_r)

            # Bright center spark
            painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
            painter.drawEllipse(active_tip, max(2.0, 2.6 * s), max(2.0, 2.6 * s))

        # Four Vedic Corner Flourishes
        self._draw_corner_accents(painter, s, flash)

    def _draw_corner_accents(self, painter: QPainter, s: float, flash: float):
        if self.__line_progress < 0.35:
            return
        corners = [(10, 10), (490, 10), (490, 490), (10, 490)]
        d_size = max(4.0, 6.0 * s)
        c_alpha = int(180 + flash * 75) if flash > 0 else 180
        col = QColor(217, 119, 6, c_alpha) if flash > 0 else QColor(30, 58, 138, 140)

        for cx, cy in corners:
            pt = self._pt(cx, cy)
            poly = QPolygonF([
                QPointF(pt.x(), pt.y() - d_size),
                QPointF(pt.x() + d_size, pt.y()),
                QPointF(pt.x(), pt.y() + d_size),
                QPointF(pt.x() - d_size, pt.y()),
            ])
            painter.setBrush(QBrush(col))
            painter.setPen(QPen(QColor(245, 158, 11 if flash > 0 else 29, 78, 216), max(1, int(1.2 * s))))
            painter.drawPolygon(poly)

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2: Lagna (House 1) Sacred Aura & Pulse
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_lagna_glow(self, painter: QPainter):
        """Draw a majestic celestial aura around Lagna house (Tanu Bhava / House 1)."""
        if self.__line_progress < 0.4:
            return
        lx, ly = HOUSE_CENTROIDS[1]
        center = self._pt(lx, ly)
        s = self._scale()

        # Outer diffuse breathing halo
        glow_r = max(42, int(60 * s))
        alpha_outer = int(20 + self._lagna_glow * 60)
        grad = QRadialGradient(center, glow_r)
        grad.setColorAt(0.0, QColor(37, 99, 235, alpha_outer))
        grad.setColorAt(0.55, QColor(245, 158, 11, int(alpha_outer * 0.45)))
        grad.setColorAt(1.0, QColor(37, 99, 235, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(center, glow_r, glow_r)

        # Concentric golden pulse ring
        ring_r = max(26, int((34 + self._lagna_glow * 6) * s))
        alpha_ring = int(60 + self._lagna_glow * 110)
        ring_pen = QPen(QColor(245, 158, 11, alpha_ring), max(1, int(1.8 * s)))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(ring_pen)
        painter.drawEllipse(center, ring_r, ring_r)

    # ─────────────────────────────────────────────────────────────────────────
    # Dynamic Flowing Liquid Light Aspects
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_aspect_arrows(self, painter: QPainter, p_name: Optional[str] = None):
        if p_name is None:
            p_name = self._hovered_planet or self._selected_planet
        if not p_name or p_name not in SPECIAL_ASPECTS:
            return
        planets = self._get_varga_planets()
        planet_data = next((p for p in planets if p.get("name") == p_name), None)
        if not planet_data:
            return
        from_house = planet_data.get("house", 1)
        color = QColor(ASPECT_COLORS.get(p_name, "#ffffff"))

        # Anchor origin precisely at the active planet label's coordinate (not the generic house centroid!)
        src_pt: Optional[QPointF] = None
        for hit in planet_label_positions(planets):
            if hit.get("name") == p_name:
                src_pt = self._pt(hit["x"], hit["y"])
                break
        if src_pt is None:
            fx, fy = HOUSE_CENTROIDS[from_house]
            src_pt = self._pt(fx, fy)

        offsets = SPECIAL_ASPECTS[p_name]
        for offset in offsets:
            to_house = _aspect_house(from_house, offset)
            tx, ty = HOUSE_CENTROIDS[to_house]
            to_pt = self._pt(tx, ty)

            dx = to_pt.x() - src_pt.x()
            dy = to_pt.y() - src_pt.y()
            mx = (src_pt.x() + to_pt.x()) / 2.0
            my = (src_pt.y() + to_pt.y()) / 2.0
            length = math.sqrt(dx * dx + dy * dy) or 1
            px_off = (-dy / length) * 35.0 * self._scale()
            py_off = (dx  / length) * 35.0 * self._scale()

            path = QPainterPath()
            path.moveTo(src_pt)
            path.quadTo(QPointF(mx + px_off, my + py_off), to_pt)

            # Flowing liquid light ray effect: animated dash offset
            glow_pen = QPen(color, max(3, int(self._scale() * 4)))
            glow_pen.setColor(QColor(color.red(), color.green(), color.blue(), 75))
            glow_pen.setStyle(Qt.CustomDashLine)
            glow_pen.setDashPattern([7.0, 4.0])
            glow_pen.setDashOffset(self._aspect_flow_offset)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            core_pen = QPen(color, max(2, int(self._scale() * 2.2)))
            core_pen.setStyle(Qt.CustomDashLine)
            core_pen.setDashPattern([7.0, 4.0])
            core_pen.setDashOffset(self._aspect_flow_offset)
            painter.setPen(core_pen)
            painter.drawPath(path)

            # Arrowhead at target
            arrow_pt = to_pt
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            arrow_size = max(7, int(self._scale() * 8))
            poly = QPolygonF([
                QPointF(arrow_pt.x(), arrow_pt.y()),
                QPointF(arrow_pt.x() - arrow_size, arrow_pt.y() - arrow_size // 2),
                QPointF(arrow_pt.x() - arrow_size, arrow_pt.y() + arrow_size // 2),
            ])
            painter.drawPolygon(poly)

            # Target house incoming energy resonance ring
            res_pulse = (math.sin(self._pulse_tick * 0.15) + 1.0) / 2.0
            r = max(22, int((33 + res_pulse * 6) * self._scale()))
            hl_color = QColor(color)
            hl_color.setAlpha(int(35 + res_pulse * 40))
            painter.setPen(QPen(color, max(1, int(1.8 * self._scale()))))
            painter.setBrush(QBrush(hl_color))
            painter.drawEllipse(to_pt, r, r)

            # Offset badge (number)
            badge_x = mx + (-dy / length) * 40.0 * self._scale()
            badge_y = my + (dx  / length) * 40.0 * self._scale()
            badge_center = QPointF(badge_x, badge_y)
            badge_r = max(11, int(15 * self._scale()))
            badge_bg = QColor(BG_PRIMARY)
            badge_bg.setAlpha(225)
            painter.setPen(QPen(color, 1.5))
            painter.setBrush(QBrush(badge_bg))
            painter.drawEllipse(badge_center, badge_r, badge_r)
            painter.setPen(color)
            font = QFont("Segoe UI", max(8, int(11 * self._scale())), QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(badge_center.x() - badge_r, badge_center.y() - badge_r,
                       badge_r * 2, badge_r * 2),
                Qt.AlignCenter, str(offset)
            )

        # Highlight source planet precisely (Centered on active planet position, NOT house centroid!)
        src_color = QColor(ASPECT_COLORS.get(p_name, "#ffffff"))
        src_hl = QColor(src_color)
        src_hl.setAlpha(45)
        painter.setPen(QPen(src_color, max(1.5, 2.2 * self._scale())))
        painter.setBrush(QBrush(src_hl))
        r = max(18, int(26 * self._scale()))
        painter.drawEllipse(src_pt, r, r)

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 3: Staggered Planetary Descent & Celestial House Manifestation
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_house_labels(self, painter: QPainter):
        planets = self._get_varga_planets()
        sav_mode = bool(self._sav_scores)
        prog = self.__planet_progress
        s = self._scale()

        # Track global planet index for staggered arrival
        total_p_idx = 0

        for house_num, (lx, ly) in HOUSE_CENTROIDS.items():
            sign = self._get_sign_for_house(house_num)
            house_planets = [p for p in planets if p.get("house") == house_num]
            is_lagna = house_num == 1

            # ── SAV overlay mode ──
            if sav_mode:
                sav_val = self._sav_scores.get(house_num, "—")
                card_rect = QRectF(self._pt(lx - 40, ly - 32), self._pt(lx + 40, ly + 40))
                card_color = QColor(BG_SECONDARY)
                card_color.setAlpha(200)
                painter.setBrush(QBrush(card_color))
                painter.setPen(QPen(QColor(BORDER_COLOR), 1))
                painter.drawRoundedRect(card_rect, 8, 8)
                painter.setPen(QColor(COLOR_TEXT_PRIMARY))
                font = QFont("Noto Sans Devanagari", max(12, int(22 * s)), QFont.Black)
                painter.setFont(font)
                painter.drawText(
                    QRectF(self._pt(lx - 40, ly - 20), self._pt(lx + 40, ly + 30)),
                    Qt.AlignCenter, self._format_num(sav_val)
                )
                continue

            # ── Sign number (fade & gentle scale) ──
            h_thresh = (house_num - 1) / 24.0
            if prog > h_thresh:
                sign_alpha_factor = min(1.0, (prog - h_thresh) / 0.25)
                sign_y = ly - 28
                sign_label = self._format_num(sign)
                sign_font = QFont("Segoe UI", max(9, int(13 * s)), QFont.Bold)
                sign_color = QColor(CHART_SIGN)
                sign_color.setAlpha(int(255 * sign_alpha_factor))
                painter.setFont(sign_font)
                painter.setPen(sign_color)
                sign_rect = QRectF(self._pt(lx - 30, sign_y - 12), self._pt(lx + 30, sign_y + 12))
                painter.drawText(sign_rect, Qt.AlignCenter, sign_label)

            # ── Lagna marker (▲ ल) ──
            if is_lagna and prog > 0.05:
                lagna_alpha = min(1.0, prog / 0.3)
                lagna_text = "▲ ल" if self._is_ne else "▲ L"
                marker_font = QFont("Segoe UI", max(7, int(11 * s)), QFont.Bold)
                painter.setFont(marker_font)
                m_color = QColor(0, 60, 210, int(255 * lagna_alpha))
                painter.setPen(m_color)
                marker_rect = QRectF(
                    self._pt(lx - 30, ly - 56),
                    self._pt(lx + 30, ly - 38)
                )
                painter.drawText(marker_rect, Qt.AlignCenter, lagna_text)

            # ── Planet labels with Staggered Elastic Pop-in ──
            if not house_planets:
                continue

            planet_count = len(house_planets)
            logical_font_size = max(11, 18 - math.floor((planet_count - 1) * 1.1))
            planet_font_size = max(8, int(logical_font_size * s))
            logical_line_height = logical_font_size + 7
            start_y = ly + 28 - ((planet_count - 1) * logical_line_height) / 2

            for i, planet in enumerate(house_planets):
                total_p_idx += 1
                p_name = planet.get("name", "")
                abbr = PLANET_ABBR.get(self._lang, PLANET_ABBR["ne"]).get(p_name, p_name[:2])

                # Suffix for retrograde/combust
                is_retro = planet.get("is_retrograde", False)
                is_comb  = planet.get("is_combust",    False)
                if is_retro and is_comb:
                    suffix = "(ब,अ)" if self._is_ne else "(R,C)"
                elif is_retro:
                    suffix = "(ब)" if self._is_ne else "(R)"
                elif is_comb:
                    suffix = "(अ)" if self._is_ne else "(C)"
                else:
                    suffix = ""
                label = f"{abbr}{suffix}"

                is_special = p_name in SPECIAL_ASPECTS
                is_hovered = self._hovered_planet == p_name
                is_selected = self._selected_planet == p_name

                # Staggered entry calculation
                p_thresh = 0.08 + (total_p_idx % 9) * 0.07
                if prog <= p_thresh:
                    continue   # planet has not manifested yet

                sub_p = min(1.0, (prog - p_thresh) / 0.35)
                # OutBack spring bounce formula: 1 + c3*(t)^3 + c1*(t)^2
                t = sub_p - 1.0
                bounce_scale = max(0.0, 1.0 + 2.70158 * (t ** 3) + 1.70158 * (t ** 2))
                if is_hovered:
                    bounce_scale *= 1.14

                planet_y_logical = start_y + i * logical_line_height
                center_pt = self._pt(lx, planet_y_logical)

                # Color logic
                if is_hovered or is_special:
                    color = QColor(ASPECT_COLORS.get(p_name, COLOR_TEXT_PRIMARY))
                else:
                    rel = planet.get("relationship", "")
                    exalt = planet.get("exaltation_state", "")
                    if exalt == "exalted" or rel in ("own", "friend"):
                        color = QColor(PLANET_COLORS.get("Mercury", "#22c55e"))
                    elif exalt == "debilitated" or rel in ("enemy",):
                        color = QColor(PLANET_COLORS.get("Mars", "#ef4444"))
                    else:
                        color = QColor(COLOR_TEXT_PRIMARY)

                # Cosmic Shockwave Arrival Ripple
                if sub_p < 0.85:
                    ripple_r = max(10, int((14 + 28 * sub_p) * s))
                    ripple_alpha = int((1.0 - sub_p) * 140)
                    r_pen = QPen(QColor(color.red(), color.green(), color.blue(), ripple_alpha), max(1, int(1.5 * s)))
                    painter.setPen(r_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(center_pt, ripple_r, ripple_r)

                # Save painter state to apply spring scale around planet center
                painter.save()
                painter.translate(center_pt.x(), center_pt.y())
                painter.scale(bounce_scale, bounce_scale)
                painter.translate(-center_pt.x(), -center_pt.y())

                # Hovered Celestial Dual-Ring Halo
                if is_hovered:
                    # Glassmorphic pill backing
                    hl_w = 36 * s
                    hl_h = (logical_line_height / 2 + 3) * s
                    hl_rect = QRectF(center_pt.x() - hl_w, center_pt.y() - hl_h, hl_w * 2, hl_h * 2)
                    hl_col = QColor(ASPECT_COLORS.get(p_name, "#ffffff"))
                    hl_col.setAlpha(45)
                    painter.setBrush(QBrush(hl_col))
                    painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 140), max(1, int(1.2 * s))))
                    painter.drawRoundedRect(hl_rect, 6, 6)

                    # Rotating dual celestial rings
                    ring_r1 = max(18, int(26 * s))
                    arc_pen1 = QPen(color, max(2, int(2.4 * s)), Qt.SolidLine, Qt.RoundCap)
                    painter.setPen(arc_pen1)
                    painter.setBrush(Qt.NoBrush)
                    arc_rect1 = QRectF(center_pt.x() - ring_r1, center_pt.y() - ring_r1, ring_r1 * 2, ring_r1 * 2)
                    start1 = int(self._hover_ring_angle * 16)
                    painter.drawArc(arc_rect1, start1, 120 * 16)
                    painter.drawArc(arc_rect1, start1 + 180 * 16, 120 * 16)

                    # Counter-rotating outer dashed ring
                    ring_r2 = max(22, int(32 * s))
                    arc_pen2 = QPen(QColor(color.red(), color.green(), color.blue(), 130), max(1, int(1.5 * s)), Qt.DashLine, Qt.RoundCap)
                    painter.setPen(arc_pen2)
                    arc_rect2 = QRectF(center_pt.x() - ring_r2, center_pt.y() - ring_r2, ring_r2 * 2, ring_r2 * 2)
                    start2 = int(self._hover_ring_angle2 * 16)
                    painter.drawArc(arc_rect2, start2, 90 * 16)
                    painter.drawArc(arc_rect2, start2 + 180 * 16, 90 * 16)

                # Draw planet label text
                font_weight = QFont.ExtraBold if (is_special or is_hovered) else QFont.Bold
                font = QFont(["Nirmala UI", "Segoe UI Historic", "Mangal", "Noto Sans Devanagari", "Segoe UI"])
                font.setPointSize(max(1, planet_font_size))
                font.setWeight(font_weight)
                font.setStyleStrategy(QFont.PreferAntialias)
                painter.setFont(font)
                painter.setPen(color)

                box_pad_v = max(12.0, (logical_line_height / 2.0) + 4.0)
                text_rect = QRectF(
                    self._pt(lx - 42, planet_y_logical - box_pad_v),
                    self._pt(lx + 42, planet_y_logical + box_pad_v)
                )
                painter.drawText(text_rect, Qt.AlignCenter, label)

                # Selected Planet Golden/Accent Seal
                if is_selected:
                    sel_pen = QPen(QColor(COLOR_ACCENT), max(1, int(1.8 * s)))
                    painter.setPen(sel_pen)
                    painter.setBrush(Qt.NoBrush)
                    sel_rect = QRectF(
                        self._pt(lx - 34, planet_y_logical - (logical_line_height / 2 + 1)),
                        self._pt(lx + 34, planet_y_logical + (logical_line_height / 2 + 2))
                    )
                    painter.drawRoundedRect(sel_rect, 5, 5)

                # Special aspect indicator dot
                if is_special and not is_hovered:
                    dot_pt = self._pt(lx + 18, planet_y_logical - 8)
                    dot_r = max(2, int(3.5 * s))
                    dot_color = QColor(ASPECT_COLORS.get(p_name, "#888"))
                    painter.setBrush(QBrush(dot_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(dot_pt, dot_r, dot_r)

                painter.restore()

    # ─────────────────────────────────────────────────────────────────────────
    # Sleek Replay Button
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_replay_button(self, painter: QPainter):
        """Draws an elegant, discrete replay icon button in the top-right corner."""
        rect = self._replay_btn_rect()
        s = self._scale()

        # Background pill/circle
        bg_col = QColor(255, 255, 255, 210 if self._replay_hovered else 110)
        border_col = QColor(245, 158, 11 if self._replay_hovered else 147, 197, 253, 180)
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, max(1, int(1.2 * s))))
        painter.drawEllipse(rect)

        # Icon '↻'
        icon_col = QColor(217, 119, 6 if self._replay_hovered else 30, 58, 138)
        painter.setPen(icon_col)
        font = QFont("Segoe UI", max(9, int(12 * s)), QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, "↻")


# ── Page wrapper ─────────────────────────────────────────────────────────────

class NorthIndianChartPage(QWidget):
    """
    Complete Page for North Indian Kundali charts (Rashi D1, Navamsha D9, etc.).
    Displays:
      - Left: Clean North Indian Chart (no outer border box, left aligned)
      - Middle: Classical Shadbala dual-zone bar graph
      - Right: Planet Analysis summary + Dignity Legend
      - Bottom: Chart Status, Aspects, and Yogas
    """
    def __init__(self, data: Optional[dict],
                 varga: str = "D1",
                 language: str = "ne",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._data  = data or {}
        self._varga = varga
        self._lang  = language
        self._is_ne = language == "ne"
        self._model = chart_page_model(self._data, varga, language)
        self._selected_planet_name: Optional[str] = None
        self._build_ui()
        self.refresh(self._data)

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)
        heading = QLabel(title)
        heading.setStyleSheet(f"color:{COLOR_GOLD};font-size:13px;font-weight:700;")
        layout.addWidget(heading)
        return frame, layout

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        self._title = QLabel(self._model["title"])
        self._title.setObjectName("chartPageTitle")
        self._title.setStyleSheet(f"color:{COLOR_GOLD};font-size:17px;font-weight:700;")
        outer.addWidget(self._title)

        self._meta = QLabel()
        self._meta.setObjectName("chartMetadata")
        self._meta.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:11px;")
        outer.addWidget(self._meta)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 4, 0)
        body_layout.setSpacing(10)

        # ── Primary Top Row: [Kundali Chart] [Shadbala/Karaka (Center)] [Planet Analysis (Right)] ──
        primary = QHBoxLayout()
        primary.setContentsMargins(0, 0, 0, 0)
        primary.setSpacing(12)
        primary.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 1. Left: Kundali Chart (Clean, borderless, fixed matching height)
        self._chart_widget = NorthIndianChartWidget(self._data, self._varga, self._lang)
        self._chart_widget.setObjectName("northIndianChart")
        self._chart_widget.setFixedSize(415, 415)
        self._chart_widget.planet_selected.connect(self._select_planet)
        self._chart_widget.planet_double_clicked.connect(self._open_full_report_for_planet)
        primary.addWidget(self._chart_widget, 0, Qt.AlignTop)

        # 2. Middle: [Karaka / Maraka / Sama Classification Box] + [Shadbala Bar Chart]
        mid_col = QVBoxLayout()
        mid_col.setContentsMargins(0, 0, 0, 0)
        mid_col.setSpacing(6)
        mid_col.setAlignment(Qt.AlignTop)

        # Karaka / Maraka / Sama Classification Box (Height 88px for full 3-line Devanagari visibility)
        self._role_box = QFrame()
        self._role_box.setObjectName("RoleClassificationBox")
        self._role_box.setFixedSize(340, 88)
        self._role_box.setStyleSheet("""
            QFrame#RoleClassificationBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        role_layout = QVBoxLayout(self._role_box)
        role_layout.setContentsMargins(10, 6, 10, 6)
        role_layout.setSpacing(0)

        self._role_label = QLabel()
        self._role_label.setTextFormat(Qt.RichText)
        self._role_label.setWordWrap(True)
        self._role_label.setFont(QFont(["Nirmala UI", "Segoe UI Historic", "Mangal", "Noto Sans Devanagari", "Segoe UI"], 10))
        self._role_label.setStyleSheet("color: #1e293b; background: transparent;")
        role_layout.addWidget(self._role_label)
        mid_col.addWidget(self._role_box)

        # Shadbala Bar Chart (Height 321px: 88 + 6 + 321 = 415px total, matching Kundali & Analysis Card)
        self._shadbala_bar_widget = ShadbalaMiniBarWidget(self._data)
        self._shadbala_bar_widget.setObjectName("shadbalaMiniBarWidget")
        self._shadbala_bar_widget.setFixedSize(340, 321)
        self._shadbala_bar_widget.planet_clicked.connect(self._select_planet)
        mid_col.addWidget(self._shadbala_bar_widget)

        primary.addLayout(mid_col, 0)

        # 3. Right: Planet Analysis Sidebar (Height 415px, perfectly aligned on bottom baseline)
        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(8)
        side.setAlignment(Qt.AlignTop)

        detail_card, detail_layout = self._card("ग्रह विश्लेषण" if self._is_ne else "Planet Analysis")
        detail_card.setFixedSize(275, 415)

        sade_row = QHBoxLayout()
        sade_row.setContentsMargins(0, 0, 0, 0)
        sade_row.setSpacing(4)
        self._sade_status = QLabel()
        self._sade_status.setObjectName("sadeSatiStatus")
        self._sade_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._sade_status.setStyleSheet(
            f"color:{COLOR_TEXT_SECONDARY};font-size:10px;font-weight:600;"
        )
        sade_row.addWidget(self._sade_status, 1)
        self._btn_sade_report = QPushButton("थप जानकारी" if self._is_ne else "More info")
        self._btn_sade_report.setObjectName("sadeSatiReportButton")
        self._btn_sade_report.setToolTip(
            "साढेसाती तथा अढैयाको पूर्ण रिपोर्ट खोल्नुहोस्"
            if self._is_ne else "Open the full Sade Sati and Adhaiya report"
        )
        self._btn_sade_report.setCursor(Qt.PointingHandCursor)
        self._btn_sade_report.setFixedHeight(22)
        self._btn_sade_report.setStyleSheet(f"""
            QPushButton#sadeSatiReportButton {{
                background: transparent;
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                color: {COLOR_GOLD};
                font-size: 9px;
                padding: 1px 5px;
            }}
            QPushButton#sadeSatiReportButton:hover {{
                background: rgba(212, 175, 55, 0.14);
                border-color: {COLOR_GOLD};
            }}
        """)
        self._btn_sade_report.clicked.connect(self._open_sade_sati_report)
        sade_row.addWidget(self._btn_sade_report, 0, Qt.AlignRight)
        detail_layout.addLayout(sade_row)

        self._detail = QLabel()
        self._detail.setObjectName("planetDetail")
        self._detail.setWordWrap(True)
        self._detail.setTextFormat(Qt.RichText)
        self._detail.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._detail.setMinimumHeight(240)
        self._detail.setStyleSheet(f"color:{COLOR_TEXT_PRIMARY};font-size:12px;")
        detail_layout.addWidget(self._detail, 1)

        self._btn_full_report = QPushButton("🔍 पूर्ण विश्लेषण रिपोर्ट" if self._is_ne else "🔍 Full Analysis Report")
        self._btn_full_report.setFixedHeight(30)
        self._btn_full_report.setStyleSheet(f"""
            QPushButton {{
                background: rgba(212, 175, 55, 0.15);
                border: 1px solid rgba(212, 175, 55, 0.4);
                border-radius: 6px;
                color: {COLOR_GOLD};
                font-weight: 700;
                font-size: 11px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background: rgba(212, 175, 55, 0.3);
                border-color: {COLOR_GOLD};
            }}
        """)
        self._btn_full_report.hide()
        self._btn_full_report.clicked.connect(self._open_full_report)
        detail_layout.addWidget(self._btn_full_report)

        self._btn_remedies_report = QPushButton("💎 रत्न तथा वैदिक उपचार" if self._is_ne else "💎 Gemstones & Remedies")
        self._btn_remedies_report.setFixedHeight(30)
        self._btn_remedies_report.setCursor(Qt.PointingHandCursor)
        self._btn_remedies_report.setStyleSheet(f"""
            QPushButton {{
                background: rgba(212, 175, 55, 0.15);
                border: 1px solid rgba(212, 175, 55, 0.4);
                border-radius: 6px;
                color: {COLOR_GOLD};
                font-weight: 700;
                font-size: 11px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background: rgba(212, 175, 55, 0.3);
                border-color: {COLOR_GOLD};
            }}
        """)
        self._btn_remedies_report.clicked.connect(self._open_remedies_report)
        detail_layout.addWidget(self._btn_remedies_report)
        side.addWidget(detail_card)

        primary.addLayout(side, 0)
        primary.addStretch(1)
        body_layout.addLayout(primary)

        sections = QGridLayout()
        sections.setSpacing(10)

        # 1. Samudaya Ashtakavarga Chart Card (Replacing old "कुण्डली स्थिति" box)
        sav_card = QFrame()
        sav_card.setObjectName("samudayaAshtakavargaCard")
        sav_card.setStyleSheet(f"""
            QFrame#samudayaAshtakavargaCard {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
        """)
        sav_layout = QVBoxLayout(sav_card)
        sav_layout.setContentsMargins(6, 6, 6, 6)
        sav_layout.setSpacing(4)

        sav_heading = QLabel("समुदाय अष्टकवर्ग" if self._is_ne else "Samudaya Ashtakavarga")
        sav_heading.setAlignment(Qt.AlignCenter)
        sav_heading.setStyleSheet(f"color:{COLOR_GOLD};font-size:13.5px;font-weight:800;padding-bottom:2px;")
        sav_layout.addWidget(sav_heading, 0, Qt.AlignCenter)

        from gui.widgets.ashtakavarga import SamudayaAshtakavargaChartWidget
        self._sav_chart_widget = SamudayaAshtakavargaChartWidget(
            lagna_sign=int(self._model.get("lagna", {}).get("sign_number", 1) or 1),
            sav_scores=[28] * 12,
            language=self._lang,
            chart_data=self._data
        )
        self._sav_chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._sav_chart_widget.setMinimumHeight(280)
        sav_layout.addWidget(self._sav_chart_widget, 1)
        sections.addWidget(sav_card, 0, 0)
        sections.setColumnStretch(0, 1)
        sections.setColumnStretch(1, 1)
        sections.setColumnStretch(2, 1)
        body_layout.addLayout(sections)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

    def _select_planet(self, name: str) -> None:
        if not name:
            return
        self._selected_planet_name = name
        planets = self._model.get("planets", []) or self._data.get("planets", [])
        planet = next((p for p in planets if p.get("name") == name), None)
        if not planet:
            planet = next((p for p in planets if str(p.get("name", "")).strip().lower() == str(name).strip().lower()), None)
        if not planet:
            planet = {"name": name}
        self._chart_widget.set_selected_planet(name)
        if hasattr(self, "_shadbala_bar_widget"):
            self._shadbala_bar_widget.set_selected_planet(name)
        self._set_planet_detail(planet)

    def _open_full_report(self) -> None:
        if not hasattr(self, "_selected_planet_name") or not self._selected_planet_name:
            return
        from gui.widgets.planet_analysis_dialog import PlanetAnalysisDialog
        dlg = PlanetAnalysisDialog(self._selected_planet_name, self._data, self)
        dlg.exec()

    def _open_full_report_for_planet(self, name: str) -> None:
        if not name:
            return
        self._select_planet(name)
        from gui.widgets.planet_analysis_dialog import PlanetAnalysisDialog
        dlg = PlanetAnalysisDialog(name, self._data, self)
        dlg.exec()

    def _set_planet_detail(self, planet: Optional[dict]) -> None:
        if not planet:
            self._detail.setText("ग्रह छानेर विस्तृत विश्लेषण हेर्नुहोस्।" if self._is_ne else "Select any planet in the chart to inspect its position.")
            self._btn_full_report.hide()
            return

        from gui.utils.planet_analysis_engine import analyze_planet_full
        p_name = planet.get("name", "")
        rep = analyze_planet_full(p_name, self._data)
        is_shubha = rep.get("is_shubha", True)
        color = "#16a34a" if is_shubha else "#dc2626"
        status_lbl = rep.get("status_label", "शुभ")
        status_pct = rep.get("status_pct_ne", "८०")

        sign = rashi_name(int(planet.get("sign_number", 1) or 1), self._lang)
        degree = float(planet.get("longitude_in_sign", 0) or 0)
        p_ne = rep.get("1_name", p_name)

        shubha_pct_ne = rep.get("shubha_pct_ne", "५०")
        ashubha_pct_ne = rep.get("ashubha_pct_ne", "५०")

        html = f"""
        <div style="margin-bottom: 6px;">
            <span style="font-size: 14px; font-weight: bold; color: {COLOR_GOLD};">🪐 {p_ne}</span>
            &nbsp; — &nbsp;
            <span style="font-size: 13px; font-weight: 900; color: #16a34a;">शुभ: {shubha_pct_ne}%</span>
            &nbsp;|&nbsp;
            <span style="font-size: 13px; font-weight: 900; color: #dc2626;">अशुभ: {ashubha_pct_ne}%</span>
        </div>
        <div style="font-size: 11px; line-height: 1.4; color: {COLOR_TEXT_PRIMARY};">
            <b>राशि:</b> {sign} ({degree:.2f}°)<br>
            <b>भाव:</b> {planet.get('house', '—')} | <b>स्थिति:</b> {rep.get('9_dignity', '—')}<br>
            <b>षड्बल:</b> {rep.get('2_shadbala', '—')}<br>
            <b>इष्ट–कष्ट:</b> {rep.get('5_ishta_kashta', '—')}<br>
            <b>कारकत्व:</b> {rep.get('15_karakatwa', '—')[:38]}...
        </div>
        """
        self._detail.setText(html)
        self._btn_full_report.show()

    def _open_sade_sati_report(self) -> None:
        """Open the existing full report through the owning main window."""
        window = self.window()
        navigate = getattr(window, "_navigate", None)
        if callable(navigate):
            navigate("report_sadesati_adhaiya")

    def _open_remedies_report(self) -> None:
        """Open the Remedies & Gemstones page through the owning main window."""
        window = self.window()
        navigate = getattr(window, "_navigate", None)
        if callable(navigate):
            navigate("report_remedies")

    def _update_sade_sati_status(self) -> None:
        planets = self._data.get("planets", []) if isinstance(self._data, dict) else []
        moon = next((p for p in planets if p.get("name") == "Moon"), None)
        saturn = next((p for p in planets if p.get("name") == "Saturn"), None)
        if not moon or not saturn:
            self._sade_status.setText(
                "साढेसाती वा अढैया : —" if self._is_ne else "Sade Sati / Adhaiya: —"
            )
            self._sade_status.setStyleSheet(
                f"color:{COLOR_TEXT_MUTED};font-size:10px;font-weight:600;"
            )
            return

        try:
            moon_sign = int(moon.get("sign_number", 0) or 0)
            saturn_sign = int(saturn.get("sign_number", 0) or 0)
        except (TypeError, ValueError):
            moon_sign = saturn_sign = 0
        offset = (saturn_sign - moon_sign) % 12 if moon_sign and saturn_sign else -1
        active = offset in (0, 1, 11, 4, 7)
        if self._is_ne:
            value = "छ" if active else "छैन"
            label = f"साढेसाती वा अढैया : {value}"
        else:
            label = f"Sade Sati / Adhaiya: {'Yes' if active else 'No'}"
        color = "#ef4444" if active else "#22c55e"
        self._sade_status.setText(label)
        self._sade_status.setStyleSheet(
            f"color:{color};font-size:10px;font-weight:700;"
        )

    def refresh(self, data: dict) -> None:
        self._data = data or {}
        self._model = chart_page_model(self._data, self._varga, self._lang)
        self._chart_widget.set_data(self._data, self._varga)
        if hasattr(self, "_shadbala_bar_widget"):
            self._shadbala_bar_widget.set_data(self._data)
        self._title.setText(self._model["title"])
        meta = self._model["metadata"]
        self._meta.setText(
            f"{meta.get('name', '—')}  |  {meta.get('birth_date', '—')} {meta.get('birth_time', '')}  |  "
            f"{meta.get('city', '—')}  |  {meta.get('ayanamsha_type', 'LAHIRI')}"
        )
        lagna = self._model["lagna"]
        lagna_sign = int(lagna.get("sign_number", 1) or 1)

        # Update Samudaya Ashtakavarga Chart
        if hasattr(self, "_sav_chart_widget"):
            planets = self._data.get("planets", [])
            av = self._data.get("ashtakavarga", {})
            if not isinstance(av, dict):
                av = {}
            if not av or not av.get("sav") or not av.get("bhinnashtakavarga"):
                try:
                    from backend.calculator.ashtakavarga import compute_samudaya_ashtakavarga
                    av = compute_samudaya_ashtakavarga(planets, lagna_sign)
                    self._data["ashtakavarga"] = av
                except Exception:
                    av = {"sav": [28] * 12}
            sav_raw = av.get("sav", [28] * 12)
            if isinstance(sav_raw, dict):
                sav_scores = [sav_raw.get(str(i), 28) for i in range(1, 13)]
            elif isinstance(sav_raw, list) and len(sav_raw) == 12:
                sav_scores = sav_raw
            else:
                sav_scores = [28] * 12
            self._sav_chart_widget.set_data(lagna_sign, sav_scores, chart_data=self._data)

        self._set_planet_detail(None)
        self._update_sade_sati_status()
        lagna_sign = int(lagna.get("sign_number", 1) or 1)
        self._update_functional_roles(lagna_sign)

    def _update_functional_roles(self, lagna_sign: int) -> None:
        """Update Karaka / Maraka / Sama classification text based on chart ascendant."""
        ROLES_BY_LAGNA = {
            1: {  # मेष
                "karaka": ["सूर्य", "मंगल", "गुरु"],
                "maraka": ["शुक्र", "शनि", "बुध"],
                "sama": ["चन्द्र", "राहु", "केतु"]
            },
            2: {  # वृष
                "karaka": ["शनि", "बुध", "शुक्र"],
                "maraka": ["गुरु", "मंगल"],
                "sama": ["सूर्य", "चन्द्र", "राहु", "केतु"]
            },
            3: {  # मिथुन
                "karaka": ["बुध", "शुक्र"],
                "maraka": ["मंगल", "गुरु"],
                "sama": ["सूर्य", "चन्द्र", "शनि", "राहु", "केतु"]
            },
            4: {  # कर्कट
                "karaka": ["मंगल", "चन्द्र", "गुरु"],
                "maraka": ["शुक्र", "शनि", "बुध"],
                "sama": ["सूर्य", "राहु", "केतु"]
            },
            5: {  # सिंह
                "karaka": ["मंगल", "सूर्य", "गुरु"],
                "maraka": ["शनि", "शुक्र"],
                "sama": ["बुध", "चन्द्र", "राहु", "केतु"]
            },
            6: {  # कन्या
                "karaka": ["बुध", "शुक्र"],
                "maraka": ["मंगल", "गुरु", "चन्द्र"],
                "sama": ["शनि", "सूर्य", "राहु", "केतु"]
            },
            7: {  # तुला
                "karaka": ["शनि", "शुक्र", "बुध"],
                "maraka": ["मंगल", "गुरु", "सूर्य"],
                "sama": ["चन्द्र", "राहु", "केतु"]
            },
            8: {  # वृश्चिक
                "karaka": ["चन्द्र", "सूर्य", "मंगल", "गुरु"],
                "maraka": ["बुध", "शुक्र"],
                "sama": ["शनि", "राहु", "केतु"]
            },
            9: {  # धनु
                "karaka": ["सूर्य", "गुरु", "मंगल"],
                "maraka": ["शुक्र", "शनि", "बुध"],
                "sama": ["चन्द्र", "राहु", "केतु"]
            },
            10: {  # मकर
                "karaka": ["शुक्र", "शनि", "बुध"],
                "maraka": ["गुरु", "मंगल", "चन्द्र"],
                "sama": ["सूर्य", "राहु", "केतु"]
            },
            11: {  # कुम्भ
                "karaka": ["शुक्र", "शनि", "बुध"],
                "maraka": ["गुरु", "सूर्य", "चन्द्र"],
                "sama": ["मंगल", "राहु", "केतु"]
            },
            12: {  # मीन
                "karaka": ["चन्द्र", "मंगल", "गुरु"],
                "maraka": ["शुक्र", "शनि", "बुध"],
                "sama": ["सूर्य", "राहु", "केतु"]
            }
        }
        roles = ROLES_BY_LAGNA.get(lagna_sign, {
            "karaka": ["सूर्य", "चन्द्र", "गुरु"],
            "maraka": ["मंगल", "शनि"],
            "sama": ["बुध", "शुक्र", "राहु", "केतु"]
        })
        karakas = ", ".join(roles["karaka"])
        marakas = ", ".join(roles["maraka"])
        samas = ", ".join(roles["sama"])

        html = f"""
        <div style="font-family: 'Nirmala UI', 'Segoe UI Historic', 'Mangal', 'Noto Sans Devanagari', 'Segoe UI'; font-size: 11px; line-height: 1.4; color: #1e293b;">
            <b style="color: #15803d;">कारक ग्रह :</b> <span style="color: #16a34a; font-weight: 700;">{karakas}</span><br>
            <b style="color: #b91c1c;">मारक ग्रह :</b> <span style="color: #dc2626; font-weight: 700;">{marakas}</span><br>
            <b style="color: #334155;">सम ग्रह :</b> <span style="color: #0f172a; font-weight: 600;">{samas}</span>
        </div>
        """
        if hasattr(self, "_role_label"):
            self._role_label.setText(html)
