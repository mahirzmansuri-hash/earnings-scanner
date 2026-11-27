"""Faultline Composite for ACCOUNTING problems: predicts a restatement notice within 24 months.

Run:  python -m src.model.restatement

Event = 8-K Item 4.02 "non-reliance": the company tells investors its past financial
statements can't be relied on (a true restatement, not a routine recast).
Same features and walk-forward test as the bankruptcy model; baseline = Beneish M-Score.
Companies that already went bankrupt are kept (restatements can come after distress).
"""
import json

import duckdb
import numpy as np
from sklearn.metrics import roc_auc_score

from src.config import DB_PATH, ROOT
from src.model.ablation import top_share_caught
from src.model.composite import load, walk_forward

OUT_JSON = ROOT / "data" / "processed" / "restatement_results.json"


def main():
    with duckdb.connect(str(DB_PATH)) as con:
        df = load(con, event="non_reliance")
        df["already_bankrupt"] = False
        print(f"{len(df):,} company-years, {int(df['label'].sum())} followed by a restatement notice within 24 months")
        oos = walk_forward(df)
        keep = oos[["cik", "period_end", "available_date", "composite"]].rename(columns={"composite": "restatement_risk"})
        con.register("rr_df", keep)
        con.execute("CREATE OR REPLACE TABLE restatement_risk AS SELECT * FROM rr_df")
        con.unregister("rr_df")
    rows = oos[oos["m_score"].notna()].copy()
    y = rows["label"].astype(int)
    flag = rows["m_score"] > -1.78
    alarm = flag.mean()
    fl = rows["composite"] >= rows["composite"].quantile(1 - alarm)
    res = {
        "company_years_with_beneish": int(len(rows)), "restatements": int(y.sum()),
        "beneish": {"alarm_rate": float(alarm), "hit_rate": float(flag[y == 1].mean()), "auc": float(roc_auc_score(y, rows["m_score"])),
                    "caught_if_flag_top": top_share_caught(rows, "m_score", ascending=False)},
        "faultline_same_alarm_rate": {"hit_rate": float(fl[y == 1].mean())},
        "faultline_auc": float(roc_auc_score(y, rows["composite"])),
        "faultline_caught_if_flag_top": top_share_caught(rows, "composite", ascending=False),
        "all_rows": {"company_years": int(len(oos)), "restatements": int(oos["label"].sum()),
                     "faultline_auc": float(roc_auc_score(oos["label"].astype(int), oos["composite"])),
                     "faultline_caught_if_flag_top": top_share_caught(oos, "composite", ascending=False)},
    }
    OUT_JSON.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
