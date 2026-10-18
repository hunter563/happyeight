"""将同一份历史分析转为有明确目标期号的预测，避免旧数据冒充实时下一期。"""
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .data import utc_now
from .engine import analyze


def prediction_context(draws, today=None):
    today=today or datetime.now(ZoneInfo('Asia/Shanghai')).date()
    if not draws:
        return {'suggestedNextIssue':None,'ageDays':None,'stale':True}
    latest=draws[-1]
    day=date.fromisoformat(latest['date'])
    age=(today-day).days
    # 不把上一年的末期直接加一：跨年编号和休市安排需人工核验。
    can_infer=day.year==today.year and (day.month,day.day)!=(12,31) and int(latest['issue'][-3:])<999
    return {'suggestedNextIssue':str(int(latest['issue'])+1) if can_infer else None,
            'ageDays':age,'stale':age>1,'asOfIssue':latest['issue'],'asOfDate':latest['date']}


def predict(draws,k=10,window=120,target_issue=None,today=None):
    context=prediction_context(draws,today)
    target=str(target_issue or '').strip()
    inferred=not target
    if not draws: raise ValueError('没有开奖数据，请先同步或导入')
    if inferred and context['stale']:
        raise ValueError(f"数据截至 {context['asOfDate']}，不能确定实时下一期；请先同步，或填写目标期号进行历史数据研究")
    if inferred:
        target=context['suggestedNextIssue']
        if not target: raise ValueError('跨年期号无法自动确认，请核对后填写目标期号')
    if not re.fullmatch(r'20\d{5}',target) or target<=max(d['issue'] for d in draws):
        raise ValueError('预测目标期号必须晚于所有已知开奖期号')
    result=analyze(draws,k,window)
    return {**result,'kind':'next-period-prediction','targetIssue':target,'targetInferred':inferred,
            'generatedAt':utc_now(),'freshness':context,
            'targetNote':'按最新已知期号顺延推算，未核验官方开奖日历。' if inferred else '使用你填写的目标期号。',
            'notice':'模型候选用于验证，不代表已知开奖结果或中奖保证；当前没有证据证明融合策略稳定优于随机选号。'}
