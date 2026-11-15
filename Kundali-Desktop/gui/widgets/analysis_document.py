# -*- coding: utf-8 -*-
"""Shared plain-document presentation helpers for native Life Analysis reports."""
from __future__ import annotations

from html import escape
from typing import Any, Iterable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget


WHITE = "#ffffff"
BLACK = "#111111"
MUTED = "#444444"
ERROR = "#a61b1b"
GOLD  = "#92400e"
DIVIDER = "#e2e8f0"


def build_plain_document(page: QWidget, header_object_name: str) -> tuple[QLabel, QVBoxLayout]:
    """Create a white, borderless, selectable report surface."""
    page.setObjectName("lifeAnalysisDocumentPage")
    page.setStyleSheet("QWidget#lifeAnalysisDocumentPage { background: #ffffff; }")

    root = QVBoxLayout(page)
    root.setContentsMargins(22, 16, 22, 16)
    root.setSpacing(10)

    header = QLabel()
    header.setObjectName(header_object_name)
    header.setWordWrap(True)
    header.setTextInteractionFlags(Qt.TextSelectableByMouse)
    header.setStyleSheet(
        "background: #ffffff; color: #111111; border: none; padding: 4px 0 12px 0; "
        "font-size: 22px; font-weight: 700; line-height: 1.4;"
    )
    root.addWidget(header)

    scroll = QScrollArea()
    scroll.setObjectName("lifeAnalysisDocumentScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.setStyleSheet(
        "QScrollArea#lifeAnalysisDocumentScroll, QScrollArea#lifeAnalysisDocumentScroll > QWidget, "
        "QScrollArea#lifeAnalysisDocumentScroll > QWidget > QWidget { background: #ffffff; border: none; }"
    )
    container = QWidget()
    container.setObjectName("lifeAnalysisDocumentBody")
    container.setStyleSheet("QWidget#lifeAnalysisDocumentBody { background: #ffffff; }")
    content = QVBoxLayout(container)
    content.setContentsMargins(0, 0, 8, 20)
    content.setSpacing(14)
    scroll.setWidget(container)
    root.addWidget(scroll, 1)
    return header, content


def clear_document(layout: Optional[QVBoxLayout]) -> None:
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


def add_state(layout: QVBoxLayout, object_name: str, message: str, error: bool = False) -> QLabel:
    label = QLabel(message)
    label.setObjectName(object_name)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    label.setStyleSheet(
        f"background: {WHITE}; color: {ERROR if error else BLACK}; border: none; "
        "padding: 48px 12px; font-size: 16px;"
    )
    layout.addWidget(label)
    return label


def add_section(
    layout: QVBoxLayout,
    title: str,
    rows: Iterable[tuple[str, str, Optional[str]]],
    object_prefix: str,
) -> None:
    """Render one report section as a heading followed by prose, without a card/frame."""
    heading = QLabel(title)
    heading.setObjectName(f"{object_prefix}SectionHeading")
    heading.setWordWrap(True)
    heading.setTextInteractionFlags(Qt.TextSelectableByMouse)
    heading.setStyleSheet(
        "background: #ffffff; color: #111111; border: none; padding: 8px 0 2px 0; "
        "font-size: 17px; font-weight: 700;"
    )
    layout.addWidget(heading)

    paragraphs = []
    for label, value, detail in rows:
        paragraph = f"<b>{escape(str(label))}:</b> {escape(str(value))}"
        if detail:
            paragraph += f"<br><span style='color:{MUTED}'>{escape(str(detail))}</span>"
        paragraphs.append(paragraph)
    body = QLabel("<br><br>".join(paragraphs))
    body.setObjectName(f"{object_prefix}SectionBody")
    body.setTextFormat(Qt.RichText)
    body.setWordWrap(True)
    body.setTextInteractionFlags(Qt.TextSelectableByMouse)
    body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    body.setStyleSheet(
        "background: #ffffff; color: #111111; border: none; padding: 0 0 10px 0; "
        "font-size: 16px; line-height: 1.6;"
    )
    layout.addWidget(body)


