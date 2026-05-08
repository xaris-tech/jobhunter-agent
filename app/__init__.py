from google.adk.apps import App
from .agent import root_agent

App(name="jobhunter", root_agent=root_agent)
