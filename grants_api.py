"""grants.gov Search2 API client — shared core for the MCP server and the
intelligence layer (kept separate to avoid a circular import).

No silent fallbacks: every API/network failure raises.
"""
from __future__ import annotations

import httpx

GRANTS_API_URL = "https://api.grants.gov/v1/api/search2"
GRANT_DETAIL_URL = "https://www.grants.gov/search-results-detail/{id}"
REQUEST_TIMEOUT = 25.0
MAX_ROWS = 25


def _fetch_grants(keyword: str, rows: int = 5) -> dict:
    """Query grants.gov Search2 for open opportunities. Raises on any failure."""
    if not keyword or not keyword.strip():
        raise ValueError("keyword must be a non-empty search string")

    rows = max(1, min(rows, MAX_ROWS))
    payload = {"keyword": keyword.strip(), "oppStatuses": "posted", "rows": rows}

    response = httpx.post(GRANTS_API_URL, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    body = response.json()

    if body.get("errorcode") != 0:
        raise RuntimeError(f"grants.gov returned an error: {body.get('msg', 'unknown')!r}")

    data = body["data"]
    grants = [
        {
            "title": hit["title"],
            "agency": hit.get("agency") or hit.get("agencyCode", ""),
            "opportunity_number": hit.get("number", ""),
            "open_date": hit.get("openDate", ""),
            "close_date": hit.get("closeDate", ""),
            "url": GRANT_DETAIL_URL.format(id=hit["id"]),
        }
        for hit in data.get("oppHits", [])
    ]
    return {"count": data.get("hitCount", len(grants)), "grants": grants}
