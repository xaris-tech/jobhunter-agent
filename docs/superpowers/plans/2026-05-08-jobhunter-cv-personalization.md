# JobHunter CV Personalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AI-powered CV personalization that re-frames experience and generates targeted content for each job application.

**Architecture:** The `customize_cv()` tool uses Gemini LLM to analyze job descriptions + resume, then outputs structured JSON with personalized summary, experience highlights, and optimized skills. User reviews/edits the AI draft before sending.

**Tech Stack:** Gemini (google.genai), FastAPI, Playwright, ADK Agent

---

## File Structure

| File | Purpose |
|------|---------|
| `app/tools.py` | Add `customize_cv()` function with LLM integration |
| `app/agent.py` | Add `customize_cv` tool to agent |
| `server.py` | Add `/api/customize_cv` endpoint |
| `ui/index.html` | Add CV preview panel, edit capabilities, apply flow |

---

## Task 1: Add `customize_cv()` Tool

**Files:**
- Modify: `app/tools.py:380-384` (add new function)
- Test: `app/tools.py` (manual test via server)

**Approach:** Use Gemini LLM to generate personalized CV content from job description + resume data.

- [ ] **Step 1: Add imports for Gemini**

Add to top of `app/tools.py`:
```python
import os
from google import genai
```

- [ ] **Step 2: Add Gemini client initialization**

Add after imports (around line 5):
```python
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
```

- [ ] **Step 3: Add `customize_cv()` function**

Add at end of `app/tools.py` (after `generate_cover_letter`):
```python
async def customize_cv(
    job_data: str = "{}",
    resume_data: str = "{}",
    user_name: str = ""
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
        return json.dumps({
            "status": "error",
            "message": "Invalid JSON in job or resume data"
        }, indent=2)

    job_title = job.get("title", "the position")
    company = job.get("company", "the company")
    job_description = job.get("description", job.get("requirements", ""))
    
    skills = resume.get("skills", [])
    experience = resume.get("experience", [])
    
    if not job_description:
        job_description = f"Looking for candidates with skills in: {', '.join(skills[:10])}"

    prompt = f"""You are a professional CV writer specializing in ATS optimization.
Create a personalized CV for a job application.

**Job Details:**
- Position: {job_title}
- Company: {company}
- Requirements: {job_description}

**Candidate Profile:**
- Skills: {', '.join(skills) if skills else 'Not specified'}
- Experience: {'; '.join(experience) if experience else 'Not specified'}
{f'- Name: {user_name}' if user_name else ''}

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
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        result_text = response.text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip().rstrip("```")
        
        result = json.loads(result_text)
        
        return json.dumps({
            "status": "success",
            **result
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to generate personalized CV: {str(e)}",
            "personalized_cv": {
                "summary": f"Experienced professional interested in {job_title} role at {company}.",
                "experience": [{"title": "Experience", "company": "Previous employer", "highlights": skills[:3]}],
                "skills": ", ".join(skills[:10]) if skills else "Various technical skills"
            },
            "ats_score": 50,
            "match_insights": "Fallback: using basic matching due to AI generation error"
        }, indent=2)
```

- [ ] **Step 4: Test the function**

Run: `uv run python -c "from app.tools import customize_cv; import asyncio; print(asyncio.run(customize_cv('{\"title\":\"Python Developer\",\"company\":\"TechCorp\",\"description\":\"Need Python, React, AWS experience\"}', '{\"skills\":[\"Python\",\"React\",\"AWS\",\"Docker\"]}', 'John')))" 2>&1`

Expected: JSON output with personalized_cv, ats_score, match_insights

---

## Task 2: Update Agent with New Tool

**Files:**
- Modify: `app/agent.py` (add tool, update instructions)

- [ ] **Step 1: Import the new tool**

Modify imports:
```python
from .tools import (
    scrape_onlinejobs,
    parse_resume,
    match_jobs_to_resume,
    generate_cover_letter,
    customize_cv,
)
```

- [ ] **Step 2: Add tool to agent**

Add `FunctionTool(customize_cv)` to the tools list and update instructions to include CV personalization.

---

## Task 3: Add API Endpoint

**Files:**
- Modify: `server.py` (add endpoint)

- [ ] **Step 1: Add import**

Add `customize_cv` to imports from `app.tools`

- [ ] **Step 2: Add endpoint**

```python
@app.post("/api/customize_cv")
async def api_customize_cv(request: Request):
    body = await request.json()
    job_data = body.get("job_data", "{}")
    resume_data = body.get("resume_data", "{}")
    user_name = body.get("user_name", "")
    result = await customize_cv(job_data, resume_data, user_name)
    return json.loads(result)
