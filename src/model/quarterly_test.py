"""Research question 7: do 10-Qs warn earlier or better than waiting for the next 10-K?

Run:  python -m src.model.quarterly_test     (after src.pipeline.quarterly and src.model.live)

At every 10-Q filing date we compare two scores, both trained only on outcomes known before that year:
  A. "Last 10-K"  : the annual model's score from the latest 10-K filed before that date (what the site shows today)
  B. "Fresh 10-Q" : the same kind of model, but fed trailing-twelve-month numbers and the balance sheet from the 10-Q
Label for both: a bankruptcy filing within 24 months after the 10-Q date. Same rows, same label.

Also: lead time. For each company that went bankrupt, when did each approach first place it in the riskiest
10% of filers that year? Earlier warnings matter more than slightly better rankings.
"""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.config import DB_PATH, ROOT
from src.model.composite import FEATURES, HORIZON, walk_forward
from src.scores.compute import compute_scores
from src.pipeline.tag_map import CONCEPTS

OUT_JSON = ROOT / "data" / "processed" / "quarterly_results.json"
YEARS = range(2016, 2024)


def quarterly_features(con, end: str = "2023-12-31") -> pd.DataFrame:
    prev = ", ".join(f"p.{c} AS {c}_prev" for c in CONCEPTS)
    q = con.execute(f"""
        SELECT q.*, c.is_financial, c.sic, {prev}
        FROM quarterly q JOIN companies c USING (cik)
        LEFT JOIN quarterly p ON p.cik = q.cik AND date_diff('day', p.period_end, q.period_end) BETWEEN 350 AND 380
             AND p.available_date < q.available_date
        WHERE NOT c.is_financial
        QUALIFY ROW_NUMBER() OVER (PARTITION BY q.cik, q.accn ORDER BY p.period_end DESC NULLS LAST) = 1
    """).df()
    s = compute_scores(q)
    s["accn"] = q["accn"].to_numpy()
    q = q.merge(s.drop(columns=["available_date", "is_financial", "sic"]), on=["cik", "period_end", "accn"])
    con.register("qs_df", q)
    return con.execute(f"""
    WITH b AS (SELECT *, available_date::DATE AS avail FROM qs_df WHERE available_date::DATE BETWEEN DATE '2010-01-01' AND DATE '{end}'),
    bk AS (SELECT cik, MIN(filed) AS first_bk FROM events WHERE event = 'bankruptcy' GROUP BY cik),
    tx AS (SELECT t.*, a.available_date::DATE AS tx_avail FROM text_signals t JOIN annual_first a USING (cik, period_end))
    SELECT b.*,
        ln(greatest(b.total_assets, 1)) AS log_assets, ln(greatest(b.revenue, 1)) AS log_revenue,
        ln(greatest(b.public_float, 1)) AS log_float, b.net_income / nullif(b.total_assets, 0) AS roa,
        b.cfo / nullif(b.total_assets, 0) AS cfo_ta, b.total_liabilities / nullif(b.total_assets, 0) AS liab_ta,
        (b.equity < 0)::INT AS neg_equity, b.revenue / nullif(b.revenue_prev, 0) - 1 AS rev_growth,
        least(b.cfo, 0) / nullif(b.total_assets, 0) AS cash_burn,
        date_diff('day', b.period_end::DATE, b.avail) AS days_to_file,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'auditor_change' AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_auditor_change,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'late_10k'       AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_late_10k,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'amended_10k'    AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_amended_10k,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'non_reliance'   AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_non_reliance,
        -- 10-K wording: from the latest 10-K public before this 10-Q
        (SELECT arg_max(tx_gc_doubt, (tx_avail, period_end)) FROM tx WHERE tx.cik = b.cik AND tx.tx_avail < b.avail) AS tx_gc_doubt,
        (SELECT arg_max(tx_gc_recurring, (tx_avail, period_end)) FROM tx WHERE tx.cik = b.cik AND tx.tx_avail < b.avail) AS tx_gc_recurring,
        (SELECT arg_max(tx_mw_identified, (tx_avail, period_end)) FROM tx WHERE tx.cik = b.cik AND tx.tx_avail < b.avail) AS tx_mw_identified,
        (SELECT arg_max(tx_icfr_not_effective, (tx_avail, period_end)) FROM tx WHERE tx.cik = b.cik AND tx.tx_avail < b.avail) AS tx_icfr_not_effective,
        (SELECT arg_max(tx_restated, (tx_avail, period_end)) FROM tx WHERE tx.cik = b.cik AND tx.tx_avail < b.avail) AS tx_restated,
        EXISTS (SELECT 1 FROM events e WHERE e.cik = b.cik AND e.event = 'bankruptcy' AND e.filed > b.avail AND e.filed <= b.avail + {HORIZON}) AS label,
        (bk.first_bk <= b.avail) IS TRUE AS already_bankrupt, bk.first_bk
    FROM b LEFT JOIN bk USING (cik)
    ORDER BY b.cik, b.period_end, b.accn   -- fixed order: identical results on every run
    """).df()


