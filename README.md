# GrantScribe

**Removing the money barrier to opportunity — inside Slack.**

GrantScribe is a Slack agent that finds the funding and free learning you qualify for — and drafts
the application **in your own voice**. It does the two things under-resourced people can't do for
themselves: **the searching and the first draft.**

Built for the Slack Agent Builder Challenge (Slack Agent for Good).

## What it does

| Command | Who | What |
|---|---|---|
| `/grants <what you do>` | Nonprofits | Finds open federal grants you qualify for + drafts the Letter of Intent in your org's voice |
| `/scholarships <about you>` | Students | Finds matching scholarships + drafts the essay in your voice *(U.S. DOL CareerOneStop)* |
| `/learn <a goal>` | Anyone | Free, level-matched textbooks (Internet Archive) + course links (OpenStax / MIT OCW / Khan) |
| `/ask <a question>` | Anyone | A free tutor that answers from open textbooks (Wikibooks / Wikiversity) — **with citations** |

## Why it's smarter than the source websites
Raw grants.gov / archive keyword search returns hundreds of loosely-matched, often expired or
wrong-level results. GrantScribe's value is the pipeline around them:

> messy plain-language request → tight query → drop expired → **re-rank for genuine fit (with a
> reason)** → **draft the application in your own voice**, grounded in your own history.

That last step is the moat: no website or generic tool can write in *your* voice from *your* report.

## Architecture
`Slack (Bolt, Socket Mode)` → **MCP client** → **MCP server** (capabilities as tools) →
`DeepSeek V4` + live free data (`grants.gov` · `CareerOneStop` · `Internet Archive` ·
`Wikibooks/Wikiversity`).

MCP is **load-bearing**: the Slack app calls every capability *through* the MCP server, so any MCP
client (Claude, Slack's own MCP client) can reuse the same tools. Full diagram:
[`submission/ARCHITECTURE.md`](submission/ARCHITECTURE.md).

## Tech
Python · `slack-bolt` · Model Context Protocol (FastMCP) · DeepSeek V4 (Flash for
extraction/ranking, Pro for drafting) · grants.gov · CareerOneStop · Internet Archive ·
Wikibooks/Wikiversity.

## Run it
1. `cp .env.example .env` and fill `DEEPSEEK_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`
   (and `CAREERONESTOP_USERID` / `CAREERONESTOP_TOKEN` for scholarships).
2. Start the MCP server:
   `PYTHONPATH=. uv run --with-requirements requirements.txt python grants_server.py`
3. Start the Slack app:
   `PYTHONPATH=. uv run --with-requirements requirements.txt python slack_app.py`
4. Create the Slack app from `slack_manifest.yaml`, install it to your workspace, and run the
   slash commands.

Secrets live in a git-ignored `.env`. Design principles: **no fabricated data, grounded + cited
answers, no hallucinated IDs, no silent fallbacks.**

## Impact
See [`submission/IMPACT.md`](submission/IMPACT.md) — GrantScribe levels access to opportunity for the
people the current system overlooks: each funded grant is a program that runs, each scholarship a
student enrolled, each free resource a barrier removed.
