"""Weekly update: refresh SEC data, rebuild everything, write the site.

Run:  python -m src.pipeline.update               (full weekly run)
      python -m src.pipeline.update --skip-download  (reuse submissions.zip; for local tests)

Incremental: companyfacts are re-downloaded only for companies whose latest 10-K was
filed after we last fetched them (tracked in data/raw/companyfacts/_manifest.json), plus
brand-new companies. Everything downstream is rebuilt from scratch (a few minutes).
"""
import json
import sys
import time
from datetime import date, datetime, timedelta

import duckdb
import pandas as pd

from src.config import DB_PATH
from src.pipeline.edgar import FACTS_DIR, NO_XBRL_FILE, _facts_path, download_all_company_facts, download_bulk_file
from src.pipeline.universe import OUTPUT_CSV, build_universe

MANIFEST = FACTS_DIR / "_manifest.json"


def _load_manifest() -> dict[int, str]:
    if MANIFEST.exists():
        return {int(k): v for k, v in json.loads(MANIFEST.read_text()).items()}
    # first run: use each cached file's modified date as its fetch date
    m = {int(p.name[3:13]): date.fromtimestamp(p.stat().st_mtime).isoformat() for p in FACTS_DIR.glob("CIK*.json.gz")}
    if NO_XBRL_FILE.exists():
        d = date.fromtimestamp(NO_XBRL_FILE.stat().st_mtime).isoformat()
        m.update({int(c): d for c in NO_XBRL_FILE.read_text().split()})
    return m


def refresh_facts(universe: pd.DataFrame) -> int:
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()
    stale = []
    for cik, last_10k in zip(universe["cik"], universe["last_10k"]):
        fetched = manifest.get(int(cik))
        # refetch if never fetched, or a 10-K was filed on/after the day before we fetched
        if fetched is None or last_10k >= (datetime.fromisoformat(fetched) - timedelta(days=1)).date().isoformat():
            stale.append(int(cik))
    no_xbrl = set(map(int, NO_XBRL_FILE.read_text().split())) if NO_XBRL_FILE.exists() else set()
    for cik in stale:  # clear old copies so the downloader fetches them again
        _facts_path(cik).unlink(missing_ok=True)
        no_xbrl.discard(cik)
    NO_XBRL_FILE.write_text("".join(f"{c}\n" for c in sorted(no_xbrl)))
    print(f"{len(stale):,} companies have new filings or are new; refreshing them", flush=True)
    download_all_company_facts(universe["cik"].tolist())
    today = date.today().isoformat()
    manifest.update({c: today for c in stale})
    MANIFEST.write_text(json.dumps({str(k): v for k, v in sorted(manifest.items())}))
    return len(stale)


def step(name, fn):
    t = time.time()
    print(f"\n== {name}", flush=True)
    out = fn()
    print(f"   done in {time.time() - t:.0f}s", flush=True)
    return out


def main(skip_download: bool = False):
    if not skip_download:
        step("download submissions.zip", lambda: download_bulk_file("submissions.zip", refresh=True))
    universe = step("build company universe", build_universe)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(OUTPUT_CSV, index=False)
    if not skip_download:
        step("refresh companyfacts", lambda: refresh_facts(universe))

    from src.pipeline.load_db import build_database
    step("load DuckDB", build_database)
    from src.pipeline.annual import build_annual
    from src.pipeline.events import build_events
    from src.scores.compute import build_scores
    def with_con(fn):  # fresh connection per step (DuckDB 2.0 blocks a connection with unread results)
        def run():
            with duckdb.connect(str(DB_PATH)) as con:
                return fn(con)
        return run
    step("annual values", with_con(build_annual))
    step("events", with_con(build_events))
    step("scores", with_con(build_scores))

    from src.backtest import track_record
    from src.model import ablation, composite, distress_exit, live, restatement, robustness
    step("track record", track_record.run)
    step("bankruptcy model test", composite.main)
    step("ablation", ablation.main)
    step("restatement model test", restatement.main)
    step("distress-exit test", distress_exit.main)
    step("robustness", robustness.main)
    step("live risk", live.main)
    from src.backtest import returns
    step("stock outcomes", returns.main)

    from src.web.build import build
    step("build site", build)


if __name__ == "__main__":
    main(skip_download="--skip-download" in sys.argv)
