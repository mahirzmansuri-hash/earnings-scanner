"""Case studies (Research section): five companies, what the scores said before what happened.

Built with the site (src/web/build.py). Charts and tables come from the data; the story text quotes numbers through
small helpers (pct, z), so it stays correct if the model is retrained. Facts that come straight from SEC filings
(SVB's bond losses, Bed Bath's balance sheet) are quoted from the XBRL data and checked against the 10-Ks.
Pages: research/index.html and research/<slug>.html.
"""
import pandas as pd

from src.web.style import page

CASES = [
    {"slug": "sears", "cik": 1310067, "name": "Sears Holdings", "tag": "Caught early, stayed flagged",
     "lede": "Every 10-K and 10-Q Sears filed from 2016 on was among the riskiest few percent of filers. It filed for bankruptcy in October 2018."},
    {"slug": "bed-bath-beyond", "cik": 886158, "name": "Bed Bath & Beyond", "tag": "Altman said safe",
     "lede": "The Altman Z-Score put Bed Bath & Beyond in its safe zone every year until a year before it went bankrupt. Faultline's score climbed for six straight years."},
    {"slug": "general-electric", "cik": 40545, "name": "General Electric", "tag": "A warning that didn't end in bankruptcy",
     "lede": "GE was riskier than 79-93% of filers in four of its five 10-Ks from 2016 to 2020 and lost $22 billion in 2018, but it never went bankrupt. It also had an SEC accounting case the scores missed."},
    {"slug": "kraft-heinz", "cik": 1637459, "name": "Kraft Heinz", "tag": "Altman's false alarm",
     "lede": "Kraft Heinz has been in the Altman Z-Score's distress zone in every 10-K since 2016 and never came close to bankruptcy. Faultline kept it in the middle."},
    {"slug": "svb", "cik": 719739, "name": "SVB Financial", "tag": "Where scores fail",
     "lede": "Silicon Valley Bank failed in March 2023. Faultline doesn't score banks, and none of the classic scores would have helped. Here's why."},
]


def _fmt_pct(p) -> str:
    return "n/a" if p is None or p != p else f"{min(int(p * 100), 99)}%"


class Facts:
    """Look up a company's scores by filing date, for use inside the story text."""

    def __init__(self, tl: pd.DataFrame, hist: pd.DataFrame):
        self.tl = tl.assign(d=pd.to_datetime(tl["d"]))
        self.h = hist.assign(available_date=pd.to_datetime(hist["available_date"]))

    def pct(self, date: str) -> str:
        r = self.tl[self.tl["d"] == pd.Timestamp(date)]
        return _fmt_pct(r["p"].max()) if len(r) else "n/a"

    def z(self, date: str) -> str:
        r = self.h[self.h["available_date"] == pd.Timestamp(date)]
        return "n/a" if not len(r) or r["z_score"].iloc[0] != r["z_score"].iloc[0] else f"{r['z_score'].iloc[0]:.2f}"

    def rpct(self, date: str) -> str:
        r = self.h[self.h["available_date"] == pd.Timestamp(date)]
        return _fmt_pct(r["restatement_pctile"].iloc[0]) if len(r) else "n/a"


