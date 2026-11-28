"""Industry pages: every active company in an industry, ranked by bankruptcy risk.

Built with the site (src/web/build.py) into site/industry/<slug>.html plus an index. One page per SEC industry
(SIC description) with at least MIN_COMPANIES active scored companies. Helps readers compare a company with its
peers, and gives search engines pages that match searches like "retail bankruptcy risk".
"""
import html
import re

import pandas as pd

from src.web.style import page

MIN_COMPANIES = 8


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")[:80]


def nice(name: str) -> str:
    """'Services-Prepackaged Software' -> 'Prepackaged software services'; otherwise sentence case."""
    n = str(name).replace(", NEC", " (other)").replace(" NEC", " (other)")
    if n.startswith("Services-"):
        n = n[len("Services-"):] + " services"
    n = re.sub(r"^(Retail|Wholesale)-", r"\1: ", n)
    n = re.sub(r"\s+", " ", n.replace("&", " and ")).strip()
    return n[:1].upper() + n[1:].lower()


def industry_slugs(latest: pd.DataFrame) -> dict:
    act = latest[(latest["status"] == "active") & latest["sic_description"].notna()]
    counts = act["sic_description"].value_counts()
    return {k: slug(k) for k, v in counts.items() if v >= MIN_COMPANIES}


def _pct(p) -> str:
    return "n/a" if p != p or p is None else f"{min(int(p * 100), 99)}%"


def _money(x) -> str:
    if x != x or x is None:
        return "n/a"
    x = float(x)
    for d, s in [(1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if abs(x) >= d:
            return f"${x / d:.1f}{s}"
    return f"${x:.0f}"


def write_industries(site, latest, events, slugs, as_of) -> int:
    out = site / "industry"
    out.mkdir(exist_ok=True)
    e = lambda s: html.escape(str(s))
    bk = events[events["event"] == "bankruptcy"].copy()
    bk["filed"] = pd.to_datetime(bk["filed"])
    bk = bk[bk["filed"] >= pd.Timestamp("2016-01-01")].drop_duplicates("cik")
    all_ind = latest.set_index("cik")["sic_description"].to_dict()
    names = latest.set_index("cik")["name"].to_dict()
    cards = []
    for ind, sl in slugs.items():
        g = latest[(latest["sic_description"] == ind) & (latest["status"] == "active")].sort_values("bankruptcy_pctile", ascending=False)
        n = len(g)
        top10 = int((g["bankruptcy_pctile"] >= 0.9).sum())
        safe = int((g["bankruptcy_pctile"] < 0.5).sum())
        med = g["bankruptcy_pctile"].median()
        dead = [c for c in bk["cik"] if all_ind.get(c) == ind]
        rows = "".join(
            f'<tr><td><a href="../c/{r.cik}.html">{e(r.name)}</a>'
            f'{f" <span class=mono>{e(r.tickers.split(" | ")[0])}</span>" if isinstance(r.tickers, str) and r.tickers else ""}'
            f'<span class=sub>10-K filed {pd.Timestamp(r.available_date).date()} · revenue {_money(r.revenue)}</span></td>'
            f'<td class="n">{_pct(r.bankruptcy_pctile)}</td><td class="n">{"n/a" if r.z_score != r.z_score else f"{r.z_score:.2f}"}</td></tr>'
            for r in g.itertuples())
        dead_html = ""
        if dead:
            items = ", ".join(f'<a href="../c/{c}.html">{e(names.get(c, c))}</a>' for c in dead[:25])
            more = f" and {len(dead) - 25} more" if len(dead) > 25 else ""
            dead_html = (f"<h2>Bankruptcies in this industry since 2016</h2><p>{len(dead)} companies filed for bankruptcy "
                         f"(8-K Item 1.03): {items}{more}.</p>")
        title = f"{nice(ind)}: bankruptcy risk of {n} public companies"
        body = f"""<section><div class="label"><a href="index.html">Industries</a></div><h1>{e(nice(ind))}</h1>
<p class="lede">{n} active US public companies in this industry (SEC industry: {e(ind)}), ranked by Faultline's bankruptcy risk from their latest 10-K.</p>
<div class="grid3"><div class="stat"><span class="label">In the riskiest 10% of all filers</span><span class="v">{top10} of {n}</span></div>
<div class="stat"><span class="label">In the safer half</span><span class="v">{safe} of {n}</span></div>
<div class="stat"><span class="label">Typical company</span><span class="v">{_pct(med)}</span><span class="sub">riskier than this share of all filers (median)</span></div></div>
<div class="tbl"><table><thead><tr><th>Company</th><th>Riskier than</th><th>Altman Z</th></tr></thead><tbody>{rows}</tbody></table></div>
{dead_html}
<p class="note">"Riskier than" compares each company's latest 10-K with all 10-Ks filed in the 365 days before it, across all industries.
Some industries are riskier by nature (for example, early-stage drug developers with no revenue). Data as of {as_of}. Research, not investment advice.</p></section>"""
        (out / f"{sl}.html").write_text(page(title, body, f"{top10} of {n} {nice(ind).lower()} companies are in Faultline's riskiest 10% for bankruptcy risk.",
                                             root="../", active="screener.html"))
        cards.append((top10 / n, f'<tr><td><a href="{sl}.html">{e(nice(ind))}</a></td><td class="n">{n}</td><td class="n">{top10 / n:.0%}</td>'
                                 f'<td class="n">{_pct(med)}</td></tr>'))
    cards.sort(key=lambda x: -x[0])
    (out / "index.html").write_text(page("Bankruptcy risk by industry · Faultline",
        '<section><h1>Bankruptcy risk by industry</h1><p>Every industry with at least '
        f'{MIN_COMPANIES} active public companies, sorted by the share of its companies in Faultline\'s riskiest 10%.</p>'
        '<div class="tbl"><table><thead><tr><th>Industry</th><th>Companies</th><th>In riskiest 10%</th><th>Median</th></tr></thead>'
        f'<tbody>{"".join(c for _, c in cards)}</tbody></table></div></section>',
        "Which industries have the most US public companies at risk of bankruptcy, from SEC filings.", root="../", active="screener.html"))
    return len(slugs)
