"""Piotroski F-Score (2000): financial strength, 0-9. One point per test passed.

Works on a DataFrame with this year's columns and last year's columns (suffix '_prev').
ROA uses end-of-year total assets for both years (a common simplification; Piotroski used
beginning-of-year assets). F is only given when all 9 tests can be computed.
"""
import numpy as np
import pandas as pd

from src.scores.common import safe_div, test_or_nan


def piotroski(df: pd.DataFrame) -> pd.DataFrame:
    ta, ta0 = df["total_assets"], df["total_assets_prev"]
    roa, roa0 = safe_div(df["net_income"], ta), safe_div(df["net_income_prev"], ta0)
    cfo_ta = safe_div(df["cfo"], ta)
    # no long-term debt reported -> treat as 0 debt (common for debt-free companies)
    lev, lev0 = safe_div(df["long_term_debt"].fillna(0), ta), safe_div(df["long_term_debt_prev"].fillna(0), ta0)
    cr, cr0 = safe_div(df["current_assets"], df["current_liabilities"]), safe_div(df["current_assets_prev"], df["current_liabilities_prev"])
    gm, gm0 = safe_div(df["gross_profit"], df["revenue"]), safe_div(df["gross_profit_prev"], df["revenue_prev"])
    at, at0 = safe_div(df["revenue"], ta), safe_div(df["revenue_prev"], ta0)
    sh, sh0 = df["shares_outstanding"].to_numpy(float), df["shares_outstanding_prev"].to_numpy(float)

    out = pd.DataFrame(index=df.index)
    out["f1_roa_pos"] = test_or_nan(roa > 0, roa)                  # profitable
    out["f2_cfo_pos"] = test_or_nan(cfo_ta > 0, cfo_ta)            # cash from operations
    out["f3_roa_up"] = test_or_nan(roa > roa0, roa, roa0)          # more profitable than last year
    out["f4_accrual"] = test_or_nan(cfo_ta > roa, cfo_ta, roa)     # profit backed by cash
    out["f5_lev_down"] = test_or_nan(lev <= lev0, lev, lev0)       # debt not growing
    out["f6_cr_up"] = test_or_nan(cr > cr0, cr, cr0)               # liquidity improving
    out["f7_no_dilution"] = test_or_nan(sh <= sh0 * 1.005, sh, sh0)  # no new shares (0.5% tolerance)
    out["f8_gm_up"] = test_or_nan(gm > gm0, gm, gm0)               # margins improving
    out["f9_turnover_up"] = test_or_nan(at > at0, at, at0)         # assets working harder
    tests = out.columns.tolist()
    out["f_tests_known"] = out[tests].notna().sum(axis=1)
    out["f_score"] = out[tests].sum(axis=1, min_count=9)           # NaN unless all 9 known
    return out


def f_band(f):
    f = np.asarray(f, dtype=float)
    return np.select([np.isnan(f), f >= 7, f <= 3], [None, "strong", "weak"], default="neutral").astype(object)
