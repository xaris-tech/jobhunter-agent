"""Debug page structure using Playwright with browser data"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_FILE = Path(__file__).parent.parent / "browser_data" / "cookies.json"


def debug():
    """Navigate and capture HTML structure."""
    if not COOKIES_FILE.exists():
        print("No cookies - run login first")
        return

    cookies = json.loads(COOKIES_FILE.read_text())

    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=False, args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context()
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(60000)

    print("Loading job search page...")
    page.goto("https://www.onlinejobs.ph/jobseekers/jobsearch")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(5000)

    # Scroll to load lazy content
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)

    # Get page info
    print(f"\nPage Title: {page.title()}")
    print(f"URL: {page.url}")

    # Count elements
    all_divs = page.locator("div").count()
    job_class_divs = page.locator("[class*='job']").count()
    table_rows = page.locator("tr").count()
    list_items = page.locator("li").count()

    print(f"\n=== Element counts ===")
    print(f"Total divs: {all_divs}")
    print(f"Divs with 'job' class: {job_class_divs}")
    print(f"Table rows: {table_rows}")
    print(f"List items: {list_items}")

    # Get all unique class names
    class_names = page.evaluate("""
        () => {
            const classes = new Set();
            document.querySelectorAll('*').forEach(el => {
                if (el.className && typeof el.className === 'string') {
                    el.className.split(/\\s+/).forEach(c => {
                        if (c.length > 3) classes.add(c);
                    });
                }
            });
            return Array.from(classes).sort();
        }
    """)

    print(f"\nTotal unique classes: {len(class_names)}")

    # Filter for relevant ones
    relevant = [
        c
        for c in class_names
        if any(
            x in c.lower()
            for x in ["job", "listing", "card", "post", "search", "result"]
        )
    ]
    print(f"\nJob/search-related classes ({len(relevant)}):")
    for c in relevant[:30]:
        count = page.locator(f".{c}").count()
        print(f"  .{c}: {count} elements")

    # Take screenshot
    page.screenshot(path="debug_page.png", full_page=True)
    print("\nScreenshot saved to debug_page.png")

    # Save HTML
    html = page.content()
    OUTPUT_FILE = Path(__file__).parent.parent / "debug_page.html"
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"HTML saved to {OUTPUT_FILE}")

    print("\nDone! Check debug_page.html")
    print("Press Enter to close browser...")
    input()

    browser.close()
    p.stop()


if __name__ == "__main__":
    debug()
