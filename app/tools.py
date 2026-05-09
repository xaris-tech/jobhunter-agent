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


def _scrape_jobs_sync(search_query: str, max_results: int = 50) -> list:
    """Synchronous playwright scraping - run in thread pool with pagination."""
    from playwright.sync_api import sync_playwright

    cookies_file = Path(__file__).parent.parent / "browser_data" / "cookies.json"

    p = sync_playwright().start()
    try:
        browser = p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context()
        context.set_extra_http_headers(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        if cookies_file.exists():
            cookies = json.loads(cookies_file.read_text())
            context.add_cookies(cookies)

        page = context.new_page()
        page.set_default_timeout(60000)

        jobs = []
        current_page = 1
        max_pages = 5
        job_urls = []  # Collect URLs first

        while len(job_urls) < max_results and current_page <= max_pages:
            if current_page == 1:
                page.goto("https://www.onlinejobs.ph/jobseekers/jobsearch")
            else:
                page.goto(
                    f"https://www.onlinejobs.ph/jobseekers/jobsearch?page={current_page}"
                )

            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            if current_page == 1:
                search_input = page.locator('input[name="jobkeyword"]')
                if search_input.count() > 0:
                    search_input.first.fill(search_query)
                    search_input.first.press("Enter")
                    page.wait_for_timeout(3000)

            job_cards = page.locator("div.jobpost-cat-box.latest-job-post").all()

            if not job_cards:
                break

            for card in job_cards:
                if len(job_urls) >= max_results:
                    break
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
                    work_type = (
                        badge.inner_text() if badge.count() > 0 else "Not specified"
                    )

                    if title and title != "Unknown":
                        job_urls.append(
                            {
                                "title": title.strip(),
                                "company": company.strip()
                                if company
                                else "Not specified",
                                "work_type": work_type.strip(),
                                "url": url,
                            }
                        )
                except Exception:
                    continue

            current_page += 1
            page.wait_for_timeout(1000)

        # Now visit each job URL to get full description
        for job_data in job_urls:
            try:
                page.goto(job_data["url"])
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1500)

                # Extract job description
                description = ""

                # Try multiple selectors for job description
                desc_selectors = [
                    "div.job-content",
                    "div.job-description",
                    "div.content-description",
                    "div.job-details-content",
                    "div#job_description",
                    "div[itemprop='description']",
                    ".job-desc",
                    ".job-description",
                ]

                for selector in desc_selectors:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        description = el.inner_text().strip()
                        if len(description) > 50:
                            break

                # Alternative: get all paragraph text
                if not description or len(description) < 50:
                    paragraphs = page.locator(
                        "div.content p, div.job-content p, p"
                    ).all()
                    desc_parts = []
                    for para in paragraphs:
                        text = para.inner_text().strip()
                        if len(text) > 20:
                            desc_parts.append(text)
                    description = " ".join(desc_parts[:10])

                # Extract location
                location = "Remote/Online"
                location_selectors = [
                    "span.location",
                    "div.location",
                    "span.job-location",
                    "[itemprop='jobLocation']",
                ]
                for selector in location_selectors:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        loc = el.inner_text().strip()
                        if loc:
                            location = loc
                            break

                # Extract salary
                salary = "Not specified"
                salary_selectors = [
                    "span.salary",
                    "div.salary",
                    "span.job-salary",
                    "[itemprop='baseSalary']",
                ]
                for selector in salary_selectors:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        sal = el.inner_text().strip()
                        if sal:
                            salary = sal
                            break

                job = {
                    "title": job_data["title"],
                    "company": job_data["company"],
                    "location": location,
                    "work_type": job_data["work_type"],
                    "salary": salary,
                    "url": job_data["url"],
                    "description": description[:2000]
                    if description
                    else "",  # Limit description length
                }

                jobs.append(job)
                print(
                    f"  Scraped: {job['title'][:40]}... (desc: {len(job.get('description', ''))} chars)"
                )

            except Exception as e:
                print(f"  Error scraping {job_data['title'][:30]}: {str(e)[:50]}")
                # Add job anyway without description
                jobs.append(
                    {
                        "title": job_data["title"],
                        "company": job_data["company"],
                        "location": "Remote/Online",
                        "work_type": job_data["work_type"],
                        "salary": "Not specified",
                        "url": job_data["url"],
                        "description": "",
                    }
                )

        browser.close()
        return jobs[:max_results]
    finally:
        p.stop()


