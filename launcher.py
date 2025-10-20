"""
HEIST ENGINE - Launcher
Runs both the web API (for Render port requirement) and the heist engine
"""

import multiprocessing
import os
import sys

def run_web_api():
    """Run the FastAPI web server"""
    import uvicorn
    from web_api import app
    
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def run_heist_engine():
    """Run the main heist engine"""
    import subprocess
    subprocess.run([sys.executable, "heist_engine.py"])

if __name__ == "__main__":
    print("🚀 HEIST ENGINE - DUAL LAUNCH")
    print("=" * 60)
    print("Starting Web API and Heist Engine in parallel...")
    print("=" * 60)
    
    # Create processes
    web_process = multiprocessing.Process(target=run_web_api, name="WebAPI")
    engine_process = multiprocessing.Process(target=run_heist_engine, name="HeistEngine")
    
    # Start both
    web_process.start()
    engine_process.start()
    
    print(f"✅ Web API started (PID: {web_process.pid})")
    print(f"✅ Heist Engine started (PID: {engine_process.pid})")
    
    # Wait for both to complete
    web_process.join()
    engine_process.join()

