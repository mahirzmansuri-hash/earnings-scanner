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
