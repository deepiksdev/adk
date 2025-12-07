
import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from twilio_voice_agent.main import api as twilio_app

import sys
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def create_app():
    logger.info("Starting application creation...")
    try:
        # Load the standard ADK app
        logger.info("Loading ADK app...")
        adk_app = get_fast_api_app(agents_dir=".", web=True)
        logger.info("ADK app loaded successfully.")
        
        # Merge Twilio routes
        logger.info("Merging Twilio routes...")
        # safer way to merge routes from another FastAPI app
        adk_app.include_router(twilio_app.router)
        logger.info("Twilio routes merged.")

        return adk_app
    except Exception as e:
        logger.error(f"Failed to create app: {e}", exc_info=True)
        raise

try:
    app = create_app()
except Exception as e:
    logger.critical(f"Application startup failed: {e}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
