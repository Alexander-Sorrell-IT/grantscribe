# GrantScribe — Slack Agent Builder Challenge Submission

**Track:** Slack Agent for Good
**Tagline:** You describe what you do. The Letter of Intent appears, in your voice, ready to submit — with a receipt the funder can verify.

This file is the single entry point for judges. It maps every Devpost requirement to where it
lives in the repo, self-assesses against the four judging criteria, lists the live-validation
results, and tracks what still needs to ship before the July 13 deadline.

---

## 1. Devpost submission checklist

| Required by Devpost | Where it is | Status |
|---|---|---|
| Project track | "Slack Agent for Good" (above) | Done |
| Text description: features & functionality | [`submission/DEVPOST.md`](submission/DEVPOST.md) + §2 below | Done |
| Impact explanation (Slack Agent for Good) | [`submission/IMPACT.md`](submission/IMPACT.md) + §3 below | Done |
| Architecture diagram | [`submission/architecture.png`](submission/architecture.png) (Mermaid source in [`submission/ARCHITECTURE.md`](submission/ARCHITECTURE.md)) | Done |
| ~3-minute demo video | [`demo/out/GrantScribe_trailer.mp4`](demo/out/GrantScribe_trailer.mp4) (~2:30, recorded with per-block voiceover; script in [`demo/SCRIPT.md`](demo/SCRIPT.md)) | Done (recorded — upload to a host + paste link in the Devpost form) |
| Slack developer sandbox URL with access for `slackhack@salesforce.com` + `testing@devpost.com` | Slack workspace `GrantScribe` | **Sandbox URL not captured; testers not invited yet** |
| Public code repo | [github.com/Alexander-Sorrell-IT/grantscribe](https://github.com/Alexander-Sorrell-IT/grantscribe) | Done |

---

## 2. What it does (text description)

**GrantScribe is one Slack agent. You describe what you do. The Letter of Intent appears, in your voice, ready to submit.**

| Slash command | Audience | What happens |
|---|---|---|
| `/setreport` | Whoever installs the agent | Opens a modal (or `/setreport <text>` inline). Paste any prior grant/annual report — stored privately per workspace. This is the org's voice; `/grants` refuses to draft without it. |
| `/grants <what you do>` | Nonprofits / fiscal sponsors / capacity-building orgs | Tight grants.gov query → drop expired → DeepSeek re-rank for genuine fit (with a reason on every card) → "✍️ Draft LOI" button drafts a Letter of Intent in the org's voice with the **verbatim** opportunity number, URL, and deadline from grants.gov. The drafter raises `RuntimeError` if any of those identifiers is missing — there are no non-submittable drafts. |
| `/training <a skill>` | Students / career-changers / workforce orgs | Live query to U.S. DOL CareerOneStop (ETA Training API) → real accredited programs (nationwide, or near a ZIP you add) → each card naming the **credential** that program grants. No fixtures — the programs are the ones the federal database returns. |
| `/pathway <a goal job>` | Students / career-changers / workforce orgs | Maps the goal job → its O\*NET occupation → the credential it requires → real ETPL programs that grant it (nationwide, or near a ZIP you add). "📝 Draft my plan" drafts a funded-path plan in your own voice with the **verbatim** program, school, and credential — the drafter raises `RuntimeError` if the funded program isn't named verbatim — and emits a second receipt the funder re-verifies back to the CareerOneStop ETPL by `DetailId` via `verify_pathway.py`. |
| `/scholarships <about you>` | Students | **The honest finding is the answer.** We checked: CareerOneStop's developer API has no scholarship service, and no free public scholarship API exists. Rather than fake a database, the handler says exactly that and redirects you to the routes that *do* remove the money barrier — `/pathway`, `/training`, `/grants`. |
| `/learn <a goal>` | Anyone | Internet Archive search → re-rank for level + fit → free books + curated providers (OpenStax · MIT OCW · Khan · freeCodeCamp). |
| `/ask <a question>` | Anyone | Free tutor answering **only** from Wikibooks / Wikiversity, **with citations**. Returns `null` if no source is retrievable — refuses to invent. |

**The shape**: messy plain-language request → tight query → drop noise → re-rank for true fit with a reason → draft in the user's voice with verbatim identifiers, or refuse to ship. Reshape the activity, and the application becomes the path of least resistance.

---

## 3. Impact (Slack Agent for Good) — short version

The U.S. high school class of 2024 left **$4.4 billion in Pell Grants on the table** because 830,000 eligible students never finished the application (NCAN, 2025). Not applying was easier than applying. GrantScribe inverts that incentive: when describing what you do is easier than writing what you do, the application becomes the default rather than the exception. The grant-writer, the college counselor, and the tutor — three roles most people can't afford — are inside a Slack channel for free.

Full version, with the comparisons table and the audience pivot, in [`submission/IMPACT.md`](submission/IMPACT.md).

---

## 4. How we measure up against the judging criteria

### Technological Implementation

- **Verifiable application infrastructure (the category-defining piece) — and now it ships twice.** Every LOI ships with a structured receipt — hashes of the live grants.gov payload at draft time + the org-report content hash + timestamp + receipt ID — that a funder can re-verify back to grants.gov via `verify_loi.py --live` *without trusting the sender*. Tampering with the opportunity number, URL, or deadline breaks the hash. The same pattern now runs a second time: every `/pathway` plan ships its own receipt that a workforce board re-verifies live against the U.S. DOL CareerOneStop ETPL by `DetailId` via `verify_pathway.py` — tampering with the program, school, credential, CIP code, or DetailId breaks *its* hash. Two receipts, one rule: draft-then-prove, or it doesn't exist. *See `loi_receipt.py` / `verify_loi.py` (round-trip + tampering-detection + live re-verification tested as claims 10–12, plus the standing-announcement guard at claim 22 of `verify.py`) and `pathway_receipt.py` / `verify_pathway.py` (the same three tested as claims 17–19, plus claims 20–21 and 23). Honest scope on both: content hashing only — no HMAC/PKI signing yet; that is the named v2 hardening.*
- **MCP is load-bearing, in code.** Two distinct MCP clients call the server's tools today: the Slack app via `mcp_bridge.py`, and a standalone CLI at `demo/mcp_client.py` (no shared imports from `grantscribe`). Portability is observable in a terminal, not asserted in copy.
- **The system refuses to ship a non-submittable artifact.** `loi_drafter.py` post-checks that the verbatim opportunity number, URL, and (when present) deadline from grants.gov all appear in the letter — missing any → `RuntimeError`. Then the receipt is appended. The artifact is submittable AND verifiable, or it doesn't exist.
- **The moat is shipped, not narrated.** `/setreport` (`slack_app.py:handle_setreport`) opens a Slack modal, stores the org's report in `state/org_reports.json` keyed by `(workspace, user)`. `/grants` and the LOI handler refuse to run without it. There is no fixture fallback in production code.
- **Hallucination guarded three ways.** (1) Drafter system prompt forbids inventing IDs/statistics. (2) Post-check verifies the *real* grants.gov fields appear verbatim in the letter. (3) Receipt embeds a canonical hash of the grant's opportunity number, URL, and deadline, so tampering with any of those three breaks the hash — the funder catches it without trusting the sender. Tutor refuses to answer without retrievable sources.
- **Honest engine count.** Two retrieval pipelines share an *extract → fetch → JSON-rerank-with-reason* shape (`grant_intel`, `resources`); one workforce pipeline maps a goal job → real O*NET occupation → credential → live CareerOneStop ETPL programs (`pathway`, `training_api`, `occupation_api`); **two drafters share one draft-then-prove shape** — single-shot + verbatim post-check + verifiable receipt (`loi_drafter`+`loi_receipt`, `pathway_drafter`+`pathway_receipt`); one grounded tutor does multi-source MediaWiki retrieval + cited single answer (`ask`). Seven user-facing commands, four engine shapes, two re-verifiable receipts, one MCP server.

### Design

- **Native Slack UX** — slash commands + Block Kit cards + "✍️ Draft LOI" action buttons + a paste-your-report modal. Socket Mode means no public URL needed.
- **Trust signals visible on every card.** Each grant card shows the fit score, the deadline, and the one-line reason it was chosen — *before* the user clicks anything.
- **Honest empty states.** No stored report → the agent says exactly that and tells you to run `/setreport`. No honest scholarship source exists — we checked: CareerOneStop has no scholarship service and no free public scholarship API exists — so `/scholarships` says so plainly and points you to the routes that *do* remove the money barrier: `/pathway` (the credential a job needs + real funded programs near you), `/training` (real accredited U.S. DOL CareerOneStop programs), `/grants` (federal grants + an LOI in your voice). The empty state that tells the truth is the feature.

### Potential Impact

- **The Reshape transfers — and it already ran twice.** Same pattern (extract → rerank-with-reason → draft-with-verbatim-identifiers or refuse) carried from grants to the workforce pillar: `/training` and `/pathway` run live on the DOL CareerOneStop ETPL, and `/pathway` emits a *second* verifiable receipt, re-checkable by DetailId via `verify_pathway.py`. Two receipts, one pattern — draft-then-prove, the Reshaping Principle run twice. From there it reaches the learning resources and the tutor. New verticals are tool adapters, not new architectures.
- **Audience that's actually in Slack.** Capacity-building intermediaries — fiscal sponsors, foundation program teams, college-access nonprofits — already live in Slack and serve dozens of grassroots groups. The per-user report store means one intermediary can hold 20 client voices.
- **The access gap is real and large.** $4.4B in Pell alone in 2024; hundreds of billions in annual federal grant flows where application-capacity bounds participation more than eligibility does.

### Quality of the Idea

- **A new category, not an incremental product.** We didn't just delete the blank page; we invented the receipt that a funder uses to audit the draft. **Verifiable application infrastructure** didn't exist yesterday. After this, every grant submitted via an AI tool needs verification metadata — because LLM-drafted prose without it is, by construction, unverifiable.
- **The technical signature is the refusal + the proof.** Other LLM tools fail open — they ship the confident-sounding wrong draft. GrantScribe fails loud *and* emits a hash chain back to grants.gov so the receiver doesn't have to take the sender's word for it. That is the Reshaping Principle compiled into Python.
- **Re-rank-with-a-reason as a primitive.** The reason is a *stage* of the ranking pipeline, written to JSON, then surfaced on the card — not optimistic post-hoc text generated to make the result look smart.

---

## 5. Validation — what we actually ran

> **Single auditable proof:** run `python verify.py` from the repo root. It starts
> the MCP server, exercises every shipped claim listed in §4, and prints PASS / FAIL
> per claim with file:line evidence. Exits 0 iff every claim is verified live.
> Last run (2026-06-13): **23/23 PASS** — covering both verifiable receipts, the same
> draft-then-prove pattern run twice. The LOI receipt: round-trip, tampering detection on
> the opportunity number, and live re-verification against grants.gov. The /pathway receipt:
> round-trip, tampering detection on a swapped school, and live re-verification against the
> U.S. DOL CareerOneStop ETPL by DetailId. Plus the live workforce engine under both:
> /training and /pathway run against CareerOneStop, mapping a goal job to a real occupation,
> credential, and funded programs near you.

All run live against real APIs. Every test exits 0.

| Test | What it proves | Result |
|---|---|---|
| `test_deepseek.py` | DeepSeek API key + base URL work | ✓ |
| `test_grants.py` | Live grants.gov fetch + parse | ✓ (raw 654-result query parsed) |
| `test_intel.py` | Description → tight query → re-rank for fit with reasons | ✓ (e.g. 121 raw → 2 explained matches) |
| `test_loi.py` | Full pipeline → **submittable** LOI in org voice | ✓ Verbatim opportunity number, URL, and deadline all present in the draft (asserted in the test) |
| `test_resources.py` | Live Internet Archive + curated providers, re-ranked | ✓ 4 books + 4 providers |
| `test_ask.py` | Wikibooks/Wikiversity tutor with citations | ✓ Cited answer; refuses without sources |
| `check_slack.py` | Bot & app tokens valid | ✓ team=`GrantScribe`, bot=`@grantscribe` |
| `test_mcp_bridge.py` | Find-grants + draft-LOI **through the MCP server** | ✓ MCP round-trip OK |
| `test_mcp_ask.py` | `/ask` through MCP | ✓ |
| `test_mcp_resources.py` | `/learn` through MCP | ✓ |
| `demo/mcp_client.py` (manual) | A second, **standalone** MCP client (no GrantScribe imports) hits the same server and gets the same ranked grants + cited tutor answers. | ✓ Verified 2026-05-26 |
| **`verify.py`** | **Self-contained claim-by-claim audit** — starts the MCP server, runs all 23 §4 claims (including **both** verifiable receipts: the LOI round-trip + tampering-detection + live grants.gov re-verification, and the `/pathway` plan round-trip + tampering-detection + live DOL CareerOneStop ETPL re-verification by DetailId — plus the live `/training` and `/pathway` workforce lookups that feed them) with PASS/FAIL output and file:line evidence. **Designed for judges to run.** | **✓ 23/23 PASS 2026-06-13** |
| **`verify_loi.py`** | **Funder-side audit tool.** Takes a received LOI and verifies its embedded receipt offline (hash self-consistency) or live (re-fetches the grant from grants.gov, recomputes the canonical hash). Tampering with the opportunity number, URL, or deadline breaks the hash. **Designed for receiving funders.** | ✓ Verified live against `ED-GRANT-26-054` on 2026-05-26 |
| **`verify_pathway.py`** | **The same audit tool, a second time — for workforce boards.** Takes a received `/pathway` plan and verifies its embedded receipt offline (hash self-consistency) or live (re-fetches the program from U.S. DOL CareerOneStop by `DetailId`, recomputes the canonical hash). Tampering with the program, school, credential, CIP code, or `DetailId` breaks the hash. **Designed for receiving funders.** Two receipts, one pattern: draft-then-prove. | ✓ Verified live by `DetailId` against a real CareerOneStop ETPL program (`verify.py` claims 17–21, 23) |

**The scholarship truth — and the second pillar that replaces it:** there is no free public scholarship API to test against — CareerOneStop has no scholarship service, and no free public one exists. So `/scholarships` ships an honest empty-state that says exactly that and redirects to the routes that actually fund a path: `/grants`, `/training`, and `/pathway`. Those are not placeholders — `/training` and `/pathway` run **live** against the U.S. DOL CareerOneStop Training/Occupation APIs (the credentials are real and obtained), and `/pathway` emits a second verifiable receipt the funder re-checks against the CareerOneStop ETPL by `DetailId` via `verify_pathway.py`. We deleted the scholarship we couldn't honestly find, and we shipped the credential a job needs instead. The empty-state that tells the truth is the feature. See §6.

---

## 6. What's left before submission

**Required by Devpost:**

1. _(Recorded — see "Already complete.")_ The ~2:30 demo video is at [`demo/out/GrantScribe_trailer.mp4`](demo/out/GrantScribe_trailer.mp4) (Piper per-block voiceover). **Remaining:** upload it to a public host (YouTube/Vimeo) and paste the link in the Devpost form.
2. **Capture sandbox URL + invite the two testers.** Add `slackhack@salesforce.com` and `testing@devpost.com` to the `GrantScribe` workspace; record the workspace URL for the Devpost form.
3. **File the Devpost submission form.** Paste the copy from `submission/DEVPOST.md`, attach `submission/architecture.png`, link the uploaded video, select the "Slack Agent for Good" track, and submit before the July 13 deadline.
4. _(Done — see "Already complete.")_ The CareerOneStop credentials are obtained and valid; they power `/training` and `/pathway` live against the U.S. DOL CareerOneStop Training/Occupation APIs. `/scholarships` does **not** become "live," and that is the honest finding, not a gap: there is no free public scholarship API — CareerOneStop has none, and the alternatives are paywalled or have no live host. So the second pillar isn't a scholarship search; it's `/pathway` and `/training` — the credential a job needs, plus real funded programs near you. `/scholarships` ships an honest empty state that says this and redirects to `/pathway`, `/training`, and `/grants`. Nothing left to wire.

**Already complete:**

- All four shipping pipelines work live (see §5).
- **Two verifiable receipts shipped end-to-end, one pattern.** The LOI receipt (`loi_receipt.py` + `verify_loi.py`) re-verifies back to grants.gov; the `/pathway` plan receipt (`pathway_receipt.py` + `verify_pathway.py`) re-verifies to the DOL CareerOneStop ETPL by DetailId. Funder-side audit closes the loop on both. Draft-then-prove, run twice — the Reshaping Principle a second time. New category: *verifiable application infrastructure*.
- The moat lives in code: `/setreport` + per-(workspace, user) store + LOI post-check refusing non-submittable drafts.
- MCP is observably load-bearing: two clients call the same server (Slack bridge + standalone CLI, both verified live).
- Architecture diagram exported to `submission/architecture.png`.
- Devpost-form-ready copy in `submission/DEVPOST.md` with the Reshape framing.
- Impact statement in `submission/IMPACT.md`, with the access-gap math ($4.4B Pell, 2024) and the audience pivot.
- Demo video recorded: `demo/out/GrantScribe_trailer.mp4` (~2:30, per-block voiceover); script + shot list in `demo/SCRIPT.md`.
- GitHub repo renamed (no trailing dot), local clean and pushed to `origin/main`.
- All shipped commands registered in `slack_manifest.yaml` — including the live workforce-data second pillar (`/training` + `/pathway`, both running on the U.S. DOL CareerOneStop APIs). Re-install the app or re-import the manifest before recording the demo.

---

## 7. How to run it (judges)

```bash
cp .env.example .env   # fill DEEPSEEK_API_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN; add CAREERONESTOP_USERID + CAREERONESTOP_TOKEN (free) to power /training and /pathway
PYTHONPATH=. uv run --with-requirements requirements.txt python grants_server.py   # MCP server (binds localhost:8000; set FASTMCP_PORT=<n> if 8000 is busy — verify.py honors it too)
PYTHONPATH=. uv run --with-requirements requirements.txt python slack_app.py       # Slack app

# In a separate terminal — the same MCP tools, from a separate process:
python demo/mcp_client.py list
python demo/mcp_client.py find-grants "youth refugee tutoring Ohio"
```

Create (or update) the Slack app from `slack_manifest.yaml`, install to the workspace, then in any
channel run `/setreport` once to seed the voice, then `/grants <what your org does>`.
