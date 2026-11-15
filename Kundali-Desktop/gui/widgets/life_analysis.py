"""
gui/widgets/life_analysis.py

Life Analysis & Predictions Reports:
- LifeAnalysisPage (Marriage, Career, Health, Child, Education, Finance)
- DashaPhalPage (Interpretation of current Dasha)
- HoroscopePage (Daily & Period Forecast)
- VarshaphalaPage (Yearly Progressed Chart & Tajika Analysis)
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QPushButton, QSizePolicy, QComboBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BG_TERTIARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
                        COLOR_ACCENT, BG_PRIMARY)
from gui.utils.planet_colors import rashi_name, planet_full_name

ANALYSIS_TITLE = {
    "marriage":  {"ne": "💍 विवाह तथा वैवाहिक जीवन विश्लेषण", "en": "💍 Marriage & Relationship Analysis"},
    "career":    {"ne": "💼 करियर, पेशा तथा व्यापार विश्लेषण", "en": "💼 Career & Profession Analysis"},
    "health":    {"ne": "🩺 स्वास्थ्य तथा शारीरिक आरोग्य विश्लेषण", "en": "🩺 Health & Vitality Analysis"},
    "child":     {"ne": "👶 सन्तान, वंश तथा परिवार विश्लेषण", "en": "👶 Children & Family Analysis"},
    "education": {"ne": "📚 उच्च शिक्षा तथा बुद्धि विश्लेषण", "en": "📚 Education & Intellect Analysis"},
    "finance":   {"ne": "💰 आर्थिक, धन सम्पत्ति तथा समृद्धि", "en": "💰 Wealth, Finance & Property"},
}


class LifeAnalysisPage(QWidget):
    """Dynamic Life Analysis Report based on Houses, Planets & Yogas."""
    def __init__(self, data: Optional[dict], category: str = "marriage", language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._cat = category
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        if data:
            self.refresh(data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        info = ANALYSIS_TITLE.get(self._cat, {"ne": self._cat, "en": self._cat})
        title = QLabel(info["ne"] if self._is_ne else info["en"])
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 17px; font-weight: 700;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll, 1)

        container = QWidget()
        self._c_layout = QVBoxLayout(container)
        self._c_layout.setContentsMargins(0, 0, 0, 0)
        self._c_layout.setSpacing(14)
        scroll.setWidget(container)

    def refresh(self, data: dict):
        self._data = data
        while self._c_layout.count():
            item = self._c_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            no_data = QLabel(
                "कुण्डली गणना नभएकाले विश्लेषण उपलब्ध छैन।" if self._is_ne
                else "No chart data available. Calculate a chart first.")
            no_data.setWordWrap(True)
            no_data.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 16px; padding: 24px;")
            no_data.setAlignment(Qt.AlignCenter)
            self._c_layout.addWidget(no_data)
            return

        # Route to the appropriate narrative engine based on category
        try:
            if self._cat == "career":
                from backend.calculator.career_narrative_engine import generate_career_narrative
                chapters = generate_career_narrative(data, self._lang)
            elif self._cat == "health":
                from backend.calculator.health_narrative_engine import generate_health_narrative
                chapters = generate_health_narrative(data, self._lang)
            elif self._cat == "education":
                from backend.calculator.education_narrative_engine import generate_education_narrative
                chapters = generate_education_narrative(data, self._lang)
            elif self._cat == "child":
                from backend.calculator.child_narrative_engine import generate_child_narrative
                chapters = generate_child_narrative(data, self._lang)
            elif self._cat == "finance":
                from backend.calculator.finance_narrative_engine import generate_finance_narrative
                chapters = generate_finance_narrative(data, self._lang)
            elif self._cat == "marriage":
                from backend.calculator.marriage_narrative_engine import generate_marriage_narrative
                chapters = generate_marriage_narrative(data, self._lang)
            else:
                chapters = []
        except ImportError:
            try:
                import importlib
                mod_name = f"calculator.{self._cat}_narrative_engine"
                fn_name  = f"generate_{self._cat}_narrative"
                mod = importlib.import_module(mod_name)
                chapters = getattr(mod, fn_name)(data, self._lang)
            except Exception:
                chapters = []

        if not chapters:
            # Fallback: show key planets relevant to this category
            lagna = data.get("lagna", {})
            lagna_sign = rashi_name(lagna.get("sign_number", 1), self._lang)
            planets = data.get("planets", [])
            cat_planets = {
                "marriage":  ["Venus", "Jupiter", "Mars"],
                "career":    ["Sun", "Saturn", "Mars", "Jupiter"],
                "health":    ["Sun", "Moon", "Mars", "Saturn"],
                "child":     ["Jupiter", "Moon", "Mars"],
                "education": ["Mercury", "Jupiter", "Moon"],
                "finance":   ["Jupiter", "Venus", "Mercury"],
            }.get(self._cat, [])

            info = ANALYSIS_TITLE.get(self._cat, {})
            h = QLabel(info.get("ne" if self._is_ne else "en", self._cat))
            h.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 20px; font-weight: 700; padding-bottom: 8px;")
            h.setWordWrap(True)
            self._c_layout.addWidget(h)

            for p in planets:
                if p.get("name") not in cat_planets:
                    continue
                pname = planet_full_name(p.get("name", ""), self._lang)
                sign  = rashi_name(p.get("sign_number", 1), self._lang)
                house = p.get("house", "—")
                exalt = str(p.get("exaltation_state", "")).lower()
                exalt_label = ("उच्च ✓" if exalt == "exalted" else
                               "नीच ✗" if exalt == "debilitated" else "")
                retro = "वक्री ℞" if p.get("is_retrograde") else ""
                tags  = "  ".join(t for t in [exalt_label, retro] if t)

                row = QLabel(
                    f"<b>{pname}</b>: {sign} राशि, {house} भाव"
                    + (f"  <span style='color:#f59e0b'>{tags}</span>" if tags else "")
                )
                row.setTextFormat(Qt.RichText)
                row.setWordWrap(True)
                row.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; padding: 4px 0;")
                self._c_layout.addWidget(row)
            self._c_layout.addStretch()
            return

        # Render narrative chapters directly (no card/box wrapping)
        from gui.widgets.analysis_document import add_chapter
        for ch in chapters:
            add_chapter(self._c_layout, ch.get("title", ""), ch.get("content", ""), "lifeAn")
        self._c_layout.addStretch()


class DashaPhalPage(QWidget):
    """Interactive five-level dasha report shared by supported systems."""

    LEVELS = {
        1: ("महादशा", "Mahadasha"),
        2: ("अन्तर्दशा", "Antardasha"),
        3: ("प्रत्यन्तरदशा", "Pratyantardasha"),
        4: ("सूक्ष्मदशा", "Sookshmadasha"),
        5: ("प्राणदशा", "Pranadasha"),
    }
    PLANET_NE = {
        "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
        "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु",
    }
    SIGNIFICATION = {
        "Sun": ("अधिकार, पिता, प्रतिष्ठा र नेतृत्व", "authority, father, recognition and leadership"),
        "Moon": ("मन, माता, जनसम्पर्क र यात्रा", "mind, mother, public life and travel"),
        "Mars": ("साहस, भूमि, भाइ र प्रतिस्पर्धा", "courage, land, siblings and competition"),
        "Mercury": ("शिक्षा, व्यापार, वाणी र बुद्धि", "education, trade, speech and intellect"),
        "Jupiter": ("ज्ञान, गुरु, धर्म, सन्तान र धन", "wisdom, guru, dharma, children and wealth"),
        "Venus": ("विवाह, कला, सवारी र सुख-सुविधा", "marriage, arts, vehicles and comforts"),
        "Saturn": ("कर्म, अनुशासन, आयु र दीर्घ परिश्रम", "karma, discipline, longevity and sustained effort"),
        "Rahu": ("विदेश, प्रविधि, महत्त्वाकांक्षा र अचानक घटना", "foreign matters, technology, ambition and sudden events"),
        "Ketu": ("आध्यात्म, वैराग्य, गुप्त विद्या र रूपान्तरण", "spirituality, detachment, occult knowledge and transformation"),
    }
    FRIENDS = {
        "Sun": {"Moon", "Mars", "Jupiter"}, "Moon": {"Sun", "Mercury"},
        "Mars": {"Sun", "Moon", "Jupiter"}, "Mercury": {"Sun", "Venus"},
        "Jupiter": {"Sun", "Moon", "Mars"}, "Venus": {"Mercury", "Saturn"},
        "Saturn": {"Mercury", "Venus"}, "Rahu": {"Mercury", "Venus", "Saturn"},
        "Ketu": {"Mercury", "Venus", "Saturn"},
    }
    ENEMIES = {
        "Sun": {"Venus", "Saturn"}, "Moon": set(), "Mars": {"Mercury"},
        "Mercury": {"Moon"}, "Jupiter": {"Mercury", "Venus"}, "Venus": {"Sun", "Moon"},
        "Saturn": {"Sun", "Moon", "Mars"}, "Rahu": {"Sun", "Moon", "Mars"},
        "Ketu": {"Sun", "Moon", "Mars"},
    }

    def __init__(self, data: Optional[dict], language: str = "ne", system: str = "vimshottari", parent=None):
        super().__init__(parent)
        self._data = data or {}
        self._center_generation = 0
        self._lang = language
        self._system = system
        self._is_ne = language == "ne"
        self._level = 2
        self._selected = None
        self._period_buttons = []
        # The Yogini five-level tree is huge (level 5 alone can exceed 11k
        # periods), so the timeline is rendered in fixed-size windows. Each
        # window builds at most TIMELINE_PAGE_SIZE QPushButtons, keeping any
        # single render pass a few hundred milliseconds instead of freezing
        # the UI for many seconds (regression: switching Yogini levels hung).
        self._timeline_page_size = 500
        self._timeline_start = None  # None => auto-center window on selection
        self._selected_button = None
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink_active_selection)
        self._blink_count = 0
        self._blink_on = False
        self._pending_level = None
        self._render_scheduled = False
        self._rendering = False
        self._level_render_timer = QTimer(self)
        self._level_render_timer.setSingleShot(True)
        self._level_render_timer.setInterval(50)
        self._level_render_timer.timeout.connect(self._apply_pending_level)
        self._build_ui()
        if data:
            self.refresh(data)

    @staticmethod
    def flatten_periods(nodes, level, parents=None, output=None):
        parents = list(parents or [])
        output = output if output is not None else []
        for node in nodes or []:
            path = parents + [node]
            if int(node.get("level", len(path))) == level:
                output.append((node, path))
            DashaPhalPage.flatten_periods(node.get("children") or [], level, path, output)
        return output

    @staticmethod
    def active_path(nodes, path=None):
        for node in nodes or []:
            current = list(path or []) + [node]
            deeper = DashaPhalPage.active_path(node.get("children") or [], current)
            if deeper:
                return deeper
            if node.get("is_active"):
                return current
        return []

    def _nodes(self):
        # All supported systems use the normalized five-level report tree. Keep
        # the legacy Vimshottari/Yogini fields only as compatibility fallbacks.
        report = (self._data.get("dasha_reports") or {}).get(self._system) or {}
        if report.get("status") == "ready" and report.get("periods"):
            return report["periods"]
        if self._system == "vimshottari":
            return self._data.get("dasha", []) or []
        if self._system == "ashtottari":
            return self._data.get("ashtottari_dasha", []) or []
        if self._system == "yogini":
            legacy = self._data.get("yogini_dasha_five_level") or self._data.get("yogini_dasha") or []
            return legacy
        return report.get("periods", []) or []

    def _system_title(self):
        labels = {
            "vimshottari": ("विंशोत्तरी दशा फलादेश", "Vimshottari Dasha Phal"),
            "tribhagi": ("त्रिभागी दशा फलादेश", "Tribhagi Dasha Phal"),
            "ashtottari": ("अष्टोत्तरी दशा फलादेश", "Ashtottari Dasha Phal"),
            "yogini": ("योगिनी दशा फलादेश", "Yogini Dasha Phal"),
        }
        return labels.get(self._system, labels["vimshottari"])[0 if self._is_ne else 1]

    def _name(self, node):
        if self._system == "yogini":
            if self._is_ne:
                return (
                    node.get("yogini_nepali")
                    or node.get("lord_nepali")
                    or node.get("nepali")
                    or node.get("yogini")
                    or node.get("lord")
                    or node.get("name")
                    or "—"
                )
            return node.get("yogini") or node.get("lord") or node.get("name") or "—"
        lord = node.get("lord", "—")
        return node.get("lord_nepali") or self.PLANET_NE.get(lord, lord) if self._is_ne else lord

    def _dates(self, node):
        start = node.get("start_bs") or str(node.get("start", ""))[:10] or "—"
        end = node.get("end_bs") or str(node.get("end", ""))[:10] or "—"
        if self._is_ne:
            from gui.utils.planet_colors import to_nepali_digits
            return f"{to_nepali_digits(start)} – {to_nepali_digits(end)}"
        return f"{start} – {end}"

    def _path_text(self, path):
        return " → ".join(self._name(node) for node in path)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        header = QHBoxLayout()
        header.setSpacing(12)
        self._title = QLabel("🔮 " + self._system_title())
        self._title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 17px; font-weight: 700;")
        header.addWidget(self._title, 0, Qt.AlignVCenter)
        self._levels = QHBoxLayout()
        self._levels.setSpacing(6)
        header.addLayout(self._levels)
        header.addStretch(1)
        layout.addLayout(header)
        splitter = QHBoxLayout()
        splitter.setSpacing(10)
        layout.addLayout(splitter, 1)
        self._timeline_scroll = QScrollArea()
        self._timeline_scroll.setWidgetResizable(True)
        self._timeline_scroll.setMinimumWidth(285)
        self._timeline_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._timeline = QWidget()
        self._timeline_layout = QVBoxLayout(self._timeline)
        self._timeline_layout.setContentsMargins(0, 0, 0, 0)
        self._timeline_layout.setSpacing(6)
        self._timeline_scroll.setWidget(self._timeline)
        timeline_column = QVBoxLayout()
        timeline_column.setSpacing(6)
        timeline_column.addWidget(self._timeline_scroll, 1)
        # Always-visible pagination row (rendered only when the timeline is
        # windowed, i.e. more than _timeline_page_size periods).
        self._timeline_footer = QHBoxLayout()
        self._timeline_footer.setSpacing(6)
        timeline_column.addLayout(self._timeline_footer)
        splitter.addLayout(timeline_column, 1)
        self._result_scroll = QScrollArea()
        self._result_scroll.setWidgetResizable(True)
        self._result_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._result = QWidget()
        self._result_layout = QVBoxLayout(self._result)
        self._result_layout.setContentsMargins(0, 0, 0, 0)
        self._result_layout.setSpacing(10)
        self._result_scroll.setWidget(self._result)
        splitter.addWidget(self._result_scroll, 2)
        for level, labels in self.LEVELS.items():
            button = QPushButton(labels[0] if self._is_ne else labels[1])
            button.setCheckable(True)
            button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            button.setMinimumHeight(30)
            button.setContentsMargins(0, 0, 0, 0)
            button.setStyleSheet(
                f"QPushButton {{ padding: 4px 7px; font-size: 12px; "
                f"color: {COLOR_TEXT_PRIMARY}; background: {BG_SECONDARY}; "
                f"border: 1px solid {BORDER_COLOR}; border-radius: 6px; }} "
                f"QPushButton:checked {{ color: #052e16; background: #86efac; "
                f"border: 2px solid #166534; }} "
                f"QPushButton:hover {{ border-color: {COLOR_GOLD}; }}"
            )
            button.clicked.connect(lambda checked=False, value=level: self._set_level(value))
            self._levels.addWidget(button)
            setattr(self, f"_level_button_{level}", button)
        self._levels.addStretch(1)

    def _set_level(self, level):
        self._pending_level = level
        self._render_scheduled = True
        # A short debounce lets a burst of level clicks settle before any
        # expensive timeline/result rebuild starts. Only the final level wins.
        self._level_render_timer.start()

    def _apply_pending_level(self):
        if self._rendering:
            self._level_render_timer.start()
            return
        level = self._pending_level
        self._pending_level = None
        self._render_scheduled = False
        if level is None:
            return
        self._rendering = True
        try:
            self._blink_timer.stop()
            self._level = level
            for number in self.LEVELS:
                getattr(self, f"_level_button_{number}").setChecked(number == level)
            nodes = self._nodes()
            choices = self.flatten_periods(nodes, self._level)
            active = self._active_path(nodes)
            self._selected = next(
                ((node, path) for node, path in choices if node in active),
                next(
                    ((node, path) for node, path in choices if self._is_node_active(node)),
                    choices[0] if choices else None,
                ),
            )
            # Start each level pass from a fresh window centered on the active
            # period; a stale pagination offset must not hide the selection.
            self._timeline_start = None
            self._render_timeline()
            self._render_result()
            self._focus_selected_period(blink=True)
        finally:
            self._rendering = False
            # A click may arrive while the rebuild was in progress. Schedule
            # that newest selection after the current pass completes.
            if self._pending_level is not None:
                self._render_scheduled = True
                self._level_render_timer.start()

    def _select(self, item):
        self._blink_timer.stop()
        self._selected = item
        self._render_timeline()
        self._render_result()
        self._focus_selected_period(blink=True)

    def _focus_selected_period(self, blink=True):
        button = self._selected_button
        if button is None:
            return
        self._center(button)
        if blink and self._is_node_active(self._selected[0]):
            self._blink_count = 0
            self._blink_on = True
            self._blink_timer.start(180)

    def _blink_active_selection(self):
        button = self._selected_button
        if button is None or not self._selected or not self._is_node_active(self._selected[0]):
            self._blink_timer.stop()
            return
        self._blink_on = not self._blink_on
        self._blink_count += 1
        self._apply_period_style(button, active=True, blink=self._blink_on)
        if self._blink_count >= 6:
            self._blink_timer.stop()
            self._blink_on = False
            self._apply_period_style(button, active=True, blink=False)

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
                continue
            sub = item.layout()
            if sub is not None:
                self._clear(sub)

    def _center(self, button):
        if not button:
            return

        self._center_generation += 1
        generation = self._center_generation

        def center_button():
            if (
                generation != self._center_generation
                or not button
                or not button.parentWidget()
                or not self.isVisible()
                or not self._timeline_scroll.isVisible()
            ):
                return
            self._timeline_layout.activate()
            self._timeline.adjustSize()
            viewport_height = self._timeline_scroll.viewport().height()
            scrollbar = self._timeline_scroll.verticalScrollBar()
            if viewport_height <= 0:
                QTimer.singleShot(80, center_button)
                return
            if scrollbar.maximum() <= 0:
                return
            target = button.y() - max(0, (viewport_height - button.height()) // 2)
            scrollbar.setValue(max(0, min(target, scrollbar.maximum())))

        for delay in (0, 80, 200, 400, 800):
            QTimer.singleShot(delay, center_button)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, lambda: self._focus_selected_period(blink=False))
        QTimer.singleShot(120, lambda: self._focus_selected_period(blink=False))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._selected_button is not None:
            QTimer.singleShot(0, lambda: self._focus_selected_period(blink=False))

    def _apply_period_style(self, button, active=False, blink=False):
        if active:
            border_color = "#166534" if not blink else "#15803d"
            background = "#86efac" if not blink else "#4ade80"
            text_color = "#052e16"
            border = f"2px solid {border_color}"
            padding = "9px"
            radius = "8px"
        else:
            # Selection is communicated by the result panel; the timeline stays
            # a plain list so an inactive selection cannot resemble an active row.
            background = "transparent"
            text_color = COLOR_TEXT_PRIMARY
            border = "none"
            padding = "9px 4px"
            radius = "0px"
        button.setStyleSheet(
            f"QPushButton {{ text-align: left; padding: {padding}; color: {text_color}; "
            f"background: {background}; border: {border}; border-radius: {radius}; }} "
            f"QPushButton:hover {{ color: {COLOR_GOLD}; }}"
        )

    def _md_header(self, md):
        """Group the flattened sub-periods under their Mahadasha.

        Mirrors the web timeline's Mahadasha group headers. Without a visible
        boundary, Antardashas from all Mahadashas run into one flat list and
        each Mahadasha boundary looks like a missing planet/yogini (e.g. a
        Bhadrika Mahadasha ending with भ्रामरी followed by an Ulka Mahadasha
        starting with उल्का reads as "भ्रामरी → उल्का, भद्रिका छैन")."""
        if md is None:
            return QLabel()
        label = self._name(md)
        dates = self._dates(md)
        md_label = self.LEVELS[1][0 if self._is_ne else 1]
        active = self._is_node_active(md)
        text = f"{label} · {md_label} · {dates}" + (" ●" if active else "")
        header = QLabel(text)
        header.setWordWrap(True)
        if active:
            header.setStyleSheet(
                "color: #166534; background: #86efac; font-weight: 800; font-size: 13px;"
                "border: 1px solid #166534; border-radius: 6px; padding: 6px 8px; margin-top: 8px;"
            )
        else:
            header.setStyleSheet(
                f"color: {COLOR_GOLD}; background: {BG_SECONDARY}; font-weight: 700; font-size: 12px;"
                f"border-left: 3px solid {COLOR_GOLD}; border-radius: 3px; padding: 4px 8px; margin-top: 8px;"
            )
        return header

    def _render_timeline(self):
        self._blink_timer.stop()
        self._clear(self._timeline_layout)
        self._period_buttons = []
        self._selected_button = None
        choices = self.flatten_periods(self._nodes(), self._level)
        total = len(choices)
        page = self._timeline_page_size
        # Windowed rendering: at most `page` buttons are built per pass. The
        # Yogini five-level tree can flatten to ~9k-12k periods (levels 4-5);
        # materializing all of them as QPushButtons froze the UI for seconds,
        # so only the window around the selection is ever created.
        start = self._timeline_start
        if start is None:
            start = self._auto_window_start(choices, page)
        if start is None:
            start = 0
        if start < 0 or start >= total:
            start = 0
        # Persist the displayed window so prev/next pagination continues from
        # it; a fresh level pass resets _timeline_start to None beforehand.
        self._timeline_start = start
        end = min(start + page, total)
        previous_md = None
        for index in range(start, end):
            node, path = choices[index]
            if self._level > 1 and path:
                parent_md = path[0]
                if parent_md is not previous_md:
                    self._timeline_layout.addWidget(self._md_header(parent_md))
                    previous_md = parent_md
            button = QPushButton()
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            text = f"{self._path_text(path)}\n{self._dates(node)}"
            if self._is_node_active(node):
                text += "\n● " + ("हाल सक्रिय" if self._is_ne else "ACTIVE")
            button.setText(text)
            button.setMinimumHeight(58)
            selected = bool(self._selected and self._selected[0] is node)
            if selected:
                self._selected_button = button
            self._apply_period_style(button, active=self._is_node_active(node), blink=False)
            button.clicked.connect(lambda checked=False, choice=(node, path): self._select(choice))
            self._timeline_layout.addWidget(button)
            self._period_buttons.append(button)
        self._timeline_layout.addStretch(1)
        self._add_page_controls(start, end, total)
        self._timeline_layout.activate()
        self._timeline.adjustSize()
        self._center(self._selected_button)

    def _auto_window_start(self, choices, page_size):
        """Offset of the window that centers the selected/active period.

        Returns None when the whole list already fits one page so the caller
        can render everything without pagination."""
        total = len(choices)
        if total <= page_size:
            return None
        target = 0
        if self._selected:
            for index, (node, _path) in enumerate(choices):
                if node is self._selected[0]:
                    target = index
                    break
        half = page_size // 2
        return max(0, min(target - half, total - page_size))

    def _add_page_controls(self, start, end, total):
        """Always-visible pagination row below the timeline scroll area."""
        self._clear(self._timeline_footer)
        if total <= self._timeline_page_size:
            return
        prev = QPushButton("◀ " + ("अघिल्लो" if self._is_ne else "Prev"))
        next = QPushButton(("अर्को" if self._is_ne else "Next") + " ▶")
        for button in (prev, next):
            button.setStyleSheet(
                f"QPushButton {{ padding: 4px 10px; font-size: 12px; "
                f"color: {COLOR_TEXT_PRIMARY}; background: {BG_SECONDARY}; "
                f"border: 1px solid {BORDER_COLOR}; border-radius: 6px; }} "
                f"QPushButton:hover {{ color: {COLOR_GOLD}; border-color: {COLOR_GOLD}; }}"
            )
        label = QLabel(f"{start + 1}–{end} / {total}")
        label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        self._timeline_footer.addWidget(prev)
        self._timeline_footer.addWidget(label)
        self._timeline_footer.addWidget(next)
        self._timeline_footer.addStretch(1)
        prev.clicked.connect(lambda: self._jump_page(-self._timeline_page_size))
        next.clicked.connect(lambda: self._jump_page(self._timeline_page_size))

    def _jump_page(self, delta):
        total = len(self.flatten_periods(self._nodes(), self._level))
        page = self._timeline_page_size
        if total <= page:
            self._timeline_start = None
            self._render_timeline()
            return
        current = self._timeline_start if self._timeline_start is not None else 0
        self._timeline_start = max(0, min(current + delta, total - page))
        self._render_timeline()

    def _active_path(self, nodes, path=None):
        """Return the deepest date-active path, never trusting stale flags."""
        for node in nodes or []:
            current = list(path or []) + [node]
            if not self._is_node_active(node):
                continue
            deeper = self._active_path(node.get("children") or [], current)
            return deeper or current
        return []

    def _is_node_active(self, node):
        # Date ranges are authoritative. Some legacy/derived Tribhagi payloads
        # carry a stale is_active flag on the birth-period node.
        from datetime import date
        try:
            start = date.fromisoformat(str(node.get("start", ""))[:10])
            end = date.fromisoformat(str(node.get("end", ""))[:10])
            return start <= date.today() < end
        except (TypeError, ValueError):
            return node.get("is_active") is True

    def _planet_lord(self, node):
        if self._system != "yogini":
            return node.get("lord", "")
        return node.get("planet_lord") or {
            "Mangala": "Moon", "Pingala": "Sun", "Dhanya": "Jupiter",
            "Bhramari": "Mars", "Bhadrika": "Mercury", "Ulka": "Saturn",
            "Siddha": "Venus", "Sankata": "Rahu",
        }.get(node.get("name") or node.get("lord"), "")

    def _score(self, lord):
        lord = self._planet_lord({"lord": lord, "name": lord}) if self._system == "yogini" else lord
        planet = next((p for p in self._data.get("planets", []) if p.get("name") == lord), {})
        score = 50
        house = int(planet.get("house") or 0)
        if house in (1, 4, 5, 7, 9, 10): score += 14
        elif house in (6, 8, 12): score -= 14
        if str(planet.get("exaltation_state", "")).lower() == "exalted": score += 18
        if str(planet.get("exaltation_state", "")).lower() in ("debilitated", "debilitated (neecha)"): score -= 18
        if planet.get("is_combust"): score -= 8
        if planet.get("is_retrograde"): score -= 3
        return max(5, min(95, score))

    def _render_result(self):
        self._clear(self._result_layout)
        if not self._selected:
            lbl = QLabel("दशा छान्नुहोस् — बायाँतर्फको सूचीबाट एउटा दशा अवधिमा क्लिक गर्नुहोस्।"
                         if self._is_ne else
                         "Select a dasha period from the list on the left.")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 16px; padding: 24px;")
            lbl.setAlignment(Qt.AlignCenter)
            self._result_layout.addWidget(lbl)
            return

        node, path = self._selected
        lord = self._planet_lord(node)
        label = self._name(node)
        score = self._score(lord)
        level_label = self.LEVELS[self._level][0 if self._is_ne else 1]
        active = self._is_node_active(node)

        # -- Title ----------------------------------------------------------
        prefix = "● हाल सक्रिय" if active and self._is_ne else ("● Active" if active else
                  ("चयनित" if self._is_ne else "Selected"))
        title = QLabel(f"{prefix}  {level_label} फलादेश — {self._path_text(path)}"
                       if self._is_ne else
                       f"{prefix}  {level_label} Reading — {self._path_text(path)}")
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {'#22c55e' if active else COLOR_GOLD}; "
            f"font-size: 20px; font-weight: 700; padding-bottom: 4px;")
        self._result_layout.addWidget(title)

        # -- Period dates ---------------------------------------------------
        dates_lbl = QLabel(
            f"अवधि: {self._dates(node)}" if self._is_ne else f"Period: {self._dates(node)}")
        dates_lbl.setStyleSheet(
            f"color: {'#22c55e' if active else COLOR_TEXT_SECONDARY}; "
            f"font-size: 16px; font-weight: 600; padding-bottom: 2px;")
        self._result_layout.addWidget(dates_lbl)

        # -- Score bar ------------------------------------------------------
        score_lbl = QLabel(
            f"शुभता: {score}%   अशुभता: {100 - score}%"
            if self._is_ne else f"Auspicious: {score}%   Inauspicious: {100 - score}%")
        score_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        self._result_layout.addWidget(score_lbl)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(score)
        bar.setTextVisible(False)
        bar.setFixedHeight(14)
        green = "#22c55e" if score >= 60 else ("#f59e0b" if score >= 40 else "#ef4444")
        bar.setStyleSheet(
            f"QProgressBar {{ background: #e2e8f0; border: none; border-radius: 7px; }}"
            f"QProgressBar::chunk {{ background: {green}; border-radius: 7px; }}")
        self._result_layout.addWidget(bar)

        # ── Actual natal planet details from live data ──────────────────────
        planet_data = next(
            (p for p in self._data.get("planets", []) if p.get("name") == lord), {})
        planet_sign_no = planet_data.get("sign_number")
        planet_house   = planet_data.get("house", "—")
        exalt_state    = str(planet_data.get("exaltation_state", "")).lower()
        is_retro       = bool(planet_data.get("is_retrograde"))
        is_combust     = bool(planet_data.get("is_combust"))
        is_vargo       = bool(planet_data.get("is_vargottama"))
        relationship   = str(planet_data.get("relationship", "")).lower()
        nakshatra      = planet_data.get("nakshatra_nepali") or planet_data.get("nakshatra_name", "—")

        # Sign name
        from gui.utils.planet_colors import rashi_name as _rashi
        sign_name = _rashi(planet_sign_no, self._lang) if planet_sign_no else "—"

        # Conjunctions: planets in same house
        conjoined = [
            p.get("name") for p in self._data.get("planets", [])
            if p.get("house") == planet_house
            and p.get("name") != lord
            and p.get("name")
        ]
        conj_text = (", ".join(
            self.PLANET_NE.get(p, p) for p in conjoined
        ) if self._is_ne else ", ".join(conjoined)) if conjoined else ("—" if self._is_ne else "—")

        # Dignity flags
        dignity_parts = []
        if exalt_state == "exalted":
            dignity_parts.append("उच्च ✓" if self._is_ne else "Exalted ✓")
        elif exalt_state == "debilitated":
            dignity_parts.append("नीच ✗" if self._is_ne else "Debilitated ✗")
        if relationship in ("own", "swakshetra"):
            dignity_parts.append("स्वराशि" if self._is_ne else "Own sign")
        elif relationship == "friend":
            dignity_parts.append("मित्र राशि" if self._is_ne else "Friendly sign")
        elif relationship == "enemy":
            dignity_parts.append("शत्रु राशि" if self._is_ne else "Enemy sign")
        if is_vargo:
            dignity_parts.append("वर्गोत्तम ✨" if self._is_ne else "Vargottama ✨")
        if is_retro:
            dignity_parts.append("वक्री ℞" if self._is_ne else "Retrograde ℞")
        if is_combust:
            dignity_parts.append("अस्त ☌" if self._is_ne else "Combust ☌")
        dignity_str = "  |  ".join(dignity_parts) if dignity_parts else ("सामान्य" if self._is_ne else "Normal")

        ne_sig, en_sig = self.SIGNIFICATION.get(lord, ("जीवनका विषयहरू", "life themes"))

        # ── BPHS Analysis Sections ─────────────────────────────────────────
        sep_style = (f"border: none; border-top: 1px solid #e2e8f0; "
                     f"margin: 8px 0 4px 0; max-height: 1px; background: #e2e8f0;")

        def add_sep():
            f = QFrame(); f.setFrameShape(QFrame.HLine)
            f.setStyleSheet(sep_style)
            self._result_layout.addWidget(f)

        def add_h(text, color=None):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"color: {color or COLOR_GOLD}; font-size: 17px; font-weight: 700; "
                f"border-left: 5px solid {color or COLOR_GOLD}; padding: 6px 0 4px 12px;")
            self._result_layout.addWidget(lbl)

        def add_p(text, bold=False, color=None):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"color: {color or COLOR_TEXT_PRIMARY}; font-size: 16px; "
                f"font-weight: {'700' if bold else '400'}; line-height: 1.7; padding: 2px 0 4px 0;")
            self._result_layout.addWidget(lbl)

        add_sep()

        # 1. ग्रह जन्म स्थिति
        add_h("🪐 " + ("ग्रह जन्म स्थिति (Natal Placement)" if self._is_ne else "Natal Planet Placement"))
        if self._is_ne:
            add_p(f"• {label} जन्मकुण्डलीको {planet_house} औं भाव, {sign_name} राशिमा रहेको छ।", bold=True)
            add_p(f"• नक्षत्र: {nakshatra}")
            add_p(f"• ग्रह अवस्था: {dignity_str}", bold=True)
            add_p(f"• यस भावमा युति ग्रह: {conj_text}")
            add_p(f"• BPHS कारकत्व: {ne_sig}")
        else:
            add_p(f"• {label} is placed in house {planet_house} in {sign_name}.", bold=True)
            add_p(f"• Nakshatra: {nakshatra}")
            add_p(f"• Planet condition: {dignity_str}", bold=True)
            add_p(f"• Conjunctions in same house: {conj_text}")
            add_p(f"• BPHS significations: {en_sig}")

        add_sep()

        # 2. दशाफल विश्लेषण
        add_h("📊 " + ("दशाफल विश्लेषण (Dasha Phal Analysis)" if self._is_ne else "Dasha Phal Analysis"))
        phal_conclusion = (
            "अत्यन्त शुभ समय — उन्नति, सफलता र अवसरको काल।" if score >= 75 else
            "शुभ समय — सावधानीपूर्वक सदुपयोग गर्दा राम्रो फल।" if score >= 55 else
            "मिश्रित समय — चुनौती र अवसर दुवै सम्भव, सतर्कता आवश्यक।" if score >= 40 else
            "कठिन समय — सावधानी, उपाय र आध्यात्मिक अभ्यास आवश्यक।"
        ) if self._is_ne else (
            "Highly auspicious period — progress, success and opportunity." if score >= 75 else
            "Auspicious period — good results with careful use of opportunities." if score >= 55 else
            "Mixed period — both challenges and opportunities possible, stay alert." if score >= 40 else
            "Challenging period — exercise caution and maintain spiritual practice."
        )
        add_p(phal_conclusion, bold=True,
              color=("#16a34a" if score >= 55 else "#f59e0b" if score >= 40 else "#dc2626"))

        if self._is_ne:
            # Exaltation effect
            if exalt_state == "exalted":
                add_p(f"• {label} उच्च राशिमा हुनाले यस दशामा विशेष बल र उन्नति मिल्छ।")
            elif exalt_state == "debilitated":
                add_p(f"• {label} नीच राशिमा हुनाले दशाको पूर्ण फल पाउन चुनौती हुन सक्छ — उपाय महत्त्वपूर्ण।")
            if is_retro:
                add_p("• वक्री (Retrograde) ग्रहको दशामा परिणाम ढिलो आउन सक्छ, पुरानो कामहरू पुनः सक्रिय हुन्छन्।")
            if is_combust:
                add_p("• अस्त (Combust) ग्रहको दशामा ग्रहको पूर्ण क्षमता प्रकट हुन कठिन हुन्छ।")
            if is_vargo:
                add_p("• वर्गोत्तम ग्रहको दशामा प्राकृतिक बल सर्वोच्च हुन्छ — फल बलियो र स्थायी।")
            if conjoined:
                add_p(f"• {conj_text} सँगको युतिले दशाफलमा मिश्रित वा सुदृढ प्रभाव पर्दछ।")
        else:
            if exalt_state == "exalted":
                add_p(f"• {label} is exalted, granting extra strength and upliftment in this dasha.")
            elif exalt_state == "debilitated":
                add_p(f"• {label} is debilitated — full results may be delayed; remedies are important.")
            if is_retro:
                add_p("• Retrograde: results may be delayed; past matters resurface during this period.")
            if is_combust:
                add_p("• Combust: the planet's full expression may be suppressed by solar proximity.")
            if is_vargo:
                add_p("• Vargottama: maximum natural strength — results are strong and lasting.")
            if conjoined:
                add_p(f"• Conjunction with {conj_text} blends or modifies the dasha outcome.")

        add_sep()

        # 3. भाव फल
        add_h("🏠 " + (f"{planet_house} औं भाव फल" if self._is_ne else f"House {planet_house} Results"))
        _house_sig_ne = {
            1: "स्वास्थ्य, व्यक्तित्व, आत्मबल र समग्र जीवन दिशा",
            2: "धन, परिवार, वाणी र संचित सम्पत्ति",
            3: "साहस, भाइबहिनी, छोटो यात्रा र सञ्चार",
            4: "माता, भूमि, गृहसुख र शिक्षाको आधार",
            5: "सन्तान, बुद्धि, पूर्वजन्म पुण्य र सृजनात्मकता",
            6: "शत्रु, रोग, ऋण र प्रतिस्पर्धा",
            7: "विवाह, साझेदारी र व्यापारिक सम्बन्ध",
            8: "आयु, रहस्य, विरासत र अप्रत्याशित घटना",
            9: "धर्म, भाग्य, गुरु र दीर्घयात्रा",
            10: "करियर, यश, सामाजिक पद र अधिकार",
            11: "लाभ, आय, बडो भाइ र महत्त्वाकांक्षा पूर्ति",
            12: "व्यय, मोक्ष, विदेश र गुप्त विषय",
        }
        _house_sig_en = {
            1: "health, personality, self-expression and life direction",
            2: "wealth, family, speech and accumulated assets",
            3: "courage, siblings, short journeys and communication",
            4: "mother, land, domestic happiness and educational foundation",
            5: "children, intellect, past-life merit and creativity",
            6: "enemies, illness, debt and competition",
            7: "marriage, partnerships and business relationships",
            8: "longevity, secrets, inheritance and sudden events",
            9: "dharma, fortune, teachers and long journeys",
            10: "career, reputation, social standing and authority",
            11: "gains, income, elder siblings and fulfilment of ambitions",
            12: "expenditure, moksha, foreign matters and hidden issues",
        }
        h_num = int(planet_house) if str(planet_house).isdigit() else 0
        house_sig = _house_sig_ne.get(h_num, ne_sig) if self._is_ne else _house_sig_en.get(h_num, en_sig)
        if self._is_ne:
            add_p(f"• {label} {planet_house} भावको कारक — यस दशामा {house_sig} विषय सक्रिय हुन्छ।", bold=True)
            add_p(f"• {label} को प्राकृतिक कारकत्व: {ne_sig}")
        else:
            add_p(f"• {label} in house {planet_house} — activating {house_sig} during this period.", bold=True)
            add_p(f"• Natural significations: {en_sig}")

        add_sep()

        # 4. उपाय
        planet_mantras = {
            "Sun":     ("ॐ घृणि सूर्याय नमः", "Om Ghrini Suryaya Namah"),
            "Moon":    ("ॐ सों सोमाय नमः", "Om Som Somaya Namah"),
            "Mars":    ("ॐ अं अङ्गारकाय नमः", "Om Am Angarakaya Namah"),
            "Mercury": ("ॐ बुं बुधाय नमः", "Om Bum Budhaya Namah"),
            "Jupiter": ("ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः", "Om Gram Grim Graum Sah Gurave Namah"),
            "Venus":   ("ॐ द्रां द्रीं द्रौं सः शुक्राय नमः", "Om Dram Drim Draum Sah Shukraya Namah"),
            "Saturn":  ("ॐ शं शनैश्चराय नमः", "Om Sham Shanaishcharaya Namah"),
            "Rahu":    ("ॐ रां राहवे नमः", "Om Ram Rahave Namah"),
            "Ketu":    ("ॐ कें केतवे नमः", "Om Kem Ketave Namah"),
        }
        mantra_ne, mantra_en = planet_mantras.get(lord, ("ॐ नमः शिवाय", "Om Namah Shivaya"))
        add_h("🕉 " + ("शान्ति उपाय (BPHS अनुसार)" if self._is_ne else "Remedies (per BPHS)"),
              color="#16a34a")
        if self._is_ne:
            add_p(f"• मन्त्र: {mantra_ne}", bold=True, color="#16a34a")
            add_p(f"• दान: {label} सम्बन्धित वस्तु दान — बिहीबार/शनिबार/आइतबार (ग्रह अनुसार)।")
            add_p(f"• रत्न: ज्योतिषीको परामर्श लिएर {label} को रत्न धारण गर्न सकिन्छ।")
            add_p("• आचरण: सात्त्विक भोजन, नियमित पूजा र यस अवधिमा महत्त्वपूर्ण निर्णयमा सावधानी अपनाउनुहोस्।")
        else:
            add_p(f"• Mantra: {mantra_en}", bold=True, color="#16a34a")
            add_p(f"• Charity: Donate items associated with {label} on the appropriate day.")
            add_p(f"• Gemstone: Consult a Jyotishi for the suitable gemstone for {label}.")
            add_p("• Conduct: Follow a sattvic diet, maintain regular puja and exercise care in major decisions.")

        self._result_layout.addStretch(1)

    def _print_report(self):
        callback = getattr(self.window(), "_print_screen", None)
        if callable(callback):
            callback()

    def refresh(self, data: dict):
        self._data = data or {}
        choices = self.flatten_periods(self._nodes(), 2)
        self._level = 2 if choices else 1
        self._set_level(self._level)


class HoroscopePage(QWidget):
    """
    Comprehensive Daily Horoscope (दैनिक राशिफल) & Planetary Transit Forecast
    Covers all key life dimensions: Career, Finance, Health, Family/Love, Education,
    Travel, Challenges, and Daily Lucky Factors & Remedies.
    Supports date filtering by day / month / year with BS date selectors.
    """
    def __init__(self, data: Optional[dict], mode: str = "daily", language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        # Current filter state
        self._filter_mode = "day"  # "day" | "month" | "year"
        self._build_ui()
        if data:
            self.refresh(data)

    # ── Shared selector style: black text on white box ─────────────────────────
    _SELECTOR_STYLE = (
        "QComboBox {"
        "  background: #ffffff;"
        "  color: #000000;"
        "  border: 1px solid #cbd5e1;"
        "  border-radius: 5px;"
        "  padding: 2px 6px;"
        "  font-size: 12px;"
        "  font-weight: 600;"
        "  min-width: 68px;"
        "}"
        "QComboBox::drop-down { border: none; }"
        "QComboBox QAbstractItemView {"
        "  background: #ffffff;"
        "  color: #000000;"
        "  selection-background-color: #e0f2fe;"
        "  selection-color: #000000;"
        "}"
    )
    # ── High-contrast radio button style (स्पस्ट देखिने रेडियो बटन) ───────────────
    _RADIO_STYLE = (
        "QRadioButton {"
        "  color: #0f172a;"
        "  font-size: 13px;"
        "  font-weight: 800;"
        "  spacing: 8px;"
        "  padding: 3px 8px;"
        "  background: transparent;"
        "}"
        "QRadioButton:hover {"
        "  color: #1d4ed8;"
        "}"
        "QRadioButton::indicator {"
        "  width: 18px;"
        "  height: 18px;"
        "  border-radius: 9px;"
        "  border: 2px solid #475569;"
        "  background-color: #ffffff;"
        "}"
        "QRadioButton::indicator:hover {"
        "  border-color: #1d4ed8;"
        "}"
        "QRadioButton::indicator:checked {"
        "  border: 5px solid #1d4ed8;"
        "  background-color: #ffffff;"
        "}"
    )

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 16)
        main_layout.setSpacing(8)

        # Plain white background
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(pal)

        # ── Header row ──────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(8)

        # Title
        title_lbl = QLabel("☀ " + ("दैनिक राशिफल" if self._is_ne else "Daily Horoscope"))
        title_lbl.setStyleSheet("color: #000000; font-size: 22px; font-weight: 800;")
        header.addWidget(title_lbl)
        header.addStretch(1)

        # ── Radio buttons in a clear, high-contrast container: दिन | महिना | वर्ष ──
        radio_box = QFrame()
        radio_box.setStyleSheet(
            "QFrame {"
            "  background-color: #f1f5f9;"
            "  border: 1.5px solid #cbd5e1;"
            "  border-radius: 8px;"
            "}"
        )
        radio_layout = QHBoxLayout(radio_box)
        radio_layout.setContentsMargins(8, 2, 8, 2)
        radio_layout.setSpacing(12)

        self._radio_day   = QRadioButton("दिन"   if self._is_ne else "Day")
        self._radio_month = QRadioButton("महिना" if self._is_ne else "Month")
        self._radio_year  = QRadioButton("वर्ष"  if self._is_ne else "Year")

        self._mode_group = QButtonGroup(self)
        for idx, rb in enumerate([self._radio_day, self._radio_month, self._radio_year]):
            rb.setStyleSheet(self._RADIO_STYLE)
            rb.setCursor(Qt.PointingHandCursor)
            self._mode_group.addButton(rb, idx)
            radio_layout.addWidget(rb)

        self._radio_day.setChecked(True)  # default: day
        header.addWidget(radio_box)

        # Separator
        sep = QLabel("│")
        sep.setStyleSheet("color: #cbd5e1; font-size: 14px; padding: 0 2px;")
        header.addWidget(sep)

        # ── BS Year selector ──
        self._lbl_year = QLabel("वर्ष" if self._is_ne else "Year")
        self._lbl_year.setStyleSheet("color: #000000; font-size: 11px; font-weight: 600;")
        header.addWidget(self._lbl_year)
        self._year_combo = QComboBox()
        self._year_combo.setStyleSheet(self._SELECTOR_STYLE)
        self._populate_year_combo()
        header.addWidget(self._year_combo)

        # ── BS Month selector ──
        self._lbl_month = QLabel("महिना" if self._is_ne else "Month")
        self._lbl_month.setStyleSheet("color: #000000; font-size: 11px; font-weight: 600;")
        header.addWidget(self._lbl_month)
        self._month_combo = QComboBox()
        self._month_combo.setStyleSheet(self._SELECTOR_STYLE)
        from gui.utils.bs_calendar import BS_MONTHS_NE, BS_MONTHS_EN
        _months = BS_MONTHS_NE if self._is_ne else BS_MONTHS_EN
        for idx, mn in enumerate(_months, 1):
            self._month_combo.addItem(mn, idx)
        header.addWidget(self._month_combo)

        # ── गते (Day) selector ──
        self._lbl_day = QLabel("गते" if self._is_ne else "Day")
        self._lbl_day.setStyleSheet("color: #000000; font-size: 11px; font-weight: 600;")
        header.addWidget(self._lbl_day)
        self._day_combo = QComboBox()
        self._day_combo.setStyleSheet(self._SELECTOR_STYLE)
        from gui.utils.bs_calendar import to_nepali_digits as _tnd2
        for d in range(1, 32):
            self._day_combo.addItem(_tnd2(d) if self._is_ne else str(d), d)
        header.addWidget(self._day_combo)

        # ── Run button ──
        self._run_btn = QPushButton("हेर्नुहोस" if self._is_ne else "View")
        self._run_btn.setFixedHeight(28)
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.setStyleSheet(
            "QPushButton {"
            "  background: #1d4ed8;"
            "  color: #ffffff;"
            "  border: none;"
            "  border-radius: 6px;"
            "  font-size: 12px;"
            "  font-weight: 800;"
            "  padding: 2px 14px;"
            "}"
            "QPushButton:hover {"
            "  background: #1e40af;"
            "}"
        )
        self._run_btn.clicked.connect(self._on_run)
        header.addWidget(self._run_btn)

        # ── BS date badge (shows the selected/current date) ──
        self._date_badge = QLabel()
        self._date_badge.setStyleSheet("color: #000000; font-size: 13px; font-weight: 700; padding-left: 6px;")
        header.addWidget(self._date_badge)

        main_layout.addLayout(header)

        # Set selectors to today's BS date
        self._init_today_selectors()

        # Connect radio buttons
        self._radio_day.toggled.connect(self._on_mode_changed)
        self._radio_month.toggled.connect(self._on_mode_changed)
        self._radio_year.toggled.connect(self._on_mode_changed)
        # Also update day count and badge when selectors change
        self._month_combo.currentIndexChanged.connect(self._on_month_or_year_changed)
        self._year_combo.currentIndexChanged.connect(self._on_month_or_year_changed)
        self._day_combo.currentIndexChanged.connect(self._refresh_date_badge)

        # Scroll Area with plain white background
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")
        main_layout.addWidget(scroll, 1)

        self._container = QWidget()
        self._container.setAutoFillBackground(True)
        cpal = self._container.palette()
        cpal.setColor(self._container.backgroundRole(), Qt.white)
        self._container.setPalette(cpal)
        self._card_layout = QVBoxLayout(self._container)
        self._card_layout.setContentsMargins(4, 4, 4, 4)
        self._card_layout.setSpacing(18)
        scroll.setWidget(self._container)

        # Apply initial mode visibility
        self._apply_mode_visibility()
        self._refresh_date_badge()

    def _get_birth_bs_year(self, data: Optional[dict] = None) -> int:
        """Extract birth Bikram Sambat year from chart data with fallback."""
        d = data if data is not None else self._data
        if not isinstance(d, dict):
            from gui.utils.bs_calendar import get_today_bs
            t = get_today_bs()
            return (t["year"] - 30) if t else 2050

        meta = d.get("metadata") or {}

        # 1. Direct BS dictionary
        bs_dict = d.get("bs") or meta.get("bs")
        if isinstance(bs_dict, dict) and bs_dict.get("year"):
            try:
                y = int(bs_dict["year"])
                if 1900 <= y <= 2200:
                    return y
            except (ValueError, TypeError):
                pass

        # 2. Bikram Sambat date string (e.g. birth_date_bs, bs_date, date_bs)
        for key in ("birth_date_bs", "bs_date", "date_bs"):
            val = meta.get(key) or d.get(key)
            if val:
                val_str = str(val).translate(str.maketrans("०१२३४५६७८९", "0123456789"))
                import re
                m = re.search(r'\b(19\d\d|20\d\d|21\d\d)\b', val_str)
                if m:
                    y = int(m.group(1))
                    if 1900 <= y <= 2200:
                        return y

        # 3. Gregorian birth_date converted to BS
        for key in ("birth_date", "birthDate", "date"):
            val = meta.get(key) or d.get(key)
            if val:
                raw_date = str(val)[:10]
                try:
                    import datetime
                    ad = datetime.date.fromisoformat(raw_date)
                    from gui.utils.bs_calendar import gregorian_to_bs
                    bs = gregorian_to_bs(ad.year, ad.month, ad.day)
                    if bs and bs.get("year"):
                        return int(bs["year"])
                    return ad.year + 57
                except Exception:
                    pass

        from gui.utils.bs_calendar import get_today_bs
        t = get_today_bs()
        return (t["year"] - 30) if t else 2050

    def _populate_year_combo(self, birth_year: Optional[int] = None):
        """Populate the year selector with a list from birth year to 120 years (जन्म वर्ष देखि १२० वर्ष)."""
        if birth_year is None:
            birth_year = self._get_birth_bs_year()

        from gui.utils.bs_calendar import to_nepali_digits, get_today_bs

        current_selected = self._year_combo.currentData()
        today_bs = get_today_bs()
        today_y = today_bs["year"] if today_bs else (birth_year + 30)

        self._year_combo.blockSignals(True)
        self._year_combo.clear()

        # List from birth year to 120 years (birth_year .. birth_year + 120)
        start_year = birth_year
        end_year = birth_year + 120

        for y in range(start_year, end_year + 1):
            lbl = to_nepali_digits(y) if self._is_ne else str(y)
            self._year_combo.addItem(lbl, y)

        # Retain previous selection if valid, else default to today's BS year, else birth year
        target_year = current_selected if current_selected is not None else today_y
        idx = self._year_combo.findData(target_year)
        if idx >= 0:
            self._year_combo.setCurrentIndex(idx)
        else:
            idx_today = self._year_combo.findData(today_y)
            if idx_today >= 0:
                self._year_combo.setCurrentIndex(idx_today)
            else:
                self._year_combo.setCurrentIndex(0)

        self._year_combo.blockSignals(False)

    def _init_today_selectors(self):
        """Set year/month/day combos to today's BS date."""
        from gui.utils.bs_calendar import get_today_bs
        today_bs = get_today_bs()
        if today_bs:
            y, m, d = today_bs["year"], today_bs["month"], today_bs["day"]
        else:
            import datetime
            t = datetime.date.today()
            y, m, d = t.year + 57, 1, 1

        # Set year
        idx_y = self._year_combo.findData(y)
        if idx_y >= 0:
            self._year_combo.setCurrentIndex(idx_y)
        # Set month
        idx_m = self._month_combo.findData(m)
        if idx_m >= 0:
            self._month_combo.setCurrentIndex(idx_m)
        # Update day count for this month
        self._update_day_count()
        # Set day
        idx_d = self._day_combo.findData(d)
        if idx_d >= 0:
            self._day_combo.setCurrentIndex(idx_d)

    def _update_day_count(self):
        """Refresh the day combo to match the max days for selected BS month."""
        from gui.utils.bs_calendar import bs_month_length, to_nepali_digits
        y = self._year_combo.currentData() or 2083
        m = self._month_combo.currentData() or 1
        max_days = bs_month_length(y, m) or 30
        current_d = self._day_combo.currentData() or 1
        self._day_combo.blockSignals(True)
        self._day_combo.clear()
        for d in range(1, max_days + 1):
            self._day_combo.addItem(to_nepali_digits(d) if self._is_ne else str(d), d)
        idx = self._day_combo.findData(min(current_d, max_days))
        if idx >= 0:
            self._day_combo.setCurrentIndex(idx)
        self._day_combo.blockSignals(False)

    def _apply_mode_visibility(self):
        """Show/hide selectors based on current filter mode."""
        mode = self._filter_mode
        # Day mode: year + month + day all visible
        # Month mode: year + month visible, day hidden
        # Year mode: year visible, month and day hidden
        day_vis   = (mode == "day")
        month_vis = (mode in ("day", "month"))
        self._lbl_day.setVisible(day_vis)
        self._day_combo.setVisible(day_vis)
        self._lbl_month.setVisible(month_vis)
        self._month_combo.setVisible(month_vis)
        self._lbl_year.setVisible(True)
        self._year_combo.setVisible(True)

    def _on_mode_changed(self):
        """Called when any radio button is toggled."""
        if self._radio_day.isChecked():
            self._filter_mode = "day"
        elif self._radio_month.isChecked():
            self._filter_mode = "month"
        elif self._radio_year.isChecked():
            self._filter_mode = "year"
        self._apply_mode_visibility()
        self._refresh_date_badge()
        self._render_result()

    def _on_month_or_year_changed(self):
        """When year or month combo changes, recalculate days in month and update badge."""
        self._update_day_count()
        self._refresh_date_badge()

    def _refresh_date_badge(self):
        """Update the date badge label based on current selector state."""
        from gui.utils.bs_calendar import BS_MONTHS_NE, BS_MONTHS_EN, to_nepali_digits
        y = self._year_combo.currentData() or 2083
        m = self._month_combo.currentData() or 1
        d = self._day_combo.currentData() or 1
        months = BS_MONTHS_NE if self._is_ne else BS_MONTHS_EN
        m_name = months[m - 1] if 1 <= m <= 12 else str(m)
        mode = self._filter_mode
        if mode == "day":
            if self._is_ne:
                txt = f"📅 वि.सं. {to_nepali_digits(y)} {m_name} {to_nepali_digits(d)}"
            else:
                txt = f"📅 {d} {m_name} {y} BS"
        elif mode == "month":
            if self._is_ne:
                txt = f"📅 वि.सं. {to_nepali_digits(y)} {m_name}"
            else:
                txt = f"📅 {m_name} {y} BS"
        else:
            if self._is_ne:
                txt = f"📅 वि.सं. {to_nepali_digits(y)}"
            else:
                txt = f"📅 {y} BS"
        self._date_badge.setText(txt)

    def _on_run(self):
        """Run button pressed — refresh the result display with the selected date/mode."""
        self._refresh_date_badge()
        self._render_result()

    def _get_today_date_str(self) -> str:
        import datetime
        now = datetime.date.today()
        try:
            from gui.utils.bs_calendar import gregorian_to_bs, BS_MONTHS_NE, to_nepali_digits
            bs = gregorian_to_bs(now.year, now.month, now.day)
            if bs:
                return f"वि.सं. {to_nepali_digits(bs['year'])} {BS_MONTHS_NE[bs['month']-1]} {to_nepali_digits(bs['day'])}"
        except Exception:
            pass
        return now.strftime("%Y-%m-%d")

    def _get_selected_label(self) -> str:
        """Return a human-readable label for the currently selected date/period."""
        from gui.utils.bs_calendar import BS_MONTHS_NE, BS_MONTHS_EN, to_nepali_digits
        y = self._year_combo.currentData() or 2083
        m = self._month_combo.currentData() or 1
        d = self._day_combo.currentData() or 1
        months = BS_MONTHS_NE if self._is_ne else BS_MONTHS_EN
        m_name = months[m - 1] if 1 <= m <= 12 else str(m)
        mode = self._filter_mode
        if mode == "day":
            return (f"{to_nepali_digits(y)} {m_name} {to_nepali_digits(d)}"
                    if self._is_ne else f"{d} {m_name} {y}")
        elif mode == "month":
            return (f"{to_nepali_digits(y)} {m_name}"
                    if self._is_ne else f"{m_name} {y}")
        else:
            return to_nepali_digits(y) if self._is_ne else str(y)

    def refresh(self, data: dict):
        self._data = data
        birth_year = self._get_birth_bs_year(data)
        self._populate_year_combo(birth_year)
        self._render_result()

    def _render_result(self):
        """Re-render the result cards for the selected date/period and mode."""
        data = self._data
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            empty_lbl = QLabel("कुण्डली डाटा उपलब्ध छैन। कृपया पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne else "Chart data unavailable. Please calculate chart first.")
            empty_lbl.setStyleSheet("color: #000000; font-size: 16px; padding: 20px;")
            self._card_layout.addWidget(empty_lbl)
            return

        y = self._year_combo.currentData() or 2083
        m = self._month_combo.currentData() or 1
        d = self._day_combo.currentData() or 1
        mode = self._filter_mode

        # Calculate fully dynamic astrological predictions for this selected date/mode
        from backend.calculator.daily_horoscope_engine import calculate_dynamic_horoscope
        h_data = calculate_dynamic_horoscope(
            natal_data=data,
            mode=mode,
            bs_year=y,
            bs_month=m,
            bs_day=d,
            language=self._lang,
        )

        def add_topic(title: str, body: str):
            t_lbl = QLabel(title)
            t_lbl.setWordWrap(True)
            t_lbl.setStyleSheet("color: #000000; font-size: 20px; font-weight: 800; padding-top: 8px;")
            self._card_layout.addWidget(t_lbl)
            b_lbl = QLabel(body)
            b_lbl.setWordWrap(True)
            b_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            b_lbl.setStyleSheet("color: #111111; font-size: 17px; line-height: 1.7; padding-bottom: 4px;")
            self._card_layout.addWidget(b_lbl)

        # ── Period heading ──
        period_lbl = QLabel(h_data["period_badge"])
        period_lbl.setWordWrap(True)
        period_lbl.setStyleSheet(
            "color: #1d4ed8; font-size: 16px; font-weight: 800;"
            " background: #eff6ff; border-left: 5px solid #1d4ed8;"
            " padding: 8px 14px; border-radius: 6px; margin-bottom: 6px;"
        )
        self._card_layout.addWidget(period_lbl)

        # ── Subject / Overview ──
        add_topic(
            "👤 " + ("जातक" if self._is_ne else "Subject"),
            f"{h_data['subject_name']} | "
            f"{('लग्न' if self._is_ne else 'Ascendant')}: {h_data['lagna_name']} | "
            f"{('चन्द्र राशि' if self._is_ne else 'Moon Sign')}: {h_data['moon_name']}"
        )

        # ── Dynamic Planetary Overview ──
        add_topic(h_data["overview_title"], h_data["overview_body"])

        # ── Dynamic 7 Dimensions ──
        for dim in h_data["dimensions"]:
            title_text = dim["title_ne"] if self._is_ne else dim["title_en"]
            body_text = dim["text_ne"] if self._is_ne else dim["text_en"]
            add_topic(title_text, body_text)

        # ── Dynamic Lucky Factors ──
        for lbl, val in h_data["lucky_lines"]:
            add_topic(lbl, val)

        # ── Dynamic Remedies ──
        add_topic(h_data["remedy_title"], h_data["remedy_body"])

        # ── Live Planetary Transit Snapshot Table ──
        table_title = QLabel("🪐 " + ("सो दिनको प्रत्यक्ष ग्रह गोचर स्थिति (Actual Transit Positions)" if self._is_ne else "Actual Planetary Transit Table"))
        table_title.setStyleSheet("color: #000000; font-size: 19px; font-weight: 800; padding-top: 14px;")
        self._card_layout.addWidget(table_title)

        table = QTableWidget()
        table.setColumnCount(7)
        headers = [
            "ग्रह" if self._is_ne else "Planet",
            "गोचर राशि" if self._is_ne else "Transit Sign",
            "अंश" if self._is_ne else "Degree",
            "चन्द्रबाट भाव" if self._is_ne else "From Moon",
            "लग्नबाट भाव" if self._is_ne else "From Lagna",
            "नक्षत्र" if self._is_ne else "Nakshatra",
            "फल प्रभाव" if self._is_ne else "Quality",
        ]
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(h_data["table_rows"]))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setStyleSheet(
            "QTableWidget {"
            "  background: #ffffff; color: #000000; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px;"
            "}"
            "QHeaderView::section {"
            "  background-color: #f1f5f9; color: #0f172a; font-weight: 800; font-size: 13px; padding: 6px; border: 1px solid #e2e8f0;"
            "}"
        )

        for r_idx, row in enumerate(h_data["table_rows"]):
            items = [
                row["planet_name"],
                row["sign_name"],
                row["degree_str"],
                f"{row['house_from_moon']}औं भाव" if self._is_ne else f"House {row['house_from_moon']}",
                f"{row['house_from_lagna']}औं भाव" if self._is_ne else f"House {row['house_from_lagna']}",
                row["nakshatra"],
                row["status_str"],
            ]
            for c_idx, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if c_idx == 6:  # status column
                    if row["is_auspicious"]:
                        item.setForeground(Qt.darkGreen)
                    else:
                        item.setForeground(Qt.red)
                table.setItem(r_idx, c_idx, item)

        table.setFixedHeight(340)
        self._card_layout.addWidget(table)


