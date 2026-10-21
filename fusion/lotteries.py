"""Eight-game historical analysis. Independent of the frozen KL8 predictor.

Only stored observations are counted. No completeness/probability claims are made.
QXC's 2020100 rule boundary is explicit and never aggregated across versions.
"""
import csv
import io
import json
import re
from collections import Counter
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .data import utc_now


def pool(label, count, low, high, ordered=False):
    return dict(label=label, count=count, min=low, max=high, ordered=ordered)


GAMES = {
    'ssq': dict(name='双色球', issuer='福彩', primary=pool('红球', 6, 1, 33), secondary=pool('蓝球', 1, 1, 16)),
    'fc3d': dict(name='福彩3D', issuer='福彩', primary=pool('百十个位', 3, 0, 9, True)),
    'kl8': dict(name='快乐8', issuer='福彩', primary=pool('开奖号码', 20, 1, 80)),
    'qlc': dict(name='七乐彩', issuer='福彩', primary=pool('基本号', 7, 1, 30), secondary=pool('特别号', 1, 1, 30)),
    'dlt': dict(name='大乐透', issuer='体彩', primary=pool('前区', 5, 1, 35), secondary=pool('后区', 2, 1, 12)),
    'pl3': dict(name='排列3', issuer='体彩', primary=pool('百十个位', 3, 0, 9, True)),
    'pl5': dict(name='排列5', issuer='体彩', primary=pool('万千百十个位', 5, 0, 9, True)),
    'qxc': dict(name='七星彩', issuer='体彩', primary=pool('前六位', 6, 0, 9, True), secondary=pool('第七位', 1, 0, 14)),
}
LIMITS = (30, 50, 100, 200, 300)


def game_spec(game, version='current'):
    if game not in GAMES:
        raise ValueError('不支持的彩种')
    if version not in ('current', 'legacy') or (version == 'legacy' and game != 'qxc'):
        raise ValueError('不支持的规则版本')
    spec = dict(GAMES[game], id=game, ruleVersion=version)
    if version == 'legacy':
        spec['secondary'] = pool('第七位（旧规则）', 1, 0, 9)
    return spec


def canonical_issue(value, year=None):
    raw = str(value).strip()
    if re.fullmatch(r'\d{5}', raw):
        raw = '20' + raw
    if not re.fullmatch(r'20\d{5}', raw) or raw[-3:] == '000':
        raise ValueError('期号须为YYYYNNN形式的7位，或YYNNN形式的5位，序号不能为000')
    if year and raw[:4] != year:
        raise ValueError('期号与开奖日期年份不一致')
    return raw


def numbers(value, spec):
    if isinstance(value, str):
        # Compact ordered digits retain zeroes, e.g. "001". QXC must use
        # separate primary/secondary fields because its last number may be 14.
        value = value.strip()
        if spec['ordered'] and re.fullmatch(r'\d{' + str(spec['count']) + '}', value):
            value = list(value)
        else:
            value = re.split(r'[,，\s]+', value) if value else []
    if not isinstance(value, list) or any(type(v) not in (int, str) or not re.fullmatch(r'\d{1,2}', str(v)) for v in value):
        raise ValueError(f"{spec['label']}必须是整数数组或空格分隔的号码")
    result = [int(v) for v in value]
    if len(result) != spec['count'] or not all(spec['min'] <= n <= spec['max'] for n in result):
        raise ValueError(f"{spec['label']}需要{spec['count']}个{spec['min']}—{spec['max']}的号码")
    if not spec['ordered']:
        if len(result) != len(set(result)):
            raise ValueError(f"{spec['label']}号码不能重复")
        result.sort()
    return result


