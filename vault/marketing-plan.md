# Faultline marketing plan (v1, 2026-11-27)

Budget: $0. Goal: real, countable users before the summer-2028 internship search.
Rule: we market with **real results**, not hype. Every post shows a number we can back up
(the track record, a dated warning before a real bankruptcy). Never "this stock will crash."

## The one-line pitch
"A free site that scores every US public company for bankruptcy and accounting risk from SEC filings,
and publishes how often its warnings came true, dead companies included."

## What makes it worth talking about (our hooks)
1. **Receipts.** Car-Mart filed for bankruptcy this month; Faultline had it riskier than 90% of filers beforehand.
   Every week's digest produces new receipts automatically.
2. **Beats the textbook.** AUC 0.85 vs Altman Z 0.71; the riskiest 10% caught 53% of bankruptcies vs 13%.
3. **Honest failures.** Fraud model is weak (AUC 0.63), so we don't publish a fraud score. SVB is a "where scores fail" case.
   Honesty is rare and people share it.
4. **Built by a high-school sophomore with AI-assisted development.** True, and a story on its own. Always say "AI-assisted."

## Phase 0: measure first - DONE Nov 28 (GoatCounter live, Search Console verified, sitemap submitted)
Without numbers we can't tell what works, and "quantifiable outcomes" is the whole point.
| Tool | What it counts | Cost | Who |
|---|---|---|---|
| GoatCounter | visits per page, where visitors came from. No cookies, no personal data | free for personal sites | Mahir makes account, Claude adds the 1-line script |
| Google Search Console | Google searches that show/click our pages | free | Mahir signs in, Claude adds the verification file + submits sitemap |
| Buttondown | email subscribers | free to 100 | done |
| GitHub | stars on the repo | free | done |

Watch-out: Buttondown's free plan ends at 100 subscribers. Decide at ~80 (options: ask about a student/non-profit
discount, or keep email capped and point extra people to RSS).

## Phase 1: make the site "share-ready" - DONE Nov 28 (readable names, Receipts page + share card, phone check)
- Company names in titles in normal case ("America's Car-Mart", not "AMERICAS CARMART INC") so Google results look clean.
- A share image per case study (chart + one sentence), made from our own data, not AI art.
- A "Receipts" page: every company that went bankrupt in the last 12 months and what Faultline said before.
  This is the page every post links to.
- Fix anything that looks broken on phones. Most Reddit traffic is mobile.

## Phase 2: launch posts, online-first (from Dec 2026, one per week)
Changed Nov 28: Mahir prefers writing to pitching in person, so the school step is a written message asking for feedback, not a talk.
Drafts for every step: `docs/marketing/launch-kit.md`. Chart: `docs/marketing/oc-bankruptcy-deciles.png` (`scripts/make_oc_chart.py`).
| Week | Channel | Post | Why |
|---|---|---|---|
| 1 | Finance/business teacher or club leader (written message) | ask for 10 minutes of honest feedback | expert eyes before strangers; no pitching |
| 2 | r/SecurityAnalysis | method + results + what failed, ask for criticism | analysts like method + honesty |
| 3 | r/dataisbeautiful ([OC]) | decile chart: 70% of 475 bankruptcies were in the riskiest 10% | big audience, chart-only |
| 4 | Hacker News "Show HN" | the site, first comment explains how it's built | qualifies: usable with no signup |
| 5+ | r/ValueInvesting, r/accounting | one case study each | ongoing |

Rules to respect:
- **Read each subreddit's sidebar rules before posting.** Many limit self-promotion (common rule of thumb: most of your
  Reddit activity should not be links to your own site). r/dataisbeautiful needs "[OC]" in the title and a comment naming the data source and tool.
  (Reddit blocked our automated check, so Mahir reads the rules when posting.)
- **Show HN:** must be something people can try without signing up (Faultline is). No asking friends to upvote. Not for newsletters or landing pages, so post the site, not the digest.
- **LinkedIn:** minimum age 16. Product Hunt says it's not for under-16s. Skip both until Mahir is 16.
- Reply to every comment in the first 2 hours. Criticism is free product research. Log it in the build log.

## Phase 3: keep it running (Feb 2027 onward, ~30 min/week)
- Send the weekly digest (draft is made automatically every Sunday).
- One "receipt" post a month from the digest: a company that went bankrupt and what we said before.
- Paper: teacher/professor review, then share the PDF on the Track record page and with finance professors (cold email, Mahir sends).
- Competitions and applications: Faultline as the project; numbers from the dashboard below.

## Targets (check monthly; first check Jan 31, 2027)
| Metric | Jan 31, 2027 | Jun 30, 2027 | Jun 1, 2028 |
|---|---|---|---|
| Monthly visitors (GoatCounter) | 500 | 3,000 | 10,000 |
| Email subscribers | 50 | 100 (free cap) | decide plan |
| Google clicks / month (Search Console) | 50 | 1,000 | 5,000 |
| GitHub stars | 25 | 100 | 250 |
These are guesses to beat, not promises. We'll reset them after the first month of real data.

## Things we never do
- Say a company "will" go bankrupt, or tell anyone to buy/sell/short. Always "research, not investment advice."
- Post about tiny, thinly traded stocks in a way that could move their price.
- Fake accounts, vote swapping, buying followers, AI-generated hype video.
- Hide that the site was built with AI help.

## Claude vs Mahir
- **Claude:** analytics code, Search Console file, site fixes, charts, Receipts page, every post draft, reply suggestions, monthly metrics report.
- **Mahir:** creating accounts, posting (in his own words, editing drafts as he likes), sending emails, talking to teachers.
