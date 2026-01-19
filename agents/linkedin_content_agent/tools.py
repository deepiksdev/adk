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



def generate_html_preview(post_content: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate a LinkedIn-style HTML preview of the post.

    Args:
        post_content: The text content of the LinkedIn post.
        tool_context: The tool context.

    Returns:
        Dict containing the path to the generated HTML file.
    """
    try:
        # Retrieve image URL from state
        image_info = tool_context.state.get("generated_image", {})
        image_url = image_info.get("url", "")
        
        # Define paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, 'linkedin_post_template.html')
        output_dir = os.path.join(script_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        # Unique filename using timestamp
        timestamp = int(os.path.getmtime(template_path)) if os.path.exists(template_path) else 0 
        # Actually better to use UUID or current time
        import time
        filename = f"linkedin_preview_{int(time.time())}.html"
        output_file = os.path.join(output_dir, filename)

        # Read Template
        if not os.path.exists(template_path):
             return {"status": "error", "error": "Template file not found."}

        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Replace Placeholders
        html_content = html_content.replace('{{ POST_CONTENT }}', post_content)
        html_content = html_content.replace('{{ IMAGE_URL }}', image_url)
        
        if image_url:
            html_content = html_content.replace('{% if IMAGE_URL %}', '').replace('{% else %}', '<!--').replace('{% endif %}', '-->')
        else:
            html_content = html_content.replace('{% if IMAGE_URL %}', '<!--').replace('{% else %}', '-->').replace('{% endif %}', '')

        # Save Output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return {
            "status": "success",
            "message": "HTML preview generated successfully.",
            "file_path": output_file,
            "preview_url": f"file:///{output_file.replace(os.sep, '/')}"
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}

def generate_nano_banana_image(prompt: str, tool_context: ToolContext) -> Dict[str, Any]:

    """
    Generate an image using the "Nano Banana" style (vibrant, fruity, abstract).

    Args:
        prompt: The base prompt for the image
        tool_context: The tool context for accessing ADK features

    Returns:
        Dict containing image generation results
    """
    nano_banana_style = "style of Nano Banana, vibrant colors, yellow and pop art aesthetics, creative, abstract, fruity undertones, high energy"
    enhanced_prompt = f"{prompt}. {nano_banana_style}"

    # Reuse the existing DALL-E integration but with the Nano Banana prompt
    return generate_image(enhanced_prompt, tool_context)