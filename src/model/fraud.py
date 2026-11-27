"""Fraud model: was this 10-K later part of an SEC accounting enforcement case (AAER)?

Run:  python -m src.model.fraud     (after src.pipeline.aaer and src.model.live)

Label: a company-year is "fraud" if an accounting AAER against the company says that fiscal year was
misstated (src/pipeline/aaer.py). Companies whose case names no years are left out (label unknown).
Bribery-only (FCPA) and procedural releases are not fraud labels.

Two tests:
1. Real-time walk-forward (the honest one). To score fiscal year Y, train on earlier fiscal years,
   counting a row as fraud only if its AAER was released before Jan 1 of Y+1 (when the year-Y 10-K
   would be scored). The SEC takes a median of 6 years to announce a case, so the model learns from
   few, old cases. This is what a live system could have done.
2. Hindsight cross-validation (how much signal exists). 5 folds split by company, so a company is
   never in training and test at once, using all labels known today. Not achievable in real time,
   but shows the ceiling and matches how many research papers test fraud models.
Benchmarks on the same rows: Beneish M-Score (1999) and Faultline's restatement-risk model.

Result (Nov 2026): fraud is much harder than bankruptcy (real-time AUC ~0.64, hindsight ~0.69, Beneish 0.58).
Too weak to put a "fraud risk" number on named companies, so the site shows only the factual SEC cases.
"""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer

from src.config import DB_PATH, ROOT
from src.model.composite import FEATURES, load

CASES = ROOT / "data" / "processed" / "aaer_cases.csv"
OUT_JSON = ROOT / "data" / "processed" / "fraud_results.json"
TEST_YEARS = range(2013, 2020)   # fiscal years whose cases have mostly been announced by now


VARIANTS = {   # fixed before testing; all are reported, the simplest one did best and is the main result
    "logistic regression (ranked inputs)": lambda: make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True), QuantileTransformer(n_quantiles=200),
        LogisticRegression(C=0.1, max_iter=2000)),
    "gradient-boosted trees": lambda: HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, min_samples_leaf=40, random_state=0),
    "shallow trees": lambda: HistGradientBoostingClassifier(
        max_iter=150, learning_rate=0.05, max_depth=3, min_samples_leaf=200, l2_regularization=5.0, random_state=0),
}
_model = VARIANTS["logistic regression (ranked inputs)"]


def labelled(con) -> pd.DataFrame:
    df = load(con, end="2026-12-31")
    df["fy"] = pd.to_datetime(df["period_end"]).dt.year
    cases = pd.read_csv(CASES)
    acc = cases[cases["kind"] == "accounting"]
    unknown = set(acc.loc[acc["years"] == "[]", "cik"]) - set(acc.loc[acc["years"] != "[]", "cik"])
    yrs = pd.DataFrame([(r.cik, y, r.date) for r in acc[acc["years"] != "[]"].itertuples() for y in json.loads(r.years)],
                       columns=["cik", "fy", "released"]).groupby(["cik", "fy"], as_index=False)["released"].min()
    df = df[~df["cik"].isin(unknown)].merge(yrs, on=["cik", "fy"], how="left")
    df["fraud"] = df["released"].notna()
    risk = con.execute("SELECT cik, period_end, restatement_risk_raw FROM risk").df()
    return df.merge(risk, on=["cik", "period_end"], how="left")


def top_share(y, s, q=0.10):
    order = np.argsort(-s)
    k = int(len(s) * q)
    return float(y[order[:k]].sum() / y.sum())


def walk_forward(df):
    out = []
    for y in TEST_YEARS:
        cutoff = pd.Timestamp(f"{y + 1}-01-01")
        train = df[df["fy"] < y]
        lab = train["fraud"] & (pd.to_datetime(train["released"]) < cutoff)
        test = df[df["fy"] == y]
        m = _model().fit(train[FEATURES].astype(float), lab.astype(int))
        out.append(test.assign(fraud_score=m.predict_proba(test[FEATURES].astype(float))[:, 1],
                               known_cases=int(lab.sum())))
    return pd.concat(out)


def hindsight_cv(df):
    rows = df[df["fy"].isin(TEST_YEARS)].copy()
    rows["fraud_score"] = np.nan
    for tr, te in GroupKFold(n_splits=5).split(rows, groups=rows["cik"]):
        m = _model().fit(rows.iloc[tr][FEATURES].astype(float), rows.iloc[tr]["fraud"].astype(int))
        rows.iloc[te, rows.columns.get_loc("fraud_score")] = m.predict_proba(rows.iloc[te][FEATURES].astype(float))[:, 1]
    return rows


def summarise(rows) -> dict:
    y = rows["fraud"].astype(int).to_numpy()
    res = {"company_years": int(len(rows)), "fraud_company_years": int(y.sum()),
           "fraud_companies": int(rows.loc[rows["fraud"], "cik"].nunique()),
           "faultline_auc": float(roc_auc_score(y, rows["fraud_score"])),
           "faultline_top10": top_share(y, rows["fraud_score"].to_numpy())}
    for name, col in [("beneish", "m_score"), ("restatement_model", "restatement_risk_raw")]:
        r = rows[rows[col].notna()]
        yy = r["fraud"].astype(int).to_numpy()
        res[name] = {"rows": int(len(r)), "fraud": int(yy.sum()), "auc": float(roc_auc_score(yy, r[col])),
                     "top10": top_share(yy, r[col].to_numpy()),
                     "faultline_auc_same_rows": float(roc_auc_score(yy, r["fraud_score"])),
                     "faultline_top10_same_rows": top_share(yy, r["fraud_score"].to_numpy())}
    return res


def main():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = labelled(con)
    print(f"{len(df):,} company-years, {int(df['fraud'].sum())} later named in an SEC accounting case")
    wf = walk_forward(df)
    res = {"test_fiscal_years": f"{min(TEST_YEARS)}-{max(TEST_YEARS)}",
           "real_time": summarise(wf),
           "known_cases_when_training": {int(y): int(k) for y, k in wf.groupby("fy")["known_cases"].first().items()},
           "hindsight_cv": summarise(hindsight_cv(df))}
    global _model
    res["variants"] = {}
    for name, mk in VARIANTS.items():
        _model = mk
        a, b = summarise(walk_forward(df)), summarise(hindsight_cv(df))
        res["variants"][name] = {"real_time_auc": a["faultline_auc"], "hindsight_auc": b["faultline_auc"],
                                 "real_time_top10": a["faultline_top10"], "hindsight_top10": b["faultline_top10"]}
    _model = VARIANTS["logistic regression (ranked inputs)"]
    OUT_JSON.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
