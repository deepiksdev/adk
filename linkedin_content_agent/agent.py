"""LinkedIn Content Creation Agent using Google ADK."""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types
from tools import search_google, search_duckduckgo, generate_image, save_content_to_state
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
    professional_indicators = ['insights', 'thoughts', 'experience', 'learning', 'sharing']
    if not any(indicator in content.lower() for indicator in professional_indicators):
        # Add a professional touch if missing
        if not content.endswith('.'):
            content += '.'
        content += "\n\nWhat are your thoughts on this?"

    # Clean up extra whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content


# Research Agents
google_research_agent = Agent(
    name="google_research_agent",
    model="gemini-2.5-flash",
    description="Conducts Google searches and gathers information for LinkedIn content creation.",
    instruction="""You are a research specialist focused on gathering comprehensive information from Google searches.

Your task is to:
1. Use the search_google tool to find relevant, current information about the given topic
2. Analyze and synthesize the search results
3. Provide detailed, factual information that can be used for LinkedIn content creation
4. Focus on trends, statistics, expert opinions, and actionable insights
5. Always cite the sources of information

Be thorough and professional in your research approach.""",
    tools=[search_google, save_content_to_state]
)

duckduckgo_research_agent = Agent(
    name="duckduckgo_research_agent",
    model="gemini-2.5-flash",
    description="Conducts DuckDuckGo searches and provides alternative perspectives for content research.",
    instruction="""You are a research specialist using DuckDuckGo to gather diverse perspectives and information.

Your task is to:
1. Use the search_duckduckgo tool to find relevant information from diverse sources
2. Focus on finding different angles and perspectives compared to mainstream sources
3. Look for unique insights, alternative viewpoints, and niche information
4. Provide comprehensive research that complements other research sources
5. Maintain factual accuracy while exploring different perspectives

Your research will be combined with other sources to create well-rounded LinkedIn content.""",
    tools=[search_duckduckgo, save_content_to_state]
)

# Parallel Research Agent
parallel_research_agent = ParallelAgent(
    name="parallel_research_agent",
    sub_agents=[google_research_agent, duckduckgo_research_agent],
    description="Conducts simultaneous research using multiple search engines for comprehensive information gathering."
)

# Content Processing Agents
research_merger_agent = Agent(
    name="research_merger_agent",
    model="gemini-2.5-flash",
    description="Combines and synthesizes research from multiple sources into coherent insights.",
    instruction="""You are a content synthesis expert. Your job is to merge research from multiple sources into coherent, valuable insights.

Your task is to:
1. Review all research findings from different sources
2. Identify common themes, patterns, and key insights
3. Resolve any conflicting information by noting different perspectives
4. Create a comprehensive summary that highlights the most important points
5. Organize information in a logical flow suitable for LinkedIn content creation
6. Maintain factual accuracy and cite sources where appropriate

Focus on creating actionable insights that would be valuable to a LinkedIn audience.""",
    tools=[save_content_to_state],
    output_key="merged_research"
)

linkedin_post_writer = Agent(
    name="linkedin_post_writer",
    model="gemini-2.5-flash",
    description="Creates engaging LinkedIn posts based on research insights.",
    instruction="""You are a LinkedIn content creation expert specializing in writing engaging, professional posts.

Create LinkedIn posts that:
1. Start with a compelling hook to grab attention
2. Use insights from the provided research: {merged_research}
3. Include storytelling elements or personal anecdotes when appropriate
4. Add value through actionable advice, insights, or thought-provoking questions
5. Use proper LinkedIn formatting (short paragraphs, bullet points when helpful)
6. Include relevant emojis sparingly to enhance readability
7. End with a call-to-action or question to encourage engagement
8. Keep the tone professional yet conversational
9. Aim for 150-300 words for optimal engagement

Remember: The goal is to educate, inspire, or provoke thoughtful discussion among LinkedIn professionals.""",
    tools=[save_content_to_state],
    output_key="linkedin_draft",
    after_agent_callback=content_guardrails_callback
)

seo_optimizer_agent = Agent(
    name="seo_optimizer_agent",
    model="gemini-2.5-flash",
    description="Optimizes LinkedIn posts for search and engagement while maintaining authenticity.",
    instruction="""You are a LinkedIn SEO and engagement optimization expert.

Your task is to enhance the LinkedIn post draft: {linkedin_draft}

Optimize for:
1. LinkedIn algorithm factors (engagement, relevance, timing considerations)
2. Strategic keyword placement that feels natural
3. Hashtag optimization (maximum 3 relevant, trending hashtags)
4. Readability and scanability (proper formatting, spacing)
5. Engagement triggers (questions, calls-to-action)
6. Professional authenticity (avoid over-optimization)

Key guidelines:
- Maintain the original tone and message
- Ensure keywords flow naturally in the content
- Research and suggest trending, relevant hashtags
- Optimize for LinkedIn's preference for native content
- Include engagement hooks without being salesy

Output the optimized post ready for publication.""",
    tools=[save_content_to_state],
    output_key="optimized_post",
    after_agent_callback=content_guardrails_callback
)

final_draft_agent = Agent(
    name="final_draft_agent",
    model="gemini-2.5-flash",
    description="Reviews and polishes the final LinkedIn post for publication.",
    instruction="""You are a final review editor ensuring the LinkedIn post meets all quality standards.

Review the optimized post: {optimized_post}

Perform final checks for:
1. Grammar, spelling, and punctuation
2. Professional tone and clarity
3. Appropriate length and formatting
4. Compliance with LinkedIn best practices
5. Call-to-action effectiveness
6. Overall coherence and flow

Make any final refinements needed and provide the publication-ready post.
Also suggest the best posting time and any additional engagement strategies.

Output format:
=== FINAL LINKEDIN POST ===
[Your polished post content]

=== POSTING RECOMMENDATIONS ===
[Timing and engagement suggestions]""",
    output_key="final_linkedin_post",
    after_agent_callback=content_guardrails_callback
)

image_generation_agent = Agent(
    name="image_generation_agent",
    model="gemini-2.5-flash",
    description="Creates compelling images to accompany LinkedIn posts using AI image generation.",
    instruction="""You are a visual content creator specializing in LinkedIn post imagery.

Based on the final LinkedIn post: {final_linkedin_post}

Create an image that:
1. Visually represents the key message or theme of the post
2. Is professional and LinkedIn-appropriate
3. Enhances the post's message without being distracting
4. Follows LinkedIn's visual best practices (clean, high-quality, relevant)
5. Appeals to a professional audience

Use the generate_image tool with a detailed, professional prompt that will create an engaging visual for the LinkedIn post.

Provide the image along with suggestions for how to integrate it with the post.""",
    tools=[generate_image, save_content_to_state],
    output_key="post_image"
)

# Main Sequential Workflow
root_agent = SequentialAgent(
    name="linkedin_content_creator",
    sub_agents=[
        parallel_research_agent,
        research_merger_agent,
        linkedin_post_writer,
        seo_optimizer_agent,
        final_draft_agent,
        image_generation_agent
    ],
    description="""A comprehensive LinkedIn content creation system that researches topics,
    creates engaging posts, optimizes for SEO and engagement, and generates accompanying visuals.

    The system follows a structured workflow:
    1. Parallel research using multiple search engines
    2. Research synthesis and insight generation
    3. Initial post creation with engaging content
    4. SEO and engagement optimization
    5. Final editing and polish
    6. Visual content generation

    Perfect for creating professional, engaging LinkedIn content that drives meaningful discussions."""
)