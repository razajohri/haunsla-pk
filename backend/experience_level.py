"""Infer internship / entry / mid / senior from title + description.

Haunsla prioritizes fresh-grad friendly roles: internships and little/no
experience postings should be tagged so the mobile filters can surface them.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

INTERNSHIP_PATTERNS = (
    r"\bintern(ship|ships)?\b",
    r"\btrainee\b",
    r"\bapprentice(ship)?\b",
    r"\bstudent\s+(job|role|program)\b",
    r"\buniversity\s+grad(uate)?\s+program\b",
    r"\bco[\s-]?op\b",
)

ENTRY_PATTERNS = (
    r"\bentry[\s-]?level\b",
    r"\bjunior\b",
    r"\bjr\.?\b",
    r"\bassociate\b",
    r"\bgraduate\b",
    r"\bfresh\s+grad(uate)?\b",
    r"\bnew\s+grad(uate)?\b",
    r"\bearly\s+career\b",
    r"\b0[\s-]?2\s+years?\b",
    r"\b0[\s-]?1\s+years?\b",
    r"\b1\+?\s+years?\b",
    r"\bno\s+experience\b",
    r"\blittle\s+experience\b",
    r"\bexperience\s+not\s+required\b",
    r"\bwill\s+train\b",
    r"\btraining\s+provided\b",
)

SENIOR_PATTERNS = (
    r"\bsenior\b",
    r"\bsr\.?\b",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\blead\b",
    r"\bhead\s+of\b",
    r"\bdirector\b",
    r"\bvp\b",
    r"\bvice\s+president\b",
    r"\bchief\b",
    r"\biii\b",
    r"\biv\b",
    r"\blevel\s*[3-9]\b",
    r"\b5\+?\s+years?\b",
    r"\b6\+?\s+years?\b",
    r"\b7\+?\s+years?\b",
    r"\b8\+?\s+years?\b",
    r"\b10\+?\s+years?\b",
)

MID_PATTERNS = (
    r"\bmid[\s-]?level\b",
    r"\bintermediate\b",
    r"\b3\+?\s+years?\b",
    r"\b4\+?\s+years?\b",
    r"\b2[\s-]?4\s+years?\b",
    r"\b3[\s-]?5\s+years?\b",
)


def _blob(row: dict[str, Any] | pd.Series) -> str:
    return " ".join(
        [
            str(row.get("title") or ""),
            str(row.get("description") or "")[:3000],
            str(row.get("tags") or ""),
            str(row.get("job_type") or ""),
        ]
    ).lower()


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(p, text, flags=re.I) for p in patterns)


def infer_experience_level(
    row: dict[str, Any] | pd.Series, *, trust_existing: bool = True
) -> str | None:
    """Return internship | entry | mid | senior | None."""
    if trust_existing:
        existing = row.get("experience_level")
        if isinstance(existing, str) and existing.strip().lower() in {
            "internship",
            "entry",
            "mid",
            "senior",
        }:
            return existing.strip().lower()

    text = _blob(row)
    title = str(row.get("title") or "").lower()
    job_type = str(row.get("job_type") or "").lower()
    title_signal = f"{title} {job_type}"

    # Internships: title/job_type only — descriptions often say "mentor interns"
    # and synthetic tags ("Internship") must not create a feedback loop.
    # "Senior … Apprenticeship Trainer" is senior, not an intern role.
    if _matches(INTERNSHIP_PATTERNS, title_signal) and not _matches(
        SENIOR_PATTERNS, title
    ):
        return "internship"
    if _matches(SENIOR_PATTERNS, title):
        return "senior"
    if _matches(ENTRY_PATTERNS, title):
        return "entry"
    if _matches(MID_PATTERNS, title):
        return "mid"

    # Body: prefer strong fresh-grad phrases; skip year-count noise alone
    strong_entry = (
        r"\bentry[\s-]?level\b",
        r"\bjunior\b",
        r"\bfresh\s+grad(uate)?\b",
        r"\bnew\s+grad(uate)?\b",
        r"\bearly\s+career\b",
        r"\bno\s+experience\b",
        r"\blittle\s+experience\b",
        r"\bexperience\s+not\s+required\b",
        r"\bwill\s+train\b",
        r"\btraining\s+provided\b",
        r"\b0[\s-]?2\s+years?\b",
        r"\b0[\s-]?1\s+years?\b",
    )
    if _matches(strong_entry, text) and not _matches(SENIOR_PATTERNS, title):
        return "entry"
    if _matches(SENIOR_PATTERNS, text) and not _matches(ENTRY_PATTERNS, title_signal):
        return "senior"
    if _matches(MID_PATTERNS, text) and not _matches(ENTRY_PATTERNS, title_signal):
        return "mid"
    return None


def is_fresh_grad_friendly(row: dict[str, Any] | pd.Series) -> bool:
    level = infer_experience_level(row, trust_existing=False)
    return level in {"internship", "entry"}


def annotate_experience_levels(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    out = df.copy()
    # Recompute from title/description so stale/wrong tags get corrected
    out["experience_level"] = out.apply(
        lambda r: infer_experience_level(r, trust_existing=False), axis=1
    )
    # Help feed chips / tags
    def _tags(row: pd.Series) -> list:
        tags = row.get("tags")
        if isinstance(tags, list):
            base = [t for t in tags if t not in {"Internship", "Entry Level"}]
        else:
            base = ["Remote"]
        level = row.get("experience_level")
        if level == "internship":
            base.append("Internship")
        if level == "entry":
            base.append("Entry Level")
        return base

    out["tags"] = out.apply(_tags, axis=1)
    return out
