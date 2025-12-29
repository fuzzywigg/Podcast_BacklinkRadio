import os
import threading
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, Header, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from hive.queen.orchestrator import QueenOrchestrator
# Global Queen instance
queen: QueenOrchestrator = None
queen_thread: threading.Thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI app.
    Starts the Queen in a background thread on startup.
    Stops the Queen on shutdown.
    """
    global queen, queen_thread
    
    # Initialize Queen
    print("Initializing Queen Orchestrator...")
    queen = QueenOrchestrator()
    
    # Start Queen loop in a separate thread
    print("Starting Queen background thread...")
    queen_thread = threading.Thread(target=queen.run, daemon=True)
    queen_thread.start()
    
    yield
    
    # Shutdown
    print("Shutting down Queen...")
    if queen:
        queen.stop()
    if queen_thread:
        queen_thread.join(timeout=5)
    print("Queen shutdown complete.")

app = FastAPI(
    title="Backlink Broadcast Hive",
    description="Orchestrator Service for AI Radio Station",
    version="1.1.0",
    lifespan=lifespan
)

@app.get("/")
async def serve_dashboard():
    """Serve the dashboard."""
    # Serve index.html or dashboard.html from frontend
    frontend_path = Path(__file__).parent.parent / "frontend"
    index_path = frontend_path / "index.html"
    dashboard_path = frontend_path / "dashboard.html"
    
    if index_path.exists():
        return FileResponse(index_path)
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return {"status": "ok", "service": "Backlink Hive (No Frontend Found)"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    if not queen:
        raise HTTPException(status_code=503, detail="Queen not initialized")
    return {"status": "ok", "service": "Backlink Hive"}

# Mount static files (if any images/css exist in frontend)
try:
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    Real-time audio streaming endpoint for Owl Voice.
    Proxies audio bidirectional between Client <-> Hive <-> Gemini Live API.
    """
    await websocket.accept()
    print("Client connected to Voice Stream.")
    
    # Check if Queen has a client (it might not during startup race conditions)
    if not queen or not queen.gemini_client:
        await websocket.close(code=1011, reason="Hive Intelligence Layer not ready.")
        return

    import json
    
    try:
        # Connect to Gemini Live API
        async with queen.gemini_client.live_connect() as gemini_ws:
            print("Connected to Gemini Live API. Bridge established.")
            
            # 1. Client -> Gemini (Audio Input)
            async def client_to_gemini():
                try:
                    while True:
                        # Receive raw PCM bytes from browser
                        data = await websocket.receive_bytes()
                        
                        # Wrap in Gemini Bidi Protocol
                        # Input Audio must be base64 encoded strings in a 'realtime_input' message
                        # BUT the cookbook uses 'realtime_input' with 'media_chunks'
                        # Reference: "realtime_input": {"media_chunks": [{"mime_type": "audio/pcm", "data": <base64>}]}
                        # Using 'websockets' library we can send bytes directly? 
                        # No, Bidi API expects JSON messages for control or data.
                        
                        import base64
                        b64_data = base64.b64encode(data).decode("utf-8")
                        
                        msg = {
                            "realtime_input": {
                                "media_chunks": [
                                    {
                                        "mime_type": "audio/pcm",
                                        "data": b64_data
                                    }
                                ]
                            }
                        }
                        await gemini_ws.send(json.dumps(msg))
                except Exception as e:
                    print(f"Upstream Error: {e}")

            # 2. Gemini -> Client (Audio Output)
            async def gemini_to_client():
                try:
                    async for raw_msg in gemini_ws:
                        # Parse Gemini Response
                        # Expected: "server_content": {"model_turn": {"parts": [{"inline_data": {"mime_type": "audio/pcm;rate=24000", "data": <base64>}}]}}
                        response = json.loads(raw_msg)
                        
                        server_content = response.get("server_content")
                        if server_content:
                            model_turn = server_content.get("model_turn")
                            if model_turn:
                                for part in model_turn.get("parts", []):
                                    inline_data = part.get("inline_data")
                                    if inline_data and inline_data.get("mime_type").startswith("audio/"):
                                        # Decode base64 and send raw bytes to client
                                        audio_bytes = base64.b64decode(inline_data["data"])
                                        await websocket.send_bytes(audio_bytes)
                                        
                        # Also handle "turn_complete" or interruptions if needed
                        
                except Exception as e:
                    print(f"Downstream Error: {e}")

            # Run both bridges concurrently
            await asyncio.gather(client_to_gemini(), gemini_to_client())
            
    except WebSocketDisconnect:
        print("Client disconnected from Voice Stream.")
    except Exception as e:
        print(f"WebSocket/Bridge Error: {e}")
        try:
            await websocket.close()
        except:
            pass

@app.get("/status")
async def get_status():
    """Get detailed hive status."""
    if not queen:
        raise HTTPException(status_code=503, detail="Queen not initialized")
    return queen.heartbeat()

@app.post("/trigger/{event_type}")
async def trigger_event(event_type: str, payload: Dict[str, Any] = {}):
    """Manually trigger a hive event."""
    if not queen:
        raise HTTPException(status_code=503, detail="Queen not initialized")
    
    results = queen.trigger_event(event_type, payload)
    return {"triggered": event_type, "results": results}

@app.get("/intel")
async def get_intel():
    """Get the hive's shared intelligence (Now Playing, Treasury)."""
    if not queen:
        raise HTTPException(status_code=503, detail="Queen not initialized")
    
    # Simple direct read of intel.json via queen's helper if possible
    # Queen doesn't expose read_intel directly public, but we can access it via honeycomb path
    # Or just add a method to Queen. 
    # Let's effectively replicate Queen's read logic here for speed or use a protected method.
    return queen._read_json_cached("intel.json")

@app.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Handle incoming Stripe webhooks.
    """
    if not queen:
        raise HTTPException(status_code=503, detail="Queen not initialized")
    
    raw_body = await request.body()
    
    # Spawn Commerce Bee directly to handle the webhook
    task = {
        "payload": {
            "action": "handle_webhook",
            "raw_body": raw_body.decode("utf-8"),
            "sig_header": stripe_signature
        }
    }
    
    # We use spawn_bee directly instead of trigger_event to target CommerceBee specifically
    result = queen.spawn_bee("commerce_bee", task)
    
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
