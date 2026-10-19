import copy
from datetime import date, timedelta
import json
from pathlib import Path
import random
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer

from fusion.data import Store
from fusion.geometry import (analyze_geometry, backtest_geometry, geometry_view,
                             predict_geometry, templates, LOOKBACK)
from fusion.server import make_handler


def sample(count=50):
    rng = random.Random(412)
    return [{'issue': f'2024{i+1:03}', 'date': (date(2024,1,1)+timedelta(days=i)).isoformat(),
             'numbers': sorted(rng.sample(range(1,81),20))} for i in range(count)]


class GeometryTests(unittest.TestCase):
    def test_template_geometry_and_past_only(self):
        seen=set()
        for kind, points in templates():
            self.assertNotIn(points,seen);seen.add(points)
            self.assertTrue(all(-LOOKBACK <= y < 0 for x,y in points))
            a,top,b=points
            self.assertEqual(top,(a[0]+b[0],a[1]+b[1]))
            dot=a[0]*b[0]+a[1]*b[1]
            al=a[0]**2+a[1]**2;bl=b[0]**2+b[1]**2
            if kind=='square':self.assertEqual(dot,0);self.assertEqual(al,bl)
            elif kind=='rectangle':self.assertEqual(dot,0);self.assertNotEqual(al,bl)
            else:self.assertEqual(al,bl);self.assertNotEqual(dot,0)

    def test_constructed_corners_and_missing_corner(self):
        # Future 40; top 40 two periods earlier; sides 39/41 last period.
        rows=sample(12)
        for row in rows:row['numbers']=list(range(1,21))
        rows[-2]['numbers'][-1]=40
        rows[-1]['numbers'][-2:]=[39,41]
        r=analyze_geometry(rows)
        proof=r['candidates'][39]['evidence']
        signature={(41,-1),(40,-2),(39,-1)}
        self.assertTrue(any(e['type']=='square' and {(p['number'],p['offset']) for p in e['points']}==signature for e in proof))
        rows[-1]['numbers'].remove(41);rows[-1]['numbers'].append(20)
        r2=analyze_geometry(rows)
        self.assertFalse(any({(p['number'],p['offset']) for p in e['points']}==signature for e in r2['candidates'][39]['evidence']))

    def test_evidence_is_real_and_chart_uses_same_coordinates(self):
        rows=sample(50);r=analyze_geometry(rows)
        for c in r['candidates']:
            self.assertEqual(c['supportCount'],len(c['evidence']))
            for e in c['evidence']:
                for p in e['points']:
                    row=rows[p['offset']]
                    self.assertEqual(row['issue'],p['issue'])
                    self.assertIn(p['number'],row['numbers'])
            self.assertTrue(0 <= c['score'] <= 1)
        for nums in r['selections'].values():
            self.assertEqual(len(nums),10);self.assertEqual(len(set(nums)),10)
        self.assertEqual(r['chart'][-1]['offset'],-1)
        self.assertTrue(all(n==0 for i,n in enumerate(r['chart'][-1]['missing']) if i+1 in rows[-1]['numbers']))

    def test_replay_excludes_future_everywhere(self):
        rows=sample(50);cut=rows[34]['issue']
        before=geometry_view(rows,as_of_issue=cut)
        altered=copy.deepcopy(rows)
        for row in altered[35:]:row['numbers']=list(range(61,81))
        self.assertEqual(before,geometry_view(altered,as_of_issue=cut))
        self.assertEqual(before['chart'][-1]['issue'],cut)
        self.assertTrue(all(p['issue']<=cut for c in before['candidates'] for e in c['evidence'] for p in e['points']))

    def test_backtest_uses_same_predictions_and_no_target_leak(self):
        rows=sample(50);before=backtest_geometry(rows,k=4,folds=5)
        first=before['records'][0]
        self.assertEqual(first['selections'],analyze_geometry(rows[:45],k=4)['selections'])
        altered=copy.deepcopy(rows);altered[45]['numbers']=list(range(61,81))
        after=backtest_geometry(altered,k=4,folds=5)
        self.assertEqual(first['selections'],after['records'][0]['selections'])
        self.assertEqual(first['dataHash'],after['records'][0]['dataHash'])
        for row in before['records']:
            self.assertLess(row['trainThrough'],row['issue'])
            for key,nums in row['selections'].items():
                self.assertEqual(row['hits'][key],len(set(nums)&set(row['actual'])))
        self.assertEqual(sum(before['summary']['geometry']['distribution']),5)

    def test_gap_and_stale_guards(self):
        rows=sample(50)
        with self.assertRaisesRegex(ValueError,'缺期'):analyze_geometry(rows[:45]+rows[46:])
        r=backtest_geometry(rows[:45]+rows[46:],folds=5)
        self.assertGreater(len(r['skipped']),0)
        with self.assertRaisesRegex(ValueError,'过旧'):predict_geometry(rows,today=date(2025,1,1))
        with self.assertRaisesRegex(ValueError,'紧邻'):predict_geometry(rows,target_issue='2024052',today=date(2024,2,19))
        for value in [0,11,True]:
            with self.assertRaises(ValueError):analyze_geometry(rows,k=value)


class GeometryApiTests(unittest.TestCase):
    def test_geometry_http_lock_settle_and_auth(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(Path(temp)/'test.sqlite');rows=sample(50);store.import_draws(rows,'test')
            server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(store))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            def request(path,body=None):
                req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req) as response:return json.load(response)
            try:
                view=request('/api/geometry?k=4&asOfIssue=2024040')
                self.assertEqual(view['asOfIssue'],'2024040')
                self.assertEqual(store.experiments(),[])
                with patch('fusion.geometry.prediction_context',return_value={'stale':False,'suggestedNextIssue':'2024051'}):
                    locked=request('/api/geometry/predict',{'k':4,'sync':False})
                original=store.experiments()[0]['payload']
                self.assertEqual(original['selections'],locked['selections'])
                store.import_draws([sample(51)[-1]],'test')
                settled=request('/api/experiments')[0]
                self.assertTrue(settled['settled']);self.assertEqual(settled['payload'],original)
                self.assertIn('geometry',settled['hits'])
                server.RequestHandlerClass=make_handler(store,'u','test-password-123456')
                for path,body in [('/api/geometry',None),('/geometry.js',None),('/api/geometry/predict',{'sync':False}),('/api/geometry/backtest',{})]:
                    with self.assertRaises(urllib.error.HTTPError) as cm:request(path,body)
                    self.assertEqual(cm.exception.code,401)
            finally:server.shutdown();server.server_close()


if __name__=='__main__':unittest.main()
