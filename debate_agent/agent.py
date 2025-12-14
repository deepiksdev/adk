import asyncio
import os
import json
from dotenv import load_dotenv
from typing import List, Optional, Any
from pydantic import BaseModel, Field

load_dotenv()
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

# --- Data Models for Structured Output ---

class DebateTurnAnalysis(BaseModel):
    """Moderator's analysis of the last turn."""
    has_agreement: bool = Field(description="True ONLY if both parties have explicitly agreed on the core resolution.")
    key_disagreements: List[str] = Field(description="List of remaining points of disagreement.")
    guidance_for_next_speaker: str = Field(description="Specific question or instruction for the next speaker to address the disagreements.")

class DebateVerdict(BaseModel):
    """Final verdict of the debate."""
    winner_alias: str = Field(description="The alias of the agent who won the debate. Use 'Tie' if it is a draw.")
    reasoning: str = Field(description="Detailed explanation of why this agent won, citing strong arguments.")

# --- Agent Factory ---

def create_debater(alias: str, persona: str, model: str = "gemini-2.0-flash-exp") -> Agent:
    """Creates a debater agent with a specific persona."""
    return Agent(
        name=f"debater_{alias.lower().replace(' ', '_')}",
        model=model,
        instruction=f"""
        You are {alias}. 
        Your Persona: {persona}
        
        Participate in a debate. 
        - State your arguments clearly and persuasively.
        - Rebut the opponent's points directly.
        - Keep your responses concise (under 150 words).
        - If you agree with the opponent's point, acknowledge it.
        """,
    )

def create_moderator(model: str = "gemini-2.0-flash-exp") -> Agent:
    """Creates the moderator agent."""
    return Agent(
        name="moderator",
        model=model,
        instruction="""
        You are an impartial debate moderator.
        Your goal is to facilitate a structured debate between two agents.
        
        Responsibilities:
        1. Analyze the latest response.
        2. Identify if an agreement has been reached.
        3. If NO agreement: Formulate a targeted question or instruction for the next speaker to address the specific disagreements using the `DebateTurnAnalysis` schema.
        4. If Agreement OR Max Turns reached: You will be asked to judge the winner separately.
        """,
    )

# --- Debate Orchestration ---

class DebateManager:
    def __init__(self, agent_a: Agent, agent_b: Agent, moderator: Agent, model: str = "gemini-2.0-flash-exp", on_message=None):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.moderator = moderator
        self.history: List[str] = []
        self.model = model
        self.session_service = InMemorySessionService()
        self.on_message = on_message if on_message else print

    async def _emit(self, message: str):
        if asyncio.iscoroutinefunction(self.on_message):
            await self.on_message(message)
        else:
            self.on_message(message)

    async def _run_agent(self, agent: Agent, prompt: str, schema: Any = None) -> Any:
        # Create a runner for the agent
        session_id = f"session_{agent.name}"
        
        # Ensure session exists
        try:
            await self.session_service.create_session(
                app_name="debate_app",
                user_id="moderator_user",
                session_id=session_id
            )
        except Exception:
            # Session might already exist, ignore duplication error
            pass

        runner = Runner(agent=agent, app_name="debate_app", session_service=self.session_service)
        
        # Run
        response_text = ""
        async for event in runner.run_async(
            user_id="moderator_user",
            session_id=session_id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=prompt)]
            )
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text

        if schema:
            # Try to parse as JSON if schema expected
            try:
                # Clean markdown code blocks if present
                clean_text = response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                     clean_text = clean_text.strip("`")
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]

                data = json.loads(clean_text)
                return schema(**data)
            except Exception as e:
                await self._emit(f"Warning: Failed to parse schema {schema.__name__}: {e}")
                await self._emit(f"Raw output: {response_text}")
                return response_text
        
        return response_text


    async def run_debate(self, topic: str, max_turns: int = 10):
        await self._emit(f"--- Starting Debate: {topic} ---")
        await self._emit(f"Agent A: {self.agent_a.name}")
        await self._emit(f"Agent B: {self.agent_b.name}\n")

        opening_prompt = f"The debate topic is: '{topic}'. Please present your opening argument."
        await self._emit(f"[Moderator]: {opening_prompt}")
        self.history.append(f"Moderator: {opening_prompt}")

        current_speaker = self.agent_a
        other_speaker = self.agent_b
        last_response = opening_prompt

        for turn in range(1, max_turns + 1):
            await self._emit(f"\n--- Turn {turn}/{max_turns} ---")
            
            # Speaker Turn
            prompt_for_speaker = f"The previous message was: '{last_response}'. \nRespond to this."
            response_text = await self._run_agent(current_speaker, prompt_for_speaker)
            
            await self._emit(f"[{current_speaker.name}]: {response_text}")
            self.history.append(f"{current_speaker.name}: {response_text}")
            last_response = response_text

            # Moderator Analysis (Create ephemeral agent for structured output)
            analysis_prompt = f"""
            The debate topic is '{topic}'.
            Last speaker was {current_speaker.name}.
            Their argument: "{response_text}"
            
            Analyze if an agreement has been reached.
            If not, provide guidance for {other_speaker.name}.
            """
            
            analyzer_agent = Agent( # dedicated agent for analysis to enforce schema
                name="moderator_analyzer",
                model=self.model,
                instruction="Analyze the debate turn.",
                output_schema=DebateTurnAnalysis
            )
            
            analysis_data = await self._run_agent(analyzer_agent, analysis_prompt, schema=DebateTurnAnalysis)
            
            if isinstance(analysis_data, DebateTurnAnalysis):
                 if analysis_data.has_agreement:
                     await self._emit(f"\n[Moderator]: Agreement Reached! Debate Concluded.")
                     return

                 await self._emit(f"[Moderator Guidance]: {analysis_data.guidance_for_next_speaker}")
                 last_response = f"Your opponent said: '{response_text}'. \nModerator's instruction: {analysis_data.guidance_for_next_speaker}"
            else:
                # Fallback
                await self._emit("[Moderator]: (Analysis unavailable, continuing standard flow)")

            # Swap
            current_speaker, other_speaker = other_speaker, current_speaker
            
            # Rate limit backoff
            await asyncio.sleep(10)

        await self.declare_winner(topic)

    async def declare_winner(self, topic):
        await self._emit("\n--- Max Turns Reached. Declaring Winner ---")
        full_transcript = "\n".join(self.history)
        
        judge_agent = Agent(
            name="judge",
            model=self.model,
            instruction="You are the judge of the debate. Decide the winner based on the transcript.",
            output_schema=DebateVerdict
        )
        
        prompt = f"Topic: {topic}\n\nTranscript:\n{full_transcript}\n\nWho won and why?"
        result = await self._run_agent(judge_agent, prompt, schema=DebateVerdict)
        
        if isinstance(result, DebateVerdict):
            await self._emit(f"\n[WINNER]: {result.winner_alias}")
            await self._emit(f"[REASON]: {result.reasoning}")
        else:
            await self._emit(f"Verdict: {result}")

# Initialize and run
async def main():
    topic = "AI will replace software engineers within 10 years."
    
    agent_a = create_debater("Tech Optimist", "You believe AI is a tool that amplifies human potential, not replaces it.")
    agent_b = create_debater("Tech Doomer", "You believe AI advancement is exponential and will inevitably automate all cognitive labor.")
    moderator = create_moderator()
    
    manager = DebateManager(agent_a, agent_b, moderator)
    await manager.run_debate(topic, max_turns=4)

if __name__ == "__main__":
    asyncio.run(main())