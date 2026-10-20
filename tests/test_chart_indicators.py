import unittest
from fusion.chart_indicators import (
    profile, history_stats, range_groups, residue_groups,
    reversal_pairs, random_match_distribution, validate
)

class ChartIndicatorsTest(unittest.TestCase):
    def setUp(self):
        self.draw = list(range(1,21))

    def test_profile(self):
        p = profile(self.draw)
        self.assertEqual(p["sum"],210)
        self.assertEqual(p["span"],19)
        self.assertEqual(p["odd"],10)
        self.assertEqual(p["small"],20)
        self.assertEqual(sum(p["color_counts"].values()),20)
        self.assertEqual(sum(p["element_counts"].values()),20)
        self.assertEqual(p["consecutive_pairs"],19)

    def test_group_counts(self):
        self.assertEqual(sum(profile(self.draw)["residue_counts"][5]),20)
        self.assertEqual(sum(profile(self.draw)["range_counts"][10]),20)
        self.assertEqual(len(residue_groups(3)),3)
        self.assertEqual(len(range_groups(10)),10)

    def test_history(self):
        h=history_stats([self.draw, list(range(21,41))])
        self.assertEqual(h["frequency"][1],1)
        self.assertEqual(h["omission"][1],1)
        self.assertEqual(h["omission"][21],0)
        self.assertEqual(h["expected_frequency"],0.5)
        self.assertEqual(history_stats([self.draw, list(range(21,41))],1)["draws"],1)

    def test_probability(self):
        dist=random_match_distribution(9)
        self.assertAlmostEqual(sum(dist.values()),1)
        self.assertAlmostEqual(sum(k*v for k,v in dist.items()),2.25)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            validate([1]*20)

    def test_reversal(self):
        pairs=reversal_pairs()
        self.assertIn((8,80),pairs)
        self.assertIn((26,62),pairs)

if __name__ == "__main__":
    unittest.main()
