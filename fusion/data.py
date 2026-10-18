"""标准化、校验和事务存储。所有分析按日期和期号升序取数。"""
import csv
import hashlib
import io
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def normalize(row):
    issue = str(row.get('issue', row.get('期号', ''))).strip()
    day = str(row.get('date', row.get('开奖日期', '')))[:10]
    values = row.get('numbers', row.get('开奖号码', []))
    if isinstance(values, str):
        values = re.split(r'[,，\s]+', values.strip())
    if not re.fullmatch(r'20\d{5}', issue):
        raise ValueError(f'非法期号：{issue}')
    date.fromisoformat(day)
    if day > datetime.now(timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Asia/Shanghai')).date().isoformat():
        raise ValueError('不能导入未来日期的开奖结果')
    if any(isinstance(n, bool) or not re.fullmatch(r'\d{1,2}', str(n)) for n in values):
        raise ValueError(f'{issue} 含有非整数号码')
    numbers = sorted(int(n) for n in values)
    if len(numbers) != 20 or len(set(numbers)) != 20 or not all(1 <= n <= 80 for n in numbers):
        raise ValueError(f'{issue} 必须包含20个不重复的1–80号码')
    if issue[:4] != day[:4]:
        raise ValueError(f'{issue} 与日期年份不一致')
    return {'issue': issue, 'date': day, 'numbers': numbers}

def parse_csv(text):
    return [normalize(row) for row in csv.DictReader(io.StringIO(text.lstrip('\ufeff')))]

def fingerprint(draws):
    canonical = [{k:d[k] for k in ('issue','date','numbers')} for d in draws]
    return hashlib.sha256(json.dumps(canonical,sort_keys=True).encode()).hexdigest()

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS draws(issue TEXT PRIMARY KEY, date TEXT NOT NULL, numbers TEXT NOT NULL, source TEXT NOT NULL, imported_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS experiments(id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, target_issue TEXT NOT NULL, as_of_issue TEXT NOT NULL, data_hash TEXT NOT NULL, payload TEXT NOT NULL);
            ''')

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def import_draws(self, rows, source):
        validated = [normalize(row) for row in rows]
        if not validated:
            raise ValueError('没有可导入的开奖数据')
        new = 0
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            for row in validated:
                numbers = json.dumps(row['numbers'])
                old = conn.execute('SELECT date,numbers FROM draws WHERE issue=?',(row['issue'],)).fetchone()
                if old:
                    if old['date'] != row['date'] or old['numbers'] != numbers:
                        raise ValueError(f"期号 {row['issue']} 与已有数据冲突，整批取消，请先核验来源")
                    continue
                conn.execute('INSERT INTO draws VALUES(?,?,?,?,?)',(row['issue'],row['date'],numbers,source,utc_now()))
                new += 1
        return {'inserted':new,'duplicates':len(validated)-new,'source':source}

    def draws(self, conn=None):
        if conn is None:
            with self.connect() as connection:
                return self.draws(connection)
        return [dict(row, numbers=json.loads(row['numbers'])) for row in conn.execute('SELECT * FROM draws ORDER BY date,issue')]

    def seed(self):
        if self.draws():
            return
        rows = parse_csv((ROOT/'vendor/luck8/kl8_history.csv').read_text(encoding='utf-8-sig'))
        self.import_draws(rows,'fightingfor/Luck8 历史快照；未经逐期官方核验')
        snapshot=ROOT/'samples/history-snapshot.json'
        if snapshot.exists():
            payload=json.loads(snapshot.read_text())
            self.import_draws(payload['draws'],payload['source'])

    def experiments(self):
        with self.connect() as conn:
            draws={d['issue']:d for d in self.draws(conn)}
            results=[]
            for row in conn.execute('SELECT * FROM experiments ORDER BY id DESC LIMIT 100'):
                item=dict(row); item['payload']=json.loads(item['payload'])
                # 仅补充展示用对照，不改写旧模型预测或已保存的 payload。
                previous=draws.get(item['as_of_issue'])
                item['previousDraw']={k:previous[k] for k in ('issue','date','numbers')} if previous else None
                actual=draws.get(item['target_issue'])
                item['actual']=actual
                item['settled']=actual is not None
                if actual:
                    item['hits']={name:len(set(numbers)&set(actual['numbers'])) for name,numbers in item['payload']['selections'].items()}
                results.append(item)
            return results
