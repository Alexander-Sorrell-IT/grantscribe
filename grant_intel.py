"""GrantScribe — grant intelligence layer (DeepSeek).

Turns a nonprofit's messy, plain-language description into a tight grants.gov
query, drops expired opportunities, then re-ranks the raw matches for TRUE
relevance with a one-line reason each. This is what makes the agent smarter
than the grants.gov website.

No silent fallbacks: missing key, API errors, and unparseable model output raise.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from grants_api import _fetch_grants

load_dotenv(Path(__file__).with_name(".env"))

_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
_MODEL_FAST = os.environ.get("DEEPSEEK_MODEL_FAST", "deepseek-v4-flash")
_NO_THINK = {"thinking": {"type": "disabled"}}


def _client() -> OpenAI:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY missing — set it in grantscribe/.env")
    return OpenAI(api_key=key, base_url=_BASE_URL)


def _not_expired(grant: dict) -> bool:
    """Drop opportunities whose close date is in the past; keep rolling/unknown."""
    close = grant.get("close_date", "")
    if not close:
        return True
    try:
        return datetime.strptime(close, "%m/%d/%Y").date() >= date.today()
    except ValueError:
        return True


def extract_query(description: str) -> str:
    """Flash (non-thinking) distills a description into a tight grants.gov query."""
    resp = _client().chat.completions.create(
        model=_MODEL_FAST,
        temperature=0,
        max_tokens=40,
        extra_body=_NO_THINK,
        messages=[
            {
                "role": "system",
                "content": (
                    "Convert a nonprofit's description into a SHORT keyword query for the "
                    "grants.gov federal grant search. Output ONLY 2-4 high-signal terms "
                    "(mission/population/activity) separated by spaces. No location unless "
                    "central, no filler words, no punctuation."
                ),
            },
            {"role": "user", "content": description},
        ],
    )
    query = (resp.choices[0].message.content or "").strip()
    if not query:
        raise RuntimeError("extract_query returned empty output")
    return query


def rank_grants(description: str, grants: list[dict], top: int = 3) -> list[dict]:
    """Flash (non-thinking, JSON) keeps only genuinely relevant grants, with reasons."""
    if not grants:
        return []
    catalog = [
        {"opportunity_number": g["opportunity_number"], "title": g["title"], "agency": g["agency"]}
        for g in grants
    ]
    resp = _client().chat.completions.create(
        model=_MODEL_FAST,
        temperature=0,
        max_tokens=1500,
        extra_body=_NO_THINK,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Match a nonprofit to U.S. federal grants. Given the org description and "
                    "candidate opportunities, decide which could PLAUSIBLY fund this org's work. "
                    'Return JSON: {"results":[{"opportunity_number":str,"relevant":bool,'
                    '"score":0-100,"reason":"one sentence"}]}. Be strict: relevant=true only if '
                    "the grant could realistically fund the described work."
                ),
            },
            {"role": "user", "content": json.dumps({"description": description, "opportunities": catalog})},
        ],
    )
    parsed = json.loads(resp.choices[0].message.content or "")  # raises on bad JSON
    verdicts = {r["opportunity_number"]: r for r in parsed.get("results", [])}

    ranked = [
        {**g, "score": int(verdicts[g["opportunity_number"]].get("score", 0)),
         "reason": verdicts[g["opportunity_number"]].get("reason", "")}
        for g in grants
        if verdicts.get(g["opportunity_number"], {}).get("relevant")
    ]
    ranked.sort(key=lambda g: g["score"], reverse=True)
    return ranked[:top]


def find_grants(description: str, rows: int = 15, top: int = 3) -> dict:
    """Full flow: description -> tight query -> fetch -> drop expired -> re-rank."""
    query = extract_query(description)
    raw = _fetch_grants(query, rows=rows)
    open_grants = [g for g in raw["grants"] if _not_expired(g)]
    ranked = rank_grants(description, open_grants, top=top)
    return {"query": query, "raw_count": raw["count"], "considered": len(open_grants), "grants": ranked}
