"""Native full-text classical Jyotish book reader (प्राचीन ग्रन्थ).

Shows the complete verbatim text of classical texts that were imported from
authoritative Internet Archive digital scans into frontend/public/. Only the
authentic book text is rendered — no analysis or invented content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# (book_id, relative dir under frontend/public, filename, nepali label, english label)
_CLASSICAL_BOOKS: tuple = (
    (
        "classical_bphs",
        "bphs",
        "bphs_nepali_text.txt",
        "बृहत् पराशर होरा शास्त्र",
        "Brihat Parashara Hora Shastra",
    ),
    (
        "classical_saravali",
        "saravali",
        "saravali_english_text.txt",
        "कल्याण वर्माको सारावली",
        "Kalyan Verma's Saravali",
    ),
    (
        "classical_phaladeepika",
        "phaladeepika",
        "phaladeepika_english_text.txt",
        "मन्त्रेश्वरको फलदीपिका",
        "Mantreswara's Phaladeepika",
    ),
    (
        "classical_jataka",
        "jataka_parijata",
        "jataka_parijata_english_text.txt",
        "जातक पारिजात",
        "Jataka Parijata",
    ),
)

# Subdirectories are mirrored exactly under both source and PyInstaller roots.
_BOOK_DIRS: tuple = tuple(entry[1] for entry in _CLASSICAL_BOOKS)

_STRINGS = {
    "title": {"ne": "प्राचीन ग्रन्थ", "en": "Classical References"},
    "close": {"ne": "← पेज बन्द गर्नुहोस्", "en": "← Close page"},
    "highlight": {"ne": "चयन गरिएको पाठ highlight गर्नुहोस्", "en": "Highlight selected text"},
    "color": {"ne": "Highlight रंग", "en": "Highlight colour"},
    "load_fail": {"ne": "पुस्तक पाठ लोड गर्न सकिएन", "en": "Unable to load the book text"},
    "source_note": {
        "ne": "पाठ Internet Archive को आधिकारिक स्क्यानबाट यथावत् आयात गरिएको हो (OCR-जन्य अशुद्धि सम्भव)। यहाँ कुनै कल्पित/अनुमानित विश्लेषण राखिएको छैन।",
        "en": "Text imported verbatim from the authoritative Internet Archive scan (OCR noise may remain). No fabricated or assumed analysis is included.",
    },
    # Jataka Parijata, Nepali UI: the verbatim Sanskrit/Hindi (Devanagari) text
    # imported from the user's digital RTF edition (भाग १ — सौरभ भाष्य). Only the
    # layout is reformatted (larger, clearer letters); no word is changed and no
    # translation is fabricated.
    "jataka_devangari_source": {
        "ne": "जातक पारिजातको प्रमाणित नेपाली अनुवाद समावेश नगरिएकाले नेपाली चयन गर्दा मूल संस्कृत/हिन्दी पाठ (देवनागरी) नै यथावत् देखाइन्छ — कुनै अनुवाद गरिएको छैन। पाठ श्री वैद्यनाथ प्रणीत 'जातक पारिजात' (भाग १ — सौरभ भाष्य) को डिजिटल प्रति (RTF) बाट आयात गरिएको हो; ढाँचा मिलाएर अलि ठुला र स्पष्ट अक्षरमा प्रस्तुत गरिएको छ।",
        "en": "Because no certified Nepali translation is bundled, the original Sanskrit/Hindi text (Devanagari) is shown verbatim when Nepali is selected — no translation is fabricated. Imported from the digital RTF edition of Jataka Parijata (Part 1, Saubhagya Bhashya) by Shri Vaidyanatha; reformatted only for larger, clearer letters.",
    },
    # Honest note shown only when the selected UI language differs from the
    # language of the authentic bundled text — never a fabricated translation.
    "edition_en_only": {
        "ne": "नोट: यहाँ देखाइएको पाठ यस ग्रन्थको आधिकारिक अङ्ग्रेजी संस्करण हो। नेपाली भाषा चयन भए पनि प्रमाणित नेपाली अनुवाद समावेश नभएकाले मौलिक अङ्ग्रेजी पाठ नै देखाइन्छ — कुनै कल्पित वा अनुमानित अनुवाद राखिएको छैन।",
        "en": "Note: the text shown here is the authoritative English edition of this work. Even when Nepali is selected, the verbatim English text is displayed because no certified Nepali translation is bundled — no fabricated translation is included.",
    },
    "edition_ne_only": {
        "ne": "नोट: यहाँ देखाइएको पाठ यस ग्रन्थको आधिकारिक नेपाली (देवनागरी) संस्करण हो। अङ्ग्रेजी भाषा चयन भए पनि प्रमाणित अङ्ग्रेजी संस्करण समावेश नभएकाले मौलिक नेपाली पाठ नै देखाइन्छ — कुनै कल्पित वा अनुमानित अनुवाद राखिएको छैन।",
        "en": "Note: the text shown here is the authoritative Nepali (Devanagari) edition of this work. Even when English is selected, the verbatim Nepali text is displayed because no certified English edition is bundled — no fabricated translation is included.",
    },
}

# Fixed edition language for books that ship exactly one authentic edition in
# every UI language (English-only Saravali/Phaladeepika; Nepali-only BPHS).
# Jataka Parijata is intentionally absent here: it ships a *matching* authentic
# edition per UI language (Nepali → Devanagari Sanskrit/Hindi RTF text; English
# → Subrahmanya Sastri OCR text), so no mismatch note can ever apply to it.
_EDITION_LANGUAGE_BY_ID: dict = {"classical_bphs": "ne"}

# Books whose bundled authentic edition always matches the selected UI language.
_LANGUAGE_MATCHING_BOOKS: frozenset = frozenset({"classical_jataka"})

# Per-language filenames for language-matching books — overrides the default
# filename from _CLASSICAL_BOOKS for that (book_id, UI language) combination.
_EDITION_FILENAME_BY_BOOK_LANG: dict = {
    ("classical_jataka", "ne"): "jataka_parijata_devangari_text.txt",
    ("classical_jataka", "en"): "jataka_parijata_english_text.txt",
}


def _book_path(book_dir: str, filename: str) -> Path:
    """Resolve a book beside both source and PyInstaller application roots."""
    root = Path(__file__).resolve().parents[2]
    candidates = (
        root / "public" / book_dir / filename,
        Path.cwd() / "public" / book_dir / filename,
        root / "frontend" / "public" / book_dir / filename,
        Path.cwd() / "frontend" / "public" / book_dir / filename,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


class ClassicalReferencePage(QWidget):
    """Display only the complete selectable book text for one classical text."""

    close_requested = Signal()

    def __init__(self, data: Optional[dict], language: str = "ne",
                 book_id: str = "classical_bphs", parent=None):
        super().__init__(parent)
        self._language = language
        self._book_id = book_id
        book = next((entry for entry in _CLASSICAL_BOOKS if entry[0] == book_id), _CLASSICAL_BOOKS[0])
        self._book_dir = book[1]
        # Language-matching books resolve their file by the selected UI language.
        self._book_filename = _EDITION_FILENAME_BY_BOOK_LANG.get((book_id, language), book[2])
        self._book_title = book[3] if language == "ne" else book[4]
        self._browser = QTextEdit()
        self._highlight_color = QColor("#fff09a")
        self._build_ui()
        self.refresh(data)

    def _ui_text(self, key: str) -> str:
        return _STRINGS[key]["ne" if self._language == "ne" else "en"]

    def _text_language(self) -> str:
        """Language of the authentic edition actually bundled for this page.

        Language-matching books (Jataka Parijata) load an edition that follows
        the selected UI language; every other book ships one fixed edition."""
        if self._book_id in _LANGUAGE_MATCHING_BOOKS:
            return self._language
        return _EDITION_LANGUAGE_BY_ID.get(self._book_id, "en")

    def _edition_mismatch_note(self) -> str:
        """Honest bilingual note when the UI language differs from the language
        of the authentic bundled edition (English-only books; Nepali-only BPHS).
        Never a fabricated translation."""
        text_lang = self._text_language()
        if text_lang == "en" and self._language == "ne":
            return _STRINGS["edition_en_only"]["ne"]
        if text_lang == "ne" and self._language == "en":
            return _STRINGS["edition_ne_only"]["en"]
        return ""

    def _is_devanagari(self) -> bool:
        """True when the bundled text is Devanagari script (BPHS always; Jataka
        Parijata only while the Nepali UI language is selected)."""
        if self._book_id in _LANGUAGE_MATCHING_BOOKS:
            return self._language == "ne"
        return self._book_id == "classical_bphs"

    def _font_family(self) -> str:
        # English OCR texts read best in a serif book face, while Devanagari
        # editions (BPHS; Jataka Parijata in Nepali) need a Devanagari font.
        return (
            "'Noto Sans Devanagari', 'Nirmala UI', 'Mangal', 'Kokila', sans-serif"
            if self._is_devanagari()
            else "Georgia, 'Times New Roman', 'Noto Sans Devanagari', "
            "'Nirmala UI', 'Mangal', serif"
        )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        self.setStyleSheet("background: #ffffff; color: #111111;")

        # Book heading: title + provenance, matching the web reader
        heading = QLabel(f"<b style='font-size:22px;'>{self._book_title}</b>")
        heading.setTextFormat(Qt.RichText)
        layout.addWidget(heading)
        if self._book_id in _LANGUAGE_MATCHING_BOOKS and self._language == "ne":
            # Jataka Parijata (Nepali UI): verbatim Sanskrit/Hindi Devanagari text.
            source = QLabel(_STRINGS["jataka_devangari_source"]["ne"])
        else:
            source = QLabel(self._ui_text("source_note"))
        source.setWordWrap(True)
        source.setStyleSheet("color: #555555; font-size: 13px;")
        layout.addWidget(source)

        mismatch_note = self._edition_mismatch_note()
        if mismatch_note:
            note = QLabel(mismatch_note)
            note.setWordWrap(True)
            note.setStyleSheet(
                "color: #5a4632; background: #fdf6e3; border: 1px solid #e0cda0; "
                "border-radius: 4px; padding: 8px 10px; font-size: 13px;"
            )
            layout.addWidget(note)

        tools = QHBoxLayout()
        close_button = QPushButton(self._ui_text("close"))
        close_button.clicked.connect(self.close_requested.emit)
        tools.addWidget(close_button)
        tools.addStretch(1)
        highlight = QPushButton(self._ui_text("highlight"))
        highlight.clicked.connect(self._highlight_selection)
        tools.addWidget(highlight)
        color = QPushButton(self._ui_text("color"))
        color.clicked.connect(self._choose_highlight_color)
        tools.addWidget(color)
        layout.addLayout(tools)

        self._browser.setReadOnly(True)
        self._browser.setAcceptRichText(False)
        self._browser.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        # Larger, clearer letters for the Jataka Parijata Devanagari edition
        # (Nepali UI), mirroring the web reader's Devanagari-first style.
        dev_large = self._book_id in _LANGUAGE_MATCHING_BOOKS and self._language == "ne"
        font_size = 20 if dev_large else 17
        line_height = "200%" if dev_large else "180%"
        self._browser.setStyleSheet(
            "QTextEdit { background: #ffffff; color: #111111; border: none; "
            "padding: 4px 0; font-family: "
            f"{self._font_family()}"
            f"; font-size: {font_size}px; line-height: {line_height}; }}"
        )
        layout.addWidget(self._browser, 1)

    def refresh(self, data: Optional[dict]) -> None:
        """Load the complete imported book text; chart data is intentionally unused."""
        try:
            book_text = _book_path(self._book_dir, self._book_filename).read_text(encoding="utf-8")
        except OSError as exc:
            book_text = f"{self._ui_text('load_fail')}: {exc}"
        self._browser.setPlainText(book_text)
        self._browser.moveCursor(QTextCursor.Start)

    def _highlight_selection(self) -> None:
        cursor = self._browser.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setBackground(self._highlight_color)
            self._browser.mergeCurrentCharFormat(fmt)
            self._browser.setTextCursor(cursor)

    def _choose_highlight_color(self) -> None:
        color = QColorDialog.getColor(self._highlight_color, self, self._ui_text("color"))
        if color.isValid():
            self._highlight_color = color
            self._highlight_selection()


__all__ = ["ClassicalReferencePage", "_CLASSICAL_BOOKS"]
