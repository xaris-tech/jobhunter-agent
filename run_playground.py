"""Run ADK Playground Server"""

import os

from dotenv import load_dotenv
from google.adk.cli.fast_api import get_fast_api_app
import uvicorn

load_dotenv()


def main():
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project or project == "your-project-id":
        print("ERROR: Please set GOOGLE_CLOUD_PROJECT in .env file")
        return

    print("Starting JobHunter Playground...")
    print(f"Project: {project}, Location: {location}")
    print("Open http://127.0.0.1:8080 in your browser")

    app = get_fast_api_app(agents_dir="app", web=True, host="127.0.0.1", port=8080)

    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