def attach_last_10k(con, q: pd.DataFrame) -> pd.DataFrame:
    """Annual-model score (raw) of the latest 10-K filed before each 10-Q."""
    r = con.execute("SELECT cik, available_date::DATE AS k_avail, bankruptcy_risk_raw FROM risk WHERE bankruptcy_risk_raw IS NOT NULL").df()
    r["k_avail"] = pd.to_datetime(r["k_avail"])
    q = q.copy()
    q["avail_ts"] = pd.to_datetime(q["avail"])
    out = pd.merge_asof(q.sort_values("avail_ts"), r.sort_values("k_avail"), left_on="avail_ts", right_on="k_avail",
                        by="cik", allow_exact_matches=False)
    out["k_age_days"] = (out["avail_ts"] - out["k_avail"]).dt.days
    return out[out["k_age_days"] <= 400]          # a 10-K from the last ~13 months, as on the site


def top_share(y, s, q=0.10):
    order = np.argsort(-np.asarray(s))
    k = int(len(order) * q)
    return float(np.asarray(y)[order[:k]].sum() / np.sum(y))


def lead_times(rows: pd.DataFrame) -> dict:
    """Days before the bankruptcy filing when each score first put the company in that year's riskiest 10%."""
    rows = rows.copy()
    for col in ["fresh_10q", "last_10k"]:
        rows[col + "_top"] = rows[col] >= rows.groupby("year")[col].transform(lambda s: s.quantile(0.9))
    bk = rows[rows["label"]]
    out = {}
    for col in ["fresh_10q", "last_10k"]:
        first = bk[bk[col + "_top"]].groupby("cik").agg(first_warn=("avail_ts", "min"), bk=("first_bk", "first"))
        lead = (pd.to_datetime(first["bk"]) - first["first_warn"]).dt.days
        out[col] = {"companies_warned": int(len(first)), "median_days_before_bankruptcy": float(lead.median())}
    out["companies_bankrupt"] = int(bk["cik"].nunique())
    return out


def live():
    """Site scores: every 10-Q since 2016 scored out of sample, calibrated like the annual model (src/model/live.py).
    Table risk_q keeps each company's latest 10-Q, with its percentile among 10-Qs filed that year."""
    from src.model.live import calibrate
    with duckdb.connect(str(DB_PATH)) as con:
        as_of = pd.Timestamp(con.execute("SELECT MAX(available_date) FROM quarterly").fetchone()[0])
        q = quarterly_features(con, end=str(as_of.date()))
        wf = walk_forward(q, years=range(2016, as_of.year + 1), verbose=False)
        wf["q_risk"] = calibrate(wf)
        wf["q_pctile"] = wf.groupby("year")["composite"].rank(pct=True)
        latest = wf.sort_values("avail").groupby("cik").tail(1)
        out = latest[["cik", "accn", "period_end", "available_date", "q_risk", "composite", "q_pctile"]].rename(columns={"composite": "q_risk_raw"})
        con.register("rq_df", out)
        con.execute("CREATE OR REPLACE TABLE risk_q AS SELECT * FROM rq_df")
        con.unregister("rq_df")
    print(f"risk_q: latest 10-Q scored for {len(out):,} companies (10-Qs to {as_of.date()})")


def main():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        q = quarterly_features(con)
        print(f"{len(q):,} 10-Q rows with features, {int(q['label'].sum())} followed by bankruptcy within 24 months")
        wf = walk_forward(q, years=YEARS, verbose=False).rename(columns={"composite": "fresh_10q"})
        rows = attach_last_10k(con, wf).rename(columns={"bankruptcy_risk_raw": "last_10k"})
    rows = rows[rows["fresh_10q"].notna() & rows["last_10k"].notna()]
    rows["year"] = rows["avail_ts"].dt.year
    y = rows["label"].astype(int)
    combo = (rows.groupby("year")["fresh_10q"].rank(pct=True) + rows.groupby("year")["last_10k"].rank(pct=True)) / 2
    res = {"test_years": f"{min(YEARS)}-{max(YEARS)}", "rows": int(len(rows)), "bankruptcies": int(y.sum()),
           "companies": int(rows["cik"].nunique()),
           "last_10k": {"auc": float(roc_auc_score(y, rows["last_10k"])), "top10": top_share(y, rows["last_10k"])},
           "fresh_10q": {"auc": float(roc_auc_score(y, rows["fresh_10q"])), "top10": top_share(y, rows["fresh_10q"])},
           "average_of_both": {"auc": float(roc_auc_score(y, combo)), "top10": top_share(y, combo)},
           "by_10k_age": {}, "lead_time": lead_times(rows)}
    for name, lo, hi in [("10-K under 4 months old", 0, 120), ("4-8 months", 121, 240), ("over 8 months", 241, 400)]:
        r = rows[rows["k_age_days"].between(lo, hi)]
        yy = r["label"].astype(int)
        res["by_10k_age"][name] = {"rows": int(len(r)), "bankruptcies": int(yy.sum()),
                                   "last_10k_auc": float(roc_auc_score(yy, r["last_10k"])),
                                   "fresh_10q_auc": float(roc_auc_score(yy, r["fresh_10q"]))}
    OUT_JSON.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
    live()
