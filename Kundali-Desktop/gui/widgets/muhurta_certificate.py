# -*- coding: utf-8 -*-
"""
gui/widgets/muhurta_certificate.py

Muhurta Certificate Generator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates a printable/PDF "Muhurta Certificate" for:
  - Marriage (विवाह), Griha Pravesh (गृहप्रवेश), Business Start (व्यापार आरम्भ),
    Namkaran (नामकरण), Travel (यात्रा), Thread Ceremony (यज्ञोपवीत), Custom

User selects:
  - Event type, Date, Time, Place (lat/lon/tz), Name
  - Widget shows auspicious summary (tithi, nakshatra, yoga, vara, rahu kaal check)
  - Export as PDF or PNG
"""
from __future__ import annotations
import sys, os, datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QLineEdit, QDateEdit, QTimeEdit,
    QFormLayout, QScrollArea, QMessageBox, QFileDialog, QGroupBox,
    QDoubleSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QLinearGradient, QPen, QBrush
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED, COLOR_GOLD, COLOR_ACCENT,
    COLOR_SUCCESS, COLOR_ERROR
)

EVENT_TYPES_NE = [
    "विवाह (Marriage)",
    "गृहप्रवेश (Griha Pravesh)",
    "व्यापार आरम्भ (Business Start)",
    "नामकरण (Namkaran)",
    "यात्रा (Travel / Yatra)",
    "यज्ञोपवीत (Thread Ceremony)",
    "अन्य (Custom)",
]

TITHI_GOOD = {"द्वितीया","तृतीया","पञ्चमी","सप्तमी","दशमी","एकादशी","द्वादशी","त्रयोदशी"}
NAKSHATRA_GOOD = {"रोहिणी","मृगशिरा","पुनर्वसु","पुष्य","हस्त","चित्रा","स्वाति","अनुराधा","श्रवण","धनिष्ठा","रेवती"}

def _input_style():
    return """
        QWidget {
            background-color: #ffffff;
            color: #0f172a;
        }
        QLineEdit, QComboBox, QDateEdit, QTimeEdit, QDoubleSpinBox {
            background-color: #ffffff;
            border: 1px solid #94a3b8;
            border-radius: 6px;
            padding: 6px 10px;
            color: #000000;
            font-size: 13px;
            font-weight: 500;
            min-height: 32px;
        }
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QDoubleSpinBox:focus {
            border: 2px solid #1d4ed8;
        }
        QLabel {
            color: #0f172a;
            font-weight: 600;
            font-size: 13px;
            background: transparent;
        }
    """


