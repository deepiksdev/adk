"""LinkedIn Content Creation Agent using Google ADK."""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types
from .tools import search_google, search_duckduckgo, generate_image, save_content_to_state, generate_nano_banana_image, generate_html_preview
import re
from typing import Optional


def content_guardrails_callback(callback_context: CallbackContext) -> Optional[genai_types.Content]:
    """
    Callback function to apply guardrails and formatting to LinkedIn content.

    Ensures content follows LinkedIn best practices:
    - Professional tone
    - Limited hashtags (max 3)
    - No external links
    - Proper formatting
    """
    try:
        # Get the agent's response from the last event
        session = callback_context._invocation_context.session
        if not session.events:
            return None

        last_event = session.events[-1]
        if not (last_event.content and last_event.content.parts):
            return None

        content_text = last_event.content.parts[0].text
        if not content_text:
            return None

        # Apply guardrails
        processed_content = apply_content_guardrails(content_text)

        # Return modified content if changes were made
        if processed_content != content_text:
            return genai_types.Content(
                parts=[genai_types.Part(text=processed_content)],
                role="model"
            )

        return None

    except Exception as e:
        print(f"Error in content guardrails callback: {e}")
        return None


def apply_content_guardrails(content: str) -> str:
    """Apply content guardrails to ensure LinkedIn compliance."""

    # Remove external links (keep LinkedIn-friendly format)
    content = re.sub(r'https?://[^\s]+', '', content)

    # Limit hashtags to maximum 3
    hashtags = re.findall(r'#\w+', content)
    if len(hashtags) > 3:
        # Keep only the first 3 hashtags
        for hashtag in hashtags[3:]:
            content = content.replace(hashtag, '', 1)

    # Ensure professional tone indicators are present
    professional_indicators = ['insights', 'thoughts', 'experience', 'learning', 'sharing', 'update']
    if not any(indicator in content.lower() for indicator in professional_indicators):
        # Add a professional touch if missing
        if not content.endswith('.'):
            content += '.'
        # content += "\n\nWhat are your thoughts on this?" # Optional, can be annoying if added every time

    # Clean up extra whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content


# Research Agents (Kept for potential sub-usage or structural clarity)
google_research_agent = Agent(
    name="google_research_agent",
    model="gemini-2.5-flash",
    description="Conducts Google searches.",
    instruction="Research the topic using search_google.",
    tools=[search_google, save_content_to_state]
)

duckduckgo_research_agent = Agent(
    name="duckduckgo_research_agent",
    model="gemini-2.5-flash",
    description="Conducts DuckDuckGo searches.",
    instruction="Research the topic using search_duckduckgo.",
    tools=[search_duckduckgo, save_content_to_state]
)

# New Super Agent implementation
root_agent = Agent(
    name="super_coordinator_agent",
    model="gemini-2.5-flash",
    description="A Super Agent that orchestrates the entire LinkedIn content creation process.",
    instruction="""You are the Super Agent for LinkedIn Content Creation.
    
    Your goal is to work with the user to create the PERFECT LinkedIn post.
    
    ### Process:
    1. **Understand Key Requirements**: Ask the user for the topic if not provided.
    2. **Research**: Use `search_google` and `search_duckduckgo` to gather insights on the logical topic.
    3. **Drafting**: Write a professional, engaging LinkedIn post based on the research.
       - Use a compelling hook.
       - Keep it concise (150-300 words).
       - Max 3 hashtags.
    4. **Visuals**: Generate a visual using `generate_nano_banana_image`.
       - ALWAYS use `generate_nano_banana_image` for the image.
       - The prompt should be creative and related to the post.
    5. **Review & Modify**:
       - Present the draft and the image to the user.
       - Ask: "Does this look good? Or would you like to modify the text or the image?"
       - **Critically**: If the user asks for changes (e.g., "Make it shorter", "Change image to be more blue"), MODIFY the specific part and show the updated version.
       - Continue this loop until the user explicitly confirms/validates the post.
    6. **Validation & Output**: 
       - When the user says "It's good" or "I validate this", you **MUST** call the tool `generate_html_preview`.
       - **DO NOT** just format the text as a preview. You **MUST** run the tool to create the actual file.
       - The tool will return a `preview_url`. **You must display this link as a clickable Markdown hyperlink.**
       - Say: "Here is your HTML preview link: [Click here to view preview](<preview_url>)"
    
    ### Tools Usage:
    - Use `search_google` / `search_duckduckgo` for information.
    - Use `generate_nano_banana_image` for ALL image generation.
    - Use `save_content_to_state` to checkpoint your drafts.
    - Use `generate_html_preview` **MANDATORY** after user validation.
    
    Be helpful, professional, and responsive to feedback.
    """,
    tools=[search_google, search_duckduckgo, generate_nano_banana_image, save_content_to_state, generate_html_preview],
    # We apply the guardrails callback to ensure the text output is always polished
    after_agent_callback=content_guardrails_callback
)
