"""GrantScribe — Slack front-end (Bolt, Socket Mode).

Flow:
  /grants <what your org does>  -> find_grants -> Block Kit cards
       (each: grant title, agency, due date, fit score, why it fits, "Draft LOI" button)
  "Draft LOI" button            -> draft_loi (grounded in the org's report) -> posts the letter

Socket Mode = no public URL needed; runs from a laptop against the sandbox.
No silent fallbacks: handler errors surface to the user AND re-raise to the logs.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from mcp_bridge import (
    mcp_answer_question as ask_question,
    mcp_draft_loi as draft_loi,
    mcp_find_grants as find_grants,
    mcp_find_resources as find_resources,
)

load_dotenv(Path(__file__).with_name(".env"))

# Org context for the LOI voice. (v1: seeded sample; v2: pull from Slack via RTS.)
ORG_REPORT = (Path(__file__).parent / "sample_data" / "org_report.md").read_text()

app = App(token=os.environ["SLACK_BOT_TOKEN"])


def _chunk_sections(text: str, size: int = 2800) -> list[dict]:
    """Split long text into Block Kit section blocks (3000-char mrkdwn limit)."""
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": text[i : i + size]}}
        for i in range(0, len(text), size)
    ]


def _grant_card(grant: dict) -> list[dict]:
    due = grant["close_date"] or "rolling / unspecified"
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*<{grant['url']}|{grant['title']}>*\n"
                    f"_{grant['agency']}_  •  due *{due}*  •  fit *{grant['score']}/100*\n"
                    f"> {grant['reason']}"
                ),
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✍️  Draft LOI"},
                    "style": "primary",
                    "action_id": "draft_loi",
                    "value": json.dumps({"title": grant["title"], "agency": grant["agency"]}),
                }
            ],
        },
        {"type": "divider"},
    ]


@app.command("/grants")
def handle_grants(ack, command, respond):
    ack()
    description = (command.get("text") or "").strip()
    if not description:
        respond("Tell me what your organization does — e.g. "
                "`/grants youth refugee tutoring in Ohio, need operating funds`")
        return

    respond(f"🔍 Searching open federal grants for: _{description}_ …")
    try:
        result = find_grants(description, rows=15, top=3)
    except Exception as exc:  # surface, don't swallow
        respond(f":warning: Grant search failed: `{exc}`")
        raise

    if not result["grants"]:
        respond(f"No clearly-relevant open grants (searched {result['raw_count']} "
                f"for `{result['query']}`). Try describing the work differently.")
        return

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (f":dart: *{len(result['grants'])} grants that fit* — "
                         f"narrowed from {result['raw_count']} matches on `{result['query']}`:"),
            },
        },
        {"type": "divider"},
    ]
    for grant in result["grants"]:
        blocks.extend(_grant_card(grant))
    respond(blocks=blocks, text="Grant matches")


@app.action("draft_loi")
def handle_draft_loi(ack, body, respond):
    ack()
    grant = json.loads(body["actions"][0]["value"])
    respond(f":writing_hand: Drafting a Letter of Intent for *{grant['title']}* in your org's voice …")
    try:
        letter = draft_loi(grant, ORG_REPORT)
    except Exception as exc:
        respond(f":warning: LOI draft failed: `{exc}`")
        raise

    header = {"type": "section",
              "text": {"type": "mrkdwn", "text": f"*Letter of Intent — {grant['title']}*"}}
    respond(blocks=[header, *_chunk_sections(letter)], text="Letter of Intent draft")


@app.command("/learn")
def handle_learn(ack, command, respond):
    ack()
    goal = (command.get("text") or "").strip()
    if not goal:
        respond("Tell me what you want to learn — e.g. "
                "`/learn free ways to study high school algebra`")
        return

    respond(f"📚 Finding free ways to learn: _{goal}_ …")
    try:
        result = find_resources(goal)
    except Exception as exc:
        respond(f"⚠️ Resource search failed: `{exc}`")
        raise

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"📚 *Free ways to learn {result['topic']}*"}},
        {"type": "divider"},
    ]
    if result["books"]:
        books = "\n".join(f"• *<{b['url']}|{b['title']}>* — {b.get('note', '')}" for b in result["books"])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Free books:*\n{books}"}})
    courses = "\n".join(f"• <{c['url']}|{c['title']}>" for c in result["courses"])
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Free courses & textbooks:*\n{courses}"}})
    respond(blocks=blocks, text="Free learning resources")


@app.command("/ask")
def handle_ask(ack, command, respond):
    ack()
    question = (command.get("text") or "").strip()
    if not question:
        respond("Ask a learning question — e.g. `/ask what is a derivative in calculus?`")
        return

    respond(f"📖 Looking it up in free open textbooks: _{question}_ …")
    try:
        result = ask_question(question)
    except Exception as exc:
        respond(f"⚠️ Tutor failed: `{exc}`")
        raise

    answer = result.get("answer") or result.get("note") or "No answer found."
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": f"*📖 {question}*\n\n{answer[:2800]}"}}]
    if result.get("sources"):
        src = "\n".join(f"• <{s['url']}|{s['site']}: {s['title']}>" for s in result["sources"])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"_Sources (free open textbooks):_\n{src}"}})
    respond(blocks=blocks, text="Tutor answer")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
