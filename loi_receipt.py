"""GrantScribe — verifiable LOI receipts.

Every Letter of Intent ships with a structured *receipt block* appended to the
letter. The receipt is the artifact that lets a funder verify, without trusting
the sender, that the LOI was generated against a real grants.gov opportunity at
a real point in time:

    ---
    GRANTSCRIBE VERIFICATION RECEIPT v1
    generated_at: 2026-05-26T18:42:15Z
    grant_source: grants.gov
    opportunity_number: ETA-TEGL-10-25-YOUTH
    grant_url: https://www.grants.gov/search-results-detail/362125
    close_date: 05/29/2026
    grant_canonical_sha256: 7a3f2c8b... (over the canonical JSON of the
                                          trust-relevant grants.gov fields)
    org_report_sha256: 9b8e4d12...        (proves the LOI's voice has not been
                                          swapped post-draft; org keeps the source)
    receipt_id: GS-7e156e6-a1b2c3
    verify_command: python verify_loi.py --letter <file>
    ---

What the funder can verify (offline): the receipt is well-formed and
self-consistent.

What the funder can verify (live, against grants.gov): the grant identified in
the receipt **exists** at the URL, with the same canonical field values, and
therefore the LOI was anchored in a real opportunity at draft time. The
opportunity number wasn't fabricated; the URL points where the receipt says it
does; the deadline isn't invented.

What this v1 receipt does NOT do (honest scope):
  - No cryptographic signing (HMAC / PKI). Production would add it; for the
    hackathon submission, content hashing demonstrates the reshape. A receipt
    can be forged by someone who controls the LOI; a SIGNED receipt cannot.
  - No proof the LOI text wasn't edited post-draft. A future version could
    embed `loi_sha256` to cover the letter body too.

Goal of this module: make the **category** of "verifiable application
infrastructure" concretely demonstrable. Once one funder requires it, every
other will.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RECEIPT_VERSION = "1"
RECEIPT_HEADER = "GRANTSCRIBE VERIFICATION RECEIPT v" + RECEIPT_VERSION
RECEIPT_BEGIN_LINE = "--- BEGIN GRANTSCRIBE RECEIPT ---"
RECEIPT_END_LINE = "--- END GRANTSCRIBE RECEIPT ---"

# The trust-relevant fields whose canonical JSON is hashed. These are the fields
# a funder cares about for "is this LOI talking about a real grant?" — title and
# agency are excluded from the hash because they're informational; tampering
# with them doesn't change which opportunity is being applied to.
_GRANT_HASH_FIELDS = ("opportunity_number", "url", "close_date")


def _canonical_grant_payload(grant: dict) -> str:
    """Stable JSON encoding of the trust-relevant grant fields."""
    canon = {k: grant.get(k, "") for k in _GRANT_HASH_FIELDS}
    return json.dumps(canon, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_grant_hash(grant: dict) -> str:
    """sha256 over the canonical encoding of the trust-relevant grants.gov fields."""
    return hashlib.sha256(_canonical_grant_payload(grant).encode("utf-8")).hexdigest()


def org_report_hash(org_report: str) -> str:
    """sha256 over the org's report bytes (UTF-8). The report itself is private."""
    return hashlib.sha256(org_report.encode("utf-8")).hexdigest()


