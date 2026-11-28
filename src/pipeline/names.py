"""Readable company names: "America's Car-Mart, Inc." instead of SEC's "AMERICAS CARMART INC".

Run:  python -m src.pipeline.names     (reads the cached companyfacts files, no downloads)

SEC's company list stores about half of all names in capitals without punctuation. The XBRL filings carry
the registrant's own spelling (entityName), which keeps apostrophes, hyphens and commas but is often also in
capitals. So:
  1. use entityName when it is the same name as SEC's (same letters and digits, ignoring punctuation),
     otherwise SEC's name (entityName can be an old or odd legal name);
  2. if the result is all capitals, convert it to normal case, keeping acronyms and suffixes readable.
Table display_names (cik, display_name). The original SEC name stays in companies.name for matching.
"""
import gzip
import json
import re

import duckdb
import pandas as pd

from src.config import DB_PATH
from src.pipeline.edgar import FACTS_DIR

SUFFIX = {"INC": "Inc", "CORP": "Corp", "CO": "Co", "LTD": "Ltd", "LLC": "LLC", "LP": "LP", "PLC": "plc", "NV": "NV",
          "SA": "SA", "AG": "AG", "SE": "SE", "LLP": "LLP", "TR": "Tr", "HLDGS": "Hldgs", "INTL": "Intl", "BANCORP": "Bancorp",
          "CORPORATION": "Corporation", "INCORPORATED": "Incorporated", "COMPANY": "Company", "HOLDINGS": "Holdings"}
SMALL = {"OF", "AND", "THE", "FOR", "IN", "ON", "AT", "BY", "TO", "A", "AN", "OR", "DE", "DU", "LA"}
ACRONYMS = {"US", "USA", "UK", "AI", "IT", "TV", "BDC", "REIT", "ETF", "II", "III", "IV", "VI", "VII", "VIII", "IX", "XI",
            "IBM", "AIG", "GE", "GM", "HP", "AT&T", "CVS", "NRG", "MBIA", "AMC", "UPS", "CBS", "NBC", "ABC", "RPM", "SPX", "NCR",
            "AES", "CSX", "PPG", "PPL", "WEC", "CMS", "DTE", "ADT", "EQT", "AMD", "ATI", "BJ", "EOG", "FMC", "IDT", "KB", "MSC",
            "NL", "NVR", "PG", "PNC", "RLI", "SLM", "TJX", "UGI", "USG", "WD", "HCA", "HNI", "IAC", "ICU", "JPMORGAN", "NASDAQ",
            "ADR", "ESG", "LNG", "RV", "SPAC", "MLP", "NA", "FSB", "SB"}
FIXED = {"JPMORGAN": "JPMorgan", "NASDAQ": "Nasdaq"}
VOWELS = set("AEIOUY")


def _word(w: str, first: bool) -> str:
    core = re.sub(r"[^A-Z0-9&]", "", w)
    if not core:
        return w
    if core in FIXED:
        return w.replace(core, FIXED[core])
    if core in SUFFIX:
        return w.replace(core, SUFFIX[core])
    if core in SMALL and not first:
        return w.lower()
    if core in ACRONYMS or any(ch.isdigit() for ch in core) or "&" in core or not (set(core) & VOWELS):
        return w                                   # acronym, number or no vowels (e.g. "CVS", "HSBC"): keep capitals
    if "." in w and len(core) <= 3:
        return w                                   # "U.S.", "N.V."
    out, cap = [], True                            # capital after a hyphen or slash, lower after an apostrophe
    for ch in w:
        out.append(ch.upper() if cap else ch.lower())
        cap = ch in "-/("
    return "".join(out)


def nice_case(name: str) -> str:
    if not isinstance(name, str) or any(ch.islower() for ch in name):
        return name                                # already mixed case: trust it
    words = name.split()
    return " ".join(_word(w, i == 0) for i, w in enumerate(words))


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower().replace("&", "and"))


STATE_TAG = re.compile(r"\s*/\s*[A-Za-z]{2,3}\s*/?(\s+NEW)?\s*$", re.I)     # SEC's state of incorporation, e.g. "CLOROX CO /DE/"


def pick(sec_name: str, entity_name) -> str:
    sec_name = STATE_TAG.sub("", sec_name)
    base = entity_name if isinstance(entity_name, str) and _norm(entity_name) == _norm(sec_name) else sec_name
    return nice_case(base.replace("’", "'").strip())


def _entity(path) -> tuple[int, str | None]:
    try:
        return int(path.name[3:13]), json.loads(gzip.decompress(path.read_bytes())).get("entityName")
    except (OSError, ValueError):
        return int(path.name[3:13]), None


def build(con) -> pd.DataFrame:
    from multiprocessing import Pool
    with Pool(6) as pool:
        ent = dict(pool.map(_entity, sorted(FACTS_DIR.glob("CIK*.json.gz")), chunksize=50))
    comp = con.execute("SELECT cik, name FROM companies").df()
    comp["display_name"] = [pick(n, ent.get(c)) for c, n in zip(comp["cik"], comp["name"])]
    out = comp[["cik", "display_name"]]
    con.register("dn", out)
    con.execute("CREATE OR REPLACE TABLE display_names AS SELECT * FROM dn ORDER BY cik")
    con.unregister("dn")
    changed = (comp["display_name"] != comp["name"]).sum()
    print(f"display_names: {len(out):,} companies, {changed:,} names made readable")
    return comp


if __name__ == "__main__":
    with duckdb.connect(str(DB_PATH)) as con:
        c = build(con)
    print(c[c["display_name"] != c["name"]].sample(25, random_state=1).to_string(index=False))
