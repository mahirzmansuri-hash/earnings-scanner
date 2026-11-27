"""Download companyfacts for every company in data/processed/companies.csv.

Run:  python -m src.pipeline.download_facts
Safe to stop (Ctrl+C) and re-run; finished companies are skipped.
"""
import pandas as pd

from src.pipeline.edgar import download_all_company_facts
from src.pipeline.universe import OUTPUT_CSV

if __name__ == "__main__":
    ciks = pd.read_csv(OUTPUT_CSV, usecols=["cik"])["cik"].tolist()
    download_all_company_facts(ciks)
