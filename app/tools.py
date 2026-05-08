import json
import os
from typing import Dict, Any
from pathlib import Path

# Load .env file
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
gemini_client = None
openai_client = None

if os.getenv("GEMINI_API_KEY"):
    from google import genai

    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

if os.getenv("OPENROUTER_API_KEY"):
    from openai import OpenAI

    openai_client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1"
    )


def _scrape_jobs_sync(search_query: str, max_results: int) -> list:
    """Synchronous playwright scraping - run in thread pool."""
    from playwright.sync_api import sync_playwright

    cookies_file = Path(__file__).parent.parent / "browser_data" / "cookies.json"

    p = sync_playwright().start()
    try:
        browser = p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context()

        if cookies_file.exists():
            cookies = json.loads(cookies_file.read_text())
            context.add_cookies(cookies)

        page = context.new_page()
        page.set_default_timeout(60000)

        # Navigate to search page
        page.goto("https://www.onlinejobs.ph/jobseekers/jobsearch")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # Use the correct form input name="jobkeyword"
        search_input = page.locator('input[name="jobkeyword"]')
        if search_input.count() > 0:
            search_input.first.fill(search_query)
            search_input.first.press("Enter")
            page.wait_for_timeout(3000)

        job_cards = page.locator("div.jobpost-cat-box.latest-job-post").all()

        jobs = []
        for card in job_cards[:max_results]:
            try:
                title_html = card.locator("h4.fs-16").first.inner_html()
                title = title_html.split("<span")[0].strip()

                link = card.locator('a[href*="/jobseekers/job/"]').first
                href = link.get_attribute("href")
                url = "https://www.onlinejobs.ph" + href if href else ""

                logos = card.locator("img.jobpost-cat-box-logo")
                company = (
                    logos.first.get_attribute("alt")
                    if logos.count() > 0
                    else "Not specified"
                )

                badge = card.locator("span.badge").first
                work_type = badge.inner_text() if badge.count() > 0 else "Not specified"

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
            except Exception:
                continue

        browser.close()
        return jobs
    finally:
        p.stop()


async def scrape_onlinejobs(search_query: str, max_results: int = 20) -> Dict[str, Any]:
    """
    Scrape job listings from OnlineJobs.ph using Playwright.

    Args:
        search_query: Job title or keywords to search for
        max_results: Maximum number of jobs to return

    Returns:
        JSON string containing list of job postings
    """
    import asyncio

    jobs = await asyncio.to_thread(_scrape_jobs_sync, search_query, max_results)

    return json.dumps(
        {
            "status": "success",
            "source": "onlinejobs.ph",
            "count": len(jobs),
            "jobs": jobs,
        },
        indent=2,
    )


