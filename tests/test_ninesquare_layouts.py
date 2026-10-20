import unittest
from fusion.ninesquare_layouts import grid, grid_hits

class NineSquareTests(unittest.TestCase):
    def test_verified_layouts(self):
        for mode in ("standard", "symmetric"):
            rows=grid(mode)
            self.assertEqual((len(rows),len(rows[0])),(9,9))
            vals=[n for row in rows for n in row if n is not None]
            self.assertEqual(sorted(vals),list(range(1,81)))
            self.assertEqual(sum(n is None for row in rows for n in row),1)
            mask=grid_hits(mode,list(range(1,21)))
            self.assertEqual(sum(v is True for row in mask for v in row),20)
    def test_unknown(self):
        with self.assertRaises(ValueError):
            grid("unknown")
if __name__=="__main__":
    unittest.main()
