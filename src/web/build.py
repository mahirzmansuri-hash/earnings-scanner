"""Build the Faultline website as plain static files in site/.

Run:  python -m src.web.build      Preview:  python -m http.server -d site 8000

One page per scored company (site/c/<cik>.html), plus home, screener, track record,
methodology and about. No framework: Python writes HTML, charts are inline SVG,
the screener and search use one JSON file and a little vanilla JavaScript.
"""
import html
import json
import math
import shutil
from pathlib import Path

import duckdb
import pandas as pd

from src.config import DB_PATH, ROOT
from src.web.style import page

SITE = ROOT / "site"
PROC = ROOT / "data" / "processed"
def e(s):
    """HTML-escape text; missing values (NaN/None) become empty strings."""
    return html.escape(s) if isinstance(s, str) else ""


def txt(s):
    return s if isinstance(s, str) else ""


# ---------- formatting ----------
def money(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    a = abs(x)
    s = f"${a/1e9:,.1f}B" if a >= 1e9 else f"${a/1e6:,.1f}M" if a >= 1e6 else f"${a/1e3:,.0f}K"
    return ("-" if x < 0 else "") + s


def num(x, d=2):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:,.{d}f}"


def band(p):
    """Percentile among companies filing that year -> (word, css color)."""
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return ("Not scored", "--ink-2")
    if p >= 0.95:
        return ("High", "--risk")
    if p >= 0.80:
        return ("Elevated", "--watch")
    return ("Normal", "--safe")


def pct_text(p):
    return "n/a" if p is None or (isinstance(p, float) and math.isnan(p)) else f"riskier than {p*100:.0f}% of filers that year"


def reading(p):
    w, c = band(p)
    return f'<span class="read" style="--c:var({c})">{w}</span>'


def isnan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


# ---------- data ----------
def load(con):
    latest = con.execute("""
    WITH r AS (
      SELECT r.*, s.z_score, s.z_zone, s.z2_score, s.f_score, s.m_score, s.dsri, s.tata, s.sgi,
             a.revenue, a.net_income, a.cfo, a.total_assets, a.equity, a.public_float,
             ROW_NUMBER() OVER (PARTITION BY r.cik ORDER BY r.available_date DESC) AS rn
      , tx.tx_gc_doubt, tx.tx_mw_identified, tx.tx_icfr_not_effective, tx.tx_restated
      FROM risk r JOIN scores s USING (cik, period_end) JOIN annual_first a USING (cik, period_end)
      LEFT JOIN text_signals tx USING (cik, period_end)
      WHERE r.bankruptcy_risk IS NOT NULL)
    SELECT r.* EXCLUDE (rn), c.name, c.former_names, c.tickers, c.sic, c.sic_description, c.status,
           c.last_10k, c.fiscal_year_end
    FROM r JOIN companies c USING (cik) WHERE rn = 1""").df()
    hist = con.execute("""
    SELECT r.cik, r.period_end, r.available_date, r.bankruptcy_risk, r.bankruptcy_pctile, r.restatement_risk,
           r.restatement_pctile, s.z_score, s.z_zone, s.f_score, s.m_score, a.revenue, a.net_income, a.cfo, a.total_assets
    FROM risk r JOIN scores s USING (cik, period_end) JOIN annual_first a USING (cik, period_end)
    ORDER BY r.cik, r.period_end""").df()
    events = con.execute("SELECT cik, event, filed, accn FROM events ORDER BY cik, filed").df()
    accn = con.execute("""SELECT cik, period_end, accn_first FROM annual WHERE concept = 'total_assets'""").df()
    as_of = con.execute("SELECT MAX(filed) FROM facts").fetchone()[0]
    return latest, hist, events, accn, as_of


EVENT_WORDS = {"bankruptcy": "Bankruptcy filing (8-K Item 1.03)", "non_reliance": "Restatement notice (8-K Item 4.02)",
               "auditor_change": "Auditor change (8-K Item 4.01)", "late_10k": "Late annual report (NT 10-K)",
               "amended_10k": "Amended annual report (10-K/A)", "change_in_control": "Change in control (8-K Item 5.01)",
               "deregistration": "Ended SEC registration (Form 15)"}
RED_FLAG_EVENTS = {"bankruptcy", "non_reliance", "auditor_change", "late_10k"}


