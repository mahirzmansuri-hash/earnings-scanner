"""Risk scores for the website: bankruptcy and restatement risk for every company-year, 2016-now.

Run:  python -m src.model.live   (after src.scores.compute and src.pipeline.events)

Every score is out-of-sample: for filings made in year Y, the model is trained only on rows
whose 24-month outcome was known before Jan 1 of Y. Same rule as the published test, just
extended to the newest filings. Also stores each row's percentile among companies that
filed in the same year ("riskier than 97% of companies").

Calibration: raw model scores rank well but their middle values read too low. For filing year Y,
an isotonic map from raw score to observed rate is fitted on EARLIER years' out-of-sample scores
whose outcomes were known before Y, then applied to year Y. Rankings don't change; the shown
percentages get closer to how often companies really failed. 2016 (no earlier years) stays raw.
"""
import duckdb
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from src.config import DB_PATH
from src.model.composite import HORIZON, load, walk_forward
from src.model.explain import explain


def calibrate(wf: pd.DataFrame) -> pd.Series:
    out = wf["composite"].copy()
    avail = pd.to_datetime(wf["avail"])
    for y in sorted(wf["year"].unique()):
        known = (wf["year"] < y) & (avail + pd.Timedelta(days=HORIZON) < pd.Timestamp(f"{y}-01-01"))
        if known.sum() < 2000 or wf.loc[known, "label"].sum() < 20:
            continue
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
        iso.fit(wf.loc[known, "composite"], wf.loc[known, "label"].astype(float))
        m = wf["year"] == y
        out[m] = iso.predict(wf.loc[m, "composite"])
    return out


def main():
    with duckdb.connect(str(DB_PATH)) as con:
        as_of = pd.Timestamp(con.execute("SELECT MAX(filed) FROM facts").fetchone()[0])
        years = range(2016, as_of.year + 1)
        out = None
        for event, col in [("bankruptcy", "bankruptcy_risk"), ("non_reliance", "restatement_risk")]:
            df = load(con, event=event, end=str(as_of.date()))
            if event != "bankruptcy":
                df["already_bankrupt"] = False
            models = {}
            wf = walk_forward(df, years=years, verbose=False, models=models)
            if event == "bankruptcy":
                # why-this-score breakdown for each company's latest filing (shown on its page)
                latest = wf.sort_values("avail").groupby("cik").tail(1)
                why = explain(latest, models)
                con.register("why_df", why)
                con.execute("CREATE OR REPLACE TABLE risk_why AS SELECT * FROM why_df")
                con.unregister("why_df")
                print(f"  explained {len(latest):,} latest filings ({len(why):,} group effects)")
            wf["calibrated"] = calibrate(wf)
            part = wf[["cik", "period_end", "available_date", "calibrated", "composite"]]
            part = part.rename(columns={"calibrated": col, "composite": col + "_raw"})
            out = part if out is None else out.merge(part.drop(columns=["available_date"]), on=["cik", "period_end"], how="outer")
            print(f"  {event}: scored {len(part):,} company-years")
        out["year"] = pd.to_datetime(out["available_date"]).dt.year
        for col in ["bankruptcy_risk", "restatement_risk"]:
            # rank by the raw score: calibration groups scores into steps, raw keeps the fine order
            out[col.replace("_risk", "_pctile")] = out.groupby("year")[col + "_raw"].rank(pct=True)
        con.register("risk_df", out.drop(columns=["year"]))
        con.execute("CREATE OR REPLACE TABLE risk AS SELECT * FROM risk_df")
        con.unregister("risk_df")
        print(f"risk table: {len(out):,} company-years (filed 2016-{as_of.year}), data as of {as_of.date()}")


if __name__ == "__main__":
    main()
