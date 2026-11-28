"""Point-in-time percentiles: rank each score only against scores public in the 365 days up to its own filing date.

The old method ranked a filing against every filing in its calendar year, including ones filed later that year
(a small look-ahead). Here the comparison set is: same kind of score, filed in (date - 365 days, date].
Ties count half (same convention as pandas rank(pct=True), average method).
"""
import numpy as np
import pandas as pd


def trailing_pctile(dates, scores, days: int = 365) -> np.ndarray:
    d = pd.to_datetime(pd.Series(dates)).dt.normalize().to_numpy()
    s = np.asarray(scores, dtype=float)
    out = np.full(len(s), np.nan)
    ok = ~np.isnan(s) & ~np.isnat(d)           # no date (e.g. restatement-only rows): no percentile, as before
    idx = np.where(ok)[0]
    order = idx[np.argsort(d[idx], kind="stable")]
    dd, ss = d[order], s[order]
    win = np.timedelta64(days, "D")
    for day in np.unique(dd):
        lo, hi = np.searchsorted(dd, day - win, "right"), np.searchsorted(dd, day, "right")
        ref = np.sort(ss[lo:hi])
        today = slice(np.searchsorted(dd, day, "left"), hi)
        x = ss[today]
        below = np.searchsorted(ref, x, "left")
        equal = np.searchsorted(ref, x, "right") - below
        out[order[today]] = (below + (equal + 1) / 2) / len(ref)    # average rank / n, like rank(pct=True)
    return out
