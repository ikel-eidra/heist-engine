#!/bin/bash
# HEIST ENGINE - Launcher Script
# Runs both the web API (for Render) and the heist engine (background)

echo "🚀 Starting Heist Engine..."

# Start the web API in the background
python3 web_api.py &
WEB_PID=$!

echo "✅ Web API started (PID: $WEB_PID)"

# Start the heist engine in the foreground
python3 heist_engine.py

# If heist engine exits, kill the web API too
kill $WEB_PID

