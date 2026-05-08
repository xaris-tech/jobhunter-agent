# JobHunter CV Personalization - Design Specification

**Date:** 2026-05-08  
**Project:** AI-Powered CV Personalization for Job Applications  
**Approach:** B (Experience re-framing) + C (Full content generation)

## Overview

This enhancement adds AI-powered CV customization for each job application. Instead of a generic cover letter + resume, the system now:
1. Analyzes the job description for required skills and keywords
2. Re-frames existing experience to highlight relevant achievements
3. Generates targeted content that matches each job's requirements
4. Presents AI draft to user for review/editing before sending

## Architecture

### New Tool: `customize_cv`

```python
async def customize_cv(
    job_data: str,      # JSON with title, company, description, requirements
    resume_data: str,   # JSON with skills, experience, education
    user_name: str = "" # Optional: user name for personalization
) -> Dict[str, Any]
```

**Returns:**
```json
{
  "status": "success",
  "personalized_cv": {
    "summary": "Tailored professional summary highlighting relevant skills",
    "experience": [
      {
        "title": "Original title",
        "highlights": ["Reframed bullets matching job requirements"]
      }
    ],
    "skills": "Keyword-optimized skills section",
    "tailored_keywords": ["Extracted from job description"]
  },
  "ats_score": 85,  # Estimated ATS keyword match percentage
  "match_insights": "Why this CV matches the role"
}
```

### Data Flow

```
User Search → Scrape Job (with description) → Match Jobs
                                    ↓
                              Select Job → Customize CV (AI)
                                                   ↓
                                            AI Draft Generated
                                                   ↓
                                            User Reviews/Edits
                                                   ↓
                                            Send/Apply
```

## AI Personalization Logic

### Step 1: Job Analysis
- Extract key skills from job description (required vs preferred)
- Identify industry-specific keywords
- Parse experience requirements (years, level)

### Step 2: CV Re-framing
- Match resume experience bullets to job requirements
- Prioritize achievements that demonstrate required skills
- Re-order experiences to put most relevant first

### Step 3: Content Generation
- Rewrite professional summary with job-specific keywords
- Create targeted skills section matching job requirements
- Format experience bullets to mirror job description language

### Step 4: ATS Optimization
- Calculate keyword match score
- Suggest additional keywords to add
- Flag missing requirements

## UI Changes

### Search Section Enhancement
- Add "Job Description" textarea (optional input)
- If user pastes job description, use for deeper personalization
- Fallback: Use scraped job data (may be limited)

### Matched Jobs → Application Flow
1. User clicks "Apply" on job card
2. If job description available → Show CV customization preview
3. AI generates personalized CV
4. User reviews in modal/panel
5. User can edit text inline
6. "Send Application" button

### CV Review Panel
- Side-by-side view: Original CV ↔ Personalized CV
- Diff highlighting (optional)
- Edit buttons per section
- "Regenerate" button for AI revision

## API Changes

### New Endpoint: `/api/customize_cv`

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

### Tool Signature Changes

**scrape_onlinejobs** → Add optional `include_description` flag  
**match_jobs_to_resume** → Can also accept job description for scoring

## Implementation Notes

### LLM Integration
Use Gemini via `google.genai` to generate personalized content:
- System prompt: "You are a professional CV writer specializing in ATS optimization"
- Input: Job description + Resume + User name
- Output: Structured JSON with personalized sections

### Rate Limiting
- Cache generated CVs for 1 hour
- Avoid regenerating for same job (user might edit multiple times)
- Respect API limits

### Error Handling
- If LLM fails → Return original CV with warning
- If job description missing → Generate generic but still personalized
- Timeout handling → Show loading state with fallback

## Files to Modify

1. `app/tools.py` — Add `customize_cv()` function
2. `app/agent.py` — Add tool to agent, update instructions
3. `server.py` — Add API endpoint
4. `ui/index.html` — Add CV review panel, edit capabilities

## Success Criteria

- [ ] AI generates personalized CV in < 5 seconds
- [ ] User can edit all sections before sending
- [ ] ATS keyword score improves vs original CV
- [ ] UI is intuitive — no learning curve
- [ ] Works with/without job description input