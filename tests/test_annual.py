"""Tests for src/pipeline/annual.py using a tiny fake database.

Each test builds a handful of made-up facts where we KNOW the right answer,
runs build_annual(), and checks the result. Run with:  pytest
"""
import duckdb
import pytest

from src.pipeline.annual import build_annual
from src.pipeline.load_db import FACTS_SCHEMA

CIK = 1


@pytest.fixture
def con():
    c = duckdb.connect()  # in-memory database: nothing touches data/
    c.execute(FACTS_SCHEMA)
    c.execute("CREATE TABLE companies (cik INTEGER, name VARCHAR)")
    yield c
    c.close()


def add(con, tag, value, filed, accn, start="2022-01-01", end="2022-12-31", taxonomy="us-gaap"):
    con.execute("INSERT INTO facts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [CIK, taxonomy, tag, "USD", start, end, value, accn, 2022, "FY", "10-K", filed, None])


def get(con, concept, end="2022-12-31"):
    return con.execute("SELECT value_first, value_latest, revised FROM annual WHERE concept=? AND period_end=?",
                       [concept, end]).fetchone()


def test_first_filed_is_point_in_time(con):
    """The backtest must see the ORIGINAL number, not a later restated one."""
    add(con, "Revenues", 100.0, "2023-02-15", "A1")
    add(con, "Revenues", 80.0, "2024-02-15", "A2")   # restated a year later
    build_annual(con)
    assert get(con, "revenue") == (100.0, 80.0, True)


def test_quarters_inside_a_10k_are_ignored(con):
    add(con, "Revenues", 100.0, "2023-02-15", "A1")
    add(con, "Revenues", 30.0, "2023-02-15", "A1", start="2022-10-01")  # Q4 only
    build_annual(con)
    assert get(con, "revenue")[0] == 100.0


def test_identity_referee_beats_bigger_wrong_tag(con):
    """Hasbro-style: plain 'Revenues' is wrong; revenue - COGS = gross profit decides."""
    add(con, "Revenues", 150.0, "2023-02-15", "A1")
    add(con, "RevenueFromContractWithCustomerExcludingAssessedTax", 100.0, "2023-02-15", "A1")
    add(con, "CostOfRevenue", 60.0, "2023-02-15", "A1")
    add(con, "GrossProfit", 40.0, "2023-02-15", "A1")
    build_annual(con)
    assert get(con, "revenue")[0] == 100.0


def test_largest_wins_without_referee(con):
    """General Mills-style: a component tag must not beat the total."""
    add(con, "Revenues", 10.0, "2023-02-15", "A1")
    add(con, "RevenueFromContractWithCustomerExcludingAssessedTax", 200.0, "2023-02-15", "A1")
    build_annual(con)
    assert get(con, "revenue")[0] == 200.0


def test_first_filed_never_uses_a_later_filings_tag(con):
    """A newer tag in a 2024 reprint must not replace what was public in 2023."""
    add(con, "SalesRevenueNet", 100.0, "2023-02-15", "A1")
    add(con, "Revenues", 120.0, "2024-02-15", "A2")
    build_annual(con)
    assert get(con, "revenue")[0] == 100.0


def test_balance_sheet_uses_fiscal_year_end_only(con):
    add(con, "Revenues", 100.0, "2023-02-15", "A1")                       # defines FYE 2022-12-31
    add(con, "Assets", 500.0, "2023-02-15", "A1", start=None)              # year end: keep
    add(con, "Assets", 450.0, "2023-02-15", "A1", start=None, end="2022-06-30")  # mid-year: drop
    build_annual(con)
    assert get(con, "total_assets")[0] == 500.0
    assert get(con, "total_assets", end="2022-06-30") is None


def test_cover_page_shares_belong_to_the_filings_year(con):
    add(con, "Revenues", 100.0, "2023-02-15", "A1")
    add(con, "EntityCommonStockSharesOutstanding", 7.0, "2023-02-15", "A1",
        start=None, end="2023-02-01", taxonomy="dei")   # dated near the filing day
    build_annual(con)
    assert get(con, "shares_outstanding")[0] == 7.0


def test_derived_gross_profit(con):
    add(con, "Revenues", 100.0, "2023-02-15", "A1")
    add(con, "CostOfRevenue", 70.0, "2023-02-15", "A1")
    build_annual(con)
    gp = con.execute("SELECT gross_profit FROM annual_first").fetchone()[0]
    assert gp == 30.0
