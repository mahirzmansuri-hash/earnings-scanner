# Requirements

Acceptance criteria per phase. A phase is done only when every box is ticked.

## Phase 0: Setup
- [x] Python 3.12 venv in `.venv/`, pinned `requirements.txt`
- [x] Folder structure for pipeline, scores, backtest, app, tests
- [x] Project vault (this folder)
- [x] `.env` / `.env.example` for `SEC_USER_AGENT`; `.env` gitignored
- [x] Local git repo initialized, files staged
- [x] First commit
- [x] Pushed to a GitHub repo

## Phase 1 modules (2-3 hours/week, about 2 weeks per module)
Each module has topics. Each topic is a short lesson plus a build step. A module ends with an explain-back quiz and `/end-session`.

### Module 1: EDGAR basics (DONE 2026-11-26)
- [x] 1.1 How SEC data is organized: facts, tags, units
- [x] 1.2 Fetch function: User-Agent, rate limit, caching (`src/pipeline/edgar.py`)
- [x] 1.3 Point-in-time: the filed date vs the period end (look-ahead bias)
- [x] 1.4 Comparative columns and restatements (why values repeat)
- [x] 1.5 Spot-check 1/5: AAPL FY2025 revenue

### Module 2: The full company universe (target ~Dec 13)
- [ ] 2.1 Getting every company: bulk files vs one-by-one API (`companyfacts.zip` returned 503/403 on 2026-11-26; `submissions.zip` is 1.58 GB and works)
- [ ] 2.2 Survivorship bias: what it is and why dead companies matter
- [ ] 2.3 Build the company list: CIK, name, ticker(s), sector (SIC), status, including delisted
- [ ] 2.4 Download facts for every company (resumable, polite)
- [ ] 2.5 When XBRL data starts (~2009-2011) and why the backtest starts in 2012

### Module 3: The database (target ~Dec 27, light over break)
- [ ] 3.1 What a database is; SQL basics
- [ ] 3.2 Table design: companies, facts
- [ ] 3.3 Load the raw JSON into DuckDB
- [ ] 3.4 First queries: one company's history, counts by year

### Module 4: Clean point-in-time data (target ~Jan 17)
- [ ] 4.1 Tag mapping: the same item under different tag names
- [ ] 4.2 Annual vs quarterly facts
- [ ] 4.3 First-filed values for the backtest, latest values for Lookup
- [ ] 4.4 Detecting restatements automatically (a red-flag feature)

### Module 5: Verify and test (target ~Feb 7)
- [ ] 5.1 Spot-checks 2-5 (including one delisted company and one non-December fiscal year)
- [ ] 5.2 pytest tests for the pipeline
- [ ] 5.3 Phase 1 wrap-up

Rough targets: Phase 2 Mar, Phase 3 May, Phase 4 Jul, Phase 5 Sep 2027.

## Phase 1: EDGAR pipeline
- [ ] Download companyfacts JSON for all US filers, under 10 req/sec, User-Agent from `.env`
- [ ] Load into DuckDB with the **filed date** on every value (point-in-time)
- [ ] Delisted and bankrupt companies kept
- [ ] 5 companies spot-checked by hand against their 10-K

## Phase 2: Scores (I write the formulas)
- [ ] Beneish M-Score (8 ratios), Piotroski F-Score (9 tests), Altman Z-Score
- [ ] pytest test for each score against a known hand-calculated example

## Phase 3: Backtest 2012-2025
- [ ] Yearly portfolios by score vs the S&P 500, using only data filed before the formation date
- [ ] Missing prices for delisted stocks flagged clearly

## Phase 4: Streamlit app
- [ ] Lookup, Screener (CSV export), Research, Methodology pages
- [ ] Deployed on Streamlit Community Cloud

## Phase 5: Write-up and ML
- [ ] 2-page write-up
- [ ] ML model vs the classic scores
- [ ] Real users and feedback
