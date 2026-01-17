import logging
import os
import asyncio
import base64
from uuid import uuid4

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google.adk.cli.fast_api import get_fast_api_app

# Twilio imports
from twilio.twiml.voice_response import Connect, Stream, VoiceResponse
from agents.twilio_voice_agent.live_messaging import AgentEvent, agent_to_client_messaging, send_pcm_to_agent, start_agent_session, text_to_content, start_agent_session_with_agent
from agents.twilio_voice_agent.audio import adk_pcm24k_to_twilio_ulaw8k, twilio_ulaw8k_to_adk_pcm16k

# Import voicemail agent if needed
try:
    from agents.voicemail_agent.agent import root_agent as voicemail_root_agent
except ImportError:
    voicemail_root_agent = None

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
# Initialize the standard ADK FastAPI app
# agents_dir="." allows it to find agents in the current directory
app = get_fast_api_app(
    agents_dir="agents",
    web=True,  # Enable the Web UI
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    extra_plugins=["plugins.logging_plugin.LoggingPlugin"]
)

# --- PATCH FOR WEB UI CONFIGURATION ---
# --- PATCH FOR WEB UI CONFIGURATION ---
# --- PATCH FOR WEB UI CONFIGURATION ---
try:
    print("PATCH: Attempting to patch Runner/InMemoryRunner for French voice...")
    
    import google.adk.runners
    from google.adk.runners import InMemoryRunner, Runner
    from agents.voicemail_agent.agent import run_config as voicemail_run_config

    print(f"PATCH: InMemoryRunner path: {InMemoryRunner}")
    print(f"PATCH: Runner path: {Runner}")

    # Patch the BASE class Runner, as run_live is likely defined there
    if not hasattr(Runner, "_original_run_live"):
        Runner._original_run_live = Runner.run_live
        
    async def patched_run_live(self, session, live_request_queue, run_config=None):
        print(f"PATCH: run_live called on {self.__class__.__name__} for app: {getattr(self, 'app_name', 'UNKNOWN')}")
        
        # Check if this runner is for the voicemail_agent
        if getattr(self, 'app_name', '') == "voicemail_agent":
            # If no config provided (default from Web UI), inject ours
            if run_config is None:
                print("PATCH: Injecting French RunConfig into Runner!")
                run_config = voicemail_run_config
        
        # Call original using Keyword Arguments (signature enforces it)
        async for item in Runner._original_run_live(self, session=session, live_request_queue=live_request_queue, run_config=run_config):
            yield item
            
    # Apply patch to Runner (which InMemoryRunner inherits from)
    Runner.run_live = patched_run_live
    print("PATCH: Runner (base) patch successfully applied.")

except ImportError as e:
    print(f"PATCH: Could not import dependencies: {e}")
except Exception as e:
    print(f"PATCH: Failed to patch Runner: {e}")
# ----------------------------------------
# ----------------------------------------

@app.get("/hello")
def hello():
    """Simple Hello World endpoint for testing custom routes."""
    return {"message": "Hello World"}

@app.post("/connect")
def create_call(req: Request):
    """Generate TwiML to connect a call to a Twilio Media Stream"""
    host = req.url.hostname
    scheme = req.url.scheme
    #ws_protocol = "ws" if scheme == "http" else "wss"
    ws_protocol= "wss"
    ws_url = f"{ws_protocol}://{host}/twilio/stream"

    stream = Stream(url=ws_url)
    connect = Connect()
    connect.append(stream)
    response = VoiceResponse()
    response.append(connect)
    
    logger.info(response)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/twilio/stream")