def story(slug: str, f: Facts) -> str:
    if slug == "sears":
        return f"""
<h2>What the numbers showed</h2>
<p>By 2016 Sears was losing money every year, burning cash (operating cash flow was about minus $2 billion a year), and owed more
than it owned: liabilities were 121% of assets in its first 10-Q of 2016 and 164% by its last one in 2018.</p>
<h2>What the scores said</h2>
<ul><li><b>Faultline:</b> riskier than {f.pct("2016-03-16")} of filers with the 10-K filed March 2016, {f.pct("2017-03-21")} in March 2017,
and {f.pct("2018-09-13")} with its last 10-Q, filed September 13, 2018: 32 days before the bankruptcy filing.</li>
<li><b>Altman Z-Score:</b> in the distress zone (below 1.8) in every 10-K: {f.z("2016-03-16")}, {f.z("2017-03-21")}, {f.z("2018-03-23")}.</li>
<li><b>10-K wording:</b> the 10-K filed in March 2017 said there was substantial doubt about Sears's ability to continue as a going concern.</li></ul>
<h2>The lesson</h2>
<p>Sears is the easy case: every score caught it, years ahead. The value of a warning system here is not being clever but being
consistent. Sears stayed flagged for almost three years, through store closures and asset sales that made headlines look like recovery.</p>"""
    if slug == "bed-bath-beyond":
        return f"""
<h2>What the scores said</h2>
<ul><li><b>Faultline</b> climbed every year: riskier than {f.pct("2016-04-26")} of filers in April 2016, {f.pct("2019-04-30")} in 2019,
{f.pct("2021-04-22")} in April 2021 (two years before the bankruptcy) and {f.pct("2022-04-21")} in April 2022. Its 10-Qs were in
the riskiest 5% from September 2021 on.</li>
<li><b>Altman Z-Score</b> said <b>safe</b> (above 3) in every 10-K through April 2022: {f.z("2016-04-26")} in 2016 and still {f.z("2022-04-21")}
in April 2022, a year before the company filed for bankruptcy on April 23, 2023.</li></ul>
<h2>Why Altman missed it</h2>
<p>The Z-Score adds up five ratios. In the April 2022 10-K, one of them did most of the work: <b>retained earnings were 188% of total
assets</b>. Bed Bath had decades of past profits on its books, and spending billions on buying back its own shares didn't reduce that
number. Meanwhile, liabilities had reached 97% of assets ($4.96 billion of $5.13 billion), operating cash flow had fallen from about
$1 billion a year to $18 million, and sales had dropped by a third since 2019.</p>
<p>Faultline looks at those things directly: debt load, cash flow, falling sales, and their trend. That's why its score rose while the
classic score stayed calm.</p>
<h2>The lesson</h2>
<p>A single famous formula can be fooled by one odd number. Retained earnings measure the past; bankruptcy is about the next two years.</p>"""
    if slug == "general-electric":
        return f"""
<h2>What the scores said</h2>
<ul><li><b>Faultline:</b> riskier than {f.pct("2016-02-26")} of filers in February 2016, {f.pct("2018-02-23")} in 2018 and {f.pct("2019-02-26")}
in 2019, the year it reported a $22.4 billion loss for 2018.</li>
<li><b>Then it fell:</b> {f.pct("2023-02-10")} in 2023 and {f.pct("2025-02-03")} in 2025, after GE sold businesses, paid down debt and
split into three companies.</li>
<li><b>Accounting:</b> the SEC announced an accounting enforcement case against GE in December 2020.
Faultline's restatement-risk score for GE was low the whole time (riskier than {f.rpct("2018-02-23")} of filers in 2018).</li></ul>
<h2>How to read this</h2>
<p>GE counts as a <b>false alarm</b> in Faultline's bankruptcy test: it was in the riskiest group and did not go bankrupt within two
years. That is normal. Of all companies in Faultline's riskiest 10%, only about 1 in 9 went bankrupt within two years in the test. The score ranks how
fragile a company looks, it doesn't predict that any one company will fail. GE's real trouble (huge losses, heavy debt) was
exactly what the score measured; management fixed it.</p>
<h2>The lesson</h2>
<p>High risk is not a prediction of failure. And financial ratios are poor at spotting misleading accounting: Faultline found too
little signal to publish a fraud score at all (see the <a href="../track-record.html">track record</a>).</p>"""
    if slug == "kraft-heinz":
        return f"""
<h2>What the scores said</h2>
<ul><li><b>Altman Z-Score:</b> distress zone (below 1.8) in every 10-K from 2017 to 2026, for example {f.z("2017-02-23")} in 2017,
{f.z("2019-06-07")} in 2019 and {f.z("2024-02-15")} in 2024. Kraft Heinz never came near bankruptcy.</li>
<li><b>Faultline:</b> after 2017 mostly in the middle of the pack: riskier than {f.pct("2018-02-16")} of filers in 2018,
{f.pct("2021-02-17")} in 2021 and {f.pct("2025-02-13")} in 2025.</li>
<li><b>Accounting:</b> in May 2019 Kraft Heinz told investors that earlier financial statements could no longer be relied on
(an 8-K Item 4.02 restatement notice). Faultline's restatement score had it riskier than only {f.rpct("2018-02-16")} of filers
in its February 2018 10-K: a miss.</li></ul>
<h2>Why Altman flags it</h2>
<p>The Z-Score was built in 1968 on manufacturers. Kraft Heinz was formed by a 2015 merger, so most of its $90-100 billion of assets is
goodwill and brand value. That makes sales look tiny next to assets (about 25-30 cents of sales per dollar of assets), and the merger
reset retained earnings to near zero. Both push the Z-Score down even though the company earns billions and pays its bills.</p>
<h2>The lesson</h2>
<p>A score that flags everyone big and acquisitive isn't useful. Testing against real outcomes is how you find out: in Faultline's
test, the Altman Z-Score's riskiest 10% caught 13% of bankruptcies; Faultline's caught 53%.</p>"""
    if slug == "svb":
        return """
<h2>What happened</h2>
<p>Silicon Valley Bank was closed by regulators on March 10, 2023, after depositors pulled $42 billion in a day. Its parent company,
SVB Financial Group, filed for bankruptcy a week later.</p>
<h2>What was in the filings</h2>
<p>SVB's last 10-K, filed February 24, 2023, two weeks before the failure, showed the problem in plain numbers: it held $91.3 billion
of bonds it planned to keep to maturity, and those bonds had <b>$15.2 billion of unrealized losses</b> because interest rates had risen.
The company's entire equity was <b>$16.0 billion</b>. If it ever had to sell those bonds, the losses would wipe out almost all of it.
And 94% of those bonds ($86.0 billion) didn't mature for more than ten years.</p>
<h2>Why Faultline doesn't score banks</h2>
<ul><li>For a bank, deposits are liabilities by design, so "liabilities are 90% of assets" is normal, not a warning.</li>
<li>The Altman, Piotroski and Beneish scores were all built for non-financial companies.</li>
<li>Bank failures come from risks these ratios don't see: interest-rate risk, uninsured deposits, and how fast depositors can leave.</li></ul>
<h2>The lesson</h2>
<p>Every model has a boundary. The honest move is to say where it is instead of putting a confident-looking number on a company the
model doesn't understand. A bank score would need different inputs (unrealized bond losses vs. equity, uninsured deposit share),
and it would be judged by its own track record.</p>"""
    return ""


