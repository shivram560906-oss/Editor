"""
gui/widgets/ashtakavarga.py
Complete Samudaya & Bhinnashtakavarga (BAV/SAV) Page with:
- Classical North Indian Samudaya Ashtakavarga Chart (matching traditional Jyotish layout)
- Full Parashari house-by-house & planet-by-planet detailed interpretations
- Clean white background layout with crisp dark text & bold emphasis
- Complete guide on "अष्टकवर्ग कसरी हेर्ने?" (How to interpret Ashtakavarga & Transits)
"""
from __future__ import annotations
import sys
import os
import math
from typing import Optional, Dict, Any, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy
)
from PySide6.QtCore import (
    Qt, QRectF, QPointF, Signal, QTimer, QPropertyAnimation, QEasingCurve,
    QSequentialAnimationGroup, Property
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QRadialGradient, QLinearGradient
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    COLOR_GOLD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    BORDER_COLOR
)
from gui.utils.planet_colors import (
    PLANET_ABBR, rashi_name, to_nepali_digits
)
from backend.calculator.ashtakavarga import (
    compute_samudaya_ashtakavarga, SEVEN_GRAHAS, EXPECTED_BAV_TOTALS
)

RASHI_NAMES_NE = [
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
]

RASHI_NAMES_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

BHAVA_NAMES_NE = [
    "प्रथम भाव (लग्न - शरीर, व्यक्तित्व, स्वास्थ्य)",
    "द्वितीय भाव (धन, कुटुम्ब, वाणी)",
    "तृतीय भाव (पराक्रम, भाइबहिनी, साहस)",
    "चतुर्थ भाव (सुख, माता, वाहन, घर)",
    "पञ्चम भाव (सन्तान, बुद्धि, ज्ञान, मन्त्र)",
    "षष्ठ भाव (ऋण, रोग, शत्रु, प्रतिस्पर्धा)",
    "सप्तम भाव (दाम्पत्य, साझेदारी, व्यापार)",
    "अष्टम भाव (आयु, सङ्कट, अनुसन्धान, आकस्मिक धन)",
    "नवम भाव (भाग्य, धर्म, गुरु, तीर्थयात्रा)",
    "दशम भाव (कर्म, पद, प्रतिष्ठा, व्यवसाय)",
    "एकादश भाव (लाभ, आय, मित्र, सिद्धि)",
    "द्वादश भाव (व्यय, विदेश, मोक्ष, अस्पताल)"
]

PLANET_NAMES_NE = {
    "Sun": "सूर्य",
    "Moon": "चन्द्र",
    "Mars": "मङ्गल",
    "Mercury": "बुध",
    "Jupiter": "बृहस्पति (गुरु)",
    "Venus": "शुक्र",
    "Saturn": "शनि"
}


