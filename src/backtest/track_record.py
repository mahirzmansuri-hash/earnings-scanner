"""Faultline's track record: did the scores warn BEFORE bankruptcies and restatements?

Run:  python -m src.backtest.track_record   (after src.scores.compute and src.pipeline.events)

Method (point-in-time; non-financial companies only, since the scores aren't built for banks):
  Hit rate     For each company's FIRST bankruptcy notice (8-K Item 1.03), take the latest
               score that was public between `lead_min` and 24 months before it. Was it flagged?
  Alarm rate   Share of ALL scored company-years that were flagged. A useless score would have
               a hit rate equal to its alarm rate (it flags everyone equally).
  Lift         hit rate / alarm rate. "Flagged companies were N times more likely to be ones
               that went bankrupt than a random company."
  Precision    Of flagged company-years, the share followed by the event within 24 months.
Same for Beneish M vs restatements (8-K Item 4.02 "non-reliance"), using scores public
0-24 months before the restatement notice (the score is computed on the numbers later restated).
"""
import json

import duckdb
import pandas as pd

from src.config import DB_PATH, ROOT

OUT_JSON = ROOT / "data" / "processed" / "track_record.json"
WINDOW_DAYS = 730  # 24 months


def _evaluate(con, score_flag_sql: str, score_ok_sql: str, event: str, lead_min_days: int,
              first_event_only: bool, years=("2012-01-01", "2023-12-31")) -> dict:
    """score_flag_sql: SQL boolean for 'flagged'; score_ok_sql: SQL boolean for 'score exists'."""
    lo, hi = years
    first = "QUALIFY ROW_NUMBER() OVER (PARTITION BY cik ORDER BY filed) = 1" if first_event_only else ""
    r = con.execute(f"""
    WITH scored AS (
        SELECT s.*, s.available_date::DATE AS avail FROM scores s
        WHERE NOT s.is_financial AND {score_ok_sql}
    ),
    ev AS (
        SELECT cik, filed FROM events WHERE event = '{event}' {first}
    ),
    -- hit rate: latest score public in the warning window before each event
    before AS (
        SELECT e.cik, e.filed, ({score_flag_sql}) AS flagged
        FROM ev e JOIN scored s ON s.cik = e.cik
         AND s.avail BETWEEN e.filed - {WINDOW_DAYS} AND e.filed - {lead_min_days}
        WHERE e.filed BETWEEN DATE '{lo}' + {WINDOW_DAYS} AND DATE '{hi}' + {WINDOW_DAYS}
        QUALIFY ROW_NUMBER() OVER (PARTITION BY e.cik, e.filed ORDER BY s.avail DESC) = 1
    ),
    -- base rates over all scored company-years in the study period
    base AS (
        SELECT ({score_flag_sql}) AS flagged,
               EXISTS (SELECT 1 FROM events x WHERE x.cik = s.cik AND x.event = '{event}'
                       AND x.filed BETWEEN s.avail + {lead_min_days} AND s.avail + {WINDOW_DAYS}) AS followed
        FROM scored s WHERE s.avail BETWEEN DATE '{lo}' AND DATE '{hi}'
    )
    SELECT
      (SELECT COUNT(*) FROM ev WHERE filed BETWEEN DATE '{lo}' + {WINDOW_DAYS} AND DATE '{hi}' + {WINDOW_DAYS}) AS events_in_period,
      (SELECT COUNT(*) FROM before) AS events_with_score,
      (SELECT AVG(flagged::INT) FROM before) AS hit_rate,
      (SELECT COUNT(*) FROM base) AS company_years,
      (SELECT AVG(flagged::INT) FROM base) AS alarm_rate,
      (SELECT AVG(followed::INT) FROM base) AS base_event_rate,
      (SELECT AVG(followed::INT) FROM base WHERE flagged) AS precision_flagged,
      (SELECT AVG(followed::INT) FROM base WHERE NOT flagged) AS event_rate_unflagged
    """).df().iloc[0].to_dict()
    r["lift"] = r["hit_rate"] / r["alarm_rate"] if r["alarm_rate"] else None
    r["risk_ratio"] = (r["precision_flagged"] / r["event_rate_unflagged"]) if r["event_rate_unflagged"] else None
    counts = {"events_in_period", "events_with_score", "company_years"}
    return {k: (int(v) if k in counts else round(float(v), 4)) for k, v in r.items()}


TESTS = {
    "altman_z_distress__bankruptcy_12to24m": ("z_zone = 'distress'", "z_score IS NOT NULL", "bankruptcy", 365, True),
    "altman_z2_distress__bankruptcy_12to24m": ("z2_zone = 'distress'", "z2_score IS NOT NULL", "bankruptcy", 365, True),
    "altman_z_distress__bankruptcy_0to24m": ("z_zone = 'distress'", "z_score IS NOT NULL", "bankruptcy", 0, True),
    "piotroski_weak__bankruptcy_12to24m": ("f_score <= 3", "f_score IS NOT NULL", "bankruptcy", 365, True),
    "beneish_flag__restatement_0to24m": ("m_score > -1.78", "m_score IS NOT NULL", "non_reliance", 0, False),
    "altman_z_distress__late_10k_0to24m": ("z_zone = 'distress'", "z_score IS NOT NULL", "late_10k", 0, False),
}


def run() -> dict:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        results = {name: _evaluate(con, *args) for name, args in TESTS.items()}
    OUT_JSON.write_text(json.dumps(results, indent=2))
    for name, r in results.items():
        print(f"\n{name}")
        print(f"  events {r['events_in_period']:,} | with a score in window {r['events_with_score']:,}"
              f" | hit rate {r['hit_rate']:.1%} | alarm rate {r['alarm_rate']:.1%} | lift {r['lift']:.1f}x")
        print(f"  precision {r['precision_flagged']:.2%} vs {r['event_rate_unflagged']:.2%} unflagged"
              f" (risk ratio {r['risk_ratio']:.1f}x) over {r['company_years']:,} company-years")
    return results


if __name__ == "__main__":
    run()
