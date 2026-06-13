"""Headless demo recorder — drives the REAL GrantScribe Slack app and records video.

Uses the captured session (demo/slack_session.json). Runs the full flow:
  /setreport (modal) -> /grants -> Draft LOI -> /pathway -> Draft my plan
and records the whole thing to demo/recordings/*.webm.

Run:  python demo/record_demo.py
Needs grants_server.py + slack_app.py running.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
SESSION = HERE / "slack_session.json"
REC_DIR = HERE / "recordings"
REPORT = (HERE.parent / "sample_data" / "org_report.md").read_text()

GRANTS_DESC = "youth refugee tutoring in Ohio, after-school literacy, need operating funds"
PATHWAY_GOAL = "registered nurse near 45241"
SHORT_REPORT = (
    "New Roots Tutoring Collective is a Columbus, Ohio nonprofit founded in 2019 providing free "
    "after-school tutoring and English-language support to refugee youth in grades 3-12. In 2024-25 "
    "we served 142 students across three sites with 61 volunteer tutors and four bilingual coordinators; "
    "88% of students were promoted to the next grade. We need operating funds to clear 30-student "
    "waitlists. Executive Director: Amara Okonkwo."
)


def log(m: str) -> None:
    print(m, flush=True)


def composer(page):
    box = page.locator('[data-qa="message_input"]').last
    box.wait_for(timeout=70000)
    return box


def send_command(page, text: str, settle: float = 1.0) -> None:
    """Type a slash command and send it (Escape dismisses the autocomplete popup)."""
    box = composer(page)
    box.click()
    box.type(text, delay=30)
    page.wait_for_timeout(700)
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    page.keyboard.press("Enter")
    page.wait_for_timeout(int(settle * 1000))


def wait_for_text(page, needles, timeout_s: int = 60) -> bool:
    needles = [n.lower() for n in needles]
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            blocks = page.locator('[data-qa="message_content"]')
            n = blocks.count()
            for i in range(max(0, n - 4), n):
                t = blocks.nth(i).inner_text().lower()
                if any(x in t for x in needles):
                    return True
        except Exception:
            pass
        page.wait_for_timeout(1500)
    return False


def click_button(page, name: str, timeout_s: int = 25) -> bool:
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            btn = page.locator(f'button:has-text("{name}")').last
            if btn.count() and btn.is_visible():
                btn.scroll_into_view_if_needed()
                page.wait_for_timeout(600)
                btn.click()
                return True
        except Exception:
            pass
        page.wait_for_timeout(1000)
    return False


def main() -> int:
    if not SESSION.exists():
        log("No session — capture it first.")
        return 1
    REC_DIR.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
        ctx = b.new_context(
            storage_state=str(SESSION),
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(REC_DIR),
            record_video_size={"width": 1440, "height": 900},
        )
        page = ctx.new_page()
        page.goto("https://app.slack.com/client", wait_until="domcontentloaded")
        log("waiting for workspace to populate…")
        composer(page)
        page.wait_for_timeout(2500)

        # ---- /setreport (inline form, TYPED so it dispatches; short so it fits) ----
        log("beat: /setreport (inline, typed)")
        send_command(page, f"/setreport {SHORT_REPORT}", settle=2)
        ack = wait_for_text(page, ["saved your org report", "saved"], 30)
        log(f"  report saved ack: {ack}")
        page.wait_for_timeout(2500)

        # ---- /grants ----
        log("beat: /grants")
        send_command(page, f"/grants {GRANTS_DESC}", settle=2)
        got = wait_for_text(page, ["grants that fit", "fit", "due", "no clearly-relevant"], 75)
        log(f"  grants reply: {got}")
        page.wait_for_timeout(3000)

        # ---- Draft LOI ----
        log("beat: Draft LOI")
        if click_button(page, "Draft LOI"):
            wait_for_text(page, ["letter of intent", "RE:", "submission deadline"], 90)
            log("  LOI drafted")
        page.wait_for_timeout(4000)

        # ---- /pathway ----
        log("beat: /pathway")
        send_command(page, f"/pathway {PATHWAY_GOAL}", settle=2)
        wait_for_text(page, ["pathway", "credential", "real training programs", "occupation"], 75)
        page.wait_for_timeout(3000)

        # ---- Draft my plan ----
        log("beat: Draft my plan")
        if click_button(page, "Draft my plan"):
            wait_for_text(page, ["funded-path plan", "credential to be earned", "RE: funding"], 90)
            log("  plan drafted")
        page.wait_for_timeout(4000)

        log("done — finalizing video")
        page.close()
        ctx.close()
        b.close()
    vids = sorted(REC_DIR.glob("*.webm"))
    log(f"VIDEO: {vids[-1] if vids else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
