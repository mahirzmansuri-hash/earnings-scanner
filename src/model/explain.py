"""Why does a company get its bankruptcy risk? A per-company breakdown for the website.

Method (a "swap test", also called occlusion): the model's 46 inputs are put in 9 plain-English
groups. For each group, we replace the company's values with a typical company's (the median of
the rows the model was trained on) and score it again. If the risk falls a lot, that group was
pushing it up; if it rises, that group was holding it down.

  effect = log-odds(real risk) - log-odds(risk with this group made typical)

Log-odds (log of p / (1 - p)) is used because risk is multiplicative near 0: going from 1% to 2%
matters as much as 10% to 20%. An effect of +0.69 means the group roughly doubles the odds.

Same model that scored the filing (trained only on earlier years), so this explains the number
shown on the page. Limit: groups overlap (a big loss hurts both "profits" and "cash flow"), so the
effects don't add up exactly to the total; they show which areas matter most, not exact shares.
"""
import numpy as np
import pandas as pd

from src.model.composite import FEATURES

GROUPS = {
    "debt": ["liab_ta", "neg_equity", "altman_x4", "altman_x4_book", "f5_lev_down", "lvgi", "f7_no_dilution"],
    "past_losses": ["altman_x2"],
    "profits": ["roa", "altman_x3", "f1_roa_pos", "f3_roa_up", "f8_gm_up", "gmi"],
    "cash_flow": ["cfo_ta", "cash_burn", "f2_cfo_pos", "f4_accrual", "tata"],
    "liquidity": ["altman_x1", "f6_cr_up"],
    "sales": ["rev_growth", "altman_x5", "sgi", "f9_turnover_up"],
    "size": ["log_assets", "log_revenue", "log_float"],
    "accounting": ["dsri", "aqi", "depi", "sgai"],
    "classic_scores": ["z_score", "z2_score", "f_score", "m_score"],
    "warnings": ["days_to_file", "ev_auditor_change", "ev_late_10k", "ev_amended_10k", "ev_non_reliance",
                 "tx_gc_doubt", "tx_gc_recurring", "tx_mw_identified", "tx_icfr_not_effective", "tx_restated"],
}
assert sorted(f for g in GROUPS.values() for f in g) == sorted(FEATURES), "every input must be in exactly one group"

LABELS = {"debt": "Debt and financing", "past_losses": "Retained earnings", "profits": "Profits", "cash_flow": "Cash flow",
          "liquidity": "Short-term cash", "sales": "Sales", "size": "Company size", "accounting": "Accounting patterns",
          "classic_scores": "Classic scores", "warnings": "Warning signs in filings"}


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _pct(x):
    return "n/a" if pd.isna(x) else f"{x * 100:.0f}%"


def _money(x):
    if pd.isna(x):
        return "n/a"
    for div, unit in [(1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if abs(x) >= div:
            return f"${x / div:.1f}{unit}"
    return f"${x:,.0f}"


def detail(g: str, r: pd.Series, med: pd.Series) -> str:
    """One plain sentence with the company's number next to the typical company's."""
    if g == "debt":
        s = f"Liabilities are {_pct(r.liab_ta)} of assets (typical {_pct(med.liab_ta)})"
        return s + "; liabilities exceed assets" if pd.notna(r.neg_equity) and r.neg_equity == 1 else s
    if g == "past_losses":
        return f"Retained earnings are {_pct(r.altman_x2)} of assets (typical {_pct(med.altman_x2)})"
    if g == "profits":
        return f"Net income is {_pct(r.roa)} of assets (typical {_pct(med.roa)})"
    if g == "cash_flow":
        return f"Operating cash flow is {_pct(r.cfo_ta)} of assets (typical {_pct(med.cfo_ta)})"
    if g == "liquidity":
        return f"Working capital is {_pct(r.altman_x1)} of assets (typical {_pct(med.altman_x1)})"
    if g == "sales":
        return f"Revenue changed {'n/a' if pd.isna(r.rev_growth) else f'{r.rev_growth * 100:+.0f}%'} from the year before (typical {med.rev_growth * 100:+.0f}%)"
    if g == "size":
        return f"Total assets {_money(r.total_assets)} (typical {_money(np.exp(med.log_assets))})"
    if g == "accounting":
        return "Receivables, asset quality, depreciation and overhead trends (Beneish ratios)"
    if g == "classic_scores":
        z = "n/a" if pd.isna(r.z_score) else f"{r.z_score:.2f}"
        f = "n/a" if pd.isna(r.f_score) else f"{r.f_score:.0f}"
        z2 = "n/a" if pd.isna(r.z2_score) else f"{r.z2_score:.2f}"
        return f"Altman Z {z} (typical {med.z_score:.2f}), Z'' on book equity {z2} (typical {med.z2_score:.2f}), Piotroski F {f}"
    if g == "warnings":
        found = [name for col, name in [("tx_gc_doubt", "going-concern wording"), ("tx_mw_identified", "material weakness"),
                                        ("tx_icfr_not_effective", "ineffective internal controls"), ("tx_restated", "restated numbers"),
                                        ("ev_late_10k", "late 10-K notice"), ("ev_auditor_change", "auditor change"),
                                        ("ev_non_reliance", "non-reliance notice"), ("ev_amended_10k", "amended 10-K")]
                 if pd.notna(r.get(col)) and r.get(col) > 0]
        days = "" if pd.isna(r.days_to_file) else f"10-K filed {r.days_to_file:.0f} days after year end (typical {med.days_to_file:.0f})"
        return "; ".join(([(lambda t: t[0].upper() + t[1:])(", ".join(found))] if found else []) + ([days] if days else [])) or "None found"
    return ""


def explain(rows: pd.DataFrame, models: dict) -> pd.DataFrame:
    """rows: model input rows with a 'year' column; models: {year: (model, training medians)}."""
    out = []
    for y, part in rows.groupby("year"):
        model, med = models[y]
        X = part[FEATURES].astype(float)
        base = _logit(model.predict_proba(X)[:, 1])
        for g, cols in GROUPS.items():
            X2 = X.copy()
            for c in cols:
                X2[c] = med[c]
            eff = base - _logit(model.predict_proba(X2)[:, 1])
            for (_, r), e in zip(part.iterrows(), eff):
                out.append({"cik": r.cik, "period_end": r.period_end, "grp": g, "label": LABELS[g],
                            "effect": float(e), "detail": detail(g, r, med)})
    return pd.DataFrame(out)
