# GrantScribe — Demo Video Script (~3 minutes)

Devpost wants ~3 minutes that **shows the working project**. This script is timed for ~2:55. The
demo is built around the single sentence the product delivers: **"You describe what you do. The
Letter of Intent appears, in your voice, ready to submit."** Every scene either sets up that
sentence or pays it off.

`/scholarships` is mentioned, not demoed — CareerOneStop credentials are pending. `/learn` is also
intentionally cut from the main act to keep the judge's "one thing they remember next week" sharp.
The two visible capabilities are `/grants → Draft LOI` (the main act) and `/ask` (proof that the
same engine writes the tutor with citations).

---

## Pre-flight checklist (do this BEFORE you hit record)

1. `.env` filled: `DEEPSEEK_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` (CareerOneStop optional).
2. **Three things running, in three terminals / windows:**
   - `PYTHONPATH=. uv run --with-requirements requirements.txt python grants_server.py`
   - `PYTHONPATH=. uv run --with-requirements requirements.txt python slack_app.py`
   - A spare terminal positioned next to the Slack window, ready to type the `demo/mcp_client.py` command.
3. Slack workspace `GrantScribe` open in a browser, **zoomed 110–125%**. Use a clean channel
   (`#demo`) with no prior messages. Close DMs and other workspaces in the sidebar.
4. **Wipe any prior org report** — delete `state/org_reports.json` before recording so the
   `/setreport` step shows the real first-time flow.
5. Have the org report ready to paste — `sample_data/org_report.md` is the staged example (the
   "New Roots Tutoring Collective" annual report). The script below assumes that's what you paste.
6. Have `submission/architecture.png` open in a separate browser tab — you'll cut to it once.
7. Recorder: OBS or QuickTime, 1080p, 30fps, capture system audio + mic.

> **Honesty note:** the demo runs against **live** APIs (grants.gov, Wikibooks, DeepSeek).
> Results will differ slightly between takes — that's fine and proves it isn't faked. Don't
> re-record because the top grant changed.

---

## Scene-by-scene (voiceover + on-screen action)

### 0:00 – 0:15 · Hook (15s)
**On screen:** Cold open on the empty Slack channel. Cursor blinking in the message box. No music.

**Voiceover:**
> The U.S. high school class of 2024 left **four-point-four billion dollars** in Pell Grants
> on the table — because not applying was easier than applying.
>
> *(beat — cursor still blinking)*
>
> GrantScribe inverts that. **You describe what you do. The Letter of Intent appears, in your
> voice, ready to submit.**

---

### 0:15 – 0:40 · `/setreport` — the moat is shipped, on camera (25s)
**On screen — 0:15:** Type `/setreport` and press Enter. The Slack modal appears.

**Voiceover (over the modal opening):**
> First time: tell GrantScribe how your organization writes. Paste any prior grant report,
> annual report, or program write-up — it stays in your workspace, private.

**On screen — 0:22:** Paste a chunk of `sample_data/org_report.md` (~5–10 seconds of paste,
let the textarea scroll). Click **Save**. The modal closes; a DM confirmation appears: *"Saved
your org report (… chars). Run /grants…"*.

**Voiceover:**
> Now the agent knows the org's voice — its cities, its programs, its student counts, its
> partners. The moat isn't a marketing line. It's a stored file.

---

### 0:40 – 1:35 · `/grants` + Draft LOI — the main act (55s)
**On screen — 0:40:** Type the command, press Enter:
```
/grants youth refugee tutoring and after-school program in Ohio — need operating funds for staff and supplies
```

**Voiceover (over the "🔍 Searching open federal grants for…" placeholder):**
> A nonprofit serving refugee youth types what they actually do — no grant-writer jargon.
> Under the hood: a tight grants.gov query, expired listings dropped, DeepSeek re-ranking
> for genuine fit.

**On screen — 0:55:** The 3 grant cards appear. Pause and **slowly scroll past them** so the
viewer reads:
- The title (e.g., *"Promise Neighborhoods-84.215N"*)
- *"fit 80/100"*
- The italicized **"why this fits"** reason — **highlight this with the cursor**
- The *"✍️ Draft LOI"* button

**Voiceover:**
> Three results, each with a fit score and *why* it fits — shown on the card before the user
> clicks anything. That's the trust signal raw search can't give you.

**On screen — 1:10:** Click **✍️ Draft LOI** on the top card. The "✍️ Drafting…" placeholder
appears, then the letter resolves.

