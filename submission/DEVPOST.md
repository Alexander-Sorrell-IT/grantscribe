# GrantScribe
**Tagline:** Removing the money barrier to opportunity — inside Slack.

*This file mirrors the Devpost submission form fields — paste each section into its matching
text area on the form.*

## Inspiration
A grant-writer. A college counselor. A tutor. Three people the wealthy hire, three people the underserved can't afford — and the U.S. high school class of 2024 left **$4.4 billion in Pell Grants on the table** because 830,000 eligible students never finished the application (NCAN, 2025). The money was sitting there. **Not applying was easier than applying.**

So we stopped trying to build "a grants chatbot," and stopped writing copy about "helping people apply." We removed the act of applying.

## What it does
**GrantScribe is one Slack agent. You describe what you do. The Letter of Intent appears, in your voice, ready to submit.**

Run `/setreport` once and paste any prior grant report or annual report — that's the org's voice, stored privately per workspace. Then type `/grants youth refugee tutoring in Ohio — need operating funds`. Behind that one line: a tight grants.gov query, expired listings dropped, an LLM re-rank for true fit *with the reason shown on the card before you click anything*, and on one click, a Letter of Intent in **the organization's own voice** — grounded in their cities, programs, student counts, and partners lifted from the report you just pasted. The opportunity number, the grants.gov URL, and the submission deadline are copied verbatim from the live API. The drafter is forbidden in the prompt from inventing statistics or grant IDs — and `loi_drafter.py` **raises `RuntimeError` if the verbatim opportunity number, URL, or deadline aren't all present in the letter.** The artifact is submittable or it doesn't exist.

The same agent ships three other capabilities: `/scholarships` (the college-counselor pillar, pointed at U.S. DOL CareerOneStop — same drafting shape applied to scholarship essays, pending the free CareerOneStop token); `/learn` (free, level-matched textbooks from the Internet Archive plus curated providers — OpenStax, MIT OCW, Khan, freeCodeCamp); and `/ask` — a tutor that answers **only from Wikibooks and Wikiversity, always with citations**, and returns `null` rather than make a fact up.

Every capability is exposed through a load-bearing MCP server. Two distinct MCP clients call the same tools today — the Slack app's MCP bridge in production, and `demo/mcp_client.py` (a standalone CLI that doesn't import anything from the GrantScribe codebase, proving portability). Any MCP-aware surface that comes next — Claude desktop, Slack's own MCP client — works the same way.

The merge isn't *"three professionals in one agent."* That's the setup. The payoff is one level deeper: **the blank page was the barrier. We deleted the blank page** — and then we invented the **receipt**.

Every LOI now ships with a structured verification receipt appended to the letter: hashes of the live grants.gov payload at draft time, the org-report content hash, a timestamp, and a receipt ID. A funder runs `python verify_loi.py --letter received.txt --live` and the script re-fetches the grant from grants.gov, recomputes the canonical hash of the live payload, and confirms it matches the receipt. **Without the funder having to trust the sender.** Tampering with any trust-relevant field breaks the hash. We didn't just build a grants chatbot — we invented **verifiable application infrastructure**. After this, every grant submitted via an AI tool needs verification metadata, and we shipped the first one.

## How we built it
- **Slack agent** — Bolt (Python), Socket Mode, slash commands + Block Kit cards + action buttons + a paste-your-report modal (`/setreport`).
- **MCP server, load-bearing in code** — `grants_server.py` exposes `find_grants`, `draft_loi`, `find_resources`, `answer_question` as MCP tools. Two distinct clients call them today: the Slack app via `mcp_bridge.py`, and a standalone CLI at `demo/mcp_client.py` that has zero imports from the GrantScribe codebase. Portability is demonstrated, not promised.
- **Three engine shapes under four commands, honest version** — two retrieval pipelines share an *extract → fetch → JSON-rerank-with-reason* shape (`grant_intel`, `resources`); one drafter is single-shot generation + verbatim post-check (`loi_drafter`); one grounded tutor does multi-source MediaWiki retrieval + cited single answer (`ask`).
- **Per-(workspace, user) report store** — `/setreport` opens a modal, writes to `state/org_reports.json` (git-ignored). `/grants` refuses to draft if the user hasn't set a report. No fixtures, no fictional fallback.
- **DeepSeek V4** — Flash for query extraction + re-ranking; Pro for drafting in voice.
- **Live, free data** — grants.gov, CareerOneStop (pending free token), Internet Archive, Wikibooks/Wikiversity.
- **Principles, enforced in code** — no fabricated data, grounded + cited answers, no hallucinated grant IDs, no silent fallbacks (MCP tool errors raise; LOI post-check raises if any verbatim identifier is missing); secrets stay in a git-ignored `.env`; private user content stays in a git-ignored `state/`.

