import unittest
from fusion.chart_trends import transition_labels, draw_streaks, category_trend

class ChartTrendsTests(unittest.TestCase):
    def test_neighbors_and_repeats(self):
        old=list(range(1,21))
        new=list(range(2,22))
        labels=transition_labels(new,old)
        self.assertEqual(labels["repeat"],list(range(2,21)))
        self.assertEqual(labels["new"],[21])
        self.assertIn(21,labels["adjacentNew"])
        self.assertEqual(transition_labels(old,None)["repeat"],[])

    def test_streaks(self):
        first=list(range(1,21))
        second=list(range(21,41))
        stats=draw_streaks([first,first,second,first])
        self.assertEqual(stats[1]["currentRun"],1)
        self.assertEqual(stats[1]["maxObservedRun"],2)
        self.assertEqual(stats[1]["completedRuns"],1)
        self.assertEqual(stats[1]["meanCompletedRun"],2)
        self.assertEqual(stats[21]["currentRun"],0)
        self.assertEqual(stats[21]["maxObservedRun"],1)

    def test_distribution(self):
        first=list(range(1,21))
        second=list(range(2,22))
        rows=category_trend([first,second])
        self.assertEqual(len(rows),2)
        self.assertFalse(rows[0]["overlapKnown"])
        self.assertTrue(rows[1]["overlapKnown"])
        self.assertEqual(rows[1]["repeat"],19)
        self.assertEqual(sum(rows[1]["decadeDistribution"]),20)
        self.assertEqual(sum(rows[1]["tailDistribution"]),20)
        self.assertEqual(rows[1]["odd"]+rows[1]["even"],20)

if __name__=="__main__":
    unittest.main()
