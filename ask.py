"""/ask tutor — answers a learning question GROUNDED in free open content
(Wikibooks / Wikiversity), with citations.

Lightweight RAG, no vector DB: search the open source -> fetch the page text ->
answer ONLY from that text. No hallucinated tutoring; always cites the source.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from mediawiki_api import SOURCES, fetch_extract, search

load_dotenv(Path(__file__).with_name(".env"))

_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
_MODEL = os.environ.get("DEEPSEEK_MODEL_FAST", "deepseek-v4-flash")
_NO_THINK = {"thinking": {"type": "disabled"}}


def _client() -> OpenAI:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY missing — set it in grantscribe/.env")
    return OpenAI(api_key=key, base_url=_BASE_URL)


def answer_question(question: str) -> dict:
    """Answer a learning question from free open textbooks, with citations."""
    hits: list[dict] = []
    errors: list[str] = []
    for site in SOURCES:
        try:
            hits += search(site, question, limit=2)
        except Exception as exc:  # one source failing shouldn't kill the answer
            errors.append(f"{site}: {exc}")
    if not hits:
        if errors:
            raise RuntimeError("all open sources failed: " + "; ".join(errors))
        return {"question": question, "answer": None, "sources": [],
                "note": "No open-textbook page found for this question."}

    passages: list[str] = []
    sources: list[dict] = []
    for h in hits[:2]:
        text = fetch_extract(h["site"], h["title"])
        if text:
            passages.append(f"[{h['site']} — {h['title']}]\n{text}")
            sources.append({"title": h["title"], "site": h["site"], "url": h["url"]})
    if not passages:
        return {"question": question, "answer": None, "sources": [],
                "note": "Found pages but no readable text to answer from."}

    resp = _client().chat.completions.create(
        model=_MODEL,
        temperature=0,
        max_tokens=600,
        extra_body=_NO_THINK,
        messages=[
            {"role": "system", "content": (
                "You are a tutor. Answer the student's question USING ONLY the provided reference "
                "text from free open textbooks. Be clear and pedagogical. If the text does not cover "
                "it, say so plainly. Do NOT invent facts beyond the provided text."
            )},
            {"role": "user", "content": f"QUESTION:\n{question}\n\nREFERENCE TEXT:\n" + "\n\n".join(passages)},
        ],
    )
    answer = (resp.choices[0].message.content or "").strip()
    if not answer:
        raise RuntimeError("answer_question returned empty output")
    return {"question": question, "answer": answer, "sources": sources}
