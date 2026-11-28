"""Free data API: static JSON files published with the site (no server, no key, no sign-up).

Built by src/web/build.py into site/api/v1/:
  companies.json      every scored company, latest scores (one row each)
  c/<cik>.json        one company: every 10-K and 10-Q score, filing events, SEC accounting cases, why-this-score
  receipts.json       bankruptcies of the last 12 months and the last score before each
  meta.json           data date, field descriptions, version
Docs page: site/api/index.html. GitHub Pages serves these with CORS open, so browsers and scripts can fetch them.
Same numbers as the website; every score is point-in-time and walk-forward (see methodology).
"""
import json
import math

import pandas as pd

from src.web.style import SITE_URL, page

VERSION = "v1"
FIELDS = {
    "cik": "SEC Central Index Key (company id)",
    "name": "company name",
    "ticker": "main ticker, if any",
    "industry": "SEC industry (SIC) description",
    "status": "active or inactive (no filings for over a year: delisted, acquired or bankrupt)",
    "filed": "filing date of the 10-K behind the scores (the date the data became public)",
    "period_end": "fiscal period end of that 10-K",
    "bankruptcy_risk": "calibrated probability of a bankruptcy filing within 2 years (0-1)",
    "bankruptcy_percentile": "share of 10-Ks filed in the previous 365 days with a lower risk (0-1)",
    "restatement_risk": "calibrated probability of a restatement notice (8-K Item 4.02) within 2 years (0-1)",
    "restatement_percentile": "share of 10-Ks filed in the previous 365 days with a lower restatement risk (0-1)",
    "altman_z": "Altman Z-Score (1968); below 1.8 distress, above 3 safe",
    "piotroski_f": "Piotroski F-Score (0-9); higher is stronger",
    "beneish_m": "Beneish M-Score; above -1.78 flags possible earnings manipulation",
    "latest_10q": "latest 10-Q update: filing date, bankruptcy risk and percentile among 10-Qs of the previous 365 days",
}


def _num(x, d=4):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else round(x, d)


def _date(x):
    return None if x is None or x != x else str(pd.Timestamp(x).date())


def _tick(t):
    return t.split(" | ")[0] if isinstance(t, str) and t else None


def summary_row(r, q) -> dict:
    return {"cik": int(r.cik), "name": r.name, "ticker": _tick(r.tickers),
            "industry": r.sic_description if isinstance(r.sic_description, str) else None, "status": r.status,
            "filed": _date(r.available_date), "period_end": _date(r.period_end),
            "bankruptcy_risk": _num(r.bankruptcy_risk), "bankruptcy_percentile": _num(r.bankruptcy_pctile, 3),
            "restatement_risk": _num(r.restatement_risk), "restatement_percentile": _num(r.restatement_pctile, 3),
            "altman_z": _num(r.z_score, 2), "piotroski_f": None if r.f_score != r.f_score else int(r.f_score),
            "beneish_m": _num(r.m_score, 2),
            "latest_10q": None if q is None else {"filed": _date(q.available_date), "bankruptcy_risk": _num(q.q_risk),
                                                  "bankruptcy_percentile": _num(q.q_pctile, 3)},
            "url": f"{SITE_URL}c/{int(r.cik)}.html"}


def company_json(r, q, hist, qhist, evs, why, cases) -> dict:
    out = summary_row(r, q)
    out["history_10k"] = [{"filed": _date(h.available_date), "period_end": _date(h.period_end),
                           "bankruptcy_risk": _num(h.bankruptcy_risk), "bankruptcy_percentile": _num(h.bankruptcy_pctile, 3),
                           "restatement_risk": _num(h.restatement_risk), "restatement_percentile": _num(h.restatement_pctile, 3),
                           "altman_z": _num(h.z_score, 2), "piotroski_f": None if h.f_score != h.f_score else int(h.f_score),
                           "beneish_m": _num(h.m_score, 2), "revenue": _num(h.revenue, 0), "net_income": _num(h.net_income, 0),
                           "operating_cash_flow": _num(h.cfo, 0), "total_assets": _num(h.total_assets, 0)}
                          for h in hist.itertuples()]
    out["history_10q"] = [{"filed": _date(x.available_date), "period_end": _date(x.period_end), "accession": x.accn,
                           "bankruptcy_risk": _num(x.q_risk), "bankruptcy_percentile": _num(x.q_pctile, 3)} for x in qhist.itertuples()]
    out["events"] = [{"event": ev.event, "filed": _date(ev.filed), "accession": ev.accn} for ev in evs.itertuples()]
    out["why_latest"] = [{"area": w.label, "effect_log_odds": _num(w.effect, 3), "detail": w.detail}
                         for w in why.sort_values("effect", key=abs, ascending=False).itertuples()] if why is not None else []
    out["sec_accounting_cases"] = [{"date": c.date, "release": c.url, "misstated_years": json.loads(c.years)}
                                   for c in cases.itertuples()] if cases is not None else []
    return out


