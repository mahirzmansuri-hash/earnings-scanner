# Build Log

One entry per session, newest at the bottom. Each entry must be enough to resume with no chat history.

```
## YYYY-MM-DD: Session title
- Did:
- Decisions: (details in [[design-notes]])
- Bugs / gotchas: (details in [[gotchas]])
- State: (what works, what's uncommitted)
- Next:
```

## 2026-11-25: Phase 0 setup
- **Did:** installed Python 3.12.10 and its SSL certificates; created the venv and pinned requirements; made the folder structure, `src/config.py`, `.env`/`.env.example`, this vault, `.gitignore`, and a git repo (files staged).
- **Decisions:** Python 3.12, pinned deps, DuckDB, User-Agent kept in `.env`, raw data not committed. See [[design-notes]].
- **Bugs / gotchas:** SSL certificate error, then a 403 from SEC without a User-Agent (expected). See [[gotchas]].
- **State:** Phase 0 done. Pushed to github.com/mahirzmansuri-hash/earnings-scanner. Commits use my GitHub noreply email. The token is in macOS Keychain. `.env` still has the placeholder.
- **Next:** put my real name and email in `.env`; decide hours per week; plan the weeks for Phase 1.

## 2026-11-26: Module 1 done: EDGAR basics
- **Did:** wrote `src/pipeline/edgar.py` (`fetch_company_facts`: User-Agent from `.env`, rate limit of 8 req/sec, caches raw JSON in `data/raw/companyfacts/`). Fetched Apple (CIK 320193): 4.3 MB, 512 us-gaap tags.
- **Spot-check 1/5:** AAPL FY2025 revenue. EDGAR `RevenueFromContractWithCustomerExcludingAssessedTax` = $416,161,000,000 (period 2024-09-29 to 2025-09-27, first filed 2025-10-31, accn 0000320193-25-000079). The 10-K Statement of Operations shows "Total net sales" of 416,161 (in millions). **Match.**
- **Bugs / gotchas:** `fy` describes the filing, not the period; the same value repeats in later 10-Ks. See [[gotchas]].
- **Decisions:** Claude does all lookups and checks itself and teaches the results as lessons (CLAUDE.md and `/spot-check` updated).
- **Decisions:** the schedule changed from weeks to modules with topics (see [[requirements]]).
- **Explain-back quiz:** Q4 (restatement scenario) correct. Gaps fixed: a fact is *one number* with tag, value, unit, period, **filed** date and accn (I'd named tags); look-ahead bias is about information **not being public yet**, not about numbers changing; values repeat because each 10-K reprints 2 prior years; the backtest uses **first-filed**, Lookup uses **latest-filed**.
- **Found:** `companyfacts.zip` bulk file returned 503 then 403 (2026-11-26); `submissions.zip` (1.58 GB) is fine. Investigate in Module 2.1.
- **State:** committed and pushed. Spot-checks done: 1/5.
- **Next:** Module 2, the full company universe. Start with 2.1 (bulk vs one-by-one) and 2.2 (survivorship bias).

## 2026-11-26 (cont.): Modules 2-4 and spot-checks 2-5
- **Did:** downloaded `submissions.zip` (1.58 GB) with `download_bulk_file()`; built the company universe (`src/pipeline/universe.py`): 15,686 companies with a 10-K since 2009, minus bond trusts (6189), SPACs (6770) and no-SIC entities; banks etc. flagged `is_financial`; 5,337 active, 10,349 inactive. Downloaded companyfacts for all of them (gzip, threaded, resumable, 8 req/s): 13,480 with data, 2,206 none (404), 0 failed, 1.2 GB. Loaded DuckDB (`load_db.py`): 39.0M annual-report facts, 793 MB. Built `tag_map.py` (20 concepts) and `annual.py`: 1.63M clean annual values, 116,107 company-years, first-filed + latest + `revised` flag. 8 pytest tests pass.
- **Measured:** 64% of operating companies have no ticker today (survivorship); 500-900 companies stop filing every year; 10-Ks with XBRL: 0.4% (2009), 6.7% (2010), 21.7% (2011), 91.1% (2012); 2,482 of the companies with no XBRL data died 2009-2011. Core inputs (revenue, assets, net income, CFO) present for 73% (2012) to 87% (2024) of non-financial company-years; Beneish's extra inputs only ~55-60%. Identity checks: revenue - COGS = GP passes 97.5%; assets = liabilities + equity (2%) passes 89.6%.
- **Spot-check 2/5:** Sears Holdings (dead) FY2017 revenue $16,702M = 10-K "Total revenues" 16,702 (accn 0001310067-18-000006, filed 2018-03-23). 53-week year (370 days). The $4,376M fact in the same filing is Q4 (97 days), correctly excluded. **Match.**
- **Spot-check 3/5:** General Mills (May FY) FY2023 net sales $20,094.2M = 10-K Consolidated Statements of Earnings 20,094.2 (accn 0001193125-23-177500). **Match** (after the revenue-referee fix).
- **Spot-check 4/5:** SVB Financial (bank, failed) total assets 2022-12-31 $211,793M = 10-K balance sheet 211,793 (accn 0000719739-23-000021). **Match.**
- **Spot-check 5/5:** Conagra FY2015 revenue first-filed $15,832.4M = original 10-K net sales 15,832.4 (accn 0001628280-15-005333). Latest is $9,034M (recast after the Lamb Weston spin-off). **Match**; shows why the backtest uses first-filed.
- **Bugs / gotchas:** revenue tags disagree in 14.2% of filings (General Mills, Hasbro) -> identity referee then largest; revised != restated; bankrupt companies get renamed (use CIK); DuckDB 2.0 removed `.fetchone()` on `con.sql()`. See [[gotchas]].
- **Decisions:** name **Faultline**, research-report look, signal-cyan pop; gzip cache; DB keeps annual forms only; first-filed picked by filing date before tag. See [[design-notes]].
- **State:** all committed and pushed except this entry. Phase 1 acceptance criteria met. Explain-back quiz for Modules 2-5 not done yet.
- **Next:** explain-back quiz (Modules 2-5); then Phase 2: Mahir writes the scores (`/review-my-score`), starting with Altman Z. Open items: 4.4 real restatement detection; improve Beneish input coverage (~55-60%); price data for Altman X4 and the backtest.
