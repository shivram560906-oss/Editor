"""Regression tests for the classical dasha engines.

The reference chart is the one used while auditing the Janmapatrika: a male
born on 2043-03-15 BS (1986-06-29 AD) at 09:15 in Nawalparasi West.  Its Moon
falls in Uttara Bhadrapada pada 4 and the Lagna is Leo with no graha in it.
"""

import datetime
import itertools
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend")
))

from calculator import dasha, yogini
from calculator.dasha_contract import validate_tree

MOON = 344.7034913728455
BIRTH = "1986-06-29"
TIME = "09:15:00"


class VimshottariReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.timeline = dasha.calculate_vimshottari_dasha(MOON, BIRTH, TIME)

    def test_mahadasha_sequence_and_birth_balance(self):
        self.assertEqual(
            [md["lord"] for md in self.timeline],
            ["Saturn", "Mercury", "Ketu", "Venus", "Sun",
             "Moon", "Mars", "Rahu", "Jupiter"],
        )
        self.assertEqual(sum(md["total_years"] for md in self.timeline), 120)
        first = self.timeline[0]
        self.assertTrue(first["is_partial"])
        self.assertEqual((first["start"], first["end"]), (BIRTH, "1989-04-15"))
        self.assertEqual(
            (self.timeline[1]["start"], self.timeline[1]["end"]),
            ("1989-04-15", "2006-04-15"),
        )
        self.assertTrue(all(not md["is_partial"] for md in self.timeline[1:]))

    def test_first_mahadasha_antardashas_mark_pre_birth_periods(self):
        first = self.timeline[0]
        antardashas = first["antardashas"]
        self.assertEqual(len(antardashas), 9)
        # Saturn's conceptual start is 1970-04-16; only Rahu and Jupiter are
        # still running at birth, the other seven antardashas ended earlier.
        self.assertEqual(
            [ad["is_before_birth"] for ad in antardashas],
            [True] * 7 + [False] * 2,
        )
        self.assertEqual(
            (antardashas[7]["lord"], antardashas[8]["lord"]),
            ("Rahu", "Jupiter"),
        )
        self.assertEqual(antardashas[-1]["end"], first["end"])
        self.assertEqual(len(first["children"]), 2)

    def test_every_mahadasha_has_a_complete_contiguous_ad_cycle(self):
        for mahadasha in self.timeline:
            antardashas = mahadasha["antardashas"]
            self.assertEqual(len(antardashas), 9, mahadasha["lord"])
            self.assertEqual(antardashas[0]["lord"], mahadasha["lord"])
            for previous, current in itertools.pairwise(antardashas):
                self.assertEqual(previous["end"], current["start"])
            self.assertEqual(antardashas[-1]["end"], mahadasha["end"])
        self.assertEqual(validate_tree(self.timeline), [])


class YoginiReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.timeline = yogini.calculate_yogini_dasha(MOON, BIRTH, TIME)

    def test_birth_period_is_partial_bhadrika(self):
        self.assertEqual(len(self.timeline), 24)
        first = self.timeline[0]
        self.assertEqual(first["name"], "Bhadrika")
        self.assertTrue(first["is_partial"])
        self.assertEqual((first["start"], first["end"]), (BIRTH, "1987-03-25"))
        self.assertEqual(
            (self.timeline[1]["name"], self.timeline[1]["start"]),
            ("Ulka", "1987-03-25"),
        )

    def test_birth_antardasha_is_dhanya_followed_by_bhramari(self):
        first = self.timeline[0]
        antardashas = first["antardashas"]
        self.assertEqual(len(antardashas), 8)
        self.assertEqual(
            [ad["name"] for ad in antardashas],
            ["Bhadrika", "Ulka", "Siddha", "Sankata",
             "Mangala", "Pingala", "Dhanya", "Bhramari"],
        )
        self.assertEqual(
            [ad["is_before_birth"] for ad in antardashas],
            [True] * 6 + [False] * 2,
        )
        # Dhanya began conceptually on 1986-04-04 and is still running at
        # birth; Bhramari keeps its full 5 * 4 / 36 year duration.
        dhanya, bhramari = antardashas[-2:]
        self.assertEqual((dhanya["start"], dhanya["end"]),
                         ("1986-04-04", "1986-09-03"))
        self.assertFalse(dhanya["is_before_birth"])
        self.assertEqual((bhramari["start"], bhramari["end"]),
                         ("1986-09-03", "1987-03-25"))
        self.assertEqual(bhramari["end"], first["end"])
        self.assertEqual(validate_tree(self.timeline), [])

    def test_child_duration_uses_weight_over_thirty_six(self):
        bhramari = self.timeline[0]["antardashas"][-1]
        days = (datetime.date.fromisoformat(bhramari["end"])
                - datetime.date.fromisoformat(bhramari["start"])).days
        # Bhramari weighs 4 years of the 36-year Yogini cycle and the parent
        # Bhadrika period is 5 years long.
        expected = 5 * 4 / 36 * 365.25
        self.assertAlmostEqual(days, expected, delta=2)

    def test_five_level_tree_starts_at_birth_and_is_valid(self):
        tree = yogini.calculate_yogini_dasha_five_level(
            MOON, BIRTH, TIME,
            current_date=datetime.date(2026, 11, 15),
        )
        self.assertEqual(tree[0]["yogini"], "Bhadrika")
        self.assertEqual(
            [child["yogini"] for child in tree[0]["children"]],
            ["Dhanya", "Bhramari"],
        )
        self.assertTrue(tree[0]["children"][0]["is_partial"])
        self.assertEqual(validate_tree(tree), [])


class AshtottariReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.timeline = dasha.calculate_ashtottari_dasha(
            MOON, BIRTH, TIME, lagna_occupied=False
        )

    def test_constants_match_bphs_eight_lord_scheme(self):
        self.assertEqual(
            [lord["years"] for lord in dasha.ASHTOTTARI_ORDER],
            [6, 15, 8, 17, 10, 19, 12, 21],
        )
        self.assertEqual(sum(
            lord["years"] for lord in dasha.ASHTOTTARI_ORDER
        ), dasha.ASHTOTTARI_TOTAL_YEARS)
        self.assertEqual(dasha.ASHTOTTARI_NAKSHATRA_GROUPS,
                         [4, 2, 4, 2, 4, 3, 4, 4])
        self.assertEqual(sum(dasha.ASHTOTTARI_NAKSHATRA_GROUPS), 27)
        self.assertNotIn(
            "Ketu", [lord["name"] for lord in dasha.ASHTOTTARI_ORDER]
        )

    def test_birth_period_rotates_from_krittika_or_ardra(self):
        def center(nakshatra_index):
            return (nakshatra_index + 0.5) / 27.0 * 360.0

        # Krittika and Ardra both begin the Sun group of four nakshatras.
        krittika = dasha._ashtottari_birth_period(center(2), False)
        ardra = dasha._ashtottari_birth_period(center(5), True)
        self.assertEqual(krittika[0], 0)
        self.assertAlmostEqual(krittika[1], 0.75)
        self.assertAlmostEqual(krittika[2], 5.25)
        self.assertEqual(ardra[0], 0)
        self.assertAlmostEqual(ardra[1], 0.75)
        self.assertAlmostEqual(ardra[2], 5.25)

        # Uttara Bhadrapada is the first Venus nakshatra when counting from
        # Krittika, but falls in Rahu's group when counting from Ardra.
        venus = dasha._ashtottari_birth_period(center(25), False)
        rahu = dasha._ashtottari_birth_period(center(25), True)
        self.assertEqual(venus[0], 7)
        self.assertAlmostEqual(venus[1], 2.625)
        self.assertAlmostEqual(venus[2], 18.375)
        self.assertEqual(rahu[0], 6)
        self.assertAlmostEqual(rahu[1], 4.5)
        self.assertAlmostEqual(rahu[2], 7.5)

    def test_reference_chart_starts_with_partial_venus(self):
        self.assertEqual(len(self.timeline), 8)
        self.assertEqual(
            [md["lord"] for md in self.timeline],
            ["Venus", "Sun", "Moon", "Mars",
             "Mercury", "Saturn", "Jupiter", "Rahu"],
        )
        first = self.timeline[0]
        self.assertTrue(first["is_partial"])
        self.assertEqual(first["total_years"], 21)
        self.assertEqual((first["start"], first["end"]),
                         (BIRTH, "2003-01-06"))
        self.assertEqual(
            (self.timeline[1]["start"], self.timeline[1]["end"]),
            ("2003-01-06", "2009-01-05"),
        )
        self.assertTrue(all(not md["is_partial"] for md in self.timeline[1:]))

    def test_partial_venus_keeps_only_post_birth_antardashas(self):
        children = self.timeline[0]["children"]
        self.assertEqual([child["lord"] for child in children], [
            "Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu",
        ])
        self.assertEqual(children[0]["start"], BIRTH)
        self.assertEqual(children[-1]["end"], self.timeline[0]["end"])
        self.assertEqual(validate_tree(self.timeline), [])

    def test_lagna_occupation_rotates_to_ardra(self):
        timeline = dasha.calculate_ashtottari_dasha(
            MOON, BIRTH, TIME, lagna_occupied=True
        )
        self.assertEqual(timeline[0]["lord"], "Rahu")
        self.assertEqual(timeline[0]["end"], "1992-12-07")
        self.assertEqual(timeline[1]["lord"], "Venus")
        self.assertNotIn("Ketu", [md["lord"] for md in timeline])
        self.assertEqual(validate_tree(timeline), [])


class TribhagiReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.timeline = dasha.calculate_tribhagi_dasha(MOON, BIRTH, TIME)

    def test_three_continuous_cycles_from_the_birth_cycle(self):
        self.assertEqual(len(self.timeline), 27)
        expected = [
            "Saturn", "Mercury", "Ketu", "Venus", "Sun",
            "Moon", "Mars", "Rahu", "Jupiter",
        ]
        self.assertEqual(
            [md["lord"] for md in self.timeline], expected * 3
        )
        self.assertTrue(self.timeline[0]["is_partial"])
        self.assertEqual(
            (self.timeline[0]["start"], self.timeline[0]["end"]),
            (BIRTH, "1987-06-05"),
        )
        self.assertTrue(all(not md["is_partial"] for md in self.timeline[1:]))
        # No cycle is skipped: every boundary meets the next one.
        for previous, current in itertools.pairwise(self.timeline):
            self.assertEqual(previous["end"], current["start"])
        self.assertEqual(self.timeline[9]["start"], self.timeline[8]["end"])
        self.assertEqual(self.timeline[18]["start"], self.timeline[17]["end"])

    def test_each_period_is_one_third_of_its_vimshottari_duration(self):
        expected = [
            19 / 3, 17 / 3, 7 / 3, 20 / 3, 6 / 3,
            10 / 3, 7 / 3, 18 / 3, 16 / 3,
        ] * 3
        for period, years in zip(self.timeline, expected):
            self.assertAlmostEqual(period["total_years"], years)
        self.assertEqual(validate_tree(self.timeline), [])

    def test_partial_first_period_keeps_post_birth_children(self):
        children = self.timeline[0]["children"]
        self.assertEqual([child["lord"] for child in children],
                         ["Rahu", "Jupiter"])
        self.assertEqual(children[0]["start"], BIRTH)
        self.assertEqual(children[-1]["end"], self.timeline[0]["end"])


if __name__ == "__main__":
    unittest.main()
