"""Project settings. The only place that reads secrets from .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "db" / "scanner.duckdb"

# SEC rule: max 10 requests/second. We stay a bit under.
SEC_MAX_REQUESTS_PER_SEC = 8


def sec_user_agent() -> str:
    """Return the SEC User-Agent from .env, or stop with a clear message."""
    ua = os.getenv("SEC_USER_AGENT", "").strip()
    if not ua or "example.com" in ua:
        raise RuntimeError(
            "SEC_USER_AGENT is not set. Open .env and put your real name and "
            'email, e.g. SEC_USER_AGENT="Jane Doe jane@gmail.com"'
        )
    return ua
