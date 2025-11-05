#!/usr/bin/env python3
"""
Debug script to test customer service agent with detailed logging.
"""
import asyncio
import logging
import os
import sys

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug logging for customer service modules
logging.getLogger("customer_service").setLevel(logging.DEBUG)
logging.getLogger("google.adk").setLevel(logging.INFO)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from customer_service.agent import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    print("✅ Agent imported successfully")

except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


async def debug_agent_conversation():
    """Run a detailed debug conversation with the agent."""
    try:
        print("🔍 Starting debug conversation...")

        session_service = InMemorySessionService()
        await session_service.create_session(
            app_name="customer_service", user_id="debug_user", session_id="debug_session"
        )

        runner = Runner(
            agent=root_agent,
            app_name="customer_service",
            session_service=session_service
        )

        # Test with simple queries that should work
        test_queries = [
            "Hello, I need help with my account",
            "What products do you have?",
            "I want to return an item"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*50}")
            print(f"🤖 Test {i}: '{query}'")
            print('='*50)

            try:
                event_count = 0
                async for event in runner.run_async(
                    user_id="debug_user",
                    session_id="debug_session",
                    new_message=genai_types.Content(
                        role="user",
                        parts=[genai_types.Part.from_text(text=query)]
                    ),
                ):
                    event_count += 1
                    print(f"📨 Event {event_count}: {event.author}")

                    if event.content:
                        if hasattr(event.content, 'parts') and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    print(f"💬 Text: {part.text[:200]}...")
                                if hasattr(part, 'function_call') and part.function_call:
                                    print(f"🔧 Tool call: {part.function_call.name}")
                                if hasattr(part, 'function_response') and part.function_response:
                                    print(f"📋 Tool response: {str(part.function_response)[:100]}...")

                    if event.actions:
                        print(f"⚡ Actions: {event.actions}")

                    if event.error_message:
                        print(f"❌ Error: {event.error_message}")

                    if event.is_final_response():
                        print("✅ Final response received")
                        break

                if event_count == 0:
                    print("⚠️  No events received - this might be the issue!")

            except Exception as e:
                print(f"❌ Error in conversation {i}: {e}")
                import traceback
                traceback.print_exc()

            # Small delay between tests
            await asyncio.sleep(1)

    except Exception as e:
        print(f"❌ Debug conversation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(debug_agent_conversation())
    except KeyboardInterrupt:
        print("\n⚠️  Debug interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()