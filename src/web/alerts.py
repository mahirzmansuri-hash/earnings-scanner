"""Alerts: what changed for each company, built from the same tables as the site.

Used by src/web/build.py. Every alert is a dated fact with a source:

  entered_high     a new 10-K or 10-Q puts the company in the riskiest 5% of filers, after it was not
  risk_jump        bankruptcy-risk percentile up 20+ points vs the company's previous filing, now in the riskiest 20%
  bankruptcy       8-K Item 1.03          non_reliance  8-K Item 4.02 (past statements can't be relied on)
  auditor_change   8-K Item 4.01          late_10k      NT 10-K (annual report will be late)
  going_concern    the 10-K uses "raise substantial doubt" and the previous one did not
  sec_case         named in an SEC accounting enforcement release (AAER)

Outputs (in site/): alerts.html (last 90 days, filters, watchlist), feed.xml (Atom, main alerts),
c/<cik>.xml (one feed per company), digest/<date>.html (weekly summary, the future newsletter).
"""
import html
import json

import pandas as pd

KINDS = {  # name, severity (high / elevated / watch), included in the main feed
    "entered_high": ("Entered riskiest 5%", "high", True),
    "risk_jump": ("Risk jump", "elevated", True),
    "bankruptcy": ("Bankruptcy filing", "high", True),
    "non_reliance": ("Restatement notice", "high", True),
    "going_concern": ("Going-concern wording", "elevated", True),
    "sec_case": ("SEC accounting case", "high", True),
    "auditor_change": ("Auditor change", "watch", False),
    "late_10k": ("Late 10-K notice", "watch", False),
}
KINDS_MAIN = {k: v[2] for k, v in KINDS.items()}
SEV_VAR = {"high": "--risk", "elevated": "--watch", "watch": "--ink-2"}
EDGAR = "https://www.sec.gov/Archives/edgar/data/{cik}/{accn}/"


def e(x) -> str:
    return html.escape("" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x))


def _pct(p) -> str:
    return f"{p * 100:.0f}%"


def score_alerts(con) -> list[dict]:
    """Percentile changes along each company's timeline of 10-K and 10-Q scores."""
    t = con.execute("""
        SELECT cik, available_date::DATE AS d, bankruptcy_pctile AS p, '10-K' AS form, NULL AS accn FROM risk WHERE bankruptcy_pctile IS NOT NULL
        UNION ALL
        SELECT cik, available_date::DATE, q_pctile, '10-Q', accn FROM risk_q WHERE q_pctile IS NOT NULL
        ORDER BY cik, d, form""").df()
    t["prev"] = t.groupby("cik")["p"].shift()
    t["prev_form"] = t.groupby("cik")["form"].shift()
    out = []
    for r in t[t["prev"].notna()].itertuples():
        base = f"with the {r.form} filed {r.d.date() if hasattr(r.d, 'date') else r.d}"
        if r.p >= 0.95 and r.prev < 0.95:
            out.append({"cik": r.cik, "date": r.d, "kind": "entered_high",
                        "text": f"Bankruptcy risk entered the riskiest 5%: riskier than {_pct(r.p)} of filers {base} (was {_pct(r.prev)})."})
        elif r.p - r.prev >= 0.20 and r.p >= 0.80:
            out.append({"cik": r.cik, "date": r.d, "kind": "risk_jump",
                        "text": f"Bankruptcy risk rose from riskier than {_pct(r.prev)} to {_pct(r.p)} of filers {base}."})
    return out


def event_alerts(con) -> list[dict]:
    ev = con.execute("""SELECT cik, filed AS date, event, accn FROM events
                        WHERE event IN ('bankruptcy', 'non_reliance', 'auditor_change', 'late_10k') AND filed >= DATE '2016-01-01'""").df()
    words = {"bankruptcy": "Filed an 8-K under Item 1.03 (bankruptcy or receivership).",
             "non_reliance": "Filed an 8-K under Item 4.02: previously issued financial statements should no longer be relied on.",
             "auditor_change": "Filed an 8-K under Item 4.01: change of auditor.",
             "late_10k": "Filed an NT 10-K: the annual report will be late."}
    out = [{"cik": r.cik, "date": r.date, "kind": r.event, "text": words[r.event],
            "link": EDGAR.format(cik=r.cik, accn=str(r.accn).replace("-", "")) if isinstance(r.accn, str) else None}
           for r in ev.itertuples()]
    gc = con.execute("""
        SELECT t.cik, a.available_date::DATE AS date, t.accn, t.tx_gc_doubt,
               LAG(t.tx_gc_doubt) OVER (PARTITION BY t.cik ORDER BY t.period_end) AS prev
        FROM text_signals t JOIN annual_first a USING (cik, period_end)""").df()
    gc = gc[(gc["tx_gc_doubt"] == 1) & (gc["prev"] == 0) & (pd.to_datetime(gc["date"]) >= "2016-01-01")]
    out += [{"cik": r.cik, "date": r.date, "kind": "going_concern",
             "text": 'The new 10-K says events "raise substantial doubt" (going-concern wording); the previous 10-K did not.',
             "link": EDGAR.format(cik=r.cik, accn=str(r.accn).replace("-", ""))} for r in gc.itertuples()]
    return out


