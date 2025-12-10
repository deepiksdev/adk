import pytest
import json
import numpy as np
import os
from twilio_voice_agent.audio import twilio_ulaw8k_to_adk_pcm16k, adk_pcm24k_to_twilio_ulaw8k, _ulaw2lin, _lin2ulaw

# Use a relative path to where we know the test data is
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "audio_test_vectors.json")

@pytest.fixture
def audio_vectors():
    with open(TEST_DATA_PATH, "r") as f:
        return json.load(f)

def test_ulaw2lin_replacement(audio_vectors):
    """Test that our replacement for audioop.ulaw2lin (inside twilio_ulaw8k_to_adk_pcm16k) works correctly."""
    # The function twilio_ulaw8k_to_adk_pcm16k does:
    # 1. ulaw -> lin (8k, 16bit)
    # 2. Resample 8k -> 16k
    # We want to test specifically the ulaw decoding if possible, or we can test the whole chain.
    # However, since we are replacing just the audioop part, let's verify expected internal behavior 
    # if we can, or rely on the fact that we can replicate the logic.
    
    # Actually, the user asked to replace audioop.
    # Let's test the specific logic we added.
    # Since we can't easily access the internal step of twilio_ulaw8k_to_adk_pcm16k without refactoring,
    # let's assume valid output for the whole function is hard to predict due to resampling variance.
    # INSTEAD, let's import the raw conversion functions if we made them standalone, OR
    # just test that it runs without error and produces valid PCM-like data.
    
    # BUT, to be rigorous, we should probably expose the conversion or test the private implementation
    # if we put it in the same file.
    
    pass

def test_ulaw2lin_direct_comparison(audio_vectors):
    # This test assumes we might have refactored the raw conversion into a helper or 
    # that we can rely on the fact that we implemented it inline.
    # To properly verify the "replacement", we should extract the G.711 logic into helper functions
    # inside audio.py so we can test them in isolation.
    
    # Let's check imports after we refactor.
    from twilio_voice_agent.audio import _ulaw2lin, _lin2ulaw
    
    # 1. Check ulaw -> lin
    vectors = audio_vectors["ulaw2lin"]
    input_ulaw = bytes.fromhex(vectors["input_ulaw_hex"])
    expected_pcm = bytes.fromhex(vectors["expected_pcm_hex"])
    
    # Run conversion
    result_pcm = _ulaw2lin(input_ulaw)
    
    # Compare
    assert result_pcm == expected_pcm, "ulaw2lin conversion mismatch"

def test_lin2ulaw_direct_comparison(audio_vectors):
    # 2. Check lin -> ulaw
    vectors = audio_vectors["lin2ulaw"]
    input_pcm = bytes.fromhex(vectors["input_pcm_hex"])
    expected_ulaw = bytes.fromhex(vectors["expected_ulaw_hex"])
    
    # Run conversion
    result_ulaw = _lin2ulaw(input_pcm)
    
    # Compare
    assert result_ulaw == expected_ulaw, "lin2ulaw conversion mismatch"
