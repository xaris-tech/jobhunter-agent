# JobHunter Agent - Design Specification

## Overview
JobHunter is an ADK agent that helps users find matching jobs from OnlineJobs.ph based on their resume, ranks them by relevance (HTL - High-Target List), and generates tailored cover letters.

## Core Capabilities
1. **Resume Parser** - Parse user's resume (PDF/text) to extract skills, experience, and qualifications
2. **Job Scraper** - Custom scraper for OnlineJobs.ph to extract job listings
3. **Job Matching** - Match resume skills/experience to job requirements with relevance scoring
4. **HTL Filtering** - Only notify users of high-potential job matches (configurable threshold)
5. **Cover Letter Generator** - Generate tailored cover letters based on job descriptions

## Tools Required
- `scrape_onlinejobs` - Custom scraper for OnlineJobs.ph job listings
- `parse_resume` - Extract structured data from resume files
- `match_jobs` - Score and rank jobs against resume
- `generate_cover_letter` - Create personalized cover letters

## Constraints
- Rate limit scraping to respect OnlineJobs.ph ToS
- Store only session-scoped data (no persistent personal data)
- Filter jobs based on minimum relevance threshold for HTL

## Success Criteria
- Agent can parse resumes and extract key skills/experience
- Scraper successfully retrieves job listings from OnlineJobs.ph
- Matching algorithm produces relevant job recommendations
- Cover letters are personalized to each job description