**Voiceover (over the placeholder):**
> One click. The letter is grounded in the report you just pasted, the opportunity number and
> URL come verbatim from the live grants.gov API, and the function literally **refuses to return
> a draft that's missing the real identifiers.** Submittable or it doesn't exist.

**On screen — 1:20:** Letter appears. **Scroll slowly for ~15 seconds.** Land on three highlights
with the cursor in this order:
1. **First line:** `RE: <opportunity_number> — <title>` — the verbatim grants.gov ID.
2. **A specific phrase from the pasted report** — e.g. *"Northland, Hilltop, and Whitehall sites"*
   or *"142 students"* — proves it's the org's own facts.
3. **Bottom of the letter:** `Submission deadline: <close_date>` — verbatim from the API.

**Voiceover (over the scroll):**
> That's the headline. You described what you do. The letter appeared, in your voice, ready
> to submit. The blank page was the barrier. We deleted the blank page.

---

### 1:35 – 2:00 · MCP from a second client — portability, on camera (25s)
**On screen:** Cut to the spare terminal next to Slack. Type and run:
```
python demo/mcp_client.py find-grants "youth refugee tutoring Ohio"
```

**Voiceover:**
> The same MCP tools, called from a completely separate process — no imports from the
> GrantScribe codebase. Same ranked grants, same opportunity numbers, same reasons. **MCP isn't
> a sticker. It's two proven clients today, with Claude desktop next.**

**On screen:** The terminal prints the ranked results with the verbatim RE: numbers visible.
Hold for ~5 seconds so the judge sees them.

---

### 2:00 – 2:25 · `/ask` — the tutor that cites or refuses (25s)
**On screen:** Back in Slack. Type and send:
```
/ask what is photosynthesis?
```

**Voiceover (over the placeholder):**
> The same agent — *"You describe what you want, the answer appears"* — is also the free tutor
> a kid uses for homework when there's no money for one.

**On screen — 2:10:** Answer appears. **Highlight the "Sources" section** with the cursor —
linked Wikibooks/Wikiversity URLs.

**Voiceover:**
> It answers only from open textbooks — Wikibooks and Wikiversity — and **every answer cites
> its sources.** No source page, no answer. It cannot invent a fact when a kid is doing homework.

---

### 2:25 – 2:45 · The pattern — one MCP server, four jobs (20s)
**On screen:** Cut to the architecture diagram (`submission/architecture.png`) full-screen.

**Voiceover:**
> One pattern under everything: extract the user's plain language into a tight query, pull
> from live free data, re-rank with a reason, draft in the user's voice — or, in the tutor's
> case, ground in cited sources and refuse to answer otherwise.
>
> Four user-facing capabilities. One MCP server. Two MCP clients calling it today. Honest tech,
> honest claims, honest code.

---

### 2:45 – 2:55 · Close (10s)
**On screen:** Cut back to Slack. Final still: tagline + repo URL.

**Voiceover:**
> A grant-writer. A college counselor. A tutor. Three people the wealthy hire — inside the
> place people already work.
>
> Built for the Slack Agent Builder Challenge. The application is no longer the barrier.

---

## Exact slash-command inputs (copy-paste these)

```
/setreport
   (paste sample_data/org_report.md into the modal, click Save)
/grants youth refugee tutoring and after-school program in Ohio — need operating funds for staff and supplies
/ask what is photosynthesis?
```

Terminal beat:
```
python demo/mcp_client.py find-grants "youth refugee tutoring Ohio"
```

These match the inputs already used in `test_loi.py`, `test_mcp_bridge.py`, and
`test_mcp_ask.py`, so we know they return strong, real results.

---

## Optional add-on — if CareerOneStop tokens arrive before recording

Insert a 20s `/scholarships` beat between the `/grants` LOI and the MCP-client beat, showing the
same drafting shape applied to a scholarship essay. Trim the architecture scene by 20s to keep
total under 3:00.

```
/scholarships first-generation student in Texas, intended engineering major, household income under $40k
```

---

## Post-production checklist
- Add captions / subtitles (some judges watch muted).
- Lower-third text for each scene tag (`/setreport`, `/grants`, `mcp_client`, `/ask`).
- Mute any system notification sounds.
- Export 1080p MP4, ≤ ~150 MB so it uploads quickly to Devpost.
- Drop the file in `demo/` (e.g., `demo/grantscribe-demo.mp4`).