```

---

## Task 4: Update UI with CV Preview Panel

**Files:**
- Modify: `ui/index.html` (add CV preview, edit, apply flow)

- [ ] **Step 1: Add CV preview modal HTML**

Add after cover letter section:
```html
<div class="card hidden" id="cvPreviewSection">
  <h2 class="card-title">
    <span class="card-title-icon">📋</span>
    Personalized CV
    <span id="atsScore" style="margin-left: auto; font-size: 13px; color: var(--success);"></span>
  </h2>
  <div id="cvPreviewContent">
    <div class="cv-section">
      <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">Summary</h3>
      <div id="cvSummary" contenteditable="true" style="padding: 12px; background: var(--bg); border-radius: 8px; min-height: 60px;"></div>
    </div>
    <div class="cv-section" style="margin-top: 16px;">
      <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">Experience</h3>
      <div id="cvExperience"></div>
    </div>
    <div class="cv-section" style="margin-top: 16px;">
      <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">Skills</h3>
      <div id="cvSkills" contenteditable="true" style="padding: 12px; background: var(--bg); border-radius: 8px;"></div>
    </div>
  </div>
  <div class="cv-insights" id="cvInsights" style="margin-top: 16px; padding: 12px; background: #EFF6FF; border-radius: 8px; font-size: 13px;"></div>
  <div class="btn-group" style="margin-top: 20px;">
    <button class="btn btn-secondary" onclick="regenerateCV()">Regenerate</button>
    <button class="btn btn-primary" onclick="sendApplication()">Send Application</button>
  </div>
</div>
```

- [ ] **Step 2: Add JavaScript functions**

Add to `<script>` section:
```javascript
async function generateCV(jobIndex) {
  const job = appState.jobs.results[jobIndex];
  if (!appState.resume.parsed) {
    alert('Please parse your resume first');
    return;
  }
  
  setStatus('Generating personalized CV...', true);
  
  try {
    const response = await fetch('/api/customize_cv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_data: JSON.stringify(job),
        resume_data: JSON.stringify(appState.resume),
        user_name: ''
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      showCVPreview(data);
      setStatus('CV ready for review', false);
    }
  } catch (error) {
    setStatus('Error', false);
    alert('Failed to generate CV: ' + error.message);
  }
}

function showCVPreview(data) {
  const section = document.getElementById('cvPreviewSection');
  const atsBadge = document.getElementById('atsScore');
  const summary = document.getElementById('cvSummary');
  const experience = document.getElementById('cvExperience');
  const skills = document.getElementById('cvSkills');
  const insights = document.getElementById('cvInsights');
  
  atsBadge.textContent = `ATS Score: ${data.ats_score}%`;
  atsBadge.style.color = data.ats_score >= 80 ? 'var(--success)' : 
                         data.ats_score >= 60 ? 'var(--warning)' : 'var(--text-secondary)';
  
  summary.textContent = data.personalized_cv.summary;
  
  experience.innerHTML = data.personalized_cv.experience.map(exp => `
    <div style="margin-bottom: 12px; padding: 12px; background: var(--bg); border-radius: 8px;">
      <div style="font-weight: 600;">${exp.title}</div>
      <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">${exp.company}</div>
      <ul style="margin: 0; padding-left: 20px;">
        ${exp.highlights.map(h => `<li>${h}</li>`).join('')}
      </ul>
    </div>
  `).join('');
  
  skills.textContent = data.personalized_cv.skills;
  insights.textContent = data.match_insights;
  
  section.classList.remove('hidden');
  section.scrollIntoView({ behavior: 'smooth' });
}

function regenerateCV() {
  if (appState.selectedJob) {
    const jobIndex = appState.jobs.results.findIndex(j => j.title === appState.selectedJob.title);
    if (jobIndex >= 0) generateCV(jobIndex);
  }
}

function sendApplication() {
  alert('Application sent! (This would integrate with email/job portal in production)');
  document.getElementById('cvPreviewSection').classList.add('hidden');
}
```

- [ ] **Step 3: Update job card click handler**

Modify `selectJob()` to call `generateCV(index)` instead of just generating cover letter:
```javascript
async function selectJob(index) {
  const job = appState.jobs.results[index];
  const matched = appState.jobs.matched.find(m => m.title === job.title);
  appState.selectedJob = { ...job, ...matched };
  
  // Highlight selected card
  document.querySelectorAll('.job-card').forEach(card => {
    card.style.borderLeftColor = card.classList.contains('score-high') ? 'var(--success)' :
                                card.classList.contains('score-medium') ? 'var(--warning)' : 'var(--border)';
  });
  const selectedCard = document.querySelector(`[data-index="${index}"]`);
  if (selectedCard) selectedCard.style.borderLeftColor = 'var(--secondary)';
  
  await generateCV(index);
}
```

- [ ] **Step 4: Test the UI**

Start server, open http://127.0.0.1:8001, parse resume, search jobs, click a job card.

---

## Task 5: Commit Changes

- [ ] **Step 1: Push to GitHub**

```bash
git add -A
git commit -m "feat: add AI-powered CV personalization with Gemini LLM

- Add customize_cv() tool for job-specific CV generation
- Add /api/customize_cv endpoint
- Add CV preview panel with editable sections
- ATS scoring and match insights
- User can edit and send application"
git push
```

---

## Success Criteria

- [ ] AI generates personalized CV in < 5 seconds
- [ ] User can edit all sections before sending
- [ ] ATS keyword score improves vs original CV
- [ ] UI is intuitive — no learning curve
- [ ] Works with/without job description input