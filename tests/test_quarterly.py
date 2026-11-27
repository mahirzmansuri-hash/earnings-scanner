"""Trailing twelve months from a 10-Q, checked against Apple's real 10-Q for the quarter ended June 29, 2024 ($ millions)."""
import duckdb
import pandas as pd

from src.pipeline.quarterly import FLOWS, build_quarterly

ACCN, FILED = "0000320193-24-000081", "2024-08-02"


def test_apple_ttm_revenue_and_net_income():
    con = duckdb.connect()
    q = pd.DataFrame([
        # cik, concept, start, end, value, accn, filed
        (320193, "revenue", "2023-10-01", "2024-06-29", 296105, ACCN, FILED),      # 9 months, this year
        (320193, "revenue", "2024-03-31", "2024-06-29", 85777, ACCN, FILED),       # 3 months (ignored: not the longest)
        (320193, "revenue", "2022-09-25", "2023-07-01", 293787, "prior", "2023-08-04"),  # 9 months, last year
        (320193, "net_income", "2023-10-01", "2024-06-29", 79000, ACCN, FILED),
        (320193, "net_income", "2022-09-25", "2023-07-01", 74039, "prior", "2023-08-04"),
        (320193, "total_assets", None, "2024-06-29", 331612, ACCN, FILED),
        (320193, "total_assets", None, "2023-07-01", 335038, "prior", "2023-08-04"),
    ], columns=["cik", "concept", "period_start", "period_end", "value", "accn", "filed"])
    for c in ["period_start", "period_end", "filed"]:
        q[c] = pd.to_datetime(q[c])
    con.register("q_in", q)
    con.execute("CREATE TABLE qfacts AS SELECT * FROM q_in")
    ann = pd.DataFrame([{"cik": 320193, "period_end": pd.Timestamp("2023-09-30"), "available_date": pd.Timestamp("2023-11-03"),
                         **{c: None for c in FLOWS}, "revenue": 383285.0, "net_income": 96995.0, "public_float": 2.6e12}])
    con.register("a_in", ann)
    con.execute("CREATE TABLE annual_first AS SELECT * FROM a_in")
    out = build_quarterly(con)
    row = out[out["accn"] == ACCN].iloc[0]
    assert row["revenue"] == 296105 + 383285 - 293787 == 385603
    assert row["net_income"] == 101956
    assert row["total_assets"] == 331612
    assert row["public_float"] == 2.6e12
