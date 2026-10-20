import unittest
from fusion.chart_ranked import ranked_groups,ranking_series

class RankingChartsTest(unittest.TestCase):
 def test_partition_and_ties(self):
  a=list(range(1,21)); b=list(range(21,41))
  for mode in ('frequency','omission'):
   for k in (4,5,8,10):
    groups=ranked_groups([a,b],mode,k,2)
    self.assertEqual(len(groups),k)
    self.assertEqual(sorted(n for group in groups for n in group),list(range(1,81)))
    self.assertTrue(all(len(g)==80//k for g in groups))
 def test_future_does_not_change_prior_ranking(self):
  a={'issue':'1','numbers':list(range(1,21))}
  b={'issue':'2','numbers':list(range(21,41))}
  c={'issue':'3','numbers':list(range(41,61))}
  first=ranking_series([a,b], 'frequency',4,2,30)['rows'][1]
  second=ranking_series([a,b,c],'frequency',4,2,30)['rows'][1]
  self.assertEqual(first,second)
  self.assertEqual(sum(first['counts']),20)
  self.assertIsNone(ranking_series([a,b],'frequency',4,2,30)['rows'][0]['counts'])
 def test_omission_lookback(self):
  a={'issue':'1','numbers':list(range(1,21))}
  b={'issue':'2','numbers':list(range(21,41))}
  c={'issue':'3','numbers':list(range(41,61))}
  rows=ranking_series([a,b,c],'omission',5,1,30)['rows']
  self.assertEqual(rows[-1]['historyCount'],1)
  self.assertEqual(sum(rows[-1]['counts']),20)
if __name__=='__main__':unittest.main()
