"""Compute every score for every company-year and save them as the 'scores' table.

Run:  python -m src.scores.compute   (after src.pipeline.annual)

Point-in-time: each row uses first-filed values for year t and year t-1, and is stamped
with available_date = when the year-t 10-K became public. A backtest may only use a score
on or after that date.
"""
import duckdb
import pandas as pd

from src.config import DB_PATH
from src.pipeline.tag_map import CONCEPTS
from src.scores.altman import altman_ratios, altman_z, altman_z2, altman_z2_zone, altman_zone
from src.scores.beneish import beneish
from src.scores.piotroski import f_band, piotroski


def load_inputs(con) -> pd.DataFrame:
    """This year + last year side by side (prior year = fiscal year ending 350-380 days earlier)."""
    prev_cols = ", ".join(f"p.{c} AS {c}_prev" for c in CONCEPTS)
    return con.execute(f"""
        SELECT a.*, c.is_financial, c.sic, {prev_cols}
        FROM annual_first a
        JOIN companies c USING (cik)
        LEFT JOIN annual_first p
          ON p.cik = a.cik AND date_diff('day', p.period_end, a.period_end) BETWEEN 350 AND 380
        QUALIFY ROW_NUMBER() OVER (PARTITION BY a.cik, a.period_end ORDER BY p.period_end DESC) = 1
    """).df()


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["cik", "period_end", "available_date", "is_financial", "sic"]].copy()
    args = dict(current_assets=df["current_assets"], current_liabilities=df["current_liabilities"],
                total_assets=df["total_assets"], retained_earnings=df["retained_earnings"],
                ebit=df["operating_income"], total_liabilities=df["total_liabilities"])
    ratios = altman_ratios(**args, market_value_equity=df["public_float"], sales=df["revenue"], book_equity=df["equity"])
    for k, v in ratios.items():
        out[f"altman_{k}"] = v
    out["z_score"] = altman_z(**args, market_value_equity=df["public_float"], sales=df["revenue"])
    out["z_zone"] = altman_zone(out["z_score"])
    out["z2_score"] = altman_z2(**args, book_equity=df["equity"])
    out["z2_zone"] = altman_z2_zone(out["z2_score"])
    out = out.join(piotroski(df))
    out["f_band"] = f_band(out["f_score"])
    out = out.join(beneish(df))
    return out


def build_scores(con) -> pd.DataFrame:
    scores = compute_scores(load_inputs(con))
    # register under a different name: "SELECT * FROM scores" would read the OLD DuckDB table, not this DataFrame
    con.register("scores_df", scores)
    con.execute("CREATE OR REPLACE TABLE scores AS SELECT * FROM scores_df")
    con.unregister("scores_df")
    nf = scores[~scores["is_financial"] & (scores["period_end"] >= pd.Timestamp("2012-01-01"))]
    print(f"scores: {len(scores):,} company-years ({len(nf):,} non-financial since 2012)")
    for col in ["z_score", "z2_score", "f_score", "m_score"]:
        print(f"  {col:9} available for {nf[col].notna().mean():.0%} of non-financial company-years")
    return scores


if __name__ == "__main__":
    with duckdb.connect(str(DB_PATH)) as con:
        build_scores(con)
