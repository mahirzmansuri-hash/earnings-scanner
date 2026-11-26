"""Download data from the SEC EDGAR API.

SEC rules we follow:
- Every request sends a User-Agent with a name and email (from .env).
- No more than 10 requests per second (we cap at 8 to be safe).
"""
import json
import time

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
