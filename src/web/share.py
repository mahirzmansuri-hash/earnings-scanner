"""Share card for the Receipts page (1200x630 PNG: the preview when the link is posted on Reddit, HN, iMessage...).

Made during every site build from the same numbers as the page, so the card is never out of date.
One dot per bankrupt company that had a score: filled = it was already in Faultline's riskiest 10%.
Fonts: Georgia/Arial on a Mac, DejaVu on the GitHub runner (Ubuntu), Pillow's built-in font as a last resort.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAPER, INK, INK2, RULE, BRAND, POP, POPFILL = "#FFFFFF", "#15191E", "#525A63", "#D9DCDF", "#1B3A5C", "#0FB3C8", "#D5F4F8"
FONTS = {"serif": ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
         "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
         "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]}


def font(kind: str, size: int):
    for p in FONTS[kind]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def receipts_card(out: Path, flagged: int, scored: int, median_days: int | None, as_of) -> None:
    img = Image.new("RGB", (1200, 630), PAPER)
    d = ImageDraw.Draw(img)
    d.line([(72, 82), (104, 82)], fill=BRAND, width=7)
    d.line([(110, 100), (142, 100)], fill=BRAND, width=7)
    d.line([(104, 82), (110, 100)], fill=POP, width=7)
    d.text((160, 66), "Faultline  ·  Receipts", font=font("serif", 40), fill=INK)
    d.line([(72, 140), (1128, 140)], fill=RULE, width=2)
    head = f"{flagged} of {scored} companies that went bankrupt"
    d.text((72, 170), head, font=font("serif", 50), fill=INK)
    line2 = "were already in our riskiest 10%."
    w = d.textlength(line2, font=font("serif", 50))
    d.rectangle([(68, 241), (76 + w, 301)], fill=POPFILL)
    d.rectangle([(68, 297), (76 + w, 301)], fill=POP)
    d.text((72, 240), line2, font=font("serif", 50), fill=INK)
    # one dot per company: filled = flagged
    per_row, r, gap = 26, 15, 40
    for i in range(scored):
        x, y = 72 + (i % per_row) * gap + r, 350 + (i // per_row) * gap + r
        if i < flagged:
            d.ellipse([(x - r, y - r), (x + r, y + r)], fill=BRAND)
        else:
            d.ellipse([(x - r, y - r), (x + r, y + r)], outline=INK2, width=3)
    y0 = 350 + ((scored - 1) // per_row + 1) * gap + 14
    chance = round(scored * 0.1)
    sub = f"By chance, about {chance} would be.  First flagged a median of {median_days} days before filing." if median_days else \
          f"By chance, about {chance} would be."
    d.text((72, y0), sub, font=font("sans", 28), fill=INK2)
    d.text((72, 570), f"US bankruptcy filings (8-K Item 1.03), 12 months to {as_of}. Free, from SEC filings. Research, not investment advice.",
           font=font("sans", 20), fill=INK2)
    img.save(out, optimize=True)
