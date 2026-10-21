"""Meaningful rule, transaction, time-boundary and authenticated API checks."""
import base64
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer

from fusion.data import Store
from fusion.lotteries import GAMES, LotteryStore, analyze_lottery, normalize_draw, parse_lottery_csv
from fusion.server import make_handler


def draw(game='fc3d', issue='2026001', day='2026-01-01', primary=None, secondary=None):
    return dict(game=game, issue=issue, date=day, primary=[0,0,1] if primary is None else primary, secondary=[] if secondary is None else secondary)


EXAMPLES = {
    'ssq': ([1,2,3,4,5,33], [1]), 'fc3d': ([0,0,1], []),
    'kl8': (list(range(1,21)), []), 'qlc': ([1,2,3,4,5,6,7], [30]),
    'dlt': ([1,2,3,4,35], [1,12]), 'pl3': ([0,0,0], []),
    'pl5': ([0,0,1,1,9], []), 'qxc': ([0,0,1,2,3,9], [14]),
}


class RuleTests(unittest.TestCase):
    def test_all_eight_rules_roundtrip(self):
        self.assertEqual(len(GAMES),8)
        for game, (p,s) in EXAMPLES.items():
            with self.subTest(game=game):
                result=normalize_draw(game,draw(game,primary=p,secondary=s))
                self.assertEqual((result['primary'],result['secondary']),(p,s))

    def test_ordered_zeroes_repeats_and_order(self):
        for game, value, expected in [('fc3d','001',[0,0,1]),('pl3','909',[9,0,9]),('pl5','00091',[0,0,0,9,1]),('qxc','003120',[0,0,3,1,2,0])]:
            with self.subTest(game=game):
                result=normalize_draw(game,draw(game,primary=value,secondary=[14] if game=='qxc' else []))
                self.assertEqual(result['primary'],expected)

    def test_unordered_sort_but_pools_remain_independent(self):
        r=normalize_draw('ssq',draw('ssq',primary=[33,5,4,3,2,1],secondary=[1]))
        self.assertEqual(r['primary'],[1,2,3,4,5,33])
        self.assertEqual(r['secondary'],[1])

    def test_qlc_seven_basic_plus_distinct_special(self):
        for primary, secondary in [([1,2,3,4,5,6],[7]),([1,2,3,4,5,6,7],[7]),([1,2,3,4,5,6,7],[31])]:
            with self.subTest(primary=primary,secondary=secondary), self.assertRaises(ValueError):
                normalize_draw('qlc',draw('qlc',primary=primary,secondary=secondary))

    def test_qxc_rule_transition_by_issue_not_date_of_sale(self):
        old=draw('qxc','20099','2020-10-11',[0]*6,[9])
        self.assertEqual(normalize_draw('qxc',old)['ruleVersion'],'legacy')
        with self.assertRaises(ValueError):normalize_draw('qxc',dict(old,secondary=[10]))
        new=draw('qxc','20100','2020-10-13',[0]*6,[14])
        self.assertEqual(normalize_draw('qxc',new)['ruleVersion'],'current')
        with self.assertRaises(ValueError):normalize_draw('qxc',dict(new,secondary=[15]))
        with self.assertRaises(ValueError):normalize_draw('qxc',dict(new,ruleVersion='legacy'))

    def test_issue_canonicalization(self):
        self.assertEqual(normalize_draw('fc3d',draw(issue='26001'))['issue'],'2026001')
        for issue in ('2026000','26000','2025001','2601','<script>'):
            with self.subTest(issue=issue),self.assertRaises(ValueError):normalize_draw('fc3d',draw(issue=issue))

    def test_invalid_numbers_and_extra_pool(self):
        for primary in ([True,0,1],[0.0,0,1],[0,-1,1],[0,0,10],[0,1],'1234',123,None,{'0':1}):
            with self.subTest(primary=primary),self.assertRaises(ValueError):normalize_draw('fc3d',draw(primary=primary) if primary is not None else dict(draw(),primary=None))
        with self.assertRaises(ValueError):normalize_draw('fc3d',draw(secondary=[1]))
        with self.assertRaises(ValueError):normalize_draw('ssq',draw('ssq',primary=[1,1,2,3,4,5],secondary=[1]))

    def test_dates_wrong_game_unknown_game(self):
        for day in ('2099-01-01','2026-02-30','2026-01-01T00:00:00','01/01/2026'):
            with self.subTest(day=day),self.assertRaises(ValueError):normalize_draw('fc3d',draw(day=day))
        with self.assertRaises(ValueError):normalize_draw('pl3',draw())
        with self.assertRaises(ValueError):normalize_draw('unknown',draw())

    def test_csv_bom_and_leading_zero(self):
        rows=parse_lottery_csv('\ufeffissue,date,primary,secondary\n26001,2026-01-01,001,\n')
        self.assertEqual(normalize_draw('fc3d',rows[0])['primary'],[0,0,1])
        with self.assertRaises(ValueError):parse_lottery_csv('foo,bar\n1,2')


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.temp.name)/'test.sqlite')
        self.lotteries=LotteryStore(self.store)
    def tearDown(self):self.temp.cleanup()

    def test_same_issue_isolated_across_all_eight(self):
        for game,(p,s) in EXAMPLES.items():
            self.lotteries.import_draws(game,[draw(game,primary=p,secondary=s)],f'test:{game}')
        self.assertEqual([g['count'] for g in self.lotteries.catalog()],[1]*8)
        self.assertEqual(self.lotteries.draws('fc3d')[0]['source'],'test:fc3d')
        self.assertEqual(len(self.store.draws()),1)

    def test_conflict_rolls_back_earlier_insert_in_batch(self):
        self.lotteries.import_draws('fc3d',[draw()])
        before=self.lotteries.draws('fc3d')
        with self.assertRaises(ValueError):
            self.lotteries.import_draws('fc3d',[draw(issue='2026002',day='2026-01-02'),draw(primary=[9,9,9])])
        self.assertEqual(self.lotteries.draws('fc3d'),before)

    def test_duplicates_preserve_original_provenance(self):
        self.lotteries.import_draws('fc3d',[draw()],'original')
        r=self.lotteries.import_draws('fc3d',[draw(),draw()],'other')
        self.assertEqual((r['inserted'],r['duplicates']),(0,2))
        self.assertEqual(self.lotteries.draws('fc3d')[0]['source'],'original')

    def test_invalid_row_cancels_entire_batch(self):
        with self.assertRaises(ValueError):self.lotteries.import_draws('fc3d',[draw(),draw(primary=[99,1,1])])
        self.assertEqual(self.lotteries.draws('fc3d'),[])

    def test_invalid_input_bounded(self):
        for rows in ([],{},[draw()]*10001):
            with self.subTest(type=type(rows)),self.assertRaises(ValueError):self.lotteries.import_draws('fc3d',rows)
        for source in ('',None,'a'*301):
            with self.assertRaises(ValueError):self.lotteries.import_draws('fc3d',[draw()],source)

    def test_kl8_reuses_existing_table(self):
        self.store.import_draws([dict(issue='2026001',date='2026-01-01',numbers=list(range(1,21)))],'legacy source')
        self.assertEqual(self.lotteries.draws('kl8')[0]['primary'],list(range(1,21)))
        r=self.lotteries.import_draws('kl8',[draw('kl8',primary=list(range(1,21)))])
        self.assertEqual(r['duplicates'],1)
        with self.store.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM lottery_draws').fetchone()[0],0)


