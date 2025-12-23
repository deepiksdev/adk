"""Simple test script for the LinkedIn Content Creation Agent."""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from root .env file
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, '.env'))

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent import root_agent
from google.genai import types as genai_types


async def main():
    """Test the LinkedIn Content Creation Agent with a simple query."""

    # Initialize session service
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="linkedin_content_agent",
        user_id="test_user",
        session_id="test_session"
    )

    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name="linkedin_content_agent",
        session_service=session_service
    )

    # Test query
    query = "Create a LinkedIn post about the benefits of AI in software development"

    print(f"Query: {query}")
    print("Processing...")

    # Run the agent and capture final response
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.is_final_response():
            print("\n" + "="*50)
            print("FINAL LINKEDIN POST:")
            print("="*50)
            print(event.content.parts[0].text)
            print("="*50)


if __name__ == "__main__":
    asyncio.run(main())