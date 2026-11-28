"""Check that recent "bankruptcy" 8-Ks really are about bankruptcy.

Run:  python -m src.pipeline.verify_bk     (after events)

Our bankruptcy events come from SEC's filing index, which lists the 8-K items the filer tagged. Tags can be
wrong: Granite Construction's 8-K of Feb 18, 2026 is tagged Item 1.03 (bankruptcy) but is about a note exchange.
For the public Receipts page we read every bankruptcy 8-K from the last 2 years and keep it only if the text
mentions Item 1.03, chapter 11/7, a bankruptcy court or receivership.

Results are cached in data/raw/bk_check.json (each filing is read once). Table bk_verified(accn, verified).
"""
import html
import json
import re
import time

import duckdb
import requests

from src.config import DB_PATH, RAW_DIR, sec_user_agent

CACHE = RAW_DIR / "bk_check.json"
WORDS = re.compile(r"item\s*1\.03|chapter\s*(11|7)\b|bankruptcy\s+court|receiver(ship)?\b", re.I)


def check(cik: int, accn: str, head: dict) -> bool | None:
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn.replace('-', '')}/"
    try:
        items = requests.get(base + "index.json", headers=head, timeout=30).json()["directory"]["item"]
        # skip the full-submission .txt: its SEC header repeats the filer's item tags ("Bankruptcy or Receivership")
        docs = sorted((x for x in items if x["name"].lower().endswith((".htm", ".html", ".txt")) and "index" not in x["name"]
                       and x["name"] != f"{accn}.txt"),
                      key=lambda x: ("8k" not in x["name"].lower().replace("-", ""), -int(x.get("size") or 0)))
        for d in docs[:5]:                      # the 8-K itself first, then the largest exhibits
            time.sleep(0.15)                    # stay well under SEC's 10 requests per second
            t = requests.get(base + d["name"], headers=head, timeout=30).text
            if WORDS.search(html.unescape(re.sub(r"<[^>]+>", " ", t))):
                return True
        return False
    except (requests.RequestException, ValueError, KeyError):
        return None                             # couldn't read it: try again next run


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    head = {"User-Agent": sec_user_agent()}
    with duckdb.connect(str(DB_PATH)) as con:
        ev = con.execute("""SELECT cik, accn FROM events WHERE event = 'bankruptcy'
                            AND filed >= (SELECT MAX(filed) FROM events) - INTERVAL 730 DAY ORDER BY filed""").fetchall()
        for cik, accn in ev:
            if not cache.get(accn):           # unread or failed: (re)check, so a fix to check() applies to old misses
                cache[accn] = check(cik, accn, head)
        CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True))
        con.execute("CREATE OR REPLACE TABLE bk_verified (accn VARCHAR, verified BOOLEAN)")
        con.executemany("INSERT INTO bk_verified VALUES (?, ?)", [(a, v) for a, v in cache.items() if v is not None])
    bad = [a for a, v in cache.items() if v is False]
    print(f"bk_verified: {len(ev)} recent bankruptcy 8-Ks checked, {len(bad)} not about bankruptcy: {bad}")


if __name__ == "__main__":
    main()
