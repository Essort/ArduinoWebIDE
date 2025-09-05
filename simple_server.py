#!/usr/bin/env python3
"""
Arduino Web IDE - Simple Production Server
Minimal server configuration for reliable deployment
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

# Create FastAPI app
app = FastAPI(title="Arduino Web IDE", description="Web-based Arduino IDE with AI integration")

# Project directories
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
for dir_name in ["sketches", "templates", "libraries", "uploads"]:
    (BASE_DIR / dir_name).mkdir(exist_ok=True)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Root route
@app.get("/")
async def root():
    """Serve the main Arduino IDE interface"""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file, media_type="text/html")
    else:
        return HTMLResponse(
            content="""<!DOCTYPE html>
<html>
<head><title>Arduino Web IDE</title></head>
<body>
<h1>Arduino Web IDE</h1>
<p>Error: index.html not found in static directory.</p>
<p>Static directory: {}</p>
<p>Exists: {}</p>
</body>
</html>""".format(STATIC_DIR, STATIC_DIR.exists()),
            status_code=500
        )

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "Arduino Web IDE"}

# API endpoints
@app.get("/api/boards")
async def get_boards():
    """Get list of supported Arduino boards"""
    boards = {
        "arduino:avr:nano": "Arduino Nano",
        "arduino:avr:uno": "Arduino Uno", 
        "arduino:avr:mega": "Arduino Mega 2560",
        "esp32:esp32:esp32": "ESP32 Dev Module",
        "esp8266:esp8266:nodemcuv2": "ESP8266 NodeMCU"
    }
    return {"boards": boards}

@app.get("/api/sketches")
async def get_sketches():
    """Get list of Arduino sketches"""
    sketches_dir = BASE_DIR / "sketches"
    sketches = []
    if sketches_dir.exists():
        for sketch_file in sketches_dir.glob("*.ino"):
            sketches.append({
                "name": sketch_file.name,
                "path": str(sketch_file),
                "modified": os.path.getmtime(sketch_file)
            })
    return {"sketches": sketches}

@app.get("/api/templates")
async def get_templates():
    """Get list of Arduino sketch templates"""
    templates_dir = BASE_DIR / "templates"
    templates = []
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.ino"):
            templates.append({
                "name": template_file.name,
                "path": str(template_file)
            })
    return {"templates": templates}

if __name__ == "__main__":
    print("Starting Simple Arduino Web IDE Server...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Static directory: {STATIC_DIR}")
    print(f"Static files exist: {STATIC_DIR.exists()}")
    
    if STATIC_DIR.exists():
        print("Static files:")
        for file in STATIC_DIR.iterdir():
            print(f"  - {file.name}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )