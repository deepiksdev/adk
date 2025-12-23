
import asyncio
import os
from dotenv import load_dotenv
from agent import create_debater, create_moderator, DebateManager

load_dotenv()

async def main():
    topic = "The universe is a simulation."
    
    agent_a = create_debater("Simulation Believer", "You are convinced the universe is a computer simulation tailored for us.")
    agent_b = create_debater("Simulation Skeptic", "You are a physicist who believes in physical reality and empirical evidence.")
    moderator = create_moderator()
    
    manager = DebateManager(agent_a, agent_b, moderator)
    
    print("Starting 30-turn debate test...")
    await manager.run_debate(topic, max_turns=30)
    
    # Save transcript
    with open("debate_transcript_30_turns.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(manager.history))
    
    print("\nDebate finished. Transcript saved to debate_transcript_30_turns.txt")

if __name__ == "__main__":
    asyncio.run(main())
