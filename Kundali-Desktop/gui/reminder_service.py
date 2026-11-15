# -*- coding: utf-8 -*-
"""
gui/reminder_service.py

System tray reminder service for Shivram Jyotish Desktop.

Runs inside the main Qt event loop (no extra process).  While the app is
running (even minimised to the tray) it:

  - Shows a daily "आजको शुभ-अशुभ" panchang digest at a user-chosen time.
  - Alerts when an inauspicious period (Rahu Kaal / Gulika / Yamaganda)
    starts.
  - Alerts when a good choghadiya (Amrit / Shubh / Labh) starts.
  - Alerts for tithi observances (Ekadashi, Purnima, Amavasya) and fixed
    Nepali festivals, and lists upcoming ones in the tray menu.

All alerts are computed with the same backend engine as the in-app reports
(backend.calculator.reminder_panchang) so they always agree with the screen.

Preferences are persisted with QSettings("ShivramJyotish", "Desktop").
"""
from __future__ import annotations

import datetime
import sys
import os
import threading
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, QThread, Signal, Slot, QSettings, Qt
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont
from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu, QMessageBox, QApplication, QDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QTimeEdit,
    QSpinBox, QPushButton, QFrame, QDoubleSpinBox
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import COLOR_GOLD, BG_SECONDARY, BORDER_COLOR, COLOR_TEXT_PRIMARY  # noqa: E402


# ── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_LOCATION = {"latitude": 27.7172, "longitude": 85.3240, "timezone": 5.75}
DEFAULT_DIGEST_TIME = "07:00"

SETTING_ENABLED      = "reminders/enabled"
SETTING_DIGEST_TIME  = "reminders/digest_time"
SETTING_RAHU         = "reminders/rahu_kaal"
SETTING_CHOGHADIYA   = "reminders/choghadiya"
SETTING_FESTIVALS    = "reminders/festivals"
SETTING_UPCOMING     = "reminders/upcoming_days"
SETTING_LATITUDE     = "reminders/latitude"
SETTING_LONGITUDE    = "reminders/longitude"
SETTING_TIMEZONE     = "reminders/timezone"
SETTING_DIGEST_SENT   = "reminders/digest_sent_for"


