"""Tools for the LinkedIn Content Creation Agent."""

import json
import os
from typing import Dict, List, Any
from google.adk.tools import ToolContext


def search_google(query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Perform a Google search and return formatted results.

    Args:
        query: The search query string
        tool_context: The tool context for accessing ADK features

    Returns:
        Dict containing search results in a structured format
    """
    try:
        # For now, this is a mock implementation
        # In the real implementation, you would integrate with Google Search API
        # or use the built-in google_search tool from ADK

        results = [
            {
                "title": f"Sample Result 1 for: {query}",
                "url": "https://example.com/result1",
                "snippet": "This is a sample search result snippet that would contain relevant information about your query.",
            },
            {
                "title": f"Sample Result 2 for: {query}",
                "url": "https://example.com/result2",
                "snippet": "Another sample search result with different relevant information about the topic.",
            }
        ]

        return {
            "status": "success",
            "query": query,
            "results": results,
            "total_results": len(results)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query,
            "results": []
        }


def search_duckduckgo(query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Perform a DuckDuckGo search and return formatted results.

    Args:
        query: The search query string
        tool_context: The tool context for accessing ADK features

    Returns:
        Dict containing search results in a structured format
    """
    try:
        # Mock implementation for DuckDuckGo search
        # In real implementation, you would use DuckDuckGo API or LangChain's DuckDuckGo tool

        results = [
            {
                "title": f"DDG Result 1 for: {query}",
                "url": "https://duckduckgo-example.com/result1",
                "snippet": "DuckDuckGo search result providing privacy-focused information about your query.",
            },
            {
                "title": f"DDG Result 2 for: {query}",
                "url": "https://duckduckgo-example.com/result2",
                "snippet": "Another DuckDuckGo result with complementary information from different sources.",
            }
        ]

        return {
            "status": "success",
            "query": query,
            "results": results,
            "total_results": len(results),
            "source": "duckduckgo"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query,
            "results": []
        }


def generate_image(prompt: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate an image using DALL-E for LinkedIn posts.

    Args:
        prompt: The image generation prompt
        tool_context: The tool context for accessing ADK features

    Returns:
        Dict containing image generation results
    """
    try:
        # Check if OpenAI API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key or openai_key == "your_openai_api_key_here":
            return {
                "status": "error",
                "error": "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file.",
                "image_url": None
            }

        # Import OpenAI client
        try:
            from openai import OpenAI
        except ImportError:
            return {
                "status": "error",
                "error": "OpenAI package not installed. Please run: pip install openai",
                "image_url": None
            }

        # Initialize OpenAI client
        client = OpenAI(api_key=openai_key)

        # Enhanced prompt for LinkedIn-appropriate professional imagery
        enhanced_prompt = f"""Create a professional, high-quality image suitable for LinkedIn business content about: {prompt}.
        The image should be:
        - Professional and business-appropriate
        - Clean, modern design
        - Suitable for social media sharing
        - Visually appealing and engaging
        - High contrast and readable
        - LinkedIn-appropriate color scheme (blues, whites, professional tones)

        Original concept: {prompt}"""

        # Generate image using DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1024x1024",  # Square format works well for LinkedIn
            quality="standard",  # Use "hd" for higher quality if needed
            n=1,
        )

        # Extract the image URL
        image_url = response.data[0].url

        # Save image info to session state for later reference
        image_info = {
            "url": image_url,
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "generated_at": json.dumps({"timestamp": "now"}),  # In real implementation, use datetime
        }
        tool_context.state["generated_image"] = image_info

        return {
            "status": "success",
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "image_url": image_url,
            "message": "Image generated successfully using DALL-E 3",
            "usage_notes": "Image URL is valid for a limited time. Download and save if needed for long-term use."
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Error generating image: {str(e)}",
            "image_url": None,
            "troubleshooting": "Check your OpenAI API key, account credits, and internet connection."
        }


def save_content_to_state(content: str, content_type: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Save generated content to the session state for later use.

    Args:
        content: The content to save
        content_type: Type of content (e.g., 'research', 'draft', 'final')
        tool_context: The tool context for accessing ADK features

    Returns:
        Dict confirming content was saved
    """
    try:
        state_key = f"linkedin_content_{content_type}"
        tool_context.state[state_key] = content

        return {
            "status": "success",
            "message": f"Content saved to state as '{state_key}'",
            "content_length": len(content)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }