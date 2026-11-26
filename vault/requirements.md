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

## Schedule (2-3 hours/week, set 2026-11-25)
| Weeks | Dates | Goal |
|---|---|---|
| 1-2 | Nov 30 - Dec 13 | Explore Apple's EDGAR data; build the fetch function |
| 3-4 | Dec 14 - Dec 27 | Bulk download, including delisted companies |
| 5-6 | Dec 28 - Jan 10 | DuckDB table and loading (winter break is light) |
| 7-8 | Jan 11 - Jan 24 | Map tags; keep the first-filed value (point-in-time) |
| 9-10 | Jan 25 - Feb 7 | Spot-check 5 companies vs 10-K; tests |

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
