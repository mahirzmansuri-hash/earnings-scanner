---
name: spot-check
description: Verify a number from our EDGAR/DuckDB data against the company's actual 10-K or 10-Q. Use when the user says "spot-check", "verify against the 10-K", "is this number right", or runs /spot-check <ticker or CIK> <item>. Required before trusting any new data source, tag mapping, or score input.
---

# Spot-check a number against the filing

Goal: the user confirms the number with their own eyes in the real filing. Don't just assert it.

## Steps
1. **Pull our value.** From the raw companyfacts JSON (`data/raw/companyfacts/`) or DuckDB, get: tag, value, unit, `start`/`end`, form, `filed`, `accn`. If several rows cover the same period, show all of them and point out the earliest `filed`.
2. **Point the user to the filing.**
   - Filing index URL: `https://www.sec.gov/Archives/edgar/data/<CIK without leading zeros>/<accn without dashes>/`
   - Name the statement (Statement of Operations, Balance Sheet, Cash Flows), the line item as the filing words it, and the column (the fiscal year).
   - Remind them about units: tables are usually "in millions" and our data is in raw dollars.
3. **Have the user report the number.** Don't tell them the expected figure in a way that lets them skip looking.
4. **Compare.** They should match exactly after the unit conversion. If not, check:
   - wrong tag (for example `Revenues` vs `RevenueFromContractWithCustomerExcludingAssessedTax`)
   - wrong period (a quarter vs the full year, or `fy` used in place of `end`)
   - a restatement (a later filing shows a different number for the same period)
   - sign conventions (expenses, or cash flow outflows)
5. **Record it.**
   - Match: add a line to the build log, for example `Spot-check: AAPL FY2025 revenue $416,161M matches 10-K (accn ...)`.
   - Mismatch: add the cause to `vault/gotchas.md` and fix the pipeline before moving on.

## Phase 1 target
Five companies, including at least one later delisted or bankrupt, and at least one non-December fiscal year.
