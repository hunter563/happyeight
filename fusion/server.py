"""个人研究 HTTP 服务；云端试用使用可选的 HTTP Basic 访问认证。"""
import argparse
import base64
import hmac
import json
import mimetypes
import os
import traceback
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from .data import ROOT, Store, parse_csv
from .engine import node_call, probabilities
from .locked_model import analyze, backtest, metadata, validate_options, VERSION, KEY
from .provider import fetch_history, fetch_recent
from .chart_series import chart_series
from .prediction import predict, prediction_context

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
                return self.send(200,{'ok':True,'activeRule':VERSION})
            if self.authorized(): self.guarded(self.get)

        def get(self):
            url=urlsplit(self.path); q=parse_qs(url.query)
            if url.path=='/api/status':
                draws=store.draws();latest=draws[-1] if draws else None
                today=datetime.now(ZoneInfo('Asia/Shanghai')).date()
                age=(today-datetime.fromisoformat(latest['date']).date()).days if latest else None
                self.send(200,{'count':len(draws),'first':draws[0] if draws else None,'latest':latest,'ageDays':age,'recent':draws[-20:][::-1],'sources':json.loads((ROOT/'UPSTREAM_SOURCES.json').read_text()),'engines':[KEY],'activeRule':metadata(),'nonCommercial':True,'prediction':prediction_context(draws)})
            elif url.path=='/api/chart-series':
                requested=q.get('limit',['50'])
                if len(requested)!=1: raise ValueError('limit only once')
                self.send(200,chart_series(store.draws(),int(requested[0])))
            elif url.path=='/api/analysis':
                validate_options(q.get('k'),q.get('window'))
                if 'strategy' in q or 'model' in q: raise ValueError('后台仅有一个固定模型')
                self.send(200,analyze(store.draws()))
            elif url.path=='/api/experiments':
                rows=store.experiments()
                for item in rows:item['archived']=item['payload'].get('version')!=VERSION
                self.send(200,rows if q.get('includeArchived')==['1'] else [r for r in rows if not r['archived']])
            elif url.path=='/api/geometry':
                self.send(410,{'error':'独立图形预测已停用，后台仅保留固定评分筛选规则','activeRule':VERSION})
            elif url.path=='/api/export':
                self.send(200,[{k:d[k] for k in ('issue','date','numbers')} for d in store.draws()])
            else:
                name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}.get(url.path)
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
            if route in ('/api/geometry/predict','/api/geometry/backtest'):
                return self.send(410,{'error':'独立图形预测已停用，后台仅保留固定评分筛选规则','activeRule':VERSION})
            elif route in ('/api/predict','/api/experiments'):
                validate_options(body.get('k'),body.get('window'))
                if 'strategy' in body or 'model' in body:
                    raise ValueError('后台仅有一个固定模型，不支持切换预测策略')
                sync=body.get('sync',route=='/api/predict')
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
                    result=predict(store.draws(conn),target_issue=body.get('targetIssue'))
                    result['sync']=sync_result
                    cursor=conn.execute('INSERT INTO experiments(created_at,target_issue,as_of_issue,data_hash,payload) VALUES(?,?,?,?,?)',
                        (result['generatedAt'],result['targetIssue'],result['asOfIssue'],result['dataHash'],json.dumps(result)))
                    result['recordId']=cursor.lastrowid
                    result['id']=cursor.lastrowid
                self.send(201,result)
            elif route=='/api/backtest':
                validate_options(body.get('k'),body.get('window'))
                if 'strategy' in body or 'model' in body: raise ValueError('后台仅有一个固定模型')
                self.send(200,backtest(store.draws(),body.get('folds',100)))
            elif route=='/api/import':
                rows=parse_csv(body['csv']) if 'csv' in body else body['draws']
                self.send(200,store.import_draws(rows,'用户导入'))
            elif route=='/api/sync':
                fetched=fetch_history()
                self.send(200,store.import_draws(fetched['draws'],fetched['source']))
            elif route=='/api/calculate':
                self.send(200,{**node_call({'op':'calc',**{k:body[k] for k in ('k','selected','hits')}}),'probabilities':probabilities(body['k'])})
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
