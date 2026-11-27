# Can public filings warn of bankruptcy? An out-of-sample test of classic forensic scores and a machine-learning composite, 2016-2023

Mahir, Faultline project (draft, November 2026). Built with AI-assisted development.

## Abstract

The Altman Z-Score, Piotroski F-Score and Beneish M-Score are taught in accounting and finance courses as early-warning tools, but they are rarely tested on the full set of US companies with the failures included and with only the information that was public at the time. I build a point-in-time panel of 116,121 company-years from SEC XBRL filings (15,686 companies, 10,349 of which later stopped filing) and test the scores against 1,144 companies' bankruptcy filings and 2,904 companies' restatement notices. Altman's distress zone caught 83% of bankruptcies 12 to 24 months ahead but flagged about half of all company-years. A gradient-boosted model using the same ingredients plus size, profitability, filing behaviour and warning phrases in the 10-K text, trained only on outcomes known before each test year, raised the ranking accuracy (AUC) for bankruptcy within two years from 0.71 to 0.85 on 25,169 unseen company-years from 2016 to 2023. Flagging the riskiest 10% of companies caught 53% of bankruptcies, against 13% for the lowest Altman scores. The model beat Altman in every test year and every size group. Restatements were much harder to predict: the Beneish M-Score's ranking was close to random (AUC 0.52) and the model reached 0.74.

## 1. Introduction

Altman (1968) built the Z-Score from 66 manufacturing firms. Beneish (1999) built the M-Score from 74 companies caught manipulating earnings. Piotroski (2000) built the F-Score to separate strong and weak value stocks. All three are still used, and all three were fitted on small samples from decades ago.

Two problems make it hard to know how well they work today. The first is survivorship bias: lists of current companies leave out the ones that failed, which are exactly the cases a warning score should catch. The second is look-ahead bias: databases often store numbers as later corrected, not as first reported, so a test can accidentally use information nobody had at the time.

This study avoids both. It asks three questions:

1. How often did the classic scores flag bankruptcies and restatements in advance, and how many false alarms did they raise?
2. Do warning events (auditor changes, late filings, amended reports) add information beyond the financial statements?
3. Can a model trained on the same public data beat the classic scores on years it has never seen?

## 2. Data

**Companies.** SEC's bulk submissions file lists every entity that has filed with the SEC. I keep entities with at least one 10-K filed since 2009 and drop asset-backed trusts (SIC 6189), blank-check companies (SIC 6770) and entities with no industry code. This leaves 15,686 companies. Of these, 10,349 had not filed a 10-K in the 18 months before November 2026, meaning they failed, were acquired or went private.

**Financial data.** For each company I download its XBRL "companyfacts" from SEC (13,480 companies have data; 2,206 have none, mostly companies that stopped filing before XBRL reached small companies in 2011). I keep about 39 million values from annual reports. Each value keeps the date it was filed.

**Point-in-time values.** Each company-year uses the numbers from that year's original 10-K, dated by its filing date. Values that first appeared in a later filing are left out. Companies tag the same item in different ways, so a mapping turns 21 accounting items into consistent inputs. In 14.2% of filings, two revenue tags disagree; I keep the value where revenue minus cost of goods sold equals gross profit, which passes for 97.5% of the company-years where it can be checked. Five companies (Apple, Sears, General Mills, SVB, Conagra) were checked by hand against their 10-Ks and all matched.

**XBRL coverage.** Only 0.4% of 10-Ks filed in 2009 had XBRL data, rising to 21.7% in 2011 and 91.1% in 2012. Tests therefore start in 2012.

**Market value.** Altman's Z-Score needs the market value of equity. I use the public float reported on each 10-K's cover page, which is free and available for 99% of 10-Ks since 2012 but leaves out shares held by insiders.

**Outcomes.** From the same SEC data I collect bankruptcy filings (8-K Item 1.03; 1,144 companies), restatement notices (8-K Item 4.02, "non-reliance on previously issued financial statements"; 2,904 companies), auditor changes (8-K Item 4.01; 7,509), late annual reports (Form NT 10-K; 6,774) and amended annual reports (10-K/A; 8,860).