class AnalysisTests(unittest.TestCase):
    def normalized(self,rows,game='fc3d'):return [normalize_draw(game,r) for r in rows]

    def test_digit_occurrences_are_not_draw_occurrences(self):
        result=analyze_lottery(self.normalized([draw(),draw(issue='2026002',day='2026-01-02',primary=[0,1,2])]),'fc3d')
        zero=result['activeField']['frequencies'][0]
        self.assertEqual((zero['count'],zero['drawCount']),(3,2))
        self.assertEqual(result['activeField']['series'][0]['values'],[0,0,1])

    def test_previous_record_and_omission_precede_visible_window(self):
        rows=[draw(issue=f'2026{i:03}',day=f'2026-01-{i:02}',primary=[0,0,1] if i==1 else [2,2,2]) for i in range(1,32)]
        result=analyze_lottery(self.normalized(rows),'fc3d',limit=30)
        self.assertEqual(result['count'],30)
        zero=result['activeField']['frequencies'][0]
        self.assertEqual((zero['count'],zero['omission'],zero['lowerBound']),(0,30,False))
        first=result['activeField']['series'][0]
        self.assertEqual(first['omissions'][0]['value'],1)
        self.assertEqual(first['repeat'],0)

    def test_end_filter_excludes_future_context_and_recomputes_omission(self):
        rows=self.normalized([draw(),draw(issue='2026002',day='2026-01-02',primary=[9,9,9])])
        result=analyze_lottery(rows,'fc3d',end='26001')
        nine=result['activeField']['frequencies'][9]
        self.assertEqual((nine['count'],nine['omission'],nine['lowerBound']),(0,1,True))
        self.assertEqual(result['toIssue'],'2026001')

    def test_ordered_position_amplitude(self):
        rows=self.normalized([draw(),draw(issue='2026002',day='2026-01-02',primary=[9,0,0])])
        result=analyze_lottery(rows,'fc3d',field_id='primary:0')
        self.assertEqual(result['activeField']['label'],'百十个位 · 百位')
        self.assertEqual([r['amplitude'] for r in result['activeField']['series']],[None,9])

    def test_unordered_position_is_labeled_sorted(self):
        result=analyze_lottery([], 'ssq',field_id='primary:0')
        self.assertIn('升序第1位',result['activeField']['label'])

    def test_odd_sized_number_pool_big_small_boundaries(self):
        for game,primary,secondary,field,expected in [
            ('ssq',[1,2,3,4,16,17],[1],'primary',1),
            ('dlt',[1,2,3,17,18],[1,12],'primary',1),
            ('qxc',[0]*6,[7],'secondary',1),
            ('qxc',[0]*6,[6],'secondary',0),
            ('pl3',[4,5,9],[],'primary',2),
        ]:
            with self.subTest(game=game,secondary=secondary):
                row=normalize_draw(game,draw(game,primary=primary,secondary=secondary))
                result=analyze_lottery([row],game,field_id=field)
                self.assertEqual(result['activeField']['series'][0]['big'],expected)

    def test_qxc_rule_versions_never_blend(self):
        rows=self.normalized([draw('qxc','20099','2020-10-11',[0]*6,[9]),draw('qxc','20100','2020-10-13',[0]*6,[14])],'qxc')
        current=analyze_lottery(rows,'qxc',field_id='secondary')
        legacy=analyze_lottery(rows,'qxc',version='legacy',field_id='secondary')
        self.assertEqual((current['count'],legacy['count']),(1,1))
        self.assertEqual(len(current['activeField']['frequencies']),15)
        self.assertEqual(len(legacy['activeField']['frequencies']),10)
        self.assertIsNone(current['activeField']['series'][0]['amplitude'])
        self.assertEqual(current['activeField']['series'][0]['big'],1)

    def test_range_validation_empty_and_mixed_game(self):
        self.assertIsNone(analyze_lottery([],'ssq')['latest'])
        for kwargs in (dict(limit=999),dict(limit=True),dict(start='26002',end='26001'),dict(field_id='primary:99'),dict(version='legacy')):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):analyze_lottery([],'ssq',**kwargs)
        with self.assertRaises(ValueError):analyze_lottery(self.normalized([draw()]),'ssq')


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.store=Store(Path(cls.temp.name)/'http.sqlite')
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(cls.store,'tester','a-long-test-password'))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()
    def request(self,path,body=None,auth=True,headers=None):
        h={'Authorization':'Basic '+base64.b64encode(b'tester:a-long-test-password').decode()} if auth else {}
        if body is not None:h['Content-Type']='application/json'
        h.update(headers or {})
        req=urllib.request.Request(self.url+path,data=None if body is None else json.dumps(body).encode(),headers=h)
        try:response=urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:response=exc
        with response:
            raw=response.read();ctype=response.headers['Content-Type']
            return response.status,json.loads(raw) if ctype.startswith('application/json') else raw,response.headers

    def test_new_ui_and_apis_require_existing_auth(self):
        for path in ('/lotteries','/lotteries.js','/api/lotteries','/api/lotteries/ssq','/api/lotteries/ssq/export'):
            with self.subTest(path=path):self.assertEqual(self.request(path,auth=False)[0],401)
        self.assertEqual(self.request('/api/lotteries/ssq/import',{'draws':[]},auth=False)[0],401)
        self.assertEqual(self.request('/api/health',auth=False)[0],200)

    def test_import_analysis_export_and_catalog(self):
        body={'game':'pl5','draws':[draw('pl5',primary='00119')],'source':'synthetic test fixture'}
        self.assertEqual(self.request('/api/lotteries/pl5/import',body)[0],200)
        status,result,_=self.request('/api/lotteries/pl5?field=primary:0')
        self.assertEqual(status,200);self.assertEqual(result['latest']['primary'],[0,0,1,1,9])
        status,export,headers=self.request('/api/lotteries/pl5/export')
        self.assertEqual(export['game'],'pl5');self.assertIn('attachment',headers['Content-Disposition'])
        self.assertEqual(len(self.request('/api/lotteries')[1]['games']),8)

    def test_bad_input_and_cross_origin(self):
        self.assertEqual(self.request('/api/lotteries/pl3/import',{'draws':[]},headers={'Origin':'https://attacker.invalid'})[0],403)
        for body in ([],{'draws':[]},{'draws':[draw()]},{'game':'ssq','draws':[]},{'draws':[],'csv':'x'}):
            with self.subTest(body=body):self.assertEqual(self.request('/api/lotteries/pl3/import',body)[0],400)
        for path in ('/api/lotteries/evil','/api/lotteries/pl3?limit=999','/api/lotteries/pl3?limit=30&limit=50','/api/lotteries/pl3?field=bad','/api/lotteries/pl3?evil=1'):
            with self.subTest(path=path):self.assertEqual(self.request(path)[0],400)
        self.assertEqual(self.request('/api/lotteries/pl3/delete',{})[0],404)

    def test_static_wiring_and_csp(self):
        for path in ('/lotteries','/lotteries.js','/lotteries.css'):
            status,body,headers=self.request(path)
            self.assertEqual(status,200);self.assertGreater(len(body),100)
            self.assertIn("script-src 'self'",headers['Content-Security-Policy'])
        self.assertIn(b'/lotteries',self.request('/')[1])


if __name__=='__main__':unittest.main()
