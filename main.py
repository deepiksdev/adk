import logging
import os
import asyncio
import base64
import importlib
from uuid import uuid4

from fastapi import Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from google.adk.cli.fast_api import get_fast_api_app

# Twilio imports
from twilio.twiml.voice_response import Connect, Stream, VoiceResponse
from channels.twilio.live_messaging import AgentEvent, agent_to_client_messaging, send_pcm_to_agent, start_agent_session, text_to_content, start_agent_session_with_agent
from channels.twilio.audio import adk_pcm24k_to_twilio_ulaw8k, twilio_ulaw8k_to_adk_pcm16k

# Import assistant agent if needed
try:
    from agents.assistant_agent.agent import root_agent as assistant_root_agent
except ImportError:
    assistant_root_agent = None



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

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PATCH FOR WEB UI CONFIGURATION ---
# --- PATCH FOR WEB UI CONFIGURATION ---
# --- PATCH FOR WEB UI CONFIGURATION ---
try:
    print("PATCH: Attempting to patch Runner/InMemoryRunner for French voice...")
    
    import google.adk.runners
    from google.adk.runners import InMemoryRunner, Runner
    import importlib

    print(f"PATCH: InMemoryRunner path: {InMemoryRunner}")
    print(f"PATCH: Runner path: {Runner}")

    # Patch the BASE class Runner, as run_live is likely defined there
    if not hasattr(Runner, "_original_run_live"):
        Runner._original_run_live = Runner.run_live
        
    async def patched_run_live(self, session, live_request_queue, run_config=None):
        app_name = getattr(self, "app_name", None)
        print(f"PATCH: run_live called on {self.__class__.__name__} for app: {app_name}")
        
        if app_name:
            try:
                # Dynamically import the agent module
                agent_module = importlib.import_module(f"agents.{app_name}.agent")
                
                # Check for root_run_config in the agent module
                if hasattr(agent_module, "root_run_config"):
                    root_run_config = getattr(agent_module, "root_run_config")
                    print(f"PATCH: Found root_run_config for {app_name}: {root_run_config}")
                    
                    if run_config is None:
                        print(f"PATCH: Injecting root_run_config for {app_name}")
                        run_config = root_run_config
                    else:
                        print(f"PATCH: Merging into existing run_config for {app_name}")
                        # Overwrite specific settings if they exist in root_run_config
                        if root_run_config.speech_config:
                            run_config.speech_config = root_run_config.speech_config
                        if root_run_config.realtime_input_config:
                            run_config.realtime_input_config = root_run_config.realtime_input_config
            except ImportError:
                 print(f"PATCH: Could not import module agents.{app_name}.agent")
            except Exception as e:
                print(f"PATCH: Error checking for root_run_config: {e}")
        
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

@app.get("/connect")
def create_call(req: Request):
    """Generate TwiML to connect a call to a Twilio Media Stream"""
    print("HANDLING CONNECT REQUEST")
    host = req.url.hostname
    scheme = req.url.scheme
    #ws_protocol = "ws" if scheme == "http" else "wss"
    ws_protocol= "wss"
    
    agent = req.query_params.get("agent")
    ws_url = f"{ws_protocol}://{host}/twilio/stream"
    if agent:
        ws_url += f"?agent={agent}"
    print("WILL STREAM TO: ", ws_url)
    stream = Stream(url=ws_url)
    connect = Connect()
    connect.append(stream)
    response = VoiceResponse()
    response.append(connect)
    
    logger.info(response)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/twilio/stream")
async def twilio_websocket(ws: WebSocket, agent: str = Query(None)):
    """Handle Twilio Media Stream WebSocket connection"""
    # This shows the raw path and query string bytes
    print(f"Full Scope Path: {ws.scope['path']}")
    print(f"Raw Query String: {ws.scope['query_string']}")
    
    # 1. Determine which agent to use
    agent_object = None
    # Explicitly get agent from query params as dependency injection might fail or be overridden
    agent_param = agent or ws.query_params.get("agent")
    agent_name = agent_param or "assistant_agent" # Default to assistant_agent if not specified

    try:
        # Dynamically import the agent module
        module = importlib.import_module(f"agents.{agent_name}.agent")
        # Assume the agent object is named 'root_agent' inside the module
        agent_object = getattr(module, "root_agent")
        logger.info(f"Loaded agent: {agent_name}")
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load agent '{agent_name}': {e}")
        # We can't really return a 404 in a websocket, but we can close with a code
        await ws.close(code=1008, reason=f"Agent '{agent_name}' not found")
        return

    await ws.accept()
    await ws.receive_json() # throw away `connected` event
    
    start_event = await ws.receive_json()
    assert start_event["event"] == "start"
    
    call_sid = start_event["start"]["callSid"]
    stream_sid = start_event["start"]["streamSid"]
    user_id = uuid4().hex # Fake user ID for the time being
    initial_message = text_to_content("Allo") # This will trigger an initial message from the agent
    live_events, live_request_queue = await start_agent_session_with_agent(user_id, call_sid, agent_object, agent_name=agent_name)
    
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
