"""The why-this-score breakdown: every model input is explained, and a group that is already typical has no effect."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from src.model.composite import FEATURES
from src.model.explain import GROUPS, explain


def test_every_input_in_one_group():
    flat = [f for g in GROUPS.values() for f in g]
    assert sorted(flat) == sorted(FEATURES) and len(flat) == len(set(flat))


def test_typical_company_has_no_effect_and_debt_shows_up():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(2000, len(FEATURES))), columns=FEATURES)
    y = (X["liab_ta"] > 1.0).astype(int)            # toy rule: only debt matters
    model = HistGradientBoostingClassifier(max_iter=50, random_state=0).fit(X, y)
    med = X.median()
    rows = pd.concat([med.to_frame().T, med.to_frame().T.assign(liab_ta=3.0)], ignore_index=True)
    rows = rows.assign(cik=[1, 2], period_end=pd.Timestamp("2024-12-31"), year=2024, total_assets=1e9, neg_equity=0)
    why = explain(rows, {2024: (model, med)})
    assert why[why.cik == 1]["effect"].abs().max() < 1e-9          # typical in every area -> nothing moves
    top = why[why.cik == 2].sort_values("effect", ascending=False).iloc[0]
    assert top["grp"] == "debt" and top["effect"] > 1
