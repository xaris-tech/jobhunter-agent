"""Capture page HTML for analysis - dump to file"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_FILE = Path(__file__).parent.parent / "browser_data" / "cookies.json"
OUTPUT_FILE = Path(__file__).parent.parent / "debug_page.html"


async def capture_page():
    """Navigate and capture raw HTML to file."""
    if not COOKIES_FILE.exists():
        print("No cookies - run login first")
        return

    cookies = json.loads(COOKIES_FILE.read_text())

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context()
        await context.add_cookies(cookies)

        page = await context.new_page()

        print("Loading job search page...")
        await page.goto("https://www.onlinejobs.ph/jobseekers/jobsearch", timeout=60000)

        # Wait for content to load
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(5000)

        # Scroll down to load lazy content
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

        # Save HTML
        html = await page.content()
        OUTPUT_FILE.write_text(html, encoding="utf-8")
        print(f"Saved {len(html)} bytes to {OUTPUT_FILE}")

        # Also save screenshot
        await page.screenshot(path="debug_page.png", full_page=True)
        print("Screenshot saved")

        # Quick structure check
        print("\n=== Quick structure check ===")
        print(f"Title: {await page.title()}")
        print(f"URL: {page.url}")

        # Count elements
        job_count = await page.locator("[class*='job']").count()
        print(f"Elements with 'job' class: {job_count}")

        print("\nDone! Check debug_page.html")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(capture_page())
