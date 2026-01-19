# import audioop  <-- REMOVED
import numpy as np
import soxr

# Internal G.711 u-law tables and logic
# Pre-computed tables are faster than computing log/exp every sample.
# Standard G.711 u-law definition.

def _ulaw2lin(ulaw_bytes: bytes) -> bytes:
    """Convert u-law bytes to 16-bit linear PCM."""
    # u-law to linear conversion table
    # We can compute it or use a lookup table. u-law is 8-bit, so 256 entries.
    # Formula: s = sign(u) * (1/255) * ((1+255)^|u| - 1) ... simplified:
    #
    # Actually, Python's audioop used a standard table. Let's implement the standard expansion.
    # 
    # Input: 8-bit u-law
    # Output: 16-bit PCM (signed)
    
    # Helper to generate the table if needed, but doing it on fly or hardcoding?
    # NumPy allows efficient logical operations.
    
    # Create the LUT once or cache it? For simplicity, create it inside or global.
    # Use global LUT for performance.
    
    ulaw_vals = np.frombuffer(ulaw_bytes, dtype=np.uint8)
    return _ULAW_TO_LIN_TABLE[ulaw_vals].tobytes()

def _lin2ulaw(pcm_bytes: bytes) -> bytes:
    """Convert 16-bit linear PCM to u-law bytes."""
    # Linear to u-law is trickier; requires compression.
    # Simple G.711 encoder.
    samples = np.frombuffer(pcm_bytes, dtype=np.int16)
    
    # Clamp to 13 bits (standard for u-law input is effectively 14 bits signed but often treated as 13)
    # Actually G.711 takes 14 bit signed linear.
    # audioop.lin2ulaw takes 16-bit and likely truncates/rounds.
    
    # Let's use a vectorized implementation.
    # 1. Get sign and magnitude
    sign = (samples < 0)
    mag = np.abs(samples)
    
    # 2. Clip to 32635 ? Standard G.711 clipping
    mag = np.clip(mag, 0, 32635)
    
    # 3. Add bias 0x84 (132)
    mag += 132
    
    # 4. Find exponent and mantissa
    # We need position of leading 1.
    # This is rough to do efficiently in pure numpy without bitwise hacks.
    # Alternatively, we can use a massive LUT (65536 entries) for 16-bit -> 8-bit.
    # A 64KB LUT is trivial for modern memory.
    
    # We track values as uint16 to use as index.
    # samples (int16) -> interpret as uint16 for indexing.
    # But negative values need to be handled.
    # We can map -32768..32767 to 0..65535 index?
    # No, simple array indexing: table[sample] where sample is int16.
    # Python/NumPy handles negative indices wrapping around, which is fine if we order the table right.
    # Or just cast to uint16 viewing.
    
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
    
    # Iterate -32768 to 32767
    # But array is 0..65535. 
    # approach: create standard encoding function, verify against audioop, then fill table.
    # OR: Replicate the bit manipulation logic for single sample then vectorize generation?
    # Faster to just write the logic in loop, it runs once at import time.
    
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
        # Determine exponent (approx log2)
        # 7 6 5 4 3 2 1 0
        if sample >= (1 << 15): warnings = True # Shouldn't happen max 32635+132=32767
        # exp ranges 0-7
        # simple check
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
    # Indices 0 to 32767 correspond to positive 0..32767
    # Indices 32768 to 65535 correspond to negative -32768..-1 (in two's complement view)
    
    # However we can just iterate -32768 to 32767 and cast to uint16 to find index
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
    
    # ulaw = audioop.lin2ulaw(pcm8, 2)
    ulaw = _lin2ulaw(pcm8_samples)
    return ulaw
