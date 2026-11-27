"""Faultline Composite v1: one model that predicts bankruptcy within 24 months.

Run:  python -m src.model.composite   (after src.scores.compute and src.pipeline.events)

Why: Altman's 1968 cutoffs catch most bankruptcies but flag ~half of all companies.
A model trained on 116k real company-years can weigh the same evidence better.

Rules that keep the test honest:
- Features: only what was public on the row's available_date (scores, ratios, size, and
  warning events filed BEFORE that date).
- Label: did the company file a bankruptcy 8-K within 24 months AFTER that date?
- Walk-forward: to test year Y, train only on rows whose 24-month outcome was already
  known before Y began (available_date + 24 months < Jan 1 of Y). Nothing from the future.
- Compare to Altman on the SAME rows, at the SAME false-alarm rate.
"""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from src.config import DB_PATH, ROOT

OUT_JSON = ROOT / "data" / "processed" / "composite_results.json"
HORIZON = 730
TEST_YEARS = range(2016, 2024)  # outcomes known through 2025

FEATURES = [
    # Altman pieces
    "altman_x1", "altman_x2", "altman_x3", "altman_x4", "altman_x5", "altman_x4_book", "z_score", "z2_score",
    # Piotroski pieces
    "f1_roa_pos", "f2_cfo_pos", "f3_roa_up", "f4_accrual", "f5_lev_down", "f6_cr_up", "f7_no_dilution",
    "f8_gm_up", "f9_turnover_up", "f_score",
    # Beneish pieces
    "dsri", "gmi", "aqi", "sgi", "depi", "sgai", "tata", "lvgi", "m_score",
    # size, profitability, leverage, growth
    "log_assets", "log_revenue", "log_float", "roa", "cfo_ta", "liab_ta", "neg_equity", "rev_growth",
    "cash_burn",
    # filing behaviour and warning events in the 24 months BEFORE the filing
    "days_to_file", "ev_auditor_change", "ev_late_10k", "ev_amended_10k", "ev_non_reliance",
]


def load(con, event: str = "bankruptcy", end: str = "2023-12-31") -> pd.DataFrame:
    """Features + label: did `event` happen within 24 months after the filing?

    event = 'distress_exit' means: a bankruptcy filing within 24 months, OR this was the
    company's last 10-K and it stopped filing without a change of control (no 8-K Item 5.01
    from a year before to three years after), i.e. it went dark rather than being bought.
    """
    in_window = lambda ev: (f"EXISTS (SELECT 1 FROM events e WHERE e.cik = b.cik AND e.event = '{ev}' "
                            f"AND e.filed > b.avail AND e.filed <= b.avail + {HORIZON})")
    if event == "distress_exit":
        label_sql = f"""({in_window('bankruptcy')} OR (
            co.status = 'inactive' AND abs(date_diff('day', co.last_10k::DATE, b.avail)) <= 45
            AND NOT EXISTS (SELECT 1 FROM events e WHERE e.cik = b.cik AND e.event = 'change_in_control'
                            AND e.filed BETWEEN b.avail - 365 AND b.avail + 1095)))"""
    else:
        label_sql = in_window(event)
    return con.execute(f"""
    WITH base AS (
        SELECT s.*, s.available_date::DATE AS avail, a.total_assets, a.revenue, a.public_float,
               a.net_income, a.cfo, a.total_liabilities, a.equity
        FROM scores s JOIN annual_first a USING (cik, period_end)
        WHERE NOT s.is_financial AND s.available_date::DATE BETWEEN DATE '2010-01-01' AND DATE '{end}'
    ),
    prev AS (
        SELECT cik, period_end, revenue AS revenue_prev FROM annual_first
    ),
    bk AS (SELECT cik, MIN(filed) AS first_bk FROM events WHERE event = 'bankruptcy' GROUP BY cik)
    SELECT b.*,
        ln(greatest(b.total_assets, 1)) AS log_assets,
        ln(greatest(b.revenue, 1)) AS log_revenue,
        ln(greatest(b.public_float, 1)) AS log_float,
        b.net_income / nullif(b.total_assets, 0) AS roa,
        b.cfo / nullif(b.total_assets, 0) AS cfo_ta,
        b.total_liabilities / nullif(b.total_assets, 0) AS liab_ta,
        (b.equity < 0)::INT AS neg_equity,
        b.revenue / nullif(p.revenue_prev, 0) - 1 AS rev_growth,
        least(b.cfo, 0) / nullif(b.total_assets, 0) AS cash_burn,
        date_diff('day', b.period_end::DATE, b.avail) AS days_to_file,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'auditor_change' AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_auditor_change,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'late_10k'       AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_late_10k,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'amended_10k'    AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_amended_10k,
        (SELECT COUNT(*) FROM events e WHERE e.cik = b.cik AND e.event = 'non_reliance'   AND e.filed BETWEEN b.avail - {HORIZON} AND b.avail - 1) AS ev_non_reliance,
        -- label: the event happens within 24 months AFTER the filing (not before it)
        {label_sql} AS label,
        (bk.first_bk <= b.avail) IS TRUE AS already_bankrupt
    FROM base b
    LEFT JOIN prev p ON p.cik = b.cik AND date_diff('day', p.period_end, b.period_end) BETWEEN 350 AND 380
    LEFT JOIN bk ON bk.cik = b.cik
    JOIN companies co ON co.cik = b.cik
    """).df()


