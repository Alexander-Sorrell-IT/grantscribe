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
    """Draft a Letter of Intent for `grant`, in the voice of the org behind `org_report`."""
    if not org_report.strip():
        raise ValueError("org_report is empty — need the org's prior grant report for voice/grounding")

    resp = _client().chat.completions.create(
        model=_MODEL_PRO,
        temperature=0.4,
        max_tokens=900,
        extra_body=_NO_THINK,
        messages=[
            {
                "role": "system",
                "content": (
                    "You draft a Letter of Intent (LOI) for a U.S. federal grant on behalf of a "
                    "nonprofit. Write in the ORGANIZATION'S OWN VOICE — mirror the tone, terminology, "
                    "program names, populations, and specifics from their prior grant report. The LOI: "
                    "(1) introduces the org using REAL details from the report, (2) states intent to "
                    "apply for the named grant, (3) connects the org's mission and track record to the "
                    "grant's purpose, (4) names the funding need. ~250-350 words, professional and "
                    "specific. Ground ONLY in facts from the report — do NOT invent statistics, "
                    "outcomes, or achievements not present. Reference the grant ONLY by its title and "
                    "funding agency; do NOT include or invent any opportunity number, CFDA number, "
                    "grant ID, or 'RE:' line (those are tracked separately). End with a signature placeholder."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"GRANT:\n  Title: {grant['title']}\n  Funding agency: {grant['agency']}\n\n"
                    f"ORG'S PRIOR GRANT REPORT (their voice + facts to ground in):\n{org_report}"
                ),
            },
        ],
    )
    letter = (resp.choices[0].message.content or "").strip()
    if not letter:
        raise RuntimeError("draft_loi returned empty output")
    return letter
