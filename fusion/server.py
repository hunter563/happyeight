"""个人研究 HTTP 服务；云端试用使用可选的 HTTP Basic 访问认证。"""
import argparse
import base64
import hmac
import json
import mimetypes
import os
import re
import traceback
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from .data import ROOT, Store, parse_csv, utc_now
from .engine import analyze, backtest, node_call, probabilities, params
from .provider import fetch_history, fetch_recent
from .prediction import predict, prediction_context
from .geometry import geometry_view, predict_geometry, backtest_geometry, validate_k

def make_handler(store, access_username=None, access_password=None):
    username=access_username if access_username is not None else os.environ.get('KL8_ACCESS_USERNAME','happy8')
    password=access_password if access_password is not None else os.environ.get('KL8_ACCESS_PASSWORD','')
    expected=base64.b64encode(f'{username}:{password}'.encode())
    class Handler(BaseHTTPRequestHandler):
        def send(self,status,payload,content_type='application/json; charset=utf-8',headers=None):
            data=payload if isinstance(payload,bytes) else json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
            for key,value in (headers or {}).items(): self.send_header(key,value)
            self.end_headers();self.wfile.write(data)

        def authorized(self):
            if not password: return True
            scheme,_,value=self.headers.get('Authorization','').partition(' ')
            if scheme.lower()=='basic' and hmac.compare_digest(value.encode(),expected): return True
            self.send(401,{'error':'请输入试用账号和密码'},headers={'WWW-Authenticate':'Basic realm="HappyEight", charset="UTF-8"'})
            return False

        def guarded(self,callback):
            try: callback()
            except (ValueError,KeyError,TypeError) as exc: self.send(400,{'error':str(exc)})
            except Exception as exc:
                traceback.print_exc()
                self.send(503,{'error':str(exc)})

        def do_GET(self):
            if urlsplit(self.path).path=='/api/health':
                return self.send(200,{'ok':True})
            if self.authorized(): self.guarded(self.get)

        def get(self):
            url=urlsplit(self.path); q=parse_qs(url.query)
            if url.path=='/api/status':
                draws=store.draws();latest=draws[-1] if draws else None
                today=datetime.now(ZoneInfo('Asia/Shanghai')).date()
                age=(today-datetime.fromisoformat(latest['date']).date()).days if latest else None
                self.send(200,{'count':len(draws),'first':draws[0] if draws else None,'latest':latest,'ageDays':age,'recent':draws[-20:][::-1],'sources':json.loads((ROOT/'UPSTREAM_SOURCES.json').read_text()),'engines':['kitten','luck8','luckydd','gin-18'],'nonCommercial':True,'prediction':prediction_context(draws)})
            elif url.path=='/api/analysis':
                self.send(200,analyze(store.draws(),int(q.get('k',[10])[0]),int(q.get('window',[120])[0])))
            elif url.path=='/api/experiments':
                self.send(200,store.experiments())
            elif url.path=='/api/geometry':
                self.send(200,geometry_view(store.draws(),int(q.get('k',[10])[0]),int(q.get('rows',[30])[0]),q.get('asOfIssue',[None])[0]))
            elif url.path=='/api/export':
                self.send(200,[{k:d[k] for k in ('issue','date','numbers')} for d in store.draws()])
            else:
                name={'/':'index.html','/app.js':'app.js','/geometry.js':'geometry.js','/style.css':'style.css'}.get(url.path)
                if not name: return self.send(404,{'error':'页面不存在'})
                path=ROOT/'web'/name
                self.send(200,path.read_bytes(),(mimetypes.guess_type(name)[0] or 'text/plain')+'; charset=utf-8')

        def do_POST(self):
            if self.authorized(): self.guarded(self.post)

        def post(self):
            host=self.headers.get('Host','')
            origin=self.headers.get('Origin')
            if origin and origin not in ('http://'+host,'https://'+host):
                return self.send(403,{'error':'拒绝跨站写入'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                return self.send(415,{'error':'需要application/json请求'})
            size=int(self.headers.get('Content-Length',0))
            if not 0<size<=2_000_000: return self.send(413,{'error':'请求大小不合法（上限2MB）'})
            body=json.loads(self.rfile.read(size))
            route=urlsplit(self.path).path
            if route=='/api/geometry/predict':
                k=body.get('k',10);rows=body.get('rows',30)
                validate_k(k)
                if type(rows) is not int or rows not in (30,50,100): raise ValueError('走势图可显示30、50或100期')
                sync=body.get('sync',True)
                if type(sync) is not bool: raise ValueError('sync 必须为布尔值')
                sync_result={'status':'skipped'}
                if sync:
                    fetched=fetch_recent()
                    sync_result={'status':'ok',**store.import_draws(fetched['draws'],fetched['source'])}
                with store.connect() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    result=predict_geometry(store.draws(conn),k,rows,body.get('targetIssue'))
                    result['sync']=sync_result
                    cursor=conn.execute('INSERT INTO experiments(created_at,target_issue,as_of_issue,data_hash,payload) VALUES(?,?,?,?,?)',
                        (result['generatedAt'],result['targetIssue'],result['asOfIssue'],result['dataHash'],json.dumps(result)))
                    result['recordId']=cursor.lastrowid
                self.send(201,result)
            elif route=='/api/geometry/backtest':
                self.send(200,backtest_geometry(store.draws(),body.get('k',10),body.get('folds',100)))
            elif route=='/api/predict':
                k=body.get('k',10);window=body.get('window',120)
                params(k,window)
                sync=body.get('sync',True)
                if type(sync) is not bool: raise ValueError('sync 必须为布尔值')
                sync_result={'status':'skipped'}
                if sync:
                    try:
                        fetched=fetch_recent()
                        sync_result={'status':'ok',**store.import_draws(fetched['draws'],fetched['source'])}
                    except Exception as exc:
                        sync_result={'status':'error','message':'在线更新失败，使用库内数据。'+str(exc)}
                with store.connect() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    result=predict(store.draws(conn),k,window,body.get('targetIssue'))
                    result['sync']=sync_result
                    cursor=conn.execute('INSERT INTO experiments(created_at,target_issue,as_of_issue,data_hash,payload) VALUES(?,?,?,?,?)',
                        (result['generatedAt'],result['targetIssue'],result['asOfIssue'],result['dataHash'],json.dumps(result)))
                    result['recordId']=cursor.lastrowid
                self.send(201,result)
            elif route=='/api/backtest':
                self.send(200,backtest(store.draws(),body.get('k',10),body.get('window',120),body.get('folds',30),body.get('seed',20261018)))
            elif route=='/api/import':
                rows=parse_csv(body['csv']) if 'csv' in body else body['draws']
                self.send(200,store.import_draws(rows,'用户导入'))
            elif route=='/api/sync':
                fetched=fetch_history()
                self.send(200,store.import_draws(fetched['draws'],fetched['source']))
            elif route=='/api/calculate':
                self.send(200,{**node_call({'op':'calc',**{k:body[k] for k in ('k','selected','hits')}}),'probabilities':probabilities(body['k'])})
            elif route=='/api/experiments':
                target=str(body.get('targetIssue',''))
                with store.connect() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    draws=store.draws(conn)
                    if not re.fullmatch(r'20\d{5}',target) or not draws or target<=max(d['issue'] for d in draws):
                        raise ValueError('锁定期号必须晚于当前所有已知开奖期号')
                    result=analyze(draws,body.get('k',10),body.get('window',120),body.get('seed',20261018))
                    cursor=conn.execute('INSERT INTO experiments(created_at,target_issue,as_of_issue,data_hash,payload) VALUES(?,?,?,?,?)',(utc_now(),target,result['asOfIssue'],result['dataHash'],json.dumps(result)))
                    item={'id':cursor.lastrowid,'targetIssue':target,'asOfIssue':result['asOfIssue']}
                self.send(201,item)
            else: self.send(404,{'error':'接口不存在'})
    return Handler

def main():
    parser=argparse.ArgumentParser(description='快乐8个人研究融合系统')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8768)
    parser.add_argument('--database',default=os.environ.get('KL8_DATABASE',str(ROOT/'data/fusion.sqlite')))
    parser.add_argument('--no-seed',action='store_true',help='不导入随仓库附带的历史快照')
    parser.add_argument('--open-browser',action='store_true',help='启动后打开本机网页')
    args=parser.parse_args()
    if os.environ.get('KL8_REQUIRE_AUTH')=='1' and len(os.environ.get('KL8_ACCESS_PASSWORD',''))<16:
        parser.error('云端运行需要至少16字符的 KL8_ACCESS_PASSWORD')
    store=Store(Path(args.database))
    if not args.no_seed: store.seed()
    server=ThreadingHTTPServer((args.host,args.port),make_handler(store))
    print(f'快乐8融合研究系统：http://{args.host}:{args.port}（Ctrl+C退出）',flush=True)
    if args.open_browser:
        webbrowser.open(f'http://127.0.0.1:{args.port}')
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()

if __name__=='__main__': main()
