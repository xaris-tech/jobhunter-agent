"""Debug using existing Chrome profile instead of fresh launch"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def debug_with_existing_profile():
    """Use existing browser profile for debugging."""
    cookies_file = Path(__file__).parent.parent / "browser_data" / "cookies.json"
    profile_dir = Path(__file__).parent.parent / "browser_data" / "Default"

    if not cookies_file.exists():
        print("No cookies found. Run login first!")
        return

    cookies = json.loads(cookies_file.read_text())

    async with async_playwright() as p:
        # Try using existing Chrome profile
        browser = await p.chromium.launch(
            headless=False,
            channel="chromium",
            args=[
                "--user-data-dir=" + str(profile_dir.absolute()),
            ],
        )

        context = await browser.new_context()
        await context.add_cookies(cookies)

        page = await context.new_page()
        page.set_default_timeout(30000)

        print("Navigating to job search...")
        await page.goto(
            "https://www.onlinejobs.ph/jobseekers/jobsearch?q=python+developer"
        )

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)

        # Scroll to load lazy content
        await page.evaluate("window.scrollTo(0, 500)")
        await page.wait_for_timeout(2000)

        await page.screenshot(path="debug_scroll.png")

        # Get all visible elements that could be job cards
        print("\n=== Looking for job content ===")

        # Check for table-based layout (common in older PHP sites)
        rows = await page.locator("table tr").count()
        print(f"Table rows: {rows}")

        # Check for div-based layout
        divs = await page.locator("div[class*='job']").count()
        print(f"Divs with 'job' class: {divs}")

        # Check for list items
        lis = await page.locator("li").count()
        print(f"List items: {lis}")

        # Get the page HTML structure for analysis
        print("\n=== Page structure ===")
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")

        # Count all elements by tag
        tags = await page.evaluate("""
            () => {
                const counts = {};
                document.querySelectorAll('*').forEach(el => {
                    const tag = el.tagName.toLowerCase();
                    counts[tag] = (counts[tag] || 0) + 1;
                });
                return counts;
            }
        """)
        print(f"Element counts by tag: {tags}")

        print("\n=== Analyzing page source ===")
        html = await page.content()

        # Look for job-related keywords in HTML
        import re

        patterns = ["joblisting", "vacancy", "position", "opening", "career"]
        for pat in patterns:
            count = len(re.findall(pat, html, re.IGNORECASE))
            if count > 0:
                print(f"'{pat}' found {count} times in HTML")

        print("\nBrowser is open. Check debug_scroll.png")
        print("Press Ctrl+C to exit...")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(debug_with_existing_profile())