def red_flags(r, ev_recent):
    """Plain-English findings from the latest filing. Each one is a fact with its number."""
    out = []
    if r.z_zone == "distress":
        out.append(("Altman Z", "--risk", f"Altman Z-Score is {r.z_score:.2f}, below the 1.8 distress line."))
    if not isnan(r.equity) and r.equity < 0:
        out.append(("Equity", "--risk", f"Liabilities exceed assets: shareholders' equity is {money(r.equity)}."))
    if not isnan(r.net_income) and not isnan(r.cfo) and r.net_income < 0 and r.cfo < 0:
        out.append(("Cash burn", "--watch", f"Lost money ({money(r.net_income)}) and burned cash in operations ({money(r.cfo)})."))
    if not isnan(r.tata) and r.tata > 0.05:
        out.append(("Accruals", "--watch", f"Net income beat operating cash flow by an amount equal to {r.tata*100:.0f}% of total assets."))
    if not isnan(r.dsri) and r.dsri > 1.4:
        out.append(("Receivables", "--watch", f"Money owed by customers grew {r.dsri:.1f} times as fast as sales."))
    if not isnan(r.m_score) and r.m_score > -1.78:
        out.append(("Beneish M", "--watch", f"Beneish M-Score is {r.m_score:.2f}, above the -1.78 manipulation threshold."))
    if not isnan(r.sgi) and r.sgi < 0.8:
        out.append(("Sales", "--watch", f"Revenue fell {(1 - r.sgi)*100:.0f}% from the year before."))
    phrases = [("tx_gc_doubt", "Going concern", "--risk", "raise substantial doubt", "usually part of a going-concern warning"),
               ("tx_mw_identified", "Controls", "--watch", "identified a material weakness", "a flaw found in internal controls"),
               ("tx_icfr_not_effective", "Controls", "--watch", "internal control over financial reporting was not effective", ""),
               ("tx_restated", "Restatement", "--watch", "have been restated", "past figures were changed")]
    for col, label, c, phrase, why in phrases:
        if getattr(r, col, 0) == 1:
            out.append((label, c, f'The 10-K uses the phrase "{phrase}"' + (f" ({why})." if why else ".")))
    for ev in ev_recent:
        out.append(("Filing event", "--watch", f"{EVENT_WORDS[ev.event]} on {pd.Timestamp(ev.filed).date()}."))
    return out


def chart(h: pd.DataFrame, evs: pd.DataFrame) -> str:
    """Bankruptcy-risk percentile by filing date, with event markers."""
    h = h.dropna(subset=["bankruptcy_pctile"])
    if len(h) < 2:
        return ""
    d = pd.to_datetime(h["available_date"])
    x0, x1 = pd.Timestamp("2016-01-01"), max(d.max(), pd.Timestamp("2026-12-31"))
    W, H, L, R, T, B = 680, 200, 40, 12, 12, 26
    X = lambda t: L + (t - x0) / (x1 - x0) * (W - L - R)
    Y = lambda p: T + (1 - p) * (H - T - B)
    s = [f'<rect x="{L}" y="{Y(1)}" width="{W-L-R}" height="{Y(.95)-Y(1)}" fill="var(--risk-bg)"/>',
         f'<rect x="{L}" y="{Y(.95)}" width="{W-L-R}" height="{Y(.8)-Y(.95)}" fill="var(--watch-bg)"/>']
    for p in (0, .5, .8, .95, 1):
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(p)}" y2="{Y(p)}" stroke="var(--rule)"/><text x="{L-6}" y="{Y(p)+4}" text-anchor="end">{p*100:.0f}</text>')
    for yr in range(2016, x1.year + 1, 2):
        s.append(f'<text x="{X(pd.Timestamp(f"{yr}-01-01"))}" y="{H-6}" text-anchor="middle">{yr}</text>')
    pts = " ".join(f"{X(t):.1f},{Y(p):.1f}" for t, p in zip(d, h["bankruptcy_pctile"]))
    s.append(f'<polyline points="{pts}" fill="none" stroke="var(--ink)" stroke-width="1.6"/>')
    for t, p in zip(d, h["bankruptcy_pctile"]):
        s.append(f'<rect x="{X(t)-3.5:.1f}" y="{Y(p)-3.5:.1f}" width="7" height="7" fill="var({band(p)[1]})"/>')
    for i, ev in enumerate(evs[evs["event"].isin(["bankruptcy", "non_reliance"])].itertuples()):
        t = pd.Timestamp(ev.filed)
        if x0 <= t <= x1:
            ly = T + 10 + (i % 3) * 13  # stagger labels so nearby events don't overlap
            c = "--risk" if ev.event == "bankruptcy" else "--watch"
            word = "Bankruptcy" if ev.event == "bankruptcy" else "Restatement"
            s.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T}" y2="{H-B}" stroke="var({c})" stroke-dasharray="3 3"/>'
                     f'<text x="{X(t)+4:.1f}" y="{ly}" style="fill:var({c})">{word}</text>')
    return (f'<div class="tbl"><svg viewBox="0 0 {W} {H}" width="100%" style="min-width:420px" role="img" '
            f'aria-label="Bankruptcy risk percentile by filing date">{"".join(s)}</svg></div>'
            '<p class="note">Percentile of bankruptcy risk among all companies that filed a 10-K the same year. '
            'Shaded bands: top 5% (high) and top 20% (elevated). Each point is scored by a model that had only seen '
            'outcomes known before that year.</p>')