async def scrape_onlinejobs(search_query: str, max_results: int = 50) -> Dict[str, Any]:
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
    resume_data: str, jobs_data: str, min_score: float = 0.3
) -> Dict[str, Any]:
    """
    Match jobs against resume and rank by relevance percentage.

    Args:
        resume_data: JSON string from parse_resume
        jobs_data: JSON string from scrape_onlinejobs
        min_score: Minimum relevance score (0-1) to include in results

    Returns:
        JSON string with matched and ranked jobs
    """
    import re

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

    resume_skills = [s.lower() for s in resume.get("skills", [])]
    resume_experience = " ".join(resume.get("experience", [])).lower()
    resume_text = (
        f"{resume_skills} {resume_experience} {resume.get('raw_text', '')}".lower()
    )

    job_keywords = {
        "python": ["python", "django", "flask", "fastapi"],
        "javascript": ["javascript", "js", "react", "vue", "angular", "node"],
        "frontend": ["frontend", "front-end", "ui", "ux", "css", "html"],
        "backend": ["backend", "back-end", "api", "server", "database"],
        "data": ["data", "analytics", "ml", "ai", "machine learning", "sql"],
        "devops": ["devops", "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd"],
        "mobile": ["mobile", "ios", "android", "react native", "flutter"],
    }

    def calculate_match_score(job_title: str, job_text: str) -> tuple[float, list]:
        score = 0.0
        matched = []

        # Combine title and description for matching
        full_text = f"{job_title} {job_text}" if job_text else job_title
        job_lower = full_text.lower()

        # Count total relevant skills (skip common words)
        common_words = {"html", "css", "linux", "rest", "agile", "scrum", "git", "api"}
        relevant_skills = [s for s in resume_skills if s.lower() not in common_words]
        total_skill_weight = (
            len(relevant_skills) if relevant_skills else len(resume_skills)
        )

        skill_match_weight = 0
        title_matches = []

        for skill in resume_skills:
            skill_lower = skill.lower()

            if skill_lower in job_lower:
                skill_match_weight += 1.0
                matched.append(skill)
                # Track if matched in title
                if skill_lower in job_title.lower():
                    title_matches.append(skill)
                continue

            for category, variations in job_keywords.items():
                if skill_lower in variations or any(
                    v in skill_lower for v in variations
                ):
                    if any(v in job_lower for v in [skill_lower] + variations):
                        skill_match_weight += 0.7
                        if skill not in matched:
                            matched.append(skill)
                            if skill_lower in job_title.lower():
                                title_matches.append(skill)
                        break

        # Skill score - weighted more toward exact matches
        if total_skill_weight > 0:
            skill_score = (skill_match_weight / total_skill_weight) * 0.5
            score += skill_score

        # Title overlap - improved algorithm
        title_words = set(re.findall(r"\b[a-z]{3,}\b", job_title.lower()))
        resume_words = set(re.findall(r"\b[a-z]{3,}\b", resume_text))

        # Filter out common words from both
        stop_words = {
            "and",
            "the",
            "with",
            "for",
            "looking",
            "needed",
            "required",
            "experience",
            "years",
        }
        title_words = title_words - stop_words
        resume_words = resume_words - stop_words

        overlap = title_words & resume_words
        if title_words:
            title_overlap = len(overlap) / max(len(title_words), 1)
            score += title_overlap * 0.2

        # Description keyword boost
        if job_text and len(job_text) > 50:
            desc_words = (
                set(re.findall(r"\b[a-z]{3,}\b", job_text.lower())) & resume_words
            )
            if len(desc_words) > 0:
                score += min(
                    len(desc_words) * 0.02, 0.1
                )  # Up to 10% bonus for description matches

        # Experience bonus - more generous
        exp_keywords = [
            "years",
            "experience",
            "senior",
            "junior",
            "lead",
            "manager",
            "principal",
            "staff",
        ]
        if any(kw in job_lower for kw in exp_keywords):
            if any(kw in resume_text for kw in exp_keywords):
                score += 0.1

        # Boost for exact matches in title
        for skill in title_matches:
            score += 0.08  # Extra boost for skills in job title

        score = min(score, 1.0)

        return round(score, 2), matched

    matched_jobs = []

    for job in jobs:
        job_text = job.get("description", "") or ""
        job_title = job.get("title", "")

        score, matched_skills = calculate_match_score(job_title, job_text)

        if score >= min_score:
            matched_jobs.append(
                {
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "work_type": job.get("work_type"),
                    "salary": job.get("salary"),
                    "url": job.get("url"),
                    "description": job.get("description", ""),
                    "relevance_score": score,
                    "matched_skills": matched_skills,
                    "htl": score >= 0.6,
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
            "all_matched_jobs": matched_jobs[:50],
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
    job_data: str = "{}",
    resume_data: str = "{}",
    user_name: str = "",
    format_style: str = "paragraph",
) -> Dict[str, Any]:
    """
    Generate a complete email-style job application using AI.

    Args:
        job_data: JSON string with job title, company, description, requirements
        resume_data: JSON string with full resume data (skills, experience, raw text)
        user_name: Optional user name (ignored - extracted from resume if available)

    Returns:
        JSON string with complete email application ready to send
    """
    try:
        job = json.loads(job_data)
        resume = json.loads(resume_data)
    except json.JSONDecodeError:
        return json.dumps(
            {"status": "error", "message": "Invalid JSON in job or resume data"},
            indent=2,
        )

    format_style = format_style or "paragraph"

    job_title = job.get("title", "the position")
    company = job.get("company", "the company")
    job_description = job.get("description", job.get("requirements", ""))

    resume_text = resume.get("text", resume.get("raw", ""))
    resume_skills = resume.get("skills", [])
    resume_experience = resume.get("experience", [])
    resume_education = resume.get("education", [])

    applicant_name = resume.get("name", user_name) or "[Your Name]"

    if not resume_text:
        return json.dumps(
            {
                "status": "error",
                "message": "No resume content provided. Please upload or paste your resume first.",
            },
            indent=2,
        )

    if not job_description:
        job_description = "Please match the candidate's skills to the job requirements"

    resume_context = (
        f"Skills: {', '.join(resume_skills[:15]) if resume_skills else 'None listed'}"
    )
    if resume_experience:
        resume_context += f"\nExperience: {'; '.join(resume_experience[:3])}"
    if resume_education:
        resume_context += f"\nEducation: {'; '.join(resume_education[:2])}"
    resume_context += f"\n\nFull Resume:\n{resume_text[:2500]}"

    if format_style == "paragraph":
        prompt = f"""Write a professional job application email in this exact format (no JSON):

Subject: Application for [Job Title] - [Your Name]

Hi,

[2-3 sentences: state interest in the position, mention how you found it, briefly state your key qualification]

[2-3 sentences: highlight qualifications that directly match the job requirements. Use keywords from the job posting]

[2-3 sentences: summarize your most relevant work experience that applies to this role]

[One line: comma-separated list of 4-6 skills you have that match the job requirements]

[I am fully available to work (remote/hybrid/onsite) and can accommodate (any specific hours/timezone mentioned)].

Thank you for considering my application. I look forward to discussing how my skills can contribute to your team.

Best regards,
[Your Full Name]
[Your contact info]

Job Requirements:
{job_description}

Your Resume:
{resume_context}

Rules:
- Write based ONLY on what's in the job requirements
- Only mention skills/tools that appear in the job posting
- Keep email under 400 words
- Use professional but friendly tone"""
    else:
        prompt = f"""You are a professional job application writer for OnlineJobs.ph.

CRITICAL INSTRUCTION: Write the application based ONLY on the job requirements below. Do NOT invent job requirements or company details. Do NOT mention skills or experience from your resume that are NOT mentioned in the job posting.

**Job Details (THIS IS THE ONLY SOURCE OF TRUTH):**
- Position: {job_title}
- Company: {company}
- Requirements: {job_description}

**Candidate's Resume:**
{resume_context}

**Task:**
Create a complete application message that addresses EXACTLY what the job posting asks for.

{{
  "subject": "Application for [Position Title] - [Your Name]",
  "greeting": "Dear Hiring Manager," or "Hi,",
  "introduction": "2-3 sentence introduction. State your interest in the position and how you found it.",
  "qualifications": "2-3 sentences highlighting qualifications that DIRECTLY MATCH the job requirements. ONLY mention skills/experience that are IN THE JOB POSTING. Use keywords from the job description verbatim.",
  "experience_summary": "2-3 sentences about relevant experience. Focus on what matches the job requirements.",
  "skills_match": "List 4-6 skills that EXACTLY match what's in the job requirements section. Do NOT add resume skills that aren't in the job posting.",
  "availability": "One sentence about availability. If the job mentions specific hours or timezone, state that you can accommodate.",
  "closing": "1-2 sentence professional closing.",
  "signature_name": "Applicant's full name from resume",
  "signature_contact": "Contact info"
}}

Rules:
- ONLY mention tools/technologies that appear in the job requirements
- Do NOT mention a company name unless it's in the job posting
- Do NOT claim experience with tools/frameworks not listed in the job
- If the job mentions "Codex" or "Cursor" or specific tools, mention YOUR experience with those specific tools if you have it
- Keep total email under 400 words
- Return ONLY valid JSON"""

    try:
        result_text = None

        if openai_client:
            try:
                response = openai_client.chat.completions.create(
                    model="openrouter/auto",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional job application writer. Return ONLY valid JSON with no markdown formatting.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=2000,
                    temperature=0.7,
                )
                result_text = response.choices[0].message.content
            except Exception as e:
                print(f"OpenRouter error: {e}")

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
                {
                    "status": "error",
                    "message": "No AI provider available. Please check your API keys.",
                },
                indent=2,
            )

        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip().rstrip("```").rstrip()

        if format_style == "paragraph":
            subject_match = (
                result_text.split("\n")[0]
                if result_text
                else f"Application for {job_title}"
            )
            if "Subject:" in subject_match:
                subject = subject_match.split("Subject:")[1].strip()
            else:
                subject = f"Application for {job_title}"

            email_body = result_text.replace(f"Subject: {subject}", "").strip()

            return json.dumps(
                {
                    "status": "success",
                    "email": {
                        "subject": subject,
                        "body": email_body,
                        "full_email": f"Subject: {subject}\n\n{email_body}",
                    },
                    "applicant_name": applicant_name,
                    "match_score": job.get("relevance_score", 0),
                },
                indent=2,
            )

        result = json.loads(result_text)

        email_body = f"""{result.get("greeting", "Dear Hiring Manager,")}

{result.get("introduction", f"I am writing to express my interest in the {job_title} position at {company}.")}

{result.get("qualifications", "")}

{result.get("experience_summary", "")}

{result.get("skills_match", "")}

{result.get("availability", "")}

{result.get("closing", "Thank you for considering my application. I look forward to hearing from you.")}

Best regards,
{result.get("signature_name", applicant_name)}
{result.get("signature_contact", "Available for interview at your convenience")}"""

        return json.dumps(
            {
                "status": "success",
                "email": {
                    "subject": result.get("subject", f"Application for {job_title}"),
                    "body": email_body.strip(),
                    "full_email": f"Subject: {result.get('subject', f'Application for {job_title}')}\n\n{email_body.strip()}",
                },
                "applicant_name": result.get("signature_name", applicant_name),
                "match_score": job.get("relevance_score", 0),
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"status": "error", "message": f"Failed to parse AI response: {str(e)}"},
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"status": "error", "message": f"Failed to generate application: {str(e)}"},
            indent=2,
        )


