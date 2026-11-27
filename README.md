# Faultline

Bankruptcy and accounting-risk scores for US public companies, built from free SEC filings and tested against what actually happened.

**Live site:** https://mahirzmansuri-hash.github.io/earnings-scanner/

## What it does

Faultline reads every annual report (10-K) filed with the SEC since 2009, including the reports of companies that later went bankrupt or stopped filing. For each company and year it computes the three classic forensic accounting scores (Altman Z, Piotroski F, Beneish M) and two machine-learning risk scores: the chance of a bankruptcy filing within two years, and the chance of a restatement notice within two years. Then it checks those scores against real outcomes.

## Main results

Tested out of sample on filings from 2016 to 2023 (25,169 company-years, 539 bankruptcies). For each test year, the model was trained only on companies whose outcome was already known before that year began.

| | Altman Z-Score | Faultline |
|---|---|---|
| Ranking accuracy (AUC; 0.5 = coin flip) | 0.71 | 0.84 |
| Bankruptcies caught by flagging the riskiest 10% of companies | 13% | 53% |
| Share of companies flagged to catch 86% of bankruptcies | 50% | 36% |

Stock outcomes (free approximation from 10-K cover-page market values, companies worth $10M+, 2016-2022): Faultline's riskiest 10% had a median change of -14.8% the following year against +2.9% for its safest half, and 34% of them lost half their value or more against 11%.

Counting companies that stopped filing without being bought as failures too (a "distress exit"), Faultline's AUC is 0.83 against 0.75 for Altman.

For restatements (8-K Item 4.02 notices), Faultline's AUC is 0.74 against 0.52 for the Beneish M-Score. Full tables, method and limits are in [`vault/research/results.md`](vault/research/results.md) and on the site's Track record page.

## How it works

1. **Universe.** SEC's bulk `submissions.zip` lists every filer. Faultline keeps the 15,686 operating companies with a 10-K since 2009, of which 10,349 later stopped filing. Asset-backed trusts and SPACs are dropped; banks and insurers are flagged.
2. **Facts.** Each company's XBRL facts come from SEC's companyfacts API (polite: under 8 requests per second, User-Agent from a private `.env`). About 39 million annual-report values go into DuckDB.
3. **Point in time.** Every value keeps the date it was first filed. Tests use only the original 10-K's numbers, never later corrections. Corrections are kept separately and shown as revisions.
4. **Cleaning.** A tag map turns 21 accounting items into consistent inputs. When one filing reports conflicting revenue figures, the one where revenue minus cost of goods equals gross profit wins. Five companies were checked by hand against their 10-Ks.
5. **Events.** Bankruptcy filings, restatement notices, auditor changes, late filings and amendments come from the same SEC data.
6. **Models.** Gradient-boosted trees (scikit-learn) on 41 point-in-time features, tested walk-forward by year.
7. **Site.** A Python script writes a static site (one page per company) that GitHub Pages serves. A GitHub Actions job rebuilds everything every Sunday.

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