def company_page(r, h, evs, accn_map, as_of):
    tick = r.tickers.split(" | ")[0] if isinstance(r.tickers, str) else ""
    title = f"{r['name']} ({tick}) bankruptcy and accounting risk" if tick else f"{r['name']} bankruptcy and accounting risk"
    dead = r.status == "inactive"
    recent = [ev for ev in evs.itertuples() if pd.Timestamp(ev.filed) > pd.Timestamp(r.available_date) - pd.Timedelta(days=730)
              and pd.Timestamp(ev.filed) <= pd.Timestamp(r.available_date) and ev.event in RED_FLAG_EVENTS]
    flags = red_flags(r, recent)
    later = evs[(pd.to_datetime(evs["filed"]) > pd.Timestamp(r.available_date)) & evs["event"].isin(["bankruptcy", "non_reliance"])]
    accn = accn_map.get((r.cik, pd.Timestamp(r.period_end)), "")
    parts = [f'<section><div class="label">{e(r.sic_description or "")} · CIK {r.cik}'
             f'{" · " + e(r.tickers) if isinstance(r.tickers, str) else ""}</div><h1>{e(r["name"])}</h1>']
    if isinstance(r.former_names, str) and r.former_names:
        parts.append(f'<p class="dim">Formerly: {e(r.former_names)}</p>')
    if dead:
        parts.append(f'<p class="banner">This company stopped filing annual reports. Its last 10-K was filed on {pd.Timestamp(r.last_10k).date()}. '
                     'The scores below are from that last report.</p>')
    parts.append('</section>')
    bw, bc = band(r.bankruptcy_pctile)
    rw, rc = band(r.restatement_pctile)
    parts.append(f"""<section><div class="label">From the 10-K filed {pd.Timestamp(r.available_date).date()}
    (fiscal year ended {pd.Timestamp(r.period_end).date()})</div>
    <div class="grid3">
      <div class="stat"><span class="label">Bankruptcy risk, next 2 years</span><span class="v">{r.bankruptcy_risk*100:.1f}%</span>
        <span class="read" style="--c:var({bc})">{bw}</span> <span class="dim">· {pct_text(r.bankruptcy_pctile)}</span></div>
      <div class="stat"><span class="label">Restatement risk, next 2 years</span><span class="v">{"n/a" if isnan(r.restatement_risk) else f"{r.restatement_risk*100:.1f}%"}</span>
        <span class="read" style="--c:var({rc})">{rw}</span> <span class="dim">· {pct_text(r.restatement_pctile)}</span></div>
      <div class="stat"><span class="label">Size</span><span class="v">{money(r.revenue)}</span>
        <span class="dim">revenue · {money(r.public_float)} public float</span></div>
    </div>
    <div class="tbl"><table><thead><tr><th>Classic score</th><th class="n">Value</th><th>Reading</th><th>Rule</th></tr></thead><tbody>
      <tr><td>Altman Z-Score</td><td class="n">{num(r.z_score)}</td><td>{zone_read(r.z_zone)}</td><td class="dim">Distress below 1.8, safe above 3.0</td></tr>
      <tr><td>Piotroski F-Score</td><td class="n">{"n/a" if isnan(r.f_score) else f"{r.f_score:.0f} / 9"}</td><td>{f_read(r.f_score)}</td><td class="dim">0-3 weak, 7-9 strong</td></tr>
      <tr><td>Beneish M-Score</td><td class="n">{num(r.m_score)}</td><td>{m_read(r.m_score)}</td><td class="dim">Above -1.78 suggests manipulation</td></tr>
    </tbody></table></div></section>""")
    if flags:
        items = "".join(f'<li><span class="chip" style="--c:var({c});--cb:var({c}-bg)">{e(k)}</span><span>{e(t)}</span></li>' for k, c, t in flags)
        parts.append(f'<section><h2>What stands out</h2><ul class="flags">{items}</ul></section>')
    else:
        parts.append('<section><h2>What stands out</h2><p class="dim">None of our warning rules fired on the latest filing.</p></section>')
    if len(later):
        lines = "".join(f"<li>{EVENT_WORDS[x.event]} on {pd.Timestamp(x.filed).date()}.</li>" for x in later.itertuples())
        parts.append(f'<section><h2>What happened after this filing</h2><ul>{lines}</ul></section>')
    hh = h[pd.to_datetime(h["available_date"]) >= pd.Timestamp("2016-01-01")]
    parts.append(f'<section><h2>Risk over time</h2>{chart(hh, evs)}')
    rows = "".join(
        f'<tr><td class="d">{pd.Timestamp(x.available_date).date()}</td><td class="d">{pd.Timestamp(x.period_end).date()}</td>'
        f'<td class="n">{money(x.revenue)}</td><td class="n">{money(x.net_income)}</td><td class="n">{money(x.cfo)}</td>'
        f'<td class="n">{num(x.z_score)}</td><td class="n">{"" if isnan(x.f_score) else f"{x.f_score:.0f}"}</td>'
        f'<td class="n">{num(x.m_score)}</td><td>{reading(x.bankruptcy_pctile)}</td></tr>'
        for x in h.sort_values("period_end", ascending=False).itertuples())
    parts.append(f"""<div class="tbl"><table><thead><tr><th>10-K filed</th><th>Year ended</th><th class="n">Revenue</th>
    <th class="n">Net income</th><th class="n">Operating cash</th><th class="n">Z</th><th class="n">F</th><th class="n">M</th>
    <th>Bankruptcy risk</th></tr></thead><tbody>{rows}</tbody></table></div>
    <p class="note">Figures are as first reported in each year's original 10-K, so they show what investors could see at the time.
    Source: SEC EDGAR XBRL. Latest filing: accession <span class="mono">{e(accn)}</span>.
    Data as of {as_of}. Research, not investment advice.</p></section>""")
    return page(e(title), "".join(parts), e(f"Faultline risk scores for {r['name']}: bankruptcy and accounting risk from SEC filings."), root="../")


def zone_read(z):
    m = {"safe": ("Safe", "--safe"), "gray": ("Gray zone", "--watch"), "distress": ("Distress", "--risk")}
    w, c = m.get(z, ("n/a", "--ink-2"))
    return f'<span class="read" style="--c:var({c})">{w}</span>'


def f_read(f):
    if isnan(f):
        return '<span class="read">n/a</span>'
    w, c = ("Strong", "--safe") if f >= 7 else ("Weak", "--risk") if f <= 3 else ("Neutral", "--watch")
    return f'<span class="read" style="--c:var({c})">{w}</span>'


