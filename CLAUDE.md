# Earnings Quality Scanner

## What this is
A forensic accounting web app. It scores US public companies on earnings manipulation and financial distress using SEC filings, then backtests whether the scores predicted stock returns. Personal project for my resume and college apps (finance/accounting major, CS minor).

## About me
High school sophomore. I know basic Python from AP CSP. I'm building this with AI help, but I have to understand everything, because I'll explain it in interviews.

## How to work with me
- Explain every file you write in plain words, and why you made each choice.
- I write the score formulas myself (Beneish, Piotroski, Altman). Don't write them for me. Give me the formula and the inputs, then check my code.
- Before any big step, tell me the plan in a few lines and wait for my OK.
- Keep answers short and direct. No filler.
- You write the plumbing (pipeline, database, app). I don't need to be a strong coder, but I must understand it.
- End every session with an explain-back: I explain what we built in my own words, and you correct gaps.
- After each session, add an entry to the build log: what we did, the decisions, bugs found, and what's next.
- Pace: 2-3 hours a week. Schedule is in vault/requirements.md.

## Memory (read at the start of every session)
- Start with `vault/START-HERE.md`, then the latest entry in `vault/build-log.md`. These files are the project memory; don't rely on chat history.
- End of every session: build log entry, new decisions in `vault/design-notes.md`, new traps in `vault/gotchas.md`, tick phases and checkboxes.

## My Obsidian brain (linked)
- Project note: `/Users/mahir/Documents/Obsidian Vault/Mahir's Second Brain/Areas/Earnings Quality Scanner.md`
- End of every session, update only that note: status, phase checkboxes, and a one-line entry under "Progress log" (date, what we did, what's next). Link to the full build log on GitHub; don't copy it.
- Never edit other notes in my vault without asking. Never copy personal notes from my vault into this repo.

## Stack
- Python 3, DuckDB (database), pandas
- Streamlit (web app), hosted on Streamlit Community Cloud
- GitHub for code; GitHub Actions for weekly data updates
- Later: scikit-learn (ML layer)

## Data rules (do not break)
- Financials come from the SEC EDGAR API (companyfacts / XBRL). Send a User-Agent header with my name and email, and stay under 10 requests per second.
- The User-Agent is read from the `SEC_USER_AGENT` environment variable, loaded from a gitignored `.env` file. Never hardcode it, never commit `.env`, and never print it in logs. `.env.example` holds a placeholder only.
- Point-in-time only: use each filing's filed date, not the fiscal period end. A backtest can only use data that was public on that date.
- No survivorship bias: keep companies that were later delisted or went bankrupt. Flag it clearly wherever price data is missing for delisted stocks.
- Spot-check numbers against the actual 10-K before trusting them.

## Scores
- Beneish M-Score: 8 ratios; above -1.78 means a likely manipulator
- Piotroski F-Score: 9 binary tests, scored 0-9
- Altman Z-Score: above 3 is safe, 1.8-3 is the gray zone, below 1.8 is distress

## Phases
- [x] 0. Setup: repo, venv, folder structure, project vault, GitHub
- [ ] 1. EDGAR data pipeline into DuckDB, spot-check 5 companies
- [ ] 2. Scores (I code them, you review)
- [ ] 3. Backtest 2012-2025: yearly portfolios by score vs the S&P 500
- [ ] 4. Streamlit app: Lookup, Screener, Research, Methodology pages, then deploy
- [ ] 5. Write-up (2 pages), ML model vs the classic scores, real users

## App pages
1. Lookup: enter a ticker and get the 3 scores (color coded), red flags in plain English, and 10-year trend charts
2. Screener: filter all companies by score, sector, and size; export to CSV
3. Research: backtest charts and case studies (Wirecard, Luckin Coffee, SVB)
4. Methodology: formulas, data sources, limits

## Resume wording
"Built ... using AI-assisted development." Never "coded from scratch."