async def parse_resume(
    resume_text: str = "", resume_file_path: str = ""
) -> Dict[str, Any]:
    """
    Parse resume content to extract key information.

    Args:
        resume_text: Raw resume text content
        resume_file_path: Path to resume file (pdf, txt)

    Returns:
        JSON string with extracted skills, experience, education
    """
    import re

    text = resume_text

    if resume_file_path and Path(resume_file_path).exists():
        ext = Path(resume_file_path).suffix.lower()
        if ext == ".txt":
            text = Path(resume_file_path).read_text(encoding="utf-8")
        elif ext == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(resume_file_path)
                text = "\n".join([page.extract_text() for page in reader.pages])
            except Exception:
                pass

    if not text:
        return json.dumps(
            {
                "status": "error",
                "message": "No resume content provided",
                "skills": [],
                "experience": [],
                "education": [],
            },
            indent=2,
        )

    tech_keywords = [
        "Python",
        "JavaScript",
        "TypeScript",
        "React",
        "Angular",
        "Vue",
        "Node.js",
        "Go",
        "Rust",
        "Java",
        "C++",
        "C#",
        "PHP",
        "Ruby",
        "Swift",
        "Kotlin",
        "SQL",
        "NoSQL",
        "MongoDB",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Elasticsearch",
        "AWS",
        "GCP",
        "Azure",
        "Docker",
        "Kubernetes",
        "Terraform",
        "Jenkins",
        "Git",
        "Linux",
        "REST",
        "GraphQL",
        "HTML",
        "CSS",
        "React Native",
        "TensorFlow",
        "PyTorch",
        "Machine Learning",
        "AI",
        "Data Science",
        "Agile",
        "Scrum",
        "CI/CD",
        "DevOps",
        "Cloud",
        "Serverless",
        "Prometheus",
        "Grafana",
        "Docker",
        "Flask",
        "Django",
        "FastAPI",
    ]

    tech_pattern = r"\b(" + "|".join(re.escape(t) for t in tech_keywords) + r")\b"

    skills = re.findall(tech_pattern, text, re.IGNORECASE)
    skills = list(set([s.title() for s in skills]))[:20]

    experience = []
    exp_pattern = (
        r"(?:experience|employment|work history)(?:\s*:|\s*-\s*)?([^\n]{10,200})"
    )
    for match in re.finditer(exp_pattern, text, re.IGNORECASE):
        exp_text = match.group(1).strip()
        if len(exp_text) > 20:
            experience.append(exp_text[:200])

    education = []
    edu_pattern = (
        r"(?:education|degree|university|college)(?:\s*:|\s*-\s*)?([^\n]{10,150})"
    )
    for match in re.finditer(edu_pattern, text, re.IGNORECASE):
        edu_text = match.group(1).strip()
        if len(edu_text) > 10:
            education.append(edu_text[:150])

    return json.dumps(
        {
            "status": "success",
            "skills": skills,
            "experience": experience[:5],
            "education": education[:3],
            "word_count": len(text.split()),
        },
        indent=2,
    )


async def match_jobs_to_resume(
    resume_data: str, jobs_data: str, min_score: float = 0.5
) -> Dict[str, Any]:
    """
    Match jobs against resume and rank by relevance (HTL).

    Args:
        resume_data: JSON string from parse_resume
        jobs_data: JSON string from scrape_onlinejobs
        min_score: Minimum relevance score (0-1) for HTL

    Returns:
        JSON string with matched and ranked jobs
    """
    try:
        resume = json.loads(resume_data)
        jobs = json.loads(jobs_data)

        if isinstance(jobs, dict):
            jobs = jobs.get("jobs", [])

    except json.JSONDecodeError:
        return json.dumps(
            {"status": "error", "message": "Invalid JSON in resume or jobs data"},
            indent=2,
        )

    if not resume.get("skills"):
        return json.dumps(
            {"status": "error", "message": "No skills found in resume"}, indent=2
        )

    matched_jobs = []

    for job in jobs:
        score = 0.0
        job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()
        resume_skills = [s.lower() for s in resume.get("skills", [])]

        matched_skills = []
        for skill in resume_skills:
            if skill in job_text:
                score += 0.15
                matched_skills.append(skill)

        score = min(score, 1.0)

        if score >= min_score:
            matched_jobs.append(
                {
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "salary": job.get("salary"),
                    "url": job.get("url"),
                    "relevance_score": round(score, 2),
                    "matched_skills": matched_skills,
                    "htl": score >= 0.7,
                }
            )

    matched_jobs.sort(key=lambda x: x["relevance_score"], reverse=True)

    htl_jobs = [j for j in matched_jobs if j["htl"]]

    return json.dumps(
        {
            "status": "success",
            "total_matched": len(matched_jobs),
            "htl_count": len(htl_jobs),
            "htl_jobs": htl_jobs[:10],
            "all_matched_jobs": matched_jobs[:20],
        },
        indent=2,
    )


async def generate_cover_letter(job_data: str, resume_data: str) -> Dict[str, Any]:
    """
    Generate personalized cover letter based on job and resume.

    Args:
        job_data: JSON string with job details
        resume_data: JSON string with parsed resume

    Returns:
        JSON string with generated cover letter
    """
    try:
        job = json.loads(job_data)
        resume = json.loads(resume_data)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON data"}, indent=2)

    if isinstance(job, str):
        job = json.loads(job)
    if isinstance(resume, str):
        resume = json.loads(resume)

    skills = resume.get("skills", [])
    experience = resume.get("experience", [])[:2]
    job_title = job.get("title", "the position")
    company = job.get("company", "your company")

    skills_line = f" With my background in {', '.join(skills[:5])}," if skills else ""
    exp_line = (
        f" In my recent experience, I have {experience[0][:100]}." if experience else ""
    )

    cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}.

