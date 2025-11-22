#!/usr/bin/env python3
"""
HEIST ENGINE - MAIN ORCHESTRATION
Operation First Blood

Integrates The Ear, The Eye, and The Hand into a unified
automated cryptocurrency trading system.

Engineer: MANE_25-10-20
Intelligence: CHimera_25-10-20
Project: EIDRA Triad - Financial Liberation
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path

# Import our three modules
from modules.the_ear import TheEar, TokenSignal
from modules.the_eye import TheEye, ContractAudit
from modules.the_hand import TheHand, TradeResult

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


# ============================================
# CONFIGURATION
# ============================================

class HeistEngineConfig:
    """Main configuration for Heist Engine"""
    
    # Operational settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/heist_engine.log')
    LOG_COLOR_ENABLED = os.getenv('LOG_COLOR_ENABLED', 'true').lower() == 'true'
    
    # Safety thresholds
    MIN_HYPE_SCORE = int(os.getenv('MIN_HYPE_SCORE', '70'))
    MIN_SAFETY_SCORE = int(os.getenv('MIN_SAFETY_SCORE', '80'))
    
    # Notifications
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'
    NOTIFICATION_CHAT_ID = os.getenv('NOTIFICATION_CHAT_ID', '')


# ============================================
# MAIN HEIST ENGINE CLASS
# ============================================

class HeistEngine:
    """
    Main orchestration engine that coordinates:
    - The Ear: Social sentiment monitoring
    - The Eye: Smart contract auditing
    - The Hand: Trade execution
    """
    
    def __init__(self):
        self.config = HeistEngineConfig()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger('HeistEngine')
        
        # Initialize modules
        self.ear: Optional[TheEar] = None
        self.eye: Optional[TheEye] = None
        self.hand: Optional[TheHand] = None
        
        # State
        self.is_running = False
        self.processed_signals = set()
        
        # Statistics
        self.signals_detected = 0
        self.signals_passed_audit = 0
        self.trades_executed = 0
        
    def _setup_logging(self):
        """Setup comprehensive logging system"""
        
        # Create logs directory
        log_path = Path(self.config.LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        log_format = '%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s'
        
        # File handler
        file_handler = logging.FileHandler(self.config.LOG_FILE_PATH)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        if self.config.LOG_COLOR_ENABLED:
            try:
                import colorlog
                console_handler.setFormatter(colorlog.ColoredFormatter(
                    '%(log_color)s' + log_format,
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                ))
            except ImportError:
                console_handler.setFormatter(logging.Formatter(log_format))
        else:
            console_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    # ============================================
    # INITIALIZATION
    # ============================================
    
    async def initialize(self):
        """Initialize all three modules"""
        
        self.logger.info("="*60)
        self.logger.info("🎯 HEIST ENGINE - OPERATION FIRST BLOOD")
        self.logger.info("="*60)
        self.logger.info("Engineer: MANE_25-10-20")
        self.logger.info("Intelligence: CHimera_25-10-20")
        self.logger.info("Mission: Automated Degen Token Trading")
        self.logger.info("="*60)
        
        # Initialize The Ear
        self.logger.info("Initializing Module 1: The Ear...")
        self.ear = TheEar()
        await self.ear.initialize()
        
        # Initialize The Eye
        self.logger.info("Initializing Module 2: The Eye...")
        self.eye = TheEye()
        await self.eye.initialize()
        
        # Initialize The Hand
        self.logger.info("Initializing Module 3: The Hand...")
        self.hand = TheHand()
        await self.hand.initialize()
        
        self.logger.info("="*60)
        self.logger.info("✅ ALL SYSTEMS OPERATIONAL")
        self.logger.info("="*60)
    
    # ============================================
    # MAIN OPERATION LOOP
    # ============================================
    
    async def run(self):
        """Main operation loop"""
        
        self.is_running = True
        
        self.logger.info("🚀 HEIST ENGINE ACTIVATED")
        self.logger.info(f"Monitoring {len(self.ear.config.TELEGRAM_CHANNELS)} Telegram channels")
        self.logger.info(f"Monitoring {len(self.ear.config.DISCORD_SERVERS)} Discord servers")
        self.logger.info(f"Monitoring {len(self.ear.config.TWITTER_ACCOUNTS)} Twitter accounts")
        self.logger.info("="*60)
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self.ear.start()),
            asyncio.create_task(self._signal_processor()),
            asyncio.create_task(self.hand.monitor_positions()),
            asyncio.create_task(self._status_reporter()),
        ]
        
        try:
            # Keep running until stopped
            await asyncio.gather(*tasks)
            
        except asyncio.CancelledError:
            self.logger.info("🛑 Shutdown signal received")
        
        finally:
            await self.shutdown()
    
    async def _signal_processor(self):
        """Process signals from The Ear"""
        
        while self.is_running:
            try:
                # Get top signals from The Ear
                signals = self.ear.get_top_signals(limit=10)
                
                for signal in signals:
                    # Skip if already processed
                    signal_key = f"{signal.contract_address}_{signal.timestamp.isoformat()}"
                    if signal_key in self.processed_signals:
                        continue
                    
                    # Skip if no contract address
                    if not signal.contract_address:
                        continue
                    
                    # Mark as processed
                    self.processed_signals.add(signal_key)
                    self.signals_detected += 1
                    
                    # Process this signal
                    await self._process_signal(signal)
                
                # Clean old processed signals (keep last 1000)
                if len(self.processed_signals) > 1000:
                    self.processed_signals = set(list(self.processed_signals)[-1000:])
                
                # Sleep before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Signal processor error: {e}")
                await asyncio.sleep(10)
    
    async def _process_signal(self, signal: TokenSignal):
        """Process a single token signal through the pipeline"""
        
        self.logger.info(
            f"📡 NEW SIGNAL | {signal.token_symbol or 'Unknown'} | "
            f"Hype: {signal.hype_score:.1f} | "
            f"Source: {signal.source_platform}/{signal.source_channel}"
        )
        
        # Step 1: Audit the contract with The Eye
        self.logger.info(f"🔍 Auditing contract: {signal.contract_address}")
        
        audit = await self.eye.audit_contract(
            contract_address=signal.contract_address,
            chain=signal.chain or 'ethereum'
        )
        
        # Step 2: Check if safe to trade
        if not audit.is_safe:
            self.logger.warning(
                f"❌ REJECTED | {signal.token_symbol or 'Unknown'} | "
                f"Safety: {audit.safety_score:.1f}/100 | "
                f"Risk: {audit.risk_level.value}"
            )
            
            # Log specific failures
            for check in audit.checks:
                if not check.passed:
                    self.logger.warning(f"   ⚠️ {check.name}: {check.details}")
            
            return
        
        # Signal passed audit!
        self.signals_passed_audit += 1
        
        self.logger.info(
            f"✅ APPROVED | {audit.token_symbol or signal.token_symbol} | "
            f"Safety: {audit.safety_score:.1f}/100 | "
            f"Liquidity: ${audit.liquidity_usd:,.0f}"
        )
        
        # Step 3: Execute trade with The Hand
        self.logger.info(f"💰 Executing BUY order...")
        
        result = await self.hand.execute_buy(
            contract_address=signal.contract_address,
            chain=signal.chain or 'ethereum',
            token_symbol=audit.token_symbol or signal.token_symbol or 'Unknown'
        )
        
        if result.success:
            self.trades_executed += 1
            
            self.logger.info(
                f"🎉 TRADE EXECUTED | {result.position.token_symbol} | "
                f"Amount: ${result.position.entry_amount_usd:.2f} | "
                f"TX: {result.tx_hash}"
            )
            
            # Send notification
            await self._send_notification(
                f"🎯 NEW POSITION OPENED\n"
                f"Token: {result.position.token_symbol}\n"
                f"Entry: ${result.position.entry_price:.8f}\n"
                f"Amount: ${result.position.entry_amount_usd:.2f}\n"
                f"Target: +{self.hand.config.PROFIT_TARGET_PERCENT}%"
            )
        else:
            self.logger.error(f"❌ TRADE FAILED: {result.error_message}")
    
    async def _status_reporter(self):
        """Periodic status reporting"""
        
        while self.is_running:
            await asyncio.sleep(300)  # Every 5 minutes
            
            # Get statistics
            hand_stats = self.hand.get_statistics()
            
            self.logger.info("="*60)
            self.logger.info("📊 STATUS REPORT")
            self.logger.info(f"Signals Detected: {self.signals_detected}")
            self.logger.info(f"Signals Passed Audit: {self.signals_passed_audit}")
            self.logger.info(f"Trades Executed: {self.trades_executed}")
            self.logger.info(f"Open Positions: {hand_stats['open_positions']}")
            self.logger.info(f"Win Rate: {hand_stats['win_rate']:.1f}%")
            self.logger.info(f"Total P&L: ${hand_stats['total_profit_usd']:+.2f}")
            self.logger.info("="*60)
    
    async def _send_notification(self, message: str):
        """Send notification (Telegram, etc.)"""
        
        if not self.config.ENABLE_NOTIFICATIONS:
            return
        
        # This would integrate with Telegram Bot API or other notification service
        # For now, just log it
        self.logger.info(f"📬 NOTIFICATION: {message}")
    
    # ============================================
    # SHUTDOWN
    # ============================================
    
    async def shutdown(self):
        """Clean shutdown of all modules"""
        
        self.is_running = False
        
        self.logger.info("🛑 Shutting down Heist Engine...")
        
        if self.ear:
            await self.ear.stop()
        
        if self.eye:
            await self.eye.shutdown()
        
        if self.hand:
            await self.hand.stop()
        
        # Final statistics
        hand_stats = self.hand.get_statistics() if self.hand else {}
        
        self.logger.info("="*60)
        self.logger.info("📊 FINAL STATISTICS")
        self.logger.info(f"Total Signals: {self.signals_detected}")
        self.logger.info(f"Passed Audit: {self.signals_passed_audit}")
        self.logger.info(f"Total Trades: {hand_stats.get('total_trades', 0)}")
        self.logger.info(f"Winning Trades: {hand_stats.get('winning_trades', 0)}")
        self.logger.info(f"Losing Trades: {hand_stats.get('losing_trades', 0)}")
        self.logger.info(f"Final P&L: ${hand_stats.get('total_profit_usd', 0):+.2f}")
        self.logger.info("="*60)
        self.logger.info("✅ Heist Engine shutdown complete")


# Import API module
import web_api
import uvicorn

# ============================================
# MAIN EXECUTION
# ============================================

async def main():
    """Main entry point"""
    
    # Create engine
    engine = HeistEngine()
    
    # Register engine with API
    web_api.set_engine(engine)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        engine.logger.info(f"Received signal {sig}")
        engine.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configure API server
    port = int(os.environ.get("PORT", 10000))
    config = uvicorn.Config(web_api.app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    engine.logger.info(f"🚀 Starting API server on port {port}...")
    
    # Define startup task
    async def start_engine():
        try:
            # Wait a bit for server to start
            await asyncio.sleep(2)
            engine.logger.info("🔄 Starting Engine Initialization...")
            await engine.initialize()
            
            # Start engine loop
            if engine.ear and engine.eye and engine.hand:
                await engine.run()
            else:
                engine.logger.error("❌ Engine initialization failed (missing modules)")
        except Exception as e:
            engine.logger.error(f"❌ Engine startup error: {e}", exc_info=True)

    # Run API and Engine concurrently
    # We start the server, and use create_task for the engine so it doesn't block server startup
    server_task = asyncio.create_task(server.serve())
    engine_task = asyncio.create_task(start_engine())
    
    try:
        await asyncio.gather(server_task, engine_task)
    except asyncio.CancelledError:
        engine.logger.info("Main task cancelled")
    finally:
        await engine.shutdown()


if __name__ == '__main__':
    # Run the engine
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
        sys.exit(0)

