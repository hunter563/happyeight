import unittest
from fusion.chart_special import special_groups,special_profile,REVERSED

class SpecialChartTest(unittest.TestCase):
    def test_groups(self):
        groups=special_groups()
        self.assertEqual(set(groups["double"]),{11,22,33,44,55,66,77})
        self.assertEqual(len(groups["sum81_1"]),20)
        self.assertEqual(sorted(set().union(*(set(groups["sum81_"+str(i)]) for i in range(1,5)))),list(range(1,81)))
        self.assertIn((8,80),REVERSED)
        self.assertIn((26,62),REVERSED)
        self.assertFalse(set(groups["neither"]) & set(groups["reverse"]))
        self.assertFalse(set(groups["neither"]) & set(groups["double"]))
        self.assertEqual(len(set(groups["neither"])|set(groups["reverse"])|set(groups["double"])),80)
        self.assertEqual(sum(len(groups["element_"+k]) for k in ("metal","wood","water","fire","earth")),80)
        self.assertEqual(sum(len(groups["color_"+k]) for k in ("red","blue","green")),80)

    def test_profile(self):
        result=special_profile(list(range(1,21)))
        self.assertEqual(sum(result["sum81_"+str(i)] for i in range(1,5)),20)
        self.assertEqual(sum(result["color_"+k] for k in ("red","blue","green")),20)
        self.assertEqual(result["double"],1)

if __name__=="__main__":
    unittest.main()
