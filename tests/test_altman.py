"""Tests for Mahir's Altman Z-Score (src/scores/altman.py).

These will FAIL until altman.py exists. That's expected: write the code until they pass.
Run:  pytest tests/test_altman.py -v
"""
import pytest

from src.scores.altman import altman_z, altman_zone

# Apple FY2025 (period ending 2025-09-27, first filed 2025-10-31), from annual_first.
# Market value of equity is a round PLACEHOLDER until we have price data.
APPLE = dict(
    current_assets=147_957_000_000,
    current_liabilities=165_631_000_000,
    total_assets=359_241_000_000,
    retained_earnings=-14_264_000_000,
    ebit=133_050_000_000,
    market_value_equity=3_700_000_000_000,
    total_liabilities=285_508_000_000,
    sales=416_161_000_000,
)


def test_apple_worked_example():
    assert altman_z(**APPLE) == pytest.approx(10.042, abs=0.001)


@pytest.mark.parametrize("z, zone", [
    (10.04, "safe"),
    (3.01, "safe"),
    (3.0, "gray"),      # "above 3 is safe", so exactly 3 is still gray
    (2.5, "gray"),
    (1.8, "gray"),      # 1.8-3 is the gray zone, 1.8 included
    (1.79, "distress"),
    (-0.5, "distress"),
])
def test_zones(z, zone):
    assert altman_zone(z) == zone