class SamudayaAshtakavargaChartWidget(QWidget):
    """
    Renders the North Indian Diamond Kundali specifically for Samudaya Ashtakavarga
    with animated sacred line tracing, glowing Jyoti tip, staggered score pop-in,
    and interactive click-to-detail functionality.
    """
    house_hovered = Signal(int)                          # house number 1-12
    house_clicked = Signal(int, int)                     # (house_number, sav_score)
    element_clicked = Signal(int, int, int, str)         # (house_number, sign_num, sav_score, target_type)

    # ── Qt Properties for QPropertyAnimation ───────────────────────────────
    def _get_line_progress(self) -> float: return self._line_progress
    def _set_line_progress(self, v: float):
        self._line_progress = max(0.0, min(1.0, float(v)))
        self.update()
    line_progress = Property(float, _get_line_progress, _set_line_progress)

    def _get_score_progress(self) -> float: return self._score_progress
    def _set_score_progress(self, v: float):
        self._score_progress = max(0.0, min(1.0, float(v)))
        self.update()
    score_progress = Property(float, _get_score_progress, _set_score_progress)

    def __init__(
        self,
        lagna_sign: int = 1,
        sav_scores: Optional[List[int]] = None,
        language: str = "ne",
        chart_data: Optional[dict] = None,
        parent=None
    ):
        super().__init__(parent)
        self._lagna_sign = lagna_sign
        self._sav_scores = sav_scores or [28] * 12  # 12 signs (Aries..Pisces)
        self._chart_data = chart_data or {}
        self._language = language
        self._is_ne = language == "ne"

        # ── Animation State ─────────────────────────────────────────────────
        self._line_progress: float = 0.0
        self._score_progress: float = 0.0
        self._has_animated: bool = False
        self._pulse_tick: int = 0
        self._anim_group: Optional[QSequentialAnimationGroup] = None
        self._pulse_timer: Optional[QTimer] = None
        self._clicked_house: Optional[int] = None      # currently selected house
        self._clicked_target: Optional[str] = None     # "rashi" | "score" | "house"
        self._hovered_house: Optional[int] = None      # currently hovered house
        self._hovered_target: Optional[str] = None     # "rashi" | "score" | "house"
        self._house_rects: Dict[int, QRectF] = {}      # combined house hit areas
        self._rashi_rects: Dict[int, QRectF] = {}      # rashi number hit areas
        self._sav_rects: Dict[int, QRectF] = {}        # SAV score hit areas

        self.setMinimumSize(240, 140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMouseTracking(True)
        self.setToolTip("समुदाय अष्टकवर्ग कुण्डली — कुनै पनि भाव वा बिन्दुमा क्लिक गरी विस्तृत प्रतिवेदन हेर्नुहोस्")

        self._start_pulse_timer()
        QTimer.singleShot(80, self._play_animation)

    # ── Lifecycle & Public API ────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if not self._has_animated:
            self._play_animation()

    def set_data(self, lagna_sign: int, sav_scores: List[int], chart_data: Optional[dict] = None):
        self._lagna_sign = lagna_sign
        self._sav_scores = sav_scores
        if chart_data is not None:
            self._chart_data = chart_data
        self._has_animated = False
        self._play_animation()

    def _play_animation(self) -> None:
        """Plays the 2-phase animation: line drawing → score pop-in."""
        if self._anim_group and self._anim_group.state() != QPropertyAnimation.Stopped:
            self._anim_group.stop()

        self._line_progress = 0.0
        self._score_progress = 0.0
        self._has_animated = True
        self.update()

        line_anim = QPropertyAnimation(self, b"line_progress", self)
        line_anim.setStartValue(0.0)
        line_anim.setEndValue(1.0)
        line_anim.setDuration(600)
        line_anim.setEasingCurve(QEasingCurve.OutCubic)

        score_anim = QPropertyAnimation(self, b"score_progress", self)
        score_anim.setStartValue(0.0)
        score_anim.setEndValue(1.0)
        score_anim.setDuration(520)
        score_anim.setEasingCurve(QEasingCurve.OutBack)

        self._anim_group = QSequentialAnimationGroup(self)
        self._anim_group.addAnimation(line_anim)
        self._anim_group.addPause(30)
        self._anim_group.addAnimation(score_anim)
        self._anim_group.start()

    def _start_pulse_timer(self) -> None:
        if self._pulse_timer is not None:
            return
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(30)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start()

    def _tick_pulse(self) -> None:
        self._pulse_tick += 1
        self.update()

    def mouseDoubleClickEvent(self, event):
        self._play_animation()

    def mouseMoveEvent(self, event):
        h, target = self._target_at(event.pos())
        if (h, target) != (self._hovered_house, self._hovered_target):
            self._hovered_house = h
            self._hovered_target = target
            self.setCursor(Qt.PointingHandCursor if h else Qt.ArrowCursor)
            if h is not None:
                sign_num = ((self._lagna_sign - 1 + h - 1) % 12) + 1
                score = (self._sav_scores[sign_num - 1] if 0 <= sign_num - 1 < len(self._sav_scores) else 28)
                r_name = RASHI_NAMES_NE[sign_num - 1] if 0 <= sign_num - 1 < len(RASHI_NAMES_NE) else ""
                if target == "rashi":
                    self.setToolTip(f"भाव {self._fmt(h)} (राशि: {r_name} {self._fmt(sign_num)}) — क्लिक गरी भाव कारकत्व र फल हेर्नुहोस्")
                elif target == "score":
                    self.setToolTip(f"समुदाय अष्टकवर्ग: {self._fmt(score)} बिन्दु — क्लिक गरी बिन्दु फल र लाभ/हानि प्रतिशत हेर्नुहोस्")
                else:
                    self.setToolTip(f"भाव {self._fmt(h)} — क्लिक गरी पूर्ण अष्टकवर्ग प्रतिवेदन हेर्नुहोस्")
            else:
                self.setToolTip("समुदाय अष्टकवर्ग कुण्डली — कुनै पनि भाव वा बिन्दुमा क्लिक गरी विस्तृत प्रतिवेदन हेर्नुहोस्")
            self.update()

    def leaveEvent(self, event):
        self._hovered_house = None
        self._hovered_target = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            h, target = self._target_at(event.pos())
            if h is not None:
                self._clicked_house = h
                self._clicked_target = target
                sign_num = ((self._lagna_sign - 1 + h - 1) % 12) + 1
                score = (self._sav_scores[sign_num - 1]
                         if 0 <= sign_num - 1 < len(self._sav_scores) else 28)
                self.house_clicked.emit(h, score)
                self.element_clicked.emit(h, sign_num, score, target or "house")
                self.open_detail_dialog(h, initial_tab=target or "house")
                self.update()

    def open_detail_dialog(self, house_num: int, initial_tab: str = "house"):
        """Opens the full Samudaya Ashtakavarga house & bindu detailed report dialog."""
        from gui.widgets.ashtakavarga_house_dialog import SamudayaHouseDetailDialog
        dlg = SamudayaHouseDetailDialog(
            house_num=house_num,
            lagna_sign=self._lagna_sign,
            sav_scores=self._sav_scores,
            chart_data=self._chart_data,
            initial_tab=initial_tab,
            parent=self.window()
        )
        dlg.exec()

    def _target_at(self, pos) -> Tuple[Optional[int], Optional[str]]:
        """Return (house_num, target_type) where target_type is 'rashi', 'score', or 'house'."""
        px, py = float(pos.x()), float(pos.y())
        for h_num, rect in self._rashi_rects.items():
            if rect.contains(px, py):
                return h_num, "rashi"
        for h_num, rect in self._sav_rects.items():
            if rect.contains(px, py):
                return h_num, "score"
        for h_num, rect in self._house_rects.items():
            if rect.contains(px, py):
                return h_num, "house"
        return None, None

    def _fmt(self, val: Any) -> str:
        s = str(val)
        return to_nepali_digits(s) if self._is_ne else s

    # ── Paint Pipeline ────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()

        pad_x = 2.0
        pad_y = 2.0
        chart_w = w - 2 * pad_x
        chart_h = h - 2 * pad_y

        ox = pad_x
        oy = pad_y

        # 1. Background with gentle central ambient glow
        bg_rect = QRectF(ox, oy, chart_w, chart_h)
        painter.fillRect(bg_rect, QColor("#dce8ff"))

        c_pt = QPointF(ox + chart_w / 2.0, oy + chart_h / 2.0)
        c_glow_r = max(40.0, min(chart_w, chart_h) * 0.45)
        c_glow = QRadialGradient(c_pt, c_glow_r)
        c_alpha = int(22 + 18 * math.sin(self._pulse_tick * 0.08))
        c_glow.setColorAt(0.0, QColor(245, 158, 11, c_alpha))
        c_glow.setColorAt(0.6, QColor(59, 130, 246, int(c_alpha * 0.4)))
        c_glow.setColorAt(1.0, QColor(220, 232, 255, 0))
        painter.setBrush(QBrush(c_glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(c_pt, c_glow_r, c_glow_r)

        # 2. Outer double border
        pen_outer = QPen(QColor("#002288"), 2.0)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(bg_rect)

        inner_rect = QRectF(ox + 3.0, oy + 3.0, chart_w - 6.0, chart_h - 6.0)
        painter.setPen(QPen(QColor("#002288"), 1.0))
        painter.drawRect(inner_rect)

        # Coordinate shortcuts relative to chart box
        x0, y0 = ox, oy
        x1 = ox + chart_w / 4.0
        x2 = ox + chart_w / 2.0
        x3 = ox + 3.0 * chart_w / 4.0
        x4 = ox + chart_w

        y1 = oy + chart_h / 4.0
        y2 = oy + chart_h / 2.0
        y3 = oy + 3.0 * chart_h / 4.0
        y4 = oy + chart_h

        # 3. Animated Sacred Lines Tracing (6 internal segments)
        segments = [
            (QPointF(x0, y0), QPointF(x4, y4)),      # Diagonal 1
            (QPointF(x0, y4), QPointF(x4, y0)),      # Diagonal 2
            (QPointF(x2, y0), QPointF(x0, y2)),      # Diamond Top-Left
            (QPointF(x0, y2), QPointF(x2, y4)),      # Diamond Bottom-Left
            (QPointF(x2, y4), QPointF(x4, y2)),      # Diamond Bottom-Right
            (QPointF(x4, y2), QPointF(x2, y0)),      # Diamond Top-Right
        ]
        n = len(segments)
        seg_w = 1.0 / n
        active_tip: Optional[QPointF] = None

        for idx, (s_pt, e0_pt) in enumerate(segments):
            seg_start = idx * seg_w
            if self._line_progress <= seg_start:
                break

            local = min(1.0, (self._line_progress - seg_start) / seg_w)
            cur_end = QPointF(
                s_pt.x() + (e0_pt.x() - s_pt.x()) * local,
                s_pt.y() + (e0_pt.y() - s_pt.y()) * local
            )

            if local < 1.0 and self._line_progress < 1.0:
                active_tip = cur_end
                # Glowing trail
                glow_pen = QPen(QColor(245, 158, 11, 140), 3.5, Qt.SolidLine, Qt.RoundCap)
                painter.setPen(glow_pen)
                painter.drawLine(s_pt, cur_end)

            core_pen = QPen(QColor("#002288"), 1.5, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(core_pen)
            painter.drawLine(s_pt, cur_end)

        # Drawing tip radiant spark
        if active_tip is not None:
            tip_r = 7.0
            flare = QRadialGradient(active_tip, tip_r)
            flare.setColorAt(0.0, QColor(255, 255, 255, 255))
            flare.setColorAt(0.4, QColor(254, 240, 138, 220))
            flare.setColorAt(1.0, QColor(245, 158, 11, 0))
            painter.setBrush(QBrush(flare))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(active_tip, tip_r, tip_r)

        # 4. 12 Houses Staggered Score & Rashi Cascade
        rashi_font_size = max(9, min(13, int(min(w, h) / 24.0)))
        sav_font_size = max(12, min(18, int(min(w, h) / 16.0)))
        rashi_font = QFont("Noto Sans Devanagari", rashi_font_size, QFont.Bold)
        sav_font = QFont("Noto Sans Devanagari", sav_font_size, QFont.Bold)

        def get_house_data(h_num: int):
            sign_num = ((self._lagna_sign - 1 + h_num - 1) % 12) + 1
            score = self._sav_scores[sign_num - 1] if 0 <= sign_num - 1 < len(self._sav_scores) else 28
            return sign_num, score

        house_defs = [
            (1,  QRectF(x2 - 30, (y0 + y2) / 2.0 - 13, 60, 26), QRectF(x2 - 30, y2 - 24, 60, 20)),
            (2,  QRectF(x1 - 22, y0 + (y1 - y0) * 0.35 - 10, 44, 24), QRectF(x1 - 20, y1 - 20, 40, 20)),
            (3,  QRectF(x0 + (x1 - x0) * 0.35 - 22, y1 - 12, 44, 24), QRectF(x1 - 34, y1 - 10, 32, 20)),
            (4,  QRectF(x1 - 22, y2 - 13, 44, 26), QRectF(x2 - 34, y2 - 10, 32, 20)),
            (5,  QRectF(x0 + (x1 - x0) * 0.35 - 22, y3 - 12, 44, 24), QRectF(x1 - 34, y3 - 10, 32, 20)),
            (6,  QRectF(x1 - 22, y4 - (y4 - y3) * 0.35 - 14, 44, 24), QRectF(x1 - 20, y3 + 2, 40, 20)),
            (7,  QRectF(x2 - 30, (y2 + y4) / 2.0 - 8, 60, 26), QRectF(x2 - 30, y2 + 6, 60, 20)),
            (8,  QRectF(x3 - 22, y4 - (y4 - y3) * 0.35 - 14, 44, 24), QRectF(x3 - 20, y3 + 2, 40, 20)),
            (9,  QRectF(x3 + (x4 - x3) * 0.65 - 22, y3 - 12, 44, 24), QRectF(x3 + 2, y3 - 10, 32, 20)),
            (10, QRectF(x3 - 22, y2 - 13, 44, 26), QRectF(x2 + 2, y2 - 10, 32, 20)),
            (11, QRectF(x3 + (x4 - x3) * 0.65 - 22, y1 - 12, 44, 24), QRectF(x3 + 2, y1 - 10, 32, 20)),
            (12, QRectF(x3 - 22, y0 + (y1 - y0) * 0.35 - 10, 44, 24), QRectF(x3 - 20, y1 - 20, 40, 20)),
        ]

        # Reset hit rects each frame
        self._house_rects = {}
        self._rashi_rects = {}
        self._sav_rects = {}

        prog = self._score_progress

        for h_num, sav_rect, rashi_rect in house_defs:
            sign_num, score = get_house_data(h_num)

            sav_hit = sav_rect.adjusted(-6, -6, 6, 6)
            rashi_hit = rashi_rect.adjusted(-4, -4, 4, 4)
            combined_hit = sav_hit.united(rashi_hit).adjusted(-4, -4, 4, 4)

            self._sav_rects[h_num] = sav_hit
            self._rashi_rects[h_num] = rashi_hit
            self._house_rects[h_num] = combined_hit

            # Hover / click highlight ring with target distinction
            is_clicked = (self._clicked_house == h_num)
            is_hovered = (self._hovered_house == h_num)
            if is_clicked or is_hovered:
                target = self._hovered_target if is_hovered else self._clicked_target
                ring_alpha = int(200 + 55 * math.sin(self._pulse_tick * 0.16))

                if target == "rashi":
                    r_color = QColor(2, 132, 199, ring_alpha) if is_hovered else QColor(245, 158, 11, ring_alpha)
                    painter.setPen(QPen(r_color, 1.8))
                    painter.setBrush(QBrush(QColor(2, 132, 199, 32) if is_hovered else QColor(245, 158, 11, 35)))
                    painter.drawRoundedRect(rashi_hit, 4.0, 4.0)
                elif target == "score":
                    s_color = QColor(245, 158, 11, ring_alpha) if is_clicked else (
                        QColor(22, 163, 74, ring_alpha) if score >= 28 else QColor(220, 38, 38, ring_alpha)
                    )
                    painter.setPen(QPen(s_color, 2.2))
                    painter.setBrush(QBrush(QColor(s_color.red(), s_color.green(), s_color.blue(), 30)))
                    painter.drawRoundedRect(sav_hit, 5.0, 5.0)
                else:
                    ring_color = QColor(245, 158, 11, ring_alpha) if is_clicked else QColor(59, 130, 246, 160)
                    ring_pen   = QPen(ring_color, 2.0 if is_hovered else 2.8)
                    ring_pen.setStyle(Qt.DashLine if is_hovered else Qt.SolidLine)
                    painter.setPen(ring_pen)
                    painter.setBrush(QBrush(QColor(245, 158, 11, 18) if is_clicked else QColor(59, 130, 246, 12)))
                    painter.drawRoundedRect(combined_hit, 5.0, 5.0)

            # Staggered pop-in calculation
            delay = (h_num - 1) * 0.05
            if prog <= delay:
                continue

            raw_t = min(1.0, (prog - delay) / 0.45)
            t_rem = raw_t - 1.0
            scale = max(0.0, 1.0 + 2.5 * (t_rem ** 3) + 1.5 * (t_rem ** 2))

            center_x = sav_rect.center().x()
            center_y = sav_rect.center().y()

            painter.save()
            painter.translate(center_x, center_y)
            painter.scale(scale, scale)
            painter.translate(-center_x, -center_y)

            # Draw Rashi number
            painter.setFont(rashi_font)
            painter.setPen(QColor("#001144"))
            painter.drawText(rashi_rect, Qt.AlignCenter, self._fmt(sign_num))

            # SAV Score with strength styling
            painter.setFont(sav_font)
            if score >= 30:
                badge = QRectF(sav_rect.x() + 4, sav_rect.y() + 2, sav_rect.width() - 8, sav_rect.height() - 4)
                painter.setBrush(QBrush(QColor(22, 163, 74, 35)))
                painter.setPen(QPen(QColor(22, 163, 74, 180), 1.2))
                painter.drawRoundedRect(badge, 4.0, 4.0)
                painter.setPen(QColor("#15803d"))
            elif score < 25:
                badge = QRectF(sav_rect.x() + 4, sav_rect.y() + 2, sav_rect.width() - 8, sav_rect.height() - 4)
                painter.setBrush(QBrush(QColor(220, 38, 38, 28)))
                painter.setPen(QPen(QColor(220, 38, 38, 160), 1.2))
                painter.drawRoundedRect(badge, 4.0, 4.0)
                painter.setPen(QColor("#dc2626"))
            else:
                painter.setPen(QColor("#0f172a"))

            painter.drawText(sav_rect, Qt.AlignCenter, self._fmt(score))
            painter.restore()

        painter.end()


class AshtakavargaPage(QWidget):
    """
    Main Ashtakavarga Report Page containing:
    1. Classical Header pill + Samudaya Ashtakavarga Kundali chart
    2. Detailed Parashari house-by-house & planet-by-planet interpretation
    3. Life dimensions analysis (Finance, Career, Health, Family, etc.)
    4. Comprehensive practical guide on 'अष्टकवर्ग कसरी हेर्ने?' (Transit & Dasha application)
    All formatted in clean, professional white background with bold emphasis.
    """
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data or {}
        self._lang = language
        self._is_ne = language == "ne"

        self._build_ui()
        if data:
            self.refresh(data)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area for complete report reading
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #ffffff; border: none; }")

        self._container = QWidget()
        self._container.setObjectName("AshtakavargaContainer")
        self._container.setStyleSheet("QWidget#AshtakavargaContainer { background: #ffffff; color: #1e293b; }")
        
        self._content_layout = QVBoxLayout(self._container)
        self._content_layout.setContentsMargins(28, 20, 28, 32)
        self._content_layout.setSpacing(16)

        scroll.setWidget(self._container)
        main_layout.addWidget(scroll)

    def refresh(self, data: dict) -> None:
        self._data = data or {}

        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Extract or compute Ashtakavarga
        av = data.get("ashtakavarga", {})
        planets = data.get("planets", [])
        lagna_data = data.get("lagna", {})
        lagna_sign = int(lagna_data.get("sign_number", 1) or 1)

        # If data["ashtakavarga"] is missing or incomplete, compute directly
        if not av or not av.get("sav") or not av.get("bhinnashtakavarga"):
            try:
                av = compute_samudaya_ashtakavarga(planets, lagna_sign)
            except Exception:
                av = {
                    "sav": [28] * 12,
                    "bhinnashtakavarga": {p: [4] * 12 for p in SEVEN_GRAHAS},
                    "total_bindus": 337,
                    "lagna_sign": lagna_sign
                }

        sav_scores = av.get("sav", [28] * 12)
        bav_scores = av.get("bhinnashtakavarga", {})

        # ── 1. Page Title ─────────────────────────────────────────────────────
        title_lbl = QLabel("अष्टकवर्ग विश्लेषण (Ashtakavarga Complete Report)" if not self._is_ne else "अष्टकवर्ग बृहत् प्रतिवेदन")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 2px;")
        self._content_layout.addWidget(title_lbl)

        sub_lbl = QLabel(
            "महर्षि पराशर प्रतिपादित अष्टकवर्ग पद्धति अनुसार समुदाय एवं भिन्न अष्टकवर्ग बिन्दु, भावगत सामर्थ्य, गोचर फल तथा जीवनका महत्त्वपूर्ण पक्षहरूको विस्तृत विवेचना।"
            if self._is_ne else
            "Comprehensive Parashari Samudaya & Bhinnashtakavarga analysis, house strengths, transit potentials and planetary bindus."
        )
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet("font-size: 13px; color: #475569; margin-bottom: 12px;")
        self._content_layout.addWidget(sub_lbl)

        # ── 2. Top Kundali Section matching Image 1 ───────────────────────────
        chart_section = QWidget()
        chart_vbox = QVBoxLayout(chart_section)
        chart_vbox.setContentsMargins(0, 0, 0, 8)
        chart_vbox.setSpacing(6)
        chart_vbox.setAlignment(Qt.AlignHCenter)

        # Header pill badge matching Image 1: [ समुदाय अष्टकवर्ग ]
        badge_frame = QFrame()
        badge_frame.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 2px solid #0284c7;
                border-radius: 12px;
                padding: 2px 20px;
            }
        """)
        badge_layout = QHBoxLayout(badge_frame)
        badge_layout.setContentsMargins(12, 2, 12, 2)
        badge_lbl = QLabel("समुदाय अष्टकवर्ग" if self._is_ne else "Samudaya Ashtakavarga")
        badge_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #0369a1; border: none;")
        badge_lbl.setAlignment(Qt.AlignCenter)
        badge_layout.addWidget(badge_lbl)
        chart_vbox.addWidget(badge_frame, alignment=Qt.AlignLeft)

        # Kundali Chart widget
        self._chart_widget = SamudayaAshtakavargaChartWidget(
            lagna_sign=lagna_sign, sav_scores=sav_scores, language=self._lang, chart_data=self._data
        )
        self._chart_widget.setFixedSize(540, 270)
        chart_vbox.addWidget(self._chart_widget, alignment=Qt.AlignHCenter)

        chart_note = QLabel(
            "<b>कुण्डली सङ्केत:</b> प्रत्येक कोठामा भित्री अंकले <b>राशि संख्या</b> र बीचको मुख्य अंकले सो राशिमा प्राप्त <b>समुदाय अष्टकवर्ग बिन्दु (SAV Points)</b> जनाउँछ।"
            if self._is_ne else
            "<b>Chart Legend:</b> Inside each house, the corner number indicates the <b>Sign Number</b> and the centered bold number indicates the <b>Samudaya Ashtakavarga (SAV) Bindus</b>."
        )
        chart_note.setStyleSheet("font-size: 12px; color: #334155; margin-top: 4px;")
        chart_vbox.addWidget(chart_note, alignment=Qt.AlignHCenter)

        self._content_layout.addWidget(chart_section)

        # ── 3. Summary Score Badges ───────────────────────────────────────────
        total_sav = sum(sav_scores)
        avg_sav = total_sav / 12.0
        strong_houses = [i + 1 for i, s in enumerate(sav_scores) if s >= 28]
        weak_houses = [i + 1 for i, s in enumerate(sav_scores) if s < 25]

        summary_box = QFrame()
        summary_box.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
        sum_layout = QVBoxLayout(summary_box)
        sum_layout.setSpacing(6)

        sum_text = (
            f"<b>कुल अष्टकवर्ग बिन्दु (Total Bindus):</b> {to_nepali_digits(total_sav)} (शास्त्रीय आदर्श: ३३७) &nbsp;|&nbsp; "
            f"<b>औसत प्रति राशि:</b> {to_nepali_digits(f'{avg_sav:.1f}')} &nbsp;|&nbsp; "
            f"<b>बलिया/शुभ भावहरू (≥ २८ बिन्दु):</b> {to_nepali_digits(', '.join(str(h) for h in strong_houses)) if strong_houses else 'कुनै छैन'} &nbsp;|&nbsp; "
            f"<b>कमजोर भावहरू (< २५ बिन्दु):</b> {to_nepali_digits(', '.join(str(h) for h in weak_houses)) if weak_houses else 'कुनै छैन'}"
        )
        sum_lbl = QLabel(sum_text)
        sum_lbl.setWordWrap(True)
        sum_lbl.setStyleSheet("font-size: 13px; color: #0f172a;")
        sum_layout.addWidget(sum_lbl)
        self._content_layout.addWidget(summary_box)

        # ── 4. Table 1: Samudaya Ashtakavarga (SAV) House-by-House Analysis ──
        self._add_section_header("१. समुदाय अष्टकवर्ग (SAV) भावगत पूर्ण फल एवं विश्लेषण")
        self._build_sav_detailed_table(lagna_sign, sav_scores)

        # ── 5. Table 2: Bhinnashtakavarga (BAV) 7 Planets Matrix ─────────────
        self._add_section_header("२. भिन्न अष्टकवर्ग (BAV) - सात ग्रहहरूको राशिगत बिन्दु तालिका")
        self._build_bav_matrix_table(bav_scores)

        # ── 6. Life Dimensions Interpretation by Ashtakavarga ─────────────────
        self._add_section_header("३. अष्टकवर्गको आधारमा जीवनका महत्त्वपूर्ण पक्षहरूको विस्तृत विवेचना")
        self._build_life_dimensions_section(lagna_sign, sav_scores)

        # ── 7. How to Interpret Ashtakavarga (अष्टकवर्ग कसरी हेर्ने?) ─────────
        self._add_section_header("४. अष्टकवर्ग कसरी हेर्ने र व्यवहारमा कसरी प्रयोग गर्ने? (विस्तृत मार्गदर्शिका)")
        self._build_how_to_read_guide()

    def _add_section_header(self, text: str):
        sec_lbl = QLabel(text)
        sec_lbl.setStyleSheet("""
            font-size: 16px;
            font-weight: 800;
            color: #0f172a;
            padding-top: 14px;
            padding-bottom: 4px;
            border-bottom: 2px solid #0284c7;
        """)
        self._content_layout.addWidget(sec_lbl)

    def _build_sav_detailed_table(self, lagna_sign: int, sav_scores: List[int]):
        """Builds a compact, content-adaptive 12-house SAV analysis table."""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "भाव", "राशि", "बिन्दु", "स्थिति / सामर्थ्य", "शास्त्रीय फल एवं प्रभाव"
        ])
        table.setRowCount(12)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setWordWrap(True)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
                border: 1px solid #cbd5e1;
                font-size: 12px;
                color: #0f172a;
                selection-background-color: transparent;
                selection-color: inherit;
            }
            QTableWidget::item {
                padding: 4px 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: inherit;
            }
            QTableWidget::item:hover {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #0f172a;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 4px;
                border: 1px solid #cbd5e1;
            }
        """)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        table.setColumnWidth(0, 115)  # भाव
        table.setColumnWidth(1, 75)   # राशि
        table.setColumnWidth(2, 55)   # बिन्दु
        table.setColumnWidth(3, 140)  # स्थिति

        for h in range(1, 13):
            sign_num = ((lagna_sign - 1 + h - 1) % 12) + 1
            rashi_n = RASHI_NAMES_NE[sign_num - 1]
            pts = sav_scores[sign_num - 1] if 0 <= sign_num - 1 < len(sav_scores) else 28

            # Strength category
            if pts >= 32:
                status = "अत्यन्त बलियो (उत्कृष्ट)"
                status_color = "#15803d"  # green
            elif pts >= 28:
                status = "बलियो (शुभ)"
                status_color = "#16a34a"  # green
            elif pts >= 25:
                status = "मध्यम / सम"
                status_color = "#ca8a04"  # amber
            else:
                status = "कमजोर (सावधानी)"
                status_color = "#dc2626"  # red

            # Detailed classical results per house
            phal = self._get_house_sav_phal(h, pts, rashi_n)

            # Row items
            h_item = QTableWidgetItem(f"{to_nepali_digits(h)} औं भाव")
            h_item.setTextAlignment(Qt.AlignCenter)
            h_item.setFont(QFont("Noto Sans Devanagari", 12, QFont.Bold))
            h_item.setForeground(QColor("#0f172a"))

            r_item = QTableWidgetItem(f"{rashi_n} ({to_nepali_digits(sign_num)})")
            r_item.setTextAlignment(Qt.AlignCenter)
            r_item.setFont(QFont("Noto Sans Devanagari", 12, QFont.Bold))
            r_item.setForeground(QColor("#0f172a"))

            p_item = QTableWidgetItem(to_nepali_digits(pts))
            p_item.setTextAlignment(Qt.AlignCenter)
            p_item.setFont(QFont("Noto Sans Devanagari", 14, QFont.Bold))
            p_item.setForeground(QColor("#0f172a"))

            s_item = QTableWidgetItem(status)
            s_item.setTextAlignment(Qt.AlignCenter)
            s_item.setForeground(QColor(status_color))
            s_item.setFont(QFont("Noto Sans Devanagari", 12, QFont.Bold))

            phal_lbl = QLabel(phal)
            phal_lbl.setWordWrap(True)
            phal_lbl.setFont(QFont("Noto Sans Devanagari", 13))
            phal_lbl.setStyleSheet("font-size: 14px; color: #0f172a; line-height: 1.45; padding: 6px 8px; background: transparent;")
            phal_lbl.setTextInteractionFlags(Qt.NoTextInteraction)

            table.setItem(h - 1, 0, h_item)
            table.setItem(h - 1, 1, r_item)
            table.setItem(h - 1, 2, p_item)
            table.setItem(h - 1, 3, s_item)
            table.setCellWidget(h - 1, 4, phal_lbl)

        table.resizeRowsToContents()
        total_h = table.horizontalHeader().height() + sum(table.rowHeight(r) for r in range(12)) + 6
        table.setFixedHeight(total_h)
        self._content_layout.addWidget(table)

    def _get_house_sav_phal(self, house: int, bindus: int, sign_name: str) -> str:
        """Returns deep Parashari astrological interpretations for SAV score in a house."""
        if house == 1:
            if bindus >= 28:
                return f"लग्नमा {to_nepali_digits(bindus)} बिन्दु हुनुले सुदृढ शारीरिक स्वास्थ्य, दीर्घायु, आकर्षक व्यक्तित्व, समाजमा मान-प्रतिष्ठा र आत्मबल उच्च रहने जनाउँछ। जातकमा रोगसँग लड्ने क्षमता प्रचुर हुन्छ।"
            elif bindus >= 25:
                return f"लग्नमा {to_nepali_digits(bindus)} बिन्दु सामान्य शुभ छ। स्वास्थ्य अनुकूल रहन्छ, तर मौसम र खानपानमा सन्तुलन आवश्यक हुन्छ। व्यक्तित्व सामान्य र स्थिर रहनेछ।"
            else:
                return f"लग्नमा {to_nepali_digits(bindus)} बिन्दु कमजोर मानिन्छ। शारीरिक दुर्बलता, शीघ्र थकान वा आत्मविश्वासमा कमी आउन सक्छ। योग, प्राणायाम र सूर्य उपासना लाभदायक हुन्छ।"

        elif house == 2:
            if bindus >= 28:
                return f"द्वितीय भावमा {to_nepali_digits(bindus)} बिन्दुले स्थिर धन सञ्चय, पैतृक सम्पत्ति लाभ, मिठासपूर्ण वाणी तथा पारिवारिक सुख-समृद्धि बलियो रहने संकेत गर्दछ। आर्थिक स्थिरता प्राप्त हुन्छ।"
            elif bindus >= 25:
                return f"द्वितीय भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। धन आर्जन र खर्च बराबरी जस्तै रहनेछ, पारिवारिक स्थिति सामान्य र सन्तोषप्रद रहनेछ।"
            else:
                return f"द्वितीय भावमा {to_nepali_digits(bindus)} बिन्दु कमजोर छ। बचतमा अवरोध, आकस्मिक पारिवारिक खर्च वा वाणीमा कटुताका कारण सम्बन्धमा समस्या आउन सक्छ। बजेट व्यवस्थापनमा ध्यान दिनुपर्छ।"

        elif house == 3:
            if bindus >= 28:
                return f"तृतीय भावमा {to_nepali_digits(bindus)} बिन्दुले उच्च पराक्रम, दाजुभाइ तथा मित्रहरूको पूर्ण सहयोग, साहसिक निर्णय लिने क्षमता तथा सञ्चार, लेखन वा व्यापारमा सफलता दर्शाउँछ।"
            elif bindus >= 25:
                return f"तृतीय भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। पुरुषार्थ सामान्य रहनेछ, भाइबहिनीसँगको सम्बन्ध सामान्य रहनेछ।"
            else:
                return f"तृतीय भावमा {to_nepali_digits(bindus)} बिन्दु न्यून हुनाले मेहनतको तुलनामा कम श्रेय प्राप्त हुने, भाइबहिनीसँग मतभेद वा साहसको कमी हुन सक्छ।"

        elif house == 4:
            if bindus >= 28:
                return f"चतुर्थ भावमा {to_nepali_digits(bindus)} बिन्दु हुनु अत्यन्त शुभ हो। माताको सुख, गृह सुख, वाहन, अचल सम्पत्ति (जग्गा-जमिन) तथा मानसिक शान्ति उत्कृष्ट रहनेछ। जीवनमा सधैं सुख-सुविधाको वृद्धि हुनेछ।"
            elif bindus >= 25:
                return f"चतुर्थ भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। घर-जग्गा र वाहनको सामान्य सुख मिल्नेछ, मानसिक स्थिति सन्तोषप्रद रहनेछ।"
            else:
                return f"चतुर्थ भावमा {to_nepali_digits(bindus)} बिन्दु न्यून हुँदा मानसिक अशान्ति, घरेलु वातावरणमा कलह, माताको स्वास्थ्य चिन्ता वा सम्पत्ति विवाद हुन सक्छ। ध्यान र गृह शान्ति आवश्यक छ।"

        elif house == 5:
            if bindus >= 28:
                return f"पञ्चम भावमा {to_nepali_digits(bindus)} बिन्दुले तीव्र बौद्धिक क्षमता, उच्च विद्या, योग्य एवं आज्ञाकारी सन्तान सुख, मन्त्र सिद्धि र पूर्वजन्मको पुण्य फल प्रबल रहने संकेत गर्दछ।"
            elif bindus >= 25:
                return f"पञ्चम भावमा {to_nepali_digits(bindus)} बिन्दु सामान्य छ। विद्या र सन्तान पक्ष सामान्य रूपमा अघि बढ्नेछ।"
            else:
                return f"पञ्चम भावमा {to_nepali_digits(bindus)} बिन्दु कम हुँदा पढाइमा एकाग्रता भंग हुने, सन्तान सम्बन्धी चिन्ता वा निर्णयमा भ्रम उत्पन्न हुन सक्छ। सरस्वती तथा गायत्री मन्त्र साधना शुभ रहन्छ।"

        elif house == 6:
            if bindus >= 28:
                return f"षष्ठ भावमा {to_nepali_digits(bindus)} बिन्दु हुनुले शत्रुमाथि विजय (शत्रुहन्ता योग), प्रतिस्पर्धात्मक परीक्षामा सफलता, रोग निवारण क्षमता र ऋणबाट मुक्ति पाउने प्रबल सामर्थ्य जनाउँछ।"
            elif bindus >= 25:
                return f"षष्ठ भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। प्रतिस्पर्धा र सामान्य रोग-शत्रुको प्रभाव नियन्त्रणमा रहनेछ।"
            else:
                return f"षष्ठ भावमा {to_nepali_digits(bindus)} बिन्दु न्यून हुँदा पुराना रोग बल्झिने, शत्रुहरू सक्रिय हुने वा ऋणको भार बढ्न सक्ने सम्भावना रहन्छ। स्वास्थ्य र कानुनी मामिलामा सतर्क रहनुपर्छ।"

        elif house == 7:
            if bindus >= 28:
                return f"सप्तम भावमा {to_nepali_digits(bindus)} बिन्दुले सुखी एवं सामञ्जस्यपूर्ण वैवाहिक जीवन, योग्य र सहयोगी जीवनसाथी, व्यावसायिक साझेदारीमा लाभ तथा जनसम्पर्क राम्रो रहने संकेत गर्दछ।"
            elif bindus >= 25:
                return f"सप्तम भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। वैवाहिक जीवन र साझेदारी सामान्य तथा स्थिर रहनेछ।"
            else:
                return f"सप्तम भावमा {to_nepali_digits(bindus)} बिन्दु कमजोर हुँदा दाम्पत्य जीवनमा वैचारिक मतभेद, साझेदारीमा धोका वा व्यापारमा उतार-चढाव आउन सक्छ। संयम र समझदारी आवश्यक छ।"

        elif house == 8:
            if bindus >= 28:
                return f"अष्टम भावमा {to_nepali_digits(bindus)} बिन्दुले दीर्घायु, गम्भीर संकटहरूबाट सहज मुक्ति, गूढ विद्या (ज्योतिष, तन्त्र, विज्ञान) मा रुचि तथा आकस्मिक धन वा बीमा/पैतृक लाभको योग बनाउँछ।"
            elif bindus >= 25:
                return f"अष्टम भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। आयु सामान्य छ, संकटहरू आए पनि टरेर जानेछन्।"
            else:
                return f"अष्टम भावमा {to_nepali_digits(bindus)} बिन्दु न्यून हुनुले अचानक चोटपटक, पुरानो रोग, मानसिक तनाव वा आकस्मिक संकटको भय रहन्छ। महामृत्युञ्जय जप तथा शिव आराधना लाभदायक हुन्छ।"

        elif house == 9:
            if bindus >= 28:
                return f"नवम भाव (भाग्य भाव) मा {to_nepali_digits(bindus)} बिन्दु हुनु अत्यन्तै सौभाग्यशाली मानिन्छ। भाग्यको पूर्ण साथ, पिता र गुरुको आशीर्वाद, धर्म-कर्ममा निष्ठा, तीर्थयात्रा तथा विदेश यात्राबाट विशेष लाभ मिल्नेछ।"
            elif bindus >= 25:
                return f"नवम भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। भाग्यले मध्यम साथ दिनेछ, प्रयास अनुसारको फल मिल्नेछ।"
            else:
                return f"नवम भावमा {to_nepali_digits(bindus)} बिन्दु कमजोर हुँदा भाग्यमा अवरोध, कार्य ढिलाइ वा पितासँग मतभेद हुन सक्छ। धर्म र गुरु सेवाबाट भाग्य वृद्धि हुन्छ।"

        elif house == 10:
            if bindus >= 28:
                return f"दशम भाव (कर्म भाव) मा {to_nepali_digits(bindus)} बिन्दु हुनुले पेशा-व्यवसाय, जागिर वा राजनीतिमा उच्च पद, मान-सम्मान, नेतृत्व क्षमता र सरकारी क्षेत्रबाट लाभ दर्शाउँछ। कार्यक्षेत्रमा स्थायित्व रहन्छ।"
            elif bindus >= 25:
                return f"दशम भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। कर्मक्षेत्रमा सामान्य सफलता र स्थिरता रहनेछ।"
            else:
                return f"दशम भावमा {to_nepali_digits(bindus)} बिन्दु न्यून हुँदा कार्यक्षेत्रमा बारम्बार परिवर्तन, अधिकारीहरूसँग विवाद वा मेहनत अनुसारको पदोन्नति नहुन सक्छ।"

        elif house == 11:
            if bindus >= 28:
                return f"एकादश भाव (लाभ भाव) मा {to_nepali_digits(bindus)} बिन्दु हुनुले सबै प्रकारका मनोकामना पूर्ण हुने, आम्दानीका बहुआयामिक स्रोतहरू बन्ने, ठूला दाजुभाइ तथा मित्रहरूबाट लाभ तथा धनधान्यमा निरन्तर वृद्धि हुने जनाउँछ।"
            elif bindus >= 25:
                return f"एकादश भावमा {to_nepali_digits(bindus)} बिन्दु मध्यम छ। नियमित आयस्रोत रहनेछ र सामान्य अभिलाषा पूरा हुनेछन्।"
            else:
                return f"एकादश भावमा {to_nepali_digits(bindus)} बिन्दु कमजोर हुँदा आम्दानीमा रोकावट, लगानी फस्ने वा साथीभाइबाट सहयोग नपाइने हुन सक्छ। ११ औं भावमा १० औं र १२ औं भन्दा बढी बिन्दु हुनु अनिवार्य मानिन्छ।"

        elif house == 12:
            if bindus >= 28:
                return f"द्वादश भावमा {to_nepali_digits(bindus)} बिन्दुले विदेश गमन, शुभ कार्यमा खर्च, दान-पुण्य, अस्पताल वा जेल जस्ता संकटबाट मुक्ति तथा मोक्ष मार्गमा रुचि बढाउँछ।"
            elif bindus >= 25:
                return f"द्वादश भावमा {to_nepali_digits(bindus)} बिन्दु सामान्य छ। खर्च नियन्त्रणमा रहनेछ र विदेश यात्रा सामान्य फलदायी हुनेछ।"
            else:
                return f"द्वादश भावमा {to_nepali_digits(bindus)} बिन्दु कम हुनुले खर्च कम हुने सकारात्मक पक्ष रहे पनि निन्द्रामा समस्या वा विदेश यात्रामा झन्झट आउन सक्छ।"

        return "सामान्य शास्त्रीय फल।"

    def _build_bav_matrix_table(self, bav_scores: Dict[str, List[int]]):
        """Builds the 7-planet Bhinnashtakavarga Matrix Table."""
        table = QTableWidget()
        table.setColumnCount(15)  # Planet + 12 Signs + Total + Expected
        
        headers = ["ग्रह (Planet)"] + [f"{RASHI_NAMES_NE[i]} ({to_nepali_digits(i+1)})" for i in range(12)] + ["कुल (Total)", "अपेक्षित (Expected)"]
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(7)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
                border: 1px solid #cbd5e1;
                font-size: 13px;
                color: #0f172a;
                selection-background-color: transparent;
                selection-color: inherit;
            }
            QTableWidget::item {
                padding: 6px 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: inherit;
            }
            QTableWidget::item:hover {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #0f172a;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 4px;
                border: 1px solid #cbd5e1;
            }
        """)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1, 13):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(13, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(14, QHeaderView.ResizeToContents)

        for row_idx, p_name in enumerate(SEVEN_GRAHAS):
            scores = bav_scores.get(p_name, [0] * 12)
            tot = sum(scores)
            exp = EXPECTED_BAV_TOTALS.get(p_name, 48)

            p_item = QTableWidgetItem(f"{PLANET_NAMES_NE.get(p_name, p_name)}")
            p_item.setFont(QFont("Noto Sans Devanagari", 12, QFont.Bold))
            p_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            p_item.setForeground(QColor("#0f172a"))
            table.setItem(row_idx, 0, p_item)

            for col_idx in range(12):
                sc = scores[col_idx] if col_idx < len(scores) else 0
                val_item = QTableWidgetItem(to_nepali_digits(sc))
                val_item.setTextAlignment(Qt.AlignCenter)
                val_item.setFont(QFont("Noto Sans Devanagari", 12, QFont.Bold))
                if sc >= 5:
                    val_item.setForeground(QColor("#15803d"))
                elif sc <= 2:
                    val_item.setForeground(QColor("#dc2626"))
                else:
                    val_item.setForeground(QColor("#0f172a"))
                table.setItem(row_idx, col_idx + 1, val_item)

            tot_item = QTableWidgetItem(to_nepali_digits(tot))
            tot_item.setTextAlignment(Qt.AlignCenter)
            tot_item.setFont(QFont("Noto Sans Devanagari", 13, QFont.Bold))
            tot_item.setForeground(QColor("#0f172a"))
            table.setItem(row_idx, 13, tot_item)

            exp_item = QTableWidgetItem(to_nepali_digits(exp))
            exp_item.setTextAlignment(Qt.AlignCenter)
            exp_item.setFont(QFont("Noto Sans Devanagari", 12))
            exp_item.setForeground(QColor("#475569"))
            table.setItem(row_idx, 14, exp_item)

        table.resizeRowsToContents()
        table.setFixedHeight(table.verticalHeader().length() + table.horizontalHeader().height() + 10)
        self._content_layout.addWidget(table)

        bav_note = QLabel(
            "<b>भिन्न अष्टकवर्ग (BAV) नियम:</b> कुनै पनि राशिमा ग्रहको बिन्दु <b>५ वा सोभन्दा बढी</b> भएमा त्यो ग्रहले सो राशिमा गोचर गर्दा वा दशा चल्दा <b>अत्यन्त शुभ फल</b> दिन्छ। "
            "<b>४ बिन्दु</b> भए मध्यम फल र <b>३ वा सोभन्दा कम</b> बिन्दु भएमा अशुभ/कष्टदायी फल दिन्छ।"
        )
        bav_note.setWordWrap(True)
        bav_note.setStyleSheet("font-size: 12px; color: #334155; margin-top: 4px;")
        self._content_layout.addWidget(bav_note)

    def _build_life_dimensions_section(self, lagna_sign: int, sav_scores: List[int]):
        """Renders comprehensive domain-by-domain analysis."""
        def get_h(h_num: int) -> int:
            s_num = ((lagna_sign - 1 + h_num - 1) % 12) + 1
            return sav_scores[s_num - 1] if 0 <= s_num - 1 < len(sav_scores) else 28

        h1, h2, h4, h5, h7, h8, h9, h10, h11, h12 = (
            get_h(1), get_h(2), get_h(4), get_h(5), get_h(7), get_h(8), get_h(9), get_h(10), get_h(11), get_h(12)
        )

        box = QFrame()
        box.setStyleSheet("background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px;")
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(12)

        # 1. Wealth & Finance
        income_vs_exp = "आम्दानी खर्चभन्दा धेरै बलियो छ (उत्कृष्ट धन सञ्चय योग)" if h11 > h12 else "खर्च आम्दानी बराबर वा बढी हुन सक्छ (बचतमा सतर्कता आवश्यक)"
        w_text = (
            f"<b>१. धन, सम्पत्ति र आम्दानी (Wealth & Finance):</b><br>"
            f"• द्वितीय भाव (सञ्चित धन): <b>{to_nepali_digits(h2)} बिन्दु</b> &nbsp;|&nbsp; एकादश भाव (आम्दानी/लाभ): <b>{to_nepali_digits(h11)} बिन्दु</b> &nbsp;|&nbsp; द्वादश भाव (खर्च): <b>{to_nepali_digits(h12)} बिन्दु</b><br>"
            f"• <b>शास्त्रीय सूत्र:</b> लाभ भाव (११ औं) मा व्यय भाव (१२ औं) भन्दा बढी बिन्दु हुनुलाई महाधनी योग मानिन्छ। यस कुण्डलीमा {income_vs_exp}।"
        )
        w_lbl = QLabel(w_text)
        w_lbl.setWordWrap(True)
        w_lbl.setStyleSheet("font-size: 13px; color: #0f172a; line-height: 1.5;")
        box_layout.addWidget(w_lbl)

        # 2. Career & Profession
        c_text = (
            f"<b>२. कर्म, पेसा र प्रतिष्ठा (Career & Profession):</b><br>"
            f"• दशम भाव (कर्म/व्यवसाय): <b>{to_nepali_digits(h10)} बिन्दु</b> &nbsp;|&nbsp; एकादश भाव (प्राप्ति/लाभ): <b>{to_nepali_digits(h11)} बिन्दु</b><br>"
            f"• <b>निष्कर्ष:</b> {'दशम भाव बलवान् भएकाले कार्यक्षेत्रमा स्थायित्व, नेतृत्व क्षमता र उच्च मान-सम्मान प्राप्त हुनेछ।' if h10 >= 28 else 'कर्मक्षेत्रमा सफलता पाउन निरन्तर कडा परिश्रम र धैर्यता आवश्यक पर्दछ।'}"
        )
        c_lbl = QLabel(c_text)
        c_lbl.setWordWrap(True)
        c_lbl.setStyleSheet("font-size: 13px; color: #0f172a; line-height: 1.5;")
        box_layout.addWidget(c_lbl)

        # 3. Health & Longevity
        hl_text = (
            f"<b>३. स्वास्थ्य र दीर्घायु (Health & Longevity):</b><br>"
            f"• प्रथम भाव (लग्न/शरीर): <b>{to_nepali_digits(h1)} बिन्दु</b> &nbsp;|&nbsp; अष्टम भाव (आयु/संकट): <b>{to_nepali_digits(h8)} बिन्दु</b><br>"
            f"• <b>निष्कर्ष:</b> {'लग्न बलियो भएकाले समग्र स्वास्थ्य र रोगप्रतिरोधात्मक क्षमता उच्च रहनेछ।' if h1 >= 28 else 'स्वास्थ्यको नियमित हेरचाह र सन्तुलित दिनचर्या अपनाउनु आवश्यक छ।'}"
        )
        hl_lbl = QLabel(hl_text)
        hl_lbl.setWordWrap(True)
        hl_lbl.setStyleSheet("font-size: 13px; color: #0f172a; line-height: 1.5;")
        box_layout.addWidget(hl_lbl)

        # 4. Family & Property
        fp_text = (
            f"<b>४. गृह, सुख, वाहन र भाग्य (Home, Assets & Fortune):</b><br>"
            f"• चतुर्थ भाव (घर/वाहन/सुख): <b>{to_nepali_digits(h4)} बिन्दु</b> &nbsp;|&nbsp; नवम भाव (भाग्य/धर्म): <b>{to_nepali_digits(h9)} बिन्दु</b><br>"
            f"• <b>निष्कर्ष:</b> {'चतुर्थ र नवम दुवै भाव शुभ बिन्दुयुक्त रहेकाले जीवनमा भूमि, भवन, वाहन सुख र भाग्यको पूर्ण साथ रहनेछ।' if h4 >= 28 and h9 >= 28 else 'भाग्य र सुख पक्ष सामान्य छ, सत्कर्म र धर्मानुष्ठानबाट यसलाई अझ बलियो बनाउन सकिन्छ।'}"
        )
        fp_lbl = QLabel(fp_text)
        fp_lbl.setWordWrap(True)
        fp_lbl.setStyleSheet("font-size: 13px; color: #0f172a; line-height: 1.5;")
        box_layout.addWidget(fp_lbl)

        self._content_layout.addWidget(box)

    def _build_how_to_read_guide(self):
        """Renders the comprehensive 'अष्टकवर्ग कसरी हेर्ने?' guide at the bottom."""
        guide_box = QFrame()
        guide_box.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;")
        g_layout = QVBoxLayout(guide_box)
        g_layout.setSpacing(10)

        guide_content = (
            "<b>अष्टकवर्ग विश्लेषण विधिको पूर्ण नियम एवं प्रयोग विधि:</b><br><br>"
            "<b>१. बिन्दु सामर्थ्य मापदण्ड (Score Thresholds):</b><br>"
            "• <b>३० भन्दा माथि बिन्दु:</b> अत्यन्त बलियो, सर्वाङ्गीण शुभ, राजयोग समान फलदायी।<br>"
            "• <b>२८ देखि २९ बिन्दु:</b> बलियो, सकारात्मक र शुभ फल।<br>"
            "• <b>२५ देखि २७ बिन्दु:</b> मध्यम, सम, सामान्य फल।<br>"
            "• <b>२५ भन्दा कम बिन्दु:</b> कमजोर, कष्टदायी, सो भावसँग सम्बन्धित कुरामा विशेष सावधानी अपनाउनु पर्ने।<br><br>"
            "<b>२. गोचर (Transit) मा अष्टकवर्गको अद्भूत प्रयोग:</b><br>"
            "• जब <b>बृहस्पति (गुरु), सूर्य वा शुक्र</b> जस्ता शुभ ग्रहहरू कुण्डलीमा <b>३० भन्दा बढी बिन्दु</b> भएको राशिमा गोचर गर्छन्, तब जीवनमा पदोन्नति, धनलाभ, विवाह वा ठूलो सफलता मिल्छ।<br>"
            "• जब <b>शनि, राहु वा केतु</b> जस्ता क्रूर ग्रहहरू <b>२५ भन्दा कम बिन्दु</b> भएको राशिमा गोचर गर्छन्, तब रोग, मानसिक तनाव, धनहानि वा विवाद हुन सक्छ। त्यस्तो समयमा शान्ति अनुष्ठान गर्नु पर्दछ।<br><br>"
            "<b>३. दशा र अष्टकवर्गको तालमेल:</b><br>"
            "• महादशा वा अन्तर्दशा नाथ जुन राशिमा बसेका छन्, सो राशिमा यदि <b>भिन्न अष्टकवर्ग (BAV) बिन्दु ५ वा सोभन्दा बढी</b> छ भने सो दशाले जीवनमा सुनौलो फल दिन्छ।<br>"
            "• यदि दशा स्वामी ३ भन्दा कम बिन्दु भएको राशिमा छ भने सो दशा कष्टदायी हुन सक्छ।<br><br>"
            "<b>४. महत्त्वपूर्ण शास्त्रीय तुलना नियम:</b><br>"
            "• <b>११ औं भाव > १० औं भाव:</b> कम मेहनतमा धेरै लाभ र सफलता।<br>"
            "• <b>११ औं भाव > १२ औं भाव:</b> खर्चभन्दा आम्दानी बढी, स्थायी धन संचय।<br>"
            "• <b>१ औं भाव > ७ औं भाव:</b> जीवनसाथी तथा व्यापारिक साझेदारमाथि जातकको प्रभाव र व्यक्तित्व प्रबल।"
        )

        g_lbl = QLabel(guide_content)
        g_lbl.setWordWrap(True)
        g_lbl.setStyleSheet("font-size: 13px; color: #1e293b; line-height: 1.6;")
        g_layout.addWidget(g_lbl)

        self._content_layout.addWidget(guide_box)
