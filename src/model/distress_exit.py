"""Second outcome: 'distress exit' = bankruptcy filing OR going dark without being bought.

Run:  python -m src.model.distress_exit

Why: small companies often stop filing instead of filing a bankruptcy 8-K, so a
bankruptcy-only label under-counts their failures. Same walk-forward test (2016-2023),
compared with Altman Z on the same rows.
"""
import json

import duckdb
from sklearn.metrics import roc_auc_score

from src.config import DB_PATH, ROOT
from src.model.ablation import top_share_caught
from src.model.composite import load, walk_forward

OUT_JSON = ROOT / "data" / "processed" / "distress_exit_results.json"


def main():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = load(con, event="distress_exit")
    print(f"{len(df):,} company-years, {int(df['label'].sum()):,} followed by a distress exit within 24 months")
    oos = walk_forward(df, verbose=False)
    rows = oos[oos["z_score"].notna()]
    y = rows["label"].astype(int)
    res = {"company_years": int(len(rows)), "distress_exits": int(y.sum()),
           "faultline_auc": float(roc_auc_score(y, rows["composite"])), "altman_auc": float(roc_auc_score(y, -rows["z_score"])),
           "faultline_caught_if_flag_top": top_share_caught(rows, "composite", ascending=False),
           "altman_caught_if_flag_top": top_share_caught(rows, "z_score", ascending=True)}
    size = rows["revenue"] < 1e8
    for name, m in [("small_under_100m", size), ("large_100m_plus", ~size)]:
        g = rows[m]
        res[name] = {"n": int(len(g)), "exits": int(g["label"].sum()),
                     "faultline_auc": float(roc_auc_score(g["label"].astype(int), g["composite"])),
                     "altman_auc": float(roc_auc_score(g["label"].astype(int), -g["z_score"]))}
    OUT_JSON.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
