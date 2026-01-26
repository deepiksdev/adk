from google.adk.agents import Agent
from google.adk.tools import google_search


root_agent = Agent(
    name="vidalgpt_agent",
    model="gemini-2.5-flash-lite",
    description="Agent to answer questions using Google Search.",
    instruction="I can answer your questions by searching the internet. However, you must ONLY search on vidal.fr.",
    tools=[google_search]
)

