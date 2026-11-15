"""
gui/widgets/life_conclusion_page.py

Comprehensive Parashari Predictive Life Reading Document Page (निष्कर्ष → फलित).
Features:
  - Document-style scrollable reading view (Clean white background, crisp dark text)
  - 15 Evidence-based life chapters from birth to later years
  - Native Print and High-Fidelity PDF Export support
  - English & Nepali language support
"""
from __future__ import annotations
import os
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QFileDialog, QMessageBox,
    QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QMarginsF
from PySide6.QtGui import (
    QFont, QColor, QTextDocument, QPageLayout, QPageSize,
    QPainter, QTextCursor, QTextCharFormat, QTextBlockFormat
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# ── Clean Document Theme ─────────────────────────────────────────────────────
COLOR_PAGE_BG       = "#f1f5f9"
COLOR_DOC_BG        = "#ffffff"
COLOR_DOC_BORDER    = "#cbd5e1"
COLOR_TEXT_DARK     = "#0f172a"
COLOR_TEXT_SECONDARY= "#334155"
COLOR_TEXT_MUTED    = "#64748b"
COLOR_PRIMARY_GOLD  = "#92400e"
COLOR_ACCENT_BLUE   = "#1d4ed8"
COLOR_HEADER_BG     = "#f8fafc"
COLOR_DIVIDER       = "#e2e8f0"


class LifeConclusionPage(QWidget):
    """
    Complete Life Reading (निष्कर्ष → फलित) Document Page.
    """

    def __init__(self, chart_data: Optional[dict] = None, language: str = "ne",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data
        self._report_data: Dict[str, Any] = {}

        self.setStyleSheet(f"background-color: {COLOR_PAGE_BG};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # ── Top Toolbar ───────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        title_lbl = QLabel(
            "📜 सम्पूर्ण जीवन फलित तथा निष्कर्ष" if self._is_ne else "📜 Comprehensive Life Reading & Conclusion"
        )
        title_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_GOLD}; font-size: 16px; font-weight: 700;")
        toolbar.addWidget(title_lbl)
        toolbar.addStretch()

        # Action Buttons
        self._btn_print = QPushButton("🖨 प्रिन्ट" if self._is_ne else "🖨 Print")
        self._btn_pdf = QPushButton("📄 PDF डाउनलोड" if self._is_ne else "📄 Export PDF")

        btn_style = """
            QPushButton {
                background: #ffffff;
                color: #1e293b;
                border: 1px solid #94a3b8;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f8fafc;
                border-color: #2563eb;
                color: #2563eb;
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
        """
        for b in (self._btn_print, self._btn_pdf):
            b.setStyleSheet(btn_style)
            b.setCursor(Qt.PointingHandCursor)
            toolbar.addWidget(b)

        self._btn_print.clicked.connect(self._handle_print)
        self._btn_pdf.clicked.connect(self._handle_export_pdf)

        main_layout.addLayout(toolbar)

        # ── Document Scroll Area ──────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLOR_DOC_BORDER};
                border-radius: 8px;
                background-color: {COLOR_PAGE_BG};
            }}
        """)

        # Document Container Widget (White Sheet style)
        self._doc_widget = QWidget()
        self._doc_widget.setStyleSheet(f"background-color: {COLOR_DOC_BG};")
        self._doc_layout = QVBoxLayout(self._doc_widget)
        self._doc_layout.setContentsMargins(40, 36, 40, 40)
        self._doc_layout.setSpacing(24)

        scroll.setWidget(self._doc_widget)
        main_layout.addWidget(scroll, 1)

        # Load and render content
        self.load(chart_data, language)

    def load(self, chart_data: Optional[dict], language: str = "ne"):
        self._language = language
        self._is_ne = language == "ne"
        self._chart_data = chart_data

        # Clear existing layout items
        while self._doc_layout.count():
            item = self._doc_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not chart_data:
            empty_lbl = QLabel(
                "कुण्डली डाटा उपलब्ध छैन।\nकृपया पहिले जन्म विवरण भर्नुहोस्।"
                if self._is_ne else
                "Chart data is unavailable.\nPlease enter birth details first."
            )
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 40px;")
            self._doc_layout.addWidget(empty_lbl)
            return

        try:
            try:
                from backend.calculator.life_conclusion_engine import generate_comprehensive_life_phalita
            except ImportError:
                from calculator.life_conclusion_engine import generate_comprehensive_life_phalita
            self._report_data = generate_comprehensive_life_phalita(chart_data, language)
            self._render_document(self._report_data)
        except Exception as e:
            err_lbl = QLabel(f"⚠ फलित निर्माणमा त्रुटि: {e}")
            err_lbl.setStyleSheet("color: #b91c1c; font-size: 13px;")
            self._doc_layout.addWidget(err_lbl)

    def _render_document(self, r: dict):
        lay = self._doc_layout
        is_ne = self._is_ne
        meta = r.get("metadata", {})

        # ── 1. Document Header ────────────────────────────────────────────────
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_HEADER_BG};
                border: 1px solid {COLOR_DIVIDER};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        hl = QVBoxLayout(hdr_frame)
        hl.setSpacing(8)

        doc_title = QLabel("श्री गणेशाय नमः\nजन्मकुण्डली सम्पूर्ण जीवन फलित तथा अन्तिम निष्कर्ष")
        doc_title.setAlignment(Qt.AlignCenter)
        doc_title.setStyleSheet(f"color: {COLOR_PRIMARY_GOLD}; font-size: 18px; font-weight: 800; line-height: 1.5;")
        hl.addWidget(doc_title)

        div_line = QFrame()
        div_line.setFrameShape(QFrame.HLine)
        div_line.setStyleSheet(f"color: {COLOR_DIVIDER}; margin: 6px 0;")
        hl.addWidget(div_line)

        # Meta Grid Table
        grid_html = f"""
        <table style="width:100%; font-size:13.5px; color:{COLOR_TEXT_SECONDARY}; line-height:1.7;">
            <tr>
                <td style="width:50%;"><b>नाम:</b> {meta.get('name', '—')} ({meta.get('gender', '')})</td>
                <td style="width:50%;"><b>जन्म मिति:</b> {meta.get('birth_date_bs', '—')}</td>
            </tr>
            <tr>
                <td><b>जन्म समय:</b> {meta.get('birth_time', '—')} | <b>स्थान:</b> {meta.get('birth_place', '—')}</td>
                <td><b>लग्न:</b> {meta.get('lagna', '—')} | <b>राशि:</b> {meta.get('moon_rashi', '—')}</td>
            </tr>
            <tr>
                <td><b>नक्षत्र:</b> {meta.get('nakshatra', '—')} | <b>तिथि:</b> {meta.get('tithi', '—')}</td>
                <td><b>सक्रिय दशा:</b> <span style="color:#b45309;font-weight:700;">{meta.get('current_dasha', '—')}</span></td>
            </tr>
        </table>
        """
        meta_lbl = QLabel(grid_html)
        meta_lbl.setWordWrap(True)
        hl.addWidget(meta_lbl)

        lay.addWidget(hdr_frame)

        # ── 2. Chapters ───────────────────────────────────────────────────────
        chapters: List[dict] = r.get("chapters", [])
        if not chapters:
            msg = r.get("message", "")
            note = QLabel(msg or ("फलित उपलब्ध छैन।" if is_ne else "No reading available."))
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 20px;")
            lay.addWidget(note)
            chapters = []

        for ch in chapters:
            unavailable = bool(ch.get("unavailable"))
            ch_box = QFrame()
            ch_box.setStyleSheet(f"""
                QFrame {{
                    background: #ffffff;
                    border: none;
                    border-bottom: 1px solid {COLOR_DIVIDER};
                    padding-bottom: 18px;
                }}
            """)
            cl = QVBoxLayout(ch_box)
            cl.setContentsMargins(0, 10, 0, 10)
            cl.setSpacing(10)

            title_text = ch.get("title", "")
            if unavailable:
                title_text += ("  (गणना नभएको)" if is_ne else "  (not calculated)")
            ch_title = QLabel(title_text)
            ch_title.setStyleSheet(f"""
                color: {COLOR_PRIMARY_GOLD if not unavailable else COLOR_TEXT_MUTED};
                font-size: 15.5px;
                font-weight: 700;
                border-left: 4px solid
                    {COLOR_PRIMARY_GOLD if not unavailable else COLOR_DOC_BORDER};
                padding-left: 10px;
            """)
            cl.addWidget(ch_title)

            # Body HTML (the engine already emits <br>-separated rich text).
            body_text = ch.get("body", ch.get("content", ""))
            p_lbl = QLabel(body_text)
            p_lbl.setWordWrap(True)
            p_lbl.setTextFormat(Qt.RichText)
            p_lbl.setStyleSheet(f"""
                color: {COLOR_TEXT_DARK if not unavailable else COLOR_TEXT_MUTED};
                font-size: 14.5px;
                line-height: 1.8;
                font-family: 'Segoe UI', 'Noto Sans Devanagari', sans-serif;
            """)
            cl.addWidget(p_lbl)

            # Provenance footer: exactly which engine/field produced this chapter.
            src = ch.get("sources") or []
            ref = ch.get("reference") or ""
            if src or ref:
                prov_text = (
                    (f"स्रोत: {', '.join(str(s) for s in src)}" if is_ne
                     else f"Sources: {', '.join(str(s) for s in src)}")
                    + (f" | शास्त्रीय सन्दर्भ: {ref}" if ref else "")
                )
                prov_lbl = QLabel(prov_text)
                prov_lbl.setWordWrap(True)
                prov_lbl.setStyleSheet(
                    f"color: {COLOR_ACCENT_BLUE}; font-size: 11.5px; line-height: 1.5;"
                )
                cl.addWidget(prov_lbl)

            lay.addWidget(ch_box)

        # ── 3. Document Footer / Classical Authority Statement ─────────────────
        ftr_frame = QFrame()
        ftr_frame.setStyleSheet(f"background:{COLOR_HEADER_BG}; border:1px solid {COLOR_DIVIDER}; border-radius:8px; padding:14px;")
        fl = QVBoxLayout(ftr_frame)
        fl.setSpacing(10)

        fn_text = r.get("footnote_ne" if is_ne else "footnote_en", "")
        fn_lbl = QLabel(f"<b>फलित निर्माणको आधार:</b><br>{fn_text}")
        fn_lbl.setWordWrap(True)
        fn_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; line-height: 1.6;")
        fl.addWidget(fn_lbl)

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)
        b_print = QPushButton("🖨 प्रिन्ट" if is_ne else "🖨 Print")
        b_pdf = QPushButton("📄 PDF डाउनलोड" if is_ne else "📄 Export PDF")
        for b in (b_print, b_pdf):
            b.setStyleSheet("""
                QPushButton {
                    background: #2563eb;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    padding: 7px 16px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover { background: #1d4ed8; }
            """)
            b.setCursor(Qt.PointingHandCursor)
            bottom_bar.addWidget(b)
        b_print.clicked.connect(self._handle_print)
        b_pdf.clicked.connect(self._handle_export_pdf)
        bottom_bar.addStretch()
        fl.addLayout(bottom_bar)

        lay.addWidget(ftr_frame)

    def _build_html_document(self) -> str:
        """Build clean, printable HTML document representation for Print/PDF."""
        r = self._report_data
        if not r:
            return "<html><body><p>कुण्डली डाटा उपलब्ध छैन।</p></body></html>"

        meta = r.get("metadata", {})
        chapters = r.get("chapters", [])
        footnote = r.get("footnote_ne" if self._is_ne else "footnote_en", "")
        is_ne = self._is_ne

        doc_title = (
            "श्री गणेशाय नमः<br>जन्मकुण्डली सम्पूर्ण जीवन फलित तथा अन्तिम निष्कर्ष"
            if is_ne else
            "Comprehensive Life Reading &amp; Conclusion"
        )
        if not chapters:
            message = r.get("message") or (
                "कुण्डली डाटा उपलब्ध छैन।" if is_ne else "Chart data is unavailable."
            )
            return (
                "<html><body><p style=\"font-family:'Segoe UI','Noto Sans "
                f"Devanagari',sans-serif;\">{message}</p></body></html>"
            )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Segoe UI', 'Noto Sans Devanagari', 'Georgia', serif;
                    color: #0f172a;
                    line-height: 1.8;
                    padding: 24px;
                }}
                .header-box {{
                    background-color: #f8fafc;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 16px 20px;
                    margin-bottom: 24px;
                }}
                .title {{
                    text-align: center;
                    color: #92400e;
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    line-height: 1.4;
                }}
                .meta-table {{
                    width: 100%;
                    font-size: 13.5px;
                    border-collapse: collapse;
                }}
                .meta-table td {{
                    padding: 5px 8px;
                    vertical-align: top;
                }}
                .chapter {{
                    margin-bottom: 22px;
                    padding-bottom: 16px;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .chapter-title {{
                    color: #92400e;
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 8px;
                }}
                .chapter-content {{
                    font-size: 14px;
                    text-align: justify;
                    line-height: 1.8;
                }}
                .footer-box {{
                    margin-top: 30px;
                    background-color: #f8fafc;
                    border: 1px solid #cbd5e1;
                    padding: 14px 18px;
                    font-size: 12px;
                    color: #64748b;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="header-box">
                <div class="title">{doc_title}</div>
                <table class="meta-table">
                    <tr>
                        <td><b>{'नाम' if is_ne else 'Name'}:</b> {meta.get('name', '')}</td>
                        <td><b>{'जन्म मिति' if is_ne else 'Birth date'}:</b> {meta.get('birth_date', '')}</td>
                    </tr>
                    <tr>
                        <td><b>{'समय' if is_ne else 'Time'}:</b> {meta.get('birth_time', '')}
                            | <b>{'स्थान' if is_ne else 'Place'}:</b> {meta.get('birth_place', '')}</td>
                        <td><b>{'लग्न' if is_ne else 'Lagna'}:</b> {meta.get('lagna', '')}
                            | <b>{'राशि' if is_ne else 'Moon sign'}:</b> {meta.get('moon_rashi', '')}</td>
                    </tr>
                    <tr>
                        <td><b>{'नक्षत्र' if is_ne else 'Nakshatra'}:</b> {meta.get('nakshatra', '')}
                            | <b>{'तिथि' if is_ne else 'Tithi'}:</b> {meta.get('tithi', '')}</td>
                        <td><b>{'सक्रिय दशा' if is_ne else 'Active dasha'}:</b> {meta.get('current_dasha', '')}</td>
                    </tr>
                    <tr>
                        <td><b>{'अयनांश' if is_ne else 'Ayanamsha'}:</b> {meta.get('ayanamsha', '')}</td>
                        <td><b>{'गणना संस्करण' if is_ne else 'Calculation version'}:</b> {meta.get('calculation_version', '')}</td>
                    </tr>
                </table>
            </div>
        """

        for ch in chapters:
            unavailable = bool(ch.get("unavailable"))
            body_text = ch.get("body", ch.get("content", ""))
            src = ch.get("sources") or []
            ref = ch.get("reference") or ""
            prov = (
                (f"{'स्रोत' if is_ne else 'Sources'}: {', '.join(str(s) for s in src)}")
                + (f" | {'शास्त्रीय सन्दर्भ' if is_ne else 'Reference'}: {ref}" if ref else "")
            )
            colour = "#64748b" if unavailable else "#92400e"
            html += f"""
            <div class="chapter">
                <div class="chapter-title" style="color:{colour};">{ch.get('title', '')}</div>
                <div class="chapter-content">{body_text}</div>
                <div style="font-size:11.5px; color:#1d4ed8; margin-top:6px;">{prov}</div>
            </div>
            """

        html += f"""
            <div class="footer-box">
                <b>{'फलित निर्माणको आधार' if is_ne else 'Basis of this reading'}:</b><br>{footnote}
            </div>
        </body>
        </html>
        """
        return html

    def _handle_print(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPageLayout.Portrait)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(self._build_html_document())
            doc.print_(printer)

    def _handle_export_pdf(self):
        default_name = f"Kundali_Phalita_{self._report_data.get('metadata', {}).get('name', 'Report')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF सेभ गर्नुहोस्" if self._is_ne else "Export PDF",
            default_name,
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageOrientation(QPageLayout.Portrait)
            printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Millimeter)

            doc = QTextDocument()
            doc.setHtml(self._build_html_document())
            doc.print_(printer)

            QMessageBox.information(
                self,
                "सफलता" if self._is_ne else "Success",
                f"PDF सफलतापूर्वक सेभ गरियो:\n{file_path}"
                if self._is_ne else
                f"PDF successfully exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "त्रुटि" if self._is_ne else "Error",
                f"PDF सेभ गर्न सकिएन: {e}" if self._is_ne else f"Failed to export PDF: {e}"
            )
