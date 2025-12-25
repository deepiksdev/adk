import asyncio
import websockets
import json
import base64
import sys
import numpy as np
from audio import _lin2ulaw, adk_pcm16k_to_twilio_ulaw8k

# Simulation configuration
URI = "ws://localhost:8765/twilio/stream"

def generate_tone_ulaw(duration_sec=1.0, freq=440.0, sample_rate=8000):
    """Generates a sine wave tone in u-law 8kHz."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # Generate sine wave with max amplitude (32767)
    # Use 0.5 amplitude to be safe but loud
    pcm = (np.sin(2 * np.pi * freq * t) * 16000).astype(np.int16)
    return _lin2ulaw(pcm.tobytes())

async def test_speech():
    print(f"Connecting to {URI}...")
    try:
        async with websockets.connect(URI) as websocket:
            print("Connected.")
            
            # 1. Start Event
            stream_sid = "TEST_SPEECH_01"
            await websocket.send(json.dumps({
                "event": "start",
                "start": { "streamSid": stream_sid, "mediaFormat": { "encoding": "audio/x-mulaw", "sampleRate": 8000 } },
                "streamSid": stream_sid
            }))
            
            # 2. Wait for initial audio (Intro)
            print("Waiting for intro...")
            # Consume intro audio for a bit
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(msg)
                    if data.get("event") == "media":
                        continue # Ignore intro audio
            except asyncio.TimeoutError:
                print("Intro finished (or silence). Sending speech...")

            # 3. Send Real Speech Audio
            print("Reading speech.pcm...")
            with open("speech.pcm", "rb") as f:
                pcm_data = f.read()
            
            # Convert 16k PCM to 8k u-law
            ulaw_audio = adk_pcm16k_to_twilio_ulaw8k(pcm_data)
            
            chunk_size = 160 # 20ms at 8kHz
            
            print(f"Sending {len(ulaw_audio)} bytes of speech audio (single shot)...")
            
            payload = base64.b64encode(ulaw_audio).decode("ascii")
            await websocket.send(json.dumps({
                "event": "media",
                "streamSid": stream_sid,
                "media": { "payload": payload }
            }))
            
            # for i in range(0, len(ulaw_audio), chunk_size):
            #     chunk = ulaw_audio[i:i+chunk_size]
            #     if len(chunk) < chunk_size: # padding
            #          chunk = chunk + b'\xff' * (chunk_size - len(chunk))
            #          
            #     payload = base64.b64encode(chunk).decode("ascii")
            #     await websocket.send(json.dumps({
            #         "event": "media",
            #         "streamSid": stream_sid,
            #         "media": { "payload": payload }
            #     }))
            #     await asyncio.sleep(0.02) # Simulate real-time
            
            await asyncio.sleep(5.0) # Wait for processing
            
            print("Finished sending speech. Sending silence...")
            
            # Send 2 seconds of silence to trigger VAD End of Speech
            silence_chunk = b'\xFF' * chunk_size # u-law silence is 0xFF
            for _ in range(0, 100): # 100 * 20ms = 2000ms
                payload = base64.b64encode(silence_chunk).decode("ascii")
                await websocket.send(json.dumps({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": { "payload": payload }
                }))
                await asyncio.sleep(0.02)
                
            print("Finished sending silence. Sending MANUAL TRIGGER...")
            await websocket.send(json.dumps({
                "event": "mark_end_of_speech",
                "streamSid": stream_sid
            }))
            
            print("Trigger sent. Waiting for response...")
            
            # 4. Wait for response
            # expected: Audio response or at least logs on server showing transcript
            # We can't easily see server logs here, but if we receive media back, it means VAD triggered.
            
            try:
                response_received = False
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(msg)
                    if data.get("event") == "media":
                        print("SUCCESS: Received audio response after speaking!")
                        response_received = True
                        break
            except asyncio.TimeoutError:
                print("FAILURE: Timed out waiting for response.")
                
            if not response_received:
                sys.exit(1)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_speech())
