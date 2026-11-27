"""Load the company list and every annual-report XBRL fact into DuckDB.

Run:  python -m src.pipeline.load_db
Rebuilds data/db/scanner.duckdb from scratch each time (raw files are the source of truth).

Tables
  companies : one row per company (from data/processed/companies.csv)
  facts     : one row per reported number: which company, which tag (e.g. Revenues),
              which period, what value, and WHEN it was filed (for point-in-time work)
"""
import gzip
import json
import time

import duckdb
import pandas as pd

from src.config import DB_PATH
from src.pipeline.edgar import FACTS_DIR
from src.pipeline.universe import OUTPUT_CSV

ANNUAL_FORMS = {"10-K", "10-K/A", "10-KT", "10-KT/A"}  # /A = amendment (a corrected filing)
TAXONOMIES = {"us-gaap", "dei"}  # us-gaap = the accounting numbers; dei = cover-page info (shares out, etc.)
BATCH = 300  # companies per insert: big enough to be fast, small enough for memory

FACTS_SCHEMA = """
CREATE TABLE facts (
    cik          INTEGER,   -- company ID
    taxonomy     VARCHAR,   -- 'us-gaap' or 'dei'
    tag          VARCHAR,   -- e.g. 'Revenues', 'Assets'
    unit         VARCHAR,   -- 'USD', 'shares', 'USD/shares'
    period_start DATE,      -- empty for balance-sheet items (a single date, not a period)
    period_end   DATE,
    value        DOUBLE,
    accn         VARCHAR,   -- accession number: the ID of the filing it came from
    fy           INTEGER,   -- fiscal year OF THE FILING (not of the period! see gotchas)
    fp           VARCHAR,
    form         VARCHAR,   -- '10-K', '10-K/A', ...
    filed        DATE,      -- the day it became public: the key to point-in-time data
    frame        VARCHAR    -- SEC's calendar label, e.g. 'CY2023'; only on one row per period
)
"""


def _company_rows(cik: int, data: dict) -> list[tuple]:
    """Flatten one company's nested JSON into a list of rows."""
    rows = []
    for taxonomy, tags in data.get("facts", {}).items():
        if taxonomy not in TAXONOMIES:
            continue
        for tag, info in tags.items():
            for unit, values in info["units"].items():
                for v in values:
                    if v.get("form") in ANNUAL_FORMS:
                        rows.append((cik, taxonomy, tag, unit, v.get("start"), v["end"], v["val"],
                                     v["accn"], v.get("fy"), v.get("fp"), v["form"], v["filed"], v.get("frame")))
    return rows


def build_database() -> None:
    start = time.time()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)  # fresh build every time
    con = duckdb.connect(str(DB_PATH))

    con.execute(f"CREATE TABLE companies AS SELECT * FROM read_csv('{OUTPUT_CSV}', header=true, types={{'fiscal_year_end': 'VARCHAR'}})")
    con.execute(FACTS_SCHEMA)

    cols = ["cik", "taxonomy", "tag", "unit", "period_start", "period_end", "value",
            "accn", "fy", "fp", "form", "filed", "frame"]
    files = sorted(FACTS_DIR.glob("CIK*.json.gz"))
    rows: list[tuple] = []
    for i, path in enumerate(files, 1):
        cik = int(path.name[3:13])
        rows += _company_rows(cik, json.loads(gzip.decompress(path.read_bytes())))
        if i % BATCH == 0 or i == len(files):
            batch = pd.DataFrame(rows, columns=cols)  # noqa: F841 (DuckDB reads it by name)
            con.execute("INSERT INTO facts SELECT * FROM batch")
            rows = []
            print(f"{i:,}/{len(files):,} companies loaded", flush=True)

    n = con.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    con.close()
    print(f"Done: {n:,} facts in {time.time() - start:.0f}s, database {DB_PATH.stat().st_size / 1e9:.2f} GB")


if __name__ == "__main__":
    build_database()
