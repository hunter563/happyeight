import unittest
from fusion.chart_series import chart_series, is_prime, omission_summary, position_profile

class ChartSeriesTest(unittest.TestCase):
    def test_prime_convention(self):
        self.assertTrue(is_prime(1))
        self.assertTrue(is_prime(2))
        self.assertFalse(is_prime(4))
    def test_series(self):
        d1={"issue":"2026001","date":"2026-01-01","numbers":list(range(1,21))}
        d2={"issue":"2026002","date":"2026-01-02","numbers":list(range(2,22))}
        out=chart_series([d1,d2],30)
        self.assertEqual(out["count"],2)
        self.assertEqual(out["rows"][0]["sum"],210)
        self.assertEqual(out["rows"][1]["repeatFromPrevious"],19)
        self.assertEqual(sum(out["rows"][0]["residues"]["18"]),20)
        self.assertEqual(out["rows"][0]["prime"],9)
    def test_omission_censoring(self):
        a=list(range(1,21))
        b=list(range(21,41))
        c=list(range(1,21))
        summary=omission_summary([a,b,c])
        self.assertEqual(summary[1]["current"],0)
        self.assertEqual(summary[1]["previousCompleted"],1)
        self.assertEqual(summary[1]["maxCompleted"],1)
        self.assertEqual(summary[1]["avgCompleted"],1)
        self.assertEqual(summary[21]["current"],1)
        self.assertIsNone(summary[21]["avgCompleted"])
        self.assertEqual(omission_summary([])[1]["appearances"],0)

    def test_sorted_position(self):
        a=list(range(1,21))
        b=list(range(2,22))
        p=position_profile(b[::-1],a)
        self.assertEqual(len(p),20)
        self.assertEqual(p[0]["number"],2)
        self.assertEqual(p[0]["direction"],"up")
        self.assertEqual(p[0]["amplitude"],1)

    def test_bad_limit(self):
        with self.assertRaises(ValueError):
            chart_series([],999)
if __name__=="__main__":
    unittest.main()
