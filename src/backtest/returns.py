"""Stage 2: did flagged companies' stocks do worse? A free, survivorship-free approximation.

Run:  python -m src.backtest.returns   (after src.model.live)

No free source has full daily prices for dead companies, so this uses the market value of
outside shareholders' stock that every 10-K reports on its cover page (public float, valued
on the last day of the company's second fiscal quarter).

For a score published in the year-t 10-K (available_date A_t):
  start value  = public float reported in the year t+1 10-K (valued ~3-6 months AFTER A_t)
  end value    = public float reported in the year t+2 10-K (about one year later)
  return       = end / start - 1
If the company didn't make it to the t+2 report:
  bankruptcy filing within 3 years after A_t  -> -100% (stock wiped out)
  stopped filing, no change of control        -> -50% (assumption; -100% and 0% also tested)
  change of control (buyout)                  -> left out (sale price unknown)
Limits: public float also grows when a company issues shares, which flatters companies
that raise money (often the distressed ones), so underperformance is if anything understated.
Only companies with at least $10M of public float when the score came out (tradable). Medians and the
share that lost half or more are the main measures; means cap single returns at +300% because a few
reported values jump 10x or more (reverse mergers, IPOs, data errors).
"""
import json

import duckdb
import numpy as np
import pandas as pd

from src.config import DB_PATH, ROOT

OUT_JSON = ROOT / "data" / "processed" / "returns_results.json"


def load(con) -> pd.DataFrame:
    return con.execute("""
    WITH base AS (
        SELECT r.cik, r.period_end, r.available_date::DATE AS avail, r.bankruptcy_pctile, s.z_zone, s.is_financial, a.public_float AS f0
        FROM risk r JOIN scores s USING (cik, period_end) JOIN annual_first a USING (cik, period_end)
        WHERE r.bankruptcy_pctile IS NOT NULL AND NOT s.is_financial
          AND year(r.available_date) BETWEEN 2016 AND 2022
          AND a.public_float >= 1e7   -- investable: at least $10M of stock held by outsiders when the score came out
    ),
    fl AS (SELECT cik, period_end, public_float FROM annual_first WHERE public_float > 0)
    SELECT b.*,
        (SELECT f.public_float FROM fl f WHERE f.cik = b.cik AND date_diff('day', b.period_end, f.period_end) BETWEEN 350 AND 380 LIMIT 1) AS f1,
        (SELECT f.public_float FROM fl f WHERE f.cik = b.cik AND date_diff('day', b.period_end, f.period_end) BETWEEN 715 AND 745 LIMIT 1) AS f2,
        EXISTS (SELECT 1 FROM events e WHERE e.cik = b.cik AND e.event = 'bankruptcy' AND e.filed > b.avail AND e.filed <= b.avail + 1095) AS bankrupt,
        EXISTS (SELECT 1 FROM events e WHERE e.cik = b.cik AND e.event = 'change_in_control' AND e.filed BETWEEN b.avail - 365 AND b.avail + 1095) AS bought,
        c.status = 'inactive' AND c.last_10k::DATE <= b.avail + 400 AS stopped
    FROM base b JOIN companies c USING (cik)
    ORDER BY b.cik, b.period_end
    """).df()


def outcome(df: pd.DataFrame, dark_return: float) -> pd.Series:
    r = pd.Series(np.nan, index=df.index)
    both = df["f1"].notna() & df["f2"].notna()
    r[both] = df.loc[both, "f2"] / df.loc[both, "f1"] - 1
    r[~both & df["bankrupt"]] = -1.0
    r[~both & ~df["bankrupt"] & df["stopped"] & ~df["bought"]] = dark_return
    return r


def summarize(r: pd.Series) -> dict:
    r = r.dropna()
    return {"n": int(len(r)), "median": float(r.median()), "mean_capped": float(r.clip(upper=3.0).mean()),
            "share_lost_half": float((r <= -0.5).mean()), "share_wiped_out": float((r <= -0.95).mean())}


def groups(df: pd.DataFrame, r: pd.Series) -> dict:
    p = df["bankruptcy_pctile"]
    g = {
        "faultline_riskiest_10pct": r[p >= 0.9],
        "faultline_10_to_20pct": r[(p >= 0.8) & (p < 0.9)],
        "faultline_safest_50pct": r[p < 0.5],
        "altman_distress": r[df["z_zone"] == "distress"],
        "altman_safe": r[df["z_zone"] == "safe"],
        "all": r,
    }
    return {k: summarize(v) for k, v in g.items()}


def main():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = load(con)
    both = df["f1"].notna() & df["f2"].notna()
    cov = {"company_years": int(len(df)), "market_value_both_years": int(both.sum()),
           "bankrupt_minus_100": int((~both & df["bankrupt"]).sum()),
           "stopped_filing_assumed": int((~both & ~df["bankrupt"] & df["stopped"] & ~df["bought"]).sum()),
           "left_out": int(outcome(df, -0.5).isna().sum())}
    res = {"coverage": cov, "main_dark_minus_50": groups(df, outcome(df, -0.5)),
           "dark_minus_100": groups(df, outcome(df, -1.0)), "dark_zero": groups(df, outcome(df, 0.0))}
    r = outcome(df, -0.5)
    df["year"] = pd.to_datetime(df["avail"]).dt.year
    res["by_year_median"] = {int(y): {"riskiest_10pct": float(r[g.index][g["bankruptcy_pctile"] >= 0.9].median()),
                                      "safest_50pct": float(r[g.index][g["bankruptcy_pctile"] < 0.5].median())}
                             for y, g in df.groupby("year")}
    OUT_JSON.write_text(json.dumps(res, indent=2))
    print("coverage:", cov)
    for name in ["main_dark_minus_50", "dark_minus_100", "dark_zero"]:
        print(f"\n{name}")
        for k, v in res[name].items():
            print(f"  {k:26} n={v['n']:6,}  median {v['median']*100:6.1f}%  mean(cap) {v['mean_capped']*100:6.1f}%  lost half+ {v['share_lost_half']*100:5.1f}%  wiped out {v['share_wiped_out']*100:4.1f}%")
    print("\nby year, median (riskiest 10% vs safest 50%):")
    for y, v in res["by_year_median"].items():
        print(f"  {y}: {v['riskiest_10pct']*100:6.1f}% vs {v['safest_50pct']*100:6.1f}%")


if __name__ == "__main__":
    main()