{skills_line}

{exp_line}

I am confident that my skills and passion make me a great fit for this role. I would welcome the opportunity to discuss how I can contribute to your team.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
[Your Name]"""

    if not skills:
        cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}.

I am confident that my skills and experience make me a great fit for this role. I would welcome the opportunity to discuss how I can contribute to your team.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
[Your Name]"""

    return json.dumps(
        {
            "status": "success",
            "job_title": job_title,
            "company": company,
            "cover_letter": cover_letter,
        },
        indent=2,
    )


async def customize_cv(
    job_data: str = "{}", resume_data: str = "{}", user_name: str = ""
) -> Dict[str, Any]:
    """
    Generate a personalized CV for a specific job application.

    Args:
        job_data: JSON string with job title, company, description, requirements
        resume_data: JSON string with skills, experience, education
        user_name: Optional user name for personalization

    Returns:
        JSON string with personalized CV sections and ATS score
    """
    try:
        job = json.loads(job_data)
        resume = json.loads(resume_data)
    except json.JSONDecodeError:
        return json.dumps(
            {"status": "error", "message": "Invalid JSON in job or resume data"},
            indent=2,
        )

    job_title = job.get("title", "the position")
    company = job.get("company", "the company")
    job_description = job.get("description", job.get("requirements", ""))

    skills = resume.get("skills", [])
    experience = resume.get("experience", [])

    if not job_description:
        job_description = (
            f"Looking for candidates with skills in: {', '.join(skills[:10])}"
        )

    prompt = f"""You are a professional CV writer specializing in ATS optimization.
Create a personalized CV for a job application.

**Job Details:**
- Position: {job_title}
- Company: {company}
- Requirements: {job_description}

**Candidate Profile:**
- Skills: {", ".join(skills) if skills else "Not specified"}
- Experience: {"; ".join(experience) if experience else "Not specified"}
{f"- Name: {user_name}" if user_name else ""}

**Task:**
Generate a personalized CV with these sections ONLY (JSON format):

```json
{{
  "personalized_cv": {{
    "summary": "2-3 sentence professional summary highlighting relevant skills for this specific role",
    "experience": [
      {{
        "title": "Job title",
        "company": "Company name",
        "highlights": ["Bullet point 1 tailored to job requirements", "Bullet point 2 emphasizing relevant achievements"]
      }}
    ],
    "skills": "Relevant technical and soft skills for this role, comma-separated"
  }},
  "ats_score": 85,
  "match_insights": "Brief explanation of why this CV matches the role"
}}
```

Rules:
- Match keywords from job description in summary and experience
- Re-frame experience bullets to highlight relevant skills
- ATS score should be 60-95 based on keyword match quality
- Return ONLY valid JSON, no markdown code blocks or explanation"""

    try:
        result_text = None

        # Try OpenRouter first
        if openai_client:
            try:
                response = openai_client.chat.completions.create(
                    model="openrouter/auto",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional CV writer. Return ONLY valid JSON, no markdown.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=2000,
                    temperature=0.7,
                )
                result_text = response.choices[0].message.content
            except Exception as e:
                print(f"OpenRouter error: {e}")

        # Fall back to Gemini
        if not result_text and gemini_client:
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                result_text = response.text.strip()
            except Exception as e:
                print(f"Gemini error: {e}")

        if not result_text:
            return json.dumps(
                {"status": "error", "message": "No AI provider available"},
                indent=2,
            )

        # Clean response
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip().rstrip("```")

        result = json.loads(result_text)
        return json.dumps({"status": "success", **result}, indent=2)

    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "message": f"Failed to generate personalized CV: {str(e)}",
            },
            indent=2,
        )
