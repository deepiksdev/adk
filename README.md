# ADK Agents Repository

This repository contains multiple AI agents built with Google's Agent Development Kit (ADK).

## Available Agents

- **`my_agent`** - Basic agent example
- **`linkedin_content_agent`** - LinkedIn content creation agent with DALL-E image generation
- **`my_blogger_agent`** - Technical blog writing assistant

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env` file:
   ```bash
   # For Google AI Studio (simpler setup)
   GOOGLE_GENAI_USE_VERTEXAI=false
   GOOGLE_API_KEY=your_google_api_key_here

   # For OpenAI (required for linkedin_content_agent DALL-E)
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Running Agents

### Web Interface (Recommended)
```bash
adk web
```
This launches a web UI where you can select and interact with any agent.

### Command Line Interface
```bash
adk run <agent_name>
```
Example:
```bash
adk run my_agent
adk run linkedin_content_agent
adk run my_blogger_agent
```

### API Server
```bash
adk api_server
```
This starts a REST API server for programmatic access to the agents.

## Agent Development

Each agent is contained in its own directory with:
- `__init__.py` - Package initialization
- `agent.py` - Main agent definition
- Additional files as needed (tools, sub-agents, etc.)

For detailed development information, see `CLAUDE.md`.

## Local Development

To run the custom server (including Twilio integration) with auto-reload enabled:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```