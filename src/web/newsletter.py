"""Email the weekly digest through Buttondown (free for the first 100 subscribers).

Run:  python -m src.web.newsletter [digest.md]   (default file: data/processed/digest_latest.md, written by src.web.build)

Settings (environment variables; in GitHub they are repository secrets/variables, locally in .env):
  BUTTONDOWN_API_KEY   the key from buttondown.com/requests. Missing -> this step does nothing.
  FL_DIGEST_MODE       "draft" (default): the email waits in Buttondown for a human to press send.
                       "send": it goes out right away. Switch only after a few drafts look right.

Safe to re-run: if an email with this week's subject already exists in Buttondown, nothing new is created.
The API key is never printed.
"""
import os
import sys
from pathlib import Path

import requests

from src.config import ROOT
from src.web.style import SITE_URL

API = "https://api.buttondown.com/v1/emails"
DIGEST = ROOT / "data" / "processed" / "digest_latest.md"
FOOTER = (f"\n---\n\nEvery company above has a full page on [Faultline]({SITE_URL}): scores, trends and why the risk is what it is. "
          f"All alerts: [{SITE_URL}alerts.html]({SITE_URL}alerts.html). Past weeks: [digest archive]({SITE_URL}digest/index.html).\n\n"
          "Faultline is research built from free SEC filings, not investment advice.\n")


def email_from_digest(md: str) -> tuple[str, str]:
    """(subject, body): the first line '# Faultline weekly: A to B' becomes the subject."""
    first, _, rest = md.partition("\n")
    subject = first.lstrip("# ").strip()
    return subject, rest.strip() + "\n" + FOOTER


def main(path=None) -> int:
    digest = Path(path) if path else DIGEST
    key = os.getenv("BUTTONDOWN_API_KEY", "").strip()
    if not key:
        print("newsletter: BUTTONDOWN_API_KEY not set, skipped")
        return 1 if os.getenv("FL_REQUIRE_KEY") else 0     # the test workflow must fail loudly without a key
    if not digest.exists():
        print("newsletter: no digest file, run src.web.build first")
        return 1
    mode = os.getenv("FL_DIGEST_MODE", "draft").strip().lower()
    status = "about_to_send" if mode == "send" else "draft"
    subject, body = email_from_digest(digest.read_text())
    head = {"Authorization": f"Token {key}"}
    try:
        r = requests.get(API, headers=head, params={"ordering": "-creation_date"}, timeout=30)
        r.raise_for_status()
        if any(e.get("subject") == subject for e in r.json().get("results", [])):
            print(f"newsletter: '{subject}' already in Buttondown, skipped")
            return 0
        # status is always set explicitly, so a change in Buttondown's default can never send by surprise
        r = requests.post(API, headers=head, json={"subject": subject, "body": body, "status": status}, timeout=30)
        r.raise_for_status()
    except requests.RequestException as err:
        code = getattr(getattr(err, "response", None), "status_code", "no response")
        print(f"newsletter: Buttondown request failed ({code}); the site is unaffected")
        return 1
    print(f"newsletter: '{subject}' created in Buttondown as {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
