"""CareerOneStop Training Finder (v2) client — real accredited training programs.

Removes the money barrier to *learning*: surfaces real, enrollable training
programs (the credential you'd earn, the format, the school, and where it is)
from the U.S. Department of Labor's CareerOneStop database.

CareerOneStop has no scholarship API — its developer catalog exposes Training,
Certifications, Occupations, etc., but not scholarships. This is the honest,
licensed use of the credentials: concrete programs you can actually enroll in.

No silent fallbacks: missing creds or any API/network failure raises.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

API_URL = "https://api.careeronestop.org/v2/training/programs"
DETAIL_URL = "https://api.careeronestop.org/v2/training/program"  # singular: one program by DetailId
REQUEST_TIMEOUT = 30.0
MAX_ROWS = 20


def _normalize_program(p: dict) -> dict:
    """The ONE normalizer used by both search and single-program fetch.

    Both paths must produce byte-identical trust fields or the receipt's live
    re-anchor (recompute-and-compare hash) would spuriously fail.
    """
    return {
        "detail_id": str(p.get("DetailId") or "").strip(),
        "program": (p.get("EtaProgramName") or p.get("CipTitle") or "").strip().rstrip("."),
        "credential": (p.get("Credential") or "").strip(),
        "award_level": (p.get("AwardLevel") or "").strip(),
        "format": ", ".join(p.get("Format") or []),
        "school": (p.get("SchoolName") or "").strip(),
        "city": (p.get("City") or "").strip(),
        "state": (p.get("StateAbbr") or "").strip(),
        "url": (p.get("SchoolURL") or "").strip(),
        "cip_code": str(p.get("CipCode") or "").strip(),
    }


def _creds() -> tuple[str, str]:
    uid = os.environ.get("CAREERONESTOP_USERID", "").strip()
    tok = os.environ.get("CAREERONESTOP_TOKEN", "").strip()
    if not (uid and tok):
        raise RuntimeError(
            "CareerOneStop credentials missing — set CAREERONESTOP_USERID and "
            "CAREERONESTOP_TOKEN in grantscribe/.env (free at "
            "careeronestop.org/Developers/WebAPI/registration.aspx)."
        )
    return uid, tok


def find_training(keyword: str, location: str = "0", rows: int = 5) -> dict:
    """Search CareerOneStop for real training programs matching `keyword`.

    Args:
        keyword: what to train for (e.g. "nursing", "welding", "data analytics").
        location: ZIP or "City, ST" to search near; "0" for nationwide.
        rows: max programs to return (1-20).

    Raises on missing creds or any API/network failure.
    """
    if not keyword or not keyword.strip():
        raise ValueError("keyword must be a non-empty search string")
    uid, tok = _creds()
    rows = max(1, min(rows, MAX_ROWS))

    location = (location or "0").strip() or "0"
    radius = "25" if location != "0" else "0"
    # v2 path order (after userId), "0" = no filter:
    #   keyword/location/radius/programLength/school/programName/programFormat/
    #   occupation/filterBySource/area/sortColumns/sortDirection/startRecord/limitRecord
    # Slashes in user input would inject extra path segments (the v2 API is fully
    # positional and quote() leaves "/" unencoded), so collapse them to spaces.
    parts = [
        quote(keyword.strip().replace("/", " ")), quote(location.replace("/", " ")), radius,
        "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", str(rows),
    ]
    url = f"{API_URL}/{uid}/" + "/".join(parts)

    resp = httpx.get(
        url,
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    # CareerOneStop returns 404 {"Message":"No data available"} for a zero-hit
    # search — that's an empty result, not an error.
    if resp.status_code == 404 and "No data available" in resp.text:
        return {"count": 0, "programs": [], "keyword": keyword.strip(), "source": "U.S. DOL CareerOneStop"}
    resp.raise_for_status()
    body = resp.json()

    programs = [_normalize_program(p) for p in body.get("SchoolPrograms", [])]
    return {
        "count": body.get("RecordCount", len(programs)),
        "programs": programs,
        "keyword": keyword.strip(),
        "source": "U.S. DOL CareerOneStop",
    }


def fetch_program_detail(detail_id: str) -> dict:
    """Re-fetch a single training program by its CareerOneStop DetailId.

    This is the live-anchor path: a pathway receipt records a program's DetailId
    + canonical hash at draft time; a verifier calls this to recompute the hash
    from CareerOneStop's current record. Raises on missing creds / API failure /
    unknown DetailId.
    """
    if not detail_id or not str(detail_id).strip():
        raise ValueError("detail_id must be a non-empty CareerOneStop DetailId")
    uid, tok = _creds()
    url = f"{DETAIL_URL}/{uid}/{quote(str(detail_id).strip())}"

    resp = httpx.get(
        url,
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    # The details endpoint returns SchoolPrograms as a single object; search
    # returns it as a list. Accept either.
    sp = resp.json().get("SchoolPrograms")
    record = sp[0] if isinstance(sp, list) else sp
    if not record:
        raise RuntimeError(f"CareerOneStop returned no program for DetailId {detail_id!r}")
    return _normalize_program(record)
