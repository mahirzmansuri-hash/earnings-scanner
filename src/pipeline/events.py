"""Warning-event table: every bankruptcy notice, restatement, auditor change and late filing.

Run:  python -m src.pipeline.events   (after load_db)

Source: data/raw/submissions.zip (already downloaded; no new SEC requests).
These events are the "answer key" for testing whether the scores warned in advance.

event                 form / 8-K item    meaning
bankruptcy            8-K Item 1.03      the company filed for bankruptcy or receivership
non_reliance          8-K Item 4.02      "don't rely on our past financial statements" = a true restatement
auditor_change        8-K Item 4.01      the auditor resigned or was dismissed
late_10k              NT 10-K            the company said its annual report would be late
amended_10k           10-K/A             the annual report was amended after filing
change_in_control     8-K Item 5.01      someone took control (usually a completed buyout)
deregistration        Form 15            the company ended its SEC registration (stops filing)
"""
import json
import zipfile

import duckdb
import pandas as pd

from src.config import DB_PATH
from src.pipeline.universe import OUTPUT_CSV, SUBMISSIONS_ZIP

START = "2009-01-01"
ITEM_EVENTS = {"1.03": "bankruptcy", "4.02": "non_reliance", "4.01": "auditor_change", "5.01": "change_in_control"}
FORM_EVENTS = {"NT 10-K": "late_10k", "10-K/A": "amended_10k",
               "15-12G": "deregistration", "15-12B": "deregistration", "15-15D": "deregistration"}


def _events_for(cik: int, filings: dict) -> list[tuple]:
    rows = []
    items_list = filings.get("items") or [""] * len(filings["form"])
    for form, filed, accn, items in zip(filings["form"], filings["filingDate"], filings["accessionNumber"], items_list):
        if filed < START:
            continue
        if form == "8-K":
            for code in (items or "").split(","):
                if code.strip() in ITEM_EVENTS:
                    rows.append((cik, ITEM_EVENTS[code.strip()], filed, form, accn))
        elif form in FORM_EVENTS:
            rows.append((cik, FORM_EVENTS[form], filed, form, accn))
    return rows


def build_events(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    ciks = pd.read_csv(OUTPUT_CSV, usecols=["cik"])["cik"].tolist()
    rows = []
    with zipfile.ZipFile(SUBMISSIONS_ZIP) as z:
        for cik in ciks:
            data = json.loads(z.read(f"CIK{cik:010d}.json"))
            rows += _events_for(cik, data["filings"]["recent"])
            for extra in data["filings"].get("files", []):
                rows += _events_for(cik, json.loads(z.read(extra["name"])))
    events = pd.DataFrame(rows, columns=["cik", "event", "filed", "form", "accn"]).drop_duplicates()
    events["filed"] = pd.to_datetime(events["filed"]).dt.date
    con.register("events_df", events)  # distinct name, or DuckDB would read the old "events" table
    con.execute("CREATE OR REPLACE TABLE events AS SELECT * FROM events_df")
    con.unregister("events_df")
    summary = events.groupby("event").agg(filings=("accn", "size"), companies=("cik", "nunique"))
    print(summary.to_string())
    return events


if __name__ == "__main__":
    with duckdb.connect(str(DB_PATH)) as con:
        build_events(con)
