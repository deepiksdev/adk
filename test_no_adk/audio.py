# import audioop  <-- REMOVED
import numpy as np
import soxr

# Internal G.711 u-law tables and logic
# Pre-computed tables are faster than computing log/exp every sample.
# Standard G.711 u-law definition.

def _ulaw2lin(ulaw_bytes: bytes) -> bytes:
    """Convert u-law bytes to 16-bit linear PCM."""
    ulaw_vals = np.frombuffer(ulaw_bytes, dtype=np.uint8)
    return _ULAW_TO_LIN_TABLE[ulaw_vals].tobytes()

def _lin2ulaw(pcm_bytes: bytes) -> bytes:
    """Convert 16-bit linear PCM to u-law bytes."""
    samples = np.frombuffer(pcm_bytes, dtype=np.int16)
    
    indices = samples.view(np.uint16)
    return _LIN_TO_ULAW_TABLE[indices].tobytes()


# --- Look-up Tables Generation ---
# Generate these once at module level

def _generate_ulaw_to_lin_table():
    # Standard G.711 expansion
    t = np.zeros(256, dtype=np.int16)
    for i in range(256):
        ulaw = ~i & 0xFF # Invert logic
        sign = -1 if (ulaw & 0x80) else 1
        exponent = (ulaw >> 4) & 0x07
        mantissa = ulaw & 0x0F
        sample = sign * ( ((mantissa * 2 + 33) << (exponent + 2)) - 132 )
        t[i] = sample
    return t

def _generate_lin_to_ulaw_table():
    # 65536 entries for full 16-bit coverage
    # We map every possible int16 value to its u-law byte
    t = np.zeros(65536, dtype=np.uint8)
    
    # Implementation based on standard G.711 C code
    VAL_CLIP = 32635
    BIAS = 0x84
    
    # Helper for scalar
    def encode_sample(sample):
        sign = 0
        if sample < 0:
            sample = -sample
            sign = 0x80
        
        if sample > VAL_CLIP:
            sample = VAL_CLIP
            
        sample += BIAS
        exponent = 0
        
        if sample >= (1 << 15): warnings = True 
        if sample >= 0x4000: exponent = 7 # 16384
        elif sample >= 0x2000: exponent = 6 # 8192
        elif sample >= 0x1000: exponent = 5 # 4096
        elif sample >= 0x0800: exponent = 4 # 2048
        elif sample >= 0x0400: exponent = 3 # 1024
        elif sample >= 0x0200: exponent = 2 # 512
        elif sample >= 0x0100: exponent = 1 # 256
        else: exponent = 0
        
        mantissa = (sample >> (exponent + 3)) & 0x0F
        ulaw_byte = ~(sign | (exponent << 4) | mantissa) & 0xFF
        return ulaw_byte

    # Fill table
    for s in range(-32768, 32768):
        val = encode_sample(s)
        # Cast s to uint16 index
        idx = s & 0xFFFF
        t[idx] = val
        
    return t

_ULAW_TO_LIN_TABLE = _generate_ulaw_to_lin_table()
_LIN_TO_ULAW_TABLE = _generate_lin_to_ulaw_table()


# Inbound: Twilio 8-bit 8kHz μ-law -> 16-bit 16kHz PCM for ADK
def twilio_ulaw8k_to_adk_pcm16k(mulaw_bytes: bytes) -> bytes:
    if not mulaw_bytes:
        return b""
    # pcm8 = audioop.ulaw2lin(mulaw_bytes, 2)
    pcm8 = _ulaw2lin(mulaw_bytes)
    
    # resample: int16 <-> float32 for soxr
    x = np.frombuffer(pcm8, dtype=np.int16).astype(np.float32) / 32768.0
    y = soxr.resample(x, 8000, 16000) # 8kHz -> 16kHz
    pcm16 = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    return pcm16

# Outbound: ADK 16-bit 24kHz PCM -> Twilio 8-bit 8kHz μ-law
def adk_pcm24k_to_twilio_ulaw8k(pcm24: bytes) -> bytes:
    if not pcm24:
        return b""
    x = np.frombuffer(pcm24, dtype=np.int16).astype(np.float32) / 32768.0
    y = soxr.resample(x, 24000, 8000) # 24kHz -> 8kHz
    pcm8_samples = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    
    ulaw = _lin2ulaw(pcm8_samples)
    return ulaw

# Outbound: ADK 16-bit 16kHz PCM -> Twilio 8-bit 8kHz μ-law
# Useful for echo tests or if Gemini sends 16k
def adk_pcm16k_to_twilio_ulaw8k(pcm16: bytes) -> bytes:
    if not pcm16:
        return b""
    x = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
    y = soxr.resample(x, 16000, 8000) # 16kHz -> 8kHz
    pcm8_samples = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    
    ulaw = _lin2ulaw(pcm8_samples)
    return ulaw