async def twilio_websocket(ws: WebSocket):
    """Handle Twilio Media Stream WebSocket connection"""
    await ws.accept()
    await ws.receive_json() # throw away `connected` event
    
    start_event = await ws.receive_json()
    assert start_event["event"] == "start"
    
    call_sid = start_event["start"]["callSid"]
    stream_sid = start_event["start"]["streamSid"]
    user_id = uuid4().hex # Fake user ID for this example
    
    
    # Check if we should use the voicemail agent
    is_voicemail_mode = os.environ.get("USE_VOICEMAIL_AGENT", "false").lower() == "true"
    
    if voicemail_root_agent:
        # Start a session with the voicemail agent
        live_events, live_request_queue = await start_agent_session_with_agent(user_id, call_sid, voicemail_root_agent)
        # For voicemail, we let the instruction handle the first greeting naturally or we can force it.
        # The issue specifies: It should start by replying in French...
        # So we send an initial trigger.
        initial_message = text_to_content(
            f"La conversation commence. Dis EXACTEMENT la phrase suivante pour accueillir le correspondant : 'Bonjour, je suis une IA répondeur téléphonique. {os.environ.get('VOICEMAIL_USER_NAME', 'User')} n'est pas disponible. Voulez-vous que je prenne un message à son intention, ou avez-vous des questions ?'", 
            "user"
        )
    else:

        live_events, live_request_queue = await start_agent_session(user_id, call_sid)
        # Sending an initial message makes the agent speak first when the call starts.
        initial_message = text_to_content("Présente-toi en Français.", "user")
    
    live_request_queue.send_content(initial_message)

    async def handle_agent_event(event: AgentEvent):
        """Handle outgoing AgentEvent to Twilio WebSocket"""
        if event.type == "complete":
            # logger.info(f"Agent turn complete at {event.timestamp}")
            return
            
        if event.type == "interrupted":
            # logger.info(f"Agent interrupted at {event.timestamp}")
            # https://www.twilio.com/docs/voice/media-streams/websocket-messages#clear
            return await ws.send_json({"event": "clear", "streamSid": stream_sid})
            
        ulaw_bytes = adk_pcm24k_to_twilio_ulaw8k(event.payload)
        payload = base64.b64encode(ulaw_bytes).decode("ascii")
        
        await ws.send_json(
            {
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": payload},
            }
        )

    async def websocket_loop():
        """
        Handle incoming WebSocket messages to Agent.
        """
        while True:
            event = await ws.receive_json()
            event_type = event["event"]
            
            if event_type == "stop":
                logger.debug(f"Call ended by Twilio. Stream SID: {stream_sid}")
                break
                
            if event_type == "start" or event_type == "connected":
                logger.warning(f"Unexpected Twilio Initialization event: {event}")
                continue
                
            elif event_type == "dtmf":
                digit = event["dtmf"]["digit"]
                logger.info(f"DTMF: {digit}")
                continue
                
            elif event_type == "mark":
                logger.info(f"Twilio sent a Mark Event: {event}")
                continue
                
            elif event_type == "media":
                payload = event["media"]["payload"]
                mulaw_bytes = base64.b64decode(payload)
                pcm_bytes = twilio_ulaw8k_to_adk_pcm16k(mulaw_bytes)
                send_pcm_to_agent(pcm_bytes, live_request_queue)

    try:
        websocket_coro = websocket_loop()
        websocket_task = asyncio.create_task(websocket_coro)
        
        messaging_coro = agent_to_client_messaging(handle_agent_event, live_events)
        messaging_task = asyncio.create_task(messaging_coro)
        
        tasks = [websocket_task, messaging_task]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        for p in pending:
            p.cancel()
            
        await asyncio.gather(*pending, return_exceptions=True)
        
        for d in done:
            if d.cancelled():
                continue
            exception = d.exception()
            if exception:
                raise exception
                
    except (KeyboardInterrupt, asyncio.CancelledError, WebSocketDisconnect):
        logger.warning("Process interrupted, exiting...")
    except Exception as ex:
        logger.exception(f"Unexpected Error: {ex}")
    finally:
        live_request_queue.close()
        try:
            await ws.close()
        except Exception as ex:
            logger.warning(f"Error while closing WebSocket: {ex}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
