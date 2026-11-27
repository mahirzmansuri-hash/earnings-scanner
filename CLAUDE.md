# Faultline (Earnings Quality Scanner)

## What this is
A public early-warning system for every US public company: it scores manipulation, distress and strength from SEC filings, tracks warning events, and measures how often its warnings came true (point-in-time, dead companies included). A year-plus project meant to be used publicly at scale, possibly a startup. Full plan: `vault/roadmap.md`. For my resume and college apps (finance/accounting major, CS minor).

## About me
High school sophomore. I know basic Python from AP CSP. I'm building this with AI help. I need a broad, interview-level understanding of what we built and how I used AI to build it, not line-by-line detail.

## How to work with me
- Do all lookups and checks yourself (SEC filings, 10-Ks, docs, data). Don't send me links to dig through or ask me to find numbers.
- Teach as you go: treat each step as a short lesson. Say what you checked, what you found (with the real numbers), and why it matters for the project, the finance, or interviews.
- Explain every file you write in plain words, and why you made each choice.
- You write everything, including the score formulas. No coding homework for me.
- Drive the project: at each point, propose the next step: what it is, how it works, how big it gets, what research it needs. Do the research yourself and spend credits where they add real value.
- Aim big: public, high-quality, quantifiable outcomes that could scale. Not a weekend project.
- Before any big step, tell me the plan in a few lines and wait for my OK.
- Keep answers short and direct. No filler. Report progress in short blocks.
- End every session (and before credits run out) with a running summary of everything done from the start: small bullets, very short simple sentences. Save it to `vault/summary.md`.
- No quizzes or hyper-specific questions. At the end of each stage, give me a 5-line plain-English summary I could say in an interview.
- After each session, add an entry to the build log: what we did, the decisions, bugs found, and what's next.
- Timeline: everything done by Jun 1, 2028 (end of junior year), before the summer-2028 internship search (see `vault/roadmap.md`).
- Style: I mostly accept prompts and vibecode small things I think are strong. Offer clear choices with a recommendation; build what I pick; build my own small ideas when they're good, and say so honestly when they're not.

## Memory (read at the start of every session)
- Start with `vault/START-HERE.md`, then the latest entry in `vault/build-log.md`. These files are the project memory; don't rely on chat history.
- End of every session: build log entry, new decisions in `vault/design-notes.md`, new traps in `vault/gotchas.md`, tick phases and checkboxes.

## Project skills (`.claude/skills/`)
- `/end-session`: interview summary, vault updates, Obsidian note, commit
- `/spot-check`: verify a number against the real 10-K
- `/review-my-score`: retired (Claude now writes the scores)

## My Obsidian brain (linked)
- Project note: `/Users/mahir/Documents/Obsidian Vault/Mahir's Second Brain/Areas/Earnings Quality Scanner.md`
- End of every session, update only that note: status, phase checkboxes, and a one-line entry under "Progress log" (date, what we did, what's next). Link to the full build log on GitHub; don't copy it.
- Never edit other notes in my vault without asking. Never copy personal notes from my vault into this repo.

## Stack
- Python 3, DuckDB (database), pandas
- Website: static site, one page per company, free hosting (decided in Stage 3; Streamlit only for internal tools)
- GitHub for code; GitHub Actions for weekly data updates
- Later: scikit-learn (ML layer), LLM text signals

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

## Stages (details in vault/roadmap.md)
- [x] 0. Setup
- [x] 1. EDGAR data pipeline: 15,686 companies, 39M facts, 5/5 spot-checks
- [ ] Stage 1: Score engine + first track record (bankruptcies, restatements), Dec 2026 - Jan 2027
- [ ] Stage 2: Price data + return backtest, Feb - Mar 2027
- [ ] Stage 3: Public website v1, Apr - Jun 2027
- [ ] Stage 4: ML composite + research paper, Jul - Oct 2027
- [ ] Stage 5: Alerts, newsletter, API, growth, Nov 2027 - mid 2028

## App pages
1. Lookup: enter a ticker and get the 3 scores (color coded), red flags in plain English, and 10-year trend charts
2. Screener: filter all companies by score, sector, and size; export to CSV
3. Research: track record and backtest charts; case studies must be 10-K filers (e.g. Sears, Bed Bath & Beyond, GE, Kraft Heinz; SVB as a 'where scores fail' bank case)
4. Methodology: formulas, data sources, limits

## Resume wording
"Built ... using AI-assisted development." Never "coded from scratch."
