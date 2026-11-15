# -*- coding: utf-8 -*-
"""
gui/widgets/gandanta_shanti.py

Native Gandanta & Arishta Janma Shanti page assembled from classical BPHS chapters 80-100.
Pure white background, high-contrast typography, and authoritative Vedic presentation.
"""
from __future__ import annotations
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QFrame

from gui.widgets.analysis_document import (
    add_chapter,
    add_state,
    build_plain_document,
    clear_document,
    WHITE,
    BLACK,
    MUTED,
    GOLD,
    DIVIDER
)
from gui.backend_bridge import calculate_gandanta_shanti


def build_gandanta_shanti_model(data: Optional[dict]) -> dict:
    """Builds the Gandanta and Shanti model from chart data."""
    if data is None:
        return {"state": "no_chart"}
    if not isinstance(data, dict):
        return {"state": "empty"}
    if data.get("error"):
        return {"state": "error", "message": str(data["error"])}

    lagna = data.get("lagna")
    planets = data.get("planets")
    if not lagna or not planets:
        return {"state": "empty"}

    # Run analysis
    res = calculate_gandanta_shanti(data, language="ne")
    if res.get("state") == "empty":
        return {"state": "empty"}
    return res


class GandantaShantiPage(QWidget):
    """
    Classical BPHS Gandanta and Arishta Janma Shanti Report Page.
    """

    def __init__(
        self,
        data: Optional[dict] = None,
        chart_data: Optional[dict] = None,
        language: str = "ne",
        parent=None
    ):
        super().__init__(parent)
        self._language = language
        self._is_ne = language == "ne"
        self._model: dict = {}
        self._header: Optional[QLabel] = None
        self._content_layout: Optional[QVBoxLayout] = None
        self._build_ui()
        actual_data = chart_data if chart_data is not None else data
        self.refresh(actual_data)


    def _text(self, ne: str, en: str) -> str:
        return ne if self._is_ne else en

    def _build_ui(self) -> None:
        self._header, self._content_layout = build_plain_document(self, "gandantaShantiHeader")

    def _clear(self) -> None:
        clear_document(self._content_layout)

    def _state(self, message: str, error: bool = False) -> None:
        add_state(self._content_layout, "gandantaShantiState", message, error)

    def refresh(self, data: Optional[dict]) -> None:
        self._model = build_gandanta_shanti_model(data)
        self._clear()
        state = self._model.get("state")
        if state == "no_chart":
            self._header.setText(self._text("गण्डान्त तथा अनिष्ट शान्ति", "Gandanta & Shanti Analysis"))
            self._state(self._text("कृपया पहिले जन्म कुण्डली गणना गर्नुहोस्।", "Calculate a birth chart first."))
            return
        if state == "error":
            self._header.setText(self._text("गण्डान्त तथा अनिष्ट शान्ति", "Gandanta & Shanti Analysis"))
            self._state(self._model.get("message", self._text("विश्लेषण गर्न सकिएन।", "Analysis failed.")), True)
            return
        if state != "success":
            self._header.setText(self._text("गण्डान्त तथा अनिष्ट शान्ति", "Gandanta & Shanti Analysis"))
            self._state(self._text("गण्डान्त विश्लेषणका लागि आवश्यक तथ्याङ्क उपलब्ध छैन।", "Required chart data is unavailable."))
            return

        m = self._model
        nak = m.get("nakshatra_gandanta", {})
        tithi = m.get("tithi_gandanta", {})
        lagna = m.get("lagna_gandanta", {})
        remedies = m.get("remedies")
        arishta_yogas = m.get("arishta_yogas", [])
        bhanga_reasons = m.get("bhanga_reasons", [])

        title_ne = (
            f"गण्डान्त तथा अनिष्ट जन्म-शान्ति निर्णय (BPHS अध्याय ८०–१००)\n"
            f"नक्षत्र: {nak.get('nakshatra_ne')} (चरण {nak.get('pada')}) | तिथि: {tithi.get('tithi_name')} | लग्न: {lagna.get('lagna_sign_name')}"
        )
        title_en = (
            f"Classical Gandanta & Arishta Janma Shanti (BPHS Ch. 80–100)\n"
            f"Nakshatra: {nak.get('nakshatra_name')} (Pada {nak.get('pada')}) | Tithi: {tithi.get('tithi_name')} | Ascendant: {lagna.get('lagna_sign_name')}"
        )
        self._header.setText(self._text(title_ne, title_en))

        # ── Banner / Summary Alert Box ─────────────────────────────────────────
        status_box = QLabel()
        status_box.setObjectName("gandantaStatusBanner")
        status_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        status_box.setWordWrap(True)
        status_color = m.get("status_color", "#15803d")
        status_text = m.get("overall_status", "दोषमुक्त")

        status_box.setText(
            f"<div style='background:#f8fafc; border-left:6px solid {status_color}; padding:14px 18px; border-radius:4px;'>"
            f"<span style='font-size:14px; color:{MUTED}; font-weight:600; text-transform:uppercase;'>समग्र गण्डान्त एवं अनिष्ट स्थिति:</span><br>"
            f"<span style='font-size:18px; font-weight:700; color:{status_color};'>{status_text}</span>"
            f"</div>"
        )
        self._content_layout.addWidget(status_box)

        # ── Chapter 1: गण्डान्त त्रिविध विचार (Threefold Gandanta) ────────────
        pada_phala = nak.get("pada_phala")
        pada_text = pada_phala.get("ne", "सामान्य फल") if pada_phala else "यस चरणमा कुनै विशिष्ट गण्डान्त दोष छैन।"

        ch1_html = (
            f"<b>१. नक्षत्र गण्डान्त विचार:</b><br>"
            f"• <b>जन्म नक्षत्र:</b> {nak.get('nakshatra_ne')} ({nak.get('nakshatra_name')}) — <b>चरण:</b> {nak.get('pada')}<br>"
            f"• <b>नक्षत्र स्थिति:</b> {nak.get('gandanta_level')}<br>"
            f"• <b>चरणगत शास्त्रीय फल (BPHS):</b> {pada_text}<br>"
            f"• <b>अभुक्त मूल सन्धिकाल:</b> {'<b>हो (अत्यन्त गम्भीर सन्धि)</b>' if nak.get('is_abhukta_moola') else 'छैन (सामान्य)'}<br>"
            f"• <b>जन्म काल भेद (Kala Bheda):</b> {nak.get('kala_bheda_ne')}<br><br>"
            f"<b>२. तिथि गण्डान्त विचार:</b><br>"
            f"• <b>जन्म तिथि:</b> {tithi.get('tithi_name')} ({tithi.get('deg_in_tithi')}° भुक्त)<br>"
            f"• <b>तिथि गण्डान्त अवस्था:</b> {tithi.get('gandanta_desc_ne')}<br><br>"
            f"<b>३. लग्न गण्डान्त विचार:</b><br>"
            f"• <b>जन्म लग्न:</b> {lagna.get('lagna_sign_name')} ({lagna.get('lagna_deg_in_sign')}° मा)<br>"
            f"• <b>लग्न गण्डान्त अवस्था:</b> {lagna.get('desc_ne')}<br>"
        )
        add_chapter(self._content_layout, "अध्याय १: गण्डान्त त्रिविध विचार (नक्षत्र, तिथि, लग्न)", ch1_html, "ch1")

        # ── Chapter 2: अनिष्ट जन्म दोषहरू (Arishta Janma Afflictions) ──────────
        if arishta_yogas:
            yogas_paragraphs = []
            for y in arishta_yogas:
                yogas_paragraphs.append(
                    f"<b>• {y['name']}</b> [{y['reference']}]<br>"
                    f"&nbsp;&nbsp;<b>कारण:</b> {y['condition']}<br>"
                    f"&nbsp;&nbsp;<b>शास्त्रीय प्रभाव:</b> {y['impact_ne']}<br>"
                    f"&nbsp;&nbsp;<b>उपचार:</b> {y['shanti_ne']}<br>"
                )
            ch2_html = "<br>".join(yogas_paragraphs)
        else:
            ch2_html = (
                "कुण्डलीमा अमावास्या जन्म, कृष्ण चतुर्दशी षष्ठ्यंश, संक्रान्ति जन्म, ग्रहण जनन वा त्रिखल दोष जस्ता "
                "कुनै पनि गम्भीर अनिष्ट जन्मदोषहरू फेला परेनन्। जन्म शुभ एवं सामान्य घडीमा भएको छ।"
            )
        add_chapter(self._content_layout, "अध्याय २: अनिष्ट जन्म दोष परीक्षण (अमावास्या, चतुर्दशी, संक्रान्ति, ग्रहण)", ch2_html, "ch2")

        # ── Chapter 3: दोष भंग तथा शुभाशुभ सन्तुलन (Arishta Bhanga) ─────────
        if bhanga_reasons:
            reasons_html = "<br><br>".join(f"• {r}" for r in bhanga_reasons)
            ch3_html = (
                f"<b>बृहत्पाराशर होराशास्त्र अनुसार दोष भंग योगहरू सक्रिय छन्:</b><br><br>"
                f"{reasons_html}<br><br>"
                f"<span style='color:{MUTED}'><i>शास्त्रीय प्रमाण:</i> 'यथा सिंहं समालोक्य पलायन्ते मृगा वने। "
                f"तद्वद् दोषाः पलायन्ते गुरुणा केन्द्रे स्थिते॥' (बृहस्पति वा शुभ ग्रह केन्द्रमा रहँदा हजारौं अनिष्ट नष्ट हुन्छन्)।</span>"
            )
        else:
            ch3_html = (
                "कुण्डलीमा केन्द्रमा देवगुरु बृहस्पति वा प्रमुख शुभ ग्रहको विशेष अरिष्ट-नाशक योग देखिएन। "
                "तसर्थ यदि कुनै गण्डान्त वा जन्मदोष विद्यमान भएमा शास्त्रीय विधिपूर्वक शान्ति-उपचार गर्नु लाभदायक हुन्छ।"
            )
        add_chapter(self._content_layout, "अध्याय ३: दोष भंग तथा शुभाशुभ सन्तुलन (Arishta Bhanga)", ch3_html, "ch3")

        # ── Chapter 4: शास्त्रीय शान्ति मन्त्र तथा वैदिक उपचार विधान ────────
        if remedies:
            materials_html = "<br>".join(f"• {m_item}" for m_item in remedies.get("materials", []))
            rules_html = "<br>".join(f"• {r_item}" for r_item in remedies.get("classical_rules", []))
            ch4_html = (
                f"<b>१. अधिष्ठाता देवता तथा मन्त्र:</b><br>"
                f"• <b>नक्षत्र देवता:</b> {remedies.get('deity')}<br>"
                f"• <b>वैदिक मन्त्र:</b> <code>{remedies.get('vedic_mantra')}</code><br>"
                f"• <b>तान्त्रिक / पौराणिक मन्त्र:</b> <b>{remedies.get('tantric_mantra')}</b> (जप संख्या: {remedies.get('japa_count')})<br>"
                f"• <b>गायत्री मन्त्र:</b> <i>{remedies.get('gayatri')}</i><br><br>"
                f"<b>२. शान्ति गर्ने उपयुक्त साइत:</b><br>"
                f"{remedies.get('timing_ne')}<br><br>"
                f"<b>३. आवश्यक शास्त्रीय पूजन एवं दान सामग्रीहरू:</b><br>"
                f"{materials_html}<br><br>"
                f"<b>४. पितृ मुखावलोकन नियम एवं शास्त्रीय प्रतिबन्धहरू:</b><br>"
                f"{rules_html}<br>"
            )
        else:
            ch4_html = (
                "जातकको जन्म कुनै पनि तीव्र गण्डान्त वा गम्भीर अनिष्ट दोषमा नभएकोले विशेष नक्षत्र शान्ति वा "
                "छाँयापात्र दानको आवश्यकता छैन। केवल सामान्य कुलदेवता पूजन, स्वस्तिवाचन र बालरक्षा मन्त्र जप पर्याप्त छ।"
            )
        add_chapter(self._content_layout, "अध्याय ४: शास्त्रीय शान्ति मन्त्र तथा वैदिक उपचार विधान", ch4_html, "ch4")