Banks, insurers and other financial companies (SIC 6000-6799) are excluded from all tests because the scores were not designed for them.

## 3. Method

**Classic scores.** I compute the Altman Z-Score, Altman's Z'' (which replaces market value with book equity), the Piotroski F-Score and the Beneish M-Score for each company-year, using the original thresholds: Z below 1.8 is distress, F of 3 or less is weak, and M above -1.78 suggests manipulation.

**Faultline models.** Two gradient-boosted tree models (scikit-learn's HistGradientBoostingClassifier) use 46 inputs per company-year: every component of the three scores, company size, return on assets, cash flow, leverage, revenue growth, the number of days between year end and the 10-K filing, counts of warning events in the prior 24 months, and five 0/1 flags for warning phrases in the 10-K text. One model predicts a bankruptcy filing within 24 months after the 10-K; the other predicts a restatement notice in the same window.

**Walk-forward testing.** To score filings made in year Y, a model is trained only on company-years whose 24-month outcome was known before January 1 of Y. Test years are 2016 to 2023, the last years whose outcomes are fully known. No test-year information reaches training.

**Measures.** AUC is the probability that a randomly chosen company that went bankrupt is ranked riskier than one that did not (0.5 is random, 1 is perfect). I also report the share of events caught when flagging the riskiest 5%, 10% or 20% of companies, and comparisons at a matched alarm rate. Because bankruptcies are about 2% of company-years, plain accuracy is not useful.

## 4. Results

**Classic scores alone (2012-2023).** In Altman's distress zone 12 to 24 months before a bankruptcy filing: 83.3% of the 419 bankruptcies that had a score in that window. But 49.2% of all company-years were in the distress zone. Flagged company-years were followed by bankruptcy 2.38% of the time, against 0.45% for the rest (5.3 times as often). Restricted to companies with at least $100 million in revenue, the hit rate was 76.4% and the alarm rate 34.3%. The Piotroski F-Score flagged 40.3% of bankruptcies at a 17.9% alarm rate. The Beneish M-Score flagged 26.1% of 555 restatements at a 13.7% alarm rate.

**Faultline vs Altman (2016-2023, out of sample).** On 25,169 company-years with an Altman score and 539 bankruptcies within two years:

| | Altman Z | Faultline |
|---|---|---|
| AUC | 0.71 | 0.85 |
| Caught in riskiest 5% / 10% / 20% | 5% / 13% / 38% | 37% / 53% / 70% |
| Caught at Altman's alarm rate (50%) | 85.5% | 92.8% |
| Alarm rate needed to catch 85.5% | 50.3% | 37.2% |

**What drives the gain (question 2).** Using only the components of the three classic scores, the model already reaches an AUC of 0.82, so most of the improvement comes from combining the same ingredients better than the fixed 1968 weights do. Adding size and fundamentals raises it to 0.84. Adding filing behaviour and warning events adds little (0.85). The events do carry signal on their own (AUC 0.65), but the financial statements already contain most of it.

**10-K wording (question 5).** Using SEC's full-text search, I flagged every 10-K containing five warning phrases: "raise substantial doubt" (going concern; 28,157 company-years), "recurring losses from operations" (9,132), "identified a material weakness" (6,147), "internal control over financial reporting was not effective" (12,037) and "have been restated" (5,071). Company-years with the going-concern phrase were followed by bankruptcy 3.2% of the time against 1.5% without it. On their own the five flags reached an AUC of 0.63 for bankruptcy and 0.61 for restatements, but adding them to the model changed nothing (bankruptcy 0.847 before and after; restatement 0.738 vs 0.737). Simple phrase flags are crude: the same words appear in boilerplate and hypothetical risk factors, and what they signal is mostly already in the financial statements.

**Restatements.** On 14,421 company-years with a Beneish score and 479 restatement notices within two years, the Beneish M-Score's AUC was 0.52 and Faultline's 0.74. Flagging the riskiest 10% caught 19% of restatements with Beneish and 28% with Faultline.

**Stock outcomes.** Free daily prices for companies that no longer trade are not available, so I approximate returns with the public float on 10-K cover pages: the change from the float reported in the year t+1 10-K to the one in the year t+2 10-K, a window that starts after the year-t score was public. Bankruptcies count as -100%, companies that stopped filing without a change of control as -50%, and buyouts are left out. For companies with at least $10 million of public float (20,648 company-years, 2016-2022), Faultline's riskiest 10% had a median change of -13.6% against +2.9% for its safest half; 33.7% lost half their value or more against 11.2%, and 10.8% were wiped out against 1.0%. The average was not lower (about +20% vs +15% with single returns capped at +300%), because a few flagged stocks rose enormously and share issues raise market value. The median gap held in 5 of 7 years; 2020, a broad rebound year, was the clear exception.

**Example.** Sears Holdings entered Altman's distress zone with its 10-K filed in March 2015 and stayed there until its last 10-K in March 2018, when Faultline ranked it riskier than 99% of filers that year. It filed for bankruptcy in October 2018.

## 5. Robustness

Faultline's AUC beat Altman's in every test year, from 0.77 vs 0.72 (2018) to 0.93 vs 0.71 (2020), and in every size group: revenue under $100 million (0.77 vs 0.62), $100 million to $1 billion (0.88 vs 0.81) and over $1 billion (0.90 vs 0.78).

Calibration is good at the top and low in the middle. In the riskiest tenth of company-years the model predicted 10.8% and 9.5% went bankrupt. In the middle tenths it predicted roughly 60% of the observed rate (for example 0.71% predicted vs 1.22% observed).

The most important inputs, measured by how much AUC falls when one input is shuffled, were company size (assets), return on assets, public float, revenue, working capital to assets, operating cash flow to assets and EBIT to assets.

## 6. Limits

- The main outcome counts only formal bankruptcy filings. Small companies often stop filing instead, which likely explains part of why size is the most important input. A second outcome, a "distress exit" (bankruptcy, or going dark without a change of control), gives 1,278 events in the test years instead of 539. Faultline still ranks them better than Altman (AUC 0.84 vs 0.75; 0.73 vs 0.67 for companies under $100 million in revenue), but the gap is smaller.
- About 40% of bankrupt companies had no score in the warning window, usually because they had stopped filing or left out a needed number.
- Public float leaves out insider shares, so Altman's market-value ratio is understated for closely held companies.
- One model setting was used without tuning.
- These are rankings, not forecasts for single companies, and not investment advice.

## 7. Conclusion

When tested on all US filers with the failures included and only the information public at the time, the classic scores do warn, but Altman's original cut-offs flag about half of all companies and Beneish's ranking of restatement risk is close to random. A model that combines the same public data, trained only on the past, ranks bankruptcy risk much better in every year and size group. Flagged companies' stock usually lost value, though a few large winners kept the average up. Simple warning phrases in 10-K text added nothing beyond the numbers. The next steps are better price data for a true trading test and reading 10-K text with methods smarter than exact phrases.

## References

- Altman, E. I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. *Journal of Finance*, 23(4), 589-609.
- Altman, E. I., Hartzell, J., & Peck, M. (1995). *Emerging markets corporate bonds: A scoring system.* Salomon Brothers.
- Beneish, M. D. (1999). The detection of earnings manipulation. *Financial Analysts Journal*, 55(5), 24-36.
- Dechow, P. M., Ge, W., Larson, C. R., & Sloan, R. G. (2011). Predicting material accounting misstatements. *Contemporary Accounting Research*, 28(1), 17-82.
- Piotroski, J. D. (2000). Value investing: The use of historical financial statement information to separate winners from losers. *Journal of Accounting Research*, 38, 1-41.
- Shumway, T. (2001). Forecasting bankruptcy more accurately: A simple hazard model. *Journal of Business*, 74(1), 101-124.
- U.S. Securities and Exchange Commission. EDGAR XBRL companyfacts and submissions data, accessed November 2026.

## Data and code

All code is at https://github.com/mahirzmansuri-hash/earnings-scanner. Results tables are in `vault/research/results.md`. The live site is https://mahirzmansuri-hash.github.io/earnings-scanner/.
