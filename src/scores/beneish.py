"""Beneish M-Score (1999): likelihood of earnings manipulation.

M = -4.84 + 0.920 DSRI + 0.528 GMI + 0.404 AQI + 0.892 SGI + 0.115 DEPI
          - 0.172 SGAI + 4.679 TATA - 0.327 LVGI
M > -1.78 -> likely manipulator (CLAUDE.md threshold).

Index ratios compare this year (t) with last year (t-1). TATA uses the modern definition
(net income - operating cash flow) / total assets. Missing securities / long-term debt -> 0.
"""
import numpy as np
import pandas as pd

from src.scores.common import safe_div

M_THRESHOLD = -1.78
WEIGHTS = {"dsri": 0.920, "gmi": 0.528, "aqi": 0.404, "sgi": 0.892, "depi": 0.115,
           "sgai": -0.172, "tata": 4.679, "lvgi": -0.327}


def beneish(df: pd.DataFrame) -> pd.DataFrame:
    s, s0 = df["revenue"], df["revenue_prev"]
    ta, ta0 = df["total_assets"], df["total_assets_prev"]
    out = pd.DataFrame(index=df.index)
    out["dsri"] = safe_div(safe_div(df["receivables"], s), safe_div(df["receivables_prev"], s0))
    out["gmi"] = safe_div(safe_div(df["gross_profit_prev"], s0), safe_div(df["gross_profit"], s))
    hard = (df["current_assets"] + df["ppe"] + df["securities"].fillna(0)) / ta
    hard0 = (df["current_assets_prev"] + df["ppe_prev"] + df["securities_prev"].fillna(0)) / ta0
    out["aqi"] = safe_div(1 - hard, 1 - hard0)
    out["sgi"] = safe_div(s, s0)
    rate = safe_div(df["depreciation"], df["depreciation"] + df["ppe"])
    rate0 = safe_div(df["depreciation_prev"], df["depreciation_prev"] + df["ppe_prev"])
    out["depi"] = safe_div(rate0, rate)
    out["sgai"] = safe_div(safe_div(df["sga"], s), safe_div(df["sga_prev"], s0))
    out["tata"] = safe_div(df["net_income"] - df["cfo"], ta)
    lev = safe_div(df["current_liabilities"] + df["long_term_debt"].fillna(0), ta)
    lev0 = safe_div(df["current_liabilities_prev"] + df["long_term_debt_prev"].fillna(0), ta0)
    out["lvgi"] = safe_div(lev, lev0)
    out["m_score"] = -4.84 + sum(w * out[k] for k, w in WEIGHTS.items())  # NaN if any ratio missing
    out["m_flag"] = np.where(out["m_score"].isna(), np.nan, (out["m_score"] > M_THRESHOLD).astype(float))
    return out
