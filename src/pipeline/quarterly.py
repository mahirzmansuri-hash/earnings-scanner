"""Quarterly (10-Q) data: a fresh, full-year view of each company at every 10-Q.

Run:  python -m src.pipeline.quarterly     (after annual; reads the cached companyfacts files, no downloads)

A 10-Q has a balance sheet at the quarter end, but its income statement and cash flow only cover
"year to date" (3, 6 or 9 months). To compare with annual numbers we build trailing twelve months:

    TTM = year-to-date now + last full fiscal year - the same year-to-date period last year

Example: a 10-Q for the 9 months to Sep 30, 2024 -> Oct 2023-Sep 2024 =
         9M 2024 + FY2023 - 9M 2023.

Point in time: every piece must have been public on the 10-Q's filing date. Last year's
year-to-date value is the first-filed one (usually from last year's 10-Q); the full year is the
original 10-K value from annual_first, used only if that 10-K was filed before the 10-Q.

Tables
  qfacts     : 10-Q facts for the tags in tag_map (cik, concept, period, value, accn, filed)
  quarterly  : one row per 10-Q: balance sheet at quarter end + TTM flows, same columns as annual_first
"""
import gzip
import json
import time
from multiprocessing import Pool

import duckdb
import pandas as pd

from src.config import DB_PATH
from src.pipeline.edgar import FACTS_DIR
from src.pipeline.tag_map import CONCEPTS, DERIVED

Q_FORMS = {"10-Q", "10-Q/A"}
TAG_TO_CONCEPTS = {}
for c, spec in CONCEPTS.items():
    if c == "public_float":          # only on 10-K covers; the latest annual value is carried forward
        continue
    for prio, t in enumerate(spec["tags"]):
        TAG_TO_CONCEPTS.setdefault(t, []).append((c, prio))
FLOWS = [c for c, s in CONCEPTS.items() if s["kind"] == "duration"]
STOCKS = [c for c, s in CONCEPTS.items() if s["kind"] == "instant" and c != "public_float"]


def _rows(path) -> list[tuple]:
    cik = int(path.name[3:13])
    data = json.loads(gzip.decompress(path.read_bytes()))
    out = []
    for tax in ("us-gaap", "dei"):
        for tag, info in data.get("facts", {}).get(tax, {}).items():
            if tag not in TAG_TO_CONCEPTS:
                continue
            for unit, vals in info["units"].items():
                if unit not in ("USD", "shares"):
                    continue
                for v in vals:
                    if v.get("form") in Q_FORMS:
                        for concept, prio in TAG_TO_CONCEPTS[tag]:
                            out.append((cik, concept, prio, v.get("start"), v["end"], float(v["val"]), v["accn"], v["filed"]))
    return out


def load_qfacts(con) -> None:
    files = sorted(FACTS_DIR.glob("CIK*.json.gz"))
    cols = ["cik", "concept", "prio", "period_start", "period_end", "value", "accn", "filed"]
    con.execute("""CREATE OR REPLACE TABLE qfacts_raw (cik INTEGER, concept VARCHAR, prio INTEGER, period_start DATE,
                   period_end DATE, value DOUBLE, accn VARCHAR, filed DATE)""")
    t0, buf = time.time(), []
    with Pool(6) as pool:
        for i, rows in enumerate(pool.imap(_rows, files, chunksize=20), 1):
            buf += rows
            if i % 500 == 0 or i == len(files):
                con.register("qbuf", pd.DataFrame(buf, columns=cols))
                con.execute("INSERT INTO qfacts_raw SELECT * FROM qbuf")
                con.unregister("qbuf")
                buf = []
                print(f"  {i:,}/{len(files):,} companies ({time.time() - t0:.0f}s)", flush=True)
    largest = [c for c, s in CONCEPTS.items() if s.get("pick") == "largest"]
    # one value per filing, concept and period: the largest tag for totals, else the highest-priority tag
    con.execute(f"""CREATE OR REPLACE TABLE qfacts AS
        SELECT cik, concept, period_start, period_end, accn, filed,
               CASE WHEN concept IN ({", ".join(f"'{c}'" for c in largest)}) THEN max(value) ELSE arg_min(value, (prio, value)) END AS value
        FROM qfacts_raw GROUP BY cik, concept, period_start, period_end, accn, filed""")
    con.execute("DROP TABLE qfacts_raw")
    print(f"qfacts: {con.execute('SELECT COUNT(*) FROM qfacts').fetchone()[0]:,} rows")


