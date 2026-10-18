"""复用 Luck8 的中彩网接口映射，替换掉无超时和硬编码Cookie的请求方式。"""
import json
import time
import urllib.parse
import urllib.request

from .data import normalize

def fetch_history(max_pages=10):
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
