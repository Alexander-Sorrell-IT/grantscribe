"""Free-resources pillar: a learning goal -> the subject -> real free resources
(Internet Archive books + deterministic links to free-course providers).

Unlike grants/scholarships, there is NO application to draft here — this pillar
surfaces what's free to learn from right now. No silent fallbacks.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from resources_api import curated_providers, search_archive

load_dotenv(Path(__file__).with_name(".env"))

_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
_MODEL_FAST = os.environ.get("DEEPSEEK_MODEL_FAST", "deepseek-v4-flash")
_NO_THINK = {"thinking": {"type": "disabled"}}


def _client() -> OpenAI:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY missing — set it in grantscribe/.env")
    return OpenAI(api_key=key, base_url=_BASE_URL)


def extract_topic(description: str) -> str:
    """Flash (non-thinking) distills a learning goal into a 1-3 word subject."""
    resp = _client().chat.completions.create(
        model=_MODEL_FAST,
        temperature=0,
        max_tokens=20,
        extra_body=_NO_THINK,
        messages=[
            {"role": "system", "content": (
                "Extract the single subject or skill the person wants to learn, as 1-3 words. "
                "No filler, no punctuation. e.g. 'I want to study cell biology for free' -> 'cell biology'."
            )},
            {"role": "user", "content": description},
        ],
    )
    topic = (resp.choices[0].message.content or "").strip()
    if not topic:
        raise RuntimeError("extract_topic returned empty output")
    return topic


def rank_resources(goal: str, books: list[dict], top: int = 4) -> list[dict]:
    """Flash (non-thinking, JSON) keeps only genuinely useful, level-appropriate books."""
    if not books:
        return []
    catalog = [{"i": i, "title": b["title"], "year": b.get("year", "")} for i, b in enumerate(books)]
    resp = _client().chat.completions.create(
        model=_MODEL_FAST,
        temperature=0,
        max_tokens=900,
        extra_body=_NO_THINK,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": (
                "From candidate free books, keep only those GENUINELY useful and level-appropriate "
                "for the learner's stated goal. Return JSON: "
                '{"results":[{"i":int,"keep":bool,"note":"one short sentence: what it is / who it suits"}]}. '
                "Be strict: drop off-topic, wrong-level, or novelty items."
            )},
            {"role": "user", "content": json.dumps({"goal": goal, "books": catalog})},
        ],
    )
    parsed = json.loads(resp.choices[0].message.content or "")
    verdicts = {r["i"]: r for r in parsed.get("results", [])}
    kept = [
        {**books[i], "note": verdicts[i].get("note", "")}
        for i in range(len(books))
        if verdicts.get(i, {}).get("keep")
    ]
    return kept[:top]


def find_resources(description: str, rows: int = 12, top: int = 4) -> dict:
    """Learning goal -> subject -> level-fit free books (re-ranked) + course providers."""
    topic = extract_topic(description)
    raw_books = search_archive(topic, rows=rows)
    return {
        "topic": topic,
        "books": rank_resources(description, raw_books, top=top),
        "courses": curated_providers(topic),
    }
