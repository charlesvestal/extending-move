#!/usr/bin/env python3
"""
FastAPI-based Move webserver - modernized version of move-webserver.py
"""
import os
import signal
import sys
import atexit
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.routers import refresh, reverse, restore, chord
# Temporarily disabled due to import issues - will fix these next
# from app.routers import slice_router  # Now enabled
# from app.routers import drum_rack  # Now enabled
# from app.routers import synth_preset  # Now enabled

# Define the PID file location
PID_FILE = os.path.expanduser('~/extending-move/move-webserver.pid')

def write_pid():
    """Write the current process PID to the PID_FILE."""
    pid = os.getpid()
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(pid))
        print(f"PID {pid} written to {PID_FILE}")
    except Exception as e:
        print(f"Error writing PID file: {e}")

def remove_pid():
    """Remove the PID file."""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print(f"PID file {PID_FILE} removed.")
    except Exception as e:
        print(f"Error removing PID file: {e}")

def handle_exit(signum, frame):
    """Handle termination signals gracefully."""
    print(f"Received signal {signum}, exiting gracefully.")
    sys.exit(0)

# Create FastAPI app
app = FastAPI(
    title="Move Extended",
    description="Audio processing tools for Ableton Move",
    version="2.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers WITHOUT /api prefix to match frontend expectations
app.include_router(refresh.router)
app.include_router(reverse.router)
app.include_router(restore.router)
app.include_router(chord.router)
# Temporarily disabled - will re-enable after fixing import issues
# app.include_router(slice_router.router)
# app.include_router(drum_rack.router)
# app.include_router(synth_preset.router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/samples/{path:path}")
async def serve_samples(path: str):
    """Handle requests for sample files."""
    from urllib.parse import unquote
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    
    # URL decode the path
    relative_path = unquote(path)
    
    # Construct the full path to the samples directory
    base_samples_dir = '/data/UserData/UserLibrary/Samples/Preset Samples'
    full_path = os.path.join(base_samples_dir, relative_path)
    
    # Security check: ensure the requested path is within the samples directory
    real_path = os.path.realpath(full_path)
    if not real_path.startswith(os.path.realpath(base_samples_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        real_path,
        media_type='audio/wav',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    write_pid()
    atexit.register(remove_pid)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)
    
    print("Starting FastAPI webserver")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=909,
        reload=False,
        access_log=True
    )
