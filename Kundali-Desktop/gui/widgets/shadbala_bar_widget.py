"""
gui/widgets/shadbala_bar_widget.py

Custom Native Qt Shadbala Comparison Bar Widget with Animated Rising Bars.
Matches the classical Vedic astrology Shadbala bar chart:
- Top Header Pill: Rounded capsule with blue border & "षड्बल" label
- Dual-Zone Background:
    - Upper Zone: Rich Green (Auspicious / Adequate strength >= 1.0 Rupa)
    - Lower Zone: Rich Red (Inauspicious / Deficit strength < 1.0 Rupa)
    - Distinct pulsating threshold line at 1.0 Rupa baseline
- 7 Planetary Strength Bars:
    - Order: Sun (सू), Moon (चं), Mars (मं), Mercury (बु), Jupiter (गु), Venus (शु), Saturn (श)
    - Staggered dynamic rising animation with OutBack spring bounce
    - Luminous crest flare on top of each rising bar
    - Inside bar: Distinct colored abbreviation + exact numerical Rupa value
    - Interactive: Click or hover a bar to select that planet in the Kundali
    - Double click replays the rising animation
"""
from __future__ import annotations
import math
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QRadialGradient, QMouseEvent

PLANETS_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

PLANET_LABELS_NE = {
    "Sun": "सू",
    "Moon": "चं",
    "Mars": "मं",
    "Mercury": "बु",
    "Jupiter": "गु",
    "Venus": "शु",
    "Saturn": "श"
}

PLANET_TEXT_COLORS = {
    "Sun": "#dc2626",      # Red / Orange
    "Moon": "#1e293b",     # Dark Charcoal
    "Mars": "#e11d48",     # Crimson Red
    "Mercury": "#059669",  # Emerald Green
    "Jupiter": "#ea580c",  # Warm Orange
    "Venus": "#c026d3",    # Magenta / Purple
    "Saturn": "#2563eb",   # Royal Blue
}


