# Faultline: everything so far (simple version)

## Setup (Nov 25)
- Installed Python 3.12 on your Mac.
- Made a project folder with a clean structure.
- Hid your name and email in a secret `.env` file. SEC requires it.
- Put the code on GitHub.
- Linked the project to your Obsidian notes.

## Learning the SEC data (Nov 26)
- SEC gives every company's numbers for free, as "facts."
- A fact = one number + what it is + its date + **when it was published**.
- Built a tool to download a company's facts politely (max 8 requests per second).
- Checked Apple's revenue ($416.2B) against its real 10-K. It matched.
- Learned "look-ahead bias": you can't use numbers before they were public.

## Every company, including dead ones (Nov 26)
- Downloaded SEC's list of every filer (1.6 GB, about 1 million entities).
- Kept real companies with an annual report since 2009: **15,686**.
- **10,349 of them are dead or bought out.** Most free tools leave those out.
- Leaving them out makes strategies look too good. That's "survivorship bias."
- Bankrupt companies get renamed (RadioShack = "RS Legacy Corp"), so we track by ID number.

## Downloading and storing it all (Nov 26)
- Downloaded every company's facts. Zipped, it's 1.2 GB instead of 27 GB.
- Put 39 million numbers into a fast database (DuckDB).
- Found out XBRL data really starts in 2012 (91% of reports). That's why we start there.

## Cleaning the numbers (Nov 26)
- Companies use different names for the same thing (like "revenue").
- Built a map that translates 20 items.
- Kept two versions of each number: the original, and the corrected one.
- The original is for testing the past. The corrected one is for today's website.
- Fixed a bug: General Mills showed $2B revenue instead of $20B.
- Fix: check that revenue − costs = gross profit.
- Checked 5 companies against real 10-Ks (Apple, Sears, General Mills, SVB, Conagra). All matched.

## Name and look (Nov 26)
- Named it **Faultline**.
- Look: clean research-report style, white and navy, one small cyan highlight.
- Rule: no AI-looking gradients, glows or emoji.

## Bigger plan (Nov 26-27)
- Turned it into a research project, done by **Jun 1, 2028** (end of junior year).
- Budget: **$0.** Everything uses free data and free tools.
- Market value comes free from the 10-K cover page.
- Plan: scores → smarter model → public website → research paper → users.

## Scores and first results (Nov 27)
- Built the 3 famous scores for 116,121 company-years.
- **Altman Z** = bankruptcy risk. **Piotroski F** = strength. **Beneish M** = fake-numbers risk.
- Found every bankruptcy (1,144 companies) and restatement (2,904) in SEC filings.
- Tested: did the scores warn before these happened?
- Altman warned before 83% of bankruptcies. But it flags half of all companies.
- Beneish warned before only 26% of restatements.
- Sears was flagged 3.5 years before it went bankrupt.

## Faultline's own model (Nov 27)
- Built a machine-learning model that reads 41 clues per company.
- Tested it only on years it never trained on, so it's fair.
- **Flag the riskiest 10% → catches 52% of bankruptcies.** Altman: 13%.
- Same catch rate as Altman with 26% fewer false alarms.
- A second model for accounting problems beats Beneish (0.74 vs 0.52 ranking score).
- Finding: auditor changes and late filings add almost nothing on top of the financials.

## Website v1 (Nov 27)
- Made sure every risk score is fair: each year is scored by a model that never saw that year's outcome.
- Built the website on your Mac. It's not public yet.
- **7,693 company pages.** Each shows risk, the 3 scores, red flags in plain words, and a chart.
- Home page shows recent bankruptcies and whether Faultline saw them coming.
- **62 of 87 recent bankruptcies were already in Faultline's riskiest 20%,** 1-2 years early.
- Misses are shown too, so it's honest.
- A screener filters all companies and downloads a spreadsheet.
- Pages for the track record, methodology and about.
- Designed to not look AI-made: no flashy hero, no fake reviews, real numbers with sources.
- Works on phones.

## Publishing (Nov 27)
- Put your first name (Mahir) on the About page. No last name, to keep a minor safer online.
- Uploaded the finished site to GitHub (a branch called gh-pages, 7,700 files).
- You turned on GitHub Pages. **The site is live:** https://mahirzmansuri-hash.github.io/earnings-scanner/
- Checked it live: every page loads, search works (Sears, Apple), screener loads 3,911 active companies.
- Added a "Loading" message so the screener doesn't look broken on slow phones.

## Weekly auto-update (Nov 27)
- Wrote one command that rebuilds everything: data, scores, models, website (4 minutes).
- It only re-downloads companies that filed something new.
- Set up GitHub to run it every Sunday for free, even when your Mac is off.
- Waiting on you: allow your GitHub token to change workflows, and add your SEC name/email as a secret.

## Overnight work (Nov 27, while you slept)
- Wrote a **README** for GitHub: what Faultline is, results, how to run it.
- **Robustness:** Faultline beats Altman in all 8 test years and for small, mid and big companies.
- Found that size matters most, partly because tiny companies quietly stop filing instead of declaring bankruptcy.
- So added a second test: "failed" = bankruptcy OR stopped filing without being bought.
- Faultline still wins there: **0.83 vs 0.75**.
- Fixed a subtle bug: results changed slightly on every run (duplicate rows). Now identical every time.
- Final main result: riskiest 10% catches **53%** of bankruptcies vs Altman's **13%** (AUC 0.85 vs 0.71).
- Wrote the **research paper draft** (`docs/paper.md`), linked from the site.
- Made a **share image** so links look good on LinkedIn or in texts, plus a small tab icon.
- Tests went from 16 to **24**, all passing.

