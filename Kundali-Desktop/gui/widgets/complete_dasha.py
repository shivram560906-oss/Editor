"""
gui/widgets/complete_dasha.py
Complete Dasha report — all three dasha systems in one page:
Vimshottari + Yogini + Ashtottari
"""
from __future__ import annotations
import sys, os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QTabWidget, QFrame, QPushButton,
    QStackedWidget, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QBrush

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import datetime

from gui.theme import (COLOR_GOLD, BG_SECONDARY, BORDER_COLOR,
                        COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED)
from gui.utils.planet_colors import planet_color, planet_full_name, to_nepali_digits
from gui.utils.bs_calendar import gregorian_to_bs, format_bs_date
from gui.widgets.life_analysis import DashaPhalPage

UNAVAILABLE = "—"
LEVEL_KEYS = {1: "maha", 2: "antar", 3: "pratyantar", 4: "sookshma", 5: "prana"}
LEVEL_LABELS = {
    "en": {1: "Mahadasha", 2: "Antardasha", 3: "Pratyantardasha", 4: "Sookshmadasha", 5: "Pranadasha"},
    "ne": {1: "महादशा", 2: "अन्तर्दशा", 3: "प्रत्यन्तर्दशा", 4: "सूक्ष्मदशा", 5: "प्राणदशा"},
}


def _fmt_date(date_str: str, lang: str, bs_value: str = "") -> str:
    """Format an exact BS date, or state clearly when BS is unavailable."""
    if bs_value:
        return to_nepali_digits(bs_value) if lang == "ne" else bs_value
    try:
        d = datetime.date.fromisoformat(str(date_str)[:10])
    except (TypeError, ValueError):
        return str(date_str)[:10] or UNAVAILABLE

    ad_value = d.strftime("%Y-%m-%d")
    if lang == "ne":
        return f"वि.सं. उपलब्ध छैन · {to_nepali_digits(ad_value)} AD"
    return f"BS unavailable · {ad_value} AD"


def _is_active(start: str, end: str) -> bool:
    today = datetime.date.today()
    try:
        s = datetime.date.fromisoformat(str(start)[:10])
        e = datetime.date.fromisoformat(str(end)[:10])
        return s <= today < e
    except (TypeError, ValueError):
        return False


def build_dasha_model(data: Optional[dict], language: str = "ne") -> dict:
    """Normalize the dasha hierarchy while preserving payload active state."""
    is_ne = language == "ne"
    if data is None:
        return {"state": "no_chart", "message": "कुण्डली गणना गर्नुहोस्।" if is_ne else "Calculate a chart to view Vimshottari Dasha.", "nodes": [], "active_chain": []}
    if not isinstance(data, dict):
        return {"state": "error", "message": "अमान्य दशा विवरण।" if is_ne else "Invalid dasha data.", "nodes": [], "active_chain": []}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"]), "nodes": [], "active_chain": []}
    periods = data.get("dasha")
    if periods is None:
        return {"state": "empty", "message": "विंशोत्तरी दशा उपलब्ध छैन।" if is_ne else "Vimshottari Dasha is not available.", "nodes": [], "active_chain": []}
    if not isinstance(periods, list):
        return {"state": "error", "message": "अमान्य दशा विवरण।" if is_ne else "Invalid dasha data.", "nodes": [], "active_chain": []}

    def convert(period, depth=0, ancestors=None):
        ancestors = list(ancestors or [])
        level = int(period.get("level") or depth + 1)
        lord = str(period.get("lord") or UNAVAILABLE)
        display_lord = str(period.get("lord_nepali") or lord) if is_ne else lord
        start = str(period.get("start") or "")[:10]
        end = str(period.get("end") or "")[:10]
        active = bool(period["is_active"]) if "is_active" in period else _is_active(start, end)
        path = ancestors + [display_lord]
        node = {
            "lord": lord, "display_lord": display_lord, "level": level,
            "level_key": LEVEL_KEYS.get(level, f"level_{level}"),
            "level_label": LEVEL_LABELS.get(language, LEVEL_LABELS["en"]).get(level, f"Level {level}"),
            "path": path, "path_text": " / ".join(path),
            "start": start, "end": end,
            "start_display": _fmt_date(start, language, str(period.get("start_bs") or "")),
            "end_display": _fmt_date(end, language, str(period.get("end_bs") or "")),
            "active": active, "partial": bool(period.get("is_partial")),
            "color": planet_color(lord), "children": [],
        }
        children = period.get("children") if isinstance(period.get("children"), list) else []
        node["children"] = [convert(child, depth + 1, path) for child in children if isinstance(child, dict)]
        return node

    nodes = [convert(period) for period in periods if isinstance(period, dict)]
    active_chain = []
    current = nodes
    while current:
        active = next((node for node in current if node["active"]), None)
        if not active:
            break
        active_chain.append(active)
        current = active["children"]
    state = "ready" if nodes else "empty"
    message = "" if nodes else ("विंशोत्तरी दशा उपलब्ध छैन।" if is_ne else "Vimshottari Dasha is not available.")
    return {"state": state, "message": message, "nodes": nodes, "active_chain": active_chain}


