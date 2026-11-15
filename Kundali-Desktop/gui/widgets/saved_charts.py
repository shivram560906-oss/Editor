"""
gui/widgets/saved_charts.py

Saved Charts page — shows all saved kundali records.
Features:
  - List of saved charts with name, birth date, birth place
  - Click to open / recalculate
  - Search/filter by name
  - Delete button
  - Shows BS date in Nepali
"""
from __future__ import annotations
import sys, os
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QSizePolicy,
    QMessageBox, QApplication, QCheckBox, QFileDialog, QProgressDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QCursor

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY, COLOR_ERROR)
from gui.utils.bs_calendar import gregorian_to_bs, format_bs_date


def _parse_bs(birth_date: str, lang: str) -> str:
    """Convert YYYY-MM-DD to BS string."""
    try:
        import datetime
        d = datetime.date.fromisoformat(birth_date[:10])
        bs = gregorian_to_bs(d.year, d.month, d.day)
        if bs:
            return format_bs_date(bs, lang)
    except Exception:
        pass
    return birth_date


def _gender_icon(gender: str) -> str:
    return {"male": "पुरुष", "female": "महिला", "other": "अन्य"}.get(gender or "male", "पुरुष")


class ChartCard(QFrame):
    """Single saved chart card widget with optional checkbox for bulk selection."""
    open_requested   = Signal(int)   # record_id
    delete_requested = Signal(int)   # record_id
    selection_changed = Signal(int, bool)  # (record_id, is_selected)

    def __init__(self, record: dict, language: str = "ne", show_checkbox: bool = False, parent=None):
        super().__init__(parent)
        self._record = record
        self._lang   = language
        self._is_ne  = language == "ne"
        self._show_cb = show_checkbox
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 4px;
            }}
            QFrame:hover {{
                border-color: {COLOR_ACCENT};
                background: {BG_TERTIARY};
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        r = self._record

        # ── Top row: checkbox (optional) + name + gender + delete ──
        top = QHBoxLayout()
        top.setSpacing(8)

        if self._show_cb:
            self._checkbox = QCheckBox()
            self._checkbox.toggled.connect(
                lambda checked: self.selection_changed.emit(self._record["id"], checked)
            )
            top.addWidget(self._checkbox)

        gender_lbl = QLabel(_gender_icon(r.get("gender", "male")))
        gender_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 12px; font-weight: 600;")
        top.addWidget(gender_lbl)

        name_lbl = QLabel(r.get("name", "—"))
        name_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 700;"
        )
        top.addWidget(name_lbl, 1)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(28, 28)
        del_btn.setToolTip("मेट्नुहोस्" if self._is_ne else "Delete")
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 5px;
                color: {COLOR_TEXT_MUTED};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: rgba(239,68,68,0.15);
                border-color: #ef4444;
                color: #ef4444;
            }}
        """)
        del_btn.setCursor(QCursor(Qt.PointingHandCursor))
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._record["id"]))
        top.addWidget(del_btn)
        layout.addLayout(top)

        # ── Date row ──
        bs_date = _parse_bs(r.get("birth_date", ""), self._lang)
        bt      = r.get("birth_time", "")[:5]
        date_lbl = QLabel(f"📅 {bs_date}  {bt}")
        date_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(date_lbl)

        # ── Place row ──
        place = r.get("birth_place") or ""
        lat   = r.get("latitude",  0)
        lon   = r.get("longitude", 0)
        if place:
            place_text = f"📍 {place}  ({lat:.2f}°, {lon:.2f}°)"
        else:
            place_text = f"📍 {lat:.4f}°, {lon:.4f}°"
        place_lbl = QLabel(place_text)
        place_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(place_lbl)

        # ── Bottom row: ayanamsha + saved time + open button ──
        bottom = QHBoxLayout()
        ayan = r.get("ayanamsha_type", "LAHIRI")
        ayan_lbl = QLabel(ayan)
        ayan_lbl.setStyleSheet(f"""
            background: rgba(212,175,55,0.12);
            border: 1px solid rgba(212,175,55,0.3);
            border-radius: 8px;
            color: {COLOR_GOLD};
            font-size: 10px;
            font-weight: 700;
            padding: 2px 8px;
        """)
        bottom.addWidget(ayan_lbl)

        saved_at = r.get("created_at", "")[:16]
        saved_lbl = QLabel(f"💾 {saved_at}")
        saved_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        bottom.addWidget(saved_lbl)
        bottom.addStretch()

        open_btn = QPushButton("🔭 " + ("खोल्नुहोस्" if self._is_ne else "Open"))
        open_btn.setMinimumHeight(30)
        open_btn.setCursor(QCursor(Qt.PointingHandCursor))
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(140,122,230,0.2);
                border: 1px solid {COLOR_ACCENT};
                border-radius: 7px;
                color: {COLOR_TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 600;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background: rgba(212,175,55,0.2);
                border-color: {COLOR_GOLD};
                color: {COLOR_GOLD};
            }}
        """)
        open_btn.clicked.connect(lambda: self.open_requested.emit(self._record["id"]))
        bottom.addWidget(open_btn)
        layout.addLayout(bottom)

    def mouseDoubleClickEvent(self, event):
        self.open_requested.emit(self._record["id"])


