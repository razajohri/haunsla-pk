"""Pakistan / worldwide-remote geo rules for scraped job rows.

Looser than remotejobscanada.ca: keep PK-explicit roles plus open
international remote; reject US-only / EU-only / single-country-abroad posts.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

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

STRONG_OPEN_DESC_TOKENS = (
    "work from anywhere",
    "remote worldwide",
    "remotely from anywhere",
    "candidates worldwide",
    "candidates from anywhere",
    "all countries",
    "any country",
    "location independent",
    "no location requirement",
    "unrestricted location",
    "global remote",
    "international remote",
    "remote - worldwide",
    "remote, worldwide",
    "remote/worldwide",
)

PK_LOCATION_TOKENS = (
    "pakistan",
    "lahore",
    "karachi",
    "islamabad",
    "rawalpindi",
    "peshawar",
    "multan",
    "faisalabad",
)

OPEN_LOCATION_TOKENS = (
    "worldwide",
    "anywhere",
    "global",
    "international",
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

_SINGLE_COUNTRY_ABROAD = re.compile(
    r"\b("
    r"united states|usa|u\.s\.a\.?|u\.s\.?|north america|south america|americas|\bamer\b|europe|emea|apac|latam|mena|meta|"
    r"canada|united kingdom|uk|england|scotland|"
    r"germany|france|australia|japan|brazil|mexico|singapore|netherlands|"
    r"ireland|spain|italy|sweden|norway|denmark|switzerland|india|"
    r"uae|united arab emirates|ksa|saudi arabia|turkey|south africa|"
    r"bangalore|bengaluru|gurugram|gurgaon|toronto|chicago|sydney|london|"
    r"berlin|paris|amsterdam|dublin|illinois|california|texas|seattle|"
    r"new york|nyc|san francisco|\bsf\b|\bsea\b|\bchi\b"
    r")\b",
    flags=re.IGNORECASE,
)

# Remote-US / US-Remote / Remote in the US / Remote - Illinois etc.
_REMOTE_US_STYLE = re.compile(
    r"\bremote(\s+in)?[\s\-_,/]+(the\s+)?(us|usa|u\.s\.?|united states|north america)\b"
    r"|\b(us|usa|u\.s\.?|united states|north america)[\s\-_,/]+remote\b"
    r"|\bremote[\s\-_,/]+(illinois|california|texas|new york|nyc|seattle|chicago)\b",
    flags=re.IGNORECASE,
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


def _location_text(row: dict[str, Any] | pd.Series) -> str:
    return f" {str(row.get('location') or '').lower()} "


def has_remote_signal(row: dict[str, Any] | pd.Series) -> bool:
    loc = _location_text(row)
    title = str(row.get("title") or "").lower()
    # Prefer explicit remote signals over a noisy is_remote flag from ATS
    if any(token in loc for token in ("remote", "distributed", "worldwide", "anywhere", "wfh")):
        return True
    if any(token in title for token in ("remote", "work from home")):
        return True
    if bool(row.get("is_remote")):
        return True
    text = _blob(row)
    return any(token in text for token in REMOTE_TOKENS)


def is_geo_blocked(text: str) -> bool:
    for pattern in (*US_ONLY_PATTERNS, *EU_ONLY_PATTERNS, *BLOCKED_REGION_PATTERNS):
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def location_is_pakistan(loc: str) -> bool:
    return any(token in loc for token in PK_LOCATION_TOKENS)


_REMOTE_WITH_SUFFIX = re.compile(
    r"^\s*remote(?:\s+in)?\s*(?:[-–,:/]|\()\s*(.+?)\)?\s*$",
    flags=re.IGNORECASE,
)


def location_is_open_remote(loc: str) -> bool:
    if not loc.strip():
        return False
    if _REMOTE_US_STYLE.search(loc):
        return False

    # "Remote - Colombia" / "Remote, UAE" / "Remote in the US" → only keep if
    # the suffix is an open/PK token (not a specific foreign country/city).
    suffixed = _REMOTE_WITH_SUFFIX.match(loc.strip())
    if suffixed:
        suffix = f" {suffixed.group(1).lower()} "
        if any(token in suffix for token in (*OPEN_LOCATION_TOKENS, *PK_LOCATION_TOKENS)):
            return True
        if suffix.strip() in {"remote", "fully remote", "work from home"}:
            return True
        return False

    if _SINGLE_COUNTRY_ABROAD.search(loc) and not any(
        token in loc for token in (*OPEN_LOCATION_TOKENS, *PK_LOCATION_TOKENS)
    ):
        return False
    if any(token in loc for token in OPEN_LOCATION_TOKENS):
        return True
    # Bare "Remote" with no foreign geo token.
    if re.fullmatch(r"\s*remote\s*", loc):
        return True
    if "remote" in loc:
        return not _SINGLE_COUNTRY_ABROAD.search(loc)
    return False


def description_is_strongly_open(text: str) -> bool:
    return any(token in text for token in STRONG_OPEN_DESC_TOKENS)


def is_pakistan_job_row(row: dict[str, Any] | pd.Series) -> bool:
    """Keep PK + open international remote roles."""
    if not has_remote_signal(row):
        return False

    text = _blob(row)
    title = str(row.get("title") or "").lower()
    if is_geo_blocked(text):
        return False

    loc = _location_text(row)
    title_and_loc = f"{title} {loc}"
    if _REMOTE_US_STYLE.search(title_and_loc) or _REMOTE_US_STYLE.search(text[:1000]):
        return False

    # Title cues for geo-locked / US-gov sales roles
    if re.search(
        r"\b("
        r"washington\s*dc|based in|us based|u\.s\. based|"
        r"federal\b|sled|civilian government|us public sector|\bamer\b"
        r")\b",
        title,
        flags=re.IGNORECASE,
    ):
        return False
    if _SINGLE_COUNTRY_ABROAD.search(title) and not location_is_pakistan(loc):
        if not any(token in loc for token in OPEN_LOCATION_TOKENS):
            return False

    if location_is_pakistan(loc):
        return True
    if location_is_open_remote(loc):
        return True

    # Vague locations ("Distributed", "Hybrid") need a strong open-remote phrase
    return description_is_strongly_open(text) and not _SINGLE_COUNTRY_ABROAD.search(
        title_and_loc
    )


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    mask = df.apply(is_pakistan_job_row, axis=1)
    return df.loc[mask].reset_index(drop=True)
