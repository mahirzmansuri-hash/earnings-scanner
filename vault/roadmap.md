# Faultline Roadmap (2026-11-26 → mid-2028)

## Vision
**Faultline: a free, public early-warning system for every US public company.**
It reads every SEC filing since 2009, scores each company on manipulation, distress and
financial strength, watches for warning events (auditor changes, restatements, late filings,
bankruptcy notices), and **proves how often its warnings came true**, with point-in-time
data and the dead companies included. Long term: alerts, an API and a research paper; possible startup.

## Why it can matter (positioning)
- The classic scores already exist behind paywalls: GuruFocus shows M/F/Z scores on plans of
  roughly $424-$1,400/yr (third-party reviews, 2026). Professional red-flag tools (Audit Analytics,
  AlphaSense) are institutional-priced.
- None of them publish a **measured track record** ("we flagged X% of bankruptcies 12 months ahead")
  that includes the dead companies. That track record is Faultline's core asset.
- Legal footing: impersonal, general-circulation ratings are covered by the "publisher's exclusion"
  (Lowe v. SEC, 1985; reaffirmed for Seeking Alpha in 2024). Rules for us: no personalized advice,
  regular publication, clear "not investment advice" disclaimer. Any company/payments → through a parent.

## Measured so far (data already on disk)
- 15,686 companies (10,349 dead or acquired), 39.0M facts, 116,107 company-years.
- Outcome labels in submissions.zip since 2009: bankruptcy 8-Ks (Item 1.03) 1,144 companies;
  non-reliance restatements (Item 4.02) 2,904; auditor changes (4.01) 7,509; late 10-Ks (NT 10-K) 6,774;
  10-K/A amendments 8,860.

## Stages
### Stage 1: Score engine + first track record (Dec 2026 - Jan 2027)
- Beneish M, Piotroski F, Altman Z (and Z'' which needs no stock price) for all 116k company-years.
- Event table from submissions: bankruptcy, restatement, auditor change, late filing, with filing dates.
- **Outcome #1:** "Of the N companies that filed for bankruptcy, X% were in Altman's distress zone
  12+ months earlier; false alarm rate Y%." Same for Beneish vs restatements. No paid data needed.
### Stage 2: Market data + return backtest (Feb - Mar 2027)
- Pick a survivorship-free price source (candidates: EODHD ~$199/yr historical incl. delisted;
  Sharadar via Nasdaq Data Link; Norgate ~$630/yr, Windows-only). Needs a budget decision.
- Classic Z with market value; yearly portfolios by score vs the S&P 500, 2012-2025.
- **Outcome #2:** return spread of flagged vs clean companies, with delisting returns handled.
### Stage 3: Public website v1 (Apr - Jun 2027)
- Static site, one page per company (~13k pages, indexable by Google), screener, methodology,
  research page with the track record. Weekly auto-update with GitHub Actions. Free hosting.
- Research-report design system (tokens in design-notes). Analytics from day one.
- **Outcome #3:** launch; first users; traffic numbers.
### Stage 4: Faultline Composite (ML) + research paper (Jul - Oct 2027)
- Train a model on the event labels (plus SEC enforcement releases (AAERs) as fraud labels),
  strictly out-of-sample by year. Compare against the three classic scores.
- Write it up as a paper (SSRN) and a 2-page summary.
- **Outcome #4:** "Composite catches X% of bankruptcies/restatements vs Y% for Altman/Beneish."
### Stage 5: Product + growth (Nov 2027 - mid 2028)
- Alerts when a company's flags change (new 10-K / 8-K), watchlists, weekly "Faultline Report"
  newsletter, public API, text signals from 10-K risk factors and auditor reports (LLM).
- Distribution: SEO pages, investing communities, school investment clubs, LinkedIn.
- Startup tests: who would pay (alerts/API), pricing experiments, competitions.
- **Outcome #5:** monthly users, newsletter subscribers, paper downloads.

## Working model
Claude proposes each next step (what, how, how big, research needed), waits for OK on big
steps, then builds it and reports progress in short blocks. Mahir steers, decides, and keeps a
broad interview-level understanding; no quizzes or coding homework. End of each stage: a
5-line plain-English summary Mahir could say in an interview.
