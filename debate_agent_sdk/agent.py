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
# Settings for the debate agent
# ----------------------------------------------------------------------
DEBATE_ROUNDS = 3   # Number of debate rounds (each round = Agent A + Agent B)
                    # We will keep 3 as the numbers of rounds so adk can show the   
                    # The entirety of the debate


# ----------------------------------------------------------------------
# Initialize OpenAI-compatible client (DeepGen backend)
# ----------------------------------------------------------------------
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


# ----------------------------------------------------------------------
# Internal function: Agent A answers the moderator’s question or Agent B's arguments.
# ----------------------------------------------------------------------
def answer_agentA(question: str) -> str:
    """
    Agent A is the first agent to answer the moderator's question.
    It will give an answer directly based on the question provided.
    Later, it can also respond to Agent B's arguments.
    """

    system_prompt_mod = (
        "You are Agent A in a debate. "
        "You answer the moderator's question in a structured, "
        "well-reasoned way, using 1 paragraph. "
        "Do NOT address the user directly. Your tone should be analytical and neutral."
    )

    system_prompt_answer = (
        "You are Agent A in a debate. "
        "You will respond to Agent B's arguments in a structured, "
        "well-reasoned way, using 1 paragraph. "
        "You may defend your previous position, clarify it, or extend it."
    )

    stripped = question.strip()
    if stripped.startswith("Question :"):
        system_prompt = system_prompt_mod
    else:
        system_prompt = system_prompt_answer

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    content = response.choices[0].message.content
    final_text = f"[AGENT A]\n{content}"

    print("📡 [SENT_TO_GPT - AGENT_A_INPUT] ", question)
    print("📡 [RECEIVED_FROM_GPT - AGENT_A_ANSWER] ", final_text)

    return final_text


# ----------------------------------------------------------------------
# Internal function: Agent B reacts to Agent A's arguments.
# ----------------------------------------------------------------------
def answer_agentB(answerA: str) -> str:
    """
    Agent B reacts to Agent A's arguments.
    It aims to provide a different position, while remaining factual and analytical.
    If Agent B agrees with Agent A, it should add new insights or perspectives.
    """

    system_prompt = (
        "You are Agent B in a debate. "
        "You are going to react to Agent A's arguments. "
        "Your objective is to provide a position that is clearly distinct from "
        "Agent A's, while remaining factual and analytical. "
        "If you genuinely agree with Agent A, you should still add new insights, "
        "nuances, or alternative perspectives. Use 1 paragraph."
    )

    if not answerA.startswith("[AGENT A]"):
        raise ValueError("Input to Agent B must start with '[AGENT A]'")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": answerA},
        ],
    )

    content = response.choices[0].message.content
    final_text = f"[AGENT B]\n{content}"

    print("📡 [SENT_TO_GPT - AGENT_B_INPUT] ", answerA)
    print("📡 [RECEIVED_FROM_GPT - AGENT_B_ANSWER] ", final_text)

    return final_text


# ----------------------------------------------------------------------
# Moderator function, used to process the user topic and orchestrate the debate.
# ----------------------------------------------------------------------
def moderated_step(topic: str) -> dict:
    """
    Represents one full moderated debate session.

    - If the user input is a greeting, return a simple reply.
    - Otherwise:
        1) The moderator reformulates the topic into a clear question.
        2) Agent A answers this question.
        3) Agent B reacts to Agent A.
        4) Steps 2 and 3 are repeated for DEBATE_ROUNDS rounds.
        5) The moderator then writes a conclusion, trying to synthesize or find consensus.
    """

    greetings = ["hi", "hello", "salut", "hey", "yo", "hola", "bonjour"]
    cleaned = topic.strip().lower()

    if cleaned in greetings or len(cleaned) <= 3:
        reply = "Hi! Please give me a debate topic 🙂"
        print("📡 [NO_DEBATE_TRIGGERED] Greeting detected → returning simple message.")
        return {"final": reply}

    moderator_system_prompt = (
        "You are a moderator preparing a debate. "
        "Your job is to rewrite the user's topic into a clear, precise, neutral question "
        "that will be asked to the debating agents.\n\n"
        "Respond using EXACTLY this format:\n"
        "Question : ...\n"
    )

    mod_response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": moderator_system_prompt},
            {"role": "user", "content": f"Users proposed topic: {topic}"},
        ],
    )

    moderator_text = mod_response.choices[0].message.content
    moderator_block = f"[MODERATOR]\n{moderator_text}"

    print("📡 [SENT_TO_GPT - MODERATOR_TOPIC] ", topic)
    print("📡 [RECEIVED_FROM_GPT - MODERATOR_QUESTION] ", moderator_block)

    transcript = moderator_block
    last_agentB_answer = None

    # Debate rounds: A then B
    for round_index in range(1, DEBATE_ROUNDS + 1):
        print(f"🔁 [DEBATE ROUND {round_index}] Starting")

        if round_index == 1:
            agentA_input = moderator_text
        else:
            agentA_input = last_agentB_answer

        agentA_answer = answer_agentA(agentA_input)
        transcript += "\n\n" + agentA_answer

        agentB_answer = answer_agentB(agentA_answer)
        transcript += "\n\n" + agentB_answer

        last_agentB_answer = agentB_answer

    # Final moderator conclusion
    conclusion_prompt_system = (
        "You are the moderator of this debate. "
        "You will now write a short conclusion summarizing the main points of both agents. "
        "If there is a clear consensus, mention it. "
        "If there is disagreement, highlight the key differences without taking sides."
    )

    conclusion_response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": conclusion_prompt_system},
            {"role": "user", "content": transcript},
        ],
    )

    conclusion_text = conclusion_response.choices[0].message.content
    transcript += "\n\n[MODERATOR CONCLUSION]\n" + conclusion_text

    return {"final": transcript}


# ----------------------------------------------------------------------
# ADK tool declaration
# ----------------------------------------------------------------------
moderated_step_tool = FunctionTool(
    func=moderated_step,
)


# ----------------------------------------------------------------------
# Root ADK agent
# ----------------------------------------------------------------------
root_agent = Agent(
    name="debate_agent_step2",
    model="gemini-2.5-flash",
    instruction=(
        "IMPORTANT: You must NEVER answer by yourself.\n"
        "- For EVERY user message, you MUST call the tool 'moderated_step'.\n"
        "- You MUST return EXACTLY the value of the key 'final' from the tool result, "
        "without modifying or adding anything.\n"
    ),
    tools=[moderated_step_tool],
)
