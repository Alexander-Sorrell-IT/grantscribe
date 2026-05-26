# GrantScribe

**You describe what you do. The Letter of Intent appears, in your voice, ready to submit.**

A Slack agent that finds the funding and free learning you qualify for, then **drafts the application in your own voice — and refuses to ship a draft that isn't actually submittable.** The grant-writer, the college counselor, and the tutor — three people the wealthy hire — inside one Slack channel.

Built for the Slack Agent Builder Challenge (Slack Agent for Good).

## What it does

| Command | Who | What |
|---|---|---|
| `/setreport` | Anyone installing the agent | Paste any prior grant/annual report (modal, or inline). Stored privately per workspace. `/grants` refuses to draft without one — **no fixtures, no fictional fallback**. |
| `/grants <what you do>` | Nonprofits / intermediaries | Finds open federal grants that fit + drafts the LOI in your org's voice. The drafter raises `RuntimeError` if the verbatim opportunity number, URL, or deadline from grants.gov are missing from the letter. Submittable or it doesn't exist. |
| `/scholarships <about you>` | Students | Same drafting shape against U.S. DOL CareerOneStop. Manifest-registered; pending the free CareerOneStop token. |
| `/learn <a goal>` | Anyone | Free, level-matched textbooks (Internet Archive) + curated providers (OpenStax · MIT OCW · Khan · freeCodeCamp). |
| `/ask <a question>` | Anyone | A free tutor that answers from open textbooks (Wikibooks / Wikiversity) **with citations** — returns `null` rather than invent. |

## Why it works where a chatbot doesn't

Raw grants.gov / Archive keyword search returns hundreds of loosely-matched, often expired results. Pasting a report into a generic chatbot gets you a fluent draft missing the real opportunity number. GrantScribe's value is the **pipeline + the refusal**:

> messy plain-language request → tight query → drop expired → **re-rank for genuine fit (with a reason on every card)** → draft in **your** voice from **your** report → **post-check verbatim grants.gov identifiers, or raise**.

The moat is two things, both shipped in code:
1. The user supplies the voice (`/setreport` → per-(workspace, user) store), so every workspace's drafts are grounded in that workspace's history — never in a fixture.
2. The drafter is structurally incapable of returning a non-submittable artifact (`loi_drafter.py` post-checks every verbatim grants.gov field).

## Architecture

`Slack (Bolt, Socket Mode)` → **MCP client (`mcp_bridge.py`)** → **MCP server (`grants_server.py`)** → `DeepSeek V4` + live free data (`grants.gov` · `CareerOneStop` · `Internet Archive` · `Wikibooks/Wikiversity`).

MCP is **load-bearing** — and observable: two distinct MCP clients call the same server today. The Slack app's bridge in production, and `demo/mcp_client.py` (a standalone CLI with no imports from `grantscribe`) for portability proof. Any MCP-aware surface (Claude desktop, Slack's own MCP client) can reuse the tools unchanged. Full diagram: [`submission/architecture.png`](submission/architecture.png) (Mermaid source in [`submission/ARCHITECTURE.md`](submission/ARCHITECTURE.md)).

## Tech

Python · `slack-bolt` · Model Context Protocol (FastMCP) · DeepSeek V4 (Flash for extraction/ranking, Pro for drafting) · grants.gov · CareerOneStop · Internet Archive · Wikibooks/Wikiversity.

## Run it

1. `cp .env.example .env` and fill `DEEPSEEK_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` (CareerOneStop optional).
2. Start the MCP server:
   `PYTHONPATH=. uv run --with-requirements requirements.txt python grants_server.py`
3. Start the Slack app:
   `PYTHONPATH=. uv run --with-requirements requirements.txt python slack_app.py`
4. Create (or update) the Slack app from `slack_manifest.yaml`, install it to your workspace.
5. In any channel: `/setreport` to seed the voice (paste any prior report). Then `/grants <what your org does>` and click ✍️ Draft LOI on a result.

To exercise the same MCP tools from a separate process (the portability demonstration):

```
python demo/mcp_client.py list
python demo/mcp_client.py find-grants "youth refugee tutoring Ohio"
python demo/mcp_client.py ask "what is photosynthesis?"
```

Secrets live in a git-ignored `.env`. Per-workspace org reports live in a git-ignored `state/`. Design principles: **no fabricated data, grounded + cited answers, no hallucinated IDs, no silent fallbacks, no fixture fallbacks.**

## For judges

Single entry point: [`SUBMISSION.md`](SUBMISSION.md). It maps every Devpost requirement to a file, self-assesses against the four judging criteria, and tracks remaining work.

**Audit the claims yourself:**

```
python verify.py
```

The script starts the MCP server, exercises every shipped claim from `SUBMISSION.md` §4 (the moat refuses, the post-check rejects bad drafts, the MCP server exposes the load-bearing tools, the tutor cites or refuses, the per-user report store isolates users), and prints PASS/FAIL per claim with file:line evidence. Exits 0 only if every claim is verified live. Last run: **9/9 PASS** on 2026-05-26.

## Impact

See [`submission/IMPACT.md`](submission/IMPACT.md). The U.S. high school class of 2024 left **$4.4 billion in Pell Grants on the table** because not applying was easier than applying. GrantScribe inverts that incentive — when describing what you do is easier than writing what you do, the application is the default, not the exception.
