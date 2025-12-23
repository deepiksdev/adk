#!/usr/bin/env python3
"""
Test script for customer service agent.
Imports the agent and tests basic functionality.
"""
import asyncio
import os
import sys

# Add current directory to path so we can import customer_service
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.customer_service.agent import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    print("✅ Successfully imported customer service agent")
    print(f"Agent name: {root_agent.name}")
    print(f"Agent model: {root_agent.model}")
    print(f"Number of tools: {len(root_agent.tools)}")

    # List available tools
    print("\nAvailable tools:")
    for tool in root_agent.tools:
        tool_name = getattr(tool, '__name__', str(tool))
        print(f"  - {tool_name}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to install dependencies with: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error initializing agent: {e}")
    sys.exit(1)


async def test_agent_response():
    """Test the customer service agent with a simple query."""
    try:
        session_service = InMemorySessionService()
        await session_service.create_session(
            app_name="customer_service", user_id="test_user", session_id="test_session"
        )

        runner = Runner(
            agent=root_agent,
            app_name="customer_service",
            session_service=session_service
        )

        query = "Hi, I need help with my garden plants"
        print(f"\n🤖 Testing with query: '{query}'")
        print("=" * 50)

        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=query)]
            ),
        ):
            if event.is_final_response():
                response = event.content.parts[0].text
                print(f"Agent response: {response}")
                return True

        print("❌ No response received from agent")
        return False

    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False


async def main():
    """Main test function."""
    print("Testing Customer Service Agent")
    print("=" * 40)

    # Test basic import and initialization
    if 'root_agent' not in globals():
        print("❌ Agent import failed")
        return False

    # Test agent response
    success = await test_agent_response()

    if success:
        print("\n✅ Customer service agent test completed successfully!")
        print("You can now run 'adk web' to interact with the agent in the browser.")
    else:
        print("\n❌ Customer service agent test failed")

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)