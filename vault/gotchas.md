# Gotchas

Traps that cost time once. Format: **symptom** → cause → fix.

## Setup
- **`CERTIFICATE_VERIFY_FAILED` on any HTTPS request** → the python.org installer doesn't set up SSL certificates → run `/Applications/Python 3.12/Install Certificates.command` (done 2026-11-25).
- **`HTTP Error 403` from sec.gov** → no User-Agent header. SEC blocks anonymous requests → send `SEC_USER_AGENT` from `.env`.
- **`python3` is 3.9** → that's Apple's built-in version → always use `.venv/bin/python` or activate the venv.

## Data (known in advance; confirm in Phase 1)
- **Look-ahead bias** → using the fiscal period end and not the `filed` date → always filter by `filed`.
- **Restated numbers** → companyfacts can hold several values for the same period (original plus amendments) → keep the first one filed for point-in-time work.
- **`fy` column doesn't match the period** (confirmed 2026-11-25, Apple) → `fy`/`fp` describe the *filing*, so FY2025 revenue repeated in the FY2026 10-K shows `fy=2026` → identify a period by `start`/`end`, never by `fy`.
- **Same value appears in several filings** (confirmed 2026-11-25) → each 10-K repeats prior years for comparison → for point-in-time, keep the row with the earliest `filed`.
- **Survivorship bias** → building the stock universe from today's tickers → build it from every company that filed in each year.
- **`companyfacts.zip` returns 503/403** (2026-11-26) → SEC may be throttling or restricting the bulk file → fallback: per-company API at 8 req/sec (~20-40 min for every filer). Investigate in Module 2.1.
- **Bankrupt companies get renamed** (confirmed 2026-11-26) → after bankruptcy the shell takes a new name: RadioShack = "RS Legacy Corp", Bed Bath & Beyond = "20230930-DK-Butterfly-1, Inc.", JCPenney = "Old COPPER Company, Inc." → always identify companies by CIK, never by name or ticker.
- **Revenue tags disagree inside one filing** (measured 2026-11-26: 14.2% of filing-years) → e.g. General Mills FY2023: `Revenues` = $1.96B (a component) vs `RevenueFromContract...` = $20.09B (the total); Hasbro FY2022 (2025 filing): `Revenues` = $6.67B is wrong, $5.86B right → pick by the identity revenue − COGS = gross profit in the same filing, then largest; never trust one tag blindly.
- **Revised ≠ restated** → a later filing can change an old number because of an error (restatement, red flag) or because of a rule change or divestiture (recast, normal; e.g. Conagra after the Lamb Weston spin-off) → our `revised` flag can't tell them apart; use 10-K/A and 8-K Item 4.02 to find real restatements.
- **DuckDB 2.0: `con.sql(...).fetchone()` is gone** → use `con.execute(...).fetchone()`.
- **DuckDB reads its own table before your DataFrame** (2026-11-27) → `CREATE OR REPLACE TABLE scores AS SELECT * FROM scores` silently rebuilt the table from its OLD self, not the new pandas `scores` → always `con.register("scores_df", df)` under a distinct name.
- **Row dated by the latest input is late** (2026-11-27) → a value first appearing in a later filing (e.g. COGS) pushed a whole year's date forward (Sears FY2015 dated 2018) → date rows by the original 10-K and drop inputs that weren't in it.
- **DuckDB 2.0: unread results block the connection** (2026-11-27) → `ResourceInUseException` after a `fetchone()` → open a fresh connection per pipeline step (or use `con.cursor()`).
- **Model results changed between identical runs** (2026-11-27) → (1) SQL without ORDER BY returns rows in varying order, which changes the model's internal validation split; (2) a fiscal-year change made the prior-year join match twice (194 duplicate rows) → always ORDER BY and dedupe joins with QUALIFY.
- **CI publish failed with exit 126** (2026-11-27) → script shebang was `#!/bin/zsh`; GitHub's Ubuntu runners have no zsh → use `#!/usr/bin/env bash` and call `bash script.sh` in workflows. Also: `actions/cache` only saves when the job succeeds, so a late failure threw away a 45-minute download → use `cache/restore` + `cache/save` with `if: always()`.

## AAER list mixes fraud with bribery and procedure
- **Symptom:** 3M, HP, Honeywell, Barclays "fraud" cases. **Cause:** FCPA books-and-records cases are AAERs too; so are Rule 12b-25 late-notice and procedural orders. **Fix:** classify each release from its text before using it as a label.

## Respondent names split on commas
- **Symptom:** "Latch, Inc." became "Latch" + "Inc.". **Fix:** join ", Inc/LLC/Ltd/Corp" before splitting; strip EDGAR state tags like /DE/ from company names.

## DuckDB arg_min/arg_max ties are random
- **Symptom:** 10-Q results changed slightly between identical runs. **Cause:** ties in arg_min(value, filed) etc. are resolved by parallel scan order; pandas drop_duplicates on unsorted SQL output too. **Fix:** order key as a struct with tie-breakers, e.g. arg_min(value, (filed, accn)); sort before drop_duplicates; verify with an md5 of two builds.

## 10-Q flows are year-to-date
- **Fix:** TTM = YTD now + last full year - same YTD last year; Q4 is never in a 10-Q.

## SEC 8-K item tags can be wrong
- **Symptom:** Granite Construction (healthy) appeared as a bankruptcy on Receipts.
- **Cause:** our events come from the item tags in SEC's filing index; the filer tagged Item 1.03 on an 8-K about a note exchange. SEC's full-submission .txt header repeats the tag, so text checks must skip it.
- **Fix:** `src/pipeline/verify_bk.py` reads recent bankruptcy 8-Ks (main document first) and drops ones that never mention bankruptcy. Older training labels are not checked yet (rare; would need ~1,000 fetches).
