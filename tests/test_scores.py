"""Tests for Piotroski, Beneish, the shared helpers and the website formatters."""
import math

import numpy as np
import pandas as pd
import pytest

from src.scores.altman import altman_z2, altman_z2_zone
from src.scores.beneish import beneish
from src.scores.common import safe_div, zone
from src.scores.piotroski import piotroski
from src.web.build import band, money

BASE = dict(revenue=100.0, cogs=60.0, gross_profit=40.0, sga=10.0, depreciation=5.0, net_income=8.0, cfo=10.0,
            total_assets=200.0, current_assets=80.0, current_liabilities=40.0, receivables=20.0, ppe=50.0,
            securities=10.0, long_term_debt=30.0, shares_outstanding=10.0)


def frame(this: dict, prev: dict) -> pd.DataFrame:
    row = {**this, **{f"{k}_prev": v for k, v in prev.items()}}
    return pd.DataFrame([row])


def test_safe_div_handles_zero_and_missing():
    assert math.isnan(safe_div(1, 0))
    assert math.isnan(safe_div(1, float("nan")))
    assert safe_div(6, 3) == 2


def test_zone_boundaries_and_missing():
    assert zone(1.79, 1.8, 3.0) == "distress"
    assert zone(1.8, 1.8, 3.0) == "gray"
    assert zone(3.01, 1.8, 3.0) == "safe"
    assert zone(float("nan"), 1.8, 3.0) is None


def test_beneish_no_change_gives_known_score():
    """Same numbers both years -> every index is 1 and TATA = (8 - 10) / 200 = -0.01."""
    m = beneish(frame(BASE, BASE)).iloc[0]
    for k in ["dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi"]:
        assert m[k] == pytest.approx(1.0)
    expected = -4.84 + 0.920 + 0.528 + 0.404 + 0.892 + 0.115 - 0.172 - 0.327 + 4.679 * -0.01
    assert m["m_score"] == pytest.approx(expected)
    assert m["m_flag"] == 0


def test_beneish_receivables_jump_raises_score():
    worse = {**BASE, "receivables": 40.0}
    assert beneish(frame(worse, BASE)).iloc[0]["m_score"] > beneish(frame(BASE, BASE)).iloc[0]["m_score"]


def test_piotroski_improving_company_scores_9():
    prev = {**BASE, "net_income": 4.0, "long_term_debt": 40.0, "current_assets": 60.0,
            "gross_profit": 30.0, "revenue": 90.0, "shares_outstanding": 10.0}
    f = piotroski(frame(BASE, prev)).iloc[0]
    assert f["f_score"] == 9


def test_piotroski_missing_input_gives_no_score():
    this = {**BASE, "cfo": float("nan")}
    f = piotroski(frame(this, BASE)).iloc[0]
    assert np.isnan(f["f_score"]) and f["f_tests_known"] == 7


def test_altman_z2_zones():
    z2 = altman_z2(current_assets=80, current_liabilities=40, total_assets=200, retained_earnings=50,
                   ebit=20, book_equity=100, total_liabilities=100)
    assert z2 == pytest.approx(6.56 * 0.2 + 3.26 * 0.25 + 6.72 * 0.1 + 1.05 * 1.0)
    assert altman_z2_zone(z2) == "safe"


def test_web_formatters():
    assert money(416_161_000_000) == "$416.2B"
    assert money(-383_000_000) == "-$383.0M"
    assert money(float("nan")) == "n/a"
    assert band(0.99)[0] == "High" and band(0.85)[0] == "Elevated" and band(0.5)[0] == "Normal"