def kt_table(f: Facts, cik: int) -> str:
    h = f.h.dropna(subset=["available_date"]).sort_values(["available_date", "period_end"])
    h = h.drop_duplicates("available_date", keep="last")     # a first 10-K can also report an older year: show its own year
    if not len(h):
        return ""
    rows = "".join(
        f'<tr><td class="d">{r.available_date.date()}</td><td class="n">{_fmt_pct(r.bankruptcy_pctile)}</td>'
        f'<td class="n">{"n/a" if r.z_score != r.z_score else f"{r.z_score:.2f}"}'
        f'<span class=sub>{r.z_zone if isinstance(r.z_zone, str) else ""}</span></td>'
        f'<td class="n">{_fmt_pct(r.restatement_pctile)}</td></tr>' for r in h.itertuples())
    return ('<h2>Every 10-K, side by side</h2><p class="dim">Faultline and restatement columns: riskier than this share of filers.</p>'
            '<div class="tbl"><table><thead><tr><th>Filed</th><th>Faultline</th>'
            f'<th>Altman Z</th><th>Restate</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="dim"><a href="../c/{cik}.html">Full company page</a></p>')


def write_cases(site, timeline, hist_by_cik, events, chart_fn, has_page) -> int:
    out = site / "research"
    out.mkdir(exist_ok=True)
    cards = []
    for c in CASES:
        tl = timeline[timeline["cik"] == c["cik"]]
        h = hist_by_cik.get(c["cik"], pd.DataFrame(columns=["available_date", "bankruptcy_pctile", "z_score", "z_zone", "restatement_pctile"]))
        f = Facts(tl, h)
        ch = ""
        if len(tl) >= 2:
            ev = events[events["cik"] == c["cik"]]
            first_bk = ev[ev["event"] == "bankruptcy"].head(1)                  # later 8-Ks are about the same case
            ev = pd.concat([first_bk, ev[ev["event"] == "non_reliance"]])
            ch = chart_fn(tl.rename(columns={"d": "available_date", "p": "bankruptcy_pctile"}), ev)
            ch = ch.replace("among all 10-Ks filed in the 365 days", "among all 10-Ks or 10-Qs (each point is one filing) filed in the 365 days")
        body = (f'<section><div class="label"><a href="index.html">Case studies</a></div><h1>{c["name"]}: {c["tag"]}</h1>'
                f'<p class="lede">{c["lede"]}</p>{ch}{story(c["slug"], f)}'
                f'{kt_table(f, c["cik"]) if c["cik"] in has_page else ""}'
                '<p class="note">Every score shown was made by a model trained only on outcomes known before that year, using filings public '
                'on that date. Percentiles compare with filings of the previous 365 days. Research, not investment advice.</p></section>')
        (out / f'{c["slug"]}.html').write_text(page(f'{c["name"]}: {c["tag"]} · Faultline case study', body, c["lede"],
                                                   root="../", active="track-record.html"))
        cards.append(f'<li><a href="{c["slug"]}.html"><b>{c["name"]}</b></a>: {c["tag"]}<span class=sub>{c["lede"]}</span></li>')
    (out / "index.html").write_text(page("Case studies · Faultline",
        '<section><h1>Case studies</h1><p>Five companies, and what the scores said before what happened: two bankruptcies the scores '
        'caught, a warning that didn\'t end in bankruptcy, a famous score\'s false alarm, and a failure no score here could see.</p>'
        f'<ul class="cases">{"".join(cards)}</ul><p class="dim">For every bankruptcy of the last 12 months, see '
        '<a href="../receipts.html">Receipts</a>. For the full test, see the <a href="../track-record.html">track record</a>.</p></section>',
        "Case studies: Sears, Bed Bath & Beyond, GE, Kraft Heinz and SVB, and what bankruptcy-risk scores said before what happened.",
        root="../", active="track-record.html"))
    return len(CASES)
