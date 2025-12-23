"""Test script for the LinkedIn Content Creation Agent."""

import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from agent import root_agent


async def test_linkedin_agent():
    """Test the LinkedIn Content Creation Agent with a sample query."""

    print("🚀 Testing LinkedIn Content Creation Agent...")
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

    # Test query - feel free to modify this
    test_topic = "AI's impact on remote work productivity in 2024"

    query = f"""Create a LinkedIn post about: {test_topic}

Please research this topic thoroughly and create an engaging LinkedIn post that:
- Provides valuable insights
- Is optimized for LinkedIn engagement
- Includes relevant hashtags
- Has a professional tone
- Encourages discussion

Also generate a complementary image for the post."""

    print(f"📝 Query: {query}")
    print("\n" + "=" * 60)
    print("🔄 Processing... (this may take a moment)")
    print("=" * 60 + "\n")

    try:
        # Run the agent
        events = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=query)]
            ),
        ):
            events.append(event)

            # Print agent activity
            if event.author != "user" and event.content and event.content.parts:
                content = event.content.parts[0].text
                if content and len(content.strip()) > 0:
                    print(f"🤖 {event.author}:")
                    print(f"   {content[:200]}..." if len(content) > 200 else f"   {content}")
                    print()

            # Print final response
            if event.is_final_response():
                print("=" * 60)
                print("✅ FINAL RESULT:")
                print("=" * 60)
                print(event.content.parts[0].text)
                print("=" * 60)

        # Get session state to see intermediate results
        session = await session_service.get_session(
            app_name="linkedin_content_agent",
            user_id="test_user",
            session_id="test_session"
        )

        print("\n📊 SESSION STATE SUMMARY:")
        print("-" * 40)
        for key, value in session.state.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"{key}: {value[:100]}...")
            else:
                print(f"{key}: {value}")

        print(f"\nTotal events generated: {len(events)}")
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_individual_agents():
    """Test individual agents to debug any issues."""

    print("\n🔧 Testing individual agent components...")

    from agent import google_research_agent, linkedin_post_writer

    # Test Google research agent
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="test_individual",
        user_id="test_user",
        session_id="test_session"
    )

    runner = Runner(
        agent=google_research_agent,
        app_name="test_individual",
        session_service=session_service
    )

    print("\n🔍 Testing Google Research Agent:")
    query = "Research AI productivity tools for remote teams"

    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.is_final_response():
            print("Research result:", event.content.parts[0].text[:300] + "...")
            break


if __name__ == "__main__":
    print("LinkedIn Content Creation Agent - Test Suite")
    print("=" * 60)

    # Run main test
    asyncio.run(test_linkedin_agent())

    # Optionally run individual tests for debugging
    # asyncio.run(test_individual_agents())