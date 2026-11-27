"""Turn docs/paper.md into a print-ready PDF with the key figure.

Run:  .venv/bin/python scripts/make_paper_pdf.py      (needs Google Chrome and `pip install markdown`)
Writes docs/paper.html and docs/Faultline-paper.pdf.

Figure 1 is recomputed from the out-of-sample test, so it always matches the paper's numbers.
"""
import subprocess
from pathlib import Path

import duckdb
import markdown
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))
from src.config import DB_PATH  # noqa: E402
from src.model.composite import load, walk_forward  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def capture_curve(rows, col, ascending):
    """For each share of companies flagged (0-100%), the share of bankruptcies caught."""
    r = rows.sort_values(col, ascending=ascending)
    caught = np.cumsum(r["label"].to_numpy()) / r["label"].sum()
    x = np.arange(1, len(r) + 1) / len(r)
    idx = np.linspace(0, len(r) - 1, 101).astype(int)
    return x[idx], caught[idx]


def figure_svg() -> str:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = load(con)
    oos = walk_forward(df, verbose=False)
    rows = oos[oos["z_score"].notna()]
    fx, fy = capture_curve(rows, "composite", ascending=False)
    ax, ay = capture_curve(rows, "z_score", ascending=True)
    W, H, L, B, T, R = 560, 330, 52, 44, 14, 16
    X = lambda v: L + v * (W - L - R)
    Y = lambda v: T + (1 - v) * (H - T - B)
    s = []
    for v in (0, .25, .5, .75, 1):
        s.append(f'<line x1="{X(0)}" x2="{X(1)}" y1="{Y(v)}" y2="{Y(v)}" stroke="#D9DCDF"/>'
                 f'<text x="{L-8}" y="{Y(v)+4}" text-anchor="end">{v*100:.0f}%</text>'
                 f'<text x="{X(v)}" y="{H-B+18}" text-anchor="middle">{v*100:.0f}%</text>')
    s.append(f'<line x1="{X(0)}" y1="{Y(0)}" x2="{X(1)}" y2="{Y(1)}" stroke="#9AA2AA" stroke-dasharray="4 4"/>')
    s.append(f'<line x1="{X(.1)}" x2="{X(.1)}" y1="{Y(0)}" y2="{Y(1)}" stroke="#0FB3C8" stroke-dasharray="2 3"/>')
    pts = lambda xs, ys: " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(xs, ys))
    s.append(f'<polyline points="{pts(ax, ay)}" fill="none" stroke="#9A6212" stroke-width="2"/>')
    s.append(f'<polyline points="{pts(fx, fy)}" fill="none" stroke="#1B3A5C" stroke-width="2.4"/>')
    f10, a10 = fy[10], ay[10]
    s.append(f'<text x="{X(.13)}" y="{Y(f10)+4}" style="fill:#1B3A5C;font-weight:600">Faultline: {f10*100:.0f}% at 10%</text>')
    s.append(f'<text x="{X(.13)}" y="{Y(a10)+4}" style="fill:#9A6212;font-weight:600">Altman Z: {a10*100:.0f}% at 10%</text>')
    s.append(f'<text x="{X(.62)}" y="{Y(.5)}" style="fill:#525A63">random ranking</text>')
    s.append(f'<text x="{(L + W - R) / 2}" y="{H-4}" text-anchor="middle">Share of companies flagged (riskiest first)</text>')
    s.append(f'<text transform="rotate(-90)" x="{-(T + H - B) / 2}" y="13" text-anchor="middle">Share of bankruptcies caught</text>')
    return (f'<figure><svg viewBox="0 0 {W} {H}" width="100%" style="font:11px Helvetica,Arial,sans-serif;fill:#525A63">{"".join(s)}</svg>'
            f'<figcaption><b>Figure 1.</b> Out-of-sample capture curves, 2016-2023 ({len(rows):,} company-years, '
            f'{int(rows["label"].sum())} bankruptcies within two years). Companies are ranked from riskiest to safest by each score; '
            'the curve shows what share of later bankruptcies falls within the flagged share. The dashed diagonal is a random ranking.</figcaption></figure>')


CSS = """
@page { size: Letter; margin: 0.9in 0.95in 0.9in; @bottom-center { content: counter(page); font: 9pt Helvetica, Arial, sans-serif; color: #525A63; } }
body { font: 10.5pt/1.5 Georgia, 'Times New Roman', serif; color: #15191E; }
h1 { font: 600 19pt/1.2 Georgia, serif; margin: 0 0 6pt; letter-spacing: -0.01em; }
h1 + p { font: 9.5pt Helvetica, Arial, sans-serif; color: #525A63; margin-bottom: 18pt; padding-bottom: 10pt; border-bottom: 1px solid #D9DCDF; }
h2 { font: 600 12.5pt Georgia, serif; margin: 18pt 0 6pt; break-after: avoid; }
p { margin: 0 0 8pt; text-align: left; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 8pt 18pt; padding: 0; } li { margin-bottom: 3pt; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 12pt; font: 9pt/1.35 Helvetica, Arial, sans-serif; break-inside: avoid; font-variant-numeric: tabular-nums; }
th { text-align: left; border-bottom: 1px solid #15191E; padding: 4pt 6pt; font-weight: 600; }
td { border-bottom: 1px solid #D9DCDF; padding: 4pt 6pt; }
td:not(:first-child), th:not(:first-child) { text-align: right; }
figure { margin: 10pt 0 14pt; break-inside: avoid; }
figcaption { font: 8.5pt/1.4 Helvetica, Arial, sans-serif; color: #525A63; margin-top: 4pt; }
code { font: 8.5pt Menlo, monospace; }
a { color: #1B3A5C; text-decoration: none; }
h2:first-of-type { margin-top: 6pt; }
"""


def main():
    md = (ROOT / "docs" / "paper.md").read_text()
    body = markdown.markdown(md, extensions=["tables"])
    anchor = "<p><strong>What drives the gain"
    assert anchor in body, "figure anchor missing"
    body = body.replace(anchor, figure_svg() + anchor, 1)
    html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Faultline paper</title><style>{CSS}</style></head><body>{body}</body></html>'
    out_html = ROOT / "docs" / "paper.html"
    out_pdf = ROOT / "docs" / "Faultline-paper.pdf"
    out_html.write_text(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}",
                    out_html.as_uri()], check=True, capture_output=True)
    print(f"wrote {out_pdf.relative_to(ROOT)} ({out_pdf.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
