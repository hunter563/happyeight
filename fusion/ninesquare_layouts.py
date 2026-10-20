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

# Additional published 9x9 arrangements verified against public chart text.
LOOSENED = [
[4,9,2,3,5,7,8,1,6],
[35,37,38,31,36,30,80,10,14],
[33,52,53,55,57,58,51,20,19],
[32,59,74,79,72,73,56,40,12],
[39,54,66,76,None,75,64,60,13],
[34,46,61,71,78,77,69,70,15],
[26,41,68,67,65,63,62,50,17],
[21,48,47,45,43,42,49,44,18],
[28,27,25,23,22,29,24,16,11],
]
WOUND = [
[79,72,73,75,77,78,71,76,None],
[74,70,50,44,49,42,43,45,47],
[66,60,22,23,25,27,28,21,48],
[61,40,29,8,1,6,14,26,41],
[68,20,24,7,4,9,19,34,46],
[67,10,16,5,3,2,12,39,54],
[65,80,11,18,17,15,13,32,59],
[63,30,36,31,38,37,35,33,52],
[62,69,64,56,51,58,57,55,53],
]
ZIGZAG = [
[4,9,7,8,17,18,34,39,44],
[2,5,1,15,11,26,32,50,49],
[3,6,13,16,21,33,70,42,58],
[14,12,24,28,35,60,43,57,51],
[19,29,27,37,40,45,55,56,66],
[22,25,38,20,47,53,64,61,74],
[23,31,10,48,52,69,68,79,78],
[36,80,41,59,62,67,72,77,71],
[30,46,54,63,65,73,75,76,None],
]
FOLDED = [
[4,9,2,3,5,7,8,1,6],
[16,11,18,17,15,13,12,19,14],
[24,29,22,23,25,27,28,21,26],
[36,31,38,37,35,33,32,39,34],
[30,80,10,20,40,60,70,50,44],
[54,46,41,48,47,45,43,42,49],
[59,52,53,55,57,58,51,56,64],
[74,66,61,68,67,65,63,62,69],
[79,72,73,75,77,78,71,76,None],
]
LAYOUTS = {
    "standard": STANDARD,
    "symmetric": SYMMETRIC,
    "loosened": LOOSENED,
    "wound": WOUND,
    "zigzag": ZIGZAG,
    "folded": FOLDED,
}
for key, rows in LAYOUTS.items():
    assert len(rows) == 9 and all(len(row) == 9 for row in rows), key
    assert sorted(n for row in rows for n in row if n is not None) == list(range(1,81)), key
    assert sum(n is None for row in rows for n in row) == 1, key


# Odd/even rotating charts contain 40 numbered cells each, with intentional blanks.
# Publicly displayed row order, not a forecast model.
EVEN_ROTATION = [
[None,2,None,4,None,6,None,8,None],
[32,None,34,None,36,None,38,None,10],
[None,56,None,58,None,60,None,40,None],
[30,None,72,None,74,None,62,None,12],
[None,54,None,80,None,76,None,42,None],
[28,None,70,None,78,None,64,None,14],
[None,52,None,68,None,66,None,44,None],
[26,None,50,None,48,None,46,None,16],
[None,24,None,22,None,20,None,18,None],
]
ODD_ROTATION = [
[1,None,3,None,5,None,7,None,9],
[None,33,None,35,None,37,None,39,None],
[31,None,57,None,59,None,61,None,11],
[None,55,None,73,None,75,None,41,None],
[29,None,71,None,None,None,63,None,13],
[None,53,None,79,None,77,None,43,None],
[27,None,69,None,67,None,65,None,15],
[None,51,None,49,None,47,None,45,None],
[25,None,23,None,21,None,19,None,17],
]
HALF_LAYOUTS = {"even_rotation": EVEN_ROTATION, "odd_rotation": ODD_ROTATION}
for key, rows in HALF_LAYOUTS.items():
    assert len(rows)==9 and all(len(row)==9 for row in rows), key
    expected = list(range(2,81,2)) if key=="even_rotation" else list(range(1,80,2))
    assert sorted(n for row in rows for n in row if n is not None)==expected, key

def grid(name):
    if name not in LAYOUTS and name not in HALF_LAYOUTS:
        raise ValueError("Unknown verified nine-square layout")
    rows = LAYOUTS[name] if name in LAYOUTS else HALF_LAYOUTS[name]
    return [row[:] for row in rows]

def grid_hits(name, numbers):
    from .chart_indicators import validate
    hits = set(validate(numbers))
    return [[None if n is None else (n in hits) for n in row] for row in grid(name)]
