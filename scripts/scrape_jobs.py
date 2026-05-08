"""Scrape jobs from OnlineJobs.ph using Playwright with correct selectors."""

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_FILE = Path(__file__).parent.parent / "browser_data" / "cookies.json"


def scrape_jobs(search_query: str, max_results: int = 20) -> list:
    """Scrape job listings from OnlineJobs.ph."""
    if not COOKIES_FILE.exists():
        print("ERROR: No cookies found. Run login_onlinejobs.py first!")
        return []

    cookies = json.loads(COOKIES_FILE.read_text())

    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=True, args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context()
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(60000)

    print(f"Searching for: '{search_query}'...")

    # Navigate to search with query
    query_encoded = search_query.replace(" ", "+")
    page.goto(f"https://www.onlinejobs.ph/jobseekers/jobsearch?search={query_encoded}")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)

    # Count job cards
    job_cards = page.locator("div.jobpost-cat-box.latest-job-post").all()
    print(f"Found {len(job_cards)} job cards")

    jobs = []

    for i, card in enumerate(job_cards[:max_results]):
        try:
            # Title - in h4 inside the card
            title_el = card.locator("h4.fs-16").first
            title_html = title_el.inner_html()
            title = title_html.split("<span")[0].strip()

            # Link - anchor inside card
            link_el = card.locator("a[href*='/jobseekers/job/']").first
            href = link_el.get_attribute("href")
            url = "https://www.onlinejobs.ph" + href if href else ""

            # Company - logo alt text
            logo = card.locator("img.jobpost-cat-box-logo").first
            company = logo.get_attribute("alt") if logo else "Not specified"

            # Work type badge
            badge_el = card.locator("span.badge").first
            work_type = (
                badge_el.inner_text() if badge_el.count() > 0 else "Not specified"
            )

            job = {
                "title": title.strip(),
                "company": company.strip() if company else "Not specified",
                "location": "Remote/Online",
                "work_type": work_type.strip(),
                "salary": "Not specified",
                "url": url,
            }

            if job["title"] and job["title"] != "Unknown":
                jobs.append(job)
                print(f"  [+] {job['title'][:50]} @ {job['company'][:30]}")

        except Exception as e:
            print(f"  [-] Error: {e}")
            continue

    browser.close()
    p.stop()

    return jobs


if __name__ == "__main__":
    # Parse args
    search_query = sys.argv[1] if len(sys.argv) > 1 else "python developer"
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    print("=" * 60)
    print("OnlineJobs.ph Scraper")
    print("=" * 60)

    jobs = scrape_jobs(search_query, max_results)

    if jobs:
        print(f"\n=== Found {len(jobs)} jobs ===")

        # Save to JSON
        output_file = Path(__file__).parent.parent / "scraped_jobs.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "status": "success",
                    "source": "onlinejobs.ph",
                    "count": len(jobs),
                    "jobs": jobs,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\nSaved to {output_file}")
    else:
        print("\nNo jobs found. Try a different search or check login.")