# ── Small settings dialog (used from the tray menu) ─────────────────────────
class ReminderSettingsDialog(QDialog):
    """Compact reminder configuration dialog reachable from the tray menu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("रिमाइन्डर सेटिङ / Reminder Settings")
        self.setMinimumWidth(420)
        s = QSettings("ShivramJyotish", "Desktop")
        self._old = {
            "enabled": s.value(SETTING_ENABLED, True, type=bool),
            "digest_time": str(s.value(SETTING_DIGEST_TIME, DEFAULT_DIGEST_TIME)),
            "rahu": s.value(SETTING_RAHU, True, type=bool),
            "choghadiya": s.value(SETTING_CHOGHADIYA, True, type=bool),
            "festivals": s.value(SETTING_FESTIVALS, True, type=bool),
            "upcoming": int(s.value(SETTING_UPCOMING, 15)),
            "latitude": float(s.value(SETTING_LATITUDE, DEFAULT_LOCATION["latitude"])),
            "longitude": float(s.value(SETTING_LONGITUDE, DEFAULT_LOCATION["longitude"])),
            "timezone": float(s.value(SETTING_TIMEZONE, DEFAULT_LOCATION["timezone"])),
        }

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel("⏰ रिमाइन्डर सेटिङ (Reminder Settings)")
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 15px; font-weight: 700;")
        root.addWidget(title)

        box = QFrame()
        box.setStyleSheet(f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(14, 12, 14, 12)
        bl.setSpacing(8)

        self._enabled = QCheckBox("रिमाइन्डर सक्षम गर्नुहोस् (Enable reminders)")
        self._enabled.setChecked(self._old["enabled"])
        bl.addWidget(self._enabled)

        # Digest time
        row = QHBoxLayout()
        row.addWidget(QLabel("दैनिक पञ्चाङ्ग डाइजेस्ट समय (Digest time):"))
        self._digest = QTimeEdit()
        hh, mm = map(int, self._old["digest_time"].split(":"))
        self._digest.setTime(self._digest.time().fromString(f"{hh:02d}:{mm:02d}", "HH:mm"))
        self._digest.setDisplayFormat("HH:mm")
        row.addWidget(self._digest)
        row.addStretch()
        bl.addLayout(row)

        # Upcoming days
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("आगामी पर्व कति दिन देखाउने (Upcoming days):"))
        self._upcoming = QSpinBox()
        self._upcoming.setRange(1, 60)
        self._upcoming.setValue(self._old["upcoming"])
        row2.addWidget(self._upcoming)
        row2.addStretch()
        bl.addLayout(row2)

        # Alert toggles
        self._rahu = QCheckBox("राहुकाल / गुलिका / यमगण्ड सुरु हुँदा सूचना (Inauspicious period alerts)")
        self._rahu.setChecked(self._old["rahu"])
        bl.addWidget(self._rahu)

        self._choghadiya = QCheckBox("शुभ चौघडीया सुरु हुँदा सूचना (Good choghadiya alerts)")
        self._choghadiya.setChecked(self._old["choghadiya"])
        bl.addWidget(self._choghadiya)

        self._festivals = QCheckBox("पर्व / एकादशी / पूर्णिमा सूचना (Festival & observance alerts)")
        self._festivals.setChecked(self._old["festivals"])
        bl.addWidget(self._festivals)

        # Location
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("अक्षांश (Latitude):"))
        self._lat = QDoubleSpinBox()
        self._lat.setRange(-90, 90)
        self._lat.setDecimals(4)
        self._lat.setValue(self._old["latitude"])
        row3.addWidget(self._lat)
        row3.addWidget(QLabel("देशान्तर (Longitude):"))
        self._lon = QDoubleSpinBox()
        self._lon.setRange(-180, 180)
        self._lon.setDecimals(4)
        self._lon.setValue(self._old["longitude"])
        row3.addWidget(self._lon)
        bl.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("समय क्षेत्र (Timezone UTC+):"))
        self._tz = QDoubleSpinBox()
        self._tz.setRange(-12, 14)
        self._tz.setDecimals(2)
        self._tz.setValue(self._old["timezone"])
        row4.addWidget(self._tz)
        row4.addStretch()
        bl.addLayout(row4)

        root.addWidget(box)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        ok = QPushButton("💾 सेभ गर्नुहोस् / Save")
        ok.setStyleSheet(f"background: {COLOR_GOLD}; color: #000; font-weight: 700; padding: 6px 16px; border-radius: 6px;")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("रद्द / Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        root.addLayout(btns)

    def values(self) -> dict:
        return {
            "enabled": self._enabled.isChecked(),
            "digest_time": self._digest.time().toString("HH:mm"),
            "rahu": self._rahu.isChecked(),
            "choghadiya": self._choghadiya.isChecked(),
            "festivals": self._festivals.isChecked(),
            "upcoming": self._upcoming.value(),
            "latitude": self._lat.value(),
            "longitude": self._lon.value(),
            "timezone": self._tz.value(),
        }


# ── Background digest worker ────────────────────────────────────────────────
class _DigestWorker(QThread):
    """Computes today's digest + upcoming events off the UI thread."""
    finished = Signal(dict)

    def __init__(self, params: dict, parent=None):
        super().__init__(parent)
        self._params = params

    def run(self):
        try:
            from calculator.reminder_panchang import get_daily_digest, get_upcoming_events
            p = self._params
            today = datetime.date.today()
            digest = get_daily_digest(
                today,
                latitude=p["latitude"], longitude=p["longitude"],
                timezone=p["timezone"], language=p["language"],
            )
            events = get_upcoming_events(
                today,
                days=p["upcoming"],
                latitude=p["latitude"], longitude=p["longitude"],
                timezone=p["timezone"], language=p["language"],
            )
            self.finished.emit({"digest": digest, "events": events, "date": today.isoformat()})
        except Exception as exc:  # pragma: no cover - defensive
            self.finished.emit({"error": str(exc)})