def m_read(m):
    if isnan(m):
        return '<span class="read">n/a</span>'
    w, c = ("Flagged", "--risk") if m > -1.78 else ("Not flagged", "--safe")
    return f'<span class="read" style="--c:var({c})">{w}</span>'


# ---------- other pages ----------
SEARCH_JS = """<script>
(async()=>{const box=document.getElementById('q'),out=document.getElementById('res');let data=[];
try{data=await (await fetch('ROOTdata/companies.json')).json()}catch(e){}
box.addEventListener('input',()=>{const q=box.value.trim().toLowerCase();out.innerHTML='';if(q.length<2){out.hidden=true;return}
const hits=data.filter(c=>c.t.toLowerCase()===q||c.t.toLowerCase().split(' | ').includes(q)||c.n.toLowerCase().includes(q)||(c.f||'').toLowerCase().includes(q)).slice(0,12);
out.hidden=!hits.length;for(const c of hits){const a=document.createElement('a');a.href='ROOTc/'+c.c+'.html';
a.innerHTML='<span></span><span class="dim"></span>';a.children[0].textContent=c.n+(c.t?' ('+c.t.split(' | ')[0]+')':'');
a.children[1].textContent=c.s==='inactive'?'stopped filing':'';out.appendChild(a)}});})();
</script>"""


def table_rows(df, cols_fn):
    return "".join(cols_fn(r) for r in df.itertuples())


def home(latest, events, results, as_of):
    tr = results["composite"]
    abl = results["ablation"]
    top10 = abl["4. + 10-K text signals (full)"]["caught_if_flag_top"]["top_10pct"]
    alt10 = abl["altman_z (lowest first)"]["caught_if_flag_top"]["top_10pct"]
    recent = latest[pd.to_datetime(latest["available_date"]) >= pd.Timestamp(as_of) - pd.Timedelta(days=400)]
    top = recent.sort_values("bankruptcy_risk", ascending=False).head(40)
    rows = table_rows(top, lambda r: (
        f'<tr><td><a href="c/{r.cik}.html">{e(r.name)}</a></td><td class="mono">{e((r.tickers or "").split(" | ")[0]) if isinstance(r.tickers, str) else ""}</td>'
        f'<td class="dim">{e(txt(r.sic_description)[:34])}</td><td class="d">{pd.Timestamp(r.available_date).date()}</td>'
        f'<td class="n">{money(r.revenue)}</td><td class="n">{r.bankruptcy_risk*100:.1f}%</td><td class="n">{num(r.z_score)}</td></tr>'))
    # recent bankruptcies: what did the out-of-sample score say 12-24 months before?
    bk = events[(events["event"] == "bankruptcy") & (pd.to_datetime(events["filed"]) >= pd.Timestamp(as_of) - pd.Timedelta(days=730))]
    bk = bk.sort_values("filed").drop_duplicates("cik", keep="first")
    seen = []
    for ev in bk.itertuples():
        h = HIST.get(ev.cik)
        if h is None:
            continue
        w = h[(pd.to_datetime(h["available_date"]) <= pd.Timestamp(ev.filed) - pd.Timedelta(days=365)) &
              (pd.to_datetime(h["available_date"]) >= pd.Timestamp(ev.filed) - pd.Timedelta(days=730))]
        if len(w):
            x = w.iloc[-1]
            seen.append((ev.cik, NAMES.get(ev.cik, ""), pd.Timestamp(ev.filed).date(), x.available_date, x.bankruptcy_pctile))
    seen_rows = "".join(f'<tr><td><a href="c/{c}.html">{e(n)}</a></td><td class="d">{f}</td><td class="d">{pd.Timestamp(a).date()}</td>'
                        f'<td class="n">{p*100:.0f}</td><td>{reading(p)}</td></tr>' for c, n, f, a, p in seen)
    flagged = sum(p >= 0.8 for *_, p in seen)
    body = f"""<section><div class="label">Bankruptcy and accounting risk for {len(latest):,} US public companies</div>
<h1>Warnings from SEC filings, <span class="hl">tested against what actually happened.</span></h1>
<p class="dim">Faultline reads every annual report filed with the SEC since 2009, including companies that later went bankrupt,
scores each one, and checks the scores against real bankruptcies and restatements.</p>
<div class="search"><input id="q" type="search" placeholder="Search a company or ticker, e.g. Apple or AAPL" aria-label="Search companies" autocomplete="off">
<div id="res" class="results" hidden></div></div></section>
<section><h2>Track record</h2><div class="grid3">
<div class="stat"><span class="v">{top10*100:.0f}%</span>of companies that went bankrupt within two years of a filing were already in Faultline's riskiest 10%. Altman Z-Score's riskiest 10% held {alt10*100:.0f}%.</div>
<div class="stat"><span class="v">{tr['faultline_auc']:.2f}</span>ranking accuracy (AUC) for bankruptcy, against {tr['altman']['auc']:.2f} for Altman Z. 0.5 is a coin flip.</div>
<div class="stat"><span class="v">{tr['bankruptcies']}</span>bankruptcies in the test, across {tr['company_years']:,} company-years from {tr['test_years']}. The model never saw the years it was tested on.</div>
</div><p class="note"><a href="track-record.html">Full results and method</a>. Counted as a bankruptcy: a company's 8-K Item 1.03 filing within 24 months.</p></section>
<section><h2>Recent bankruptcies: did Faultline see them coming?</h2>
<p class="dim">Every company that filed for bankruptcy in the last two years and had a score 12 to 24 months earlier. Misses are included.
{flagged} of {len(seen)} were in the riskiest 20%.</p>
<div class="tbl"><table><thead><tr><th>Company</th><th>Bankruptcy filed</th><th>Score from 10-K filed</th><th class="n">Risk percentile</th><th>Reading</th></tr></thead>
<tbody>{seen_rows}</tbody></table></div></section>
<section><h2>Highest bankruptcy risk now</h2><p class="dim">Companies whose latest 10-K was filed in the past 13 months, ranked by Faultline's bankruptcy risk.</p>
<div class="tbl"><table><thead><tr><th>Company</th><th>Ticker</th><th>Industry</th><th>10-K filed</th><th class="n">Revenue</th>
<th class="n">Risk, 2 yrs</th><th class="n">Altman Z</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">A high score is a reason to read the filings closely, not a prediction that any single company will fail. Data as of {as_of}.</p></section>
{SEARCH_JS.replace("ROOT", "")}"""
    return page("Faultline: bankruptcy and accounting risk from SEC filings", body,
                "Free bankruptcy and accounting-risk scores for US public companies, tested against real outcomes.", active="index.html")


