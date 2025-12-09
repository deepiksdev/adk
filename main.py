import logging
import os
from google.adk.cli.fast_api import get_fast_api_app

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Initialize the standard ADK FastAPI app
# agents_dir="." allows it to find agents in the current directory
app = get_fast_api_app(
    agents_dir=".",
    web=True,  # Enable the Web UI
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080))
)

@app.get("/hello")
def hello():
    """Simple Hello World endpoint for testing custom routes."""
    return {"message": "Hello World"}