def add_chapter(
    layout: QVBoxLayout,
    title: str,
    content_html: str,
    object_prefix: str,
) -> None:
    """Render a narrative chapter: gold left-bar heading + flowing paragraph body."""
    heading = QLabel(title)
    heading.setObjectName(f"{object_prefix}ChapterHeading")
    heading.setWordWrap(True)
    heading.setTextInteractionFlags(Qt.TextSelectableByMouse)
    heading.setStyleSheet(
        f"background: {WHITE}; color: {GOLD}; border: none; "
        f"border-left: 5px solid {GOLD}; padding: 8px 0 6px 12px; "
        "font-size: 17px; font-weight: 700;"
    )
    layout.addWidget(heading)

    html = content_html.replace("\n", "<br>")
    body = QLabel(html)
    body.setObjectName(f"{object_prefix}ChapterBody")
    body.setTextFormat(Qt.RichText)
    body.setWordWrap(True)
    body.setTextInteractionFlags(Qt.TextSelectableByMouse)
    body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    body.setStyleSheet(
        f"background: {WHITE}; color: {BLACK}; border: none; "
        "padding: 4px 0 18px 0; font-size: 16px; line-height: 1.8; "
        "font-family: 'Segoe UI', 'Noto Sans Devanagari', sans-serif;"
    )
    layout.addWidget(body)

    line = QFrame()
    line.setObjectName(f"{object_prefix}ChapterDivider")
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {DIVIDER}; border: none; border-top: 1px solid {DIVIDER}; margin: 2px 0 6px 0;")
    layout.addWidget(line)


def render_narrative(
    layout: QVBoxLayout,
    chapters: list[dict],
    object_prefix: str,
) -> None:
    """Render a list of ``{'title': str, 'content': str}`` chapter dicts."""
    for chapter in chapters:
        add_chapter(layout, chapter.get("title", ""), chapter.get("content", ""), object_prefix)


def dasha_timeline(value: Any) -> list[dict]:
    """Return only real payload periods; never synthesize ages or missing dates."""
    if not isinstance(value, list):
        return []
    timeline = []
    for period in value:
        if not isinstance(period, dict):
            continue
        children = period.get("children") if isinstance(period.get("children"), list) else []
        timeline.append({
            "lord": period.get("lord"),
            "start": period.get("start_bs") or period.get("start"),
            "end": period.get("end_bs") or period.get("end"),
            "is_active": bool(period.get("is_active")),
            "children": [
                {
                    "lord": child.get("lord"),
                    "start": child.get("start_bs") or child.get("start"),
                    "end": child.get("end_bs") or child.get("end"),
                    "is_active": bool(child.get("is_active")),
                }
                for child in children
                if isinstance(child, dict)
            ],
        })
    return timeline


def timeline_rows(
    periods: list[dict],
    planet_name,
    text,
) -> list[tuple[str, str, Optional[str]]]:
    """Format authoritative Mahadasha/Antardasha payload dates for document pages."""
    if not periods:
        return [(
            text("जन्मदेखि १२० वर्षसम्मको दशा क्रम", "Dasha sequence from birth to age 120"),
            text("पूर्ण मिति-सहितको दशा क्रम उपलब्ध छैन", "A complete dated Dasha sequence is unavailable"),
            text(
                "उपलब्ध नभएको उमेर वा अवधि अनुमान गरेर थपिएको छैन।",
                "Missing ages or periods have not been estimated or invented.",
            ),
        )]
    rows = []
    for period in periods:
        lord = planet_name(period.get("lord")) if period.get("lord") else text("अज्ञात", "Unknown")
        start = period.get("start") or "-"
        end = period.get("end") or "-"
        active = text(" (हाल सक्रिय)", " (currently active)") if period.get("is_active") else ""
        children = []
        for child in period.get("children", []):
            child_lord = planet_name(child.get("lord")) if child.get("lord") else text("अज्ञात", "Unknown")
            child_dates = f"{child.get('start') or '-'} → {child.get('end') or '-'}"
            child_active = text(" सक्रिय", " active") if child.get("is_active") else ""
            children.append(f"{child_lord}: {child_dates}{child_active}")
        detail = "; ".join(children) if children else text("अन्तर्दशा मिति उपलब्ध छैन", "Antardasha dates are unavailable")
        rows.append((
            text("महादशा", "Mahadasha"),
            f"{lord}: {start} → {end}{active}",
            detail,
        ))
    return rows
