"""SEC Accounting and Auditing Enforcement Releases (AAERs): the SEC's own list of accounting-fraud cases.

Run:  python -m src.pipeline.aaer      (after universe; resumable, cached in data/raw/aaer/)

Why: a restatement (8-K Item 4.02) can be an honest mistake. An AAER means the SEC took action over
the accounting itself, so it is the standard "fraud" label in research (Dechow et al. 2011).

Steps
1. list:  download the SEC's AAER index (about 3,400 releases, 100 per page) -> date, respondents, document link.
2. match: respondents that are companies (Inc, Corp, ...) -> CIK, by normalised name against current
          and former names in companies.csv. Releases that name only people are not matched here.
3. years: download each matched release's document and read which fiscal years it says were misstated
          (see misstated_years). The label is: was this company-year's 10-K later part of an SEC accounting case?
"""
import html
import io
import json
import re
import time

import pandas as pd

from src.config import RAW_DIR, ROOT
from src.pipeline.edgar import _sec_get_bytes

LIST_URL = "https://www.sec.gov/enforcement-litigation/accounting-auditing-enforcement-releases?page={p}"
DIR = RAW_DIR / "aaer"
DOCS = DIR / "docs"
OUT = ROOT / "data" / "processed" / "aaer_cases.csv"

SUFFIX = r"\b(incorporated|inc|corporation|corp|company|co|ltd|limited|plc|llc|lp|l\.p|holdings?|group|n\.?v|s\.?a|ag|the)\b"
COMPANY_HINT = re.compile(r"\b(inc|corp|corporation|company|ltd|limited|plc|llc|holdings|group|n\.v|s\.a|technologies|bancorp)\b\.?", re.I)


def norm(name: str) -> str:
    n = html.unescape(str(name)).lower().replace("&", " and ")
    n = re.sub(r"\(.*?\)|/[a-z]{2,4}/?", " ", n)          # "(f/k/a ...)", EDGAR's state tags like /DE/
    n = re.sub(r"[^a-z0-9. ]", " ", n)
    n = re.sub(SUFFIX, " ", n)
    n = re.sub(r"[. ]+", " ", n)
    return n.strip()


def download_list() -> pd.DataFrame:
    DIR.mkdir(parents=True, exist_ok=True)
    rows, p = [], 0
    while True:
        h = _sec_get_bytes(LIST_URL.format(p=p)).decode("utf-8", "replace")
        trs = re.findall(r'<tr class="pr-list-page-row">(.*?)</tr>', h, re.S)
        if not trs:
            break
        for tr in trs:
            date = re.search(r'datetime="([0-9-]{10})', tr)
            link = re.search(r"<a href='([^']+)'>(.*?)</a>", tr, re.S)
            num = re.search(r"AAER-(\d+)", tr)
            if date and link and num:
                rows.append({"aaer": int(num.group(1)), "date": date.group(1), "url": link.group(1),
                             "respondents": html.unescape(re.sub(r"<[^>]+>", "", link.group(2))).strip()})
        p += 1
    df = pd.DataFrame(rows).drop_duplicates("aaer")
    df.to_csv(DIR / "aaer_list.csv", index=False)
    print(f"AAER list: {len(df):,} releases, {df['date'].min()} to {df['date'].max()} ({p} pages)")
    return df


