"""Robustness checks for the bankruptcy model (all out-of-sample, same walk-forward test).

Run:  python -m src.model.robustness

1. By year: does Faultline beat Altman in EVERY test year, or only on average?
2. By size: small, mid and large companies (revenue).
3. Calibration: when the model says 5%, do about 5% go bankrupt?
4. Which clues matter: permutation importance (how much AUC drops when one clue is shuffled),
   for a model trained on outcomes known before 2021 and tested on 2021-2023 filings.
"""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score

from src.config import DB_PATH, ROOT
from src.model.composite import FEATURES, HORIZON, load, walk_forward

OUT_JSON = ROOT / "data" / "processed" / "robustness.json"


def auc(y, s):
    y = np.asarray(y, int)
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else None


def main():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = load(con)
    oos = walk_forward(df, verbose=False)
    rows = oos[oos["z_score"].notna()]
    res = {}

    res["by_year"] = {int(y): {"n": int(len(g)), "bankruptcies": int(g["label"].sum()),
                               "faultline_auc": auc(g["label"], g["composite"]), "altman_auc": auc(g["label"], -g["z_score"])}
                      for y, g in rows.groupby("year")}

    size = pd.cut(rows["revenue"], [-np.inf, 1e8, 1e9, np.inf], labels=["under $100M", "$100M-$1B", "over $1B"])
    res["by_size"] = {str(k): {"n": int(len(g)), "bankruptcies": int(g["label"].sum()),
                               "faultline_auc": auc(g["label"], g["composite"]), "altman_auc": auc(g["label"], -g["z_score"])}
                      for k, g in rows.groupby(size, observed=True)}

    bins = pd.qcut(oos["composite"], 10, labels=False, duplicates="drop")
    res["calibration_deciles"] = [{"decile": int(d) + 1, "predicted": float(g["composite"].mean()), "actual": float(g["label"].mean()),
                                   "n": int(len(g))} for d, g in oos.groupby(bins)]

    avail = pd.to_datetime(df["avail"])
    train = df[(avail + pd.Timedelta(days=HORIZON) < pd.Timestamp("2021-01-01")) & ~df["already_bankrupt"]]
    test = df[(avail >= pd.Timestamp("2021-01-01")) & (avail <= pd.Timestamp("2023-12-31")) & ~df["already_bankrupt"]]
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=0)
    model.fit(train[FEATURES].astype(float), train["label"].astype(int))
    pi = permutation_importance(model, test[FEATURES].astype(float), test["label"].astype(int), scoring="roc_auc",
                                n_repeats=5, random_state=0, n_jobs=-1)
    imp = sorted(zip(FEATURES, pi.importances_mean), key=lambda x: -x[1])
    res["top_features"] = [{"feature": f, "auc_drop": float(v)} for f, v in imp[:12]]

    OUT_JSON.write_text(json.dumps(res, indent=2))
    print("By year (Faultline vs Altman AUC):")
    for y, v in res["by_year"].items():
        print(f"  {y}: {v['faultline_auc']:.3f} vs {v['altman_auc']:.3f}  ({v['bankruptcies']} bankruptcies)")
    print("By size:")
    for k, v in res["by_size"].items():
        print(f"  {k:12} {v['faultline_auc']:.3f} vs {v['altman_auc']:.3f}  (n={v['n']:,}, {v['bankruptcies']} bankruptcies)")
    print("Calibration (predicted vs actual, by decile):")
    for c in res["calibration_deciles"]:
        print(f"  {c['decile']:2}: {c['predicted']*100:5.2f}% vs {c['actual']*100:5.2f}%")
    print("Top clues (AUC drop when shuffled):")
    for f in res["top_features"]:
        print(f"  {f['feature']:16} {f['auc_drop']:.4f}")


if __name__ == "__main__":
    main()
