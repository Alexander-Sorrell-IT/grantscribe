# GrantScribe — Impact (Slack Agent for Good)

> *"Time always needs people to write the stories. So maybe that's your place — not to make the stories, just to write them down."*

For the people whose stories never reach the funder, GrantScribe writes them down.

---

## We didn't help under-resourced orgs apply for grants. We deleted "applying" — and invented the receipt.

**You describe what you do. The Letter of Intent appears, in your voice, ready to submit. And the funder can verify, without trusting you, that it's anchored in a real grants.gov opportunity.**

That is the category collapse. Not "AI that helps you apply." A system that **collapses applying into describing** — refuses to ship anything that isn't a real, submittable artifact — and **ships a cryptographic receipt with every Letter of Intent** so the funder can re-verify it back to the live API. The procedural "no hallucination" guarantee just became a verifiable one. After this, every grant submitted via an AI tool needs verification metadata — because LLM-drafted prose without it is, by construction, unverifiable. We built the first one.

The U.S. high school class of 2024 left **$4.4 billion in Pell Grants on the table** — 830,000 eligible students who never finished the FAFSA (NCAN, reported via NASFAA and Higher Education Today, 2025). Up $400 million from the class of 2023. The money was there. Not applying was easier than applying. Treat that as the thematic anchor for an access gap that runs through every federal grant program: nonprofits walk past hundreds of billions of federal dollars per year for the same reason — no one in the office has the hours to find the right opportunity and write the first draft.

Reshape the activity, and the gap inverts. When describing what you do is easier than writing what you do, the application is the default, not the exception.

---

## A grant-writer. A college counselor. A tutor.

Three people the wealthy hire. Three people the underserved can't afford.

- A grant-writer costs **$75–$150 an hour**; small nonprofits don't have one.
- A college counselor costs **$150–$300 an hour**; first-generation students don't have one.
- A tutor costs **$40–$80 an hour**; the parent priced out doesn't know that a peer-reviewed textbook and a full free course already exist for whatever their kid needs.

GrantScribe is one Slack agent that is all three. These are not three agents — but the merge is the *setup* beat. The payoff is one level deeper: **the blank page was the barrier. We deleted the blank page.**

---

## How the moat is shipped in code (not asserted in copy)

A judge can grep for it.

- **Voice is loaded by the user, not by us.** The Slack app no longer carries a fixture. `/setreport` opens a paste dialog (or `/setreport <text>` inline); the report is stored per `(workspace, user)` in `state/org_reports.json` (git-ignored, private). `/grants` *refuses to draft* if no report is set — *"No fixtures, no fictional fallback."* See `slack_app.py` `handle_setreport` + `handle_grants`.
- **The drafter is structurally incapable of returning a non-submittable artifact.** `loi_drafter.py` lines ~101–115 — a post-check verifies the verbatim opportunity number, the verbatim grants.gov URL, and (when present) the verbatim deadline are all in the letter. Missing any → `RuntimeError`. Not a warning, not a fallback. Other LLM tools fail open; this one fails loud.
- **The "why this fits" reason is a stage of the ranking, not optimistic post-hoc text.** `grant_intel.py` line ~93 — the rerank prompt requires `reason` per candidate, structured JSON. The reason appears on the Slack card before the user clicks anything.
- **The tutor cannot invent facts.** `ask.py` answers `/ask` only from text fetched from Wikibooks/Wikiversity for this specific question. If no source page is retrievable, the tutor returns `{"answer": null, ...}` rather than making one up.
- **No hallucinated grant IDs.** The drafter is forbidden in the system prompt from inventing an opportunity number, and the post-check confirms the *real* one from grants.gov appears verbatim.

The moat is not "in your voice from your report" as a marketing line. The moat is: **the user supplies the voice, the system supplies the verifiable identifiers, and the system refuses to ship anything that isn't both.**

## The receipt — a new category: verifiable application infrastructure

Every Letter of Intent now ships with a structured **verification receipt** appended to the letter:

```
--- BEGIN GRANTSCRIBE RECEIPT ---
GRANTSCRIBE VERIFICATION RECEIPT v1
generated_at: 2026-05-27T03:51:35Z
grant_source: grants.gov
opportunity_number: ETA-TEGL-10-25-YOUTH
grant_url: https://www.grants.gov/search-results-detail/362125
close_date: 05/29/2026
grant_canonical_sha256: de568f1c…
org_report_sha256: b5e05398…
receipt_id: GS-7e156e6-059b15
verify_command: python verify_loi.py --letter <file>
--- END GRANTSCRIBE RECEIPT ---
```

**The funder runs one command:** `python verify_loi.py --letter received.txt --live`. The script re-fetches the grant from grants.gov, recomputes the canonical hash of the live payload, and confirms it matches the receipt. If it does, the LOI is *anchored* in a real opportunity that existed at draft time — the opportunity number wasn't fabricated, the URL isn't a typo, the deadline isn't invented. **Without the sender being trusted.**

Tampering with any trust-relevant field (e.g. swapping `opportunity_number`) breaks the hash, and `verify_loi.py` flags it. We verified this end-to-end: see `verify.py` claims 10–12 (12/12 PASS).

This is the category that didn't exist yesterday: **verifiable application infrastructure**. Once one funder requires it, every funder will — because LLM-drafted prose *without* it is indistinguishable from chatbot slop, and the volume of AI-generated applications hitting funders is about to scale by 100×.

---

## Who actually uses it

