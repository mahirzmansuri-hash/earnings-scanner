# Design Notes

One entry per decision: what we chose, why, and what we gave up. Newest at the bottom.

## 2026-11-25: Python 3.12 in a venv
- **Why:** macOS ships Python 3.9, which is too old for current pandas. A venv keeps project packages separate from the system Python.
- **Trade-off:** you must activate it (`source .venv/bin/activate`) or call `.venv/bin/python`.

## 2026-11-25: Pinned versions in requirements.txt
- **Why:** Streamlit Cloud installs exactly what's listed, so the app runs the same there as on my Mac.
- **Trade-off:** upgrades are a deliberate step, not automatic.

## 2026-11-25: DuckDB as the database
- **Why:** a single file with no server, fast on the column-heavy queries a screener and backtest need, and it reads pandas DataFrames directly.

## 2026-11-25: SEC User-Agent lives in `.env`
- **Why:** SEC requires a name and email. Hardcoding it would publish my email on GitHub. `src/config.py` is the only reader, and it fails loudly if the value is missing.

## 2026-11-25: Raw data and the database are not committed
- **Why:** the files are large and can be rebuilt from EDGAR. `data/` is gitignored except the `.gitkeep` placeholders.

## 2026-11-26: Claude does the lookups and teaches
- **Why:** my time (2-3 hrs/week) goes further learning *why* than hunting through SEC pages. Claude fetches and verifies the filings itself, then explains the results as a lesson.
- **Trade-off:** I must still be able to explain everything, so every module ends with a quiz.

## 2026-11-26: Two versions of each number
- **Backtest:** first-filed value (what investors knew then). **Lookup page:** latest-filed value (most accurate today).
- **Why:** using corrected numbers in a backtest is look-ahead bias. Comparing the two versions also detects restatements, which are a red flag.

## 2026-11-26: Schedule in modules, not weeks
- **Why:** progress is measured by topics learned and built, not by the calendar. Each module has 3-5 topics and ends with a quiz.

## 2026-11-26: Name and look: "Faultline"
- **Name:** Faultline. Tagline: "Find the cracks in a company's numbers before the stock breaks." A quick web search found no finance product with this name (not a trademark check).
- **Format:** a website (Streamlit app, custom theme). Shown with a 30-60 s demo clip, a GitHub page, and the 2-page write-up.
- **Look (v2, research-report style):** v1 (dark background, neon cyan, Space Grotesk/Inter, glowing animation) read as generic AI design and was rejected. v2 is styled like an equity research note: white paper / near-black ink, ink blue #1B3A5C as the only brand color, forest / ochre / brick for safe / gray zone / risk. Fonts: Source Serif 4 (headings), Libre Franklin (text, tabular numbers), IBM Plex Mono (identifiers only). Dark mode mirrors the same tokens.
- **Pop color (v3): highlighter yellow #FFE24A** (dark mode #E9CF3A), always with ink text on top. Used once per screen on the single most important fact (the key score, the key finding), plus the logo's break and text selection. **Why:** big brands keep 90%+ neutral and use one signature accent sparingly (60-30-10 rule; FT's salmon has a story from 1893). Ours has a story too: forensic analysts read 10-Ks with a highlighter.
- **Rules:** no gradients, glows, shadows, animation, icons or emoji; corners 2px max; color never the only signal; every number shows its source and filing date; tables before cards.
- **Signature visuals:** point-in-time slider, Beneish ratio table vs Beneish (1999) group means, Screener table, Z-Score chart with distress zones.
- **Why:** looks like professional research, not a template. It sets the project apart from data-extraction dashboards because it judges the numbers and proves the judgment with a backtest. Concept board: https://claude.ai/artifact/KqXTTugqFM6opLPiQYc8TY (private).
- **Case studies must be 10-K filers:** Luckin Coffee (20-F filer) is out. Candidates to verify: GE, Kraft Heinz, MiMedx (accounting), Sears, Bed Bath & Beyond, Rite Aid (bankruptcy).
