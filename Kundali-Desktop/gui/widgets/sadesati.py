"""
Native Sade Sati and Adhaiya report.

The report follows the web report structure: transit-cycle tabs, BS/AD
intervals, classical effects, remedies, and the astrological definition.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.theme import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER_COLOR,
    COLOR_ACCENT,
    COLOR_GOLD,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from gui.utils.bs_calendar import BS_MONTHS_EN, BS_MONTHS_NE, gregorian_to_bs, to_nepali_digits
from gui.utils.planet_colors import rashi_name


PHASES = (
    ("sade", 1, -1, "पहिलो चरण", "First phase", "१२ औं भाव", "12th from Moon"),
    ("sade", 2, 0, "दोस्रो चरण", "Second phase", "चन्द्र राशि", "Moon Sign"),
    ("sade", 3, 1, "तेस्रो चरण", "Third phase", "२ औं भाव", "2nd from Moon"),
    ("adhai", 1, 3, "कण्टक शनि (४ औं भाव)", "Kantak Shani (4th house)", "४ औं भाव", "4th from Moon"),
    ("adhai", 2, 7, "अष्टम शनि (८ औं भाव)", "Ashtam Shani (8th house)", "८ औं भाव", "8th from Moon"),
)


def _parse_birth_datetime(data: dict) -> Optional[dt.datetime]:
    metadata = data.get("metadata") or {}
    raw_date = str(metadata.get("birth_date") or "")[:10]
    if not raw_date:
        return None
    try:
        date_value = dt.date.fromisoformat(raw_date)
    except ValueError:
        return None
    raw_time = str(metadata.get("birth_time") or "00:00:00")
    try:
        parts = [int(value) for value in raw_time.split(":")[:3]]
        parts += [0] * (3 - len(parts))
        return dt.datetime.combine(date_value, dt.time(*parts[:3]))
    except (TypeError, ValueError):
        return dt.datetime.combine(date_value, dt.time())


def _add_days(value: dt.datetime, days: float) -> dt.datetime:
    return value + dt.timedelta(days=days)


def _normalize_sign(sign: int) -> int:
    return ((int(sign) - 1) % 12) + 1


def _format_bs_only(value: dt.datetime, language: str) -> str:
    bs = gregorian_to_bs(value.year, value.month, value.day)
    if not bs:
        return value.strftime("%Y-%m-%d")
    months = BS_MONTHS_NE if language == "ne" else BS_MONTHS_EN
    year = to_nepali_digits(bs["year"]) if language == "ne" else str(bs["year"])
    day = to_nepali_digits(bs["day"]) if language == "ne" else str(bs["day"])
    return f"{year} {months[bs['month'] - 1]} {day}"


def _format_bs_ad(value: dt.datetime, language: str) -> str:
    ad = value.strftime("%Y-%m-%d")
    return f"{_format_bs_only(value, language)} ({to_nepali_digits(ad) if language == 'ne' else ad} AD)"


def _panel(title: str, parent: Optional[QWidget] = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setObjectName("sadeReportPanel")
    frame.setStyleSheet(f"""
        QFrame#sadeReportPanel {{
            background: {BG_SECONDARY};
            border: 1px solid {BORDER_COLOR};
            border-radius: 6px;
        }}
    """)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 10, 14, 12)
    layout.setSpacing(6)
    heading = QLabel(title)
    heading.setStyleSheet(f"color:{COLOR_GOLD};font-size:15px;font-weight:700;")
    layout.addWidget(heading)
    return frame, layout


def _rich_panel(title: str, html: str) -> tuple[QFrame, QTextBrowser]:
    frame, layout = _panel(title)
    browser = QTextBrowser()
    browser.setObjectName("sadeReportText")
    browser.setOpenExternalLinks(False)
    browser.setFrameShape(QFrame.NoFrame)
    browser.setStyleSheet(
        f"QTextBrowser {{ background: transparent; color: {COLOR_TEXT_SECONDARY}; "
        "border: none; font-size: 13.5px; line-height: 1.65; }}"
    )
    browser.setHtml(html)
    browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout.addWidget(browser)
    return frame, browser


class SadeSatiPage(QWidget):
    def __init__(self, data: Optional[dict], language: str = "ne", parent=None):
        super().__init__(parent)
        self._data = data or {}
        self._lang = language
        self._is_ne = language == "ne"
        self._active_tab = "sade"
        self._build_ui()
        self.refresh(self._data)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(6)

        # ── Top bar: title + tabs side by side ───────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(14)
        top_bar.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🪐 " + ("साढेसाती र अढैया" if self._is_ne else "Sade Sati & Adhaiya"))
        title.setStyleSheet(f"color:{COLOR_GOLD};font-size:18px;font-weight:700;")
        top_bar.addWidget(title)
        top_bar.addStretch(1)

        self._sade_tab = self._tab_button("साढे साती" if self._is_ne else "Sade Sati", "sade")
        self._adhai_tab = self._tab_button("अढैया" if self._is_ne else "Adhaiya", "adhai")
        top_bar.addWidget(self._sade_tab)
        top_bar.addWidget(self._adhai_tab)
        root.addLayout(top_bar)

        # ── Short description just below title ────────────────────────────────
        description = QLabel(
            "शनि चन्द्र राशिबाट १२ औं, चन्द्र राशि र २ औं भावमा हुँदा साढेसाती हुन्छ।"
            if self._is_ne else
            "Sade Sati occurs when Saturn transits the 12th, Moon and 2nd signs from the natal Moon."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color:{COLOR_TEXT_MUTED};font-size:13px;")
        root.addWidget(description)

        # ── Single scrollable document browser ───────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setFrameShape(QFrame.NoFrame)
        self._browser.setStyleSheet(
            f"QTextBrowser {{ background: {BG_PRIMARY}; border: none; "
            f"color: {COLOR_TEXT_SECONDARY}; font-size: 13.5px; line-height: 1.7; }}"
        )
        self._browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self._browser, 1)

        # ── User Guide button (at the bottom; opens the shared guide dialog) ───
        # No inline guide box is rendered here, so the report keeps the full page.
        _guide_btn = QPushButton("📖 " + ("निर्देशिका" if self._is_ne else "Guide"))
        _guide_btn.setObjectName("sadesatiGuideBox")
        _guide_btn.setToolTip("साढेसाती निर्देशिका" if self._is_ne else "Sade Sati guide")
        _guide_btn.setCursor(Qt.PointingHandCursor)
        _guide_btn.setStyleSheet(
            "QPushButton { background: #e0f2fe; color: #0369a1; border: 1.5px solid #0284c7; "
            "border-radius: 8px; padding: 8px 14px; font-size: 12.5px; font-weight: 800; } "
            "QPushButton:hover { background: #bae6fd; }"
        )

        def _open_sadesati_guide():
            from gui.widgets.user_guide import show_page_guide
            show_page_guide(self, topic_id="page_sadesati_view")

        _guide_btn.clicked.connect(_open_sadesati_guide)
        root.addWidget(_guide_btn)

        # Keep scroll_area ref for focus helper compatibility
        self._scroll_area = self._browser
        self._content_layout = None  # unused in single-browser mode

    def _tab_button(self, text: str, tab: str) -> QPushButton:
        button = QPushButton(text)
        button.setCheckable(True)
        button.setFixedSize(100, 38)
        button.setStyleSheet("font-size:14px;")
        button.clicked.connect(lambda: self._set_tab(tab))
        return button

    def _set_tab(self, tab: str) -> None:
        self._active_tab = tab
        self._style_tabs()
        self._render_report()

    def _style_tabs(self) -> None:
        for button, tab in ((self._sade_tab, "sade"), (self._adhai_tab, "adhai")):
            button.setChecked(tab == self._active_tab)
            if tab == self._active_tab:
                button.setStyleSheet(
                    f"QPushButton {{ background:#1761bd; color:white; border:1px solid #1761bd; "
                    "border-radius:18px; font-weight:700; }}"
                )
            else:
                button.setStyleSheet(
                    f"QPushButton {{ background:transparent; color:#1761bd; border:1px solid #1761bd; "
                    "border-radius:18px; font-weight:700; }} QPushButton:hover { background:#e8f1ff; }"
                )

    def _phase_definitions(self, moon_sign: int) -> list[dict]:
        result = []
        for kind, phase, offset, label_ne, label_en, house_ne, house_en in PHASES:
            result.append({
                "type": kind,
                "phase": phase,
                "sign": _normalize_sign(moon_sign + offset),
                "label": label_ne if self._is_ne else label_en,
                "house": house_ne if self._is_ne else house_en,
            })
        return result

    def _timeline(self, moon_sign: int, saturn: dict, birth: dt.datetime) -> list[dict]:
        motion = 30.0 / (2.5 * 365.25)
        sign = int(saturn.get("sign_number", 1) or 1)
        longitude = float(saturn.get("longitude_in_sign", 0) or 0)
        boundary = _add_days(birth, max(0.0, (30.0 - longitude) / motion))
        try:
            end_date = birth.replace(year=birth.year + 120)
        except ValueError:
            # Keep leap-day births valid when projecting the report horizon.
            end_date = birth.replace(year=birth.year + 120, day=28)
        timeline = []
        start = birth
        stop = boundary
        while start < end_date:
            actual_stop = min(stop, end_date)
            timeline.append({"sign": _normalize_sign(sign), "start": start, "end": actual_stop})
            sign = _normalize_sign(sign + 1)
            start = stop
            stop = _add_days(stop, 30.0 / motion)
        definitions = self._phase_definitions(moon_sign)
        matches = []
        for entry in timeline:
            for definition in definitions:
                if entry["sign"] == definition["sign"]:
                    matches.append({**definition, **entry})
        return matches

    def _cycles(self, stages: list[dict], kind: str) -> list[dict]:
        selected = [stage for stage in stages if stage["type"] == kind]
        if kind == "adhai":
            return [{"start": s["start"], "end": s["end"], "phases": [s]} for s in selected]
        cycles = []
        current = None
        for stage in selected:
            if current is None:
                current = {"start": stage["start"], "end": stage["end"], "phases": [stage]}
                continue
            gap_years = (stage["start"] - current["end"]).days / 365.25
            if gap_years < 3:
                current["end"] = stage["end"]
                current["phases"].append(stage)
            else:
                cycles.append(current)
                current = {"start": stage["start"], "end": stage["end"], "phases": [stage]}
        if current:
            cycles.append(current)
        return cycles

    def _cycle_html(self, cycles: list[dict], now: dt.datetime) -> tuple[str, Optional[str], Optional[str]]:
        if not cycles:
            return (
                f"<p style='color:{COLOR_TEXT_MUTED};'>{'कुनै गोचर चक्र उपलब्ध छैन।' if self._is_ne else 'No transit cycles are available.'}</p>",
                None,
                None,
            )
        active = next((phase for cycle in cycles for phase in cycle["phases"]
                       if phase["start"] <= now < phase["end"]), None)
        upcoming = next((phase for cycle in cycles for phase in cycle["phases"]
                         if phase["start"] > now), None)
        active_key = _format_bs_ad(active["start"], self._lang) if active else None
        upcoming_key = _format_bs_ad(upcoming["start"], self._lang) if upcoming else None
        parts = []
        for cycle in cycles:
            parts.append(
                f"<div style='border-left:3px solid #1761bd;padding-left:12px;margin:2px 0 12px;'>"
                f"<div style='color:{COLOR_TEXT_PRIMARY};font-size:14.5px;font-weight:700;margin-bottom:6px;'>"
                f"{_format_bs_only(cycle['start'], self._lang)} → {_format_bs_only(cycle['end'], self._lang)}</div>"
            )
            for phase in cycle["phases"]:
                sign = rashi_name(phase["sign"], self._lang)
                phase_date = _format_bs_ad(phase["start"], self._lang)
                phase_style = "color:#5b4600;background:#fff4bd;font-weight:700;" if active and phase is active else "color:%s;" % COLOR_TEXT_SECONDARY
                parts.append(
                    f"<div style='{phase_style}font-size:13px;line-height:1.7;padding:3px 5px;'>"
                    f"<span style='color:#1761bd;font-weight:700;'>✦</span> "
                    f"<b>{phase['label']} ({sign}):</b> "
                    f"{phase_date} – {_format_bs_ad(phase['end'], self._lang)}</div>"
                )
            parts.append("</div>")
        return "".join(parts), active_key, upcoming_key

    @staticmethod
    def _cursor_for_text(browser: QTextBrowser, text: Optional[str]) -> Optional[QTextCursor]:
        if not text:
            return None
        cursor = browser.document().find(text)
        if cursor.isNull():
            return None
        cursor.select(QTextCursor.BlockUnderCursor)
        return cursor

    def _focus_upcoming(self, browser: QTextBrowser, upcoming_key: Optional[str]) -> None:
        cursor = self._cursor_for_text(browser, upcoming_key)
        if cursor is None:
            return

        rect = browser.cursorRect(cursor)
        bar = browser.verticalScrollBar()
        target = bar.value() + rect.center().y() - (browser.viewport().height() // 2)
        bar.setValue(max(0, min(target, bar.maximum())))

        selection = QTextEdit.ExtraSelection()
        selection.cursor = QTextCursor(cursor)
        selection.format.setBackground(QColor("#fff0a6"))
        selection.format.setForeground(QColor("#5b4600"))
        state = {"on": False, "count": 0}

        def blink() -> None:
            state["on"] = not state["on"]
            browser.setExtraSelections([selection] if state["on"] else [])
            state["count"] += 1
            if state["count"] >= 4:
                timer.stop()

        timer = QTimer(browser)
        timer.setInterval(300)
        timer.timeout.connect(blink)
        timer.start()

    def _apply_cycle_focus(self, browser: QTextBrowser, upcoming_key: Optional[str]) -> None:
        if upcoming_key:
            QTimer.singleShot(80, lambda: self._focus_upcoming(browser, upcoming_key))

    def _effects_html(self) -> str:
        if self._is_ne:
            return """
            <b style='color:#1761bd;'>सामान्य विश्लेषण (General Analysis):</b>
            <p>साढे सातीको प्रभाव व्यक्तिको कुण्डली, चन्द्र राशि, अष्टकवर्ग विन्दु, गोचरमा अन्य ग्रहको दृष्टि र व्यक्तिको कर्म अनुसार फरक-फरक रूपमा प्रकट हुन्छ। सामान्यतया यो अवधिलाई मानसिक, शारीरिक र सामाजिक चुनौतीहरूको समय मानिन्छ। यस अवधिमा बाधा, ढिलाइ, आर्थिक उतारचढाव, स्वास्थ्य समस्या, पारिवारिक तनाव वा कार्यस्थलमा अस्थिरता देखिन सक्छ।</p>
            <p>यदि कुण्डलीमा शनि शुभ स्थानमा वा उच्च राशिमा छ भने यही अवधिले ठूलो परिवर्तन, आत्मबोध, सामाजिक प्रगति र दीर्घकालीन सफलता पनि ल्याउन सक्छ। साढे साती शनिले आत्मनिरीक्षण, धैर्यता, सहनशीलता र अनुशासन सिकाउने समय हो।</p>
            <br><b style='color:#1761bd;'>उमेर र अवस्था अनुसार प्रभाव (Effects by Age/Status):</b>
            <p>यो परिपक्व उमेर, जिम्मेवारी र नेतृत्वको समय हो। करियरमा असन्तुष्टि, सरुवा, कार्यस्थलमा असुरक्षा, अचानक खर्च वा आर्थिक दबाब आउन सक्छ। वैवाहिक जीवनमा सञ्चारको कमी देखिए पनि आत्मनिरीक्षण, जीवनको उद्देश्य खोज्ने र आध्यात्मिकतातर्फ झुकाव बढ्ने सम्भावना रहन्छ।</p>
            """
        return """
        <b style='color:#1761bd;'>General Analysis:</b>
        <p>The effect of Sade Sati varies according to the natal chart, Moon sign, Ashtakavarga points, aspects from transiting planets, and personal actions. It may bring delays, financial fluctuations, health concerns, family tension, or work instability.</p>
        <p>When Saturn is well placed or exalted, the same period can bring transformation, self-realization, social progress, and lasting success. It teaches introspection, patience, endurance, and discipline.</p>
        <br><b style='color:#1761bd;'>Effects by Age/Status:</b>
        <p>Career dissatisfaction, transfers, financial pressure, or relationship communication gaps may occur. Introspection, purpose, and spiritual growth can also become stronger.</p>
        """

    def _remedies_html(self) -> str:
        if self._is_ne:
            return """
            शनिदेवको प्रतिकूल प्रभाव कम गर्न र शुभ फल प्राप्त गर्न निम्न उपायहरू गर्न सकिन्छ:<br><br>
            <b>1. शनिलाई तिल र तेल चढाउने:</b> शनिबार शनि मन्दिरमा तोरी वा तिलको तेल चढाउनु लाभदायक मानिन्छ।<br><br>
            <b>2. कालो वस्तु तथा फलाम दान:</b> कालो कपडा, कालो दाल, कम्बल वा फलामका सामान गरिब तथा असहायलाई दान गर्नुहोस्।<br><br>
            <b>3. शनि बीज मन्त्रको जप:</b><br><i style='color:#1761bd;'>ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः</i><br>दैनिक १०८ पटक जप गर्न सकिन्छ।<br><br>
            <b>4. दशरथकृत शनि स्तोत्र पाठ:</b> शनिबार श्रद्धापूर्वक पाठ गर्नुहोस्।<br><br>
            <b>5. पिपलको पूजा र परिक्रमा:</b> जल चढाउने, तिलको तेलको दियो बाल्ने र परिक्रमा गर्ने।<br><br>
            <b>6. दिनदुःखी तथा वृद्धवृद्धाको सेवा:</b> गरिब, असहाय, अपाङ्ग वा वृद्धवृद्धालाई आदर र सहयोग गर्नुहोस्।<br><br>
            <b>7. शनिबारको व्रत:</b> सात्विक आहार र अनुशासन पालना गर्नुहोस्।<br><br>
            <b>8. हनुमान चालीसा वा बजरंग बाण पाठ:</b> शनिबार नियमित पाठ गर्नुहोस्।<br><br>
            <b>9. महामृत्युञ्जय मन्त्र जप:</b><br><i style='color:#1761bd;'>ॐ त्र्यम्बकं यजामहे सुगन्धिं पुष्टिवर्धनम् । उर्वारुकमिव बन्धनान्मृत्योर्मुक्षीय माऽमृतात् ॥</i>
            """
        return """
        Here are practical traditional remedies for Saturn:<br><br>
        <b>1. Offer sesame or mustard oil to Saturn.</b><br><br>
        <b>2. Donate black clothing, lentils, blankets, or iron items.</b><br><br>
        <b>3. Chant the Shani Beej Mantra:</b><br><i style='color:#1761bd;'>Om Praam Preem Praum Sah Shanaischaraya Namah</i><br><br>
        <b>4. Recite Dasharatha Krit Shani Stotra.</b><br><br>
        <b>5. Worship and circumambulate the Peepal tree.</b><br><br>
        <b>6. Serve poor, disabled, and elderly people.</b><br><br>
        <b>7. Observe a disciplined Saturday fast.</b><br><br>
        <b>8. Recite Hanuman Chalisa or Bajrang Baan.</b><br><br>
        <b>9. Chant the Mahamrityunjaya Mantra.</b>
        """

    def _render_report(self) -> None:
        planets = self._data.get("planets", []) if isinstance(self._data, dict) else []
        moon = next((p for p in planets if p.get("name") == "Moon"), {})
        saturn = next((p for p in planets if p.get("name") == "Saturn"), {})
        try:
            moon_sign = int(moon.get("sign_number", 1) or 1)
        except (TypeError, ValueError):
            moon_sign = 1
        birth = _parse_birth_datetime(self._data)

        if not saturn or birth is None:
            self._browser.setHtml(
                f"<p style='color:{COLOR_TEXT_MUTED};font-size:14px;padding:20px;'>"
                + ("कुण्डली गणना गरेपछि विस्तृत गोचर चक्र देखिनेछ।" if self._is_ne else "Calculate a chart to view detailed transit cycles.")
                + "</p>"
            )
            return

        stages = self._timeline(moon_sign, saturn, birth)
        cycles = self._cycles(stages, self._active_tab)
        now = dt.datetime.now()
        heading = ("साढे साती गोचर चक्रहरू" if self._is_ne else "Sade Sati Transit Cycles") if self._active_tab == "sade" else ("अढैया गोचर चक्रहरू" if self._is_ne else "Adhaiya Transit Cycles")
        cycle_html, _active_key, upcoming_key = self._cycle_html(cycles, now)

        effects_title = "साढे साती र अढैयाको शास्त्रीय प्रभाव" if self._is_ne else "Classical Effects"
        remedies_title = "🪔 साढे साती र अढैयाका सरल वैदिक उपचारहरू" if self._is_ne else "🪔 Vedic Remedies"
        definition = (
            "पञ्चाङ्ग परिभाषा: ज्योतिष शास्त्रमा साढे सातीको अर्थ शनिको गोचर चन्द्र राशिभन्दा एक भाव अगाडि (१२ औं), चन्द्र राशिमा (१ औं) र एक भाव पछाडि (२ औं) हुँदाको ७.५ वर्षको कुल अवधि हो।"
            if self._is_ne else
            "Astrological Definition: Sade Sati is Saturn's transit through the 12th, 1st, and 2nd signs from the natal Moon, lasting about 7.5 years."
        )

        def section(title: str, body: str) -> str:
            return (
                f"<h3 style='color:{COLOR_GOLD};font-size:15px;font-weight:700;"
                f"margin:22px 0 8px 0;border-bottom:2px solid #e2e8f0;padding-bottom:5px;'>"
                f"{title}</h3>"
                f"<div style='font-size:13.5px;line-height:1.75;color:{COLOR_TEXT_SECONDARY};'>{body}</div>"
            )

        full_html = f"""
        <!DOCTYPE html><html><head><meta charset='utf-8'>
        <style>
            body {{ font-family:'Segoe UI','Noto Sans Devanagari',sans-serif;
                   color:{COLOR_TEXT_SECONDARY}; background:{BG_PRIMARY};
                   margin:0; padding:10px 4px; }}
            h3  {{ margin:20px 0 6px 0; }}
            p   {{ margin:6px 0 10px 0; }}
            b   {{ color:{COLOR_TEXT_PRIMARY}; }}
        </style></head><body>
        {section(heading, cycle_html)}
        {section(effects_title, self._effects_html())}
        {section(remedies_title, self._remedies_html())}
        {section('परिभाषा' if self._is_ne else 'Definition', definition)}
        </body></html>
        """

        self._browser.setHtml(full_html)
        # highlight upcoming cycle
        if upcoming_key:
            QTimer.singleShot(80, lambda: self._focus_upcoming(self._browser, upcoming_key))

    def refresh(self, data: dict) -> None:
        self._data = data or {}
        self._style_tabs()
        self._render_report()
