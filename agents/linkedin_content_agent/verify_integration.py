
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from the agent directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from .agent import root_agent

async def main():
    print("🚀 Verifying HTML Preview Integration in Agent...")
    
    session_service = InMemorySessionService()
    session_id = "integration_test_session"
    user_id = "user_1"
    
    await session_service.create_session(
        app_name="linkedin_content_agent",
        user_id=user_id,
        session_id=session_id
    )

    runner = Runner(
        agent=root_agent,
        app_name="linkedin_content_agent",
        session_service=session_service
    )

    # Step 1: Request Post
    query = "Create a post about: AI in Education. Use Nano Banana style."
    print(f"📝 Step 1: User says: '{query}'")
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=query)])
    ):
        if event.is_final_response():
             if event.content and event.content.parts:
                print(f"   Agent response: {event.content.parts[0].text[:50]}...")

    # Step 2: Validate and Expect HTML Generation
    validation = "It's perfect, I validate this."
    print(f"✅ Step 2: User says: '{validation}'")
    print("   (Expecting agent to call generate_html_preview...)")

    html_file_found = False
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=validation)])
    ):
        # We want to check tool calls here ideally, but inspecting the text response is also good
        if event.is_final_response():
             if event.content and event.content.parts:
                text = event.content.parts[0].text
                print(f"   Agent Final Response: {text}")
                print(f"   Agent Final Response: {text}")
                # Check for standard markdown link format: [Text](URL)
                if "](" in text and "file:///" in text and ".html" in text:
                    print("   [SUCCESS] Agent provided a clickable Markdown file link.")
                    html_file_found = True
                else:
                    print("   [FAILURE] Agent did not provide a file link.")

    # Verify file existence
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    files = sorted([f for f in os.listdir(output_dir) if f.startswith('linkedin_preview_')], key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
    
    if files:
        print(f"📁 Found generated file: {files[0]}")
        print("🎉 Verification SUCCESS!")
    else:
        print("❌ Verification FAILED: No new HTML file found.")

if __name__ == "__main__":
    asyncio.run(main())
