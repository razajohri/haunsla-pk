"""ATS company slug lists for Ashby / Greenhouse / Lever.

Merged with config/ats_companies.json. Unlike the Canada seed, this list
targets global remote-friendly employers relevant to Pakistani talent.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "ats_companies.json"

# Built-in remote-friendly / global ATS boards (slugs)
BUILTIN_ASHBY = [
    "openai",
    "anthropic",
    "ramp",
    "notion",
    "linear",
    "vercel",
    "supabase",
    "resend",
    "mercury",
    "rippling",
    "airtable",
    "cursor",
]

BUILTIN_GREENHOUSE = [
    "gitlab",
    "automattic",
    "stripe",
    "figma",
    "twilio",
    "hashicorp",
    "elastic",
    "duolingo",
    "shopify",
    "zapier",
    "reddit",
]

BUILTIN_LEVER = [
    "netflix",
    "spotify",
    "twitch",
    "palantir",
    "fingerfood",
    "away",
    "shopify",
    "canva",
]


def _normalize_slug(board: str, raw: str) -> str:
    value = (raw or "").strip().lower()
    if not value:
        return ""
    if board == "greenhouse":
        return value.replace(" ", "").replace("_", "")
    return value.replace(" ", "-").replace("_", "-")


def _load_config() -> dict[str, list[str]]:
    if not CONFIG_PATH.exists():
        return {"ashby": [], "greenhouse": [], "lever": []}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to read %s", CONFIG_PATH)
        return {"ashby": [], "greenhouse": [], "lever": []}
    return {
        "ashby": list(data.get("ashby") or []),
        "greenhouse": list(data.get("greenhouse") or []),
        "lever": list(data.get("lever") or []),
    }


def get_ats_company_lists() -> dict[str, list[str]]:
    cfg = _load_config()
    merged = {
        "ashby": sorted(
            {
                _normalize_slug("ashby", s)
                for s in [*BUILTIN_ASHBY, *cfg["ashby"]]
                if _normalize_slug("ashby", s)
            }
        ),
        "greenhouse": sorted(
            {
                _normalize_slug("greenhouse", s)
                for s in [*BUILTIN_GREENHOUSE, *cfg["greenhouse"]]
                if _normalize_slug("greenhouse", s)
            }
        ),
        "lever": sorted(
            {
                _normalize_slug("lever", s)
                for s in [*BUILTIN_LEVER, *cfg["lever"]]
                if _normalize_slug("lever", s)
            }
        ),
    }
    return merged


def patch_jobspy_company_lists() -> dict[str, list[str]]:
    """Return merged slug lists.

    Public python-jobspy has no Ashby/Greenhouse/Lever boards, so Haunsla
    scrapes those ATS APIs directly via ats_scraper.py. Kept as a named
    hook so the Canada playbook call sites still make sense.
    """
    lists = get_ats_company_lists()
    logger.info(
        "ATS company lists ready: ashby=%s greenhouse=%s lever=%s",
        len(lists["ashby"]),
        len(lists["greenhouse"]),
        len(lists["lever"]),
    )
    return lists
