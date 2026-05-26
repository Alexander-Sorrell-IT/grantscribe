# GrantScribe — Demo Video Script (~3 minutes)

Devpost wants ~3 minutes that **shows the working project**. This script is timed for ~2:55,
which leaves a few seconds of slack at the end so the cut feels deliberate.

`/scholarships` is omitted — CareerOneStop credentials aren't in `.env` yet. If you have them
by the recording date, see "Optional add-on" at the bottom.

---

## Pre-flight checklist (do this BEFORE you hit record)

1. `.env` filled: `DEEPSEEK_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` (CareerOneStop optional).
2. Two terminals open, both running:
   - `PYTHONPATH=. uv run --with-requirements requirements.txt python grants_server.py`
   - `PYTHONPATH=. uv run --with-requirements requirements.txt python slack_app.py`
3. Slack workspace `GrantScribe` open in your browser, **zoomed in 110–125%** so text reads on
   1080p. Use a clean channel (`#demo`) with no prior messages.
4. Close Slack notifications, DMs, and any other workspaces in the sidebar (visual noise).
5. Have `submission/architecture.png` open in a separate browser tab — you'll cut to it once.
6. Recorder: OBS or QuickTime, 1080p, 30fps, capture system audio + mic.

> **Honesty note:** the demo runs against **live** APIs (grants.gov, Internet Archive,
> Wikibooks, DeepSeek). Results will differ slightly from this script — that's fine and
> proves it isn't faked. Don't re-record because the grant titles changed.

---

## Scene-by-scene (voiceover + on-screen action)

### 0:00 – 0:15 · Hook (15s)
**On screen:** Cold open on the empty Slack channel. Cursor in the message box.
**Voiceover:**
> Small nonprofits don't have grant-writers. First-generation students don't have counselors.
> The money for opportunity is *there* — billions in federal grants, thousands of scholarships,
> free textbooks — but the searching and the blank-page application stop people from ever
> reaching it. GrantScribe is a Slack agent that does both for them.

---

### 0:15 – 1:25 · `/grants` + Draft LOI — the main act (70s)
**On screen — 0:15–0:20:** Type the command, hit enter:
```
/grants youth refugee tutoring and after-school program in Ohio — need operating funds for staff and supplies
```

**Voiceover (over the "🔍 Searching open federal grants for…" placeholder):**
> A nonprofit serving refugee youth in Ohio types what they actually do — no grant-writer
> jargon. Under the hood, GrantScribe rewrites that into a tight query, calls grants.gov,
> drops the expired listings, and uses DeepSeek to re-rank for genuine fit.

**On screen — 0:30:** The 3 grant cards appear. Pause and **slowly scroll past them** so the
viewer reads:
- The title (e.g., "Promise Neighborhoods 84.215N")
- The "fit 80/100" score
- The italicized **"why this fits"** reason
- The "✍️ Draft LOI" button

**Voiceover:**
> Notice it doesn't just dump 654 keyword matches. Three results, each with a fit score and
> *why* it fits — the trust signal raw search can't give you.

**On screen — 0:55:** Click the **✍️ Draft LOI** button on the top result. The
"✍️ Drafting a Letter of Intent…" placeholder appears.

**Voiceover:**
> One click. GrantScribe is grounded in *this organization's own annual report* — their cities,
> their student counts, their funder partnerships — and drafts a Letter of Intent **in the
> organization's voice.**

**On screen — 1:05:** The letter appears. **Scroll through it slowly** for ~15s. Linger on a
specific phrase from the org's actual report (e.g., "Northland, Hilltop, and Whitehall sites"
or "142 students") to make it obvious the letter is grounded in real history, not stock language.

**Voiceover (over the scroll):**
> This is the moat. No website or generic AI can write in *your* voice from *your* report. That
> first draft is the difference between an application that gets submitted and one that doesn't.

---

### 1:25 – 1:55 · `/ask` — the free tutor (30s)
**On screen:** Type and send:
```
/ask what is photosynthesis?
```

**Voiceover (over the placeholder):**
> The same engine powers a tutor for any kid whose family can't afford one. Ask anything —
> here, photosynthesis.

**On screen — 1:35:** Answer appears. **Highlight the "Sources" section at the bottom** with
the cursor — show the linked Wikibooks/Wikiversity URLs.

**Voiceover:**
> It only answers from open textbooks — Wikibooks and Wikiversity — and **every answer cites
> its sources.** It can't invent facts. That matters when a 12-year-old is using it for homework.

---

### 1:55 – 2:15 · `/learn` — free books at the right level (20s)
**On screen:** Type and send:
```
/learn I'm a parent who can't afford tutoring — free ways to learn high school algebra
```

**Voiceover (over the placeholder):**
> Same shape for free learning. A parent asks for help with high school algebra…

**On screen — 2:05:** Results appear (4 free books from Internet Archive + 4 curated course
providers — OpenStax, MIT OCW, Khan, freeCodeCamp). Scroll briefly so all are visible.

**Voiceover:**
> Four free books from the Internet Archive, level-matched and re-ranked for fit, plus the
> curated free-course providers. No paywalls.

---

### 2:15 – 2:35 · MCP is load-bearing (20s)
**On screen:** Cut to the **architecture diagram** (`submission/architecture.png`) full-screen.

**Voiceover:**
> One thing under the hood. The Slack app is an **MCP client** — every capability lives in an
> MCP server. Slash command, MCP bridge, MCP server, tool. The same tools light up unchanged
> from Claude desktop, from Slack's own MCP client, from any future MCP-aware surface. MCP
> isn't a sticker on this project; it's the spine.

---

### 2:35 – 2:55 · Close (20s)
**On screen:** Cut back to Slack. Optional final card: a still image with the tagline + repo URL.

**Voiceover:**
> The barrier to opportunity has never been availability — it's been access. GrantScribe puts
> the grants, the scholarships, the textbooks, and the first draft of the application **inside
> the place people already work.** Built for the Slack Agent Builder Challenge — Agent for Good.

---

## Exact slash-command inputs (copy-paste these)

```
/grants youth refugee tutoring and after-school program in Ohio — need operating funds for staff and supplies
/ask what is photosynthesis?
/learn I'm a parent who can't afford tutoring — free ways to learn high school algebra
```

These match the inputs used in `test_intel.py`, `test_mcp_ask.py`, and `test_resources.py`, so we
already know they return strong, real results.

---

## Optional add-on — if CareerOneStop tokens are filled before recording

Insert a 20s `/scholarships` segment between `/grants` and `/ask`. Trim the architecture or
close scene by 20s to keep the total under 3:00.

```
/scholarships first-generation student in Texas, intended engineering major, household income under 40k
```

---

## Post-production checklist
- Add captions / subtitles (some judges watch muted).
- Lower-third text for each scene tag (`/grants`, `/ask`, `/learn`).
- Mute or trim any system notification sounds.
- Export 1080p MP4, ≤ ~150 MB so it uploads quickly to Devpost.
- Drop the file in `demo/` (e.g., `demo/grantscribe-demo.mp4`).
