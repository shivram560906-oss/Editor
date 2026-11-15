"""
gui/widgets/chart_input.py

Birth data entry form — full port of ChartInput.jsx.
Features:
 - Name, gender selector
 - Calendar mode: BS (Bikram Sambat) or AD (Gregorian)
 - BS → AD / AD → BS live conversion
 - Country → province/state → district → place selection
 - Lat/Lon/Timezone auto-fill from known place selection
 - Ayanamsha selector
 - Calculate button
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QButtonGroup, QScrollArea,
    QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QCompleter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

# ── path setup ──────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.backend_bridge import get_all_cities, convert_bs_to_ad, convert_ad_to_bs
from gui.widgets.north_indian_chart import NorthIndianChartWidget
from gui.theme import (COLOR_GOLD, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                       BG_SECONDARY, BG_TERTIARY, BORDER_COLOR, INPUT_BG,
                       COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_ERROR, BG_PRIMARY)
from gui.utils.bs_calendar import gregorian_to_bs
from gui.utils.location_data import (
    NEPAL_PROVINCE_NE, bilingual_district_label, countries,
    district_metadata, districts_for_region, enrich_cities, filtered_cities,
    regions_for_country,
)
from gui.widgets.smart_nepali_date_dropdown import SmartNepaliDateDropdown
from gui.utils.nepali_date_input import normalize_birth_time

def _sep() -> QFrame:
    """Return spacing only; the compact form does not need divider lines."""
    f = QFrame()
    f.setFixedHeight(2)
    f.setFrameShape(QFrame.NoFrame)
    return f

def _label(text: str, bold: bool = False, muted: bool = False) -> QLabel:
    lbl = QLabel(text)
    if muted:
        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
    elif bold:
        lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-weight: 700; font-size: 12px;")
    else:
        lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
    return lbl


class ChartInputWidget(QWidget):
    """
    Full birth data input form.
    Emits calculate_requested(params_dict) when Calculate is clicked.
    params_dict matches exactly what backend_bridge.calculate_chart() expects.
    """
    calculate_requested = Signal(dict)
    approve_requested = Signal(dict)
    reject_requested = Signal()

    def __init__(self, language: str = "ne", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._lang = language
        self._is_ne = language == "ne"
        self._calendar_mode = "BS"   # "BS" or "AD"
        self._cities = enrich_cities(get_all_cities())
        self._selected_city: Optional[dict] = None
        self._pending_preview_params: Optional[dict] = None
        self._preview_params: Optional[dict] = None

        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setStyleSheet("""
            QLineEdit, QSpinBox, QTextEdit, QComboBox {
                background: #ffffff;
                color: #111111;
                border: 1px solid #9ca3af;
                padding: 2px 5px;
                selection-background-color: #1d4ed8;
                selection-color: #ffffff;
            }
            QLineEdit:read-only {
                background: #ffffff;
                color: #111111;
            }
            QComboBox QAbstractItemView {
                background: #ffffff;
                color: #111111;
                selection-background-color: #1d4ed8;
                selection-color: #ffffff;
                border: 1px solid #4b5563;
                outline: 0;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        workspace = QHBoxLayout()
        workspace.setContentsMargins(0, 0, 0, 0)
        workspace.setSpacing(6)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.setMinimumWidth(350)
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: {BG_SECONDARY}; }}
            QTabBar::tab {{ padding: 6px 12px; color: {COLOR_TEXT_SECONDARY}; background: {BG_TERTIARY}; }}
            QTabBar::tab:selected {{ color: {COLOR_GOLD}; border-bottom: 2px solid {COLOR_GOLD}; }}
        """)
        workspace.addWidget(self._tabs, 3)

        preview_frame = QFrame()
        preview_frame.setFixedWidth(280)
        preview_frame.setStyleSheet(f"QFrame {{ background: {BG_PRIMARY}; border: none; }}")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(6, 6, 6, 6)
        preview_title = _label(
            "कुण्डली पूर्वावलोकन" if self._is_ne else "Kundali Preview",
            bold=True,
        )
        preview_title.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_title)
        self._preview_hint = _label(
            "विवरण भरेर पूर्वावलोकन गर्नुहोस्" if self._is_ne
            else "Complete the details and calculate a preview",
            muted=True,
        )
        self._preview_hint.setAlignment(Qt.AlignCenter)
        self._preview_hint.setWordWrap(True)
        preview_layout.addWidget(self._preview_hint)
        self._preview_chart = NorthIndianChartWidget(language=self._lang)
        self._preview_chart.setMinimumSize(250, 250)
        self._preview_chart.setMaximumSize(270, 270)
        preview_layout.addWidget(self._preview_chart, 1, Qt.AlignCenter)
        workspace.addWidget(preview_frame, 2)
        root.addLayout(workspace, 1)

        birth_tab = QWidget()
        self._tabs.addTab(birth_tab, "जन्म विवरण" if self._is_ne else "Birth Details")
        birth_root = QVBoxLayout(birth_tab)
        birth_root.setContentsMargins(0, 0, 0, 0)

        # Scroll area for the required birth details and calculation settings.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        birth_root.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet(f"background: transparent;")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(4)

        # ── Section: Personal Info ──
        layout.addWidget(self._section_title("👤 " + ("व्यक्तिगत विवरण" if self._is_ne else "Personal Info")))

        self._name_edit = self._input_field("", "John Doe / राम बहादुर")
        self._name_edit.setFixedWidth(220)
        self._btn_male = self._gender_btn("पुरुष" if self._is_ne else "Male")
        self._btn_female = self._gender_btn("महिला" if self._is_ne else "Female")
        self._gender_group = QButtonGroup(self)
        self._gender_group.setExclusive(True)
        for btn in (self._btn_male, self._btn_female):
            self._gender_group.addButton(btn)

        name_gender_row = QHBoxLayout()
        name_gender_row.setSpacing(5)
        name_label = _label("नाम:" if self._is_ne else "Name:", muted=True)
        name_label.setFixedWidth(82)
        name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        name_gender_row.addWidget(name_label)
        name_gender_row.addWidget(self._name_edit)
        name_gender_row.addWidget(self._btn_male)
        name_gender_row.addWidget(self._btn_female)
        name_gender_row.addStretch(1)
        layout.addLayout(name_gender_row)
        self._gender_group.buttonClicked.connect(self._on_gender_changed)

        layout.addWidget(_sep())

        # ── Section: Birth Date ──
        layout.addWidget(self._section_title("📅 " + ("जन्म मिति" if self._is_ne else "Birth Date")))

        # Calendar mode toggle
        cal_layout = QHBoxLayout()
        cal_layout.setSpacing(6)
        self._btn_bs = self._toggle_btn("BS (वि.सं.)")
        self._btn_ad = self._toggle_btn("AD (ई.सं.)")
        self._cal_group = QButtonGroup(self)
        self._cal_group.setExclusive(True)
        for btn in [self._btn_bs, self._btn_ad]:
            self._cal_group.addButton(btn)
            cal_layout.addWidget(btn)
        cal_layout.addStretch()
        self._btn_bs.setStyleSheet(self._active_toggle_style())
        self._cal_group.buttonClicked.connect(self._on_calendar_mode_changed)
        cal_widget = QWidget()
        cal_widget.setLayout(cal_layout)
        cal_widget.setStyleSheet("background: transparent;")
        layout.addWidget(cal_widget)

        # BS date row (year / month / day)
        self._bs_year = SmartNepaliDateDropdown("year", 1970, 2099)
        self._bs_month = SmartNepaliDateDropdown("month", 1, 12)
        self._bs_day = SmartNepaliDateDropdown("day", 1, 32)
        for control, width in (
            (self._bs_year, 100),
            (self._bs_month, 120),
            (self._bs_day, 72),
        ):
            control.setFixedHeight(26)
            control.setMaximumWidth(width)

        bs_row_layout = QHBoxLayout()
        bs_row_layout.setSpacing(6)
        bs_row_layout.addWidget(_label("वर्ष:" if self._is_ne else "Year:", muted=True))
        bs_row_layout.addWidget(self._bs_year, 2)
        bs_row_layout.addWidget(_label("महिना:" if self._is_ne else "Month:", muted=True))
        bs_row_layout.addWidget(self._bs_month, 3)
        bs_row_layout.addWidget(_label("दिन:" if self._is_ne else "Day:", muted=True))
        bs_row_layout.addWidget(self._bs_day, 2)
        self._bs_row_widget = QWidget()
        self._bs_row_widget.setLayout(bs_row_layout)
        self._bs_row_widget.setStyleSheet("background: transparent;")
        layout.addWidget(self._bs_row_widget)

        # AD date row
        self._ad_date_edit = self._input_field("", "YYYY-MM-DD")
        self._ad_date_edit.setPlaceholderText("YYYY-MM-DD")
        self._ad_row_widget = QWidget()
        ad_row_layout = QHBoxLayout()
        ad_row_layout.setContentsMargins(0,0,0,0)
        ad_row_layout.addWidget(_label("AD मिति:" if self._is_ne else "AD Date:", muted=True))
        ad_row_layout.addWidget(self._ad_date_edit)
        self._ad_row_widget.setLayout(ad_row_layout)
        self._ad_row_widget.setStyleSheet("background: transparent;")
        layout.addWidget(self._ad_row_widget)
        self._ad_row_widget.hide()

        # Sync BS↔AD
        self._bs_year.valueChanged.connect(self._sync_bs_to_ad)
        self._bs_month.valueChanged.connect(self._sync_bs_to_ad)
        self._bs_day.valueChanged.connect(self._sync_bs_to_ad)
        for control in (self._bs_year, self._bs_month, self._bs_day):
            control.lineEdit().textEdited.connect(self._clear_ad_verification)
        self._ad_date_edit.textChanged.connect(self._sync_ad_to_bs)

        # Birth time and automatic AD verification for the selected BS date.
        self._time_edit = self._input_field("", "HH:MM")
        self._time_edit.setPlaceholderText("HH:MM")
        self._time_edit.setMaximumWidth(120)
        self._time_edit.returnPressed.connect(self._normalize_time_field)
        self._time_edit.editingFinished.connect(self._normalize_time_field)
        self._ad_verification_label = QLabel("")
        self._ad_verification_label.setStyleSheet(
            "color: #111111; font-size: 12px; background: transparent;"
        )
        self._ad_verification_label.setMinimumWidth(130)
        self._ad_verification_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        time_row = QHBoxLayout()
        time_row.setSpacing(5)
        time_label = _label("जन्म समय:" if self._is_ne else "Birth Time:", muted=True)
        time_label.setFixedWidth(82)
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_row.addWidget(time_label)
        time_row.addWidget(self._time_edit)
        time_row.addWidget(self._ad_verification_label)
        time_row.addStretch(1)
        layout.addLayout(time_row)

        layout.addWidget(_sep())

        # ── Section: Location ──
        layout.addWidget(self._section_title("📍 " + ("जन्म स्थान" if self._is_ne else "Birth Location")))

        self._country_combo = QComboBox()
        self._region_combo = QComboBox()
        self._district_combo = QComboBox()
        self._city_combo = QComboBox()
        for combo in (
            self._country_combo, self._region_combo,
            self._district_combo, self._city_combo,
        ):
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.setFixedHeight(26)
            combo.setMaximumWidth(300)
            combo.setMaxVisibleItems(14)
            combo.setStyleSheet("""
                QComboBox { background: #ffffff; color: #111111;
                    border: 1px solid #9ca3af; padding: 2px 5px; }
                QComboBox QAbstractItemView { background: #ffffff; color: #111111;
                    selection-background-color: #1d4ed8; selection-color: #ffffff;
                    border: 1px solid #4b5563; outline: 0; }
            """)
            completer = combo.completer()
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)
        self._city_combo.setInsertPolicy(QComboBox.NoInsert)
        self._city_combo.lineEdit().setPlaceholderText(
            "सहर वा स्थानको नाम" if self._is_ne else "City or place name"
        )
        layout.addLayout(self._form_row(
            "देश:" if self._is_ne else "Country:", self._country_combo,
        ))
        layout.addLayout(self._form_row(
            "प्रदेश/राज्य:" if self._is_ne else "Province/State:", self._region_combo,
        ))
        layout.addLayout(self._form_row(
            "जिल्ला:" if self._is_ne else "District:", self._district_combo,
        ))
        layout.addLayout(self._form_row(
            "सहर/स्थान:" if self._is_ne else "City/Place:", self._city_combo,
        ))

        self._custom_location = QCheckBox(
            "सूची बाहिरको स्थान (अक्षांश/देशान्तर सम्पादन)" if self._is_ne
            else "Unlisted location (edit coordinates)"
        )
        self._custom_location.toggled.connect(self._on_custom_location_toggled)
        layout.addWidget(self._custom_location)

        # Lat / Lon / TZ
        coords_layout = QHBoxLayout()
        coords_layout.setSpacing(5)
        self._lat_edit = self._input_field("27.5833", "Latitude")
        self._lon_edit = self._input_field("83.05", "Longitude")
        self._tz_edit = self._input_field("5.75", "Timezone")
        for edit in (self._lat_edit, self._lon_edit, self._tz_edit):
            edit.setMaximumWidth(96)
        self._set_coordinate_editable(False)
        for lbl, w in [("अक्षांश:" if self._is_ne else "Lat:", self._lat_edit),
                        ("देशान्तर:" if self._is_ne else "Lon:", self._lon_edit),
                        ("समयक्षेत्र:" if self._is_ne else "TZ:", self._tz_edit)]:
            col = QVBoxLayout()
            col.setSpacing(3)
            col.addWidget(_label(lbl, muted=True))
            col.addWidget(w)
            coords_layout.addLayout(col, 1)
        layout.addLayout(coords_layout)

        self._country_combo.currentIndexChanged.connect(self._on_country_changed)
        self._region_combo.currentIndexChanged.connect(self._on_region_changed)
        self._district_combo.currentIndexChanged.connect(self._on_district_changed)
        self._city_combo.currentIndexChanged.connect(self._on_place_changed)
        self._city_combo.currentTextChanged.connect(self._on_place_text_changed)
        self._populate_countries()

        layout.addWidget(_sep())

        # Optional Janmapatrika controls are constructed here and placed on the Family tab below.
        self._janmapatrika_edits = {}
        detail_fields = [
            ("full_name", "राशीको नाम:" if self._is_ne else "Rashi Name:", "Rashi name / राशीको नाम"),
            ("father_name", "बाबुको नाम:" if self._is_ne else "Father's name:", "Father name / बाबुको नाम"),
            ("mother_name", "आमाको नाम:" if self._is_ne else "Mother's name:", "Mother name / आमाको नाम"),
            ("gotra", "गोत्र:" if self._is_ne else "Gotra:", "Gotra"),
            ("surname", "थर:" if self._is_ne else "Surname:", "Surname"),
            ("kula", "कुल:" if self._is_ne else "Kula:", "Kula"),
            ("kuladevata", "कुलदेवता:" if self._is_ne else "Family deity:", "Kuladevata"),
            ("spouse_name", "पति/पत्नी:" if self._is_ne else "Spouse:", "Spouse name"),
            ("caste", "जात:" if self._is_ne else "Caste:", "Caste"),
            ("religion", "धर्म:" if self._is_ne else "Religion:", "Religion"),
        ]
        self._family_rows = []
        for key, label, placeholder in detail_fields:
            edit = self._input_field("", placeholder)
            self._janmapatrika_edits[key] = edit
            self._family_rows.append((label, edit))
        self._marital_status = QComboBox()
        self._marital_status.setFixedHeight(26)
        self._marital_status.setMaximumWidth(300)
        self._marital_status.addItem("छान्नुहोस्" if self._is_ne else "Select", None)
        for value in ["अविवाहित", "विवाहित", "विधवा/विधुर", "सम्बन्धविच्छेद", "अन्य"]:
            self._marital_status.addItem(value, value)
        self._family_details = QLineEdit()
        self._family_details.setPlaceholderText("Family details / परिवारको विवरण")
        self._family_details.setFixedHeight(26)
        self._family_details.setMaximumWidth(300)
        layout.addWidget(_sep())

        layout.addStretch()

        events_tab = QWidget()
        events_layout = QVBoxLayout(events_tab)
        events_layout.setContentsMargins(16, 16, 16, 16)
        events_layout.addWidget(_label("जीवनका महत्वपूर्ण घटनाहरू (वैकल्पिक)" if self._is_ne else "Important life events (optional)", bold=True))
        self._events_table = QTableWidget(3, 2)
        self._events_table.setHorizontalHeaderLabels(["मिति", "घटना"] if self._is_ne else ["Date", "Event"])
        self._events_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._events_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        events_layout.addWidget(self._events_table)
        add_event_btn = QPushButton("+ घटना थप्नुहोस्" if self._is_ne else "+ Add event")
        add_event_btn.clicked.connect(lambda: self._events_table.insertRow(self._events_table.rowCount()))
        events_layout.addWidget(add_event_btn, 0, Qt.AlignLeft)
        self._tabs.addTab(events_tab, "घटनाहरू" if self._is_ne else "Events")

        family_tab = QScrollArea()
        family_tab.setWidgetResizable(True)
        family_body = QWidget()
        family_layout = QVBoxLayout(family_body)
        family_layout.setContentsMargins(16, 16, 16, 16)
        family_layout.addWidget(_label("यी सबै विवरण वैकल्पिक हुन्।" if self._is_ne else "All of these details are optional.", muted=True))
        for label, edit in self._family_rows:
            family_layout.addLayout(self._form_row(label, edit))
        family_layout.addLayout(self._form_row("वैवाहिक अवस्था:" if self._is_ne else "Marital status:", self._marital_status))
        family_layout.addLayout(self._form_row("परिवार:" if self._is_ne else "Family:", self._family_details))
        family_layout.addStretch()
        family_tab.setWidget(family_body)
        self._tabs.addTab(family_tab, "परिवार" if self._is_ne else "Family")

        comments_tab = QWidget()
        comments_layout = QVBoxLayout(comments_tab)
        comments_layout.setContentsMargins(16, 16, 16, 16)
        comments_layout.addWidget(_label("टिप्पणी (वैकल्पिक)" if self._is_ne else "Comments (optional)", bold=True))
        self._comments_edit = QTextEdit()
        self._comments_edit.setMaximumWidth(420)
        self._comments_edit.setPlaceholderText("थप टिप्पणी लेख्नुहोस्..." if self._is_ne else "Add notes...")
        comments_layout.addWidget(self._comments_edit)
        self._tabs.addTab(comments_tab, "टिप्पणी" if self._is_ne else "Comments")

        actions_host = QWidget()
        actions_host.setFixedHeight(42)
        actions = QHBoxLayout(actions_host)
        actions.setContentsMargins(8, 4, 8, 4)
        actions.setSpacing(6)
        self._calc_btn = QPushButton("कुण्डली पूर्वावलोकन" if self._is_ne else "Preview Kundali")
        self._calc_btn.setObjectName("PrimaryBtn")
        self._calc_btn.setFixedHeight(32)
        self._calc_btn.clicked.connect(self._on_calculate)
        actions.addWidget(self._calc_btn)

        self._guide_btn = QPushButton("📖 " + ("गाइड" if self._is_ne else "Guide"))
        self._guide_btn.setFixedHeight(32)
        self._guide_btn.setToolTip("कुण्डली इन्पुट निर्देशिका तथा नियमहरू (F1)" if self._is_ne else "User Guide & Kundali Guidelines (F1)")
        self._guide_btn.setStyleSheet("""
            QPushButton {
                background: rgba(212, 175, 55, 0.18);
                border: 1px solid #d4af37;
                border-radius: 6px;
                color: #d4af37;
                font-weight: 700;
                font-size: 12px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background: rgba(212, 175, 55, 0.32);
            }
        """)
        self._guide_btn.clicked.connect(self._open_user_guide)
        actions.addWidget(self._guide_btn)

        self._approve_btn = QPushButton("✓ " + ("स्वीकृत" if self._is_ne else "Approve"))
        self._approve_btn.setFixedHeight(32)
        self._approve_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(22, 163, 74, 0.2);
                border: 1px solid #16a34a;
                border-radius: 6px;
                color: #16a34a;
                font-weight: 800;
                font-size: 12px;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background: rgba(22, 163, 74, 0.35);
            }}
        """)
        self._approve_btn.clicked.connect(self._on_approve)
        actions.addWidget(self._approve_btn)
        self._reject_btn = QPushButton("✕ " + ("अस्वीकृत" if self._is_ne else "Reject"))
        self._reject_btn.setFixedHeight(32)
        self._reject_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(220, 38, 38, 0.15);
                border: 1px solid #dc2626;
                border-radius: 6px;
                color: #dc2626;
                font-weight: 700;
                font-size: 12px;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background: rgba(220, 38, 38, 0.3);
            }}
        """)
        self._reject_btn.clicked.connect(self.reject_requested.emit)
        actions.addWidget(self._reject_btn)
        root.addWidget(actions_host)

        self._error_label = QLabel("")
        self._error_label.setFixedHeight(20)
        self._error_label.setStyleSheet(f"color: {COLOR_ERROR}; font-size: 11px; padding: 0 8px;")
        self._error_label.setWordWrap(False)
        root.addWidget(self._error_label)

        # Initialize BS date to today
        import datetime
        from gui.utils.bs_calendar import gregorian_to_bs
        today = datetime.date.today()
        bs = gregorian_to_bs(today.year, today.month, today.day)
        if bs:
            self._bs_year.setValue(bs["year"])
            self._bs_month.setValue(bs["month"])
            self._bs_day.setValue(bs["day"])

        self._sync_bs_to_ad()
        self._connect_preview_invalidation()

    # ── Helper widget factories ──────────────────────────────────────────────

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {COLOR_GOLD};
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
            padding: 4px 0;
        """)
        return lbl

    @staticmethod
    def _white_field_style() -> str:
        return """
            QLineEdit, QSpinBox, QComboBox {
                background-color: #ffffff;
                color: #111111;
                border: 1px solid #9ca3af;
                padding: 2px 5px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #ffffff;
                border-left: 1px solid #9ca3af;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #111111;
                selection-background-color: #1d4ed8;
                selection-color: #ffffff;
            }
        """

    def _input_field(self, default: str = "", placeholder: str = "") -> QLineEdit:
        e = QLineEdit(default)
        e.setPlaceholderText(placeholder)
        e.setFixedHeight(26)
        e.setMaximumWidth(300)
        e.setStyleSheet(self._white_field_style())
        return e

    def _spinbox(self, default: int, minimum: int, maximum: int):
        from PySide6.QtWidgets import QSpinBox
        s = QSpinBox()
        s.setMinimum(minimum)
        s.setMaximum(maximum)
        s.setValue(default)
        s.setFixedHeight(26)
        s.setMaximumWidth(100)
        s.setStyleSheet(self._white_field_style())
        return s

    def _gender_btn(self, text: str) -> QPushButton:
        btn = self._toggle_btn(text)
        btn.setObjectName("GenderBtn")
        btn.setStyleSheet(btn.styleSheet() + "QPushButton#GenderBtn { padding: 0px 4px; min-height: 20px; max-height: 26px; }")
        btn.setFixedSize(68, 26)
        return btn

    def _toggle_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_TERTIARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                color: {COLOR_TEXT_SECONDARY};
                font-size: 12px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                border-color: {COLOR_ACCENT};
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background: rgba(140,122,230,0.25);
                border-color: {COLOR_ACCENT};
                color: {COLOR_TEXT_PRIMARY};
                font-weight: 700;
            }}
        """)
        return btn

    def _active_toggle_style(self) -> str:
        return f"""
            QPushButton {{
                background: rgba(140,122,230,0.3);
                border: 1px solid {COLOR_ACCENT};
                border-radius: 6px;
                color: {COLOR_TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 700;
                padding: 4px 12px;
            }}
        """

    def _form_row(self, label_text: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(5)
        lbl = _label(label_text, muted=True)
        lbl.setFixedWidth(82)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)
        row.addWidget(widget, 0)
        row.addStretch(1)
        return row

    def _connect_preview_invalidation(self) -> None:
        for edit in [
            self._name_edit, self._ad_date_edit, self._time_edit,
            self._lat_edit, self._lon_edit, self._tz_edit,
            self._family_details, *self._janmapatrika_edits.values(),
        ]:
            edit.textChanged.connect(self.invalidate_preview)
        self._city_combo.currentTextChanged.connect(self.invalidate_preview)
        self._comments_edit.textChanged.connect(self.invalidate_preview)
        self._events_table.itemChanged.connect(self.invalidate_preview)
        self._events_table.model().rowsInserted.connect(self.invalidate_preview)
        for combo in [self._country_combo, self._region_combo, self._district_combo,
                      self._marital_status]:
            combo.currentIndexChanged.connect(self.invalidate_preview)
        self._gender_group.buttonClicked.connect(self.invalidate_preview)
        self._cal_group.buttonClicked.connect(self.invalidate_preview)
        self._bs_year.valueChanged.connect(self.invalidate_preview)
        self._bs_month.valueChanged.connect(self.invalidate_preview)
        self._bs_day.valueChanged.connect(self.invalidate_preview)

    # ── Logic: Calendar mode ─────────────────────────────────────────────────

    def _on_calendar_mode_changed(self, btn: QPushButton) -> None:
        if btn is self._btn_bs:
            self._calendar_mode = "BS"
            self._bs_row_widget.show()
            self._ad_row_widget.hide()
            self._sync_bs_to_ad()
        else:
            self._calendar_mode = "AD"
            self._bs_row_widget.hide()
            self._ad_row_widget.show()
            self._clear_ad_verification()

    def _clear_ad_verification(self, *args) -> None:
        self._ad_verification_label.clear()

    def _sync_bs_to_ad(self) -> None:
        if self._calendar_mode != "BS":
            self._clear_ad_verification()
            return
        if not all(control.isValid() for control in (
            self._bs_year, self._bs_month, self._bs_day,
        )):
            self._clear_ad_verification()
            return
        y = self._bs_year.value()
        m = self._bs_month.value()
        d = self._bs_day.value()
        result = convert_bs_to_ad(y, m, d)
        if not result:
            self._clear_ad_verification()
            return
        ad_date = f"{result['year']:04d}-{result['month']:02d}-{result['day']:02d}"
        self._ad_date_edit.blockSignals(True)
        self._ad_date_edit.setText(ad_date)
        self._ad_date_edit.blockSignals(False)
        prefix = "AD मिति" if self._is_ne else "AD Date"
        self._ad_verification_label.setText(f"{prefix}: {ad_date}")

    def _sync_ad_to_bs(self) -> None:
        if self._calendar_mode != "AD":
            return
        text = self._ad_date_edit.text().strip()
        try:
            parts = text.split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                result = convert_ad_to_bs(y, m, d)
                if result:
                    self._bs_year.blockSignals(True)
                    self._bs_month.blockSignals(True)
                    self._bs_day.blockSignals(True)
                    self._bs_year.setValue(result["year"])
                    self._bs_month.setValue(result["month"])
                    self._bs_day.setValue(result["day"])
                    self._bs_year.blockSignals(False)
                    self._bs_month.blockSignals(False)
                    self._bs_day.blockSignals(False)
        except (ValueError, IndexError):
            pass

    # ── Logic: Cascading location selection ─────────────────────────────────

    @staticmethod
    def _combo_value(combo: QComboBox) -> Optional[str]:
        data = combo.currentData()
        if isinstance(data, str) and data.strip():
            return data.strip()
        if combo.currentIndex() <= 0:
            return None
        text = combo.currentText().strip()
        return text or None

    def _set_coordinate_editable(self, editable: bool) -> None:
        for edit in (self._lat_edit, self._lon_edit, self._tz_edit):
            edit.setReadOnly(not editable)
            edit.setStyleSheet("background: #ffffff; color: #111111;")

    def _on_custom_location_toggled(self, checked: bool) -> None:
        self._set_coordinate_editable(checked)
        if checked:
            self._selected_city = None

    def _apply_known_location(self, location: Optional[dict]) -> None:
        if not location:
            return
        self._selected_city = dict(location)
        self._lat_edit.setText(str(location.get("lat", "")))
        self._lon_edit.setText(str(location.get("lon", "")))
        self._tz_edit.setText(str(location.get("tz", "")))
        self._custom_location.setChecked(False)
        self._set_coordinate_editable(False)

    def _populate_countries(self) -> None:
        self._country_combo.blockSignals(True)
        self._country_combo.clear()
        self._country_combo.addItem(
            "देश छान्नुहोस्" if self._is_ne else "Select country", None,
        )
        for country in countries(self._cities):
            label = "Nepal / नेपाल" if country == "Nepal" else country
            self._country_combo.addItem(label, country)
        self._country_combo.blockSignals(False)
        nepal_index = self._country_combo.findData("Nepal")
        self._country_combo.setCurrentIndex(max(nepal_index, 0))
        self._on_country_changed()
        lumbini_index = self._region_combo.findData("Lumbini")
        self._region_combo.setCurrentIndex(max(lumbini_index, 0))
        self._on_region_changed()
        kapilvastu_index = self._district_combo.findData("Kapilvastu")
        self._district_combo.setCurrentIndex(max(kapilvastu_index, 0))
        self._on_district_changed()

    def _reset_combo(self, combo: QComboBox, prompt: str, enabled: bool = True) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(prompt, None)
        combo.setCurrentIndex(0)
        combo.setEnabled(enabled)
        combo.blockSignals(False)

    def _on_country_changed(self, *args) -> None:
        country = self._combo_value(self._country_combo)
        self._selected_city = None
        self._clear_coordinates()
        regions = regions_for_country(country, self._cities) if country else []
        self._reset_combo(
            self._region_combo,
            "प्रदेश/राज्य छान्नुहोस्" if self._is_ne else "Select province/state",
            bool(regions),
        )
        self._region_combo.blockSignals(True)
        for region in regions:
            translated = NEPAL_PROVINCE_NE.get(region)
            label = f"{region} / {translated}" if translated else region
            self._region_combo.addItem(label, region)
        self._region_combo.blockSignals(False)
        self._reset_combo(
            self._district_combo,
            "जिल्ला उपलब्ध छैन" if self._is_ne else "District unavailable",
            False,
        )
        self._populate_places()

    def _on_region_changed(self, *args) -> None:
        country = self._combo_value(self._country_combo)
        region = self._combo_value(self._region_combo)
        self._selected_city = None
        self._clear_coordinates()
        districts = districts_for_region(country, region, self._cities)
        self._reset_combo(
            self._district_combo,
            ("जिल्ला छान्नुहोस्" if districts else "जिल्ला उपलब्ध छैन")
            if self._is_ne else
            ("Select district" if districts else "District unavailable"),
            bool(districts),
        )
        self._district_combo.blockSignals(True)
        for district in districts:
            label = bilingual_district_label(district) if country == "Nepal" else district
            self._district_combo.addItem(label, district)
        self._district_combo.blockSignals(False)
        self._populate_places()

    def _on_district_changed(self, *args) -> None:
        self._selected_city = None
        self._clear_coordinates()
        self._populate_places()
        country = self._combo_value(self._country_combo)
        district = self._combo_value(self._district_combo)
        metadata = district_metadata(country, district)
        if metadata:
            self._apply_known_location(metadata)
            self._city_combo.setEditText(district or "")

    def _populate_places(self) -> None:
        country = self._combo_value(self._country_combo)
        region = self._combo_value(self._region_combo)
        district = self._combo_value(self._district_combo)
        requires_region = self._region_combo.isEnabled()
        requires_district = country == "Nepal"
        ready = bool(country) and (not requires_region or bool(region)) \
            and (not requires_district or bool(district))
        places = filtered_cities(self._cities, country, region, district) if ready else []

        self._city_combo.blockSignals(True)
        self._city_combo.clear()
        self._city_combo.addItem(
            "सहर/स्थान छान्नुहोस् वा लेख्नुहोस्" if self._is_ne
            else "Select or type a city/place",
            None,
        )
        for city in places:
            self._city_combo.addItem(city.get("name", ""), city)
        self._city_combo.setCurrentIndex(0)
        if self._city_combo.lineEdit() is not None:
            self._city_combo.lineEdit().clear()
        self._city_combo.setEnabled(ready)
        self._city_combo.blockSignals(False)

    def _clear_coordinates(self) -> None:
        if not hasattr(self, "_lat_edit"):
            return
        for edit in (self._lat_edit, self._lon_edit, self._tz_edit):
            edit.clear()

    def _on_place_changed(self, *args) -> None:
        city = self._city_combo.currentData()
        if not isinstance(city, dict):
            return
        self._apply_known_location(city)

    def _on_place_text_changed(self, text: str) -> None:
        city = self._city_combo.currentData()
        if not isinstance(city, dict) or text.strip() != city.get("name"):
            self._selected_city = None

    # ── Logic: Gender ────────────────────────────────────────────────────────

    def _on_gender_changed(self, btn: QPushButton) -> None:
        for button in (self._btn_male, self._btn_female):
            button.setChecked(button is btn)

    def _get_gender(self) -> int:
        return 1 if self._btn_female.isChecked() else 0

    # ── Logic: Validate & Calculate ─────────────────────────────────────────

    def _on_calculate(self) -> None:
        self._error_label.setText("")
        params = self._collect_params()
        if params is None:
            return
        self.invalidate_preview()
        self._pending_preview_params = params
        self.calculate_requested.emit(params)

    def _on_approve(self) -> None:
        self._error_label.setText("")
        params = self._collect_params()
        if params is None:
            return
        self.approve_requested.emit(dict(params))

    def _collect_params(self) -> Optional[dict]:
        """Collect & validate all form fields. Returns param dict or None."""
        name = self._name_edit.text().strip()
        if not name:
            self._show_error("नाम भर्नुहोस्!" if self._is_ne else "Please enter a name.")
            return None

        if self._gender_group.checkedButton() is None:
            self._show_error("लिङ्ग छान्नुहोस्!" if self._is_ne else "Please select gender.")
            return None

        # AD birth_date
        ad_text = self._ad_date_edit.text().strip()
        if not ad_text:
            self._show_error("जन्म मिति भर्नुहोस्!" if self._is_ne else "Please enter birth date.")
            return None
        try:
            import datetime
            parts = ad_text.split("-")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            datetime.date(y, m, d)  # validate
            birth_date = f"{y:04d}-{m:02d}-{d:02d}"
        except Exception:
            self._show_error("मिति ढाँचा YYYY-MM-DD हुनुपर्छ।" if self._is_ne else "Date must be YYYY-MM-DD.")
            return None

        # Birth time
        time_text = self._time_edit.text().strip()
        birth_time = normalize_birth_time(time_text)
        if birth_time is None:
            self._show_error(
                "समय घण्टा:मिनेट वा घण्टा:मिनेट:सेकेन्ड ढाँचामा हुनुपर्छ।"
                if self._is_ne else
                "Time must contain hour and minute, with optional seconds."
            )
            return None
        self._set_canonical_time_text(birth_time)

        city = self._city_combo.currentText().strip() or None
        selected_country = self._combo_value(self._country_combo)
        selected_district = self._combo_value(self._district_combo)
        selected_region = self._combo_value(self._region_combo)

        # यदि सहर/स्थान खालि भएमा वा पूर्वनिर्धारित प्रम्प्ट भएमा जिल्ला अनुसारको स्थान र अक्षांश/देशान्तर प्रयोग गर्ने
        if not city or city in ("सहर/स्थान छान्नुहोस् वा लेख्नुहोस्", "Select or type a city/place", "—"):
            if selected_country == "Nepal" and selected_district:
                meta = district_metadata(selected_country, selected_district)
                city = (meta.get("name_ne") or selected_district) if meta else selected_district
                if meta:
                    try:
                        if not self._lat_edit.text().strip():
                            self._lat_edit.setText(str(meta.get("lat", "")))
                        if not self._lon_edit.text().strip():
                            self._lon_edit.setText(str(meta.get("lon", "")))
                        if not self._tz_edit.text().strip():
                            self._tz_edit.setText(str(meta.get("tz", 5.75)))
                    except Exception:
                        pass
            elif selected_country:
                city = selected_district or selected_region or selected_country
            else:
                self._show_error("जन्म स्थान वा जिल्ला छान्नुहोस्!" if self._is_ne else "Please enter birth place or select district.")
                return None

        if not selected_country:
            self._show_error("देश छान्नुहोस्!" if self._is_ne else "Please select a country.")
            return None

        # Lat / Lon / TZ
        try:
            lat = float(self._lat_edit.text())
            lon = float(self._lon_edit.text())
            tz  = float(self._tz_edit.text())
        except ValueError:
            self._show_error("अक्षांश/देशान्तर/समयक्षेत्र नम्बर हुनुपर्छ।" if self._is_ne
                             else "Lat/Lon/Timezone must be numbers.")
            return None

        if not (-90 <= lat <= 90):
            self._show_error("अक्षांश -90 देखि 90 बीच हुनुपर्छ।" if self._is_ne else "Latitude must be -90 to 90.")
            return None
        if not (-180 <= lon <= 180):
            self._show_error("देशान्तर -180 देखि 180 बीच हुनुपर्छ।" if self._is_ne else "Longitude must be -180 to 180.")
            return None
        life_events = []
        for row in range(self._events_table.rowCount()):
            date_item = self._events_table.item(row, 0)
            event_item = self._events_table.item(row, 1)
            event_text = event_item.text().strip() if event_item else ""
            if event_text:
                life_events.append({
                    "date": date_item.text().strip() if date_item else "",
                    "event": event_text,
                })

        return {
            "name":                  name,
            "birth_date":            birth_date,
            "birth_time":            birth_time,
            "latitude":              lat,
            "longitude":             lon,
            "timezone":              tz,
            "calculation_siddhanta": self._jyotish_settings("calculation_siddhanta", "DRIK"),
            "ayanamsha_type":        self._jyotish_settings("ayanamsha", "LAHIRI"),
            "node_type":             self._jyotish_settings("node_type", "MEAN"),
            "house_system":          self._jyotish_settings("house_system", "WHOLE_SIGN"),
            "city":                  city,
            "birth_place":           city,
            "country":               selected_country,
            "region":                self._combo_value(self._region_combo),
            "province":              self._combo_value(self._region_combo),
            "district":              self._combo_value(self._district_combo),
            "timezone_id":           (self._selected_city or {}).get("timezone_id"),
            "gender":                self._get_gender(),
            **{key: edit.text().strip() or None for key, edit in self._janmapatrika_edits.items()},
            "marital_status":        self._marital_status.currentData() or None,
            "family_details":        self._family_details.text().strip() or None,
            "life_events":           life_events,
            "comments":              self._comments_edit.toPlainText().strip() or None,
        }

    def _show_error(self, msg: str) -> None:
        self._error_label.setText("⚠ " + msg)

    def _set_canonical_time_text(self, value: str) -> None:
        """Display time compactly while retaining seconds for submitted params."""
        display = value[:5] if value.endswith(":00") else value
        self._time_edit.blockSignals(True)
        self._time_edit.setText(display)
        self._time_edit.blockSignals(False)

    def _normalize_time_field(self) -> bool:
        value = normalize_birth_time(self._time_edit.text())
        if value is None:
            return False
        self._set_canonical_time_text(value)
        return True

    # ── Public API ───────────────────────────────────────────────────────────

    def set_language(self, language: str) -> None:
        self._lang = language
        self._is_ne = language == "ne"

    @staticmethod
    def _jyotish_settings(key: str, default: str) -> str:
        """Read a Jyotish calculation preference from persistent QSettings."""
        from PySide6.QtCore import QSettings
        settings = QSettings("ShivramJyotish", "Desktop")
        value = settings.value(key, default)
        return str(value) if value else default

    def reload_settings(self) -> None:
        """Reload saved preferences from persistent QSettings.

        Jyotish calculation preferences (siddhanta/ayanamsha/node/house) are
        configured centrally in the Settings dialog; this widget reads them live
        via QSettings on every collect, so there is nothing to rebuild here.
        """
        self.invalidate_preview()

    def collect_params(self) -> Optional[dict]:
        return self._collect_params()

    def invalidate_preview(self, *args) -> None:
        self._pending_preview_params = None
        self._preview_params = None
        self._approve_btn.setEnabled(True)
        self._preview_hint.setText(
            "विवरण भरेर कुण्डली स्वीकृत वा पूर्वावलोकन गर्नुहोस्" if self._is_ne
            else "Complete details and approve or preview Kundali"
        )

    def set_preview_data(self, data: dict) -> None:
        self._preview_chart.set_data(data, "D1")
        if self._pending_preview_params is not None:
            self._preview_params = dict(self._pending_preview_params)
            self._pending_preview_params = None
        self._approve_btn.setEnabled(True)
        self._preview_hint.setText(
            "कुण्डली तयार छ। जाँच गरेर स्वीकृत वा अस्वीकृत गर्नुहोस्।"
            if self._is_ne else
            "Preview ready. Review it before approving or rejecting."
        )

    def set_preview_ready(self, ready: bool) -> None:
        self._approve_btn.setEnabled(ready and self._preview_params is not None)

    def set_loading(self, loading: bool) -> None:
        self._calc_btn.setEnabled(not loading)
        self._tabs.setEnabled(not loading)
        self._calc_btn.setText(
            ("गणना हुँदैछ..." if loading else "कुण्डली पूर्वावलोकन")
            if self._is_ne else
            ("Calculating..." if loading else "Preview Kundali")
        )

    def load_params(self, params: dict) -> None:
        """
        Pre-populate all form fields from a saved params dict.
        Called when user opens a saved chart.
        """
        import datetime

        self.invalidate_preview()
        self._selected_city = None

        # Name
        name = params.get("name", "")
        self._name_edit.setText(name)

        # Gender
        gender = params.get("gender")
        if gender not in (0, 1):
            self._gender_group.setExclusive(False)
            for button in (self._btn_male, self._btn_female):
                button.setChecked(False)
            self._gender_group.setExclusive(True)
        elif gender == 1:
            self._btn_female.setChecked(True)
            self._on_gender_changed(self._btn_female)
        else:
            self._btn_male.setChecked(True)
            self._on_gender_changed(self._btn_male)

        # Birth date — use AD mode (simplest)
        birth_date = params.get("birth_date", "")
        if birth_date:
            self._btn_ad.setChecked(True)
            self._on_calendar_mode_changed(self._btn_ad)
            self._ad_date_edit.setText(birth_date)
            try:
                d = datetime.date.fromisoformat(birth_date)
                bs = gregorian_to_bs(d.year, d.month, d.day)
                if bs:
                    self._bs_year.setValue(bs["year"])
                    self._bs_month.setValue(bs["month"])
                    self._bs_day.setValue(bs["day"])
            except Exception:
                pass

        # Birth time
        birth_time = params.get("birth_time", "")
        if birth_time:
            normalized_time = normalize_birth_time(birth_time)
            self._set_canonical_time_text(normalized_time or birth_time)

        # Location hierarchy
        country = params.get("country") or "Nepal"
        region = params.get("region") or params.get("province") or (
            "Lumbini" if country == "Nepal" else None
        )
        district = params.get("district") or (
            "Kapilvastu" if country == "Nepal" and region == "Lumbini" else None
        )
        city = params.get("city") or params.get("birth_place") or district or ""
        default_location = district_metadata(country, district) or {}
        lat = params.get("latitude", default_location.get("lat", 0))
        lon = params.get("longitude", default_location.get("lon", 0))
        tz = params.get("timezone", default_location.get("tz", 5.75))

        country_index = self._country_combo.findData(country)
        self._country_combo.setCurrentIndex(max(country_index, 0))
        self._on_country_changed()
        if region:
            region_index = self._region_combo.findData(region)
            if region_index >= 0:
                self._region_combo.setCurrentIndex(region_index)
                self._on_region_changed()
        if district:
            district_index = self._district_combo.findData(district)
            if district_index >= 0:
                self._district_combo.setCurrentIndex(district_index)
                self._on_district_changed()

        city_name = city.split(",", 1)[0].strip() if city else ""
        city_index = self._city_combo.findText(city_name, Qt.MatchFixedString)
        if city_index >= 0:
            self._city_combo.setCurrentIndex(city_index)
            self._on_place_changed()
        elif city_name and self._city_combo.lineEdit() is not None:
            self._city_combo.lineEdit().setText(city_name)
            self._selected_city = None
        self._lat_edit.setText(str(lat))
        self._lon_edit.setText(str(lon))
        self._tz_edit.setText(str(tz))
        known_values = self._selected_city is not None or district_metadata(country, district)
        self._custom_location.setChecked(not bool(known_values))
        self._set_coordinate_editable(not bool(known_values))
        if self._selected_city is not None and params.get("timezone_id"):
            self._selected_city["timezone_id"] = params.get("timezone_id")

        # Additional Janmapatrika details
        for key, edit in self._janmapatrika_edits.items():
            edit.setText(str(params.get(key) or ""))
        status = params.get("marital_status")
        index = self._marital_status.findData(status) if status else 0
        self._marital_status.setCurrentIndex(max(index, 0))
        self._family_details.setText(str(params.get("family_details") or ""))
        self._comments_edit.setPlainText(str(params.get("comments") or ""))
        self._events_table.clearContents()
        self._events_table.setRowCount(max(3, len(params.get("life_events") or [])))
        for row, event in enumerate(params.get("life_events") or []):
            self._events_table.setItem(row, 0, QTableWidgetItem(str(event.get("date") or "")))
            self._events_table.setItem(row, 1, QTableWidgetItem(str(event.get("event") or "")))

        self.invalidate_preview()

    def _open_user_guide(self) -> None:
        """Open the interactive User Guide dialog."""
        try:
            from gui.widgets.user_guide import show_user_guide
            show_user_guide(self)
        except Exception:
            pass
