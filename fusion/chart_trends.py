"""Additional read-only historical trend markers, independent of forecasting.
All inputs are known draws, chronological oldest to newest.
No claims of statistical predictiveness.
"""
from .chart_indicators import validate

def classify_number(n):
    return {
        "number":n, "size":"small" if n<=40 else "large",
        "parity":"even" if n%2==0 else "odd",
        "tail":n%10, "mod3":n%3,
        "decade":(n-1)//10+1
    }

def transition_labels(current, previous=None):
    current=set(validate(current))
    if previous is None:
        return {"repeat":[],"new":sorted(current),"adjacent":[],"adjacentNew":[]}
    previous=set(validate(previous))
    adjacent={candidate for n in previous for candidate in (n-1,n+1) if 1<=candidate<=80}
    return {
        "repeat":sorted(current & previous),
        "new":sorted(current - previous),
        "adjacent":sorted(current & adjacent),
        "adjacentNew":sorted((current-previous) & adjacent),
    }

def draw_streaks(draws):
    """Current per-number consecutive-hit run and maximum completed/observed run."""
    rows=[set(validate(row)) for row in draws]
    output={}
    for n in range(1,81):
        run=0; maximum=0; streaks=[]
        for row in rows:
            if n in row:
                run+=1
                maximum=max(maximum,run)
            elif run:
                streaks.append(run)
                run=0
        output[n]={
            "currentRun":run,
            "maxObservedRun":maximum,
            "completedRuns":len(streaks),
            "meanCompletedRun":round(sum(streaks)/len(streaks),3) if streaks else None
        }
    return output

def category_trend(draws):
    """Complete historical rows for common public visual toggles."""
    rows=[validate(row) for row in draws]
    out=[]
    prev=None
    for row in rows:
        s=set(row)
        labels=transition_labels(row,prev)
        out.append({
            "repeat":len(labels["repeat"]),
            "repeatNumbers":labels["repeat"],
            "adjacent":len(labels["adjacent"]),
            "adjacentNumbers":labels["adjacent"],
            "adjacentNew":len(labels["adjacentNew"]),
            "adjacentNewNumbers":labels["adjacentNew"],
            "decadeDistribution":[sum(lo<=n<=lo+9 for n in s) for lo in range(1,81,10)],
            "tailDistribution":[sum(n%10==t for n in s) for t in range(10)],
            "odd":sum(n%2==1 for n in s),
            "even":sum(n%2==0 for n in s),
            "overlapKnown":prev is not None,
        })
        prev=row
    return out
