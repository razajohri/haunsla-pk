"""Pakistan / worldwide-remote geo rules for scraped job rows.

Policy (Haunsla):
- If a board marks a role remote (`is_remote=True` or clear remote location), keep it.
- Keep Pakistan city / local employer roles (Lahore, Karachi, Islamabad, etc.)
  when ALLOW_PAKISTAN_LOCAL=1 (default) — needed for banks & graduate programs.
- Only drop clear hard blocks (US-only / EU-only / must-reside-in-X) for non-PK rows.
"""

from __future__ import annotations

import os
import re
from typing import Any

import pandas as pd

ALLOW_PAKISTAN_LOCAL = os.getenv("ALLOW_PAKISTAN_LOCAL", "1") == "1"

PAKISTAN_LOCAL_TOKENS = (
    "pakistan",
    "lahore",
    "karachi",
    "islamabad",
    "rawalpindi",
    "peshawar",
    "faisalabad",
    "multan",
    "gujranwala",
    "hyderabad",
    "sialkot",
    "quetta",
    ", pk",
    " pk ",
)

REMOTE_TOKENS = (
    "remote",
    "work from home",
    "wfh",
    "distributed",
    "anywhere",
    "worldwide",
    "work from anywhere",
    "fully remote",
    "100% remote",
)

US_ONLY_PATTERNS = (
    r"\bus only\b",
    r"\busa only\b",
    r"\bunited states only\b",
    r"\bmust be (located |based )?in the (us|usa|united states)\b",
    r"\bmust reside in the (us|usa|united states)\b",
    r"\b(us|usa|united states) residents? only\b",
    r"\brequires? (us|usa) work authorization\b",
    r"\bmust have (us|usa) work authorization\b",
    r"\bno (sponsorship|visa).{0,40}(us|usa|united states)\b",
    r"\b(us|usa)-based candidates? only\b",
)

EU_ONLY_PATTERNS = (
    r"\beu only\b",
    r"\beurope only\b",
    r"\beea only\b",
    r"\bmust be (located |based )?in (the )?eu\b",
    r"\beu residents? only\b",
    r"\buk only\b",
    r"\bunited kingdom only\b",
    r"\bmust be (located |based )?in the (uk|united kingdom)\b",
)

BLOCKED_REGION_PATTERNS = (
    r"\bcanada only\b",
    r"\baustralia only\b",
    r"\bindia only\b",
)


def _blob(row: dict[str, Any] | pd.Series) -> str:
    parts = [
        str(row.get("title") or ""),
        str(row.get("company") or ""),
        str(row.get("location") or ""),
        str(row.get("description") or ""),
        str(row.get("work_from_home_type") or ""),
    ]
    return " ".join(parts).lower()


def has_remote_signal(row: dict[str, Any] | pd.Series) -> bool:
    # Trust the board flag first (user request: board says remote → remote)
    val = row.get("is_remote")
    if val is True or (isinstance(val, (int, float)) and val == 1):
        return True
    if isinstance(val, str) and val.strip().lower() in {"true", "1", "yes"}:
        return True
    text = _blob(row)
    return any(token in text for token in REMOTE_TOKENS)


def is_geo_blocked(text: str) -> bool:
    for pattern in (*US_ONLY_PATTERNS, *EU_ONLY_PATTERNS, *BLOCKED_REGION_PATTERNS):
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def is_pakistan_local_row(row: dict[str, Any] | pd.Series) -> bool:
    text = _blob(row)
    return any(token in text for token in PAKISTAN_LOCAL_TOKENS)


def is_pakistan_job_row(row: dict[str, Any] | pd.Series) -> bool:
    """Keep remote (non-geo-blocked) or Pakistan-local employer roles."""
    text = _blob(row)
    local = ALLOW_PAKISTAN_LOCAL and is_pakistan_local_row(row)
    if local:
        return True
    if not has_remote_signal(row):
        return False
    if is_geo_blocked(text):
        return False
    return True


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    mask = df.apply(is_pakistan_job_row, axis=1)
    return df.loc[mask].reset_index(drop=True)
