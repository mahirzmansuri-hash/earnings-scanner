"""Chart for Reddit/X posts: where Faultline ranked companies before they filed for bankruptcy (2017 to now).

Run:  PYTHONPATH=. .venv/bin/python scripts/make_oc_chart.py
Writes docs/marketing/oc-bankruptcy-deciles.png (1600x1000) and prints the numbers used, for the post text.

Each bar = companies whose last Faultline score (10-K or 10-Q, within 13 months before the bankruptcy 8-K)
fell in that tenth of all filings made in the 365 days up to it. With no skill, every bar would be the dashed line (10%).
Scores are walk-forward: each year's model was trained only on outcomes known before that year.
"""
import duckdb
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from src.config import DB_PATH, ROOT
from src.web.build import receipts_rows
from src.web.share import font, INK, INK2, RULE, BRAND, PAPER, POP

OUT = ROOT / "docs" / "marketing" / "oc-bankruptcy-deciles.png"
START = pd.Timestamp("2017-01-01")      # scores begin in 2016, so 2017 is the first year with a full 13-month look-back


def data():
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        ev = con.execute("SELECT cik, event, filed, accn FROM events ORDER BY cik, filed").df()
        tl = con.execute("""SELECT cik, available_date::DATE AS d, bankruptcy_pctile AS p, '10-K' AS src FROM risk WHERE bankruptcy_pctile IS NOT NULL
                            UNION ALL SELECT cik, available_date::DATE, q_pctile, '10-Q' FROM risk_q WHERE q_pctile IS NOT NULL ORDER BY cik, d, src""").df()
        bad = frozenset(a for (a,) in con.execute("SELECT accn FROM bk_verified WHERE NOT verified").fetchall())
        as_of = con.execute("SELECT MAX(filed) FROM events").fetchone()[0]
    r = receipts_rows(ev, tl, as_of, days=(pd.Timestamp(as_of) - START).days, not_bankruptcy=bad)
    return r, r[r["p"].notna()], pd.Timestamp(as_of).date()


def main():
    rows, s, as_of = data()
    dec = np.minimum((s["p"] * 10).astype(int), 9).value_counts().reindex(range(10), fill_value=0)
    share = dec / dec.sum()
    W, H = 1600, 1000
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.text((80, 60), f"Where the model ranked {len(s)} companies before they went bankrupt", font=font("serif", 40), fill=INK)
    d.text((80, 125), f"Last bankruptcy-risk score before each filing, ranked against all filings of the year before it  ·  2017 to {as_of}",
           font=font("sans", 26), fill=INK2)
    x0, x1, y0, y1 = 140, W - 80, 230, 820          # plot area
    top = 0.75
    bw = (x1 - x0) / 10
    for t in [0, 0.25, 0.5, 0.75]:
        y = y1 - (y1 - y0) * t / top
        d.line([(x0, y), (x1, y)], fill=RULE, width=2)
        d.text((x0 - 20, y - 14), f"{t:.0%}", font=font("sans", 22), fill=INK2, anchor="ra")
    for i in range(10):
        h = (y1 - y0) * share[i] / top
        bx = x0 + i * bw + 10
        d.rectangle([(bx, y1 - h), (bx + bw - 20, y1)], fill=BRAND if i == 9 else "#9AA7B5")
        lab = f"{share[i]:.0%}" if share[i] >= 0.01 or share[i] == 0 else f"{share[i]:.1%}"
        d.text((bx + (bw - 20) / 2, y1 - h - 12), f"{lab}", font=font("bold" if i == 9 else "sans", 30 if i == 9 else 22),
               fill=INK if i == 9 else INK2, anchor="md")
        d.text((bx + (bw - 20) / 2, y1 + 16), ["safest", "", "", "", "", "", "", "", "", "riskiest"][i] or f"{i + 1}",
               font=font("sans", 22), fill=INK2, anchor="ma")
        d.text((bx + (bw - 20) / 2, y1 + 44), "10%" if i in (0, 9) else "", font=font("sans", 22), fill=INK2, anchor="ma")
    yc = y1 - (y1 - y0) * 0.10 / top                # chance line
    for xx in range(x0, x1, 24):
        d.line([(xx, yc), (xx + 12, yc)], fill=POP, width=4)
    d.text((x0 + 10, yc - 40), "if the score were random: 10% in each bar", font=font("sans", 24), fill=POP)
    for k, line in enumerate([
            "Data: SEC EDGAR (XBRL financials; bankruptcy = 8-K Item 1.03). Model: gradient-boosted trees, walk-forward (each year trained only on earlier outcomes).",
            f"{len(rows) - len(s)} more bankrupt companies had no score in the 13 months before (mostly banks/insurers, or no XBRL data).",
            "Chart: Python + Pillow. Faultline (free): mahirzmansuri-hash.github.io/earnings-scanner"]):
        d.text((80, 895 + 32 * k), line, font=font("sans", 21), fill=INK2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    fl = s[s["p"] >= 0.9]
    print(f"bankrupt companies {len(rows)}, scored {len(s)}, by tenth {dec.tolist()}")
    print(f"riskiest 10%: {share[9]:.1%}  riskiest 20%: {(s['p'] >= .8).mean():.1%}  safer half: {(s['p'] < .5).mean():.1%}")
    print(f"median days from first entering riskiest 10% to filing: {(fl['filed'] - pd.to_datetime(fl['first_top'])).dt.days.median():.0f}")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
