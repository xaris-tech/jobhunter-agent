"""Debug and fix job card selectors on OnlineJobs.ph"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def debug_selectors():
    """Navigate to job search and find correct selectors."""
    cookies_file = Path(__file__).parent.parent / "browser_data" / "cookies.json"

    if not cookies_file.exists():
        print("No cookies found. Run login first!")
        return

    cookies = json.loads(cookies_file.read_text())

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await context.add_cookies(cookies)

        page = await context.new_page()
        page.set_default_timeout(30000)

        print("Navigating to job search...")
        await page.goto("https://www.onlinejobs.ph/jobseekers/jobsearch")

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

        await page.screenshot(path="debug_selectors.png")

        # Get all classes with "job" in them
        job_classes = await page.evaluate("""
            () => {
                const classes = new Set();
                document.querySelectorAll('*').forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        el.className.split(/\\s+/).forEach(c => {
                            if (c.length > 3 && (c.includes('job') || c.includes('listing'))) {
                                classes.add(c);
                            }
                        });
                    }
                });
                return Array.from(classes);
            }
        """)

        print(f"\nFound {len(job_classes)} job/listing classes:")
        for c in job_classes[:30]:
            print(f"  - {c}")

        # Try each class as selector
        print("\n=== Testing class selectors ===")
        for cls in job_classes[:15]:
            try:
                count = await page.locator(f".{cls}").count()
                if count > 0:
                    print(f"✓ .{cls}: {count} elements")
                    # Get first element HTML
                    first_html = await page.locator(f".{cls}").first.inner_html()
                    print(f"  → {first_html[:150]}...")
            except:
                pass

        print("\n=== Checking page structure ===")
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")

        # Wait for user
        print("\nBrowser is open. Press Ctrl+C to exit...")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(debug_selectors())
