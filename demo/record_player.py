"""Record an HTML player to video.  Usage: record_player.py [file.html] [out_dir]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "player.html"
REC = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "recordings"
REC.mkdir(exist_ok=True)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
        ctx = b.new_context(viewport={"width": 1440, "height": 900},
                            record_video_dir=str(REC), record_video_size={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(f"file://{HTML.resolve()}")
        page.wait_for_timeout(800)
        page.evaluate("window.__start()")
        for _ in range(240):
            if page.evaluate("document.body.getAttribute('data-done')"):
                break
            page.wait_for_timeout(1000)
        page.wait_for_timeout(1500)
        page.close()
        ctx.close()
        b.close()
    vids = sorted(REC.glob("*.webm"), key=lambda f: f.stat().st_mtime)
    print("VIDEO:", vids[-1] if vids else "none")


if __name__ == "__main__":
    main()
