"""Period × number geometry experiments. Rules are fixed before evaluation.

One grid step means one number horizontally and one draw vertically. Only
templates with exactly one future vertex are scored. These are hypotheses,
not a reverse-engineered forecasting algorithm from the reference website.
"""
from functools import lru_cache
import math
import random
import re
from statistics import mean

from .data import fingerprint, utc_now
from .prediction import prediction_context

VERSION = 'geometry-0.1.0'
STEP = 6
LOOKBACK = 2 * STEP
FAMILIES = {'square': '正方形（倾斜）', 'rectangle': '长方形（倾斜）', 'diamond': '菱形'}
RULES = {
    'coordinateSystem': '横轴01–80；纵轴按开奖期顺序，每行一期；横纵每格等距。',
    'maxSideComponent': STEP, 'lookback': LOOKBACK,
    'knownVertices': 3, 'unknownVertices': 1,
    'score': '每类匹配模板数 / 该号码可容纳的模板数，再对三类等权平均。分数不是概率。',
    'scope': '仅检测下一行缺一个角的倾斜正方形、倾斜长方形和上下对称菱形；边向量分量固定1–6格。水平矩形有两个未知下角，不进入单点评分。',
    'source': '布局参考图感觉公开走势图；几何模板、评分和回测由本项目独立实现，非对方预测算法。',
}


def validate_k(k):
    if type(k) is not int or not 1 <= k <= 10:
        raise ValueError('选取数量必须是1–10的整数')


def adjacent(previous, following):
    if previous[:4] == following[:4]:
        return int(following) == int(previous) + 1
    return int(following[:4]) == int(previous[:4]) + 1 and following.endswith('001')


def validate_history(draws):
    if len(draws) < LOOKBACK:
        raise ValueError(f'图形分析至少需要{LOOKBACK}期数据')
    for a, b in zip(draws[-LOOKBACK:], draws[-LOOKBACK + 1:]):
        if not adjacent(a['issue'], b['issue']) or a['date'] >= b['date']:
            raise ValueError('最近12期存在缺期或顺序异常，不能压缩时间轴形成图形')


@lru_cache(maxsize=1)
def templates():
    result = []
    # Future corner (0,0); side vectors (u,-v), (-w,-z).
    # Orthogonality: u*w == v*z. Equal squared lengths gives a square.
    for u in range(1, STEP + 1):
        for v in range(1, STEP + 1):
            for w in range(1, STEP + 1):
                for z in range(1, STEP + 1):
                    if u*w != v*z:
                        continue
                    kind = 'square' if u*u+v*v == w*w+z*z else 'rectangle'
                    points = ((u, -v), (u-w, -v-z), (-w, -z))
                    result.append((kind, points))
    # Symmetric rhombi with unequal diagonals; squares above are not counted twice.
    for w in range(1, STEP + 1):
        for h in range(1, STEP + 1):
            if w != h:
                result.append(('diamond', ((w, -h), (0, -2*h), (-w, -h))))
    return tuple(result)


@lru_cache(maxsize=80)
def number_templates(n):
    return tuple((kind, points) for kind, points in templates()
                 if all(1 <= n+dx <= 80 for dx, _ in points))


def ranked(scores, k, seed):
    rng = random.Random(seed)
    tie = {n: rng.random() for n in range(1, 81)}
    return sorted(scores, key=lambda n: (-scores[n], tie[n]))[:k]


def analyze_geometry(draws, k=10, detail=True, chart_rows=30):
    validate_k(k)
    validate_history(draws)
    if type(chart_rows) is not int or chart_rows not in (30, 50, 100):
        raise ValueError('走势图可显示30、50或100期')
    history = draws[-LOOKBACK:]
    hits_by_offset = {i-LOOKBACK: set(d['numbers']) for i, d in enumerate(history)}
    by_offset = {i-LOOKBACK: d for i, d in enumerate(history)}
    candidates = []
    for n in range(1, 81):
        counts = {kind: {'matched': 0, 'possible': 0} for kind in FAMILIES}
        evidence = []
        for kind, points in number_templates(n):
            counts[kind]['possible'] += 1
            if all(n+dx in hits_by_offset[dy] for dx, dy in points):
                counts[kind]['matched'] += 1
                if detail:
                    evidence.append({'type': kind, 'points': [
                        {'number': n+dx, 'offset': dy, 'issue': by_offset[dy]['issue']}
                        for dx, dy in points]})
        family_scores = {kind: c['matched']/c['possible'] if c['possible'] else 0.0
                         for kind, c in counts.items()}
        item = {'number': n, 'score': mean(family_scores.values()), 'families': counts,
                'familyScores': family_scores, 'supportCount': sum(c['matched'] for c in counts.values())}
        if detail:
            item['evidence'] = sorted(evidence, key=lambda e: (-min(p['offset'] for p in e['points']), e['type']))
        candidates.append(item)
    seed = int(history[-1]['issue'])
    order = ranked({c['number']: c['score'] for c in candidates}, k, seed)
    selections = {'geometry': sorted(order)}
    for kind in FAMILIES:
        selections[kind] = sorted(ranked({c['number']: c['familyScores'][kind] for c in candidates}, k, seed))
    selections['random'] = sorted(random.Random(seed + 700001).sample(range(1, 81), k))
    result = {'version': VERSION, 'asOfIssue': history[-1]['issue'], 'asOfDate': history[-1]['date'],
              'window': LOOKBACK, 'k': k, 'seed': seed, 'dataHash': fingerprint(history),
              'rules': RULES, 'families': FAMILIES, 'rankedNumbers': order,
              'selections': selections, 'previousDraw': {key: history[-1][key] for key in ('issue', 'date', 'numbers')},
              'unsupportedSelections': [n for n in order if not candidates[n-1]['supportCount']],
              'notice': '图形为待检验假设。固定数量比较时，零分号码也可能按固定种子入选；没有形态依据的号码会明确标注。'}
    if detail:
        result['candidates'] = candidates
        # Omission counts use the whole known prefix, never later draws.
        missing = [0] * 80
        seen = set()
        chart = []
        for i, d in enumerate(draws):
            present = set(d['numbers'])
            missing = [0 if n in present else missing[n-1]+1 for n in range(1, 81)]
            seen.update(present)
            if i >= len(draws)-chart_rows:
                chart.append({**{key: d[key] for key in ('issue', 'date', 'numbers')},
                              'offset': i-len(draws), 'missing': missing[:],
                              'missingCensored': [n for n in range(1, 81) if n not in seen]})
        result['chart'] = chart
    return result


