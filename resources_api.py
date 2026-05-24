"""Internet Archive search — free books/texts (zero-auth) — plus deterministic
links to known free-course providers. Real data source for the "free resources"
pillar. No hallucinated links: provider URLs are constructed, never guessed.

No silent fallbacks: API/network failures raise.
"""
from __future__ import annotations

from urllib.parse import quote_plus

import httpx

IA_SEARCH_URL = "https://archive.org/advancedsearch.php"
IA_DETAIL_URL = "https://archive.org/details/{id}"
REQUEST_TIMEOUT = 25.0


def search_archive(topic: str, rows: int = 6) -> list[dict]:
    """Search the Internet Archive for free texts on a topic. Raises on failure."""
    if not topic or not topic.strip():
        raise ValueError("topic must be a non-empty search string")

    rows = max(1, min(rows, 25))
    params = {
        "q": f"({topic.strip()}) AND mediatype:(texts)",
        "fl[]": ["identifier", "title", "creator", "year"],
        "rows": rows,
        "sort[]": "downloads desc",
        "output": "json",
    }
    resp = httpx.get(IA_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    docs = resp.json()["response"]["docs"]
    return [
        {
            "title": d.get("title", "(untitled)"),
            "creator": d.get("creator", ""),
            "year": d.get("year", ""),
            "url": IA_DETAIL_URL.format(id=d["identifier"]),
            "kind": "free book / text (Internet Archive)",
        }
        for d in docs
    ]


def curated_providers(topic: str) -> list[dict]:
    """Known free-course/textbook providers with DETERMINISTIC search links."""
    q = quote_plus(topic.strip())
    return [
        {"title": f"OpenStax — free peer-reviewed textbooks", "kind": "free textbooks",
         "url": "https://openstax.org/subjects"},
        {"title": f"MIT OpenCourseWare — free courses on {topic}", "kind": "free course",
         "url": f"https://ocw.mit.edu/search/?q={q}"},
        {"title": f"Khan Academy — free lessons on {topic}", "kind": "free course",
         "url": f"https://www.khanacademy.org/search?page_search_query={q}"},
        {"title": f"freeCodeCamp — free coding curriculum ({topic})", "kind": "free course",
         "url": f"https://www.freecodecamp.org/news/search/?query={q}"},
    ]
