"""Read-only chart series: independent reconstruction of publicly described indicators."""
from .chart_indicators import validate, profile, history_stats, group_counts, residue_groups, range_groups

def is_prime(n):
    if n == 1:
        return True  # Chart convention: 1 is counted as 质
    if n < 2:
        return False
    return all(n % p for p in range(2, int(n ** 0.5) + 1))

def omission_summary(draws):
    """Window-based number omission; leading gap is censored, not a completed gap."""
    records = [set(validate(row)) for row in draws]
    results = {}
    for n in range(1,81):
        appearances = [i for i,row in enumerate(records) if n in row]
        current = len(records)-1-appearances[-1] if appearances else len(records)
        previous = (appearances[-1]-appearances[-2]-1) if len(appearances)>1 else None
        completed = [b-a-1 for a,b in zip(appearances,appearances[1:])]
        results[n] = {
            "appearances":len(appearances),
            "current":current,
            "previousCompleted":previous,
            "maxCompleted":max(completed) if completed else None,
            "avgCompleted":round(sum(completed)/len(completed),3) if completed else None,
            "maxObservedIncludingCensored":max([current]+completed) if records else 0,
            "censoredAtWindowStart":bool(not appearances or appearances[0]>0),
        }
    return results

def position_profile(draw, previous=None):
    """Positions mean sorted positions, never arbitrary input order."""
    nums=sorted(validate(draw))
    older=sorted(validate(previous)) if previous is not None else None
    return [{
        "position":i+1,
        "number":n,"tail":n%10,"tailSize":"small" if n%10<5 else "large",
        "tailParity":"odd" if n%2 else "even",
        "prime":is_prime(n),
        "mod3":n%3,
        "direction":None if older is None else ("up" if n>older[i] else "down" if n<older[i] else "flat"),
        "amplitude":None if older is None else abs(n-older[i]),
    } for i,n in enumerate(nums)]

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
            "positions":position_profile(nums,previous),
        })
        previous=nums
    return {
        "mode":"historical-statistics-only",
        "count":len(rows),
        "limit":limit,
        "rows":rows,
        "frequency": history_stats([r["numbers"] for r in rows]),
        "omissionSummary": omission_summary([r["numbers"] for r in rows]),
        "omissionMethod": "Window-only: completed gaps exclude leading/trailing censored observations; insufficient history is null.",
    }