class MuhurtaCertificatePage(QWidget):
    """Muhurta Certificate generator page."""

    def __init__(self, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._result: dict = {}
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #ffffff;")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(20)

        # ── LEFT: Input form ──
        left = QFrame()
        left.setObjectName("muhurtaLeftFrame")
        left.setFixedWidth(350)
        left.setStyleSheet("""
            QFrame#muhurtaLeftFrame {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
            }
        """)
        form_layout = QVBoxLayout(left)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        form_title = QLabel("📝 " + ("मुहूर्त विवरण भर्नुहोस्" if self._is_ne else "Enter Muhurta Details"))
        form_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #1e3a8a; background: transparent;")
        form_layout.addWidget(form_title)

        form_widget = QWidget()
        form_widget.setStyleSheet(_input_style())
        form = QFormLayout(form_widget)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft)

        # Event type
        self._event_combo = QComboBox()
        for ev in EVENT_TYPES_NE:
            self._event_combo.addItem(ev)
        lbl_event = QLabel("कार्यक्रम प्रकार:" if self._is_ne else "Event Type:")
        form.addRow(lbl_event, self._event_combo)

        # Person name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("नाम / Name")
        lbl_name = QLabel("नाम:" if self._is_ne else "Name:")
        form.addRow(lbl_name, self._name_edit)

        # Date
        self._date_edit = QDateEdit()
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        lbl_date = QLabel("मिति:" if self._is_ne else "Date:")
        form.addRow(lbl_date, self._date_edit)

        # Time
        self._time_edit = QTimeEdit()
        self._time_edit.setTime(QTime(7, 0))
        lbl_time = QLabel("समय:" if self._is_ne else "Time:")
        form.addRow(lbl_time, self._time_edit)

        # Latitude
        self._lat_spin = QDoubleSpinBox()
        self._lat_spin.setRange(-90, 90)
        self._lat_spin.setValue(27.7172)
        self._lat_spin.setDecimals(4)
        lbl_lat = QLabel("अक्षांश:" if self._is_ne else "Latitude:")
        form.addRow(lbl_lat, self._lat_spin)

        # Longitude
        self._lon_spin = QDoubleSpinBox()
        self._lon_spin.setRange(-180, 180)
        self._lon_spin.setValue(85.3240)
        self._lon_spin.setDecimals(4)
        lbl_lon = QLabel("देशान्तर:" if self._is_ne else "Longitude:")
        form.addRow(lbl_lon, self._lon_spin)

        form_layout.addWidget(form_widget)

        gen_btn = QPushButton("🔮 " + ("मुहूर्त प्रमाणपत्र बनाउनुस्" if self._is_ne else "Generate Certificate"))
        gen_btn.setMinimumHeight(42)
        gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 800;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1e40af;
            }
        """)
        gen_btn.clicked.connect(self._generate)
        form_layout.addWidget(gen_btn)
        form_layout.addStretch()
        outer.addWidget(left)

        # ── RIGHT: Certificate preview ──
        right = QVBoxLayout()
        right.setSpacing(10)

        # Action buttons
        btn_row = QHBoxLayout()
        self._pdf_btn = QPushButton("📄 PDF Export")
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.clicked.connect(self._export_pdf)
        self._pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:disabled {
                background-color: #e2e8f0;
                color: #94a3b8;
            }
            QPushButton:hover {
                background-color: #1e40af;
            }
        """)
        btn_row.addWidget(self._pdf_btn)

        self._png_btn = QPushButton("🖼 PNG Export")
        self._png_btn.setEnabled(False)
        self._png_btn.clicked.connect(self._export_png)
        self._png_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #94a3b8;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
            }
            QPushButton:hover {
                background-color: #f8fafc;
                border-color: #1d4ed8;
                color: #1d4ed8;
            }
        """)
        btn_row.addWidget(self._png_btn)
        btn_row.addStretch()
        right.addLayout(btn_row)

        # Certificate canvas
        self._canvas = _CertificateCanvas()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #e2e8f0; background: #ffffff; }")
        scroll.setWidget(self._canvas)
        right.addWidget(scroll, 1)
        outer.addLayout(right, 1)

    def _generate(self):
        d = self._date_edit.date()
        t = self._time_edit.time()
        event  = self._event_combo.currentText()
        name   = self._name_edit.text().strip() or ("व्यक्ति" if self._is_ne else "Person")
        lat    = self._lat_spin.value()
        lon    = self._lon_spin.value()
        date   = datetime.date(d.year(), d.month(), d.day())
        time_s = f"{t.hour():02d}:{t.minute():02d}"

        panchang = {}
        try:
            backend = os.path.join(_ROOT, "backend")
            if backend not in sys.path:
                sys.path.insert(0, backend)
            from calculator.reminder_panchang import get_daily_digest
            digest = get_daily_digest(date, latitude=lat, longitude=lon, timezone=5.75, language=self._lang)
            is_ne  = self._lang == "ne"
            t_d    = digest.get("tithi", {})
            n_d    = digest.get("nakshatra", {})
            y_d    = digest.get("yoga", {})
            w_d    = digest.get("weekday", {})
            panchang = {
                "tithi":     t_d.get("nepali") or t_d.get("name", "—"),
                "nakshatra": n_d.get("nepali") or n_d.get("name", "—"),
                "yoga":      y_d.get("nepali") or y_d.get("name", "—"),
                "vara":      w_d.get("nepali") or w_d.get("english", "—"),
                "sunrise":   digest.get("sunrise", "—"),
                "sunset":    digest.get("sunset", "—"),
                "inauspicious": digest.get("inauspicious_periods", []),
                "festivals":    [f[0] if isinstance(f, (list, tuple)) else str(f)
                                 for f in (digest.get("festivals") or [])],
            }
        except Exception:
            panchang = {"tithi": "—", "nakshatra": "—", "yoga": "—", "vara": "—",
                        "sunrise": "—", "sunset": "—", "inauspicious": [], "festivals": []}

        # Auspiciousness check
        inauspicious_now = any(
            p.get("start", "") <= time_s <= p.get("end", "")
            for p in panchang.get("inauspicious", [])
        )
        tithi_good = panchang.get("tithi", "") in TITHI_GOOD
        nakshatra_good = panchang.get("nakshatra", "") in NAKSHATRA_GOOD
        score = sum([tithi_good, nakshatra_good, not inauspicious_now])
        if score == 3:
            rating = ("🟢 अत्यन्त शुभ" if self._is_ne else "🟢 Highly Auspicious")
        elif score == 2:
            rating = ("🟡 शुभ" if self._is_ne else "🟡 Auspicious")
        elif score == 1:
            rating = ("🟠 साधारण" if self._is_ne else "🟠 Moderate")
        else:
            rating = ("🔴 अशुभ — अर्को मुहूर्त छनोट गर्नुस्" if self._is_ne else "🔴 Inauspicious — choose another time")

        self._result = {
            "name": name, "event": event, "date": str(date),
            "time": time_s, "lang": self._lang, "rating": rating,
            "inauspicious_now": inauspicious_now, **panchang
        }
        self._canvas.set_data(self._result)
        self._pdf_btn.setEnabled(True)
        self._png_btn.setEnabled(True)

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PNG", "muhurta_certificate.png", "PNG (*.png)")
        if path:
            pixmap = self._canvas.grab()
            pixmap.save(path)
            QMessageBox.information(self, "Export", f"Saved: {path}")

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "muhurta_certificate.pdf", "PDF (*.pdf)")
        if not path:
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPrinter.A4)
        painter = QPainter(printer)
        target = printer.pageRect(QPrinter.DevicePixel)
        pixmap = self._canvas.grab()
        scaled = pixmap.scaled(int(target.width()), int(target.height()),
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled)
        painter.end()
        QMessageBox.information(self, "PDF Export", f"Saved: {path}")


class _CertificateCanvas(QWidget):
    """Renders the Muhurta Certificate as a styled widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {}
        self.setMinimumSize(580, 700)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, data: dict):
        self._data = data
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        d = self._data

        # Background — pure white
        p.fillRect(0, 0, W, H, QColor("#ffffff"))

        if not d:
            p.setPen(QColor("#475569"))
            p.setFont(QFont("Segoe UI", 14, QFont.Bold))
            p.drawText(0, 0, W, H, Qt.AlignCenter,
                       "विवरण भरेर 'मुहूर्त प्रमाणपत्र बनाउनुस्' थिच्नुस्।")
            p.end()
            return

        # Double ornamental border in rich traditional gold
        p.setPen(QPen(QColor("#b45309"), 3))
        p.drawRoundedRect(12, 12, W - 24, H - 24, 12, 12)
        p.setPen(QPen(QColor("#d97706"), 1))
        p.drawRoundedRect(18, 18, W - 36, H - 36, 10, 10)

        cx = W // 2
        y = 42

        # Header Title
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.setPen(QColor("#92400e"))
        p.drawText(0, y, W, 22, Qt.AlignCenter, "🪐 शिवराम ज्योतिष सफ्टवेयर")
        y += 30

        p.setFont(QFont("Segoe UI", 24, QFont.Bold))
        p.setPen(QColor("#0f172a"))
        p.drawText(0, y, W, 42, Qt.AlignCenter, "मुहूर्त प्रमाणपत्र")
        y += 46

        p.setFont(QFont("Segoe UI", 12, QFont.Bold))
        p.setPen(QColor("#1d4ed8"))
        p.drawText(0, y, W, 24, Qt.AlignCenter, "MUHURTA CERTIFICATE")
        y += 36

        # Decorative Divider
        p.setPen(QPen(QColor("#b45309"), 2))
        p.drawLine(50, y, W - 50, y)
        y += 24

        # Event + name
        p.setFont(QFont("Segoe UI", 17, QFont.Bold))
        p.setPen(QColor("#000000"))
        p.drawText(0, y, W, 32, Qt.AlignCenter, d.get("event", ""))
        y += 38

        lang = d.get("lang", "ne")
        label_name = "नाम:" if lang == "ne" else "Name:"
        p.setFont(QFont("Segoe UI", 14, QFont.Bold))
        p.setPen(QColor("#1e293b"))
        p.drawText(0, y, W, 28, Qt.AlignCenter, f"{label_name}  {d.get('name','')}")
        y += 34

        # Date + Time
        p.setFont(QFont("Segoe UI", 13, QFont.Bold))
        p.setPen(QColor("#1d4ed8"))
        date_lbl = "मिति:" if lang == "ne" else "Date:"
        time_lbl = "समय:" if lang == "ne" else "Time:"
        p.drawText(0, y, W, 28, Qt.AlignCenter,
                   f"{date_lbl} {d.get('date','')}    |    {time_lbl} {d.get('time','')}")
        y += 36

        p.setPen(QPen(QColor("#cbd5e1"), 1, Qt.DashLine))
        p.drawLine(50, y, W - 50, y)
        y += 20

        # Panchang table
        rows = [
            ("वार / Vara",          d.get("vara", "—")),
            ("तिथि / Tithi",        d.get("tithi", "—")),
            ("नक्षत्र / Nakshatra", d.get("nakshatra", "—")),
            ("योग / Yoga",          d.get("yoga", "—")),
            ("सूर्योदय / Sunrise",   d.get("sunrise", "—")),
            ("सूर्यास्त / Sunset",    d.get("sunset", "—")),
        ]
        for label, value in rows:
            p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.setPen(QColor("#475569"))
            p.drawText(60, y, 220, 26, Qt.AlignLeft | Qt.AlignVCenter, label)
            p.setFont(QFont("Segoe UI", 12, QFont.Bold))
            p.setPen(QColor("#000000"))
            p.drawText(W // 2, y, W // 2 - 60, 26, Qt.AlignLeft | Qt.AlignVCenter, value)
            y += 28

        y += 12
        p.setPen(QPen(QColor("#b45309"), 2))
        p.drawLine(50, y, W - 50, y)
        y += 24

        # Rating
        p.setFont(QFont("Segoe UI", 18, QFont.Bold))
        rating = d.get("rating", "")
        color = "#15803d" if "🟢" in rating else ("#b45309" if "🟡" in rating else "#b91c1c")
        p.setPen(QColor(color))
        p.drawText(0, y, W, 38, Qt.AlignCenter, rating)
        y += 48

        # Rahu kaal warning
        if d.get("inauspicious_now"):
            p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.setPen(QColor("#dc2626"))
            p.drawText(0, y, W, 24, Qt.AlignCenter,
                       "⚠️ चेतावनी: यो समयमा अशुभ काल (राहुकाल आदि) छ!")
            y += 28

        # Festivals
        festivals = d.get("festivals") or []
        if festivals:
            p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.setPen(QColor("#b45309"))
            p.drawText(0, y, W, 24, Qt.AlignCenter, "🪔 " + " · ".join(festivals))
            y += 28

        # Footer
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor("#64748b"))
        p.drawText(0, H - 35, W, 22, Qt.AlignCenter,
                   f"Generated by Shivram Jyotish Desktop — {datetime.date.today()}")
        p.end()
