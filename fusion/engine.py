"""将四个上游接到同一数据快照，显式隔离未校准分数。"""
import importlib.util
import json
import math
import os
import random
import subprocess
import sys
import types
import warnings
from statistics import mean

import numpy as np
import pandas as pd

from .data import ROOT, fingerprint

def load_module(name, path, package=False):
    spec = importlib.util.spec_from_file_location(name, path, submodule_search_locations=[str(path.parent)] if package else None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    with warnings.catch_warnings():
        spec.loader.exec_module(module)
    return module

# 建立命名空间，避免上游 __init__ 引入无关的下载/训练依赖。
upstream_package = types.ModuleType('kl8_upstream')
upstream_package.__path__ = [str(ROOT/'vendor/kl8-analyzer/src')]
sys.modules['kl8_upstream'] = upstream_package
from kl8_upstream.analysis.feature_enhancer import compute_enhanced_scores, GRAPH_EMBED_CONFIG
# 禁止读取用全量/未来开奖训练的外部缓存；各回测折仅计算训练窗口。
GRAPH_EMBED_CONFIG['enabled'] = False
GRAPH_EMBED_CONFIG['weight'] = 0
Luck8 = load_module('luck8_upstream',ROOT/'vendor/luck8/kl8_predictor.py').KL8Predictor

def node_call(payload):
    try:
        result = subprocess.run([os.environ.get('KL8_NODE','node'),'--disable-warning=ExperimentalWarning',str(ROOT/'fusion/bridge.mjs')], input=json.dumps(payload),text=True,capture_output=True,timeout=90,check=True)
    except FileNotFoundError as exc:
        raise RuntimeError('需要安装 Node.js 24，或设置 KL8_NODE 指定可执行文件') from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError('JavaScript 分析失败：'+exc.stderr[-500:]) from exc
    return json.loads(result.stdout)

def params(k,window):
    if type(k) is not int or not 1 <= k <= 10:
        raise ValueError('选号数量必须是1–10的整数')
    if type(window) is not int or not 30 <= window <= 500:
        raise ValueError('分析窗口必须是30–500期')

def unit_scores(scores):
    values=np.array([scores.get(n,0.0) for n in range(1,81)],dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError('上游产生了非有限分数')
    span=float(np.ptp(values))
    return {n:float((values[n-1]-values.min())/span) if span else 0.0 for n in range(1,81)}

def top(scores,k,seed):
    # 同分采用固定种子打散，避免长期偏向小号码。
    rng=random.Random(seed);tie={n:rng.random() for n in range(1,81)}
    return sorted(sorted(scores,key=lambda n:(-scores[n],tie[n]))[:k])

def analyze(draws,k=10,window=120,seed=20261018,js=None):
    params(k,window)
    if len(draws)<30:
        raise ValueError('至少需要30期有效历史开奖数据')
    history=draws[-window:]
    if js is None:
        js=node_call({'op':'analyze','draws':history})
    matrix=np.array([[int(d['issue']),*d['numbers']] for d in reversed(history)],dtype=int)
    enhanced,_=compute_enhanced_scores(matrix,len(matrix),use_pca=False)
    kitten=unit_scores(dict(enhanced))
    # 使用上游真实加权频率函数，避开其旧奖金表和有目标泄露的期望值函数。
    predictor=Luck8.__new__(Luck8)
    predictor.df=pd.DataFrame({'开奖日期':pd.to_datetime([d['date'] for d in history]),'numbers_list':[d['numbers'] for d in history]})
    luck=unit_scores(predictor.analyze_frequency(weight_recent=True))
    frequency={x['number']:x['frequency'] for x in js['frequency']}
    pair={n:0.0 for n in range(1,81)}
    for x in js['correlations']:
        value=x['count']/len(history)
        pair[x['number1']]+=value;pair[x['number2']]+=value
    f,p=unit_scores(frequency),unit_scores(pair)
    lucky=unit_scores({n:0.75*f[n]+0.25*p[n] for n in range(1,81)})
    scores={'kitten':kitten,'luck8':luck,'luckydd':lucky}
    scores['fusion']={n:sum(s[n] for s in (kitten,luck,lucky))/3 for n in range(1,81)}
    selections={name:top(value,k,seed) for name,value in scores.items()}
    selections['random']=sorted(random.Random(seed).sample(range(1,81),k))
    missing={x['number']:x['missing'] for x in js['missing']}
    gin={int(x['num']):x['count'] for x in js['ginCounts']}
    numbers=[{'number':n,'count':gin[n],'frequency':frequency.get(n,0),'missing':missing[n],**{name:round(score[n],6) for name,score in scores.items()}} for n in range(1,81)]
    return {'version':'0.1.0','asOfIssue':history[-1]['issue'],'asOfDate':history[-1]['date'],'window':len(history),'k':k,'seed':seed,'dataHash':fingerprint(history),'selections':selections,'numbers':numbers,'statistics':js,'weights':{'kitten':1/3,'luck8':1/3,'luckydd':1/3},'scoreMeaning':'0–1仅为归一化排序分数，不是中奖概率。四个项目中，gin-18提供统计/规则工具，三个分析分支参与固定等权融合。','disabled':['外部图嵌入缓存','PCA','LuckyDD随机置信分','Luck8原期望值/奖金推荐']}

def backtest(draws,k=10,window=120,folds=30,seed=20261018):
    params(k,window)
    if type(folds) is not int or not 1<=folds<=100:
        raise ValueError('回测期数必须是1–100的整数')
    start=max(window,len(draws)-folds)
    if start>=len(draws):
        raise ValueError('数据量必须大于分析窗口')
    indexes=list(range(start,len(draws)))
    batches=[draws[i-window:i] for i in indexes]
    js_batches=node_call({'op':'batch','batches':batches})
    records=[]
    for i,history,js in zip(indexes,batches,js_batches):
        result=analyze(history,k,window,seed+i,js)
        actual=draws[i]
        if int(history[-1]['issue'])>=int(actual['issue']):
            raise ValueError('开奖期号顺序异常，无法执行时序回测')
        records.append({'issue':actual['issue'],'trainThrough':history[-1]['issue'],'dataHash':result['dataHash'],'actual':actual['numbers'],'selections':result['selections'],'hits':{name:len(set(nums)&set(actual['numbers'])) for name,nums in result['selections'].items()}})
    expected=k/4
    sd=math.sqrt(k*.25*.75*(80-k)/79/len(records))
    summary={name:{'meanHits':mean(r['hits'][name] for r in records),'totalHits':sum(r['hits'][name] for r in records),'hitRate':mean(r['hits'][name] for r in records)/k,'deltaFromRandomExpectation':mean(r['hits'][name] for r in records)-expected} for name in records[0]['hits']}
    return {'k':k,'window':window,'folds':len(records),'seed':seed,'theoreticalMeanHits':expected,'randomNull95Band':[max(0,expected-1.96*sd),min(k,expected+1.96*sd)],'summary':summary,'records':records,'note':'严格滚动：每期只用此前开奖；同样选号数量，对照均匀随机策略。区间为公平独立开奖假设下平均命中数的近似95%范围，不是模型胜率保证；未校正多重比较。'}

def probabilities(k):
    params(k,30)
    return [{'hits':h,'probability':math.comb(20,h)*math.comb(60,k-h)/math.comb(80,k)} for h in range(k+1)]
