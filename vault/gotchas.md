# Gotchas

Traps that cost time once. Format: **symptom** → cause → fix.

## Setup
- **`CERTIFICATE_VERIFY_FAILED` on any HTTPS request** → the python.org installer doesn't set up SSL certificates → run `/Applications/Python 3.12/Install Certificates.command` (done 2026-11-25).
- **`HTTP Error 403` from sec.gov** → no User-Agent header. SEC blocks anonymous requests → send `SEC_USER_AGENT` from `.env`.
- **`python3` is 3.9** → that's Apple's built-in version → always use `.venv/bin/python` or activate the venv.

## Data (known in advance; confirm in Phase 1)
- **Look-ahead bias** → using the fiscal period end and not the `filed` date → always filter by `filed`.
- **Restated numbers** → companyfacts can hold several values for the same period (original plus amendments) → keep the first one filed for point-in-time work.
- **Survivorship bias** → building the stock universe from today's tickers → build it from every company that filed in each year.