class SavedChartsPage(QWidget):
    """
    Full saved charts page.
    Emits chart_open_requested(params_dict) when user clicks Open.
    """
    chart_open_requested = Signal(dict)   # params dict for calculate_chart()

    def __init__(self, language: str = "ne", parent=None):
        super().__init__(parent)
        self._lang   = language
        self._is_ne  = language == "ne"
        self._all_records: list[dict] = []
        self._build_ui()
        # Auto-load on show
        self._reload()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── Header ──
        hdr_row = QHBoxLayout()

        title = QLabel("💾 " + ("सेव गरिएका कुण्डलीहरू" if self._is_ne else "Saved Charts"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 700;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()

        self._count_badge = QLabel("0")
        self._count_badge.setStyleSheet(f"""
            background: rgba(212,175,55,0.15);
            border: 1px solid rgba(212,175,55,0.35);
            border-radius: 12px;
            color: {COLOR_GOLD};
            font-size: 12px;
            font-weight: 700;
            padding: 3px 12px;
        """)
        hdr_row.addWidget(self._count_badge)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                color: {COLOR_TEXT_SECONDARY};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {BG_TERTIARY};
                color: {COLOR_GOLD};
            }}
        """)
        refresh_btn.clicked.connect(self._reload)
        hdr_row.addWidget(refresh_btn)
        layout.addLayout(hdr_row)

        # ── Toolbar row: search + refresh + bulk export ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText(
            "🔍  नाम खोज्नुहोस्..." if self._is_ne else "🔍  Search by name..."
        )
        self._search.setMinimumHeight(36)
        self._search.textChanged.connect(self._filter)
        toolbar.addWidget(self._search, 1)

        self._select_mode_btn = QPushButton(
            "☑️ " + ("चयन" if self._is_ne else "Select")
        )
        self._select_mode_btn.setCheckable(True)
        self._select_mode_btn.setMinimumHeight(34)
        self._select_mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_TERTIARY}; border: 1px solid {BORDER_COLOR};
                border-radius: 6px; padding: 4px 12px; font-size: 12px;
                color: {COLOR_TEXT_SECONDARY};
            }}
            QPushButton:checked {{
                background: {COLOR_ACCENT}; color: #fff; border-color: {COLOR_ACCENT};
            }}
            QPushButton:hover {{ background: {BG_SECONDARY}; }}
        """)
        self._select_mode_btn.toggled.connect(self._toggle_select_mode)
        toolbar.addWidget(self._select_mode_btn)

        self._export_sel_btn = QPushButton(
            "🗄️ " + ("चयनित Export" if self._is_ne else "Export Selected")
        )
        self._export_sel_btn.setMinimumHeight(34)
        self._export_sel_btn.setEnabled(False)
        self._export_sel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: #fff;
                border: none; border-radius: 6px; padding: 4px 14px; font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:disabled {{ background: {BORDER_COLOR}; color: {COLOR_TEXT_MUTED}; }}
            QPushButton:hover {{ background: #1d4ed8; }}
        """)
        self._export_sel_btn.clicked.connect(self._export_selected)
        toolbar.addWidget(self._export_sel_btn)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(34, 34)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                color: {COLOR_TEXT_SECONDARY};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {BG_TERTIARY};
                color: {COLOR_GOLD};
            }}
        """)
        refresh_btn.clicked.connect(self._reload)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        self._selected_ids: set[int] = set()
        self._select_mode: bool = False

        # ── Empty state ──
        self._empty_label = QLabel(
            "कुनै कुण्डली सेव गरिएको छैन।\nजन्म विवरण भरेर गणना गर्नुहोस् र सेव गर्नुहोस्।"
            if self._is_ne else
            "No saved charts yet.\nFill birth details, calculate, and save."
        )
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 13px;
            padding: 40px 20px;
            border: 2px dashed {BORDER_COLOR};
            border-radius: 12px;
        """)
        self._empty_label.setWordWrap(True)
        layout.addWidget(self._empty_label)

        # ── Scrollable card list ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._scroll.hide()

        self._cards_container = QWidget()
        self._cards_container.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setSpacing(10)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._cards_container)
        layout.addWidget(self._scroll, 1)

        layout.addStretch()

    # ── Data operations ──────────────────────────────────────────────────────

    def _reload(self):
        """Load all records from database."""
        try:
            from gui.utils.chart_storage import list_charts
            self._all_records = list_charts()
        except Exception as e:
            self._all_records = []
        self._count_badge.setText(str(len(self._all_records)))
        self._filter(self._search.text())

    def _filter(self, query: str = ""):
        q = query.strip().lower()
        if q:
            filtered = [r for r in self._all_records
                        if q in r.get("name", "").lower()
                        or q in (r.get("birth_place") or "").lower()]
        else:
            filtered = self._all_records
        self._render_cards(filtered)

    def _render_cards(self, records: list):
        # Clear
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not records:
            self._scroll.hide()
            self._empty_label.show()
            return

        self._empty_label.hide()
        self._scroll.show()

        for rec in records:
            card = ChartCard(rec, self._lang, show_checkbox=self._select_mode)
            card.open_requested.connect(self._on_open)
            card.delete_requested.connect(self._on_delete)
            card.selection_changed.connect(self._on_card_selected)
            self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()

    def _on_open(self, record_id: int):
        try:
            from gui.utils.chart_storage import get_chart_params
            params = get_chart_params(record_id)
            if params:
                self.chart_open_requested.emit(params)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load chart: {e}")

    def _on_delete(self, record_id: int):
        is_ne = self._is_ne
        reply = QMessageBox.question(
            self,
            "मेट्नुहोस्" if is_ne else "Delete",
            "के तपाईं यो कुण्डली मेट्न चाहनुहुन्छ?" if is_ne
            else "Are you sure you want to delete this chart?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            from gui.utils.chart_storage import delete_chart
            if not delete_chart(record_id):
                QMessageBox.warning(
                    self,
                    "मेट्न सकिएन" if is_ne else "Delete Failed",
                    "यो कुण्डली मेट्न सकिएन वा तपाईंसँग यसको अनुमति छैन।"
                    if is_ne else
                    "The chart could not be deleted, or you do not have permission to delete it.",
                )
            self._reload()

    def _on_card_selected(self, record_id: int, checked: bool):
        if checked:
            self._selected_ids.add(record_id)
        else:
            self._selected_ids.discard(record_id)
        self._export_sel_btn.setEnabled(bool(self._selected_ids))
        count = len(self._selected_ids)
        self._export_sel_btn.setText(
            f"🗄️ चयनित Export ({count})" if self._is_ne else f"🗄️ Export Selected ({count})"
        )

    def _toggle_select_mode(self, enabled: bool):
        self._select_mode = enabled
        self._selected_ids.clear()
        self._export_sel_btn.setEnabled(False)
        self._export_sel_btn.setText(
            "🗄️ चयनित Export" if self._is_ne else "🗄️ Export Selected"
        )
        self._filter(self._search.text())  # Re-render with/without checkboxes

    def _export_selected(self):
        """Export selected charts as PNG screenshots."""
        if not self._selected_ids:
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "कुनल फोल्डरमा Export गर्ने?" if self._is_ne else "Select folder to export charts",
        )
        if not folder:
            return

        records = [r for r in self._all_records if r.get("id") in self._selected_ids]
        progress = QProgressDialog(
            "कुण्डली Export हुँदैछ..." if self._is_ne else "Exporting charts...",
            "रद्द" if self._is_ne else "Cancel",
            0, len(records), self
        )
        progress.setWindowTitle("Export")
        progress.setMinimumDuration(0)

        from gui.backend_bridge import calculate_chart
        from gui.widgets.north_indian_chart import NorthIndianChartPage
        import os

        exported = 0
        for i, rec in enumerate(records):
            if progress.wasCanceled():
                break
            progress.setValue(i)
            progress.setLabelText(
                f"कुण्डली {i+1}/{len(records)}: {rec.get('name', '?')}" if self._is_ne
                else f"Chart {i+1}/{len(records)}: {rec.get('name', '?')}"
            )
            QApplication.processEvents()
            try:
                data = calculate_chart(dict(rec))
                page = NorthIndianChartPage(data, "D1", self._lang)
                page.resize(800, 700)
                page.show()
                QApplication.processEvents()
                pixmap = page.grab()
                page.close()
                name = rec.get("name", f"chart_{rec.get('id',i)}").replace(" ", "_")
                path = os.path.join(folder, f"{name}.png")
                pixmap.save(path)
                exported += 1
            except Exception:
                pass

        progress.setValue(len(records))
        QMessageBox.information(
            self,
            "Export सम्पन्न",
            f"{exported} कुण्डली Export गरियो: {folder}" if self._is_ne
            else f"{exported} chart(s) exported to: {folder}"
        )

    def showEvent(self, event):
        """Reload when page becomes visible."""
        super().showEvent(event)
        self._reload()
