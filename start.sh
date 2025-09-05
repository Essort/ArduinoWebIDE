#!/bin/bash

# Arduino Web IDE - Deployment Startup Script
echo "Arduino Web IDE - Starting Deployment"
echo "====================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -q fastapi uvicorn aiofiles requests

# Start the simple server (more reliable for deployment)
echo "Starting Arduino Web IDE server..."
echo "Server will be available at the deployment URL"
python3 simple_server.py