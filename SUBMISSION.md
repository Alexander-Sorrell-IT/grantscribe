# GrantScribe — Slack Agent Builder Challenge Submission

**Track:** Slack Agent for Good
**Tagline:** You describe what you do. The Letter of Intent appears, in your voice, ready to submit.

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
| ~3-minute demo video | [`demo/SCRIPT.md`](demo/SCRIPT.md) (script + shot list ready); MP4 not yet recorded | **Recording pending** |
| Slack developer sandbox URL with access for `slackhack@salesforce.com` + `testing@devpost.com` | Slack workspace `GrantScribe` | **Sandbox URL not captured; testers not invited yet** |
| Public code repo | [github.com/Alexander-Sorrell-IT/grantscribe](https://github.com/Alexander-Sorrell-IT/grantscribe) | Done |

---

## 2. What it does (text description)

**GrantScribe is one Slack agent. You describe what you do. The Letter of Intent appears, in your voice, ready to submit.**

| Slash command | Audience | What happens |
|---|---|---|
| `/setreport` | Whoever installs the agent | Opens a modal (or `/setreport <text>` inline). Paste any prior grant/annual report — stored privately per workspace. This is the org's voice; `/grants` refuses to draft without it. |
| `/grants <what you do>` | Nonprofits / fiscal sponsors / capacity-building orgs | Tight grants.gov query → drop expired → DeepSeek re-rank for genuine fit (with a reason on every card) → "✍️ Draft LOI" button drafts a Letter of Intent in the org's voice with the **verbatim** opportunity number, URL, and deadline from grants.gov. The drafter raises `RuntimeError` if any of those identifiers is missing — there are no non-submittable drafts. |
| `/scholarships <about you>` | Students | Same drafting shape against U.S. DOL CareerOneStop; pending the free CareerOneStop token. Registered in the manifest with a clear "credentials needed" message until wired. |
| `/learn <a goal>` | Anyone | Internet Archive search → re-rank for level + fit → free books + curated providers (OpenStax · MIT OCW · Khan · freeCodeCamp). |
| `/ask <a question>` | Anyone | Free tutor answering **only** from Wikibooks / Wikiversity, **with citations**. Returns `null` if no source is retrievable — refuses to invent. |

**The shape**: messy plain-language request → tight query → drop noise → re-rank for true fit with a reason → draft in the user's voice with verbatim identifiers, or refuse to ship. Reshape the activity, and the application becomes the path of least resistance.

---

## 3. Impact (Slack Agent for Good) — short version

The U.S. high school class of 2024 left **$4.4 billion in Pell Grants on the table** because 830,000 eligible students never finished the application (NCAN, 2025). Not applying was easier than applying. GrantScribe inverts that incentive: when describing what you do is easier than writing what you do, the application becomes the default rather than the exception. The grant-writer, the college counselor, and the tutor — three people the wealthy hire — are inside a Slack channel for free.

Full version, with the comparisons table and the audience pivot, in [`submission/IMPACT.md`](submission/IMPACT.md).

---

## 4. How we measure up against the judging criteria

### Technological Implementation

- **MCP is load-bearing, in code.** Two distinct MCP clients call the server's tools today: the Slack app via `mcp_bridge.py`, and a standalone CLI at `demo/mcp_client.py` (no shared imports from `grantscribe`). Portability is observable in a terminal, not asserted in copy. *See `grants_server.py`, `mcp_bridge.py`, `demo/mcp_client.py`.*
- **The system refuses to ship a non-submittable artifact.** `loi_drafter.py` post-checks that the verbatim opportunity number, URL, and (when present) deadline from grants.gov all appear in the letter — missing any → `RuntimeError`. That's not a soft guideline; it's a hard gate. *See `loi_drafter.py` lines ~101–115.*
- **The moat is shipped, not narrated.** `/setreport` (`slack_app.py:handle_setreport`) opens a Slack modal, stores the org's report in `state/org_reports.json` keyed by `(workspace, user)`. `/grants` and the LOI handler refuse to run without it. There is no fixture fallback in production code.
- **Hallucination guarded twice.** Drafter system prompt forbids inventing IDs/statistics; post-check then verifies the *real* grants.gov fields appear verbatim. Tutor refuses to answer without retrievable sources. Both behaviors are tested live.
- **Honest engine count.** Two retrieval pipelines share an *extract → fetch → JSON-rerank-with-reason* shape (`grant_intel`, `resources`); one drafter is single-shot + verbatim post-check (`loi_drafter`); one grounded tutor does multi-source MediaWiki retrieval + cited single answer (`ask`). Four user-facing capabilities, three engine shapes, one MCP server.

### Design

- **Native Slack UX** — slash commands + Block Kit cards + "✍️ Draft LOI" action buttons + a paste-your-report modal. Socket Mode means no public URL needed.
- **Trust signals visible on every card.** Each grant card shows the fit score, the deadline, and the one-line reason it was chosen — *before* the user clicks anything.
- **Honest empty states.** No stored report → the agent says exactly that and tells you to run `/setreport`. No CareerOneStop credentials → `/scholarships` explains what's missing instead of pretending to work.

### Potential Impact

- **The Reshape transfers.** Same pattern (extract → rerank-with-reason → draft-with-verbatim-identifiers or refuse) maps from grants to scholarships to learning resources to the tutor. New verticals are tool adapters, not new architectures.
- **Audience that's actually in Slack.** Capacity-building intermediaries — fiscal sponsors, foundation program teams, college-access nonprofits — already live in Slack and serve dozens of grassroots groups. The per-user report store means one intermediary can hold 20 client voices.
- **The access gap is real and large.** $4.4B in Pell alone in 2024; hundreds of billions in annual federal grant flows where application-capacity bounds participation more than eligibility does.

### Quality of the Idea

- **The merge isn't three labels glued on.** The setup is "grant-writer + counselor + tutor → one agent." The payoff is a level deeper: *the blank page was the barrier. We deleted the blank page.* The activity itself collapses into "describe what you do."
- **The technical signature is the refusal.** Other LLM tools fail open — they ship the confident-sounding wrong draft. GrantScribe fails loud. That is the Reshaping Principle compiled into Python.
- **Re-rank-with-a-reason as a primitive.** The reason is a *stage* of the ranking pipeline, written to JSON, then surfaced on the card — not optimistic post-hoc text generated to make the result look smart.

---

## 5. Validation — what we actually ran

> **Single auditable proof:** run `python verify.py` from the repo root. It starts
> the MCP server, exercises every shipped claim listed in §4, and prints PASS / FAIL
> per claim with file:line evidence. Exits 0 iff every claim is verified live.
> Last run (2026-05-26): **9/9 PASS**.

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
| **`verify.py`** | **Self-contained claim-by-claim audit** — starts the MCP server, runs all 9 §4 claims with PASS/FAIL output and file:line evidence. **Designed for judges to run.** | **✓ 9/9 PASS 2026-05-26** |

**Not tested live:** `/scholarships` — CareerOneStop credentials not yet obtained. The command is registered in the manifest with an honest empty-state message until wired. See §6.

---

## 6. What's left before submission

**Required by Devpost:**

1. **Record the ~3-minute demo video** using `demo/SCRIPT.md`. The script is timed to ~2:55 and shows `/setreport` → `/grants` → Draft LOI (with verbatim RE: line and deadline) → MCP CLI from a terminal → `/ask` with citations → architecture diagram → close.
2. **Capture sandbox URL + invite the two testers.** Add `slackhack@salesforce.com` and `testing@devpost.com` to the `GrantScribe` workspace; record the workspace URL for the Devpost form.
3. **Get CareerOneStop credentials** so `/scholarships` is live in the demo. Free at `https://www.careeronestop.org/Developers/WebAPI/registration.aspx`. Deadline is July 13, so there's time. If credentials don't arrive close to the deadline, the manifest message already explains the gap honestly — don't ship a broken path.

**Already complete:**

- All four shipping pipelines work live (see §5).
- The moat lives in code: `/setreport` + per-(workspace, user) store + LOI post-check refusing non-submittable drafts.
- MCP is observably load-bearing: two clients call the same server (Slack bridge + standalone CLI, both verified live).
- Architecture diagram exported to `submission/architecture.png`.
- Devpost-form-ready copy in `submission/DEVPOST.md` with the Reshape framing.
- Impact statement in `submission/IMPACT.md`, GrantScribe-vs-other-hackathon-entries comparison table included.
- Demo video script + shot list in `demo/SCRIPT.md`.
- GitHub repo renamed (no trailing dot), local clean and pushed to `origin/main`.
- `/setreport` and `/scholarships` registered in `slack_manifest.yaml` (re-install the app or re-import the manifest before recording the demo).

---

## 7. How to run it (judges)

```bash
cp .env.example .env   # fill DEEPSEEK_API_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN; CareerOneStop optional
PYTHONPATH=. uv run --with-requirements requirements.txt python grants_server.py   # MCP server
PYTHONPATH=. uv run --with-requirements requirements.txt python slack_app.py       # Slack app

# In a separate terminal — the same MCP tools, from a separate process:
python demo/mcp_client.py list
python demo/mcp_client.py find-grants "youth refugee tutoring Ohio"
```

Create (or update) the Slack app from `slack_manifest.yaml`, install to the workspace, then in any
channel run `/setreport` once to seed the voice, then `/grants <what your org does>`.
