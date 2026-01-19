"""Test script for the LinkedIn Content Creation Agent."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, '.env'))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
try:
    from .agent import root_agent
except ImportError:
    from agent import root_agent



async def test_linkedin_agent():
    """Test the LinkedIn Content Creation Agent with a sample query and conversation loop."""

    print("🚀 Testing LinkedIn Content Creation Agent with Super Agent Loop...")
    print("=" * 60)

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

    # Step 1: Initial Request
    # ----------------------------------------------------------------------
    test_topic = "AI's impact on remote work productivity in 2024"
    query = f"Create a LinkedIn post about: {test_topic}"

    print(f"📝 User Step 1: {query}")
    print("\n" + "-" * 60)

    # Run step 1
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=query)]),
    ):
        if event.is_final_response():
             print(f"🤖 Agent Response 1:\n{event.content.parts[0].text}\n")


    # Step 2: Modification Request
    # ----------------------------------------------------------------------
    modification_query = "The post is good, but please change the image to be more 'cyberpunk' style."
    print(f"📝 User Step 2: {modification_query}")
    print("-" * 60)

    # Run step 2
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=modification_query)]),
    ):
        if event.is_final_response():
             print(f"🤖 Agent Response 2:\n{event.content.parts[0].text}\n")


    # Step 3: Validation
    # ----------------------------------------------------------------------
    validation_query = "Great, I validate this post."
    print(f"📝 User Step 3: {validation_query}")
    print("-" * 60)

    # Run step 3
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=validation_query)]),
    ):
        if event.is_final_response():
             print(f"🤖 Agent Response 3:\n{event.content.parts[0].text}\n")

    print("✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_linkedin_agent())
