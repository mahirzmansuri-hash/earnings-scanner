"""Risk scores for the website: bankruptcy and restatement risk for every company-year, 2016-now.

Run:  python -m src.model.live   (after src.scores.compute and src.pipeline.events)

Every score is out-of-sample: for filings made in year Y, the model is trained only on rows
whose 24-month outcome was known before Jan 1 of Y. Same rule as the published test, just
extended to the newest filings. Also stores each row's percentile among companies that
filed in the same year ("riskier than 97% of companies").
"""
import duckdb
import pandas as pd

from src.config import DB_PATH
from src.model.composite import load, walk_forward


def main():
    with duckdb.connect(str(DB_PATH)) as con:
        as_of = pd.Timestamp(con.execute("SELECT MAX(filed) FROM facts").fetchone()[0])
        years = range(2016, as_of.year + 1)
        out = None
        for event, col in [("bankruptcy", "bankruptcy_risk"), ("non_reliance", "restatement_risk")]:
            df = load(con, event=event, end=str(as_of.date()))
            if event != "bankruptcy":
                df["already_bankrupt"] = False
            part = walk_forward(df, years=years, verbose=False)[["cik", "period_end", "available_date", "composite"]]
            part = part.rename(columns={"composite": col})
            out = part if out is None else out.merge(part.drop(columns=["available_date"]), on=["cik", "period_end"], how="outer")
            print(f"  {event}: scored {len(part):,} company-years")
        out["year"] = pd.to_datetime(out["available_date"]).dt.year
        for col in ["bankruptcy_risk", "restatement_risk"]:
            out[col.replace("_risk", "_pctile")] = out.groupby("year")[col].rank(pct=True)
        con.register("risk_df", out.drop(columns=["year"]))
        con.execute("CREATE OR REPLACE TABLE risk AS SELECT * FROM risk_df")
        con.unregister("risk_df")
        print(f"risk table: {len(out):,} company-years (filed 2016-{as_of.year}), data as of {as_of.date()}")


if __name__ == "__main__":
    main()
