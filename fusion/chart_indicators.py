"""Independent descriptive chart indicators inspired by publicly documented chart categories.
No prediction API changes, no external scraping, no copying proprietary implementation.
Input: chronological draws, each sequence of 20 unique integers in 1..80.
"""
from collections import Counter
from math import comb

def validate(draw):
    nums = list(draw)
    if len(nums) != 20 or len(set(nums)) != 20 or any(not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 80 for n in nums):
        raise ValueError("Each draw needs 20 distinct integers from 1 to 80")
    return nums

def group_counts(draw, groups):
    s = set(validate(draw))
    return [sum(n in s for n in group) for group in groups]

def residue_groups(modulus):
    if not 2 <= modulus <= 20:
        raise ValueError("modulus must be in [2,20]")
    return [[n for n in range(1, 81) if n % modulus == r] for r in range(modulus)]

def range_groups(parts):
    if not 2 <= parts <= 20:
        raise ValueError("parts must be in [2,20]")
    q, r = divmod(80, parts)
    out, start = [], 1
    for i in range(parts):
        width = q + (i < r)
        out.append(list(range(start, start + width)))
        start += width
    return out

def digit_presence_groups():
    return [[n for n in range(1, 81) if str(d) in str(n)] for d in range(10)]

def color_groups():
    return {
        "red": [1,2,7,8,12,13,18,19,23,24,29,30,34,35,40,45,46,53,54,59,60,64,65,70,75,76,80],
        "blue": [3,4,9,10,14,15,20,25,26,31,36,37,41,42,47,48,50,55,56,61,66,67,71,72,77,78],
        "green": [5,6,11,16,17,21,22,27,28,32,33,38,39,43,44,49,51,52,57,58,62,63,68,69,73,74,79],
    }

def element_groups():
    return {
        "metal": [9,10,21,22,33,34,45,46,57,58,69,70],
        "wood": [3,4,15,16,27,28,39,40,51,52,63,64,75,76],
        "water": [1,12,13,24,25,36,37,48,49,60,61,72,73],
        "fire": [6,7,18,19,30,31,42,43,54,55,66,67,78,79],
        "earth": [2,5,8,11,14,17,20,23,26,29,32,35,38,41,44,47,50,53,56,59,62,65,68,71,74,77,80],
    }

def reversal_pairs():
    pairs = set()
    for n in range(1,81):
        if n % 10 == 0:
            rev = n // 10
        elif n < 10:
            rev = n * 10
        else:
            rev = (n % 10) * 10 + n // 10
        if 1 <= rev <= 80 and rev != n:
            pairs.add(tuple(sorted((n,rev))))
    return sorted(pairs)

def profile(draw, previous=None):
    raw = validate(draw)
    nums = sorted(raw)
    total = sum(nums)
    span = nums[-1] - nums[0]
    s = set(nums)
    out = {
        "sum": total, "sum_tail": total % 10,
        "span": span, "span_tail": span % 10,
        "mean": total / 20,
        "min": nums[0], "max": nums[-1],
        "odd": sum(n % 2 != 0 for n in nums),
        "even": sum(n % 2 == 0 for n in nums),
        "small": sum(n <= 40 for n in nums),
        "large": sum(n > 40 for n in nums),
        "tail_sum": sum(n % 10 for n in nums),
        "tail_small": sum(n % 10 < 5 for n in nums),
        "tail_large": sum(n % 10 >= 5 for n in nums),
        "residue_counts": {m: group_counts(nums, residue_groups(m)) for m in range(3, 15)},
        "range_counts": {m: group_counts(nums, range_groups(m)) for m in range(3, 13)},
        "digit_presence": group_counts(nums, digit_presence_groups()),
        "color_counts": {k:len(s.intersection(v)) for k,v in color_groups().items()},
        "element_counts": {k:len(s.intersection(v)) for k,v in element_groups().items()},
        "repeat_pairs": sum(a in s and b in s for a,b in reversal_pairs()),
        "consecutive_pairs": sum(n+1 in s for n in nums),
    }
    if previous is not None:
        prior = set(validate(previous))
        out["repeat_from_previous"] = len(prior & s)
        out["new_from_previous"] = len(s - prior)
        a = sorted(prior)
        out["position_direction"] = [
            "up" if x > y else "same" if x == y else "down"
            for x,y in zip(nums,a)
        ]
        out["position_amplitude"] = [abs(x-y) for x,y in zip(nums,a)]
    return out

def history_stats(draws, window=None):
    rows = [validate(row) for row in draws]
    if window is not None:
        if not isinstance(window,int) or window < 1:
            raise ValueError("window must be a positive integer")
        rows = rows[-window:]
    freq = Counter(n for row in rows for n in row)
    omissions = {}
    for n in range(1,81):
        misses = 0
        for row in reversed(rows):
            if n in row:
                break
            misses += 1
        omissions[n] = misses
    ranked_hot = sorted(range(1,81),key=lambda n:(-freq[n],n))
    ranked_missing = sorted(range(1,81),key=lambda n:(-omissions[n],n))
    return {
        "draws":len(rows), "frequency":{n:freq[n] for n in range(1,81)},
        "omission":omissions,
        "hot_order":ranked_hot, "omission_order":ranked_missing,
        "expected_frequency":len(rows)/4,
        "expected_overlap_next_draw_for_k9":2.25,
    }

def random_match_distribution(picks=9):
    """Exact hypergeometric null, not a prediction."""
    if not 1 <= picks <= 80:
        raise ValueError("picks must be between 1 and 80")
    denominator = comb(80,picks)
    return {hits:comb(20,hits)*comb(60,picks-hits)/denominator
            for hits in range(max(0,picks-60),min(20,picks)+1)}
