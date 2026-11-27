"""Alerts: feeds stay valid XML with odd company names, and the digest counts the right week."""
import xml.etree.ElementTree as ET

import pandas as pd

from src.web.alerts import atom, week_digest


def _alerts():
    return pd.DataFrame([
        {"cik": 1, "date": pd.Timestamp("2026-11-24"), "kind": "bankruptcy", "name": "AT&T <Test> Co", "ticker": "X",
         "label": "Bankruptcy filing", "severity": "high", "text": "Filed an 8-K under Item 1.03.", "link": None},
        {"cik": 2, "date": pd.Timestamp("2026-11-10"), "kind": "entered_high", "name": "Old Week Inc", "ticker": "",
         "label": "Entered riskiest 5%", "severity": "high", "text": "Old.", "link": None},
    ])


def test_feed_is_valid_xml_with_special_characters():
    xml = atom("Faultline alerts", "https://x/feed.xml", "https://x/alerts.html", _alerts(), "https://x/", "2026-11-25")
    root = ET.fromstring(xml)
    assert len(root.findall("{http://www.w3.org/2005/Atom}entry")) == 2


def test_digest_only_counts_its_week_and_shows_prior_score():
    html, md = week_digest(_alerts(), pd.Timestamp("2026-11-25"), lambda cik, d: 0.9)
    assert "Bankruptcy filings 1" in md and "Entered the riskiest 5% 0" in md
    assert "riskier than 90% of filers" in md and "Old Week" not in md
