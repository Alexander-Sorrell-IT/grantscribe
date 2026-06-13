"""One-time Slack login capture for the demo recorder.

Opens a real Chromium window using a PERSISTENT profile (demo/.slack_profile), so
your login sticks even across restarts. You log into the GrantScribe workspace;
this detects the loaded web client (the message box appearing) and saves the
session to demo/slack_session.json. record_demo.py reuses the same profile.

Run:  python -u demo/save_slack_session.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

WORKSPACE_URL = "https://e0b5s2b156h-3lz3eai2.slack.com/"
HERE = Path(__file__).parent
PROFILE_DIR = HERE / ".slack_profile"
SESSION_PATH = HERE / "slack_session.json"
LOGIN_TIMEOUT_S = 540


def _log(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    PROFILE_DIR.mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(WORKSPACE_URL, wait_until="domcontentloaded")
        _log(">>> Log into the GrantScribe Slack in this window.")
        _log(">>> If it offers 'open the Slack app', choose 'use Slack in your browser'.")

        deadline = time.time() + LOGIN_TIMEOUT_S
        saved = False
        while time.time() < deadline:
            try:
                url = page.url
                composer = page.locator('[data-qa="message_input"]').count()
            except Exception as exc:
                _log(f"(page busy: {exc})")
                time.sleep(2)
                continue
            _log(f"   url={url[:70]}  composer_present={bool(composer)}")
            if composer or "app.slack.com/client" in url:
                time.sleep(4)  # let storage settle
                ctx.storage_state(path=str(SESSION_PATH))
                _log(f">>> ✅ Saved session to {SESSION_PATH}")
                saved = True
                break
            time.sleep(3)

        if not saved:
            _log(">>> Timed out waiting for login.")
        # Keep the window open briefly so it doesn't vanish from under you.
        time.sleep(5)
        ctx.close()
    return 0 if saved else 1


if __name__ == "__main__":
    sys.exit(main())
