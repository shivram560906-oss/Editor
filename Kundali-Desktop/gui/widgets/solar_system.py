"""Animated native Qt Solar System used by the desktop home page."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
    QWheelEvent,
)
from PySide6.QtWidgets import QSizePolicy, QWidget


@dataclass(frozen=True)
class Planet:
    key: str
    name_en: str
    name_ne: str
    orbit: float
    radius: float
    orbit_speed: float
    spin_speed: float
    light: str
    mid: str
    dark: str
    start_angle: float
    rings: bool = False


PLANETS = (
    # Traditional Navagraha bodies: Sun is painted separately at the center.
    Planet("moon", "Moon", "चन्द्र", 0.085, 0.016, 1.86, 0.16, "#ffffff", "#b9c2d0", "#4e5868", 5.65),
    Planet("mercury", "Mercury", "बुध", 0.13, 0.012, 1.58, 0.35, "#ddd8ce", "#8f8980", "#373532", 0.2),
    Planet("venus", "Venus", "शुक्र", 0.23, 0.020, 1.22, -0.18, "#fff0b4", "#c99055", "#643c24", 1.3),
    Planet("earth", "Earth", "पृथ्वी", 0.33, 0.022, 1.00, 1.00, "#88ddff", "#237bc2", "#092d64", 2.7),
    Planet("mars", "Mars", "मंगल", 0.43, 0.017, 0.82, 0.92, "#ff9a70", "#b3472e", "#491c19", 4.0),
    # Rahu and Ketu are opposite lunar nodes, represented on one shared track.
    Planet("rahu", "Rahu", "राहु", 0.50, 0.019, 0.34, 0.52, "#d6c6ff", "#65499d", "#181329", 0.75),
    Planet("ketu", "Ketu", "केतु", 0.50, 0.018, 0.34, -0.52, "#b9fff0", "#2b8f86", "#102d32", 0.75 + math.pi),
    Planet("jupiter", "Jupiter", "बृहस्पति", 0.56, 0.050, 0.48, 1.70, "#fff1cd", "#c69772", "#5b392b", 5.1),
    Planet("saturn", "Saturn", "शनि", 0.68, 0.043, 0.37, 1.55, "#fff0bd", "#c7a46d", "#604c32", 0.8, True),
    Planet("uranus", "Uranus", "अरुण", 0.79, 0.030, 0.28, -1.08, "#d9ffff", "#68c9d0", "#1d6076", 2.2, True),
    Planet("neptune", "Neptune", "वरुण", 0.90, 0.029, 0.22, 1.18, "#89baff", "#3167d4", "#102665", 3.5),
)


class SolarSystemWidget(QWidget):
    """Responsive, interactive Solar System painted without external assets."""

    def __init__(self, language: str = "ne", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._language = language
        self._started_at = time.monotonic()
        self._elapsed_before_pause = 0.0
        self._paused_at: float | None = None
        self._zoom = 1.0
        self._tilt = 0.58
        self._rotation = -0.08
        self._dragging = False
        self._last_mouse = QPointF()
        self._hovered: int | None = None
        self._planet_positions: list[tuple[QPointF, float]] = []
        self._stars = self._build_stars(310)

        self.setObjectName("SolarSystemHome")
        self.setMinimumSize(640, 430)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.setInterval(20)  # ~50 FPS smooth render
        self._timer.timeout.connect(self.update)
        self._timer.start()
        self._bg_cache = None

    @staticmethod
    def _build_stars(count: int) -> tuple[tuple[float, float, float, float, float], ...]:
        rng = random.Random(28473)
        return tuple(
            (rng.random(), rng.random(), 0.35 + rng.random() * 1.45,
             0.28 + rng.random() * 0.65, rng.random() * math.tau)
            for _ in range(count)
        )

    def _elapsed(self) -> float:
        now = self._paused_at if self._paused_at is not None else time.monotonic()
        return self._elapsed_before_pause + max(0.0, now - self._started_at)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._bg_cache = None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._paused_at is not None:
            self._started_at = time.monotonic()
            self._paused_at = None
        if not self._timer.isActive():
            self._timer.start()

    def hideEvent(self, event) -> None:
        if self._paused_at is None:
            self._elapsed_before_pause = self._elapsed()
            self._paused_at = time.monotonic()
        self._timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        self._timer.stop()
        super().closeEvent(event)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        width = float(self.width())
        height = float(self.height())
        elapsed = self._elapsed()

        self._draw_background(painter, width, height, elapsed)
        if width < 10 or height < 10:
            return

        cx = width * 0.56
        cy = height * 0.55
        available_x = min(cx - 18.0, width - cx - 18.0)
        available_y = min(cy - 76.0, height - cy - 58.0)
        orbit_flatten = max(0.30, min(0.74, self._tilt))
        base = min(available_x / 0.92, available_y / (0.92 * orbit_flatten)) * self._zoom
        base = max(170.0, base)
        center = QPointF(cx, cy)

        self._draw_orbits(painter, center, base, orbit_flatten)
        self._draw_sun(painter, center, max(25.0, min(52.0, base * 0.078)), elapsed)
        self._draw_planets(painter, center, base, orbit_flatten, elapsed)
        self._draw_overlay(painter, width, height)

    def _draw_background(self, painter: QPainter, width: float, height: float, elapsed: float) -> None:
        from PySide6.QtGui import QPixmap
        w_int = max(1, int(width))
        h_int = max(1, int(height))

        if self._bg_cache is None or self._bg_cache.size() != self.size():
            pix = QPixmap(w_int, h_int)
            p = QPainter(pix)
            p.setRenderHint(QPainter.Antialiasing, True)

            background = QRadialGradient(QPointF(width * 0.55, height * 0.52), max(width, height) * 0.82)
            background.setColorAt(0.0, QColor("#101936"))
            background.setColorAt(0.48, QColor("#050b1d"))
            background.setColorAt(1.0, QColor("#01030a"))
            p.fillRect(pix.rect(), QBrush(background))

            nebula = QRadialGradient(QPointF(width * 0.12, height * 0.16), width * 0.55)
            nebula.setColorAt(0.0, QColor(42, 91, 180, 44))
            nebula.setColorAt(0.6, QColor(25, 49, 112, 16))
            nebula.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillRect(pix.rect(), QBrush(nebula))

            p.setPen(Qt.NoPen)
            for x, y, radius, opacity, phase in self._stars:
                alpha = int(255 * opacity * 0.85)
                color = QColor(205, 224, 255, alpha) if phase > 5.0 else QColor(255, 247, 220, alpha)
                p.setBrush(color)
                p.drawEllipse(QPointF(x * width, y * height), radius, radius)
            p.end()
            self._bg_cache = pix

        painter.drawPixmap(0, 0, self._bg_cache)

    def _draw_orbits(self, painter: QPainter, center: QPointF, base: float, flatten: float) -> None:
        painter.save()
        painter.translate(center)
        painter.rotate(math.degrees(self._rotation))
        pen = QPen(QColor(164, 191, 235, 48), 1.0, Qt.DashLine)
        pen.setDashPattern([2.0, 7.0])
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for planet in PLANETS:
            if planet.key in ("moon", "ketu"):
                continue
            radius = base * planet.orbit
            painter.drawEllipse(QRectF(-radius, -radius * flatten, radius * 2, radius * flatten * 2))
        painter.restore()

    def _draw_sun(self, painter: QPainter, center: QPointF, radius: float, elapsed: float) -> None:
        glow = QRadialGradient(center, radius * 3.7)
        glow.setColorAt(0.0, QColor(255, 219, 82, 155))
        glow.setColorAt(0.25, QColor(255, 141, 26, 70))
        glow.setColorAt(0.64, QColor(242, 80, 12, 18))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(center, radius * 3.7, radius * 3.7)

        body = QRadialGradient(center - QPointF(radius * 0.30, radius * 0.34), radius * 1.35)
        body.setColorAt(0.0, QColor("#fffbd0"))
        body.setColorAt(0.24, QColor("#ffd44d"))
        body.setColorAt(0.72, QColor("#ef7b1d"))
        body.setColorAt(1.0, QColor("#8f2609"))
        painter.setBrush(body)
        painter.drawEllipse(center, radius, radius)

        painter.save()
        painter.setClipPath(self._circle_path(center, radius))
        painter.setPen(QPen(QColor(255, 244, 168, 80), max(1.2, radius * 0.055)))
        spin = elapsed * 0.34
        for offset in (-0.48, -0.12, 0.25, 0.55):
            y = center.y() + offset * radius
            x = center.x() + math.sin(spin + offset * 4.0) * radius * 0.28
            painter.drawArc(QRectF(x - radius, y - radius * 0.22, radius * 2, radius * 0.44), 0, 180 * 16)
        painter.restore()

    def _draw_planets(self, painter: QPainter, center: QPointF, base: float, flatten: float, elapsed: float) -> None:
        items = []
        earth_position = center
        orbital_states = []
        cos_r = math.cos(self._rotation)
        sin_r = math.sin(self._rotation)

        for index, planet in enumerate(PLANETS):
            if planet.key == "moon":
                continue
            angle = planet.start_angle + elapsed * planet.orbit_speed * 0.13
            orbit_radius = base * planet.orbit
            local_x = math.cos(angle) * orbit_radius
            local_y = math.sin(angle) * orbit_radius * flatten
            x = center.x() + local_x * cos_r - local_y * sin_r
            y = center.y() + local_x * sin_r + local_y * cos_r
            position = QPointF(x, y)
            orbital_states.append((index, planet, angle, position))
            if planet.key == "earth":
                earth_position = position

        moon_orbit = max(18.0, base * 0.048)
        painter.save()
        painter.translate(earth_position)
        painter.rotate(math.degrees(self._rotation))
        painter.setPen(QPen(QColor(205, 220, 245, 62), 0.8, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(-moon_orbit, -moon_orbit * flatten,
                                   moon_orbit * 2.0, moon_orbit * flatten * 2.0))
        painter.restore()

        for index, planet, angle, position in orbital_states:
            perspective = 0.88 + 0.18 * ((math.sin(angle) + 1.0) * 0.5)
            radius = max(5.0, base * planet.radius * perspective)
            items.append((position.y(), index, planet, position, radius))

        moon_index, moon = next(
            (index, planet) for index, planet in enumerate(PLANETS)
            if planet.key == "moon"
        )
        moon_angle = moon.start_angle + elapsed * moon.orbit_speed * 0.42
        moon_local_x = math.cos(moon_angle) * moon_orbit
        moon_local_y = math.sin(moon_angle) * moon_orbit * flatten
        moon_position = QPointF(
            earth_position.x() + moon_local_x * cos_r - moon_local_y * sin_r,
            earth_position.y() + moon_local_x * sin_r + moon_local_y * cos_r,
        )
        moon_perspective = 0.88 + 0.18 * ((math.sin(moon_angle) + 1.0) * 0.5)
        moon_radius = max(5.0, base * moon.radius * moon_perspective)
        items.append((moon_position.y(), moon_index, moon, moon_position, moon_radius))

        self._planet_positions = [(QPointF(), 0.0)] * len(PLANETS)
        for _, index, planet, position, radius in sorted(items, key=lambda item: item[0]):
            self._planet_positions[index] = (position, radius)
            self._draw_planet(painter, planet, position, radius, elapsed, index == self._hovered)

    def _draw_planet(self, painter: QPainter, planet: Planet, position: QPointF,
                     radius: float, elapsed: float, hovered: bool) -> None:
        if planet.rings:
            self._draw_rings(painter, planet, position, radius, front=False)

        glow = QRadialGradient(position, radius * (2.2 if hovered else 1.65))
        glow.setColorAt(0.0, QColor(planet.light))
        edge = QColor(planet.mid)
        edge.setAlpha(hovered and 80 or 35)
        glow.setColorAt(0.52, edge)
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(position, radius * (2.2 if hovered else 1.65), radius * (2.2 if hovered else 1.65))

        body = QRadialGradient(position - QPointF(radius * 0.36, radius * 0.40), radius * 1.45)
        body.setColorAt(0.0, QColor(planet.light))
        body.setColorAt(0.43, QColor(planet.mid))
        body.setColorAt(1.0, QColor(planet.dark))
        painter.setBrush(body)
        painter.drawEllipse(position, radius, radius)

        painter.save()
        painter.setClipPath(self._circle_path(position, radius))
        spin = elapsed * planet.spin_speed
        if planet.key == "earth":
            self._draw_earth_surface(painter, position, radius, spin)
        elif planet.key == "jupiter":
            self._draw_jupiter_surface(painter, position, radius, spin)
        elif planet.key == "moon":
            self._draw_moon_surface(painter, position, radius, spin)
        elif planet.key in ("rahu", "ketu"):
            self._draw_node_surface(painter, position, radius, planet.key, spin)
        else:
            self._draw_surface_mark(painter, position, radius, spin, planet.key)
        painter.restore()

        if planet.rings:
            self._draw_rings(painter, planet, position, radius, front=True)
        painter.setPen(QPen(QColor(255, 255, 255, 65), 0.8))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(position, radius, radius)

        if hovered or planet.key in ("moon", "rahu", "ketu"):
            self._draw_tooltip(painter, planet, position, radius)

    def _draw_earth_surface(self, painter: QPainter, center: QPointF, radius: float, spin: float) -> None:
        shift = math.sin(spin) * radius * 0.42
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(73, 162, 80, 220))
        painter.drawEllipse(QRectF(center.x() - radius * 0.67 + shift, center.y() - radius * 0.30,
                                   radius * 0.75, radius * 0.40))
        painter.drawEllipse(QRectF(center.x() + radius * 0.05 + shift, center.y() + radius * 0.02,
                                   radius * 0.52, radius * 0.28))
        painter.setBrush(QColor(242, 249, 255, 155))
        painter.drawEllipse(QRectF(center.x() - radius * 0.82 - shift * 0.3, center.y() - radius * 0.52,
                                   radius * 1.35, radius * 0.16))

    def _draw_moon_surface(self, painter: QPainter, center: QPointF, radius: float, spin: float) -> None:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(89, 98, 112, 115))
        craters = ((-0.42, -0.22, 0.17), (0.30, -0.34, 0.13), (0.18, 0.30, 0.21), (-0.30, 0.34, 0.10))
        for index, (x, y, size) in enumerate(craters):
            drift = math.sin(spin + index) * radius * 0.08
            painter.drawEllipse(QPointF(center.x() + x * radius + drift, center.y() + y * radius),
                                radius * size, radius * size * 0.72)
        painter.setPen(QPen(QColor(255, 255, 255, 100), max(0.8, radius * 0.07)))
        painter.drawArc(QRectF(center.x() - radius * 0.68, center.y() - radius * 0.75,
                               radius * 1.36, radius * 1.5), -70 * 16, 130 * 16)

    def _draw_node_surface(self, painter: QPainter, center: QPointF, radius: float,
                           key: str, spin: float) -> None:
        painter.setPen(QPen(QColor(248, 236, 255, 190), max(1.0, radius * 0.12)))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius * 0.62, radius * 0.62)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#171225") if key == "rahu" else QColor("#d7fff4"))
        painter.drawEllipse(QPointF(center.x() + math.sin(spin) * radius * 0.25, center.y()),
                            radius * 0.22, radius * 0.22)

    def _draw_jupiter_surface(self, painter: QPainter, center: QPointF, radius: float, spin: float) -> None:
        colors = (QColor(105, 63, 45, 105), QColor(255, 225, 178, 90), QColor(150, 91, 59, 105))
        for index, offset in enumerate((-0.55, -0.25, 0.03, 0.31, 0.56)):
            half_width = radius * math.sqrt(max(0.06, 1.0 - offset * offset))
            painter.setPen(QPen(colors[index % len(colors)], max(1.0, radius * 0.12)))
            painter.drawLine(QPointF(center.x() - half_width, center.y() + offset * radius),
                             QPointF(center.x() + half_width, center.y() + offset * radius))
        spot_x = center.x() + math.sin(spin * 0.42) * radius * 0.55
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(171, 67, 47, 205))
        painter.drawEllipse(QRectF(spot_x - radius * 0.24, center.y() + radius * 0.16,
                                   radius * 0.48, radius * 0.20))

    def _draw_surface_mark(self, painter: QPainter, center: QPointF, radius: float,
                           spin: float, key: str) -> None:
        painter.setPen(QPen(QColor(255, 255, 255, 58), max(1.0, radius * 0.08)))
        x = center.x() + math.sin(spin * 0.42) * radius * 0.62
        painter.drawArc(QRectF(x - radius * 0.52, center.y() - radius * 0.72,
                               radius * 1.04, radius * 1.44), -70 * 16, 140 * 16)
        if key == "mars":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(82, 27, 22, 135))
            painter.drawEllipse(QPointF(center.x() - radius * 0.25, center.y() + radius * 0.18),
                                radius * 0.24, radius * 0.15)

    def _draw_rings(self, painter: QPainter, planet: Planet, center: QPointF,
                    radius: float, front: bool) -> None:
        painter.save()
        painter.translate(center)
        painter.rotate(-12.0)
        ring_color = QColor(226, 201, 146, 175) if planet.key == "saturn" else QColor(145, 224, 230, 80)
        painter.setPen(QPen(ring_color, max(1.2, radius * (0.18 if planet.key == "saturn" else 0.08))))
        painter.setBrush(Qt.NoBrush)
        start = 180 * 16 if front else 0
        painter.drawArc(QRectF(-radius * 1.85, -radius * 0.45, radius * 3.7, radius * 0.90), start, 180 * 16)
        if planet.key == "saturn":
            painter.setPen(QPen(QColor(181, 145, 88, 115), max(1.0, radius * 0.09)))
            painter.drawArc(QRectF(-radius * 2.18, -radius * 0.54, radius * 4.36, radius * 1.08), start, 180 * 16)
        painter.restore()

    def _draw_tooltip(self, painter: QPainter, planet: Planet, center: QPointF, radius: float) -> None:
        label = planet.name_ne if self._language == "ne" else planet.name_en
        painter.setFont(QFont("Noto Sans Devanagari" if self._language == "ne" else "Segoe UI", 10, QFont.DemiBold))
        metrics = painter.fontMetrics()
        width = metrics.horizontalAdvance(label) + 20
        rect = QRectF(center.x() - width / 2, center.y() - radius - 34, width, 25)
        painter.setPen(QPen(QColor(232, 201, 120, 135), 1.0))
        painter.setBrush(QColor(4, 10, 25, 225))
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QColor("#f2d68e"))
        painter.drawText(rect, Qt.AlignCenter, label)

    def _draw_overlay(self, painter: QPainter, width: float, height: float) -> None:
        left = max(24.0, width * 0.035)
        painter.setPen(QColor("#e8c978"))
        painter.setFont(QFont("Noto Sans Devanagari" if self._language == "ne" else "Segoe UI", 11, QFont.DemiBold))
        kicker = "जीवित सौर्यमण्डल" if self._language == "ne" else "LIVE SOLAR SYSTEM"
        painter.drawText(QRectF(left, 25, width * 0.36, 24), Qt.AlignLeft | Qt.AlignVCenter, kicker)

        painter.setPen(QColor("#f5f0df"))
        painter.setFont(QFont("Noto Sans Devanagari" if self._language == "ne" else "Georgia", 20, QFont.DemiBold))
        title = "शिवराम ज्योतिष सफ्टवेयर" if self._language == "ne" else "Shivram Jyotish Software"
        painter.drawText(QRectF(left, 50, width * 0.42, 40), Qt.AlignLeft | Qt.AlignVCenter, title)

        painter.setPen(QColor(211, 222, 242, 150))
        painter.setFont(QFont("Noto Sans Devanagari" if self._language == "ne" else "Segoe UI", 9))
        hint = ("ग्रहमा होभर गर्नुहोस्  •  तानेर झुकाव बदल्नुहोस्  •  माउस व्हीलले जुम गर्नुहोस्"
                if self._language == "ne" else
                "Hover planets  •  drag to change the view  •  use the mouse wheel to zoom")
        painter.drawText(QRectF(left, height - 43, width - left * 2, 24), Qt.AlignLeft | Qt.AlignVCenter, hint)

    @staticmethod
    def _circle_path(center: QPointF, radius: float) -> QPainterPath:
        path = QPainterPath()
        path.addEllipse(center, radius, radius)
        return path

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        position = event.position()
        if self._dragging:
            delta = position - self._last_mouse
            self._rotation += delta.x() * 0.004
            self._tilt = max(0.32, min(0.74, self._tilt + delta.y() * 0.003))
            self._last_mouse = position
            self.update()
            return

        hovered = None
        for index, (planet_position, radius) in enumerate(self._planet_positions):
            delta = position - planet_position
            if math.hypot(delta.x(), delta.y()) <= max(12.0, radius + 7.0):
                hovered = index
                break
        if hovered != self._hovered:
            self._hovered = hovered
            self.setCursor(Qt.PointingHandCursor if hovered is not None else Qt.ArrowCursor)
            self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_mouse = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.PointingHandCursor if self._hovered is not None else Qt.ArrowCursor)
            event.accept()

    def leaveEvent(self, event) -> None:
        if not self._dragging:
            self._hovered = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
        super().leaveEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        steps = event.angleDelta().y() / 120.0
        self._zoom = max(0.76, min(1.17, self._zoom + steps * 0.045))
        self.update()
        event.accept()