def case_alerts(cases: pd.DataFrame) -> list[dict]:
    c = cases[(cases["kind"] == "accounting") & (cases["n_candidates"] == 1)]
    url = lambda u: u if u.startswith("http") else "https://www.sec.gov" + u
    return [{"cik": r.cik, "date": pd.Timestamp(r.date), "kind": "sec_case", "link": url(r.url),
             "text": f"Named in SEC Accounting and Auditing Enforcement Release AAER-{r.aaer}."} for r in c.itertuples()]


def build_alerts(con, cases: pd.DataFrame, companies: pd.DataFrame) -> pd.DataFrame:
    a = pd.DataFrame(score_alerts(con) + event_alerts(con) + case_alerts(cases))
    a["date"] = pd.to_datetime(a["date"])
    a["cik"] = a["cik"].astype(int)
    a = a[a["cik"].isin(set(companies["cik"]))]                       # only companies with a page
    a = a.merge(companies[["cik", "name", "tickers"]], on="cik", how="left")
    a["ticker"] = a["tickers"].map(lambda t: t.split(" | ")[0] if isinstance(t, str) else "")
    a["label"] = a["kind"].map(lambda k: KINDS[k][0])
    a["severity"] = a["kind"].map(lambda k: KINDS[k][1])
    order = {k: i for i, k in enumerate(KINDS)}
    a = a.assign(_o=a["kind"].map(order)).sort_values(["date", "_o", "cik"], ascending=[False, True, True]).drop(columns="_o")
    return a.drop(columns=["tickers"]).reset_index(drop=True)


# ---------------------------------------------------------------- pages and feeds

ALERTS_JS = """<script>
(function(){
let W=[];try{W=JSON.parse(localStorage.getItem('fl_watch')||'[]')}catch(e){}
const tb=document.getElementById('atb'),kind=document.getElementById('akind'),wo=document.getElementById('awatch'),cnt=document.getElementById('acount');
let A=[];
function draw(){const k=kind.value,w=wo.checked;const rows=A.filter(a=>(!k||a.k===k)&&(!w||W.includes(a.c)));
cnt.textContent=rows.length.toLocaleString()+(rows.length===1?' alert':' alerts')+(w?' on your watchlist ('+W.length+(W.length===1?' company)':' companies)'):'');
tb.innerHTML=rows.slice(0,600).map(a=>'<tr><td class="d">'+a.d+'</td><td><a href="c/'+a.c+'.html">'+a.n+'</a>'+(a.t?' <span class="mono dim">'+a.t+'</span>':'')+'</td><td><span class="read" style="--c:var('+a.v+')">'+a.l+'</span><span class="sub">'+a.x+(a.u?' <a href="'+a.u+'">Source</a>':'')+'</span></td></tr>').join('')||'<tr><td colspan="3" class="dim">'+(w&&!W.length?'Your watchlist is empty. Open any company page and choose Add to watchlist.':'No alerts match.')+'</td></tr>';}
fetch('data/alerts.json').then(r=>r.json()).then(d=>{A=d;draw()}).catch(()=>{tb.innerHTML='<tr><td colspan="3">Could not load alerts.</td></tr>'});
kind.addEventListener('change',draw);wo.addEventListener('change',draw);
})();
</script>"""

WATCH_JS = """<script>
(function(){const b=document.getElementById('watch'),c=+b.dataset.cik;let W=[];
try{W=JSON.parse(localStorage.getItem('fl_watch')||'[]')}catch(e){}
const show=()=>{b.textContent=W.includes(c)?'On your watchlist (remove)':'Add to watchlist'};show();
b.addEventListener('click',()=>{W=W.includes(c)?W.filter(x=>x!==c):W.concat([c]);try{localStorage.setItem('fl_watch',JSON.stringify(W))}catch(e){}show()});})();
</script>"""


def watch_box(cik: int, n_alerts: int) -> str:
    """Company-page block: watchlist button and this company's alert feed."""
    return (f'<section class="watchbox"><button id="watch" class="btn" data-cik="{cik}">Add to watchlist</button> '
            f'<span class="dim">Watched companies can be filtered on the <a href="../alerts.html">Alerts</a> page '
            f'(saved in this browser only). <a href="{cik}.xml">Follow this company\'s alerts (RSS)</a>'
            f'{f" · {n_alerts} alerts since 2016" if n_alerts else ""}.</span></section>' + WATCH_JS)


def alerts_json(a: pd.DataFrame, as_of) -> str:
    recent = a[a["date"] >= pd.Timestamp(as_of) - pd.Timedelta(days=90)]
    rows = [{"d": str(r.date.date()), "c": int(r.cik), "n": e(r.name), "t": e(r.ticker), "k": r.kind, "l": r.label,
             "v": SEV_VAR[r.severity], "x": e(r.text), "u": r.link if isinstance(r.link, str) else ""} for r in recent.itertuples()]
    return json.dumps(rows, separators=(",", ":"))


