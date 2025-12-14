# Debate Agent with Moderator

This project implements a multi-agent debate system using the Google Agent Development Kit (ADK).

## Overview

The system consists of three agents:
1.  **Debater A**: Argues for a specific stance.
2.  **Debater B**: Argues for the opposing stance.
3.  **Moderator Agent**: Orchestrates the conversation, checks for agreement, and declares a winner if the debate times out.

## Features

- **Structured Workflow**: The moderator ensures agents respond to each other's points.
- **Turn Analysis**: After each turn, the moderator analyzes if an agreement has been reached.
- **Winner Declaration**: If the `max_turns` limit is reached without agreement, a judge (specialized moderator role) evaluates the transcript to declare a winner.
- **Structured Output**: Uses Pydantic schemas to ensure reliable decision-making (Agreement Boolean, Winner Alias).

## Usage

1.  **Install Dependencies**:
    Ensure you have `google-adk` and `pydantic` installed.
    ```bash
    pip install google-adk pydantic requests python-dotenv
    ```

2.  **Configure Environment**:
    Set your API keys in a `.env` file or environment variables.

3.  **Run the Debate**:
    You can run the agent directly to see a sample debate:
    ```bash
    python debate_agent/agent.py
    ```

## Web Interface (Streaming)

The agent includes a FastAPI server with a real-time web interface.

1.  **Run the Server**:
    ```bash
    python -m uvicorn debate_agent.server:app --reload
    ```
2.  **Open Browser**: Go to [http://localhost:8000](http://localhost:8000)
3.  **Use UI**: Enter a topic and click "Start Debate". The debate will stream 10 turns by default.

## Testing

- **Basic Test** (Console):
    ```bash
    python debate_agent/agent.py
    ```
- **Long Debate Test** (30 Turns, Console):
    ```bash
    python debate_agent/test_long_debate.py
    ```
    This script includes rate-limit handling and saves the transcript to a file.

## Customization

To change the debate topic or agent personas, modify the `if __name__ == "__main__":` block in `debate_agent/agent.py`.

```python
agent_a = create_debater("Alias A", "Persona description A")
agent_b = create_debater("Alias B", "Persona description B")
manager.run_debate("Your Topic Here", max_turns=10)
```
