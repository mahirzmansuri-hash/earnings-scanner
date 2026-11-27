"""Extra model inputs (v2): two classic academic benchmarks, multi-year trends, and industry context.

Everything here uses only data public on the row's available_date:
- prior years' values come from those years' own first-filed 10-Ks (annual_first)
- industry medians and industry bankruptcy rates use only the PREVIOUS calendar year

Ohlson O-score (Ohlson 1980, model 1):
  O = -1.32 - 0.407*log(TA) + 6.03*TL/TA - 1.43*WC/TA + 0.0757*CL/CA - 2.37*NI/TA
      - 1.83*FFO/TL + 0.285*INTWO - 1.72*OENEG - 0.521*CHIN
  TA in $ millions. Ohlson divided TA by a price index; we skip that (it is the same for every
  company in a year, so it barely changes the ranking). FFO (funds from operations) is
  approximated as net income + depreciation. Higher O = riskier.
Zmijewski score (Zmijewski 1984):
  X = -4.336 - 4.513*NI/TA + 5.679*TL/TA + 0.004*CA/CL.   Higher = riskier.
"""
import numpy as np
import pandas as pd

LAG_COLS = ["net_income", "total_assets", "total_liabilities", "cfo", "revenue", "current_assets"]

TREND_FEATURES = ["roa_chg", "liab_ta_chg", "chin", "intwo", "cfo_neg_two", "rev_growth_2y", "z_chg", "assets_growth"]
INDUSTRY_FEATURES = ["roa_vs_ind", "liab_ta_vs_ind", "z_vs_ind", "ind_bk_rate"]
BENCH_FEATURES = ["o_score", "zmijewski"]
NEW_FEATURES = BENCH_FEATURES + TREND_FEATURES + INDUSTRY_FEATURES


def _div(a, b):
    b = b.where(b != 0)
    return a / b


def _lag(df: pd.DataFrame, a: pd.DataFrame, k: int) -> pd.DataFrame:
    """Attach the fiscal year ending ~k years earlier (closest match), columns suffixed _l{k}."""
    lagged = a.rename(columns={c: f"{c}_l{k}" for c in a.columns if c != "cik"})
    m = df[["cik", "period_end"]].reset_index().merge(lagged, on="cik")
    gap = (m["period_end"] - m[f"period_end_l{k}"]).dt.days
    m = m[gap.between(365 * k - 15, 365 * k + 15)]
    m = m.assign(_off=(gap - 365 * k).abs()).sort_values("_off").drop_duplicates("index")
    return m.set_index("index").drop(columns=["cik", "period_end", "_off", f"period_end_l{k}"])


def add_features(df: pd.DataFrame, con) -> pd.DataFrame:
    df = df.copy()
    df["period_end"] = pd.to_datetime(df["period_end"])
    a = con.execute(f"""SELECT a.cik, a.period_end, {', '.join('a.' + c for c in LAG_COLS)}, s.z_score
                        FROM annual_first a LEFT JOIN scores s USING (cik, period_end)""").df()
    a["period_end"] = pd.to_datetime(a["period_end"])
    df = df.join(_lag(df, a, 1)).join(_lag(df, a, 2)[["net_income_l2", "cfo_l2", "revenue_l2"]])

    ta, tl, ni = df["total_assets"], df["total_liabilities"], df["net_income"]
    roa, roa1 = _div(ni, ta), _div(df["net_income_l1"], df["total_assets_l1"])
    liab_ta = _div(tl, ta)

    # --- trends
    df["roa_chg"] = roa - roa1
    df["liab_ta_chg"] = liab_ta - _div(df["total_liabilities_l1"], df["total_assets_l1"])
    df["chin"] = _div(ni - df["net_income_l1"], ni.abs() + df["net_income_l1"].abs())
    df["intwo"] = ((ni < 0) & (df["net_income_l1"] < 0)).astype(float).where(df["net_income_l1"].notna())
    df["cfo_neg_two"] = ((df["cfo"] < 0) & (df["cfo_l1"] < 0)).astype(float).where(df["cfo_l1"].notna())
    df["rev_growth_2y"] = _div(df["revenue"], df["revenue_l2"]) - 1
    df["z_chg"] = df["z_score"] - df["z_score_l1"]
    df["assets_growth"] = _div(ta, df["total_assets_l1"]) - 1

    # --- classic benchmarks
    wc = df["current_assets"] - df["current_liabilities"]
    ffo = ni + df["depreciation"].fillna(0)
    df["o_score"] = (-1.32 - 0.407 * np.log(ta.where(ta > 0) / 1e6) + 6.03 * liab_ta - 1.43 * _div(wc, ta)
                     + 0.0757 * _div(df["current_liabilities"], df["current_assets"]) - 2.37 * roa
                     - 1.83 * _div(ffo, tl) + 0.285 * df["intwo"].fillna(0) - 1.72 * (tl > ta).astype(float)
                     - 0.521 * df["chin"].fillna(0))
    df["zmijewski"] = (-4.336 - 4.513 * roa + 5.679 * liab_ta
                       + 0.004 * _div(df["current_assets"], df["current_liabilities"]))

    # --- industry context (2-digit SIC), from the PREVIOUS calendar year only
    df["sic2"] = (pd.to_numeric(df["sic"], errors="coerce") // 100).astype("Int64")
    df["year"] = pd.to_datetime(df["avail"]).dt.year
    tmp = df.assign(_roa=roa, _lta=liab_ta)
    med = (tmp.groupby(["sic2", "year"])[["_roa", "_lta", "z_score"]].median()
           .rename(columns={"_roa": "m_roa", "_lta": "m_lta", "z_score": "m_z"}).reset_index())
    med["year"] += 1                                   # last year's medians, used this year
    bk = con.execute("""SELECT co.sic, year(e.filed) AS year, COUNT(DISTINCT e.cik) AS n_bk
                        FROM events e JOIN companies co USING (cik)
                        WHERE e.event = 'bankruptcy' GROUP BY ALL""").df()
    bk["sic2"] = (pd.to_numeric(bk["sic"], errors="coerce") // 100).astype("Int64")
    bk = bk.groupby(["sic2", "year"])["n_bk"].sum().reset_index()
    n = tmp.groupby(["sic2", "year"]).size().rename("n_co").reset_index()
    rate = n.merge(bk, on=["sic2", "year"], how="left").fillna({"n_bk": 0})
    rate["ind_bk_rate"] = rate["n_bk"] / rate["n_co"]
    rate = rate[rate["n_co"] >= 10][["sic2", "year", "ind_bk_rate"]]
    rate["year"] += 1                                  # bankruptcies filed last year
    ctx = med.merge(rate, on=["sic2", "year"], how="outer")
    df = df.reset_index().merge(ctx, on=["sic2", "year"], how="left").set_index("index").sort_index()
    df["roa_vs_ind"] = roa - df["m_roa"]
    df["liab_ta_vs_ind"] = liab_ta - df["m_lta"]
    df["z_vs_ind"] = df["z_score"] - df["m_z"]
    return df.drop(columns=["m_roa", "m_lta", "m_z"])
