"""Read-only chart series: independent reconstruction of publicly described indicators."""
from .chart_indicators import validate, profile, history_stats, group_counts, residue_groups, range_groups

def is_prime(n):
    if n == 1:
        return True  # Chart convention: 1 is counted as 质
    if n < 2:
        return False
    return all(n % p for p in range(2, int(n ** 0.5) + 1))

def chart_series(draw_records, limit=50):
    """Records must be chronological and shaped {issue,date,numbers}; never predicts."""
    if type(limit) is not int or limit not in (30, 50, 100, 200, 300):
        raise ValueError("limit must be one of 30,50,100,200,300")
    records = draw_records[-limit:]
    rows = []
    previous = None
    for item in records:
        nums = validate(item["numbers"])
        p = profile(nums, previous)
        s = set(nums)
        total=p["sum"]
        span=p["span"]
        rows.append({
            "issue":str(item["issue"]),
            "date":item.get("date"),
            "numbers":sorted(nums),
            "sum":total,
            "sumTail":total % 10,
            "span":span,
            "spanTail":span % 10,
            "mean":p["mean"],
            "max":p["max"], "min":p["min"],
            "sumSpanSumTail":(total+span)%10,
            "sumSpanDiffTail":(total-span)%10,
            "odd":p["odd"],"even":p["even"],
            "prime":sum(is_prime(n) for n in nums),
            "composite":sum(not is_prime(n) for n in nums),
            "small":p["small"], "large":p["large"],
            "tailSmall":p["tail_small"],"tailLarge":p["tail_large"],
            "residues":{str(m):group_counts(nums,residue_groups(m)) for m in range(3,21)},
            "ranges":{str(m):group_counts(nums,range_groups(m)) for m in range(3,13)},
            "repeatFromPrevious":p.get("repeat_from_previous"),
            "positionDirection":p.get("position_direction"),
            "positionAmplitude":p.get("position_amplitude"),
            "consecutivePairs":p["consecutive_pairs"],
        })
        previous=nums
    return {
        "mode":"historical-statistics-only",
        "count":len(rows),
        "limit":limit,
        "rows":rows,
        "frequency": history_stats([r["numbers"] for r in rows]),
    }
