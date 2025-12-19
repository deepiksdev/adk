
import pytest
from unittest.mock import MagicMock, AsyncMock
from google.genai import types
from google.adk.events.event import Event
from google.adk.agents.invocation_context import InvocationContext
from plugins.logging_plugin import LoggingPlugin

@pytest.mark.asyncio
async def test_on_event_callback_logs_usage_metadata(capsys):
    # Setup
    plugin = LoggingPlugin()
    mock_context = MagicMock(spec=InvocationContext)
    
    # Create an event with usage metadata
    usage_metadata = types.GenerateContentResponseUsageMetadata(
        prompt_token_count=100,
        candidates_token_count=50,
        total_token_count=150
    )
    
    event = Event(
        id="test_event_id",
        author="test_user",
        usage_metadata=usage_metadata
    )
    
    # Act
    await plugin.on_event_callback(invocation_context=mock_context, event=event)
    
    # Assert
    captured = capsys.readouterr()
    output = captured.out
    
    # Verify standard event logs are present
    assert "📢 EVENT YIELDED" in output
    assert "Event ID: test_event_id" in output
    
    # Verify usage metadata logs are present (EXPECTED TO FAIL BEFORE FIX)
    assert "Token Usage" in output
    assert "Input: 100" in output
    assert "Output: 50" in output
    assert "Total: 150" in output
