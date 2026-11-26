"""Download data from the SEC EDGAR API.

SEC rules we follow:
- Every request sends a User-Agent with a name and email (from .env).
- No more than 10 requests per second (we cap at 8 to be safe).
"""
import json
import time
from pathlib import Path

import requests

from src.config import RAW_DIR, SEC_MAX_REQUESTS_PER_SEC, sec_user_agent

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

_MIN_SECONDS_BETWEEN_REQUESTS = 1 / SEC_MAX_REQUESTS_PER_SEC
_last_request_time = 0.0


def _sec_get(url: str) -> dict:
    """GET a SEC URL politely: User-Agent header + rate limit."""
    global _last_request_time
    wait = _MIN_SECONDS_BETWEEN_REQUESTS - (time.time() - _last_request_time)
    if wait > 0:
        time.sleep(wait)

    response = requests.get(url, headers={"User-Agent": sec_user_agent()}, timeout=30)
    _last_request_time = time.time()
    response.raise_for_status()  # stop with an error on 403, 404, etc.
    return response.json()


BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/{name}"


def download_bulk_file(name: str, refresh: bool = False) -> Path:
    """Download one of SEC's big bulk files (e.g. submissions.zip) to data/raw/.

    Streams in 1 MB chunks (never holds the whole file in memory) and writes to
    a .part file first, renaming only when complete, so a crashed download is
    never mistaken for a finished one.
    """
    path = RAW_DIR / name
    if path.exists() and not refresh:
        return path

    part = path.with_suffix(path.suffix + ".part")
    headers = {"User-Agent": sec_user_agent()}
    with requests.get(BULK_URL.format(name=name), headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        with open(part, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total and done % (100 << 20) < (1 << 20):  # progress every ~100 MB
                    print(f"{name}: {done / 1e9:.2f} / {total / 1e9:.2f} GB", flush=True)
    part.rename(path)
    return path


def fetch_company_facts(cik: int, refresh: bool = False) -> dict:
    """Return every XBRL fact a company has reported, as a dict.

    cik: the company's SEC ID number (Apple = 320193).
    Saves the raw JSON to data/raw/companyfacts/ and reuses it next time,
    unless refresh=True.
    """
    cik10 = f"{cik:010d}"  # SEC URLs need the CIK padded to 10 digits
    path = RAW_DIR / "companyfacts" / f"CIK{cik10}.json"

    if path.exists() and not refresh:
        return json.loads(path.read_text())

    data = _sec_get(COMPANYFACTS_URL.format(cik=cik10))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data
