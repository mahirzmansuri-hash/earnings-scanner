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

## Next
- 2-page brief for professors.
- Public website (built and previewed first; goes live only with your OK).
