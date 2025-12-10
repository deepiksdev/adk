import os
from dotenv import load_dotenv
from openai import OpenAI

from google.adk.tools import FunctionTool
from google.adk.agents import Agent


# ----------------------------------------------------------------------
# Load environment variables from .env
# ----------------------------------------------------------------------
load_dotenv()

API_KEY = os.getenv("DEEPGEN_API_KEY")
BASE_URL = os.getenv("DEEPGEN_BASE_URL", "https://api.deepgen.app/v1")
MODEL = os.getenv("MODEL_NAME", "gpt-4o")  # You may change the model here

if not API_KEY:
    raise ValueError("DEEPGEN_API_KEY is missing in .env")


# ----------------------------------------------------------------------
# Initialize OpenAI-compatible client (DeepGen backend)
# ----------------------------------------------------------------------
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


# ----------------------------------------------------------------------
# Internal function: AGENT that answers the moderator’s question.
# In Step 1, there is only ONE debating agent (no dual-agent debate yet).
# ----------------------------------------------------------------------
def answer_agent(question: str) -> str:
    """
    The debating agent answers the question formulated by the moderator.
    Only ONE answer is produced (no multi-turn debate).
    """

    system_prompt = (
        "You are an agent participating in a debate. "
        "You answer the question posed by the moderator in a structured, "
        "well-reasoned way, using 1 to 3 paragraphs. "
        "Do NOT address the user directly. Your tone should be analytical and neutral."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    content = response.choices[0].message.content
    final_text = f"[AGENT 1]\n{content}"

    # Debug logs to confirm that the answer was produced by GPT (via the tool)
    print("📡 [SENT_TO_GPT - AGENT_1_QUESTION] ", question)
    print("📡 [RECEIVED_FROM_GPT - AGENT_1_ANSWER] ", final_text)

    return final_text


# ----------------------------------------------------------------------
# Moderator + Agent logic exposed as an ADK tool.
#
# Step 1 requirements:
#   - The user provides a topic.
#   - The moderator reformulates it into a clear debate question.
#   - The agent answers this question ONCE.
#
# No dialogue loop, no Agent A vs Agent B yet.
# ----------------------------------------------------------------------
def moderated_step(topic: str) -> dict:
    """
    Implements Step 1 of the debate pipeline:
    - If the user input is a greeting, return a simple reply.
    - Otherwise:
        1) The moderator rewrites the topic as a clear question.
        2) The debating agent answers that question once.
    """

    greetings = ["hi", "hello", "salut", "hey", "yo", "hola", "bonjour"]
    cleaned = topic.strip().lower()

    # Case 1: Greeting → no debate
    if cleaned in greetings or len(cleaned) <= 3:
        reply = "Hi! Please give me a debate topic 🙂"
        print("📡 [NO_DEBATE_TRIGGERED] Greeting detected → returning simple message.")
        return {"final": reply}

    # Case 2: Moderator reformulates the topic into a proper debate question
    moderator_system_prompt = (
        "You are a moderator preparing a debate. "
        "Your job is to rewrite the user's topic into a clear, precise, neutral question "
        "that will be asked to the debating agent.\n\n"
        "Respond using EXACTLY this format:\n"
        "Question : ...\n"
    )

    mod_response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": moderator_system_prompt},
            {"role": "user", "content": f"User's proposed topic: {topic}"},
        ],
    )

    moderator_text = mod_response.choices[0].message.content
    moderator_block = f"[MODERATOR]\n{moderator_text}"

    print("📡 [SENT_TO_GPT - MODERATOR_TOPIC] ", topic)
    print("📡 [RECEIVED_FROM_GPT - MODERATOR_QUESTION] ", moderator_block)

    # For Step 1, we simply forward the entire moderator question block to the agent.
    agent_input = moderator_text
    agent_block = answer_agent(agent_input)

    # Output: moderator question + agent answer
    final_text = moderator_block + "\n\n" + agent_block

    return {"final": final_text}


# ----------------------------------------------------------------------
# ADK tool declaration.
# The ADK agent sees only ONE tool: moderated_step.
# ----------------------------------------------------------------------
moderated_step_tool = FunctionTool(
    func=moderated_step,
)


# ----------------------------------------------------------------------
# Root ADK agent.
#
# Critical behavior:
# - This agent MUST NOT answer by itself.
# - For EVERY user message, it MUST call the tool 'moderated_step'.
# - It MUST return EXACTLY the "final" field produced by the tool.
# ----------------------------------------------------------------------
root_agent = Agent(
    name="debate_agent_step1",
    model="gemini-2.5-flash",  # Used only as an orchestrator for the tool
    instruction=(
        "IMPORTANT: You must NEVER answer by yourself.\n"
        "- For EVERY user message, you MUST call the tool 'moderated_step'.\n"
        "- You MUST return EXACTLY the value of the key 'final' from the tool result, "
        "without modifying or adding anything.\n"
    ),
    tools=[moderated_step_tool],
)
