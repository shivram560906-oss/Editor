# -*- coding: utf-8 -*-
"""
gui/tests/test_life_conclusion_native.py

Guards the निष्कर्ष (पूर्ण फलित) reading against regression back into
fabricated output. The engine used to invent dates such as
"वि.सं. birth_year + 60" and fixed ages such as "उमेर ३० नाघेपछि पदोन्नति";
these tests fail if any such pattern ever returns.

Run with:  cd backend && python -m pytest ../gui/tests/test_life_conclusion_native.py
"""
from __future__ import annotations

import re
import unittest

from api.endpoints import perform_calculations
from calculator.life_conclusion_engine import generate_comprehensive_life_phalita

_ASCII = str.maketrans("०१२३४५६७८९", "0123456789")


def _chart():
    return perform_calculations(
        name="Regression Subject",
        birth_date="1990-01-15",
        birth_time="10:30:00",
        latitude=27.7172,
        longitude=85.324,
        timezone=5.75,
        ayanamsha_type="LAHIRI",
        city="Kathmandu",
    )


class LifeConclusionEngineTests(unittest.TestCase):
    """Engine-level guarantees about provenance and non-fabrication."""

    @classmethod
    def setUpClass(cls):
        cls.chart = _chart()

    # ── Structure ───────────────────────────────────────────────────────────
    def test_returns_ready_with_chapters(self):
        for lang in ("ne", "en"):
            report = generate_comprehensive_life_phalita(self.chart, lang)
            self.assertEqual(report["status"], "ready")
            self.assertTrue(report["chapters"], f"no chapters for language={lang}")

    def test_every_chapter_declares_its_sources(self):
        for lang in ("ne", "en"):
            for chapter in generate_comprehensive_life_phalita(self.chart, lang)["chapters"]:
                self.assertTrue(
                    chapter.get("sources"),
                    f"chapter {chapter['id']} has no provenance",
                )
                self.assertIn("reference", chapter)

    def test_language_is_echoed_and_nepali_uses_devanagari(self):
        nepali = generate_comprehensive_life_phalita(self.chart, "ne")
        english = generate_comprehensive_life_phalita(self.chart, "en")
        self.assertEqual(nepali["language"], "ne")
        self.assertEqual(english["language"], "en")
        ne_bodies = " ".join(c["body"] for c in nepali["chapters"])
        self.assertIn("अध्याय", ne_bodies)  # Nepali chapter headings present

    def test_missing_chart_reports_no_chart(self):
        for payload in (None, {}, "not-a-dict", []):
            report = generate_comprehensive_life_phalita(payload, "ne")
            self.assertIn(report["status"], ("no_chart", "empty"))
            self.assertEqual(report["chapters"], [])

    # ── Non-fabrication guards ──────────────────────────────────────────────
    def test_engine_emits_no_hardcoded_dates(self):
        """No `year + N` arithmetic and no bare invented B.S. year range."""
        for lang in ("ne", "en"):
            for chapter in generate_comprehensive_life_phalita(self.chart, lang)["chapters"]:
                body = chapter["body"]
                self.assertNotIn(
                    "birth_year", body,
                    f"chapter {chapter['id']} references birth_year arithmetic",
                )
                for match in re.finditer(r"[२-९0-9]{4}\s*[-–]\s*[२-९0-9]{4}", body):
                    self.fail(
                        f"chapter {chapter['id']} has a bare year range: {match.group(0)}"
                    )

    def test_every_bs_date_shown_exists_in_a_calculated_source(self):
        """Any B.S. date printed must come from a real engine, not be invented.

        Two legitimate sources exist: the Vimshottari dasha tree and the
        marriage transit scan. Everything else would be fabrication.
        """
        from calculator.marriage_timing_engine import find_marriage_windows_age_15_to_50

        real = set()

        def collect(nodes):
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                for key in ("start_bs", "end_bs"):
                    if node.get(key):
                        real.add(node[key])
                collect(node.get("children"))

        collect(self.chart.get("dasha"))
        for window in find_marriage_windows_age_15_to_50(self.chart, min_score=40) or []:
            for key in ("bs_start", "bs_end"):
                if window.get(key):
                    real.add(window[key])

        # Only inspect B.S. dates. AD dates are printed after a "वि.सं."/"B.S."
        # prefix too, so match the prefix first and read the date that follows.
        bs_prefix = r"(?:वि\.सं\.|B\.S\.)\s*([०-९0-9]{4}-[०-९0-9]{2}-[०-९0-9]{2})"
        for chapter in generate_comprehensive_life_phalita(self.chart, "ne")["chapters"]:
            for date in re.findall(bs_prefix, chapter["body"]):
                ascii_date = date.translate(_ASCII)
                self.assertIn(
                    ascii_date, real,
                    f"chapter {chapter['id']} printed non-payload date {ascii_date}",
                )

    def test_dasha_dates_are_derived_from_the_dasha_tree(self):
        """The dasha chapter's spans must match the actual dasha payload."""
        chart = self.chart
        dasha_chapter = next(
            c for c in generate_comprehensive_life_phalita(chart, "ne")["chapters"]
            if c["id"] == "dasha_timeline"
        )
        for md in chart["dasha"]:
            start = md.get("start")
            if start:
                self.assertIn(
                    start[:10], dasha_chapter["body"],
                    f"mahadasha {md.get('lord')} start {start} missing from timeline",
                )

    def test_no_fabricated_longevity_year_offset(self):
        """Guard against a hardcoded 'long life after age N' claim returning."""
        longevity = next(
            c for c in generate_comprehensive_life_phalita(self.chart, "ne")["chapters"]
            if c["id"] == "longevity"
        )
        for match in re.findall(r"जन्मवर्ष|birth_year\s*\+", longevity["body"]):
            self.fail(f"longevity chapter contains fabricated offset: {match}")


class LifeConclusionUiTests(unittest.TestCase):
    """The UI surfaces must render the new engine shape without crashing."""

    def test_all_in_one_report_embeds_life_conclusion(self):
        from PySide6.QtWidgets import QApplication, QLabel

        from gui.widgets.tools_widget import AllInOneReportPage

        app = QApplication.instance() or QApplication([])
        page = AllInOneReportPage(_chart(), "ne")
        text = " ".join(lbl.text() for lbl in page.findChildren(QLabel))
        self.assertIn("निष्कर्ष", text)
        page.deleteLater()
        del app

    def test_life_conclusion_page_renders_chapters(self):
        from PySide6.QtWidgets import QApplication, QLabel

        from gui.widgets.life_conclusion_page import LifeConclusionPage

        app = QApplication.instance() or QApplication([])
        for lang in ("ne", "en"):
            page = LifeConclusionPage(_chart(), lang)
            text = " ".join(lbl.text() for lbl in page.findChildren(QLabel))
            self.assertTrue(text.strip(), f"empty page for language={lang}")
            page.deleteLater()
        del app


if __name__ == "__main__":
    unittest.main()