## Challenges we ran into
- **grants.gov keyword search is blunt** — a literal query returns 654 loosely-matched, often expired results. An LLM re-rank with explicit "why this fits" reduces that to the 2–3 grants that actually apply.
- **The model fabricated a grant opportunity number once.** First fix was the wrong shape: we forbade the model from including any opportunity number at all. That made the LOI *unsubmittable* — the small nonprofit still had to look up the number themselves, in exactly the place we said we removed friction. **Final fix:** the opportunity number, URL, and deadline come *verbatim* from the grants.gov API into the prompt, and `loi_drafter.py` *post-checks* that all three appear in the output. Missing any → `RuntimeError`. Honest beats fluent — and submittable beats both.
- **The moat we kept pitching was unshipped.** Earlier the Slack app hardcoded the org report to a sample fixture, so every workspace would have drafted every LOI from the same fictional Ohio nonprofit. A round of adversarial review caught it before submission. **Fix:** `/setreport` (modal + per-workspace store), `/grants` refuses to draft without one. The moat is now in code.
- **Making MCP genuinely load-bearing.** The temptation was to `import` the tool functions directly from the Slack app. Instead the Slack app calls the MCP server over streamable-HTTP via `mcp_bridge.py`; and `demo/mcp_client.py` exercises the same server from a completely separate process with no shared imports, demonstrating that any MCP client can reuse the tools unchanged.

## Accomplishments that we're proud of
- **We invented verifiable application infrastructure.** Every LOI ships with a structured receipt that a funder can re-verify back to live grants.gov data with one command (`verify_loi.py`). No other LLM-based grant tool does this. After this, every funder will require it.
- **A submittable artifact, not a chatbot transcript.** `loi_drafter.py`'s post-check refuses to return a draft missing the verbatim opportunity number, URL, or deadline. Other LLM tools fail open; this one fails loud. That's the Reshaping Principle in five lines of Python.
- **The moat is in code, not in copy.** `/setreport` ships the voice-from-the-user's-own-report mechanism end-to-end. No fixtures. No fictional fallback Ohio nonprofit. The thing the pitch promises is the thing the code does.
- **The submission is itself auditable.** `python verify.py` exercises 12 shipped claims live (including the receipt round-trip, the tampering detection, and the live grants.gov re-fetch). 12/12 PASS. Judges don't have to trust the submission — they can run it.
- **MCP earned its keep.** Two distinct MCP clients call the same tools — the Slack bridge in production and a standalone CLI with no internal imports. Portability is observable.

## What we learned
- **Re-rank-with-a-reason is the user-facing trust signal** — showing *why* a match was picked beats showing more matches.
- **Refusing to ship beats shipping nicely.** The version of the LOI that hallucinated a grant opportunity number looked fluent and was wrong. The version that raises a `RuntimeError` if any grants.gov identifier is missing is honest. Honest beats fluent.
- **The moat survives a skeptic only if it lives in code.** "Writes in your voice" was a billboard until `/setreport` shipped. Now it's a feature.
- **MCP makes capabilities portable, demonstrably.** The same tools we built for Slack are usable from a separate process with no shared imports.

## What's next for GrantScribe
Full scholarship rollout (CareerOneStop token in hand), a guided "next steps to apply" checklist
after each draft, and more open-learning sources. Beyond Slack, the MCP server already works
with any MCP-aware client.

## Built with
`python` · `slack-bolt` · `model-context-protocol` · `deepseek` · `grants.gov` · `careeronestop` ·
`internet-archive` · `wikibooks` · `socket-mode`
