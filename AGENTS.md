# JobHunter Agent - Development Guide

## Architecture

- **Agent Type**: Standard ADK (`adk`)
- **Prototype**: Yes (local development)
- **Deployment Target**: None (prototype)

## Key Files

| File | Purpose |
|------|---------|
| `app/agent.py` | Agent definition with tools and instructions |
| `app/tools.py` | Custom tools: scraper, parser, matcher, cover letter |
| `app/__init__.py` | App entry point |
| `ui/index.html` | A2UI-inspired web interface (Light Soft style) |
| `server.py` | FastAPI backend for UI integration |

## Development Commands

```bash
# Install dependencies
uv sync

# Run playground
agents-cli playground

# Test prompt
agents-cli run "Find Python jobs"

# Lint
agents-cli lint

# Run UI Server
uv run python server.py
# Then open http://127.0.0.1:8000
```

## Tools

1. **scrape_onlinejobs** - Scrapes OnlineJobs.ph for job listings
2. **parse_resume** - Parses resume (text or PDF)
3. **match_jobs_to_resume** - Ranks jobs by relevance (HTL)
4. **generate_cover_letter** - Creates personalized cover letters

## Constraints

- Rate limit scraping to respect OnlineJobs.ph ToS
- Minimum HTL score: 0.5 (configurable via .env)
- Maximum job results: 20 (configurable)