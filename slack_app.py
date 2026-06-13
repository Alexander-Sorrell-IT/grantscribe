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
import re
from pathlib import Path

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from mcp_bridge import (
    mcp_answer_question as ask_question,
    mcp_draft_loi as draft_loi,
    mcp_find_grants as find_grants,
    mcp_find_resources as find_resources,
    mcp_find_training as find_training,
    mcp_build_pathway as build_pathway,
    mcp_draft_pathway_plan as draft_pathway_plan,
)
from report_store import get_report, set_report

load_dotenv(Path(__file__).with_name(".env"))


app = App(token=os.environ["SLACK_BOT_TOKEN"])


_LOCATION_RE = re.compile(r"^\d{5}$|^.+,\s*[A-Za-z]{2}$")  # ZIP or "City, ST"


def _split_near(text: str) -> tuple[str, str]:
    """Split `<keyword> near <location>` only when the suffix is a real location
    (ZIP or 'City, ST'). Otherwise the whole text is the keyword (nationwide) —
    so plain phrasing like 'nursing near downtown' isn't mangled into a bad query."""
    keyword, sep, loc = text.partition(" near ")
    loc = loc.strip()
    if sep and _LOCATION_RE.match(loc):
        return keyword.strip(), loc
    return text.strip(), "0"


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
                        "grounded in what you paste. The grant's number, URL, and deadline are "
                        "checked in code to appear verbatim, or the draft is refused.\n\n"
                        "*Applying as an individual?* Paste your own story instead — where you are, what "
                        "you're good at, what you're aiming for — and `/pathway` will draft your funding "
                        "plan in your voice.\n\n"
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


def _training_card(p: dict) -> str:
    where = ", ".join(x for x in (p["city"], p["state"]) if x)
    school = f"<{p['url']}|{p['school']}>" if p["url"] else (p["school"] or "—")
    cred = p["credential"] or p["award_level"] or "credential varies"
    meta = "  •  ".join(x for x in (cred, p["format"], where) if x)
    return f"• *{p['program'] or 'Program'}*\n  _{school}_  —  {meta}"


def _pathway_program_card(program: dict, goal_occupation: str) -> list[dict]:
    """A program card with a 'Draft my plan' button — produces a verifiable,
    in-voice funding plan anchored to THIS CareerOneStop program."""
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": _training_card(program)}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📝  Draft my plan"},
                    "style": "primary",
                    "action_id": "draft_pathway_plan",
                    "value": json.dumps({"program": program, "goal": goal_occupation}),
                }
            ],
        },
        {"type": "divider"},
    ]


@app.command("/training")
def handle_training(ack, command, respond):
    ack()
    text = (command.get("text") or "").strip()
    if not text:
        respond(
            "Tell me what you want to train for — e.g. "
            "`/training nursing` or `/training welding near 45241`"
        )
        return

    # Optional "near <ZIP or City, ST>" suffix narrows to programs you can reach.
    keyword, location = _split_near(text)

    respond(
        f"🎓 Finding real training programs for: _{keyword}_"
        + (f" near *{location}*" if location != "0" else "")
        + " …"
    )
    try:
        result = find_training(keyword, location=location, rows=5)
    except Exception as exc:  # surface, don't swallow
        respond(f":warning: Training search failed: `{exc}`")
        raise

    if not result["programs"]:
        respond(f"No training programs found for `{keyword}`. Try a broader term.")
        return

    listing = "\n".join(_training_card(p) for p in result["programs"])
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"🎓 *{len(result['programs'])} real training programs for "
                    f"{result['keyword']}* — {result['count']:,} in the database:"
                ),
            },
        },
        {"type": "divider"},
        *_chunk_sections(listing),
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Source: {result['source']} (U.S. Department of Labor)"}
            ],
        },
    ]
    respond(blocks=blocks, text="Training programs")


