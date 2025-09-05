#!/usr/bin/env python3
"""
Arduino Web IDE - Production Server
Optimized deployment configuration for production environment
"""

import os
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import aiofiles

# Import the main app
from main import app

# Override static file configuration for production
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# Ensure static directory exists
if not STATIC_DIR.exists():
    raise FileNotFoundError(f"Static directory not found: {STATIC_DIR}")

# Clear existing static mount if any and remount
try:
    # Remove existing static mount
    for route in app.routes:
        if hasattr(route, 'path') and route.path == '/static':
            app.routes.remove(route)
            break
except:
    pass

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Override root route to ensure it works in production
@app.get("/")
async def production_root():
    """Production root route that ensures HTML is served correctly"""
    try:
        html_file = STATIC_DIR / "index.html"
        if html_file.exists():
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content, status_code=200)
        else:
            return HTMLResponse(
                content="<h1>Arduino Web IDE</h1><p>Static files not found. Please check deployment.</p>",
                status_code=500
            )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Arduino Web IDE</h1><p>Error loading application: {str(e)}</p>",
            status_code=500
        )

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Arduino Web IDE"}

if __name__ == "__main__":
    print("Starting Arduino Web IDE Production Server...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Static directory: {STATIC_DIR}")
    print(f"Static directory exists: {STATIC_DIR.exists()}")
    
    # List static files for debugging
    if STATIC_DIR.exists():
        print("Static files:")
        for file in STATIC_DIR.iterdir():
            print(f"  - {file.name}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )