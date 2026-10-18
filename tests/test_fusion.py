import copy
import io
import json
import random
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date,timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from fusion import engine
from fusion.data import Store,normalize,fingerprint,parse_csv
from fusion.server import make_handler
from fusion.provider import parse_gin,fetch_history,fetch_gin,FIELDS

def sample(count=90):
    rng=random.Random(77)
    return [{'issue':str(2024001+i),'date':(date(2024,1,1)+timedelta(days=i)).isoformat(),'numbers':sorted(rng.sample(range(1,81),20))} for i in range(count)]

class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'test.sqlite')
    def tearDown(self): self.temp.cleanup()
    def test_validation_and_csv(self):
        row=sample(1)[0]
        self.assertEqual(normalize(row),row)
        csv='期号,开奖日期,开奖号码\n'+row['issue']+','+row['date']+',"'+','.join(map(str,row['numbers']))+'"'
        self.assertEqual(parse_csv(csv),[row])
        for numbers in [[1]*20,list(range(20)),[1.5]+list(range(2,21)),list(range(1,20))]:
            with self.assertRaises(ValueError): normalize({**row,'numbers':numbers})
    def test_import_idempotent(self):
        rows=sample(3);self.assertEqual(self.store.import_draws(rows,'test')['inserted'],3)
        self.assertEqual(self.store.import_draws(rows,'test')['duplicates'],3)
    def test_conflict_rolls_back_entire_batch(self):
        rows=sample(2);self.store.import_draws([rows[0]],'test')
        wrong={**rows[0],'numbers':list(range(1,21))}
        with self.assertRaises(ValueError): self.store.import_draws([rows[1],wrong],'test')
        self.assertEqual(len(self.store.draws()),1)
    def test_hash_ignores_import_metadata(self):
        row=sample(1)[0]
        self.assertEqual(fingerprint([row]),fingerprint([{**row,'source':'different'}]))

class EngineTests(unittest.TestCase):
    def test_gin_counts_and_luckydd_missing_boundaries(self):
        draws=[{**d,'numbers':list(range(1,21))} for d in sample(30)]
        r=engine.node_call({'draws':draws})
        self.assertEqual(r['ginCounts'][0]['count'],30)
        self.assertEqual(r['ginCounts'][79]['count'],0)
        missing={x['number']:x['missing'] for x in r['missing']}
        self.assertEqual(missing[1],0);self.assertEqual(missing[80],30)
    def test_real_upstream_calls_and_reproducibility(self):
        with patch.object(engine,'compute_enhanced_scores',wraps=engine.compute_enhanced_scores) as kitten:
            with patch.object(engine.Luck8,'analyze_frequency',autospec=True,side_effect=engine.Luck8.analyze_frequency) as luck:
                r=engine.analyze(sample(),k=7,window=60)
                self.assertTrue(kitten.called);self.assertTrue(luck.called)
        again=engine.analyze(sample(),k=7,window=60)
        self.assertEqual(r['selections'],again['selections'])
        for values in r['selections'].values():
            self.assertEqual(len(set(values)),7);self.assertTrue(all(1<=n<=80 for n in values))
        self.assertEqual(len(r['numbers']),80)
    def test_temporal_isolation(self):
        draws=sample(65)
        before=engine.backtest(draws,k=5,window=60,folds=5)
        changed=copy.deepcopy(draws)
        changed[-1]['numbers']=list(range(1,21))
        after=engine.backtest(changed,k=5,window=60,folds=5)
        self.assertEqual([r['selections'] for r in before['records']],[r['selections'] for r in after['records']])
        for r in before['records']: self.assertLess(int(r['trainThrough']),int(r['issue']))
    def test_probabilities_normalized_and_mean(self):
        for k in range(1,11):
            p=engine.probabilities(k)
            self.assertAlmostEqual(sum(x['probability'] for x in p),1)
            self.assertAlmostEqual(sum(x['hits']*x['probability'] for x in p),k/4)
    def test_combinatorial_calculator(self):
        r=engine.node_call({'op':'calc','k':3,'selected':5,'hits':3})
        self.assertEqual(r['stakes'],10)
        self.assertEqual(sum(x['count'] for x in r['breakdown']),10)
        r=engine.node_call({'op':'calc','k':10,'selected':10,'hits':10})
        self.assertEqual(r['floatingTickets'],1);self.assertEqual(r['fixedPrize'],0)
    def test_parameter_validation(self):
        for k,window in [(0,120),(11,120),(3,10),(3,501)]:
            with self.assertRaises(ValueError):engine.analyze(sample(),k,window)

class ProviderTests(unittest.TestCase):
    def test_gin_follows_actual_pagination(self):
        pages=[]
        for row in sample(2):
            raw={'code':row['issue'],'day':row['date'],**dict(zip(FIELDS,map(str,row['numbers'])))}
            stream=io.BytesIO(json.dumps({'code':1,'data':{'data':{'list':[raw],'totalPage':2}}}).encode())
            stream.url='https://api.huiniao.top/interface/home/lotteryHistory'
            pages.append(stream)
        with patch('fusion.provider.urllib.request.urlopen',side_effect=pages) as request:
            rows=fetch_gin();self.assertEqual(len(rows),2)
            self.assertIn('page=2',request.call_args_list[1].args[0].full_url)
    def test_gin_mapping(self):
        row=sample(1)[0]
        raw={'code':row['issue'],'day':row['date'],**dict(zip(FIELDS,map(str,row['numbers'])))}
        self.assertEqual(parse_gin({'code':1,'data':{'data':{'list':[raw]}}}),[row])
        with self.assertRaises(ValueError):parse_gin({'code':0,'data':{}})
    def test_provider_fallback(self):
        with patch('fusion.provider.fetch_gin',side_effect=RuntimeError('offline')):
            with patch('fusion.provider.fetch_zhcw',return_value=sample(1)):
                result=fetch_history();self.assertEqual(result['source'],'中彩网在线接口')
                self.assertEqual(len(result['draws']),1)

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'api.sqlite')
        self.store.import_draws(sample(150),'test')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.store))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):self.server.shutdown();self.server.server_close();self.temp.cleanup()
    def request(self,path,body=None,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        req=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        with urllib.request.urlopen(req) as r:return r.status,json.loads(r.read())
    def test_status_and_analysis(self):
        _,r=self.request('/api/status');self.assertEqual(r['count'],150)
        _,r=self.request('/api/analysis?k=3&window=60');self.assertEqual(len(r['selections']['fusion']),3)
    def test_lock_and_settle(self):
        status,r=self.request('/api/experiments',{'targetIssue':'2024151','k':5,'window':60})
        self.assertEqual(status,201)
        snapshot=self.store.experiments()[0]['data_hash']
        self.store.import_draws([sample(151)[-1]],'test')
        result=self.store.experiments()[0]
        self.assertTrue(result['settled']);self.assertEqual(result['data_hash'],snapshot)
        self.assertEqual(len(result['hits']),5)
    def test_past_target_and_cross_origin_rejected(self):
        for body,origin,code in [({'targetIssue':'2024001'},None,400),({},'https://unrelated.example',403)]:
            with self.assertRaises(urllib.error.HTTPError) as cm:self.request('/api/experiments',body,origin)
            self.assertEqual(cm.exception.code,code)

if __name__=='__main__':unittest.main()
