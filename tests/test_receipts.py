import pandas as pd

from src.web.build import _floor_pct, receipts_rows


def test_receipts_uses_only_earlier_scores_and_skips_bad_tags():
    ev = pd.DataFrame({"cik": [1, 2, 3], "event": ["bankruptcy"] * 3, "accn": ["a", "b", "bad"],
                       "filed": pd.to_datetime(["2026-06-01", "2026-07-01", "2026-07-01"])})
    tl = pd.DataFrame({"cik": [1, 1, 1, 2], "d": pd.to_datetime(["2025-11-01", "2026-03-01", "2026-06-15", "2024-01-01"]),
                       "p": [0.95, 0.80, 0.99, 0.99], "src": ["10-K", "10-Q", "10-Q", "10-K"]})
    r = receipts_rows(ev, tl, "2026-11-25", not_bankruptcy={"bad"}).set_index("cik")
    assert set(r.index) == {1, 2}                                     # mis-tagged filing left out
    assert r.loc[1, "p"] == 0.80                                      # the score after the filing is ignored
    assert r.loc[1, "first_top"] == pd.Timestamp("2025-11-01")
    assert pd.isna(r.loc[2, "p"])                                     # only score is older than 13 months


def test_floor_pct():
    assert _floor_pct(0.897) == "89%" and _floor_pct(1.0) == "99%"
