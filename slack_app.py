"""GrantScribe — Slack front-end (Bolt, Socket Mode).

Flow:
  /setreport                    -> opens a modal; user pastes their org's report.
                                   Stored per (workspace, user) in state/org_reports.json.
  /grants <what your org does>  -> find_grants -> Block Kit cards (each: grant title,
                                   agency, due date, fit score, why it fits, "Draft LOI" button)
  "Draft LOI" button            -> draft_loi grounded in THIS user's stored report (not a fixture)
                                   -> posts the letter, opens with the verbatim grants.gov RE: line
                                   and the real submission deadline.

Socket Mode = no public URL needed; runs from a laptop against the sandbox.
No silent fallbacks: handler errors surface to the user AND re-raise to the logs.
No hardcoded fixtures: if the user hasn't run /setreport, the agent refuses to draft
a generic letter and tells them to set their report first. The moat (your voice from
your report) is shipped in code, not asserted in copy.
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
from report_store import get_report, set_report

load_dotenv(Path(__file__).with_name(".env"))


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
                    "value": json.dumps({
                        "title": grant["title"],
                        "agency": grant["agency"],
                        "opportunity_number": grant["opportunity_number"],
                        "url": grant["url"],
                        "close_date": grant.get("close_date", ""),
                    }),
                }
            ],
        },
        {"type": "divider"},
    ]


def _setreport_modal_view() -> dict:
    return {
        "type": "modal",
        "callback_id": "setreport_modal",
        "title": {"type": "plain_text", "text": "Set your org report"},
        "submit": {"type": "plain_text", "text": "Save"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "Paste any prior grant report, annual report, or program write-up from your "
                        "organization. GrantScribe uses it to draft Letters of Intent *in your org's "
                        "own voice* — your cities, programs, populations, partners, and numbers — "
                        "with hallucination forbidden in code.\n\n"
                        "Stays private to your workspace. You can re-run `/setreport` any time to update it."
                    ),
                },
            },
            {
                "type": "input",
                "block_id": "report_block",
                "label": {"type": "plain_text", "text": "Org report (paste anything)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "report_text",
                    "multiline": True,
                    "min_length": 200,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g. 'New Roots Tutoring Collective is a Columbus, Ohio nonprofit founded in 2019...'",
                    },
                },
            },
        ],
    }


@app.command("/setreport")
def handle_setreport(ack, command, client):
    text = (command.get("text") or "").strip()
    if text:
        # Inline form: `/setreport <paste text>` — useful for the CLI/test path.
        set_report(command["team_id"], command["user_id"], text)
        ack(
            f":white_check_mark: Saved your org report ({len(text)} chars). "
            "Now run `/grants <what your org does and what you need>`."
        )
        return

    ack()
    client.views_open(trigger_id=command["trigger_id"], view=_setreport_modal_view())


@app.view("setreport_modal")
def handle_setreport_submit(ack, view, body, client):
    report = (view["state"]["values"]["report_block"]["report_text"]["value"] or "").strip()
    if not report:
        ack(response_action="errors", errors={"report_block": "Paste your org's report first."})
        return
    team_id = body["team"]["id"]
    user_id = body["user"]["id"]
    set_report(team_id, user_id, report)
    ack()
    # DM the user a confirmation since modals don't post into channels.
    client.chat_postMessage(
        channel=user_id,
        text=(
            f":white_check_mark: Saved your org report ({len(report)} chars). "
            "Run `/grants <what your org does and what you need>` and click Draft LOI on any result — "
            "the letter will be in your org's voice, grounded in what you just pasted."
        ),
    )


def _no_report_message() -> str:
    return (
        ":wave: Before I can draft an LOI *in your org's voice*, I need a sample of how you write. "
        "Run `/setreport` once (paste any prior grant report, annual report, or program write-up — "
        "it stays in your workspace), then come back and re-run this command. "
        "No fixtures, no fictional fallback."
    )


@app.command("/grants")
def handle_grants(ack, command, respond):
    ack()
    description = (command.get("text") or "").strip()
    if not description:
        respond(
            "Tell me what your organization does — e.g. "
            "`/grants youth refugee tutoring in Ohio, need operating funds`"
        )
        return

    if not get_report(command["team_id"], command["user_id"]):
        respond(_no_report_message())
        return

    respond(f"🔍 Searching open federal grants for: _{description}_ …")
    try:
        result = find_grants(description, rows=15, top=3)
    except Exception as exc:  # surface, don't swallow
        respond(f":warning: Grant search failed: `{exc}`")
        raise

    if not result["grants"]:
        respond(
            f"No clearly-relevant open grants (searched {result['raw_count']} "
            f"for `{result['query']}`). Try describing the work differently."
        )
        return

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":dart: *{len(result['grants'])} grants that fit* — "
                    f"narrowed from {result['raw_count']} matches on `{result['query']}`:"
                ),
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
    team_id = body["team"]["id"]
    user_id = body["user"]["id"]
    report = get_report(team_id, user_id)
    if not report:
        respond(":warning: Run `/setreport` first to set your org's voice/context.")
        return

    respond(f":writing_hand: Drafting a Letter of Intent for *{grant['title']}* in your org's voice …")
    try:
        letter = draft_loi(grant, report)
    except Exception as exc:
        respond(f":warning: LOI draft failed: `{exc}`")
        raise

    header = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*Letter of Intent — {grant['title']}*"},
    }
    respond(blocks=[header, *_chunk_sections(letter)], text="Letter of Intent draft")


@app.command("/learn")
def handle_learn(ack, command, respond):
    ack()
    goal = (command.get("text") or "").strip()
    if not goal:
        respond(
            "Tell me what you want to learn — e.g. `/learn free ways to study high school algebra`"
        )
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
        books = "\n".join(
            f"• *<{b['url']}|{b['title']}>* — {b.get('note', '')}" for b in result["books"]
        )
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
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*📖 {question}*\n\n{answer[:2800]}"}}
    ]
    if result.get("sources"):
        src = "\n".join(f"• <{s['url']}|{s['site']}: {s['title']}>" for s in result["sources"])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"_Sources (free open textbooks):_\n{src}"}})
    respond(blocks=blocks, text="Tutor answer")


@app.command("/scholarships")
def handle_scholarships(ack, command, respond):
    """Placeholder until CareerOneStop credentials are wired.

    Registered in the manifest so the three-professionals merge is truthful at the command level;
    when CAREERONESTOP_USERID + CAREERONESTOP_TOKEN are in .env, this handler will delegate to the
    same engine the LOI drafter uses.
    """
    ack()
    co_userid = os.environ.get("CAREERONESTOP_USERID", "").strip()
    co_token = os.environ.get("CAREERONESTOP_TOKEN", "").strip()
    if not (co_userid and co_token):
        respond(
            ":hourglass_flowing_sand: `/scholarships` (the college-counselor pillar) is the same engine "
            "as `/grants`, pointed at the U.S. Department of Labor's CareerOneStop scholarship database. "
            "It needs `CAREERONESTOP_USERID` and `CAREERONESTOP_TOKEN` in `.env` — free at "
            "<https://www.careeronestop.org/Developers/WebAPI/registration.aspx|careeronestop.org/Developers>. "
            "Once those are set, this command will draft your essay in your own voice the same way `/grants` "
            "drafts the LOI."
        )
        return
    respond(":warning: Live scholarship flow not yet wired. Credentials present but engine not connected.")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
