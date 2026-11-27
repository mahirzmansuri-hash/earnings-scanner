# Results log
Each entry: date, question (RQ#), method in one line, exact numbers, caveats.

## 2026-11-27: RQ1 first track record (Stage 1)
**Method:** point-in-time scores (first-filed values, dated by the original 10-K), non-financial companies, scores public 2012-2023. Event = first bankruptcy 8-K (Item 1.03) or restatement 8-K (Item 4.02). Hit rate = share of events whose latest score in the warning window was flagged. Alarm rate = share of all scored company-years flagged. Lift = hit / alarm. Code: `src/backtest/track_record.py`; output `data/processed/track_record.json`.

| Test | Events (with a score) | Hit rate | Alarm rate | Lift | Risk ratio* |
|---|---|---|---|---|---|
| Altman Z distress, 12-24 mo before bankruptcy | 704 (419) | 83.3% | 49.2% | 1.7x | 5.3x |
| Altman Z'' (no price) distress, 12-24 mo before | 704 (480) | 82.1% | 50.7% | 1.6x | 5.0x |
| Altman Z distress, 0-24 mo before | 704 (478) | 88.9% | 49.2% | 1.8x | 6.6x |
| Piotroski F <= 3, 12-24 mo before bankruptcy | 704 (258) | 40.3% | 17.9% | 2.2x | 3.0x |
| Beneish M > -1.78, 0-24 mo before restatement | 2,254 (555) | 26.1% | 13.7% | 1.9x | 2.0x |
| Altman Z distress, 0-24 mo before late 10-K | 11,155 (5,176) | 78.1% | 49.2% | 1.6x | 3.3x |
| Altman Z distress, 12-24 mo, revenue >= $100M only | (220) | 76.4% | 34.3% | 2.2x | n/a |

*Risk ratio = event rate within 24 months for flagged company-years / for unflagged ones (e.g. 2.38% vs 0.45% for Altman Z).

**Findings:** (1) The classic scores do warn: flagged companies are 2-6x more likely to go bankrupt or restate. (2) But the 1968/1999 thresholds raise far too many false alarms: Altman flags ~half of all US company-years (many tiny or loss-making firms). (3) Beneish catches about 1 in 4 restatements. (4) 285 of 704 bankruptcies had no score in the window (company stopped filing, missing inputs): a coverage gap to report.
**Next questions:** better thresholds / a combined model (RQ3); add warning events (RQ2); size groups.

## 2026-11-27: RQ2 + RQ3 Faultline Composite v1 (bankruptcy within 24 months)
**Method:** gradient-boosted trees (scikit-learn HistGradientBoosting) on 41 point-in-time features (all Altman/Piotroski/Beneish pieces, size, profitability, leverage, growth, filing delay, warning events in the prior 24 months). Walk-forward: to test year Y, train only on rows whose 24-month outcome was known before Jan 1 of Y. Test years 2016-2023. Compared with Altman on the same rows. Code: `src/model/composite.py`, `src/model/ablation.py`.

| On 25,231 unseen company-years (542 bankruptcies) | Altman Z | Faultline |
|---|---|---|
| AUC (ranking quality; 0.5 = coin flip) | 0.708 | **0.847** |
| Catch rate at Altman's alarm rate (50%) | 85.6% | **93.4%** |
| Alarm rate needed to catch 85.6% | 50.3% | **37.1%** (26% fewer alarms) |
| Bankruptcies caught if you flag only the riskiest 10% | 13% | **52%** |
| ... riskiest 5% / 20% | 5% / 38% | **34% / 71%** |

**Ablation (RQ2):** classic-score ingredients alone AUC 0.831 (the gain over Altman is mostly from *combining* the same ingredients better); + size & fundamentals 0.847; + filing behaviour & warning events 0.848 (adds almost nothing on top); events alone 0.645 (informative, but already captured by the financials).
**Sanity check:** 2022 top-12 riskiest: 3 filed bankruptcy within 24 months (Lannett, Cyxtera, ShiftPixy); several others were distressed sales/acquisitions or out-of-court restructurings (Redbox, Vivint, Abraxas), which our label (8-K Item 1.03 only) counts as misses, so measured precision is conservative.
**Caveats:** only formal bankruptcy notices count; companies that stop filing ("go dark") aren't labelled; 2020 COVID year included; one model setting, not tuned.

## 2026-11-27: Label update + restatement model (RQ3, accounting side)
- **Label change:** the bankruptcy label now counts ANY bankruptcy notice within 24 months (was: only the company's first). 1,500 positive company-years (was 1,358). Re-run: Faultline AUC 0.845 (Altman 0.708); at Altman's alarm rate Faultline catches 92.8% vs 85.6%. Conclusions unchanged.
- **Restatement model** (`src/model/restatement.py`): same 41 features, label = 8-K Item 4.02 within 24 months; walk-forward 2016-2023. On 14,443 company-years with a Beneish score (479 restatements):

| | Beneish M | Faultline |
|---|---|---|
| AUC | 0.521 (almost a coin flip) | **0.738** |
| Catch rate at Beneish's alarm rate (14%) | 25.9% | **36.3%** |
| Caught if flagging riskiest 10% | 19.4% | **28.6%** |

- **Finding:** restatements are much harder to predict than bankruptcies; Beneish's ranking carries almost no information in 2016-2023, though its yes/no flag still has some lift. On all 40,311 company-years (no Beneish needed), Faultline AUC 0.696.

## 2026-11-27: Robustness of the bankruptcy model (`src/model/robustness.py`)
- **Every test year:** Faultline AUC beats Altman in all 8 years: 2016 0.819 vs 0.717; 2017 0.824 vs 0.775; 2018 0.802 vs 0.718; 2019 0.866 vs 0.698; 2020 0.920 vs 0.708; 2021 0.851 vs 0.726; 2022 0.829 vs 0.672; 2023 0.867 vs 0.710.
- **Every size group:** revenue under $100M 0.772 vs 0.615 (10,301 company-years, 250 bankruptcies); $100M-$1B 0.875 vs 0.809 (6,694, 174); over $1B 0.902 vs 0.781 (8,236, 118).
- **Calibration (deciles, predicted vs actual):** top decile 10.84% vs 9.15%; deciles 4-9 under-predict (e.g. decile 6: 0.77% vs 1.42%). Ranking is reliable; the middle probabilities read about 1.5x too low.
- **Most important clues** (permutation importance, model trained on outcomes known before 2021, tested on 2021-2023; AUC drop when shuffled): company size (log assets) 0.058, ROA 0.019, Altman X3 (EBIT/assets) 0.013, Z'' 0.011, log revenue 0.009, cash flow/assets 0.008, Altman X1 (working capital) 0.007, log public float 0.007.
- **Caveat:** size is the top clue partly because small companies often stop filing instead of filing a formal bankruptcy 8-K, so the label under-counts small-company failures. Next: add "stopped filing within 24 months" as a second outcome.

## 2026-11-27: Second outcome: "distress exit" (`src/model/distress_exit.py`)
**Why:** small companies often stop filing instead of filing a bankruptcy 8-K. **Label:** bankruptcy 8-K within 24 months, OR this was the company's last 10-K and it stopped filing without a change of control (no 8-K Item 5.01 from 1 year before to 3 years after). New events: change in control (7,043 companies), Form 15 deregistration (8,025).
- Positives: 5,112 company-years overall; 1,282 in the 2016-2023 test (vs 542 bankruptcies).
- **AUC:** Faultline 0.834 vs Altman 0.749. Riskiest 10% caught 40% vs 30%; riskiest 20% 65% vs 51%.
- Small companies (revenue under $100M; 865 exits): 0.733 vs 0.666. Larger (417 exits): 0.883 vs 0.791.
- **Reading:** Faultline still wins on the broader outcome, but the gap narrows and Altman does better here (0.75) than on bankruptcy alone (0.71). This supports the caveat: the bankruptcy-only label hid many small-company failures. Report both outcomes.

## 2026-11-27: Final reproducible numbers (supersede earlier entries)
Fixes: model input had 194 duplicate rows (fiscal-year changes matched two prior years) and no fixed row order, so results moved slightly between runs. Now deduped and ordered; two runs give identical results.
- **Bankruptcy, 2016-2023:** 25,169 company-years, 539 bankruptcies. AUC Faultline 0.847 vs Altman 0.707. Riskiest 5/10/20%: 35/53/70% vs 5/13/38%. At Altman's 50.3% alarm rate: 92.8% vs 85.5% caught. To catch 85.5%: 36.4% alarm rate.
- **Ablation:** classic-score parts 0.824; + size & fundamentals 0.844; + filing behaviour & events 0.847; events only 0.646.
- **Restatement:** 14,421 company-years, 479 notices. AUC 0.738 vs Beneish 0.521. Riskiest 10%: 28% vs 19%. At Beneish's alarm rate: 37.4% vs 25.9%.
- **Distress exit:** 1,278 events. AUC 0.833 vs 0.748. Riskiest 10%: 40% vs 29%. Under $100M revenue: 0.732 vs 0.666; larger: 0.883 vs 0.791.
- **By year:** 2016 0.818/0.717; 2017 0.844/0.775; 2018 0.774/0.716; 2019 0.875/0.698; 2020 0.933/0.708; 2021 0.864/0.726; 2022 0.830/0.672; 2023 0.871/0.710.
- **By size:** <$100M 0.771/0.616; $100M-$1B 0.879/0.809; >$1B 0.903/0.781.
- **Calibration:** top decile 10.83% predicted vs 9.50% actual; decile 6: 0.71% vs 1.22%.
- **Top clues:** log assets 0.063, ROA 0.022, log float 0.009, log revenue 0.007, Altman X1 0.007, CFO/assets 0.007, Altman X3 0.006.

## 2026-11-27: RQ4 stock outcomes (Stage 2, option A, $0) (`src/backtest/returns.py`)
**Method:** market value of outside shareholders' stock from 10-K cover pages (public float). Return = float in the t+2 10-K / float in the t+1 10-K - 1, a window that starts 3-6 months after the year-t score was public. Missing because of bankruptcy within 3 years -> -100%; stopped filing without buyout -> -50% (also tested -100% and 0%); buyouts left out. Only companies with >= $10M public float when the score came out. Filings 2016-2022; 22,966 company-years, 20,648 with an outcome (19,574 measured, 391 bankrupt, 683 stopped filing; 2,318 left out).

| Group | n | Median | Lost half+ | Wiped out (<= -95%) | Mean (capped +300%) |
|---|---|---|---|---|---|
| Faultline riskiest 10% | 2,257 | -14.8% | 33.5% | 10.9% | +19.6% |
| Faultline 10-20% | 1,825 | -7.2% | 27.2% | 4.4% | +22.5% |
| Faultline safest 50% | 11,592 | +2.8% | 11.1% | 1.0% | +15.2% |
| Altman distress | 6,505 | -4.4% | 24.4% | 4.8% | +19.8% |
| Altman safe | 6,626 | +3.2% | 11.5% | 1.5% | +14.9% |

- **By year (median, riskiest 10% vs safest 50%):** 2016 -0.8/+11.0; 2017 +7.3/+6.8; 2018 -29.3/-4.1; 2019 -18.8/-4.2; 2020 +77.7/+39.7; 2021 -42.4/-22.5; 2022 -29.9/+3.6. Riskiest worse in 5 of 7 years by median (2017 about equal, 2020 rebound rally the exception).
- **Reading:** the typical flagged company lost value and flagged companies were 3x as likely to lose half; but the average was not lower, because a few flagged stocks rose enormously (lottery-like skew) and share issuance inflates market value. Robust to the stopped-filing assumption (median -14.8% at -50% and -100%; -1.2% at 0%).
- **Limits:** float is valued once a year mid-year, excludes insider shares, and rises with share issuance; not a tradable strategy test.

## 2026-11-27: Calibrated risk percentages (`src/model/live.py`)
- For each filing year, raw scores are mapped to observed rates with isotonic regression fitted only on earlier years' out-of-sample scores whose outcomes were known (no look-ahead). Percentiles still come from the raw scores (calibration creates ties).
- Check, filings 2018-2023, deciles shown vs actual 2-year bankruptcy rate: top 10.78% vs 10.26%; 9th 4.11% vs 3.38%; 6th 1.77% vs 1.83% (before calibration the middle deciles read about 0.6x the actual rate).
- Stock-outcome table after percentile recompute: safest half median +2.9% (was +2.8%); other rows unchanged.

## 2026-11-27: RQ5 10-K wording (`src/pipeline/text_signals.py`)
**Method:** SEC full-text search (efts.sec.gov), month by month 2009-2026, 10-K forms; a filing is flagged if any of its documents contains the exact phrase. No document downloads (~15 min, a few thousand requests; retries on server errors).
- Filings with phrase / matched company-years: "raise substantial doubt" 36,713 / 28,157; "recurring losses from operations" 11,051 / 9,132; "identified a material weakness" 7,440 / 6,147; "internal control over financial reporting was not effective" 15,224 / 12,037; "have been restated" 7,840 / 5,071.
- Going-concern phrase: 2-year bankruptcy rate 3.20% with vs 1.47% without (2012-2023, non-financial).
- **Bankruptcy model:** + text 0.847 (unchanged); riskiest 5/10/20% 37/53/70%; text alone 0.629.
- **Restatement model:** without text 0.738, with 0.737; text alone 0.608.
- **Answer to RQ5:** simple phrase flags carry signal on their own but add nothing once the financials are in (crude matching: boilerplate, hypotheticals; overlap with numbers and past events).
- **Re-synced numbers with text in the model:** alarm rate to catch 85.5% = 37.2%; distress exit AUC 0.838 vs 0.748; stock outcomes riskiest 10% median -13.6%, lost half 33.7%, wiped out 10.8% (safest half +2.9%, 11.2%, 1.0%).

- **Robustness with text in the model:** by year 2016 0.82/0.72, 2017 0.86/0.78, 2018 0.78/0.72, 2019 0.87/0.70, 2020 0.93/0.71, 2021 0.86/0.73, 2022 0.83/0.67, 2023 0.87/0.71; raw calibration top decile 11.47% vs 9.76%, decile 6 0.68% vs 1.25%; top clues: log assets, ROA, log revenue, log float, Z'', going-concern phrase, F-Score.

## Classic benchmarks (Nov 27, 2026, same 2016-2023 rows)
| | AUC | Caught top 5/10/20% |
|---|---|---|
| Altman Z | 0.707 | 5 / 13 / 38% |
| Ohlson O | 0.719 | 5 / 11 / 34% |
| Zmijewski | 0.743 | 5 / 13 / 47% |
| Faultline | 0.847 | 37 / 53 / 70% |
| v2 test (+ trends, industry, O, Zmijewski as inputs) | 0.847 | 35 / 52 / 71% |
