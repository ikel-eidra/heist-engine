#!/usr/bin/env python3
"""
HEIST ENGINE - MODULE 3: THE HAND
High-Speed Trade Execution Engine

Purpose: Automated buy/sell execution on DEXs with profit-taking,
         stop-loss, and position management.

Engineer: MANE_25-10-20
Project: Operation First Blood
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
import json

# External imports
try:
    from web3 import Web3
    from web3.contract import Contract
    from eth_account import Account
except ImportError:
    Web3 = None
    Account = None

try:
    from solana.rpc.async_api import AsyncClient as SolanaClient
    from solana.transaction import Transaction
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
except ImportError:
    SolanaClient = None

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


# ============================================
# CONFIGURATION
# ============================================

class HandConfig:
    """Configuration for The Hand module"""
    
    # RPC endpoints
    ETHEREUM_RPC_URL = os.getenv('ETHEREUM_RPC_URL', 'https://eth.llamarpc.com')
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    
    # Wallet credentials (KEEP THESE SECRET!)
    ETH_PRIVATE_KEY = os.getenv('ETH_PRIVATE_KEY', '')
    SOL_PRIVATE_KEY = os.getenv('SOL_PRIVATE_KEY', '')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', '')
    
    # Trading parameters
    TRADE_AMOUNT_USD = float(os.getenv('TRADE_AMOUNT_USD', '10'))
    PROFIT_TARGET_PERCENT = float(os.getenv('PROFIT_TARGET_PERCENT', '500'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '50'))
    TRAILING_STOP_PERCENT = float(os.getenv('TRAILING_STOP_PERCENT', '20'))
    MAX_SLIPPAGE_PERCENT = float(os.getenv('MAX_SLIPPAGE_PERCENT', '5'))
    MAX_HOLD_TIME_HOURS = int(os.getenv('MAX_HOLD_TIME_HOURS', '24'))
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))
    
    # Gas settings
    GAS_PRICE_MULTIPLIER = float(os.getenv('GAS_PRICE_MULTIPLIER', '1.2'))
    TX_TIMEOUT_SECONDS = int(os.getenv('TX_TIMEOUT_SECONDS', '60'))
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    
    # Safety
    DRY_RUN_MODE = os.getenv('DRY_RUN_MODE', 'true').lower() == 'true'
    
    # DEX Router addresses
    UNISWAP_V2_ROUTER = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    UNISWAP_V3_ROUTER = '0xE592427A0AEce92De3Edee1F18E0157C05861564'
    RAYDIUM_PROGRAM_ID = '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'
    JUPITER_AGGREGATOR = 'JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB'


# ============================================
# DATA STRUCTURES
# ============================================

class TradeStatus(Enum):
    """Trade execution status"""
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExitReason(Enum):
    """Reason for closing a position"""
    PROFIT_TARGET = "PROFIT_TARGET"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    TIME_LIMIT = "TIME_LIMIT"
    MANUAL = "MANUAL"
    EMERGENCY = "EMERGENCY"


@dataclass
class Position:
    """Represents an open trading position"""
    position_id: str
    contract_address: str
    chain: str
    token_symbol: str
    
    # Entry details
    entry_time: datetime = field(default_factory=datetime.now)
    entry_price: float = 0.0
    entry_amount_usd: float = 0.0
    entry_amount_tokens: float = 0.0
    entry_tx_hash: Optional[str] = None
    
    # Current state
    current_price: float = 0.0
    current_value_usd: float = 0.0
    peak_price: float = 0.0
    
    # Exit details
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_amount_usd: Optional[float] = None
    exit_tx_hash: Optional[str] = None
    exit_reason: Optional[ExitReason] = None
    
    # Performance
    profit_loss_usd: float = 0.0
    profit_loss_percent: float = 0.0
    
    # Status
    status: TradeStatus = TradeStatus.PENDING
    
    def update_current_price(self, price: float):
        """Update current price and metrics"""
        self.current_price = price
        self.current_value_usd = self.entry_amount_tokens * price
        
        # Update peak price
        if price > self.peak_price:
            self.peak_price = price
        
        # Calculate P&L
        self.profit_loss_usd = self.current_value_usd - self.entry_amount_usd
        self.profit_loss_percent = (
            (self.current_value_usd / self.entry_amount_usd - 1) * 100
            if self.entry_amount_usd > 0 else 0
        )
    
    def should_take_profit(self, target_percent: float) -> bool:
        """Check if profit target is reached"""
        return self.profit_loss_percent >= target_percent
    
    def should_stop_loss(self, stop_percent: float) -> bool:
        """Check if stop loss is triggered"""
        return self.profit_loss_percent <= -stop_percent
    
    def should_trailing_stop(self, trailing_percent: float) -> bool:
        """Check if trailing stop is triggered"""
        if self.peak_price <= 0:
            return False
        
        drop_from_peak = ((self.peak_price - self.current_price) / self.peak_price) * 100
        return drop_from_peak >= trailing_percent
    
    def should_time_exit(self, max_hours: int) -> bool:
        """Check if maximum hold time is exceeded"""
        if max_hours <= 0:
            return False
        
        hold_time = datetime.now() - self.entry_time
        return hold_time > timedelta(hours=max_hours)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'position_id': self.position_id,
            'contract_address': self.contract_address,
            'chain': self.chain,
            'token_symbol': self.token_symbol,
            'entry_time': self.entry_time.isoformat(),
            'entry_price': self.entry_price,
            'entry_amount_usd': self.entry_amount_usd,
            'entry_amount_tokens': self.entry_amount_tokens,
            'current_price': self.current_price,
            'current_value_usd': self.current_value_usd,
            'profit_loss_usd': self.profit_loss_usd,
            'profit_loss_percent': self.profit_loss_percent,
            'status': self.status.value,
            'exit_reason': self.exit_reason.value if self.exit_reason else None,
        }


@dataclass
class TradeResult:
    """Result of a trade execution"""
    success: bool
    position: Optional[Position] = None
    error_message: Optional[str] = None
    tx_hash: Optional[str] = None


# ============================================
# THE HAND - MAIN CLASS
# ============================================

class TheHand:
    """
    The Hand: High-Speed Trade Execution Engine
    
    Executes buy/sell orders on DEXs with automated profit-taking,
    stop-loss, and position management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('TheHand')
        self.config = HandConfig()
        
        # Blockchain clients
        self.eth_web3: Optional[Web3] = None
        self.eth_account: Optional[Account] = None
        self.solana_client: Optional[SolanaClient] = None
        self.solana_keypair: Optional[Keypair] = None
        
        # Position tracking
        self.open_positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        
        # State
        self.is_running = False
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit_usd = 0.0
        
    # ============================================
    # INITIALIZATION
    # ============================================
    
    async def initialize(self):
        """Initialize blockchain connections and wallets"""
        self.logger.info("✋ Initializing The Hand...")
        
        if self.config.DRY_RUN_MODE:
            self.logger.warning("⚠️ DRY RUN MODE ENABLED - No real trades will be executed")
        
        # Initialize Ethereum
        await self._init_ethereum()
        
        # Initialize Solana
        await self._init_solana()
        
        self.logger.info("✅ The Hand is ready to trade")
    
    async def _init_ethereum(self):
        """Initialize Ethereum wallet and connection"""
        if not Web3 or not Account:
            self.logger.warning("⚠️ web3.py not installed, Ethereum trading disabled")
            return
        
        try:
            self.eth_web3 = Web3(Web3.HTTPProvider(self.config.ETHEREUM_RPC_URL))
            
            if not self.eth_web3.is_connected():
                self.logger.error("❌ Failed to connect to Ethereum")
                return
            
            # Load wallet
            if self.config.ETH_PRIVATE_KEY:
                self.eth_account = Account.from_key(self.config.ETH_PRIVATE_KEY)
                balance = self.eth_web3.eth.get_balance(self.eth_account.address)
                balance_eth = self.eth_web3.from_wei(balance, 'ether')
                
                self.logger.info(
                    f"✅ Ethereum wallet loaded: {self.eth_account.address[:10]}... "
                    f"Balance: {balance_eth:.4f} ETH"
                )
            else:
                self.logger.warning("⚠️ No Ethereum private key configured")
                
        except Exception as e:
            self.logger.error(f"❌ Ethereum initialization failed: {e}")
    
    async def _init_solana(self):
        """Initialize Solana wallet and connection"""
        if not SolanaClient:
            self.logger.warning("⚠️ solana-py not installed, Solana trading disabled")
            return
        
        try:
            self.solana_client = SolanaClient(self.config.SOLANA_RPC_URL)
            
            # Load wallet
            if self.config.SOL_PRIVATE_KEY:
                # Note: This is simplified - actual implementation needs proper key handling
                self.logger.info("✅ Solana wallet configured")
            else:
                self.logger.warning("⚠️ No Solana private key configured")
                
        except Exception as e:
            self.logger.error(f"❌ Solana initialization failed: {e}")
    
    # ============================================
    # TRADE EXECUTION
    # ============================================
    
    async def execute_buy(
        self,
        contract_address: str,
        chain: str,
        token_symbol: str,
        amount_usd: Optional[float] = None
    ) -> TradeResult:
        """
        Execute a buy order
        
        Args:
            contract_address: Token contract to buy
            chain: 'ethereum' or 'solana'
            token_symbol: Token symbol for logging
            amount_usd: Amount in USD to spend (defaults to config)
            
        Returns:
            TradeResult with position details
        """
        
        # Check position limit
        if len(self.open_positions) >= self.config.MAX_POSITIONS:
            return TradeResult(
                success=False,
                error_message=f"Maximum positions ({self.config.MAX_POSITIONS}) reached"
            )
        
        amount_usd = amount_usd or self.config.TRADE_AMOUNT_USD
        
        self.logger.info(
            f"🎯 Executing BUY: {token_symbol} on {chain} "
            f"Amount: ${amount_usd:.2f}"
        )
        
        try:
            # Route to appropriate chain
            if chain.lower() == 'ethereum':
                result = await self._execute_ethereum_buy(contract_address, token_symbol, amount_usd)
            elif chain.lower() == 'solana':
                result = await self._execute_solana_buy(contract_address, token_symbol, amount_usd)
            else:
                return TradeResult(
                    success=False,
                    error_message=f"Unsupported chain: {chain}"
                )
            
            # Track position if successful
            if result.success and result.position:
                self.open_positions[result.position.position_id] = result.position
                self.total_trades += 1
                
                self.logger.info(
                    f"✅ BUY executed: {token_symbol} | "
                    f"Price: ${result.position.entry_price:.8f} | "
                    f"Tokens: {result.position.entry_amount_tokens:.2f}"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ BUY failed: {e}")
            return TradeResult(
                success=False,
                error_message=str(e)
            )
    
    async def _execute_ethereum_buy(
        self,
        contract_address: str,
        token_symbol: str,
        amount_usd: float
    ) -> TradeResult:
        """Execute buy on Ethereum (Uniswap)"""
        
        if self.config.DRY_RUN_MODE:
            # Simulate successful trade
            position = Position(
                position_id=f"eth_{contract_address}_{int(datetime.now().timestamp())}",
                contract_address=contract_address,
                chain='ethereum',
                token_symbol=token_symbol,
                entry_price=0.00001,  # Simulated price
                entry_amount_usd=amount_usd,
                entry_amount_tokens=amount_usd / 0.00001,
                entry_tx_hash="0xDRYRUN",
                status=TradeStatus.OPEN
            )
            position.peak_price = position.entry_price
            position.update_current_price(position.entry_price)
            
            return TradeResult(
                success=True,
                position=position,
                tx_hash="0xDRYRUN"
            )
        
        # Real implementation would:
        # 1. Get current ETH price
        # 2. Calculate ETH amount needed
        # 3. Build Uniswap swap transaction
        # 4. Estimate gas
        # 5. Sign and send transaction
        # 6. Wait for confirmation
        # 7. Create Position object
        
        return TradeResult(
            success=False,
            error_message="Real Ethereum trading not yet implemented (remove DRY_RUN_MODE)"
        )
    
    async def _execute_solana_buy(
        self,
        contract_address: str,
        token_symbol: str,
        amount_usd: float
    ) -> TradeResult:
        """Execute buy on Solana (Raydium/Jupiter)"""
        
        if self.config.DRY_RUN_MODE:
            # Simulate successful trade
            position = Position(
                position_id=f"sol_{contract_address}_{int(datetime.now().timestamp())}",
                contract_address=contract_address,
                chain='solana',
                token_symbol=token_symbol,
                entry_price=0.00001,  # Simulated price
                entry_amount_usd=amount_usd,
                entry_amount_tokens=amount_usd / 0.00001,
                entry_tx_hash="DRYRUN",
                status=TradeStatus.OPEN
            )
            position.peak_price = position.entry_price
            position.update_current_price(position.entry_price)
            
            return TradeResult(
                success=True,
                position=position,
                tx_hash="DRYRUN"
            )
        
        # Real implementation would use Jupiter Aggregator API
        
        return TradeResult(
            success=False,
            error_message="Real Solana trading not yet implemented (remove DRY_RUN_MODE)"
        )
    
    async def execute_sell(
        self,
        position_id: str,
        reason: ExitReason = ExitReason.MANUAL
    ) -> TradeResult:
        """
        Execute a sell order to close a position
        
        Args:
            position_id: ID of position to close
            reason: Reason for closing
            
        Returns:
            TradeResult with final position details
        """
        
        if position_id not in self.open_positions:
            return TradeResult(
                success=False,
                error_message=f"Position {position_id} not found"
            )
        
        position = self.open_positions[position_id]
        
        self.logger.info(
            f"🎯 Executing SELL: {position.token_symbol} | "
            f"Reason: {reason.value} | "
            f"P&L: {position.profit_loss_percent:+.2f}%"
        )
        
        try:
            # Route to appropriate chain
            if position.chain == 'ethereum':
                result = await self._execute_ethereum_sell(position)
            elif position.chain == 'solana':
                result = await self._execute_solana_sell(position)
            else:
                return TradeResult(
                    success=False,
                    error_message=f"Unsupported chain: {position.chain}"
                )
            
            # Update position
            if result.success:
                position.status = TradeStatus.CLOSED
                position.exit_time = datetime.now()
                position.exit_price = position.current_price
                position.exit_amount_usd = position.current_value_usd
                position.exit_reason = reason
                position.exit_tx_hash = result.tx_hash
                
                # Move to closed positions
                del self.open_positions[position_id]
                self.closed_positions.append(position)
                
                # Update statistics
                if position.profit_loss_usd > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
                
                self.total_profit_usd += position.profit_loss_usd
                
                self.logger.info(
                    f"✅ SELL executed: {position.token_symbol} | "
                    f"P&L: ${position.profit_loss_usd:+.2f} ({position.profit_loss_percent:+.2f}%)"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ SELL failed: {e}")
            return TradeResult(
                success=False,
                error_message=str(e)
            )
    
    async def _execute_ethereum_sell(self, position: Position) -> TradeResult:
        """Execute sell on Ethereum"""
        
        if self.config.DRY_RUN_MODE:
            return TradeResult(
                success=True,
                position=position,
                tx_hash="0xDRYRUN_SELL"
            )
        
        # Real implementation would swap tokens back to ETH
        
        return TradeResult(
            success=False,
            error_message="Real Ethereum selling not yet implemented"
        )
    
    async def _execute_solana_sell(self, position: Position) -> TradeResult:
        """Execute sell on Solana"""
        
        if self.config.DRY_RUN_MODE:
            return TradeResult(
                success=True,
                position=position,
                tx_hash="DRYRUN_SELL"
            )
        
        # Real implementation would swap tokens back to SOL
        
        return TradeResult(
            success=False,
            error_message="Real Solana selling not yet implemented"
        )
    
    # ============================================
    # POSITION MANAGEMENT
    # ============================================
    
    async def monitor_positions(self):
        """Monitor all open positions and execute exit strategies"""
        
        while self.is_running:
            try:
                for position_id, position in list(self.open_positions.items()):
                    # Update current price (simplified - would fetch from DEX)
                    await self._update_position_price(position)
                    
                    # Check exit conditions
                    exit_reason = None
                    
                    # 1. Profit target
                    if position.should_take_profit(self.config.PROFIT_TARGET_PERCENT):
                        exit_reason = ExitReason.PROFIT_TARGET
                    
                    # 2. Stop loss
                    elif position.should_stop_loss(self.config.STOP_LOSS_PERCENT):
                        exit_reason = ExitReason.STOP_LOSS
                    
                    # 3. Trailing stop
                    elif position.should_trailing_stop(self.config.TRAILING_STOP_PERCENT):
                        exit_reason = ExitReason.TRAILING_STOP
                    
                    # 4. Time limit
                    elif position.should_time_exit(self.config.MAX_HOLD_TIME_HOURS):
                        exit_reason = ExitReason.TIME_LIMIT
                    
                    # Execute sell if any condition met
                    if exit_reason:
                        await self.execute_sell(position_id, exit_reason)
                
                # Sleep before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Position monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _update_position_price(self, position: Position):
        """Update position with current price"""
        
        # In dry run mode, simulate price movement
        if self.config.DRY_RUN_MODE:
            # Random walk simulation
            import random
            change_percent = random.uniform(-5, 15)  # Bias towards profit for testing
            new_price = position.current_price * (1 + change_percent / 100)
            position.update_current_price(new_price)
        else:
            # Real implementation would fetch from DEX
            pass
    
    # ============================================
    # PUBLIC API
    # ============================================
    
    async def start(self):
        """Start position monitoring"""
        self.is_running = True
        self.logger.info("✋ The Hand is now active")
        
        # Start monitoring task
        await self.monitor_positions()
    
    async def stop(self):
        """Stop all operations"""
        self.is_running = False
        
        if self.solana_client:
            await self.solana_client.close()
        
        self.logger.info("✋ The Hand has stopped")
    
    def get_statistics(self) -> Dict:
        """Get trading statistics"""
        win_rate = (
            (self.winning_trades / self.total_trades * 100)
            if self.total_trades > 0 else 0
        )
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit_usd': self.total_profit_usd,
            'open_positions': len(self.open_positions),
            'closed_positions': len(self.closed_positions),
        }
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.open_positions.values())


# ============================================
# MAIN EXECUTION
# ============================================

async def main():
    """Main execution function for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    
    hand = TheHand()
    await hand.initialize()
    
    # Test buy
    result = await hand.execute_buy(
        contract_address="0xTEST",
        chain="ethereum",
        token_symbol="TEST"
    )
    
    if result.success:
        print(f"\n✅ Test buy successful: {result.position.position_id}")
        print(f"Entry: ${result.position.entry_amount_usd:.2f}")
        
        # Simulate some price updates
        for i in range(5):
            await asyncio.sleep(2)
            await hand._update_position_price(result.position)
            print(f"Price update {i+1}: ${result.position.current_price:.8f} | P&L: {result.position.profit_loss_percent:+.2f}%")
    
    stats = hand.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
    
    await hand.stop()


if __name__ == '__main__':
    asyncio.run(main())

