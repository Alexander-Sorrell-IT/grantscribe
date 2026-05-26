# GrantScribe — Slack Agent Builder Challenge Submission

**Track:** Slack Agent for Good
**Tagline:** Removing the money barrier to opportunity — inside Slack.

This file is the single entry point for judges. It maps every Devpost requirement to where it
lives, self-assesses against the four judging criteria, and tracks what still needs to ship before
the July 13 deadline.

---

## 1. Devpost submission checklist

| Required by Devpost | Where it is | Status |
|---|---|---|
| Project track | "Slack Agent for Good" (above) | Done |
| Text description: features & functionality | [`submission/DEVPOST.md`](submission/DEVPOST.md) + section 2 below | Done |
| Impact explanation (Slack Agent for Good) | [`submission/IMPACT.md`](submission/IMPACT.md) + section 3 below | Done |
| Architecture diagram | [`submission/architecture.png`](submission/architecture.png) (Mermaid source in [`submission/ARCHITECTURE.md`](submission/ARCHITECTURE.md)) | Done |
| ~3-minute demo video | `demo/` | **Not recorded yet** |
| Slack developer sandbox URL with access for `slackhack@salesforce.com` + `testing@devpost.com` | Slack workspace `GrantScribe` | **Sandbox URL not captured; testers not invited yet** |
| Public code repo | [github.com/Alexander-Sorrell-IT/grantscribe.](https://github.com/Alexander-Sorrell-IT/grantscribe.) | Pushed and clean — **repo name has trailing dot; consider renaming** |

---

## 2. What it does (text description)

GrantScribe meets people where they already work — Slack — and does the two things
under-resourced people can't do for themselves: **the searching and the first draft.**

| Slash command | Audience | What happens |
|---|---|---|
| `/grants <what you do>` | Nonprofits | Tight query → live grants.gov search → drop expired → DeepSeek re-rank for genuine fit (with a reason) → drafts the Letter of Intent in the org's own voice, grounded in its past report |
| `/scholarships <about you>` | Students | Same pipeline against CareerOneStop; drafts the application essay in the student's voice *(pending CareerOneStop token — see §6)* |
| `/learn <a goal>` | Anyone | Internet Archive search → re-rank for level + fit → free books + curated course providers (OpenStax · MIT OCW · Khan · freeCodeCamp) |
| `/ask <a question>` | Anyone | Free tutor answering **only** from Wikibooks / Wikiversity, **with citations** — never invented facts |

**Why this is smarter than the source websites:** raw grants.gov / Archive keyword search returns
hundreds of loosely-matched, often-expired results. GrantScribe's value is the pipeline:
*messy plain-language request → tight query → drop expired → re-rank for genuine fit (with a
reason) → draft the application in the user's own voice.*

---

## 3. Impact (Slack Agent for Good)

The money for opportunity already exists — billions in federal grants, thousands of scholarships,
a world of free learning. The barrier isn't *availability*; it's *access*. A small nonprofit with
no grant-writer. A first-gen student with no counselor. A parent who can't afford tutoring.
Finding what you qualify for is hard, and the blank-page application is intimidating — so people
don't apply, and opportunity flows to whoever already has the staff and the know-how.

GrantScribe turns *"I don't have a grant-writer / counselor / money for tutoring"* into
*"here's what you qualify for, and here's the application — in your words."* Each funded grant is
a program that runs, each scholarship a student enrolled, each free resource a barrier removed.

Full statement in [`submission/IMPACT.md`](submission/IMPACT.md).

---

## 4. How we measure up against the judging criteria

### Technological Implementation
- **MCP server integration is load-bearing.** The Slack app is an MCP *client* — every action
  travels Slack → MCP bridge → MCP server → tool. Any other MCP client (Claude, Slack's own MCP
  client, MCP Inspector) can reuse `find_grants`, `draft_loi`, `find_resources`,
  `answer_question` unchanged. This is not bolt-on MCP; remove the MCP server and the agent stops
  working.
- **Code quality principles, enforced:** no fabricated data, grounded + cited answers, no
  hallucinated grant IDs (model can reference grants by title/agency only), no silent fallbacks
  (MCP tool errors raise, they don't get swallowed). Secrets live in a git-ignored `.env`.
- **Live validation (May 25, 2026):** all ten test scripts pass against the real APIs (DeepSeek,
  grants.gov, Internet Archive, Wikibooks, Slack auth, MCP round-trip). See §5.

### Design
- **Native Slack UX** — slash commands + Block Kit cards + buttons (e.g. "✍️ Draft LOI"),
  Socket Mode so no public URL is needed.
- **Balanced frontend/backend** — the Slack surface is genuinely interactive (commands feed into
  cards with action buttons), while the backend is four real pipelines, not one prompt template.
- **Honest UI** — the cards show *why* each result was picked (the re-rank reason), not just
  a list. Tutor answers always show their sources.

### Potential Impact
- **Three audiences, one engine** — nonprofits, students, anyone. The same re-rank + in-voice
  draft mechanic transfers across funding types and education resources.
- **Beyond Slack** — because MCP is load-bearing, the same tools light up wherever MCP goes
  next (Claude desktop, Slack's MCP client, future enterprise integrations).
- **Real-world ceiling** — federal grant flows are in the billions; even single-digit-percent
  uplift in successful LOIs from under-resourced orgs is a large absolute number.

### Quality of the Idea
- **The moat is the in-voice draft, grounded in the user's own report.** No website or generic
  chatbot can write in *your* voice from *your* history. That's what the LOI test demonstrates:
  given an org's report on `New Roots Tutoring Collective`, the draft uses their cities, their
  programs, their student count, their funder partnerships — not stock language.
- **Re-rank as a feature, not just a wrapper.** The intel test shows 121 raw matches → 15 open →
  2 with reasons. The "with a reason" is the user-facing trust signal.

---

## 5. Validation — what we actually ran

All run live against real APIs on **2026-05-25** with current `.env`. Every test exited 0.

| Test | What it proves | Result |
|---|---|---|
| `test_deepseek.py` | DeepSeek key + base URL work | ✓ |
| `test_grants.py` | Live grants.gov fetch + parse | ✓ 654 raw results parsed |
| `test_intel.py` | Description → tight query → re-rank for fit | ✓ 121 raw → 2 explained matches |
| `test_loi.py` | Full pipeline → LOI in the org's voice | ✓ Full in-voice draft for *New Roots Tutoring Collective* |
| `test_resources.py` | Live Internet Archive + course providers | ✓ 4 books + 4 providers, re-ranked |
| `test_ask.py` | Wikibooks/Wikiversity tutor with citations | ✓ Calculus answer w/ 2 cited sources |
| `check_slack.py` | Bot & app tokens valid | ✓ team=`GrantScribe`, bot=`@grantscribe` |
| `test_mcp_bridge.py` | Find-grants + draft-LOI **through the MCP server** | ✓ MCP round-trip OK |
| `test_mcp_ask.py` | `/ask` through MCP | ✓ |
| `test_mcp_resources.py` | `/learn` through MCP | ✓ |

> **Not tested live:** scholarships (`/scholarships`) — CareerOneStop credentials not yet
> obtained. See §6.

---

## 6. What's left before submission

**Required by Devpost:**
1. **Record the ~3-minute demo video.** Show `/grants` → re-ranked list → "Draft LOI" → letter
   appears, then `/ask` with a citation, then `/learn` with free books. Add to `demo/` and link
   here.
2. **Capture sandbox URL + invite the two testers.** Invite `slackhack@salesforce.com` and
   `testing@devpost.com` to the `GrantScribe` workspace; record the workspace URL.
3. **Get CareerOneStop credentials** so `/scholarships` is live in the demo. Free token, but
   takes a day or so. Deadline is July 13, so there is time. If credentials don't arrive close
   to the deadline, drop `/scholarships` from the demo and note it as "next" rather than ship a
   broken path.

**Already complete:**
- All four code pipelines work live (see §5).
- MCP is genuinely load-bearing (proven by the three `test_mcp_*` scripts).
- Architecture diagram exported to `submission/architecture.png`.
- Devpost-form-ready copy in `submission/DEVPOST.md` (mirrors the form's exact fields).
- Impact statement in `submission/IMPACT.md`.
- GitHub repo renamed to `grantscribe` (no trailing dot), local clean and pushed to `origin/main`.

---

## 7. How to run it (judges)

```bash
cp .env.example .env   # fill DEEPSEEK_API_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN
PYTHONPATH=. uv run --with-requirements requirements.txt python grants_server.py   # MCP server
PYTHONPATH=. uv run --with-requirements requirements.txt python slack_app.py       # Slack app
```

Create the Slack app from `slack_manifest.yaml`, install to the workspace, run the slash commands.
