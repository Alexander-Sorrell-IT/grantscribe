"""Post the REAL GrantScribe demo conversation into #general as the bot, for recording.

Reads the real artifacts (/tmp/demo_summary.json, demo_loi.txt, demo_plan.txt) and
posts them as the actual bot via chat.postMessage — real Block Kit cards, real LOI,
real plan. User-prompt lines use username override so the convo reads naturally.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

import httpx

CH = "C0B5S2D91B7"  # #general
TOK = next(l.split("=", 1)[1].strip().strip('"') for l in (Path(__file__).parent.parent / ".env").read_text().splitlines() if l.startswith("SLACK_BOT_TOKEN"))
API = "https://slack.com/api"
H = {"Authorization": f"Bearer {TOK}", "Content-type": "application/json"}

summary = json.loads(Path("/tmp/demo_summary.json").read_text())
loi = Path("/tmp/demo_loi.txt").read_text()
plan = Path("/tmp/demo_plan.txt").read_text()


def call(method, **payload):
    r = httpx.post(f"{API}/{method}", headers=H, json=payload, timeout=30).json()
    if not r.get("ok"):
        print(f"  ! {method}: {r.get('error')}")
    return r


def clear_recent():
    """Delete the bot's own recent messages so the demo starts clean."""
    hist = call("conversations.history", channel=CH, limit=50)
    for m in hist.get("messages", []):
        if m.get("bot_id") or m.get("user") == hist.get("__bot__"):
            call("chat.delete", channel=CH, ts=m["ts"])
            time.sleep(0.3)


def user(text):
    call("chat.postMessage", channel=CH, text=text, username="Amara (New Roots Tutoring)",
         icon_emoji=":teacher:")
    time.sleep(1.2)


def bot(text=None, blocks=None):
    call("chat.postMessage", channel=CH, text=text or "GrantScribe", blocks=blocks)
    time.sleep(1.4)


def grant_blocks():
    blocks = [{"type": "section", "text": {"type": "mrkdwn",
              "text": ":dart: *3 grants that fit* — narrowed from hundreds of live grants.gov matches:"}},
              {"type": "divider"}]
    for g in summary["grants_all"]:
        due = g.get("close_date") or "rolling"
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f"*<{g['url']}|{g['title']}>*\n_{g['agency']}_  •  due *{due}*  •  fit *{g['score']}/100*\n> {g['reason']}"}})
        blocks.append({"type": "actions", "elements": [{"type": "button",
            "text": {"type": "plain_text", "text": "✍️  Draft LOI"}, "style": "primary", "action_id": "x"}]})
        blocks.append({"type": "divider"})
    return blocks


def pathway_blocks():
    occ = summary.get("occupation") or {}
    creds = ", ".join(summary.get("credentials") or []) or "varies"
    blocks = [{"type": "section", "text": {"type": "mrkdwn",
        "text": f":dart: *{occ.get('title','')}* (O*NET {occ.get('onet_code','')}) — a real occupation\n:mortar_board: *Credential you need:* {creds}\n:school: *Real funded programs near you:*"}},
        {"type": "divider"}]
    for p in summary["programs_all"]:
        where = ", ".join(x for x in (p["city"], p["state"]) if x)
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f"• *{p['program']}*\n  _{p['school']}_ — {p['credential'] or p['award_level']}  •  {p['format']}  •  {where}"}})
        blocks.append({"type": "actions", "elements": [{"type": "button",
            "text": {"type": "plain_text", "text": "📝  Draft my plan"}, "style": "primary", "action_id": "y"}]})
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "Source: U.S. DOL CareerOneStop"}]})
    return blocks


def main():
    print("clearing old bot messages…")
    clear_recent()
    print("posting demo conversation…")
    user("/grants youth refugee tutoring in Ohio, after-school literacy, need operating funds")
    bot(blocks=grant_blocks())
    user("*(clicks ✍️ Draft LOI)*")
    bot(text="*Letter of Intent — in your org's voice*\n" + loi)
    user("/pathway registered nurse near 45241")
    bot(blocks=pathway_blocks())
    user("*(clicks 📝 Draft my plan)*")
    bot(text="*Your funded-path plan — in your own voice*\n" + plan)
    print("done posting.")


if __name__ == "__main__":
    main()
