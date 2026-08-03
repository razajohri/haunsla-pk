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
    r"uae|united arab emirates|saudi arabia|ksa|singapore|"
    r"north america|emea|apac|latam|americas|\bamer\b|mena|meta|"
    r"washington|bangalore|bengaluru|india"
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
    # Title region locks even when location only says "Remote"
    if re.search(
        r"\b(amer|emea|apac|latam|mena|saarc|us only|uk only|"
        r"based in|washington\s*dc)\b",
        title,
        flags=re.I,
    ):
        return True
    # Location names a country/region → locked unless description has a STRONG
    # any-country phrase (bare "worldwide" in marketing copy is too weak).
    if COUNTRY_LOCKED_LOCATION.search(loc):
        desc = str(row.get("description") or "").lower()
        strong = (
            "work from anywhere",
            "candidates from anywhere",
            "hire from anywhere",
            "any country",
            "all countries",
            "remote worldwide",
            "remotely from anywhere",
            "location independent",
            "no location requirement",
        )
        if not any(token in desc for token in strong):
            return True
    return False


# Boards that primarily list worldwide / any-country remote roles.
WORLDWIDE_NATIVE_SITES = {
    "remoteok",
    "jobicy",
    "himalayas",
    "remotive",
    "weworkremotely",
    "arbeitnow",
}


def is_worldwide_remote_row(row: dict[str, Any] | pd.Series) -> bool:
    """Keep worldwide / any-country remote jobs (plus Pakistan-open roles)."""
    if not bool(row.get("is_remote")) and "remote" not in _text(row):
        return False
    loc = str(row.get("location") or "").lower()
    # Haunsla also keeps explicit Pakistan remote roles
    if "pakistan" in loc:
        return True
    if is_country_locked_remote(row):
        return False
    site = str(row.get("site") or "").lower()
    if site in WORLDWIDE_NATIVE_SITES or site == "repstack":
        return True
    return has_worldwide_signal(row)


def filter_worldwide(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    mask = df.apply(is_worldwide_remote_row, axis=1)
    return df.loc[mask].reset_index(drop=True)
