# Faultline

Bankruptcy and accounting-risk scores for US public companies, built from free SEC filings and tested against what actually happened.

**Live site:** https://mahirzmansuri-hash.github.io/earnings-scanner/

## What it does

Faultline reads every annual report (10-K) filed with the SEC since 2009, including the reports of companies that later went bankrupt or stopped filing. For each company and year it computes the three classic forensic accounting scores (Altman Z, Piotroski F, Beneish M) and two machine-learning risk scores: the chance of a bankruptcy filing within two years, and the chance of a restatement notice within two years. Then it checks those scores against real outcomes. Since 2017, 69% of companies that went bankrupt were in its riskiest 10% at their last score before the filing. Each company page also explains its score: which areas (debt, cash flow, profits, warning signs and so on) push its bankruptcy risk up or down, measured by re-scoring the filing with each area set to typical values.

## Main results

Tested out of sample on filings from 2016 to 2023 (25,195 company-years, 539 bankruptcies). For each test year, the model was trained only on companies whose outcome was already known before that year began.

| | Altman Z (1968) | Ohlson O (1980) | Zmijewski (1984) | Faultline |
|---|---|---|---|---|
| Ranking accuracy (AUC; 0.5 = coin flip) | 0.71 | 0.72 | 0.74 | 0.85 |
| Bankruptcies caught by flagging the riskiest 10% of companies | 13% | 11% | 13% | 52% |
| Share of companies flagged to catch 86% of bankruptcies | 50% | | | 35% |

Quarterly updates (10-Qs, 2016-2023, 99,584 filing dates): scoring each 10-Q with trailing-twelve-month numbers raised the AUC from 0.81 (score from the last 10-K) to 0.82, caught 51% of bankruptcies in the riskiest 10% instead of 43%, and warned 324 of 464 later-bankrupt companies instead of 263, with about the same lead time (median 512 vs 507 days before the filing).

Accounting fraud (SEC enforcement releases, fiscal 2013-2019, 266 misstated company-years): much harder. Trained only on cases the SEC had already announced, the model reached an AUC of 0.63 against 0.58 for the Beneish M-Score (0.69 with hindsight). Company pages list SEC cases as facts; there is no fraud score.

Stock outcomes (free approximation from 10-K cover-page market values, companies worth $10M+, 2016-2022): Faultline's riskiest 10% had a median change of -12.4% the following year against +2.4% for its safest half, and 32% of them lost half their value or more against 11%.

Counting companies that stopped filing without being bought as failures too (a "distress exit"), Faultline's AUC is 0.84 against 0.75 for Altman.

Warning phrases in the 10-K text (going-concern doubt, material weaknesses, restatements; found with SEC full-text search) did not improve either model once the financial data was in.

For restatements (8-K Item 4.02 notices), Faultline's AUC is 0.74 against 0.52 for the Beneish M-Score. Full write-up: [research paper (PDF)](docs/Faultline-paper.pdf). Tables, method and limits are also in [`vault/research/results.md`](vault/research/results.md) and on the site's Track record page.

## How it works

1. **Universe.** SEC's bulk `submissions.zip` lists every filer. Faultline keeps the 15,686 operating companies with a 10-K since 2009, of which 10,349 later stopped filing. Asset-backed trusts and SPACs are dropped; banks and insurers are flagged.
2. **Facts.** Each company's XBRL facts come from SEC's companyfacts API (polite: under 8 requests per second, User-Agent from a private `.env`). About 39 million annual-report values go into DuckDB.
3. **Point in time.** Every value keeps the date it was first filed. Tests use only the original 10-K's numbers, never later corrections. Corrections are kept separately and shown as revisions.
4. **Cleaning.** A tag map turns 21 accounting items into consistent inputs. When one filing reports conflicting revenue figures, the one where revenue minus cost of goods equals gross profit wins. Five companies were checked by hand against their 10-Ks.
5. **Events.** Bankruptcy filings, restatement notices, auditor changes, late filings and amendments come from the same SEC data. Filer item tags can be wrong, so every bankruptcy 8-K's text is read to confirm it is about a bankruptcy.
6. **Text.** SEC full-text search flags 10-Ks containing five warning phrases, with no document downloads.
7. **Models.** Gradient-boosted trees (scikit-learn) on 46 point-in-time features, tested walk-forward by year. Percentiles ("riskier than X% of filers") compare each filing only with filings from the 365 days before it.
8. **Site.** A Python script writes a static site (one page per company) that GitHub Pages serves. A GitHub Actions job rebuilds everything every Sunday.
9. **Extras.** Alerts with RSS feeds for every company, a weekly email digest, a Receipts page (every recent bankruptcy and the score before it), five case studies (Sears, Bed Bath & Beyond, GE, Kraft Heinz, SVB) and a [free JSON API](https://mahirzmansuri-hash.github.io/earnings-scanner/api/index.html) with every score, no key needed.

## Run it yourself

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env      # then put your name and email in it (SEC requires this)
.venv/bin/python -m src.pipeline.update   # downloads data, rebuilds scores, models and site (~45 min first time)
.venv/bin/python -m pytest
```

## Repository map

| Path | What it is |
|---|---|
| `src/pipeline/` | SEC downloads, company universe, DuckDB load, clean annual values, events, weekly update |
| `src/scores/` | Altman, Piotroski and Beneish scores |
| `src/model/` | Bankruptcy and restatement models, ablation, live scoring |
| `src/backtest/` | Track record of the classic scores |
| `src/web/` | Static site generator |
| `tests/` | pytest tests |
| `vault/` | Project notes: roadmap, design decisions, gotchas, build log, research results |

## Limits

Only formal bankruptcy filings count as bankruptcies, so distressed sales and out-of-court restructurings are scored as misses. Financial companies are not scored. A score ranks a company's filings against the filings of companies that later failed or restated; it is not a forecast for any single company.

Faultline is research, not investment advice.

## About

An independent research project by Mahir, a high school student, built with AI-assisted development (Claude Code). Data: SEC EDGAR, which is free public data.
