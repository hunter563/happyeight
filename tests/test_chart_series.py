import unittest
from fusion.chart_series import chart_series, is_prime

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
    def test_bad_limit(self):
        with self.assertRaises(ValueError):
            chart_series([],999)
if __name__=="__main__":
    unittest.main()