def build_quarterly(con) -> pd.DataFrame:
    flows = ", ".join(f"'{c}'" for c in FLOWS)
    con.execute(f"""
    CREATE OR REPLACE TABLE quarterly AS
    WITH filings AS (            -- each original 10-Q and its quarter end (the latest balance-sheet date in it)
        SELECT cik, accn, MIN(filed) AS filed, MAX(period_end) AS q_end
        FROM qfacts WHERE concept = 'total_assets' GROUP BY cik, accn
        -- one row per quarter: the original 10-Q (an amendment for the same quarter comes later and is dropped)
        QUALIFY ROW_NUMBER() OVER (PARTITION BY cik, MAX(period_end) ORDER BY MIN(filed), accn) = 1
    ),
    firsts AS (                  -- first-filed value for each concept and period
        SELECT cik, concept, period_start, period_end, arg_min(value, (filed, accn)) AS value, MIN(filed) AS first_filed
        FROM qfacts GROUP BY ALL
    ),
    ytd AS (                     -- this filing's year-to-date flows: the longest period ending at the quarter end
        SELECT f.cik, f.accn, q.concept, -- ties broken by start date, so value and start always come from the same fact
               arg_max(q.value, (date_diff('day', q.period_start, q.period_end), q.period_start)) AS ytd,
               max(date_diff('day', q.period_start, q.period_end)) AS days,
               arg_max(q.period_start, (date_diff('day', q.period_start, q.period_end), q.period_start)) AS ytd_start
        FROM filings f JOIN qfacts q ON q.cik = f.cik AND q.accn = f.accn AND q.period_end = f.q_end
        WHERE q.concept IN ({flows}) AND q.period_start IS NOT NULL
          AND date_diff('day', q.period_start, q.period_end) BETWEEN 80 AND 290
        GROUP BY ALL
    ),
    prior_ytd AS (               -- same year-to-date span one year earlier, as first filed, public by now
        SELECT y.cik, y.accn, y.concept, arg_min(p.value, (abs(date_diff('day', p.period_end, f.q_end - INTERVAL 1 YEAR)),
                                 abs(date_diff('day', p.period_start, p.period_end) - y.days), p.period_start, p.value)) AS prior_ytd
        FROM ytd y JOIN filings f USING (cik, accn)
        JOIN firsts p ON p.cik = y.cik AND p.concept = y.concept AND p.first_filed <= f.filed
         AND abs(date_diff('day', p.period_end, f.q_end - INTERVAL 1 YEAR)) <= 10
         AND abs(date_diff('day', p.period_start, p.period_end) - y.days) <= 10
        GROUP BY ALL
    ),
    stocks AS (
        SELECT f.cik, f.accn, q.concept, arg_min(q.value, (q.filed, q.accn)) AS value
        FROM filings f JOIN qfacts q ON q.cik = f.cik AND q.period_end = f.q_end AND q.filed <= f.filed
        WHERE q.period_start IS NULL GROUP BY ALL
    )
    SELECT f.cik, f.accn, f.q_end AS period_end, f.filed AS available_date, y.concept, y.ytd, y.days, y.ytd_start,
           p.prior_ytd, NULL::DOUBLE AS value
    FROM filings f JOIN ytd y USING (cik, accn) LEFT JOIN prior_ytd p USING (cik, accn, concept)
    UNION ALL
    SELECT f.cik, f.accn, f.q_end, f.filed, s.concept, NULL, NULL, NULL, NULL, s.value
    FROM filings f JOIN stocks s USING (cik, accn)
    """)
    long = con.execute("SELECT * FROM quarterly ORDER BY cik, accn, concept").df()
    # last full fiscal year: the annual_first row ending the day before this year-to-date period began
    ann = con.execute(f"SELECT cik, period_end AS fy_end, available_date AS fy_avail, {', '.join(FLOWS)}, public_float FROM annual_first").df()
    ann["fy_end"] = pd.to_datetime(ann["fy_end"])
    fl = long[long["ytd"].notna()].copy()
    fl["ytd_start"] = pd.to_datetime(fl["ytd_start"])
    keys = fl[["cik", "accn", "ytd_start", "available_date"]].drop_duplicates()
    m = keys.merge(ann, on="cik")
    gap = (m["ytd_start"] - m["fy_end"]).dt.days
    m = m.assign(gap=gap)[gap.between(1, 20) & (pd.to_datetime(m["fy_avail"]) <= pd.to_datetime(m["available_date"]))]
    m = m.sort_values(["cik", "accn", "ytd_start", "gap", "fy_end"]).drop_duplicates(["cik", "accn", "ytd_start"])
    fy = m.melt(id_vars=["cik", "accn", "ytd_start"], value_vars=FLOWS, var_name="concept", value_name="fy_value")
    fl = fl.merge(fy, on=["cik", "accn", "ytd_start", "concept"], how="left")
    fl["value"] = fl["ytd"] + fl["fy_value"] - fl["prior_ytd"]          # trailing twelve months
    wide = pd.concat([fl[["cik", "accn", "period_end", "available_date", "concept", "value"]],
                      long[long["ytd"].isna()][["cik", "accn", "period_end", "available_date", "concept", "value"]]])
    wide = wide.pivot_table(index=["cik", "accn", "period_end", "available_date"], columns="concept", values="value", aggfunc="first").reset_index()
    for c in FLOWS + STOCKS:
        if c not in wide:
            wide[c] = float("nan")
    for target, formula in DERIVED.items():
        a, op, b = formula.split()
        calc = wide[a] - wide[b]
        wide[target] = wide[target].fillna(calc)
    # public float: the latest 10-K cover value public before this 10-Q
    pf = ann[["cik", "fy_avail", "fy_end", "public_float"]].dropna().rename(columns={"fy_avail": "available_date"})
    pf = pf.sort_values(["available_date", "fy_end", "cik"]).drop(columns=["fy_end"])
    pf["available_date"] = pd.to_datetime(pf["available_date"])
    wide["available_date"] = pd.to_datetime(wide["available_date"])
    wide = pd.merge_asof(wide.sort_values(["available_date", "cik", "accn"]), pf, on="available_date", by="cik")
    wide = wide[["cik", "accn", "period_end", "available_date"] + FLOWS + STOCKS + ["public_float"]]
    con.register("q_df", wide)
    con.execute("CREATE OR REPLACE TABLE quarterly AS SELECT * FROM q_df ORDER BY cik, period_end, accn")
    con.unregister("q_df")
    ttm = wide["revenue"].notna().mean()
    print(f"quarterly: {len(wide):,} 10-Q rows from {wide['cik'].nunique():,} companies; TTM revenue for {ttm:.0%}, "
          f"TTM net income for {wide['net_income'].notna().mean():.0%}")
    return wide


if __name__ == "__main__":
    with duckdb.connect(str(DB_PATH)) as con:
        load_qfacts(con)
    with duckdb.connect(str(DB_PATH)) as con:
        build_quarterly(con)