def _build_dasha_tree(dasha_data: list, language: str) -> QTreeWidget:
    is_ne = language == "ne"
    tree = QTreeWidget()
    tree.setHeaderLabels([
        "ग्रह" if is_ne else "Planet",
        "सुरु" if is_ne else "Start",
        "अन्त" if is_ne else "End",
        "अवधि" if is_ne else "Duration"
    ])
    tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
    tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
    tree.setAlternatingRowColors(True)

    import datetime
    today = datetime.date.today()

    for maha in (dasha_data or []):
        lord  = maha.get("lord", "")
        start = maha.get("start", "")[:10]
        end   = maha.get("end", "")[:10]

        # Duration
        try:
            s = datetime.date.fromisoformat(start)
            e = datetime.date.fromisoformat(end)
            days = (e - s).days
            yrs  = round(days / 365.25, 1)
            dur  = f"{yrs}y"
        except Exception:
            dur = "—"

        active = _is_active(start, end)
        item = QTreeWidgetItem([
            planet_full_name(lord, language),
            _fmt_date(start, language),
            _fmt_date(end, language),
            dur
        ])
        item.setForeground(0, QBrush(QColor(planet_color(lord))))
        item.setFont(0, QFont("Noto Sans Devanagari", 12, QFont.Bold))

        if active:
            hl = QColor(planet_color(lord))
            hl.setAlpha(28)
            for c in range(4):
                item.setBackground(c, QBrush(hl))
            item.setExpanded(True)

        for antar in maha.get("children", []):
            al    = antar.get("lord", "")
            as_   = antar.get("start", "")[:10]
            ae    = antar.get("end",   "")[:10]
            try:
                s2 = datetime.date.fromisoformat(as_)
                e2 = datetime.date.fromisoformat(ae)
                d2 = (e2 - s2).days
                y2 = round(d2 / 365.25 * 12, 1)
                dur2 = f"{y2}m"
            except Exception:
                dur2 = "—"

            a_item = QTreeWidgetItem([
                "  " + planet_full_name(al, language),
                _fmt_date(as_, language),
                _fmt_date(ae,  language),
                dur2
            ])
            a_item.setForeground(0, QBrush(QColor(planet_color(al))))
            if active and _is_active(as_, ae):
                hl2 = QColor(planet_color(al))
                hl2.setAlpha(20)
                for c in range(4):
                    a_item.setBackground(c, QBrush(hl2))
            item.addChild(a_item)

        tree.addTopLevelItem(item)

    return tree


