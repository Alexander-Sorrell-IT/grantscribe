"""Record the REAL Slack client scrolling through the posted demo conversation."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
REC = HERE / "recordings_slack"
REC.mkdir(exist_ok=True)
CH_URL = "https://app.slack.com/client/E0B5S2B156H/C0B5S2D91B7"


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
        ctx = b.new_context(storage_state=str(HERE / "slack_session.json"),
                            viewport={"width": 1440, "height": 900},
                            record_video_dir=str(REC), record_video_size={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(CH_URL, wait_until="domcontentloaded")
        page.locator('[data-qa="message_input"]').last.wait_for(timeout=70000)
        time.sleep(5)
        # Scroll up to the start of the demo conversation.
        try:
            page.get_by_text("youth refugee tutoring in Ohio", exact=False).first.scroll_into_view_if_needed(timeout=8000)
        except Exception:
            pass
        time.sleep(2)
        # Cinematic slow scroll down through the whole conversation.
        page.mouse.move(720, 450)
        for _ in range(60):
            page.mouse.wheel(0, 230)
            time.sleep(0.9)
        time.sleep(2)
        page.close()
        ctx.close()
        b.close()
    vids = sorted(REC.glob("*.webm"))
    print("SLACK VIDEO:", vids[-1] if vids else "none")


if __name__ == "__main__":
    main()
