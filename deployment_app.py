
import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from twilio_voice_agent.main import api as twilio_app

def create_app():
    # Load the standard ADK app
    # get_fast_api_app typically expects the directory causing the agent loading
    # We assume 'twilio_voice_agent' is the agent directory based on previous context
    adk_app = get_fast_api_app(agents_dir=".", web=True)
    
    # Mount the Twilio app under the root as well, or we can just merge the routes.
    # Since ADK app might have a catch-all or specific routes, mounting is cleaner 
    # if we want to separate them, but the user asked to make the backend available.
    # The ADK app usually serves the UI at /.
    # The Twilio app serves /connect and /twilio/stream.
    
    # Option 1: Mount. This puts twilio under a subpath like /voice
    # adk_app.mount("/voice", twilio_app)
    
    # Option 2: Include router. This merges them at root level if possible.
    # FastAPI include_router would work if twilio_app was a router. 
    # Since twilio_app is a FastAPI app, we can use it as a sub-application.
    # However, to keep /connect at the root (as external webhooks might expect),
    # we might need to mount it at root or copy routes.
    
    # Let's inspect twilio_app. 
    # It has @api.post("/connect") and @api.websocket("/twilio/stream")
    # We want these accessible at the top level alongside ADK routes.
    
    # Let's try to add the routes from twilio_app to adk_app
    for route in twilio_app.routes:
        adk_app.router.routes.append(route)
        
    return adk_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
