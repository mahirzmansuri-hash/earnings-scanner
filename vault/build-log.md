# Build Log

One entry per session, newest at the bottom. Each entry must be enough to resume with no chat history.

```
## YYYY-MM-DD: Session title
- Did:
- Decisions: (details in [[design-notes]])
- Bugs / gotchas: (details in [[gotchas]])
- State: (what works, what's uncommitted)
- Next:
```

## 2026-11-25: Phase 0 setup
- **Did:** installed Python 3.12.10 and its SSL certificates; created the venv and pinned requirements; made the folder structure, `src/config.py`, `.env`/`.env.example`, this vault, `.gitignore`, and a git repo (files staged).
- **Decisions:** Python 3.12, pinned deps, DuckDB, User-Agent kept in `.env`, raw data not committed. See [[design-notes]].
- **Bugs / gotchas:** SSL certificate error, then a 403 from SEC without a User-Agent (expected). See [[gotchas]].
- **State:** Phase 0 done. Pushed to github.com/mahirzmansuri-hash/earnings-scanner. Commits use my GitHub noreply email. The token is in macOS Keychain. `.env` still has the placeholder.
- **Next:** put my real name and email in `.env`; decide hours per week; plan the weeks for Phase 1.

## 2026-11-26: Module 1 done: EDGAR basics
- **Did:** wrote `src/pipeline/edgar.py` (`fetch_company_facts`: User-Agent from `.env`, rate limit of 8 req/sec, caches raw JSON in `data/raw/companyfacts/`). Fetched Apple (CIK 320193): 4.3 MB, 512 us-gaap tags.
- **Spot-check 1/5:** AAPL FY2025 revenue. EDGAR `RevenueFromContractWithCustomerExcludingAssessedTax` = $416,161,000,000 (period 2024-09-29 to 2025-09-27, first filed 2025-10-31, accn 0000320193-25-000079). The 10-K Statement of Operations shows "Total net sales" of 416,161 (in millions). **Match.**
- **Bugs / gotchas:** `fy` describes the filing, not the period; the same value repeats in later 10-Ks. See [[gotchas]].
- **Decisions:** Claude does all lookups and checks itself and teaches the results as lessons (CLAUDE.md and `/spot-check` updated).
- **Decisions:** the schedule changed from weeks to modules with topics (see [[requirements]]).
- **Explain-back quiz:** Q4 (restatement scenario) correct. Gaps fixed: a fact is *one number* with tag, value, unit, period, **filed** date and accn (I'd named tags); look-ahead bias is about information **not being public yet**, not about numbers changing; values repeat because each 10-K reprints 2 prior years; the backtest uses **first-filed**, Lookup uses **latest-filed**.
- **Found:** `companyfacts.zip` bulk file returned 503 then 403 (2026-11-26); `submissions.zip` (1.58 GB) is fine. Investigate in Module 2.1.
- **State:** committed and pushed. Spot-checks done: 1/5.
- **Next:** Module 2, the full company universe. Start with 2.1 (bulk vs one-by-one) and 2.2 (survivorship bias).

## 2026-11-26 (cont.): Modules 2-4 and spot-checks 2-5
- **Did:** downloaded `submissions.zip` (1.58 GB) with `download_bulk_file()`; built the company universe (`src/pipeline/universe.py`): 15,686 companies with a 10-K since 2009, minus bond trusts (6189), SPACs (6770) and no-SIC entities; banks etc. flagged `is_financial`; 5,337 active, 10,349 inactive. Downloaded companyfacts for all of them (gzip, threaded, resumable, 8 req/s): 13,480 with data, 2,206 none (404), 0 failed, 1.2 GB. Loaded DuckDB (`load_db.py`): 39.0M annual-report facts, 793 MB. Built `tag_map.py` (20 concepts) and `annual.py`: 1.63M clean annual values, 116,107 company-years, first-filed + latest + `revised` flag. 8 pytest tests pass.
- **Measured:** 64% of operating companies have no ticker today (survivorship); 500-900 companies stop filing every year; 10-Ks with XBRL: 0.4% (2009), 6.7% (2010), 21.7% (2011), 91.1% (2012); 2,482 of the companies with no XBRL data died 2009-2011. Core inputs (revenue, assets, net income, CFO) present for 73% (2012) to 87% (2024) of non-financial company-years; Beneish's extra inputs only ~55-60%. Identity checks: revenue - COGS = GP passes 97.5%; assets = liabilities + equity (2%) passes 89.6%.
- **Spot-check 2/5:** Sears Holdings (dead) FY2017 revenue $16,702M = 10-K "Total revenues" 16,702 (accn 0001310067-18-000006, filed 2018-03-23). 53-week year (370 days). The $4,376M fact in the same filing is Q4 (97 days), correctly excluded. **Match.**
- **Spot-check 3/5:** General Mills (May FY) FY2023 net sales $20,094.2M = 10-K Consolidated Statements of Earnings 20,094.2 (accn 0001193125-23-177500). **Match** (after the revenue-referee fix).
- **Spot-check 4/5:** SVB Financial (bank, failed) total assets 2022-12-31 $211,793M = 10-K balance sheet 211,793 (accn 0000719739-23-000021). **Match.**
- **Spot-check 5/5:** Conagra FY2015 revenue first-filed $15,832.4M = original 10-K net sales 15,832.4 (accn 0001628280-15-005333). Latest is $9,034M (recast after the Lamb Weston spin-off). **Match**; shows why the backtest uses first-filed.
- **Bugs / gotchas:** revenue tags disagree in 14.2% of filings (General Mills, Hasbro) -> identity referee then largest; revised != restated; bankrupt companies get renamed (use CIK); DuckDB 2.0 removed `.fetchone()` on `con.sql()`. See [[gotchas]].
- **Decisions:** name **Faultline**, research-report look, signal-cyan pop; gzip cache; DB keeps annual forms only; first-filed picked by filing date before tag. See [[design-notes]].
- **Explain-back quiz (Modules 2-5):** Q4 (why 2012) and Q5 (.part file; 350-380-day filter) solid; Q1 (survivorship) mostly right. Gaps fixed: (Q1) the missing 64% includes the bankruptcies where a low Z was RIGHT, so leaving them out biases the test against Altman; (Q2) Lookup uses the LATEST value ($9.0B Conagra), not first-filed, so the trend compares like with like; the backtest uses first-filed ($15.8B); (Q3) General Mills is alive; the issue was two revenue tags with different values in ONE filing, settled by revenue - COGS = gross profit from the same filing; 'largest' alone failed on Hasbro; (Q4) a 2010 start = size bias (only big companies had XBRL); (Q5d) the filter drops quarters inside 10-Ks (Sears Q4 = 97 days) and allows 52/53-week years (370 days).
- **State:** all committed and pushed. Phase 1 acceptance criteria met; explain-back done.
- **Next:** explain-back quiz (Modules 2-5); then Phase 2: Mahir writes the scores (`/review-my-score`), starting with Altman Z. Open items: 4.4 real restatement detection; improve Beneish input coverage (~55-60%); price data for Altman X4 and the backtest.

## 2026-11-27: Stage 1: score engine + first track record
- **Did:** new scope and working model (Claude writes all code and drives; no quizzes; $0 budget; done by Jun 1, 2028; multi-year research framing with RQ1-RQ5 in [[roadmap]]). Added `public_float` (10-K cover-page market value, 91% of company-years). Built `events.py` (bankruptcy 1,144 cos, non-reliance 2,904, auditor change 7,509, late 10-K 6,774, 10-K/A 8,860). Built `src/scores/` (Altman Z with public float, Z'', Piotroski F, Beneish M) for 116,121 company-years; `track_record.py` (RQ1).
- **Results:** see `vault/research/results.md`. Altman Z distress caught 83% of bankruptcies 12-24 months ahead but flags 49% of all company-years (lift 1.7x; 2.2x for revenue >= $100M); Beneish caught 26% of restatements (lift 1.9x). Sears: Z in distress from Mar 2015, 3.5 years before its Oct 2018 bankruptcy.
- **Bugs:** DuckDB table-name shadowing (scores/events rebuilt from stale tables); rows dated by the latest input (fixed: date by original 10-K). See [[gotchas]].
- **State:** 16 tests pass; committed and pushed.
- **Next:** pick Stage 1 follow-ups (better thresholds / composite, warning events, coverage gap), then a 2-page RQ1 brief for professors.

## 2026-11-27 (cont.): Faultline Composite v1
- **Did:** installed scikit-learn 1.9.1; `src/model/composite.py` (41 features, walk-forward 2016-2023, `composite` table with out-of-sample risk for every company-year); `src/model/ablation.py` (feature groups, top-X% table).
- **Results:** AUC 0.847 vs Altman 0.708; flag riskiest 10% -> catch 52% of bankruptcies vs 13% for lowest-Z; same catch rate with 26% fewer alarms. Warning events add ~nothing on top of financials. See `vault/research/results.md`.
- **State:** committed and pushed. 16 tests pass.
- **Next:** options: restatement model (Beneish side), case-study pages, 2-page brief for professors, start the website.

## 2026-11-27 (cont.): Restatement model + website v1
- **Did:** restatement model (AUC 0.74 vs Beneish 0.52); `src/model/live.py` (out-of-sample risk for every filing 2016-2026, with same-year percentiles); `src/web/` static site generator; local preview via `.claude/launch.json`. Dropped the professor brief (teacher check instead).
- **Bugs:** a "final model" would have shown in-sample scores for early-2024 filings, replaced by walk-forward for every year; NaN in screener JSON (now `allow_nan=False`); NaN-safe escaping; overlapping chart labels; misleading accrual sentence for loss-makers.
- **Result on the site:** 62 of 87 companies that went bankrupt in the last two years were in Faultline's riskiest 20% one to two years earlier.
- **State:** committed and pushed; site not public.
- **Next:** decide hosting (GitHub Pages or Cloudflare Pages, free) and weekly auto-update; company pages for banks (classic scores only); share image.

## 2026-11-27 (cont.): Site published
- **Live:** https://mahirzmansuri-hash.github.io/earnings-scanner/ (GitHub Pages from the `gh-pages` branch, pushed by `scripts/publish_site.sh`; Pages switched on by Mahir).
- **Checked live:** all page types return 200; search works; screener loads (added a loading message); no console errors.
- **Note:** URL contains the GitHub username; companies that died before 2016 (e.g. RadioShack) have no page because scores start in 2016.
- **Next:** weekly auto-update (needs SEC data in CI or a local scheduled run), bank pages, share image, analytics.

## 2026-11-27 (cont.): Weekly auto-update
- **Did:** `src/pipeline/update.py` (incremental companyfacts refresh via `_manifest.json`, then full rebuild; 4 min locally with `--skip-download`); `.github/workflows/weekly-update.yml` (Sundays 12:00 UTC + manual button; caches company facts; publishes with GITHUB_TOKEN); `publish_site.sh` accepts `PUBLISH_REMOTE`.
- **Blocked:** push rejected: the saved fine-grained token lacks the Workflows permission. Commit 6cc8ffb is local only.
- **Mahir to do:** (1) token: Workflows = Read and write; (2) repo secret `SEC_USER_AGENT`; then push + first manual run (first run downloads everything, ~45 min).
- **Note:** GitHub pauses scheduled workflows in public repos after 60 days with no repo activity; re-enable from the Actions tab if that happens.

## 2026-11-27 (overnight, autonomous)
- **Did:** README; `src/model/robustness.py` (by year, by size, calibration, permutation importance); new events (8-K 5.01 change in control, Form 15 deregistration); `src/model/distress_exit.py` (second outcome); `docs/paper.md` draft; share image (`scripts/make_share_image.py` -> `src/web/assets/og.png`) + favicon + og/twitter meta; `tests/test_scores.py` (24 tests pass); paper link and distress-exit section on the site; update.py runs the new steps.
- **Bugs:** model input had 194 duplicate rows + no fixed order -> results drifted between runs; fixed (QUALIFY + ORDER BY), all numbers re-run and synced. New event types broke the site's red flags -> only warning events are shown.
- **Final numbers:** see last entry of `vault/research/results.md`.
- **State:** committed and pushed. First GitHub Actions run in progress; site to be republished after it finishes.
- **Next:** verify the CI run; republish; paper polish; Stage 2 (free price data) research.

## 2026-11-27 (overnight, cont.): First CI run
- **Result:** run #1 (43m 50s): all data, model and site steps succeeded on GitHub's servers; "Publish to GitHub Pages" failed (exit 126: zsh shebang on Linux). Cache not saved because the job failed.
- **Fix:** bash shebang + `bash scripts/publish_site.sh`; cache restore/save split with `if: always()`. Pushed (2f399a1). Published tonight's site from the Mac with the bash script (works).
- **Next:** Sunday's scheduled run will confirm the fix (it will re-download everything once, since no cache was saved). A manual "Run workflow" click would confirm sooner.

## 2026-11-27 (second night, autonomous): Stage 2 + New filings
- **Did:** `src/backtest/returns.py` (option A: public-float changes, window starts after the score is public; bankrupt -100%, stopped filing -50%/-100%/0%, buyouts excluded; >= $10M float); results on Track record page, paper, README; weekly pipeline runs it. `new.html` (last 30 days of 10-Ks + biggest percentile jumps), nav link, sitemap. Republished and verified.
- **Findings:** riskiest 10% median -14.8% vs +2.8% for safest half; lost half+ 33.5% vs 11.1%; wiped out 10.9% vs 1.0%; mean not lower (lottery-like skew + share issuance). Median gap in 5 of 7 years.
- **Data notes:** 3.4% of float pairs are identical (illiquid shells); 2.6% jump 10x+ (reverse mergers/IPOs/errors) -> medians as main measure, $10M floor.
- **Next:** decide RQ5 (10-K text at $0), calibration fix, Search Console (Mahir).

## 2026-11-27 (day): RQ5 10-K text signals
- **Did:** `src/pipeline/text_signals.py` (EDGAR full-text search, 5 phrases, monthly since 2009, cached in data/raw/fulltext, retries + skip-and-log on 500s); text flags as 5 model features; ablation groups 4 + text-only; weekly pipeline + CI cache include it; company pages show phrase flags (3,671 pages); methodology says 46 inputs.
- **Result:** null for prediction (bankruptcy 0.847 unchanged; restatement 0.738 -> 0.737); phrase flags alone 0.63 / 0.61; going-concern phrase doubles the bankruptcy rate (3.2% vs 1.5%). See results.md.
- **Bug:** SEC full-text search returned HTTP 500 on a page mid-run -> retries with backoff, incomplete months retried next run.
- **State:** committed, pushed, site republished.

## 2026-11-27 (evening): Paper PDF live + tougher benchmarks
- **Did:** CI run passed every step (publish fix confirmed); republished with the paper PDF (live, 200). Added `src/model/features.py`: Ohlson O-score (1980), Zmijewski (1984), multi-year trends, industry-relative ratios and industry bankruptcy rate (previous calendar year only). Ablation now reports all three classic formulas + a "v2 test" group. Site track-record table, paper (table, abstract, refs) and README updated; README AUC typo 0.84 -> 0.85 fixed.
- **Result:** Faultline 0.847 vs Altman 0.707, Ohlson 0.719, Zmijewski 0.743 (riskiest 10% caught: 53% vs 13/11/13%). v2 features: no gain (0.847; 52% vs 53% at top 10%) -> live model stays v1.
- **Decision:** keep the simpler model; report the null v2 result in the paper.
- **Next:** per-company "why this score" explanations; SEC AAER fraud cases as true fraud labels; quarterly 10-Q signals.

## 2026-11-27 (evening, cont.): Why-this-score breakdown
- **Did:** `src/model/explain.py` (swap test / occlusion: 46 inputs in 10 plain-English groups; each group set to the training median, effect = change in log-odds). `walk_forward(models={})` keeps each year's model so the explanation uses the exact model that scored the filing. `live.py` writes table `risk_why` for each company's latest filing (7,693). Company pages: "Why this score" table (area, the company's number vs typical, strength word + bar). Methodology section `#why`; README line; `tests/test_explain.py` (26 tests pass).
- **Checks:** Sears 2018: classic scores, debt (liabilities 151% of assets), losses, sales -25% push risk up. Apple: profits and Z pull it down. Bed Bath 2022: debt 97% of assets; its Altman Z/Z'' looked fine only because buybacks left retained earnings at 188% of assets.
- **Bugs:** pandas NA in `neg_equity` broke an `if`; "Amended 10-k" capitalization; 3-column table overflowed on phones -> 2 columns with the detail under the area name, short headers.
- **Quirk (documented on Methodology):** size can "raise" risk for big companies, because small failing companies usually go dark instead of filing for bankruptcy.
- **Next:** SEC AAER fraud-case labels; quarterly 10-Q signals.

## 2026-11-27 (night): SEC fraud cases (AAER) - RQ6
- **Did:** `src/pipeline/aaer.py` (SEC AAER index, 3,324 releases, 34 pages; company respondents matched to CIKs by normalised current/former name; release documents read (PDF via pypdfium2, HTML for litigation releases); kinds: accounting / bribery (FCPA) / late-filing notice / procedural; misstated fiscal years read from the text). `src/model/fraud.py` (real-time walk-forward where a case counts only once announced; hindsight 5-fold CV split by company; 3 model types fixed in advance, all reported). Company pages: "SEC accounting cases" (129 pages, unambiguous matches only, facts + links). Track record section, paper RQ6 (+ Bao et al. 2020), README; weekly update + CI cache include it.
- **Result:** 266 misstated company-years at 95 companies (FY2013-2019). Real-time AUC 0.63 (logistic), top 10% holds 24%; Beneish 0.58 / 16%; on Beneish's rows AUC 0.57 vs 0.58 but top 10% 26% vs 16%. Hindsight 0.69 (Bao et al. 0.72). Restatement model 0.50 on fraud. Median 6 years from first misstated year to release; only 11 known cases when scoring 2013.
- **Decision:** no fraud score on company pages (too weak to rank named companies); show SEC cases as facts.
- **Bugs:** name splitter broke "Latch, Inc."; EDGAR "/OR/" state tags; relative litigation-release links; FCPA bribery and Rule 12b-25 releases were being counted as fraud -> filtered.
- **Next:** quarterly 10-Q signals; or Stage 5 (alerts, newsletter, API).

## 2026-11-27 (night, cont.): Quarterly 10-Q signals - RQ7
- **Did:** `src/pipeline/quarterly.py` (10-Q facts from the cached companyfacts files, 22 s, 11.6M rows; one row per quarter, original 10-Q only; trailing twelve months = YTD now + last FY (original 10-K, public before the 10-Q) - same YTD last year (first-filed); balance sheet at quarter end; public float carried from the latest 10-K). `src/model/quarterly_test.py` (10-Q model vs last-10-K score at every 10-Q date, same label; by 10-K age; lead time; `live()` writes `risk_q`). Company pages show "Updated with the 10-Q filed ..." (6,712 pages). Track record + Methodology sections, paper RQ7, README, weekly update steps. `tests/test_quarterly.py` rebuilds Apple's TTM (27 tests pass).
- **Spot-check:** Apple 10-Q (Jun 29, 2024): 9M revenue 296,105 / prior 293,787 match the filing; TTM revenue 385,603, TTM net income 101,956.
- **Result:** 99,507 10-Q dates (2016-2023, 6,984 companies). AUC 0.81 (last 10-K) -> 0.83 (fresh 10-Q) -> 0.84 (both); riskiest 10% 46% -> 51%. Gain grows with 10-K age (0.807/0.812 under 4 months; 0.847/0.875 over 8). Bankrupt companies warned: 326 vs 270 of 464, median 517 vs 472 days before filing.
- **Bugs:** results drifted between runs -> amended 10-Qs duplicated quarters, and DuckDB arg_min/arg_max ties + unsorted pandas merges picked arbitrary values. Fixed with original-only rows and explicit tie-breakers; two builds now hash identical. Date subtraction broke on TIMESTAMP columns (caught by the new test) -> date_diff.
- **Next:** Stage 5 (alerts when a company's risk jumps, newsletter, API), or show the combined 10-K+10-Q score.

## 2026-11-27 (night, cont.): Stage 5 begins - alerts
- **Did:** `src/web/alerts.py`: alert engine (entered riskiest 5%, risk jump of 20+ percentile points into the top 20% along each company's 10-K + 10-Q timeline, 8-K 1.03 / 4.02 / 4.01, NT 10-K, new going-concern wording, SEC AAER cases). Site: Alerts page (last 90 days, type filter, watchlist filter), watchlist button on every company page (browser localStorage), Atom feeds (main `feed.xml` + `c/<cik>.xml` for all 7,693 companies), weekly digest pages for the last 12 weeks (`digest/`), `data/processed/digest_latest.md` (newsletter text). `risk_q` now keeps every 10-Q (142,260) so 10-Q jumps can be found. Nav "Alerts"; sitemap. `tests/test_alerts.py` (29 tests pass).
- **Numbers:** 25,838 alerts since 2016; 238 in the last 90 days. This week's digest: America's Car-Mart filed for bankruptcy; Faultline's last score before it was riskier than 90% of filers.
- **Checks:** all 7,693 company feeds parse as XML; watchlist add/filter tested in the browser; alerts table folded to 3 columns for phones.
- **Waiting on Mahir:** email delivery (free newsletter account, e.g. Buttondown or Substack) - the digest text is ready.
- **Next:** email delivery; marketing plan (Reddit, Show HN, Search Console, school investing clubs).

## 2026-11-27 (night, cont.): Digest email via Buttondown (code ready, account pending)
- **Did:** `src/web/newsletter.py` turns `digest_latest.md` into a Buttondown email (subject from the title line, footer with site links + "not investment advice"). Skips cleanly with no `BUTTONDOWN_API_KEY`; never prints the key; won't create a second email with the same subject. Status set explicitly: `draft` by default, `send` only if `FL_DIGEST_MODE=send`. Digest markdown now links every company to its page. Optional sign-up form (`NEWSLETTER_USER` in `src/web/style.py`, hidden while empty) on Alerts + digest index. Weekly workflow step after publish (continue-on-error). `.env.example` placeholders. `tests/test_newsletter.py` (32 tests pass).
- **Decision:** Buttondown over Substack (free to 100 subscribers, API, Markdown). Drafts first, auto-send later.
- **Unverified:** Buttondown docs pages we fetched didn't show the status values or the embed form snippet; used the standard `embed-subscribe/<username>` + `email` field. Confirm against Buttondown's embed generator when the account exists.
- **Waiting on Mahir:** create the Buttondown account, add repo secret `BUTTONDOWN_API_KEY`, tell Claude the username.
- **Next:** turn on sign-up box, first draft email, then marketing plan.
- **Update:** username `mahir`. Buttondown's own page (buttondown.com/mahir) uses `embed-subscribe/mahir` + `email` field, matching our form. Sign-up box now live on Alerts + digest pages (checked on a phone-size screen). Still needed: `BUTTONDOWN_API_KEY` repo secret for the weekly draft.
- **Test:** new workflow `digest-email-test.yml` (draft only, fails without a key) ran on GitHub: success, so the secret works and Buttondown accepted the API calls. Draft for 2026-11-19 to 2026-11-25 created.
- Marketing plan v1 written (`vault/marketing-plan.md`): measure first (GoatCounter, Search Console), share-ready site + Receipts page, then one channel a week (school club, r/SecurityAnalysis, r/dataisbeautiful, Show HN). Reddit blocked automated rule checks; LinkedIn needs age 16.

## 2026-11-27 (night, cont.): Marketing Phase 0+1 - share-ready site
- **Did:** `src/pipeline/names.py` -> table `display_names`: readable company names (8,374 changed; "AMERICAS CARMART INC" -> "America's Car-Mart, Inc.", uses the filer's own XBRL entityName when it's the same name, keeps acronyms like JPMorgan/CVS/3M, drops SEC state tags like /DE/). Receipts page (`receipts.html`, in the nav): every bankruptcy 8-K in the last 12 months + Faultline's last score before it, misses included, with a share card made at build time (`src/web/share.py`, `og-receipts.png`). Analytics hooks off until codes exist (`GOATCOUNTER_CODE`, `GOOGLE_VERIFY` in style.py). Tests: test_names, test_receipts (38 pass).
- **Result:** 48 bankruptcy filings; 39 had a score in the 13 months before; 30 of 39 (77%) were already in the riskiest 10% (chance: ~4). Median 330 days from first entering the riskiest 10% to the filing (capped by the 13-month window).
- **Bug found:** SEC's filing index tagged Granite Construction's Feb 18, 2026 8-K as Item 1.03 (bankruptcy); the 8-K is a note exchange. New `src/pipeline/verify_bk.py` reads each bankruptcy 8-K from the last 2 years (165) and drops ones whose text never mentions bankruptcy (1: Granite). First version matched SEC's own header text and missed Avinger's real 8-K (read exhibits first) -> fixed.
- **Display fix:** percentiles round down on Receipts (89.7% showed as "90%" while labelled "riskiest 25%").
- **Waiting on Mahir:** GoatCounter account (site code), Google Search Console (HTML-tag verification value).
- **Next:** turn on analytics + submit sitemap; then launch week 1 (school club demo).