Two honest audiences live in Slack today:

- **Capacity-building intermediaries** — fiscal sponsors, re-granters, foundation program teams, and college-access nonprofits (e.g. Bottom Line, College Possible affiliates). Their explicit job is to write applications on behalf of smaller groups they shelter or advise. They're in Slack now and need 20 drafts in 20 voices from 20 reports — which is exactly what the per-user `/setreport` store enables.
- **Mid-size nonprofits with operations staff** for whom "we don't have a grant-writer" is true even though they're Slack-equipped.

For the smallest, most marginal grassroots org that lives in WhatsApp and Gmail rather than Slack, the path is through the intermediary that already serves them. The product doesn't pretend the ED of the unstaffed refugee-serving nonprofit is logging into Slack to use it.

---

## Why it's built

The builder's grandfather had a standing rule: any child in the family who wanted to go to college, he paid for it. No charge. That rule is being continued, formalized — trusts for the four eligible family kids, doubled-amount, so college and adjacent expenses are covered.

GrantScribe is the universalized version of the same instinct: **every other family's kid, every under-resourced org, every adult who's been told they're not the right kind of "qualified."** Not by handing out money. By writing the application that gets them to it. That motive is in the Ledger, not the marketing.

---

## Why it stands out *in this specific hackathon*

Compare GrantScribe to the field a Devpost judge will actually read this summer. The other 100+ "Slack Agent for Good" entries will be slash-commands wrapped around an LLM.

| | Typical Slack Agent-for-Good hackathon entry | **GrantScribe** |
|---|---|---|
| LLM role | The product | One stage of a multi-stage pipeline |
| Failure mode on bad output | Ships in confident prose | **`RuntimeError` — refuses to ship** |
| Output guarantee | None | **Verbatim opportunity number + grants.gov URL + deadline, or no draft** |
| Hallucinated grant ID | Possible, undetectable to user | **Impossible by post-check** |
| "Why this fits" reason on each result | Optimistic post-hoc text | **A stage of the ranking, on every card** |
| Voice | Generic LLM | **The org's own, loaded via `/setreport`** |
| Citations on tutor answers | Sometimes, optional | **Required — no source page, no answer** |
| MCP integration | Sticker | **Two proven clients: the Slack bridge, and a standalone CLI (`demo/mcp_client.py`)** |
| Funder-side verifiability | None — receiver must trust the sender | **Cryptographic receipt on every LOI, re-verified live against grants.gov by `verify_loi.py`** |
| Auditability of the submission itself | "Trust us, we built this" | **`python verify.py` → 12/12 PASS with file:line evidence** |

**Every other entry will be measurable in tokens. GrantScribe is measurable in submittable artifacts.**

---

## What lives under the hood — honest version

Four commands, three engine shapes, one MCP server:

- **Two retrieval pipelines** share a *extract → fetch → JSON-rerank-with-reason* shape: `grant_intel.find_grants` (grants.gov) and `resources.find_resources` (Internet Archive + curated providers).
- **One drafter** is single-shot generation + verbatim post-check: `loi_drafter.draft_loi`.
- **One grounded tutor** is multi-source MediaWiki retrieval + cited single answer: `ask.answer_question`.
- **All four** are exposed through one MCP server (`grants_server.py`). Both the Slack app (via `mcp_bridge.py`) and a generic standalone CLI (`demo/mcp_client.py`, which doesn't import anything from `grantscribe`) call the same tools the same way.

Not "one engine." One MCP server, three engine shapes, four user-facing capabilities — and one ironclad rule across all of them: **the system never invents a fact and never ships an artifact it can't verify.**

---

## The size of the access gap, in real numbers

- **$4.4 billion** in Pell Grants left unclaimed by the U.S. high school class of 2024 (NCAN, 2025) — used here as a thematic anchor for the access gap, not a served-market number. GrantScribe does not write the FAFSA. The $4.4B is the size of the inverted-incentive problem the Reshape solves, not the size of the market we own.
- The U.S. federal government disburses **hundreds of billions of dollars in grants** per fiscal year. The share that flows to under-resourced organizations is bounded almost entirely by **application capacity**, not eligibility.
- A grant-writer's median fee for a single federal LOI: **$1,500–$5,000**, or 5–10% of the awarded amount on contingency. That gate is what `/setreport` + the post-checked LOI removes for an org with one document of prior writing.

---

## What the live demo proves

Against real grants.gov data, end-to-end on 2026-05-26:

1. The user runs `/setreport`, pastes a sample organizational report. Stored privately, per-(workspace, user).
2. The user runs `/grants youth refugee tutoring and after-school program in Ohio — need operating funds for staff and supplies`. Behind that one line: 654 raw matches → expired listings dropped → 2–3 grants ranked for fit, each with a one-line reason shown on the card.
3. One click of "✍️ Draft LOI". The letter appears, opens with `RE: ETA-TEGL-10-25-YOUTH — Workforce Innovation and Opportunity Act…`, uses *the org's actual cities, programs, student counts, and partners* lifted from the report they just pasted, and closes with the real `Submission deadline: 05/29/2026`. **Submittable.**
4. The same MCP tools, called from `demo/mcp_client.py` in a terminal next to Slack, return the same ranked grants. Portability is demonstrated, not claimed.

---

## In one sentence

**We deleted the blank page, and we invented the receipt. After this, every grant application written by an AI tool needs verification metadata — and every funder will require it. We built the first one.**
