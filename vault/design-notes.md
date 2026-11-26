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
