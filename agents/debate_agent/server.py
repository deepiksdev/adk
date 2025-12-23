
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect
from .agent import create_debater, create_moderator, DebateManager

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>ADK Debate Agent</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; }
            h1 { color: #333; }
            #chat { border: 1px solid #ddd; padding: 20px; height: 500px; overflow-y: scroll; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .message { margin-bottom: 10px; padding: 10px; border-radius: 5px; }
            .moderator { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
            .debater_a { background-color: #fff3e0; border-left: 4px solid #ff9800; }
            .debater_b { background-color: #e8f5e9; border-left: 4px solid #4caf50; }
            .system { color: #888; font-style: italic; }
            button { padding: 10px 20px; font-size: 16px; background-color: #2196f3; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #1976d2; }
            input { padding: 10px; width: 60%; font-size: 16px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🤖 ADK Debate Arena</h1>
        <div>
            <input type="text" id="topicInput" value="AI will replace software engineers" placeholder="Enter debate topic...">
            <button onclick="startDebate()">Start Debate (10 Turns)</button>
        </div>
        <hr>
        <div id="chat"></div>

        <script>
            let ws;

            function startDebate() {
                const topic = document.getElementById("topicInput").value;
                const charDiv = document.getElementById("chat");
                charDiv.innerHTML = ""; // Clear previous

                if (ws) ws.close();
                
                // Connect to WebSocket
                var loc = window.location;
                var proto = loc.protocol === "https:" ? "wss:" : "ws:";
                ws = new WebSocket(proto + "//" + loc.host + "/ws");

                ws.onopen = function() {
                    ws.send(topic);
                };

                ws.onmessage = function(event) {
                    const msg = event.data;
                    const div = document.createElement("div");
                    div.className = "message";
                    
                    if (msg.startsWith("[Moderator")) {
                        div.classList.add("moderator");
                    } else if (msg.includes("Optimist")) { // Heuristic for demo
                        div.classList.add("debater_a");
                    } else if (msg.includes("Doomer")) {
                        div.classList.add("debater_b");
                    } else {
                        div.classList.add("system");
                    }
                    
                    // Format bolding
                    div.innerText = msg;
                    charDiv.appendChild(div);
                    charDiv.scrollTop = charDiv.scrollHeight;
                };
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        topic = data
        
        # Callback to send messages to WS
        async def handle_message(message: str):
            await websocket.send_text(message)

        # Setup Agents
        agent_a = create_debater("Tech Optimist", "You believe AI is a tool that amplifies human potential, not replaces it.")
        agent_b = create_debater("Tech Doomer", "You believe AI advancement is exponential and will inevitably automate all cognitive labor.")
        moderator = create_moderator()
        
        manager = DebateManager(agent_a, agent_b, moderator, on_message=handle_message)
        
        # Run Debate (Limit 10)
        await manager.run_debate(topic, max_turns=10)
        
        await websocket.send_text("--- Debate Finished ---")
        await websocket.close()
        
    except WebSocketDisconnect:
        print("Client disconnected")