SCREENER_JS = """<script>
(async()=>{const data=await (await fetch('data/companies.json')).json();
const sec=document.getElementById('sector'),st=document.getElementById('status'),minr=document.getElementById('minrev'),q=document.getElementById('f'),
tb=document.getElementById('tb'),cnt=document.getElementById('cnt');let key='b',dir=-1;
[...new Set(data.map(c=>c.i).filter(Boolean))].sort().forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent=s;sec.appendChild(o)});
const fmt=(v,d=2)=>v==null?'':v.toFixed(d), money=v=>v==null?'':(Math.abs(v)>=1e9?'$'+(v/1e9).toFixed(1)+'B':'$'+(v/1e6).toFixed(1)+'M');
function rows(){const s=sec.value,t=st.value,m=+minr.value*1e6,qq=q.value.toLowerCase();
return data.filter(c=>(!s||c.i===s)&&(!t||c.s===t)&&(c.r||0)>=m&&(!qq||c.n.toLowerCase().includes(qq)||c.t.toLowerCase().includes(qq)))
.sort((a,b)=>((a[key]??-1e18)-(b[key]??-1e18))*dir)}
function draw(){const r=rows();cnt.textContent=r.length.toLocaleString()+' companies';tb.innerHTML='';
for(const c of r.slice(0,300)){const tr=document.createElement('tr');
tr.innerHTML=`<td><a href="c/${c.c}.html"></a></td><td class="mono"></td><td class="dim ind"></td><td class="n">${money(c.r)}</td>
<td class="n">${c.b==null?'':(c.b*100).toFixed(1)+'%'}</td><td class="n">${c.bp==null?'':Math.round(c.bp*100)}</td>
<td class="n">${c.rr==null?'':(c.rr*100).toFixed(1)+'%'}</td><td class="n">${fmt(c.z)}</td><td class="n">${c.fs==null?'':c.fs}</td><td class="n">${fmt(c.m)}</td><td class="d">${c.d}</td>`;
tr.children[0].firstChild.textContent=c.n;tr.children[1].textContent=c.t.split(' | ')[0];tr.children[2].textContent=c.i||'';tr.children[2].title=c.i||'';tb.appendChild(tr)}}
document.querySelectorAll('th.sort').forEach(th=>th.addEventListener('click',()=>{dir=key===th.dataset.k?-dir:-1;key=th.dataset.k;draw()}));
[sec,st,minr,q].forEach(x=>x.addEventListener('input',draw));
document.getElementById('csv').addEventListener('click',()=>{const r=rows(),h='cik,name,ticker,industry,revenue,bankruptcy_risk,bankruptcy_pctile,restatement_risk,altman_z,piotroski_f,beneish_m,filed\\n';
const body=r.map(c=>[c.c,'"'+c.n.replace(/"/g,'""')+'"',c.t.split(' | ')[0],'"'+(c.i||'')+'"',c.r??'',c.b??'',c.bp??'',c.rr??'',c.z??'',c.fs??'',c.m??'',c.d].join(',')).join('\\n');
const u=URL.createObjectURL(new Blob([h+body],{type:'text/csv'}));const a=document.createElement('a');a.href=u;a.download='faultline-screener.csv';a.click()});
draw()})();</script>"""


def screener():
    body = """<section><h1>Screener</h1><p class="dim">Every scored company, using each one's latest 10-K. Click a column to sort. Shows the first 300 matches.</p>
<div class="filters"><label>Name or ticker<input id="f" type="search"></label>
<label>Industry<select id="sector"><option value="">All</option></select></label>
<label>Status<select id="status"><option value="">All</option><option value="active" selected>Still filing</option><option value="inactive">Stopped filing</option></select></label>
<label>Min revenue ($M)<input id="minrev" type="number" value="0" min="0" step="50" style="width:110px"></label>
<button id="csv" type="button">Download CSV</button><span id="cnt" class="dim">Loading 7,000+ companies…</span></div>
<div class="tbl"><table><thead><tr><th>Company</th><th>Ticker</th><th>Industry</th><th class="n sort" data-k="r">Revenue</th>
<th class="n sort" data-k="b">Bankruptcy risk</th><th class="n sort" data-k="bp">Pctile</th><th class="n sort" data-k="rr">Restatement risk</th>
<th class="n sort" data-k="z">Altman Z</th><th class="n sort" data-k="fs">F</th><th class="n sort" data-k="m">Beneish M</th><th>10-K filed</th></tr></thead>
<tbody id="tb"></tbody></table></div></section>""" + SCREENER_JS
    return page("Screener · Faultline", body, "Filter every scored US public company by bankruptcy risk, accounting risk, industry and size.", active="screener.html")


