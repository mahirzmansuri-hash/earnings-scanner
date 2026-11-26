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
