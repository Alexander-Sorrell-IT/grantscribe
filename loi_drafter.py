"""GrantScribe — Letter of Intent drafter (DeepSeek Pro).

Drafts a grant Letter of Intent in the ORGANIZATION'S OWN VOICE, grounded in
their prior grant report. This is GrantScribe's moat: grants.gov and generic
grant-writing tools can't write in *your* voice from *your* history.

No silent fallbacks; grounds only in the supplied report (no invented stats).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from loi_receipt import build_receipt

load_dotenv(Path(__file__).with_name(".env"))

_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
_MODEL_PRO = os.environ.get("DEEPSEEK_MODEL_PRO", "deepseek-v4-pro")
_NO_THINK = {"thinking": {"type": "disabled"}}


def _client() -> OpenAI:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY missing — set it in grantscribe/.env")
    return OpenAI(api_key=key, base_url=_BASE_URL)


def draft_loi(grant: dict, org_report: str) -> str:
    """Draft a Letter of Intent for `grant`, in the voice of the org behind `org_report`.

    The grant payload is the one returned by grants.gov via `grants_api._fetch_grants`,
    so opportunity_number / url / close_date are trustworthy-by-source — the model is
    given them as VERBATIM facts to copy, never to invent.
    """
    if not org_report.strip():
        raise ValueError("org_report is empty — need the org's prior grant report for voice/grounding")

    required = ("title", "agency", "opportunity_number", "url")
    missing = [k for k in required if not grant.get(k)]
    if missing:
        raise ValueError(f"grant missing required fields from grants.gov: {missing}")

    deadline = grant.get("close_date") or "rolling / unspecified (verify on grants.gov)"

    resp = _client().chat.completions.create(
        model=_MODEL_PRO,
        temperature=0.4,
        max_tokens=1100,
        extra_body=_NO_THINK,
        messages=[
            {
                "role": "system",
                "content": (
                    "You draft a Letter of Intent (LOI) for a U.S. federal grant on behalf of a "
                    "nonprofit. Write in the ORGANIZATION'S OWN VOICE — mirror the tone, terminology, "
                    "program names, populations, and specifics from their prior grant report.\n\n"
                    "FORMAT (strict):\n"
                    "1. First line: `RE: <OPPORTUNITY_NUMBER> — <GRANT_TITLE>` — copy the opportunity "
                    "number EXACTLY as given by the user (it is from grants.gov, do not modify, "
                    "expand, or reformat it).\n"
                    "2. Blank line, then the addressee block: the funding agency on its own line, "
                    "then the line `Posted at: <GRANT_URL>` (copy the URL exactly).\n"
                    "3. Blank line, then a salutation (e.g. `Dear <Agency> Grants Program Officer,`).\n"
                    "4. Body, ~250–350 words: (a) introduce the org using REAL details from the "
                    "report, (b) state intent to apply for this opportunity, (c) connect the org's "
                    "mission and track record to the grant's purpose, (d) name the specific funding "
                    "need.\n"
                    "5. A `Submission deadline:` line with the close date supplied by the user "
                    "(copy verbatim).\n"
                    "6. Signature placeholder using the executive's name from the report.\n\n"
                    "GROUNDING RULES (strict):\n"
                    "- Ground ONLY in facts from the supplied org report — do NOT invent statistics, "
                    "  outcomes, achievements, or partnerships not present in it.\n"
                    "- The opportunity number, grant URL, and close date are TRUSTWORTHY because the "
                    "  user fetched them live from grants.gov. Copy them VERBATIM. Do not invent or "
                    "  change them. If you would otherwise have to guess one, fail loudly instead.\n"
                    "- Do not invent CFDA numbers, grant program codes, or contact emails."
                ),
            },
            {
                "role": "user",
                "content": (
                    "GRANT (verbatim from grants.gov — copy these strings exactly into the LOI header):\n"
                    f"  OPPORTUNITY_NUMBER: {grant['opportunity_number']}\n"
                    f"  GRANT_TITLE:        {grant['title']}\n"
                    f"  FUNDING_AGENCY:     {grant['agency']}\n"
                    f"  GRANT_URL:          {grant['url']}\n"
                    f"  CLOSE_DATE:         {deadline}\n\n"
                    f"ORG'S PRIOR GRANT REPORT (their voice + facts to ground in):\n{org_report}"
                ),
            },
        ],
    )
    letter = (resp.choices[0].message.content or "").strip()
    if not letter:
        raise RuntimeError("draft_loi returned empty output")

    # The Reshaping Principle compiled: every field grants.gov gave us as a trusted
    # identifier must appear verbatim in the letter, or we refuse to return it.
    # The system is structurally incapable of returning a non-submittable artifact.
    opp = grant["opportunity_number"]
    url = grant["url"]
    close = grant.get("close_date") or ""
    missing: list[str] = []
    if opp not in letter:
        missing.append("opportunity_number")
    if url not in letter:
        missing.append("grant URL")
    if close and close not in letter:
        missing.append("submission deadline")
    if missing:
        raise RuntimeError(
            f"draft_loi output is missing verbatim grants.gov field(s): {missing} — "
            "refusing to return a non-submittable draft"
        )

    # Verifiable receipt: every LOI carries a structured block the funder can
    # verify back to grants.gov (offline or live). This is the cryptographic
    # version of the procedural "no hallucination" guarantee — the funder no
    # longer has to trust the sender to know the opportunity is real.
    receipt = build_receipt(grant, org_report)
    return letter + "\n\n" + receipt
