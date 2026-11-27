# Faultline Roadmap: a high-school research program (Nov 2026 → done by end of junior year, Jun 2028)

## Vision
**Faultline: a free, public early-warning system for every US public company.**
It reads every SEC filing since 2009, scores each company on manipulation, distress and
financial strength, watches for warning events (auditor changes, restatements, late filings,
bankruptcy notices), and **proves how often its warnings came true**, with point-in-time
data and the dead companies included. Long term: alerts, an API and a research paper; possible startup. **Budget: $0.** Free data (SEC), free hosting, free automation (GitHub Actions).

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
### Stage 2: Market value + free return backtest (Feb - Mar 2027)
- **Zero cost.** Market value from the 10-K cover page (`dei:EntityPublicFloat`): reported in
  89,989 of 90,667 10-Ks since 2012 (99%), 12,609 companies incl. 7,410 dead ones. It is the
  market value held by outside investors on the last day of Q2, so it slightly understates
  total market value (insider shares excluded); good enough for Altman X4 and size groups.
- Returns from free sources only (e.g. free daily price downloads for listed stocks); every
  missing delisted price is flagged, never silently dropped. The main track record (Stage 1:
  flagged before bankruptcy / restatement) needs no prices at all.
- **Outcome #2:** classic Altman Z for every company; return comparison where free prices exist,
  with the coverage gap stated openly.
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

## Research framing (what I present to teachers, professors, internship mentors)
**Central question:** Can public SEC filings warn investors *in advance* about bankruptcy and
accounting problems, when tested honestly (point-in-time, dead companies included)?
- **RQ1:** How often did the classic scores (Altman, Beneish, Piotroski) flag bankruptcies and
  restatements 12+ months ahead, 2012-2025, and how many false alarms did they raise?
- **RQ2:** Do warning *events* (auditor changes, late filings, amendments) add early warning?
- **RQ3:** Can a machine-learning composite beat the classic scores out-of-sample?
- **RQ4:** Do flagged companies' stocks underperform (where free price data exists)?
- **RQ5:** Does the *language* of 10-Ks (risk factors, auditor reports) add signal? (AI/NLP)

## Multi-year plan (small increments: 1-2 hour sessions)
| When | Build (stages above) | Research / people | Deliverable |
|---|---|---|---|
| Sophomore yr, winter-spring 2027 | Stages 1-3 | Show results to a teacher at school (econ/math/CS) for a fairness check; no professor outreach yet (hard as a 10th grader). The website's Methodology page + results log become the write-up | Track record #1, website v1 |
| Summer 2027 (internship) | Stage 4 begins | Present Faultline to mentors; ask what practitioners actually check; interview 2-3 practitioners (auditor, analyst, investor) | Interview notes, feedback list |
| Junior yr fall 2027 | Stage 4 (ML composite) | Paper draft (SSRN); optional: email 3-5 professors with the live site + paper | ML results, paper v1 |
| Junior yr spring 2028 | Stage 5 (alerts, newsletter, API, growth) | Final paper; present at school / a competition; final user numbers | **Everything finished by Jun 1, 2028** |
| Summer 2028 | Maintenance only (weekly auto-update) | **Internship search and internship**: Faultline is the portfolio piece | Interviews, internship |
| Fall 2028 | Maintenance only | College applications | Application materials |

**Hard deadline: Jun 1, 2028 (end of junior year).** Site, paper, results, user numbers and
professor feedback all exist before the summer-2028 internship search.

- **Research log:** `vault/build-log.md` (what was built) + `vault/research/` (questions, professor
  emails, interview notes, results). Every result keeps its exact numbers and date.
- **AI disclosure:** keep an honest record of what Claude built vs what I decided; many
  competitions and programs ask. Resume wording stays "Built ... using AI-assisted development."

## Working model
Claude proposes each next step (what, how, how big, research needed), waits for OK on big
steps, then builds it and reports progress in short blocks. Mahir steers, decides, and keeps a
broad interview-level understanding; no quizzes or coding homework. End of each stage: a
5-line plain-English summary Mahir could say in an interview.