def track_record(results):
    c, a, rs, tr, de = results["composite"], results["ablation"], results["restatement"], results["classic"], results["distress"]
    rt = results["returns"]["main_dark_minus_50"]
    names = {"faultline_riskiest_10pct": "Faultline riskiest 10%", "faultline_10_to_20pct": "Faultline next 10%",
             "faultline_safest_50pct": "Faultline safest 50%", "altman_distress": "Altman distress zone", "altman_safe": "Altman safe zone"}
    ret_rows = "".join(f'<tr><td>{v}</td><td class="n">{rt[k]["n"]:,}</td><td class="n">{rt[k]["median"]*100:+.1f}%</td>'
                       f'<td class="n">{rt[k]["share_lost_half"]*100:.0f}%</td><td class="n">{rt[k]["share_wiped_out"]*100:.1f}%</td></tr>' for k, v in names.items())
    ab = "".join(f'<tr><td>{e(k)}</td><td class="n">{v["auc_same_rows_as_altman"]:.3f}</td>'
                 + "".join(f'<td class="n">{x*100:.0f}%</td>' for x in v["caught_if_flag_top"].values()) + "</tr>"
                 for k, v in a.items() if "auc_same_rows_as_altman" in v)
    alt = a["altman_z (lowest first)"]["caught_if_flag_top"]
    ab += f'<tr><td>Altman Z-Score (lowest first)</td><td class="n">{c["altman"]["auc"]:.3f}</td>' + "".join(f'<td class="n">{x*100:.0f}%</td>' for x in alt.values()) + "</tr>"
    cl = "".join(f'<tr><td>{e(k.replace("__", ", ").replace("_", " "))}</td><td class="n">{v["events_in_period"]:,} ({v["events_with_score"]:,})</td>'
                 f'<td class="n">{v["hit_rate"]*100:.1f}%</td><td class="n">{v["alarm_rate"]*100:.1f}%</td><td class="n">{v["lift"]:.1f}x</td></tr>'
                 for k, v in tr.items())
    body = f"""<section><h1>Track record</h1><p class="dim">Full write-up: <a href="Faultline-paper.pdf">research paper (PDF, 6 pages)</a>.</p><p>Every number here comes from a test where the model was trained only on years whose
outcomes were already known, then scored years it had never seen ({c['test_years']}). Companies that later failed or stopped filing
are included. Banks, insurers and other financial companies are left out because these scores were not built for them.</p></section>
<section><h2>Bankruptcy within two years</h2><p class="dim">{c['company_years']:,} company-years with an Altman score, {c['bankruptcies']} followed by a bankruptcy filing.</p>
<div class="tbl"><table><thead><tr><th>Model</th><th class="n">AUC</th><th class="n">Caught in top 5%</th><th class="n">Top 10%</th><th class="n">Top 20%</th></tr></thead><tbody>{ab}</tbody></table></div>
<p>At the same share of companies flagged as Altman's distress zone ({c['altman']['alarm_rate']*100:.0f}%), Faultline caught
{c['faultline_same_alarm_rate']['hit_rate']*100:.1f}% of bankruptcies against Altman's {c['altman']['hit_rate']*100:.1f}%.
To catch as many as Altman, Faultline needed to flag {c['faultline_same_hit_rate']['alarm_rate']*100:.0f}% of companies instead of {c['altman']['alarm_rate']*100:.0f}%.</p>
<p>Adding auditor changes and late filings barely moved the result. Those events do carry warning signs on their own, but the financial statements already contain most of that information.</p></section>
<section><h2>Restatements within two years</h2><p class="dim">A restatement here is an 8-K Item 4.02 notice telling investors not to rely on past financial statements.
{rs['company_years_with_beneish']:,} company-years with a Beneish score, {rs['restatements']} followed by a restatement notice.</p>
<div class="tbl"><table><thead><tr><th>Model</th><th class="n">AUC</th><th class="n">Caught in top 5%</th><th class="n">Top 10%</th><th class="n">Top 20%</th></tr></thead><tbody>
<tr><td>Faultline restatement model</td><td class="n">{rs['faultline_auc']:.3f}</td>{"".join(f'<td class="n">{x*100:.0f}%</td>' for x in rs['faultline_caught_if_flag_top'].values())}</tr>
<tr><td>Beneish M-Score</td><td class="n">{rs['beneish']['auc']:.3f}</td>{"".join(f'<td class="n">{x*100:.0f}%</td>' for x in rs['beneish']['caught_if_flag_top'].values())}</tr>
</tbody></table></div><p>Restatements are much harder to see coming than bankruptcies. Beneish's ranking was close to a coin flip in these years.</p></section>
<section><h2>The classic scores on their own</h2><p class="dim">Hit rate: share of events where the latest score before it was flagged. Alarm rate: share of all company-years flagged.</p>
<div class="tbl"><table><thead><tr><th>Test</th><th class="n">Events (with a score)</th><th class="n">Hit rate</th><th class="n">Alarm rate</th><th class="n">Lift</th></tr></thead><tbody>{cl}</tbody></table></div></section>
<section><h2>What happened to the stock</h2><p class="dim">Free prices for companies that no longer trade are not available, so this uses the market value of outside shareholders' stock reported on each 10-K cover page. The change is measured over a year that starts after the score was public. Bankruptcies count as -100%, companies that stopped filing without being bought as -50%, and buyouts are left out. Companies worth at least $10 million, filings from 2016 to 2022.</p><div class="tbl"><table><thead><tr><th>Group</th><th class="n">Company-years</th><th class="n">Median change</th><th class="n">Lost half or more</th><th class="n">Wiped out</th></tr></thead><tbody>{ret_rows}</tbody></table></div><p>The typical flagged company lost value, and flagged companies were about three times as likely to lose half of it. The average was not lower, because a few flagged stocks rose enormously and new share issues raise market value. This is an approximation, not a trading test.</p></section>
<section><h2>A wider definition of failure</h2><p>Small companies often stop filing instead of filing for bankruptcy. Counting a company as failed if it filed for bankruptcy or stopped filing without being bought gives {de['distress_exits']:,} events in the test years. Faultline ranked them with an AUC of {de['faultline_auc']:.2f}, against {de['altman_auc']:.2f} for Altman Z.</p></section>
<section><h2>Limits</h2><p>Only formal bankruptcy filings count, so distressed sales and out-of-court restructurings are scored as misses.
Companies that simply stop filing are not counted either way. About 40% of bankrupt companies had no score in the warning window,
usually because they stopped filing or left out a needed number. Results come from one model setting that has not been tuned.</p></section>"""
    return page("Track record · Faultline", body, "How often Faultline's scores flagged bankruptcies and restatements in advance, tested out of sample.", active="track-record.html")


