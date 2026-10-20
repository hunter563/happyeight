"""Read-only pre-draw hot/cold and omission partitions, with strict temporal cutoffs.

For each target draw, rankings use ONLY prior draws. A display window of N rows
does not justify removing context from older history; caller supplies all draws.
"""
from collections import Counter
from .chart_indicators import validate

PARTITION_SIZES=(4,5,8,10)
def ranked_groups(draws, mode, partitions, lookback=30):
    if mode not in ('frequency','omission'): raise ValueError('unknown rank mode')
    if partitions not in PARTITION_SIZES: raise ValueError('invalid partition count')
    if type(lookback) is not int or lookback<1: raise ValueError('invalid lookback')
    history=[set(validate(row)) for row in draws[-lookback:]]
    if mode=='frequency':
        count=Counter(n for row in history for n in row)
        order=sorted(range(1,81),key=lambda n:(-count[n],n))
    else:
        omissions={}
        for n in range(1,81):
            missed=0
            for row in reversed(history):
                if n in row:break
                missed+=1
            omissions[n]=missed
        order=sorted(range(1,81),key=lambda n:(-omissions[n],n))
    size=80//partitions
    return [order[i:i+size] for i in range(0,80,size)]

def ranking_series(draw_records, mode, partitions, lookback=30, limit=50):
    if type(limit) is not int or limit not in (30,50,100,200,300):raise ValueError('invalid limit')
    records=list(draw_records)
    output=[]
    # First visible rows still use older history. No target outcome in ranking.
    for index in range(max(0,len(records)-limit),len(records)):
        previous=[validate(x['numbers']) for x in records[max(0,index-lookback):index]]
        current=set(validate(records[index]['numbers']))
        if not previous:
            output.append({'issue':str(records[index]['issue']),'counts':None,'groups':None,'historyCount':0})
            continue
        groups=ranked_groups(previous,mode,partitions,lookback)
        output.append({'issue':str(records[index]['issue']),
                       'counts':[len(current.intersection(g)) for g in groups],
                       'groups':groups,'historyCount':len(previous)})
    return {'mode':mode,'partitions':partitions,'lookback':lookback,'rows':output,
            'rankingPoint':'before-target-draw','description':'Descriptive retrospective classification, not future prediction.'}
