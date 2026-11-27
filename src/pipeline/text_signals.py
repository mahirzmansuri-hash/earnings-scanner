"""Text signals from 10-K wording, using SEC's free full-text search (no document downloads).

Run:  python -m src.pipeline.text_signals   (after load_db; resumable)

For each phrase, ask EDGAR full-text search which 10-K filings contain it, month by month
since 2009, and record the filing IDs (accession numbers). Then store a 0/1 flag per 10-K:

  gc_doubt            "raise substantial doubt"           going-concern warning (auditor or management)
  gc_recurring        "recurring losses from operations"  typical going-concern wording
  mw_identified       "identified a material weakness"    a flaw found in internal controls
  icfr_not_effective  "internal control over financial reporting was not effective"
  restated            "have been restated"                past numbers were changed

Why not download the 10-Ks? About 75 GB for every filing since 2009. The search answers
"which filings contain this phrase" with a few thousand small requests instead.
Limit: phrase search is exact, so different wording is missed, and a phrase can appear in a
hypothetical sentence ("if we identified a material weakness"). The model decides how much to trust each flag.
"""
import json
import time
import urllib.parse
from datetime import date

import duckdb
import pandas as pd

from src.config import DB_PATH, RAW_DIR
import requests

from src.pipeline.edgar import _sec_get

PHRASES = {
    "gc_doubt": "raise substantial doubt",
    "gc_recurring": "recurring losses from operations",
    "mw_identified": "identified a material weakness",
    "icfr_not_effective": "internal control over financial reporting was not effective",
    "restated": "have been restated",
}
FTS_URL = "https://efts.sec.gov/LATEST/search-index?q={q}&forms=10-K&dateRange=custom&startdt={start}&enddt={end}&from={offset}"
CACHE = RAW_DIR / "fulltext"
START_YEAR = 2009


def _months(until: date):
    y, m = START_YEAR, 1
    while date(y, m, 1) <= until:
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        yield date(y, m, 1), nxt
        y, m = nxt.year, nxt.month


def _get_with_retry(url: str, tries: int = 5):
    """SEC full-text search sometimes returns 500 under load; wait and retry before giving up."""
    for i in range(tries):
        try:
            return _sec_get(url)
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            if i == tries - 1:
                print(f"    giving up on a page after {tries} tries: {str(e)[:80]}", flush=True)
                return None
            time.sleep(3 * 2 ** i)  # 3, 6, 12, 24 seconds


def collect(name: str, phrase: str, until: date) -> set[str]:
    """Accession numbers of 10-K filings containing `phrase`. Cached per month, so re-runs only fetch new months."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    q = urllib.parse.quote(f'"{phrase}"')
    this_month = date(until.year, until.month, 1).isoformat()
    partial = {}
    for start, nxt in _months(until):
        key = start.isoformat()
        if key in cache and key != this_month:   # the current month is always refreshed
            continue
        end = (pd.Timestamp(nxt) - pd.Timedelta(days=1)).date().isoformat()
        found, offset, complete = set(), 0, True
        while True:
            d = _get_with_retry(FTS_URL.format(q=q, start=key, end=end, offset=offset))
            if d is None:          # keep what we have; the month is retried on the next run
                complete = False
                break
            hits = d["hits"]["hits"]
            found |= {h["_source"]["adsh"] for h in hits}
            offset += len(hits)
            if not hits or offset >= min(d["hits"]["total"]["value"], 10_000):
                break
        if complete:
            cache[key] = sorted(found)
            path.write_text(json.dumps(cache))
        else:
            partial[key] = sorted(found)
    if partial:
        print(f"  {name}: {len(partial)} month(s) incomplete, will retry next run: {sorted(partial)}", flush=True)
    return {a for v in list(cache.values()) + list(partial.values()) for a in v}


def build_text_signals(con) -> pd.DataFrame:
    until = date.today()
    flags = {name: collect(name, phrase, until) for name, phrase in PHRASES.items()}
    # original 10-K accession for each company-year (the filing the point-in-time row is dated by)
    rows = con.execute("""
        SELECT cik, period_end, arg_min(accn_first, filed_first) AS accn
        FROM annual GROUP BY cik, period_end""").df()
    for name, accns in flags.items():
        rows[f"tx_{name}"] = rows["accn"].isin(accns).astype(int)
        print(f"  {name:20} {len(accns):7,} filings with the phrase | {rows[f'tx_{name}'].sum():7,} matched to company-years")
    con.register("tx_df", rows)
    con.execute("CREATE OR REPLACE TABLE text_signals AS SELECT * FROM tx_df")
    con.unregister("tx_df")
    return rows


if __name__ == "__main__":
    with duckdb.connect(str(DB_PATH)) as con:
        build_text_signals(con)
