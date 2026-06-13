"""GrantScribe — verifiable PATHWAY receipts (education-to-employment).

Every /pathway plan ships with a receipt block that lets a WIOA workforce board
/ ETPL funder confirm, WITHOUT trusting the applicant, that the plan names a
REAL CareerOneStop training program at a real point in time.

Distinct from the LOI receipt (which anchors to grants.gov): this anchors to
CareerOneStop's Eligible Training Provider List (ETPL) record by DetailId. The
markers are deliberately DIFFERENT from the LOI receipt's, so a verifier built
for one correctly reports "no receipt of my kind here" on the other — rather
than mis-judging a real receipt as forged.

    --- BEGIN GRANTSCRIBE PATHWAY RECEIPT ---
    GRANTSCRIBE PATHWAY RECEIPT v1
    generated_at: 2026-06-05T18:42:15Z
    training_source: CareerOneStop (U.S. DOL ETA / ETPL)
    goal_occupation: Registered Nurses (O*NET 29-1141.00)
    detail_id: 306216513899
    program: Registered Nursing/Registered Nurse
    school: Galen College of Nursing
    credential: Associate Degree
    cip_code: 513801
    program_canonical_sha256: 7a3f…  (over detail_id/program/school/credential/cip_code)
    student_story_sha256: 9b8e…      (proves the plan's voice wasn't swapped post-draft)
    receipt_id: GS-984bcfc-a1b2c3
    verify_command: python verify_pathway.py --plan <file>
    --- END GRANTSCRIBE PATHWAY RECEIPT ---

What a workforce board can verify (live): re-fetch the program from CareerOneStop
by DetailId, recompute the canonical hash, confirm it matches — i.e. the named
ETPL program is real and the plan wasn't pointed at a fabricated one.

Honest scope (same as the LOI receipt): content hashing only — no HMAC/PKI
signing yet. A signed receipt is the v2 hardening.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from loi_receipt import _new_receipt_id  # generic envelope helper (git commit + token)

RECEIPT_VERSION = "1"
RECEIPT_HEADER = "GRANTSCRIBE PATHWAY RECEIPT v" + RECEIPT_VERSION
RECEIPT_BEGIN_LINE = "--- BEGIN GRANTSCRIBE PATHWAY RECEIPT ---"
RECEIPT_END_LINE = "--- END GRANTSCRIBE PATHWAY RECEIPT ---"

# The fields whose canonical JSON is hashed — the program's identity in the ETPL.
# DetailId is the load-bearing anchor (it's what the live re-fetch keys on).
_PROGRAM_HASH_FIELDS = ("detail_id", "program", "school", "credential", "cip_code")


def _canonical_program_payload(program: dict) -> str:
    canon = {k: str(program.get(k, "")) for k in _PROGRAM_HASH_FIELDS}
    return json.dumps(canon, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_program_hash(program: dict) -> str:
    """sha256 over the canonical encoding of the program's ETPL identity fields."""
    return hashlib.sha256(_canonical_program_payload(program).encode("utf-8")).hexdigest()


def student_story_hash(student_story: str) -> str:
    """sha256 over the student's story bytes. The story itself stays private."""
    return hashlib.sha256(student_story.encode("utf-8")).hexdigest()


def build_pathway_receipt(program: dict, student_story: str, goal_occupation: str = "") -> str:
    """Construct the receipt block to append to a pathway plan."""
    fields = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "training_source": "CareerOneStop (U.S. DOL ETA / ETPL)",
        "goal_occupation": goal_occupation,
        "detail_id": str(program.get("detail_id", "")),
        "program": program.get("program", ""),
        "school": program.get("school", ""),
        "credential": program.get("credential", ""),
        "cip_code": str(program.get("cip_code", "")),
        "program_canonical_sha256": canonical_program_hash(program),
        "student_story_sha256": student_story_hash(student_story),
        "receipt_id": _new_receipt_id(),
        "verify_command": "python verify_pathway.py --plan <file>",
    }
    lines = [RECEIPT_BEGIN_LINE, RECEIPT_HEADER]
    for k, v in fields.items():
        lines.append(f"{k}: {v}")
    lines.append(RECEIPT_END_LINE)
    return "\n".join(lines)


