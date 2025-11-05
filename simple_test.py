#!/usr/bin/env python3
"""
Simple test to verify customer service agent import and basic setup.
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from customer_service.agent import root_agent
    from customer_service.config import Config

    print("✅ Customer Service Agent imported successfully!")
    print(f"Agent name: {root_agent.name}")
    print(f"Agent model: {root_agent.model}")
    print(f"Tools available: {len(root_agent.tools)}")

    # Check configuration
    config = Config()
    print(f"Config app name: {config.app_name}")
    print(f"Config Vertex AI setting: {config.GENAI_USE_VERTEXAI}")
    print(f"Config API key set: {'Yes' if config.API_KEY else 'No'}")

    print("\n📋 Tool list:")
    for i, tool in enumerate(root_agent.tools, 1):
        print(f"  {i}. {getattr(tool, '__name__', str(tool))}")

    print("\n✅ Ready to test! You can run 'adk web' to interact with the agent.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()