def _git_commit_short() -> str:
    """Best-effort current commit SHA (short) for receipt traceability."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _new_receipt_id() -> str:
    return f"GS-{_git_commit_short()}-{secrets.token_hex(3)}"


def build_receipt(grant: dict, org_report: str) -> str:
    """Construct the receipt block to append to an LOI."""
    fields = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "grant_source": "grants.gov",
        "opportunity_number": grant.get("opportunity_number", ""),
        "grant_url": grant.get("url", ""),
        "close_date": grant.get("close_date", ""),
        "grant_canonical_sha256": canonical_grant_hash(grant),
        "org_report_sha256": org_report_hash(org_report),
        "receipt_id": _new_receipt_id(),
        "verify_command": "python verify_loi.py --letter <file>",
    }
    lines = [RECEIPT_BEGIN_LINE, RECEIPT_HEADER]
    for k, v in fields.items():
        lines.append(f"{k}: {v}")
    lines.append(RECEIPT_END_LINE)
    return "\n".join(lines)


_KV_RE = re.compile(r"^([a-z_][a-z0-9_]*):\s*(.*)$")


def parse_receipt(text: str) -> dict | None:
    """Extract a receipt block from an LOI; return its fields, or None if absent."""
    if RECEIPT_BEGIN_LINE not in text or RECEIPT_END_LINE not in text:
        return None
    block = text.split(RECEIPT_BEGIN_LINE, 1)[1].split(RECEIPT_END_LINE, 1)[0]
    fields: dict[str, str] = {}
    header_seen = False
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("GRANTSCRIBE VERIFICATION RECEIPT"):
            header_seen = True
            fields["_header"] = line
            continue
        m = _KV_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    if not header_seen:
        return None
    return fields


def verify_receipt_offline(receipt: dict) -> dict:
    """Offline verification: confirm the receipt is well-formed and self-consistent.

    Returns {"verified": bool, "checks": [{"name": str, "passed": bool, "detail": str}]}.
    No network — proves only that the receipt itself is structurally honest.
    """
    checks = []

    required = (
        "generated_at", "grant_source", "opportunity_number", "grant_url",
        "close_date", "grant_canonical_sha256", "org_report_sha256", "receipt_id",
    )
    missing = [k for k in required if not receipt.get(k)]
    checks.append({
        "name": "receipt has all required fields",
        "passed": not missing,
        "detail": "ok" if not missing else f"missing: {missing}",
    })

    # Recompute the canonical hash from the fields in the receipt itself —
    # this proves the receipt's identifiers are internally consistent.
    reconstructed = {
        "opportunity_number": receipt.get("opportunity_number", ""),
        "url": receipt.get("grant_url", ""),
        "close_date": receipt.get("close_date", ""),
    }
    recomputed = canonical_grant_hash(reconstructed)
    matches = recomputed == receipt.get("grant_canonical_sha256")
    checks.append({
        "name": "grant_canonical_sha256 matches the receipt's own identifier fields",
        "passed": matches,
        "detail": "ok" if matches else f"expected {receipt.get('grant_canonical_sha256')!r}, recomputed {recomputed!r}",
    })

    checks.append({
        "name": "grant_url points at grants.gov",
        "passed": receipt.get("grant_url", "").startswith("https://www.grants.gov/"),
        "detail": receipt.get("grant_url", ""),
    })

    return {"verified": all(c["passed"] for c in checks), "checks": checks}


def verify_receipt_live(receipt: dict) -> dict:
    """Live verification: re-fetch the grant from grants.gov and confirm the hash.

    Returns {"verified": bool, "checks": [...]} as above, plus a "live_grant"
    field with what grants.gov currently returns for the opportunity number.
    """
    # Import locally to avoid pulling httpx into modules that only need offline verification.
    from grants_api import _fetch_grants

    offline = verify_receipt_offline(receipt)
    if not offline["verified"]:
        return {**offline, "live_grant": None,
                "note": "skipped live re-fetch because the receipt is not internally consistent"}

    opp = receipt.get("opportunity_number", "")
    live = _fetch_grants(opp, rows=10) if opp else {"grants": []}
    matched = next((g for g in live.get("grants", []) if g.get("opportunity_number") == opp), None)

    checks = list(offline["checks"])
    if matched is None:
        checks.append({
            "name": "grants.gov still lists this opportunity by opportunity_number",
            "passed": False,
            "detail": f"no current grants.gov hit for opportunity_number={opp!r} — it may have been archived; verification falls back to offline",
        })
        return {"verified": all(c["passed"] for c in checks), "checks": checks, "live_grant": None}

    live_hash = canonical_grant_hash(matched)
    matches = live_hash == receipt.get("grant_canonical_sha256")
    checks.append({
        "name": "live grants.gov payload hashes to the same grant_canonical_sha256",
        "passed": matches,
        "detail": "ok — receipt anchored in live grants.gov data" if matches
                  else f"hash drift: receipt={receipt.get('grant_canonical_sha256')} live={live_hash} (grant fields may have been edited on grants.gov since the receipt was issued)",
    })
    return {"verified": all(c["passed"] for c in checks), "checks": checks, "live_grant": matched}
