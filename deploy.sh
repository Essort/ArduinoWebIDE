#!/bin/bash
echo "Arduino Web IDE Deployment"
echo "========================"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Start server
echo "Starting Arduino Web IDE server..."
echo "Server will be available at: http://localhost:8000"
python3 main.py