## Stage 2: stock outcomes, free (Nov 27, second night)
- You picked option A. Built it: uses the market value printed on each 10-K cover page.
- Measured what happened to each stock the year after its score came out. No peeking.
- Bankrupt companies count as -100%. Buyouts are left out.
- Only companies worth $10M+ (20,648 company-years, 2016-2022).
- **Riskiest 10%: typical stock fell 13.6%.** Safest half: rose 2.9%.
- **34% of the riskiest lost half their value or more.** Only 11% of the safest did.
- **11% of the riskiest were wiped out**, vs 1% of the safest.
- But the average wasn't lower: a few risky stocks shot up like lottery tickets.
- Worse in 5 of 7 years. 2020's big rebound was the exception.
- Added it to the website, paper and README. Stage 2 is done.

## New filings page (Nov 27)
- A new page lists every 10-K filed in the last 30 days with its fresh score.
- It shows the biggest jumps in risk since each company's last report.
- Gives people a reason to come back every week.

## Fairer risk percentages (Nov 27)
- The % shown on each company page was too low for middle-risk companies.
- Fixed it using only past years, so no peeking. Now "10% risk" really means about 10% failed.
- Rankings didn't change, so every result above stays the same.

## 10-K text signals (Nov 27)
- Used SEC's free full-text search. No downloading of whole reports.
- Found every 10-K with 5 warning phrases, like "substantial doubt" (going concern).
- About 36,700 filings had the going-concern phrase.
- Companies with it went bankrupt twice as often.
- But adding the phrases to the model changed nothing. The numbers already say it.
- That's a real research answer: simple warning phrases don't add early warning.
- Paper, README and results updated.

## Paper PDF (Nov 27)
- Turned the paper into a clean 6-page PDF.
- Added Figure 1: how many bankruptcies each score catches as you flag more companies.
- Faultline's line rises much faster than Altman's.
- Fixed a few numbers and the intro (now 5 research questions).
- The PDF is on the website and in the GitHub README.

## Next
- Optional for you: click Run workflow once on GitHub to confirm the fixed weekly update (or wait for Sunday).
- Optional for you: submit the sitemap to Google Search Console.
- Show the PDF to a teacher for feedback.

## Tougher benchmarks (Nov 27, evening)
- Weekly auto-update confirmed working.
- Paper PDF is live on the site.
- Tested two more classic bankruptcy formulas: Ohlson (1980) and Zmijewski (1984).
- Faultline beats all three classics (0.85 vs 0.71 / 0.72 / 0.74).
- Tried adding trends and industry comparisons. No gain, so we kept the simpler model.
- Added both results to the site, paper and README.

## Why-this-score (Nov 27, evening)
- Every company page now explains its risk.
- It shows which areas push risk up or down: debt, cash flow, profits, and more.
- How: swap one area for a typical company's numbers and re-score.
- If risk drops, that area was the problem.
- Example: Sears was pushed up by heavy debt and a 25% sales drop.
- Added tests. 26 tests pass.

## SEC fraud cases (Nov 27, night)
- Downloaded the SEC's full list of accounting-fraud cases (3,324 releases).
- Matched them to our companies by name.
- Dropped bribery cases and paperwork orders.
- Read each case to find which years were faked.
- Built a fraud model. Fraud is much harder than bankruptcy.
- It beats Beneish a little (0.63 vs 0.58), but it's too weak to accuse named companies.
- So company pages list SEC cases as facts, with no fraud score.
- Paper now has 6 research questions (7 pages).

## Quarterly 10-Q updates (Nov 27, night)
- Read every 10-Q from files we already had. No new downloads.
- Built a full-year view at each 10-Q (trailing twelve months).
- Checked Apple's numbers against the real 10-Q. Exact match.
- Fresh 10-Q scores beat the old 10-K score (0.83 vs 0.81).
- They warned 56 more bankrupt companies, about 45 days earlier.
- Company pages now show the latest 10-Q update.
- Fixed results that changed slightly between runs (random tie-breaks).
- Paper now has 7 research questions.

## Alerts (Stage 5 starts, Nov 27, night)
- New Alerts page: what changed in the last 90 days.
- Alerts fire when risk jumps, a company enters the riskiest 5%, or a warning filing appears.
- Anyone can star companies (watchlist, saved in their browser).
- Every company has its own RSS feed. There is a main feed too.
- A weekly digest page is written automatically. It's our future newsletter.
- Example: this week Car-Mart went bankrupt; we had it riskier than 90% of companies.
- Email sending needs a free account from you (next).

## Digest email (Nov 27, night)
- Picked Buttondown. Free up to 100 subscribers.
- New code emails the weekly digest.
- It makes a draft first. You press send.
- Later it can send on its own.
- Each company in the email links to its page.
- A sign-up box appears once your account exists.
- Needs you: make the account, add the API key to GitHub.
