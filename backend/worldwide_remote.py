"""Detect worldwide / any-country remote roles.

Used when WORLDWIDE_ONLY=1 (default for the diversified scrape path).
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

WORLDWIDE_TOKENS = (
    "worldwide",
    "work from anywhere",
    "anywhere in the world",
    "any country",
    "all countries",
    "location independent",
    "unrestricted location",
    "no location requirement",
    "candidates from anywhere",
    "hire from anywhere",
    "globally remote",
    "global remote",
    "remote - worldwide",
    "remote worldwide",
    "remote, worldwide",
    "remote/worldwide",
    "remote — worldwide",
    "remote – worldwide",
    "internationally remote",
    "open to all locations",
    "open to candidates worldwide",
)

# Country-locked remote labels in the location field
COUNTRY_LOCKED_LOCATION = re.compile(
    r"\b("
    r"united states|usa|u\.s\.a?|u\.s|"
    r"united kingdom|uk|england|"
    r"canada|australia|germany|france|india|brazil|mexico|"
    r"netherlands|ireland|spain|italy|sweden|norway|denmark|"
    r"switzerland|poland|estonia|colombia|argentina|japan|"
    r"uae|singapore|north america|emea|apac|latam|americas|\bamer\b"
    r")\b",
    flags=re.I,
)

REMOTE_US_STYLE = re.compile(
    r"\bremote(\s+in)?[\s\-_,/()]+(the\s+)?(us|usa|u\.s\.?|united states|uk|canada|eu)\b"
    r"|\b(us|usa|u\.s\.?|united states|uk|canada|eu)[\s\-_,/()]+remote\b",
    flags=re.I,
)


def _text(row: dict[str, Any] | pd.Series) -> str:
    parts = [
        str(row.get("title") or ""),
        str(row.get("company") or ""),
        str(row.get("location") or ""),
        str(row.get("description") or "")[:4000],
        str(row.get("work_from_home_type") or ""),
    ]
    return " ".join(parts).lower()


def has_worldwide_signal(row: dict[str, Any] | pd.Series) -> bool:
    text = _text(row)
    if any(token in text for token in WORLDWIDE_TOKENS):
        return True
    loc = str(row.get("location") or "").strip().lower()
    # Bare Remote / Worldwide with no country lock
    if loc in {"remote", "worldwide", "anywhere", "global", "work from anywhere"}:
        return True
    if loc.startswith("remote") and not COUNTRY_LOCKED_LOCATION.search(loc) and not REMOTE_US_STYLE.search(loc):
        return True
    return False


def is_country_locked_remote(row: dict[str, Any] | pd.Series) -> bool:
    loc = str(row.get("location") or "")
    title = str(row.get("title") or "")
    blob = f"{title} {loc}"
    if REMOTE_US_STYLE.search(blob):
        return True
    if COUNTRY_LOCKED_LOCATION.search(loc) and not has_worldwide_signal(row):
        return True
    return False


def is_worldwide_remote_row(row: dict[str, Any] | pd.Series) -> bool:
    """Keep true worldwide / any-country remote jobs."""
    if not bool(row.get("is_remote")) and "remote" not in _text(row):
        return False
    if is_country_locked_remote(row):
        return False
    return has_worldwide_signal(row)


def filter_worldwide(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    mask = df.apply(is_worldwide_remote_row, axis=1)
    return df.loc[mask].reset_index(drop=True)
