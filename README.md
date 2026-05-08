# JobHunter Agent

An AI-powered job search agent that scrapes jobs from OnlineJobs.ph, parses resumes, matches jobs with relevance scoring (HTL), and generates personalized cover letters.

## Features

- **Job Scraping** - Extract job listings from OnlineJobs.ph using Playwright
- **Resume Parsing** - Parse resume text/PDF to extract skills, experience, education
- **Job Matching** - Rank jobs by relevance to your resume (HTL scoring)
- **Cover Letter Generation** - Create personalized cover letters for matched jobs
- **Web UI** - A2UI-inspired visualization interface with Light Soft design

## Quick Start

```bash
# Clone the repo
git clone https://github.com/xaris-tech/jobhunter-agent.git
cd jobhunter-agent

# Install dependencies
uv sync

# Run the UI server
uv run python server.py

# Open http://127.0.0.1:8000
```

## Development

```bash
# Run agent playground
agents-cli playground

# Test with prompt
agents-cli run "Find Python jobs"

# Lint
agents-cli lint
```

## Architecture

```
jobhunter-agent/
├── app/
│   ├── agent.py      # ADK agent definition
│   ├── tools.py      # Custom tools (scrape, parse, match, cover letter)
│   └── __init__.py   # App entry point
├── ui/
│   └── index.html    # A2UI-inspired web interface
├── server.py         # FastAPI backend for UI
├── pyproject.toml    # Project dependencies
└── AGENTS.md         # Development guide
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/api/parse_resume` | POST | Parse resume text |
| `/api/scrape_jobs` | POST | Scrape jobs from OnlineJobs.ph |
| `/api/match_jobs` | POST | Match jobs to resume |
| `/api/generate_cover_letter` | POST | Generate cover letter |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_HTL_SCORE` | 0.5 | Minimum relevance score |
| `MAX_RESULTS` | 20 | Max jobs to return |

## License

MIT