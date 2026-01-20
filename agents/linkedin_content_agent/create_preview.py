
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from the agent directory
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir) # For 'agents' package resolution if needed

# Load environment variables
load_dotenv(os.path.join(root_dir, '.env'))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from .agent import root_agent

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'linkedin_post_template.html')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'linkedin_preview.html')

async def main():
    print("🚀 Starting LinkedIn Preview Generator...")
    
    # Initialize session
    session_service = InMemorySessionService()
    session_id = "preview_session_1"
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

    # --- Step 1: Initial Request ---
    topic = "The Future of AI in Healthcare"
    query = f"Create a LinkedIn post about: {topic}. Use Nano Banana style for the image."
    print(f"📝 Step 1: Requesting post about '{topic}'...")

    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print("   (Agent draft received)")

    # --- Step 2: Auto-Validation (Simulating User) ---
    print("✅ Step 2: Validating result...")
    validation_msg = "It looks great, I validate this."
    
    final_post_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=validation_msg)]
        ),
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_post_text = event.content.parts[0].text
                print("   (Final confirmation received)")
            else:
                 print("   (Warning: empty final response)")

    # --- Step 3: Extract Data and Render HTML ---
    print("🎨 Step 3: Generating HTML preview...")
    
    # Get state to find image URL
    session = await session_service.get_session(app_name="linkedin_content_agent", user_id=user_id, session_id=session_id)
    if session is None:
         # Try with just session_id if user_id was implicit
         try:
             session = await session_service.get_session(session_id=session_id)
         except:
             pass
    
    if session:
        image_info = session.state.get("generated_image", {})
    else:
        print("⚠️ Warning: Could not retrieve session.")
        image_info = {}
    image_url = image_info.get("url", "")
    
    if not image_url:
        print("⚠️ Warning: No image URL found in session state.")
    else:
        print(f"   Image found: {image_url[:50]}...")

    # Read Template
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Replace Placeholders
    # Simple formatting to html line breaks if needed, usually css 'white-space: pre-wrap' handles it
    html_content = html_content.replace('{{ POST_CONTENT }}', final_post_text)
    html_content = html_content.replace('{{ IMAGE_URL }}', image_url)
    
    # Handle conditional image block in a simple way (since we are avoiding jinja2 dependency for now if not present)
    # Actually my template used jinja-like syntax {% if %}. I'll rudimentary parsing or just replace blocks.
    # To be safe and simple:
    if image_url:
        html_content = html_content.replace('{% if IMAGE_URL %}', '').replace('{% else %}', '<!--').replace('{% endif %}', '-->')
    else:
        html_content = html_content.replace('{% if IMAGE_URL %}', '<!--').replace('{% else %}', '-->').replace('{% endif %}', '')

    # Save Output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✨ Success! Preview generated at:\n   {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
