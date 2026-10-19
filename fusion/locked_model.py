"""The single deployed, frozen model selected in the user's optimization sheet.

No fitting, parameter search, or target-draw input occurs at prediction time.
The JSON forest is an exact export of RF_5_80 trained through 2026178.
"""
import hashlib
import itertools
import json
import random
from collections import Counter
from functools import lru_cache
from pathlib import Path
from statistics import mean

import numpy as np

from .data import fingerprint

VERSION = 'shift20-rf-1.0.0'
KEY = 'locked_rf'
LOOKBACK = 12
SHAPES = ('square', 'rectangle', 'diamond', 'triangle', 'trapezoid')
GROUPS = ({'R01','R02','R03','R04'}, {'R05','R09'}, {'R06'}, {'R07','R10'}, {'R08','R11'}, {'R12'})
MODEL_PATH = Path(__file__).parent / 'models/shift20_rf_v1.json'


@lru_cache(maxsize=1)
def model():
    raw = MODEL_PATH.read_bytes()
    bundle = json.loads(raw)
    if bundle['id'] != VERSION or len(bundle['trees']) != 160:
        raise RuntimeError('固定模型文件不匹配')
    bundle['sha256'] = hashlib.sha256(raw).hexdigest()
    return bundle


def metadata():
    m = model()
    return {'id': VERSION, 'key': KEY, 'name': m['name'], 'modelSha256': m['sha256'],
            'trainedThrough': m['trainedThrough'], 'window': LOOKBACK,
            'minSelected': 10, 'maxSelected': 14, 'baseCount': 20,
            'sourceWorkbook': m['sourceWorkbook'], 'referenceReview': m['referenceReview'],
            'description': '上上期开奖号码±1生成20个候选；固定评分排序，累计评分目标4，保留10–14个。',
            'scoreMeaning': '评分用于排序，累计评分目标4不代表会中4个。'}


def validate_options(k=None, window=None):
    if k is not None or window is not None:
        raise ValueError('后台仅启用固定评分规则，数量10–14个、历史12期由规则确定，不支持修改k或window')


def adjacent(a, b):
    return int(b) == int(a)+1 if a[:4] == b[:4] else int(b[:4]) == int(a[:4])+1 and b.endswith('001')


def validate_history(draws):
    if len(draws) < LOOKBACK:
        raise ValueError('固定评分规则至少需要连续12期开奖数据')
    for a,b in zip(draws[-LOOKBACK:], draws[-LOOKBACK+1:]):
        if not adjacent(a['issue'], b['issue']) or a['date'] >= b['date']:
            raise ValueError('最近12期缺期或顺序异常，请先补齐开奖数据')
    if draws[-1]['issue'] < model()['trainedThrough']:
        raise ValueError('数据早于固定模型训练截止期2026178，不能用未来训练的模型冒充当时预测')


@lru_cache(maxsize=1)
def template_index():
    return {n: [(s,points) for s,points in model()['templates']
                if all(1 <= n+dx <= 80 for dx,dy in points)] for n in range(1,81)}


