import copy
import base64
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
from fusion.prediction import predict,prediction_context

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
    def test_last_draw_does_not_outweigh_more_frequent_older_numbers(self):
        draws=sample(120)
        for i,d in enumerate(draws):
            d['numbers']=list(range(1,21)) if i<12 else list(range(21,41))
        draws[-1]['numbers']=list(range(61,81))
        r=engine.analyze(draws,k=10,window=120)
        scores={x['number']:x['luck8'] for x in r['numbers']}
        self.assertGreater(scores[1],scores[80])
        self.assertAlmostEqual(r['methods']['luck8LatestDrawWeight'],1/120)
        self.assertEqual(r['previousDraw']['numbers'],draws[-1]['numbers'])

    def test_previous_overlap_is_diagnostic_and_not_an_exclusion(self):
        draws=[{**d,'numbers':list(range(1,21))} for d in sample(60)]
        r=engine.analyze(draws,k=5,window=60)
        self.assertEqual(len(r['overlapWithPrevious']['fusion']),5)
        for name,values in r['selections'].items():
            self.assertEqual(r['overlapWithPrevious'][name],sorted(set(values)&set(draws[-1]['numbers'])))
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
        for r in before['records']:
            previous=next(d for d in draws if d['issue']==r['trainThrough'])
            for name,values in r['selections'].items():
                self.assertEqual(r['previousOverlap'][name],len(set(values)&set(previous['numbers'])))
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
    def test_prediction_update_fetches_only_recent_page(self):
        row=sample(1)[0]
        raw={'code':row['issue'],'day':row['date'],**dict(zip(FIELDS,map(str,row['numbers'])))}
        stream=io.BytesIO(json.dumps({'code':1,'data':{'data':{'list':[raw],'totalPage':5}}}).encode())
        stream.url='https://api.huiniao.top/interface/home/lotteryHistory'
        with patch('fusion.provider.urllib.request.urlopen',return_value=stream) as request:
            self.assertEqual(fetch_gin(max_pages=1),[row])
            self.assertEqual(request.call_count,1)
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

class PredictionTests(unittest.TestCase):
    def test_target_and_stale_data_guard(self):
        draws=sample(90)
        day=date.fromisoformat(draws[-1]['date'])
        r=predict(draws,k=5,window=60,today=day+timedelta(days=1))
        self.assertEqual(r['targetIssue'],'2024091')
        self.assertTrue(r['targetInferred'])
        self.assertEqual(len(r['selections']['fusion']),5)
        with self.assertRaisesRegex(ValueError,'不能确定实时下一期'):
            predict(draws,today=day+timedelta(days=4))
        old=predict(draws,target_issue='2024091',today=day+timedelta(days=4))
        self.assertTrue(old['freshness']['stale']);self.assertFalse(old['targetInferred'])
        with self.assertRaisesRegex(ValueError,'晚于'):
            predict(draws,target_issue=draws[-1]['issue'],today=day)

    def test_year_boundary_requires_explicit_issue(self):
        draws=[{'issue':'2024351','date':'2024-12-31','numbers':list(range(1,21))}]
        for today in [date(2024,12,31),date(2025,1,1)]:
            self.assertIsNone(prediction_context(draws,today)['suggestedNextIssue'])
            with self.assertRaisesRegex(ValueError,'跨年'):
                predict(draws,today=today)

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
    def test_cloud_auth_protects_pages_reads_and_writes(self):
        self.server.RequestHandlerClass=make_handler(self.store, 'happy8', 'test-password-123456')
        for path,body in [('/',None),('/app.js',None),('/api/status',None),('/api/experiments',{'targetIssue':'2024151'}),('/api/predict',{'sync':False})]:
            with self.assertRaises(urllib.error.HTTPError) as cm:self.request(path,body)
            self.assertEqual(cm.exception.code,401)
            self.assertIn('Basic',cm.exception.headers['WWW-Authenticate'])
        self.assertEqual(self.store.experiments(),[])
        for value in ['Basic !!!','Basic '+base64.b64encode(b'happy8:wrong').decode()]:
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(urllib.request.Request(self.base+'/api/status',headers={'Authorization':value}))
            self.assertEqual(cm.exception.code,401)
        token=base64.b64encode(b'happy8:test-password-123456').decode()
        req=urllib.request.Request(self.base+'/api/status',headers={'Authorization':'Basic '+token})
        with urllib.request.urlopen(req) as response:self.assertEqual(json.loads(response.read())['count'],150)
        status,payload=self.request('/api/health')
        self.assertEqual((status,payload),(200,{'ok':True}))

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
    def test_predict_sync_target_save_and_settle(self):
        incoming=sample(151)[-1]
        with patch('fusion.server.fetch_recent',return_value={'draws':[incoming],'source':'test-online'}):
            with patch('fusion.prediction.prediction_context',side_effect=lambda draws,today=None:prediction_context(draws,today=date(2024,5,30))):
                status,r=self.request('/api/predict',{'k':5,'window':60})
        self.assertEqual(status,201)
        self.assertEqual(r['targetIssue'],'2024152')
        self.assertEqual(r['asOfIssue'],'2024151')
        self.assertEqual(r['sync']['inserted'],1)
        saved=self.store.experiments()[0]
        self.assertEqual(saved['id'],r['recordId'])
        self.assertEqual(saved['payload']['selections'],r['selections'])
        self.assertEqual(saved['data_hash'],r['dataHash'])
        actual=sample(152)[-1];self.store.import_draws([actual],'test')
        settled=self.store.experiments()[0]
        self.assertTrue(settled['settled'])
        self.assertEqual(settled['hits']['fusion'],len(set(actual['numbers'])&set(r['selections']['fusion'])))

    def test_predict_offline_fresh_data_warns_and_invalid_params_skip_network(self):
        with patch('fusion.server.fetch_recent',side_effect=RuntimeError('offline')) as source:
            with patch('fusion.prediction.prediction_context',side_effect=lambda draws,today=None:prediction_context(draws,today=date(2024,5,29))):
                status,r=self.request('/api/predict',{'k':3,'window':60})
            self.assertEqual(status,201);self.assertEqual(r['sync']['status'],'error')
            self.assertEqual(source.call_count,1)
            with self.assertRaises(urllib.error.HTTPError) as cm:self.request('/api/predict',{'k':11})
            self.assertEqual(cm.exception.code,400);self.assertEqual(source.call_count,1)
    def test_past_target_and_cross_origin_rejected(self):
        for body,origin,code in [({'targetIssue':'2024001'},None,400),({},'https://unrelated.example',403)]:
            with self.assertRaises(urllib.error.HTTPError) as cm:self.request('/api/experiments',body,origin)
            self.assertEqual(cm.exception.code,code)

if __name__=='__main__':unittest.main()
