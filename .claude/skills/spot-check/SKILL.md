---
name: spot-check
description: Verify a number from our EDGAR/DuckDB data against the company's actual 10-K or 10-Q. Use when the user says "spot-check", "verify against the 10-K", "is this number right", or runs /spot-check <ticker or CIK> <item>. Required before trusting any new data source, tag mapping, or score input.
---

# Spot-check a number against the filing

Goal: Claude does the whole check itself, then teaches the result as a short lesson. Don't send the user links to dig through. (User preference, 2026-11-26.)

## Steps
1. **Pull our value.** From the raw companyfacts JSON (`data/raw/companyfacts/`) or DuckDB, get: tag, value, unit, `start`/`end`, form, `filed`, `accn`. If several rows cover the same period, show all of them and point out the earliest `filed`.
2. **Fetch the filing yourself.**
   - Index: `https://www.sec.gov/Archives/edgar/data/<CIK without leading zeros>/<accn without dashes>/index.json`. The main document is the largest `<ticker>-<date>.htm`.
   - Send the User-Agent from `src.config.sec_user_agent()`, and never print it.
   - Strip the HTML, find the statement title (Statement of Operations, Balance Sheet, Cash Flows), and read the line item and the fiscal-year column.
   - Read the units line ("In millions...") and convert. Our data is in raw dollars.
3. **Teach it.** Show a small table (our value vs the filing), plus 1-2 things worth noticing in that statement (what makes up the number, a trend, a link to a score input).
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
