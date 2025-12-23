import os
import asyncio
import base64
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from typing import Dict
from google.genai import Client, types

# Twilio imports
from twilio.twiml.voice_response import Connect, Stream, VoiceResponse
from audio import adk_pcm24k_to_twilio_ulaw8k, twilio_ulaw8k_to_adk_pcm16k

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Default Gemini configuration
MODEL = "gemini-2.0-flash-exp"
API_KEY = os.environ.get("GOOGLE_API_KEY")

@app.get("/")
async def root():
    return {"message": "Twilio Voice Agent (No ADK) is running"}

@app.post("/")
@app.post("/connect")
async def create_call(req: Request):
    """Generate TwiML to connect a call to a Twilio Media Stream"""
    host = req.url.hostname
    port = req.url.port
    
    # In local development, req.url.hostname might be 'localhost', 
    # but Twilio needs a public URL. Assumes this runs behind ngrok or similar 
    # if hit from outside, OR just return the TwiML to the caller.
    
    # If run locally with ngrok, the Host header usually contains the public domain
    # But for simplicity, we construct it from the request url.
    ws_host = f"{host}:{port}" if port else host
    
    # Handle protocol: wss for https, ws for http
    ws_protocol = "wss" if req.url.scheme == "https" else "ws"
    ws_url = f"{ws_protocol}://{ws_host}/twilio/stream"

    stream = Stream(url=ws_url)
    connect = Connect()
    connect.append(stream)
    response = VoiceResponse()
    response.append(connect)
    
    logger.info(f"Returning TwiML with Stream URL: {ws_url}")
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/twilio/stream")
async def twilio_websocket(ws: WebSocket):
    await ws.accept()
    logger.info("Twilio WebSocket connected")

    # Audio queues
    # Twilio -> Agent (Gemini)
    # Agent (Gemini) -> Twilio
    
    client = Client(api_key=API_KEY)
    
    # Configuration for Gemini B2B session
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
            )
        ),
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                prefix_padding_ms=150,
                silence_duration_ms=400,
            )
        )
    )

    try:
        # 1. Receive 'start' event from Twilio
        # Twilio sends a 'connected' event first, then 'start'.
        # We process messages until we get 'start'.
        
        stream_sid = None
        
        # Start Gemini session
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            logger.info("Connected to Gemini Realtime API")

            async def twilio_receiver():
                nonlocal stream_sid
                try:
                    while True:
                        try:
                            # Receive JSON from Twilio
                            message = await ws.receive_json()
                        except RuntimeError:
                            # WebSocket disconnect
                            break
                            
                        event_type = message.get("event")

                        if event_type == "start":
                            stream_sid = message["start"]["streamSid"]
                            logger.info(f"Stream started: {stream_sid}")
                            
                            # Initial greeting
                            # We can send text to Gemini to trigger an audio response
                            await session.send(input="Hello! Please introduce yourself briefly.", end_of_turn=True)

                        elif event_type == "media":
                            # Audio from user (Twilio)
                            payload = message["media"]["payload"]
                            # decode base64 -> mulaw
                            mulaw_bytes = base64.b64decode(payload)
                            # mulaw 8k -> pcm 16k
                            pcm_bytes = twilio_ulaw8k_to_adk_pcm16k(mulaw_bytes)
                            
                            # Send to Gemini
                            # Protocol: mime_type="audio/pcm;rate=16000"
                            # logger.info(f"Sending audio chunk to Gemini: {len(pcm_bytes)} bytes")
                            await session.send(input={"data": pcm_bytes, "mime_type": "audio/pcm;rate=16000"}, end_of_turn=False)
                            
                        elif event_type == "stop":
                            logger.info("Twilio stream stopped")
                            break
                        elif event_type == "dtmf":
                            logger.info(f"DTMF received: {message['dtmf']['digit']}")
                except Exception as e:
                    logger.error(f"Error in twilio_receiver: {e}")

            async def gemini_receiver():
                nonlocal stream_sid
                try:
                    async for response in session.receive():
                        # We look for audio data in the server content
                        server_content = response.server_content
                        if server_content is None:
                            continue

                        # Audio is usually in model_turn.parts
                        model_turn = server_content.model_turn
                        if model_turn:
                            for part in model_turn.parts:
                                if part.text:
                                    logger.info(f"Gemini Text: {part.text}")
                                    
                                if part.inline_data:
                                    mime_type = part.inline_data.mime_type
                                    if mime_type.startswith("audio/pcm"):
                                        pcm_data = part.inline_data.data
                                        # Convert 24k PCM -> 8k u-law
                                        ulaw_data = adk_pcm24k_to_twilio_ulaw8k(pcm_data)
                                        
                                        # Encode base64
                                        payload = base64.b64encode(ulaw_data).decode("ascii")
                                        
                                        if stream_sid:
                                            await ws.send_json({
                                                "event": "media",
                                                "streamSid": stream_sid,
                                                "media": {
                                                    "payload": payload
                                                }
                                            })
                                            
                        # Handle turn completions or interruptions if needed
                        # "turn_complete" is currently inferred or handled by client logic
                        
                except Exception as e:
                    logger.error(f"Error in gemini_receiver: {e}")

            # Run both loops
            await asyncio.gather(twilio_receiver(), gemini_receiver())

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in twilio_websocket: {e}")
