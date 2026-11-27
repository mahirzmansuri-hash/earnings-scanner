"""Turn raw facts into clean annual values: one number per company, concept and fiscal year.

Run:  python -m src.pipeline.annual   (after load_db)

Creates two tables in DuckDB:
  annual       long format: cik, concept, period_end, plus TWO versions of the value
                 first  = as originally filed  -> backtest (point-in-time, no look-ahead)
                 latest = most recent filing   -> Lookup page (most accurate today)
               and a 'revised' flag when they differ by more than 0.5%. A revision can be
               a RESTATEMENT (fixing an error: a red flag) or a RECAST (re-presenting old
               years after a rule change or selling a division: normal). This flag can't
               tell them apart; 10-K/A filings and 8-K Item 4.02 notices can (later).
  annual_first wide format for the backtest: one row per company-year, one column per
               concept, plus 'available_date' = the day all of it was public.

Point-in-time rule: the first-filed value is picked by FILING DATE FIRST, then tag
priority. If we picked by tag priority first, a 2018 reprint using a newer tag could
replace a 2016 original, which would leak information from 2018 into 2016.
"""
import duckdb

from src.config import DB_PATH
from src.pipeline.tag_map import CONCEPTS, DERIVED

ANNUAL_DAYS = (350, 380)   # a fiscal year is ~365 days; 52/53-week years are 364 or 371
RESTATE_TOLERANCE = 0.005  # differences under 0.5% are treated as rounding, not revisions


def _load_concept_tags(con: duckdb.DuckDBPyConnection) -> None:
    rows = [(concept, tag, priority, spec["kind"], spec.get("pick", "priority"))
            for concept, spec in CONCEPTS.items()
            for priority, tag in enumerate(spec["tags"])]
    con.execute("CREATE OR REPLACE TABLE concept_tags (concept VARCHAR, tag VARCHAR, priority INTEGER, kind VARCHAR, pick VARCHAR)")
    con.executemany("INSERT INTO concept_tags VALUES (?, ?, ?, ?, ?)", rows)


