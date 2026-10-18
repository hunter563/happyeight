"""复用 Luck8 的中彩网接口映射，替换掉无超时和硬编码Cookie的请求方式。"""
import json
import time
import urllib.parse
import urllib.request

from .data import normalize

def fetch_zhcw(max_pages=10):
    draws=[]
    for page in range(1,max_pages+1):
        query=urllib.parse.urlencode({'transactionType':'10001001','lotteryId':'6','issueCount':'0','type':'0','pageNum':page,'pageSize':200})
        url='https://jc.zhcw.com/port/client_json.php?'+query
        request=urllib.request.Request(url,headers={'User-Agent':'KL8-Fusion/0.1 personal-research','Referer':'https://www.zhcw.com/'})
        payload=None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request,timeout=12) as response:
                    host=urllib.parse.urlsplit(response.url).hostname
                    if host!='jc.zhcw.com':
                        raise ValueError('上游跳转至未批准的域名')
                    text=response.read(4_000_001)
                    if len(text)>4_000_000: raise ValueError('上游响应过大')
                    text=text.decode('utf-8-sig').strip()
                    if not text.startswith('{'):
                        text=text[text.index('(')+1:text.rindex(')')]
                    payload=json.loads(text)
                break
            except Exception as exc:
                if attempt:
                    raise RuntimeError('在线数据源暂不可用；可继续使用已有数据或导入CSV。'+type(exc).__name__) from exc
                time.sleep(.4)
        rows=payload.get('data')
        if not isinstance(rows,list) or not rows:
            raise ValueError('上游未返回有效开奖数据，本次未写入数据库')
        draws.extend(normalize({'issue':r['issue'],'date':r['openTime'],'numbers':r['frontWinningNum']}) for r in rows)
        pages=int(payload.get('pages',1))
        if page>=pages: break
        time.sleep(.15)
    return draws

FIELDS = 'one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()

def parse_gin(payload):
    """沿用 gin-18/lottery 的字段映射，并严格校验上游返回值。"""
    rows=payload.get('data',{}).get('data',{}).get('list',[])
    if payload.get('code')!=1 or not isinstance(rows,list) or not rows:
        raise ValueError('汇鸟接口未返回有效开奖数据')
    return [normalize({'issue':r['code'],'date':r['day'],'numbers':[r[field] for field in FIELDS]}) for r in rows]

def fetch_gin():
    draws=[];seen=set();page=1;pages=1
    while page<=pages:
        url=f'https://api.huiniao.top/interface/home/lotteryHistory?type=klb&page={page}&limit=500'
        req=urllib.request.Request(url,headers={'User-Agent':'KL8-Fusion/0.1 personal-research'})
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req,timeout=12) as response:
                    if urllib.parse.urlsplit(response.url).hostname!='api.huiniao.top':
                        raise ValueError('数据源跳转至未批准的域名')
                    raw=response.read(4_000_001)
                    if len(raw)>4_000_000:raise ValueError('数据源响应过大')
                payload=json.loads(raw);rows=parse_gin(payload)
                break
            except Exception:
                if attempt:raise
                time.sleep(.4)
        if page==1:
            pages=int(payload['data']['data'].get('totalPage',1))
            if not 1<=pages<=20:raise ValueError('数据源分页数量异常')
        if any(r['issue'] in seen for r in rows):raise ValueError('数据源分页重复，本次未导入')
        seen.update(r['issue'] for r in rows);draws.extend(rows)
        page+=1
    return draws

def fetch_history():
    failures=[]
    for source,fetcher in [('汇鸟公开接口（gin-18/lottery数据源）',fetch_gin),('中彩网在线接口',fetch_zhcw)]:
        try:
            return {'draws':fetcher(),'source':source}
        except Exception as exc:
            failures.append(source+': '+type(exc).__name__)
    raise RuntimeError('在线数据源均不可用，请导入CSV/JSON；已有数据保持不变。'+'；'.join(failures))