# ── The service itself ──────────────────────────────────────────────────────
class ReminderService(QObject):
    """System-tray reminder service wired into the main event loop."""

    def __init__(self, language: str = "ne", parent: Optional[QObject] = None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._settings = QSettings("ShivramJyotish", "Desktop")
        self._tray: Optional[QSystemTrayIcon] = None
        self._tray_menu: Optional[QMenu] = None
        self._tick_timer: Optional[QTimer] = None
        self._worker: Optional[_DigestWorker] = None
        self._digest_data: Optional[dict] = None
        self._last_rahu_notified = ""
        self._last_choghadiya_notified = ""
        self._last_festival_notified = ""

    # ── Lifecycle ──────────────────────────────────────────────────────────
    def start(self) -> None:
        """Create the tray icon and start the minute ticker."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._build_tray()
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(60_000)  # every minute
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()
        # Run immediately on startup too.
        self._tick()
        # Refresh the menu / digest shortly after startup (ephemeris may still
        # be loading during the splash).
        QTimer.singleShot(2500, self._refresh_digest)

    def stop(self) -> None:
        if self._tick_timer is not None:
            self._tick_timer.stop()
        if self._tray is not None:
            self._tray.hide()

    def set_language(self, language: str) -> None:
        self._language = language
        self._is_ne = language == "ne"
        if self._tray_menu is not None:
            self._rebuild_menu()

    # ── Settings helpers ────────────────────────────────────────────────────
    def settings(self) -> dict:
        s = self._settings
        return {
            "enabled": s.value(SETTING_ENABLED, True, type=bool),
            "digest_time": str(s.value(SETTING_DIGEST_TIME, DEFAULT_DIGEST_TIME)),
            "rahu": s.value(SETTING_RAHU, True, type=bool),
            "choghadiya": s.value(SETTING_CHOGHADIYA, True, type=bool),
            "festivals": s.value(SETTING_FESTIVALS, True, type=bool),
            "upcoming": int(s.value(SETTING_UPCOMING, 15)),
            "latitude": float(s.value(SETTING_LATITUDE, DEFAULT_LOCATION["latitude"])),
            "longitude": float(s.value(SETTING_LONGITUDE, DEFAULT_LOCATION["longitude"])),
            "timezone": float(s.value(SETTING_TIMEZONE, DEFAULT_LOCATION["timezone"])),
        }

    def update_settings(self, values: dict) -> None:
        s = self._settings
        if "enabled" in values:
            s.setValue(SETTING_ENABLED, bool(values["enabled"]))
        if "digest_time" in values:
            s.setValue(SETTING_DIGEST_TIME, str(values["digest_time"]))
        if "rahu" in values:
            s.setValue(SETTING_RAHU, bool(values["rahu"]))
        if "choghadiya" in values:
            s.setValue(SETTING_CHOGHADIYA, bool(values["choghadiya"]))
        if "festivals" in values:
            s.setValue(SETTING_FESTIVALS, bool(values["festivals"]))
        if "upcoming" in values:
            s.setValue(SETTING_UPCOMING, int(values["upcoming"]))
        if "latitude" in values:
            s.setValue(SETTING_LATITUDE, float(values["latitude"]))
        if "longitude" in values:
            s.setValue(SETTING_LONGITUDE, float(values["longitude"]))
        if "timezone" in values:
            s.setValue(SETTING_TIMEZONE, float(values["timezone"]))
        # Reset daily-sent marker when settings change so a manual digest
        # refresh can fire again.
        s.remove(SETTING_DIGEST_SENT)
        self._last_rahu_notified = ""
        self._last_choghadiya_notified = ""
        self._last_festival_notified = ""
        self._refresh_digest()

    # ── Tray construction ───────────────────────────────────────────────────
    def _build_tray(self) -> None:
        icon = QIcon(self._make_icon_pixmap())
        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip("Shivram Jyotish — रिमाइन्डर / Reminders")
        self._tray.activated.connect(self._on_tray_activated)
        self._rebuild_menu()
        self._tray.show()

    def _make_icon_pixmap(self) -> QPixmap:
        pm = QPixmap(64, 64)
        pm.fill(QColor("#080711"))
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#d4af37"))
        painter.drawEllipse(6, 6, 52, 52)
        painter.setPen(QColor("#080711"))
        font = QFont("Segoe UI", 20, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pm.rect(), Qt.AlignCenter, "ॐ")
        painter.end()
        return pm

    def _rebuild_menu(self) -> None:
        if self._tray is None:
            return
        menu = QMenu()
        is_ne = self._is_ne
        act_today = menu.addAction("📅 " + ("आजको पञ्चाङ्ग (Today's Digest)" if is_ne else "Today's Digest"))
        act_today.triggered.connect(self._show_digest_dialog)
        act_settings = menu.addAction("⚙ " + ("रिमाइन्डर सेटिङ..." if is_ne else "Reminder Settings..."))
        act_settings.triggered.connect(self._open_settings)
        menu.addSeparator()

        # Upcoming events submenu (refreshed by _refresh_digest).
        self._events_menu = menu.addMenu("🪔 " + ("आगामी पर्व / Events" if is_ne else "Upcoming Events"))
        self._refresh_events_menu()
        menu.addSeparator()

        act_show = menu.addAction("🏠 " + ("एप देखाउनुहोस् (Show App)" if is_ne else "Show App"))
        act_show.triggered.connect(self._show_app)
        act_quit = menu.addAction("❌ " + ("बन्द गर्नुहोस् (Quit)" if is_ne else "Quit"))
        act_quit.triggered.connect(self._quit_app)
        menu.addSeparator()

        status = menu.addAction(("🟢 रिमाइन्डर सक्रिय" if is_ne else "🟢 Reminders active")
                                if self.settings()["enabled"]
                                else ("🔴 रिमाइन्डर निष्क्रिय" if is_ne else "🔴 Reminders disabled"))
        status.setEnabled(False)

        self._tray_menu = menu
        self._tray.setContextMenu(menu)

    def _refresh_events_menu(self) -> None:
        if getattr(self, "_events_menu", None) is None:
            return
        self._events_menu.clear()
        events = (self._digest_data or {}).get("events", [])
        is_ne = self._is_ne
        if not events:
            act = self._events_menu.addAction("—")
            act.setEnabled(False)
            return
        for ev in events[:10]:
            name = ev.get("name_ne" if is_ne else "name_en", ev.get("name_en", ""))
            if is_ne:
                date_label = ev.get("date_bs") or ev.get("date", "")
                days_label = ev.get("in_days_ne", str(ev.get("in_days", "")))
                label = f"{date_label} (+{days_label} दिन)  {name}"
            else:
                date_label = ev.get("date_bs_en") or ev.get("date", "")
                label = f"{date_label} (+{ev['in_days']}d)  {name}"
            self._events_menu.addAction(label)

    # ── Tray interaction ────────────────────────────────────────────────────
    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._show_app()

    def _show_app(self) -> None:
        window = self.parent()
        if window is not None:
            window.showNormal()
            window.raise_()
            window.activateWindow()

    def _quit_app(self) -> None:
        # Ask the main window to close (or quit directly if detached).
        window = self.parent()
        if window is not None and hasattr(window, "close"):
            window.close()
        else:
            QApplication.instance().quit()

    def _open_settings(self) -> None:
        dialog = ReminderSettingsDialog()
        if dialog.exec() == QDialog.Accepted:
            self.update_settings(dialog.values())

    # ── Public entry points for in-app pages ──────────────────────────────
    def open_reminder_panel(self, action: str) -> None:
        """Open one of the reminder dialogs from an in-app page.

        ``action`` is one of ``"digest"``, ``"events"`` or ``"settings"``.
        The digest / events dialogs need the computed data; if the background
        worker is still running we wait for it and open the dialog when ready.
        """
        if action == "settings":
            self._open_settings()
            return
        target = self._show_digest_dialog if action == "digest" else self._show_events_dialog
        if self._digest_data:
            target()
            return
        if self._worker is not None and self._worker.isRunning():
            self._worker.finished.connect(
                lambda payload: target() if "error" not in payload else None
            )
            return
        self._refresh_digest()
        self._worker.finished.connect(
            lambda payload: target() if "error" not in payload else None
        )

    def _ensure_digest_data(self) -> dict:
        if self._digest_data and self._digest_data.get("digest"):
            return self._digest_data
        try:
            from calculator.reminder_panchang import get_daily_digest, get_upcoming_events
            s = self.settings()
            today = datetime.date.today()
            digest = get_daily_digest(
                today,
                latitude=s["latitude"], longitude=s["longitude"],
                timezone=s["timezone"], language=self._language,
            )
            events = get_upcoming_events(
                today,
                days=s["upcoming"],
                latitude=s["latitude"], longitude=s["longitude"],
                timezone=s["timezone"], language=self._language,
            )
            self._digest_data = {"digest": digest, "events": events, "date": today.isoformat()}
            return self._digest_data
        except Exception:
            return self._digest_data or {}

    def _show_events_dialog(self) -> None:
        """Show a dialog listing upcoming festivals / vrat / observances."""
        data = self._ensure_digest_data()
        events = (data or {}).get("events", [])
        if not events:
            QMessageBox.information(
                self._tray_parent(),
                "Events",
                "आगामी ६० दिनभित्र कुनै पर्व/व्रत छैन।" if self._is_ne
                else "No upcoming festivals or vrats within 60 days.",
            )
            return
        lines = ["🪔 " + ("आगामी पर्व तथा व्रतहरू" if self._is_ne else "Upcoming Festivals & Vrats")]
        for ev in events:
            name = ev.get("name_ne" if self._is_ne else "name_en", "")
            if self._is_ne:
                date_label = ev.get("date_bs") or ev.get("date", "")
                days_label = ev.get("in_days_ne", str(ev.get("in_days", "")))
                lines.append(f"   • {date_label}  (+{days_label} दिन) — {name}")
            else:
                date_label = ev.get("date_bs_en") or ev.get("date", "")
                lines.append(f"   • {date_label}  (+{ev['in_days']} days) — {name}")
        box = QMessageBox(self._tray_parent())
        box.setWindowTitle("🪔 " + ("आगामी पर्व" if self._is_ne else "Upcoming Events"))
        box.setText("\n".join(lines))
        box.setStandardButtons(QMessageBox.Ok)
        box.exec()

    # ── Digest dialog ───────────────────────────────────────────────────────
    def _show_digest_dialog(self) -> None:
        data = self._ensure_digest_data()
        digest = data.get("digest") or {}
        if not digest:
            QMessageBox.information(
                self._tray_parent(),
                "Digest",
                "पञ्चाङ्ग डाटा लोड हुन सकेन।"
                if self._is_ne else "Panchang data could not be loaded.",
            )
            return
        lines = [digest.get("summary_ne" if self._is_ne else "summary_en", "")]
        if self._is_ne:
            date_label = digest.get("date_bs") or digest.get("date", "")
            lines.append(f"{digest['weekday']['nepali']} · {date_label}")
        else:
            date_label = digest.get("date_bs_en") or digest.get("date", "")
            lines.append(f"{digest['weekday']['english']} · {date_label}")
        lines.append("")
        if self._is_ne:
            lines.append(f"सूर्योदय: {digest['sunrise']}  |  सूर्यास्त: {digest['sunset']}")
            lines.append(f"लग्न-महिना: {digest['lunar_month']}  |  संवत्सर: {digest['samvatsara']}")
        else:
            lines.append(f"Sunrise: {digest['sunrise']}  |  Sunset: {digest['sunset']}")
            lines.append(f"Lunar month: {digest['lunar_month']}  |  Samvatsara: {digest['samvatsara']}")
        if digest.get("festivals"):
            fest_ne = " · ".join(n for n, _ in digest["festivals"])
            lines.append(("🪔 " + fest_ne) if self._is_ne else ("🪔 " + " · ".join(e for _, e in digest["festivals"])))
        lines.append("")
        lines.append("⚠ " + ("अशुभ काल:" if self._is_ne else "Inauspicious periods:"))
        for period in digest.get("inauspicious_periods", []):
            label = period.get("label_ne" if self._is_ne else "label_en", period["key"])
            lines.append(f"   • {label}: {period['start']} – {period['end']}")
        lines.append("")
        lines.append("✅ " + ("शुभ चौघडीया:" if self._is_ne else "Good choghadiya:"))
        for period in digest.get("good_periods", [])[:4]:
            name = period.get("name_ne" if self._is_ne else "name_en", "")
            lines.append(f"   • {name}: {period['start']} – {period['end']}")

        box = QMessageBox(self._tray_parent())
        box.setWindowTitle("📅 " + ("आजको पञ्चाङ्ग" if self._is_ne else "Today's Panchang"))
        box.setText("\n".join(lines))
        box.setStandardButtons(QMessageBox.Ok)
        box.exec()

    def _tray_parent(self):
        return self.parent() if self.parent() is not None else None

    # ── Digest / event refresh ──────────────────────────────────────────────
    def _refresh_digest(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        s = self.settings()
        self._worker = _DigestWorker(
            {
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "timezone": s["timezone"],
                "language": self._language,
                "upcoming": s["upcoming"],
            },
            self,
        )
        self._worker.finished.connect(self._on_digest_ready)
        self._worker.start()

    @Slot(dict)
    def _on_digest_ready(self, payload: dict) -> None:
        if "error" in payload:
            return
        self._digest_data = payload
        self._refresh_events_menu()
        # If today's digest has not been shown yet (per settings marker), fire
        # the daily notification once.
        if self.settings()["enabled"]:
            self._maybe_send_daily_digest()

    # ── Per-minute tick ─────────────────────────────────────────────────────
    def _tick(self) -> None:
        if not self.settings()["enabled"]:
            return
        if self._digest_data is None:
            self._refresh_digest()
            return
        digest = (self._digest_data or {}).get("digest") or {}
        if not digest:
            return
        now = datetime.datetime.now().strftime("%H:%M")
        self._check_rahu_kaal(digest, now)
        self._check_choghadiya(digest, now)
        self._check_festivals(digest)
        # Feature 11: Planetary transit (Gochar) alerts — checked every 5 min
        if not hasattr(self, "_transit_check_count"):
            self._transit_check_count = 0
        self._transit_check_count = (self._transit_check_count + 1) % 5
        if self._transit_check_count == 0:
            self._check_planetary_transits()

    def _maybe_send_daily_digest(self) -> None:
        s = self.settings()
        digest_time = str(s.get("digest_time", DEFAULT_DIGEST_TIME))
        now = datetime.datetime.now()
        today = now.date().isoformat()
        sent_for = str(self._settings.value(SETTING_DIGEST_SENT, ""))
        if sent_for == today:
            return
        target = datetime.datetime.strptime(digest_time, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        if now >= target:
            digest = (self._digest_data or {}).get("digest") or {}
            if digest:
                self._notify(
                    "📅 " + ("आजको पञ्चाङ्ग" if self._is_ne else "Today's Panchang"),
                    digest.get("summary_ne" if self._is_ne else "summary_en", ""),
                    QSystemTrayIcon.Information,
                )
                self._settings.setValue(SETTING_DIGEST_SENT, today)

    def _check_rahu_kaal(self, digest: dict, now: str) -> None:
        if not self.settings()["rahu"]:
            return
        periods = digest.get("inauspicious_periods", [])
        if not periods:
            return
        for period in periods:
            start, end = period.get("start", "—"), period.get("end", "—")
            key = f"{period['key']}:{start}"
            if now == start and key != self._last_rahu_notified:
                label = period.get("label_ne" if self._is_ne else "label_en", period["key"])
                self._notify(
                    "⚠ " + ("अशुभ काल सुरु" if self._is_ne else "Inauspicious period begins"),
                    f"{label}: {start} – {end}",
                    QSystemTrayIcon.Warning,
                )
                self._last_rahu_notified = key

    def _check_choghadiya(self, digest: dict, now: str) -> None:
        if not self.settings()["choghadiya"]:
            return
        for period in digest.get("good_periods", []):
            start = period.get("start", "—")
            key = f"chog:{start}"
            if now == start and key != self._last_choghadiya_notified:
                name = period.get("name_ne" if self._is_ne else "name_en", "")
                self._notify(
                    "✅ " + ("शुभ चौघडीया सुरु" if self._is_ne else "Good choghadiya begins"),
                    f"{name}: {start} – {period.get('end', '—')}",
                    QSystemTrayIcon.Information,
                )
                self._last_choghadiya_notified = key

    def _check_festivals(self, digest: dict) -> None:
        if not self.settings()["festivals"]:
            return
        festivals = digest.get("festivals", [])
        if not festivals:
            return
        today = (self._digest_data or {}).get("date", "")
        key = f"{today}:{','.join(n for n, _ in festivals)}"
        if key == self._last_festival_notified:
            return
        self._last_festival_notified = key
        names_ne = " · ".join(n for n, _ in festivals)
        self._notify(
            "🪔 " + ("आजको पर्व" if self._is_ne else "Today's festival"),
            names_ne,
            QSystemTrayIcon.Information,
        )

    # ── Notification helper ────────────────────────────────────────────────
    def _notify(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon) -> None:
        if self._tray is not None and QSystemTrayIcon.supportsMessages():
            self._tray.showMessage(title, message, icon, 8000)

    # ── Feature 11: Planetary Transit / Ingress Alerts ─────────────────────
    # Notifies when a major planet changes sign (Rashi) during the day.
    # Checked every minute; fires once per planet-sign transit.

    _TRANSIT_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

    def _check_planetary_transits(self) -> None:
        """Check if any planet has changed Rashi since last check — notify once."""
        if not self.settings().get("enabled", True):
            return
        try:
            import sys as _sys, os as _os
            _backend = _os.path.join(_ROOT, "backend")
            if _backend not in _sys.path:
                _sys.path.insert(0, _backend)
            from calculator.panchang import get_current_planet_positions
            s = self.settings()
            positions = get_current_planet_positions(
                latitude=s["latitude"],
                longitude=s["longitude"],
                timezone=s["timezone"],
            )
        except Exception:
            return  # backend not ready yet — fail silently

        NE = {
            "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल",
            "Mercury": "बुध", "Jupiter": "बृहस्पति",
            "Venus": "शुक्र", "Saturn": "शनि",
        }
        SIGN_NE = [
            "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
            "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"
        ]
        SIGN_EN = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]

        if not hasattr(self, "_transit_cache"):
            self._transit_cache: dict[str, int] = {}

        for planet, data in (positions or {}).items():
            if planet not in self._TRANSIT_PLANETS:
                continue
            lon = float(data.get("sidereal_longitude") or data.get("longitude") or 0)
            sign_idx = int(lon / 30) % 12  # 0-based
            prev = self._transit_cache.get(planet)
            if prev is not None and prev != sign_idx:
                # Planet just changed sign!
                if self._is_ne:
                    p_name = NE.get(planet, planet)
                    sign_name = SIGN_NE[sign_idx]
                    title = f"🪐 गोचर परिवर्तन: {p_name}"
                    msg = f"{p_name} अब {sign_name} राशिमा प्रवेश गर्‍यो।"
                else:
                    sign_name = SIGN_EN[sign_idx]
                    title = f"🪐 Transit: {planet} → {sign_name}"
                    msg = f"{planet} has entered {sign_name}."
                self._notify(title, msg, QSystemTrayIcon.Information)
            self._transit_cache[planet] = sign_idx