class CompleteDashaPage(QWidget):
    """Unified dasha shell with a web-like Vimshottari five-level report.

    Legacy period data is retained as a fallback, while new normalized report
    status controls whether a system may present calculated results.
    """

    SYSTEMS = (
        ("vimshottari", "विंशोत्तरी", "Vimshottari"),
        ("tribhagi", "त्रिभागी", "Tribhagi"),
        ("ashtottari", "अष्टोत्तरी", "Ashtottari"),
        ("yogini", "योगिनी", "Yogini"),
    )

    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data or {}
        self._lang = language
        self._is_ne = language == "ne"
        self._pages = {}
        self._buttons = {}
        self._yogini_loading = False
        self._yogini_placeholder = None
        self._build_ui()
        self.refresh(self._data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(12)
        title = QLabel("⏳ " + ("सम्पूर्ण दशा र रिपोर्ट" if self._is_ne else "Complete Dasha & Report"))
        title.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 17px; font-weight: 700;")
        header.addWidget(title, 0, Qt.AlignVCenter)

        systems = QHBoxLayout()
        systems.setSpacing(6)
        self._system_buttons = systems
        for key, ne, en in self.SYSTEMS:
            button = QPushButton(ne if self._is_ne else en)
            button.setCheckable(True)
            button.setStyleSheet(
                f"QPushButton {{ padding: 5px 9px; color: {COLOR_TEXT_PRIMARY}; "
                f"background: {BG_SECONDARY}; border: 1px solid {BORDER_COLOR}; "
                f"border-radius: 6px; }} "
                f"QPushButton:checked {{ color: #052e16; background: #bbf7d0; "
                f"border: 2px solid #166534; }} "
                f"QPushButton:hover {{ border-color: {COLOR_GOLD}; }}"
            )
            button.clicked.connect(lambda checked=False, value=key: self._select_system(value))
            systems.addWidget(button)
            self._buttons[key] = button
        header.addLayout(systems)
        header.addStretch(1)
        layout.addLayout(header)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)



    def _yogini_lazy_page(self) -> QWidget:
        """Placeholder shown until the user asks for the large Yogini tree."""
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(20, 24, 20, 20)
        box.setSpacing(12)
        label = QLabel(
            "योगिनी दशाको पाँच-तह विस्तृत वृक्ष ठूलो हुने भएकाले यो पृष्ठ खोल्दा "
            "मात्र गणना गरिन्छ।\n"
            if self._is_ne else
            "The five-level Yogini tree is large, so it is calculated only when "
            "you request it on this page.\n"
        )
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 18px;")
        box.addWidget(label)
        button = QPushButton(
            "🔮 योगिनी दशा गणना गर्नुहोस्" if self._is_ne else "🔮 Calculate Yogini Dasha"
        )
        button.setStyleSheet(
            f"background: {COLOR_GOLD}; color: #000; font-size: 13px; font-weight: 700; "
            f"padding: 8px 18px; border-radius: 6px; border: 1px solid #b45309;"
        )
        button.clicked.connect(self._load_yogini)
        box.addWidget(button, 0, Qt.AlignLeft)
        box.addStretch(1)
        self._yogini_placeholder = page
        return page

    def _load_yogini(self) -> None:
        """Calculate the deferred Yogini tree and replace the placeholder page."""
        if self._yogini_loading:
            return
        self._yogini_loading = True
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            from gui.backend_bridge import calculate_yogini_report
            report = calculate_yogini_report(self._data)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "योगिनी दशा" if self._is_ne else "Yogini Dasha",
                (
                    "योगिनी दशा गणना गर्न सकिएन:\n" if self._is_ne
                    else "Could not calculate Yogini Dasha:\n"
                ) + str(exc),
            )
            return
        finally:
            QApplication.restoreOverrideCursor()
            self._yogini_loading = False

        reports = dict(self._data.get("dasha_reports") or {})
        reports["yogini"] = report
        self._data["dasha_reports"] = reports
        self._data["yogini_dasha_five_level"] = report.get("periods") or []

        old_page = self._pages.get("yogini")
        page = DashaPhalPage(self._data, self._lang, system="yogini")
        page.refresh(self._data)
        index = self._stack.indexOf(old_page) if old_page is not None else -1
        if index >= 0:
            self._stack.insertWidget(index, page)
        else:
            self._stack.addWidget(page)
        self._pages["yogini"] = page
        self._yogini_placeholder = None
        if old_page is not None:
            self._stack.removeWidget(old_page)
            old_page.deleteLater()
        self._select_system("yogini")

    def _status_page(self, system: str) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(20, 24, 20, 20)
        report = (self._data.get("dasha_reports") or {}).get(system) or {}
        status = report.get("status", "unavailable")
        message = report.get("message") or (
            "यो दशा प्रणालीको गणना उपलब्ध छैन।" if self._is_ne else "This dasha system is not available for calculation."
        )
        label = QLabel(
            ("स्थिति: " if self._is_ne else "Status: ") + status + "\n" + message
        )
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 18px;")
        box.addWidget(label)
        box.addStretch(1)
        return page

    def _select_system(self, system: str):
        for key, button in self._buttons.items():
            button.setChecked(key == system)
        page = self._pages[system]
        self._stack.setCurrentWidget(page)
        if system == "yogini" and page is self._yogini_placeholder:
            # The user explicitly opened the Yogini tab, so start the deferred
            # calculation after the page becomes visible.
            QTimer.singleShot(0, self._load_yogini)
            return
        if isinstance(page, DashaPhalPage):
            # Pages are initialized while hidden. Re-center the active row after
            # the selected system becomes visible and its scroll area has size.
            QTimer.singleShot(0, page._focus_selected_period)
            QTimer.singleShot(120, page._focus_selected_period)

    def refresh(self, data: dict) -> None:
        self._data = data or {}
        while self._stack.count():
            widget = self._stack.widget(0)
            self._stack.removeWidget(widget)
            widget.deleteLater()
        self._pages = {}

        for system, _, _ in self.SYSTEMS:
            report = (self._data.get("dasha_reports") or {}).get(system) or {}
            periods = report.get("periods") or []
            status = report.get("status")
            legacy_nodes = self._data.get("dasha") or []
            ashtottari_nodes = self._data.get("ashtottari_dasha") or []
            if system == "vimshottari" and (not report or (status == "ready" and not periods and legacy_nodes)):
                # Missing/partial normalized envelopes remain compatible with legacy Vimshottari data.
                page = DashaPhalPage(self._data, self._lang, system=system)
                page.refresh(self._data)
            elif system == "ashtottari" and (periods or ashtottari_nodes):
                page = DashaPhalPage(self._data, self._lang, system=system)
                page.refresh(self._data)
            elif periods and status == "ready":
                page = DashaPhalPage(self._data, self._lang, system=system)
                page.refresh(self._data)
            elif system == "yogini" and self._data.get("yogini_dasha_five_level"):
                page = DashaPhalPage(self._data, self._lang, system=system)
                page.refresh(self._data)
            elif system == "yogini" and report.get("deferred"):
                # Large five-level tree was intentionally omitted from the chart
                # payload; compute it only if/when the user opens this tab.
                page = self._yogini_lazy_page()
            else:
                page = self._status_page(system)
            self._pages[system] = page
            self._stack.addWidget(page)
        self._select_system("vimshottari")