def company_parts(respondents: str) -> list[str]:
    """'Key Tronic Corporation, Brett R. Larsen, CPA, and Nicholas S. Fasciana' -> ['Key Tronic Corporation']."""
    r = re.sub(r",\s*(Inc|LLC|Ltd|L\.?P|Corp|Co|N\.V|S\.A|PLC|LLP)\b", r" \1", respondents)   # keep "Latch, Inc." together
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+(?=[A-Z])|\s+\(?(?:f/k/a|n/k/a|formerly(?: known as)?)\s+", r)
    parts = [re.sub(r"\s*(\(corrected.*|et al\.?)$", "", p, flags=re.I) for p in parts]
    return [p.strip(" )") for p in parts if COMPANY_HINT.search(p) and not re.search(r"\b(LLP|CPAs?)\b", p)]


def match(aaers: pd.DataFrame) -> pd.DataFrame:
    co = pd.read_csv(ROOT / "data" / "processed" / "companies.csv")
    index = {}
    for r in co.itertuples():
        names = [r.name] + (str(r.former_names).split(" | ") if isinstance(r.former_names, str) else [])
        for n in names:
            k = norm(n)
            if len(k) >= 2:
                index.setdefault(k, set()).add(int(r.cik))
    n10k = dict(zip(co["cik"].astype(int), co["n_10k"]))
    out = []
    for a in aaers.itertuples():
        for part in company_parts(a.respondents):
            ciks = index.get(norm(part), set())
            if ciks:  # same name, several CIKs (e.g. a holding company and its subsidiary): keep the main 10-K filer
                out.append({"aaer": a.aaer, "date": a.date, "url": a.url, "respondent": part,
                            "cik": max(ciks, key=lambda c: n10k.get(c, 0)), "n_candidates": len(ciks)})
    m = pd.DataFrame(out)
    print(f"matched {m['aaer'].nunique():,} releases to {m['cik'].nunique():,} companies")
    return m


def doc_text(url: str) -> str:
    """Release text, cached. Most are PDFs; some older ones are HTML/TXT."""
    DOCS.mkdir(parents=True, exist_ok=True)
    if url.startswith("/"):
        url = "https://www.sec.gov" + url
    path = DOCS / (re.sub(r"[^A-Za-z0-9.-]", "_", url.split("/files/")[-1].split("/litigation/")[-1]) + ".txt")
    if path.exists():
        return path.read_text()
    try:
        raw = _sec_get_bytes(url)
    except Exception as e:  # noqa: BLE001 - a missing document just leaves that case without years
        print(f"  could not fetch {url}: {str(e)[:60]}")
        return ""
    if url.lower().endswith(".pdf"):
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(io.BytesIO(raw))
        text = "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))
    else:
        h = raw.decode("utf-8", "replace")
        h = re.sub(r"(?is)<(script|style|nav|header|footer).*?</\1>", " ", h)
        text = re.sub(r"<[^>]+>", " ", h)
        i = text.find("Litigation Release No")
        text = text[i:] if i >= 0 else text
    text = html.unescape(re.sub(r"\s+", " ", text))
    path.write_text(text)
    return text


YEAR_CONTEXT = re.compile(
    r"(?:fiscal(?: years?)?|years? ended|quarters? ended|periods? ended|FY|calendar(?: year)?|annual report[s]? for|"
    r"Form 10-K for|financial statements for|during|from|through|until|since|between|beginning in|quarter of|in)\s+(?:[A-Z][a-z]+\s+\d{1,2},\s+)?((?:19|20)\d{2})")


def misstated_years(text: str, release_year: int) -> list[int]:
    """Fiscal years the release describes, read from its first part (the summary of the misconduct).

    Heuristic: years that appear right after words like 'fiscal', 'year ended', 'from', 'through',
    inside the first 12,000 characters, before the release year, and not more than 10 years earlier.
    A range 'from 2014 through 2017' fills in the years between.
    """
    head = text[:12000]
    years = {int(y) for y in YEAR_CONTEXT.findall(head)}
    for a, b in re.findall(r"((?:19|20)\d{2})\s*(?:through|to|-|and)\s*((?:19|20)\d{2})", head):
        a, b = int(a), int(b)
        if 0 < b - a <= 8:
            years |= set(range(a, b + 1))
    return sorted(y for y in years if release_year - 10 <= y < release_year)


def kind(text: str) -> str:
    """AAERs also cover bribery (FCPA books-and-records) and procedural orders; only accounting cases are fraud labels."""
    head = text[:8000]
    if re.search(r"Foreign Corrupt Practices|FCPA|brib", head, re.I) and not re.search(r"restat|overstat|revenue recognition|improperly recogni", head, re.I):
        return "bribery"
    if re.search(r"Rule 12b-25", head) and not re.search(r"restat|overstat|misstat", head, re.I):
        return "late_filing_notice"
    if re.search(r"Order Granting Extension|Order (?:Instituting )?Proceedings Pursuant to Rule 102\(e\)", head[:1500], re.I):
        return "procedural"
    return "accounting" if head else "unknown"


def main():
    cached = DIR / "aaer_list.csv"
    fresh = cached.exists() and time.time() - cached.stat().st_mtime < 6 * 86400   # re-read the SEC list weekly
    lst = pd.read_csv(cached) if fresh else download_list()
    m = match(lst[lst["date"] >= "2010-01-01"])          # our filings start in 2009
    texts = [doc_text(u) for u in m["url"]]
    m["kind"] = [kind(t) for t in texts]
    m["years"] = [json.dumps(misstated_years(t, int(d[:4]))) for t, d in zip(texts, m["date"])]
    m.to_csv(OUT, index=False)
    with_years = (m["years"] != "[]").mean()
    print(f"wrote {OUT.relative_to(ROOT)}: {len(m):,} company cases, {with_years:.0%} with misstated years found")


if __name__ == "__main__":
    main()
