# GrantScribe
**Tagline:** Removing the money barrier to opportunity — inside Slack.

*This file mirrors the Devpost submission form fields — paste each section into its matching
text area on the form.*

## Inspiration
The money for opportunity already exists — billions in federal grants, thousands of scholarships,
and a world of free, high-quality learning. The barrier isn't *availability*; it's *access*. The
organizations and people who need it most are the least equipped to get it: a small nonprofit with
no grant-writer, a first-gen student with no counselor, a parent who can't afford tutoring. Finding
what you qualify for is hard, and the blank-page application is intimidating — so people don't
apply, and opportunity flows to whoever already has the staff and the know-how. We wanted the
agent to do the two things the under-resourced can't do for themselves: **the searching and the
first draft.**

## What it does
GrantScribe meets people where they already work — Slack:

- **`/grants`** (nonprofits) — finds the open federal grants you qualify for and **drafts the
  Letter of Intent in your organization's own voice**, grounded in your past reports.
- **`/scholarships`** (students) — finds matching scholarships and drafts the application essay in
  the student's voice. *(Same engine, U.S. DOL CareerOneStop data.)*
- **`/learn`** (anyone) — surfaces free, **level-matched** textbooks and courses (Internet Archive,
  OpenStax, MIT OpenCourseWare, Khan Academy).
- **`/ask`** — a free **tutor** that answers your question **from open textbooks, with citations**
  (Wikibooks / Wikiversity) — never invented facts.

**Why it's smarter than the source websites.** Raw grants.gov / archive keyword search returns
hundreds of loosely-matched, often expired or wrong-level results. GrantScribe's value is the
pipeline around them: **messy plain-language request → tight query → drop expired → re-rank for
genuine fit (with a reason) → draft the application in your own voice.** That last step —
grounded in your own history — is the moat: no website or generic tool can write in *your* voice
from *your* report.

**Impact (Slack Agent for Good).** GrantScribe turns *"I don't have a grant-writer / counselor /
money for tutoring"* into *"here's what you qualify for, and here's the application — in your
words."* Each funded grant is a program that runs, each scholarship a student enrolled, each free
resource a barrier removed — distributing opportunity to the people the current system overlooks.

## How we built it
- **Slack agent** — Bolt (Python), Socket Mode, slash commands + Block Kit cards + action buttons.
- **MCP server (load-bearing)** — a Model Context Protocol server exposes the capabilities
  (`find_grants`, `draft_loi`, `find_resources`, `answer_question`) as tools. The Slack app is an
  **MCP client** — every action travels Slack → MCP bridge → MCP server → tool. Any MCP client
  (Claude desktop, Slack's own MCP client, MCP Inspector) can reuse the same tools unchanged.
- **DeepSeek V4** — Flash for query extraction + re-ranking, Pro for drafting in-voice.
- **Live, free data** — grants.gov, CareerOneStop, Internet Archive, Wikibooks/Wikiversity.
- **Principles, enforced in code** — no fabricated data, grounded + cited answers, no hallucinated
  grant IDs, no silent fallbacks (MCP tool errors raise, they don't get swallowed); secrets stay
  in a git-ignored `.env`.

## Challenges we ran into
- **grants.gov keyword search is blunt** — a literal query returned 654 loosely-matched, often
  expired results. An LLM re-rank with explicit "why this fits" reduces that to the 2–3 grants
  that actually apply.
- **The model fabricated a grant opportunity number once.** Fix: we now let it reference grants by
  title and agency only, and never emit IDs in the draft. Honest beats fluent.
- **Making MCP genuinely load-bearing** (not bolted on). The temptation was to `import` the tool
  functions directly from the Slack app; we routed everything through the MCP server instead, so
  the same tools light up wherever MCP goes next.

## Accomplishments that we're proud of
- **An end-to-end pipeline that works on real data, today.** Live tests against grants.gov,
  Internet Archive, Wikibooks, and DeepSeek all pass — the LOI test produces a fully-fledged
  Letter of Intent in the org's own voice, grounded in its actual past report.
- **MCP is the spine, not a sticker.** The three `test_mcp_*` scripts prove the Slack app calls
  every capability through the MCP server. Remove the MCP server and the agent stops working.
- **Three audiences, one engine.** The same re-rank + in-voice draft mechanic transfers across
  funding types (grants, scholarships) and the learn/ask pillars — that's the scalable shape, not
  four bespoke prompts.

## What we learned
- **Re-rank-with-a-reason is the user-facing trust signal** — showing *why* a match was picked
  beats showing more matches.
- **The voice is the moat, not the search.** Anyone can wrap grants.gov; nobody else can write a
  Letter of Intent in your organization's voice from your own report.
- **MCP makes capabilities portable.** The same tools we built for Slack are usable from any
  MCP client unchanged.

## What's next for GrantScribe
Full scholarship rollout (CareerOneStop token in hand), a guided "next steps to apply" checklist
after each draft, and more open-learning sources. Beyond Slack, the MCP server already works
with any MCP-aware client.

## Built with
`python` · `slack-bolt` · `model-context-protocol` · `deepseek` · `grants.gov` · `careeronestop` ·
`internet-archive` · `wikibooks` · `socket-mode`
