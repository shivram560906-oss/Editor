"""
gui/widgets/planet_analysis_dialog.py

Planet Summary Report (ग्रह सारांश रिपोर्ट) for PySide6 Desktop application.
Matches the classical Parashara clean PDF / document page format:
- Elegant outer document frame
- Top Header: Left title, Center ॐ circle, Right 'ग्रह सारांश - [ग्रह]'
- Centered Large Planet Name + Top Auspicious Status (शुभ / अशुभ %)
- 2-Column Clean Classical Grid Layout (No noisy individual boxes)
- Left Column: बल, शुभत्व, महत्व, समय: गोचर एवं दशाएँ
- Right Column: गुण, दशवर्ग में [ग्रह]
- Clear Devanagari typography, high contrast, clean line items
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from gui.utils.planet_analysis_engine import analyze_planet_full, to_nepali_digits


class PlanetAnalysisDialog(QDialog):
    """Clean, printable document-style Planet Summary Report Dialog."""

    def __init__(self, planet_name: str, chart_data: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"ग्रह सारांश — {planet_name}")
        self.resize(1180, 820)
        self.setMinimumSize(880, 600)
        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
                color: #0f172a;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #e2e8f0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                border-radius: 5px;
            }
        """)

        self._planet_name = planet_name
        self._chart_data = chart_data
        self._report = analyze_planet_full(planet_name, chart_data)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        # Action bar at top
        actions_bar = QHBoxLayout()
        actions_bar.addStretch(1)
        close_btn = QPushButton("✕ बन्द गर्नुहोस्")
        close_btn.setFixedHeight(34)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                color: #475569;
                font-weight: 700;
                font-size: 13px;
                padding: 4px 18px;
            }
            QPushButton:hover {
                background: #f1f5f9;
                color: #0f172a;
                border-color: #94a3b8;
            }
        """)
        close_btn.clicked.connect(self.accept)
        actions_bar.addWidget(close_btn)
        root.addLayout(actions_bar)

        # Scroll Area for document page
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        doc_host = QWidget()
        doc_layout = QVBoxLayout(doc_host)
        doc_layout.setContentsMargins(10, 4, 10, 14)

        # Document Page Frame - Full Width responsive
        page = QFrame()
        page.setObjectName("DocumentPage")
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        page.setStyleSheet("""
            QFrame#DocumentPage {
                background: #ffffff;
                border: 2px solid #b91c1c;
                border-radius: 10px;
                padding: 20px 24px;
            }
        """)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(24, 18, 24, 20)
        page_layout.setSpacing(14)

        # ── 1. Top Document Header ──
        hdr_layout = QHBoxLayout()
        left_hdr = QLabel("शिवराम ज्योतिष")
        left_hdr.setStyleSheet("font-size: 15px; font-weight: bold; color: #1e293b;")
        hdr_layout.addWidget(left_hdr, 1, Qt.AlignLeft | Qt.AlignVCenter)

        # Om Circle
        om_lbl = QLabel("ॐ")
        om_lbl.setAlignment(Qt.AlignCenter)
        om_lbl.setFixedSize(42, 42)
        om_lbl.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #b91c1c;
            border: 2px solid #b91c1c;
            border-radius: 21px;
            background: #fff5f5;
        """)
        hdr_layout.addWidget(om_lbl, 0, Qt.AlignCenter)

        p_ne = self._report.get("1_name", self._planet_name)
        right_hdr = QLabel(f"ग्रह सारांश - {p_ne}")
        right_hdr.setStyleSheet("font-size: 15px; font-weight: bold; color: #b91c1c; text-decoration: underline;")
        hdr_layout.addWidget(right_hdr, 1, Qt.AlignRight | Qt.AlignVCenter)
        page_layout.addLayout(hdr_layout)

        # ── 2. Large Centered Planet Name + Auspicious Verdict ──
        p_title_box = QVBoxLayout()
        p_title_box.setSpacing(8)

        p_title = QLabel(p_ne)
        p_title.setAlignment(Qt.AlignCenter)
        p_title.setStyleSheet("font-size: 30px; font-weight: 900; color: #0f172a; margin-top: 2px;")
        p_title_box.addWidget(p_title)

        shubha_pct_ne = self._report.get("shubha_pct_ne", "५०")
        ashubha_pct_ne = self._report.get("ashubha_pct_ne", "५०")

        # Top Status Row: [शुभ फल: XX%] [अशुभ फल: YY%] [📋 कारण]
        status_row = QHBoxLayout()
        status_row.setSpacing(14)
        status_row.setAlignment(Qt.AlignCenter)

        shubha_badge = QLabel(f"शुभ फल: {shubha_pct_ne}%")
        shubha_badge.setStyleSheet("""
            font-size: 16px;
            font-weight: 900;
            color: #16a34a;
            background: #f0fdf4;
            border: 1.5px solid #16a34a;
            border-radius: 6px;
            padding: 5px 16px;
        """)
        status_row.addWidget(shubha_badge)

        ashubha_badge = QLabel(f"अशुभ फल: {ashubha_pct_ne}%")
        ashubha_badge.setStyleSheet("""
            font-size: 16px;
            font-weight: 900;
            color: #dc2626;
            background: #fef2f2;
            border: 1.5px solid #dc2626;
            border-radius: 6px;
            padding: 5px 16px;
        """)
        status_row.addWidget(ashubha_badge)

        reasons_btn = QPushButton("📋 कारण")
        reasons_btn.setCursor(Qt.PointingHandCursor)
        reasons_btn.setFixedHeight(34)
        reasons_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: 800;
                color: #b91c1c;
                background: #fff1f2;
                border: 1.5px solid #b91c1c;
                border-radius: 6px;
                padding: 4px 16px;
            }
            QPushButton:hover {
                background: #b91c1c;
                color: #ffffff;
            }
        """)
        reasons_btn.clicked.connect(self._open_reasons_dialog)
        status_row.addWidget(reasons_btn)

        p_title_box.addLayout(status_row)
        page_layout.addLayout(p_title_box)

        # ── 3. Main 2-Column Content Layout ──
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(32)

        # Left Column
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Right Column
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # ── Left Column Sections ──
        # Section: बल
        left_col.addWidget(self._build_section_header("बल"))
        left_col.addWidget(self._build_item_list([
            ("षड्बल", self._report.get("2_shadbala", "—")),
            ("षड्बल तुलनात्मक स्थिति", self._report.get("3_shadbala_rank", "—")),
        ]))

        # Section: शुभत्व
        left_col.addWidget(self._build_section_header("शुभत्व"))
        left_col.addWidget(self._build_item_list([
            ("इष्ट कष्ट फल", self._report.get("5_ishta_kashta", "—")),
            ("इष्ट कष्ट तुलनात्मक स्थिति", self._report.get("6_ishta_kashta_rank", "—")),
            ("उच्च प्रतिशत", self._report.get("7_uchcha_pct", "—")),
            ("पूर्ण प्रतिशत", self._report.get("8_purna_pct", "—")),
            ("शुभाशुभ", self._report.get("9_dignity", "—")),
            ("विंशोपक बल", self._report.get("10_vimshopaka", "—")),
            ("वैशेषिका संख्या", self._report.get("11_vaisheshikamsa", "—")),
            ("अष्टकवर्ग बिन्दु", self._report.get("12_ashtakavarga", "—")),
            ("अस्त", "अस्त" if "अस्त" in self._report.get("13_state", "") else "—"),
            ("बीचमा / सहग्रह", self._report.get("31_yuti", "—")),
            ("षष्ट्यांश", "शुभ" if self._report.get("is_shubha", True) else "अशुभ"),
        ]))

        # Section: महत्व
        left_col.addWidget(self._build_section_header("महत्व"))
        left_col.addWidget(self._build_item_list([
            ("डोमिनेन्स तुलनात्मक स्थिति", self._report.get("14_dominance", "—")),
            ("कारक", self._report.get("15_karakatwa", "—")),
            ("लग्नेश संख्या", self._report.get("16_lagnesha_num", "—")),
        ]))

        # Section: समय: गोचर एवं दशाएँ
        left_col.addWidget(self._build_section_header("समय: गोचर एवं दशाएँ (वि.सं.)"))
        left_col.addWidget(self._build_item_list([
            (f"{p_ne} महादशा आरम्भ", self._report.get("19_md_start_bs", "—")),
            (f"{p_ne} महादशा अन्त", self._report.get("20_md_end_bs", "—")),
            (f"गोचर चक्र मितिहरू", self._report.get("21_transit_dates", "—")),
        ]))
        left_col.addStretch(1)

        # ── Right Column Sections ──
        # Section: गुण
        right_col.addWidget(self._build_section_header("गुण"))
        right_col.addWidget(self._build_item_list([
            ("स्वामित्व", self._report.get("22_d1_ownership", "—")),
            ("नवांश स्वामित्व", self._report.get("23_d9_ownership", "—")),
            ("राशि", self._report.get("24_rashi", "—")),
            ("नवांश", self._report.get("25_navamsha", "—")),
            ("नक्षत्र", self._report.get("26_nakshatra", "—")),
            ("नक्षत्र स्वामी, देवता", f"{self._report.get('27_nak_lord', '—')}, {self._report.get('28_nak_deity', '—')}"),
            ("षड्वर्ग डिस्पोजिटर", self._report.get("29_shadvarga_dispositors", "—")),
            ("षड्वर्ग तत्व", self._report.get("30_shadvarga_tattvas", "—")),
            ("युति", self._report.get("31_yuti", "—")),
            ("दृष्टि", self._report.get("32_drishti", "—")),
            ("जाग्रदादि अवस्था", self._report.get("33_jagradadi", "—")),
            ("बालादि अवस्था", self._report.get("34_baladi", "—")),
            ("लज्जितादि अवस्था", self._report.get("35_lajjitadi", "—")),
            ("दीप्तादि अवस्था", self._report.get("36_deeptadi", "—")),
            ("शयनादि अवस्था", self._report.get("37_shayanadi", "—")),
        ]))

        # Section: दशवर्ग में [ग्रह]
        right_col.addWidget(self._build_section_header(f"दशवर्ग में {p_ne}"))
        dashavarga_items = []
        for row in self._report.get("38_dashavarga_rows", []):
            dashavarga_items.append((f"{row['varga']} ({row['area']})", f"{row['sign']}, {row['value']}"))
        right_col.addWidget(self._build_item_list(dashavarga_items))
        right_col.addStretch(1)

        cols_layout.addLayout(left_col, 1)
        cols_layout.addLayout(right_col, 1)
        page_layout.addLayout(cols_layout)

        # Footer
        footer = QLabel("शिवराम वैदिक ज्योतिष सफ्टवेयर • सर्वाधिकार सुरक्षित")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 12.5px; color: #94a3b8; margin-top: 14px; border-top: 1px dashed #cbd5e1; padding-top: 8px;")
        page_layout.addWidget(footer)

        doc_layout.addWidget(page)
        scroll.setWidget(doc_host)
        root.addWidget(scroll, 1)

    def _build_section_header(self, title: str) -> QWidget:
        """Create a classical bold red section header with clean red underline."""
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 4, 0, 4)
        v.setSpacing(3)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #b91c1c;")
        v.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setStyleSheet("border: none; background-color: #b91c1c; height: 2px; max-height: 2px;")
        v.addWidget(line)
        return w

    def _build_item_list(self, items: List[tuple[str, str]]) -> QWidget:
        """Create a clean 2-column key-value list with high-readability typography."""
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 2, 0, 4)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(5)

        for row_idx, (key, val) in enumerate(items):
            k_lbl = QLabel(str(key))
            k_lbl.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #1e293b;")
            k_lbl.setWordWrap(True)

            v_lbl = QLabel(str(val))
            v_lbl.setStyleSheet("font-size: 13.5px; font-weight: 500; color: #334155;")
            v_lbl.setWordWrap(True)

            grid.addWidget(k_lbl, row_idx, 0, Qt.AlignTop | Qt.AlignLeft)
            grid.addWidget(v_lbl, row_idx, 1, Qt.AlignTop | Qt.AlignLeft)

        grid.setColumnStretch(0, 4)
        grid.setColumnStretch(1, 6)
        return container

    def _open_reasons_dialog(self) -> None:
        """Open the detailed Parashari Reasons Modal."""
        dlg = PlanetReasonsDialog(self._planet_name, self._report, self)
        dlg.exec()


class PlanetReasonsDialog(QDialog):
    """Detailed Parashari calculation reasons modal."""

    def __init__(self, planet_name: str, report: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        p_ne = report.get("1_name", planet_name)
        self.setWindowTitle(f"फलादेशको पाराशरी कारण तथा आधार — {p_ne}")
        self.resize(960, 720)
        self.setMinimumSize(780, 560)
        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
                color: #0f172a;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #e2e8f0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                border-radius: 5px;
            }
        """)

        self._planet_name = planet_name
        self._report = report
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(14)

        p_ne = self._report.get("1_name", self._planet_name)
        shubha_pct_ne = self._report.get("shubha_pct_ne", "५०")
        ashubha_pct_ne = self._report.get("ashubha_pct_ne", "५०")

        # ── Header Banner ──
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                padding: 14px 18px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setSpacing(10)

        t_lbl = QLabel(f"🪐 {p_ne} ग्रहको फलादेश गणना विश्लेषण")
        t_lbl.setStyleSheet("font-size: 22px; font-weight: 900; color: #0f172a;")
        h_layout.addWidget(t_lbl, 0, Qt.AlignCenter)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(14)
        badge_row.setAlignment(Qt.AlignCenter)

        s_badge = QLabel(f"शुभ फल: {shubha_pct_ne}%")
        s_badge.setStyleSheet("""
            font-size: 16px;
            font-weight: 900;
            color: #16a34a;
            background: #f0fdf4;
            border: 1.5px solid #16a34a;
            border-radius: 6px;
            padding: 5px 18px;
        """)
        badge_row.addWidget(s_badge)

        a_badge = QLabel(f"अशुभ फल: {ashubha_pct_ne}%")
        a_badge.setStyleSheet("""
            font-size: 16px;
            font-weight: 900;
            color: #dc2626;
            background: #fef2f2;
            border: 1.5px solid #dc2626;
            border-radius: 6px;
            padding: 5px 18px;
        """)
        badge_row.addWidget(a_badge)

        h_layout.addLayout(badge_row)
        layout.addWidget(header_card)

        # ── Card 1: Functional Nature ──
        fn_card = self._create_card(
            title="१. ग्रहको कार्यात्मक प्रकृति (Functional Nature)",
            title_color="#1e40af",
            bg_color="#f8fafc",
            border_color="#93c5fd"
        )
        fn_layout = QVBoxLayout(fn_card)
        fn_desc = QLabel(
            f"<b>कार्यात्मक स्थिति:</b> {self._report.get('functional_nature_text', '—')}<br>"
            f"<b>D1 भाव स्वामित्व:</b> {self._report.get('22_d1_ownership', '—')}<br>"
            f"<b>नैसर्गिक कारकत्व:</b> {self._report.get('15_karakatwa', '—')}"
        )
        fn_desc.setStyleSheet("font-size: 13.5px; line-height: 1.6; color: #334155;")
        fn_desc.setWordWrap(True)
        fn_layout.addWidget(fn_desc)
        layout.addWidget(fn_card)

        # ── Card 2: Positive / Auspicious Factors ──
        shubha_list = self._report.get("shubha_reasons", [])
        pos_card = self._create_card(
            title="२. शुभत्व बढाउने पाराशरी आधारहरू (+शुभ %)",
            title_color="#16a34a",
            bg_color="#f0fdf4",
            border_color="#86efac"
        )
        pos_layout = QVBoxLayout(pos_card)
        pos_layout.setSpacing(8)

        if shubha_list:
            for item in shubha_list:
                item_frame = QFrame()
                item_frame.setStyleSheet("""
                    QFrame {
                        background: #ffffff;
                        border: 1px solid #bbf7d0;
                        border-left: 4px solid #16a34a;
                        border-radius: 6px;
                        padding: 8px 12px;
                    }
                """)
                i_vbox = QVBoxLayout(item_frame)
                i_vbox.setContentsMargins(6, 4, 6, 4)
                i_vbox.setSpacing(3)

                top_row = QHBoxLayout()
                rule_lbl = QLabel(f"✓ [{item.get('category', '')}] {item.get('rule', '')}")
                rule_lbl.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #166534;")
                top_row.addWidget(rule_lbl, 1)

                impact_lbl = QLabel(item.get("impact", ""))
                impact_lbl.setStyleSheet("font-size: 13px; font-weight: 900; color: #15803d; background: #dcfce7; border-radius: 4px; padding: 2px 8px;")
                top_row.addWidget(impact_lbl, 0)
                i_vbox.addLayout(top_row)

                desc_lbl = QLabel(item.get("desc", ""))
                desc_lbl.setStyleSheet("font-size: 13px; color: #334155; line-height: 1.4;")
                desc_lbl.setWordWrap(True)
                i_vbox.addWidget(desc_lbl)

                pos_layout.addWidget(item_frame)
        else:
            none_lbl = QLabel("यस कुण्डलीमा कुनै विशेष अतिरिक्त शुभ कारक लागू भएको छैन।")
            none_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
            pos_layout.addWidget(none_lbl)

        layout.addWidget(pos_card)

        # ── Card 3: Negative / Inauspicious Factors ──
        ashubha_list = self._report.get("ashubha_reasons", [])
        neg_card = self._create_card(
            title="३. अशुभत्व बढाउने पाराशरी आधारहरू (+अशुभ %)",
            title_color="#dc2626",
            bg_color="#fef2f2",
            border_color="#fca5a5"
        )
        neg_layout = QVBoxLayout(neg_card)
        neg_layout.setSpacing(8)

        if ashubha_list:
            for item in ashubha_list:
                item_frame = QFrame()
                item_frame.setStyleSheet("""
                    QFrame {
                        background: #ffffff;
                        border: 1px solid #fecaca;
                        border-left: 4px solid #dc2626;
                        border-radius: 6px;
                        padding: 8px 12px;
                    }
                """)
                i_vbox = QVBoxLayout(item_frame)
                i_vbox.setContentsMargins(6, 4, 6, 4)
                i_vbox.setSpacing(3)

                top_row = QHBoxLayout()
                rule_lbl = QLabel(f"✗ [{item.get('category', '')}] {item.get('rule', '')}")
                rule_lbl.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #991b1b;")
                top_row.addWidget(rule_lbl, 1)

                impact_lbl = QLabel(item.get("impact", ""))
                impact_lbl.setStyleSheet("font-size: 13px; font-weight: 900; color: #b91c1c; background: #fee2e2; border-radius: 4px; padding: 2px 8px;")
                top_row.addWidget(impact_lbl, 0)
                i_vbox.addLayout(top_row)

                desc_lbl = QLabel(item.get("desc", ""))
                desc_lbl.setStyleSheet("font-size: 13px; color: #334155; line-height: 1.4;")
                desc_lbl.setWordWrap(True)
                i_vbox.addWidget(desc_lbl)

                neg_layout.addWidget(item_frame)
        else:
            none_lbl = QLabel("यस कुण्डलीमा कुनै विशेष अतिरिक्त अशुभ कारक लागू भएको छैन।")
            none_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
            neg_layout.addWidget(none_lbl)

        layout.addWidget(neg_card)

        # ── Card 4: Overall Verdict Synthesis ──
        syn_card = self._create_card(
            title="४. अन्तिम समग्र मूल्याङ्कन (Final Parashari Synthesis)",
            title_color="#7c2d12",
            bg_color="#fffbeb",
            border_color="#fde68a"
        )
        syn_layout = QVBoxLayout(syn_card)
        syn_desc = QLabel(self._report.get("verdict_summary", "—"))
        syn_desc.setStyleSheet("font-size: 13.5px; font-weight: 600; line-height: 1.6; color: #78350f;")
        syn_desc.setWordWrap(True)
        syn_layout.addWidget(syn_desc)
        layout.addWidget(syn_card)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Bottom Close Button
        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        close_btn = QPushButton("बन्द गर्नुहोस्")
        close_btn.setFixedHeight(34)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #0f172a;
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                padding: 4px 24px;
            }
            QPushButton:hover {
                background: #334155;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        root.addLayout(btn_box)

    def _create_card(self, title: str, title_color: str, bg_color: str, border_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border: 1.5px solid {border_color};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 14.5px; font-weight: 900; color: {title_color}; margin-bottom: 4px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)
        card_layout.addWidget(t_lbl)
        return card
