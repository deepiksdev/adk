import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from plugins.logging_plugin import LoggingPlugin

load_dotenv()

async def test_logging():
    # 1. Define a simple agent
    agent = Agent(
        name="test_agent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant. Keep your responses short."
    )

    # 2. Initialize the LoggingPlugin
    logging_plugin = LoggingPlugin()

    # 3. Create a runner with the plugin
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="test_app",
        session_service=session_service,
        plugins=[logging_plugin]
    )

    # 4. Create a session
    user_id = "test_user"
    session_id = "test_session"
    await session_service.create_session(
        app_name="test_app", 
        user_id=user_id, 
        session_id=session_id
    )

    print("\n--- Starting Conversation ---")
    
    # 5. Run a conversation
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text="Hi, what is the capital of France?")]
        )
    ):
        if event.is_final_response():
            print(f"\nFinal Response: {event.content.parts[0].text}")

if __name__ == "__main__":
    asyncio.run(test_logging())
