import audioop
import numpy as np
from audio import twilio_ulaw8k_to_adk_pcm16k, adk_pcm24k_to_twilio_ulaw8k

def test_ulaw_decoding():
    # 1. Create a simple 8kHz signal (max amplitude)
    # 0x00 is max positive value in u-law
    silence_ulaw = b'\x00' * 160 
    
    # My implementation
    pcm16_my = twilio_ulaw8k_to_adk_pcm16k(silence_ulaw)
    
    print(f"Input U-law size: {len(silence_ulaw)}")
    print(f"Output PCM16 size: {len(pcm16_my)}")
    
    # Check for NaNs or Infs
    arr = np.frombuffer(pcm16_my, dtype=np.int16)
    if not np.isfinite(arr).all():
        print("ERROR: Output contains NaNs or Infs")
    
    print(f"Output Max: {np.max(arr)}, Min: {np.min(arr)}, Mean: {np.mean(arr)}")
    
    if len(pcm16_my) != 320 * 2: # 160 samples * 2 (16k/8k) * 2 bytes/sample
        # soxr might not output exactly 2x samples due to filtering/delay? 
        # But for exact ratio resampling it usually does.
        # 160 samples @ 8kHz = 20ms. 20ms @ 16kHz = 320 samples. 320 * 2 bytes = 640 bytes.
        print(f"WARNING: Expected 640 bytes, got {len(pcm16_my)}")

    # Compare with audioop (if available)
    try:
        # audioop.ulaw2lin returns 2-byte PCM at same rate
        pcm8_ref = audioop.ulaw2lin(silence_ulaw, 2)
        print("audioop decoding successful.")
        
        arr_ref = np.frombuffer(pcm8_ref, dtype=np.int16)
        print(f"Ref Max: {np.max(arr_ref)}, Min: {np.min(arr_ref)}, Mean: {np.mean(arr_ref)}")
        
    except Exception as e:
        print(f"audioop not available: {e}")

if __name__ == "__main__":
    test_ulaw_decoding()