class ShadbalaMiniBarWidget(QWidget):
    """Clean custom painted Shadbala dual-zone bar graph with dynamic rising animation."""

    planet_clicked = Signal(str)

    # ── Qt Properties for QPropertyAnimation ───────────────────────────────
    def _get_rise_progress(self) -> float: return self._rise_progress
    def _set_rise_progress(self, v: float):
        self._rise_progress = max(0.0, min(1.0, float(v)))
        self.update()
    rise_progress = Property(float, _get_rise_progress, _set_rise_progress)

    def __init__(self, chart_data: Optional[dict] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._data = chart_data or {}
        self._hovered_planet: Optional[str] = None
        self._selected_planet: Optional[str] = None

        # ── Animation State ─────────────────────────────────────────────────
        self._rise_progress: float = 0.0 if chart_data else 1.0
        self._pulse_tick: int = 0
        self._has_animated: bool = False
        self._anim: Optional[QPropertyAnimation] = None
        self._pulse_timer: Optional[QTimer] = None

        self.setMinimumSize(310, 220)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMouseTracking(True)
        self.setToolTip("षड्बल अनुपात (डबल क्लिकले एनिमेसन पुनः देखाउँछ)")

        self._start_pulse_timer()

        if self._data:
            QTimer.singleShot(70, self._play_animation)

    # ── Lifecycle & Public API ────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if self._data and not self._has_animated:
            self._play_animation()

    def set_data(self, chart_data: dict) -> None:
        self._data = chart_data or {}
        self._has_animated = False
        self._play_animation()

    def set_selected_planet(self, planet_name: Optional[str]) -> None:
        self._selected_planet = planet_name
        self.update()

    # ── Animation Engine ──────────────────────────────────────────────────────

    def _play_animation(self) -> None:
        """Plays the smooth staggered bar rise animation with spring bounce."""
        if self._anim and self._anim.state() != QPropertyAnimation.Stopped:
            self._anim.stop()

        self._rise_progress = 0.0
        self._has_animated = True
        self.update()

        self._anim = QPropertyAnimation(self, b"rise_progress", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(850)
        self._anim.setEasingCurve(QEasingCurve.OutBack)
        self._anim.start()

    def _start_pulse_timer(self) -> None:
        """Continuous 30ms timer for threshold line pulse and bar sparkle."""
        if self._pulse_timer is not None:
            return
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(30)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start()

    def _tick_pulse(self) -> None:
        self._pulse_tick += 1
        # Gentle repaint for continuous ambient threshold pulse
        self.update()

    def _get_planet_rupas(self) -> List[tuple[str, str, Optional[float], str]]:
        """Returns list of (planet_key, label_ne, rupa_or_None, text_color)."""
        raw_shadbala = self._data.get("shadbala")
        # The payload nests the per-graha table under shadbala["planets"].
        # Reading shadbala["Sun"] directly always returned nothing, and the old
        # fabricated fallback then papered over that with invented numbers.
        # The flat shape is still accepted so older saved payloads keep working.
        nested = raw_shadbala.get("planets") if isinstance(raw_shadbala, dict) else None
        if isinstance(nested, dict):
            shadbala = nested
        else:
            shadbala = raw_shadbala if isinstance(raw_shadbala, dict) else {}
        results = []

        for p_key in PLANETS_ORDER:
            sb = shadbala.get(p_key)
            rupa: Optional[float] = None
            if isinstance(sb, dict):
                if "total_rupas" in sb and sb["total_rupas"] is not None:
                    try:
                        rupa = float(sb["total_rupas"])
                    except (TypeError, ValueError):
                        rupa = None
                if rupa is None:
                    tot = sb.get("total_shashtiamsa")
                    if tot is None:
                        tot = sb.get("total_shashtiamsas")
                    if tot is None:
                        tot = sb.get("total")
                    try:
                        tot = float(tot) if tot is not None else 0.0
                    except (TypeError, ValueError):
                        tot = 0.0
                    if tot > 0:
                        rupa = tot / 60.0

            # No synthetic estimate: a planet with no authoritative Shadbala
            # entry stays unavailable.  The previous house/sign "base + 0.25"
            # heuristic printed invented numbers beside the real ones, which
            # PROJECT_RULES.md 3.2 forbids.
            if rupa is None:
                results.append((p_key, PLANET_LABELS_NE.get(p_key, p_key[:2]), None,
                                PLANET_TEXT_COLORS.get(p_key, "#1e293b")))
                continue

            label = PLANET_LABELS_NE.get(p_key, p_key[:2])
            t_color = PLANET_TEXT_COLORS.get(p_key, "#1e293b")
            results.append((p_key, label, round(rupa, 2), t_color))

        return results

    # ── Paint Pipeline ────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        w = float(self.width())
        h = float(self.height())

        # ── 1. Draw Outer Card Container ──
        margin = 4.0
        outer_rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)
        painter.setPen(QPen(QColor("#cbd5e1"), 1.2))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRoundedRect(outer_rect, 8.0, 8.0)

        # ── 2. Top Header Pill: "षड्बल" ──
        pill_w = min(180.0, w * 0.70)
        pill_h = 24.0
        pill_x = (w - pill_w) / 2.0
        pill_y = margin + 6.0
        pill_rect = QRectF(pill_x, pill_y, pill_w, pill_h)

        # Blue border, white fill
        painter.setPen(QPen(QColor("#0284c7"), 2.0))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRoundedRect(pill_rect, 12.0, 12.0)

        # Pill text
        painter.setPen(QColor("#0f172a"))
        pill_font = QFont(["Nirmala UI", "Segoe UI Historic", "Mangal", "Noto Sans Devanagari"], 11, QFont.Bold)
        painter.setFont(pill_font)
        painter.drawText(pill_rect, Qt.AlignCenter, "षड्बल")

        # ── 3. Graph Area Dimensions ──
        graph_top = pill_y + pill_h + 8.0
        graph_bottom = h - margin - 8.0
        graph_left = margin + 8.0
        graph_right = w - margin - 8.0
        graph_w = graph_right - graph_left
        graph_h = graph_bottom - graph_top

        if graph_h <= 40 or graph_w <= 100:
            painter.end()
            return

        items = self._get_planet_rupas()
        known = [item[2] for item in items if item[2] is not None]
        if not known:
            # Nothing authoritative to plot.  Draw a muted panel and a readable
            # message: white text here would be invisible on the white card,
            # which is how this state previously looked like a blank box.
            empty_rect = QRectF(graph_left, graph_top, graph_w, graph_h)
            painter.setPen(QPen(QColor("#94a3b8"), 1.2, Qt.DashLine))
            painter.setBrush(QBrush(QColor("#f1f5f9")))
            painter.drawRoundedRect(empty_rect, 6.0, 6.0)
            painter.setPen(QColor("#475569"))
            empty_font = QFont(["Nirmala UI", "Segoe UI Historic", "Mangal",
                                "Noto Sans Devanagari"], 10, QFont.Bold)
            painter.setFont(empty_font)
            painter.drawText(empty_rect.adjusted(6, 0, -6, 0),
                             Qt.AlignCenter, "षड्बल उपलब्ध छैन")
            painter.end()
            return
        max_val = max(1.75, max(known) * 1.12)
        threshold_val = 1.00

        # Threshold Y position
        thresh_ratio = threshold_val / max_val
        thresh_y = graph_bottom - (thresh_ratio * graph_h)

        # ── Draw Background Zones with animated shimmer ──
        graph_rect = QRectF(graph_left, graph_top, graph_w, graph_h)
        painter.save()
        painter.setClipRect(graph_rect)

        tick    = self._pulse_tick
        shimmer = 0.5 + 0.5 * math.sin(tick * 0.04)   # 0..1 slow breath

        # Upper Zone: Animated Green gradient (>= 1.0 Rupa)
        green_rect = QRectF(graph_left, graph_top, graph_w, thresh_y - graph_top)
        ggrad = QLinearGradient(graph_left, graph_top, graph_left, thresh_y)
        ggrad.setColorAt(0.0,  QColor(5,  150, 105))
        ggrad.setColorAt(0.45, QColor(int(16 + 30 * shimmer), int(185 + 25 * shimmer), int(129 + 20 * shimmer)))
        ggrad.setColorAt(1.0,  QColor(52, 211, 153))
        painter.fillRect(green_rect, QBrush(ggrad))

        # Lower Zone: Animated Red gradient (< 1.0 Rupa)
        red_rect = QRectF(graph_left, thresh_y, graph_w, graph_bottom - thresh_y)
        rgrad = QLinearGradient(graph_left, thresh_y, graph_left, graph_bottom)
        rgrad.setColorAt(0.0,  QColor(int(185 + 30 * shimmer), int(28 - 5 * shimmer), 38))
        rgrad.setColorAt(0.5,  QColor(220, 38, 38))
        rgrad.setColorAt(1.0,  QColor(int(127 + 10 * shimmer), 29, 29))
        painter.fillRect(red_rect, QBrush(rgrad))

        # Diagonal animated shimmer sweep overlay
        sweep_x = graph_left + (tick * 1.8 % (graph_w + 80)) - 40
        shine_alpha = int(12 + 10 * math.sin(tick * 0.06))
        shine = QLinearGradient(sweep_x - 30, graph_top, sweep_x + 30, graph_bottom)
        shine.setColorAt(0.0, QColor(255, 255, 255, 0))
        shine.setColorAt(0.5, QColor(255, 255, 255, shine_alpha))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(shine))
        painter.setPen(Qt.NoPen)
        painter.drawRect(graph_rect)

        # Threshold line — multi-layer pulsating glow
        t_outer = int(80  + 60 * math.sin(tick * 0.10))
        t_inner = int(160 + 90 * math.sin(tick * 0.12))
        painter.setPen(QPen(QColor(254, 240, 138, t_outer), 5.0, Qt.SolidLine))
        painter.drawLine(QPointF(graph_left, thresh_y), QPointF(graph_right, thresh_y))
        painter.setPen(QPen(QColor(254, 240, 138, t_inner), 1.8, Qt.DashLine))
        painter.drawLine(QPointF(graph_left, thresh_y), QPointF(graph_right, thresh_y))

        # Outer border
        painter.setPen(QPen(QColor("#0f172a"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(graph_rect)

        # ── 4. Draw 7 Staggered Rising Planetary Bars ──
        num_bars = len(items)
        spacing  = max(4.0, graph_w * 0.018)
        bar_w    = (graph_w - spacing * (num_bars + 1)) / num_bars

        for i, (p_key, label_ne, val, t_color_hex) in enumerate(items):
            bar_x = graph_left + spacing + i * (bar_w + spacing)

            label_font_size = max(8, int(bar_w * 0.38))
            label_font = QFont(["Nirmala UI", "Segoe UI Historic", "Mangal",
                                "Noto Sans Devanagari"], label_font_size, QFont.Bold)
            value_font = QFont(["Segoe UI", "Arial", "Roboto"],
                               max(7, int(bar_w * 0.28)), QFont.Bold)

            if val is None:
                painter.setFont(label_font)
                painter.setPen(QColor("#ffffff"))
                painter.drawText(
                    QRectF(bar_x - 4.0, graph_bottom - 32.0 - label_font_size + 2.0,
                           bar_w + 8.0, label_font_size + 8.0),
                    Qt.AlignCenter, label_ne)
                painter.setFont(value_font)
                painter.setPen(QColor("#fecaca"))
                painter.drawText(
                    QRectF(bar_x - 4.0, graph_bottom - 16.0, bar_w + 8.0, 14.0),
                    Qt.AlignCenter, "—")
                continue

            bar_ratio = min(1.0, max(0.1, val / max_val))

            # Staggered rise progress with spring curve (logic unchanged)
            p_delay = i * 0.05
            if self._rise_progress <= p_delay:
                p_prog = 0.0
            else:
                raw_t = min(1.0, (self._rise_progress - p_delay) / 0.65)
                t_rem = raw_t - 1.0
                p_prog = max(0.0, 1.0 + 2.5 * (t_rem ** 3) + 1.5 * (t_rem ** 2))

            bar_h = max(0.0, bar_ratio * graph_h * p_prog)
            bar_y = graph_bottom - bar_h

            if bar_h <= 1.0:
                continue

            bar_rect    = QRectF(bar_x, bar_y, bar_w, bar_h)
            is_above    = (val >= threshold_val)
            is_hovered  = (self._hovered_planet == p_key)
            is_selected = (self._selected_planet == p_key)

            # ── Bar Fill: translucent pearl gradient (unchanged) ──
            grad = QLinearGradient(bar_x, bar_y, bar_x + bar_w, bar_y)
            if is_hovered or is_selected:
                grad.setColorAt(0.0, QColor("#e0e7ff"))
                grad.setColorAt(0.5, QColor("#eff6ff"))
                grad.setColorAt(1.0, QColor("#dbeafe"))
            else:
                grad.setColorAt(0.0, QColor("#c7d2fe"))
                grad.setColorAt(0.5, QColor("#e0e7ff"))
                grad.setColorAt(1.0, QColor("#c7d2fe"))
            painter.setBrush(QBrush(grad))

            # ── Bar Border: GREEN if above threshold, RED if below ──
            if is_selected:
                border_color = QColor("#f59e0b")   # gold
                border_w = 2.5
            elif is_hovered:
                border_color = QColor("#0284c7")   # blue
                border_w = 2.2
            elif is_above:
                g_alpha = int(200 + 55 * math.sin(tick * 0.09 + i * 0.7))
                border_color = QColor(5, 150, 105, g_alpha)   # pulsing emerald
                border_w = 2.0
            else:
                r_alpha = int(200 + 55 * math.sin(tick * 0.11 + i * 0.5))
                border_color = QColor(220, 38, 38, r_alpha)   # pulsing crimson
                border_w = 2.0

            painter.setPen(QPen(border_color, border_w))
            painter.drawRect(bar_rect)

            # ── Outer glow halo (zone-colored, subtle) ──
            if p_prog >= 0.95 and not (is_hovered or is_selected):
                glow_alpha = int(38 + 28 * math.sin(tick * 0.08 + i))
                glow_color = (QColor(5, 150, 105, glow_alpha)
                              if is_above else QColor(220, 38, 38, glow_alpha))
                painter.setPen(QPen(glow_color, 5.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(bar_rect.adjusted(-2, -2, 2, 2))

            # ── Luminous Crest line ──
            crest_alpha = int(200 + 55 * math.sin(tick * 0.13 + i * 1.1))
            painter.setPen(QPen(QColor(255, 255, 255, crest_alpha), max(1.5, bar_w * 0.08)))
            painter.drawLine(QPointF(bar_x + 1.0, bar_y + 1.0),
                             QPointF(bar_x + bar_w - 1.0, bar_y + 1.0))

            # ── Flame flicker tip above bar ──
            if p_prog >= 0.90 and bar_h > 20:
                flicker  = math.sin(tick * 0.22 + i * 1.3)
                flame_h  = max(2.0, bar_w * 0.14) * (0.7 + 0.3 * abs(flicker))
                flame_cx = bar_x + bar_w / 2.0 + flicker * bar_w * 0.10
                flame_y  = bar_y - flame_h / 2.0
                f_alpha  = int(160 + 70 * abs(flicker))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(251, 146, 60, f_alpha)))
                painter.drawEllipse(QPointF(flame_cx, flame_y),
                                    max(1.5, bar_w * 0.12), flame_h * 0.7)

            # ── Sparkle constellation above threshold bars ──
            if is_above and p_prog >= 0.95:
                star_pt = QPointF(bar_x + bar_w / 2.0,
                                  max(graph_top + 6.0, bar_y - 7.0))
                star_r     = max(2.0, bar_w * 0.10)
                star_alpha = int(190 + 65 * math.sin(tick * 0.15 + i))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(254, 240, 138, star_alpha)))
                painter.drawEllipse(star_pt, star_r, star_r)
                for dx, dy, sc in [(-bar_w * 0.20, -bar_w * 0.18, 0.55),
                                    (+bar_w * 0.22, -bar_w * 0.14, 0.45)]:
                    sa = int(130 + 80 * math.sin(tick * 0.18 + i + dx))
                    painter.setBrush(QBrush(QColor(254, 240, 138, sa)))
                    painter.drawEllipse(
                        QPointF(star_pt.x() + dx, star_pt.y() + dy),
                        star_r * sc, star_r * sc)

            # ── Text inside Bar ──
            painter.setFont(label_font)
            painter.setPen(QColor(t_color_hex))
            label_h    = label_font_size + 8.0
            label_y    = graph_bottom - 32.0
            label_rect = QRectF(bar_x - 4.0, label_y - label_h + 2.0,
                                bar_w + 8.0, label_h)
            painter.drawText(label_rect, Qt.AlignCenter, label_ne)

            painter.setFont(value_font)
            painter.setPen(QColor("#0f172a"))
            val_rect = QRectF(bar_x - 4.0, graph_bottom - 16.0, bar_w + 8.0, 14.0)
            painter.drawText(val_rect, Qt.AlignCenter, f"{val:.2f}")

        painter.restore()
        painter.end()

    # ── Mouse Interaction ─────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            hit = self._planet_at(event.pos())
            if hit:
                self._selected_planet = hit
                self.planet_clicked.emit(hit)
                self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # Double clicking anywhere on the bar chart replays the rising animation!
        self._play_animation()

    def mouseMoveEvent(self, event: QMouseEvent):
        hit = self._planet_at(event.pos())
        if hit != self._hovered_planet:
            self._hovered_planet = hit
            self.setCursor(Qt.PointingHandCursor if hit else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, event):
        self._hovered_planet = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def _planet_at(self, pos) -> Optional[str]:
        w = float(self.width())
        h = float(self.height())
        margin = 4.0
        graph_top = margin + 38.0
        graph_bottom = h - margin - 8.0
        graph_left = margin + 8.0
        graph_right = w - margin - 8.0
        graph_w = graph_right - graph_left

        items = self._get_planet_rupas()
        num_bars = len(items)
        spacing = max(4.0, graph_w * 0.018)
        total_spacing = spacing * (num_bars + 1)
        bar_w = (graph_w - total_spacing) / num_bars

        for i, (p_key, _, _, _) in enumerate(items):
            bar_x = graph_left + spacing + i * (bar_w + spacing)
            if bar_x <= pos.x() <= bar_x + bar_w and graph_top <= pos.y() <= graph_bottom:
                return p_key
        return None