def normalize_draw(game, row):
    game_spec(game)
    if not isinstance(row, dict):
        raise ValueError('每条开奖记录须为对象')
    if row.get('game', game) != game:
        raise ValueError('记录彩种与导入目标不一致')
    day = str(row.get('date', '')).strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
        raise ValueError('开奖日期须为YYYY-MM-DD')
    date.fromisoformat(day)
    if day > datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat():
        raise ValueError('不能导入未来日期的开奖结果')
    issue = canonical_issue(row.get('issue', ''), day[:4])
    version = 'legacy' if game == 'qxc' and issue < '2020100' else 'current'
    if 'ruleVersion' in row and row['ruleVersion'] != version:
        raise ValueError('记录规则版本与期号不一致')
    spec = game_spec(game, version)
    primary = numbers(row.get('primary', row.get('numbers', [])), spec['primary'])
    if 'secondary' in spec:
        secondary = numbers(row.get('secondary', []), spec['secondary'])
    else:
        if row.get('secondary') not in (None, [], ''):
            raise ValueError('该彩种没有第二号码区')
        secondary = []
    if game == 'qlc' and set(primary) & set(secondary):
        raise ValueError('七乐彩特别号不能与基本号重复')
    return dict(game=game, issue=issue, date=day, primary=primary, secondary=secondary, ruleVersion=version)


def parse_lottery_csv(text):
    if not isinstance(text, str):
        raise ValueError('CSV须为文本')
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    if not {'issue', 'date', 'primary'} <= set(reader.fieldnames or []):
        raise ValueError('CSV需要issue,date,primary列，可选secondary列')
    return list(reader)