def write_api(site, latest, hist_by, rq_all, ev_by, why_by, aaer_by, receipts, as_of) -> int:
    root = site / "api" / VERSION
    (root / "c").mkdir(parents=True, exist_ok=True)
    rq_latest = {k: g.iloc[-1] for k, g in rq_all.groupby("cik")}
    rq_by = {k: g for k, g in rq_all.groupby("cik")}
    empty_q = rq_all.iloc[0:0]
    rows = []
    for r in latest.itertuples():
        q = rq_latest.get(r.cik)
        rows.append(summary_row(r, q))
        why = why_by.get((r.cik, pd.Timestamp(r.period_end)))
        doc = company_json(r, q, hist_by.get(r.cik, pd.DataFrame()), rq_by.get(r.cik, empty_q),
                           ev_by.get(r.cik, pd.DataFrame(columns=["event", "filed", "accn"])), why, aaer_by.get(r.cik))
        (root / "c" / f"{int(r.cik)}.json").write_text(json.dumps(doc, separators=(",", ":"), allow_nan=False))
    (root / "companies.json").write_text(json.dumps({"as_of": str(as_of), "count": len(rows), "companies": rows},
                                                    separators=(",", ":"), allow_nan=False))
    rec = [{"cik": int(x.cik), "bankruptcy_filed": _date(x.filed), "last_score_filed": _date(x.score_date), "last_score_form": x.src if isinstance(x.src, str) else None,
            "last_bankruptcy_percentile": _num(x.p, 3), "first_in_riskiest_10pct": _date(x.first_top)} for x in receipts.itertuples()]
    (root / "receipts.json").write_text(json.dumps({"as_of": str(as_of), "rows": rec}, separators=(",", ":"), allow_nan=False))
    (root / "meta.json").write_text(json.dumps({"version": VERSION, "as_of": str(as_of), "fields": FIELDS,
                                                "source": "SEC EDGAR (XBRL company facts, filing index)",
                                                "docs": f"{SITE_URL}api/index.html"}, indent=1))
    ex = f"{SITE_URL}api/{VERSION}/c/320193.json"
    body = f"""<section><h1>Free data API</h1>
<p>Every score on Faultline is also available as plain JSON files: no key, no sign-up, updated weekly with the site. Fetch them from a
browser, a spreadsheet, Python or anything else. Data as of {as_of}.</p>
<div class="tbl"><table><thead><tr><th>File</th><th>What's in it</th></tr></thead><tbody>
<tr><td class="mono"><a href="{VERSION}/companies.json">api/{VERSION}/companies.json</a></td><td>Every scored company ({len(rows):,}) with its latest scores (about 3 MB)</td></tr>
<tr><td class="mono">api/{VERSION}/c/&lt;cik&gt;.json</td><td>One company: every 10-K and 10-Q score since 2016, filing events, SEC accounting cases, what drives the latest score.
Example: <a href="{VERSION}/c/320193.json">Apple (CIK 320193)</a></td></tr>
<tr><td class="mono"><a href="{VERSION}/receipts.json">api/{VERSION}/receipts.json</a></td><td>Bankruptcies of the last 12 months and the last score before each</td></tr>
<tr><td class="mono"><a href="{VERSION}/meta.json">api/{VERSION}/meta.json</a></td><td>Data date and what each field means</td></tr>
</tbody></table></div>
<h2>Example (Python)</h2>
<pre class="mono">import requests
apple = requests.get("{ex}").json()
print(apple["bankruptcy_percentile"], apple["history_10k"][-1])</pre>
<h2>Fields</h2><ul>{"".join(f"<li><span class=mono>{k}</span>: {v}</li>" for k, v in FIELDS.items())}</ul>
<p class="note">Point in time: each score uses only filings public on its date, from a model trained only on earlier outcomes. Companies
are looked up by SEC CIK (find it on any company page). Banks and insurers are not scored. Research data, not investment advice;
if you use it, please link back to Faultline.</p></section>"""
    ld = {"@context": "https://schema.org", "@type": "Dataset", "name": "Faultline bankruptcy and accounting-risk scores",
          "description": "Point-in-time bankruptcy and restatement risk scores, Altman Z, Piotroski F and Beneish M scores for US public "
                         "companies, computed from SEC EDGAR XBRL filings and updated weekly.",
          "url": f"{SITE_URL}api/index.html", "isAccessibleForFree": True, "dateModified": str(as_of),
          "creator": {"@type": "Person", "name": "Mahir"}, "temporalCoverage": "2016/..",
          "spatialCoverage": "United States", "keywords": ["bankruptcy prediction", "Altman Z-Score", "SEC EDGAR", "forensic accounting"],
          "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{SITE_URL}api/{VERSION}/companies.json"}]}
    body += f'<script type="application/ld+json">{json.dumps(ld)}</script>'
    (site / "api" / "index.html").write_text(page("Free data API · Faultline", body,
        "Free JSON API with bankruptcy and accounting-risk scores for every US public company. No key, no sign-up.", root="../"))
    return len(rows)
