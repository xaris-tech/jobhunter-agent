"""Login to OnlineJobs.ph using Playwright - preserves session for scraping."""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def login_to_onlinejobs():
    """Open browser and navigate to OnlineJobs.ph for manual login."""
    print("Starting browser...")

    async with async_playwright() as p:
        # Launch browser - headless=False so user can interact
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        page = await context.new_page()

        print("Opening OnlineJobs.ph login page...")
        await page.goto("https://www.onlinejobs.ph/login")

        print("\n" + "=" * 50)
        print("Login in the browser window.")
        print("After logging in, leave the browser open.")
        print("The script will detect when you're logged in.")
        print("=" * 50)

        # Wait for user to login - check for specific elements that appear when logged in
        try:
            # Wait for either the user dashboard or job search to appear
            await page.wait_for_selector(
                "a[href*='logout'], div.user-profile, nav.navbar, a[href*='jobsearch']",
                timeout=120000,  # 2 minutes timeout
            )
            print("\n✓ Login detected!")
        except Exception:
            print("\nTimeout waiting for login. Please login and press any key...")

        # Save cookies
        cookies = await context.cookies()
        cookies_file = Path(__file__).parent.parent / "browser_data" / "cookies.json"
        cookies_file.parent.mkdir(exist_ok=True)
        cookies_file.write_text(json.dumps(cookies, indent=2))
        print(f"Saved {len(cookies)} cookies to {cookies_file}")

        # Navigate to job search to verify
        await page.goto("https://www.onlinejobs.ph/jobseekers/jobsearch")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=cookies_file.parent / "after_login.png")
        print("Screenshot saved")

        print("\n✓ Session saved! Close the browser when done.")
        print("Press Ctrl+C to exit...")

        # Keep browser open
        await asyncio.Event().wait()


async def scrape_with_session(
    search_query: str = "python developer", max_results: int = 20
):
    """Use saved session to scrape jobs."""
    cookies_file = Path(__file__).parent.parent / "browser_data" / "cookies.json"

    if not cookies_file.exists():
        print("No cookies found. Run 'login' command first!")
        return

    cookies = json.loads(cookies_file.read_text())

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await context.add_cookies(cookies)

        page = await context.new_page()

        print(f"Searching for '{search_query}'...")
        await page.goto("https://www.onlinejobs.ph/jobseekers/jobsearch")

        # Fill search
        search_input = await page.query_selector(
            'input[name="search"], input[type="search"], input#search'
        )
        if search_input:
            await search_input.fill(search_query)
            await page.click(
                'button[type="submit"], button.search-btn, input[type="submit"]'
            )
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)

        # Extract jobs
        jobs = []
        job_cards = await page.query_selector_all(
            "div.job-post, article.job-item, div.job-listing-item, div.job-item"
        )

        print(f"Found {len(job_cards)} job cards")

        for card in job_cards[:max_results]:
            try:
                title = await card.query_selector("h3, h2, a[href*='job']")
                company = await card.query_selector("span.company, div.employer-name")
                location = await card.query_selector("span.location, div.location")
                desc = await card.query_selector("div.description, p")

                job = {
                    "title": (await title.inner_text()).strip() if title else "Unknown",
                    "company": (await company.inner_text()).strip()
                    if company
                    else "Not specified",
                    "location": (await location.inner_text()).strip()
                    if location
                    else "Not specified",
                    "description": (await desc.inner_text()).strip()[:200]
                    if desc
                    else "",
                }

                if job["title"] and job["title"] != "Unknown":
                    jobs.append(job)
            except Exception:
                continue

        print(f"\n=== Found {len(jobs)} jobs ===")
        for j in jobs[:10]:
            print(f"- {j['title']} @ {j['company']}")

        return jobs


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python login_onlinejobs.py [login|scrape] [query]")
        sys.exit(1)

    if sys.argv[1] == "login":
        asyncio.run(login_to_onlinejobs())
    elif sys.argv[1] == "scrape":
        query = sys.argv[2] if len(sys.argv) > 2 else "python developer"
        asyncio.run(scrape_with_session(query))
    else:
        print("Unknown command. Use: login or scrape")