class VarshaphalaPage(QWidget):
    """Tajika Varshaphala (Yearly Forecast & Solar Return)."""
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data
        self._lang = language
        self._is_ne = language == "ne"
        self._build_ui()
        if data:
            self.refresh(data)

    # ── Helpers ───────────────────────────────────────────────────────────────
    _PLANET_NE = {
        "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल",
        "Mercury": "बुध", "Jupiter": "बृहस्पति", "Venus": "शुक्र", "Saturn": "शनि",
        "Rahu": "राहु", "Ketu": "केतु",
    }
    _SIGN_NE = [
        "", "मेष","वृष","मिथुन","कर्क","सिंह","कन्या",
        "तुला","वृश्चिक","धनु","मकर","कुम्भ","मीन"
    ]
    _SAHAM_NE = {"Punya": "पुण्य साहम", "Rajya": "राज्य साहम", "Vivaha": "विवाह साहम"}

    @staticmethod
    def _deg_to_sign(deg: float) -> str:
        deg = float(deg) % 360.0
        sign_idx = int(deg // 30) + 1
        deg_in_sign = deg % 30
        d = int(deg_in_sign)
        m = int((deg_in_sign - d) * 60)
        signs = ["","मेष","वृष","मिथुन","कर्क","सिंह","कन्या",
                 "तुला","वृश्चिक","धनु","मकर","कुम्भ","मीन"]
        return f"{signs[sign_idx]} {d}°{m:02d}′"

    @staticmethod
    def _jd_to_bs_date(jd: float) -> str:
        """Convert Julian Day to Bikram Sambat date string."""
        try:
            import datetime
            # JD to Gregorian
            jd = jd + 0.5
            z = int(jd)
            a = z if z < 2299161 else z + 1 + int((z - 1867216.25) / 36524.25) - int(int((z - 1867216.25) / 36524.25) / 4)
            b = a + 1524
            c = int((b - 122.1) / 365.25)
            d = int(365.25 * c)
            e = int((b - d) / 30.6001)
            day = b - d - int(30.6001 * e)
            month = e - 1 if e < 14 else e - 13
            year = c - 4716 if month > 2 else c - 4715
            greg = datetime.date(year, month, day)
            try:
                import nepali_datetime
                bs = nepali_datetime.date.from_datetime_date(greg)
                NE_MONTHS = ["","वैशाख","जेठ","असार","साउन","भदौ","असोज","कात्तिक","मंसिर","पुस","माघ","फागुन","चैत"]
                m_name = NE_MONTHS[bs.month] if 1 <= bs.month <= 12 else ""
                def to_ne(n): return str(n).translate(str.maketrans("0123456789","०१२३४५६७८९"))
                return f"वि.सं. {to_ne(bs.year)} {m_name} {to_ne(bs.day)}"
            except Exception:
                return greg.strftime("%Y-%m-%d")
        except Exception:
            return "—"

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Top bar
        top_bar = QHBoxLayout()
        title = QLabel("📅 " + ("वार्षिक वर्षफल (Varshaphala & Solar Return)" if self._is_ne else "Yearly Forecast (Varshaphala)"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 18px; font-weight: 700;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Single scrollable browser
        from PySide6.QtWidgets import QTextBrowser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setFrameShape(QFrame.NoFrame)
        self._browser.setStyleSheet(
            "QTextBrowser { background: #ffffff; border: none; "
            "color: #1a1a1a; font-size: 13.5px; }"
        )
        self._browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._browser, 1)

    def refresh(self, data: dict):
        self._data = data
        vdata = data.get("varshaphala", {})
        if not vdata:
            self._browser.setHtml(
                f"<p style='color:{COLOR_TEXT_MUTED};padding:20px;font-size:14px;'>"
                + ("वर्षफल डाटा उपलब्ध छैन। कृपया पहिले कुण्डली गणना गर्नुहोस्।" if self._is_ne
                   else "Varshaphala data is unavailable. Please calculate the chart first.")
                + "</p>"
            )
            return

        yr = vdata.get("year", "—")
        muntha_deg = vdata.get("muntha", 0)
        varshesh = vdata.get("varsheshwara", "Sun")
        positions = vdata.get("positions", {})
        mudda = vdata.get("mudda_dasha", [])
        yogas = vdata.get("tajika_yogas", [])
        sahams = vdata.get("sahams", {})
        panchabala = vdata.get("panchavargiya_bala", {})

        # Nepali helpers
        def pn(name): return self._PLANET_NE.get(name, name)
        def deg_str(d): return self._deg_to_sign(float(d)) if d else "—"

        # ── Section helper ─────────────────────────────────────────────────────
        def sec(title_str, body_html):
            return (
                f"<h3 style='color:#7c3d00;font-size:15px;font-weight:700;"
                f"margin:20px 0 8px 0;border-bottom:2px solid #d4a020;padding-bottom:5px;'>"
                f"{title_str}</h3>"
                f"<div style='font-size:13.5px;line-height:1.8;color:#1a1a1a;'>{body_html}</div>"
            )

        # ── 1. वर्ष सारांश ─────────────────────────────────────────────────────
        solar_jd = vdata.get("solar_return_jd", 0)
        sr_date = self._jd_to_bs_date(solar_jd) if solar_jd else "—"
        muntha_str = deg_str(muntha_deg)
        varshesh_ne = pn(varshesh)

        summary_html = f"""
        <table style='width:100%;font-size:13.5px;border-collapse:collapse;color:#1a1a1a;'>
            <tr>
                <td style='width:50%;padding:6px 0;'><b>वर्ष:</b> {yr}</td>
                <td style='width:50%;padding:6px 0;'><b>सौर वापसी मिति:</b> {sr_date}</td>
            </tr>
            <tr>
                <td style='padding:6px 0;'><b>मुंथा स्थिति:</b> {muntha_str}</td>
                <td style='padding:6px 0;'><b>वर्षेश (Year Lord):</b>
                    <span style='color:#1761bd;font-weight:700;'>{varshesh_ne}</span></td>
            </tr>
        </table>
        """

        # ── 2. ग्रह स्थिति (Solar Return Chart) ─────────────────────────────────
        planet_rows = ""
        for pname, plong in positions.items():
            planet_rows += (
                f"<tr>"
                f"<td style='padding:5px 8px;border-bottom:1px solid #e8e8e8;color:#1a1a1a;'><b>{pn(pname)}</b></td>"
                f"<td style='padding:5px 8px;border-bottom:1px solid #e8e8e8;color:#1a1a1a;'>{deg_str(plong)}</td>"
                f"<td style='padding:5px 8px;border-bottom:1px solid #e8e8e8;color:#555555;'>"
                f"{round(panchabala.get(pname, 0), 1)} बल</td>"
                f"</tr>"
            )
        positions_html = f"""
        <table style='width:100%;font-size:13px;border-collapse:collapse;'>
            <tr style='background:#f5f0e8;'>
                <th style='padding:6px 8px;text-align:left;color:#7c3d00;'>ग्रह</th>
                <th style='padding:6px 8px;text-align:left;color:#7c3d00;'>राशि/स्थान</th>
                <th style='padding:6px 8px;text-align:left;color:#7c3d00;'>पञ्चवर्गीय बल</th>
            </tr>
            {planet_rows}
        </table>
        """ if planet_rows else "<p style='color:#888;'>ग्रह स्थिति उपलब्ध छैन।</p>"

        # ── 3. मुद्दा दशा (Mudda Dasha) ──────────────────────────────────────────
        mudda_rows = ""
        for m in mudda[:7]:
            start_str = self._jd_to_bs_date(m.get("start_jd", 0))
            end_str = self._jd_to_bs_date(m.get("end_jd", 0))
            dur = round(m.get("duration_days", 0), 1)
            lord_ne = pn(m.get("lord", ""))
            mudda_rows += (
                f"<tr>"
                f"<td style='padding:5px 8px;border-bottom:1px solid #e8e8e8;color:#1a1a1a;'><b>{lord_ne}</b></td>"
                f"<td style='padding:5px 8px;border-bottom:1px solid #e8e8e8;color:#1a1a1a;'>{start_str}</td>"
                f"<td style='padding:5px 8px;border-bottom:1px solid #e8e8e8;color:#1a1a1a;'>{end_str}</td>"
                f"<td style='padding:5px 8px;border-bottom:1px solid #e8e8e8;color:#555555;'>{dur} दिन</td>"
                f"</tr>"
            )
        mudda_html = f"""
        <table style='width:100%;font-size:13px;border-collapse:collapse;'>
            <tr style='background:#f5f0e8;'>
                <th style='padding:6px 8px;text-align:left;color:#7c3d00;'>दशा स्वामी</th>
                <th style='padding:6px 8px;text-align:left;color:#7c3d00;'>सुरु</th>
                <th style='padding:6px 8px;text-align:left;color:#7c3d00;'>समाप्त</th>
                <th style='padding:6px 8px;text-align:left;color:#7c3d00;'>अवधि</th>
            </tr>
            {mudda_rows}
        </table>
        """ if mudda_rows else "<p style='color:#888;'>मुद्दा दशा उपलब्ध छैन।</p>"

        # ── 4. ताजिक योग (Tajika Yogas) ──────────────────────────────────────────
        yoga_items = ""
        for yg in yogas:
            planets_str = " ↔ ".join(pn(p) for p in yg.get("planets", []))
            orb = yg.get("orb", 0)
            yoga_items += (
                f"<div style='padding:6px 0;border-bottom:1px solid #f0f0f0;color:#1a1a1a;'>"
                f"<b style='color:#1761bd;'>✦ {yg.get('name', '')} योग:</b> "
                f"{planets_str} — कक्षा {round(orb, 2)}°</div>"
            )
        yogas_html = yoga_items if yoga_items else "<p style='color:#888;'>कुनै ताजिक योग भेटिएन।</p>"

        # ── 5. साहम ─────────────────────────────────────────────────────────────
        saham_rows = ""
        for sname, sdeg in sahams.items():
            ne_name = self._SAHAM_NE.get(sname, sname)
            saham_rows += (
                f"<div style='padding:5px 0;color:#1a1a1a;'>"
                f"<b>{ne_name}:</b> {deg_str(sdeg)}</div>"
            )
        sahams_html = saham_rows if saham_rows else "<p style='color:#888;'>साहम उपलब्ध छैन।</p>"

        # ── Compose full HTML ─────────────────────────────────────────────────
        full_html = f"""
        <!DOCTYPE html><html><head><meta charset='utf-8'>
        <style>
            body {{ font-family:'Segoe UI','Noto Sans Devanagari',sans-serif;
                   color:#1a1a1a; background:#ffffff;
                   margin:0; padding:10px 6px; }}
            h3 {{ margin:20px 0 6px 0; }}
            b  {{ color:#111111; }}
            table {{ border-collapse:collapse; width:100%; }}
            th {{ text-align:left; font-weight:700; }}
        </style></head><body>
        {sec("🌟 वर्ष " + str(yr) + " — वार्षिक वर्षफल सारांश", summary_html)}
        {sec("🪐 सौर वापसी कुण्डलीमा ग्रह स्थिति", positions_html)}
        {sec("⏱ मुद्दा दशा (Mudda Dasha) — वार्षिक उप-दशा", mudda_html)}
        {sec("🔗 ताजिक योगहरू (Tajika Yogas)", yogas_html)}
        {sec("☀ प्रमुख साहम स्थितिहरू", sahams_html)}
        </body></html>
        """
        self._browser.setHtml(full_html)

