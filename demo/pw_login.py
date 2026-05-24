"""Demo recording — STEP 1: log into the Slack sandbox ONCE (run this yourself).

Opens a real browser, you sign in (handle the email magic-code), then press Enter
here to save the authenticated session to a local profile. Step 2 (pw_demo.py)
reuses that session to record the demo.

Run:  uv run --with playwright python demo/pw_login.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE = str(Path(__file__).parent / "pw_profile")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, headless=False, viewport={"width": 1440, "height": 900}
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://slack.com/signin")
    print("\n>>> Sign into your GrantScribe sandbox in the browser window.")
    print(">>> When you can see the workspace and the #funding channel, return here.\n")
    input("Press Enter once you're fully logged in... ")
    ctx.close()
    print("✅ Session saved to demo/pw_profile — you can run the demo now.")
