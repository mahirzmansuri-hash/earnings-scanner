"""Which evidence matters? Re-run the walk-forward test with feature groups added one at a time.

Run:  python -m src.model.ablation
Also prints the 'riskiest X%' table: if you flag only the top X% of companies, what share of
bankruptcies do you catch? (Altman ranked by lowest Z, Faultline by highest probability.)
"""
import json

import duckdb
import numpy as np
from sklearn.metrics import roc_auc_score

from src.config import DB_PATH, ROOT
from src.model.composite import FEATURES, load, walk_forward

OUT_JSON = ROOT / "data" / "processed" / "composite_ablation.json"

SCORES = FEATURES[:27]                         # Altman, Piotroski, Beneish pieces
FUNDAMENTALS = FEATURES[27:36]                 # size, profitability, leverage, growth
FILING_EVENTS = FEATURES[36:41]                # filing delay + warning events
TEXT = FEATURES[41:]                           # 10-K wording (full-text search flags)
GROUPS = {
    "1. classic scores only": SCORES,
    "2. + size & fundamentals": SCORES + FUNDAMENTALS,
    "3. + filing behaviour & warning events": SCORES + FUNDAMENTALS + FILING_EVENTS,
    "4. + 10-K text signals (full)": SCORES + FUNDAMENTALS + FILING_EVENTS + TEXT,
    "events & filing behaviour only": FILING_EVENTS,
    "10-K text signals only": TEXT,
}


def top_share_caught(rows, score_col, ascending, shares=(0.05, 0.10, 0.20)):
    r = rows.sort_values(score_col, ascending=ascending)
    total = r["label"].sum()
    return {f"top_{int(s * 100)}pct": float(r.head(int(len(r) * s))["label"].sum() / total) for s in shares}


def main():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = load(con)
    out = {}
    for name, feats in GROUPS.items():
        oos = walk_forward(df, feats, verbose=False)
        rows = oos[oos["z_score"].notna()]
        out[name] = {"auc_same_rows_as_altman": float(roc_auc_score(rows["label"].astype(int), rows["composite"])),
                     "caught_if_flag_top": top_share_caught(rows, "composite", ascending=False)}
        print(f"{name:48} AUC {out[name]['auc_same_rows_as_altman']:.3f}  caught in top 5/10/20%: "
              + " / ".join(f"{v:.0%}" for v in out[name]["caught_if_flag_top"].values()))
    altman = top_share_caught(rows, "z_score", ascending=True)
    out["altman_z (lowest first)"] = {"caught_if_flag_top": altman}
    print(f"{'Altman Z (lowest Z first)':48}            caught in top 5/10/20%: " + " / ".join(f"{v:.0%}" for v in altman.values()))
    OUT_JSON.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
