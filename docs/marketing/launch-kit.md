# Faultline launch kit (online-first)

Drafts for Mahir to edit and post in his own words. Claude never posts. Numbers are from the data as of 2026-11-25;
re-run `scripts/make_oc_chart.py` before posting so the chart and numbers are current.

**Order:** 1 teacher message → 2 r/SecurityAnalysis → 3 r/dataisbeautiful → 4 Show HN. One per week.
After each post, reply to comments for the first 2 hours, then paste the useful criticism into the build log.

**Numbers you can quote (and where they come from):**
| Claim | Number | Source |
|---|---|---|
| Recent receipts | 30 of 39 companies that filed for bankruptcy in the last 12 months were already in the riskiest 10% | Receipts page |
| Full history | 338 of 475 (71%) bankruptcies since 2017 were in the riskiest 10% at their last score; 4% were in the safer half | `oc-bankruptcy-deciles.png` |
| Warning time | median 327 days from first entering the riskiest 10% to the filing (looks back at most 13 months) | same |
| Vs. textbook | AUC 0.85 vs Altman Z 0.71, Ohlson 0.72, Zmijewski 0.74 (bankruptcy within 2 years of each 10-K, 2016-2023 test years) | Track record page |
| Honest failure | fraud prediction only AUC 0.63, so the site shows SEC cases as facts, no fraud score | Track record page |

Two different "riskiest 10%" numbers exist, so don't mix them up: **53%** = of all bankruptcies within 2 years of a 10-K, how many
that 10-K's score put in the riskiest 10% (the formal test). **71%** = the *last* score before each bankruptcy (closer to the event, so higher).

---

## 1. Message to a finance/business teacher or investing-club leader (email or school message)

> Subject: Could you look at a finance project I built?
>
> Hi [name],
>
> I've been building a website called Faultline that scores every US public company for bankruptcy risk using SEC filings,
> then checks how often the warnings came true. For example, 30 of the 39 companies that went bankrupt this year were already
> in its riskiest 10% beforehand.
>
> I built it with AI-assisted development, and I want honest feedback from someone who knows finance. Would you be willing to spend
> 10 minutes on it? The best starting page is this one:
> https://mahirzmansuri-hash.github.io/earnings-scanner/receipts.html
>
> A few questions I'd love your take on:
> 1. Is anything confusing or misleading?
> 2. Does the track record look trustworthy to you? What would make it more convincing?
> 3. Who do you think would actually use this?
>
> If it seems useful for the club, I'd be glad to share it there too.
>
> Thank you,
> Mahir

---

## 2. r/SecurityAnalysis (read the sidebar rules first; some subs want a text post, not a link)

**Title:** I backtested bankruptcy prediction on every US 10-K since 2016, including companies that died. Here's what worked and what didn't

> I built a free site that scores US public companies for bankruptcy risk from SEC XBRL data, and I tried to test it the way
> I'd want a model tested: point-in-time (only data public on each filing date), walk-forward (each year's model trained only on
> earlier outcomes), and with dead companies kept in.
>
> **Results (test years 2016-2023, ~25,000 company-years, 539 bankruptcies within 2 years of a 10-K):**
> - Ranking accuracy (AUC): 0.85, vs 0.71 for Altman Z, 0.72 Ohlson O, 0.74 Zmijewski on the same rows.
> - The riskiest 10% of filers contained 53% of later bankruptcies (Altman Z's riskiest 10%: 13%).
> - At the last score before the filing, 338 of 475 bankruptcies since 2017 (71%) were in the riskiest 10%.
> - Fresh 10-Q numbers (trailing twelve months) help, most when the last 10-K is old: AUC 0.85 → 0.88 when the 10-K is 8+ months old.
>
> **What didn't work:**
> - Fraud. Using SEC enforcement cases (AAERs) as labels, the best model got AUC 0.63 in real time (Beneish M-Score: 0.58).
>   The SEC takes a median of ~6 years to announce a case, so there's little to learn from. I don't publish a fraud score.
> - Banks and insurers aren't scored (balance sheets don't fit these models). SVB is on the site as a "where scores fail" case.
> - Adding trend and industry features gave no gain (0.847 both ways).
>
> **Biggest data lesson:** SEC's 8-K item tags are sometimes wrong. A healthy company's note exchange was tagged as a bankruptcy
> filing, so the pipeline now reads the actual text of each bankruptcy 8-K.
>
> Every company has a page with the score and a breakdown of what drives it, and there's a list of every recent bankruptcy
> with what the model said before (misses included): [link to receipts page]
>
> Methodology and a short paper are on the site. I'd really value criticism of the method, especially anything that looks like
> look-ahead bias. (Built with AI-assisted development; not investment advice.)

