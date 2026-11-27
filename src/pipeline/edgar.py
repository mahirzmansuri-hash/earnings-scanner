"""Download data from the SEC EDGAR API.

SEC rules we follow:
- Every request sends a User-Agent with a name and email (from .env).
- No more than 10 requests per second (we cap at 8 to be safe).
"""
import gzip
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from src.config import RAW_DIR, SEC_MAX_REQUESTS_PER_SEC, sec_user_agent

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

_MIN_SECONDS_BETWEEN_REQUESTS = 1 / SEC_MAX_REQUESTS_PER_SEC
_next_request_time = 0.0
_rate_lock = threading.Lock()  # several download threads share ONE rate limit


def _wait_for_turn() -> None:
    """Block until we're allowed to send the next request (max 8 per second overall)."""
    global _next_request_time
    with _rate_lock:  # only one thread at a time can claim a time slot
        now = time.time()
        slot = max(now, _next_request_time)
        _next_request_time = slot + _MIN_SECONDS_BETWEEN_REQUESTS
    time.sleep(max(0.0, slot - now))


def _sec_get_bytes(url: str) -> bytes:
    """GET a SEC URL politely (User-Agent header + rate limit) and return the raw bytes."""
    _wait_for_turn()
    response = requests.get(url, headers={"User-Agent": sec_user_agent()}, timeout=60)
    response.raise_for_status()  # stop with an error on 403, 404, etc.
    return response.content


def _sec_get(url: str) -> dict:
    """GET a SEC URL and parse the JSON."""
    return json.loads(_sec_get_bytes(url))


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


FACTS_DIR = RAW_DIR / "companyfacts"
NO_XBRL_FILE = FACTS_DIR / "_no_xbrl.txt"  # CIKs where SEC has no XBRL facts (404)


def _facts_path(cik: int) -> Path:
    return FACTS_DIR / f"CIK{cik:010d}.json.gz"


def _download_facts(cik: int) -> bool:
    """Download one company's facts to disk (gzip). Returns False if SEC has none (404)."""
    try:
        raw = _sec_get_bytes(COMPANYFACTS_URL.format(cik=f"{cik:010d}"))
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return False
        raise
    path = _facts_path(cik)
    tmp = path.with_suffix(".part")          # write to .part, rename when complete
    tmp.write_bytes(gzip.compress(raw))      # JSON shrinks ~15x (27 GB -> ~1.7 GB)
    tmp.rename(path)
    return True


def fetch_company_facts(cik: int, refresh: bool = False) -> dict | None:
    """Return every XBRL fact a company has reported, as a dict (None if SEC has none).

    cik: the company's SEC ID number (Apple = 320193).
    Caches gzip-compressed JSON in data/raw/companyfacts/ and reuses it next time,
    unless refresh=True.
    """
    path = _facts_path(cik)
    if refresh or not path.exists():
        FACTS_DIR.mkdir(parents=True, exist_ok=True)
        if not _download_facts(cik):
            return None
    return json.loads(gzip.decompress(path.read_bytes()))


def download_all_company_facts(ciks: list[int], threads: int = 4) -> None:
    """Download facts for many companies. Safe to stop and re-run: it skips finished ones.

    Threads let one request download while the next one starts, but they all share
    the same 8-per-second limit, so SEC sees the same polite rate.
    """
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    no_xbrl = set(map(int, NO_XBRL_FILE.read_text().split())) if NO_XBRL_FILE.exists() else set()
    todo = [c for c in ciks if c not in no_xbrl and not _facts_path(c).exists()]
    print(f"{len(ciks):,} companies: {len(ciks) - len(todo):,} already done, {len(todo):,} to download", flush=True)

    lock, done, missing, failed = threading.Lock(), 0, 0, []
    start = time.time()

    def work(cik: int) -> None:
        nonlocal done, missing
        try:
            ok = _download_facts(cik)
        except Exception as e:  # network blip etc.: note it, keep going, re-run later
            with lock:
                failed.append((cik, repr(e)[:80]))
            return
        with lock:
            done += 1
            if not ok:
                missing += 1
                with open(NO_XBRL_FILE, "a") as f:
                    f.write(f"{cik}\n")
            if done % 500 == 0:
                rate = done / (time.time() - start)
                print(f"{done:,}/{len(todo):,}  ({rate:.1f}/s, ~{(len(todo) - done) / rate / 60:.0f} min left)", flush=True)

    with ThreadPoolExecutor(threads) as pool:
        list(pool.map(work, todo))

    print(f"Finished: {done:,} done ({missing:,} had no XBRL), {len(failed)} failed", flush=True)
    for cik, err in failed[:10]:
        print("  failed:", cik, err)
