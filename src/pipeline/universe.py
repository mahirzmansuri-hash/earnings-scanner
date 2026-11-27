"""Build the company universe: every operating company that filed a 10-K since 2009.

Input:  data/raw/submissions.zip  (SEC bulk file, one JSON per entity)
Output: data/processed/companies.csv

Why this file exists: today's ticker list only has companies that are still alive.
Using it would drop every company that went bankrupt or was bought out
(survivorship bias). submissions.zip has everyone, dead or alive.
"""

import json
import zipfile
from datetime import date, timedelta

import pandas as pd

from src.config import RAW_DIR, ROOT

SUBMISSIONS_ZIP = RAW_DIR / "submissions.zip"
OUTPUT_CSV = ROOT / "data" / "processed" / "companies.csv"

ANNUAL_FORMS = {"10-K", "10-KT"}  # 10-KT = transition report when a company changes its fiscal year
START_DATE = "2009-01-01"         # XBRL starts phasing in during 2009

# Industry codes (SIC) we drop, because they are not real operating businesses
EXCLUDED_SIC = {
    6189: "Asset-backed securities (bond trusts)",
    6770: "Blank checks (SPACs)",
}
# Banks, insurers, REITs, etc. We KEEP these but flag them:
# Altman and Beneish were designed for industrial companies, so their scores mislead here.
FINANCIAL_SIC = range(6000, 6800)

ACTIVE_WINDOW = timedelta(days=548)  # about 18 months: no 10-K in that long = inactive


def _annual_filing_dates(filings: dict) -> list[str]:
    """Return filing dates of 10-K/10-KT forms from one block of filings."""
    return [
        filed
        for form, filed in zip(filings.get("form", []), filings.get("filingDate", []))
        if form in ANNUAL_FORMS
    ]


def _read_company(z: zipfile.ZipFile, name: str) -> dict | None:
    """Read one company's JSON (plus its overflow files) and return one row, or None to skip it."""
    data = json.loads(z.read(name))

    # Filings live in "recent", plus extra overflow files for companies with long histories
    dates = _annual_filing_dates(data["filings"]["recent"])
    for extra in data["filings"].get("files", []):
        dates += _annual_filing_dates(json.loads(z.read(extra["name"])))

    dates = sorted(d for d in dates if d >= START_DATE)
    if not dates:
        return None  # never filed an annual report in our period

    sic = int(data["sic"]) if data.get("sic") else None
    if sic is None or sic in EXCLUDED_SIC:
        return None

    return {
        "cik": int(data["cik"]),  # the permanent ID; names and tickers change, CIK never does
        "name": data["name"],
        "former_names": " | ".join(f["name"] for f in data.get("formerNames", [])),
        "tickers": " | ".join(data.get("tickers") or []),
        "exchanges": " | ".join(e for e in (data.get("exchanges") or []) if e),
        "sic": sic,
        "sic_description": data.get("sicDescription", ""),
        "is_financial": sic in FINANCIAL_SIC,
        "fiscal_year_end": data.get("fiscalYearEnd", ""),  # "MMDD", e.g. "0927" for Apple
        "first_10k": dates[0],
        "last_10k": dates[-1],
        "n_10k": len(dates),
    }


def build_universe() -> pd.DataFrame:
    """Scan submissions.zip and return one row per company in our universe."""
    rows, skipped = [], 0
    with zipfile.ZipFile(SUBMISSIONS_ZIP) as z:
        for name in z.namelist():
            if "-submissions-" in name or not name.endswith(".json"):
                continue  # overflow files are read together with their main file
            row = _read_company(z, name)
            if row is None:
                skipped += 1
            else:
                rows.append(row)

    df = pd.DataFrame(rows).sort_values("cik").reset_index(drop=True)
    cutoff = (date.today() - ACTIVE_WINDOW).isoformat()
    df["status"] = df["last_10k"].map(lambda d: "active" if d >= cutoff else "inactive")
    print(f"Kept {len(df):,} companies, skipped {skipped:,} entities")
    return df


if __name__ == "__main__":
    universe = build_universe()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {OUTPUT_CSV.relative_to(ROOT)}")