*Optional line if you want to say it:* "I'm a high school student and this is my first big finance project."
It usually gets a kinder reception, but it's your call.

---

## 3. r/dataisbeautiful (image post: `docs/marketing/oc-bankruptcy-deciles.png`)

**Title:** [OC] Where a bankruptcy-risk model ranked 475 US companies before they went bankrupt (2017-2026)

**Required first comment (source + tool):**
> **Data:** SEC EDGAR: XBRL financial data from 10-K and 10-Q filings, and 8-K Item 1.03 filings for bankruptcies.
> **Tool:** Python (pandas, DuckDB, scikit-learn), chart drawn with Pillow.
>
> Each bar is the share of bankrupt companies whose last risk score (within 13 months before the filing) fell in that tenth of
> all filings made in the 365 days up to it (never later ones). If the score were random, every bar would be 10%. The model is walk-forward: each year's model
> only learned from bankruptcies known before that year. 101 more bankrupt companies had no score in the 13 months before (mostly
> banks and insurers, which aren't scored, or companies without XBRL data).
>
> Interactive version, with every company listed: [link to receipts page]

---

## 4. Show HN (post the site, not the newsletter; no asking friends to upvote)

**Title:** Show HN: Free bankruptcy-risk scores for every US public company, with a public track record

**URL:** https://mahirzmansuri-hash.github.io/earnings-scanner/

**First comment (post right after submitting):**
> Hi HN. Faultline scores ~7,700 US public companies for bankruptcy risk from SEC filings and publishes how often the warnings
> came true. No sign-up; it's a static site rebuilt every week by GitHub Actions.
>
> How it works: XBRL financial data from SEC EDGAR, stored point-in-time (each number dated by its filing date, first-filed values
> only), DuckDB for storage, gradient-boosted trees trained walk-forward, plus signals from 10-K text (going-concern wording,
> material weaknesses) and 8-K events. Each company page explains its score by swapping groups of inputs for typical values and
> measuring the change.
>
> Track record (2016-2023 test years): AUC 0.85 vs 0.71 for the Altman Z-Score. The Receipts page lists every bankruptcy in the
> last 12 months and what the model said before; 30 of 39 were already in the riskiest 10%. What didn't work is on the site too:
> fraud prediction (AUC 0.63) wasn't good enough to publish.
>
> I built this with AI-assisted development as a student project and would love criticism, especially on the methodology.
> There's also an RSS feed for every company and a weekly digest.

**Timing:** a weekday, around 8-10am US Eastern.

---

## Reply bank (honest answers to the likely criticism)

- **"Isn't this look-ahead bias?"** Every number is the first-filed value, dated by the filing date, and each year's model is
  trained only on outcomes known before that year. Percentiles compare each score only with scores filed in the 365 days before it.
  (An earlier version ranked within the calendar year, which peeked at later filings; fixing it moved scores ~2 points on average
  and changed the headline from 70% to 71%.)
- **"71% sounds too good."** It's the *last* score before the filing, often a few weeks before, when trouble is visible.
  The stricter test (bankruptcy within 2 years of each 10-K) is 53% in the riskiest 10%. Most companies in the riskiest 10%
  do *not* go bankrupt: it's a ranking, not a prediction for any one company.
- **"Can I trade on this?"** It's research, not investment advice. The stock-outcome test is on the Track record page;
  distressed stocks are hard to short and often delisted.
- **"Why no banks?"** Bank balance sheets don't fit these ratios (deposits are liabilities by design). SVB is shown as a failure case.
- **"Survivorship bias?"** Dead and delisted companies are kept; that's where the bankruptcies come from.
- **"Did AI write it?"** Yes, built with AI-assisted development. Every decision, test and bug is written down in the public build log (`vault/build-log.md` in the repo).
