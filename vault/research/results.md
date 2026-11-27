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
