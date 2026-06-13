"""CareerOneStop Occupation search — confirms a goal job is a real occupation
and returns its canonical title + O*NET code.

Used by the education-to-employment pathway to anchor a messy goal ("i want to
be a nurse") to a real occupation before suggesting the training to get there.

No silent fallbacks: missing creds or any API/network failure raises.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

API_URL = "https://api.careeronestop.org/v1/occupation"
REQUEST_TIMEOUT = 30.0
MAX_ROWS = 20


def _creds() -> tuple[str, str]:
    uid = os.environ.get("CAREERONESTOP_USERID", "").strip()
    tok = os.environ.get("CAREERONESTOP_TOKEN", "").strip()
    if not (uid and tok):
        raise RuntimeError(
            "CareerOneStop credentials missing — set CAREERONESTOP_USERID and "
            "CAREERONESTOP_TOKEN in grantscribe/.env."
        )
    return uid, tok


def find_occupations(keyword: str, rows: int = 5) -> dict:
    """Search CareerOneStop occupations for `keyword`.

    Returns each match's canonical title + O*NET code. Raises on missing creds
    or any API/network failure.
    """
    if not keyword or not keyword.strip():
        raise ValueError("keyword must be a non-empty search string")
    uid, tok = _creds()
    rows = max(1, min(rows, MAX_ROWS))
    # verified path: /occupation/{userId}/{keyword}/{trainingType=N}/{startRecord}/{limit}
    # Collapse slashes so a keyword can't inject extra positional path segments.
    url = f"{API_URL}/{uid}/{quote(keyword.strip().replace('/', ' '))}/N/0/{rows}"

    resp = httpx.get(
        url,
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    # A zero-hit search returns 404 {"Message":"No data available"} — empty, not an error.
    if resp.status_code == 404 and "No data available" in resp.text:
        return {"count": 0, "occupations": [], "keyword": keyword.strip()}
    resp.raise_for_status()
    body = resp.json()

    occupations = [
        {
            "title": (o.get("OnetTitle") or "").strip(),
            "onet_code": (o.get("OnetCode") or "").strip(),
        }
        for o in body.get("OccupationList", [])
    ]
    return {
        "count": body.get("RecordCount", len(occupations)),
        "occupations": occupations,
        "keyword": keyword.strip(),
    }
