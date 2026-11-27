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

## Next
- Check the first automatic GitHub run, then republish with tonight's changes.
- Pages for banks (classic scores only).
- A share image so links look good when posted.
- Auto-update every week.
