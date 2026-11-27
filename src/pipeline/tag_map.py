"""Tag map: which XBRL tags hold each input the three scores need.

Companies don't all use the same tag for the same thing. Apple reports sales as
"RevenueFromContractWithCustomerExcludingAssessedTax", an older 10-K might use
"SalesRevenueNet", and many use plain "Revenues". This file lists, for each
concept, the tags to try IN PRIORITY ORDER: for a given company and period we
take the first tag on the list that has a value.

Order was chosen from measured coverage (first ~1,700 companies, FY2015-2024)
plus accounting meaning: the most precise tag goes first, broader ones later.

pick (optional):
  "largest" = when ONE filing has several of these tags, take the biggest value.
              Used for totals (revenue, COGS, SG&A): a total is never smaller than its parts.
              Found 2026-11-26: General Mills' FY2023 10-K tags Revenues = $1.96B (a
              component) and RevenueFromContract... = $20.09B (the real total).
  default   = take the first tag in the list (priority order).

kind:
  "duration" = covers a span of time (income statement, cash flow), e.g. FY revenue
  "instant"  = a snapshot on one date (balance sheet), e.g. total assets on Dec 31
"""

CONCEPTS: dict[str, dict] = {
    # ---------- income statement (duration) ----------
    "revenue": {"kind": "duration", "pick": "largest", "tags": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",   # new standard (ASC 606), from 2018
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",                                       # old standard, before 2018
        "SalesRevenueGoodsNet",
    ]},
    "cogs": {"kind": "duration", "pick": "largest", "tags": [
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
        "CostOfGoodsSold",
        "CostOfServices",
    ]},
    "gross_profit": {"kind": "duration", "tags": ["GrossProfit"]},
    "sga": {"kind": "duration", "pick": "largest", "tags": [
        "SellingGeneralAndAdministrativeExpense",
        "GeneralAndAdministrativeExpense",   # some report only G&A
    ]},
    "depreciation": {"kind": "duration", "tags": [
        "Depreciation",                          # PP&E only: what Beneish's DEPI really wants
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
    ]},
    "operating_income": {"kind": "duration", "tags": ["OperatingIncomeLoss"]},  # stand-in for EBIT
    "net_income": {"kind": "duration", "tags": [
        "NetIncomeLoss",   # profit belonging to the company's own shareholders
        "ProfitLoss",      # includes minority owners' share; fallback only
    ]},
    "cfo": {"kind": "duration", "tags": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ]},

    # ---------- balance sheet (instant) ----------
    "total_assets": {"kind": "instant", "tags": ["Assets"]},
    "current_assets": {"kind": "instant", "tags": ["AssetsCurrent"]},
    "current_liabilities": {"kind": "instant", "tags": ["LiabilitiesCurrent"]},
    "total_liabilities": {"kind": "instant", "tags": ["Liabilities"]},
    "liabilities_and_equity": {"kind": "instant", "tags": ["LiabilitiesAndStockholdersEquity"]},
    "equity": {"kind": "instant", "tags": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ]},
    "receivables": {"kind": "instant", "tags": [
        "AccountsReceivableNetCurrent",
        "ReceivablesNetCurrent",
    ]},
    "ppe": {"kind": "instant", "tags": ["PropertyPlantAndEquipmentNet"]},
    "securities": {"kind": "instant", "tags": [   # long-term investments, for Beneish AQI
        "LongTermInvestments",
        "MarketableSecuritiesNoncurrent",
        "AvailableForSaleSecuritiesDebtSecuritiesNoncurrent",
    ]},
    "long_term_debt": {"kind": "instant", "tags": [
        "LongTermDebtNoncurrent",   # only the part due after 1 year
        "LongTermDebt",             # may include the part due within 1 year
    ]},
    "retained_earnings": {"kind": "instant", "tags": ["RetainedEarningsAccumulatedDeficit"]},
    "shares_outstanding": {"kind": "instant", "tags": [
        "CommonStockSharesOutstanding",           # balance-sheet date
        "EntityCommonStockSharesOutstanding",     # cover page (dei), a date near the filing
    ]},
}

# Filled in by arithmetic when no tag exists (applied after tag lookup):
DERIVED = {
    "gross_profit": "revenue - cogs",
    "cogs": "revenue - gross_profit",
    "total_liabilities": "liabilities_and_equity - equity",
}
