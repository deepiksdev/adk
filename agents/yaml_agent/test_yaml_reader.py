#!/usr/bin/env python3
"""
Simple test to read YAML config and create agent from it.
"""
import os
from google.adk.agents import config_agent_utils

def get_yaml_string_from_file(yaml_file_path: str) -> str:
    """
    Read and return the YAML string from a file.

    Args:
        yaml_file_path: Path to the YAML file

    Returns:
        String content of the YAML file
    """
    with open(yaml_file_path, 'r') as file:
        return file.read()

def get_agent_from_yaml_string(yaml_content: str):
    """
    Create an ADK agent from a YAML string.

    Args:
        yaml_content: YAML configuration as string

    Returns:
        ADK Agent instance
    """
    # Write the YAML content to a temporary file
    temp_file = "/tmp/temp_agent.yaml"
    with open(temp_file, 'w') as f:
        f.write(yaml_content)

    # Use ADK's config utility to load the agent
    agent = config_agent_utils.from_config(temp_file)

    # Clean up temp file
    os.remove(temp_file)

    return agent

def main():
    """Test the functions."""
    # Define YAML string directly (no file needed)
    yaml_string = """name: dynamic_test_agent
description: A dynamically created agent from YAML string
instruction: You are a test agent created directly from a YAML string without needing a file
model: gemini-2.5-flash
tools:
  - name: google_search"""

    print("YAML content (from string, no file):")
    print(yaml_string)
    print("\n" + "="*50 + "\n")

    # Create agent from the YAML string
    agent = get_agent_from_yaml_string(yaml_string)

    print(f"Agent created from YAML string:")
    print(f"  Name: {agent.name}")
    print(f"  Model: {agent.model}")
    print(f"  Description: {getattr(agent, 'description', 'N/A')}")
    print(f"  Instruction: {agent.instruction}")
    print(f"  Tools: {len(agent.tools) if agent.tools else 0}")

    # Test with a different YAML string
    print("\n" + "="*50)
    print("Testing with different YAML configuration:\n")

    different_yaml = """name: customer_service_bot
description: A customer service agent
instruction: You are a helpful customer service representative. Be polite and professional.
model: gemini-2.5-flash"""

    print("Second YAML content:")
    print(different_yaml)
    print()

    agent2 = get_agent_from_yaml_string(different_yaml)
    print(f"Second agent created:")
    print(f"  Name: {agent2.name}")
    print(f"  Model: {agent2.model}")
    print(f"  Description: {getattr(agent2, 'description', 'N/A')}")
    print(f"  Instruction: {agent2.instruction}")

if __name__ == "__main__":
    main()