class LotteryStore:
    """Share the SQLite connection while leaving existing KL8 tables intact."""
    def __init__(self, store):
        self.store = store
        with store.connect() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS lottery_draws(
                game TEXT NOT NULL, issue TEXT NOT NULL, date TEXT NOT NULL,
                primary_numbers TEXT NOT NULL, secondary_numbers TEXT NOT NULL,
                rule_version TEXT NOT NULL, source TEXT NOT NULL, imported_at TEXT NOT NULL,
                PRIMARY KEY(game,issue))''')

    def draws(self, game):
        game_spec(game)
        if game == 'kl8':
            return [dict(game=game, issue=r['issue'], date=r['date'], primary=r['numbers'],
                         secondary=[], ruleVersion='current', source=r['source'], importedAt=r['imported_at'])
                    for r in self.store.draws()]
        with self.store.connect() as conn:
            rows = conn.execute('SELECT * FROM lottery_draws WHERE game=? ORDER BY date,issue', (game,))
            return [dict(game=game, issue=r['issue'], date=r['date'], primary=json.loads(r['primary_numbers']),
                         secondary=json.loads(r['secondary_numbers']), ruleVersion=r['rule_version'],
                         source=r['source'], importedAt=r['imported_at']) for r in rows]

    def catalog(self):
        with self.store.connect() as conn:
            counts = {r['game']: (r['n'], r['latest']) for r in conn.execute(
                'SELECT game,COUNT(*) n,MAX(date) latest FROM lottery_draws GROUP BY game')}
            r = conn.execute('SELECT COUNT(*) n,MAX(date) latest FROM draws').fetchone()
            counts['kl8'] = (r['n'], r['latest'])
        return [dict(game_spec(game), count=counts.get(game, (0, None))[0],
                     latestDate=counts.get(game, (0, None))[1], onlineSync=game == 'kl8') for game in GAMES]

    def import_draws(self, game, rows, source='用户导入'):
        game_spec(game)
        if not isinstance(source, str) or not 1 <= len(source.strip()) <= 300:
            raise ValueError('请填写1—300字的数据来源')
        if not isinstance(rows, list) or not 1 <= len(rows) <= 10000:
            raise ValueError('每批需包含1—10000条开奖记录')
        validated = [normalize_draw(game, row) for row in rows]
        if game == 'kl8':
            return dict(self.store.import_draws([
                dict(issue=r['issue'], date=r['date'], numbers=r['primary']) for r in validated], source.strip()), game=game)
        inserted = 0
        with self.store.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            for row in validated:
                values = (row['date'], json.dumps(row['primary']), json.dumps(row['secondary']), row['ruleVersion'])
                old = conn.execute('SELECT date,primary_numbers,secondary_numbers,rule_version FROM lottery_draws WHERE game=? AND issue=?', (game, row['issue'])).fetchone()
                if old:
                    if tuple(old) != values:
                        raise ValueError(f"期号 {row['issue']} 与已有数据冲突，整批取消，请先核验来源")
                    continue
                conn.execute('INSERT INTO lottery_draws VALUES(?,?,?,?,?,?,?,?)', (game, row['issue'], *values, source.strip(), utc_now()))
                inserted += 1
        return dict(game=game, inserted=inserted, duplicates=len(validated)-inserted, source=source.strip())


def _values(row, field):
    values = row[field['pool']]
    return [values[field['index']]] if 'index' in field else values


def _metrics(values, spec, previous):
    threshold = (spec['min'] + spec['max'] + 1) // 2
    return dict(sum=sum(values), span=max(values)-min(values), odd=sum(n % 2 for n in values),
                big=sum(n >= threshold for n in values), residues=[sum(n % 3 == r for n in values) for r in range(3)],
                repeat=None if previous is None else len(set(values) & set(previous)),
                amplitude=None if previous is None or len(values) != 1 else abs(values[0]-previous[0]))


def analyze_lottery(draws, game, limit=50, start=None, end=None, version='current', field_id='primary'):
    spec = game_spec(game, version)
    if type(limit) is not int or limit not in LIMITS:
        raise ValueError('统计期数仅支持30、50、100、200、300')
    start = canonical_issue(start) if start else None
    end = canonical_issue(end) if end else None
    if start and end and start > end:
        raise ValueError('起始期号不能晚于结束期号')
    if any(d['game'] != game for d in draws):
        raise ValueError('分析数据混入其他彩种')
    history = sorted((d for d in draws if d['ruleVersion'] == version and (not end or d['issue'] <= end)), key=lambda d: (d['date'], d['issue']))
    candidates = [d for d in history if not start or d['issue'] >= start]
    selected = candidates[-limit:]
    fields = []
    for key in ('primary', 'secondary'):
        if key not in spec:
            continue
        p = spec[key]
        fields.append(dict(id=key, label=p['label'], pool=key, spec=p))
        if p['count'] > 1:
            if p['ordered'] and p['count'] in (3, 5):
                positions = list('万千百十个'[-p['count']:])
            else:
                positions = [str(i+1) for i in range(p['count'])]
            for i, name in enumerate(positions):
                label = f'{name}位' if p['ordered'] and p['count'] in (3, 5) else f"{'第' if p['ordered'] else '升序第'}{name}位"
                fields.append(dict(id=f'{key}:{i}', label=f"{p['label']} · {label}", pool=key, index=i, spec=dict(p, count=1)))
    selected_issues = {r['issue'] for r in selected}
    selected_history = [r for r in history if selected and r['issue'] <= selected[-1]['issue']]
    if field_id not in {f['id'] for f in fields}:
        raise ValueError('不支持的号码区或位置')
    active = None
    for field in fields:
        if field['id'] != field_id:
            continue
        p = field['spec']
        # History before the visible window supplies omission and previous values.
        previous = None
        last_seen = {}
        frequency = Counter()
        occurrences = Counter()
        series = []
        for index, row in enumerate(selected_history):
            values = _values(row, field)
            omissions = [dict(number=n, value=0 if n in values else index-last_seen[n] if n in last_seen else index+1,
                              lowerBound=n not in last_seen and n not in values) for n in range(p['min'], p['max']+1)]
            if row['issue'] in selected_issues:
                frequency.update(values)
                occurrences.update(set(values))
                series.append(dict(issue=row['issue'], date=row['date'], values=values, omissions=omissions,
                                   **_metrics(values, p, previous)))
            for n in values:
                last_seen[n] = index
            previous = values
        n_history = len(selected_history)
        frequencies = [dict(number=n, count=frequency[n], drawCount=occurrences[n],
                            omission=n_history-1-last_seen[n] if n in last_seen else n_history,
                            lowerBound=n not in last_seen) for n in range(p['min'], p['max']+1)]
        active = dict(id=field['id'], label=field['label'], spec=p, series=series, frequencies=frequencies)
    latest = selected[-1] if selected else None
    age = (datetime.now(ZoneInfo('Asia/Shanghai')).date()-date.fromisoformat(latest['date'])).days if latest else None
    return dict(game=spec, totalStored=len(draws), availableInRule=sum(d['ruleVersion'] == version for d in draws),
                count=len(selected), requestedLimit=limit, fromIssue=selected[0]['issue'] if selected else None,
                toIssue=latest['issue'] if latest else None, latest=latest, ageDays=age, draws=selected,
                fields=[{k:f[k] for k in ('id','label','spec')} for f in fields], activeField=active,
                definition='频次为选定窗口内的出现次数；遗漏仅按库内记录计数，未见过的号码以≥标记。未验证缺期，不代表官方连续开奖。')
