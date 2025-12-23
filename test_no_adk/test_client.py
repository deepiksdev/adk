import asyncio
import websockets
import json
import base64
import sys

# Simulation configuration
URI = "ws://localhost:8765/twilio/stream"

async def test_client():
    print(f"Connecting to {URI}...")
    try:
        async with websockets.connect(URI) as websocket:
            print("Connected.")
            
            # 1. Send Connected event (Twilio style)
            # Not strictly required by logic but good simulation
            await websocket.send(json.dumps({
                "event": "connected",
                "protocol": "Call",
                "version": "1.0.0"
            }))

            # 2. Send Start event
            stream_sid = "MZ12345"
            await websocket.send(json.dumps({
                "event": "start",
                "sequenceNumber": "1",
                "start": {
                    "accountSid": "AC123",
                    "streamSid": stream_sid,
                    "callSid": "CA123",
                    "tracks": ["inbound"],
                    "mediaFormat": {
                        "encoding": "audio/x-mulaw",
                        "sampleRate": 8000,
                        "channels": 1
                    },
                    "customParameters": {}
                },
                "streamSid": stream_sid
            }))
            print("Sent 'start' event.")

            # Send some audio immediately to trigger the server-side processing
            # 1 sec of silence (8000 samples)
            silence = b'\xff' * 160 
            payload = base64.b64encode(silence).decode("ascii")
            await websocket.send(json.dumps({
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": payload,
                    "track": "inbound",
                    "chunk": "1",
                    "timestamp": "1"
                }
            }))

            # 3. Listen for media
            # We expect the agent to say hello immediately.
            
            print("Listening for audio response...")
            media_received = False
            
            # Wait for up to 10 seconds for some media
            startTime = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - startTime) < 10:
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    message = json.loads(message_str)
                    
                    if message.get("event") == "media":
                        print("Received media packet!")
                        media_received = True
                        break
                    else:
                        print(f"Received other event: {message.get('event')}")
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for message, sending silence...")
                    # Send some silence to keep connection alive or simulate input
                    # 1 sec of silence (8000 samples)
                    silence = b'\xff' * 160 # small chunk
                    payload = base64.b64encode(silence).decode("ascii")
                    await websocket.send(json.dumps({
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {
                            "payload": payload,
                            "track": "inbound",
                            "chunk": "1",
                            "timestamp": "1"
                        }
                    }))
            
            if media_received:
                print("SUCCESS: Received audio from agent.")
            else:
                print("FAILURE: Did not receive audio from agent.")
                sys.exit(1)

            # Cleanup
            await websocket.send(json.dumps({
                "event": "stop",
                "streamSid": stream_sid
            }))
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_client())