def build_annual(con: duckdb.DuckDBPyConnection) -> None:
    _load_concept_tags(con)
    lo, hi = ANNUAL_DAYS
    is_annual = f"period_start IS NOT NULL AND date_diff('day', period_start, period_end) BETWEEN {lo} AND {hi}"

    con.execute(f"""
    CREATE OR REPLACE TABLE annual AS
    WITH
    -- every fiscal-year-end date a company has (from any full-year income/cash-flow fact)
    fiscal_year_ends AS (
        SELECT DISTINCT cik, period_end FROM facts WHERE {is_annual}
    ),
    -- the fiscal year each FILING is about (its latest full-year period)
    filing_year AS (
        SELECT cik, accn, MAX(period_end) AS fye FROM facts WHERE {is_annual} GROUP BY cik, accn
    ),
    candidates AS (
        -- income statement / cash flow: full-year periods only (drops quarters inside 10-Ks)
        SELECT f.cik, ct.concept, ct.priority, ct.pick, f.period_end, f.value, f.filed, f.accn, f.form
        FROM facts f JOIN concept_tags ct ON f.tag = ct.tag AND ct.kind = 'duration'
        WHERE f.taxonomy = 'us-gaap' AND f.{is_annual}
        UNION ALL
        -- balance sheet: snapshots taken exactly on a fiscal year end
        SELECT f.cik, ct.concept, ct.priority, ct.pick, f.period_end, f.value, f.filed, f.accn, f.form
        FROM facts f
        JOIN concept_tags ct ON f.tag = ct.tag AND ct.kind = 'instant'
        JOIN fiscal_year_ends y ON y.cik = f.cik AND y.period_end = f.period_end
        WHERE f.taxonomy = 'us-gaap' AND f.period_start IS NULL
        UNION ALL
        -- cover-page shares (dei) are dated near the filing day: assign to the filing's own year
        SELECT f.cik, ct.concept, ct.priority, ct.pick, fy.fye, f.value, f.filed, f.accn, f.form
        FROM facts f
        JOIN concept_tags ct ON f.tag = ct.tag
        JOIN filing_year fy ON fy.cik = f.cik AND fy.accn = f.accn
        WHERE f.taxonomy = 'dei'
    ),
    -- Referee for revenue: gross profit and COGS reported in the SAME filing for the same year.
    -- In 14% of filings, revenue tags disagree (e.g. one is a component). The right total
    -- is the one where revenue - COGS = gross profit. Same filing only, so no look-ahead.
    referee AS (
        SELECT cik, accn, period_end,
               MAX(value) FILTER (WHERE tag = 'GrossProfit') AS gp,
               MAX(value) FILTER (WHERE tag IN ('CostOfGoodsAndServicesSold', 'CostOfRevenue', 'CostOfGoodsSold')) AS cogs
        FROM facts WHERE taxonomy = 'us-gaap' AND {is_annual}
        GROUP BY cik, accn, period_end
    ),
    ranked0 AS (
        SELECT c.*,
          -- 1st choice for revenue: the value that passes the identity check
          CASE WHEN c.concept = 'revenue' AND r.gp IS NOT NULL AND r.cogs IS NOT NULL
               THEN abs(c.value - r.cogs - r.gp) <= 0.005 * abs(c.value) END AS identity_ok,
          -- then: 'largest' concepts take the biggest value, others the top-priority tag
          CASE WHEN c.pick = 'largest' THEN -abs(c.value) ELSE c.priority END AS tiebreak,
          ROW_NUMBER() OVER (PARTITION BY c.cik, c.concept, c.period_end
                             ORDER BY c.filed, c.accn, identity_ok DESC NULLS LAST, tiebreak) AS r_first,
          FIRST_VALUE(c.value) OVER (PARTITION BY c.cik, c.concept, c.period_end
                             ORDER BY c.filed, c.accn, identity_ok DESC NULLS LAST, tiebreak) AS first_value,
          COUNT(DISTINCT c.accn) OVER (PARTITION BY c.cik, c.concept, c.period_end) AS n_filings
        FROM candidates c
        LEFT JOIN referee r ON r.cik = c.cik AND r.accn = c.accn AND r.period_end = c.period_end
    ),
    ranked AS (
        -- latest version: newest filing; if its tags disagree and there's no referee, prefer the
        -- value that matches the original (look-ahead doesn't matter for today's Lookup page)
        SELECT *,
          ROW_NUMBER() OVER (PARTITION BY cik, concept, period_end
                             ORDER BY filed DESC, accn DESC, identity_ok DESC NULLS LAST,
                                      (abs(value - first_value) <= 0.005 * abs(first_value)) DESC, tiebreak) AS r_latest
        FROM ranked0
    )
    SELECT f.cik, f.concept, f.period_end,
           f.value AS value_first,  f.filed AS filed_first,  f.accn AS accn_first,
           l.value AS value_latest, l.filed AS filed_latest, l.accn AS accn_latest,
           f.n_filings,
           abs(l.value - f.value) > {RESTATE_TOLERANCE} * greatest(abs(f.value), 1) AS revised
    FROM ranked f JOIN ranked l
      ON f.cik = l.cik AND f.concept = l.concept AND f.period_end = l.period_end
    WHERE f.r_first = 1 AND l.r_latest = 1
    """)

    # Wide table for the backtest: one column per concept (first-filed values)
    concepts = list(CONCEPTS)
    cols = ",\n".join(f"MAX(value_first) FILTER (WHERE concept = '{c}') AS {c}" for c in concepts)
    con.execute(f"""
    CREATE OR REPLACE TABLE annual_first AS
    SELECT cik, period_end,
           MAX(filed_first) AS available_date,   -- the latest of the first-filed dates = when ALL of it was public
           {cols}
    FROM annual GROUP BY cik, period_end
    """)
    for target, formula in DERIVED.items():   # fill gaps with arithmetic, e.g. gross_profit = revenue - cogs
        con.execute(f"UPDATE annual_first SET {target} = {formula} WHERE {target} IS NULL")

    n_long = con.execute("SELECT COUNT(*) FROM annual").fetchone()[0]
    n_wide = con.execute("SELECT COUNT(*) FROM annual_first").fetchone()[0]
    print(f"annual: {n_long:,} values | annual_first: {n_wide:,} company-years")


if __name__ == "__main__":
    with duckdb.connect(str(DB_PATH)) as con:
        build_annual(con)