def choose_balanced(pool, weights, tie):
    # This reproduces the historical rule-vote feature; it is not an extra
    # constraint on the final 10–14 selected numbers.
    dp={(0,0):(0,0,0.0,())}
    for segment in range(8):
        bucket=[n for n in pool if (n-1)//10==segment]
        options={(0,0):(0,0,0.0,())}
        for size in [1,2]:
            for picked in itertools.combinations(bucket,size):
                odd=sum(n%2 for n in picked)
                val=(1,sum(weights[n] for n in picked),sum(tie[n] for n in picked),picked)
                key=(size,odd)
                if key not in options or val>options[key]: options[key]=val
        new={}
        for (cnt,odd),value in dp.items():
            for (add,addodd),option in options.items():
                n,o=cnt+add,odd+addodd
                if n>11 or o>6 or n-o>6: continue
                val=(value[0]+option[0],value[1]+option[1],value[2]+option[2],value[3]+option[3])
                key=(n,o)
                if key not in new or val>new[key]: new[key]=val
        dp=new
    return list(max(((n,v) for (n,o),v in dp.items() if abs(2*o-n)<=1),key=lambda x:(x[0],x[1]))[1][3])


def prepare_features(draws):
    validate_history(draws)
    history=draws[-LOOKBACK:]
    past={j-12:set(d['numbers']) for j,d in enumerate(history)}
    support=Counter(n+s for n in history[-2]['numbers'] for s in (-1,1) if 1<=n+s<=80)
    rng=random.Random(int(history[-2]['issue']))
    tie={n:rng.random() for n in range(1,81)}
    base=sorted(support,key=lambda n:(-support[n],tie[n],n))[:20]
    if len(base)!=20:
        raise ValueError('上上期加减1候选不足20个，不能执行固定规则')
    counts={};possible={};old_scores={}
    for n,templates in template_index().items():
        counts[n]=dict.fromkeys(SHAPES,0);possible[n]=dict.fromkeys(SHAPES[:3],0)
        for s,points in templates:
            if s in possible[n]: possible[n][s]+=1
            if all(n+dx in past[dy] for dx,dy in points): counts[n][s]+=1
        old_scores[n]=mean(counts[n][s]/possible[n][s] if possible[n][s] else 0 for s in SHAPES[:3])
    rng=random.Random(int(history[-1]['issue']))
    vote_tie={n:rng.random() for n in range(1,81)}
    eligible=[n for n in range(1,81) if sum(counts[n][s] for s in SHAPES[:3])>=2]
    ranks={n:j+1 for j,n in enumerate(sorted(eligible,key=lambda n:(-old_scores[n],vote_tie[n])))}
    def freq(n,start,stop): return sum(n in past[-j] for j in range(start,stop+1))
    def lag(n): return next((j for j in range(1,13) if n in past[-j]),13)
    old_x={n:[lag(n),freq(n,1,3),freq(n,4,6),freq(n,7,12),lag(n-1),lag(n+1),
              freq(n-1,1,3),freq(n+1,1,3),counts[n]['square'],counts[n]['rectangle'],counts[n]['diamond'],
              sum(counts[n][s] for s in SHAPES[:3]),ranks.get(n,81),old_scores.get(n-1,0),old_scores.get(n+1,0),old_scores[n]] for n in range(1,81)}
    rules_by={n:set() for n in base};shapes_by={n:set() for n in base};cache={}
    for shape in SHAPES:
        for rule in model()['rules']:
            shift=rule['shift']
            pool=sorted({n+shift for n in range(1,81) if counts[n][shape]>0 and 1<=n+shift<=80
                         and all(old_x[n][c['feature']]<=c['value'] if c['op']=='<=' else old_x[n][c['feature']]>c['value'] for c in rule['conditions'])})
            key=(tuple(pool),shift)
            if key not in cache:
                weights={n:int(round(old_scores[n-shift]*1e12)) for n in pool}
                cache[key]=choose_balanced(pool,weights,vote_tie)
            for n in set(cache[key])&set(base):
                rules_by[n].add(rule['id']);shapes_by[n].add(shape)
    features=[]
    for j,n in enumerate(base):
        sc=sum(v>0 for v in counts[n].values())
        geo=sum(counts[n][s]/possible[n][s] if possible[n][s] else 0 for s in SHAPES[:3])/3
        streak=0
        for a in range(1,13):
            if n not in past[-a]:break
            streak+=1
        f={'number':n,'originalRank':j+1,'support':support[n],
           'f1':int(n in past[-1]),'f2':int(n in past[-2]),'f3':freq(n,1,3),'f6':freq(n,1,6),'f12':freq(n,1,12),
           'f4to6':freq(n,4,6),'f7to12':freq(n,7,12),'lag':lag(n),'streak':streak,
           'shapeCount':sc,**counts[n],'geometryScore':geo,'ruleCount':len(rules_by[n]),
           'voteShapeCount':len(shapes_by[n]),'ruleGroupCount':sum(bool(g&rules_by[n]) for g in GROUPS),
           'fiveShapes':int(sc==5),'scoreBand':int(sc>=4 and .04<geo<=.06),'recent3Hot':int(freq(n,1,3)>=2)}
        f.update({f'R{a:02}':int(f'R{a:02}' in rules_by[n]) for a in range(1,13)})
        features.append(f)
    return base,features


def forest_scores(features):
    m=model()
    # sklearn's forest casts input to float32 before comparing float64 splits.
    x=np.asarray([[f[k] for k in m['features']] for f in features],dtype=np.float32)
    scores=np.zeros(len(x),dtype=float)
    for tree in m['trees']:
        for i,row in enumerate(x):
            node=0
            while tree['left'][node]!=-1:
                node=tree['left'][node] if float(row[tree['feature'][node]])<=tree['threshold'][node] else tree['right'][node]
            scores[i]+=tree['p1'][node]
    return scores/len(m['trees'])


def analyze(draws):
    base,features=prepare_features(draws)
    scores=forest_scores(features)
    order=np.argsort(-scores,kind='stable')
    policy=model()['policy']
    k=int(np.searchsorted(np.cumsum(scores[order]),policy['target']))+1
    k=max(policy['min'],min(policy['max'],k))
    selected=sorted(base[a] for a in order[:k])
    last=draws[-1]
    return {'version':VERSION,'rule':metadata(),'k':k,'window':12,'dataCount':len(draws),
            'asOfIssue':last['issue'],'asOfDate':last['date'],'sourceIssue':draws[-2]['issue'],
            'dataHash':fingerprint(draws[-12:]),'modelSha256':model()['sha256'],
            'selections':{KEY:selected},'baseCandidates':sorted(base),'deletedCandidates':sorted(set(base)-set(selected)),
            'previousDraw':{k:last[k] for k in ('issue','date','numbers')},
            'scores':[{'number':n,'score':float(scores[j]),'selected':n in selected,'features':features[j]} for j,n in enumerate(base)],
            'scoreMeaning':metadata()['scoreMeaning']}


def backtest(draws,folds=100):
    if type(folds) is not int or not 1<=folds<=300:
        raise ValueError('回测期数必须是1–300的整数')
    indices=[i for i in range(12,len(draws)) if draws[i-1]['issue']>=model()['trainedThrough']]
    indices=indices[-folds:]
    if not indices:raise ValueError('没有训练截止2026178之后可复核的已开奖期数')
    records=[]
    for i in indices:
        if not adjacent(draws[i-1]['issue'],draws[i]['issue']):raise ValueError('回测目标之前存在缺期')
        r=analyze(draws[:i]);actual=set(draws[i]['numbers']);selected=r['selections'][KEY]
        matched=sorted(actual&set(selected));false=sorted(actual&set(r['deletedCandidates']))
        records.append({'issue':draws[i]['issue'],'date':draws[i]['date'],'trainThrough':draws[i-1]['issue'],
                        'sourceIssue':r['sourceIssue'],'count':r['k'],'selected':selected,'matched':matched,'hits':len(matched),
                        'falseDeleted':false,'baseHits':len(actual&set(r['baseCandidates']))})
    count=sum(r['count'] for r in records);hits=sum(r['hits'] for r in records)
    summary={'count':count,'hits':hits,'meanCount':count/len(records),'meanHits':hits/len(records),'rate':hits/count,
             'minHits':min(r['hits'] for r in records),'maxHits':max(r['hits'] for r in records),
             'below3':sum(r['hits']<3 for r in records),'falseDeleted':sum(len(r['falseDeleted']) for r in records)}
    return {'version':VERSION,'rule':metadata(),'folds':len(records),'requestedFolds':folds,
            'firstIssue':records[0]['issue'],'lastIssue':records[-1]['issue'],'summary':summary,'records':records,
            'note':'固定模型仅使用每个目标期之前12期生成候选；只复核训练截止期之后。该历史曾参与研究，不是独立前瞻验证。'}