def alerts_page(a: pd.DataFrame, as_of, page) -> str:
    from src.web.style import subscribe_box
    recent = a[a["date"] >= pd.Timestamp(as_of) - pd.Timedelta(days=90)]
    counts = recent["kind"].value_counts()
    opts = "".join(f'<option value="{k}">{v[0]} ({counts.get(k, 0):,})</option>' for k, v in KINDS.items())
    body = f"""<section><h1>Alerts</h1><p>What changed in the last 90 days, newest first: companies whose bankruptcy risk jumped or
entered the riskiest 5% with a new 10-K or 10-Q, and warning filings (bankruptcy, restatement notices, auditor changes, late
annual reports, new going-concern wording, SEC accounting cases). Data as of {as_of}.</p>
<p class="dim">Follow along: <a href="feed.xml">main alerts feed (RSS)</a>, a feed on every company page, or the
<a href="digest/index.html">weekly digest</a>. Add companies to your watchlist from their pages to filter this list.</p>{subscribe_box()}
<div class="controls"><label>Type <select id="akind"><option value="">All types ({len(recent):,})</option>{opts}</select></label>
<label><input type="checkbox" id="awatch"> Watchlist only</label> <span id="acount" class="dim"></span></div>
<div class="tbl"><table><thead><tr><th>Date</th><th>Company</th><th>Alert</th></tr></thead>
<tbody id="atb"><tr><td colspan="3" class="dim">Loading alerts...</td></tr></tbody></table></div>
<p class="note">Risk alerts use Faultline's bankruptcy-risk percentile; a 10-Q is compared with the company's previous 10-K or 10-Q.
Alerts are research signals, not predictions about any single company, and not investment advice.</p></section>""" + ALERTS_JS
    return page("Alerts · Faultline", body, "Bankruptcy-risk jumps and warning filings for US public companies, updated weekly.", active="alerts.html")


def atom(title: str, self_url: str, alt_url: str, rows: pd.DataFrame, site_url: str, updated) -> str:
    def entry(r):
        uid = f"{site_url}c/{r.cik}.html#{r.kind}-{r.date.date()}"
        return (f"<entry><id>{e(uid)}</id><title>{e(r.name)}: {e(r.label)}</title><updated>{r.date.date()}T00:00:00Z</updated>"
                f'<link href="{site_url}c/{r.cik}.html"/><summary>{e(r.text)}</summary></entry>')
    return ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">'
            f"<title>{e(title)}</title><id>{e(self_url)}</id><updated>{updated}T00:00:00Z</updated>"
            f'<link rel="self" href="{e(self_url)}"/><link href="{e(alt_url)}"/><author><name>Faultline</name></author>'
            + "".join(entry(r) for r in rows.itertuples()) + "</feed>")


def _who(r) -> str:
    return f"{r.name}{f' ({r.ticker})' if r.ticker else ''}"


def _md(t: str) -> str:
    """Escape characters that would break a Markdown link label."""
    return t.replace("[", "(").replace("]", ")")


def week_digest(a: pd.DataFrame, end: pd.Timestamp, risk_before) -> tuple[str, str]:
    from src.web.style import SITE_URL
    """(html body, markdown) for the 7 days ending `end`. risk_before(cik, date) -> last percentile before that date."""
    start = end - pd.Timedelta(days=6)
    w = a[(a["date"] >= start) & (a["date"] <= end)]
    def lines(kind, limit=15, with_prior=False):
        g = w[w["kind"] == kind].head(limit)
        items = []
        for r in g.itertuples():
            prior = ""
            if with_prior:
                p = risk_before(r.cik, r.date)
                prior = f" Faultline's last score before it: riskier than {_pct(p)} of filers." if p == p and p is not None else " No earlier Faultline score."
            items.append((r, f"{_who(r)}: {r.text}{prior}"))
        return items, int((w["kind"] == kind).sum())
    secs = [("Bankruptcy filings", "bankruptcy", True), ("Entered the riskiest 5%", "entered_high", False),
            ("Biggest risk jumps", "risk_jump", False), ("Restatement notices", "non_reliance", False),
            ("New going-concern wording", "going_concern", False), ("SEC accounting cases", "sec_case", False)]
    hb, md = [], [f"# Faultline weekly: {start.date()} to {end.date()}\n"]
    summary = "This week: " + " · ".join(f"{n} {int((w['kind'] == k).sum())}" for n, k, _ in secs)
    hb.append(f"<p>{summary}.</p>")
    md.append(summary + ".\n")
    for name, kind, prior in secs:
        items, n = lines(kind, with_prior=prior)
        if not n:
            continue
        more = f" (showing {len(items)} of {n})" if n > len(items) else ""
        hb.append(f"<h2>{name}{more}</h2><ul>" + "".join(f'<li><a href="../c/{r.cik}.html">{e(t)}</a></li>' for r, t in items) + "</ul>")
        md.append(f"## {name}{more}\n" + "".join(f"- [{_md(_who(r))}]({SITE_URL}c/{r.cik}.html): {t[len(_who(r)) + 2:]}\n" for r, t in items))
    return "".join(hb), "\n".join(md)
