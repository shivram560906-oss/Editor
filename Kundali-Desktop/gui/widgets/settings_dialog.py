# -*- coding: utf-8 -*-
"""Settings & Preferences Dialog for Shivram Jyotish Desktop.

Allows configuration and permanent persistence of:
- Calculation Siddhanta (Drik, Surya Siddhanta, Grahalaghava, KP, Raman)
- Default Ayanamsha
- Default House System
- Rahu/Ketu Node Type
- Default Language
"""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QMessageBox, QFrame,
    QScrollArea, QApplication
)

# Style tokens
COLOR_GOLD = "#a16207"
COLOR_PRIMARY = "#8b1e0f"
BG_DARK = "#ffffff"
BG_CARD = "#ffffff"
BORDER_COLOR = "#d0d0d0"
TEXT_PRIMARY = "#111111"
TEXT_MUTED = "#111111"

SIDDHANTA_MODES = [
    ("DRIK", "दृक-सिद्धान्त (Drik / Swiss Ephemeris - आधुनिक शुद्ध खगोलीय) [Default]"),
    ("SURYA_SIDDHANTA", "सूर्यसिद्धान्त (Surya Siddhanta - परम्परागत नेपाली पात्रो मोड)"),
    ("GRAHALAGHAVA", "ग्रहलाघव पद्धति (Grahalaghava System)"),
    ("KP", "कृष्णमूर्ति पद्धति (KP System)"),
    ("RAMAN", "बि.भि. रमन पद्धति (BV Raman System)"),
]

AYANAMSHA_MODES = [
    ("LAHIRI", "लाहिरी / चित्रपक्षीय (Lahiri / Chitrapaksha) [मानक]"),
    ("RAMAN", "बि.भि. रमन (B.V. Raman)"),
    ("KRISHNAMURTI", "कृष्णमूर्ति (KP)"),
    ("TRUE_CITRA", "शुद्ध चित्रपक्ष (True Chitra)"),
    ("FAGAN_BRADLEY", "फगन-ब्राड्ली (Fagan-Bradley)"),
    ("YUKTESHWAR", "युक्तेश्वर (Yukteshwar)"),
    ("JN_BHASIN", "जे.एन. भसिन (J.N. Bhasin)"),
    ("SURYASIDDHANTA", "सूर्यसिद्धान्त अयनांश (Surya Siddhanta Ayanamsha)"),
]

HOUSE_MODES = [
    ("WHOLE_SIGN", "सम्पूर्ण राशि भाव (Whole Sign - Vedic Standard)"),
    ("SRIPATI", "श्रीपति भाव (Porphyry / Sripati)"),
    ("EQUAL", "समान भाव पद्धति (Equal House)"),
    ("PLACIDUS", "प्लेसिडस (Placidus - KP Standard)"),
]

NODE_MODES = [
    ("MEAN", "औसत राहु/केतु (Mean Node) [शास्त्रीय]"),
    ("TRUE", "वास्तविक राहु/केतु (True Node)"),
]