_KV_RE = re.compile(r"^([a-z_][a-z0-9_]*):\s*(.*)$")


def parse_pathway_receipt(text: str) -> dict | None:
    """Extract a pathway receipt block from a plan; return its fields, or None."""
    if RECEIPT_BEGIN_LINE not in text or RECEIPT_END_LINE not in text:
        return None
    block = text.split(RECEIPT_BEGIN_LINE, 1)[1].split(RECEIPT_END_LINE, 1)[0]
    fields: dict[str, str] = {}
    header_seen = False
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("GRANTSCRIBE PATHWAY RECEIPT"):
            header_seen = True
            fields["_header"] = line
            continue
        m = _KV_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields if header_seen else None


def _reconstruct_program(receipt: dict) -> dict:
    return {k: receipt.get(k, "") for k in _PROGRAM_HASH_FIELDS}


def verify_pathway_receipt_offline(receipt: dict) -> dict:
    """Offline: confirm the receipt is well-formed and internally consistent.

    Returns {"verified": bool, "checks": [{"name","passed","detail"}]}. No network.
    """
    checks = []

    # detail_id is the load-bearing anchor; credential/cip_code may legitimately
    # be empty for some programs, so they aren't required to be non-empty.
    required = (
        "generated_at", "training_source", "detail_id",
        "program_canonical_sha256", "student_story_sha256", "receipt_id",
    )
    missing = [k for k in required if not receipt.get(k)]
    checks.append({
        "name": "receipt has all required fields",
        "passed": not missing,
        "detail": "ok" if not missing else f"missing: {missing}",
    })

    recomputed = canonical_program_hash(_reconstruct_program(receipt))
    matches = recomputed == receipt.get("program_canonical_sha256")
    checks.append({
        "name": "program_canonical_sha256 matches the receipt's own program fields",
        "passed": matches,
        "detail": "ok" if matches
                  else f"expected {receipt.get('program_canonical_sha256')!r}, recomputed {recomputed!r}",
    })

    checks.append({
        "name": "training_source is CareerOneStop",
        "passed": "careeronestop" in receipt.get("training_source", "").lower(),
        "detail": receipt.get("training_source", ""),
    })

    return {"verified": all(c["passed"] for c in checks), "checks": checks}


def verify_pathway_receipt_live(receipt: dict) -> dict:
    """Live: re-fetch the program from CareerOneStop by DetailId and confirm the hash."""
    from training_api import fetch_program_detail

    offline = verify_pathway_receipt_offline(receipt)
    if not offline["verified"]:
        return {**offline, "live_program": None,
                "note": "skipped live re-fetch because the receipt is not internally consistent"}

    detail_id = receipt.get("detail_id", "")
    checks = list(offline["checks"])
    try:
        live = fetch_program_detail(detail_id)
    except Exception as exc:
        checks.append({
            "name": "CareerOneStop still lists this program by DetailId",
            "passed": False,
            "detail": f"re-fetch failed for DetailId={detail_id!r}: {exc}",
        })
        return {"verified": False, "checks": checks, "live_program": None}

    live_hash = canonical_program_hash(live)
    matches = live_hash == receipt.get("program_canonical_sha256")
    checks.append({
        "name": "live CareerOneStop record hashes to the same program_canonical_sha256",
        "passed": matches,
        "detail": "ok — receipt anchored in live ETPL data" if matches
                  else f"hash drift: receipt={receipt.get('program_canonical_sha256')} live={live_hash} "
                       "(the program record may have been edited on CareerOneStop since the receipt was issued)",
    })
    return {"verified": all(c["passed"] for c in checks), "checks": checks, "live_program": live}