def geometry_view(draws, k=10, chart_rows=30, as_of_issue=None):
    if as_of_issue:
        if not re.fullmatch(r'20\d{5}', str(as_of_issue)) or not any(d['issue'] == as_of_issue for d in draws):
            raise ValueError('截止期号不在数据库中')
        draws = [d for d in draws if d['issue'] <= as_of_issue]
    result = analyze_geometry(draws, k, chart_rows=chart_rows)
    context = prediction_context(draws)
    result.update({'freshness': context, 'historicalReplay': bool(as_of_issue),
                   'targetIssue': context['suggestedNextIssue'], 'saved': False})
    return result


def predict_geometry(draws, k=10, chart_rows=30, target_issue=None, today=None):
    context = prediction_context(draws, today)
    if context['stale']:
        raise ValueError('数据过旧，请先同步最新开奖；历史研究请使用截止期回放')
    inferred = not target_issue
    target = str(target_issue or context['suggestedNextIssue'] or '').strip()
    if not re.fullmatch(r'20\d{5}', target) or not adjacent(draws[-1]['issue'], target):
        raise ValueError('图形仅预测紧邻下一期，跨年请核对后填写新年001期')
    result = analyze_geometry(draws, k, chart_rows=chart_rows)
    return {**result, 'kind': 'geometry-next-period', 'generatedAt': utc_now(),
            'targetIssue': target, 'targetInferred': inferred, 'freshness': context,
            'targetNote': '按最新已知期号顺延推算，未核验官方开奖日历。' if inferred else '使用填写的紧邻下一期期号。'}


def backtest_geometry(draws, k=10, folds=100):
    validate_k(k)
    if type(folds) is not int or not 1 <= folds <= 500:
        raise ValueError('图形回测期数必须为1–500')
    start = max(LOOKBACK, len(draws)-folds)
    records, skipped = [], []
    for i in range(start, len(draws)):
        history, actual = draws[i-LOOKBACK:i], draws[i]
        try:
            validate_history(history)
            if not adjacent(history[-1]['issue'], actual['issue']) or history[-1]['date'] >= actual['date']:
                raise ValueError('目标前缺期或顺序异常')
        except ValueError as exc:
            skipped.append({'issue': actual['issue'], 'reason': str(exc)})
            continue
        result = analyze_geometry(history, k, detail=False)
        actual_set = set(actual['numbers'])
        records.append({'issue': actual['issue'], 'trainThrough': result['asOfIssue'],
                        'dataHash': result['dataHash'], 'actual': actual['numbers'],
                        'selections': result['selections'],
                        'unsupportedSelections': result['unsupportedSelections'],
                        'hits': {name: len(set(nums)&actual_set) for name, nums in result['selections'].items()}})
    if not records:
        raise ValueError('没有足够且连续的历史数据可用于回测')
    expected = k/4
    sd = math.sqrt(k*.25*.75*(80-k)/79/len(records))
    summary = {name: {'meanHits': mean(r['hits'][name] for r in records),
                      'totalHits': sum(r['hits'][name] for r in records),
                      'deltaFromRandomExpectation': mean(r['hits'][name] for r in records)-expected,
                      'distribution': [sum(r['hits'][name] == h for r in records) for h in range(k+1)]}
               for name in records[0]['hits']}
    return {'version': VERSION, 'k': k, 'requestedFolds': folds, 'folds': len(records),
            'rules': RULES, 'summary': summary, 'records': records, 'skipped': skipped,
            'theoreticalMeanHits': expected, 'randomNull95Band': [max(0, expected-1.96*sd), min(k, expected+1.96*sd)],
            'note': '历史探索性回测；规则固定，每期仅使用前12期，每策略同选取数量。缺期窗口明确跳过。95%范围基于公平独立开奖假设，未做多重比较校正；不能替代今后开奖前锁定的验证。'}