class SettingsDialog(QDialog):
    """Settings and preferences dialog."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ सेटिङ तथा प्राथमिकताहरू (Settings & Preferences)")
        
        # Adaptive dialog sizing to comfortably fit any screen resolution
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            target_w = min(680, max(520, int(avail.width() * 0.7)))
            target_h = min(620, max(420, int(avail.height() * 0.82)))
            self.resize(target_w, target_h)
            self.setMinimumSize(min(520, avail.width() - 40), min(380, avail.height() - 60))
        else:
            self.resize(660, 560)
            self.setMinimumSize(520, 400)
            
        self._settings = QSettings("ShivramJyotish", "Desktop")
        self._init_ui()
        self._load_values()

    def _init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_DARK};
                color: {TEXT_PRIMARY};
            }}
            QLabel {{
                background-color: transparent;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QGroupBox {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 16px;
                font-weight: bold;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
            QComboBox {{
                background-color: #ffffff;
                color: #111111;
                border: 1px solid #7c6f64;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 13px;
                min-height: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                color: #111111;
                selection-background-color: #1d4ed8;
                selection-color: #ffffff;
            }}
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #a32412;
            }}
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(10)

        # Header (Fixed at top)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        header = QLabel("शिवराम ज्योतिष: मुख्य गणना तथा ज्योतिषीय प्राथमिकताहरू")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_PRIMARY};")
        header_layout.addWidget(header)
        subtitle = QLabel("तपाईंका ज्योतिषीय प्राथमिकताहरू तथा पूर्वनिर्धारित मानहरू यहाँ परिवर्तन गर्न सक्नुहुन्छ।")
        subtitle.setStyleSheet("font-size: 12px; color: #555555;")
        header_layout.addWidget(subtitle)
        root_layout.addLayout(header_layout)

        # Scroll Area for the main settings options
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #f1f1f1;
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #999999;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {BG_DARK};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(2, 2, 10, 4)
        content_layout.setSpacing(14)

        # Siddhanta Group
        siddhanta_box = QGroupBox("१. पञ्चाङ्ग तथा खगोलीय गणना सिद्धान्त (Calculation Siddhanta)")
        s_layout = QVBoxLayout(siddhanta_box)
        s_layout.setContentsMargins(14, 14, 14, 14)
        s_layout.setSpacing(8)

        s_desc = QLabel(
            "पञ्चाङ्ग र कुण्डली गणना कुन सिद्धान्त अनुसार गर्ने? "
            "(एकपटक परिवर्तन गरेपछि पुनः नबदलिएसम्म सोही सिद्धान्तले स्थायी रूपमा काम गर्दछ)"
        )
        s_desc.setWordWrap(True)
        s_desc.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
        s_layout.addWidget(s_desc)

        self._siddhanta_combo = QComboBox()
        for code, label in SIDDHANTA_MODES:
            self._siddhanta_combo.addItem(label, code)
        s_layout.addWidget(self._siddhanta_combo)
        content_layout.addWidget(siddhanta_box)

        # Astrology Defaults Group
        astro_box = QGroupBox("२. पूर्वनिर्धारित ज्योतिषीय विकल्पहरू (Astrological Defaults)")
        form = QFormLayout(astro_box)
        form.setContentsMargins(14, 14, 14, 14)
        form.setSpacing(10)

        self._ayanamsha_combo = QComboBox()
        for code, label in AYANAMSHA_MODES:
            self._ayanamsha_combo.addItem(label, code)
        form.addRow("अयनांश (Ayanamsha):", self._ayanamsha_combo)

        self._house_combo = QComboBox()
        for code, label in HOUSE_MODES:
            self._house_combo.addItem(label, code)
        form.addRow("भाव पद्धति (House System):", self._house_combo)

        self._node_combo = QComboBox()
        for code, label in NODE_MODES:
            self._node_combo.addItem(label, code)
        form.addRow("राहु/केतु प्रकार (Node Type):", self._node_combo)

        self._language_combo = QComboBox()
        self._language_combo.addItem("नेपाली (Nepali)", "ne")
        self._language_combo.addItem("English (अंग्रेजी)", "en")
        form.addRow("पूर्वनिर्धारित भाषा (Language):", self._language_combo)

        content_layout.addWidget(astro_box)

        # Appearance Group (Theme Toggle)
        appear_box = QGroupBox("३. रूप रङ र थिम (Appearance & Theme)")
        a_layout = QVBoxLayout(appear_box)
        a_layout.setContentsMargins(14, 14, 14, 14)
        a_layout.setSpacing(8)

        theme_row = QHBoxLayout()
        theme_lbl = QLabel("थिम छनोट (Theme):")
        theme_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px;")
        theme_row.addWidget(theme_lbl)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem("☀️ क्लासिक लाइट थिम (Classic Light)", "classic")
        self._theme_combo.addItem("🌙 डार्क थिम (Cosmic Dark)", "dark")
        theme_row.addWidget(self._theme_combo, 1)
        a_layout.addLayout(theme_row)

        content_layout.addWidget(appear_box)

        # Upcoming Reminders Preview
        remind_box = QGroupBox("४. आगामी रिमाइन्डर पूर्वावलोकन (Upcoming Reminders Preview)")
        r_layout = QVBoxLayout(remind_box)
        r_layout.setContentsMargins(14, 14, 14, 14)
        r_layout.setSpacing(6)

        self._reminder_preview_lbl = QLabel("लोड हुँदैछ...")
        self._reminder_preview_lbl.setWordWrap(True)
        self._reminder_preview_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; line-height: 1.5;")
        r_layout.addWidget(self._reminder_preview_lbl)

        content_layout.addWidget(remind_box)
        QTimer.singleShot(100, self._load_reminder_preview)

        # Finish scroll area setup
        scroll_area.setWidget(content_widget)
        root_layout.addWidget(scroll_area, 1)

        # Divider line above action buttons
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet(f"background-color: {BORDER_COLOR}; max-height: 1px;")
        root_layout.addWidget(divider)

        # Buttons (Pinned at the bottom, ALWAYS visible!)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(2, 4, 2, 2)
        btn_layout.setSpacing(10)

        reset_btn = QPushButton("🔄 डिफल्टमा फर्काउनुहोस् (Reset)")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #7c6f64;
                color: #222222;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #f5f5f5; border-color: #333333; }
        """)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("रद्द गर्नुहोस् (Cancel)")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #7c6f64;
                color: #222222;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #f5f5f5; border-color: #333333; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 सुरक्षित गर्नुहोस् (Save)")
        save_btn.setDefault(True)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #a32412; }}
        """)
        save_btn.clicked.connect(self._save_values)
        btn_layout.addWidget(save_btn)

        root_layout.addLayout(btn_layout)

    def _load_values(self):
        siddhanta = self._settings.value("calculation_siddhanta", "DRIK")
        self._select_combo(self._siddhanta_combo, siddhanta)

        ayanamsha = self._settings.value("ayanamsha", "LAHIRI")
        self._select_combo(self._ayanamsha_combo, ayanamsha)

        house = self._settings.value("house_system", "WHOLE_SIGN")
        self._select_combo(self._house_combo, house)

        node = self._settings.value("node_type", "MEAN")
        self._select_combo(self._node_combo, node)

        language = self._settings.value("language", "ne")
        self._select_combo(self._language_combo, language)

        theme = self._settings.value("theme_mode", "classic")
        self._select_combo(self._theme_combo, theme)

    def _select_combo(self, combo: QComboBox, value):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)

    def _save_values(self):
        siddhanta = self._siddhanta_combo.currentData()
        ayanamsha = self._ayanamsha_combo.currentData()
        house = self._house_combo.currentData()
        node = self._node_combo.currentData()
        language = self._language_combo.currentData()

        self._settings.setValue("calculation_siddhanta", siddhanta)
        self._settings.setValue("ayanamsha", ayanamsha)
        self._settings.setValue("house_system", house)
        self._settings.setValue("node_type", node)
        self._settings.setValue("language", language)

        # Save theme
        theme = self._theme_combo.currentData()
        self._settings.setValue("theme_mode", theme)
        # Apply theme live
        try:
            from PySide6.QtWidgets import QApplication
            from gui.theme import apply_theme
            apply_theme(QApplication.instance(), theme)
        except Exception:
            pass

        QMessageBox.information(
            self,
            "सेटिङ सुरक्षित",
            "सेटिङहरू सफलतापूर्वक सुरक्षित गरियो। अब सम्पूर्ण नयाँ गणनाहरू यसै अनुसार हुनेछन्।"
        )
        self.accept()

    def _reset_defaults(self):
        self._select_combo(self._siddhanta_combo, "DRIK")
        self._select_combo(self._ayanamsha_combo, "LAHIRI")
        self._select_combo(self._house_combo, "WHOLE_SIGN")
        self._select_combo(self._node_combo, "MEAN")
        self._select_combo(self._language_combo, "ne")
        self._select_combo(self._theme_combo, "classic")

    def _load_reminder_preview(self):
        """Load upcoming reminder info into the preview label."""
        try:
            from PySide6.QtCore import QSettings
            import datetime
            s = QSettings("ShivramJyotish", "Desktop")
            enabled = s.value("reminders/enabled", True)
            if not enabled or str(enabled).lower() == "false":
                self._reminder_preview_lbl.setText("⛔ रिमाइन्डर अक्षम छ। सेटिङमा सक्रिय गर्नुहोस्।")
                return
            digest_time = s.value("reminders/digest_time", "08:00")
            now = datetime.datetime.now()
            try:
                h, m = map(int, str(digest_time).split(":")[:2])
                next_digest = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if next_digest <= now:
                    next_digest += datetime.timedelta(days=1)
                delta = next_digest - now
                hours_left = int(delta.total_seconds() // 3600)
                mins_left = int((delta.total_seconds() % 3600) // 60)
                time_str = f"{hours_left}घ: {mins_left}मि" if hours_left > 0 else f"{mins_left} मिनेट"
                flags = []
                if s.value("reminders/rahu_kaal", True):
                    flags.append("राहुकाल")
                if s.value("reminders/choghadiya", False):
                    flags.append("चोघड़िया")
                if s.value("reminders/festivals", True):
                    flags.append("पर्व")
                preview = (
                    f"✅ रिमाइन्डर सक्रिय छ — अर्को डाइजेस्ट: {next_digest.strftime('%Y-%m-%d %H:%M')}\n"
                    f"• समय बाँकी: {time_str}\n"
                    f"• सक्रिय अलर्ट: {', '.join(flags) if flags else 'कुनै छैन'}"
                )
                self._reminder_preview_lbl.setText(preview)
            except Exception:
                self._reminder_preview_lbl.setText("रिमाइन्डर सक्रिय छ।")
        except Exception as e:
            self._reminder_preview_lbl.setText(f"लोड गर्न सकिएन: {e}")


def show_settings_dialog(parent: Optional[QWidget] = None) -> bool:
    """Helper to show settings dialog and return True if accepted."""
    dlg = SettingsDialog(parent)
    return dlg.exec() == QDialog.Accepted