@app.command("/pathway")
def handle_pathway(ack, command, respond):
    ack()
    text = (command.get("text") or "").strip()
    if not text:
        respond(
            "Tell me the job you're aiming for — e.g. "
            "`/pathway registered nurse near 45241`"
        )
        return

    goal, location = _split_near(text)

    respond(
        f"🧭 Mapping your path to *{goal}*"
        + (f" near *{location}*" if location != "0" else "")
        + " …"
    )
    try:
        p = build_pathway(goal, location=location, rows=4)
    except Exception as exc:  # surface, don't swallow
        respond(f":warning: Pathway lookup failed: `{exc}`")
        raise

    if not p["occupation"] and not p["programs"]:
        respond(
            f"Couldn't find a clear occupation or training for `{goal}`. "
            "Try a common job title — e.g. `electrician`, `medical assistant`."
        )
        return

    occ = p["occupation"]
    job_line = (
        f"🎯 *{occ['title']}* — a real occupation (O*NET {occ['onet_code']}), "
        f"{p['occupation_matches']} related titles"
        if occ
        else f"🎯 *{p['goal']}*"
    )
    creds = ", ".join(p["credentials"]) or "varies by program"

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": job_line}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"🎓 *The credential you need:* {creds}"},
        },
    ]
    goal_occupation = f"{occ['title']} (O*NET {occ['onet_code']})" if occ else p["goal"]
    if p["programs"]:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🏫 *Where to get it* — {len(p['programs'])} real programs"
                        + (f" near {location}" if location != "0" else "")
                        + f" (of {p['program_count']:,}). Click *Draft my plan* on any one:"
                    ),
                },
            },
            {"type": "divider"},
        ])
        for pr in p["programs"]:
            blocks.extend(_pathway_program_card(pr, goal_occupation))
    blocks.append(
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Source: {p['source']} (U.S. Department of Labor)"}
            ],
        }
    )
    respond(blocks=blocks, text=f"Pathway to {goal}")


@app.action("draft_pathway_plan")
def handle_draft_pathway_plan(ack, body, respond):
    ack()
    payload = json.loads(body["actions"][0]["value"])
    program = payload["program"]
    goal = payload.get("goal", "")
    team_id = body["team"]["id"]
    user_id = body["user"]["id"]
    story = get_report(team_id, user_id)
    if not story:
        respond(
            ":warning: Before I can draft your plan *in your own voice*, run `/setreport` once and "
            "paste your story — where you are, what you're good at, what you're aiming for. "
            "It stays in your workspace. No fixtures, no fictional fallback."
        )
        return

    respond(
        f":writing_hand: Drafting your funding plan for *{program.get('program', 'this program')}* "
        f"at *{program.get('school', '')}* in your own voice …"
    )
    try:
        plan = draft_pathway_plan(program, story, goal_occupation=goal)
    except Exception as exc:  # surface, don't swallow
        respond(f":warning: Plan draft failed: `{exc}`")
        raise

    header = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Your funded-path plan — {program.get('program', '')} @ {program.get('school', '')}*",
        },
    }
    respond(blocks=[header, *_chunk_sections(plan)], text="Funded-path plan draft")


@app.command("/scholarships")
def handle_scholarships(ack, command, respond):
    """Placeholder until CareerOneStop credentials are wired.

    Honest empty-state. Verified 2026-06-05: CareerOneStop's developer API has NO
    scholarship service, and no free public scholarship API exists (others are
    paywalled or have no live host). Rather than fake a source, point users to the
    real, funded routes GrantScribe DOES deliver.
    """
    ack()
    respond(
        ":mag: *There's no honest scholarship search to give you yet.* We checked: "
        "CareerOneStop's developer API has no scholarship service, and no free public "
        "scholarship API exists. Rather than fake a database, here's what removes the "
        "money barrier *for real*:\n"
        "• `/pathway <job>` — the credential a job needs + real funded programs near you\n"
        "• `/training <skill>` — real accredited training programs (U.S. DOL CareerOneStop)\n"
        "• `/grants <what your org does>` — federal grants + an LOI drafted in your voice"
    )


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
