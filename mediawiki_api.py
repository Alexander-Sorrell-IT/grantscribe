"""MediaWiki sources — free, zero-auth search + plain-text fetch for open
educational sites: Wikibooks (open textbooks) and Wikiversity (open courses).
Powers the /ask tutor and enriches /learn. No silent fallbacks.
"""
from __future__ import annotations

import httpx

REQUEST_TIMEOUT = 25.0
# Wikimedia requires a descriptive User-Agent (default lib UAs get 403).
HEADERS = {"User-Agent": "GrantScribe/1.0 (https://github.com/Alexander-Sorrell-IT/grantscribe.; education-access hackathon agent)"}

# label -> (api endpoint, page base url, what it is)
SOURCES: dict[str, tuple[str, str, str]] = {
    "Wikibooks": ("https://en.wikibooks.org/w/api.php", "https://en.wikibooks.org/wiki/", "open textbook"),
    "Wikiversity": ("https://en.wikiversity.org/w/api.php", "https://en.wikiversity.org/wiki/", "open course"),
}


def search(site: str, query: str, limit: int = 3) -> list[dict]:
    """Search an open-education wiki. Raises on failure."""
    api, base, kind = SOURCES[site]
    r = httpx.get(
        api,
        params={"action": "query", "list": "search", "srsearch": query, "srlimit": limit, "format": "json"},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return [
        {"title": h["title"], "site": site, "kind": kind, "url": base + h["title"].replace(" ", "_")}
        for h in r.json()["query"]["search"]
    ]


def fetch_extract(site: str, title: str, chars: int = 3500) -> str:
    """Fetch plain-text content of a wiki page (for grounding answers)."""
    api, _, _ = SOURCES[site]
    r = httpx.get(
        api,
        params={"action": "query", "prop": "extracts", "explaintext": 1, "exchars": chars,
                "redirects": 1, "format": "json", "titles": title},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    pages = r.json()["query"]["pages"]
    return next(iter(pages.values())).get("extract", "")
