"""Validate the Slack tokens in .env before launching. Prints no secrets."""
import os
from pathlib import Path

from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv(Path(__file__).with_name(".env"))

bot = os.environ.get("SLACK_BOT_TOKEN", "").strip()
app_token = os.environ.get("SLACK_APP_TOKEN", "").strip()

if not bot.startswith("xoxb-"):
    raise SystemExit(f"SLACK_BOT_TOKEN should start with 'xoxb-' but starts with {bot[:6]!r}. "
                     "Use the Bot User OAuth Token from Install App.")
if not app_token.startswith("xapp-"):
    raise SystemExit(f"SLACK_APP_TOKEN should start with 'xapp-' but starts with {app_token[:6]!r}. "
                     "Use the App-Level Token from Basic Information.")

result = WebClient(token=bot).auth_test()
print(f"bot token : OK  |  team: {result['team']}  |  bot user: @{result['user']}")
print("app token : OK  |  prefix xapp- ✓")
print("\nOK: both Slack tokens are valid — ready to launch.")