def walk_forward(df: pd.DataFrame, features: list[str] = FEATURES, verbose: bool = True, years=TEST_YEARS) -> pd.DataFrame:
    df = df[~df["already_bankrupt"]].copy()  # can't "predict" a bankruptcy that already happened
    df["year"] = pd.to_datetime(df["avail"]).dt.year
    df["composite"] = np.nan
    for y in years:
        train = df[pd.to_datetime(df["avail"]) + pd.Timedelta(days=HORIZON) < pd.Timestamp(f"{y}-01-01")]
        test = df["year"] == y
        model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                               l2_regularization=1.0, random_state=0)
        model.fit(train[features].astype(float), train["label"].astype(int))
        df.loc[test, "composite"] = model.predict_proba(df.loc[test, features].astype(float))[:, 1]
        if verbose: print(f"  test {y}: trained on {len(train):,} rows ({int(train['label'].sum())} bankruptcies), "
              f"scored {int(test.sum()):,}")
    return df[df["year"].isin(years)]


def compare(oos: pd.DataFrame) -> dict:
    """Same rows for both: those with an Altman Z. Match Faultline's alarm rate to Altman's."""
    rows = oos[oos["z_score"].notna()].copy()
    y = rows["label"].astype(int)
    altman_flag = rows["z_zone"] == "distress"
    alarm = altman_flag.mean()
    cut = rows["composite"].quantile(1 - alarm)            # flag the same SHARE of companies
    fl_same_alarm = rows["composite"] >= cut
    # and: how few alarms does Faultline need to catch as many bankruptcies as Altman?
    altman_hit = altman_flag[y == 1].mean()
    pos_scores = np.sort(rows.loc[y == 1, "composite"].to_numpy())[::-1]
    cut2 = pos_scores[int(np.ceil(altman_hit * len(pos_scores))) - 1]
    fl_same_hits = rows["composite"] >= cut2
    res = {
        "test_years": f"{min(TEST_YEARS)}-{max(TEST_YEARS)}",
        "company_years": int(len(rows)), "bankruptcies": int(y.sum()),
        "altman": {"alarm_rate": float(alarm), "hit_rate": float(altman_hit),
                   "precision": float(y[altman_flag].mean()), "auc": float(roc_auc_score(y, -rows["z_score"]))},
        "faultline_same_alarm_rate": {"alarm_rate": float(fl_same_alarm.mean()), "hit_rate": float(fl_same_alarm[y == 1].mean()),
                                      "precision": float(y[fl_same_alarm].mean())},
        "faultline_same_hit_rate": {"alarm_rate": float(fl_same_hits.mean()), "hit_rate": float(fl_same_hits[y == 1].mean()),
                                    "precision": float(y[fl_same_hits].mean())},
        "faultline_auc": float(roc_auc_score(y, rows["composite"])),
        "z2_auc": float(roc_auc_score(y[rows["z2_score"].notna()], -rows.loc[rows["z2_score"].notna(), "z2_score"])),
        "all_rows": {"company_years": int(len(oos)), "bankruptcies": int(oos["label"].sum()),
                     "faultline_auc": float(roc_auc_score(oos["label"].astype(int), oos["composite"]))},
    }
    return res


def main():
    with duckdb.connect(str(DB_PATH)) as con:
        df = load(con)
        print(f"{len(df):,} company-years, {int(df['label'].sum())} followed by bankruptcy within 24 months")
        oos = walk_forward(df)
        keep = oos[["cik", "period_end", "available_date", "composite"]]
        con.register("composite_df", keep)
        con.execute("CREATE OR REPLACE TABLE composite AS SELECT * FROM composite_df")
        con.unregister("composite_df")
    res = compare(oos)
    OUT_JSON.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
