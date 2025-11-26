from google.adk.agents.llm_agent import Agent
from google.adk.tools.base_tool import BaseTool
import requests
import json
import os

#DEBATO

class DeepGenTool(BaseTool):
    """Tool calling DeepGen API with GPT-4o model"""
    
    name = "deepgen_chat"
    description = "Calls DeepGen API to get chat completions using GPT-4o model."
    
    def __init__(self):
        self.api_key = os.getenv("DEEPGEN_API_KEY")
        self.base_url = "https://api.deepgen.app/v1/chat/completions"
    
    def chat(self, message: str) -> str: 
        """Method called by the adk agent"""
        
        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user", 
                    "content": message
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["choices"][0]["message"]["content"]
                return response_text
            else:
                error_msg = f"ERROR :  {response.status_code}: {response.text}"
                return error_msg
                
        except Exception as e:
            error_msg = f"ERROR : {str(e)}"
            return error_msg


deepgen_tool = DeepGenTool()

root_agent = Agent(
    model="gemini-2.0-flash-exp", # The model used here is just there so we can initialize the agent with ADK
                                  # It won't be used because the agent uses only DeepGen tool to generate responses
    name="debate_agent",
    description="Agent using DeepGen tool for debates ",
    instruction="You are a debate agent that uses the Deepgen tool to generate responses.",
    tools=[deepgen_tool]
)

# Test
if __name__ == "__main__":
    #Simple test to check if DeepGen tool is working
    response = deepgen_tool.chat("Hello, how are you?")
    print("Response :", response)