async def auto_apply_job(job_url: str, application_message: str = "") -> Dict[str, Any]:
    """
    Try to automatically apply to a job on OnlineJobs.ph using Playwright.

    Args:
        job_url: URL of the job posting
        application_message: Optional application message/cover letter

    Returns:
        JSON with status and details of the application attempt
    """
    import asyncio
    import re

    def _apply_sync():
        from playwright.sync_api import sync_playwright
        from pathlib import Path

        cookies_file = Path(__file__).parent.parent / "browser_data" / "cookies.json"

        p = sync_playwright().start()
        try:
            browser = p.chromium.launch(
                headless=True, args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context()
            context.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            if cookies_file.exists():
                cookies = json.loads(cookies_file.read_text())
                context.add_cookies(cookies)

            page = context.new_page()
            page.set_default_timeout(60000)

            # Navigate to job page
            page.goto(job_url)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            result = {
                "page_title": page.title(),
                "url": page.url,
                "found_apply_button": False,
                "apply_button_text": "",
                "found_contact_info": False,
                "contact_info": "",
                "form_fields_found": [],
                "success": False,
                "message": "",
            }

            # Check for apply buttons
            apply_selectors = [
                'button:has-text("Apply")',
                'a:has-text("Apply")',
                'button:has-text("Apply Now")',
                'a:has-text("Apply Now")',
                'button:has-text("Submit Application")',
                'button[type="submit"]',
                'input[type="submit"]',
            ]

            for selector in apply_selectors:
                buttons = page.locator(selector).all()
                for btn in buttons:
                    try:
                        text = btn.inner_text().strip()
                        if text and len(text) < 50:
                            result["found_apply_button"] = True
                            result["apply_button_text"] = text
                            break
                    except Exception:
                        continue
                if result["found_apply_button"]:
                    break

            # Check for contact info / employer response options
            contact_selectors = [
                "text=Contact",
                "text=Contact Employer",
                "text=Message",
                "[id*='message']",
                "textarea",
            ]

            for selector in contact_selectors:
                el = page.locator(selector).first
                if el.count() > 0:
                    result["found_contact_info"] = True
                    result["form_fields_found"].append(selector)

            # Get any visible contact information
            email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
            content = page.content()

            emails = re.findall(email_pattern, content)
            if emails:
                result["contact_info"] = emails[0]

            # Try to click "Contact Us" button and fill form
            contact_button_selectors = [
                'button:has-text("Contact")',
                'a:has-text("Contact")',
                'button:has-text("Contact Us")',
                'a:has-text("Contact Us")',
                'button:has-text("Message")',
            ]

            for selector in contact_button_selectors:
                btn = page.locator(selector).first
                if btn.count() > 0:
                    try:
                        btn.click()
                        page.wait_for_timeout(1500)
                        result["clicked_contact_button"] = True
                        break
                    except Exception:
                        continue

            # Find and fill the message textarea
            if application_message:
                message_textareas = [
                    "textarea[id*='message']",
                    "textarea[name*='message']",
                    "textarea[id*='Message']",
                    "textarea",
                    "textarea[class*='message']",
                    "[contenteditable='true']",
                ]

                for selector in message_textareas:
                    textarea = page.locator(selector).first
                    if textarea.count() > 0:
                        try:
                            textarea.fill(application_message)
                            result["filled_message"] = True
                            result["form_fields_found"].append(f"filled: {selector}")
                            break
                        except Exception:
                            continue

                # Submit the form
                submit_selectors = [
                    'button:has-text("Send")',
                    'button:has-text("Submit")',
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Send Message")',
                ]

                for selector in submit_selectors:
                    submit_btn = page.locator(selector).first
                    if submit_btn.count() > 0:
                        try:
                            submit_btn.click()
                            page.wait_for_timeout(2000)
                            result["submitted"] = True
                            result["message"] = "Application submitted successfully!"
                            break
                        except Exception:
                            continue

            # Check if we can apply
            if (
                result.get("submitted")
                or result["found_apply_button"]
                or result["found_contact_info"]
            ):
                if not result.get("submitted"):
                    result["success"] = True
                    result["message"] = "Found application controls on the page"
            else:
                result["message"] = (
                    "No obvious apply button found - may require login or be expired"
                )

            browser.close()
            return result

        except Exception as e:
            try:
                p.stop()
            except Exception:
                pass
            return {"success": False, "message": f"Error: {str(e)}"}

    try:
        result = await asyncio.to_thread(_apply_sync)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)
