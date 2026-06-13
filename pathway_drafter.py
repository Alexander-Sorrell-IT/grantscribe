"""GrantScribe — education-to-employment plan drafter (DeepSeek Pro).

Drafts a short funded-path plan / enrollment-intent statement in the STUDENT'S
OWN VOICE, grounded in their stored story, naming a REAL CareerOneStop ETPL
training program. The reader is a WIOA workforce board / ETPL funder deciding
whether to fund the enrollment — so the plan names the specific program, school,
and credential VERBATIM, and ships with a receipt the board can re-verify against
CareerOneStop without trusting the applicant.

This is the pathway equivalent of the LOI drafter+receipt: it doesn't just list
programs (CareerOneStop's own site does that) — it produces a committed,
verifiable artifact. No silent fallbacks; grounds only in the supplied story.
"""
from __future__ import annotations

from loi_drafter import _MODEL_PRO, _NO_THINK, _client
from pathway_receipt import build_pathway_receipt


def draft_pathway_plan(program: dict, student_story: str, goal_occupation: str = "") -> str:
    """Draft a funded-path plan for `program`, in the voice of the person behind `student_story`.

    `program` is a normalized CareerOneStop program (from training_api), so its
    program / school / credential are trustworthy-by-source — given to the model
    as VERBATIM facts to copy, never to invent. Raises if the draft fails to name
    the funded program (the refusal is the feature).
    """
    if not student_story.strip():
        raise ValueError("student_story is empty — need the student's story for voice/grounding")
    required = ("program", "school", "detail_id")
    missing = [k for k in required if not program.get(k)]
    if missing:
        raise ValueError(f"program missing required CareerOneStop fields: {missing}")

    prog_name = program["program"]
    school = program["school"]
    credential = program.get("credential", "")
    where = ", ".join(x for x in (program.get("city", ""), program.get("state", "")) if x)

    resp = _client().chat.completions.create(
        model=_MODEL_PRO,
        temperature=0.4,
        max_tokens=900,
        extra_body=_NO_THINK,
        messages=[
            {
                "role": "system",
                "content": (
                    "You draft a short EDUCATION-TO-EMPLOYMENT PLAN for an individual applying to a "
                    "WIOA workforce board / ETPL funder for support to enroll in a specific training "
                    "program. Write in the PERSON'S OWN VOICE — mirror the tone, circumstances, and "
                    "specifics from their story.\n\n"
                    "FORMAT (strict):\n"
                    "1. First line: `RE: Funding request — <PROGRAM> at <SCHOOL>` — copy the program "
                    "name and school EXACTLY as given (do not paraphrase or shorten them).\n"
                    "2. Blank line, then ~200–280 words: (a) who they are, using REAL details from the "
                    "story; (b) the job they're aiming for and why; (c) why THIS program/credential is "
                    "the concrete step to get there; (d) their commitment to completing it.\n"
                    "3. A `Credential to be earned:` line naming the credential VERBATIM (omit the line "
                    "only if no credential was provided).\n"
                    "4. A signature placeholder.\n\n"
                    "GROUNDING RULES (strict):\n"
                    "- Ground ONLY in facts from the supplied story — do NOT invent achievements, "
                    "  grades, work history, or hardships not present in it.\n"
                    "- The program name, school, and credential are TRUSTWORTHY because they come from "
                    "  the U.S. DOL CareerOneStop ETPL. Copy them VERBATIM. Never invent or alter them.\n"
                    "- Do not invent tuition figures, dates, or funding amounts."
                ),
            },
            {
                "role": "user",
                "content": (
                    "ETPL PROGRAM (verbatim from CareerOneStop — copy these strings exactly):\n"
                    f"  PROGRAM:    {prog_name}\n"
                    f"  SCHOOL:     {school}\n"
                    f"  CREDENTIAL: {credential or '(none specified)'}\n"
                    f"  LOCATION:   {where or '(varies)'}\n"
                    f"  GOAL JOB:   {goal_occupation or '(as described below)'}\n\n"
                    f"THE PERSON'S STORY (their voice + facts to ground in):\n{student_story}"
                ),
            },
        ],
    )
    plan = (resp.choices[0].message.content or "").strip()
    if not plan:
        raise RuntimeError("draft_pathway_plan returned empty output")

    # Same Reshaping Principle as the LOI: the funded program must be named
    # verbatim, or we refuse to return the plan. The artifact cannot misname
    # which ETPL program the board is being asked to fund.
    missing_verbatim: list[str] = []
    if prog_name not in plan:
        missing_verbatim.append("program name")
    if school not in plan:
        missing_verbatim.append("school")
    if credential and credential not in plan:
        missing_verbatim.append("credential")
    if missing_verbatim:
        raise RuntimeError(
            f"draft_pathway_plan output is missing verbatim CareerOneStop field(s): "
            f"{missing_verbatim} — refusing to return a plan that misnames the funded program"
        )

    receipt = build_pathway_receipt(program, student_story, goal_occupation=goal_occupation)
    return plan + "\n\n" + receipt
