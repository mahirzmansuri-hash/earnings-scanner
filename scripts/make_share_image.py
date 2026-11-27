"""Make the 1200x630 share image (the preview card when the site link is posted).

Run once on a Mac:  .venv/bin/python scripts/make_share_image.py   (needs `pip install pillow`)
Writes src/web/assets/og.png, which the site build copies into site/.
Numbers come from data/processed/*.json so the card matches the Track record page.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "web" / "assets" / "og.png"
F = "/System/Library/Fonts/Supplemental/"
serif = lambda s: ImageFont.truetype(F + "Georgia Bold.ttf", s)
sans = lambda s: ImageFont.truetype(F + "Arial.ttf", s)
sans_b = lambda s: ImageFont.truetype(F + "Arial Bold.ttf", s)

PAPER, INK, INK2, RULE, BRAND, POP, POPFILL = "#FFFFFF", "#15191E", "#525A63", "#D9DCDF", "#1B3A5C", "#0FB3C8", "#D5F4F8"

abl = json.loads((ROOT / "data/processed/composite_ablation.json").read_text())
comp = json.loads((ROOT / "data/processed/composite_results.json").read_text())
top10 = abl["3. + filing behaviour & warning events (full)"]["caught_if_flag_top"]["top_10pct"]
alt10 = abl["altman_z (lowest first)"]["caught_if_flag_top"]["top_10pct"]

img = Image.new("RGB", (1200, 630), PAPER)
d = ImageDraw.Draw(img)
# logo mark + wordmark
d.line([(72, 82), (104, 82)], fill=BRAND, width=7)
d.line([(110, 100), (142, 100)], fill=BRAND, width=7)
d.line([(104, 82), (110, 100)], fill=POP, width=7)
d.text((160, 66), "Faultline", font=serif(40), fill=INK)
d.line([(72, 140), (1128, 140)], fill=RULE, width=2)
# headline with one cyan highlight
d.text((72, 175), "Bankruptcy warnings from SEC filings,", font=serif(50), fill=INK)
line2 = "tested against what happened."
w = d.textlength(line2, font=serif(50))
d.rectangle([(68, 246), (76 + w, 306)], fill=POPFILL)
d.rectangle([(68, 302), (76 + w, 306)], fill=POP)
d.text((72, 245), line2, font=serif(50), fill=INK)
# three numbers
stats = [(f"{top10*100:.0f}%", "of bankruptcies were in the\nriskiest 10% of companies"),
         (f"{alt10*100:.0f}%", "for the classic Altman\nZ-Score's riskiest 10%"),
         (f"{comp['faultline_auc']:.2f}", f"ranking accuracy (AUC)\nvs {comp['altman']['auc']:.2f} for Altman")]
for i, (v, label) in enumerate(stats):
    x = 72 + i * 360
    d.line([(x, 372), (x + 320, 372)], fill=RULE, width=2)
    d.text((x, 388), v, font=sans_b(64), fill=INK)
    d.multiline_text((x, 470), label, font=sans(24), fill=INK2, spacing=6)
d.text((72, 570), "Out-of-sample test, 2016-2023, US public companies incl. those that failed. Research, not investment advice.",
       font=sans(20), fill=INK2)
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, optimize=True)
print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
