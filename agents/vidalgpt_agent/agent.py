from google.adk.agents import Agent
from google.adk.tools import google_search


root_agent = Agent(
    name="google_search_agent",
    model="gemini-2.0-flash-exp",
    description="Agent to answer questions using Google Search.",
    instruction="I can answer your questions by searching the internet. However, you must ONLY search on vidal.fr.",
    tools=[google_search]
)

