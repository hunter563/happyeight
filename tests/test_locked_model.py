import copy
import json
import unittest
from pathlib import Path

from fusion.locked_model import analyze, backtest, metadata, KEY
from fusion.prediction import predict


class LockedModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference=json.loads((Path(__file__).parent/'fixtures/locked_rf_reference.json').read_text())

    def test_frozen_workbook_all_100_periods_and_scores(self):
        rows=self.reference['draws']
        result=backtest(rows,100)
        self.assertEqual(len(result['records']),100)
        for actual,expected in zip(result['records'],self.reference['records']):
            self.assertEqual({k:actual[k] for k in expected},expected)
        self.assertEqual(result['summary']['hits'],374)
        self.assertEqual(result['summary']['count'],1400)
        self.assertEqual(result['summary']['below3'],18)
        self.assertEqual(result['summary']['falseDeleted'],142)
        for history,expected in [(rows[:12],self.reference['firstScores']),(rows[:-1],self.reference['lastScores'])]:
            scores={r['number']:r['score'] for r in analyze(history)['scores']}
            for row in expected:self.assertAlmostEqual(scores[row['number']],row['score'],places=14)

    def test_target_outcome_cannot_change_its_prediction(self):
        original=self.reference['draws']
        changed=copy.deepcopy(original)
        changed[-1]['numbers']=list(range(1,21))
        before=backtest(original,1)['records'][0]
        after=backtest(changed,1)['records'][0]
        self.assertEqual(before['selected'],after['selected'])
        self.assertEqual(before['hits'],len(set(before['selected'])&set(original[-1]['numbers'])))
        self.assertEqual(after['hits'],len(set(after['selected'])&set(changed[-1]['numbers'])))
        self.assertLess(before['trainThrough'],before['issue'])
        self.assertEqual(int(before['sourceIssue']),int(before['issue'])-2)

    def test_history_and_target_guards(self):
        rows=self.reference['draws']
        for invalid in [rows[:11],rows[:11]+rows[12:13],rows[:13][::-1]]:
            with self.assertRaises(ValueError):analyze(invalid)
        older=[{**r,'issue':str(int(r['issue'])-1)} for r in rows[:12]]
        with self.assertRaisesRegex(ValueError,'训练截止'):analyze(older)
        with self.assertRaisesRegex(ValueError,'紧邻'):predict(rows,target_issue='2026280')
        for folds in [True,0,301,1.5]:
            with self.assertRaises(ValueError):backtest(rows,folds)

    def test_model_identity_reproducibility_and_quantity(self):
        self.assertEqual(metadata()['modelSha256'],'1f1abe90572392979abfd69d3c710cced3692b0902dbe6c9bdfbcfa499fe423d')
        result=analyze(self.reference['draws'])
        self.assertEqual(result,analyze(self.reference['draws']))
        self.assertEqual(list(result['selections']),[KEY])
        self.assertEqual(len(set(result['baseCandidates'])),20)
        self.assertIn(result['k'],range(10,15))
        self.assertEqual(set(result['selections'][KEY])|set(result['deletedCandidates']),set(result['baseCandidates']))


if __name__=='__main__':unittest.main()
