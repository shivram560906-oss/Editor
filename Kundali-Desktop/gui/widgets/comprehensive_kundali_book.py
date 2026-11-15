# -*- coding: utf-8 -*-
"""
gui/widgets/comprehensive_kundali_book.py

Comprehensive 50+ Page Kundali Book Viewer & PDF Export Widget for Desktop App.
Renders all 18 astrological chapters in full Nepali with Bikram Sambat dates,
and provides one-click high-fidelity multi-page PDF generation via QPrinter.
"""
from __future__ import annotations
import sys, os
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QMarginsF
from PySide6.QtGui import QTextDocument, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY, COLOR_SUCCESS, COLOR_ERROR)

try:
    from backend.calculator.comprehensive_book_engine import build_comprehensive_kundali_book
except ImportError:
    from calculator.comprehensive_book_engine import build_comprehensive_kundali_book


class ComprehensiveKundaliBookPage(QWidget):
    """Native multi-page Kundali Book Viewer and PDF export page."""

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._book_data: Dict[str, Any] = {}
        self._build_ui()
        if data:
            self.refresh(data)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # Top Toolbar
        top_bar = QHBoxLayout()
        title_lbl = QLabel("📜 " + ("बृहत् जीवन कुण्डली पुस्तक (५०+ पृष्ठ)" if self._is_ne else "Comprehensive Kundali Book (50+ Pages)"))
        title_lbl.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 800;")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()

        # Export PDF Button
        self._btn_pdf = QPushButton("📄 " + ("५०+ पृष्ठे PDF डाउनलोड" if self._is_ne else "Export 50+ Page PDF"))
        self._btn_pdf.setCursor(Qt.PointingHandCursor)
        self._btn_pdf.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_GOLD};
                color: #000000;
                font-weight: 800;
                font-size: 13.5px;
                padding: 7px 18px;
                border-radius: 6px;
                border: 1px solid #b45309;
            }}
            QPushButton:hover {{
                background: #f59e0b;
            }}
        """)
        self._btn_pdf.clicked.connect(self._handle_export_pdf)
        top_bar.addWidget(self._btn_pdf)

        # Print Button
        self._btn_print = QPushButton("🖨️ " + ("प्रिन्ट गर्नुहोस्" if self._is_ne else "Print Book"))
        self._btn_print.setCursor(Qt.PointingHandCursor)
        self._btn_print.setStyleSheet(f"""
            QPushButton {{
                background: {BG_TERTIARY};
                color: {COLOR_TEXT_PRIMARY};
                font-weight: 700;
                font-size: 13px;
                padding: 7px 14px;
                border-radius: 6px;
                border: 1px solid {BORDER_COLOR};
            }}
            QPushButton:hover {{
                background: {BG_SECONDARY};
            }}
        """)
        self._btn_print.clicked.connect(self._handle_print)
        top_bar.addWidget(self._btn_print)

        main_layout.addLayout(top_bar)

        # Document Viewer
        self._viewer = QTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setStyleSheet(f"""
            QTextEdit {{
                background: #ffffff;
                color: #0f172a;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 18px;
                font-family: 'Noto Sans Devanagari', 'Segoe UI', 'Kokila', 'Mangal', sans-serif;
                font-size: 13.5px;
            }}
        """)
        main_layout.addWidget(self._viewer, 1)

    def refresh(self, data: dict) -> None:
        self._data = data
        if not data:
            self._viewer.setHtml("<p style='text-align:center; padding:30px; color:#64748b;'>कुण्डली डाटा उपलब्ध छैन। पहिले कुण्डली गणना गर्नुहोस्।</p>")
            return

        book = data.get("comprehensive_book")
        if not book:
            book = build_comprehensive_kundali_book(data, self._lang)
            data["comprehensive_book"] = book
            
        self._book_data = book
        html_content = book.get("html", "")
        self._viewer.setHtml(html_content)

    def _handle_export_pdf(self):
        if not self._book_data:
            QMessageBox.warning(self, "सूचना", "पहिले कुण्डली गणना गर्नुहोस्।")
            return

        meta = self._data.get("metadata", {}) if self._data else {}
        name = meta.get("name", "Kundali")
        default_name = f"Brihat_Kundali_Book_{name}.pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "५०+ पृष्ठे जीवन कुण्डली PDF सेभ गर्नुहोस्" if self._is_ne else "Save Comprehensive Kundali PDF",
            default_name,
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Millimeter)

            doc = QTextDocument()
            doc.setHtml(self._book_data.get("html", ""))
            doc.print_(printer)

            QMessageBox.information(
                self,
                "सफलता" if self._is_ne else "Success",
                f"बृहत् ५०+ पृष्ठे जीवन कुण्डली PDF सफलतापूर्वक सेभ गरियो:\n\n{file_path}"
                if self._is_ne else
                f"Comprehensive Kundali PDF successfully saved to:\n\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "त्रुटि" if self._is_ne else "Error",
                f"PDF सेभ गर्न सकिएन: {e}" if self._is_ne else f"Failed to save PDF: {e}"
            )

    def _handle_print(self):
        if not self._book_data:
            return
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(self._book_data.get("html", ""))
            doc.print_(printer)
