import os
import threading
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
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
    dashboard_path = frontend_path / "dashboard.html"
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
