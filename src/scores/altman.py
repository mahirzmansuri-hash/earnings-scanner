"""Altman Z-Score (1968) and Z''-Score (1995): bankruptcy risk.

Z   = 1.2 X1 + 1.4 X2 + 3.3 X3 + 0.6 X4 + 1.0 X5
      X1 working capital / total assets      X4 MARKET value of equity / total liabilities
      X2 retained earnings / total assets    X5 sales / total assets
      X3 EBIT / total assets
      zones: > 3 safe, 1.8-3 gray, < 1.8 distress
      Market value: we use the 10-K cover-page public float (free; excludes insider shares).

Z'' = 6.56 X1 + 3.26 X2 + 6.72 X3 + 1.05 X4''   with X4'' = BOOK equity / total liabilities
      Altman's version for non-manufacturers; needs no stock price. Drops X5 so it isn't
      biased by industry (retailers have high sales/assets).
      zones: > 2.6 safe, 1.1-2.6 gray, < 1.1 distress
"""
from src.scores.common import safe_div, zone

Z_DISTRESS, Z_SAFE = 1.8, 3.0
Z2_DISTRESS, Z2_SAFE = 1.1, 2.6


def altman_ratios(current_assets, current_liabilities, total_assets, retained_earnings, ebit,
                  market_value_equity, total_liabilities, sales, book_equity=float("nan")):
    return {
        "x1": safe_div(current_assets - current_liabilities, total_assets),
        "x2": safe_div(retained_earnings, total_assets),
        "x3": safe_div(ebit, total_assets),
        "x4": safe_div(market_value_equity, total_liabilities),
        "x5": safe_div(sales, total_assets),
        "x4_book": safe_div(book_equity, total_liabilities),
    }


def altman_z(current_assets, current_liabilities, total_assets, retained_earnings, ebit,
             market_value_equity, total_liabilities, sales):
    r = altman_ratios(current_assets, current_liabilities, total_assets, retained_earnings, ebit,
                      market_value_equity, total_liabilities, sales)
    return 1.2 * r["x1"] + 1.4 * r["x2"] + 3.3 * r["x3"] + 0.6 * r["x4"] + 1.0 * r["x5"]


def altman_z2(current_assets, current_liabilities, total_assets, retained_earnings, ebit,
              book_equity, total_liabilities):
    x1 = safe_div(current_assets - current_liabilities, total_assets)
    x2 = safe_div(retained_earnings, total_assets)
    x3 = safe_div(ebit, total_assets)
    x4 = safe_div(book_equity, total_liabilities)
    return 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4


def altman_zone(z):
    return zone(z, Z_DISTRESS, Z_SAFE)


def altman_z2_zone(z2):
    return zone(z2, Z2_DISTRESS, Z2_SAFE)
