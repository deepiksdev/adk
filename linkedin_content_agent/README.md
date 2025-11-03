# LinkedIn Content Creation Agent

A comprehensive AI-powered agent system for creating engaging LinkedIn content. This agent leverages Google's Agent Development Kit (ADK) and Gemini 2.5 models to research topics, create optimized posts, and generate accompanying visuals.

## Features

### 🔍 **Multi-Source Research**
- Parallel research using Google Search and DuckDuckGo
- Comprehensive information gathering and synthesis
- Trend analysis and expert opinion integration

### ✍️ **Content Creation Pipeline**
- Engaging LinkedIn post creation with professional tone
- SEO optimization for maximum reach
- Content guardrails ensuring LinkedIn compliance
- Professional formatting and structure

### 🎨 **Visual Content Generation**
- AI-generated images to accompany posts
- Professional visual design aligned with content
- LinkedIn-optimized imagery

### 🛡️ **Content Guardrails**
- Automatic link removal for LinkedIn compliance
- Hashtag optimization (max 3 relevant hashtags)
- Professional tone enforcement
- Content quality assurance

## Architecture

The agent uses a **Sequential Multi-Agent System** with the following workflow:

```
1. Parallel Research Agent
   ├── Google Research Agent
   └── DuckDuckGo Research Agent

2. Research Merger Agent

3. LinkedIn Post Writer

4. SEO Optimizer Agent

5. Final Draft Agent

6. Image Generation Agent
```

## Setup Instructions

### 1. Environment Configuration

The agent uses the root-level `.env` file in the repository. Make sure it has your API keys configured:

Edit the root `.env` file and ensure it contains:

```env
# Required: Google Gemini API Key
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=your_actual_google_gemini_api_key

# Optional: OpenAI API Key for image generation
OPENAI_API_KEY=your_actual_openai_api_key

# Optional: Google Cloud settings (if using Vertex AI)
# GOOGLE_CLOUD_PROJECT=your_gcp_project_id
# GOOGLE_CLOUD_LOCATION=us-central1
```

### 2. Get Your API Keys

#### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and add it to your `.env` file

#### OpenAI API Key (Optional - for image generation)
1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key and add it to your `.env` file

### 3. Install Dependencies

Ensure you have the required dependencies installed:

```bash
pip install google-adk
pip install openai  # optional, for image generation
```

## Usage

### Basic Usage

```python
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from linkedin_content_agent.agent import root_agent

async def create_linkedin_content():
    # Initialize session
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="linkedin_content_agent",
        user_id="user123",
        session_id="session456"
    )

    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name="linkedin_content_agent",
        session_service=session_service
    )

    # Your content topic
    topic = "The future of AI in healthcare"

    query = f"Create a LinkedIn post about: {topic}"

    # Run the agent
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.is_final_response():
            print("Final LinkedIn Post:")
            print(event.content.parts[0].text)
            break

# Run it
asyncio.run(create_linkedin_content())
```

### Test the Agent

Run the included test script to verify everything works:

```bash
python test_agent.py
```

This will create a sample LinkedIn post about "AI's impact on remote work productivity in 2024" and show you the entire process.

### Using the Web Interface

You can also test the agent using ADK's web interface:

```bash
# From the project root directory
adk web linkedin_content_agent/
```

Then open your browser to the provided URL and interact with the agent through the chat interface.

## Example Output

Here's what a typical output might look like:

```
=== FINAL LINKEDIN POST ===

🤖 The AI revolution is reshaping how we work remotely—and the productivity gains are remarkable!

Recent studies show remote workers using AI tools are 40% more efficient at task completion. Here's what's driving this transformation:

✨ Smart scheduling algorithms that optimize our most productive hours
📊 AI-powered analytics that identify workflow bottlenecks
🎯 Personalized focus recommendations based on work patterns

But here's the key insight: It's not about replacing human creativity—it's about amplifying it.

The most successful remote teams are those that blend AI efficiency with human collaboration, creating hybrid workflows that maximize both productivity and job satisfaction.

What AI tools have transformed your remote work experience?

#RemoteWork #ArtificialIntelligence #Productivity

=== POSTING RECOMMENDATIONS ===
Best posting times: Tuesday-Thursday, 9-10 AM or 2-3 PM
Engagement strategy: Reply to comments within first 2 hours, share in relevant LinkedIn groups
```

## Content Guidelines

The agent automatically enforces these LinkedIn best practices:

- **Professional tone** with conversational elements
- **Optimal length** (150-300 words for best engagement)
- **Maximum 3 hashtags** (LinkedIn's sweet spot)
- **No external links** (LinkedIn algorithm preference)
- **Engagement hooks** (questions, call-to-actions)
- **Proper formatting** (short paragraphs, bullet points)

## Customization

### Modify Content Style

Edit the agent instructions in `agent.py` to change the writing style:

```python
linkedin_post_writer = Agent(
    # ... other config ...
    instruction="""Your custom instruction here..."""
)
```

### Add Custom Tools

Add new tools in `tools.py` and include them in relevant agents:

```python
def custom_tool(param: str, tool_context: ToolContext) -> dict:
    # Your custom tool logic
    return {"status": "success", "result": "..."}

# Add to agent
agent = Agent(
    # ... other config ...
    tools=[existing_tools, custom_tool]
)
```

### Integrate Real APIs

Replace the mock implementations in `tools.py` with real API integrations:

- Google Custom Search API for `search_google`
- DuckDuckGo API for `search_duckduckgo`
- OpenAI DALL-E API for `generate_image`

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure your `.env` file has the correct API keys
   - Check that keys are valid and have proper permissions

2. **Import Errors**
   - Make sure you're running from the correct directory
   - Verify all dependencies are installed

3. **Content Quality Issues**
   - Adjust agent instructions for different writing styles
   - Modify guardrails in the callback functions

### Debug Mode

Enable debug logging to see detailed execution:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the ADK examples and follows the same licensing terms.

## Support

For issues related to:
- **Agent logic**: Check the GitHub issues
- **ADK framework**: Refer to Google ADK documentation
- **API integrations**: Check the respective API documentation (Google, OpenAI)