def new_filings(latest, as_of):
    """10-Ks filed in the last 30 days, plus the biggest jumps in risk vs each company's previous report."""
    cut = pd.Timestamp(as_of) - pd.Timedelta(days=30)
    recent = latest[pd.to_datetime(latest["available_date"]) >= cut].copy()
    def prev_pct(r):
        h = HIST[r.cik]
        h = h[pd.to_datetime(h["available_date"]) < pd.Timestamp(r.available_date)].dropna(subset=["bankruptcy_pctile"])
        return h["bankruptcy_pctile"].iloc[-1] if len(h) else float("nan")
    recent["prev"] = [prev_pct(r) for r in recent.itertuples()]
    recent["jump"] = recent["bankruptcy_pctile"] - recent["prev"]
    def row(r):
        tick = r.tickers.split(" | ")[0] if isinstance(r.tickers, str) else ""
        chg = "" if isnan(r.jump) else f"{r.jump*100:+.0f}"
        return (f'<tr><td class="d">{pd.Timestamp(r.available_date).date()}</td><td><a href="c/{r.cik}.html">{e(r.name)}</a></td>'
                f'<td class="mono">{e(tick)}</td><td class="n">{money(r.revenue)}</td><td class="n">{r.bankruptcy_pctile*100:.0f}</td>'
                f'<td class="n">{chg}</td><td>{reading(r.bankruptcy_pctile)}</td></tr>')
    head = ('<thead><tr><th>10-K filed</th><th>Company</th><th>Ticker</th><th class="n">Revenue</th><th class="n">Risk percentile</th>'
            '<th class="n">Change vs last report</th><th>Reading</th></tr></thead>')
    jumps = recent.dropna(subset=["jump"]).sort_values("jump", ascending=False).head(15)
    allrows = recent.sort_values(["available_date", "bankruptcy_pctile"], ascending=[False, False])
    body = f"""<section><h1>New filings</h1><p class="dim">Every annual report filed in the 30 days before {as_of}, scored the day the data
was updated. Risk percentile compares each company with all companies that filed in the same year; change is in percentile points
against the company's previous 10-K.</p></section>
<section><h2>Biggest increases in risk</h2>{'<div class="tbl"><table>' + head + '<tbody>' + "".join(row(r) for r in jumps.itertuples()) + '</tbody></table></div>' if len(jumps) else '<p class="dim">No company with an earlier report filed in this window.</p>'}</section>
<section><h2>All {len(allrows):,} filings</h2><div class="tbl"><table>{head}<tbody>{"".join(row(r) for r in allrows.itertuples())}</tbody></table></div>
<p class="note">Research, not investment advice. Updated weekly from SEC EDGAR.</p></section>"""
    return page("New filings · Faultline", body, "The latest 10-K filings scored for bankruptcy risk, and the biggest jumps in risk.", active="new.html")


def methodology():
    body = """<section><h1>Methodology</h1>
<h2>Data</h2><p>All numbers come from the SEC's free EDGAR XBRL data: about 39 million reported values from 15,686 companies that filed an
annual report since 2009, including 10,349 that later stopped filing. A list of only today's companies would hide every failure, which
makes any warning score look worse than it is.</p>
<h2>Point in time</h2><p>Each year's numbers are taken from that year's original 10-K, dated by the day it was filed. Later corrections
are kept separately and never used in tests. A number that first appeared in a later filing is left out of that year.</p>
<h2>Cleaning</h2><p>Companies tag the same item in different ways. Faultline maps 21 items to their XBRL tags. When one filing reports two
different revenue figures, it keeps the one where revenue minus cost of goods equals gross profit. Five companies were checked by hand
against their 10-Ks (Apple, Sears, General Mills, SVB, Conagra), and all matched.</p>
<h2>Classic scores</h2><p>Altman Z-Score (1968) uses five ratios to measure bankruptcy risk; market value comes from the public float
on the 10-K cover page. Z'' (1995) swaps market value for book equity. Piotroski F-Score (2000) counts nine pass/fail health tests.
Beneish M-Score (1999) combines eight ratios that tend to move before earnings manipulation is found.</p>
<h2>Faultline models</h2><p>Two gradient-boosted tree models read 46 values per company-year: every part of the classic scores, size,
profitability, debt, growth, how long the 10-K took to file, recent auditor changes, late filings and amendments, and whether the
10-K uses five warning phrases (found with SEC's full-text search). The phrases did not improve the models, but they are shown on company pages. One predicts a
bankruptcy filing (8-K Item 1.03) within two years, the other a restatement notice (8-K Item 4.02). For filings made in a given year,
each model is trained only on companies whose two-year outcome was known before that year started.</p>
<h2>What the scores are not</h2><p>A score is a ranking of how a company's filings compare with the filings of companies that later failed
or restated. It is not a forecast for any single company and not investment advice. Financial companies are not scored.</p>
<h2>Paper and code</h2><p>A write-up of the method and results is in the <a href="Faultline-paper.pdf">research paper (PDF, 6 pages)</a>. The full pipeline is open source on <a href="https://github.com/mahirzmansuri-hash/earnings-scanner">GitHub</a>.</p></section>"""
    return page("Methodology · Faultline", body, "How Faultline turns SEC filings into bankruptcy and accounting-risk scores.", active="methodology.html")


def about():
    body = """<section><h1>About</h1>
<p>Faultline is an independent research project by Mahir, a high school student, built with AI-assisted development.
It started as a question: do the famous accounting red-flag scores actually warn people before a company fails, when you test them
honestly with the companies that disappeared?</p>
<p>The data is public, the code is open, and the site costs nothing to run. It updates as companies file new reports.</p>
<p>Faultline is a publication for general information. It does not give personalized advice and is not investment advice.</p></section>"""
    return page("About · Faultline", body, "Who built Faultline and why.", active="about.html")


HIST: dict = {}
NAMES: dict = {}


def build():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        latest, hist, events, accn, as_of = load(con)
    results = {k: json.loads((PROC / f).read_text()) for k, f in [
        ("composite", "composite_results.json"), ("ablation", "composite_ablation.json"),
        ("restatement", "restatement_results.json"), ("classic", "track_record.json"),
        ("distress", "distress_exit_results.json"), ("returns", "returns_results.json")]}
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "c").mkdir(parents=True)
    (SITE / "data").mkdir()
    HIST.update({k: g for k, g in hist.groupby("cik")})
    NAMES.update(dict(zip(latest["cik"], latest["name"])))
    ev_by = {k: g for k, g in events.groupby("cik")}
    empty_ev = events.iloc[0:0]
    accn_map = {(r.cik, pd.Timestamp(r.period_end)): r.accn_first for r in accn.itertuples()}
    for r in latest.itertuples():
        r = pd.Series(r._asdict())
        (SITE / "c" / f"{r.cik}.html").write_text(company_page(r, HIST[r.cik], ev_by.get(r.cik, empty_ev), accn_map, as_of))
    comp = [{"c": int(r.cik), "n": r.name, "t": r.tickers if isinstance(r.tickers, str) else "",
             "f": r.former_names if isinstance(r.former_names, str) else "", "i": txt(r.sic_description), "s": r.status,
             "r": None if isnan(r.revenue) else float(r.revenue), "b": round(float(r.bankruptcy_risk), 4),
             "bp": None if isnan(r.bankruptcy_pctile) else round(float(r.bankruptcy_pctile), 3),
             "rr": None if isnan(r.restatement_risk) else round(float(r.restatement_risk), 4),
             "z": None if isnan(r.z_score) else round(float(r.z_score), 2),
             "fs": None if isnan(r.f_score) else int(r.f_score), "m": None if isnan(r.m_score) else round(float(r.m_score), 2),
             "d": str(pd.Timestamp(r.available_date).date())} for r in latest.itertuples()]
    (SITE / "data" / "companies.json").write_text(json.dumps(comp, separators=(",", ":"), allow_nan=False))
    shutil.copy(Path(__file__).parent / "assets" / "og.png", SITE / "og.png")  # share image (scripts/make_share_image.py)
    paper_pdf = ROOT / "docs" / "Faultline-paper.pdf"   # made by scripts/make_paper_pdf.py
    if paper_pdf.exists():
        shutil.copy(paper_pdf, SITE / "Faultline-paper.pdf")
    (SITE / "index.html").write_text(home(latest, events, results, as_of))
    (SITE / "new.html").write_text(new_filings(latest, as_of))
    (SITE / "screener.html").write_text(screener())
    (SITE / "track-record.html").write_text(track_record(results))
    (SITE / "methodology.html").write_text(methodology())
    (SITE / "about.html").write_text(about())
    # sitemap + robots.txt so search engines can find every company page
    from src.web.style import SITE_URL
    urls = ["", "new.html", "screener.html", "track-record.html", "methodology.html", "about.html"] + [f"c/{c}.html" for c in latest["cik"]]
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                      + "".join(f"<url><loc>{SITE_URL}{u}</loc><lastmod>{as_of}</lastmod></url>" for u in urls) + "</urlset>")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    size = sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file())
    print(f"site/: {len(latest):,} company pages, {size/1e6:.0f} MB")


if __name__ == "__main__":
    build()
