import os
import asyncio
import logging
# Configure logging to suppress debug spam if needed
logging.basicConfig(level=logging.ERROR)

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

# 1. Initialize the Artifact Service
# We use FileArtifactService which creates versioned artifacts
# root_dir corresponds to the base directory for artifacts
from google.adk.tools import ToolContext

# 2. Define the HTML Tool
async def save_web_content(tool_context: ToolContext, html_code: str, file_name: str = "index.html"):
    """
    Saves or updates HTML code. 
    Use this whenever the user asks for a change or a new page.
    """
    # Create the artifact using the ADK service via ToolContext
    # This automatically handles app_name, user_id, and session scoping
    try:
        await tool_context.save_artifact(
            filename=file_name,
            artifact=types.Part.from_text(text=html_code),
            custom_metadata={"type": "web_page", "language": "html"}
        )
    except Exception as e:
        print(f"Warning: Failed to save to artifact service: {e}")
    
    # Also write to local disk for immediate browser preview
    # This is critical for the "Live Preview" feature mentioned in the issue
    try:
        with open(file_name, "w") as f:
            f.write(html_code)
        return f"Successfully updated {file_name}. You can preview it in the 'Artifacts' tab."
    except Exception as e:
        return f"Error writing file: {e}"

# 3. Configure the Agent
root_agent = Agent(
    name="WebDesigner",
    model="gemini-2.5-flash", # Explicit model choice
    instruction="""
    You are an expert Frontend Developer. 
    Your goal is to build and refine HTML pages based on user feedback.
    
    FLOW:
    1. If the user asks for a design, generate the full HTML/CSS.
    2. Use 'save_web_content' to store your code.
    3. If the user asks for a change, read the previous code from your memory, 
       modify it, and call 'save_web_content' again with the full updated code.
    """,
    tools=[save_web_content]
)

# 4. Example Execution
if __name__ == "__main__":
    print("Testing save_web_content tool directly...")
    
    # Simple Mock for ToolContext
    class MockToolContext:
        async def save_artifact(self, filename, artifact, custom_metadata=None):
            print(f"Mock: Saving artifact {filename} with metadata {custom_metadata}")
            return "mock_version_id"

    mock_context = MockToolContext()
    
    test_html = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body><h1>Hello World</h1></body>
</html>"""
    
    # We use a test filename to avoid overwriting real index.html if it exists
    # Pass mock_context as first argument
    result = asyncio.run(save_web_content(mock_context, test_html, "test_index.html"))
    print(f"Tool Result: {result}")
    
    import os
    if os.path.exists("test_index.html"):
        print("Success: test_index.html created.")
        with open("test_index.html", "r") as f:
            print(f"Content: {f.read()}")
        # cleanup
        os.remove("test_index.html")
    else:
        print("Failure: test_index.html not created.")
