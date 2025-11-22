from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Optional, Dict, List

# Global reference to the running engine
# This will be set by heist_engine.py when it starts
engine_instance = None

def set_engine(engine):
    """Set the global engine instance"""
    global engine_instance
    engine_instance = engine

app = FastAPI(title="Heist Engine API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now to support local dev and Stellar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Heist Engine",
        "version": "1.0.0",
        "engineer": "MANE_25-10-20"
    }

@app.get("/status")
async def get_status():
    """Get comprehensive engine status"""
    if not engine_instance:
        return {"status": "offline", "message": "Engine not initialized"}
    
    # Get stats from The Hand
    hand_stats = engine_instance.hand.get_statistics() if engine_instance.hand else {}
    
    return {
        "status": "running" if engine_instance.is_running else "stopped",
        "uptime_seconds": 0,  # TODO: Add uptime tracking
        "simulation_mode": engine_instance.config.MIN_HYPE_SCORE == 70, # Rough check
        "stats": {
            "signals_detected": engine_instance.signals_detected,
            "signals_passed_audit": engine_instance.signals_passed_audit,
            "trades_executed": engine_instance.trades_executed,
            "open_positions": hand_stats.get('open_positions', 0),
            "total_pnl_usd": hand_stats.get('total_profit_usd', 0.0),
            "win_rate": hand_stats.get('win_rate', 0.0)
        }
    }

@app.get("/signals")
async def get_signals(limit: int = 20):
    """Get recent signals detected by The Ear"""
    if not engine_instance or not engine_instance.ear:
        return []
    
    # Convert signals to dict
    return [s.to_dict() for s in engine_instance.ear.get_top_signals(limit)]

@app.get("/positions")
async def get_positions():
    """Get all open and closed positions"""
    if not engine_instance or not engine_instance.hand:
        return {"open": [], "closed": []}
    
    return {
        "open": [p.to_dict() for p in engine_instance.hand.get_open_positions()],
        "closed": [p.to_dict() for p in engine_instance.hand.closed_positions[-20:]] # Last 20 closed
    }

@app.get("/wallet")
async def get_wallet():
    """Get wallet status and balance"""
    if not engine_instance or not engine_instance.hand:
        return {"address": "Not Configured", "balance_eth": 0.0, "balance_sol": 0.0}
    
    # In a real scenario, we would fetch balance from RPC
    # For now, we return the configured address and a simulated balance
    
    return {
        "address": engine_instance.hand.config.WALLET_ADDRESS or "0x... (Not Set)",
        "balance_eth": 1.5, # Simulated balance
        "balance_sol": 15.0, # Simulated balance
        "is_dry_run": engine_instance.hand.config.DRY_RUN_MODE
    }

@app.post("/control/stop")
async def stop_engine():
    """Stop the engine"""
    if not engine_instance:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    await engine_instance.shutdown()
    return {"message": "Engine shutdown initiated"}

if __name__ == "__main__":
    # Standalone run (mostly for testing API without engine)
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

