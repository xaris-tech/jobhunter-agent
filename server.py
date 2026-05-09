"""Backend API server for JobHunter Agent UI."""

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.tools import (
    scrape_onlinejobs,
    parse_resume,
    match_jobs_to_resume,
    generate_cover_letter,
    customize_cv,
    auto_apply_job,
)

app = FastAPI(title="JobHunter Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ui_dir = Path(__file__).parent / "ui"

if ui_dir.exists():
    app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")


@app.get("/")
async def root():
    index_path = ui_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "JobHunter API running. UI not found at /ui/index.html"}


@app.post("/api/parse_resume")
async def api_parse_resume(request: Request):
    body = await request.json()
    resume_text = body.get("resume_text", "")
    result = await parse_resume(resume_text=resume_text)
    parsed = json.loads(result)
    parsed["raw_text"] = resume_text
    parsed["name"] = ""
    return parsed


@app.post("/api/upload_resume")
async def api_upload_resume(file: UploadFile = File(...)):
    content = await file.read()

    if file.filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(content))
            text = "\n".join([page.extract_text() for page in reader.pages])
        except Exception as e:
            return {"status": "error", "message": f"Failed to read PDF: {str(e)}"}
    elif file.filename.endswith((".docx", ".doc")):
        try:
            from docx import Document
            import io

            doc = Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            return {"status": "error", "message": f"Failed to read DOCX: {str(e)}"}
    else:
        try:
            text = content.decode("utf-8")
        except:
            text = content.decode("latin-1")

    result = await parse_resume(resume_text=text)
    parsed = json.loads(result)
    parsed["raw_text"] = text
    parsed["name"] = ""
    return parsed


@app.post("/api/scrape_jobs")
async def api_scrape_jobs(request: Request):
    body = await request.json()
    search_query = body.get("search_query", "")
    max_results = body.get("max_results", 20)
    result = await scrape_onlinejobs(search_query, max_results)
    return json.loads(result)


@app.post("/api/match_jobs")
async def api_match_jobs(request: Request):
    body = await request.json()
    resume_data = body.get("resume_data", "{}")
    jobs_data = body.get("jobs_data", '{"jobs": []}')
    min_score = body.get("min_score", 0.5)
    result = await match_jobs_to_resume(resume_data, jobs_data, min_score)
    return json.loads(result)


@app.post("/api/generate_cover_letter")
async def api_generate_cover_letter(request: Request):
    body = await request.json()
    job_data = body.get("job_data", "{}")
    resume_data = body.get("resume_data", "{}")
    result = await generate_cover_letter(job_data, resume_data)
    return json.loads(result)


@app.post("/api/customize_cv")
async def api_customize_cv(request: Request):
    body = await request.json()
    job_data = body.get("job_data", "{}")
    resume_data = body.get("resume_data", "{}")
    user_name = body.get("user_name", "")
    result = await customize_cv(job_data, resume_data, user_name)
    return json.loads(result)


@app.post("/api/auto_apply")
async def api_auto_apply(request: Request):
    body = await request.json()
    job_url = body.get("job_url", "")
    application_message = body.get("application_message", "")

    if not job_url:
        return {"status": "error", "message": "No job URL provided"}

    result = await auto_apply_job(job_url, application_message)
    return json.loads(result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
