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
