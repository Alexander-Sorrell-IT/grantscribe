# GrantScribe
**Removing the money barrier to opportunity — inside Slack.**

## The problem
The money for opportunity already exists — billions in federal grants, thousands of scholarships,
and a world of free, high-quality learning. The barrier isn't *availability*; it's *access*. The
organizations and people who need it most are the least equipped to get it: a small nonprofit with
no grant-writer, a first-gen student with no counselor, a parent who can't afford tutoring. Finding
what you qualify for is hard, and the blank-page application is intimidating — so people don't apply,
and opportunity flows to whoever already has the staff and the know-how.

## What it does
GrantScribe meets people where they already work — Slack — and does the two things under-resourced
people can't do for themselves: **the searching and the first draft.**

- **`/grants`** (nonprofits) — finds the open federal grants you qualify for and **drafts the Letter
  of Intent in your organization's own voice**, grounded in your past reports.
- **`/scholarships`** (students) — finds matching scholarships and drafts the application essay in
  the student's voice. *(Same engine, U.S. DOL CareerOneStop data.)*
- **`/learn`** (anyone) — surfaces free, **level-matched** textbooks and courses (Internet Archive,
  OpenStax, MIT OpenCourseWare, Khan Academy).
- **`/ask`** — a free **tutor** that answers your question **from open textbooks, with citations**
  (Wikibooks / Wikiversity) — never invented facts.

## Why it's smarter than the source websites
Raw grants.gov / archive keyword search returns hundreds of loosely-matched, often expired or
wrong-level results. GrantScribe's value is the pipeline around them:
**messy plain-language request → tight query → drop expired → re-rank for genuine fit (with a
reason) → draft the application in your own voice.** That last step — grounded in your own history —
is the moat: no website or generic tool can write in *your* voice from *your* report.

## How we built it
- **Slack agent** — Bolt (Python), Socket Mode.
- **MCP server (load-bearing)** — a Model Context Protocol server exposes the capabilities
  (`find_grants`, `draft_loi`, `find_resources`, `answer_question`) as tools. The Slack app is an
  **MCP client** — every action travels Slack → MCP → tool. Any MCP client (Claude, Slack's own MCP
  client) can reuse the same tools.
- **DeepSeek V4** — Flash for query-extraction + re-ranking, Pro for drafting in-voice.
- **Live, free data** — grants.gov, CareerOneStop, Internet Archive, Wikibooks/Wikiversity.
- **Principles** — no fabricated data, grounded + cited answers, no hallucinated grant IDs, no silent
  fallbacks; secrets stay local.

## Impact (Slack Agent for Good)
GrantScribe levels access to opportunity. It turns *"I don't have a grant-writer / counselor / money
for tutoring"* into *"here's what you qualify for, and here's the application — in your words."* Each
funded grant is a program that runs, each scholarship a student enrolled, each free resource a
barrier removed — distributing opportunity to the people the current system overlooks.

## Challenges & what we learned
- grants.gov keyword search is blunt (654 junk matches) → an LLM re-rank turns it into the 2-3 that
  truly fit. Same lesson reused for the Internet Archive book results.
- Kept drafts honest: the model fabricated a grant opportunity number once → we now let it reference
  grants by title/agency only and never emit IDs.
- Made MCP genuinely load-bearing (the Slack app calls tools *through* the MCP server, not direct
  imports) rather than bolting it on.

## What's next
Full scholarship rollout, a guided "next steps to apply" checklist, and more open-learning sources.

## Built with
`python` · `slack-bolt` · `model-context-protocol` · `deepseek` · `grants.gov` · `careeronestop` ·
`internet-archive` · `wikibooks` · `socket-mode`
