"""Publicly visible nine-square layouts, copied as number arrangements only.

These are *layout reference fixtures* transcribed from public chart pages,
not hidden prediction models or scraped datasets.
Source: https://tb.tuganjue.com/tgj-kl8-jggjxzs.html
and https://tb.tuganjue.com/tgj-kl8-jggdcjxzs.html
"""

STANDARD = [
    [4,9,2,14,19,12,24,29,22],
    [3,5,7,13,15,17,23,25,27],
    [8,1,6,18,11,16,28,21,26],
    [34,39,32,30,80,10,44,49,42],
    [33,35,37,20,40,60,43,45,47],
    [38,31,36,70,None,50,48,41,46],
    [54,59,52,64,69,62,74,79,72],
    [53,55,57,63,65,67,73,75,77],
    [58,51,56,68,61,66,78,71,76],
]
SYMMETRIC = [
    [4,3,8,34,33,38,54,53,58],
    [9,5,1,39,35,31,59,55,51],
    [2,7,6,32,37,36,52,57,56],
    [14,13,18,30,20,70,64,63,68],
    [19,15,11,80,40,None,69,65,61],
    [12,17,16,10,60,50,62,67,66],
    [24,23,28,44,43,48,74,73,78],
    [29,25,21,49,45,41,79,75,71],
    [22,27,26,42,47,46,72,77,76],
]

def grid(name):
    if name not in ("standard", "symmetric"):
        raise ValueError("Unknown verified nine-square layout")
    rows = STANDARD if name == "standard" else SYMMETRIC
    return [row[:] for row in rows]

def grid_hits(name, numbers):
    from .chart_indicators import validate
    hits = set(validate(numbers))
    return [[None if n is None else (n in hits) for n in row] for row in grid(name)]
